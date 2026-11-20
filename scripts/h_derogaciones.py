"""Busca en el texto de las decisiones CMC las derogaciones de otras decisiones, para revisión manual.

Lee el texto principal en español de cada decisión (fe de erratas si existe) y busca frases como
"Derógase la Decisión CMC N° 6/99", "Deróganse las Decisiones CMC N° 3/91 y 5/92" o "Déjase sin efecto la Decisión ...".
Para cada caso guarda: la decisión que deroga, la derogada, si la frase menciona artículos (posible derogación parcial)
y la frase exacta. No publica nada: el resultado es un Excel para revisar a mano antes de marcar normas como derogadas.
Uso: python3 scripts/h_derogaciones.py <salida.xlsx>
"""
import csv
import re
import sys
from collections import defaultdict
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
BASE = "https://github.com/silvia-mov/normativa-mercosur/blob/main/"
VERBO = re.compile(r"(der[oó]g(?:a|ase|anse|ase|uese|uense|ar|ue|ó|an|ase)\b|d[eé]j(?:ase|anse|ar)\s+sin\s+efecto|queda(?:n)?\s+derogad[ao]s?|sin\s+efecto)", re.I)
REF = re.compile(r"Decisi[oó]n(?:es)?\s*(?:del\s+)?(?:CMC|Consejo del Mercado Común)?\s*(?:N\s*[°º.o]*\s*)?((?:\d{1,3}\s*/\s*\d{2,4}(?:\s*(?:,|y|e)\s*(?:N\s*[°º.o]*\s*)?)?)+)", re.I)
NUM = re.compile(r"(\d{1,3})\s*/\s*(\d{2,4})")

filas = list(csv.DictReader(open(RAIZ / "indice_decisiones.csv", encoding="utf-8-sig")))
por = defaultdict(list)
for r in filas:
    if r["TIPO"] in ("texto", "fe-de-erratas") and r["IDIOMA"] == "ES" and r["TEXTO"]:
        por[(int(r["AÑO"]), int(r["NUMERO"]))].append(r)
titulos = {k: v[0]["TITULO"] for k, v in por.items()}
casos = []
for (anio, num), rs in sorted(por.items()):
    r = sorted(rs, key=lambda x: (x["TIPO"] != "fe-de-erratas", -int(x["CARACTERES"] or 0)))[0]
    texto = (RAIZ / r["TEXTO"]).read_text(encoding="utf-8").split("-" * 70, 1)[-1]
    texto = re.sub(r"\s+", " ", texto)
    propia = f"{num:02d}/{anio % 100:02d}"
    for oracion in re.split(r"(?<=[.;:])\s+(?=[A-ZÁÉÍÓÚ])|Art(?:ículo|\.)\s*\d+\s*[-–.]", texto):
        if not VERBO.search(oracion):
            continue
        for ref in REF.finditer(oracion):
            for n, a in NUM.findall(ref.group(1)):
                a = int(a) % 100
                cod = f"{int(n):02d}/{a:02d}"
                if cod == propia:
                    continue
                anio_der = (1900 if a > 90 else 2000) + a
                casos.append({"Decisión que deroga": f"Dec. CMC {propia}", "Año": anio,
                              "Decisión derogada": f"Dec. CMC {cod}",
                              "Título de la derogada": titulos.get((anio_der, int(n)), "(no está en el repositorio)"),
                              "¿Menciona artículos? (posible derogación parcial)": "sí" if re.search(r"art[íi]culo|\bart\.", oracion, re.I) else "no",
                              "Frase": oracion.strip()[:600], "Texto de la que deroga": BASE + r["TEXTO"],
                              "Revisión: ¿derogación total? (sí/no/parcial)": "", "Comentario": ""})
d = pd.DataFrame(casos).drop_duplicates(["Decisión que deroga", "Decisión derogada", "Frase"])
d = d.sort_values(["Año", "Decisión que deroga"])
salida = sys.argv[1]
with pd.ExcelWriter(salida, engine="xlsxwriter") as w:
    d.to_excel(w, sheet_name="Derogaciones", index=False)
    ws = w.sheets["Derogaciones"]; wb = w.book
    fmt = wb.add_format({"text_wrap": True, "valign": "top", "font_name": "Calibri", "font_size": 10})
    for i, ancho in enumerate([14, 7, 14, 40, 16, 80, 30, 18, 25]):
        ws.set_column(i, i, ancho, fmt)
    ws.freeze_panes(1, 0); ws.autofilter(0, 0, len(d), len(d.columns) - 1)
    pd.DataFrame({"Notas": [
        "Casos encontrados automáticamente en el texto de las decisiones CMC: frases con 'deróga(n)se', 'déjase sin efecto', 'queda derogada', etc., que nombran otra decisión.",
        "Hay que revisar cada fila: una frase puede derogar solo algunos artículos, citar una derogación anterior o mencionar la decisión sin derogarla.",
        "Completar la columna 'Revisión' con sí (derogación total), parcial o no. Solo las marcadas 'sí' se publicarán como 'derogada' en la página.",
        "Fuente: textos de la normativa del MERCOSUR del repositorio normativa-mercosur. Elaboración propia."]}).to_excel(w, sheet_name="Notas", index=False)
    w.sheets["Notas"].set_column(0, 0, 140, fmt)
print(len(d), "casos;", d["Decisión derogada"].nunique(), "decisiones derogadas distintas")
print(d[d["Decisión derogada"].isin(["Dec. CMC 06/99"])][["Decisión que deroga", "Decisión derogada"]].to_string())
