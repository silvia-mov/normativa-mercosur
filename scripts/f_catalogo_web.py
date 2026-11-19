"""
Arma docs/datos/catalogo.json para el selector de descargas de la página (tipo, año, número -> .txt).

Por norma guarda: año, número, título, carpeta y archivo del texto principal, número de ficha en
normas.mercosur.int (para ir al original) y, en Resoluciones y Directivas, la vigencia.
En las Decisiones el texto principal es el texto en español (la fe de erratas si existe); los anexos,
planillas y versiones en otro idioma van como archivos extra.
Fuentes: indice_decisiones.csv, indices/fichas_decisiones.csv e indices/indice_normativa_mercosur.csv.
Uso: python3 scripts/f_catalogo_web.py
"""
import csv
import json
import re
from collections import defaultdict
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
leer = lambda p: list(csv.DictReader(open(RAIZ / p, encoding="utf-8-sig")))


def partir(ruta):
    """'decisiones/1991/DEC_001-1991_....txt' -> ('decisiones', '1991', 'DEC_001-1991_....txt')"""
    carpeta, anio, archivo = ruta.split("/")
    return carpeta, archivo


def etiqueta(r):
    tipo = r["TIPO"]
    if tipo == "texto":
        nombre = "Texto"
    elif tipo == "fe-de-erratas":
        nombre = "Fe de erratas"
    else:
        m = re.match(r"(anexo|planilla)-(\d+)", tipo)
        nombre = f"{m.group(1).capitalize()} {m.group(2)}" if m else tipo
    return f"{nombre} ({r['IDIOMA']})"


catalogo = {"dec": [], "res": [], "dir": []}

# Decisiones
fichas = {(int(r["AÑO"]), int(r["NUMERO"])): int(r["ID_FICHA"]) for r in leer("indices/fichas_decisiones.csv")}
por_dec = defaultdict(list)
for r in leer("indice_decisiones.csv"):
    if r["TEXTO"] and r["TIPO"] not in ("duplicado", "comprimido") and not r["TEXTO"].startswith("incorporacion"):
        por_dec[(int(r["AÑO"]), int(r["NUMERO"]))].append(r)
for (anio, num), rs in sorted(por_dec.items()):
    textos = [r for r in rs if r["TIPO"] in ("texto", "fe-de-erratas")]
    if not textos:
        continue
    principal = sorted(textos, key=lambda x: (x["IDIOMA"] != "ES", x["TIPO"] != "fe-de-erratas", -int(x["CARACTERES"] or 0)))[0]
    titulo = re.sub(r"\s*\(título del nombre del archivo\)", "", principal["TITULO"]).strip().strip("'\" ")
    extras = [[etiqueta(r), partir(r["TEXTO"])[1]] for r in rs if r is not principal]
    fila = [anio, num, titulo, partir(principal["TEXTO"])[1], fichas.get((anio, num), 0)]
    if extras:
        fila.append(extras)
    catalogo["dec"].append(fila)

# Resoluciones GMC y Directivas CCM
for r in leer("indices/indice_normativa_mercosur.csv"):
    if not r["TEXTO"]:
        continue
    clave = "res" if r["TIPO"].startswith("Resolución") else "dir"
    num, anio = (int(x) for x in r["NUMERO"].split("/"))
    vig = r["VIGENCIA"] if r["VIGENCIA"] in ("Vigente", "Derogada") else ""
    catalogo[clave].append([anio, num, r["TITULO"], partir(r["TEXTO"])[1], int(r["ID_SITIO"]), vig])

salida = RAIZ / "docs" / "datos" / "catalogo.json"
salida.write_text(json.dumps(catalogo, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
print({k: len(v) for k, v in catalogo.items()}, f"{salida.stat().st_size / 1e6:.2f} MB")
