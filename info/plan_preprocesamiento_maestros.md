# Plan de Implementación - Preprocesamiento de Datos Maestros (Backend)

## Objetivo

Reducir uso de tokens y aumentar precisión en creación de tickets moviendo la validación/mapeo de maestros al backend, manteniendo la estructura actual de base de datos.

Incorporar la jerarquía operativa `Division -> Area -> Usuario` para inferir contexto automáticamente durante la creación del ticket.

## Alcance

- No cambia el esquema actual (`Plantas`, `Divisiones`, `Areas`, `Categorias`, `Subcategorias`, `Prioridades`, `Users`, `Tickets`).
- El LLM extrae intención + texto de campos.
- El backend valida y convierte a IDs.
- Regla de negocio adicional: si se identifica usuario, se infiere su `Area` y, desde esa área, la `Division`.

## Estrategia

1. Cargar maestros activos desde BD al iniciar.
2. Preprocesar y normalizar nombres en memoria.
3. Construir índices de búsqueda por entidad.
4. Resolver mapeo a IDs en código (exacto, luego fuzzy opcional).
5. Enviar al LLM solo catálogos mínimos por intención.
6. Validar jerarquías antes de insertar ticket con validación blanda (no bloqueante).

## Diseño Técnico

### 1) Carga y cache de maestros

- Crear `load_master_data()`:
  - `Plantas`, `Divisiones`, `Areas`, `Categorias`, `Subcategorias`, `Prioridades`, `Estados`.
- Guardar en `st.session_state.master_data`.
- Agregar `master_data_version` o TTL para refresco controlado.

### 2) Normalización e índices

- Crear `normalize_text(value)`:
  - `strip`, lowercase, colapsar espacios.
  - opcional: remover tildes para robustez.
- Crear `build_master_indexes(master_data)`:
  - `plantas_by_norm`, `divisiones_by_norm`, `areas_by_norm`, `categorias_by_norm`, `prioridades_by_norm`, `users_by_norm`.
  - `subcategorias_by_norm` con lista de candidatos (puede haber duplicados por categoría).
  - `user_to_area_division`: índice `usuario -> (area_id, division_id)` para inferencia.

Nota:
- Como el esquema actual no tiene `Users.AreaId`, la relación usuario->área se resuelve por tabla de referencia de maestros (dataset interno) o mapeo de configuración.

### 3) Extracción IA mínima

- Ajustar prompt para devolver:
  - `intencion`, `titulo`, `descripcion`, `planta`, `division`, `area`, `categoria`, `subcategoria`, `prioridad`, `usuario_sugerido`.
- Enviar solo listas necesarias:
  - para `crear_ticket`: `plantas`, `areas`, `categorias`, `prioridades` y, si aplica, `subcategorias` filtradas por categoría detectada.
- Excluir `usuarios` del prompt por defecto.

### 4) Mapeo determinista a IDs

- Crear `map_entities_to_ids(draft, master_data, indexes)`:
  - match exacto normalizado por entidad.
  - subcategoría: resolver por `(categoria_id + subcategoria_normalizada)`.
  - si ambigua/no encontrada: marcar pendiente y no insertar.
  - si se identifica `usuario_sugerido`, completar automáticamente:
    - `suggested_assignee_id`
    - `area_id` (si no vino informada)
    - `division_id` (derivada del área)
  - si usuario y área/división informadas entran en conflicto: priorizar validación y pedir confirmación.

### 5) Validaciones de negocio previas a inserción

- Campos obligatorios para crear ticket:
  - Ninguno a nivel funcional de negocio (se permite crear ticket incompleto).
- Reglas:
  - `Area.DivisionId` coherente si se informó división.
  - `Subcategoria.CategoriaId` coherente con categoría.
  - `EstadoId` por defecto: `Abierto`.
  - `PrioridadId` por defecto: `Media` (si faltante).
  - `Usuario -> Area`: si hay usuario sugerido, validar que área del ticket sea la misma del usuario (o pedir confirmación).
  - `Area -> Division`: siempre validar consistencia jerárquica.
  - Prioridad operativa: se considera ticket "enriquecido" si tiene al menos `Area` o `Usuario_sugerido`.

