"""Descarga Resoluciones GMC o Directivas CCM a partir de enlaces_todo.json.

enlaces_todo.json se arma en el navegador con obtener_enlaces_todo.js (Cloudflare
bloquea la lista y los detalles para programas; los archivos /simfiles/ sí
responden directo). Mismo método que descargar_resoluciones_gmc.py:

  - UN archivo por norma: español .docx > .doc > .odt > .pdf > cualquier español
    > cualquier otro idioma.
  - 1 segundo de pausa entre descargas.
  - Si el archivo ya existe, no se vuelve a bajar.

Nombres:  resoluciones_gmc/<año>/RES_<nnn>-<año>_<titulo-corto>.<ext>
          directivas_ccm/<año>/DIR_<nnn>-<año>_<titulo-corto>.<ext>

Deja el resultado de cada norma en descargas_<tipo>.json (lo usa armar_indice.py).

Uso:  py descargar_normas.py gmc|ccm
Solo usa la biblioteca estándar de Python.
"""

import json
import re
import subprocess
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

CARPETA = Path(__file__).resolve().parent
BASE = "https://normas.mercosur.int/simfiles/normativas/"
PAUSA_SEGUNDOS = 1.0
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)
PREFERENCIA_EXT = [".docx", ".doc", ".odt", ".pdf"]
TIPOS = {
    "gmc": {"nombre": "Resoluciones GMC", "carpeta": "resoluciones_gmc", "prefijo": "RES"},
    "ccm": {"nombre": "Directivas CCM", "carpeta": "directivas_ccm", "prefijo": "DIR"},
}


def idioma_real(a):
    """El sitio a veces etiqueta mal el idioma (p. ej. '(Alemán)' para un archivo _ES_);
    si el nombre del archivo dice _ES_ o _PT_, manda el nombre."""
    m = re.search(r"_(ES|PT)_", a["archivo"])
    return m.group(1) if m else a["idioma"]


def ordenar(archivos):
    archivos = [dict(a, idioma=idioma_real(a)) for a in archivos]
    def puntaje(a):
        ext = Path(a["archivo"]).suffix.lower()
        orden_ext = PREFERENCIA_EXT.index(ext) if ext in PREFERENCIA_EXT else len(PREFERENCIA_EXT)
        return (a["idioma"] != "ES", orden_ext)

    return sorted(archivos, key=puntaje)


def titulo_corto(titulo, max_palabras=6, max_largo=50):
    sin_parentesis = re.sub(r"\(.*?\)", "", titulo)
    ascii_ = unicodedata.normalize("NFKD", sin_parentesis).encode("ascii", "ignore").decode()
    palabras = re.findall(r"[A-Za-z0-9]+", ascii_.lower())
    corto = "-".join(palabras[:max_palabras])[:max_largo].strip("-")
    return corto or "sin-titulo"


def numero_y_anho(numero, anho_lista):
    """'7/1995' -> ('007', '1995'). Números raros ('7bis') quedan saneados."""
    partes = numero.split("/")
    num = partes[0].strip()
    anho = partes[1].strip() if len(partes) > 1 and partes[1].strip() else str(anho_lista)
    num = f"{int(num):03d}" if num.isdigit() else re.sub(r"[^A-Za-z0-9]+", "", num) or "sn"
    return num, anho


def descargar(url):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            contenido = resp.read()
        if not contenido:
            raise RuntimeError("el sitio devolvió un archivo vacío")
        return contenido
    except urllib.error.HTTPError as e:
        # Cloudflare rechaza al cliente de Python en algunos archivos (sobre todo
        # extensiones en mayúsculas, .DOC/.DOCX) que curl baja sin problema.
        if e.code != 403:
            raise
        time.sleep(PAUSA_SEGUNDOS)
        r = subprocess.run(["curl", "-sf", "-A", USER_AGENT, "--max-time", "120", url],
                           capture_output=True)
        if r.returncode != 0 or not r.stdout:
            raise RuntimeError(f"HTTP 403 (también con curl, código {r.returncode})")
        return r.stdout


def main():
    clave = sys.argv[1] if len(sys.argv) > 1 else ""
    if clave not in TIPOS:
        sys.exit("Uso: py descargar_normas.py gmc|ccm")
    t = TIPOS[clave]
    normas = json.loads((CARPETA / "enlaces_todo.json").read_text(encoding="utf-8"))[clave]

    resultados, ok, existian, errores = [], 0, 0, 0
    for r in normas:
        num, anho = numero_y_anho(r["numero"], r["anho"])
        res = {"normativa_id": r["normativa_id"], "numero": r["numero"]}
        candidatos = ordenar(r.get("archivos") or [])
        if not candidatos:
            res.update(estado="error", motivo=r.get("error_archivos") or "sin archivos publicados")
            resultados.append(res)
            errores += 1
            continue

        def destino_de(c):
            ext = Path(c["archivo"]).suffix.lower()
            return CARPETA / t["carpeta"] / anho / f"{t['prefijo']}_{num}-{anho}_{titulo_corto(r['titulo'])}{ext}"

        previo = next((c for c in candidatos if destino_de(c).exists() and destino_de(c).stat().st_size > 0), None)
        if previo:
            res.update(estado="ya existía", archivo=destino_de(previo).relative_to(CARPETA).as_posix(),
                       idioma=previo["idioma"], origen=previo["archivo"])
            existian += 1
            resultados.append(res)
            continue
        # Prueba el preferido; si el sitio lo rechaza, el siguiente en el orden de preferencia.
        fallos = []
        for c in candidatos:
            destino = destino_de(c)
            destino.parent.mkdir(parents=True, exist_ok=True)
            try:
                time.sleep(PAUSA_SEGUNDOS)
                destino.write_bytes(descargar(BASE + urllib.parse.quote(c["archivo"])))
            except Exception as e:
                fallos.append(f"{c['archivo']}: {e}")
                continue
            res.update(estado="descargada", archivo=destino.relative_to(CARPETA).as_posix(),
                       idioma=c["idioma"], origen=c["archivo"])
            if fallos:
                res["nota"] = "versión alternativa; falló: " + " | ".join(fallos)
            ok += 1
            break
        else:
            res.update(estado="error", motivo=" | ".join(fallos))
            errores += 1
        resultados.append(res)

    (CARPETA / f"descargas_{clave}.json").write_text(
        json.dumps(resultados, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{t['nombre']}: {len(normas)} en la lista | descargadas {ok} | ya existían {existian} | errores {errores}")
    return 1 if errores else 0


if __name__ == "__main__":
    sys.exit(main())
