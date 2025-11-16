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
import os
db_url = get_database_url()

with st.sidebar.expander("🔍 Debug BD", expanded=True):
    st.write("**Detección de BD:**")
    if db_url:
        st.success(f"✅ URL encontrada ({len(db_url)} chars)")
        try:
            st.caption(f"Host: {db_url.split('@')[1].split(':')[0] if '@' in db_url else 'unknown'}")
        except:
            st.caption("Host: error parseando")
    else:
        st.warning("⚠️ No se detectó DATABASE_URL")

    st.caption(f"is_postgres(): {is_postgres()}")
    st.caption(f"POSTGRES_AVAILABLE: {os.getenv('POSTGRES_AVAILABLE', 'No set')}")

    # Mostrar qué secrets están disponibles
    try:
        st.write("**Secrets disponibles:**")
        st.write(list(st.secrets.keys()))
        if 'database' in st.secrets:
            st.success("✅ 'database' key encontrada")
            st.caption(f"URL length: {len(st.secrets['database']['url'])}")
        else:
            st.error("❌ 'database' key NO encontrada")
    except Exception as e:
        st.error(f"Error leyendo secrets: {e}")

    # Test de conexión directo
    if st.button("🔌 Test conexión PostgreSQL"):
        if not db_url:
            st.error("No hay URL de base de datos configurada")
        else:
            try:
                import psycopg2
                st.info(f"Intentando conectar a: {db_url[:50]}...")
                conn = psycopg2.connect(db_url)
                st.success("✅ ¡Conexión exitosa!")
                cursor = conn.cursor()
                cursor.execute("SELECT version();")
                version = cursor.fetchone()
                st.write(f"PostgreSQL version: {version[0][:50]}...")
                conn.close()
            except Exception as e:
                st.error(f"❌ Error de conexión: {type(e).__name__}")
                st.code(str(e))

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