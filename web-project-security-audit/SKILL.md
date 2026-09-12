---
name: web-project-security-audit
description: Realiza una auditoría de seguridad de CUALQUIER proyecto de software (sitio estático, app con backend y base de datos, sistema con login, microservicios, apps móviles, infraestructura cloud compleja), construyendo el checklist dinámicamente según lo que el proyecto realmente tenga, sin asumir un stack fijo. Úsala siempre que el usuario pida "revisar seguridad", "auditoría de seguridad", "hay vulnerabilidades", "está seguro mi sitio/app/backend", antes de un lanzamiento o despliegue a producción, o al preparar un nuevo proyecto para un cliente — sin importar la escala del proyecto. Audita el proyecto COMPLETO; si el usuario solo quiere revisar los cambios pendientes de una rama o PR, esa es una revisión de diff, no esta skill. Primero recopila el inventario real de componentes del proyecto (no asumas un stack previo, incluso si proyectos anteriores del usuario eran más simples) antes de decidir qué categorías de seguridad aplican.
---

# Auditoría de seguridad — checklist construido dinámicamente según el proyecto real

Esta skill NO asume ningún stack por defecto. Sirve igual para un sitio estático de una página como para un backend con microservicios, base de datos, autenticación, colas de mensajes, e infraestructura cloud. El objetivo es evitar dos extremos: aplicar un checklist gigante de seguridad empresarial a un proyecto simple (sobre-ingeniería), o aplicar un checklist mínimo a un proyecto que ya creció en complejidad (bajo-ingeniería, el riesgo real conforme el usuario escale).

**Regla central: nunca reutilices el resultado del inventario de un proyecto anterior.** Cada vez que se invoque esta skill, se repite el Paso 1 desde cero — un proyecto nuevo, o el mismo proyecto meses después, puede tener un inventario de componentes completamente distinto al de la última vez.

## Paso 1 — Inventario de componentes (obligatorio, siempre desde cero)

No preguntes "¿qué stack usas?" de forma genérica — investiga o pregunta punto por punto, porque cada respuesta activa o descarta categorías enteras del checklist:

1. **Hosting/infraestructura**: ¿estático, serverless, contenedores, VMs propias, Kubernetes, multi-cloud?
2. **Backend**: ¿existe? ¿monolito o microservicios? ¿qué lenguaje/framework?
3. **Base de datos**: ¿cuál(es)? ¿relacional, documental, cache (Redis), vector? ¿multi-tenant?
4. **Autenticación**: ¿hay login de usuarios? ¿propio, OAuth de terceros, SSO empresarial? ¿sesiones con cookie o tokens tipo JWT? ¿roles/permisos distintos por usuario?
5. **APIs**: ¿expone APIs propias? ¿públicas o solo internas? ¿versionadas?
6. **Puntos de entrada de datos externos**: formularios, uploads de archivos, webhooks, integraciones de terceros que envían datos
7. **Pagos**: ¿procesa pagos directamente, o delega 100% a un proveedor (Stripe, PayPal) sin tocar datos de tarjeta?
8. **Mensajería/colas**: ¿usa colas (SQS, RabbitMQ), websockets, eventos en tiempo real?
9. **Infraestructura como código**: ¿Terraform, CloudFormation, Pulumi? ¿IAM/roles configurados manualmente o vía código?
10. **Contenedores**: ¿Docker/Kubernetes? ¿imágenes propias o de terceros?
11. **Móvil**: ¿hay una app nativa o híbrida asociada?
12. **Correo saliente**: ¿el dominio envía correos transaccionales o de marketing?
13. **Equipo/acceso**: ¿un solo desarrollador o varias personas con acceso al repo/infraestructura?
14. **Secretos y proveedores externos**: ¿qué APIs de terceros consume y con qué credenciales?

Si el proyecto es tan simple que muchas de estas preguntas no aplican (por ejemplo, un sitio estático de una página), está perfectamente bien que la mayoría de categorías se descarten — el inventario corto es un resultado legítimo, no un fallo del proceso. Lo que no es aceptable es saltarse el inventario y asumir la respuesta.

