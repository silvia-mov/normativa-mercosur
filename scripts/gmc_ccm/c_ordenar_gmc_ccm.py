"""Arma los textos de las Resoluciones GMC y Directivas CCM para el repositorio público.

Entrada:
  enlaces_todo.json, descargas_gmc.json, descargas_ccm.json   (datos del sitio y archivo elegido)
  texto_crudo/<carpeta>/<año>/<nombre>.txt                    texto de Word (a_texto_word.ps1 o a2_texto_word95.py)
  texto_crudo/<carpeta>/<año>/<nombre>.pdf.txt                texto de PDF (pdftotext u OCR, b_ocr_pdf.ps1)

Salida (carpeta publico/):
  resoluciones/<año>/RES_<nnn>-<año>_<título corto>.txt
  directivas/<año>/DIR_<nnn>-<año>_<título corto>.txt
  textos_gmc.json / textos_ccm.json   control de cada texto (lo usa armar_indice.py)

Cada texto lleva una cabecera con número, título, fecha, vigencia, idioma, archivo original y
cómo se convirtió, como los de las Decisiones. Además se controla que el encabezado del texto
(MERCOSUR/GMC/RES Nº x/aa) sea el de la norma y en qué idioma está.
Uso:  py c_ordenar_gmc_ccm.py
"""
import json
import re
import unicodedata
from pathlib import Path

from armar_indice import vigencia

RAIZ = Path(__file__).resolve().parent
PUB = RAIZ / "publico"
TIPOS = {
    "gmc": ("resoluciones_gmc", "resoluciones", "Resolución GMC", "GMC", "RES"),
    "ccm": ("directivas_ccm", "directivas", "Directiva CCM", "CCM", "DIR"),
}
SEP = "-" * 70
PT = re.compile(r"\b(TENDO EM VISTA|Resolução|Diretriz|não|são|também|serão|Comissão|Considerando que o)\b", re.I)
ES = re.compile(r"\b(VISTO|Resolución|Directiva|también|serán|Comisión|deberán|según)\b", re.I)


def encabezado(texto, organo, sigla):
    """Número y año del encabezado MERCOSUR/GMC/RES Nº x/aa (o su versión con errores de OCR)."""
    m = re.search(rf"MERCOSU[RL]\s*[/\\|]\s*{organo[:2]}\w?\s*[/\\|]?\s*{sigla[:2]}\w*\.?\s*(?:N[^\d\s]{{0,2}}\.?)?\s*(\d{{1,3}})\s*[/\\|]\s*(\d{{2,4}})",
                  texto[:3000], re.I)
    return (int(m.group(1)), int(m.group(2)) % 100) if m else None


def palabras(t):
    t = unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode().lower()
    return {p for p in re.findall(r"[a-z]{4,}", t)}


def coincide_titulo(titulo, texto):
    """True si al menos el 60 % de las palabras del título aparecen al comienzo del texto."""
    pt = palabras(re.sub(r"\(.*?\)", "", titulo))
    return bool(pt) and len(pt & palabras(texto[:2500])) >= 0.6 * len(pt)


def limpiar(t):
    t = t.lstrip("﻿").replace("\r\n", "\n").replace("\r", "\n")
    t = re.sub(r"[ \t ]+\n", "\n", t)
    return re.sub(r"\n{4,}", "\n\n\n", t).strip() + "\n"


def main():
    datos = json.loads((RAIZ / "enlaces_todo.json").read_text(encoding="utf-8"))
    log = RAIZ / "texto_crudo" / "conversion_word.log"
    directos = {Path(f).stem for f in re.findall(r"^([A-Z]:\\[^\t]+)\t", log.read_text(encoding="utf-8-sig"), re.M)} if log.exists() else set()
    for clave, (carpeta, salida, nombre, organo, sigla) in TIPOS.items():
        desc = {d["normativa_id"]: d for d in json.loads((RAIZ / f"descargas_{clave}.json").read_text(encoding="utf-8"))}
        control, sin_texto = [], []
        for r in datos[clave]:
            d = desc.get(r["normativa_id"], {})
            if not d.get("archivo"):
                continue
            arch = RAIZ / d["archivo"]
            anho = arch.parent.name
            crudo = RAIZ / "texto_crudo" / carpeta / anho / (arch.stem + (".pdf.txt" if arch.suffix == ".pdf" else ".txt"))
            if not crudo.exists():
                sin_texto.append(r["numero"])
                continue
            texto = limpiar(crudo.read_text(encoding="utf-8", errors="replace"))
            conversion = "OCR (Windows)" if arch.suffix == ".pdf" else "lectura directa del .doc" if arch.stem in directos else "Word"
            num, an = (int(x) for x in r["numero"].split("/"))
            enc = encabezado(texto, organo, sigla)
            pt, es = len(PT.findall(texto[:6000])), len(ES.findall(texto[:6000]))
            idioma_texto = "PT" if pt > es else "ES"
            nota = []
            if enc and enc != (num, an % 100):
                if coincide_titulo(r["titulo"], texto):
                    nota.append(f"el encabezado del documento dice {sigla} {enc[0]}/{enc[1]:02d}, pero el contenido coincide con el título")
                else:
                    nota.append(f"el texto publicado corresponde a otra norma ({sigla} {enc[0]}/{enc[1]:02d})")
            if idioma_texto != d.get("idioma"):
                nota.append(f"el sitio lo publica como {d.get('idioma')} pero el texto está en {idioma_texto}")
            cabecera = "\n".join([
                f"{nombre} N° {num:02d}/{an % 100:02d}",
                f"Título: {r['titulo']}",
                f"Fecha de aprobación: {r.get('fecha') or 'sin dato'}",
                f"Vigencia: {vigencia(r)}" + (f" ({r['vigencia']})" if r.get("vigencia") else ""),
                f"Idioma del texto: {idioma_texto}",
                f"Archivo original: {d['origen']}",
                f"Conversión a texto: {conversion}",
                *(["Nota: " + "; ".join(nota)] if nota else []),
                f"Fuente: Secretaría del MERCOSUR, normativa (https://normas.mercosur.int/public/normativas/{r['normativa_id']}).",
                SEP,
            ])
            dest = PUB / salida / anho / (arch.stem + ".txt")
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(cabecera + "\n" + texto, encoding="utf-8")
            control.append({"normativa_id": r["normativa_id"], "numero": r["numero"],
                            "texto": dest.relative_to(PUB).as_posix(), "conversion": conversion,
                            "idioma_texto": idioma_texto, "caracteres": len(texto), "nota": "; ".join(nota)})
        (RAIZ / f"textos_{clave}.json").write_text(json.dumps(control, ensure_ascii=False, indent=1), encoding="utf-8")
        notas = [c for c in control if c["nota"]]
        print(f"{nombre}: {len(control)} textos, sin texto {len(sin_texto)} {sin_texto[:10]}, con nota {len(notas)}")
        for c in notas:
            print(f"   {c['numero']}: {c['nota']}")


if __name__ == "__main__":
    main()
