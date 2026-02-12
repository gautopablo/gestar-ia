# Diagnóstico Técnico de Arquitectura y Organización

## Nivel de madurez arquitectónica (1 a 5)

- **2/5 (baja-media)**.
- Justificación breve:
  - Existe funcionalidad consolidada, pero la arquitectura está centrada en un archivo monolítico (`app.py`) con mezcla de UI, lógica de negocio, integración IA, acceso a datos y estilos.
  - La estructura de carpetas no representa capas de aplicación (por ejemplo `ui/`, `services/`, `repositories/`, `core/`).

## Principales debilidades detectadas

- **Separación de responsabilidades insuficiente**:
  - `app.py` (2644 líneas) concentra render UI Streamlit, consultas SQL/ODBC, reglas de negocio, manejo de sesión, parsing de fechas, integración con IA y CSS.
  - El acceso a datos está acoplado a la capa de presentación (múltiples `cursor.execute(...)` en el mismo archivo donde se definen formularios y componentes `st.*`).
- **Modularización limitada**:
  - No hay capas explícitas por dominio o responsabilidad; la estructura actual está más orientada a documentación/artefactos que a módulos de aplicación.
  - Funciones y bloques extensos:
    - `render_form_mode` (~677 líneas).
    - `TicketAssistant` (~523 líneas de clase).
    - `update_ticket_from_form`, `map_entities_to_ids`, `update_subtask` con extensión alta y múltiples responsabilidades.
- **Duplicación de utilidades de infraestructura**:
  - Lógica de secretos y conexión aparece en más de un módulo (`app.py` y `master_data_admin.py`).
- **Divergencia entre documentación y estado real**:
  - Documentación menciona SQLite en partes, mientras `app.py` está orientado a Azure SQL por ODBC (`get_azure_master_connection`), lo que reduce claridad estructural para nuevos colaboradores.
- **Alta concentración de cambios en un archivo**:
  - Historial Git muestra `app.py` como principal hotspot (archivo más modificado), elevando probabilidad de conflictos.

## Riesgos técnicos a corto plazo

- **Conflictos frecuentes en Git** al trabajar varias personas sobre `app.py` (UI, reglas de negocio y SQL en un mismo punto).
- **Regresiones cruzadas**: cambios de estilo/UI pueden afectar flujos de negocio y viceversa por acoplamiento directo.
- **Curva de entrada alta** para tareas simples: cualquier ajuste exige navegar un archivo grande con alta densidad de responsabilidades.
- **Pruebas difíciles de aislar** por dependencia directa entre estado de Streamlit, acceso a base y lógica de decisión en los mismos bloques.

## Riesgos técnicos a mediano plazo

- **Escalabilidad funcional limitada**:
  - Nuevas funcionalidades (nuevos flujos, más vistas, más entidades) tenderán a aumentar la complejidad de `app.py` y el costo de cambio.
- **Escalabilidad de equipo baja**:
  - Paralelizar trabajo en frontend, reglas y datos seguirá generando solapamiento de cambios y revisiones largas.
- **Deuda estructural acumulativa**:
  - Aumenta el costo de mantenimiento y el riesgo de introducir inconsistencias entre flujos (chat vs formulario vs administración).
- **Menor claridad sistémica**:
  - La intención arquitectónica no es evidente rápidamente por ausencia de capas/módulos con responsabilidades nítidas.

## 3 acciones concretas para mejorar el orden estructural

- **1. Separar por capas mínimas dentro del proyecto actual**:
  - Extraer acceso a datos (consultas y persistencia) fuera de `app.py` a un módulo dedicado.
  - Mantener en `app.py` solo composición de UI y orquestación.
- **2. Dividir lógica de negocio por dominio funcional**:
  - Aislar reglas de tickets, subtareas y parsing/normalización en módulos independientes para reducir funciones largas y acoplamiento.
- **3. Definir convenciones estructurales explícitas**:
  - Documentar en un archivo corto la organización esperada de módulos, responsabilidades por carpeta y límites entre UI, negocio y datos.

## Estimación de complejidad de refactor (baja/media/alta)

- **Alta**.
- Motivo:
  - El núcleo funcional está centralizado en `app.py` y es el principal punto de integración entre UI, datos y reglas.
  - Cambiar orden estructural sin regresiones requiere migración progresiva por etapas y validación cuidadosa de flujos críticos.