**Mapeo de fronteras de confianza (para proyectos con más de un componente):** identifica cada punto donde los datos cruzan de un nivel de confianza a otro — usuario→servidor, servidor→base de datos, servidor→servicio de terceros, proceso sin privilegios→proceso con privilegios. Para cada frontera, considera brevemente las 6 categorías de amenaza de STRIDE: **S**uplantación de identidad, **T**ampering/alteración de datos en tránsito, **R**epudio (¿se puede negar una acción por falta de registro/auditoría?), **I**nformación divulgada indebidamente, **D**enegación de servicio, **E**levación de privilegios. No hace falta un documento formal para un proyecto simple — es un chequeo mental de "¿qué podría salir mal cruzando esta frontera?" antes de pasar al Paso 2.

### Alcance de esta ejecución en particular

No toda invocación de esta skill necesita ser una auditoría completa desde cero. **Antes de decidir el modo, busca auditorías previas en `security-audit/` dentro del proyecto** (ver Paso 3, Fase A): los modos Rápido y Diff dependen de ese reporte y, si no existe ninguno, el único modo posible es Completo.

- **Completo** — inventario y checklist desde cero (el default, y obligatorio la primera vez que se audita un proyecto o si no hay reporte previo en `security-audit/`)
- **Rápido** — repetir solo los puntos que en el último reporte quedaron ⚠️, ⏸ o 🛡, sin rehacer el inventario entero
- **Diff/PR** — el usuario solo agregó o cambió código puntual (una función nueva, un endpoint) desde la última auditoría completa; enfócate en si ese cambio introduce riesgo nuevo o afecta hallazgos previos, no en repetir todo el proyecto
- **Enfocado** — el usuario pide revisar solo una categoría específica (ej. "revisa solo las dependencias")

Aclara con el usuario cuál modo aplica si no es obvio por el contexto de la petición.

## Paso 2 — Construir el checklist específico de este proyecto

A partir del inventario, arma la lista de puntos a auditar. No copies una plantilla fija — cada categoría del inventario activa un bloque de preguntas de seguridad relacionado. Algunos bloques de referencia (no exhaustivo, usa criterio para añadir lo que el inventario sugiera que falta):

- **Si hay cualquier endpoint que reciba input externo** (formulario, API, webhook): inyección (SQL/NoSQL/comandos/CRLF), validación server-side, límites de tamaño/longitud, rate limiting, CORS. Clases de vulnerabilidad concretas a revisar activamente, no solo en teoría:
  - **XSS** — la más común y la que más se pasa por alto por darla por resuelta. Revisar los tres tipos: **reflejado** (input que vuelve en la respuesta de la misma petición), **almacenado** (input guardado en BD y renderizado después a otros usuarios — el más grave) y **basado en DOM** (el input nunca toca el servidor; el daño lo hace el JS del cliente con `innerHTML`, `document.write`, `eval`, o equivalentes del framework como `dangerouslySetInnerHTML`/`v-html`). La defensa correcta es **codificación en la salida según el contexto** (HTML, atributo, URL, JS), no "sanitizar la entrada" una sola vez al recibirla. Si el framework escapa por defecto, el hallazgo está en los puntos donde el código se salta ese escape deliberadamente — búscalos explícitamente.
  - **Open redirect** — ¿el sitio redirige a una URL que llega como parámetro, tipo `?redirect=` o `?next=`, sin verificar que sea un destino propio o de una lista blanca? Se abusa para phishing usando tu dominio como fachada.
  - **Inyección por cabecera Host** — ¿el backend confía ciegamente en la cabecera `Host` de la petición para construir links, resetear contraseñas, etc., sin validarla contra una lista de dominios esperados?
  - **XXE** — solo si el proyecto procesa XML subido por el usuario: verificar que el parser tenga deshabilitada la resolución de entidades externas.
  - Nota sobre rate limiting: distinguir dos niveles, no tratarlos como lo mismo. (a) **Límite por IP** — protege contra abuso anónimo sin cuenta (ej. spam a un formulario público); aplica casi siempre que hay un endpoint público. (b) **Límite por cuenta/API key** — protege contra abuso de un usuario autenticado que se pasa de la raya; solo aplica si existe autenticación. Un proyecto puede necesitar uno, el otro, o ambos — no asumas que basta con uno solo de los dos.
  - ⚠️ Antipatrón específico en serverless/edge (Workers, Vercel, Lambda, Cloud Run): un límite de tasa implementado con una variable en memoria (un `Map` o `Set` a nivel de módulo) NO funciona de forma confiable — cada instancia tiene su propia memoria, así que el conteo se resetea en cada cold start y se reparte entre instancias distintas, dejando el límite fácil de saltar. El límite debe vivir en un almacén compartido real (un KV de la plataforma, Redis/Upstash, DynamoDB), nunca en una variable del proceso.
