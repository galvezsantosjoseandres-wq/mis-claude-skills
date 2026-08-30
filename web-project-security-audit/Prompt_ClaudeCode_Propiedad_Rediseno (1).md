Vamos a rediseñar la página de detalle de propiedad y extender el generador para que
soporte un esquema de datos más rico. Trabaja en la rama claude/lefinor-website-updates, en un
commit separado del resto de tareas pendientes.

## Referencia visual completa (ya aprobada)

```html
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Lefinor — Propiedad (demo)</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
  :root{ --azul:#0B1D33; --dorado:#D4AF37; --gris:#606468; --neutro:#F7F8FA; }
  *{box-sizing:border-box;}
  body{ font-family:'Montserrat',sans-serif; margin:0; color:var(--azul); background:#fff; }
  a{text-decoration:none;}
  .wrap{ max-width:1180px; margin:0 auto; padding:2.5rem 1.5rem; }
  .breadcrumb{ font-size:.82rem; color:var(--gris); margin-bottom:1.3rem; }
  .breadcrumb a{ color:var(--gris); }

  /* ===== Header de la propiedad ===== */
  .prop-header{ display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; gap:1rem; margin-bottom:1.6rem; }
  .prop-title{ font-weight:800; font-size:1.7rem; margin:0 0 .4rem; }
  .prop-quickspecs{ color:var(--gris); font-size:.92rem; }
  .prop-quickspecs span{ margin-right:.9rem; }
  .prop-price{ text-align:right; }
  .prop-price .amount{ font-weight:800; font-size:1.6rem; color:var(--azul); }
  .prop-price .period{ font-size:.85rem; color:var(--gris); font-weight:500; }
  .prop-tag{ display:inline-block; background:var(--azul); color:var(--dorado); font-size:.68rem; font-weight:700; letter-spacing:.08em; text-transform:uppercase; padding:.3rem .7rem; margin-bottom:.5rem; }

  /* ===== Galería ===== */
  .gallery{ display:grid; grid-template-columns: 1.6fr 1fr 1fr; grid-template-rows: 1fr 1fr; gap:.6rem; height:420px; border-radius:4px; overflow:hidden; margin-bottom:2.2rem; }
  .gallery .g-main{ grid-row:1/3; grid-column:1; position:relative; }
  .gallery .g-tile{ position:relative; overflow:hidden; }
  .gallery img, .gallery .ph{ width:100%; height:100%; object-fit:cover; display:block; }
  .ph{ background:repeating-linear-gradient(135deg,#12294a 0,#12294a 2px,#0e2140 2px,#0e2140 40px); }
  .g-more{ position:absolute; inset:0; background:rgba(11,29,51,.72); backdrop-filter: blur(2px); display:flex; align-items:center; justify-content:center; flex-direction:column; color:#fff; cursor:pointer; }
  .g-more svg{ margin-bottom:.3rem; }
  .g-more .n{ font-weight:800; font-size:1.3rem; }
  .g-more .lbl{ font-size:.78rem; font-weight:600; letter-spacing:.03em; }
  .play-badge{ position:absolute; bottom:10px; left:10px; background:rgba(11,29,51,.85); color:#fff; font-size:.72rem; font-weight:600; padding:.25rem .6rem; border-radius:2px; display:flex; align-items:center; gap:.3rem; }

  @media (max-width:820px){
    .gallery{ grid-template-columns:1fr 1fr; grid-template-rows:180px 100px; height:auto; }
    .gallery .g-main{ grid-column:1/3; grid-row:1; }
    .gallery .g-tile:nth-child(4){ display:none; }
  }

  /* ===== Cuerpo en 2 columnas ===== */
  .layout{ display:grid; grid-template-columns:1fr 340px; gap:2.5rem; align-items:start; }
  @media (max-width:900px){ .layout{ grid-template-columns:1fr; } }

  h2.section-title{ font-weight:700; font-size:1.15rem; margin:0 0 1rem; padding-top:1.6rem; border-top:1px solid rgba(11,29,51,.08); }
  section.first h2.section-title{ border-top:none; padding-top:0; }

  .caract-grid{ display:grid; grid-template-columns:1fr 1fr; gap:.7rem 2rem; }
  .caract-item{ display:flex; justify-content:space-between; border-bottom:1px dashed rgba(11,29,51,.1); padding-bottom:.5rem; font-size:.88rem; }
  .caract-item .lbl{ color:var(--gris); }
  .caract-item .val{ font-weight:600; }
  @media (max-width:520px){ .caract-grid{ grid-template-columns:1fr; } }

  .detalle p{ line-height:1.7; color:var(--azul); font-size:.94rem; }
  .detalle ul{ padding-left:1.2rem; line-height:1.9; font-size:.92rem; color:var(--azul); }
  .detalle li::marker{ color:var(--dorado); }

  /* ===== Formulario de contacto (rediseñado) ===== */
  .contact-card{ background:var(--neutro); border-radius:6px; padding:1.8rem; position:sticky; top:2rem; }
  .contact-card h3{ font-weight:700; font-size:1.05rem; margin:0 0 1.2rem; }
  .field{ margin-bottom:.9rem; }
  .field label{ display:block; font-size:.76rem; font-weight:600; color:var(--gris); margin-bottom:.3rem; }
  .field input, .field textarea{
    width:100%; border:1px solid rgba(11,29,51,.15); border-radius:4px; padding:.65rem .8rem;
    font-family:inherit; font-size:.88rem; background:#fff;
  }
  .field textarea{ resize:vertical; min-height:70px; }
  .btn-consulta{ width:100%; background:var(--azul); color:#fff; border:none; border-radius:4px; padding:.8rem; font-weight:700; font-size:.9rem; cursor:pointer; margin-top:.3rem; }
  .btn-whatsapp{ width:100%; background:#25D366; color:#fff; border:none; border-radius:4px; padding:.8rem; font-weight:700; font-size:.9rem; cursor:pointer; margin-top:.6rem; display:flex; align-items:center; justify-content:center; gap:.5rem; }
</style>
</head>
<body>

<div class="wrap">
  <div class="breadcrumb"><a href="#">Propiedades</a> / Apartamento en Alquiler, La Vega</div>

  <!-- GALERÍA -->
  <div class="gallery">
    <div class="g-main"><div class="ph"></div><span class="play-badge">▶ 00:41</span></div>
    <div class="g-tile"><div class="ph"></div></div>
    <div class="g-tile"><div class="ph"></div></div>
    <div class="g-tile"><div class="ph"></div></div>
    <div class="g-tile">
      <div class="ph"></div>
      <div class="g-more">
        <div class="n">+9</div>
        <div class="lbl">VER MÁS FOTOS</div>
      </div>
    </div>
  </div>

  <!-- HEADER -->
  <div class="prop-header">
    <div>
      <span class="prop-tag">Alquiler · La Vega</span>
      <h1 class="prop-title">Apartamento en Alquiler, La Vega</h1>
      <div class="prop-quickspecs">
        <span>🛏 3 habitaciones</span>
        <span>🛁 3.5 baños</span>
        <span>🚗 2 parqueos</span>
      </div>
    </div>
    <div class="prop-price">
      <div class="amount">US$ 1,900</div>
      <div class="period">/ mes</div>
    </div>
  </div>

  <div class="layout">
    <div>
      <!-- CARACTERÍSTICAS -->
      <section class="first">
        <h2 class="section-title">Características</h2>
        <div class="caract-grid">
          <div class="caract-item"><span class="lbl">Localización</span><span class="val">La Vega</span></div>
          <div class="caract-item"><span class="lbl">Condición</span><span class="val">Primer uso</span></div>
          <div class="caract-item"><span class="lbl">Uso actual</span><span class="val">Residencial</span></div>
          <div class="caract-item"><span class="lbl">Construcción</span><span class="val">250 m²</span></div>
          <div class="caract-item"><span class="lbl">Terreno</span><span class="val">0 m²</span></div>
          <div class="caract-item"><span class="lbl">Nivel / Piso</span><span class="val">2</span></div>
          <div class="caract-item"><span class="lbl">Ascensores</span><span class="val">1</span></div>
          <div class="caract-item"><span class="lbl">Edificable</span><span class="val">No</span></div>
          <div class="caract-item"><span class="lbl">Año construcción</span><span class="val">2019</span></div>
          <div class="caract-item"><span class="lbl">Comodidades</span><span class="val">Estudio, Family Room, Parqueos</span></div>
        </div>
      </section>

      <!-- DETALLE -->
      <section class="detalle">
        <h2 class="section-title">Detalle</h2>
        <p>Lindo apartamento en La Vega, a unos 800 metros del centro de la ciudad.</p>
        <ul>
          <li>250 m²</li>
          <li>3 habitaciones · 3.5 baños</li>
          <li>Sala · Estudio · Comedor · Terraza cerrada</li>
          <li>Cocina</li>
          <li>Área de lavado · habitación para empleada</li>
          <li>Pisos porcelanato · Madera preciosa</li>
          <li>Aires acondicionados y lavadora/secadora</li>
          <li>2 parqueos paralelos y techados</li>
        </ul>
        <p><strong>US$ 1,900</strong> alquiler con mantenimiento incluido.</p>
      </section>
    </div>

    <!-- FORMULARIO -->
    <aside class="contact-card">
      <h3>¿Interesado en esta propiedad?</h3>
      <div class="field"><label>Nombre</label><input type="text" placeholder="Tu nombre"></div>
      <div class="field"><label>Teléfono</label><input type="tel" placeholder="Tu teléfono"></div>
      <div class="field"><label>Correo electrónico</label><input type="email" placeholder="tucorreo@ejemplo.com"></div>
      <div class="field"><label>Mensaje</label><textarea placeholder="Escribe tu consulta..."></textarea></div>
      <button class="btn-consulta">Enviar consulta</button>
      <button class="btn-whatsapp">💬 Escribir por WhatsApp</button>
    </aside>
  </div>
</div>

</body>
</html>

```

