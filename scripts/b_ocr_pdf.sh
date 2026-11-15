#!/bin/bash
# OCR de los PDF escaneados (lista en pdf_escaneados.txt: paginas|ruta). Los anexos de proyectos FOCEM
# de más de 100 páginas (planos y presupuestos de obra) se leen solo en sus primeras 5 páginas.
cd /home/user/normas_trabajo
mkdir -p ocr_tmp
while IFS='|' read -r pags ruta; do
  a=$(echo "$ruta" | cut -d/ -f2); base=$(basename "$ruta"); base="${base%.*}"
  salida="texto_crudo/$a/$base.pdf.txt"; mkdir -p "texto_crudo/$a"
  [ -s "$salida" ] && continue
  ultima=$pags
  if [ "$pags" -gt 100 ] && echo "$ruta" | grep -qiE 'focem|proyecto|projeto'; then ultima=5; fi
  tmp="ocr_tmp/$(echo "$ruta" | md5sum | cut -c1-10)"; mkdir -p "$tmp"
  pdftoppm -r 200 -gray -l "$ultima" -png "originales/${ruta#./}" "$tmp/p"
  ls "$tmp"/p*.png | OMP_THREAD_LIMIT=1 xargs -P 4 -I{} sh -c 'tesseract "{}" "${1%.png}" -l spa+por --psm 1 >/dev/null 2>&1' _ {}
  : > "$salida.parcial"
  for t in $(ls "$tmp"/p*.txt | sort -V); do n=$(basename "$t" .txt); echo "[página ${n##*-}]" >> "$salida.parcial"; cat "$t" >> "$salida.parcial"; done
  [ "$ultima" -lt "$pags" ] && echo "[OCR parcial: se leyeron $ultima de $pags páginas]" >> "$salida.parcial"
  mv "$salida.parcial" "$salida"; rm -r "$tmp"
  echo "$(date +%T) $ruta $ultima/$pags"
done < pdf_escaneados.txt
echo FIN
