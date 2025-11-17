"""
Mòdul d'autenticació per l'aplicació Marathon Companion
"""
import streamlit as st
import hashlib


def hash_password(password: str) -> str:
    """
    Genera un hash SHA-256 d'una contrasenya.

    Args:
        password: La contrasenya en text pla

    Returns:
        El hash SHA-256 de la contrasenya
    """
    return hashlib.sha256(password.encode()).hexdigest()


def check_password() -> bool:
    """
    Verifica si l'usuari està autenticat.
    Si no ho està, mostra un formulari de login.

    Returns:
        True si l'usuari està autenticat, False altrament
    """
    # Si ja està autenticat, retornem True
    if st.session_state.get("authenticated", False):
        return True

    # Carregar credencials des de secrets
    try:
        valid_username = st.secrets.get("auth", {}).get("username", "")
        valid_password_hash = st.secrets.get("auth", {}).get("password_hash", "")
    except Exception as e:
        st.error(f"Error carregant credencials: {str(e)}")
        return False

    # Mostrar formulari de login
    st.title("🔐 Accés a Marathon Companion")
    st.write("Introdueix les teves credencials per accedir a l'aplicació.")

    with st.form("login_form"):
        username = st.text_input("Usuari", key="username_input")
        password = st.text_input("Contrasenya", type="password", key="password_input")
        submit = st.form_submit_button("Iniciar sessió")

        if submit:
            # Verificar credencials
            password_hash = hash_password(password)

            if username == valid_username and password_hash == valid_password_hash:
                st.session_state["authenticated"] = True
                st.success("✅ Autenticació correcta!")
                st.rerun()
            else:
                st.error("❌ Usuari o contrasenya incorrectes")
                return False

    return False


def logout():
    """
    Tanca la sessió de l'usuari.
    """
    st.session_state["authenticated"] = False
    st.rerun()


def add_logout_button():
    """
    Afegeix un botó de logout a baix de tot de la sidebar.
    """
    if st.session_state.get("authenticated", False):
        # Afegir espai per empènyer el botó cap avall
        st.sidebar.write("")
        st.sidebar.write("")

        # Usar container per fixar-lo a baix
        with st.sidebar:
            st.divider()
            cols = st.columns([1, 2, 1])
            with cols[1]:
                if st.button("🚪 Tancar sessió", use_container_width=True):
                    logout()
