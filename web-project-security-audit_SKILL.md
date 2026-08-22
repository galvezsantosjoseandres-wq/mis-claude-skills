---
name: web-project-security-audit
description: Realiza una auditoría de seguridad de CUALQUIER proyecto de software (sitio estático, app con backend y base de datos, sistema con login, microservicios, apps móviles, infraestructura cloud compleja), construyendo el checklist dinámicamente según lo que el proyecto realmente tenga, sin asumir un stack fijo. Úsala siempre que el usuario pida "revisar seguridad", "auditoría de seguridad", "hay vulnerabilidades", "está seguro mi sitio/app/backend", antes de un lanzamiento o despliegue a producción, o al preparar un nuevo proyecto para un cliente — sin importar la escala o complejidad del proyecto. Primero recopila el inventario real de componentes del proyecto (no asumas un stack previo, incluso si proyectos anteriores del usuario eran más simples) antes de decidir qué categorías de seguridad aplican.
---

# Auditoría de seguridad — checklist construido dinámicamente según el proyecto real

Esta skill NO asume ningún stack por defecto. Sirve igual para un sitio estático de una página como para un backend con microservicios, base de datos, autenticación, colas de mensajes, e infraestructura cloud. El objetivo es evitar dos extremos: aplicar un checklist gigante de seguridad empresarial a un proyecto simple (sobre-ingeniería), o aplicar un checklist mínimo a un proyecto que ya creció en complejidad (bajo-ingeniería, el riesgo real conforme el usuario escale).

**Regla central: nunca reutilices el resultado del inventario de un proyecto anterior.** Cada vez que se invoque esta skill, se repite el Paso 1 desde cero — un proyecto nuevo, o el mismo proyecto meses después, puede tener un inventario de componentes completamente distinto al de la última vez.

## Paso 1 — Inventario de componentes (obligatorio, siempre desde cero)

No preguntes "¿qué stack usas?" de forma genérica — investiga o pregunta punto por punto, porque cada respuesta activa o descarta categorías enteras del checklist:

1. **Hosting/infraestructura**: ¿estático, serverless, contenedores, VMs propias, Kubernetes, multi-cloud?
2. **Backend**: ¿existe? ¿monolito o microservicios? ¿qué lenguaje/framework?
3. **Base de datos**: ¿cuál(es)? ¿relacional, documental, cache (Redis), vector? ¿multi-tenant?
4. **Autenticación**: ¿hay login de usuarios? ¿propio, OAuth de terceros, SSO empresarial? ¿roles/permisos distintos por usuario?
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

## Paso 2 — Construir el checklist específico de este proyecto

A partir del inventario, arma la lista de puntos a auditar. No copies una plantilla fija — cada categoría del inventario activa un bloque de preguntas de seguridad relacionado. Algunos bloques de referencia (no exhaustivo, usa criterio para añadir lo que el inventario sugiera que falta):