- **Si hay uploads de archivos**: validar el tipo real por contenido (magic bytes), no por la extensión ni por el `Content-Type` que declara el cliente; límite de tamaño aplicado en el servidor; nombre de archivo normalizado y generado por el servidor (nunca usar el nombre del cliente directo — vector de **path traversal** con `../`); almacenamiento **fuera del directorio servido públicamente** o en un bucket sin permiso de ejecución; nunca servir lo subido desde el mismo dominio de la aplicación si puede contener HTML/SVG (un SVG es un vector de XSS); y si el archivo se descarga después, verificar que la ruta de descarga no permita pedir archivos arbitrarios del servidor cambiando un parámetro.
- **Si hay base de datos**: control de acceso a nivel de fila o documento, encriptación en reposo de datos sensibles, backups y quién puede restaurarlos, principio de mínimo privilegio en credenciales de conexión
- **Si hay autenticación**: hashing de contraseñas (nunca texto plano ni cifrado reversible; usar bcrypt/scrypt/Argon2, nunca SHA/MD5 a secas), expiración y renovación de sesión/token, protección contra fuerza bruta, 2FA disponible u obligatorio, gestión de roles y permisos
  - **Si la sesión vive en una cookie**: verificar los tres flags — `HttpOnly` (el JS del cliente no puede leer la cookie, limita el impacto de un XSS), `Secure` (nunca viaja por HTTP plano) y `SameSite` (`Lax` o `Strict`; `None` obliga a `Secure` y exige justificación). Verificar también que la sesión se **regenere al iniciar sesión** (si el ID de sesión sobrevive al login, hay riesgo de fijación de sesión) y que el logout invalide la sesión **en el servidor**, no solo borre la cookie en el navegador.
  - **CSRF** — aplica siempre que el navegador autentique automáticamente la petición (cookie de sesión, autenticación básica): ¿cada acción que cambia estado (POST/PUT/DELETE, y cualquier GET que modifique algo — que ya es un error en sí) está protegida con un token anti-CSRF validado en el servidor, o con `SameSite` más verificación de origen (`Origin`/`Referer`)? Ojo con la confusión frecuente: **CORS no protege contra CSRF** — un formulario cross-site puede enviar la petición igual; CORS solo limita quién puede *leer la respuesta*. Si la API se autentica exclusivamente con un token en cabecera `Authorization` (no con cookie), CSRF normalmente no aplica: dilo así y descártalo con esa razón.
  - Si la autenticación usa JWT: verificar que el algoritmo esté fijado explícitamente en el backend (nunca confiar en el algoritmo que declara el propio token — el ataque clásico es cambiarlo a `"alg": "none"` o forzar confusión entre RS256/HS256 para falsificar la firma), que el secreto/clave de firma sea suficientemente largo y no esté hardcodeado, y que el token tenga expiración corta con mecanismo de renovación, no una validez indefinida. Un JWT no se puede revocar por sí solo: si el proyecto necesita cerrar sesión de verdad o expulsar a un usuario, verificar que exista una lista de revocación o tokens de refresco de vida corta.
- **Si hay APIs propias expuestas o cualquier lógica de negocio con dinero/cantidades/permisos**: usar como marco de referencia el **OWASP API Security Top 10**, no solo intuición suelta:
  - **BOLA** (Broken Object Level Authorization) — ¿un usuario puede acceder/modificar datos de otro cambiando un ID en la URL o el request, sin que el backend verifique la pertenencia?
  - **Autenticación rota** — tokens/sesiones débiles, sin expiración, o reutilizables tras logout
  - **BOPLA / exposición excesiva de datos** — ¿la API devuelve más campos de los que el frontend necesita (ej. hashes de contraseña, datos internos) confiando en que el frontend "no los muestre"?
  - **Consumo de recursos sin restricción** — sin límites de tamaño de página, de payload, de tiempo de ejecución, permitiendo agotar recursos con una sola petición
  - **BFLA** (Broken Function Level Authorization) — endpoints de administrador accesibles por un usuario normal solo porque no aparecen en la interfaz, sin verificación real de rol en el backend
  - **Flujos de negocio sensibles sin protección** — ¿se puede automatizar/abusar un flujo legítimo (comprar todo el stock, aplicar un cupón ilimitadas veces, saltar un paso de aprobación manipulando el request directamente)?
  - **SSRF** — si el backend hace peticiones a URLs que el usuario controla (ej. "URL de tu foto de perfil"), ¿puede apuntar a infraestructura interna?
  - **Inventario de API** — ¿existen versiones viejas o endpoints de prueba/debug todavía accesibles en producción?
  - Documentación de la API que no filtre información sensible de la arquitectura interna
