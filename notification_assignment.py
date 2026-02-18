import json
import os
import smtplib
import threading
import time
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from html import escape


_WORKER_LOCK = threading.Lock()
_WORKER_STARTED = False
_WORKER_THREAD = None
_RUNTIME = {}


def build_assignment_dedupe_key(ticket_id, old_assignee_id, new_assignee_id, ticket_updated_at):
    if isinstance(ticket_updated_at, datetime):
        updated_at_iso = ticket_updated_at.isoformat()
    else:
        updated_at_iso = str(ticket_updated_at)
    return f"{ticket_id}:{old_assignee_id}->{new_assignee_id}:{updated_at_iso}"


def start_assignment_notification_worker_once(
    get_connection,
    get_schema,
    app_url,
    poll_seconds=5,
    smtp_config=None,
):
    global _WORKER_STARTED, _WORKER_THREAD, _RUNTIME
    with _WORKER_LOCK:
        if _WORKER_STARTED:
            return False
        _RUNTIME = {
            "get_connection": get_connection,
            "get_schema": get_schema,
            "app_url": app_url or os.getenv("APP_BASE_URL", ""),
            "poll_seconds": max(1, int(poll_seconds)),
            "smtp_config": smtp_config or {},
        }
        _WORKER_THREAD = threading.Thread(
            target=_worker_loop,
            name="assignment-notification-worker",
            daemon=True,
        )
        _WORKER_THREAD.start()
        _WORKER_STARTED = True
        return True


def _worker_loop():
    while True:
        try:
            _process_pending_notifications_batch()
        except Exception:
            # El worker no debe caerse por errores puntuales.
            pass
        time.sleep(_RUNTIME["poll_seconds"])


def _qname(table_name):
    return f"{_RUNTIME['get_schema']()}.{table_name}"


def _process_pending_notifications_batch(batch_size=20):
    conn = _RUNTIME["get_connection"]()
    try:
        cursor = conn.cursor()
        top_n = max(1, int(batch_size))
        cursor.execute(
            f"""
            SELECT TOP {top_n}
                p.LogId,
                p.TicketId,
                p.UserId,
                p.OldValue,
                p.NewValue
            FROM {_qname('TicketLogs')} p
            WHERE p.FieldName = 'NotificacionPendiente'
              AND NOT EXISTS (
                  SELECT 1
                  FROM {_qname('TicketLogs')} e
                  WHERE e.TicketId = p.TicketId
                    AND e.FieldName = 'NotificacionEnviada'
                    AND e.OldValue = p.OldValue
              )
            ORDER BY p.ChangedAt ASC, p.LogId ASC
            """
        )
        rows = cursor.fetchall()
    finally:
        conn.close()

    for row in rows:
        pending_log_id, ticket_id, actor_user_id, dedupe_key, payload_raw = row
        _process_one_pending(
            pending_log_id=pending_log_id,
            ticket_id=ticket_id,
            actor_user_id=actor_user_id,
            dedupe_key=dedupe_key,
            payload_raw=payload_raw,
        )


def _process_one_pending(pending_log_id, ticket_id, actor_user_id, dedupe_key, payload_raw):
    payload = _safe_json_loads(payload_raw)
    assignee_id = payload.get("new_assignee_id")
    if assignee_id is None:
        _insert_delivery_log(ticket_id, actor_user_id, dedupe_key, "ERROR:missing_new_assignee_id")
        return

    title = payload.get("title") or ""
    estado = payload.get("estado") or ""
    assigned_by = payload.get("assigned_by") or "Sistema"
    recipient_email, _recipient_username = _fetch_user_contact(assignee_id)
    if not recipient_email:
        _insert_delivery_log(ticket_id, actor_user_id, dedupe_key, "ERROR:assignee_without_email")
        return

    subject = f"Nuevo ticket asignado #{ticket_id}"
    body_html = _build_assignment_mail_html(
        ticket_id=ticket_id,
        title=title,
        estado=estado,
        assigned_by=assigned_by,
        app_url=_RUNTIME.get("app_url", ""),
    )

    try:
        _send_html_mail_smtp(to_email=recipient_email, subject=subject, html_body=body_html)
        _insert_delivery_log(ticket_id, actor_user_id, dedupe_key, "OK")
    except Exception as exc:
        err_detail = str(exc).strip()
        if len(err_detail) > 240:
            err_detail = err_detail[:240]
        _insert_delivery_log(
            ticket_id,
            actor_user_id,
            dedupe_key,
            f"ERROR:{err_detail or 'smtp_send_failed'}",
        )


