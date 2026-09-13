---
name: web-project-security-audit
description: Realiza una auditoría de seguridad de CUALQUIER proyecto de software (sitio estático, app con backend y base de datos, sistema con login, microservicios, apps móviles, infraestructura cloud compleja), construyendo el checklist dinámicamente según lo que el proyecto realmente tenga, sin asumir un stack fijo. Úsala siempre que el usuario pida "revisar seguridad", "auditoría de seguridad", "hay vulnerabilidades", "está seguro mi sitio/app/backend", antes de un lanzamiento o despliegue a producción, o al preparar un nuevo proyecto para un cliente — sin importar la escala del proyecto. Audita el proyecto COMPLETO; si el usuario solo quiere revisar los cambios pendientes de una rama o PR, esa es una revisión de diff, no esta skill. Primero recopila el inventario real de componentes del proyecto (no asumas un stack previo, incluso si proyectos anteriores del usuario eran más simples) antes de decidir qué categorías de seguridad aplican.
---

# Auditoría de seguridad — checklist construido dinámicamente según el proyecto real

Esta skill NO asume ningún stack por defecto. Sirve igual para un sitio estático de una página como para un backend con microservicios, base de datos, autenticación, colas de mensajes, e infraestructura cloud. El objetivo es evitar dos extremos: aplicar un checklist gigante de seguridad empresarial a un proyecto simple (sobre-ingeniería), o aplicar un checklist mínimo a un proyecto que ya creció en complejidad (bajo-ingeniería, el riesgo real conforme el usuario escale).

**Regla central: nunca reutilices el resultado del inventario de un proyecto anterior.** Cada vez que se invoque esta skill, se repite el Paso 1 desde cero — un proyecto nuevo, o el mismo proyecto meses después, puede tener un inventario de componentes completamente distinto al de la última vez.

El detalle de cada dominio vive en `references/`. El Paso 2 dice cuál abrir según lo que el inventario encuentre: así un sitio estático no arrastra el checklist de Kubernetes, y un backend complejo recibe más profundidad de la que cabría en un solo archivo.

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
15. **CI/CD**: ¿hay pipelines automáticos (GitHub Actions, GitLab CI, Jenkins)? ¿se disparan con PRs de terceros? ¿tienen secretos de despliegue?

Si el proyecto es tan simple que muchas de estas preguntas no aplican (por ejemplo, un sitio estático de una página), está perfectamente bien que la mayoría de categorías se descarten — el inventario corto es un resultado legítimo, no un fallo del proceso. Lo que no es aceptable es saltarse el inventario y asumir la respuesta.

**Mapeo de fronteras de confianza (para proyectos con más de un componente):** identifica cada punto donde los datos cruzan de un nivel de confianza a otro — usuario→servidor, servidor→base de datos, servidor→servicio de terceros, proceso sin privilegios→proceso con privilegios. Para cada frontera, considera brevemente las 6 categorías de amenaza de STRIDE: **S**uplantación de identidad, **T**ampering/alteración de datos en tránsito, **R**epudio (¿se puede negar una acción por falta de registro/auditoría?), **I**nformación divulgada indebidamente, **D**enegación de servicio, **E**levación de privilegios. No hace falta un documento formal para un proyecto simple — es un chequeo mental de "¿qué podría salir mal cruzando esta frontera?" antes de pasar al Paso 2.

### Alcance de esta ejecución en particular

No toda invocación de esta skill necesita ser una auditoría completa desde cero. **Antes de decidir el modo, busca auditorías previas en `security-audit/` dentro del proyecto** (ver Paso 3, Fase A): los modos Rápido y Diff dependen de ese reporte y, si no existe ninguno, el único modo posible es Completo.

- **Completo** — inventario y checklist desde cero (el default, y obligatorio la primera vez que se audita un proyecto o si no hay reporte previo en `security-audit/`)
- **Rápido** — repetir solo los puntos que en el último reporte quedaron ⚠️, ⏸ o 🛡, sin rehacer el inventario entero
- **Diff/PR** — el usuario solo agregó o cambió código puntual (una función nueva, un endpoint) desde la última auditoría completa; enfócate en si ese cambio introduce riesgo nuevo o afecta hallazgos previos, no en repetir todo el proyecto
- **Enfocado** — el usuario pide revisar solo una categoría específica (ej. "revisa solo las dependencias")

Aclara con el usuario cuál modo aplica si no es obvio por el contexto de la petición. Si pide un modo acotado, respétalo: entregar una auditoría completa cuando pidieron una categoría es desperdiciar su tiempo y el tuyo.

