import streamlit as st
import pandas as pd
import json
import google.generativeai as genai
from datetime import datetime, timedelta
import base64
import os
import re
import unicodedata
from dotenv import load_dotenv
try:
    import pyodbc
except ImportError:
    pyodbc = None

# Cargar variables de entorno
load_dotenv()

# ==========================================
# 1. CONFIGURACIÓN Y BASE DE DATOS
# ==========================================

def normalize_text(value):
    if value is None:
        return ""
    text = str(value).strip().lower()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", text)


def get_secret(name, default=None):
    try:
        value = st.secrets.get(name, default)
    except Exception:
        value = default
    if value not in (None, ""):
        return value
    return os.getenv(name, default)


def get_azure_master_connection():
    conn_str = get_secret("ODBC_CONN_STR")
    if not conn_str:
        raise RuntimeError("Falta ODBC_CONN_STR en Streamlit Secrets o .env")
    if pyodbc is None:
        raise RuntimeError("pyodbc no está instalado")
    try:
        return pyodbc.connect(conn_str)
    except Exception as e:
        raise RuntimeError(f"No se pudo conectar a Azure SQL por ODBC: {e}")


def get_master_schema():
    return get_secret("DB_SCHEMA", "gestar")


def qname(table_name):
    return f"{get_master_schema()}.{table_name}"


def get_base64_image(image_path):
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except Exception:
        return ""


def get_users_by_id(master_data):
    return {u["id"]: u for u in master_data.get("usuarios", []) if u.get("id") is not None}


def ensure_session_user(master_data):
    users = master_data.get("usuarios", [])
    if not users:
        raise RuntimeError("No hay usuarios activos en la base para iniciar sesión.")
    users_by_id = get_users_by_id(master_data)
    current_id = st.session_state.get("current_user_id")
    if current_id not in users_by_id:
        st.session_state.current_user_id = users[0]["id"]


def get_session_user(master_data):
    users_by_id = get_users_by_id(master_data)
    current_id = st.session_state.get("current_user_id")
    return users_by_id.get(current_id)


def safe_parse_datetime(value):
    if not value:
        return None
    txt = normalize_text(value)
    # Quitar puntuación para tolerar entradas como "hoy." o "hoy,"
    txt = re.sub(r"[^\w\s/:-]", " ", txt)
    txt = re.sub(r"\s+", " ", txt).strip()
    now = datetime.now()

    # Quitar prefijos comunes para interpretar mejor fechas en lenguaje natural
    txt = re.sub(
        r"^(fecha|para|por|antes de|a mas tardar|como maximo|hasta)\s+",
        "",
        txt,
    )

    if txt == "hoy":
        return now.replace(hour=17, minute=0, second=0, microsecond=0)
    if txt == "manana":
        target = now + timedelta(days=1)
        return target.replace(hour=17, minute=0, second=0, microsecond=0)
    if txt == "pasado manana":
        target = now + timedelta(days=2)
        return target.replace(hour=17, minute=0, second=0, microsecond=0)

    # Expresiones de día de semana: "el proximo lunes", "proximo martes", etc.
    weekdays = {
        "lunes": 0,
        "martes": 1,
        "miercoles": 2,
        "jueves": 3,
        "viernes": 4,
        "sabado": 5,
        "domingo": 6,
    }
    m_weekday = re.search(
        r"^(el\s+)?(?:(proximo|este)\s+)?(lunes|martes|miercoles|jueves|viernes|sabado|domingo)$",
        txt,
    )
    if m_weekday:
        qualifier = m_weekday.group(2)
        target_weekday = weekdays[m_weekday.group(3)]
        delta_days = (target_weekday - now.weekday()) % 7
        # "proximo lunes": siempre la siguiente ocurrencia (si hoy es lunes, +7)
        if qualifier == "proximo" and delta_days == 0:
            delta_days = 7
        target = now + timedelta(days=delta_days)
        return target.replace(hour=17, minute=0, second=0, microsecond=0)

    m = re.search(r"dentro de (\d{1,3}) dias", txt)
    if m:
        days = int(m.group(1))
        target = now + timedelta(days=days)
        return target.replace(hour=17, minute=0, second=0, microsecond=0)

    words_to_days = {
        "un": 1,
        "uno": 1,
        "dos": 2,
        "tres": 3,
        "cuatro": 4,
        "cinco": 5,
        "seis": 6,
        "siete": 7,
        "ocho": 8,
        "nueve": 9,
        "diez": 10,
        "quince": 15,
        "veinte": 20,
        "treinta": 30,
    }
    m_words = re.search(r"dentro de ([a-z]+) dias", txt)
    if m_words and m_words.group(1) in words_to_days:
        target = now + timedelta(days=words_to_days[m_words.group(1)])
        return target.replace(hour=17, minute=0, second=0, microsecond=0)

    for fmt in (
        "%Y-%m-%d",
        "%d/%m/%Y",
        "%d-%m-%Y",
        "%Y/%m/%d",
        "%d/%m/%y",
        "%d-%m-%y",
    ):
        try:
            return datetime.strptime(str(value).strip(), fmt).replace(
                hour=17, minute=0, second=0, microsecond=0
            )
        except ValueError:
            pass
    return None


def has_relative_date_language(value):
    txt = normalize_text(value)
    return bool(
        re.search(
            r"\b(hoy|manana|pasado manana|proximo|este|que viene|semana que viene|dentro de)\b",
            txt,
        )
    )


def load_user_area_division_map():
    conn = get_azure_master_connection()
    try:
        cursor = conn.cursor()
        schema = get_master_schema()

        col_rows = cursor.execute(
            """
            SELECT LOWER(COLUMN_NAME)
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = ? AND TABLE_NAME = 'Users'
            """,
            (schema,),
        ).fetchall()
        user_cols = {row[0] for row in col_rows}
        if "username" not in user_cols:
            return {}

        has_active = "active" in user_cols
        has_area_id = "areaid" in user_cols
        has_division_id = "divisionid" in user_cols
        has_area_name = "area" in user_cols
        has_division_name = "division" in user_cols

        if has_area_id:
            active_filter = "WHERE u.Active = 1" if has_active else ""
            sql = f"""
                SELECT
                    u.Username,
                    a.Nombre AS AreaNombre,
                    COALESCE(d_from_user.Nombre, d_from_area.Nombre) AS DivisionNombre
                FROM {qname("Users")} u
                LEFT JOIN {qname("Areas")} a ON u.AreaId = a.AreaId
                LEFT JOIN {qname("Divisiones")} d_from_user
                    ON {"u.DivisionId = d_from_user.DivisionId" if has_division_id else "1=0"}
                LEFT JOIN {qname("Divisiones")} d_from_area ON a.DivisionId = d_from_area.DivisionId
                {active_filter}
            """
            rows = cursor.execute(sql).fetchall()
        elif has_area_name or has_division_name:
            select_area = "u.Area" if has_area_name else "NULL"
            select_div = "u.Division" if has_division_name else "NULL"
            active_filter = "WHERE u.Active = 1" if has_active else ""
            rows = cursor.execute(
                f"""
                SELECT
                    u.Username,
                    {select_area} AS AreaNombre,
                    {select_div} AS DivisionNombre
                FROM {qname("Users")} u
                {active_filter}
                """
            ).fetchall()
        else:
            return {}

        out = {}
        for row in rows:
            username = row[0]
            if not username:
                continue
            out[normalize_text(username)] = {"area": row[1], "division": row[2]}
        return out
    except Exception:
        return {}
    finally:
        conn.close()


