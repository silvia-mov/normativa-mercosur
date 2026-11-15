"""
Arma docs/datos/fragmentos.json para el buscador y el asistente de la página web.

Usa solo el texto principal en español de cada decisión (la fe de erratas si existe, porque es la versión
vigente), lo corta en fragmentos de ~1.200 caracteres y guarda: código, título, año, enlace y texto.
Uso: python3 scripts/e_datos_web.py
"""
import csv
import json
import re
from collections import defaultdict
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
BASE_URL = "https://github.com/silvia-mov/normativa-mercosur/blob/main/"
TOPE = 60_000          # los textos larguísimos son listas de compromisos; se recortan
LARGO = 1200

filas = list(csv.DictReader(open(RAIZ / "indice_decisiones.csv", encoding="utf-8-sig")))
por_dec = defaultdict(list)
for r in filas:
    if r["TIPO"] in ("texto", "fe-de-erratas") and r["IDIOMA"] == "ES" and r["TEXTO"]:
        por_dec[(int(r["AÑO"]), int(r["NUMERO"]))].append(r)

fragmentos, decisiones = [], []
for (anio, num), rs in sorted(por_dec.items()):
    r = sorted(rs, key=lambda x: (x["TIPO"] != "fe-de-erratas", -int(x["CARACTERES"])))[0]
    texto = (RAIZ / r["TEXTO"]).read_text(encoding="utf-8")
    texto = texto.split("-" * 70, 1)[-1]                       # sin la cabecera
    texto = re.sub(r"\[página \d+\]", " ", texto)
    texto = re.sub(r"[ \t]+", " ", texto)
    texto = re.sub(r"\n\s*\n+", "\n", texto).strip()[:TOPE]
    codigo = f"Dec. CMC {num:02d}/{str(anio)[2:]}"
    titulo = re.sub(r"\s*\(título del nombre del archivo\)", "", r["TITULO"]).strip().strip("'\" ")
    decisiones.append([codigo, titulo, anio, BASE_URL + r["TEXTO"]])
    parrafos, actual = texto.split("\n"), ""
    for p in parrafos:
        if len(actual) + len(p) > LARGO and actual:
            fragmentos.append([len(decisiones) - 1, actual.strip()])
            actual = ""
        actual += p + "\n"
    if actual.strip():
        fragmentos.append([len(decisiones) - 1, actual.strip()])

salida = RAIZ / "docs" / "datos" / "fragmentos.json"
salida.parent.mkdir(parents=True, exist_ok=True)
salida.write_text(json.dumps({"decisiones": decisiones, "fragmentos": fragmentos}, ensure_ascii=False,
                             separators=(",", ":")), encoding="utf-8")
print(f"{len(decisiones)} decisiones, {len(fragmentos)} fragmentos, {salida.stat().st_size / 1e6:.1f} MB")
