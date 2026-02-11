# Plan de Implementacion - Subtareas por Ticket

## 1. Objetivo
Agregar soporte de **subtareas** para que cada ticket pueda tener multiples items de trabajo, cada uno con:
- responsable
- estado
- fecha de necesidad
- fecha de completado

Alcance: implementar en el proyecto actual (`gestar-ia`) sin usar tablas `dbo` y sin romper flujo existente de chat/formulario.

## 2. Modelo de datos propuesto
Se agrega una tabla nueva en esquema `gestar`: `gestar.Subtasks`.

Cada fila representa una subtarea asociada a un ticket (`gestar.Tickets.TicketId`).

Campos recomendados:
- `SubtaskId` (PK, identidad)
- `TicketId` (FK a `gestar.Tickets`)
- `Title` (obligatorio)
- `Description` (opcional)
- `AssigneeId` (FK a `gestar.Users`, opcional)
- `StatusId` (FK a `gestar.Estados`, opcional)
- `NeedBy` (datetime2, opcional)
- `CompletedAt` (datetime2, opcional)
- `SortOrder` (int, opcional) para orden visual
- `CreatedAt`, `CreatedBy`, `UpdatedAt`, `UpdatedBy` para auditoria

## 3. Reglas de negocio
- Una subtarea siempre pertenece a un ticket existente.
- `CompletedAt` solo puede existir si el estado representa completado.
- Si estado vuelve a no completado, `CompletedAt` se limpia.
- Si se borra ticket (si alguna vez aplica), definir comportamiento:
  - recomendado: `ON DELETE CASCADE` en subtareas.
- Responsable de subtarea puede ser distinto al sugerido del ticket.

## 4. Cambios en backend (app.py)
Agregar funciones de datos para subtareas:
- `fetch_subtasks(ticket_id)`
- `create_subtask(ticket_id, payload, actor_user_id)`
- `update_subtask(subtask_id, payload, actor_user_id)`
- `delete_subtask(subtask_id, actor_user_id)` (si se habilita borrado)

Buenas practicas:
- usar consultas parametrizadas
- validar FK antes de guardar
- usar mismo `DB_SCHEMA` ya configurado (`gestar`)
- no incluir fallback a `dbo`

## 5. Cambios de UI - Modo Formulario
En vista de edicion de ticket:
- bloque nuevo "Subtareas"
- grilla con subtareas del ticket
- formulario rapido para alta de subtarea
- accion de editar subtarea seleccionada
- accion de cerrar/completar subtarea

Campos en UI:
- Titulo
- Responsable
- Estado
- Fecha necesidad (selector de fecha)
- Fecha completado (solo visible/editable si corresponde)

## 6. Cambios de UI - Chat IA
Fase inicial recomendada:
- solo lectura de subtareas en detalle de ticket (si aplica)
- sin crear subtareas desde lenguaje natural en la primera entrega

Fase posterior:
- habilitar comandos tipo "agregar subtarea ..."
- confirmacion similar a flujo actual de creacion de ticket

## 7. Logging y trazabilidad
Cada cambio de subtarea debe generar registro de auditoria en `gestar.TicketLogs`:
- `FieldName`: `subtask_created`, `subtask_updated`, `subtask_status`, etc.
- `OldValue` / `NewValue` en formato legible
- `UserId` desde usuario de sesion
- `ChangedAt` timestamp del servidor

## 8. Fases de implementacion

### Fase 0 - Preparacion
- crear DDL de `gestar.Subtasks`
- validar FKs con tablas actuales `gestar.Tickets`, `gestar.Users`, `gestar.Estados`
- documentar script SQL en `info/`

### Fase 1 - Data layer
- implementar CRUD de subtareas en `app.py`
- pruebas manuales por consola/UI minima

### Fase 2 - UI Formulario (MVP)
- mostrar listado de subtareas en edicion de ticket
- crear y editar subtarea
- cambiar estado y completar

### Fase 3 - Logs
- registrar en `gestar.TicketLogs` alta/edicion/cambio de estado

### Fase 4 - Ajustes UX
- orden visual por estado + fecha necesidad
- filtros por responsable/estado
- mensajes de error y confirmacion claros

## 9. Criterios de aceptacion
- Se pueden crear multiples subtareas por ticket.
- Cada subtarea guarda responsable, estado y fechas.
- Los cambios quedan auditados en `gestar.TicketLogs`.
- No se usan tablas `dbo`.
- La funcionalidad no rompe Chat IA ni flujo actual de tickets.

## 10. Riesgos y mitigaciones
- Riesgo: diferencias de catalogos entre ambientes.
  - Mitigacion: validar IDs de estados/usuarios antes de insertar.
- Riesgo: inconsistencias en fecha completado.
  - Mitigacion: regla de negocio centralizada al actualizar estado.
- Riesgo: impacto en rendimiento al cargar detalle de ticket.
  - Mitigacion: consulta de subtareas por `TicketId` con indice.

## 11. Siguiente paso recomendado
Ejecutar primero la **Fase 0**: definir y validar el script SQL final de `gestar.Subtasks` (con nombres exactos de columnas/FK segun tus tablas actuales) y recien despues avanzar a codigo.

