"""
Ordena y renombra las decisiones del CMC (MERCOSUR) para el repositorio público.

Entrada:
  originales/<año>/...        archivos tal como se bajaron del sitio del MERCOSUR
  texto_crudo/<año>/<nombre>.txt  su texto (Word -> LibreOffice; PDF -> pdftotext u OCR)

Salida (carpeta publico/):
  decisiones/<año>/<CODIGO>.txt          texto en UTF-8 con una cabecera de datos
  originales/<año>/<CODIGO>.<ext>        el archivo original, con el nombre nuevo
  incorporacion_paraguay/<año>/...       notas de Cancillería y decretos sobre incorporación
  indice_decisiones.csv                  una fila por archivo

Nombre nuevo: DEC_<número>-<año>_<idioma>_<tipo>_<título corto>
  tipo: texto | fe-de-erratas | anexo-N | planilla-N
Uso: python3 scripts/c_ordenar.py
"""
import csv
import hashlib
import os
import re
import shutil
import unicodedata
from collections import defaultdict
from pathlib import Path

RAIZ = Path("/home/user/normas_trabajo")
ORIG, CRUDO, PUB = RAIZ / "originales", RAIZ / "texto_crudo", RAIZ / "publico"

CABECERA = re.compile(r"MERCOSU[RL]\s*[/\\][^\n/\\]{0,20}?(?:[/\\][^\n/\\]{0,12}?)?DEC\s*\.?\s*(?:N[^\d\n]{0,3})?\s*(\d{1,3})\s*/\s*(\d{2,4})", re.I)
NUM_NOMBRE = re.compile(r"DEC[ _.\-]*0*(\d{1,3})(?!\d)", re.I)
INCORPORACION = re.compile(r"VMREI|DGPE|DIE[ _-]|MRE[-_ ]PY|Nota[ _]DIE|Incorporaci|^decreto|_decreto", re.I)


def nombre_legible(p):
    """Los nombres de archivo vienen en Windows-1252; se pasan a texto normal."""
    crudo = os.fsencode(p.name)
    try:
        return crudo.decode("utf-8")
    except UnicodeDecodeError:
        pass
    # Unos vienen en Windows-1252 y otros en la codificación de DOS (cp850): se elige la que da más letras del español
    opciones = [crudo.decode(c, "replace") for c in ("cp1252", "cp850")]
    return max(opciones, key=lambda t: sum(t.count(x) for x in "áéíóúñÁÉÍÓÚÑçãõâêô") - 2 * sum(t.count(x) for x in "¡¢£¤¥¦§¨©ª«¬®¯°±²³´µ¶·¸¹º»¼½¾¿├┤┬┴┼"))


def corto(texto, n=60):
    t = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode().lower()
    t = re.sub(r"[^a-z0-9]+", "-", t).strip("-")
    if len(t) > n:
        t = t[:n].rsplit("-", 1)[0]
    return t or "sin-titulo"


def leer_texto(p):
    # Word -> <nombre>.txt ; PDF -> <nombre>.pdf.txt ; planillas -> <nombre>.xls.txt (así no se pisan)
    ext = p.suffix.lower()
    t = CRUDO / p.parent.name / (p.stem + (ext + ".txt" if ext in (".pdf", ".xls", ".xlsx") else ".txt"))
    if not t.exists():
        return None
    s = t.read_text(encoding="utf-8", errors="replace").lstrip("﻿")
    return s


def titulo_de(texto):
    """Las líneas entre 'MERCOSUR/CMC/DEC. Nº x/aa' y 'VISTO'."""
    lineas = [l.strip() for l in texto.splitlines()]
    for i, l in enumerate(lineas[:80]):
        if CABECERA.search(l):
            partes = []
            for l2 in lineas[i + 1:i + 15]:
                if re.match(r"VISTOS?\b|VISTO:|TENDO EM VISTA|CONSIDERANDO", l2, re.I):
                    break
                if l2 and not l2.startswith("[página"):
                    partes.append(l2)
            t = re.sub(r"\s+", " ", " ".join(partes)).strip(" .")
            return t[:300]
    return ""


