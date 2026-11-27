"""Gráfico de Datawrapper: cuántas resoluciones GMC y directivas CCM se aprobaron cada año y cuántas siguen vigentes hoy.

Uso: python scripts/grafico_vigencia_datawrapper.py
Lee indices/indice_normativa_mercosur.csv (vigencia según la Secretaría del MERCOSUR), escribe
docs/datos/vigencia_por_anio.csv/.xlsx y crea o actualiza el gráfico (número en docs/datos/datawrapper_ids.json).
Las decisiones CMC no entran: el índice no tiene su vigencia.
"""
import json
import os
from pathlib import Path

import pandas as pd
import requests

RAIZ = Path(__file__).resolve().parent.parent
IDS = RAIZ / "docs" / "datos" / "datawrapper_ids.json"
API = "https://api.datawrapper.de/v3"
H = {"Authorization": "Bearer " + os.environ.get("DATAWRAPPER_TOKEN", "proxy-injected")}


def main():
    d = pd.read_csv(RAIZ / "indices" / "indice_normativa_mercosur.csv", encoding="utf-8-sig", dtype=str)
    d = d[d["VIGENCIA"].isin(["Vigente", "Derogada"])]
    t = d.groupby([d["AÑO"].astype(int), "VIGENCIA"]).size().unstack(fill_value=0)[["Vigente", "Derogada"]]
    t["TOTAL"] = t.sum(axis=1)
    t["PCT_VIGENTE"] = (100 * t["Vigente"] / t["TOTAL"]).round(1)
    t = t.reset_index().rename(columns={"AÑO": "AÑO", "Vigente": "VIGENTES", "Derogada": "DEROGADAS"})
    t.to_csv(RAIZ / "docs" / "datos" / "vigencia_por_anio.csv", index=False, encoding="utf-8-sig")
    t.to_excel(RAIZ / "docs" / "datos" / "vigencia_por_anio.xlsx", index=False)
    w = pd.DataFrame({"Año": t["AÑO"].astype(str), "Siguen vigentes": t["VIGENTES"], "Derogadas": t["DEROGADAS"]})
    a92 = t.set_index("AÑO").loc[1992]
    ultimo = t["AÑO"].max()
    ids = json.loads(IDS.read_text()) if IDS.exists() else {}
    titulo = (f"El MERCOSUR casi no deroga: {a92['PCT_VIGENTE']:.0f}% de las normas de 1992 sigue vigente, "
              f"y cada año se suman más ({t.set_index('AÑO').loc[ultimo, 'TOTAL']} en {ultimo})")
    if "vigencia" not in ids:
        r = requests.post(f"{API}/charts", headers=H, json={"title": titulo, "type": "stacked-column-chart"}, timeout=60)
        r.raise_for_status()
        ids["vigencia"] = r.json()["id"]
        IDS.write_text(json.dumps(ids, indent=1))
    cid = ids["vigencia"]
    requests.put(f"{API}/charts/{cid}/data", headers={**H, "Content-Type": "text/csv"},
                 data=w.to_csv(index=False).encode("utf-8"), timeout=60).raise_for_status()
    meta = {"describe": {"byline": "", "number-format": "0,0",
                         "intro": "Resoluciones del Grupo Mercado Común y directivas de la Comisión de Comercio aprobadas cada año, "
                                  "según sigan vigentes o hayan sido derogadas hoy. Cada columna es una «generación» de normas.",
                         "source-name": "Secretaría del MERCOSUR (vigencia de cada norma); cálculo propio",
                         "source-url": "https://silvia-mov.github.io/normativa-mercosur/"},
            "annotate": {"notes": f"{ultimo}: hasta noviembre. No incluye las decisiones del Consejo del Mercado Común (el "
                                  "registro no informa su vigencia) ni 12 normas sin vigencia registrada. Desde 2017 crecen sobre "
                                  "todo las directivas de la Comisión de Comercio."},
            "visualize": {"custom-colors": {"Siguen vigentes": "#5e8f88", "Derogadas": "#c9b3ca"}, "show-color-key": True,
                          "y-grid-format": "0,0", "tooltip-number-format": "0,0", "dark-mode-invert": True, "show-tooltips": True},
            "data": {"transpose": True},
            "publish": {"blocks": {"logo": {"enabled": False}, "embed": False, "download-pdf": False, "download-svg": False,
                                   "get-the-data": True, "download-image": True}, "autoDarkMode": True}}
    requests.patch(f"{API}/charts/{cid}", headers=H, timeout=60,
                   json={"title": titulo, "type": "stacked-column-chart", "language": "es-AR", "metadata": meta}).raise_for_status()
    requests.post(f"{API}/charts/{cid}/publish", headers=H, timeout=120).raise_for_status()
    print("vigencia", f"https://datawrapper.dwcdn.net/{cid}/")
    print(t.tail(4).to_string(), "\n", a92.to_dict())


if __name__ == "__main__":
    main()
