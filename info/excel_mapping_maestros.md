# Mapeo Excel -> Esquema Actual (Referencia)

Objetivo: usar `info/maestros gestar.xlsx` como fuente de ejemplos, sin alterar la estructura actual definida en `database_schema.sql` y usada por `app.py`.

## Regla base

- La estructura vigente es la del proyecto (`Plantas`, `Divisiones`, `Areas`, `Categorias`, `Subcategorias`, `Prioridades`, `Users`).
- El Excel se toma como dataset de ejemplo.
- Campos del Excel que no existen en el esquema actual se ignoran.

## Mapeo por hoja

| Hoja Excel | Columna Excel | Tabla destino | Columna destino | Regla |
|---|---|---|---|---|
| `tipos maestros` | `code`/`label` | N/A | N/A | Solo se usa para identificar el tipo de item en `items maestros` |
| `items maestros` | `label` (`catalog=plantas`) | `Plantas` | `Nombre` | `INSERT OR IGNORE` |
| `items maestros` | `label` (`catalog=divisiones`) | `Divisiones` | `Nombre` | `INSERT OR IGNORE` |
| `items maestros` | `label` (`catalog=areas`) | `Areas` | `Nombre` | Requiere `DivisionId`; se usa mapeo de ejemplo por nombre |
| `items maestros` | `label` (`catalog=prioridades`) | `Prioridades` | `Nombre` | `Nivel` se asigna por regla (`Crítica=0`, `Alta=1`, `Media=2`, `Baja=3`) |
| `items maestros` | `label` (`catalog=categorias`, sin `parent_item_id`) | `Categorias` | `Nombre` | Categoría padre |
| `items maestros` | `label` (`catalog=categorias`, con `parent_item_id`) | `Subcategorias` | `Nombre` + `CategoriaId` | Se resuelve `CategoriaId` por nombre de categoría padre |
| `usuarios` | `nombre_completo` | `Users` | `Username` | Normalizado: minúsculas, sin coma, espacios a `_` |
| `usuarios` | `email` | `Users` | `Email` | minúsculas |
| `usuarios` | `rol` | `Users` | `Role` | Se mantiene texto del Excel |
| `usuarios` | `activo` | `Users` | `Active` | `True -> 1`, otro -> `0` |

## Campos del Excel no usados

- `items maestros.id`
- `items maestros.catalog_id` (se usa indirectamente para clasificar, no se persiste)
- `items maestros.code` (vacío en el archivo)
- `items maestros.sort_order`
- `items maestros.is_active`
- `items maestros.created_at`
- `tipos maestros.created_at`

## Decisiones de compatibilidad

- El esquema actual no tiene tabla `Roles`; el rol del usuario queda en `Users.Role`.
- El esquema actual exige `Areas.DivisionId`; como el Excel no trae esa relación explícita, se aplica mapeo de ejemplo por nombre de área.
- Hay subcategorías con mismo nombre bajo distintas categorías. En el esquema actual eso es válido porque `Subcategorias` se relaciona por `CategoriaId`.

## Script de carga

- Archivo: `info/seed_examples_from_excel.sql`
- Tipo de carga: idempotente (`INSERT OR IGNORE`)
