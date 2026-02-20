import streamlit as st
import json
import base64

st.set_page_config(page_title="Diagnóstico Entra ID", layout="wide")

st.title("🔍 Diagnóstico de Identidad (Entra ID)")
st.info(
    "Este script muestra toda la información que el Azure App Service inyecta en la aplicación."
)

# 1. Inspeccionar Headers de Streamlit
st.subheader("1. Headers de la Solicitud")
headers = {}
try:
    # Intentar obtener headers del contexto de streamlit
    ctx = getattr(st, "context", None)
    raw_headers = getattr(ctx, "headers", None) if ctx is not None else None
    if raw_headers:
        for k, v in raw_headers.items():
            headers[str(k)] = str(v)
        st.json(headers)
    else:
        st.warning(
            "No se pudieron detectar headers vía st.context. Asegúrate de estar corriendo en Streamlit 1.30+"
        )
except Exception as e:
    st.error(f"Error al leer headers: {e}")

# 2. Decodificar x-ms-client-principal
st.subheader("2. Claims de Entra ID")
principal_raw = headers.get("X-Ms-Client-Principal") or headers.get(
    "x-ms-client-principal"
)

if principal_raw:
    try:
        # Decodificar Base64
        decoded_bytes = base64.b64decode(principal_raw)
        decoded_str = decoded_bytes.decode("utf-8")
        principal_data = json.loads(decoded_str)

        st.success("✅ Claim 'x-ms-client-principal' decodificado con éxito")
        st.json(principal_data)

        # Extraer claims específicos para facilitar lectura
        st.write("### Resumen de Claims")
        claims = principal_data.get("claims", [])
        claim_summary = {c.get("typ"): c.get("val") for c in claims if "typ" in c}
        st.table(list(claim_summary.items()))

    except Exception as e:
        st.error(f"Error al decodificar principal: {e}")
else:
    st.warning(
        "⚠️ No se encontró el header 'x-ms-client-principal'. Esto es normal si estás corriendo LOCAL. Pruébalo en Azure App Service."
    )

# 3. Datos de Sesión de Streamlit
st.subheader("3. Session State")
st.write(st.session_state)
