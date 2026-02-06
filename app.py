import streamlit as st
import sqlite3
import pandas as pd
import json
import google.generativeai as genai
from datetime import datetime

# ==========================================
# 1. CONFIGURACIÓN Y BASE DE DATOS
# ==========================================

DB_PATH = "tickets_mvp.db"


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Tablas Maestras (basadas en database_schema.sql)
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS Plantas (PlantaId INTEGER PRIMARY KEY AUTOINCREMENT, Nombre TEXT UNIQUE, Activo INTEGER DEFAULT 1)"
    )
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS Divisiones (DivisionId INTEGER PRIMARY KEY AUTOINCREMENT, Nombre TEXT UNIQUE, Activo INTEGER DEFAULT 1)"
    )
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS Areas (AreaId INTEGER PRIMARY KEY AUTOINCREMENT, Nombre TEXT, DivisionId INTEGER, Activo INTEGER DEFAULT 1, FOREIGN KEY (DivisionId) REFERENCES Divisiones(DivisionId))"
    )
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS Categorias (CategoriaId INTEGER PRIMARY KEY AUTOINCREMENT, Nombre TEXT UNIQUE, Activo INTEGER DEFAULT 1)"
    )
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS Subcategorias (SubcategoriaId INTEGER PRIMARY KEY AUTOINCREMENT, Nombre TEXT, CategoriaId INTEGER, Activo INTEGER DEFAULT 1, FOREIGN KEY (CategoriaId) REFERENCES Categorias(CategoriaId))"
    )
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS Prioridades (PrioridadId INTEGER PRIMARY KEY AUTOINCREMENT, Nombre TEXT UNIQUE, Nivel INTEGER)"
    )
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS Estados (EstadoId INTEGER PRIMARY KEY AUTOINCREMENT, Nombre TEXT UNIQUE)"
    )
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS Users (UserId INTEGER PRIMARY KEY AUTOINCREMENT, Username TEXT UNIQUE, Email TEXT UNIQUE, Role TEXT, Active INTEGER DEFAULT 1, CreatedAt DATETIME DEFAULT CURRENT_TIMESTAMP)"
    )

    # Tabla Tickets
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Tickets (
        TicketId INTEGER PRIMARY KEY AUTOINCREMENT,
        Title TEXT,
        Description TEXT,
        RequesterId INTEGER,
        AssigneeId INTEGER,
        PlantaId INTEGER,
        AreaId INTEGER,
        CategoriaId INTEGER,
        SubcategoriaId INTEGER,
        PrioridadId INTEGER,
        EstadoId INTEGER,
        ConfidenceScore REAL,
        OriginalPrompt TEXT,
        AiProcessingTime INTEGER,
        ConversationId TEXT,
        CreatedAt DATETIME DEFAULT CURRENT_TIMESTAMP,
        UpdatedAt DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (RequesterId) REFERENCES Users(UserId),
        FOREIGN KEY (PlantaId) REFERENCES Plantas(PlantaId),
        FOREIGN KEY (AreaId) REFERENCES Areas(AreaId),
        FOREIGN KEY (CategoriaId) REFERENCES Categorias(CategoriaId),
        FOREIGN KEY (SubcategoriaId) REFERENCES Subcategorias(SubcategoriaId),
        FOREIGN KEY (PrioridadId) REFERENCES Prioridades(PrioridadId),
        FOREIGN KEY (EstadoId) REFERENCES Estados(EstadoId)
    )
    """)

    # Datos Semilla
    master_data = {
        "Estados": [("Abierto",), ("En Progreso",), ("Cerrado",)],
        "Prioridades": [("Baja", 3), ("Media", 2), ("Alta", 1), ("Crítica", 0)],
        "Divisiones": [("Sellado",), ("Forja",), ("Distribución",)],
        "Plantas": [("Planta 1",), ("Planta 2",)],
        "Categorias": [("Mantenimiento",), ("IT",), ("Producción",)],
        "Users": [
            ("juan_perez", "juan@empresa.com", "Solicitante"),
            ("tecnico_1", "soporte@empresa.com", "Tecnico"),
        ],
    }

    for table, data in master_data.items():
        placeholders = ",".join(["?"] * len(data[0]))
        cursor.executemany(
            f"INSERT OR IGNORE INTO {table} ({','.join(['Nombre', 'Nivel'] if table == 'Prioridades' else ['Username', 'Email', 'Role'] if table == 'Users' else ['Nombre'])}) VALUES ({placeholders})",
            data,
        )

    # Subcategorías y Áreas iniciales
    cursor.execute(
        "INSERT OR IGNORE INTO Subcategorias (Nombre, CategoriaId) SELECT 'Falla Eléctrica', CategoriaId FROM Categorias WHERE Nombre = 'Mantenimiento'"
    )
    cursor.execute(
        "INSERT OR IGNORE INTO Areas (Nombre, DivisionId) SELECT 'Prensa 1', DivisionId FROM Divisiones WHERE Nombre = 'Forja'"
    )

    conn.commit()
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

    def extract_entities(self, user_input, context_json):
        if not self.model:
            return {"error": "API Key no configurada"}, 0, ""

        system_prompt = f"""
        Eres un experto en clasificación de intenciones y extracción de entidades para un sistema de tickets industrial.
        Tu salida debe ser ÚNICAMENTE un objeto JSON válido.

        ### Reglas de Clasificación:
        1. Si el mensaje es un saludo, despedida, agradecimiento o charla trivial (ej: "hola", "gracias", "ok"), define:
           - "intencion": "social"
           - "respuesta_social": Una respuesta amigable y breve que invite a reportar un problema.
        2. Si el mensaje describe un problema, avería o solicitud técnica, define:
           - "intencion": "crear_ticket"
        3. En cualquier otro caso:
           - "intencion": "desconocido"

        ### Extracción (solo si intencion es "crear_ticket"):
        - titulo: Breve resumen (string o null)
        - descripcion: Detalle (string o null)
        - planta: Nombre de planta (string o null)
        - division: Nombre de división (string o null)
        - area: Nombre del área (string o null)
        - categoria: Categoría principal (string o null)
        - subcategoria: Subcategoría específica (string o null)
        - prioridad: Prioridad inferida (Alta, Media, Baja, Crítica o null)
        
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
        # 1. Validación Mínima (Bloqueante)
        # Solo detenemos al usuario si no sabemos DE QUÉ se trata el ticket (Título).
        if not draft.get("titulo"):
            return (
                "Entendido, quieres crear un ticket. Por favor, dale un título o describe brevemente el problema (ej: 'Falla impresora en planta 2').",
                True,
            )

        # 2. Asignación de Valores por Defecto (Lógica de Negocio)
        descripcion_display = draft.get("descripcion") or "Sin descripción detallada"
        prioridad_display = draft.get("prioridad") or "Media (Por defecto)"
        area_display = draft.get("area") or "Sin asignar (Se definirá en triage)"
        planta_display = draft.get("planta") or "No especificada"

        # 3. Construcción del Resumen
        resumen = (
            f"<b>Título:</b> {draft.get('titulo')}\n"
            f"<b>Descripción:</b> {descripcion_display}\n"
            f"<b>Ubicación:</b> {planta_display}\n"
            f"<b>Área:</b> {area_display}\n"
            f"<b>Prioridad:</b> {prioridad_display}"
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

init_db()

# Sidebar
with st.sidebar:
    st.title("⚙️ Configuración")
    api_key = st.text_input("Google API Key", type="password")
    model_name = st.selectbox(
        "Modelo", ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-pro"]
    )

    st.divider()
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
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            # Inserción simplificada para MVP
            cursor.execute(
                "INSERT INTO Tickets (Title, Description, OriginalPrompt, ConfidenceScore) VALUES (?, ?, ?, ?)",
                (
                    d["titulo"],
                    d["descripcion"] or "Generado via resumen",
                    "Confirmado por botón",
                    1.0,
                ),
            )
            t_id = cursor.lastrowid
            conn.commit()
            conn.close()

            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": f"✅ ¡Ticket #{t_id} creado con éxito!",
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
        ai_res, p_time, s_prompt = assistant.extract_entities(
            user_input, st.session_state.ticket_draft
        )
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
                    if v:
                        st.session_state.ticket_draft[k] = v

                # 2. Generar mensaje de revisión o bloqueo
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
    st.write("**Prompt Enviado:**", st.session_state.last_prompt)
