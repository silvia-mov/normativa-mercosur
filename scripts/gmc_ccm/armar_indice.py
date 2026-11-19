"""Arma indices/indice_normativa_mercosur.xlsx con las Resoluciones GMC y Directivas CCM.

Lee enlaces_todo.json (datos del sitio) y descargas_gmc.json / descargas_ccm.json
(resultado de descargar_normas.py).

Hoja "Índice": una fila por norma (tipo, año, número, título, fecha, idioma,
archivo, vigencia) y, resaltada en amarillo, una fila por cada número que falta
en el sitio dentro de su año (entre 1 y el número más alto publicado ese año).
Hoja "Faltantes": resumen de números faltantes por tipo y año.

Vigencia:
  Derogada                -> la ficha dice que fue derogada.
  Vigente                 -> la ficha registra entrada en vigencia y no derogación.
  Sin vigencia registrada -> la ficha no registra entrada en vigencia
                             (p. ej. normas que aún esperan incorporación).

Uso:  py armar_indice.py      (requiere openpyxl)
"""

import csv
import json
import re
from collections import defaultdict
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
from openpyxl.utils import get_column_letter

CARPETA = Path(__file__).resolve().parent
SALIDA = CARPETA / "indices" / "indice_normativa_mercosur.xlsx"
SALIDA_CSV = SALIDA.with_suffix(".csv")
REPO_URL = "https://github.com/silvia-mov/normativa-mercosur/blob/main/"
TIPOS = [("gmc", "Resolución GMC"), ("ccm", "Directiva CCM")]
AMARILLO = PatternFill("solid", fgColor="FFF2A8")
ROJO = PatternFill("solid", fgColor="F8CBAD")


def vigencia(r):
    if r.get("error_detalle"):
        return "Sin dato (error al leer la ficha)"
    if r.get("derogada_por") or re.search(r"derogad", r.get("vigencia", ""), re.I):
        return "Derogada"
    if re.search(r"vigen", r.get("vigencia", ""), re.I):
        return "Vigente"
    return "Sin vigencia registrada"


def num_int(numero):
    m = re.match(r"\s*(\d+)", numero)
    return int(m.group(1)) if m else None


def main():
    datos = json.loads((CARPETA / "enlaces_todo.json").read_text(encoding="utf-8"))
    wb = Workbook()
    ws = wb.active
    ws.title = "Índice"
    cols = ["Tipo", "Año", "Número", "Título", "Fecha de aprobación", "Idioma",
            "Archivo", "Vigencia", "Derogada por", "Detalle de vigencia (SIM)",
            "Descarga", "normativa_id", "Texto (repositorio)", "Idioma del texto", "Control del texto"]
    ws.append(cols)
    filas_csv = []
    falt = wb.create_sheet("Faltantes")
    falt.append(["Tipo", "Año", "Publicadas", "Número más alto", "Cantidad faltante", "Números faltantes"])

    for clave, nombre in TIPOS:
        normas = datos.get(clave, [])
        desc_path = CARPETA / f"descargas_{clave}.json"
        desc = {d["normativa_id"]: d for d in json.loads(desc_path.read_text(encoding="utf-8"))} if desc_path.exists() else {}
        txt_path = CARPETA / f"textos_{clave}.json"
        textos = {t["normativa_id"]: t for t in json.loads(txt_path.read_text(encoding="utf-8"))} if txt_path.exists() else {}
        por_anho = defaultdict(list)
        for r in normas:
            por_anho[int(r["anho"])].append(r)
        for anho in sorted(por_anho):
            lista = por_anho[anho]
            nums = {num_int(r["numero"]) for r in lista} - {None}
            faltan = sorted(set(range(1, max(nums) + 1)) - nums) if nums else []
            if faltan:
                falt.append([nombre, anho, len(lista), max(nums), len(faltan), ", ".join(map(str, faltan))])
            filas = [(num_int(r["numero"]) or 0, r) for r in lista] + [(n, None) for n in faltan]
            for n, r in sorted(filas, key=lambda x: (x[0], x[1] is None)):
                if r is None:
                    ws.append([nombre, anho, f"{n}/{anho}", "FALTA: número no publicado en normas.mercosur.int"]
                              + [""] * (len(cols) - 4))
                    for c in ws[ws.max_row]:
                        c.fill = AMARILLO
                    continue
                d = desc.get(r["normativa_id"], {})
                estado = d.get("estado", "no procesada")
                if estado == "error":
                    estado = f"ERROR: {d.get('motivo', '')}"
                elif estado in ("descargada", "ya existía"):
                    estado = "OK" + (" (" + d["nota"] + ")" if d.get("nota") else "")
                ws.append([nombre, anho, r["numero"], r["titulo"], r.get("fecha", ""), d.get("idioma", ""),
                           d.get("archivo", ""), vigencia(r), r.get("derogada_por", ""),
                           r.get("vigencia", ""), estado, int(r["normativa_id"])])
                t = textos.get(r["normativa_id"], {})
                for col, valor in (("Texto (repositorio)", t.get("texto", "")), ("Idioma del texto", t.get("idioma_texto", "")),
                                   ("Control del texto", t.get("nota", ""))):
                    c = ws.cell(ws.max_row, cols.index(col) + 1, valor or None)
                    if col == "Texto (repositorio)" and valor:
                        c.hyperlink = REPO_URL + valor
                    if col == "Control del texto" and valor:
                        c.fill = AMARILLO
                filas_csv.append({"TIPO": nombre, "AÑO": anho, "NUMERO": r["numero"], "TITULO": r["titulo"],
                                  "FECHA": r.get("fecha", ""), "IDIOMA": d.get("idioma", ""), "ARCHIVO": d.get("archivo", ""),
                                  "VIGENCIA": vigencia(r), "DEROGADA_POR": r.get("derogada_por", ""),
                                  "TEXTO": t.get("texto", ""), "IDIOMA_TEXTO": t.get("idioma_texto", ""),
                                  "CONVERSION": t.get("conversion", ""), "CARACTERES": t.get("caracteres", ""),
                                  "NOTA": t.get("nota", ""), "ID_SITIO": r["normativa_id"]})
                if estado.startswith("ERROR") or estado == "no procesada":
                    ws.cell(ws.max_row, cols.index("Descarga") + 1).fill = ROJO

    for hoja, anchos in ((ws, [16, 6, 10, 70, 12, 7, 60, 22, 22, 50, 14, 10, 60, 9, 40]), (falt, [16, 6, 11, 15, 16, 80])):
        for i, a in enumerate(anchos, 1):
            hoja.column_dimensions[get_column_letter(i)].width = a
        for c in hoja[1]:
            c.font = Font(bold=True)
        hoja.freeze_panes = "A2"
        hoja.auto_filter.ref = hoja.dimensions
    SALIDA.parent.mkdir(exist_ok=True)
    wb.save(SALIDA)
    with open(SALIDA_CSV, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(filas_csv[0]))
        w.writeheader()
        w.writerows(filas_csv)
    print(f"Índice guardado en {SALIDA}")


if __name__ == "__main__":
    main()
