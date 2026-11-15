"""Pasa las planillas (.xls/.xlsx) a texto: cada hoja, filas separadas por tabulaciones."""
import sys
from pathlib import Path
import pandas as pd

RAIZ = Path("/home/user/normas_trabajo")
for base, salida in (("originales", "texto_crudo"), ("anidados", "texto_anidado")):
    for p in (RAIZ / base).rglob("*"):
        if not p.is_file() or p.suffix.lower() not in (".xls", ".xlsx"):
            continue
        rel = p.relative_to(RAIZ / base)
        dest = (RAIZ / salida / (rel.parent / rel.stem)).with_suffix(".txt") if base == "anidados" \
            else RAIZ / salida / rel.parts[0] / (p.stem + p.suffix.lower() + ".txt")
        dest.parent.mkdir(parents=True, exist_ok=True)
        try:
            hojas = pd.read_excel(p, sheet_name=None, header=None, dtype=str)
        except Exception as e:  # noqa: BLE001
            print("NO SE PUDO LEER", p, e)
            continue
        partes = []
        for nombre, h in hojas.items():
            h = h.dropna(how="all").dropna(axis=1, how="all").fillna("")
            partes.append(f"[hoja: {nombre}]\n" + "\n".join("\t".join(f) for f in h.values.tolist()))
        dest.write_text("\n\n".join(partes) + "\n", encoding="utf-8")
print("listo")
