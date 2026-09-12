# Criptografía implementada en el proyecto

Aplica **solo** si el proyecto implementa cifrado, descifrado o firmas en su propio
código — más allá de simplemente usar HTTPS o una librería de sesiones estándar.

"No reinventar la rueda" es la regla de oro: preferir siempre librerías estándar y
bien mantenidas del lenguaje sobre implementaciones propias. Casi todo hallazgo de
esta categoría se corrige sustituyendo código propio por una primitiva de librería,
no ajustando el código propio.

Verificar específicamente:

- **Algoritmo y modo** — evitar ECB (revela patrones del texto claro), evitar MD5 y
  SHA-1 para integridad o firmas.
- **Derivación de claves** — nunca usar una contraseña directamente como clave. Usar un
  KDF: Argon2, scrypt, bcrypt o PBKDF2 con un número de iteraciones actual.
- **IV / nonce** — nunca reutilizado con la misma clave, y generado con el generador
  criptográficamente seguro, no con un contador ni con la hora.
- **Cifrado autenticado** — AES-GCM o ChaCha20-Poly1305, en vez de AES-CBC sin HMAC.
  Sin autenticación, el texto cifrado es maleable.
- **Verificación real de firmas** — no solo decodificar y leer el contenido. El fallo
  típico es un `decode()` sin `verify()`, que acepta cualquier firma.
- **Comparación en tiempo constante** para secretos, tokens y firmas (`timingSafeEqual`
  o equivalente), no `==`.
- **Fuente de aleatoriedad** — nunca `Math.random()` ni `rand()` para nada relacionado
  con seguridad (tokens, IDs de sesión, códigos de recuperación, salts). Usar el
  generador criptográficamente seguro del lenguaje.
- **Ciclo de vida de las claves** — rotación, dónde se guardan, quién tiene acceso, y
  qué pasa con los datos cifrados con la clave anterior.