def build_master_indexes(master_data):
    indexes = {
        "plantas_by_norm": {},
        "divisiones_by_norm": {},
        "areas_by_norm": {},
        "categorias_by_norm": {},
        "subcategorias_by_norm": {},
        "prioridades_by_norm": {},
        "usuarios_by_norm": {},
        "usuarios_by_email_local": {},
        "usuarios_by_token": {},
        "areas_by_id": {},
        "subcats_by_categoria_and_norm": {},
        "user_to_area_division": {},
    }

    for p in master_data.get("plantas", []):
        indexes["plantas_by_norm"][normalize_text(p["nombre"])] = p
    for d in master_data.get("divisiones", []):
        indexes["divisiones_by_norm"][normalize_text(d["nombre"])] = d
    for a in master_data.get("areas", []):
        indexes["areas_by_norm"][normalize_text(a["nombre"])] = a
        indexes["areas_by_id"][a["id"]] = a
    for c in master_data.get("categorias", []):
        indexes["categorias_by_norm"][normalize_text(c["nombre"])] = c
    for s in master_data.get("subcategorias", []):
        key = normalize_text(s["nombre"])
        indexes["subcategorias_by_norm"].setdefault(key, []).append(s)
        combo = (s["categoria_id"], key)
        indexes["subcats_by_categoria_and_norm"][combo] = s
    for p in master_data.get("prioridades", []):
        indexes["prioridades_by_norm"][normalize_text(p["nombre"])] = p
    for u in master_data.get("usuarios", []):
        norm_user = normalize_text(u["username"])
        indexes["usuarios_by_norm"][norm_user] = u
        email = normalize_text(u.get("email"))
        if "@" in email:
            local = email.split("@", 1)[0]
            indexes["usuarios_by_email_local"][local] = u
        # Alias por tokens de username (ej: firmapaz_alfredo -> "firmapaz", "alfredo")
        for token in re.split(r"[_\s\.-]+", norm_user):
            if token:
                indexes["usuarios_by_token"].setdefault(token, []).append(u)

    user_area_division = load_user_area_division_map()
    for norm_user, mapping in user_area_division.items():
        area = indexes["areas_by_norm"].get(normalize_text(mapping.get("area")))
        division = indexes["divisiones_by_norm"].get(
            normalize_text(mapping.get("division"))
        )
        indexes["user_to_area_division"][norm_user] = {
            "area_id": area["id"] if area else None,
            "division_id": division["id"] if division else None,
        }

    return indexes


def resolve_user_candidate(raw_user, indexes):
    usuarios_by_norm = indexes.get("usuarios_by_norm", {})
    usuarios_by_email_local = indexes.get("usuarios_by_email_local", {})
    usuarios_by_token = indexes.get("usuarios_by_token", {})

    norm_value = normalize_text(raw_user)
    if not norm_value:
        return None, None

    # 1) Match exacto por username
    exact = usuarios_by_norm.get(norm_value)
    if exact:
        return exact, None

    # 2) Match por local-part de email (antes de @)
    local = norm_value.replace(" ", "")
    by_email = usuarios_by_email_local.get(local)
    if by_email:
        return by_email, None

    # 3) Match por token único de username (nombre/apellido)
    token = norm_value.split(" ")[0]
    token_hits = usuarios_by_token.get(token, [])
    if len(token_hits) == 1:
        return token_hits[0], None
    if len(token_hits) > 1:
        opciones = ", ".join(sorted({u["username"] for u in token_hits}))
        return None, f"Usuario ambiguo '{raw_user}'. Opciones: {opciones}."

    return None, f"No se encontró usuario para '{raw_user}'."


def format_full_name_from_username(username):
    norm_user = normalize_text(username).replace(".", "_")
    parts = [p for p in re.split(r"[_\s-]+", norm_user) if p]
    if not parts:
        return str(username or "").strip()
    if len(parts) >= 2:
        # Convención local habitual: apellido_nombre
        return f"{parts[1].title()} {parts[0].title()}"
    return parts[0].title()


def load_master_data():
    conn = get_azure_master_connection()
    try:
        cursor = conn.cursor()
        def run_fetchall(sql):
            cursor.execute(sql)
            return cursor.fetchall()

        master_data = {
            "plantas": [
                {"id": row[0], "nombre": row[1]}
                for row in run_fetchall(
                    f"SELECT PlantaId, Nombre FROM {qname('Plantas')} WHERE Activo = 1"
                )
            ],
            "divisiones": [
                {"id": row[0], "nombre": row[1]}
                for row in run_fetchall(
                    f"SELECT DivisionId, Nombre FROM {qname('Divisiones')} WHERE Activo = 1"
                )
            ],
            "areas": [
                {"id": row[0], "nombre": row[1], "division_id": row[2]}
                for row in run_fetchall(
                    f"SELECT AreaId, Nombre, DivisionId FROM {qname('Areas')} WHERE Activo = 1"
                )
            ],
            "categorias": [
                {"id": row[0], "nombre": row[1]}
                for row in run_fetchall(
                    f"SELECT CategoriaId, Nombre FROM {qname('Categorias')} WHERE Activo = 1"
                )
            ],
            "subcategorias": [
                {"id": row[0], "nombre": row[1], "categoria_id": row[2]}
                for row in run_fetchall(
                    f"SELECT SubcategoriaId, Nombre, CategoriaId FROM {qname('Subcategorias')} WHERE Activo = 1"
                )
            ],
            "prioridades": [
                {"id": row[0], "nombre": row[1], "nivel": row[2]}
                for row in run_fetchall(
                    f"SELECT PrioridadId, Nombre, Nivel FROM {qname('Prioridades')}"
                )
            ],
            "estados": [
                {"id": row[0], "nombre": row[1]}
                for row in run_fetchall(
                    f"SELECT EstadoId, Nombre FROM {qname('Estados')}"
                )
            ],
            "usuarios": [
                {"id": row[0], "username": row[1], "email": row[2], "role": row[3]}
                for row in run_fetchall(
                    f"SELECT UserId, Username, Email, Role FROM {qname('Users')} WHERE Active = 1"
                )
            ],
        }
        return master_data
    finally:
        conn.close()


def get_llm_catalogs(master_data):
    def unique_in_order(values):
        seen = set()
        out = []
        for value in values:
            if not value:
                continue
            norm = normalize_text(value)
            if norm in seen:
                continue
            seen.add(norm)
            out.append(value)
        return out

    return {
        "plantas": unique_in_order(
            [p["nombre"] for p in master_data.get("plantas", [])]
        ),
        "divisiones": unique_in_order(
            [d["nombre"] for d in master_data.get("divisiones", [])]
        ),
        "areas": unique_in_order([a["nombre"] for a in master_data.get("areas", [])]),
        "categorias": unique_in_order(
            [c["nombre"] for c in master_data.get("categorias", [])]
        ),
        "subcategorias": unique_in_order(
            [s["nombre"] for s in master_data.get("subcategorias", [])]
        ),
        "prioridades": unique_in_order(
            [p["nombre"] for p in master_data.get("prioridades", [])]
        ),
        "usuarios": unique_in_order(
            [u["username"] for u in master_data.get("usuarios", [])]
        ),
    }


def map_entities_to_ids(draft, indexes, master_data):
    mapped = {
        "planta_id": None,
        "division_id": None,
        "area_id": None,
        "categoria_id": None,
        "subcategoria_id": None,
        "prioridad_id": None,
        "suggested_assignee_id": None,
        "estado_id": None,
    }
    warnings = []

    planta = indexes["plantas_by_norm"].get(normalize_text(draft.get("planta")))
    if planta:
        mapped["planta_id"] = planta["id"]

    division = indexes["divisiones_by_norm"].get(normalize_text(draft.get("division")))
    if division:
        mapped["division_id"] = division["id"]

    categoria = indexes["categorias_by_norm"].get(
        normalize_text(draft.get("categoria"))
    )
    if categoria:
        mapped["categoria_id"] = categoria["id"]

    prio = indexes["prioridades_by_norm"].get(normalize_text(draft.get("prioridad")))
    if prio:
        mapped["prioridad_id"] = prio["id"]

    usuario, user_warning = resolve_user_candidate(
        draft.get("usuario_sugerido"), indexes
    )
    if usuario:
        mapped["suggested_assignee_id"] = usuario["id"]
        rel = indexes["user_to_area_division"].get(normalize_text(usuario["username"]))
        if rel:
            # Si el usuario está identificado, el área del ticket se toma desde el usuario.
            if rel.get("area_id"):
                mapped["area_id"] = rel["area_id"]
            if not mapped["division_id"] and rel.get("division_id"):
                mapped["division_id"] = rel["division_id"]
    elif user_warning and draft.get("usuario_sugerido"):
        warnings.append(user_warning)
        area = indexes["areas_by_norm"].get(normalize_text(draft.get("area")))
        if area:
            mapped["area_id"] = area["id"]
            if not mapped["division_id"]:
                mapped["division_id"] = area["division_id"]
    else:
        # Usuario desconocido/no informado: inferimos área desde el texto del ticket.
        area = indexes["areas_by_norm"].get(normalize_text(draft.get("area")))
        if area:
            mapped["area_id"] = area["id"]
            if not mapped["division_id"]:
                mapped["division_id"] = area["division_id"]

    sub_norm = normalize_text(draft.get("subcategoria"))
    if sub_norm:
        if mapped["categoria_id"]:
            sub = indexes["subcats_by_categoria_and_norm"].get(
                (mapped["categoria_id"], sub_norm)
            )
            if sub:
                mapped["subcategoria_id"] = sub["id"]
            else:
                warnings.append(
                    "La subcategoría no coincide con la categoría seleccionada."
                )
        else:
            candidates = indexes["subcategorias_by_norm"].get(sub_norm, [])
            if len(candidates) == 1:
                mapped["subcategoria_id"] = candidates[0]["id"]
                if not mapped["categoria_id"]:
                    mapped["categoria_id"] = candidates[0]["categoria_id"]
            elif len(candidates) > 1:
                warnings.append(
                    "Subcategoría ambigua: se necesita categoría para resolverla."
                )

    if mapped["area_id"] and mapped["division_id"]:
        area_row = indexes["areas_by_id"].get(mapped["area_id"])
        if area_row and area_row["division_id"] != mapped["division_id"]:
            warnings.append("El área seleccionada no pertenece a la división indicada.")

    estado = next(
        (
            e
            for e in master_data.get("estados", [])
            if normalize_text(e["nombre"]) == "abierto"
        ),
        None,
    )
    mapped["estado_id"] = estado["id"] if estado else None

    if not mapped["prioridad_id"]:
        prio_media = indexes["prioridades_by_norm"].get("media")
        mapped["prioridad_id"] = prio_media["id"] if prio_media else None

    return mapped, warnings