def idioma_de(nombre, texto):
    if re.search(r"ingl[eé]s|_ING_|english", nombre, re.I):
        return "EN"
    if re.search(r"hebreo", nombre, re.I):
        return "HE"
    if texto and len(texto) > 300:   # el contenido manda: algunos nombres dicen PT y el texto está en español
        inicio = texto[:2500].upper()
        # el que aparece primero (hay documentos con la versión en español y después en portugués)
        m_pt = inicio.find("TENDO EM VISTA")
        m_es = re.search(r"\bVISTOS?\s*:", inicio)
        m_es = m_es.start() if m_es else -1
        if m_pt >= 0 or m_es >= 0:
            if m_pt < 0:
                return "ES"
            if m_es < 0:
                return "PT"
            return "ES" if m_es < m_pt else "PT"
        t = texto[:5000].lower()
        pt = t.count("ção") + t.count("tendo em vista") * 5 + t.count(" não ") + t.count(" do ")
        es = t.count("ción") + t.count("visto:") * 5 + t.count(" del ") + t.count(" el ")
        if pt or es:
            return "PT" if pt > es else "ES"
    if re.search(r"[_ -]PT[_ .-]|_PT$|-PT\b|\bPT\b", nombre):
        return "PT"
    if re.search(r"[_ -]ES[_ .-]|-ESP|\bES\b", nombre):
        return "ES"
    if texto:
        t = texto[:4000].lower()
        return "PT" if t.count(" da ") + t.count(" não ") > t.count(" de la ") + t.count(" del ") else "ES"
    return "ES"