## 1. Extiende el esquema de datos de "propiedades"

El JSON de cada propiedad hoy es simple (título, ciudad, tipo, precio, portada). Debe soportar
estos campos nuevos (ajusta nombres de claves al estilo que ya usan):

```
{
  "id": "",
  "titulo": "",
  "tipo_operacion": "",       // "venta" | "alquiler"
  "ciudad": "",
  "precio": "",                // como texto, ej "US$ 1,900" o "US$ 145,000"
  "precio_periodo": "",        // opcional, ej "/mes" — vacío si es venta
  "quickspecs": [],            // lista corta, ej ["3 habitaciones", "3.5 baños", "2 parqueos"]
  "galeria": [                 // lista de fotos y video, EN CUALQUIER CANTIDAD (puede ser 1, puede ser 20)
    { "tipo": "foto", "src": "" },
    { "tipo": "video", "src": "", "duracion": "00:41" }
  ],
  "caracteristicas": [         // lista de pares label/valor, CANTIDAD VARIABLE por propiedad
    { "label": "Localización", "valor": "" }
  ],
  "detalle_intro": "",         // párrafo introductorio
  "detalle_bullets": [],       // lista de viñetas
  "detalle_cierre": ""         // frase de cierre, ej "US$ 1,900 alquiler con mantenimiento incluido."
}
```

