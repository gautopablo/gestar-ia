# Checklist de Validación SQLite (DB_MODE=sqlite)

## Preparación
1. Configurar variables:
   - `DB_MODE=sqlite`
   - `SQLITE_PATH=tickets_mvp.db`
2. Inicializar schema local:
   - `python scripts/bootstrap_sqlite.py --db tickets_mvp.db`
3. Iniciar app:
   - `streamlit run app.py`

## Smoke diario (10 min)
1. Crear ticket nuevo (con categoría/área/prioridad/fecha).
2. Editar ticket (estado y asignado).
3. Agregar comentario.
4. Crear, editar y eliminar subtarea.
5. Filtrar ticket por texto y por estado.
6. Reiniciar app y verificar persistencia del ticket.

## Paridad funcional (Azure vs SQLite)
1. Ejecutar mismos casos en `DB_MODE=azure` y `DB_MODE=sqlite`.
2. Validar:
   - cantidad de tickets creados,
   - cambios en `EstadoId`, `AssigneeId`, `UpdatedAt`,
   - historial en `TicketLogs`,
   - subtareas asociadas al ticket.

## Criterio de aceptación
- La app inicia y opera sin errores en ambos modos.
- Las operaciones CRUD de tickets/subtareas/logs funcionan en SQLite.
- No hay pérdida de datos al reiniciar en modo SQLite.
