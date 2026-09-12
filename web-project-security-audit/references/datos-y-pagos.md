# Base de datos, almacenamiento y pagos

Aplica si el inventario detectó **base de datos**, **almacenamiento de archivos** o
**procesamiento de pagos**.

## Base de datos

- **Control de acceso a nivel de fila o documento** — especialmente en multi-tenant y
  en plataformas donde el cliente habla directo con la base (Supabase, Firebase): ahí
  las reglas de seguridad *son* el control de acceso, y una regla permisiva equivale a
  exponer la tabla entera. Verificarlas explícitamente, no asumir que existen.
- **Encriptación en reposo** de datos sensibles, y de los backups.
- **Backups**: ¿existen, se prueba su restauración, y quién puede restaurarlos? Un
  backup que nadie ha restaurado nunca no es un backup verificado.
- **Mínimo privilegio en las credenciales de conexión** — la app no necesita permisos
  de `DROP`, ni de crear usuarios. Credenciales distintas para migraciones y para
  runtime.
- **Exposición de red** — la base de datos nunca accesible directamente desde internet.

## Almacenamiento de archivos

Buckets y contenedores nunca públicos por defecto: verificarlo explícitamente en la
consola o por API, no dar por hecho lo que dice el código de despliegue. Revisar URLs
firmadas con caducidad razonable en vez de objetos públicos permanentes.

## Pagos

- **Nunca tocar ni almacenar datos de tarjeta directamente.** Delegar a un proveedor
  certificado PCI y usar sus componentes de captura (el dato no debe pasar por el
  servidor propio). Si el proyecto sí toca datos de tarjeta, eso por sí solo es un
  hallazgo de severidad alta y una carga de cumplimiento que el usuario probablemente
  no quiere.
- **Verificar los webhooks de pago con firma.** Un webhook de confirmación sin
  verificación de firma permite a cualquiera marcar un pedido como pagado.
- **Recalcular el importe en el servidor** contra el catálogo, nunca confiar en el
  total que envía el cliente.
- **Idempotencia** en la creación de cargos, para que un reintento no cobre dos veces.
