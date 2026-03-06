# Gestar IA - Asistente de Carga de Tickets Híbrido

Este es un MVP de un **Asistente de Tickets** que utiliza una arquitectura híbrida (Inteligencia Artificial + Reglas de Negocio) para facilitar la carga de incidentes en entornos industriales. La interfaz está diseñada para imitar la experiencia de **WhatsApp Web**, ofreciendo una interacción familiar para los usuarios.

## 🚀 Características

- **Interfaz Estilo WhatsApp**: Burbujas de chat, colores corporativos y diseño responsivo utilizando Streamlit y CSS personalizado.
- **Extracción de Entidades con IA**: Integración con **Google Gemini (2.0 Flash)** para procesar lenguaje natural y extraer datos críticos (Planta, Área, Categoría, Prioridad).
- **Lógica Híbrida**: 
    - La IA extrae la información.
    - Un sistema de reglas en Python valida los datos y solicita información faltante de forma guiada.
- **Base de Datos Jerárquica**: Esquema SQL normalizado con soporte para Divisiones, Áreas, Categorías y Subcategorías (SQLite local para MVP).
- **Área de Debug**: Sidebar integrado para desarrolladores donde se puede observar el estado del JSON, el prompt enviado y el tiempo de procesamiento.

## 🛠️ Tecnologías

- **Lenguaje**: Python 3.10+
- **Frontend**: Streamlit
- **IA**: Google Generative AI (Gemini API)
- **Base de Datos**: SQLite3 / SQL Server (Esquema incluido)
- **Procesamiento de Datos**: Pandas

## 📂 Estructura del Proyecto

- `app.py`: Aplicación principal de Streamlit.
- `database_schema.sql`: Script SQL profesional con la estructura jerárquica y auditoría.
- `requirements.txt`: Dependencias del proyecto.
- `promp db.md`: Documentación de los prompts utilizados para el diseño del sistema.

## ⚙️ Instalación y Configuración

1.  **Clonar el repositorio**:
    ```bash
    git clone https://github.com/tu-usuario/gestar-ia.git
    cd gestar-ia
    ```

2.  **Instalar dependencias**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configurar Variables**:
    - Obtén una API Key de [Google AI Studio](https://aistudio.google.com/).
    - Al ejecutar la app, introduce la API Key en el campo correspondiente del Sidebar.
    - Para seleccionar backend de base de datos:
      - `DB_MODE=azure` (default, usa `ODBC_CONN_STR`)
      - `DB_MODE=sqlite` (usa `SQLITE_PATH`, por ejemplo `tickets_mvp.db`)
    - En modo SQLite puedes bootstrapear el esquema con:
    ```bash
    python scripts/bootstrap_sqlite.py --db tickets_mvp.db
    ```

4.  **Ejecutar la aplicación**:
    ```bash
    streamlit run app.py
    ```

## 📝 Auditoría e IA
El sistema está diseñado para el aprendizaje continuo. Cada ticket guarda el `OriginalPrompt` y el `ConfidenceScore` de la IA, permitiendo auditorías de calidad para mejorar el modelo de extracción en el futuro.

---
Desarrollado como prototipo para el sistema de gestión interna.
