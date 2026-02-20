# Funcionalidades de GESTAR IA

## Funcionalidades actuales

- Chat IA para carga de tickets (Gemini + reglas).
- Detección de intención (`social`, `crear_ticket`, `desconocido`).
- Borrador de ticket en sesión con revisión antes de crear.
- Confirmación de creación por texto (`si`, `crear`, `ok`, etc.).
- Flujo de borrador con acciones `Editar` y `Cancelar carga`.
- En edición de borrador: `Crear ticket`, `Agregar información`, `Cancelar carga`.
- Parsing de fecha en lenguaje natural (`hoy`, `mañana`, etc.).
- Resolución de responsable sugerido contra usuarios de base.
- Sinónimos para responsable (`responsable`, `encargado`, `a cargo`, `sugerido`).
- Modo formulario (alta de ticket) con campos maestros.
- Bandeja y edición de tickets con filtros.
- Edición de ticket existente (estado, prioridad, asignado, etc.).
- Gestión de subtareas (crear, editar, eliminar).
- Seguimiento/comentarios (logs de cambios).
- Carga y refresco de datos maestros.
- UI con tema claro/oscuro (paleta tokenizada en curso de ajuste).
- Manejo de conexión Azure SQL con reintentos y fallback de sesión.
- Indicadores de estado SQL y botón de reintento/refresco.

## Funcionalidades a implementar

- Login con Azure Entra ID.
- Lista personalizada: `MIS TICKETS`.
- Lista personalizada: `MIS TAREAS`.
- Dashboard personal:
  - Cantidad de tareas.
  - Pendientes.
  - En progreso.
  - Carga de trabajo por fecha de vencimiento.
- Vista personalizada: `MI DIA`:
  - Seleccionar 3 tareas importantes del día.
  - Organizarlas.
  - Hacer seguimiento.
- Funcionalidades por rol:
  - Solicitante.
  - Usuario.
  - Jefe de Área.
  - Director.
  - Administrador.
- Adjuntos por ticket.
- Migrar chat a WhatsApp.
- Agrupar tickets por proyectos.
- Notificación por email cuando se asigna ticket/subtarea.
- Mecanismo robusto de notificaciones (Outbox + worker o Logic App/Function).
- Ajustes finales de contraste y consistencia visual en modo oscuro.
- Fortalecer reglas de enriquecimiento de descripción en chat.
- Pruebas automáticas para flujos críticos (chat, creación, edición, subtareas).
- Ordenamiento arquitectónico progresivo (separación UI, negocio y datos).

