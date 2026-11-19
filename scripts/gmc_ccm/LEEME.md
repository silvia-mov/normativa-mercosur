# Resoluciones GMC y Directivas CCM: cómo se armaron

Programas para Windows (Word y OCR de Windows); se corren desde una carpeta de trabajo, en este orden:

1. `obtener_enlaces_todo.js`: en la consola del navegador, con normas.mercosur.int abierto (el sitio
   bloquea los pedidos de programas). Recorre los años y deja, por norma: número, título, fecha,
   vigencia y archivos publicados. El resultado se guarda como `enlaces_todo.json`.
2. `descargar_normas.py gmc|ccm`: baja una versión por norma (español .docx > .doc > .odt > .pdf), con
   1 s de pausa entre pedidos. `reemplazar_danados.py` reemplaza archivos dañados por la versión siguiente.
3. `a_texto_word.ps1` (Word), `a2_texto_word95.py` (los .doc que Word no abre; requiere `olefile`) y
   `b_ocr_pdf.ps1` (PDF escaneados): pasan todo a texto en `texto_crudo/`.
4. `c_ordenar_gmc_ccm.py`: arma los textos con cabecera (`resoluciones/`, `directivas/`) y controla que
   cada texto sea de su norma y en qué idioma está.
5. `armar_indice.py`: índice en Excel y CSV (`indices/`). `zip_por_decada.py`: zips de las releases.
6. `../e_datos_web.py`: datos del buscador de la página.
