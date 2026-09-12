# Autenticación, sesiones y CSRF

Aplica si el inventario detectó **login de usuarios** (propio, OAuth de terceros o SSO).

Contenido: contraseñas · cookies de sesión · CSRF · JWT · fuerza bruta · roles

## Contraseñas

Hashing con un KDF diseñado para ello — **bcrypt, scrypt o Argon2** — nunca texto
plano, nunca cifrado reversible, y nunca SHA-256/SHA-1/MD5 a secas: son rápidas por
diseño, que es exactamente lo contrario de lo que se necesita aquí. Verificar también
salt por usuario (los KDF anteriores lo hacen solos) y que no haya un límite de
longitud máxima sospechosamente bajo, que suele delatar almacenamiento en claro.

## Cookies de sesión

Verificar los tres flags:

- **`HttpOnly`** — el JS del cliente no puede leer la cookie. Limita el impacto de un
  XSS: sin esto, un XSS se convierte directamente en robo de sesión.
- **`Secure`** — nunca viaja por HTTP plano.
- **`SameSite`** — `Lax` o `Strict`. `None` obliga a `Secure` y exige justificación.

Además: la sesión debe **regenerarse al iniciar sesión** (si el ID de sesión sobrevive
al login, hay riesgo de fijación de sesión), el logout debe invalidarla **en el
servidor** y no solo borrar la cookie en el navegador, y la vida de la sesión debe ser
proporcional al riesgo — una sesión bancaria de 30 días no lo es.

## CSRF

Aplica siempre que **el navegador autentique la petición automáticamente** (cookie de
sesión, autenticación básica). La pregunta: ¿cada acción que cambia estado
(POST/PUT/DELETE, y cualquier GET que modifique algo — que ya es un error en sí) está
protegida con un token anti-CSRF validado en el servidor, o con `SameSite` más
verificación de origen (`Origin`/`Referer`)?

Confusión frecuente que conviene nombrar en el reporte: **CORS no protege contra
CSRF**. Un formulario cross-site puede enviar la petición igual; CORS solo limita
quién puede *leer la respuesta*.

Si la API se autentica exclusivamente con un token en cabecera `Authorization` (no con
cookie), CSRF normalmente no aplica: dilo así y descártalo con esa razón, en vez de
omitirlo en silencio.

## JWT

- **Fijar el algoritmo explícitamente en el backend.** Nunca confiar en el algoritmo
  que declara el propio token: el ataque clásico es cambiarlo a `"alg": "none"` o
  forzar confusión entre RS256/HS256 para falsificar la firma.
- Secreto/clave de firma suficientemente largo y **no hardcodeado** en el repo.
- Expiración corta con mecanismo de renovación, no validez indefinida.
- **Un JWT no se puede revocar por sí solo.** Si el proyecto necesita cerrar sesión de
  verdad, expulsar a un usuario o revocar un dispositivo, verificar que exista una
  lista de revocación o tokens de refresco de vida corta. Sin eso, "cerrar sesión" es
  cosmético hasta que el token expire.
- No guardar datos sensibles en el payload: va firmado, no cifrado, y cualquiera puede
  leerlo.

## Fuerza bruta y enumeración

Límite de intentos por cuenta y por IP, retardo progresivo o bloqueo temporal, y
mensajes de error que no revelen si el correo existe (enumeración de usuarios). Lo
mismo aplica al flujo de recuperación de contraseña, que a menudo queda sin límite.

## Roles y permisos

Verificar que el rol se resuelva **en el servidor** a partir de la sesión, nunca de un
campo que venga en el request o de algo que el cliente pueda editar. Para el detalle
de fallos de autorización por objeto y por función, ver `apis-y-logica-de-negocio.md`.

## 2FA

¿Disponible? ¿Obligatorio para roles administrativos? Si el proyecto maneja dinero o
datos de terceros, la ausencia de 2FA para administradores es un hallazgo, no una
mejora opcional.
