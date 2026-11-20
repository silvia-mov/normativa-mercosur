// Prueba la búsqueda de la página (sin la IA): para cada pregunta del banco, ¿aparece alguna de las normas
// esperadas entre las 6 fuentes que se mandarían al asistente? Usa los mismos datos y la misma configuración.
// Uso: node pruebas/probar_buscador.js   (desde la raíz del repositorio)
const fs = require("fs"), path = require("path");
const RAIZ = path.resolve(__dirname, "..");
const _ms = require(path.join(RAIZ, "docs", "minisearch.min.js"));
const MiniSearch = _ms.default || _ms.MiniSearch || _ms || global.MiniSearch;
const sinTildes = (t) => t.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();
const html = fs.readFileSync(path.join(RAIZ, "docs", "index.html"), "utf8");
const VACIAS = new Set(html.match(/const VACIAS = new Set\("([^"]+)"/)[1].split(" ").map(sinTildes));
const TIT = new Map();   // id de fragmento -> [palabras del título, año]
const terminos = (t) => sinTildes(t).split(/[^a-z0-9ñ]+/).filter((x) => x.length >= 2 && !VACIAS.has(x));
// Premia los fragmentos cuya norma tiene en el TÍTULO todas las palabras de la pregunta, y un poco a las más nuevas
const premio = (id, _t, pregunta) => { const [tt, anio] = TIT.get(id); const q = terminos(pregunta);
  const en = q.filter((w) => tt.some((x) => x.startsWith(w))).length;
  return (q.length && en === q.length ? 3 : en >= 2 ? 1.5 : 1) * (1 + (anio - 1991) / (+(process.env.RECIENTE || 30))); };
const buscador = new MiniSearch({ fields: ["texto", "titulo"], storeFields: [],
  processTerm: (t) => { const s = sinTildes(t); return s.length < 2 || VACIAS.has(s) ? null : s; },
  searchOptions: { boost: { titulo: +(process.env.BOOST || 3) }, fuzzy: 0.15, prefix: true, combineWith: "OR" } });
const normas = [], frags = [];
for (const a of ["fragmentos.json", "fragmentos_res.json", "fragmentos_dir.json"]) {
  const d = JSON.parse(fs.readFileSync(path.join(RAIZ, "docs", "datos", a), "utf8")), base = normas.length, p0 = frags.length;
  normas.push(...d.normas);
  buscador.addAll(d.fragmentos.map(([n, t], i) => { frags.push(base + n); TIT.set(p0 + i, [terminos(d.normas[n][1]), d.normas[n][2]]); return { id: p0 + i, texto: t, titulo: d.normas[n][1] + " " + d.normas[n][0] }; }));
}
function fuentes(pregunta) {           // misma lógica que la página: norma nombrada primero, máx. 2 fragmentos por norma, 6 en total
  const res = [], por = {};
  const m = pregunta.match(/\b(dec(?:isi[oó]n)?|res(?:oluci[oó]n)?|dir(?:ectiva)?)\.?\s*(?:cmc|gmc|ccm)?\s*(?:n\s*[°º.o]*\s*)?(\d{1,3})\s*\/\s*(\d{2}|\d{4})\b/i);
  if (m) {
    const t = m[1].toLowerCase().startsWith("dec") ? "Dec. CMC" : m[1].toLowerCase().startsWith("res") ? "Res. GMC" : "Dir. CCM";
    const n = normas.findIndex((x) => x[0] === `${t} ${String(+m[2]).padStart(2, "0")}/${String(+m[3] % 100).padStart(2, "0")}`);
    if (n >= 0) { res.push(n); por[n] = 3; }
  }
  for (const r of buscador.search(pregunta, process.env.SIN_PREMIO ? {} : { boostDocument: (id, t) => premio(id, t, pregunta) })) {
    const n = frags[r.id];
    if ((por[n] = (por[n] || 0) + 1) <= 2) res.push(n);
    if (res.length >= 6) break;
  }
  return [...new Set(res.map((n) => normas[n][0]))];
}
const filas = fs.readFileSync(path.join(__dirname, "banco_preguntas.csv"), "utf8").trim().split("\n").slice(1)
  .map((l) => l.match(/^(\d+),([^,]+),(.+?),([^,]*),(.*)$/)).filter(Boolean);
let ok = 0, total = 0;
const salida = ["id,tipo,resultado,normas_esperadas,fuentes_encontradas"];
for (const [, id, tipo, pregunta, esperadas] of filas) {
  const f = fuentes(pregunta.replace(/^"|"$/g, ""));
  if (tipo === "fuera") { salida.push(`${id},${tipo},(revisar la respuesta de la IA),,"${f.join(" | ")}"`); continue; }
  const esp = esperadas.split("|").filter(Boolean), acierto = esp.some((e) => e.includes("*") ? f.some((x) => x.startsWith(e.split("*")[0]) && x.endsWith(e.split("*")[1])) : f.includes(e));
  total++; if (acierto) ok++;
  salida.push(`${id},${tipo},${acierto ? "OK" : "FALLA"},${esperadas},"${f.join(" | ")}"`);
}
fs.writeFileSync(path.join(__dirname, "resultado_buscador.csv"), salida.join("\n") + "\n");
console.log(`Búsqueda: ${ok} de ${total} preguntas con la norma esperada entre las 6 fuentes.`);
console.log(salida.filter((l) => l.includes("FALLA")).join("\n"));
