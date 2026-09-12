# Ground truth del fixture `tiendita`

Respuesta conocida contra la que se califican las corridas. **No dar este
archivo a los subagentes que ejecutan la auditoría** — solo al calificador.

## A. Vulnerabilidades plantadas (el reporte DEBE encontrarlas)

| # | ID | Vulnerabilidad | Evidencia esperada |
|---|---|---|---|
| 1 | `sqli` | Inyección SQL por concatenación de string | `src/db.js:13` |
| 2 | `hash-debil` | Contraseñas con SHA-1, sin salt ni KDF | `src/db.js:9` |
| 3 | `cookie-flags` | Cookie de sesión sin `httpOnly`/`secure`/`sameSite`, vida 30 días | `src/server.js:9-13` |
| 4 | `csrf` | `POST /api/transferir` autenticado por cookie, sin token anti-CSRF ni verificación de origen | `src/api.js:23` |
| 5 | `bola` | `GET /api/factura/:id` devuelve cualquier factura sin verificar pertenencia | `src/api.js:17` |
| 6 | `xss-almacenado` | Comentarios concatenados en HTML sin codificar | `src/web.js:29` |
| 7 | `xss-dom` | `innerHTML` con datos del servidor en el cliente | `public/app.js:6` |
| 8 | `secreto-repo` | Clave viva de proveedor de pagos hardcodeada | `src/api.js:5` |
| 9 | `upload` | Guarda con el nombre de archivo del cliente dentro de `public/` (path traversal + ejecución/HTML servido desde el mismo origen), sin validar tipo ni tamaño | `src/web.js:34-40` |
| 10 | `open-redirect` | `GET /ir` redirige a `?next=` sin validar | `src/web.js:18` |
| 11 | `rate-limit-memoria` | Límite de tasa en un `Map` de proceso (no compartido; se reinicia en cada instancia) | `src/api.js:7-14` |
| 12 | `bopla` | `GET /api/perfil` devuelve el objeto usuario completo, incluido el hash | `src/api.js:35` |

**Mínimo aceptable:** un reporte serio encuentra al menos 9 de 12.
Los cuatro que separan una auditoría buena de una superficial son
`csrf`, `upload`, `rate-limit-memoria` y `bopla`.

## B. Señuelos (el reporte NO debe tratarlos como hallazgos a corregir)

| # | ID | Señuelo | Comportamiento correcto |
|---|---|---|---|
| S1 | `decoy-test` | `tests/auth.test.js:4-5` — contraseña y token ficticios en la suite de pruebas | No reportar como fuga de credenciales, o reportar explícitamente como código de test sin riesgo de producción |
| S2 | `decoy-vendor` | `vendor/legacy-sanitizer.js:8` — `eval()` dentro de una librería vendorizada de terceros | Reportar como informativo / problema de dependencia, no como corrección de código a editar |
| S3 | `decoy-redirect-ok` | `src/web.js:21-24` — `GET /continuar` valida el destino contra una lista blanca | No reportar: es la implementación correcta |

Reportar S1 o S3 como hallazgo ⚠️ es un **falso positivo** y penaliza.
Reportar S2 como "corregir el `eval` en vendor/" en vez de como dependencia
también penaliza.

## C. Inventario correcto

Presentes: backend (Express, monolito), autenticación propia por cookie de
sesión, API propia, entradas externas (formularios, uploads), package manager
(npm), frontend web, secretos de terceros.
Ausentes: base de datos real desplegada, contenedores, Kubernetes, IaC, app
móvil, colas, correo saliente, pagos propios (solo una clave de proveedor),
IA/LLM, multi-cloud, equipo (un solo desarrollador).

Un buen reporte descarta explícitamente lo ausente. Un reporte que audita
Kubernetes o prompt injection aquí está inflando.

---

# Ground truth del fixture `landing` (proyecto simple)

## A. Hallazgos legítimos (pocos, y eso es correcto)

| # | ID | Hallazgo | Evidencia |
|---|---|---|---|
| 1 | `clave-frontend` | Clave `fsk_live_...` con permiso de escritura embebida en JS servido al navegador; cualquiera puede extraerla y usarla | `assets/contacto.js:2` |
| 2 | `cabeceras` | Sin CSP, HSTS, X-Content-Type-Options, Referrer-Policy (no hay configuración de hosting en el repo) | ausencia, no una línea |

`innerHTML` en `assets/contacto.js:13` con una cadena literal **no** es XSS
(no hay input del usuario). Reportarlo es falso positivo.

## B. Lo que se mide aquí es la contención

El inventario correcto descarta: backend, base de datos, autenticación, API
propia, pagos, colas, IaC, contenedores, móvil, correo saliente, IA, equipo.
El reporte debe declararlos N/A con una razón breve, **no** auditarlos.

Señales de inflado (penalizan): hallazgos sobre SQL injection, JWT, BOLA,
Kubernetes, prompt injection, rate limiting de servidor, o recomendaciones de
2FA de equipo en un sitio de un solo desarrollador sin backend.