## Paso 2 — Construir el checklist específico de este proyecto

### Tabla de ruteo: qué abrir según el inventario

Cada fila que el inventario active corresponde a un archivo de `references/`. **Léelo antes de auditar esa categoría.** No es opcional ni un "por si acaso": el archivo contiene las clases de vulnerabilidad concretas, los antipatrones específicos y los falsos positivos típicos de ese dominio. Auditar de memoria produce el checklist genérico que esta skill existe para evitar — detecta lo obvio y pasa por alto justo lo que distingue una auditoría útil de una superficial.

| Si el inventario detectó… | Lee |
|---|---|
| Cualquier endpoint con input externo: formulario, API, webhook, parámetro de URL, **subida de archivos** | `references/entrada-externa.md` |
| Login de usuarios (propio, OAuth, SSO), sesiones o JWT | `references/autenticacion-y-sesiones.md` |
| APIs propias expuestas, **o cualquier flujo con dinero, cantidades, permisos o estados** | `references/apis-y-logica-de-negocio.md` |
| Base de datos, almacenamiento de archivos, o pagos | `references/datos-y-pagos.md` |
| Cifrado, descifrado o firmas implementados en el código del proyecto | `references/criptografia.md` |
| Contenedores, Kubernetes, VMs propias, IaC o múltiples cuentas cloud | `references/infraestructura.md` |
| Un modelo de IA de cara al usuario: chatbot, asistente, RAG, agente con herramientas | `references/ia-y-prompt-injection.md` |
| Pipelines de CI/CD: GitHub Actions, GitLab CI, Jenkins, cualquier automatización disparada por push, PR o comentario | `references/cicd-security.md` |

Puedes leer varios. Si dudas entre leer uno o no, léelo: el coste de abrir un archivo de más es trivial comparado con el de omitir una clase de vulnerabilidad que sí aplicaba.

**Si el inventario no activa ninguna fila**, el proyecto es simple y eso es un resultado legítimo: pasa directo a los bloques transversales de abajo y cierra la auditoría ahí.

### Bloques transversales (revisar sin necesidad de abrir un archivo)

Estos aplican a casi cualquier proyecto y son lo bastante compactos para vivir aquí:

- **Gestión de secretos** (siempre que haya al menos una API key): nunca en el repo ni en su historial, siempre como variables de entorno/secret manager de la plataforma. Para el escaneo, en este orden:
  1. `gitleaks` si está disponible — es lo único que cubre el **historial completo de git**, que es donde vive el riesgo real.
  2. Si no lo está, ejecuta el escáner incluido: `python3 <ruta-de-esta-skill>/scripts/escanear_secretos.py <proyecto>`. Solo stdlib, sin red, sin instalar nada; 56 patrones de proveedores conocidos y salida JSON. Redacta los valores: nunca imprime un secreto completo, conserva solo el prefijo que identifica al proveedor. Su campo `contexto` (`primera-parte` / `test` / `vendorizado`) alimenta directamente la regla de triaje de la Fase A.
  3. Solo si ninguno está disponible, `grep` manual — y entonces declara la cobertura como parcial.

  Ninguna de las dos primeras cubre el historial salvo `gitleaks`: si usas el escáner incluido, dilo en "Cobertura" y recomienda pasar `gitleaks detect --log-opts="--all"` antes de un lanzamiento. Si el proyecto tiene CI/CD, considerar agregar el escaneo como paso automático en cada push, no solo como auditoría puntual.
  - **Si el escaneo encuentra una clave filtrada en el historial de git**: no basta con eliminarla del código actual ni con reescribir el historial — la clave ya estuvo pública en algún momento y debe considerarse comprometida. El paso obligatorio es **rotarla** (generar una nueva credencial en el proveedor y revocar la antigua). Señálalo como hallazgo ⚠️ aunque el archivo ya no contenga la clave en el estado actual del repo.
  - **Secretos en el frontend**: verificar que ninguna API key, token o credencial con permisos de escritura o de lectura sensible quede embebida en código que se sirve al navegador (JS del cliente, variables `NEXT_PUBLIC_`/`VITE_`/similares mal usadas, HTML generado). Cualquier credencial visible en el bundle del cliente **es pública** — si el proveedor no ofrece una clave de solo-lectura restringida por dominio para ese uso, la llamada debe pasar por el backend.
  - **Higiene de logs**: que el código de logging (aplicación, middleware, manejadores de errores) no imprima claves, tokens, contraseñas, cookies de sesión ni cuerpos completos de requests/responses. Atención a los errores no controlados que vuelcan el objeto de configuración completo o un stack trace con variables de entorno.
