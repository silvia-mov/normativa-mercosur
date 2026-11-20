"""
Arma los datos del buscador y del asistente de la página web (docs/datos/).

Usa los textos en español y, cuando una norma solo tiene texto oficial en portugués (también idioma oficial del
MERCOSUR), ese texto, marcado en el título:
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
RECORTADAS = {"dec": 0, "res": 0, "dir": 0}


def agregar(codigo, titulo, anio, ruta, tipo, vig=""):
    completo = limpiar((RAIZ / ruta).read_text(encoding="utf-8"), 10**9)
    texto = completo[:TOPE[tipo]]
    if len(completo) > len(texto):                              # se avisa que el texto sigue en la norma completa
        texto += "\n[… texto recortado: el resto está en la norma completa]"
        RECORTADAS[tipo] += 1
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
    if not r["TEXTO"] or r["IDIOMA_TEXTO"] not in ("ES", "PT") or "otra norma" in r["NOTA"]:
        continue
    tipo, sigla = SIGLA[r["TIPO"]]
    num, anio = (int(x) for x in r["NUMERO"].split("/"))
    titulo = r["TITULO"] + (" (texto oficial en portugués)" if r["IDIOMA_TEXTO"] == "PT" else "")
    agregar(f"{sigla} {num:02d}/{anio % 100:02d}", titulo, anio, r["TEXTO"], tipo,
            r["VIGENCIA"] if r["VIGENCIA"] in ("Vigente", "Derogada") else "")

for tipo, nombre in (("dec", "fragmentos.json"), ("res", "fragmentos_res.json"), ("dir", "fragmentos_dir.json")):
    salida = RAIZ / "docs" / "datos" / nombre
    salida.parent.mkdir(parents=True, exist_ok=True)
    salida.write_text(json.dumps(datos[tipo], ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"{nombre}: {len(datos[tipo]['normas'])} normas, {len(datos[tipo]['fragmentos'])} fragmentos, "
          f"{salida.stat().st_size / 1e6:.1f} MB")

# Datos de cobertura para la página (cuántas normas hay, cuántas entran al buscador, fecha de la última)
indice = list(csv.DictReader(open(RAIZ / "indices" / "indice_normativa_mercosur.csv", encoding="utf-8-sig")))
fecha = lambda f: f[-4:] + f[3:5] + f[:2]
ultima = max(indice, key=lambda r: (fecha(r["FECHA"]), int(r["NUMERO"].split("/")[0])))
meta = {"ultima_norma": f'{ultima["TIPO"]} {ultima["NUMERO"]}', "ultima_fecha": ultima["FECHA"],
        "publicadas": {"res": sum(r["TIPO"].startswith("Res") for r in indice), "dir": sum(r["TIPO"].startswith("Dir") for r in indice)},
        "con_texto": {"res": sum(r["TIPO"].startswith("Res") and bool(r["TEXTO"]) for r in indice),
                      "dir": sum(r["TIPO"].startswith("Dir") and bool(r["TEXTO"]) for r in indice)},
        "en_buscador": {t: len(datos[t]["normas"]) for t in datos}, "recortadas": RECORTADAS,
        "en_portugues": {"res": sum(r["TIPO"].startswith("Res") and r["IDIOMA_TEXTO"] == "PT" for r in indice),
                         "dir": sum(r["TIPO"].startswith("Dir") and r["IDIOMA_TEXTO"] == "PT" for r in indice)}}
(RAIZ / "docs" / "datos" / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
print(meta)
