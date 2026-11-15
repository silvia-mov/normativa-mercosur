# Normativa del MERCOSUR en texto

Las **decisiones del Consejo del Mercado Común (CMC) del MERCOSUR, de 1991 a 2026**, pasadas a texto
plano y ordenadas con nombres claros, para leerlas, buscarlas y analizarlas con cualquier programa.

| | |
|---|---|
| Decisiones | 1.130 (1991–2026), todas con su texto completo en español |
| Archivos de texto | 1.322 (textos, fe de erratas, anexos y planillas) |
| Notas y decretos de incorporación de Paraguay | 24 |
| Índice | [`indice_decisiones.csv`](indice_decisiones.csv) y [`indice_decisiones.xlsx`](indice_decisiones.xlsx) |

> **Aviso.** Esta es una recopilación independiente, **no oficial**. No es una publicación de la Secretaría
> del MERCOSUR ni de ningún gobierno. Los textos se convirtieron automáticamente desde los archivos que
> publica la Secretaría; pueden tener errores de conversión, sobre todo los escaneados (marcados como OCR).
> Para cualquier uso formal, consulte siempre el texto oficial en la
> [normativa del MERCOSUR](https://www.mercosur.int/documentos/normativa/).

## Página de consultas

[silvia-mov.github.io/normativa-mercosur](https://silvia-mov.github.io/normativa-mercosur/): buscador y asistente que responde solo con el texto de las decisiones y cita la fuente. Usa `docs/` (página), `worker/` (intermediario de Cloudflare) y `scripts/e_datos_web.py` (datos de la página). Buscador: [MiniSearch](https://github.com/lucaong/minisearch) (MIT).

## Cómo están organizados

```
decisiones/<año>/DEC_<número>-<año>_<idioma>_<tipo>[_<título corto>].txt
incorporacion_paraguay/<año>/...      notas de Cancillería y decretos sobre incorporación
indice_decisiones.csv / .xlsx         una fila por archivo
scripts/                              programas usados para convertir y ordenar
```

**Tipo de documento**

| Tipo | Qué es |
|---|---|
| `texto` | Texto de la decisión |
| `fe-de-erratas` | Texto corregido por la Secretaría (versión vigente cuando existe) |
| `anexo-N` | Anexos (acuerdos, listas, proyectos) |
| `planilla-N` | Anexos que eran planillas de Excel, pasados a texto (columnas separadas por tabulaciones) |

Ejemplo: `decisiones/2007/DEC_001-2007_ES_texto_grupo-de-trabajo-ad-hoc-para-la-incorporacion-de-la.txt`

Cada archivo empieza con una cabecera con el número, el título, el tipo, el nombre del archivo original
y cómo se convirtió:

```
Decisión CMC N° 01/07
Título: GRUPO DE TRABAJO AD HOC PARA LA INCORPORACIÓN DE LA REPÚBLICA DE BOLIVIA COMO ESTADO PARTE DEL MERCOSUR
Tipo de documento: texto
Archivo original: 3146_DEC_001-2007_ES_GAH-IncorpBolivia.doc
Conversión a texto: Word
Fuente: Secretaría del MERCOSUR, normativa (https://www.mercosur.int/documentos/normativa/).
----------------------------------------------------------------------
MERCOSUR/CMC/DEC. Nº 01/07
...
```

## Columnas del índice

`AÑO`, `NUMERO`, `CODIGO` (DEC_001-2007), `TITULO`, `TIPO`, `IDIOMA` (ES, PT, EN, HE), `ARCHIVO_NUEVO`,
`TEXTO` (ruta del .txt), `ARCHIVO_ORIGINAL` (nombre con el que lo publica la Secretaría), `ID_SITIO`
(número interno del sitio del MERCOSUR), `CONVERSION` (Word, texto del PDF, OCR o planilla),
`CARACTERES` y `NOTA`. Las filas `duplicado` y `comprimido` no tienen archivo propio: indican copias
idénticas y archivos .zip/.rar cuyo contenido figura como anexos.

## Cómo se hizo

1. Los archivos se descargaron de la normativa del MERCOSUR, año por año.
2. Word (.doc, .docx, .rtf) a texto con LibreOffice; PDF con `pdftotext`; PDF escaneados con OCR
   (Tesseract, español y portugués); planillas con pandas. Los .zip y .rar se abrieron y su contenido
   se trató como anexo.
3. Cada archivo se identificó por el encabezado del texto (`MERCOSUR/CMC/DEC. Nº x/aa`) o, si no lo
   tenía, por su nombre o por el número interno del sitio compartido con los demás archivos de la misma
   decisión. Así se identificaron 22 archivos que el sitio publica con nombres genéricos (`ATT….docx`).
4. Se controló que la numeración de cada año no tenga huecos.

Los anexos de proyectos FOCEM de más de 100 páginas escaneadas (planos y presupuestos de obra) solo se
leyeron en sus primeras 5 páginas; su texto lo indica al final.

## Limitaciones conocidas

- **Decisión 06/99** (coordinación de políticas macroeconómicas): el sitio la marca como derogada por la
  Decisión CMC 30/00, y su versión vigente figura "en revisión"; el texto es el de la versión del 15/06/1999.
- **Decisión 10/02**: en el sitio, el enlace de la versión original descarga por error el archivo de la
  11/02; aquí se usa la fe de erratas, que es la versión vigente.
- 19 decisiones estaban solo en portugués en la primera descarga; su versión en español se bajó después
  (archivos originales `ES_secretaria_...`). Se conservan las dos versiones.
- El sitio etiqueta mal el idioma de algunos archivos; aquí el idioma se decide por el contenido.
- Los textos convertidos por OCR pueden tener letras mal leídas.

## Próximamente

Resoluciones del Grupo Mercado Común (GMC) y Directivas de la Comisión de Comercio del MERCOSUR (CCM).

## Fuente y uso

Fuente: Secretaría del MERCOSUR, normativa. Los textos de las normas son documentos públicos oficiales
del MERCOSUR. El código de la carpeta `scripts/` tiene licencia MIT. Si usa esta recopilación, cite la
fuente oficial y este repositorio.

Más proyectos: [silvia-mov.github.io](https://silvia-mov.github.io/)
