# Integración de modelos de IA: prompt injection

Aplica **solo** si el proyecto integra un modelo de IA de cara al usuario: chatbot,
asistente, generación de contenido a partir de input del usuario, o un agente con
herramientas.

## Primero: mapear la superficie

Antes de buscar vulnerabilidades, levantar el mapa: qué endpoints llaman a un modelo,
con qué input, con qué instrucciones de sistema, y **con qué herramientas y permisos
cuenta ese modelo**. Sin ese mapa, el resto de la revisión es teórica.

## Prompt injection directo

- ¿El input del usuario puede alterar las instrucciones del sistema del modelo (el
  clásico "ignora las instrucciones anteriores y...")?
- ¿El modelo filtra su propio prompt de sistema si se le pregunta directamente? Si el
  prompt contiene lógica de negocio, precios o reglas internas, eso es fuga de información.

## Prompt injection indirecto (el más peligroso)

Si el proyecto usa RAG o el modelo lee contenido externo —documentos subidos, páginas
web, correos, tickets, resultados de búsqueda— verificar que ese contenido no pueda
inyectar instrucciones. Es más grave que el directo porque **el usuario legítimo ni
siquiera necesita interactuar mal con el sistema**: basta con que el atacante coloque
el texto donde el modelo lo va a leer.

## La regla que más importa

**El modelo nunca debe ser la única barrera de autorización.** Si el modelo puede
disparar acciones sensibles —borrar datos, mover dinero, enviar correos, acceder a
datos de otros usuarios, ejecutar código— debe existir una capa de permisos y
confirmación **fuera** de lo que el modelo decide, que valide contra la identidad real
del usuario de la sesión.

Formulado como pregunta para el reporte: si un atacante controlara completamente la
salida del modelo, ¿qué podría hacer? Todo lo que esté en esa respuesta necesita un
control externo al modelo.

## Otros puntos

- **Límites de consumo** por usuario: una integración de IA sin cuota es una factura
  abierta, y el coste es un riesgo real aunque no sea una brecha de datos.
- **La clave de API del proveedor nunca en el cliente** — las llamadas al modelo pasan
  por el backend (ver la sección de gestión de secretos en SKILL.md).
- **Registro** de las conversaciones: cuidado con guardar datos sensibles que el
  usuario pegó en el chat, y con enviarlos a un tercero sin avisar.