- **Si hay pagos propios**: nunca tocar ni almacenar datos de tarjeta directamente (delegar a proveedor certificado PCI), verificar webhooks de pago con firma
- **Si el proyecto implementa criptografía propia** (cifrado/descifrado o firmas hechas en el código, más allá de simplemente usar HTTPS): "no reinventar la rueda" es la regla de oro — preferir siempre librerías estándar y bien mantenidas del lenguaje sobre implementaciones propias. Verificar específicamente: algoritmo y modo (evitar ECB, evitar algoritmos obsoletos como MD5/SHA1 para integridad), derivación de claves (nunca una contraseña usada directo como clave, usar un KDF como bcrypt/scrypt/Argon2/PBKDF2), manejo de IV/nonce (nunca reutilizado con la misma clave), uso de cifrado autenticado (AES-GCM en vez de AES-CBC sin HMAC), verificación real de firmas (no solo decodificar sin validar), fuente de aleatoriedad (nunca `Math.random()` para nada relacionado con seguridad, usar el generador criptográficamente seguro del lenguaje), y ciclo de vida de las claves (rotación, dónde se guardan, quién tiene acceso)
- **Si hay contenedores (Docker/Kubernetes)**: en el Dockerfile — imagen base con CVEs conocidas (verificar con `trivy image` o `docker scout cves`), usuario `root` por defecto (falta la directiva `USER`), tag `latest` sin fijar versión específica, secretos horneados en las capas de la imagen (visibles con `docker history`, no solo ausentes del Dockerfile final). En Kubernetes, si aplica: políticas de red que segmenten el tráfico entre pods, secretos de Kubernetes (no variables de entorno en el manifiesto plano), RBAC de mínimo privilegio, límites de recursos por pod
- **Si hay app móvil**: almacenamiento seguro de tokens en el dispositivo, certificate pinning si aplica, ofuscación si el código es sensible
- **Si hay VMs propias, infraestructura cloud gestionada directamente, o múltiples cuentas cloud** (distinto de un simple despliegue serverless/estático): IAM (roles y permisos de mínimo privilegio, sin usuarios con acceso total salvo administración real), red (grupos de seguridad/firewalls sin puertos innecesarios abiertos a internet, especialmente bases de datos), almacenamiento (buckets/contenedores de almacenamiento nunca públicos por defecto, verificar explícitamente), logging y monitoreo (¿hay registro de auditoría de quién hizo qué, y por cuánto tiempo se conserva?), gestión de secretos (uso de un secret manager real de la nube, no variables de entorno sueltas en cada VM)
- **Si el dominio envía correos**: SPF/DKIM/DMARC configurados
- **Modo debug y configuración por defecto en producción** (aplica siempre que haya backend o framework con modo desarrollo): verificar que ningún flag de debug del framework quede activo en producción (páginas de error con stack trace completo, panels de depuración accesibles, endpoints de introspección tipo GraphQL playground o Swagger UI abiertos sin protección). Revisar también que ninguna ruta, panel de administración o servicio quede accesible solo porque nunca se cambió su configuración por defecto (credenciales de fábrica, puertos de gestión expuestos, paneles de terceros — ej. un dashboard de base de datos o de cola de mensajes — sin autenticación propia habilitada).
- **Auditoría de dependencias** (siempre que el proyecto tenga un package manager: npm, pip, composer, etc.): ejecutar la herramienta real del ecosistema (`npm audit`, `pip-audit`, `composer audit` o equivalente), no solo revisar visualmente el `package.json`. Reportar vulnerabilidades conocidas (CVEs) con su severidad, distinguiendo "hay una actualización disponible" (mantenimiento normal, no es un hallazgo de seguridad) de "hay una vulnerabilidad conocida explotable" (sí lo es). Verificar también: si `npm audit fix --force` (u equivalente) propone una actualización, revisar el dry-run antes de aplicar — a veces "arregla" un CVE degradando el paquete a una versión antigua, lo cual suele ser peor que el problema original. Riesgos de cadena de suministro adicionales a revisar: scripts `postinstall` que hacen llamadas de red o ejecutan código, paquetes con nombre muy similar a uno popular (typosquatting), que el lockfile esté commiteado y que CI instale desde el lockfile de forma estricta (`npm ci`, no `npm install`; `pip install --require-hashes`)
- **Errores de lógica de negocio** (siempre que haya flujos con dinero, cantidades, permisos o estados que cambian): buscar activamente, no solo en teoría — ¿se puede enviar una cantidad negativa en un carrito o formulario numérico?, ¿se puede saltar un paso de un checkout/aprobación manipulando la URL o el request directamente?, ¿un usuario puede acceder o modificar datos de otro usuario cambiando un ID en la URL sin que el backend verifique la pertenencia (ver BOLA arriba)?, ¿hay límites de negocio (edad mínima, cupos, fechas) que solo se validan en el frontend? Este punto exige pensar como quien intenta abusar del flujo legítimo, no solo buscar errores de sintaxis — es el más fácil de pasar por alto porque el código "funciona bien" en el camino feliz.
- **Prompt injection** (SOLO si el proyecto integra un modelo de IA de cara al usuario — chatbot, asistente, generación de contenido a partir de input del usuario): mapear primero toda la superficie de exposición a IA del proyecto (qué endpoints llaman a un modelo, con qué input, con qué herramientas/permisos tiene ese modelo). Luego verificar: si el input del usuario puede alterar las instrucciones del sistema del modelo (ej. "ignora las instrucciones anteriores y..."); si el modelo puede filtrar su propio prompt de sistema si se le pregunta directamente; que el modelo no tenga acceso directo a acciones sensibles (borrar datos, mover dinero, acceder a otros usuarios) sin una capa de confirmación/permisos separada de lo que el modelo decide — el modelo nunca debe ser la única barrera de autorización; si el proyecto usa RAG o el modelo lee contenido externo (documentos, páginas web, correos), verificar que ese contenido no pueda inyectar instrucciones (prompt injection indirecto, generalmente más peligroso que el directo porque el usuario ni siquiera necesita interactuar mal con el sistema)
- **Cabeceras de seguridad HTTP** (aplica casi siempre que hay un frontend web): CSP, HSTS, X-Content-Type-Options, X-Frame-Options, Referrer-Policy — con la salvedad de que la CSP debe incluir explícitamente cualquier CDN o servicio de terceros que el frontend use, y probarse en staging antes de producción, nunca desplegarse a ciegas directo a un sitio en vivo
- **Gestión de secretos** (aplica siempre que haya al menos una API key): nunca en el repo ni en su historial, siempre como variables de entorno/secret manager de la plataforma. Herramienta concreta recomendada para el escaneo: `gitleaks` (gratuito, funciona sobre el historial completo de git, detecta patrones de credenciales de la mayoría de proveedores conocidos) — más confiable que solo hacer `grep` manual de patrones. Si el proyecto tiene CI/CD (GitHub Actions u otro), considerar agregar el escaneo de secretos como paso automático en cada push, no solo como auditoría puntual una vez.
  - **Si `gitleaks` (u otro escaneo) encuentra una clave filtrada en el historial de git**: no basta con eliminarla del código actual o reescribir el historial — la clave ya estuvo pública en algún momento y debe considerarse comprometida. El paso obligatorio es **rotarla** (generar una nueva credencial en el proveedor y revocar la antigua), no solo ocultarla. Señala esto como hallazgo ⚠️ aunque el archivo ya no contenga la clave en el estado actual del repo.
  - **Secretos en el frontend**: verificar específicamente que ninguna API key, token o credencial con permisos de escritura/lectura sensible quede embebida en código que se sirve al navegador (JS del cliente, variables `NEXT_PUBLIC_`/`VITE_`/similares mal usadas, HTML generado). Cualquier credencial visible en el bundle del cliente debe tratarse como pública — si el proveedor no ofrece una clave de solo-lectura/restringida por dominio para ese uso, la llamada debe pasar por el backend, nunca hacerse directo desde el navegador con la clave completa.
  - **Higiene de logs**: revisar que el código de logging (aplicación, middleware, manejadores de errores) no imprima claves, tokens, contraseñas, cookies de sesión ni cuerpos completos de requests/responses que puedan contener datos sensibles. Prestar atención a mensajes de error no controlados que vuelcan el objeto completo de configuración o el stack trace con variables de entorno incluidas.