def compute_completeness_score(draft, ids):
    has_area_or_user = bool(ids.get("area_id") or ids.get("suggested_assignee_id"))
    has_categoria = bool(ids.get("categoria_id"))
    has_fecha = bool(draft.get("fecha_necesidad_resuelta"))
    if has_area_or_user and has_categoria and has_fecha:
        return "alto"
    if has_area_or_user:
        return "medio"
    return "bajo"


def init_db():
    # La app usa Azure SQL de forma obligatoria.
    # Validamos conexión y existencia de tablas clave al arrancar.
    conn = get_azure_master_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(f"SELECT TOP 1 UserId FROM {qname('Users')}")
        cursor.execute(f"SELECT TOP 1 TicketId FROM {qname('Tickets')}")
    finally:
        conn.close()


def insert_ticket_record(draft, ids, metadata):
    conn = get_azure_master_connection()
    try:
        cursor = conn.cursor()
        requester_id = metadata.get("requester_id")
        if requester_id is None:
            raise RuntimeError(
                "No hay usuario de sesión para registrar el solicitante del ticket."
            )

        cursor.execute(
            f"""
            INSERT INTO {qname('Tickets')} (
                Title, Description, RequesterId, SuggestedAssigneeId, AssigneeId,
                PlantaId, AreaId, CategoriaId, SubcategoriaId, PrioridadId, EstadoId,
                ConfidenceScore, OriginalPrompt, AiProcessingTime, ConversationId, NeedByAt
            ) OUTPUT INSERTED.TicketId VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                draft.get("titulo") or "Ticket sin titulo",
                draft.get("descripcion") or "Sin descripcion detallada",
                requester_id,
                ids.get("suggested_assignee_id"),
                metadata.get("assignee_id"),
                ids.get("planta_id"),
                ids.get("area_id"),
                ids.get("categoria_id"),
                ids.get("subcategoria_id"),
                ids.get("prioridad_id"),
                ids.get("estado_id"),
                metadata.get("confidence_score", 0.8),
                metadata.get("original_prompt"),
                int(metadata.get("ai_processing_time", 0)),
                metadata.get("conversation_id"),
                draft.get("fecha_necesidad_resuelta"),
            ),
        )
        row = cursor.fetchone()
        conn.commit()
        return row[0] if row else None
    finally:
        conn.close()


def fetch_tickets_for_form(filters, limit=None):
    conn = get_azure_master_connection()
    try:
        where = []
        params = []

        if filters.get("estado_id"):
            where.append("t.EstadoId = ?")
            params.append(filters["estado_id"])
        if filters.get("prioridad_id"):
            where.append("t.PrioridadId = ?")
            params.append(filters["prioridad_id"])
        if filters.get("area_id"):
            where.append("t.AreaId = ?")
            params.append(filters["area_id"])
        if filters.get("suggested_assignee_id"):
            where.append("t.SuggestedAssigneeId = ?")
            params.append(filters["suggested_assignee_id"])
        if filters.get("query"):
            where.append("(t.Title LIKE ? OR t.Description LIKE ?)")
            pattern = f"%{filters['query']}%"
            params.extend([pattern, pattern])

        where_sql = f"WHERE {' AND '.join(where)}" if where else ""
        top_clause = f"TOP {int(limit)}" if limit else ""
        sql = f"""
            SELECT
                {top_clause}
                t.TicketId,
                t.Title,
                t.Description,
                p.Nombre AS Planta,
                d.Nombre AS Division,
                a.Nombre AS Area,
                c.Nombre AS Categoria,
                s.Nombre AS Subcategoria,
                pr.Nombre AS Prioridad,
                e.Nombre AS Estado,
                ureq.Username AS Solicitante,
                uasg.Username AS Asignado,
                usug.Username AS Sugerido,
                t.NeedByAt,
                t.CreatedAt
            FROM {qname('Tickets')} t
            LEFT JOIN {qname('Plantas')} p ON t.PlantaId = p.PlantaId
            LEFT JOIN {qname('Areas')} a ON t.AreaId = a.AreaId
            LEFT JOIN {qname('Divisiones')} d ON a.DivisionId = d.DivisionId
            LEFT JOIN {qname('Categorias')} c ON t.CategoriaId = c.CategoriaId
            LEFT JOIN {qname('Subcategorias')} s ON t.SubcategoriaId = s.SubcategoriaId
            LEFT JOIN {qname('Prioridades')} pr ON t.PrioridadId = pr.PrioridadId
            LEFT JOIN {qname('Estados')} e ON t.EstadoId = e.EstadoId
            LEFT JOIN {qname('Users')} ureq ON t.RequesterId = ureq.UserId
            LEFT JOIN {qname('Users')} uasg ON t.AssigneeId = uasg.UserId
            LEFT JOIN {qname('Users')} usug ON t.SuggestedAssigneeId = usug.UserId
            {where_sql}
            ORDER BY t.TicketId DESC
        """
        cursor = conn.cursor()
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        cols = [c[0] for c in cursor.description]
        return pd.DataFrame.from_records(rows, columns=cols)
    finally:
        conn.close()


def fetch_ticket_for_edit(ticket_id):
    conn = get_azure_master_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            f"""
            SELECT
                TicketId, Title, Description, PlantaId, AreaId, CategoriaId, SubcategoriaId,
                PrioridadId, EstadoId, SuggestedAssigneeId, AssigneeId, NeedByAt
            FROM {qname('Tickets')}
            WHERE TicketId = ?
            """,
            (ticket_id,),
        )
        row = cursor.fetchone()
        if not row:
            return None
        cols = [c[0] for c in cursor.description]
        return dict(zip(cols, row))
    finally:
        conn.close()


def update_ticket_from_form(ticket_id, updates, actor_user_id):
    if not updates:
        return

    def _normalize_cmp(v):
        if isinstance(v, datetime):
            return v.replace(microsecond=0).isoformat(sep=" ")
        if v is None:
            return None
        return str(v)

    def _lookup_display_value(cursor, field_name, raw_value):
        if raw_value is None:
            return None

        lookup_map = {
            "PlantaId": ("Plantas", "PlantaId", "Nombre"),
            "AreaId": ("Areas", "AreaId", "Nombre"),
            "CategoriaId": ("Categorias", "CategoriaId", "Nombre"),
            "SubcategoriaId": ("Subcategorias", "SubcategoriaId", "Nombre"),
            "PrioridadId": ("Prioridades", "PrioridadId", "Nombre"),
            "EstadoId": ("Estados", "EstadoId", "Nombre"),
            "AssigneeId": ("Users", "UserId", "Username"),
        }
        if field_name not in lookup_map:
            return _normalize_cmp(raw_value)

        table, pk_col, label_col = lookup_map[field_name]
        cursor.execute(
            f"SELECT TOP 1 {label_col} FROM {qname(table)} WHERE {pk_col} = ?",
            (raw_value,),
        )
        row = cursor.fetchone()
        return row[0] if row else _normalize_cmp(raw_value)

    backend = get_ticket_log_backend()
    conn = get_azure_master_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            f"""
            SELECT
                Title, Description, PlantaId, AreaId, CategoriaId, SubcategoriaId,
                PrioridadId, EstadoId, AssigneeId, NeedByAt
            FROM {qname('Tickets')}
            WHERE TicketId = ?
            """,
            (ticket_id,),
        )
        current_row = cursor.fetchone()
        if not current_row:
            raise RuntimeError(f"No existe TicketId={ticket_id}")

        current_cols = [
            "Title",
            "Description",
            "PlantaId",
            "AreaId",
            "CategoriaId",
            "SubcategoriaId",
            "PrioridadId",
            "EstadoId",
            "AssigneeId",
            "NeedByAt",
        ]
        current = dict(zip(current_cols, current_row))

        changed_items = []
        for field_name, new_value in updates.items():
            old_value = current.get(field_name)
            if _normalize_cmp(old_value) != _normalize_cmp(new_value):
                changed_items.append((field_name, old_value, new_value))

        if not changed_items:
            return

        set_parts = []
        params = []
        for field_name, _old, new_value in changed_items:
            set_parts.append(f"{field_name} = ?")
            params.append(new_value)
        set_parts.append("UpdatedAt = GETDATE()")
        params.append(ticket_id)
        cursor.execute(
            f"UPDATE {qname('Tickets')} SET {', '.join(set_parts)} WHERE TicketId = ?",
            params,
        )

        field_alias = {
            "Title": "Title",
            "Description": "Description",
            "PlantaId": "Planta",
            "AreaId": "Area",
            "CategoriaId": "Categoria",
            "SubcategoriaId": "Subcategoria",
            "PrioridadId": "Prioridad",
            "EstadoId": "Estado",
            "AssigneeId": "Assignee",
            "NeedByAt": "NeedByAt",
        }

        for field_name, old_value, new_value in changed_items:
            old_disp = _lookup_display_value(cursor, field_name, old_value)
            new_disp = _lookup_display_value(cursor, field_name, new_value)
            cursor.execute(
                f"""
                INSERT INTO {backend['table']} (TicketId, UserId, IsAi, FieldName, OldValue, NewValue)
                VALUES (?, ?, 0, ?, ?, ?)
                """,
                (
                    ticket_id,
                    actor_user_id,
                    field_alias.get(field_name, field_name),
                    None if old_disp is None else str(old_disp),
                    None if new_disp is None else str(new_disp),
                ),
            )

        conn.commit()
    finally:
        conn.close()


def get_ticket_log_backend():
    schema = get_master_schema()
    conn = get_azure_master_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT TABLE_SCHEMA, TABLE_NAME
            FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_SCHEMA = ? AND TABLE_NAME = 'TicketLogs'
            """,
            (schema,),
        )
        row = cursor.fetchone()
        if not row:
            raise RuntimeError(
                f"No existe {schema}.TicketLogs. La app no usa tablas legacy de dbo."
            )
        table_schema, table_name = row[0], row[1]
        return {"mode": "normalized", "table": f"{table_schema}.{table_name}"}
    finally:
        conn.close()


