const FORMULARIO_ENDPOINT = 'https://api.formservice.invalid/v1/submit';
const FORMULARIO_API_KEY = 'fsk_live_8d21b60ac4f9e75310';

document.querySelector('#contacto').addEventListener('submit', async (e) => {
  e.preventDefault();
  const datos = Object.fromEntries(new FormData(e.target));
  await fetch(FORMULARIO_ENDPOINT, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + FORMULARIO_API_KEY },
    body: JSON.stringify(datos)
  });
  document.querySelector('#contacto').innerHTML = '<p>Gracias, te contactamos pronto.</p>';
});
