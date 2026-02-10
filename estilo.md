# Guía Estética del Proyecto Viejo (GESTAR v2)

Este documento resume las reglas visuales y de UX observadas en el proyecto legacy (`Tickets/gestar`), sin cambiar código.

## 1) Identidad visual

- Estilo institucional Taranto con enfoque corporativo-industrial.
- UI clara, de alto contraste y jerarquía fuerte.
- Uso dominante de acentos en rojo y azul de marca.

## 2) Paleta de colores

- Rojo primario de marca: `#d52e25`.
- Azul institucional secundario: `#156099`.
- Neutros frecuentes:
- Texto principal: `#444`, `#555`.
- Fondos/superficies: `#fff`, `#f5f5f5`, `#eee`.
- Bordes suaves: grises claros y opacidades bajas.

Patrón de uso:
- Rojo para acciones primarias, títulos acentuados y línea divisoria.
- Azul para tabs activas, íconos y enlaces/acciones secundarias.

## 3) Tipografía

- Fuente base: `Lato` (texto corrido).
- Fuente de títulos: `Raleway` (peso alto).
- Convención de navegación y botones:
- Mayúsculas.
- Tracking leve (`letter-spacing` aprox `0.5px`).
- Peso fuerte.

## 4) Estructura y layout

- `layout="wide"` en Streamlit.
- Sidebar colapsado inicialmente.
- Estructura superior en tres bloques:
- Logo.
- Título principal.
- Bloque de acciones/sesión (inicio, refresh, usuario).
- Línea divisoria roja bajo el header.
- Fila de navegación principal con botones horizontales.
- Página interna por secciones (Crear, Bandeja, Mis tareas, Solicitud sencilla, Admin).

## 5) Componentes visuales

### Header / Top bar
- Barra limpia con borde inferior rojo.
- Íconos Bootstrap en azul.
- Presencia de marca (logo + título “GESTAR”).

### Botones
- Bordes discretos, look compacto.
- Botón primario en rojo.
- Botones de navegación con estado activo destacado (`active-nav`).

### Tabs
- Tabs con fondo neutro por defecto.
- Tab activa en azul con texto blanco.
- Separación moderada entre tabs.

### Tarjetas
- Superficie blanca, borde sutil, radio mediano.
- Sombra suave para profundidad baja.

### Tablas y grillas
- Dataframe con bordes redondeados y sombra suave.
- Filas compactas y separadores horizontales finos.
- Enlaces tipo “link-button” (botón visualmente como texto subrayado).

### Badge de usuario
- Contenedor tipo pill, fondo neutro, borde suave.
- Muestra usuario/rol/área de forma resumida.

## 6) Lenguaje de interacción

- Tono operativo y directo.
- Títulos de sección con ícono + verbo de acción:
- “Nueva Solicitud”
- “Gestión y Asignación”
- “Mis Tareas Pendientes”
- Validación visible e inmediata con `success`, `warning`, `error`.
- Flujo orientado a productividad:
- Crear rápido.
- Ver bandeja.
- Entrar al detalle.
- Ejecutar acciones de gestión.

## 7) Convenciones técnicas de estilo (legacy)

- CSS centralizado en `style_v2.css`.
- Íconos externos por CDN (`bootstrap-icons`).
- Ocultación de elementos nativos de Streamlit:
- `header { visibility: hidden; }`
- `footer { visibility: hidden; }`
- Uso de selectores específicos de Streamlit para personalización fina.

## 8) Principios de diseño implícitos

- Prioridad a claridad funcional sobre decoración.
- Marca visible pero no invasiva.
- Densidad media-alta de información para operación diaria.
- Consistencia cromática:
- Rojo = acción principal/identidad.
- Azul = navegación/estado activo secundario.

## 9) Resumen para replicar en el proyecto nuevo

- Mantener `Lato + Raleway`.
- Conservar acentos `#d52e25` y `#156099`.
- Repetir patrón de header corporativo + nav horizontal por módulos.
- Usar tarjetas y tablas compactas con bordes/sombras suaves.
- Mantener botones en mayúsculas y jerarquía primaria/ secundaria bien marcada.
- Reproducir tabs activas en azul y acciones primarias en rojo.
- Sostener tono operativo, sin copy decorativo.

## Fuentes revisadas

- `C:\Users\GAUTOP\OneDrive - TARANTO SAN JUAN SA\Documentos\PROYECTOS APP\Tickets\gestar\style_v2.css`
- `C:\Users\GAUTOP\OneDrive - TARANTO SAN JUAN SA\Documentos\PROYECTOS APP\Tickets\gestar\ESTILOS_CSS.md`
- `C:\Users\GAUTOP\OneDrive - TARANTO SAN JUAN SA\Documentos\PROYECTOS APP\Tickets\gestar\estilo_web_taranto.md`
- `C:\Users\GAUTOP\OneDrive - TARANTO SAN JUAN SA\Documentos\PROYECTOS APP\Tickets\gestar\app_v2.py`