def fetch_ticket_comments(ticket_id):
    backend = get_ticket_log_backend()

    conn = get_azure_master_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            f"""
            SELECT TOP 100
                l.ChangedAt AS FechaHora,
                COALESCE(u.Username, 'Sistema') AS Usuario,
                l.FieldName AS Campo,
                l.OldValue AS [Valor Anterior],
                l.NewValue AS [Nuevo Valor]
            FROM {backend['table']} l
            LEFT JOIN {qname('Users')} u ON l.UserId = u.UserId
            WHERE TicketId = ?
            ORDER BY l.ChangedAt DESC
            """,
            (ticket_id,),
        )
        rows = cursor.fetchall()
        cols = [c[0] for c in cursor.description]
        return pd.DataFrame.from_records(rows, columns=cols)
    finally:
        conn.close()


def add_ticket_comment(ticket_id, comment, user_id=None):
    backend = get_ticket_log_backend()

    conn = get_azure_master_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            f"""
            INSERT INTO {backend['table']} (TicketId, UserId, IsAi, FieldName, OldValue, NewValue)
            VALUES (?, ?, 0, 'comment', NULL, ?)
            """,
            (ticket_id, user_id, comment),
        )
        conn.commit()
    finally:
        conn.close()


# ==========================================
# 2. LÓGICA HÍBRIDA (AI + RULES)
# ==========================================


class TicketAssistant:
    def __init__(self, api_key, model_name):
        self.api_key = api_key
        if api_key:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel(model_name)
        else:
            self.model = None

    def extract_entities(self, user_input, context_json, catalogs):
        if not self.model:
            return {"error": "API Key no configurada"}, 0, ""

        system_prompt = f"""
        Eres un experto en clasificación de intenciones y extracción de entidades para un sistema de tickets industrial.
        Tu salida debe ser ÚNICAMENTE un objeto JSON válido.

        ### Reglas de Clasificación:
        1. Si el mensaje es un saludo, despedida, agradecimiento o charla trivial (ej: "hola", "gracias", "ok"), define:
           - "intencion": "social"
           - "respuesta_social": Una respuesta amigable y breve que invite a reportar un problema.
        2. Si el mensaje describe un problema, avería, tarea operativa o solicitud de gestión vinculada al trabajo, define:
           - "intencion": "crear_ticket"
        3. En cualquier otro caso:
           - "intencion": "desconocido"

        ### Extracción (solo si intencion es "crear_ticket"):
        - titulo: Breve resumen (string o null)
        - descripcion: Detalle (string o null)
        - planta: Nombre EXACTO de planta de la lista (string o null)
        - division: Nombre de división (string o null)
        - area: Nombre EXACTO del área de la lista (string o null)
        - categoria: Nombre EXACTO de categoría de la lista (string o null)
        - subcategoria: Subcategoría específica (string o null)
        - prioridad: Prioridad inferida (Alta, Media, Baja, Crítica o null)
        - usuario_sugerido: username sugerido (string o null)
        - fecha_necesidad: fecha esperada de resolución en lenguaje natural o formato fecha (string o null)
        - Si la fecha es inferible (ej: "hoy", "próximo lunes"), devuelve fecha_necesidad en formato YYYY-MM-DD.

        ### Catálogos disponibles para validar:
        Plantas: {", ".join(catalogs.get("plantas", []))}
        Divisiones: {", ".join(catalogs.get("divisiones", []))}
        Áreas: {", ".join(catalogs.get("areas", []))}
        Categorías: {", ".join(catalogs.get("categorias", []))}
        Subcategorías: {", ".join(catalogs.get("subcategorias", []))}
        Prioridades: {", ".join(catalogs.get("prioridades", []))}
        Usuarios (username): {", ".join(catalogs.get("usuarios", []))}
        
        Contexto Actual: {json.dumps(context_json)}
        Mensaje: "{user_input}"
        """

        start_time = datetime.now()
        try:
            response = self.model.generate_content(system_prompt)
            # Limpiar respuesta por si el modelo incluye ```json
            clean_res = response.text.replace("```json", "").replace("```", "").strip()
            entities = json.loads(clean_res)
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            return entities, processing_time, system_prompt
        except Exception as e:
            return {"error": str(e)}, 0, system_prompt

    def generate_review_message(self, draft):
        """
        Genera un resumen del ticket y ofrece opciones de acción.
        Retorna (mensaje, bloqueante)
        """
        # No bloqueamos por faltantes de negocio; aplicamos defaults y advertencias.
        if not draft.get("titulo"):
            draft["titulo"] = "Ticket sin titulo"

        # Asignación de valores de visualización (mostrar todos los campos)
        descripcion_display = draft.get("descripcion") or "Sin descripción detallada"
        planta_display = draft.get("planta") or "No especificada"
        division_display = draft.get("division") or "No especificada"
        area_display = (
            draft.get("area")
            or "Sin asignar (Se definirá en revisión del responsable del área)"
        )
        categoria_display = draft.get("categoria") or "No especificada"
        subcategoria_display = draft.get("subcategoria") or "No especificada"
        prioridad_display = draft.get("prioridad") or "Media (Por defecto)"
        fecha_display = draft.get("fecha_necesidad") or "No especificada"
        fecha_norm_display = draft.get("fecha_necesidad_resuelta") or "No normalizada"
        usuario_display = draft.get("usuario_sugerido") or "No especificado"
        if draft.get("usuario_sugerido_resuelto"):
            u = draft["usuario_sugerido_resuelto"]
            full_name = format_full_name_from_username(u.get("username"))
            usuario_display = f"{full_name} ({u.get('username')}) - {u.get('email')}"

        # Construcción del resumen
        resumen = (
            f"<b>Título:</b> {draft.get('titulo')}\n"
            f"<b>Descripción:</b> {descripcion_display}\n"
            f"<b>Ubicación (Planta):</b> {planta_display}\n"
            f"<b>División:</b> {division_display}\n"
            f"<b>Área:</b> {area_display}\n"
            f"<b>Categoría:</b> {categoria_display}\n"
            f"<b>Subcategoría:</b> {subcategoria_display}\n"
            f"<b>Prioridad:</b> {prioridad_display}\n"
            f"<b>Usuario sugerido:</b> {usuario_display}\n"
            f"<b>Fecha de necesidad:</b> {fecha_display}\n"
            f"<b>Fecha de necesidad normalizada:</b> {fecha_norm_display}\n"
            f"<br><span style='color:#156099;'><b>💡 Confirmación rápida:</b> para crear el ticket, respondé <b>SI</b>.</span>"
        )

        return resumen, False


