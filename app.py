import streamlit as st
import pandas as pd
import json
import google.generativeai as genai
from datetime import datetime, timedelta
import os
import re
import unicodedata
from dotenv import load_dotenv
try:
    import pyodbc
except ImportError:
    pyodbc = None
try:
    import pymssql
except ImportError:
    pymssql = None

# Cargar variables de entorno
load_dotenv()

# ==========================================
# 1. CONFIGURACIÓN Y BASE DE DATOS
# ==========================================

USER_AREA_DIVISION_MAP_PATH = "info/user_area_division_map.json"


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

    errors = []

    # Opcion preferida: pyodbc + ODBC Driver 18
    if pyodbc is not None:
        try:
            return pyodbc.connect(conn_str)
        except Exception as e:
            errors.append(f"pyodbc: {e}")

    # Fallback: pymssql (sin driver nativo del sistema)
    if pymssql is not None:
        try:
            parts = {}
            for chunk in conn_str.split(";"):
                if "=" not in chunk:
                    continue
                k, v = chunk.split("=", 1)
                parts[k.strip().lower()] = v.strip().strip("{}")

            raw_server = parts.get("server", "")
            if raw_server.lower().startswith("tcp:"):
                raw_server = raw_server[4:]
            host, port = (raw_server.split(",", 1) + ["1433"])[:2]

            return pymssql.connect(
                server=host,
                user=parts.get("uid"),
                password=parts.get("pwd"),
                database=parts.get("database"),
                port=int(port),
                login_timeout=int(parts.get("connection timeout", "30")),
                timeout=int(parts.get("connection timeout", "30")),
                tds_version="7.4",
            )
        except Exception as e:
            errors.append(f"pymssql: {e}")

    detail = " | ".join(errors) if errors else "No hay drivers Python disponibles."
    raise RuntimeError(f"No se pudo conectar a Azure SQL. {detail}")


def get_master_schema():
    return get_secret("DB_SCHEMA", "gestar")


def qname(table_name):
    return f"{get_master_schema()}.{table_name}"


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


