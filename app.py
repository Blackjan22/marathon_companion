# my_runs_analytics.py
import streamlit as st
from strava_client import sync_new_activities
from utils.db_config import get_database_url, is_postgres
from i18n import t

# Configuració principal de la pàgina. Només es crida una vegada.
st.set_page_config(
    page_title=t("app_title"),
    page_icon=t("app_page_icon"),
    layout="wide",
    initial_sidebar_state="expanded"
)

# DEBUG: Mostrar info de base de datos
import os
db_url = get_database_url()

with st.sidebar.expander(t("debug_bd"), expanded=True):
    st.write(t("db_detection"))
    if db_url:
        st.success(t("db_url_found", length=len(db_url)))
        try:
            host = db_url.split('@')[1].split(':')[0] if '@' in db_url else 'unknown'
            st.caption(t("db_host", host=host))
        except:
            st.caption(t("db_host_error"))
    else:
        st.warning(t("db_url_not_found"))

    st.caption(f"is_postgres(): {is_postgres()}")
    st.caption(f"POSTGRES_AVAILABLE: {os.getenv('POSTGRES_AVAILABLE', 'No set')}")

    # Mostrar quins secrets estan disponibles
    try:
        st.write(t("secrets_available"))
        st.write(list(st.secrets.keys()))
        if 'database' in st.secrets:
            st.success(t("database_key_found"))
            st.caption(f"URL length: {len(st.secrets['database']['url'])}")
        else:
            st.error(t("database_key_not_found"))
    except Exception as e:
        st.error(t("secrets_error", error=str(e)))

    # Test de connexió directe
    if st.button(t("test_connection")):
        if not db_url:
            st.error(t("no_db_url"))
        else:
            try:
                import psycopg2
                st.info(t("connecting_to", url=db_url[:50]))
                conn = psycopg2.connect(db_url)
                st.success(t("connection_success"))
                cursor = conn.cursor()
                cursor.execute("SELECT version();")
                version = cursor.fetchone()
                st.write(t("postgres_version", version=version[0][:50]))
                conn.close()
            except Exception as e:
                st.error(t("connection_error", error_type=type(e).__name__))
                st.code(str(e))

# --- BARRA LATERAL (SIDEBAR) ---
# El botó de refresc i els filtres comuns poden anar aquí si vols que apareguin a totes les pàgines.
# O poden anar a cada pàgina individualment. Per ara, ho deixem aquí perquè sigui global.

st.sidebar.title(t("sidebar_options"))

# Botó per refrescar activitats
if st.sidebar.button(t("refresh_activities")):
    with st.spinner(t("syncing_activities")):
        try:
            sync_new_activities('data/strava_activities.db')
            st.success(t("activities_updated"))
            # Netegem la caché de dades per forçar la recàrrega
            st.cache_data.clear()
            st.rerun()
        except Exception as e:
            st.error(t("sync_error", error=str(e)))


# --- PÀGINA PRINCIPAL ---
st.title(t("welcome_title"))
st.header(t("welcome_header"))

st.info(t("select_page_info"))
st.markdown(t("app_description"))