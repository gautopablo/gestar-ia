# Plan de Implementación: Tema Profesional en Claro y Oscuro (Streamlit)

## Contexto y decisión base

- Actualmente existe una regla temporal en `app.py:1393`:
  - `:root { color-scheme: light; }`
- Esa línea ayudó a mitigar inconsistencias en navegadores con modo oscuro, pero bloquea un dark mode real y contribuye al comportamiento mixto (componentes claros + componentes oscuros).
- Si se implementa bien el tema oscuro, esa regla debe eliminarse o condicionarse por tema activo.

## Objetivo

Lograr un tratamiento visual profesional, consistente y legible en ambos modos (claro y oscuro), con paridad de calidad en toda la app (incluyendo `st.dataframe`) y sin depender de overrides frágiles.

## Estrategia recomendada (actualizada)

1. Usar el sistema nativo de tema de Streamlit como base (`.streamlit/config.toml`).
2. Mantener CSS custom solo para branding y componentes no cubiertos por tema nativo.
3. Evitar pelear con `st.dataframe` vía CSS externo; apoyarse en tema nativo y ajustes permitidos.
4. Implementar en dos fases:
   - Fase 1: base completa y estable para ambos modos con activación automática por sistema.
   - Fase 2 (opcional): selector manual `Claro / Oscuro / Automático`.

## Respuesta a la duda de selector manual

- No implementar selector manual en Fase 1 no bloquea el resultado.
- Riesgo real de no tenerlo:
  - Menor control por usuario final cuando el modo del sistema no coincide con su preferencia.
- Recomendación:
  - Entregar primero consistencia profesional en claro y oscuro con estrategia automática.
  - Agregar selector manual después, cuando la base visual esté estable.

## Plan de trabajo detallado

### 1) Definir tokens semánticos y paletas

- Crear tokens por rol visual, no por componente:
  - `--bg-page`, `--bg-surface`, `--bg-elevated`
  - `--text-primary`, `--text-secondary`, `--text-muted`
  - `--border-default`, `--border-focus`
  - `--brand-primary`, `--brand-secondary`, `--state-success`, `--state-danger`
  - `--input-bg`, `--input-text`, `--placeholder`
  - `--chat-user-bg`, `--chat-bot-bg`, `--bottom-bar-bg`
- Definir dos paletas completas: `light` y `dark`, con equivalencias por componente y estado.
- Evitar negro puro (`#000000`) en fondos de dark mode.

### Paletas sugeridas (propuesta inicial)

Tabla de tokens con equivalencia en ambos modos.

