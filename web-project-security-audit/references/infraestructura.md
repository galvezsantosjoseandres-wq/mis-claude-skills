# Contenedores, Kubernetes e infraestructura cloud

Aplica si el inventario detectó **contenedores**, **Kubernetes**, **VMs propias**,
**infraestructura cloud gestionada directamente** o **múltiples cuentas cloud**. No
aplica a un despliegue serverless o estático simple sobre una plataforma gestionada.

Contenido: Docker · Kubernetes · IAM · red · almacenamiento · logging · secretos

## Docker

- **Imagen base con CVEs conocidas** — verificar con `trivy image` o `docker scout cves`,
  no a ojo.
- **Usuario `root` por defecto** — falta la directiva `USER`. Un contenedor que corre
  como root convierte un escape de la aplicación en un problema mayor.
- **Tag `latest`** sin fijar versión específica: el despliegue deja de ser reproducible
  y una actualización upstream puede introducir una regresión de seguridad sin aviso.
- **Secretos horneados en las capas de la imagen** — visibles con `docker history`
  aunque no aparezcan en el Dockerfile final. Un `COPY .env` seguido de `RUN rm .env`
  deja el secreto en la capa intermedia.
- Multi-stage build para no publicar el toolchain de compilación en la imagen final.

## Kubernetes

- **Políticas de red** que segmenten el tráfico entre pods: por defecto todos los pods
  se hablan entre sí.
- **Secretos de Kubernetes**, no variables de entorno en el manifiesto plano
  versionado. Recordar que los Secrets son base64, no cifrados, salvo que se habilite
  cifrado en reposo en etcd.
- **RBAC de mínimo privilegio** — sin ServiceAccounts con `cluster-admin`.
- **Límites de recursos por pod**, para que un pod comprometido o defectuoso no agote
  el nodo.
- `securityContext`: sin privilegios, sin escalada, filesystem de solo lectura donde se
  pueda.

## IAM

Roles y permisos de mínimo privilegio, sin usuarios con acceso total salvo para
administración real. Preferir roles asumibles por el servicio a claves de acceso
estáticas de larga vida. Revisar en particular los permisos comodín (`*`) en políticas.

## Red

Grupos de seguridad y firewalls sin puertos innecesarios abiertos a internet,
**especialmente bases de datos, paneles de administración y puertos de gestión**
(SSH, RDP, 6379, 5432, 27017). Preferir acceso por bastión o túnel a exponer el puerto.

## Almacenamiento

Buckets y contenedores nunca públicos por defecto: verificarlo explícitamente. Es uno
de los fallos más frecuentes y más fáciles de comprobar.

## Logging y monitoreo

¿Hay registro de auditoría de quién hizo qué, por cuánto tiempo se conserva, y está
protegido contra borrado por quien tiene acceso? Sin auditoría, la categoría "repudio"
de STRIDE queda sin respuesta: no se puede reconstruir un incidente.

## Gestión de secretos en infraestructura

Uso de un secret manager real de la nube, no variables de entorno sueltas configuradas
a mano en cada VM o en la consola. Rotación definida y acceso auditable.

## Infraestructura como código

Si hay Terraform, CloudFormation o Pulumi: revisar el estado remoto (puede contener
secretos en claro y debe estar cifrado y con acceso restringido), y que los recursos
sensibles no estén definidos con permisos abiertos "temporalmente". Herramientas de
análisis estático como `checkov` o `tfsec` aplican aquí si están disponibles.
