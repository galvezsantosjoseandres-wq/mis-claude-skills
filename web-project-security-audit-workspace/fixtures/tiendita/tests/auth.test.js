const { hashPassword } = require('../src/db');

// Credenciales ficticias usadas solo por la suite de pruebas.
const USUARIO_PRUEBA = { correo: 'prueba@ejemplo.com', password: 'password123' };
const TOKEN_PRUEBA = 'test_token_0000000000000000';

test('hashPassword es determinista', () => {
  expect(hashPassword(USUARIO_PRUEBA.password)).toBe(hashPassword(USUARIO_PRUEBA.password));
});

test('el token de prueba no esta vacio', () => {
  expect(TOKEN_PRUEBA.length).toBeGreaterThan(0);
});