# ==========================================
# 3. INTERFAZ STREAMLIT (ESTILO TARANTO)
# ==========================================

st.set_page_config(page_title="Gestar IA - Asistente de Tickets", layout="wide")

st.markdown(
    """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Lato:wght@300;400;700&family=Raleway:wght@600;700&display=swap');
    .stApp { background-color: #ffffff; }
    html, body, [class*="css"] {
        font-family: "Lato", sans-serif;
        color: #444;
    }
    h1, h2, h3, .raleway {
        font-family: "Raleway", sans-serif;
        font-weight: 700;
    }
    .block-container {
        padding-top: 0.8rem;
    }
    .taranto-header {
        background: #ffffff;
        border-bottom: 3px solid #d52e25;
        border-radius: 10px;
        padding: 0.75rem 1rem;
        margin-bottom: 1rem;
        box-shadow: 0 2px 15px rgba(0,0,0,0.04);
    }
    [data-testid="stVerticalBlock"]:has(.taranto-header-marker) {
        background: #ffffff;
        border-bottom: 3px solid #d52e25;
        border-radius: 10px;
        padding: 0.75rem 1rem 0.4rem 1rem;
        margin-bottom: 0.7rem;
        box-shadow: 0 2px 15px rgba(0,0,0,0.04);
    }
    .taranto-header-marker {
        display: none;
    }
    /* Debug visual de paneles (prueba temporal) */
    [data-testid="stVerticalBlock"]:has(.dbg-panel-header) {
        background: #ffffff !important;
        border: 1px solid #e5e7eb;
        border-radius: 10px;
        padding: 0.5rem;
    }
    [data-testid="stVerticalBlock"]:has(.dbg-panel-nav) {
        background: #ffffff !important;
        border: 1px solid #e5e7eb;
        border-radius: 10px;
        padding: 0.5rem;
        margin-top: 0.4rem;
    }
    [data-testid="stVerticalBlock"]:has(.dbg-panel-content) {
        background: #f3f4f6 !important;
        border: 1px solid #d1d5db;
        border-radius: 10px;
        padding: 0.5rem;
        margin-top: 0.4rem;
        min-height: calc(100dvh - 290px);
    }
    [data-testid="stVerticalBlock"]:has(.dbg-panel-inner) {
        background: #f3f4f6 !important;
        border: 1px solid #d1d5db;
        border-radius: 10px;
        padding: 0.5rem;
        margin-top: 0.4rem;
    }
    .dbg-panel-header,
    .dbg-panel-nav,
    .dbg-panel-content,
    .dbg-panel-inner {
        display: none;
    }
    .taranto-logo {
        color: #156099;
        font-family: "Raleway", sans-serif;
        font-size: 2rem;
        font-weight: 700;
        letter-spacing: 1px;
        margin: 0;
    }
    .taranto-title {
        margin: 0;
        color: #d52e25;
        text-align: center;
        font-family: "Raleway", sans-serif;
        font-size: 2rem;
        font-weight: 700;
        line-height: 1.15;
    }
    .taranto-subtitle {
        font-size: 1.05rem;
        color: #444;
        font-weight: 400;
    }
    .v2-card {
        background-color: #fff;
        padding: 1rem 1.1rem;
        border-radius: 10px;
        border: 1px solid rgba(128, 128, 128, 0.2);
        box-shadow: 0 2px 15px rgba(0, 0, 0, 0.04);
        margin-bottom: 0.8rem;
    }
    .chat-bubble {
        padding: 10px 14px;
        border-radius: 10px;
        margin-bottom: 8px;
        max-width: 82%;
        white-space: pre-wrap;
        border: 1px solid rgba(128,128,128,0.2);
        box-shadow: 0 2px 12px rgba(0,0,0,0.04);
    }
    .user-bubble {
        background-color: #dcf8c6;
        margin-left: auto;
        border-left: 3px solid #34b233;
    }
    .bot-bubble {
        background-color: #ffffff;
        margin-right: auto;
        border-left: 3px solid #d52e25;
    }
    div.stButton > button {
        border-radius: 4px;
        font-family: "Raleway", sans-serif;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        font-weight: 700;
        transition: all 0.25s;
        white-space: nowrap;
    }
    div.stButton > button[kind="primary"] {
        background-color: #d52e25;
        border: none;
        color: white;
    }
    .active-nav button {
        background-color: #156099 !important;
        color: white !important;
        border: none !important;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #e9edf1;
        border-radius: 4px 4px 0 0;
        padding: 8px 16px;
        font-weight: 600;
    }
    .stTabs [aria-selected="true"] {
        background-color: #156099 !important;
        color: white !important;
    }
    .stDataFrame {
        border-radius: 8px;
        overflow: hidden;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        border: 1px solid rgba(128,128,128,0.15);
    }
    /* Mayor contraste para campos de edición en formularios */
    div[data-baseweb="input"] > div,
    div[data-baseweb="select"] > div,
    div[data-baseweb="textarea"] > div,
    .stTextInput input,
    .stTextArea textarea {
        background-color: #ffffff !important;
        border: 1px solid #9aa7b5 !important;
    }
    .stTextInput input,
    .stTextArea textarea {
        color: #1f2933 !important;
    }
    div[data-baseweb="input"] > div:focus-within,
    div[data-baseweb="select"] > div:focus-within,
    div[data-baseweb="textarea"] > div:focus-within {
        border-color: #156099 !important;
        box-shadow: 0 0 0 2px rgba(21, 96, 153, 0.18) !important;
    }
    .stTextInput input::placeholder,
    .stTextArea textarea::placeholder {
        color: #6b7785 !important;
        opacity: 1 !important;
    }
    [data-testid="stBottomBlockContainer"] {
        background: #dcf8c6 !important;
        border-top: 1px solid #34b233;
    }
    header { visibility: hidden; }
    footer { visibility: hidden; }
    [data-testid="stSidebar"] { display: none !important; }
    [data-testid="stSidebarCollapsedControl"] { display: none !important; }
    [data-testid="collapsedControl"] { display: none !important; }
    .top-meta {
        text-align: right;
        color: #156099;
        font-size: 0.95rem;
        font-weight: 700;
    }
</style>
""",
    unsafe_allow_html=True,
)

try:
    init_db()
except Exception as db_err:
    st.error(f"❌ Error de conexión a Azure SQL: {db_err}")
    st.stop()

if "master_data" not in st.session_state:
    st.session_state.master_data = load_master_data()
if "master_indexes" not in st.session_state:
    st.session_state.master_indexes = build_master_indexes(st.session_state.master_data)
else:
    required_index_keys = {
        "usuarios_by_norm",
        "usuarios_by_email_local",
        "usuarios_by_token",
        "user_to_area_division",
    }
    if not required_index_keys.issubset(set(st.session_state.master_indexes.keys())):
        st.session_state.master_indexes = build_master_indexes(
            st.session_state.master_data
        )

try:
    ensure_session_user(st.session_state.master_data)
except Exception as user_err:
    st.error(f"❌ Error de usuarios de sesión: {user_err}")
    st.stop()

# Cargar API Key: prioridad Streamlit Secrets (deploy), fallback .env (local)
try:
    api_key = st.secrets.get("GOOGLE_API_KEY")
except (FileNotFoundError, KeyError):
    api_key = None

if not api_key:
    api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    st.error(
        "⚠️ API Key no configurada. Configura GOOGLE_API_KEY en Streamlit Secrets o en .env"
    )
    st.stop()

# Sidebar
with st.sidebar:
    st.title("⚙️ Configuración")
    st.info(f"Base de datos: Azure SQL ({get_master_schema()})")
    model_name = st.selectbox(
        "Modelo", ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-pro"]
    )

    # Mostrar estado de API Key (sin revelar la key completa)
    st.success(f"✅ API Key configurada ({api_key[:8]}...)")

    st.divider()
    if st.button("Refrescar Maestros"):
        st.session_state.master_data = load_master_data()
        st.session_state.master_indexes = build_master_indexes(
            st.session_state.master_data
        )
        st.success("Datos maestros actualizados.")
    st.subheader("🛠️ Debug Area")
    debug_expander = st.expander("Estado Interno", expanded=False)