### 5.1) Score de completitud (recomendado)

- Crear `compute_completeness_score(draft, ids)` para etiquetar calidad del ticket.
- Regla mínima recomendada:
  - `alto`: tiene `Area` o `Usuario_sugerido`, y además `Categoria`.
  - `medio`: tiene `Area` o `Usuario_sugerido`, pero sin `Categoria`.
  - `bajo`: no tiene ni `Area` ni `Usuario_sugerido`.
- Este score no bloquea inserción; solo informa y prioriza triage.

### 6) Inserción completa

- Reemplazar inserción simplificada por inserción completa en `Tickets`.
- Registrar `OriginalPrompt`, `ConfidenceScore`, `AiProcessingTime`.

### 7) Manejo de errores y UX

- Si faltan datos clave (`Area` y `Usuario_sugerido`): mostrar advertencia no bloqueante y sugerir completar.
- Si no hay match: mostrar opciones válidas para confirmar.
- Si hay ambigüedad de subcategoría: pedir categoría/subcategoría explícita.
- Permitir siempre `Crear Ticket` con mensaje de impacto operativo:
  - "Se creó el ticket, pero sin Área/Usuario sugerido tendrá menor precisión de asignación."

## Plan por Fases

### Fase 1 - Base sólida (recomendada)

1. `load_master_data()`
2. `normalize_text()` + índices
3. `map_entities_to_ids()` exacto con inferencia `usuario -> area -> division`
4. validaciones e inserción completa
5. prompt reducido sin usuarios

### Fase 2 - Robustez

1. fuzzy matching (umbral configurable)
2. refresco automático de cache (TTL/versionado)
3. métricas de fallas de mapeo y campos faltantes

### Fase 3 - Optimización

1. catálogos dinámicos por intención/contexto
2. shortlist de subcategorías por categoría detectada
3. A/B de prompt corto vs prompt extendido

## Impacto Esperado

- Menor costo por request (menos tokens enviados).
- Menor latencia.
- Mayor consistencia en IDs relacionales.
- Menos tickets con datos incompletos o ambiguos.

## Riesgos y Mitigación

1. Ambigüedad de subcategorías:
- Mitigar con resolución por par `categoria + subcategoria`.

2. Maestros desactualizados en memoria:
- Mitigar con TTL o botón `Refrescar maestros`.

3. Variantes de escritura de usuarios:
- Mitigar con normalización + fuzzy opcional.

4. Relación usuario-área fuera del esquema actual:
- Mitigar con fuente de mapeo explícita (maestros/config) y validación obligatoria antes de insertar.

5. Tickets con poco contexto por ausencia de `Area`/`Usuario_sugerido`:
- Mitigar con advertencia de UX + score de completitud + cola de triage priorizada.

## Checklist de Aceptación

- [ ] El prompt ya no envía todos los catálogos indiscriminadamente.
- [ ] El backend mapea nombres a IDs con índices normalizados.
- [ ] Si se identifica usuario, se infieren `Area` y `Division` automáticamente.
- [ ] Se valida coherencia `Usuario -> Area -> Division`.
- [ ] La creación de ticket inserta campos relacionales completos.
- [ ] La creación de ticket no bloquea por faltantes de negocio.
- [ ] Si faltan `Area` y `Usuario_sugerido`, se muestra advertencia no bloqueante.
- [ ] Se detecta y gestiona ambigüedad de subcategorías.
- [ ] Existe mecanismo de refresco de maestros.

## Archivos a tocar

- `app.py`: carga/cache, normalización, mapeo, validaciones e inserción.
- `database_architecture.md`: actualizar flujo IA + mapeo backend.
- `info/seed_examples_from_excel.sql`: mantener dataset de ejemplo para pruebas.
