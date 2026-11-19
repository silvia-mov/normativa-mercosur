"""Saca el texto de los .doc (Word 6/95 y 97-2003) que Word no logra abrir.

En Word 6/95 el texto del documento está guardado tal cual (Windows-1252) en el flujo
"WordDocument", entre las posiciones fcMin y fcMac que indica su cabecera (FIB).
Lee la lista de archivos que fallaron en texto_crudo/conversion_word.log y escribe
texto_crudo/<carpeta>/<año>/<nombre>.txt, igual que a_texto_word.ps1.

Uso:  py a2_texto_word95.py          (requiere olefile)
"""
import re
import struct
import sys
from pathlib import Path

import olefile

RAIZ = Path(__file__).resolve().parent


def texto_word97(ole, wd):
    """Word 97-2003: el texto está repartido en piezas que lista la tabla de piezas (Clx)."""
    flags = struct.unpack_from("<H", wd, 0x0A)[0]
    tabla = ole.openstream("1Table" if flags & 0x0200 else "0Table").read()
    fc_clx, lcb_clx = struct.unpack_from("<II", wd, 0x01A2)
    clx = tabla[fc_clx:fc_clx + lcb_clx]
    i = 0
    while clx[i] == 0x01:                       # Prc: formato agrupado, se saltea
        i += 3 + struct.unpack_from("<H", clx, i + 1)[0]
    if clx[i] != 0x02:
        raise ValueError("tabla de piezas no encontrada")
    lcb = struct.unpack_from("<I", clx, i + 1)[0]
    plc = clx[i + 5:i + 5 + lcb]
    n = (lcb - 4) // 12
    cps = struct.unpack_from(f"<{n + 1}I", plc, 0)
    partes = []
    for k in range(n):
        fc = struct.unpack_from("<I", plc, 4 * (n + 1) + 8 * k + 2)[0]
        largo = cps[k + 1] - cps[k]
        if fc & 0x40000000:                     # comprimido: 1 byte por carácter
            ini = (fc & 0x3FFFFFFF) // 2
            partes.append(wd[ini:ini + largo].decode("cp1252", errors="replace"))
        else:
            partes.append(wd[fc:fc + 2 * largo].decode("utf-16-le", errors="replace"))
    return "".join(partes)


def texto_word95(ruta):
    with olefile.OleFileIO(str(ruta)) as ole:
        wd = ole.openstream("WordDocument").read()
        ident, nfib = struct.unpack_from("<HH", wd, 0)
        if ident == 0xA5EC:
            crudo = texto_word97(ole, wd)
        elif ident == 0xA5DC:
            fc_min, fc_mac = struct.unpack_from("<II", wd, 0x18)
            crudo = wd[fc_min:fc_mac].decode("cp1252", errors="replace")
        else:
            raise ValueError(f"no es un documento de Word (0x{ident:04X})")
    # Campos: \x13 instrucción \x14 resultado \x15 -> queda solo el resultado
    crudo = re.sub(r"\x13[^\x13\x14\x15]*\x14", "", crudo)
    crudo = re.sub(r"\x13[^\x13\x14\x15]*\x15", "", crudo)
    crudo = crudo.replace("\x15", "").replace("\r", "\n").replace("\x0b", "\n").replace("\x0c", "\n")
    crudo = crudo.replace("\x07", "\t").replace("\x1e", "-").replace("\x1f", "").replace("\xa0", " ")
    crudo = re.sub(r"[\x00-\x08\x0e-\x1d]", "", crudo)
    return crudo


def main():
    log = (RAIZ / "texto_crudo" / "conversion_word.log").read_text(encoding="utf-8-sig")
    fallos = sorted(set(re.findall(r"^([A-Z]:\\[^\t]+)\t", log, re.M)))
    ok, malos = 0, []
    for f in fallos:
        p = Path(f)
        rel = p.relative_to(RAIZ)
        dest = RAIZ / "texto_crudo" / rel.parts[0] / rel.parts[1] / (p.stem + ".txt")
        if dest.exists() and dest.stat().st_size > 0:
            continue
        try:
            t = texto_word95(p)
            if len(t.strip()) < 100:
                raise ValueError("texto casi vacío")
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(t, encoding="utf-8")
            ok += 1
        except Exception as e:  # noqa: BLE001
            malos.append(f"{rel.as_posix()}: {e}")
    print(f"Word 6/95: {ok} convertidos, {len(malos)} sin convertir")
    for m in malos:
        print("  -", m)


if __name__ == "__main__":
    sys.exit(main())
