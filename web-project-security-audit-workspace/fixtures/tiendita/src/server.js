const express = require('express');
const session = require('cookie-session');
const db = require('./db');
const app = express();

app.use(express.urlencoded({ extended: true }));
app.use(express.json());

app.use(session({
  name: 'sid',
  keys: ['clave-de-sesion'],
  maxAge: 30 * 24 * 60 * 60 * 1000
}));

app.use(express.static('public'));

app.use('/api', require('./api'));
app.use('/', require('./web'));

app.listen(3000, () => console.log('tiendita en :3000'));
