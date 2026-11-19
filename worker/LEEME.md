# Intermediario de Cloudflare (Worker)

Guarda la clave de Gemini en secreto y le pasa a la IA solo los fragmentos de normas que encontró la página.

1. Cloudflare → Workers & Pages → Create → Worker ("Start with Hello World") → nombre `normas-mercosur` → Deploy.
2. Edit code → borrar todo → pegar `worker.js` → Deploy.
3. Settings → Variables and Secrets → Add → tipo **Secret**, nombre `GEMINI_API_KEY`, valor = la clave de
   Google AI Studio → Deploy.
4. Copiar la dirección del Worker (termina en `.workers.dev`) y ponerla en `ASISTENTE_URL` de `docs/index.html`.

Opcional: variable `MODELO` (texto) para usar otro modelo de Gemini (por defecto `gemini-flash-latest`). Si la página dice "Gemini 403" o "400", revisar la clave; "404", el modelo. Sin tarjeta cargada, Google no cobra:
al llegar al tope diario gratuito, la página avisa "probá mañana".
