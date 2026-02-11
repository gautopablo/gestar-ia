# Fase B - Dataset y Modelo Semantico Power BI (Gestar)

## 1. Objetivo de la fase
Construir el dataset Power BI MVP sobre Azure SQL con un modelo confiable, performante y listo para diseñar el reporte.

Resultado esperado:
- modelo semántico publicado y validado
- relaciones correctas entre tickets, subtareas y dimensiones
- medidas DAX base listas para visuales
- refresh inicial funcionando

## 2. Alcance de Fase B
Incluye:
- conexión y carga de tablas
- transformaciones mínimas en Power Query
- diseño de modelo estrella
- medidas DAX MVP
- validación de números con SQL

No incluye:
- diseño visual final (fase de reporte)
- seguridad RLS avanzada (opcional posterior)

## 3. Tablas recomendadas para el MVP

### Hechos
- `FactTickets` (origen: `gestar.Tickets`)
- `FactSubtasks` (origen: `gestar.Subtasks`)
- `FactTicketLogs` (origen: `gestar.TicketLogs`, opcional en MVP mínimo)

### Dimensiones
- `DimUsers` (`gestar.Users`)
- `DimEstados` (`gestar.Estados`)
- `DimPrioridades` (`gestar.Prioridades`)
- `DimAreas` (`gestar.Areas`)
- `DimDivisiones` (`gestar.Divisiones`)
- `DimPlantas` (`gestar.Plantas`)
- `DimCategorias` (`gestar.Categorias`)
- `DimSubcategorias` (`gestar.Subcategorias`)
- `DimDate` (generada en Power BI)

## 4. Pasos detallados de implementación

### B.1 Conectar Power BI Desktop a Azure SQL
- `Get Data > Azure SQL Database`
- Servidor: `server-sql-gestar.database.windows.net`
- Base: `sql-db-gestar`
- Autenticación: SQL o AAD según política vigente
- Seleccionar tablas del esquema `gestar` únicamente

Recomendación:
- renombrar consultas al cargar:
  - `gestar.Tickets` -> `FactTickets`
  - `gestar.Subtasks` -> `FactSubtasks`, etc.

### B.2 Limpieza mínima en Power Query
- Ajustar tipos:
  - IDs a `Whole Number`
  - fechas a `Date/DateTime`
  - textos a `Text`
- Reemplazar null de etiquetas para visualización:
  - usar `"Sin definir"` solo en dimensión derivada, no en IDs.
- Eliminar columnas no usadas en MVP para reducir tamaño.
- Opcional:
  - deshabilitar carga de queries auxiliares.

### B.3 Construcción del modelo
- Relacionar:
  - `FactSubtasks[TicketId]` -> `FactTickets[TicketId]` (Many-to-One, single direction)
  - `FactTickets[EstadoId]` -> `DimEstados[EstadoId]`
  - `FactSubtasks[EstadoId]` -> `DimEstados[EstadoId]`
  - `FactTickets[PrioridadId]` -> `DimPrioridades[PrioridadId]`
  - `FactTickets[AreaId]` -> `DimAreas[AreaId]`
  - `DimAreas[DivisionId]` -> `DimDivisiones[DivisionId]`
  - `FactTickets[PlantaId]` -> `DimPlantas[PlantaId]`
  - `FactTickets[CategoriaId]` -> `DimCategorias[CategoriaId]`
  - `FactTickets[SubcategoriaId]` -> `DimSubcategorias[SubcategoriaId]`
  - `FactSubtasks[AssigneeId]` -> `DimUsers[UserId]`
- Usuarios en tickets:
  - `RequesterId`, `AssigneeId`, `SuggestedAssigneeId` generan relaciones múltiples.
  - Recomendación MVP:
    - relación activa con `AssigneeId` (o la más usada),
    - otras por medidas con `USERELATIONSHIP`.

