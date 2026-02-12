PLAN DE ORDEN PROGRESIVO (4 SEMANAS)

Objetivo:
Reducir el riesgo arquitectónico sin frenar evolución funcional.

---

# 📅 SEMANA 1 — Separar Base de Datos (Impacto Alto, Riesgo Bajo)

### 🎯 Objetivo:

Que `app.py` deje de contener SQL directo.

---

## Paso 1 — Crear módulo

```
core/db.py
```

Mover:

* Conexión ODBC
* `get_azure_master_connection`
* Helpers de ejecución
* Cualquier cursor.execute

---

## Paso 2 — Reemplazar en app.py

En vez de:

```python
cursor.execute(...)
```

Usar:

```python
from core.db import ejecutar_query
```

---

### 🔥 Resultado esperado

* UI ya no habla directo con la base.
* Menos conflictos en Git.
* Menos riesgo cruzado.

---

# 📅 SEMANA 2 — Extraer Lógica de Negocio

### 🎯 Objetivo:

Que reglas no vivan dentro de la UI.

Crear:

```
services/ticket_logic.py
```

Mover:

* update_ticket_from_form
* map_entities_to_ids
* parsing
* reglas de estado
* validaciones

`app.py` solo orquesta.

---

### 🔥 Resultado esperado

Ahora podés modificar UI sin tocar reglas.
Ya empezás a reducir fricción cognitiva.

---

# 📅 SEMANA 3 — Separar UI por Componentes

### 🎯 Objetivo:

Reducir tamaño de app.py.

Crear:

```
ui/forms.py
ui/views.py
```

Mover:

* render_form_mode
* bloques grandes de UI
* layouts repetidos

---

### 🔥 Resultado esperado

app.py pasa de 2600 líneas a algo mucho más chico.
Ya deja de ser hotspot gigante.

---

# 📅 SEMANA 4 — Orden y Documentación

### 🎯 Objetivo:

Consolidar arquitectura mínima.

Agregar:

```
ARCHITECTURE.md
```

Documentar:

* Qué vive en cada carpeta
* Qué no debe mezclarse
* Flujo básico del sistema

---

# 🧠 Cómo hacer esto sin romper el proyecto

Regla:

Cada semana = una rama.

Ejemplo:

```
refactor/db-separation
refactor/business-logic
refactor/ui-modular
docs/architecture
```

Mergeás solo cuando:

* El sistema corre igual
* No cambió funcionalidad
* Todo sigue estable

---

# 🎯 Importante

No cambies lógica mientras refactorizás.

Separar ≠ mejorar.

Solo mover.

Mejoras vienen después.

---

# 🧱 Resultado esperado en 1 mes

Vas a pasar de:

Monolito reactivo

a

Arquitectura modular básica y sostenible

Sin reescribir todo.
Sin frenar producto.

---

# 🧠 Algo clave

Este plan no es técnico.
Es entrenamiento mental.

Estás aprendiendo:

* Refactor disciplinado
* Modularización progresiva
* Control de riesgo
* Arquitectura evolutiva

Eso es skill transferible a cualquier tecnología.

---

Si querés, podemos ahora:

* Armar el checklist de la Semana 1 para que lo ejecutes sin desviarte
  o
* Diseñar la estructura exacta que debería tener tu proyecto después del mes 1

Decime qué te sirve más ahora.