def _safe_json_loads(raw_text):
    if not raw_text:
        return {}
    try:
        return json.loads(raw_text)
    except Exception:
        return {}


def _fetch_user_contact(user_id):
    conn = _RUNTIME["get_connection"]()
    try:
        cursor = conn.cursor()
        cursor.execute(
            f"SELECT TOP 1 Username, Email FROM {_qname('Users')} WHERE UserId = ?",
            (user_id,),
        )
        row = cursor.fetchone()
        if not row:
            return None, None
        return row[1], row[0]
    finally:
        conn.close()


def _insert_delivery_log(ticket_id, actor_user_id, dedupe_key, result):
    conn = _RUNTIME["get_connection"]()
    try:
        cursor = conn.cursor()
        cursor.execute(
            f"""
            INSERT INTO {_qname('TicketLogs')} (TicketId, UserId, IsAi, FieldName, OldValue, NewValue)
            VALUES (?, ?, 0, 'NotificacionEnviada', ?, ?)
            """,
            (ticket_id, actor_user_id, str(dedupe_key), str(result)),
        )
        conn.commit()
    finally:
        conn.close()


def _build_assignment_mail_html(ticket_id, title, estado, assigned_by, app_url):
    ticket_id_safe = escape(str(ticket_id))
    title_safe = escape(str(title or "Sin titulo"))[:120]
    estado_safe = escape(str(estado or "Sin estado"))
    assigned_by_safe = escape(str(assigned_by or "Sistema"))
    app_url_safe = escape(str(app_url or ""))
    return (
        f"<p>Se te ha asignado el ticket #{ticket_id_safe}</p>"
        f"<p><strong>Titulo:</strong> {title_safe}</p>"
        f"<p><strong>Estado:</strong> {estado_safe}</p>"
        f"<p><strong>Asignado por:</strong> {assigned_by_safe}</p>"
        f"<p>Ingresa a la aplicacion para gestionarlo:<br>"
        f"<a href=\"{app_url_safe}\">{app_url_safe}</a></p>"
        f"<p>Este es un mensaje automatico.</p>"
    )


def _send_html_mail_smtp(to_email, subject, html_body):
    smtp_cfg = _RUNTIME.get("smtp_config", {})
    smtp_host = smtp_cfg.get("SMTP_HOST") or os.getenv("SMTP_HOST")
    smtp_port = int(smtp_cfg.get("SMTP_PORT") or os.getenv("SMTP_PORT", "587"))
    smtp_user = smtp_cfg.get("SMTP_USER") or os.getenv("SMTP_USER")
    smtp_password = smtp_cfg.get("SMTP_PASSWORD") or os.getenv("SMTP_PASSWORD")
    smtp_sender = smtp_cfg.get("SMTP_SENDER") or os.getenv("SMTP_SENDER")

    missing = [
        key
        for key, value in [
            ("SMTP_HOST", smtp_host),
            ("SMTP_PORT", smtp_port),
            ("SMTP_USER", smtp_user),
            ("SMTP_PASSWORD", smtp_password),
            ("SMTP_SENDER", smtp_sender),
        ]
        if value in (None, "")
    ]
    if missing:
        raise RuntimeError(f"missing_smtp_config:{','.join(missing)}")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = smtp_sender
    msg["To"] = to_email
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    with smtplib.SMTP(smtp_host, smtp_port, timeout=30) as server:
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(smtp_user, smtp_password)
        server.sendmail(smtp_sender, [to_email], msg.as_string())