- **Acceso de equipo** (si hay más de una persona): 2FA obligatorio en repositorio y plataformas de despliegue, revisión periódica de quién tiene acceso, principio de mínimo privilegio

Descarta explícitamente, con una frase breve de por qué, cualquier categoría que el inventario del Paso 1 no active. Nunca corras un punto "por si acaso" sin conexión al inventario real — eso genera ruido y resta credibilidad a la auditoría, y tampoco omitas una categoría relevante solo porque no aparecía en un proyecto anterior más simple del usuario.

### Herramientas externas: qué hacer si no están instaladas

Varios puntos recomiendan una herramienta concreta (`gitleaks`, `trivy`, `docker scout`, `npm audit`, `pip-audit`). Si la herramienta no está disponible en el entorno, no improvises en silencio:

1. Dilo, y pregunta al usuario si autoriza instalarla **por el gestor de paquetes oficial de su sistema o del ecosistema** (nunca con `curl | bash` ni scripts de repositorios de terceros no verificados).
2. Si el usuario no autoriza la instalación, usa el fallback manual que puedas (revisión de lockfile, `grep` de patrones de credenciales, lectura del Dockerfile) **y declara explícitamente en el reporte que la cobertura de ese punto es parcial**, en la sección "Cobertura de esta auditoría".

