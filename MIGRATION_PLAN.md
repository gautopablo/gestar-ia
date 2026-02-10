# MIGRATION_PLAN.md

## Contexto y Alcance
- Proyecto legacy (referencia UX/funcional): `C:\Users\GAUTOP\OneDrive - TARANTO SAN JUAN SA\Documentos\PROYECTOS APP\Tickets\gestar`
- Proyecto target (implementación real): `C:\Users\GAUTOP\OneDrive - TARANTO SAN JUAN SA\Documentos\PROYECTOS APP\gestar-ia`
- Regla central: el modelo de datos válido es el del target (Azure SQL, esquema `gestar`).
- Esta fase es solo inventario + mapeo. No incluye implementación funcional de Modo Formulario.

## Fase 0A - Inventario Legacy

### Pantallas / Flujos identificados
Archivo principal: `app_v2.py` (con `db.py` y `models.py`).

1. Inicio / selector de usuario simulado.
2. Crear ticket completo (`show_create_ticket`).
3. Crear solicitud simple (`show_simple_request`).
4. Bandeja de tickets (`show_ticket_tray`) con tabs:
- Todos
- En cola (`estado = NUEVO`)
- Mis asignados (`responsable_asignado = usuario actual` y estado en `ASIGNADO/EN PROCESO`)
- En proceso (filtro por estado + área)
- Cerrados (`RESUELTO/CERRADO`)
5. Detalle de ticket (`show_ticket_detail`):
- Tomar ticket
- Editar prioridad/estado/responsable
- Ver descripción
- Gestionar tareas (alta + marcar completada)
- Historial/comentarios (logs)
6. Mis tareas (listado de tasks por responsable).
7. Admin (`show_admin`):
- Usuarios (alta/edición)
- Maestras (catálogos, categorías, subcategorías)

### Validaciones y reglas de negocio legacy
1. Creación ticket:
- Requiere `titulo`, `descripcion`, `solicitante`.
- Estado inicial fijo `NUEVO`.
- Prioridad default `Media` si no se especifica.
2. Tomar ticket:
- Solo en estado `NUEVO`.
- Permitido a `Director` o `Analista/Jefe` del área destino.
- Al tomarlo: `responsable_asignado = usuario actual`, `estado = ASIGNADO`.
3. Gestión ticket:
- Actualización de `prioridad`, `estado`, `responsable_asignado`.
- Restricción de asignación por rol/área (Director siempre; Jefe por área).
4. Tareas:
- Task vinculada a ticket, estado de tarea manejado de forma independiente.
5. Historial:
- Toda acción relevante genera entradas en `ticket_log`.
6. Admin:
- Alta/edición de usuarios.
- Edición de maestras vía catálogo normalizado auxiliar (`master_catalogs`, `master_catalog_items`).

### Entidades/tablas usadas por legacy
Desde `models.py` y `db.py`:
- `tickets`
- `tasks`
- `users`
- `ticket_log`
- `master_catalogs`
- `master_catalog_items`

Notas:
- Legacy opera con columnas textuales (área/categoría/división como texto) en `tickets`.
- Tiene también capa de catálogos auxiliares para UI/admin.

## Fase 0B - Inventario Target

### Entidades/tablas/servicios disponibles
Referencias: `app.py` + `database_schema.sql`.

1. Conexión:
- Azure SQL obligatoria (`ODBC_CONN_STR`), esquema configurable (`DB_SCHEMA`, default `gestar`).

2. Maestros cargados desde DB:
- `gestar.Plantas`
- `gestar.Divisiones`
- `gestar.Areas`
- `gestar.Categorias`
- `gestar.Subcategorias`
- `gestar.Prioridades`
- `gestar.Estados`
- `gestar.Users`

3. Índices y mapeos en memoria:
- Normalización texto (`normalize_text`)
- Índices por nombre/id
- Resolución usuario sugerido
- Relación usuario->área/división (`load_user_area_division_map`)

4. Flujo actual principal (chat):
- Extracción de entidades por IA.
- Mapeo entidades->IDs de maestro.
- Validaciones de consistencia (área/división, subcategoría/categoría).
- Normalización de fecha de necesidad.
- Confirmación y creación de ticket en `gestar.Tickets`.

5. Tablas de operación usadas actualmente:
- `gestar.Tickets` (insert principal)
- `gestar.Users` (requester/suggested assignee)
- lectura de catálogo para sidebar de tickets.

### Cómo se crea/actualiza ticket en el modelo nuevo
Creación (hoy):
- `INSERT` en `gestar.Tickets` con IDs FK (`PlantaId`, `AreaId`, `CategoriaId`, `SubcategoriaId`, `PrioridadId`, `EstadoId`, `RequesterId`, `SuggestedAssigneeId`) + metadatos IA.
- `NeedByAt` se completa con fecha normalizada.
- Si el usuario sugerido está identificado, el área se toma del usuario; si no, se intenta inferir desde texto.

