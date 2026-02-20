# 📄 Feature Specification

## Notificación automática por cambio de responsable

**Versión:** 1.0
**Tipo:** Minor

---

## 1. Problema que resuelve

El responsable asignado puede no tomar conocimiento oportuno de una nueva asignación de ticket, generando demoras operativas y ambigüedad.

Este cambio elimina el desconocimiento sobre la asignación.

---

## 2. Usuario principal

Responsable asignado al ticket.

Usuario secundario: Supervisor/Jefe que realiza la asignación.

---

## 3. Resultado esperado

Cuando el campo `AsignadoA` cambie:

* El nuevo responsable recibe una notificación automática por email.
* El evento queda registrado en la tabla de log.
* Existe trazabilidad tanto del cambio como del envío.

---

## 4. Alcance del MVP

Incluye:

* Detección de cambio real en el campo `AsignadoA`.
* Registro en tabla `LogEventos` del evento:

  * TipoEvento: `CambioAsignacion`
  * ValorAnterior
  * ValorNuevo
  * UsuarioQueModifica
* Envío de notificación por email corporativo.
* Registro en `LogEventos` del evento:

  * TipoEvento: `NotificacionEnviada`
  * Destinatario
  * Resultado (OK / Error)
* Enlace a la aplicación (no deep link a ticket).
* Exclusión de tickets en estado Cerrado o Cancelado.

No incluye:

* Recordatorios por SLA.
* Escalamiento automático.
* Notificaciones por comentarios.
* Validación de permisos (se implementará en fase Entra ID).
* Deep link directo al ticket.

---

## 5. Modelo de datos impactado

No se agregan campos nuevos a la tabla `Tickets`.

Se utiliza la tabla existente `LogEventos` para registrar:

1. CambioAsignacion
2. NotificacionEnviada

---

## 6. Reglas de negocio

* La notificación se dispara solo si `AsignadoA` cambia efectivamente.
* No se dispara si se guardan otros campos sin modificar el responsable.
* Si el responsable cambia nuevamente, el proceso se repite.
* El envío debe ser asíncrono.
* El fallo de envío no debe bloquear la asignación; debe registrarse como error en log.

---

## 7. Riesgos técnicos

* Duplicación de notificaciones si el cambio no se controla correctamente.
* Registro inconsistente si falla el envío.
* Exposición de datos sensibles si el contenido del mail no se limita.

---

## 8. Métrica de éxito

* 100% de cambios de responsable con evento de notificación registrado.
* Reducción del tiempo promedio entre asignación y primera acción del responsable.

---

## 9. Impacto en versionado

Cambio clasificado como **Minor**.