Un `grep` manual presentado como si fuera un escaneo completo de secretos es peor que no haberlo hecho: da una falsa sensación de seguridad.

## Paso 3 — Proceso de ejecución (disciplina obligatoria, no negociable)

Sigue siempre esta estructura en 3 fases, sin saltarte ninguna:

### Fase A — Solo diagnóstico

Revisa cada punto seleccionado. Para cada uno, no te quedes en un simple ✅/⚠️/N/A — asigna una **disposición** clara, con severidad y justificación:

- **✅ Resuelto** — ya está bien implementado, sin acción pendiente
- **N/A** — no aplica a este proyecto, con la razón breve de por qué
- **⚠️ Corregir (Fix)** — vulnerabilidad real, se corrige en la Fase B
- **⏸ Diferir (Defer)** — es un riesgo real, pero el usuario decide conscientemente posponerlo (ej. por prioridad de negocio). Requiere: qué riesgo se acepta durante la espera, y cuándo se re-evalúa. Nunca uses esta disposición por tu cuenta — el usuario debe elegirla explícitamente, no es un default cuando algo es difícil de corregir
- **🛡 Riesgo aceptado (Accept Risk)** — el usuario decide no corregirlo, con una razón de negocio válida y, si existe, un control compensatorio (ej. "no hay 2FA en esta cuenta secundaria, pero tiene acceso de solo lectura y IP restringida"). También requiere aprobación explícita del usuario, nunca asumida
- **❌ Falso positivo** — parecía un problema pero, tras investigar, no lo es. Explica por qué (ejemplo típico: rutas que devuelven 200 por el fallback de SPA/CDN de la plataforma de hosting, no porque el archivo exista de verdad)

#### Regla de evidencia (la más importante de esta fase)

**Todo hallazgo ⚠️ debe citar evidencia concreta y verificable**: `archivo:línea`, la salida literal del comando ejecutado, o la petición reproducida con su respuesta. Si no puedes evidenciarlo así, no es un hallazgo: va en una sección aparte como **"sospecha a verificar"**, diciendo qué haría falta para confirmarla.

