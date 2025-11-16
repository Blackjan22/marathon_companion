# my_runs_analytics.py
import streamlit as st
from strava_client import sync_new_activities
from utils.db_config import get_database_url, is_postgres

# Configuración principal de la página. Solo se llama una vez.
st.set_page_config(
    page_title="Running Analytics",
    page_icon="🏃‍♂️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# DEBUG: Mostrar info de base de datos
db_url = get_database_url()
if db_url:
    st.sidebar.success(f"✅ PostgreSQL detectado ({len(db_url)} chars)")
    st.sidebar.caption(f"Host: {db_url.split('@')[1].split(':')[0] if '@' in db_url else 'unknown'}")
else:
    st.sidebar.warning("⚠️ Usando SQLite local")
st.sidebar.caption(f"is_postgres: {is_postgres()}")

# --- BARRA LATERAL (SIDEBAR) ---
# El botón de refresco y los filtros comunes pueden ir aquí si quieres que aparezcan en todas las páginas.
# O pueden ir en cada página individualmente. Por ahora, lo dejamos aquí para que sea global.

st.sidebar.title("Opciones")

# Botón para refrescar actividades
if st.sidebar.button("🔄 Refrescar actividades"):
    with st.spinner("Sincronizando nuevas actividades desde Strava..."):
        try:
            sync_new_activities('data/strava_activities.db')
            st.success("✅ ¡Actividades actualizadas!")
            # Limpiamos la caché de datos para forzar la recarga
            st.cache_data.clear()
            st.rerun()
        except Exception as e:
            st.error(f"No se pudo sincronizar: {e}")


# --- PÁGINA PRINCIPAL ---
st.title("🏃‍♂️ My Runs Analytics")
st.header("Bienvenido a tu panel de análisis de carreras")

st.info("Selecciona una de las páginas en el menú de la izquierda para comenzar el análisis.")
st.markdown("""
Esta aplicación te permite visualizar y analizar todas las carreras que has sincronizado desde Strava,
con planificación inteligente de entrenamientos mediante IA.

**Características principales:**
- **📊 Dashboard General:** Resumen de tus métricas clave y análisis de progreso.
- **📋 Histórico Completo:** Tabla con todas tus actividades para buscar, filtrar y analizar en detalle.
- **📅 Planificación:** Gestiona tus planes de entrenamiento semanales y vincula actividades.
- **🤖 Coach IA:** Chatbot inteligente que analiza tu progreso y crea planes personalizados.

¡Usa el menú de la izquierda para navegar!
""")