def main():
    if PUB.exists():
        shutil.rmtree(PUB)
    filas, vistos = [], {}
    archivos = sorted(p for p in ORIG.rglob("*") if p.is_file() and p.parent.parent == ORIG)
    # 1) leer cada archivo y lo que se sabe de él
    info = []
    for p in archivos:
        anio = int(p.parent.name)
        nombre = nombre_legible(p)
        texto = leer_texto(p)
        id_sitio = re.match(r"(\d+)_", nombre).group(1) if re.match(r"\d+_", nombre) else ""
        cab = CABECERA.search(texto[:2500]) if texto else None
        num_texto = int(cab.group(1)) if cab else None
        m = NUM_NOMBRE.search(nombre)
        num_nombre = int(m.group(1)) if m else None
        h = hashlib.md5(p.read_bytes()).hexdigest()
        info.append(dict(p=p, anio=anio, nombre=nombre, texto=texto, id=id_sitio, num_texto=num_texto,
                         num_nombre=num_nombre, md5=h, ext=p.suffix.lower().lstrip(".")))
    # 2) número de decisión por grupo de archivos con el mismo id del sitio
    por_id = defaultdict(set)
    for i in info:
        n = i["num_texto"] or i["num_nombre"]
        if n and i["id"] and not INCORPORACION.search(i["nombre"]):
            por_id[(i["anio"], i["id"])].add(n)
    titulos = {}
    for i in info:
        if i["num_texto"] and i["texto"]:
            t = titulo_de(i["texto"])
            if t and (i["anio"], i["num_texto"]) not in titulos:
                titulos[(i["anio"], i["num_texto"])] = t
    # Si el texto no trae título (p. ej. 1992), se usa el del nombre del archivo
    for i in info:
        n = i["num_texto"] or i["num_nombre"]
        if n and (i["anio"], n) not in titulos and i["ext"] in ("doc", "docx", "rtf", "pdf") \
                and not INCORPORACION.search(i["nombre"]) and not re.search(r"anexo", i["nombre"], re.I):
            t = re.sub(r"^\d+_|DEC[ _.\-]*\d+[ _\-]*\d{2,4}|_(ES|PT)_|FERR\s*\d*|_FE_|_?Acta\s*\d+[_ ]\d+", " ",
                       Path(i["nombre"]).stem, flags=re.I)
            t = re.sub(r"[_\s]+", " ", t).strip(" -.")
            if t:
                titulos[(i["anio"], n)] = t + " (título del nombre del archivo)"
    contador = defaultdict(int)
    comprimidos = {}   # (año, nombre sin extensión) -> número de decisión
    for i in info:
        nombre, anio = i["nombre"], i["anio"]
        if i["md5"] in vistos:
            filas.append(dict(AÑO=anio, NUMERO="", CODIGO="", TITULO="", TIPO="duplicado", IDIOMA="",
                              ARCHIVO_NUEVO="", TEXTO="", ARCHIVO_ORIGINAL=nombre, ID_SITIO=i["id"],
                              CONVERSION="", CARACTERES=0, NOTA=f"igual a {vistos[i['md5']]}"))
            continue
        vistos[i["md5"]] = nombre
        if INCORPORACION.search(nombre):
            carpeta, base = PUB / "incorporacion_paraguay" / str(anio), corto(Path(nombre).stem, 90)
            tipo, num = "incorporacion", None
        else:
            num = i["num_texto"] or i["num_nombre"]
            if num is None and len(por_id.get((anio, i["id"]), ())) == 1:
                num = next(iter(por_id[(anio, i["id"])]))
            carpeta = PUB / "decisiones" / str(anio)
            if num is None:
                tipo, base = "sin-identificar", corto(Path(nombre).stem, 90)
            else:
                if i["ext"] in ("zip", "rar"):
                    comprimidos[(anio, i["p"].stem)] = num
                primeras = [l.strip() for l in (i["texto"] or "").splitlines() if l.strip()][:6]
                al_inicio = any(CABECERA.search(l) for l in primeras) and not re.match(r"ANEXO", primeras[0] if primeras else "", re.I)
                es_principal = bool(i["num_texto"]) and (al_inicio or not re.search(r"anexo|annex", nombre, re.I))
                fe = bool(re.search(r"FERR|_FE_|FE DE ERRATAS", nombre + (i["texto"] or "")[:400], re.I))
                if es_principal:
                    tipo = "fe-de-erratas" if fe else "texto"
                else:
                    clave = (anio, num, "planilla" if i["ext"] in ("xls", "xlsx") else "anexo")
                    contador[clave] += 1
                    tipo = f"{clave[2]}-{contador[clave]}"
                titulo = titulos.get((anio, num), "")
                base = f"DEC_{num:03d}-{anio}_{idioma_de(nombre, i['texto'])}_{tipo}"
                if tipo in ("texto", "fe-de-erratas") and titulo:
                    base += "_" + corto(titulo)
        # evitar nombres repetidos (p. ej. dos fe de erratas)
        if i["ext"] in ("zip", "rar"):
            filas.append(dict(AÑO=anio, NUMERO=num or "", CODIGO=f"DEC_{num:03d}-{anio}" if num else "", TITULO="",
                              TIPO="comprimido", IDIOMA="", ARCHIVO_NUEVO="", TEXTO="", ARCHIVO_ORIGINAL=nombre,
                              ID_SITIO=i["id"], CONVERSION="", CARACTERES=0,
                              NOTA="su contenido se abrió y figura como anexos"))
            continue
        dest_orig = PUB / "originales_renombrados" / ("incorporacion_paraguay" if tipo == "incorporacion" else "decisiones") / str(anio)
        dest_orig.mkdir(parents=True, exist_ok=True)
        carpeta.mkdir(parents=True, exist_ok=True)
        nuevo, k = base, 2
        while any(dest_orig.glob(nuevo + ".*")):
            nuevo, k = f"{base}_v{k}", k + 1
        shutil.copy2(i["p"], dest_orig / (nuevo + "." + i["ext"]))
        texto, conversion = i["texto"], ""
        if texto is not None:
            conversion = "OCR" if "[página" in texto[:40] else ("texto del PDF" if i["ext"] == "pdf" else "Word")
            titulo = titulos.get((anio, num), "") if num else ""
            encabezado = [f"Decisión CMC N° {num:02d}/{str(anio)[2:]}" if num else "Documento",
                          f"Título: {titulo}" if titulo else None,
                          f"Tipo de documento: {tipo}", f"Archivo original: {nombre}",
                          f"Conversión a texto: {conversion}" + (" (puede tener errores de lectura)" if conversion == "OCR" else ""),
                          "Fuente: Secretaría del MERCOSUR, normativa (https://www.mercosur.int/documentos/normativa/).",
                          "-" * 70, ""]
            (carpeta / (nuevo + ".txt")).write_text("\n".join(l for l in encabezado if l is not None) + texto.strip() + "\n",
                                                    encoding="utf-8")
        filas.append(dict(AÑO=anio, NUMERO=num or "", CODIGO=f"DEC_{num:03d}-{anio}" if num else "",
                          TITULO=titulos.get((anio, num), "") if num else "", TIPO=tipo,
                          IDIOMA=idioma_de(nombre, texto), ARCHIVO_NUEVO=f"{nuevo}.{i['ext']}",
                          TEXTO=(str((carpeta / (nuevo + ".txt")).relative_to(PUB)) if texto is not None else ""),
                          ARCHIVO_ORIGINAL=nombre, ID_SITIO=i["id"], CONVERSION=conversion,
                          CARACTERES=len(texto or ""), NOTA=""))
    # archivos que venían dentro de un zip o rar
    ANID, TANID = RAIZ / "anidados", RAIZ / "texto_anidado"
    for p in sorted(q for q in ANID.rglob("*") if q.is_file()):
        rel = p.relative_to(ANID)
        anio, padre = int(rel.parts[0]), rel.parts[1]
        num = comprimidos.get((anio, padre))
        dentro = "/".join(os.fsencode(x).decode("utf-8", "replace") for x in rel.parts[2:])
        nombre = f"{os.fsencode(padre).decode('cp1252', 'replace')} > {dentro}"
        ext = p.suffix.lower().lstrip(".")
        t = TANID / rel.with_suffix(".txt")
        texto = t.read_text(encoding="utf-8", errors="replace").lstrip("\ufeff") if t.exists() else None
        if texto is not None and len(texto.strip()) < 200 and ext == "pdf":
            texto = None   # PDF escaneado: hay una planilla con los mismos datos
        primeras = [l.strip() for l in (texto or "").splitlines() if l.strip()][:6]
        principal = num is not None and any(CABECERA.search(l) for l in primeras) \
            and not re.match(r"ANEXO", primeras[0] if primeras else "", re.I) and idioma_de(dentro, texto) in ("ES", "PT")
        if num is None:
            tipo, base, carpeta = "sin-identificar", corto(p.stem, 90), PUB / "decisiones" / str(anio)
        elif principal:
            tipo = "texto"
            base, carpeta = f"DEC_{num:03d}-{anio}_{idioma_de(dentro, texto)}_texto", PUB / "decisiones" / str(anio)
            if titulos.get((anio, num)):
                base += "_" + corto(titulos[(anio, num)].replace(" (título del nombre del archivo)", ""))
        else:
            clave = (anio, num, "planilla" if ext in ("xls", "xlsx") else "anexo")
            contador[clave] += 1
            tipo = f"{clave[2]}-{contador[clave]}"
            base, carpeta = f"DEC_{num:03d}-{anio}_{idioma_de(dentro, texto)}_{tipo}", PUB / "decisiones" / str(anio)
        dest_orig = PUB / "originales_renombrados" / "decisiones" / str(anio)
        dest_orig.mkdir(parents=True, exist_ok=True)
        nuevo, k = base, 2
        while any(dest_orig.glob(nuevo + ".*")):
            nuevo, k = f"{base}_v{k}", k + 1
        shutil.copy2(p, dest_orig / f"{nuevo}.{ext}")
        conversion = ""
        if texto is not None:
            conversion = "planilla" if ext in ("xls", "xlsx") else ("texto del PDF" if ext == "pdf" else "Word")
            enc = [f"Decisión CMC N° {num:02d}/{str(anio)[2:]}" if num else "Documento",
                   f"Título: {titulos.get((anio, num), '')}" if num and titulos.get((anio, num)) else None,
                   f"Tipo de documento: {tipo}", f"Archivo original: {nombre}", f"Conversión a texto: {conversion}",
                   "Fuente: Secretaría del MERCOSUR, normativa (https://www.mercosur.int/documentos/normativa/).",
                   "-" * 70, ""]
            (carpeta / f"{nuevo}.txt").write_text("\n".join(l for l in enc if l is not None) + texto.strip() + "\n",
                                                 encoding="utf-8")
        filas.append(dict(AÑO=anio, NUMERO=num or "", CODIGO=f"DEC_{num:03d}-{anio}" if num else "",
                          TITULO=titulos.get((anio, num), "") if num else "", TIPO=tipo,
                          IDIOMA=idioma_de(dentro, texto), ARCHIVO_NUEVO=f"{nuevo}.{ext}",
                          TEXTO=str((carpeta / f"{nuevo}.txt").relative_to(PUB)) if texto is not None else "",
                          ARCHIVO_ORIGINAL=nombre, ID_SITIO="", CONVERSION=conversion,
                          CARACTERES=len(texto or ""), NOTA="venía dentro de un archivo comprimido"))
    with open(PUB / "indice_decisiones.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(filas[0]))
        w.writeheader()
        w.writerows(filas)
    # resumen
    decs = {(f["AÑO"], f["NUMERO"]) for f in filas if f["NUMERO"] and f["TIPO"] in ("texto", "fe-de-erratas")}
    todas = {(f["AÑO"], f["NUMERO"]) for f in filas if f["NUMERO"]}
    sin_texto = sorted(todas - decs)
    print(f"archivos {len(filas)}; decisiones {len(todas)}; con texto principal {len(decs)}")
    print("sin texto principal identificado:", sin_texto[:40], len(sin_texto))
    print("sin identificar:", sum(f["TIPO"] == "sin-identificar" for f in filas),
          "duplicados:", sum(f["TIPO"] == "duplicado" for f in filas),
          "incorporación:", sum(f["TIPO"] == "incorporacion" for f in filas))


if __name__ == "__main__":
    main()
