"""Arma un zip por década de una carpeta de normas (resoluciones_gmc o directivas_ccm).

Uso:  py zip_por_decada.py resoluciones_gmc
      -> releases/resoluciones_gmc_1990s.zip, ..._2000s.zip, ...
Dentro del zip se conserva la ruta <carpeta>/<año>/<archivo>.
"""

import sys
import zipfile
from collections import defaultdict
from pathlib import Path

CARPETA = Path(__file__).resolve().parent


def main():
    nombre = sys.argv[1]
    origen = CARPETA / nombre
    salida = CARPETA / "releases"
    salida.mkdir(exist_ok=True)
    decadas = defaultdict(list)
    for anho in sorted(p for p in origen.iterdir() if p.is_dir() and p.name.isdigit()):
        decadas[int(anho.name) // 10 * 10].extend(sorted(anho.iterdir()))
    for decada, archivos in sorted(decadas.items()):
        destino = salida / f"{nombre}_{decada}s.zip"
        with zipfile.ZipFile(destino, "w", zipfile.ZIP_DEFLATED) as z:
            for f in archivos:
                z.write(f, f.relative_to(CARPETA).as_posix())
        print(f"{destino.name}: {len(archivos)} archivos, {destino.stat().st_size / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
