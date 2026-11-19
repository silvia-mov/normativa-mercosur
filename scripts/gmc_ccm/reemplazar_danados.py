"""Reemplaza archivos descargados que están dañados por la siguiente versión disponible en el sitio.

Uso:  py reemplazar_danados.py gmc 26/1993 66/1993 ...
Baja la siguiente versión en el orden de preferencia de descargar_normas.py (normalmente el
.pdf en español), borra el archivo dañado y anota el cambio en descargas_<tipo>.json.
"""
import json
import sys
import time
import urllib.parse
from pathlib import Path

from descargar_normas import BASE, CARPETA, PAUSA_SEGUNDOS, TIPOS, descargar, numero_y_anho, ordenar, titulo_corto


def main():
    clave, numeros = sys.argv[1], set(sys.argv[2:])
    t = TIPOS[clave]
    normas = {r["normativa_id"]: r for r in json.loads((CARPETA / "enlaces_todo.json").read_text(encoding="utf-8"))[clave]}
    ruta_desc = CARPETA / f"descargas_{clave}.json"
    desc = json.loads(ruta_desc.read_text(encoding="utf-8"))
    for d in desc:
        if d["numero"] not in numeros:
            continue
        r = normas[d["normativa_id"]]
        num, anho = numero_y_anho(r["numero"], r["anho"])
        danado = CARPETA / d["archivo"]
        candidatos = [c for c in ordenar(r["archivos"]) if c["archivo"] != d["origen"]]
        for c in candidatos:
            ext = Path(c["archivo"]).suffix.lower()
            destino = CARPETA / t["carpeta"] / anho / f"{t['prefijo']}_{num}-{anho}_{titulo_corto(r['titulo'])}{ext}"
            if destino == danado:
                continue
            try:
                time.sleep(PAUSA_SEGUNDOS)
                destino.write_bytes(descargar(BASE + urllib.parse.quote(c["archivo"])))
            except Exception as e:  # noqa: BLE001
                print(f"{d['numero']}: falló {c['archivo']}: {e}")
                continue
            danado.unlink()
            d.update(archivo=destino.relative_to(CARPETA).as_posix(), idioma=c["idioma"], origen=c["archivo"],
                     estado="descargada", nota=f"versión alternativa; el archivo {Path(d['origen']).name} del sitio está dañado")
            print(f"{d['numero']}: {destino.name} ({c['idioma']})")
            break
    ruta_desc.write_text(json.dumps(desc, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