### B.4 Tabla calendario (DimDate)
Crear una tabla calendario para análisis temporal.
Campos sugeridos:
- Date
- Year
- MonthNumber
- MonthName
- YearMonth
- Week
- Quarter

Relaciones recomendadas iniciales:
- `FactTickets[CreatedAt]` -> `DimDate[Date]` (activa)
- para otras fechas (`NeedByAt`, `UpdatedAt`, `CompletedAt`), usar relaciones inactivas y `USERELATIONSHIP` en medidas específicas.

### B.5 Medidas DAX base (MVP)
Medidas mínimas:
- `Tickets Creados = COUNTROWS(FactTickets)`
- `Subtareas Creadas = COUNTROWS(FactSubtasks)`
- `Tickets Abiertos = CALCULATE([Tickets Creados], DimEstados[Nombre] IN {"Abierto","En Progreso"})`
- `Tickets Cerrados = CALCULATE([Tickets Creados], DimEstados[Nombre] = "Cerrado")`
- `% Tickets Cerrados = DIVIDE([Tickets Cerrados], [Tickets Creados])`
- `Subtareas Completadas = CALCULATE([Subtareas Creadas], NOT ISBLANK(FactSubtasks[CompletedAt]))`
- `% Subtareas Completadas = DIVIDE([Subtareas Completadas], [Subtareas Creadas])`
- `Backlog Vencido Tickets = CALCULATE([Tickets Creados], FactTickets[NeedByAt] < NOW(), DimEstados[Nombre] <> "Cerrado")`
- `Backlog Vencido Subtareas = CALCULATE([Subtareas Creadas], FactSubtasks[NeedByAt] < NOW(), ISBLANK(FactSubtasks[CompletedAt]))`

Nota:
- Ajustar lista de estados según nombres reales en catálogo.

### B.6 Validación cruzada con SQL
Validar que KPI del modelo coincida con queries SQL de control.
Controles mínimos:
- cantidad total de tickets
- cantidad total de subtareas
- tickets por estado
- subtareas por estado
- vencidos tickets/subtareas

Guardar evidencias en un archivo de validación.

### B.7 Performance inicial
- Evitar columnas de texto largas innecesarias en hechos para MVP.
- Desactivar Auto Date/Time si no se usa.
- Preferir importación selectiva.
- Si hay crecimiento alto de `TicketLogs`, mantenerlo fuera del MVP inicial o cargarlo con filtro temporal.

### B.8 Publicación del dataset
- Publicar a workspace definido (`GESTAR BI` o equivalente).
- Configurar credenciales del datasource en Service.
- Ejecutar refresh manual inicial.
- Verificar tiempos y errores.

## 5. Checklist de cierre Fase B
- [ ] Tablas cargadas con tipos correctos.
- [ ] Relaciones clave creadas y sin ambigüedad crítica.
- [ ] Tabla `DimDate` activa.
- [ ] Medidas DAX MVP disponibles.
- [ ] Validación SQL vs Power BI aprobada.
- [ ] Dataset publicado en Service.
- [ ] Refresh manual exitoso.

## 6. Criterios de aceptación de Fase B
Fase B está completa cuando:
- el dataset responde correctamente preguntas básicas de volumen y estado
- los principales KPI coinciden con SQL de control
- el modelo está listo para construir el reporte/dashboards sin retrabajo estructural

## 7. Riesgos y mitigaciones
- Ambigüedad en relaciones de usuarios (`Requester/Assignee/Suggested`):
  - Mitigar con una relación activa + medidas específicas con `USERELATIONSHIP`.
- Estados heterogéneos:
  - Mitigar con una tabla de mapeo semántico (abierto/en curso/cerrado) en Power Query.
- Rendimiento por logs:
  - Mitigar separando `FactTicketLogs` como capa opcional o con filtro temporal.

## 8. Entregables de Fase B
- PBIX con dataset MVP.
- Documento de medidas DAX base.
- Evidencia de validación SQL vs Power BI.
- Dataset publicado y refrescado en Power BI Service.