Esto no es burocracia. El modo de fallo más probable de una auditoría hecha por un modelo no es pasar algo por alto — es **reportar con seguridad una vulnerabilidad que no existe**, porque el patrón "suena" a inseguro. Un hallazgo inventado cuesta más que uno omitido: quema tiempo del usuario, y cuando descubre el primero deja de creerle al resto del reporte. Ante la duda, degrada a sospecha; nunca infles el reporte para que parezca más completo.

#### Severidad: dos ejes, no uno

No colapses todo en "qué tan grave suena". Evalúa por separado y combina:

- **Impacto** — si se explota, ¿qué se pierde? (ejecución de código o acceso total > datos de otros usuarios > datos de un usuario > información de configuración > molestia)
- **Explotabilidad** — ¿qué hace falta para lograrlo? (cualquiera desde internet sin cuenta > cualquier usuario registrado > un usuario con rol específico > requiere acceso interno o una condición poco probable)

| | Explotable por cualquiera | Requiere cuenta/rol | Requiere condiciones poco probables |
|---|---|---|---|
| **Impacto alto** | Crítica | Alta | Media |
| **Impacto medio** | Alta | Media | Baja |
| **Impacto bajo** | Media | Baja | Baja |

Indica siempre los dos ejes en el hallazgo, no solo la etiqueta final — es lo que le permite al usuario discutir tu clasificación en vez de solo aceptarla.

#### Encadenamiento de rutas de ataque

Antes de entregar el reporte, revisa si los hallazgos se combinan entre sí: dos o más hallazgos de severidad media o baja, por separado inofensivos, a veces se combinan en un riesgo crítico (ej. una fuga de información menor que revela un ID interno + un endpoint sin control de autorización que acepta ese ID = acceso no autorizado a datos de otro usuario). Señala explícitamente estas combinaciones si las encuentras, no solo la lista de hallazgos aislados.

#### No apliques el mismo estándar a todo el código por igual

Antes de reportar un hallazgo, verifica si el archivo es: código de pruebas/tests (normalmente no representa riesgo de producción), código de terceros/vendorizado o generado automáticamente (reportar como informativo, no como hallazgo a corregir directamente — la corrección ahí pasa por actualizar la dependencia, no editar el archivo), o código propio de primera parte (aquí sí aplica el rigor completo). No pierdas tiempo señalando patrones "inseguros" dentro de una librería de terceros sin modificar — el hallazgo relevante ahí es la versión de la dependencia (ver auditoría de dependencias), no el patrón en sí.

#### Entregable de la Fase A: el reporte

Escribe el reporte **a disco**, en `security-audit/AUDIT-<YYYY-MM-DD>.md` dentro del proyecto auditado (crea el directorio si no existe), además de resumirlo en la conversación. Esto no es opcional: los modos Rápido y Diff del Paso 1 leen ese archivo, y sin él la siguiente auditoría no tiene contra qué comparar. Si el proyecto es un repositorio git, verifica que ese directorio no quede excluido por `.gitignore` sin que el usuario lo sepa, y pregúntale si prefiere no versionarlo.

Usa siempre esta estructura:

```markdown
# Auditoría de seguridad — <proyecto> — <YYYY-MM-DD>

**Modo:** Completo | Rápido | Diff | Enfocado
**Auditoría previa:** <ruta del reporte anterior, o "ninguna">

## Resumen ejecutivo
3-5 líneas: postura general, conteo de hallazgos por severidad, y lo único
que hay que arreglar hoy si solo se pudiera arreglar una cosa.

## Inventario detectado
| Componente | ¿Presente? | Detalle |
|---|---|---|
(una fila por cada uno de los 14 puntos del Paso 1)

## Hallazgos
(ordenados de mayor a menor severidad)

### [Crítica] Título corto del hallazgo
- **Disposición:** ⚠️ Corregir
- **Impacto / Explotabilidad:** <alto/medio/bajo> / <por cualquiera / con cuenta / condiciones poco probables>
- **Evidencia:** `ruta/archivo.js:42` — o la salida literal del comando
- **Qué permite hacer:** descripción concreta del abuso, no la categoría genérica
- **Corrección propuesta:** el cambio mínimo que lo resuelve
- **Marco de referencia:** OWASP API Top 10 A01 / OWASP Top 10 A03 / CVE-XXXX-XXXX (si aplica)

## Rutas de ataque encadenadas
(combinaciones de hallazgos menores que juntos dan un riesgo mayor; omitir la sección si no hay)

## Sospechas a verificar
(lo que no se pudo evidenciar, y qué haría falta para confirmarlo)

## Falsos positivos descartados
(lo que parecía un problema y no lo era, con la razón)

## Categorías descartadas (N/A)
(una línea por categoría no activada por el inventario, con el motivo)

## Cobertura de esta auditoría
- Herramientas ejecutadas: <cuáles, con qué versión/comando>
- Herramientas NO disponibles y su impacto en la cobertura: <cuáles>
- Qué NO se revisó y por qué (ej. infraestructura sin acceso, código no disponible)
```

