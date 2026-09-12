# APIs propias y lógica de negocio

Aplica si el inventario detectó **APIs propias expuestas**, o **cualquier flujo con
dinero, cantidades, permisos o estados que cambian** — aunque no haya API formal.

Contenido: OWASP API Security Top 10 · errores de lógica de negocio

## OWASP API Security Top 10 como marco

Usarlo como referencia explícita en el reporte, no solo intuición suelta:

- **BOLA** (Broken Object Level Authorization) — ¿un usuario puede acceder o modificar
  datos de otro cambiando un ID en la URL o el request, sin que el backend verifique la
  pertenencia? Es el fallo más común y el más caro. La prueba concreta: tomar un
  identificador de otro usuario y pedirlo autenticado como el primero.
- **Autenticación rota** — tokens/sesiones débiles, sin expiración, o reutilizables
  tras logout (ver `autenticacion-y-sesiones.md`).
- **BOPLA / exposición excesiva de datos** — ¿la API devuelve más campos de los que el
  frontend necesita (hashes de contraseña, correos de terceros, datos internos, campos
  de auditoría) confiando en que el frontend "no los muestre"? Devolver el objeto
  completo de la base de datos es el patrón a buscar.
- **Consumo de recursos sin restricción** — sin límites de tamaño de página, de
  payload, de profundidad de consulta (GraphQL) o de tiempo de ejecución, permitiendo
  agotar recursos con una sola petición.
- **BFLA** (Broken Function Level Authorization) — endpoints de administrador
  accesibles por un usuario normal solo porque no aparecen en la interfaz, sin
  verificación real de rol en el backend.
- **Flujos de negocio sensibles sin protección** — ¿se puede automatizar o abusar un
  flujo legítimo: comprar todo el stock, aplicar un cupón ilimitadas veces, saltar un
  paso de aprobación manipulando el request directamente?
- **SSRF** — si el backend hace peticiones a URLs que el usuario controla (ej. "URL de
  tu foto de perfil", importar desde un enlace, webhooks salientes configurables),
  ¿puede apuntar a infraestructura interna, a `localhost`, o al servicio de metadatos
  de la nube?
- **Inventario de API** — ¿existen versiones viejas (`/v1/` ya reemplazada) o endpoints
  de prueba/debug todavía accesibles en producción?
- **Documentación** que no filtre información sensible de la arquitectura interna.

## Errores de lógica de negocio

Este punto exige pensar como quien intenta abusar del flujo legítimo, no buscar
errores de sintaxis. Es el más fácil de pasar por alto precisamente porque el código
"funciona bien" en el camino feliz, y ninguna herramienta automática lo detecta.

Preguntas concretas a probar, no solo a considerar:

- ¿Se puede enviar una **cantidad negativa** en un carrito, una transferencia o
  cualquier formulario numérico? ¿Y un decimal donde se esperaba entero, o un número
  tan grande que desborde?
- ¿Se puede **saltar un paso** de un checkout o de un flujo de aprobación llamando
  directo al endpoint del paso final?
- ¿Un usuario puede **acceder o modificar datos de otro** cambiando un ID (ver BOLA)?
- ¿Hay **límites de negocio** (edad mínima, cupos, fechas, stock) que solo se validan
  en el frontend?
- ¿Hay **condiciones de carrera** en operaciones que dependen de un saldo o un stock?
  Dos peticiones simultáneas que ambas leen "queda 1" y ambas restan.
- ¿El precio o el total viaja **desde el cliente** en vez de recalcularse en el servidor?