# Inicializar Estado de Sesión
if "messages" not in st.session_state:
    st.session_state.messages = []
    # Saludo inicial proactivo
    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": "Hola, soy tu asistente de tickets. Describe tu problema (ej: 'No funciona el motor de la prensa en Planta 2').",
        }
    )

if "ticket_draft" not in st.session_state:
    st.session_state.ticket_draft = {
        "titulo": None,
        "descripcion": None,
        "planta": None,
        "division": None,
        "area": None,
        "categoria": None,
        "subcategoria": None,
        "prioridad": None,
        "usuario_sugerido": None,
        "usuario_sugerido_resuelto": None,
        "fecha_necesidad": None,
        "fecha_necesidad_resuelta": None,
    }

if "last_ai_res" not in st.session_state:
    st.session_state.last_ai_res = {}
if "last_prompt" not in st.session_state:
    st.session_state.last_prompt = ""
if "show_confirm_buttons" not in st.session_state:
    st.session_state.show_confirm_buttons = False
if "form_selected_ticket_id" not in st.session_state:
    st.session_state.form_selected_ticket_id = None
if "ui_section" not in st.session_state:
    st.session_state.ui_section = "CHAT IA"

taranto_logo_b64 = get_base64_image("assets/taranto-logo.png")


def create_ticket_from_current_chat_draft(confirm_source):
    d = st.session_state.ticket_draft
    ids, map_warnings = map_entities_to_ids(
        d, st.session_state.master_indexes, st.session_state.master_data
    )
    need_by_dt = safe_parse_datetime(d.get("fecha_necesidad"))
    d["fecha_necesidad_resuelta"] = (
        need_by_dt.strftime("%Y-%m-%d %H:%M:%S") if need_by_dt else None
    )
    score = compute_completeness_score(d, ids)
    session_user = get_session_user(st.session_state.master_data)
    t_id = insert_ticket_record(
        d,
        ids,
        {
            "requester_id": session_user["id"] if session_user else None,
            "assignee_id": None,
            "confidence_score": st.session_state.last_ai_res.get("confidence", 0.8),
            "original_prompt": st.session_state.last_prompt or confirm_source,
            "ai_processing_time": st.session_state.last_ai_res.get(
                "ai_processing_time", 0
            ),
            "conversation_id": st.session_state.last_ai_res.get("conversation_id"),
        },
    )

    warnings = []
    if not ids.get("area_id") and not ids.get("suggested_assignee_id"):
        warnings.append(
            "Falta Area o Usuario sugerido. El ticket puede requerir mas revision del responsable del area."
        )
    warnings.extend(map_warnings)
    if d.get("fecha_necesidad") and not d.get("fecha_necesidad_resuelta"):
        warnings.append(
            "No pude normalizar la Fecha de Necesidad. Se guardo sin fecha normalizada."
        )

    warning_text = "<b>Observaciones:</b> Sin observaciones."
    if warnings:
        warning_lines = "<br>".join([f"- {w}" for w in warnings])
        warning_text = f"<b>Observaciones:</b><br>{warning_lines}"

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": (
                f"✅ ¡Ticket #{t_id} creado con éxito!"
                f"<br><b>Completitud:</b> {score.upper()}"
                f"<br>{warning_text}"
            ),
        }
    )
    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": "Listo. Ya podés cargar un nuevo ticket o tarea cuando quieras.",
        }
    )
    for k in st.session_state.ticket_draft:
        st.session_state.ticket_draft[k] = None
    st.session_state.show_confirm_buttons = False


def render_chat_mode(api_key, model_name, debug_expander):
    for msg in st.session_state.messages:
        role_class = "user-bubble" if msg["role"] == "user" else "bot-bubble"
        st.markdown(
            f'<div class="chat-bubble {role_class}">{msg["content"]}</div>',
            unsafe_allow_html=True,
        )

    if st.session_state.show_confirm_buttons:
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Crear Ticket", key="btn_crear"):
                create_ticket_from_current_chat_draft("Confirmado por boton")
                st.rerun()
        with col2:
            if st.button("✏️ Agregar información", key="btn_mas_info"):
                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": "Entendido. Dime qué más quieres agregar o corregir.",
                    }
                )
                st.session_state.show_confirm_buttons = False
                st.rerun()

    with debug_expander:
        st.write("**Borrador Actual:**", st.session_state.ticket_draft)
        st.write("**Última Respuesta JSON IA:**", st.session_state.last_ai_res)
        st.write("**Prompt Enviado:**")
        st.code(st.session_state.last_prompt or "", language="text")


def handle_chat_input_and_processing(api_key, model_name):
    if prompt := st.chat_input("Escribe tu solicitud/tarea aquí..."):
        if st.session_state.show_confirm_buttons and normalize_text(prompt) == "si":
            st.session_state.messages.append({"role": "user", "content": prompt})
            create_ticket_from_current_chat_draft("Confirmado por SI")
            st.rerun()
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.session_state.show_confirm_buttons = False
        st.rerun()

    if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
        assistant = TicketAssistant(api_key, model_name)
        user_input = st.session_state.messages[-1]["content"]
        with st.spinner("Procesando..."):
            catalogs = get_llm_catalogs(st.session_state.master_data)
            ai_res, p_time, s_prompt = assistant.extract_entities(
                user_input, st.session_state.ticket_draft, catalogs
            )
            ai_res["ai_processing_time"] = int(p_time)
            st.session_state.last_ai_res = ai_res
            st.session_state.last_prompt = s_prompt

            if "error" not in ai_res:
                intencion = ai_res.get("intencion", "desconocido")
                if intencion == "social":
                    bot_res = ai_res.get(
                        "respuesta_social",
                        "¡Hola! Estoy listo para ayudarte. Por favor, dime qué necesitas reportar.",
                    )
                elif intencion == "crear_ticket":
                    for k in st.session_state.ticket_draft.keys():
                        v = ai_res.get(k)
                        if v is not None and v != "":
                            st.session_state.ticket_draft[k] = v

                    resolved_user, _ = resolve_user_candidate(
                        st.session_state.ticket_draft.get("usuario_sugerido"),
                        st.session_state.master_indexes,
                    )
                    st.session_state.ticket_draft["usuario_sugerido_resuelto"] = (
                        resolved_user
                    )

                    draft_fecha = st.session_state.ticket_draft.get("fecha_necesidad")
                    parsed_from_draft = safe_parse_datetime(draft_fecha)
                    parsed_from_user = safe_parse_datetime(user_input)
                    parsed_need = parsed_from_draft
                    if parsed_from_user:
                        parsed_need = parsed_from_user
                    if (
                        parsed_need
                        and has_relative_date_language(draft_fecha)
                        and parsed_need.date() < datetime.now().date()
                    ):
                        parsed_need = parsed_from_user

                    st.session_state.ticket_draft["fecha_necesidad_resuelta"] = (
                        parsed_need.strftime("%Y-%m-%d %H:%M:%S")
                        if parsed_need
                        else None
                    )
                    bot_res, bloqueante = assistant.generate_review_message(
                        st.session_state.ticket_draft
                    )
                    if not bloqueante:
                        st.session_state.show_confirm_buttons = True
                else:
                    bot_res = "No estoy seguro de haber entendido. ¿Podrías darme más detalles sobre el problema o solicitud?"

                st.session_state.messages.append(
                    {"role": "assistant", "content": bot_res}
                )
                st.rerun()
            else:
                st.sidebar.error(f"Error de API: {ai_res['error']}")


