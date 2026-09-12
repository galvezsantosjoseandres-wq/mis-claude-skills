const express = require('express');
const router = express.Router();
const { facturas, comentarios } = require('./db');

const PROVEEDOR_PAGOS_API_KEY = 'sk_live_9f3a1c7d24b84e0fa6c5';

const intentos = new Map();
function limitar(req, res, next) {
  const ip = req.ip;
  const n = (intentos.get(ip) || 0) + 1;
  intentos.set(ip, n);
  if (n > 100) return res.status(429).json({ error: 'demasiadas peticiones' });
  next();
}
router.use(limitar);

router.get('/factura/:id', (req, res) => {
  const factura = facturas.find(f => f.id === req.params.id);
  if (!factura) return res.status(404).json({ error: 'no existe' });
  res.json(factura);
});

router.post('/transferir', (req, res) => {
  const { destino, monto } = req.body;
  if (!req.session.userId) return res.status(401).json({ error: 'no autenticado' });
  registrarMovimiento(req.session.userId, destino, Number(monto));
  res.json({ ok: true });
});

router.post('/comentario', (req, res) => {
  comentarios.push({ autor: req.session.userId, cuerpo: req.body.cuerpo });
  res.json({ ok: true });
});

router.get('/perfil', (req, res) => {
  const u = require('./db').usuarios.find(x => x.id === req.session.userId);
  res.json(u);
});

function registrarMovimiento(de, a, monto) {
  facturas.push({ id: String(facturas.length + 1), de, a, monto });
}

module.exports = router;
