# app.py - Punt d'entrada de l'aplicació Marathon Companion
import streamlit as st
from i18n import t
from auth import check_password

# Configuració principal de la pàgina
st.set_page_config(
    page_title=t("app_title"),
    page_icon=t("app_page_icon"),
    layout="wide",
    initial_sidebar_state="expanded"
)

# Verificar autenticació
if not check_password():
    st.stop()

# Redirigir automàticament a la pàgina d'Inici
st.switch_page("pages/0_Inici.py")