#!/bin/bash
# Convierte .doc/.docx/.rtf de originales/<año>/ a texto UTF-8 en texto_crudo/<año>/
cd /home/user/normas_trabajo
for d in originales/*/; do
  a=$(basename "$d"); mkdir -p "texto_crudo/$a"
  ls "$d" | grep -iE '\.(doc|docx|rtf)$' >/dev/null || continue
  timeout 1800 soffice --headless -env:UserInstallation=file:///tmp/claude-0/lo_perfil4 \
    --convert-to 'txt:Text (encoded):UTF8' --outdir "texto_crudo/$a" "$d"*.[dDrR][oOtT]* >/dev/null 2>&1
  echo "$a $(ls texto_crudo/$a | wc -l)"
done
echo FIN