- **Si hay cualquier endpoint que reciba input externo** (formulario, API, webhook): inyección (SQL/NoSQL/comandos/CRLF), sanitización, validación server-side, límites de tamaño/longitud, rate limiting, CORS
- **Si hay base de datos**: control de acceso a nivel de fila o documento, encriptación en reposo de datos sensibles, backups y quién puede restaurarlos, principio de mínimo privilegio en credenciales de conexión
- **Si hay autenticación**: hashing de contraseñas (nunca texto plano ni cifrado reversible), expiración y renovación de sesión/token, protección contra fuerza bruta, 2FA disponible u obligatorio, gestión de roles y permisos
- **Si hay APIs propias expuestas**: autenticación de cada endpoint, versionado, límites de uso por cliente/API key, documentación que no filtre información sensible de la arquitectura
- **Si hay pagos propios**: nunca tocar ni almacenar datos de tarjeta directamente (delegar a proveedor certificado PCI), verificar webhooks de pago con firma
- **Si hay contenedores/IaC**: imágenes base actualizadas sin vulnerabilidades conocidas, secretos nunca en el Dockerfile o el código de infraestructura, permisos IAM de mínimo privilegio, red segmentada
- **Si hay app móvil**: almacenamiento seguro de tokens en el dispositivo, certificate pinning si aplica, ofuscación si el código es sensible
- **Si el dominio envía correos**: SPF/DKIM/DMARC configurados
- **Cabeceras de seguridad HTTP** (aplica casi siempre que hay un frontend web): CSP, HSTS, X-Content-Type-Options, X-Frame-Options, Referrer-Policy — con la salvedad de que la CSP debe incluir explícitamente cualquier CDN o servicio de terceros que el frontend use, y probarse en staging antes de producción, nunca desplegarse a ciegas directo a un sitio en vivo
- **Gestión de secretos** (aplica siempre que haya al menos una API key): nunca en el repo ni en su historial, siempre como variables de entorno/secret manager de la plataforma
- **Acceso de equipo** (si hay más de una persona): 2FA obligatorio en repositorio y plataformas de despliegue, revisión periódica de quién tiene acceso, principio de mínimo privilegio

Descarta explícitamente, con una frase breve de por qué, cualquier categoría que el inventario del Paso 1 no active. Nunca corras un punto "por si acaso" sin conexión al inventario real — eso genera ruido y resta credibilidad a la auditoría, y tampoco omitas una categoría relevante solo porque no aparecía en un proyecto anterior más simple del usuario.

## Paso 3 — Proceso de ejecución (disciplina obligatoria, no negociable)

Sigue siempre esta estructura en 3 fases, sin saltarte ninguna:

### Fase A — Solo diagnóstico
Revisa cada punto seleccionado y repórtalo como: ✅ Resuelto / ⚠️ Vulnerable / N/A No aplica (con razón breve). **No corrijas nada todavía.** Entrega el reporte completo al usuario y espera su aprobación explícita antes de continuar.

### Fase B — Corrección (solo tras aprobación)
Corrige únicamente los puntos marcados ⚠️. Si una corrección requiere una decisión de negocio del usuario (ej. cuántos envíos por hora permitir, qué política DMARC usar), pregunta antes de decidir por tu cuenta — nunca asumas un valor arbitrario en su nombre.

Para cambios de alto riesgo de romper el sitio (especialmente CSP), prueba primero en un entorno local/staging, no directo en producción. Muestra al usuario la política/cambio exacto antes de desplegarlo.

### Fase C — Verificación final (una sola ronda)
Después de aplicar las correcciones, revisa los mismos puntos **una vez** y confirma el estado final de cada uno. No repitas este ciclo de verificación de forma indefinida — si algo sigue sin resolverse después de esta segunda revisión, repórtalo al usuario para que decida cómo proceder, en vez de seguir intentando arreglarlo solo.

## Principio general

Si en cualquier punto de la auditoría encuentras que un mecanismo de corrección no está teniendo efecto (por ejemplo, un archivo de configuración de redirección que no se aplica, un fix que parece correcto en el código pero no se refleja en producción), **no reintentes el mismo mecanismo una tercera vez** — repórtalo al usuario y propone un mecanismo alternativo. Esto ya ha ocurrido en la práctica (reglas de `_redirects` que no toman efecto en algunas plataformas) y perseverar con el mismo enfoque fallido desperdicia tiempo sin resultado.

Nunca instales ni ejecutes scripts de instalación (`curl | bash`, `install.sh`) de repositorios de terceros no verificados como parte de esta auditoría. Esta skill está diseñada para funcionar sin dependencias externas de ese tipo — toda la revisión se hace leyendo y probando el código del propio proyecto.

Esta skill es exclusivamente defensiva: diagnóstico y corrección de vulnerabilidades en proyectos propios del usuario. No incluye ni debe usarse para técnicas ofensivas, pentesting no autorizado, ni pruebas contra sistemas que no le pertenezcan al usuario.