def render_form_mode():
    st.markdown("<div class='dbg-panel-inner'></div>", unsafe_allow_html=True)
    ticket_tab, tray_tab = st.tabs(["Nuevo Ticket", "Bandeja y Edicion"])

    users = st.session_state.master_data.get("usuarios", [])
    plantas = st.session_state.master_data.get("plantas", [])
    areas = st.session_state.master_data.get("areas", [])
    categorias = st.session_state.master_data.get("categorias", [])
    subcategorias = st.session_state.master_data.get("subcategorias", [])
    prioridades = st.session_state.master_data.get("prioridades", [])
    estados = st.session_state.master_data.get("estados", [])

    with ticket_tab:
        with st.form("form_create_ticket"):
            titulo = st.text_input("Titulo *")
            descripcion = st.text_area("Descripcion *")
            c1, c2, c3 = st.columns(3)
            with c1:
                planta_opt = [""] + [p["nombre"] for p in plantas]
                planta_sel = st.selectbox("Planta", planta_opt)
                categoria_opt = [""] + [c["nombre"] for c in categorias]
                categoria_sel = st.selectbox("Categoria", categoria_opt)
            with c2:
                area_opt = [""] + [a["nombre"] for a in areas]
                area_sel = st.selectbox("Area", area_opt)
                subcat_opt = [""] + [s["nombre"] for s in subcategorias]
                subcat_sel = st.selectbox("Subcategoria", subcat_opt)
            with c3:
                prio_opt = ["Media"] + [p["nombre"] for p in prioridades]
                prio_sel = st.selectbox("Prioridad", prio_opt)
                user_opt = [""] + [u["username"] for u in users]
                user_sel = st.selectbox("Usuario sugerido", user_opt)

            fecha_sel = st.date_input("Fecha de necesidad", format="DD/MM/YYYY")
            submitted = st.form_submit_button("Crear Ticket")

        if submitted:
            if not titulo.strip() or not descripcion.strip():
                st.error("Titulo y Descripcion son obligatorios.")
            else:
                draft = {
                    "titulo": titulo.strip(),
                    "descripcion": descripcion.strip(),
                    "planta": planta_sel or None,
                    "division": None,
                    "area": area_sel or None,
                    "categoria": categoria_sel or None,
                    "subcategoria": subcat_sel or None,
                    "prioridad": prio_sel or None,
                    "usuario_sugerido": user_sel or None,
                    "fecha_necesidad": fecha_sel.strftime("%Y-%m-%d") if fecha_sel else None,
                    "fecha_necesidad_resuelta": None,
                }
                parsed = (
                    datetime(fecha_sel.year, fecha_sel.month, fecha_sel.day, 17, 0, 0)
                    if fecha_sel
                    else None
                )
                draft["fecha_necesidad_resuelta"] = (
                    parsed.strftime("%Y-%m-%d %H:%M:%S") if parsed else None
                )
                ids, warns = map_entities_to_ids(
                    draft, st.session_state.master_indexes, st.session_state.master_data
                )
                session_user = get_session_user(st.session_state.master_data)
                ticket_id = insert_ticket_record(
                    draft,
                    ids,
                    {
                        "requester_id": session_user["id"] if session_user else None,
                        "assignee_id": None,
                        "confidence_score": 1.0,
                        "original_prompt": "Creado desde Modo Formulario",
                        "ai_processing_time": 0,
                        "conversation_id": None,
                    },
                )
                st.success(f"Ticket #{ticket_id} creado correctamente.")
                if warns:
                    st.warning(" | ".join(warns))

    with tray_tab:
        if st.session_state.form_selected_ticket_id is None:
            c1, c2, c3, c4, c5 = st.columns(5)
            with c1:
                estado_opt = ["Todos"] + [e["nombre"] for e in estados]
                estado_sel = st.selectbox("Estado", estado_opt, key="form_filter_estado")
            with c2:
                prio_opt = ["Todas"] + [p["nombre"] for p in prioridades]
                prio_filter = st.selectbox("Prioridad", prio_opt, key="form_filter_prio")
            with c3:
                area_opt = ["Todas"] + [a["nombre"] for a in areas]
                area_filter = st.selectbox("Area", area_opt, key="form_filter_area")
            with c4:
                sugg_opt = ["Todos"] + [u["username"] for u in users]
                sugg_filter = st.selectbox(
                    "Usuario sugerido", sugg_opt, key="form_filter_sugg_user"
                )
            with c5:
                q = st.text_input("Buscar", key="form_filter_query")

            estado_id = next(
                (e["id"] for e in estados if e["nombre"] == estado_sel), None
            ) if estado_sel != "Todos" else None
            prioridad_id = next(
                (p["id"] for p in prioridades if p["nombre"] == prio_filter), None
            ) if prio_filter != "Todas" else None
            area_id = next(
                (a["id"] for a in areas if a["nombre"] == area_filter), None
            ) if area_filter != "Todas" else None
            suggested_assignee_id = next(
                (u["id"] for u in users if u["username"] == sugg_filter), None
            ) if sugg_filter != "Todos" else None

            df = fetch_tickets_for_form(
                {
                    "estado_id": estado_id,
                    "prioridad_id": prioridad_id,
                    "area_id": area_id,
                    "suggested_assignee_id": suggested_assignee_id,
                    "query": q.strip() if q else None,
                },
                limit=None,
            )
            if df.empty:
                st.info("No hay tickets para los filtros seleccionados.")
                return

            st.caption(f"Mostrando {len(df)} tickets.")
            st.dataframe(
                df,
                width="stretch",
                height=360,
                hide_index=True,
                selection_mode="single-row",
                on_select="rerun",
                key="form_ticket_grid",
            )
            selection = st.session_state.get("form_ticket_grid", {}).get("selection", {})
            selected_rows = selection.get("rows", [])
            selected_ticket_id = None
            if selected_rows:
                row_idx = selected_rows[0]
                selected_ticket_id = int(df.iloc[row_idx]["TicketId"])
                st.caption(f"Ticket seleccionado: #{selected_ticket_id}")

            if st.button("Editar", key="form_open_edit", type="primary"):
                if selected_ticket_id is None:
                    st.warning("Seleccioná una fila de la grilla antes de editar.")
                else:
                    st.session_state.form_selected_ticket_id = selected_ticket_id
                    st.rerun()
            return

        selected_ticket_id = st.session_state.form_selected_ticket_id
        if not selected_ticket_id:
            st.warning("No hay ticket seleccionado.")
            return

        t = fetch_ticket_for_edit(selected_ticket_id)
        if not t:
            st.error("No se pudo cargar el ticket seleccionado.")
            return

        st.markdown(f"### Detalle Ticket #{selected_ticket_id}")
        with st.form("form_edit_ticket"):
            title_new = st.text_input("Titulo", value=t.get("Title") or "")
            desc_new = st.text_area("Descripcion", value=t.get("Description") or "")

            plantas_by_id = {p["id"]: p["nombre"] for p in plantas}
            areas_by_id = {a["id"]: a["nombre"] for a in areas}
            cats_by_id = {c["id"]: c["nombre"] for c in categorias}
            subcats_by_id = {s["id"]: s["nombre"] for s in subcategorias}
            prio_by_id = {p["id"]: p["nombre"] for p in prioridades}
            est_by_id = {e["id"]: e["nombre"] for e in estados}
            users_by_id = {u["id"]: u["username"] for u in users}
            SIN_DEFINIR = "Sin definir"

            def _build_select_options(by_id, current_id):
                labels = [SIN_DEFINIR] + list(by_id.values())
                current_label = by_id.get(current_id, SIN_DEFINIR)
                index = labels.index(current_label) if current_label in labels else 0
                return labels, index

            def _map_label_to_id(by_id, label):
                if label == SIN_DEFINIR:
                    return None
                return next((k for k, v in by_id.items() if v == label), None)

            def _label_with_warning(base_label, key_name, by_id, current_id):
                current_value = st.session_state.get(
                    key_name, by_id.get(current_id, SIN_DEFINIR)
                )
                return f"{base_label} ⚠️" if current_value == SIN_DEFINIR else base_label

            c1, c2, c3 = st.columns(3)
            with c1:
                planta_key = f"edit_planta_{selected_ticket_id}"
                planta_opts, planta_idx = _build_select_options(
                    plantas_by_id, t.get("PlantaId")
                )
                planta_edit = st.selectbox(
                    _label_with_warning("Planta", planta_key, plantas_by_id, t.get("PlantaId")),
                    planta_opts,
                    index=planta_idx,
                    key=planta_key,
                )

                area_key = f"edit_area_{selected_ticket_id}"
                area_opts, area_idx = _build_select_options(areas_by_id, t.get("AreaId"))
                area_edit = st.selectbox(
                    _label_with_warning("Area", area_key, areas_by_id, t.get("AreaId")),
                    area_opts,
                    index=area_idx,
                    key=area_key,
                )
            with c2:
                cat_key = f"edit_cat_{selected_ticket_id}"
                cat_opts, cat_idx = _build_select_options(
                    cats_by_id, t.get("CategoriaId")
                )
                cat_edit = st.selectbox(
                    _label_with_warning("Categoria", cat_key, cats_by_id, t.get("CategoriaId")),
                    cat_opts,
                    index=cat_idx,
                    key=cat_key,
                )

                subcat_key = f"edit_subcat_{selected_ticket_id}"
                subcat_opts, subcat_idx = _build_select_options(
                    subcats_by_id, t.get("SubcategoriaId")
                )
                subcat_edit = st.selectbox(
                    _label_with_warning("Subcategoria", subcat_key, subcats_by_id, t.get("SubcategoriaId")),
                    subcat_opts,
                    index=subcat_idx,
                    key=subcat_key,
                )
            with c3:
                prio_key = f"edit_prio_{selected_ticket_id}"
                prio_opts, prio_idx = _build_select_options(
                    prio_by_id, t.get("PrioridadId")
                )
                prio_edit = st.selectbox(
                    _label_with_warning("Prioridad", prio_key, prio_by_id, t.get("PrioridadId")),
                    prio_opts,
                    index=prio_idx,
                    key=prio_key,
                )

                estado_key = f"edit_estado_{selected_ticket_id}"
                estado_opts, estado_idx = _build_select_options(
                    est_by_id, t.get("EstadoId")
                )
                estado_edit = st.selectbox(
                    _label_with_warning("Estado", estado_key, est_by_id, t.get("EstadoId")),
                    estado_opts,
                    index=estado_idx,
                    key=estado_key,
                )

                assignee_key = f"edit_assignee_{selected_ticket_id}"
                assignee_opt, assignee_idx = _build_select_options(
                    users_by_id, t.get("AssigneeId")
                )
                assignee_edit = st.selectbox(
                    _label_with_warning("Asignado a", assignee_key, users_by_id, t.get("AssigneeId")),
                    assignee_opt,
                    index=assignee_idx,
                    key=assignee_key,
                )

            has_need_by = t.get("NeedByAt") is not None
            use_need_by = st.checkbox(
                "Definir fecha de necesidad",
                value=has_need_by,
                key=f"edit_need_by_enabled_{selected_ticket_id}",
            )
            need_by_date = st.date_input(
                "Fecha necesidad",
                value=t.get("NeedByAt").date() if has_need_by else None,
                format="DD/MM/YYYY",
                disabled=not use_need_by,
            )
            button_col = st.columns([1, 1, 6], gap="small")
            with button_col[0]:
                accept_edit = st.form_submit_button("Aceptar", type="primary")
            with button_col[1]:
                cancel_edit = st.form_submit_button("Cancelar")

        if cancel_edit:
            st.session_state.form_selected_ticket_id = None
            st.rerun()

        if accept_edit:
            parsed = (
                datetime(
                    need_by_date.year,
                    need_by_date.month,
                    need_by_date.day,
                    17,
                    0,
                    0,
                )
                if (need_by_date and use_need_by)
                else None
            )
            updates = {
                "Title": title_new,
                "Description": desc_new,
                "PlantaId": _map_label_to_id(plantas_by_id, planta_edit),
                "AreaId": _map_label_to_id(areas_by_id, area_edit),
                "CategoriaId": _map_label_to_id(cats_by_id, cat_edit),
                "SubcategoriaId": _map_label_to_id(subcats_by_id, subcat_edit),
                "PrioridadId": _map_label_to_id(prio_by_id, prio_edit),
                "EstadoId": _map_label_to_id(est_by_id, estado_edit),
                "AssigneeId": _map_label_to_id(users_by_id, assignee_edit),
                "NeedByAt": parsed if parsed else None,
            }
            session_user = get_session_user(st.session_state.master_data)
            update_ticket_from_form(
                selected_ticket_id,
                updates,
                actor_user_id=session_user["id"] if session_user else None,
            )
            st.session_state.form_selected_ticket_id = None
            st.rerun()

        st.markdown("#### Seguimiento / Comentarios")
        try:
            comments = fetch_ticket_comments(selected_ticket_id)
            if comments.empty:
                st.caption("Sin comentarios registrados.")
            else:
                st.dataframe(
                    comments[
                        ["FechaHora", "Usuario", "Campo", "Valor Anterior", "Nuevo Valor"]
                    ],
                    width="stretch",
                    height=180,
                    hide_index=True,
                )
            cmt = st.text_area("Nuevo comentario", key="form_comment_text")
            if st.button("Agregar comentario", key="form_add_comment"):
                if cmt.strip():
                    session_user = get_session_user(st.session_state.master_data)
                    add_ticket_comment(
                        selected_ticket_id,
                        cmt.strip(),
                        user_id=session_user["id"] if session_user else None,
                    )
                    st.success("Comentario agregado.")
                    st.rerun()
                else:
                    st.warning("Escribí un comentario antes de guardar.")
        except Exception as e:
            st.error(f"Error de logs: {e}")


