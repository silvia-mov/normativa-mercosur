"""Datos de la sección "MERCOSUR en Paraguay" de la página: notas y decretos de incorporación de Paraguay.

Lee incorporacion_paraguay/<año>/*.txt (notas de la Cancillería a la Secretaría del MERCOSUR y decretos del Poder
Ejecutivo) y toma del NOMBRE del archivo original el tipo (nota o decreto), su número y año, y la decisión que nombra, si la nombra.
No se leen del texto: en los escaneados (OCR) las fechas y números salen con errores, y los textos citan otras normas.
Salida: docs/datos/paraguay.json
Uso: python3 scripts/g_paraguay_web.py
"""
import json
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
BASE = "https://github.com/silvia-mov/normativa-mercosur/blob/main/"
DEC = re.compile(r"(?:Decisi[oó]n(?:es)?|DEC\.?)\s*(?:CMC\s*)?(?:N\s*[°º.o?]*\s*)?(\d{1,3})\s*[/-]\s*(\d{2}(?:\d{2})?)\b", re.I)
FECHA = re.compile(r"\b(\d{1,2})\s*/\s*(\d{1,2})\s*/\s*(20\d{2})\b")
MESES = "enero febrero marzo abril mayo junio julio agosto septiembre setiembre octubre noviembre diciembre".split()
FECHA_TXT = re.compile(r"\b(\d{1,2})\s+de\s+(" + "|".join(MESES) + r")\s+de\s+(20\d{2})", re.I)

NUM_DEC = re.compile(r"Dec(?:isi[oó]n)?[\s._-]*(?:N[^\d]{0,3})?0*(\d{1,3})[\s._-]+(\d{2,4})\b", re.I)
NUM_DOC = re.compile(r"(?:DECRETO|Decreto)[^\d]{0,6}(\d{3,5})|(?:Nota|NOTA|DIE)[^\d]{0,12}(\d{1,3})", re.I)

filas = []
for f in sorted((RAIZ / "incorporacion_paraguay").rglob("*.txt")):
    t = f.read_text(encoding="utf-8")
    cab = t.partition("-" * 70)[0]
    original = re.search(r"Archivo original:\s*(.+)", cab).group(1).strip()
    tipo = "Decreto" if re.search(r"decreto", original, re.I) else "Nota de la Cancillería"
    m = NUM_DOC.search(original)
    numero = (m.group(1) or m.group(2)) if m else ""
    d = NUM_DEC.search(original)
    dec = f"{int(d.group(1)):02d}/{int(d.group(2)) % 100:02d}" if d else ""
    anio_doc = re.search(r"(20\d{2})", original)
    filas.append({"tipo": tipo, "numero": numero, "anio_documento": anio_doc.group(1) if anio_doc else "",
                  "decision_en_el_nombre": dec, "anio_decisiones": f.parent.name,
                  "archivo": original, "url": BASE + str(f.relative_to(RAIZ)), "ocr": "OCR" in cab})
filas.sort(key=lambda r: (r["anio_decisiones"], r["anio_documento"]), reverse=True)
(RAIZ / "docs" / "datos" / "paraguay.json").write_text(json.dumps(filas, ensure_ascii=False, indent=1), encoding="utf-8")
for r in filas:
    print(r["anio_decisiones"], r["tipo"][:7], r["numero"], r["anio_documento"], r["decision_en_el_nombre"], "|", r["archivo"][:55])
