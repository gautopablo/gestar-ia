# GESTAR — Documento Técnico: Sistema de Roles y Permisos

**Versión:** 2.0  
**Fecha:** 2026-02-20  
**Aplicación de referencia:** GESTAR v2 — Gestión de Solicitudes (Taranto)  
**Stack:** Python / Streamlit / SQLite (fallback Azure SQL)

---

## 1. Propósito

Este documento describe el **modelo de roles de usuario** implementado en GESTAR v2 (`app_v2.py` / `db.py` / `models.py`). Su objetivo es servir como **referencia técnica portable** para replicar el esquema de autorización en otras aplicaciones, independientemente del stack tecnológico utilizado.

---

## 2. Modelo de Datos — Tabla `users`

Cada usuario del sistema está registrado con los siguientes atributos:

| Campo             | Tipo    | Descripción                                        |
| ----------------- | ------- | -------------------------------------------------- |
| `id`              | INT     | Identificador único autoincremental                |
| `nombre_completo` | TEXT    | Nombre del usuario (clave funcional en el sistema) |
| `email`           | TEXT    | Correo electrónico (opcional, para notificaciones) |
| `rol`             | TEXT    | Rol asignado (ver catálogo de roles)               |
| `area`            | TEXT    | Área funcional a la que pertenece el usuario       |
| `activo`          | INTEGER | `1` = activo / `0` = inactivo (soft delete)        |

> **Clave de diseño:** El campo `area` es el eje de la **segmentación horizontal** dentro de los roles de gestión. Un Jefe o Analista solo opera sobre tickets de su propio área.

---

## 3. Catálogo de Roles (`ROLES`)

Los roles son valores maestros configurables almacenados en la tabla `master_catalog_items` (catálogo `roles`). El conjunto inicial definido en `models.py` es:

```python
ROLES = ["Solicitante", "Analista", "Jefe", "Director", "Administrador"]
```

---

## 4. Descripción Detallada de Cada Rol

### 4.1 `Solicitante`

**Perfil:** Usuario final que genera solicitudes de trabajo.

**Lo que PUEDE hacer:**

- Crear tickets a través del formulario completo ("Crear Ticket") o del formulario simplificado ("Solicitud Sencilla").
- Completar campos del ticket: título, descripción, área destino, categoría/subcategoría, división, planta.
- Sugerir una urgencia (`urgencia_sugerida`). **Esta no es la prioridad final.**
- Sugerir un responsable (`responsable_sugerido`). **Esta no es la asignación formal.**
- Ver el historial y descripción de sus propios tickets.
- Agregar comentarios en el historial de cualquier ticket.
- Ver sus tareas asignadas en "Mis Tareas".

**Lo que NO puede hacer:**

- Asignar formalmente un responsable (`responsable_asignado`).
- Cambiar el estado del ticket.
- Cambiar la prioridad formal del ticket.
- Ver ni acceder al módulo de Administración.

**Regla clave:**

> La prioridad siempre se inicializa en `"Media"` al crear el ticket. El Solicitante solo puede sugerir, nunca definir.

---

### 4.2 `Analista`

**Perfil:** Técnico operativo de un área. Atiende y ejecuta los tickets que le son asignados.

**Lo que PUEDE hacer:**

- Todo lo que puede el Solicitante.
- **Tomar un ticket** de la cola de su área (acción "🙋 TOMAR TICKET"):
  - El ticket pasa de estado `NUEVO` → `ASIGNADO`, y el Analista queda como `responsable_asignado`.
  - Esta acción solo está disponible si el ticket tiene estado `NUEVO` **y** el `area_destino` del ticket coincide con el `area` del Analista.
- Ver en la Bandeja la pestaña "**COLA**" filtrada solo por su área y estado `NUEVO`.
- Ver en la Bandeja la pestaña "**MIS TICKETS**" (tickets donde él es `responsable_asignado`, en estado `ASIGNADO` o `EN PROCESO`).
- Actualizar el **estado** del ticket que tiene asignado.
- Actualizar la **prioridad** del ticket.

**Lo que NO puede hacer:**

- **Asignar formalmente el ticket a otra persona.** El campo `responsable_asignado` aparece como campo de texto deshabilitado.
- Tomar tickets de áreas distintas a la suya.
- Acceder al módulo de Administración.

**Regla clave:**

> El Analista puede tomar pero no reasignar. La asignación a terceros es potestad del Jefe o Director.

---

### 4.3 `Jefe`

**Perfil:** Responsable de un área. Puede tomar tickets Y asignarlos a otros usuarios.

**Lo que PUEDE hacer:**

- Todo lo que puede el Analista.
- **Tomar un ticket** de la cola de su área (igual que el Analista).
- **Asignar formalmente** el ticket a cualquier usuario del sistema a través del selector `responsable_asignado`.
  - La condición es: `c_role == "Jefe"` **y** `ticket["area_destino"] == c_area`.
- Cambiar el estado del ticket a cualquier valor del ciclo (`NUEVO`, `ASIGNADO`, `EN PROCESO`, `RESUELTO`, `CERRADO`).
- Cambiar la prioridad del ticket.
- Acceder a la Bandeja completa incluyendo filtros de área en "En Proceso".

