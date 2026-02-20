# Plan Técnico v1 - Notificación automática por cambio de responsable (SMTP)

## 1. Objetivo
Implementar notificación automática cuando cambie `AssigneeId` (equivalente a `AsignadoA`), con trazabilidad completa en `TicketLogs`, procesamiento asíncrono robusto para Streamlit y envío de email por SMTP (Office 365 SMTP AUTH).

## 2. Detección actual del cambio
La detección de cambios ocurre en `update_ticket_from_form` (`app.py`) al comparar valores actuales vs nuevos (`changed_items`).
El cambio relevante es `AssigneeId`.

## 3. Diseño propuesto (desacoplado y robusto)

### 3.1 Outbox light en TicketLogs
Usar `TicketLogs` como registro de eventos y cola ligera:
- `FieldName = CambioAsignacion`
  - `OldValue = responsable anterior`
  - `NewValue = responsable nuevo`
- `FieldName = NotificacionPendiente`
  - `OldValue = dedupe_key`
  - `NewValue = payload mínimo serializado`
- `FieldName = NotificacionEnviada`
  - `OldValue = dedupe_key`
  - `NewValue = OK` o `ERROR:<detalle>`

`CambioAsignacion` y `NotificacionPendiente` se escriben en la misma transacción del update del ticket.

### 3.2 Worker singleton resistente a reruns
Implementar worker en módulo dedicado (`notification_assignment.py`) con:
- lock global de módulo (`threading.Lock`)
- bandera global de inicialización
- arranque idempotente (`start_worker_once`)
- thread daemon único por proceso

### 3.3 Polling explícito (MVP)
- Frecuencia fija: cada 5 segundos.
- Configurable opcional por env (`NOTIF_POLL_SECONDS`, default `5`).

### 3.4 Consumo de pendientes
El worker procesa `NotificacionPendiente` que no tengan `NotificacionEnviada=OK` para el mismo `dedupe_key`.

## 4. Reglas de negocio
- Disparar solo ante cambio real (`old_assignee_id != new_assignee_id`).
- No disparar si se guardan otros campos sin cambio de responsable.
- Excluir tickets en estado `cerrado` o `cancelado` (por nombre normalizado).
- Si falla el envío, no bloquear la operación principal.
- Evitar duplicados con dedupe por `dedupe_key` en `OldValue` de `NotificacionEnviada`.

## 5. Dedupe key (determinístico)
Formato:
`{ticket_id}:{old_assignee_id}->{new_assignee_id}:{ticket_updated_at_iso}`

Fuente de `ticket_updated_at_iso`:
- usar exactamente el `UpdatedAt` persistido en DB tras el update.

## 6. Historial y trazabilidad
- No eliminar registros históricos.
- No sobrescribir eventos previos.
- Cada intento/envío genera un nuevo `NotificacionEnviada`.
- Idempotencia de envío real basada en existencia de `NotificacionEnviada=OK` para `dedupe_key`.

## 7. Canal SMTP (Office 365 SMTP AUTH)

### 7.1 Variables de entorno obligatorias
- `SMTP_HOST`
- `SMTP_PORT`
- `SMTP_USER`
- `SMTP_PASSWORD`
- `SMTP_SENDER`

### 7.2 Conexión y autenticación
- Usar `smtplib.SMTP(SMTP_HOST, SMTP_PORT)`.
- Ejecutar `starttls()` antes de login.
- Autenticar con `SMTP_USER` / `SMTP_PASSWORD`.
- Enviar con remitente `SMTP_SENDER`.

## 8. Formato de notificación (MVP)
- Email HTML simple con el template definido en la spec.
- Sin adjuntos.
- Sin deep link.
- Sin datos sensibles.
- Escape HTML obligatorio de campos interpolados (`title`, `estado`, `assigned_by`, etc.).

## 9. Componentes impactados
- `app.py`
  - Hook en `update_ticket_from_form` para `AssigneeId`.
  - Alta transaccional de `CambioAsignacion` + `NotificacionPendiente`.
  - Bootstrap del worker singleton.
- `notification_assignment.py` (nuevo)
  - generación de `dedupe_key`
  - worker singleton + polling
  - envío SMTP (STARTTLS + AUTH)
  - log de `NotificacionEnviada`

## 10. Ejemplo breve en Python (smtplib)
```python
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_html_mail(to_email: str, subject: str, html_body: str) -> None:
    host = os.getenv("SMTP_HOST")
    port = int(os.getenv("SMTP_PORT", "587"))
    user = os.getenv("SMTP_USER")
    password = os.getenv("SMTP_PASSWORD")
    sender = os.getenv("SMTP_SENDER")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = to_email
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    with smtplib.SMTP(host, port, timeout=30) as server:
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(user, password)
        server.sendmail(sender, [to_email], msg.as_string())
```

## 11. Casos de prueba
1. Cambio real de responsable en ticket abierto: crea `CambioAsignacion` + `NotificacionPendiente`; worker envía y registra `NotificacionEnviada=OK`.
2. Guardado sin cambio de `AssigneeId`: no crea eventos de notificación.
3. Ticket en `Cerrado`/`Cancelado`: no crea `NotificacionPendiente`.
4. Falla SMTP/auth: ticket se actualiza igual y registra `NotificacionEnviada=ERROR:<detalle>`.
5. Reruns de Streamlit: no se levantan workers duplicados.
6. Dos cambios rápidos: sin colisión de dedupe por uso de `UpdatedAt` persistido.

## 12. Compatibilidad y alcance
- No cambia modelo de `Tickets`.
- No introduce permisos.
- No agrega deep linking.
- No modifica funcionalidades no relacionadas.
