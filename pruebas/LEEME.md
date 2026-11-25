# Pruebas del buscador y del asistente

- `banco_preguntas.csv`: 40 preguntas con las normas que deberían aparecer como fuente. Tipos: `tema`, `numero`
  (la pregunta nombra la norma), `derogada`, `fuera` (no está en el corpus: el asistente debe decir que no encuentra)
  y `anexo` (la respuesta está en anexos, que hoy no se leen: es esperable que falle).
- `probar_buscador.js`: prueba la búsqueda de la página, sin la IA, con los mismos datos y la misma configuración.
  Uso, desde la raíz: `node pruebas/probar_buscador.js`. Escribe `resultado_buscador.csv`.
- Resultado al 20/11/2026: la norma esperada aparece entre las 6 fuentes en 35 de 37 preguntas (antes del ajuste de
  orden por título y año: 32 de 37). Fallan: el FOCEM (salen los presupuestos recientes y no la norma de creación) y los
  proyectos FOCEM para Paraguay (están en anexos).
- La parte de la IA (Gemini) se prueba a mano en la página con las mismas preguntas: revisar que cite la norma
  esperada, que avise las derogadas y que en las preguntas `fuera` diga que no encuentra. Repetirlo cuando cambie el
  modelo o las instrucciones del asistente.
- Prueba de búsqueda por significado (25/11/2026), con los mismos 37 casos: buscador actual por palabras 34 aciertos;
  multilingual-e5-small 32 (mezclado con el actual, 33); granite-embedding-97m-multilingual-r2 22 (mezclado, 29).
  Ninguno mejora al actual: se deja la búsqueda por palabras. El único caso que el modelo resuelve y el actual no es el
  del FOCEM. Además, en la página cada visitante tendría que bajar unos 100 MB de modelo y 44 MB de vectores.