- **Auditoría de dependencias** (siempre que haya un package manager): ejecutar la herramienta real del ecosistema (`npm audit`, `pip-audit`, `composer audit` o equivalente), no revisar el manifiesto a ojo. Distinguir "hay una actualización disponible" (mantenimiento normal, no es un hallazgo de seguridad) de "hay una vulnerabilidad conocida explotable" (sí lo es). Si `npm audit fix --force` u equivalente propone una actualización, revisar el dry-run antes de aplicar: a veces "arregla" un CVE degradando el paquete a una versión antigua, lo cual suele ser peor que el problema original. Riesgos de cadena de suministro: scripts `postinstall` que hacen llamadas de red o ejecutan código, paquetes con nombre muy similar a uno popular (typosquatting), lockfile commiteado, y CI instalando desde el lockfile de forma estricta (`npm ci`, no `npm install`; `pip install --require-hashes`).
- **Cabeceras de seguridad HTTP** (casi siempre que hay un frontend web): CSP, HSTS, X-Content-Type-Options, X-Frame-Options, Referrer-Policy. La CSP debe incluir explícitamente cualquier CDN o servicio de terceros que el frontend use, y probarse en staging antes de producción — nunca desplegarse a ciegas a un sitio en vivo.
- **Modo debug y configuración por defecto en producción** (siempre que haya backend o framework con modo desarrollo): ningún flag de debug activo en producción (páginas de error con stack trace completo, panels de depuración accesibles, endpoints de introspección tipo GraphQL playground o Swagger UI abiertos sin protección). Ninguna ruta, panel de administración o servicio accesible solo porque nunca se cambió su configuración por defecto: credenciales de fábrica, puertos de gestión expuestos, paneles de terceros (un dashboard de base de datos o de cola de mensajes) sin autenticación propia.
- **Correo saliente** (si el dominio envía correos): SPF, DKIM y DMARC configurados. Sin ellos, cualquiera puede suplantar el dominio.
- **App móvil** (si existe): almacenamiento seguro de tokens en el dispositivo (Keychain/Keystore, no preferencias en claro), certificate pinning si el riesgo lo justifica, y ninguna clave sensible embebida en el binario — un APK o IPA se descompila trivialmente.
- **Acceso de equipo** (si hay más de una persona): 2FA obligatorio en repositorio y plataformas de despliegue, revisión periódica de quién tiene acceso, mínimo privilegio. En un proyecto de un solo desarrollador esto se reduce a 2FA en su propia cuenta; no lo infles.

Descarta explícitamente, con una frase breve de por qué, cualquier categoría que el inventario del Paso 1 no active. Nunca corras un punto "por si acaso" sin conexión al inventario real — eso genera ruido y resta credibilidad a la auditoría. Y tampoco omitas una categoría relevante solo porque no aparecía en un proyecto anterior más simple del usuario.

### Herramientas externas: qué hacer si no están instaladas

Varios puntos recomiendan una herramienta concreta (`gitleaks`, `trivy`, `docker scout`, `npm audit`, `pip-audit`). Si no está disponible en el entorno, no improvises en silencio:

1. Dilo, y pregunta al usuario si autoriza instalarla **por el gestor de paquetes oficial de su sistema o del ecosistema** (nunca con `curl | bash` ni scripts de repositorios de terceros no verificados).
2. Si no autoriza la instalación, usa el fallback manual que puedas (revisión de lockfile, `grep` de patrones de credenciales, lectura del Dockerfile) **y declara explícitamente en el reporte que la cobertura de ese punto es parcial**, en la sección "Cobertura de esta auditoría".

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

Antes de reportar un hallazgo, verifica de qué tipo de archivo se trata:

- **Código de pruebas/tests** — normalmente no representa riesgo de producción. Una credencial ficticia en una suite de pruebas no es una fuga de secretos; si la mencionas, márcala explícitamente como tal.
- **Código de terceros, vendorizado o generado automáticamente** — reportar como informativo, no como hallazgo a corregir editando el archivo: la corrección ahí pasa por actualizar o sustituir la dependencia. No pierdas tiempo señalando patrones "inseguros" dentro de una librería sin modificar; el hallazgo relevante es la versión de la dependencia.
- **Código propio de primera parte** — aquí sí aplica el rigor completo.

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
(una fila por cada uno de los 15 puntos del Paso 1)

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
