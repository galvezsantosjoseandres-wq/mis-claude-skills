# Entrada de datos externos: inyección, XSS, redirecciones y límites

Aplica si el inventario detectó **cualquier endpoint que reciba input externo**:
formulario, API, webhook, parámetro de URL, cabecera, o subida de archivos.

Todo lo de aquí presupone un endpoint HTTP. La entrada externa también llega por
**eventos de plataforma** —el título de un issue, el cuerpo de un PR, un nombre de
rama— que acaban interpolados en un pipeline sin pasar por ningún endpoint: eso está
en `cicd-security.md`.

Contenido: inyección · XSS · open redirect · cabecera Host · XXE · rate limiting · CORS · uploads

## Inyección

Revisar toda construcción de consultas o comandos a partir de input: **SQL, NoSQL,
comandos del sistema, LDAP, CRLF en cabeceras**. La señal es la concatenación de
strings; la corrección es consulta parametrizada / API que separe código de datos.
Un ORM no inmuniza: busca sus escapes a SQL crudo (`raw`, `query`, `$where`).

## XSS

La vulnerabilidad más común y la que más se pasa por alto por darla por resuelta.
Revisar los tres tipos:

- **Reflejado** — input que vuelve en la respuesta de la misma petición.
- **Almacenado** — input guardado en BD y renderizado después a otros usuarios. El
  más grave: no requiere engañar a la víctima para que haga clic en nada.
- **Basado en DOM** — el input nunca toca el servidor; el daño lo hace el JS del
  cliente con `innerHTML`, `document.write`, `eval`, o los equivalentes del
  framework: `dangerouslySetInnerHTML` (React), `v-html` (Vue), `bypassSecurityTrustHtml`
  (Angular).

La defensa correcta es **codificación en la salida según el contexto** (HTML,
atributo, URL, dentro de JS), no "sanitizar la entrada" una sola vez al recibirla:
el mismo dato puede ser inofensivo en un contexto y ejecutable en otro. Si el
framework escapa por defecto, el hallazgo está en los puntos donde el código se
salta ese escape deliberadamente — búscalos explícitamente, son pocos y localizables.

## Open redirect

¿El sitio redirige a una URL que llega como parámetro, tipo `?redirect=` o `?next=`,
sin verificar que sea un destino propio o de una lista blanca? Se abusa para phishing
usando el dominio del usuario como fachada. Una redirección que **sí** valida contra
una lista de destinos permitidos es la implementación correcta: no la reportes.

## Inyección por cabecera Host

¿El backend confía ciegamente en la cabecera `Host` de la petición para construir
links, correos de recuperación de contraseña o rutas absolutas, sin validarla contra
una lista de dominios esperados? El vector clásico es un correo de reseteo cuyo enlace
apunta al dominio del atacante.

## XXE

Solo si el proyecto procesa XML subido o enviado por el usuario: verificar que el
parser tenga deshabilitada la resolución de entidades externas. En la mayoría de
lenguajes esto es una bandera del parser, no algo que se arregle sanitizando.

## Rate limiting

Distinguir dos niveles, no tratarlos como lo mismo:

- **Límite por IP** — protege contra abuso anónimo sin cuenta (ej. spam a un
  formulario público). Aplica casi siempre que hay un endpoint público.
- **Límite por cuenta/API key** — protege contra abuso de un usuario autenticado que
  se pasa de la raya. Solo aplica si existe autenticación.

Un proyecto puede necesitar uno, el otro, o ambos — no asumas que basta con uno solo.

⚠️ **Antipatrón en serverless/edge** (Workers, Vercel, Lambda, Cloud Run): un límite
de tasa implementado con una variable en memoria (un `Map` o `Set` a nivel de módulo)
NO funciona de forma confiable — cada instancia tiene su propia memoria, así que el
conteo se resetea en cada cold start y se reparte entre instancias distintas, dejando
el límite fácil de saltar. El límite debe vivir en un almacén compartido real (un KV
de la plataforma, Redis/Upstash, DynamoDB), nunca en una variable del proceso. Este
patrón también es engañoso en un servidor tradicional con varios workers o réplicas.

## CORS

Revisar que no haya `Access-Control-Allow-Origin: *` combinado con credenciales, ni
un reflejo del `Origin` recibido sin validarlo contra una lista. Recordar el límite
de lo que CORS hace: restringe **quién puede leer la respuesta** desde otro origen;
no impide que la petición se envíe. Por eso CORS no es una defensa contra CSRF.

## Subida de archivos

- Validar el **tipo real por contenido** (magic bytes), no por la extensión ni por el
  `Content-Type` que declara el cliente — ambos los controla quien sube.
- Límite de tamaño aplicado **en el servidor**, no solo en el formulario.
- Nombre de archivo **normalizado y generado por el servidor**. Usar el nombre del
  cliente directo es el vector de **path traversal** (`../../`) y de sobrescritura de
  archivos existentes.
- Almacenar **fuera del directorio servido públicamente**, o en un bucket sin permiso
  de ejecución. Un archivo subido dentro de la carpeta estática de la app puede
  terminar siendo servido —y ejecutado— desde el propio dominio.
- Nunca servir contenido subido desde el mismo origen de la aplicación si puede
  contener HTML o SVG: **un SVG es un vector de XSS**. Servir desde un dominio
  separado, o forzar `Content-Disposition: attachment` y `X-Content-Type-Options: nosniff`.
- Si el archivo se descarga después, verificar que la ruta de descarga no permita pedir
  archivos arbitrarios del servidor cambiando un parámetro.
