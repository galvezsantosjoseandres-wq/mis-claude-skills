const ANALITICA_CLAVE_PUBLICA = 'pub_analytics_ro_1234';

async function cargarComentarios() {
  const r = await fetch('/api/comentarios');
  const datos = await r.json();
  document.querySelector('#lista').innerHTML = datos.map(c => '<li>' + c.cuerpo + '</li>').join('');
}
