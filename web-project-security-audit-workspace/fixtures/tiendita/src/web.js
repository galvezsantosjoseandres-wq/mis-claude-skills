const express = require('express');
const path = require('path');
const router = express.Router();
const { comentarios, hashPassword, usuarios } = require('./db');

const DESTINOS_PERMITIDOS = ['/panel', '/perfil', '/facturas'];

router.post('/login', (req, res) => {
  const u = usuarios.find(x => x.correo === req.body.correo);
  if (!u || u.hash !== hashPassword(req.body.password)) {
    return res.status(401).send('credenciales invalidas');
  }
  req.session.userId = u.id;
  res.redirect('/panel');
});

router.get('/ir', (req, res) => {
  res.redirect(req.query.next);
});

router.get('/continuar', (req, res) => {
  const destino = req.query.to;
  if (!DESTINOS_PERMITIDOS.includes(destino)) return res.status(400).send('destino no permitido');
  res.redirect(destino);
});

router.get('/comentarios', (req, res) => {
  const filas = comentarios
    .map(c => '<li><b>' + c.autor + '</b>: ' + c.cuerpo + '</li>')
    .join('');
  res.send('<html><body><ul>' + filas + '</ul></body></html>');
});

router.post('/subir', (req, res) => {
  const archivo = req.files.adjunto;
  const destino = path.join(__dirname, '..', 'public', 'adjuntos', archivo.name);
  archivo.mv(destino, err => {
    if (err) return res.status(500).send('error');
    res.send('subido a /adjuntos/' + archivo.name);
  });
});

module.exports = router;
