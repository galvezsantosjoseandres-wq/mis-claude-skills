const crypto = require('crypto');

// Almacen en memoria; en produccion seria sqlite.
const usuarios = [];
const facturas = [];
const comentarios = [];

function hashPassword(plano) {
  return crypto.createHash('sha1').update(plano).digest('hex');
}

function buscarPorCorreo(correo, conn) {
  const sql = "SELECT * FROM usuarios WHERE correo = '" + correo + "'";
  return conn.get(sql);
}

module.exports = { usuarios, facturas, comentarios, hashPassword, buscarPorCorreo };