**Lo que NO puede hacer:**

- Asignar tickets de otras áreas (salvo que sea Director).
- Acceder al módulo de Administración.

**Regla clave:**

> El Jefe tiene control total sobre su área. La lógica de autorización para asignación es:  
> `can_assign = (c_role == "Director") OR (c_role == "Jefe" AND ticket["area_destino"] == c_area)`

---

### 4.4 `Director`

**Perfil:** Rol transversal con visibilidad y capacidad de acción sobre **todas las áreas**.

**Lo que PUEDE hacer:**

- Todo lo que puede el Jefe, pero **sin restricción de área**.
- Tomar tickets de **cualquier área** (la condición `area_destino == c_area` no aplica).
- Asignar tickets de **cualquier área** a cualquier usuario.
- Ver la pestaña "**COLA**" con **todos los tickets en estado NUEVO** (sin filtro de área):
  ```python
  # Cuando el Director está activo, el filtro de area NO se aplica:
  "area_destino": c_area if c_role != "Director" else None
  ```
- Ver la Bandeja completa con capacidad de filtrar por área desde "En Proceso".

**Lo que NO puede hacer:**

- Acceder al módulo de Administración (eso es exclusivo del rol Administrador).

---

### 4.5 `Administrador`

**Perfil:** Superusuario técnico. Gestiona la configuración base del sistema.

**Lo que PUEDE hacer:**

- Todo lo que puede el Director (hereda visibilidad transversal).
- Acceder al módulo **ADMIN** (visible solo para este rol en la barra de navegación):
  - **Pestaña Usuarios:** Crear nuevos usuarios, editar rol, área, email y estado (activo/inactivo) de usuarios existentes.
  - **Pestaña Maestras:** Gestionar los catálogos del sistema (Áreas, Divisiones, Plantas, Prioridades, Roles, Categorías y Subcategorías). Puede agregar, editar, reordenar y activar/desactivar items de catálogo.

**Regla clave:**

> El acceso al módulo ADMIN está protegido en dos niveles:
>
> 1. El botón "ADMIN" en la navegación **solo se renderiza** si `cur_r == "Administrador"`.
> 2. Al renderizar la página, se valida nuevamente: `if cur_r == "Administrador": show_admin() else: st.error("Acceso denegado.")`.

---

## 5. Matriz de Permisos Consolidada

| Acción                               | Solicitante | Analista | Jefe | Director | Administrador |
| ------------------------------------ | :---------: | :------: | :--: | :------: | :-----------: |
| Crear ticket (completo)              |     ✅      |    ✅    |  ✅  |    ✅    |      ✅       |
| Crear solicitud sencilla             |     ✅      |    ✅    |  ✅  |    ✅    |      ✅       |
| Ver bandeja / todos los tickets      |     ✅      |    ✅    |  ✅  |    ✅    |      ✅       |
| Ver cola de su área (NUEVO)          |     ❌      |    ✅    |  ✅  |    ✅    |      ✅       |
| Ver cola de TODAS las áreas          |     ❌      |    ❌    |  ❌  |    ✅    |      ✅       |
| Tomar ticket (de su área)            |     ❌      |    ✅    |  ✅  |    ✅    |      ✅       |
| Tomar ticket (cualquier área)        |     ❌      |    ❌    |  ❌  |    ✅    |      ✅       |
| Asignar responsable (su área)        |     ❌      |    ❌    |  ✅  |    ✅    |      ✅       |
| Asignar responsable (cualquier área) |     ❌      |    ❌    |  ❌  |    ✅    |      ✅       |
| Cambiar estado del ticket            |     ❌      |    ✅    |  ✅  |    ✅    |      ✅       |
| Cambiar prioridad del ticket         |     ❌      |    ✅    |  ✅  |    ✅    |      ✅       |
| Agregar comentarios                  |     ✅      |    ✅    |  ✅  |    ✅    |      ✅       |
| Agregar/completar tareas             |     ✅      |    ✅    |  ✅  |    ✅    |      ✅       |
| Ver "Mis Tareas"                     |     ✅      |    ✅    |  ✅  |    ✅    |      ✅       |
| Acceder a módulo Admin               |     ❌      |    ❌    |  ❌  |    ❌    |      ✅       |
| Gestionar usuarios                   |     ❌      |    ❌    |  ❌  |    ❌    |      ✅       |
| Gestionar tablas maestras            |     ❌      |    ❌    |  ❌  |    ❌    |      ✅       |

---

## 6. Flujo de Vida de un Ticket y Quién Interviene

```
[SOLICITANTE] → Crea ticket
     ↓ Estado: NUEVO

[ANALISTA / JEFE / DIRECTOR] → Toma el ticket o lo asigna
     ↓ Estado: ASIGNADO

[ANALISTA / JEFE / DIRECTOR] → Comienza a trabajar
     ↓ Estado: EN PROCESO

[ANALISTA / JEFE] → Marca como resuelto
     ↓ Estado: RESUELTO

[JEFE / DIRECTOR / ADMIN] → Cierre formal
     ↓ Estado: CERRADO
```

