// Ejecutar en la consola de una pestaña de https://normas.mercosur.int ya abierta.
// Versión ampliada de obtener_enlaces.js: recorre varios años y tipos de norma y,
// además de los enlaces, toma de la página de detalle la fecha de aprobación y la
// vigencia. 1 s de pausa entre pedidos (la pausa usa un Worker para que el navegador
// no la frene si la pestaña queda en segundo plano).
// Corre en segundo plano; el avance queda en window.__sim.estado y el resultado en
// window.__sim.datos[clave] (clave 'gmc' o 'ccm').
//
// tipo_normativa_id: 1 = Decisiones CMC, 4 = Resoluciones GMC, 2 = Directivas CCM,
// 3 = Recomendaciones.
const TANDAS = [
  {clave: 'gmc', tipo: 'Resoluciones GMC', tipo_id: 4, desde: 1991, hasta: 2026},
  {clave: 'ccm', tipo: 'Directivas CCM', tipo_id: 2, desde: 1994, hasta: 2026},
];
const BASE = 'https://normas.mercosur.int/simfiles/normativas/';

window.__sim = window.__sim || {datos: {}, estado: {}, errores: []};
const S = window.__sim;
const tok = document.querySelector('meta[name=csrf-token]').content;
const H = {'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8', 'X-CSRF-TOKEN': tok, 'X-Requested-With': 'XMLHttpRequest'};
const worker = new Worker(URL.createObjectURL(new Blob(
  ['onmessage = e => setTimeout(() => postMessage(e.data), e.data.ms)'], {type: 'text/javascript'})));
let seq = 0; const pend = {};
worker.onmessage = e => { pend[e.data.id](); delete pend[e.data.id]; };
const pausa = ms => new Promise(r => { const id = ++seq; pend[id] = r; worker.postMessage({id, ms}); });
const html = s => new DOMParser().parseFromString(s, 'text/html');
const clean = s => (s || '').replace(/\s+/g, ' ').trim();

async function pedir(url, body) {
  for (let intento = 1; ; intento++) {
    await pausa(1000);
    try {
      const r = await fetch(url, body ? {method: 'POST', headers: H, body} : {});
      if (!r.ok) throw new Error(url + ' ' + r.status);
      return await r.text();
    } catch (e) {
      if (intento >= 3) throw e;
      await pausa(5000 * intento);
    }
  }
}

function detalle(texto) {
  const t = clean(html(texto).body.textContent);
  const fecha = (t.match(/Fecha de aprobaci[oó]n\s*(\d{2}\/\d{2}\/\d{4})/) || [])[1] || '';
  const vig = clean((t.match(/Entrada en Vigencia(.*?)(Marco Jur[ií]dico|Concordancia|$)/) || [])[1] || '').slice(0, 400);
  const derogadaPor = [...t.matchAll(/Es derogada por (?:la |el )?([A-Za-zé]+ \d+\/\d{4})/g)].map(m => m[1]);
  const derogada = /derogad/i.test(vig) || derogadaPor.length > 0;
  return {fecha, estado: derogada ? 'Derogada' : 'Vigente', vigencia: vig, derogada_por: derogadaPor.join('; ')};
}

async function tanda(T) {
  const lista = S.datos[T.clave] = S.datos[T.clave] || [];
  const hechos = new Set(lista.map(x => x.normativa_id));
  for (let anho = T.desde; anho <= T.hasta; anho++) {
    S.estado[T.clave] = `${anho} (lista)`;
    let filas;
    try { filas = html(await pedir('/public/normativas/list', `tipo_normativa_id=${T.tipo_id}&anho=${anho}`)).querySelectorAll('tr'); }
    catch (e) { S.errores.push({tipo: T.tipo, anho, error: String(e)}); continue; }
    for (const tr of filas) {
      const b = tr.querySelector('[data-sim-normativa-id]'); const td = tr.querySelectorAll('td');
      if (!b || td.length < 2) continue;
      const id = b.getAttribute('data-sim-normativa-id');
      if (hechos.has(id)) continue;
      const reg = {tipo: T.tipo, anho, numero: clean(td[0].textContent), titulo: clean(td[1].textContent), normativa_id: id, archivos: []};
      S.estado[T.clave] = `${anho} ${reg.numero} (${lista.length} listas)`;
      try {
        const modal = html(await pedir('/public/normativas/version/lastfiles', 'normativa_id=' + id));
        reg.archivos = [...modal.querySelectorAll('tr')].map(f => {
          const a = f.querySelector('a[href*="/simfiles/normativas/"]'); if (!a) return null;
          const etiqueta = clean(f.querySelector('small')?.textContent);
          const idioma = /Español/i.test(etiqueta) ? 'ES' : /Portugu/i.test(etiqueta) ? 'PT' : (etiqueta || '?');
          return {archivo: decodeURIComponent(a.getAttribute('href').replace(BASE, '')), idioma};
        }).filter(Boolean);
      } catch (e) { reg.error_archivos = String(e); }
      try { Object.assign(reg, detalle(await pedir('/public/normativas/' + id))); }
      catch (e) { reg.error_detalle = String(e); }
      lista.push(reg); hechos.add(id);
    }
  }
  S.estado[T.clave] = `TERMINADO (${lista.length})`;
}

S.promesa = (async () => { for (const T of TANDAS) await tanda(T); })()
  .catch(e => { S.estado.fatal = String(e); });
'iniciado';
