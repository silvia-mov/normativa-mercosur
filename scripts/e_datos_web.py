"""
Arma los datos del buscador y del asistente de la página web (docs/datos/).

Usa solo textos en español:
  - Decisiones CMC: el texto principal (la fe de erratas si existe, porque es la versión vigente),
    según indice_decisiones.csv.
  - Resoluciones GMC y Directivas CCM: el texto de cada norma, según indices/indice_normativa_mercosur.csv
    (se dejan afuera los que el control marcó como texto de otra norma).
Corta cada texto en fragmentos de ~1.200 caracteres y guarda, por norma: código, título, año, enlace,
tipo (dec, res, dir) y vigencia (solo Resoluciones y Directivas). Un archivo por tipo, para que la página
cargue primero las decisiones y sume las demás en segundo plano:
  docs/datos/fragmentos.json (decisiones), fragmentos_res.json, fragmentos_dir.json
Uso: python3 scripts/e_datos_web.py
"""
import csv
import json
import re
from collections import defaultdict
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
BASE_URL = "https://github.com/silvia-mov/normativa-mercosur/blob/main/"
TOPE = {"dec": 60_000, "res": 20_000, "dir": 15_000}   # los textos larguísimos son listas y tablas; se recortan
LARGO = 1200
SIGLA = {"Resolución GMC": ("res", "Res. GMC"), "Directiva CCM": ("dir", "Dir. CCM")}


def limpiar(texto, tope):
    texto = texto.split("-" * 70, 1)[-1]                       # sin la cabecera
    texto = re.sub(r"\[página \d+\]", " ", texto)
    texto = re.sub(r"[ \t]+", " ", texto)
    return re.sub(r"\n\s*\n+", "\n", texto).strip()[:tope]


datos = {t: {"normas": [], "fragmentos": []} for t in ("dec", "res", "dir")}


def agregar(codigo, titulo, anio, ruta, tipo, vig=""):
    texto = limpiar((RAIZ / ruta).read_text(encoding="utf-8"), TOPE[tipo])
    normas, fragmentos = datos[tipo]["normas"], datos[tipo]["fragmentos"]
    normas.append([codigo, titulo, anio, BASE_URL + ruta, tipo, vig])
    actual = ""
    for p in texto.split("\n"):
        if len(actual) + len(p) > LARGO and actual:
            fragmentos.append([len(normas) - 1, actual.strip()])
            actual = ""
        actual += p + "\n"
    if actual.strip():
        fragmentos.append([len(normas) - 1, actual.strip()])


# Decisiones CMC
filas = list(csv.DictReader(open(RAIZ / "indice_decisiones.csv", encoding="utf-8-sig")))
por_dec = defaultdict(list)
for r in filas:
    if r["TIPO"] in ("texto", "fe-de-erratas") and r["IDIOMA"] == "ES" and r["TEXTO"]:
        por_dec[(int(r["AÑO"]), int(r["NUMERO"]))].append(r)
for (anio, num), rs in sorted(por_dec.items()):
    r = sorted(rs, key=lambda x: (x["TIPO"] != "fe-de-erratas", -int(x["CARACTERES"])))[0]
    titulo = re.sub(r"\s*\(título del nombre del archivo\)", "", r["TITULO"]).strip().strip("'\" ")
    agregar(f"Dec. CMC {num:02d}/{str(anio)[2:]}", titulo, anio, r["TEXTO"], "dec")

# Resoluciones GMC y Directivas CCM
for r in csv.DictReader(open(RAIZ / "indices" / "indice_normativa_mercosur.csv", encoding="utf-8-sig")):
    if not r["TEXTO"] or r["IDIOMA_TEXTO"] != "ES" or "otra norma" in r["NOTA"]:
        continue
    tipo, sigla = SIGLA[r["TIPO"]]
    num, anio = (int(x) for x in r["NUMERO"].split("/"))
    agregar(f"{sigla} {num:02d}/{anio % 100:02d}", r["TITULO"], anio, r["TEXTO"], tipo,
            r["VIGENCIA"] if r["VIGENCIA"] in ("Vigente", "Derogada") else "")

for tipo, nombre in (("dec", "fragmentos.json"), ("res", "fragmentos_res.json"), ("dir", "fragmentos_dir.json")):
    salida = RAIZ / "docs" / "datos" / nombre
    salida.parent.mkdir(parents=True, exist_ok=True)
    salida.write_text(json.dumps(datos[tipo], ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"{nombre}: {len(datos[tipo]['normas'])} normas, {len(datos[tipo]['fragmentos'])} fragmentos, "
          f"{salida.stat().st_size / 1e6:.1f} MB")
