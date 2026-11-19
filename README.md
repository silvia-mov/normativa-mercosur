# Normativa del MERCOSUR en texto

Las **decisiones del Consejo del Mercado Común (CMC), las resoluciones del Grupo Mercado Común (GMC) y
las directivas de la Comisión de Comercio (CCM) del MERCOSUR, de 1991 a 2026**, pasadas a texto plano y
ordenadas con nombres claros, para leerlas, buscarlas y analizarlas con cualquier programa.

| | |
|---|---|
| Decisiones | 1.130 (1991–2026), todas con su texto completo en español |
| Archivos de texto | 1.322 (textos, fe de erratas, anexos y planillas) |
| Notas y decretos de incorporación de Paraguay | 24 |
| Índice de decisiones | [`indice_decisiones.csv`](indice_decisiones.csv) y [`indice_decisiones.xlsx`](indice_decisiones.xlsx) |
| Resoluciones GMC | 2.183 publicadas (1991–2026); 2.181 con archivo y texto (2.165 en español) |
| Directivas CCM | 1.934 publicadas (1994–2026); 1.933 con archivo y texto (1.931 en español) |
| Índice de resoluciones y directivas | [`indices/indice_normativa_mercosur.xlsx`](indices/indice_normativa_mercosur.xlsx) y [`.csv`](indices/indice_normativa_mercosur.csv): fecha, vigencia, idioma, archivo, texto y números faltantes por año |
| Archivos originales (Word/PDF) | releases [`resoluciones_gmc`](https://github.com/silvia-mov/normativa-mercosur/releases/tag/resoluciones_gmc) y [`directivas_ccm`](https://github.com/silvia-mov/normativa-mercosur/releases/tag/directivas_ccm), un zip por década |

> **Aviso.** Esta es una recopilación independiente, **no oficial**. No es una publicación de la Secretaría
> del MERCOSUR ni de ningún gobierno. Los textos se convirtieron automáticamente desde los archivos que
> publica la Secretaría; pueden tener errores de conversión, sobre todo los escaneados (marcados como OCR).
> Para cualquier uso formal, consulte siempre el texto oficial en la
> [normativa del MERCOSUR](https://www.mercosur.int/documentos/normativa/).

## Página de consultas

[silvia-mov.github.io/normativa-mercosur](https://silvia-mov.github.io/normativa-mercosur/): buscador y asistente que responde solo con el texto de las normas (decisiones, resoluciones y directivas) y cita la fuente. Se puede elegir en qué tipo de norma buscar; las derogadas se marcan. También permite bajar cualquier norma en .txt eligiendo tipo, año y número, con enlace a su ficha en el sitio del MERCOSUR para el original (datos: `scripts/f_catalogo_web.py`, que usa `indices/fichas_decisiones.csv` para las fichas de las decisiones). Usa `docs/` (página), `worker/` (intermediario de Cloudflare) y `scripts/e_datos_web.py` (datos de la página). Buscador: [MiniSearch](https://github.com/lucaong/minisearch) (MIT).

## Cómo están organizados

```
decisiones/<año>/DEC_<número>-<año>_<idioma>_<tipo>[_<título corto>].txt
resoluciones/<año>/RES_<número>-<año>_<título corto>.txt
directivas/<año>/DIR_<número>-<año>_<título corto>.txt
incorporacion_paraguay/<año>/...      notas de Cancillería y decretos sobre incorporación
indice_decisiones.csv / .xlsx         una fila por archivo
indices/indice_normativa_mercosur.*   resoluciones y directivas: una fila por norma
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

## Resoluciones GMC y Directivas CCM

Se descargó **una versión por norma** de [normas.mercosur.int](https://normas.mercosur.int): en español
cuando existe (preferencia .docx > .doc > .odt > .pdf) y, si no, la otra disponible. Cada texto lleva una
cabecera como la de las decisiones, con número, título, fecha de aprobación, **vigencia** (según la ficha
del sitio: vigente, derogada o sin vigencia registrada), idioma del texto, archivo original, cómo se
convirtió y enlace a la ficha.

Conversión: Word (4.024 archivos); lectura directa del formato .doc (70 archivos de 1992–2001 que Word
actual no abre); OCR de Windows en español (20 PDF escaneados).

Controles (columna `NOTA` del índice):
- **Texto de otra norma**: el archivo que publica el sitio tiene el encabezado y el contenido de otra
  resolución o directiva. Res. GMC 65/92, 23/96, 98/96, 38/97, 36/98, 38/00 y 44/15; Dir. CCM 08/07. El
  texto se conserva, pero el buscador de la página no lo usa.
- **Encabezado con otro número** pero contenido que coincide con el título (error del documento):
  Res. GMC 99/96 y 44/26.
- **Idioma mal indicado en el sitio** (dice español y está en portugués, o al revés): Res. GMC 17/92,
  43/93, 56/94, 62/94, 22/96, 20/01, 31/14, 02/17 y 52/18; Dir. CCM 08/96 y 17/13. El idioma del texto
  se decide por el contenido.

Limitaciones:
- Sin archivo publicado en el sitio: Res. GMC 80/94 y 43/23, Dir. CCM 198/25.
- Números que faltan en el sitio: Res. GMC 01/01 y 28/01. Las directivas no tienen huecos.
- Archivos dañados en el sitio, reemplazados por el PDF: Res. GMC 26/93, 66/93, 32/94, 62/94 y 83/94
  (también el .doc vacío de la Res. GMC 80/99). Res. GMC 60/06 se publica sin extensión: es un PDF.
- Solo hay texto en portugués para 16 resoluciones y 2 directivas.
- Los programas de esta parte están en `scripts/gmc_ccm/` (Windows: Word y OCR de Windows).

## Fuente y uso

Fuente: Secretaría del MERCOSUR, normativa. Los textos de las normas son documentos públicos oficiales
del MERCOSUR. El código de la carpeta `scripts/` tiene licencia MIT. Si usa esta recopilación, cite la
fuente oficial y este repositorio.

Más proyectos: [silvia-mov.github.io](https://silvia-mov.github.io/)
