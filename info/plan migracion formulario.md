OBJETIVO
Tengo 2 proyectos distintos:
- PROYECTO VIEJO (legacy) = app estilo formulario
- PROYECTO NUEVO (target) = app estilo WhatsApp + modelo de datos definitivo

Quiero que generes en el PROYECTO NUEVO un “Modo Formulario” (web) que replique las funcionalidades del PROYECTO VIEJO, PERO respetando estrictamente la lógica y el modelo de datos del PROYECTO NUEVO.

IMPORTANTE: El modelo de datos válido es el del PROYECTO NUEVO. El PROYECTO VIEJO solo sirve como referencia de UX y funcionalidades.

RUTAS (COMPLETAR)
- Ruta/URL PROYECTO VIEJO: C:\Users\GAUTOP\OneDrive - TARANTO SAN JUAN SA\Documentos\PROYECTOS APP\Tickets\gestar


- Ruta/URL PROYECTO NUEVO: C:\Users\GAUTOP\OneDrive - TARANTO SAN JUAN SA\Documentos\PROYECTOS APP\gestar-ia


REGLAS (NO NEGOCIABLES)
1) NO modificar el esquema de base de datos del PROYECTO NUEVO (tablas/columnas). Si falta algo, proponé alternativas, pero no lo implementes sin pedírmelo.
2) Todo lo implementado debe vivir en el PROYECTO NUEVO (código, pantallas, docs).
3) Nada debe escribir en el modelo/DB del PROYECTO VIEJO. No hay sincronizaciones.
4) Respetar arquitectura, estilo y convenciones del PROYECTO NUEVO.
5) Trabajar en pasos pequeños, con commits claros.

PLAN DE TRABAJO

FASE 0 — INVENTARIO Y MAPEO (sin escribir código todavía)
A) Analizá el PROYECTO VIEJO y devolveme:
   - lista de pantallas/flujos/funcionalidades (crear, editar, listar, filtros, etc.)
   - validaciones de formulario y reglas de negocio
   - entidades/tablas usadas por el legacy
B) Analizá el PROYECTO NUEVO y devolveme:
   - entidades/tablas/servicios disponibles
   - cómo se crea/actualiza un ticket en el modelo nuevo (campos + mensajes/eventos si aplica)
C) Generá un “MAPEO” feature-by-feature:
   - Funcionalidad legacy -> implementación target (qué tabla/campo/servicio del modelo nuevo se usa)
   - Brechas: cosas del legacy que no existen directo en el target
   - Propuesta de resolución de brechas SIN cambiar DB (ej: usar primer mensaje como descripción, usar eventos, etc.)
D) Entregables Fase 0:
   - documento MIGRATION_PLAN.md en el PROYECTO NUEVO con el inventario + mapeo + brechas + criterios de aceptación
   - y un checklist de pruebas manuales

FASE 1 — IMPLEMENTAR “MODO FORMULARIO” EN EL PROYECTO NUEVO
E) Crear una sección/página/ruta “Modo Formulario” dentro del PROYECTO NUEVO.
F) Implementar paridad mínima (MVP) con legacy:
   - Crear ticket
   - Editar campos principales (los que existan en el modelo nuevo)
   - Ver detalle
   - Listar + buscar + filtrar
   - Agregar comentario/seguimiento (usando la lógica de “mensajes” del target si existe)
G) Asegurar que todas las operaciones pasan por los repositorios/servicios del PROYECTO NUEVO (no acceso directo a DB si el target no lo hace así).

FASE 2 — PARIDAD COMPLETA + QA
H) Replicar validaciones y reglas del legacy dentro de lo posible.
I) Tests mínimos (unit o integration) para crear/editar/listar.
J) Documento HOW_TO_TEST.md con pasos exactos.

FORMA DE TRABAJO / OUTPUT
1) Primero ejecutá FASE 0 y mostrame el MIGRATION_PLAN.md (resumen en consola).
2) Recién después empezá a codear.
3) Commits chicos por feature con mensaje claro.
4) Cada commit debe incluir cómo probarlo (comando o pasos).

CRITERIOS DE ACEPTACIÓN
- El “Modo Formulario” en el PROYECTO NUEVO permite operar tickets como en el legacy.
- Usa exclusivamente el modelo de datos del target.
- No se tocó el esquema del target.
- Documentación MIGRATION_PLAN.md + HOW_TO_TEST.md en el PROYECTO NUEVO.

EMPEZÁ AHORA
Hacé la FASE 0: inventario + mapeo + brechas, y generá MIGRATION_PLAN.md en el PROYECTO NUEVO.