### Campos de Asignación (Distinción entre Sugerencia y Asignación Formal)

| Campo                  | Quién lo completa   | Obligatorio      | Peso en el flujo           |
| ---------------------- | ------------------- | ---------------- | -------------------------- |
| `responsable_sugerido` | Solicitante         | No               | Solo referencia/sugerencia |
| `responsable_asignado` | Jefe / Director     | No (según flujo) | **Es la asignación real**  |
| `solicitante`          | Solicitante         | Sí               | Identifica al creador      |
| `created_by`           | Automático (sesión) | Sí               | Auditoría                  |

---

## 7. Implementación Técnica en Código

### 7.1 Obtención del Perfil en Sesión

```python
# Al inicio de la app, se resuelve el usuario activo desde la sesión:
u_info = db.get_user_by_name(st.session_state["v2_user_name"])
if u_info:
    cur_u = u_info["nombre_completo"]  # Nombre
    cur_r = u_info["rol"]              # Rol
    cur_a = u_info["area"]             # Área
else:
    cur_u, cur_r, cur_a = st.session_state["v2_user_name"], "Solicitante", "IT"
```

### 7.2 Control de Navegación (Menú)

```python
# El botón ADMIN solo se muestra si el rol es Administrador
with c_nav5:
    if cur_r == "Administrador":
        if st.button("ADMIN"):
            st.session_state["v2_page"] = "ADMIN"
```

### 7.3 Lógica de "Tomar Ticket"

```python
# Solo Analista/Jefe de su área o Director puede tomar el ticket
can_take = (c_role == "Director") or (
    c_role in ["Analista", "Jefe"] and ticket["area_destino"] == c_area
)
if can_take:
    if st.button("🙋 TOMAR TICKET"):
        db.update_ticket(tid, {"responsable_asignado": c_user, "estado": "ASIGNADO"})
```

### 7.4 Lógica de Asignación Formal

```python
# Solo Jefe (de su área) o Director pueden editar el campo responsable_asignado
can_assign = (c_role == "Director") or (
    c_role == "Jefe" and ticket["area_destino"] == c_area
)
if can_assign:
    asig = st.selectbox("Responsable", ["Sin Asignar"] + u_names)
else:
    # El campo aparece deshabilitado (solo lectura)
    st.text_input("Responsable", value=ticket["responsable_asignado"], disabled=True)
```

### 7.5 Filtro de Cola por Área

```python
# Director ve toda la cola; los demás roles solo ven la de su área
f = {
    "estado": "NUEVO",
    "area_destino": c_area if c_role != "Director" else None,
}
```

### 7.6 Protección de Página Admin

```python
elif page == "ADMIN":
    if cur_r == "Administrador":
        show_admin()
    else:
        st.error("Acceso denegado.")
```

---

## 8. Reglas de Negocio Adicionales

1. **La prioridad final es siempre definida por quienes gestionan**, nunca por el Solicitante. El campo `urgencia_sugerida` es solo informativo.
2. **El campo `responsable_sugerido`** es un dato de referencia que puede ser respetado o ignorado por el Jefe al hacer la asignación formal.
3. **El Analista puede actualizar estado y prioridad** pero no puede cambiar el responsable asignado.
4. **Usuarios inactivos** (`activo = 0`) no aparecen en los selectores de usuarios, pero se mantienen en la base de datos para auditoría histórica.
5. **Todos los roles** pueden agregar comentarios en el historial del ticket (`ticket_log`), lo que asegura trazabilidad completa.
6. **Las tablas maestras** (áreas, roles, prioridades, categorías, etc.) son administrables en caliente por el Administrador sin necesidad de modificar código.

---

## 9. Consideraciones para Portar a Otra Aplicación

Al replicar este modelo, se recomienda:

1. **Tabla `users` con campos `rol` y `area`**: Son los dos atributos que determinan toda la lógica de acceso.
2. **Resolver perfil en sesión al inicio**: Antes de renderizar cualquier componente, obtener `(nombre, rol, area)` desde la base de datos.
3. **Implementar los 4 checks de permisos** descritos en la Sección 7:
   - Visibilidad de menú/secciones (`can_see`)
   - Acción "Tomar" (`can_take`)
   - Acción "Asignar" (`can_assign`)
   - Acceso administrativo (`can_admin`)
4. **Filtros de área**: Para roles no-Director, siempre filtrar por `area_destino == user.area`.
5. **Separar sugerencia de asignación**: Mantener `responsable_sugerido` y `responsable_asignado` como campos distintos.
6. **Doble validación en módulos protegidos**: Tanto en el menú como al renderizar la página destino.
7. **Estados de ticket bien definidos**: Usar un ciclo de estados explícito (`NUEVO → ASIGNADO → EN PROCESO → RESUELTO → CERRADO`) que permita saber en qué punto del flujo interviene cada rol.

---

_Documento generado a partir del análisis del código fuente de GESTAR v2 — `app_v2.py`, `db.py`, `models.py`._
