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