session_users = st.session_state.master_data.get("usuarios", [])
session_user = get_session_user(st.session_state.master_data)
session_labels = [u["username"] for u in session_users]
current_label = session_user["username"] if session_user else None

with st.container():
    st.markdown("<div class='dbg-panel-header'></div>", unsafe_allow_html=True)
    st.markdown("<div class='taranto-header-marker'></div>", unsafe_allow_html=True)
    head1, head2, head3 = st.columns([1.4, 3.2, 2.2], vertical_alignment="center")
    with head1:
        if taranto_logo_b64:
            st.markdown(
                f'<img src="data:image/png;base64,{taranto_logo_b64}" style="height:48px; width:auto;" alt="Taranto">',
                unsafe_allow_html=True,
            )
        else:
            st.markdown("<p class='taranto-logo'>TARANTO</p>", unsafe_allow_html=True)
    with head2:
        st.markdown(
            "<h1 class='taranto-title'>GESTAR <span class='taranto-subtitle'>| Gestión de Solicitudes</span></h1>",
            unsafe_allow_html=True,
        )
    with head3:
        ux1, ux2, ux3 = st.columns(
            [3.2, 1.6, 2.2], gap="small", vertical_alignment="center"
        )
        with ux1:
            if session_labels:
                idx = session_labels.index(current_label) if current_label in session_labels else 0
                selected_session_label = st.selectbox(
                    "Usuario de sesión",
                    session_labels,
                    index=idx,
                    key="header_session_user",
                )
                if selected_session_label != current_label:
                    new_user = next(
                        (u for u in session_users if u["username"] == selected_session_label),
                        None,
                    )
                    if new_user:
                        st.session_state.current_user_id = new_user["id"]
                        st.rerun()
        with ux2:
            cls = "active-nav" if st.session_state.ui_section == "CHAT IA" else ""
            st.markdown(f'<div class="{cls}">', unsafe_allow_html=True)
            if st.button("CHAT IA", key="main_nav_chat", use_container_width=True):
                st.session_state.ui_section = "CHAT IA"
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
        with ux3:
            cls = "active-nav" if st.session_state.ui_section == "MODO FORMULARIO" else ""
            st.markdown(f'<div class="{cls}">', unsafe_allow_html=True)
            if st.button("MODO FORMULARIO", key="main_nav_form", use_container_width=True):
                st.session_state.ui_section = "MODO FORMULARIO"
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

with st.container():
    st.markdown("<div class='dbg-panel-content'></div>", unsafe_allow_html=True)
    if st.session_state.ui_section == "CHAT IA":
        render_chat_mode(api_key, model_name, debug_expander)
    else:
        render_form_mode()

if st.session_state.ui_section == "CHAT IA":
    handle_chat_input_and_processing(api_key, model_name)

# Panel izquierdo (sidebar): tabla de tickets al final
with st.sidebar:
    st.divider()
    st.subheader("Tickets Cargados")
    conn = None
    try:
        conn = get_azure_master_connection()
        cursor = conn.cursor()
        cursor.execute(
            f"""
            SELECT
                t.TicketId AS Ticket,
                t.Title AS Titulo,
                p.Nombre AS Planta,
                a.Nombre AS Area,
                c.Nombre AS Categoria,
                pr.Nombre AS Prioridad,
                e.Nombre AS Estado,
                t.NeedByAt AS FechaNecesidad
            FROM {qname('Tickets')} t
            LEFT JOIN {qname('Plantas')} p ON t.PlantaId = p.PlantaId
            LEFT JOIN {qname('Areas')} a ON t.AreaId = a.AreaId
            LEFT JOIN {qname('Categorias')} c ON t.CategoriaId = c.CategoriaId
            LEFT JOIN {qname('Prioridades')} pr ON t.PrioridadId = pr.PrioridadId
            LEFT JOIN {qname('Estados')} e ON t.EstadoId = e.EstadoId
            ORDER BY t.TicketId DESC
            """
        )
        rows = cursor.fetchall()
        columns = [col[0] for col in cursor.description]
        tickets_df = pd.DataFrame.from_records(rows, columns=columns)
        if tickets_df.empty:
            st.caption("No hay tickets cargados.")
        else:
            st.dataframe(tickets_df, width="stretch", height=260)
    except Exception as err:
        st.caption(f"No se pudo cargar tickets: {err}")
    finally:
        if conn is not None:
            conn.close()