La sección "Cobertura" es tan importante como los hallazgos: un reporte que no dice qué **no** miró se lee como si lo hubiera mirado todo.

#### No corrijas nada todavía en esta fase

Entrega el reporte completo con estas disposiciones y espera aprobación explícita del usuario antes de continuar — en particular, cualquier disposición "Diferir" o "Riesgo aceptado" requiere que el usuario la elija él mismo, nunca que tú la asumas para evitarte el trabajo de corregir algo difícil.

**Si la ejecución no es interactiva** (CI, agente autónomo, o cualquier contexto sin un humano que pueda aprobar): no te quedes esperando ni asumas la aprobación. Termina en la Fase A, entrega el reporte escrito, y deja constancia de que las Fases B y C quedan pendientes de aprobación humana.

### Fase B — Corrección (solo tras aprobación)

Corrige únicamente los puntos marcados ⚠️. Si una corrección requiere una decisión de negocio del usuario (ej. cuántos envíos por hora permitir, qué política DMARC usar), pregunta antes de decidir por tu cuenta — nunca asumas un valor arbitrario en su nombre.

Para cambios de alto riesgo de romper el sitio (especialmente CSP), prueba primero en un entorno local/staging, no directo en producción. Muestra al usuario la política/cambio exacto antes de desplegarlo.

### Fase C — Verificación final (una sola ronda)

Después de aplicar las correcciones, revisa los mismos puntos **una vez** y confirma el estado final de cada uno. No repitas este ciclo de verificación de forma indefinida — si algo sigue sin resolverse después de esta segunda revisión, repórtalo al usuario para que decida cómo proceder, en vez de seguir intentando arreglarlo solo.

Actualiza el reporte en `security-audit/` con el estado final de cada punto, para que la siguiente auditoría parta de ahí.

## Principio general

Si en cualquier punto de la auditoría encuentras que un mecanismo de corrección no está teniendo efecto (por ejemplo, un archivo de configuración de redirección que no se aplica, un fix que parece correcto en el código pero no se refleja en producción), **no reintentes el mismo mecanismo una tercera vez** — repórtalo al usuario y propón un mecanismo alternativo. Esto ocurre en la práctica con reglas de redirección declarativas que algunas plataformas de hosting no aplican como documentan, y perseverar con el mismo enfoque fallido desperdicia tiempo sin resultado.

Nunca instales ni ejecutes scripts de instalación (`curl | bash`, `install.sh`) de repositorios de terceros no verificados como parte de esta auditoría. Esta skill está diseñada para funcionar sin dependencias externas de ese tipo — toda la revisión se hace leyendo y probando el código del propio proyecto.

Esta skill es exclusivamente defensiva: diagnóstico y corrección de vulnerabilidades en proyectos propios del usuario. No incluye ni debe usarse para técnicas ofensivas, pentesting no autorizado, ni pruebas contra sistemas que no le pertenezcan al usuario.

## Referencias

Algunas categorías de esta skill se alinean deliberadamente con marcos y estándares reconocidos de la industria, en vez de usar criterios inventados — cuando corresponda, cita el marco relevante en el reporte final:
- OWASP API Security Top 10 (autorización, exposición de datos, límites de recursos, SSRF, flujos de negocio)
- OWASP Top 10 general (para vulnerabilidades web clásicas: inyección, XSS, configuración incorrecta, etc.)
- OWASP Cheat Sheet Series (referencia práctica para CSRF, XSS, subida de archivos y manejo de sesiones)
- Principios estándar de criptografía aplicada (preferir librerías establecidas, nunca implementaciones propias de primitivas criptográficas)
- GitHub Advisory Database / NVD (National Vulnerability Database) para CVEs de dependencias