| Token | Claro | Oscuro | Muestra Claro | Muestra Oscuro |
|---|---|---|---|---|
| `--bg-page` | `#F7F9FC` | `#12161C` | <span style="display:inline-block;width:18px;height:18px;background:#F7F9FC;border:1px solid #999;"></span> | <span style="display:inline-block;width:18px;height:18px;background:#12161C;border:1px solid #999;"></span> |
| `--bg-surface` | `#FFFFFF` | `#1A2230` | <span style="display:inline-block;width:18px;height:18px;background:#FFFFFF;border:1px solid #999;"></span> | <span style="display:inline-block;width:18px;height:18px;background:#1A2230;border:1px solid #999;"></span> |
| `--bg-elevated` | `#EEF3F8` | `#222C3D` | <span style="display:inline-block;width:18px;height:18px;background:#EEF3F8;border:1px solid #999;"></span> | <span style="display:inline-block;width:18px;height:18px;background:#222C3D;border:1px solid #999;"></span> |
| `--text-primary` | `#1F2937` | `#E6EDF7` | <span style="display:inline-block;width:18px;height:18px;background:#1F2937;border:1px solid #999;"></span> | <span style="display:inline-block;width:18px;height:18px;background:#E6EDF7;border:1px solid #999;"></span> |
| `--text-secondary` | `#3F4D5F` | `#B6C2D1` | <span style="display:inline-block;width:18px;height:18px;background:#3F4D5F;border:1px solid #999;"></span> | <span style="display:inline-block;width:18px;height:18px;background:#B6C2D1;border:1px solid #999;"></span> |
| `--text-muted` | `#5F6E80` | `#8FA0B4` | <span style="display:inline-block;width:18px;height:18px;background:#5F6E80;border:1px solid #999;"></span> | <span style="display:inline-block;width:18px;height:18px;background:#8FA0B4;border:1px solid #999;"></span> |
| `--border-default` | `#7A889A` | `#5C6E85` | <span style="display:inline-block;width:18px;height:18px;background:#7A889A;border:1px solid #999;"></span> | <span style="display:inline-block;width:18px;height:18px;background:#5C6E85;border:1px solid #999;"></span> |
| `--border-focus` | `#156099` | `#5AA2D9` | <span style="display:inline-block;width:18px;height:18px;background:#156099;border:1px solid #999;"></span> | <span style="display:inline-block;width:18px;height:18px;background:#5AA2D9;border:1px solid #999;"></span> |
| `--brand-primary` | `#D52E25` | `#F0625D` | <span style="display:inline-block;width:18px;height:18px;background:#D52E25;border:1px solid #999;"></span> | <span style="display:inline-block;width:18px;height:18px;background:#F0625D;border:1px solid #999;"></span> |
| `--brand-secondary` | `#156099` | `#5AA2D9` | <span style="display:inline-block;width:18px;height:18px;background:#156099;border:1px solid #999;"></span> | <span style="display:inline-block;width:18px;height:18px;background:#5AA2D9;border:1px solid #999;"></span> |
| `--state-success` | `#2E7D32` | `#81C784` | <span style="display:inline-block;width:18px;height:18px;background:#2E7D32;border:1px solid #999;"></span> | <span style="display:inline-block;width:18px;height:18px;background:#81C784;border:1px solid #999;"></span> |
| `--state-danger` | `#C62828` | `#EF9A9A` | <span style="display:inline-block;width:18px;height:18px;background:#C62828;border:1px solid #999;"></span> | <span style="display:inline-block;width:18px;height:18px;background:#EF9A9A;border:1px solid #999;"></span> |
| `--input-bg` | `#FFFFFF` | `#1A2230` | <span style="display:inline-block;width:18px;height:18px;background:#FFFFFF;border:1px solid #999;"></span> | <span style="display:inline-block;width:18px;height:18px;background:#1A2230;border:1px solid #999;"></span> |
| `--input-text` | `#1F2937` | `#E6EDF7` | <span style="display:inline-block;width:18px;height:18px;background:#1F2937;border:1px solid #999;"></span> | <span style="display:inline-block;width:18px;height:18px;background:#E6EDF7;border:1px solid #999;"></span> |
| `--placeholder` | `#6B7785` | `#8FA0B4` | <span style="display:inline-block;width:18px;height:18px;background:#6B7785;border:1px solid #999;"></span> | <span style="display:inline-block;width:18px;height:18px;background:#8FA0B4;border:1px solid #999;"></span> |
| `--chat-user-bg` | `#DCF8C6` | `#1F5B3A` | <span style="display:inline-block;width:18px;height:18px;background:#DCF8C6;border:1px solid #999;"></span> | <span style="display:inline-block;width:18px;height:18px;background:#1F5B3A;border:1px solid #999;"></span> |
| `--chat-bot-bg` | `#FFFFFF` | `#1A2230` | <span style="display:inline-block;width:18px;height:18px;background:#FFFFFF;border:1px solid #999;"></span> | <span style="display:inline-block;width:18px;height:18px;background:#1A2230;border:1px solid #999;"></span> |
| `--bottom-bar-bg` | `#DCF8C6` | `#173428` | <span style="display:inline-block;width:18px;height:18px;background:#DCF8C6;border:1px solid #999;"></span> | <span style="display:inline-block;width:18px;height:18px;background:#173428;border:1px solid #999;"></span> |