## 2. Importante: el generador debe ser flexible, no asumir que siempre hay datos completos

Las propiedades reales que lleguen del cliente van a variar mucho — algunas tendrán 2 fotos, otras
20; algunas tendrán video, otras no; algunas tendrán 10 características, otras solo 4. El
generador y la plantilla deben manejar todos estos casos sin romperse:

- Si `galeria` tiene 5 elementos o menos: muestra todos, sin overlay de "ver más".
- Si tiene más de 5: muestra los primeros 5 (el quinto con el difuminado + contador "+N VER MÁS
  FOTOS" tal como está en la referencia), y el resto se ve al abrir la galería completa.
- Si no hay ningún video en `galeria`: simplemente no muestra la insignia de duración en ningún
  tile — no debe fallar ni dejar espacio vacío raro.
- Si `caracteristicas` tiene pocos elementos (ej. solo 4): la grilla de 2 columnas se ve bien
  igual, no dejes espacios rotos ni asumas una cantidad fija.
- Si `precio_periodo` está vacío (caso de venta): no muestres el "/" vacío, omite esa línea por
  completo.

## 3. Comportamiento de "Ver más fotos"

Al hacer clic en el overlay del quinto tile (o en cualquier foto/video de la galería), abre un
lightbox / modal a pantalla completa con navegación (flechas anterior/siguiente) mostrando TODOS
los elementos de `galeria` en orden, fotos y video incluidos. Reutiliza la lógica de
anterior/siguiente que ya existe en el carrusel actual de la página de propiedad si es posible,
en vez de reescribirla desde cero.

## 4. Formulario de contacto — reemplaza el actual

Los campos son: Nombre, Teléfono, Correo electrónico, Mensaje. Dos botones: "Enviar consulta"
(estilo navy, como está en la referencia) y "Escribir por WhatsApp" (verde, como ya lo tenían
antes — no lo cambies a dorado, el verde de WhatsApp se mantiene reconocible a propósito).

## 5. Actualiza las 2 propiedades de ejemplo existentes al nuevo esquema

Las propiedades placeholder actuales (alquiler en Cotuí, venta en Fantino) deben migrarse al
nuevo esquema de datos — complétalas con características y detalle razonables de ejemplo
(pueden ser genéricos/breves, ya que son placeholders), para confirmar que la plantilla funciona
con datos "delgados" y no solo con el ejemplo rico de abajo.

## 6. Agrega esta propiedad nueva de ejemplo (dato real de referencia, con datos completos)

```json
{
  "id": "apartamento-la-vega",
  "titulo": "Apartamento en Alquiler, La Vega",
  "tipo_operacion": "alquiler",
  "ciudad": "La Vega",
  "precio": "US$ 1,900",
  "precio_periodo": "/mes",
  "quickspecs": ["3 habitaciones", "3.5 baños", "2 parqueos"],
  "galeria": [
    {"tipo": "video", "src": "", "duracion": "00:41"},
    {"tipo": "foto", "src": ""},
    {"tipo": "foto", "src": ""},
    {"tipo": "foto", "src": ""},
    {"tipo": "foto", "src": ""},
    {"tipo": "foto", "src": ""},
    {"tipo": "foto", "src": ""}
  ],
  "caracteristicas": [
    {"label": "Localización", "valor": "La Vega"},
    {"label": "Condición", "valor": "Primer uso"},
    {"label": "Uso actual", "valor": "Residencial"},
    {"label": "Construcción", "valor": "250 m²"},
    {"label": "Terreno", "valor": "0 m²"},
    {"label": "Nivel / Piso", "valor": "2"},
    {"label": "Ascensores", "valor": "1"},
    {"label": "Edificable", "valor": "No"},
    {"label": "Año construcción", "valor": "2019"},
    {"label": "Comodidades", "valor": "Estudio, Family Room, Parqueos"}
  ],
  "detalle_intro": "Lindo apartamento en La Vega, a unos 800 metros del centro de la ciudad.",
  "detalle_bullets": [
    "250 m²",
    "3 habitaciones · 3.5 baños",
    "Sala · Estudio · Comedor · Terraza cerrada",
    "Cocina",
    "Área de lavado · habitación para empleada",
    "Pisos porcelanato · Madera preciosa",
    "Aires acondicionados y lavadora/secadora",
    "2 parqueos paralelos y techados"
  ],
  "detalle_cierre": "US$ 1,900 alquiler con mantenimiento incluido."
}
```

Las fotos de esta propiedad de ejemplo también son placeholder (patrón de rayas diagonales, como
ya usan en las otras) — no hay fotos reales todavía.

Al terminar, muéstrame capturas de escritorio y móvil de esta propiedad de ejemplo, y confirma
que las 2 propiedades placeholder anteriores (con menos datos) también se ven bien con la nueva
plantilla, antes de abrir el Pull Request.
