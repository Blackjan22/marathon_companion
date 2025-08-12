# my_runs_analytics.py
import streamlit as st
from strava_client import sync_new_activities  # Asumiendo que este archivo existe

# Configuración principal de la página. Solo se llama una vez.
st.set_page_config(
    page_title="Running Analytics",
    page_icon="🏃‍♂️",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
Esta aplicación te permite visualizar y analizar todas las carreras que has sincronizado desde Strava.

**Características principales:**
- **Dashboard General:** Un resumen de tus métricas clave.
- **Análisis de Rendimiento:** Estudia la evolución de tu ritmo, frecuencia cardíaca y más.
- **Análisis de Ritmos:** Profundiza en tus zonas de entrenamiento.
- **Tendencias Temporales:** Descubre tus patrones de entrenamiento semanales y mensuales.
- **Análisis de Splits:** Revisa el ritmo de cada kilómetro en carreras específicas.
- **Histórico Completo:** Una tabla con todas tus actividades para buscar y filtrar.
- **Coach:** Un entrenador personal basado en IA.

¡Usa el menú de la izquierda para navegar!
""")