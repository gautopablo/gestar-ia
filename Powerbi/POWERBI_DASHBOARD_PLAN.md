# Plan de Implementacion - Panel de Control Power BI (Tareas y Tickets)

## 1. Objetivo
Construir un panel en Power BI para monitorear tickets y subtareas cargadas, usando la base actual en Azure SQL (`gestar`), sin modificar la arquitectura de la app.

## 2. Alcance
- Fuente única: Azure SQL Database.
- Entidades principales:
  - `gestar.Tickets`
  - `gestar.Subtasks`
  - `gestar.TicketLogs`
  - catálogos (`gestar.Estados`, `gestar.Prioridades`, `gestar.Users`, `gestar.Areas`, `gestar.Divisiones`, `gestar.Plantas`, `gestar.Categorias`, `gestar.Subcategorias`)
- Resultado: 1 dataset + 1 reporte + 1 dashboard en Power BI Service.

## 3. Preguntas de negocio a responder
- ¿Cuántos tickets/subtareas se crean por día/semana/mes?
- ¿Qué porcentaje está abierto, en progreso y cerrado?
- ¿Dónde hay más carga (área/división/planta)?
- ¿Quiénes tienen más asignaciones?
- ¿Qué backlog vencido existe (NeedByAt < hoy y no completado)?
- ¿Cuál es el tiempo promedio de resolución/completitud?

## 4. Diseño del modelo semántico
Modelo estrella recomendado:

- Hechos:
  - `FactTickets` (base: `gestar.Tickets`)
  - `FactSubtasks` (base: `gestar.Subtasks`)
  - `FactTicketLogs` (base: `gestar.TicketLogs`, para auditoría/eventos)
- Dimensiones:
  - `DimDate` (calendario)
  - `DimUsers`
  - `DimEstados`
  - `DimPrioridades`
  - `DimAreas`
  - `DimDivisiones`
  - `DimPlantas`
  - `DimCategorias`
  - `DimSubcategorias`

Relaciones clave:
- `FactTickets[RequesterId]`, `FactTickets[AssigneeId]`, `FactTickets[SuggestedAssigneeId]` -> `DimUsers[UserId]` (usar roles/medidas para cada relación).
- `FactSubtasks[TicketId]` -> `FactTickets[TicketId]`.
- `FactSubtasks[AssigneeId]` -> `DimUsers[UserId]`.
- Estados y prioridades por sus IDs.
- Fechas a `DimDate` (CreatedAt, NeedByAt, UpdatedAt, CompletedAt según caso).

## 5. Definicion de KPIs
KPIs mínimos (fase inicial):
- `Tickets creados`
- `Tickets abiertos`
- `% Tickets cerrados`
- `Subtareas creadas`
- `Subtareas completadas`
- `% Subtareas completadas`
- `Backlog vencido tickets`
- `Backlog vencido subtareas`
- `Tiempo promedio hasta completar subtarea` (cuando haya `CompletedAt`)
- `Tickets por prioridad`

## 6. Páginas del reporte

### Página 1: Resumen Ejecutivo
- Tarjetas KPI principales.
- Tendencia mensual de tickets/subtareas.
- Distribución por estado y prioridad.

### Página 2: Operación por Área
- Tickets/subtareas por área/división/planta.
- Matriz de responsables con carga activa.
- Top 10 responsables con mayor backlog.

### Página 3: SLA / Fechas
- Vencidos vs no vencidos.
- Antigüedad de tickets abiertos.
- Tiempo de resolución (si hay cierre).

### Página 4: Auditoría
- Eventos desde `gestar.TicketLogs`.
- Filtros por tipo de cambio (`FieldName`), usuario y rango de fechas.

## 7. Estrategia de conexión y actualización
- Modo recomendado inicial: `Import` (mejor performance y simpleza).
- Frecuencia recomendada: cada 30 min o 1 hora (según plan/licencia).
- Si volumen crece:
  - habilitar Incremental Refresh por `CreatedAt`/`UpdatedAt`.
  - evaluar `DirectQuery` solo si se necesita casi tiempo real.

## 8. Seguridad y acceso
- Publicar en workspace dedicado (ej. `GESTAR BI`).
- Definir roles de acceso en Power BI Service:
  - Lectura general
  - Supervisores
  - Administradores BI
- Opcional: RLS por usuario/área usando `DimUsers` y mapeo de áreas.

## 9. Calidad de datos y validaciones
Antes de publicar:
- Verificar nulos críticos (`TicketId`, `SubtaskId`, títulos, estados).
- Validar integridad de FKs (`Subtasks.TicketId` con `Tickets.TicketId`).
- Revisar valores fuera de catálogo.
- Confirmar fechas inválidas o incompletas.

## 10. Plan por fases

### Fase A - Preparación técnica
1. Confirmar credenciales de solo lectura para Power BI.
2. Definir workspace y owner funcional.
3. Documentar diccionario de campos.

### Fase B - Dataset (Modelo)
1. Conectar a Azure SQL desde Power BI Desktop.
2. Cargar tablas de hechos y dimensiones.
3. Crear relaciones y tabla calendario.
4. Crear medidas DAX base.

### Fase C - Reporte MVP
1. Construir página Resumen Ejecutivo.
2. Construir página Operación por Área.
3. Validar números con muestreo SQL.

### Fase D - Hardening
1. Agregar página SLA y Auditoría.
2. Configurar refresh en Service.
3. Configurar permisos y (si aplica) RLS.

### Fase E - Go Live
1. Publicar versión v1.
2. Capacitación breve a usuarios clave.
3. Recolección de feedback y backlog BI v2.

## 11. Entregables
- `PBIX` versión MVP.
- Dataset publicado en Power BI Service.
- Dashboard con KPIs principales.
- Documento de diccionario de métricas.
- Manual corto de uso (filtros, interpretación, alcance).

## 12. Riesgos y mitigación
- Datos incompletos en estados/fechas:
  - Mitigar con KPI de calidad y alertas.
- Cambios futuros en modelo de app:
  - Mitigar con capa semántica estable y versionado.
- Performance con crecimiento de logs:
  - Mitigar con incremental refresh y particionado temporal.

## 13. Próximo paso recomendado
Arrancar con **Fase A/B**: armar el dataset MVP en Power BI Desktop con `Tickets`, `Subtasks`, `Estados`, `Prioridades`, `Users` y una primera página de KPIs para validar números con negocio.