Actualización (hoy):
- No existe aún módulo CRUD completo estilo formulario; hay creación desde chat + listado simple lateral.

## Fase 0C - Mapeo Feature-by-Feature (Legacy -> Target)

| Funcionalidad legacy | Implementación target propuesta (sin cambiar DB) | Estado |
|---|---|---|
| Crear ticket completo (form) | Formulario web en target que escriba en `gestar.Tickets` usando los mismos mappers/validadores de `app.py` | Brecha |
| Solicitud simple | Variante reducida del formulario que complete defaults y cree en `gestar.Tickets` | Brecha |
| Bandeja con filtros/estados | Vista tabular contra `gestar.Tickets` con joins a maestros para mostrar nombres | Brecha |
| Detalle de ticket | Vista de detalle por `TicketId` con campos principales + timeline | Brecha |
| Tomar ticket | Update en `gestar.Tickets.AssigneeId` + transición de `EstadoId` | Brecha |
| Editar prioridad/estado/responsable | Update de FKs (`PrioridadId`, `EstadoId`, `AssigneeId`) | Brecha |
| Tareas por ticket | CRUD básico en `gestar.Tasks` (`IsDone`) | Brecha |
| Historial/comentarios | Usar `gestar.TicketLogs` para trazabilidad y comentarios (FieldName/evento) | Brecha |
| Mis tareas | Query a `gestar.Tasks` unido a `gestar.Tickets`/assignee | Brecha |
| Admin usuarios | Pantalla contra `gestar.Users` (alta/edición de columnas existentes) | Parcial |
| Admin maestras | Pantalla contra tablas maestras (`Plantas/Divisiones/...`) ya existentes | Parcial |

## Brechas detectadas y resolución propuesta (sin tocar esquema)

1. Legacy guarda campos de ticket como texto; target usa FKs.
- Resolución: reutilizar funciones de mapeo del target (`map_entities_to_ids`, índices maestros) en Modo Formulario.

2. Legacy tiene `ticket_log` orientado a mensajes; target tiene `TicketLogs` orientado a cambios de campo.
- Resolución: estandarizar comentario como `FieldName = 'comment'`, `OldValue = NULL`, `NewValue = texto`, `IsAi = 0`.

3. Roles/permisos en legacy están en UI; target no tiene módulo de permisos explícito aún.
- Resolución: implementar reglas en capa de servicio/UI del Modo Formulario (sin alterar DB).

4. Bandeja rica (tabs/paginación) no existe hoy en target.
- Resolución: crear sección "Modo Formulario" con filtros por estado, asignado, área, prioridad y búsqueda textual.

5. Solicitud simple del legacy no existe en target.
- Resolución: formulario corto con defaults (estado inicial + prioridad default) y mapeo a IDs.

6. Actualizaciones de ticket/tareas no están implementadas en app target actual.
- Resolución: agregar funciones de repositorio (en target) para update de `Tickets`, CRUD de `Tasks`, y log en `TicketLogs`.

## Criterios de aceptación (Fase 1/2)
1. Modo Formulario vive íntegramente en el proyecto target.
2. Todas las operaciones leen/escriben solo en modelo target (`gestar.*`).
3. No se modifica esquema de DB en esta migración.
4. Existe paridad funcional MVP: crear, listar/filtrar, ver detalle, editar campos principales, comentar/seguimiento.
5. Documentación presente: `MIGRATION_PLAN.md` + `HOW_TO_TEST.md`.

## Checklist de pruebas manuales (para ejecutar al implementar)

### Crear ticket
- [ ] Crear ticket completo con todos los campos.
- [ ] Crear ticket mínimo y validar defaults.
- [ ] Validar mapeo correcto de texto->IDs.
- [ ] Validar guardado de `NeedByAt`.

### Listado y filtros
- [ ] Ver tickets en grilla con nombres legibles (no solo IDs).
- [ ] Filtrar por estado.
- [ ] Filtrar por asignado.
- [ ] Filtrar por área/división.
- [ ] Buscar por texto en título/descripción.

### Detalle y gestión
- [ ] Abrir detalle por `TicketId`.
- [ ] Cambiar prioridad.
- [ ] Cambiar estado.
- [ ] Asignar/reasignar responsable.
- [ ] Confirmar que cambios persisten tras recargar.

### Tareas y seguimiento
- [ ] Crear tarea en ticket.
- [ ] Marcar tarea como hecha/no hecha.
- [ ] Agregar comentario/seguimiento.
- [ ] Ver trazabilidad en `TicketLogs`.

### Reglas y seguridad funcional
- [ ] Verificar reglas de toma/asignación por rol definido para el modo formulario.
- [ ] Verificar que no hay escrituras en DB/tablas legacy.
- [ ] Verificar operación 100% sobre Azure SQL target.