Sugerencia de mapeo inicial a Streamlit (`config.toml`):

- Claro:
  - `primaryColor = "#D52E25"`
  - `backgroundColor = "#F7F9FC"`
  - `secondaryBackgroundColor = "#FFFFFF"`
  - `textColor = "#1F2937"`
- Oscuro:
  - `primaryColor = "#F0625D"`
  - `backgroundColor = "#12161C"`
  - `secondaryBackgroundColor = "#1A2230"`
  - `textColor = "#E6EDF7"`

### Validación WCAG de la paleta (resumen)

- Se validaron combinaciones de texto/fondo y bordes en claro y oscuro con criterios:
  - Texto normal: AA >= 4.5:1
  - Elementos no texto (bordes/focus): >= 3:1
- Ajustes aplicados a la propuesta para cumplir:
  - `--text-muted` (light) -> `#5F6E80`
  - `--placeholder` (light) -> `#6B7785`
  - `--brand-secondary` (dark) -> `#5AA2D9`
  - `--border-default` (light) -> `#7A889A`
  - `--border-default` (dark) -> `#5C6E85`

### 2) Configurar tema nativo de Streamlit

- Crear `.streamlit/config.toml` con:
  - base clara y colores de marca para light.
  - base dark y equivalentes dark para contraste y legibilidad.
- Priorizar que `background`, `secondaryBackground`, `textColor` y `primaryColor` queden coherentes con la paleta de tokens.

### 3) Refactor del CSS actual

- Reemplazar hardcodes de color por tokens.
- Resolver los puntos de conflicto actuales:
  - `app.py:1393` (`color-scheme: light`) -> retirar o condicionar por tema activo.
  - Inputs/placeholders/autofill en Android/WebKit -> mantener overrides, pero tokenizados.
- Conservar identidad Taranto (rojo/azul) con contraste correcto en dark.

### 4) Alinear componentes críticos

- Header, navegación, tabs, cards, botones, formularios, chat bubbles, barra inferior.
- `st.dataframe`:
  - No depender de CSS agresivo externo.
  - Usar tema nativo y validar encabezados, filas, selección y contraste.

### 5) Pruebas funcionales y visuales

- Plataformas:
  - Desktop (Chrome/Edge).
  - Android Chrome en modo oscuro y claro.
- Flujos:
  - Chat IA.
  - Modo formulario completo (filtros, edición, subtareas, comentarios).
  - Grillas principales (`st.dataframe`).
- Criterio de aceptación:
  - Paridad visual profesional entre claro y oscuro (sin sensación de modo "secundario").
  - Sin texto ilegible.
  - Sin mezcla de superficies claras/oscuras no intencional.
  - Contraste consistente en estados `hover/focus/active/disabled`.

### 6) Fase 2 opcional: selector manual de tema

- Agregar selector `Claro / Oscuro / Automático`.
- Guardar preferencia en `st.session_state`.
- Definir precedencia:
  - Manual > Automático por sistema.
- Validar que el cambio de tema rerenderice correctamente todos los componentes.

## Riesgos y mitigaciones

- Riesgo: mezcla de estilos entre tema nativo y CSS custom.
  - Mitigación: reducir CSS custom a branding/tokens y evitar reglas globales invasivas.
- Riesgo: inconsistencias en Android (autofill/forzado de contraste).
  - Mitigación: mantener reglas WebKit específicas, tokenizadas y testeadas en dispositivo real.
- Riesgo: `st.dataframe` no responde como HTML estándar.
  - Mitigación: priorizar configuración de tema nativo sobre hacks CSS.

## Entregables

1. Configuración de tema nativo en `.streamlit/config.toml` (light + dark).
2. CSS refactorizado con tokens semánticos.
3. Ajuste de la regla temporal de `app.py:1393`.
4. Validación visual documentada para desktop y Android.
5. (Opcional) Selector manual de tema en Fase 2.