def load_user_area_division_map():
    if not os.path.exists(USER_AREA_DIVISION_MAP_PATH):
        # Fallback to seed data if file doesn't exist
        try:
            from seed_data import USER_AREA_DIVISION_MAP

            out = {}
            for username, mapping in USER_AREA_DIVISION_MAP.items():
                out[normalize_text(username)] = {
                    "area": mapping.get("area"),
                    "division": mapping.get("division"),
                }
            return out
        except ImportError:
            return {}
    try:
        with open(USER_AREA_DIVISION_MAP_PATH, "r", encoding="utf-8") as f:
            raw = json.load(f)
        out = {}
        for username, mapping in raw.items():
            if not isinstance(mapping, dict):
                continue
            out[normalize_text(username)] = {
                "area": mapping.get("area"),
                "division": mapping.get("division"),
            }
        return out
    except Exception:
        return {}


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
        master_data = {
            "plantas": [
                {"id": row[0], "nombre": row[1]}
                for row in cursor.execute(
                    f"SELECT PlantaId, Nombre FROM {qname('Plantas')} WHERE Activo = 1"
                ).fetchall()
            ],
            "divisiones": [
                {"id": row[0], "nombre": row[1]}
                for row in cursor.execute(
                    f"SELECT DivisionId, Nombre FROM {qname('Divisiones')} WHERE Activo = 1"
                ).fetchall()
            ],
            "areas": [
                {"id": row[0], "nombre": row[1], "division_id": row[2]}
                for row in cursor.execute(
                    f"SELECT AreaId, Nombre, DivisionId FROM {qname('Areas')} WHERE Activo = 1"
                ).fetchall()
            ],
            "categorias": [
                {"id": row[0], "nombre": row[1]}
                for row in cursor.execute(
                    f"SELECT CategoriaId, Nombre FROM {qname('Categorias')} WHERE Activo = 1"
                ).fetchall()
            ],
            "subcategorias": [
                {"id": row[0], "nombre": row[1], "categoria_id": row[2]}
                for row in cursor.execute(
                    f"SELECT SubcategoriaId, Nombre, CategoriaId FROM {qname('Subcategorias')} WHERE Activo = 1"
                ).fetchall()
            ],
            "prioridades": [
                {"id": row[0], "nombre": row[1], "nivel": row[2]}
                for row in cursor.execute(
                    f"SELECT PrioridadId, Nombre, Nivel FROM {qname('Prioridades')}"
                ).fetchall()
            ],
            "estados": [
                {"id": row[0], "nombre": row[1]}
                for row in cursor.execute(
                    f"SELECT EstadoId, Nombre FROM {qname('Estados')}"
                ).fetchall()
            ],
            "usuarios": [
                {"id": row[0], "username": row[1], "email": row[2], "role": row[3]}
                for row in cursor.execute(
                    f"SELECT UserId, Username, Email, Role FROM {qname('Users')} WHERE Active = 1"
                ).fetchall()
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

    area = indexes["areas_by_norm"].get(normalize_text(draft.get("area")))
    if area:
        mapped["area_id"] = area["id"]
        if not mapped["division_id"]:
            mapped["division_id"] = area["division_id"]

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
            if not mapped["area_id"] and rel.get("area_id"):
                mapped["area_id"] = rel["area_id"]
            if not mapped["division_id"] and rel.get("division_id"):
                mapped["division_id"] = rel["division_id"]
            if (
                mapped["area_id"]
                and rel.get("area_id")
                and mapped["area_id"] != rel["area_id"]
            ):
                warnings.append(
                    "El área indicada no coincide con el área asociada al usuario sugerido."
                )
    elif user_warning and draft.get("usuario_sugerido"):
        warnings.append(user_warning)

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
            f"<b>Fecha de necesidad normalizada:</b> {fecha_norm_display}"
        )

        return resumen, False


# ==========================================
# 3. INTERFAZ STREAMLIT (WHATSAPP STYLE)
# ==========================================

st.set_page_config(page_title="Gestar IA - Asistente de Tickets", layout="wide")

# CSS para estilo WhatsApp
st.markdown(
    """
<style>
    .stApp { background-color: #f0f2f5; }
    .chat-bubble {
        padding: 10px 15px;
        border-radius: 15px;
        margin-bottom: 10px;
        max-width: 70%;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        white-space: pre-wrap;
    }
    .user-bubble {
        background-color: #dcf8c6;
        margin-left: auto;
        border-top-right-radius: 0;
    }
    .bot-bubble {
        background-color: #ffffff;
        margin-right: auto;
        border-top-left-radius: 0;
        box-shadow: 0 1px 0.5px rgba(0,0,0,0.13);
    }
    .chat-container {
        background-color: #e5ddd5;
        padding: 20px;
        border-radius: 10px;
        height: 600px;
        overflow-y: auto;
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

# Mostrar Mensajes
for msg in st.session_state.messages:
    role_class = "user-bubble" if msg["role"] == "user" else "bot-bubble"
    st.markdown(
        f'<div class="chat-bubble {role_class}">{msg["content"]}</div>',
        unsafe_allow_html=True,
    )

# Si hay botones activos, se muestran debajo del último mensaje
if st.session_state.show_confirm_buttons:
    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Crear Ticket", key="btn_crear"):
            d = st.session_state.ticket_draft
            ids, map_warnings = map_entities_to_ids(
                d, st.session_state.master_indexes, st.session_state.master_data
            )
            need_by_dt = safe_parse_datetime(d.get("fecha_necesidad"))
            d["fecha_necesidad_resuelta"] = (
                need_by_dt.strftime("%Y-%m-%d %H:%M:%S") if need_by_dt else None
            )
            score = compute_completeness_score(d, ids)

            conn = get_azure_master_connection()
            cursor = conn.cursor()

            cursor.execute(
                f"SELECT TOP 1 UserId FROM {qname('Users')} WHERE Active = 1 ORDER BY UserId"
            )
            requester = cursor.fetchone()
            requester_id = requester[0] if requester else None
            tickets_table = qname("Tickets")

            cursor.execute(
                f"""
                INSERT INTO {tickets_table} (
                    Title, Description, RequesterId, SuggestedAssigneeId, AssigneeId,
                    PlantaId, AreaId, CategoriaId, SubcategoriaId, PrioridadId, EstadoId,
                    ConfidenceScore, OriginalPrompt, AiProcessingTime, ConversationId, NeedByAt
                ) OUTPUT INSERTED.TicketId VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    d.get("titulo") or "Ticket sin titulo",
                    d.get("descripcion") or "Sin descripción detallada",
                    requester_id,
                    ids.get("suggested_assignee_id"),
                    None,
                    ids.get("planta_id"),
                    ids.get("area_id"),
                    ids.get("categoria_id"),
                    ids.get("subcategoria_id"),
                    ids.get("prioridad_id"),
                    ids.get("estado_id"),
                    st.session_state.last_ai_res.get("confidence", 0.8),
                    st.session_state.last_prompt or "Confirmado por botón",
                    int(st.session_state.last_ai_res.get("ai_processing_time", 0)),
                    st.session_state.last_ai_res.get("conversation_id"),
                    d.get("fecha_necesidad_resuelta"),
                ),
            )
            # SQL Server: recuperamos el TicketId desde OUTPUT INSERTED
            ticket_row = cursor.fetchone()
            t_id = ticket_row[0] if ticket_row else None
            conn.commit()
            conn.close()

            warnings = []
            if not ids.get("area_id") and not ids.get("suggested_assignee_id"):
                warnings.append(
                    "Falta Área o Usuario sugerido. El ticket puede requerir más revisión del responsable del área."
                )
            warnings.extend(map_warnings)
            if d.get("fecha_necesidad") and not d.get("fecha_necesidad_resuelta"):
                warnings.append(
                    "No pude normalizar la Fecha de Necesidad. Se guardó sin fecha normalizada."
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
            # Reset
            for k in st.session_state.ticket_draft:
                st.session_state.ticket_draft[k] = None
            st.session_state.show_confirm_buttons = False
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

# Chat Input
if prompt := st.chat_input("Escribe tu reporte aquí..."):
    # Agregar mensaje de usuario
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.session_state.show_confirm_buttons = (
        False  # Ocultar botones al recibir nuevo input
    )
    st.rerun()

# Procesar último mensaje si es del usuario
if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
    assistant = TicketAssistant(api_key, model_name)
    user_input = st.session_state.messages[-1]["content"]

    # 1. Procesamiento con IA
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

            # --- FLUJO SOCIAL ---
            if intencion == "social":
                bot_res = ai_res.get(
                    "respuesta_social",
                    "¡Hola! Estoy listo para ayudarte. Por favor, dime qué necesitas reportar.",
                )

            # --- FLUJO CREAR TICKET ---
            elif intencion == "crear_ticket":
                # Actualizar borrador con lo nuevo (si no es null)
                for k in st.session_state.ticket_draft.keys():
                    v = ai_res.get(k)
                    if v is not None and v != "":
                        st.session_state.ticket_draft[k] = v

                # Resolver usuario sugerido para mostrar nombre+mail en el resumen
                resolved_user, _ = resolve_user_candidate(
                    st.session_state.ticket_draft.get("usuario_sugerido"),
                    st.session_state.master_indexes,
                )
                st.session_state.ticket_draft["usuario_sugerido_resuelto"] = (
                    resolved_user
                )

                parsed_need = safe_parse_datetime(
                    st.session_state.ticket_draft.get("fecha_necesidad")
                )
                st.session_state.ticket_draft["fecha_necesidad_resuelta"] = (
                    parsed_need.strftime("%Y-%m-%d %H:%M:%S") if parsed_need else None
                )

                # 2. Generar mensaje de revisión o bloqueo (ya con fecha normalizada)
                bot_res, bloqueante = assistant.generate_review_message(
                    st.session_state.ticket_draft
                )

                if not bloqueante:
                    st.session_state.show_confirm_buttons = True

            # --- FALLBACK ---
            else:
                bot_res = "No estoy seguro de haber entendido. ¿Podrías darme más detalles sobre el problema o solicitud?"

            st.session_state.messages.append({"role": "assistant", "content": bot_res})
            st.rerun()
        else:
            st.sidebar.error(f"Error de API: {ai_res['error']}")

# Mostrar Debug en el Sidebar
with debug_expander:
    st.write("**Borrador Actual:**", st.session_state.ticket_draft)
    st.write("**Última Respuesta JSON IA:**", st.session_state.last_ai_res)
    st.write("**Prompt Enviado:**")
    st.code(st.session_state.last_prompt or "", language="text")

# Panel izquierdo (sidebar): tabla de tickets al final
with st.sidebar:
    st.divider()
    st.subheader("Tickets Cargados")
    try:
        conn = get_azure_master_connection()
        tickets_df = pd.read_sql_query(
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
            """,
            conn,
        )
        conn.close()
        if tickets_df.empty:
            st.caption("No hay tickets cargados.")
        else:
            st.dataframe(tickets_df, use_container_width=True, height=260)
    except Exception as err:
        st.caption(f"No se pudo cargar tickets: {err}")
