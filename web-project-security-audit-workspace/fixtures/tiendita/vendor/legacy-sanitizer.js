/*!
 * legacy-sanitizer v0.4.2 — copia vendorizada, NO EDITAR A MANO.
 * Fuente: https://example.invalid/legacy-sanitizer
 */
(function (root, factory) { root.LegacySanitizer = factory(); })(this, function () {
  function compilarRegla(expr) {
    // La libreria compila reglas del usuario con eval.
    return eval('(function(v){ return ' + expr + '; })');
  }
  function limpiar(html) {
    return String(html).replace(/<script[\s\S]*?<\/script>/gi, '');
  }
  return { compilarRegla: compilarRegla, limpiar: limpiar };
});
