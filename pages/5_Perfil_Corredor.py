# pages/5_Perfil_Corredor.py
import streamlit as st
import sys
import os
from datetime import datetime

# Afegir el directori src al path per importar mòduls
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.db_config import get_connection
from i18n import t
from auth import check_password, add_logout_button

st.set_page_config(layout="wide")

# Verificar autenticació
if not check_password():
    st.stop()

# Afegir botó de logout a la sidebar
add_logout_button()

st.title(t("profile_title"))

st.markdown(t("profile_description"))


def get_current_profile():
    """Obté el perfil actual de la base de dades."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM runner_profile ORDER BY updated_at DESC LIMIT 1")
    row = cur.fetchone()
    conn.close()

    if not row:
        return None

    # Convertir row a dict
    columns = [
        'id', 'name', 'height_cm', 'weight_kg', 'age', 'vo2max_estimate',
        'threshold_pace', 'easy_pace_min', 'easy_pace_max', 'training_philosophy',
        'current_goal', 'goal_race_date', 'goal_race_distance',
        'pr_5k', 'pr_10k', 'pr_half', 'pr_marathon', 'created_at', 'updated_at'
    ]
    return dict(zip(columns, row))


def save_profile(profile_data):
    """Guarda o actualitza el perfil a la base de dades."""
    conn = get_connection()
    cur = conn.cursor()

    # Verificar si ya existe un perfil
    current = get_current_profile()

    if current:
        # Actualizar
        cur.execute("""
            UPDATE runner_profile
            SET name = ?, height_cm = ?, weight_kg = ?, age = ?,
                vo2max_estimate = ?, threshold_pace = ?, easy_pace_min = ?, easy_pace_max = ?,
                training_philosophy = ?, current_goal = ?, goal_race_date = ?, goal_race_distance = ?,
                pr_5k = ?, pr_10k = ?, pr_half = ?, pr_marathon = ?,
                updated_at = ?
            WHERE id = ?
        """, (
            profile_data['name'], profile_data['height_cm'], profile_data['weight_kg'], profile_data['age'],
            profile_data['vo2max_estimate'], profile_data['threshold_pace'], profile_data['easy_pace_min'], profile_data['easy_pace_max'],
            profile_data['training_philosophy'], profile_data['current_goal'], profile_data['goal_race_date'], profile_data['goal_race_distance'],
            profile_data['pr_5k'], profile_data['pr_10k'], profile_data['pr_half'], profile_data['pr_marathon'],
            datetime.now().isoformat(),
            current['id']
        ))
    else:
        # Insertar nuevo
        cur.execute("""
            INSERT INTO runner_profile (
                name, height_cm, weight_kg, age,
                vo2max_estimate, threshold_pace, easy_pace_min, easy_pace_max,
                training_philosophy, current_goal, goal_race_date, goal_race_distance,
                pr_5k, pr_10k, pr_half, pr_marathon, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            profile_data['name'], profile_data['height_cm'], profile_data['weight_kg'], profile_data['age'],
            profile_data['vo2max_estimate'], profile_data['threshold_pace'], profile_data['easy_pace_min'], profile_data['easy_pace_max'],
            profile_data['training_philosophy'], profile_data['current_goal'], profile_data['goal_race_date'], profile_data['goal_race_distance'],
            profile_data['pr_5k'], profile_data['pr_10k'], profile_data['pr_half'], profile_data['pr_marathon'],
            datetime.now().isoformat(),
            datetime.now().isoformat()
        ))

    conn.commit()
    conn.close()


# Cargar perfil actual
current_profile = get_current_profile()

# Formulari
with st.form("profile_form"):
    st.subheader(t("basic_info"))

    col1, col2, col3 = st.columns(3)

    with col1:
        name = st.text_input(
            t("name"),
            value=current_profile['name'] if current_profile else "",
            placeholder="El teu nom"
        )

    with col2:
        height_cm = st.number_input(
            t("height"),
            min_value=140.0,
            max_value=220.0,
            value=float(current_profile['height_cm']) if current_profile and current_profile['height_cm'] else 175.0,
            step=1.0
        )

    with col3:
        weight_kg = st.number_input(
            t("weight"),
            min_value=40.0,
            max_value=150.0,
            value=float(current_profile['weight_kg']) if current_profile and current_profile['weight_kg'] else 70.0,
            step=0.5
        )

    age = st.number_input(
        t("age"),
        min_value=15,
        max_value=100,
        value=int(current_profile['age']) if current_profile and current_profile['age'] else 30,
        step=1
    )

    st.divider()
    st.subheader(t("training_zones"))

    col1, col2, col3 = st.columns(3)

    with col1:
        threshold_pace = st.text_input(
            t("threshold_pace"),
            value=current_profile['threshold_pace'] if current_profile and current_profile['threshold_pace'] else "",
            placeholder=t("threshold_pace_placeholder"),
            help="Ritme que pots mantenir ~1 hora a esforç alt"
        )

    with col2:
        easy_pace_min = st.text_input(
            t("easy_pace_min"),
            value=current_profile['easy_pace_min'] if current_profile and current_profile['easy_pace_min'] else "",
            placeholder="Ex: 5:30"
        )

    with col3:
        easy_pace_max = st.text_input(
            t("easy_pace_max"),
            value=current_profile['easy_pace_max'] if current_profile and current_profile['easy_pace_max'] else "",
            placeholder="Ex: 6:00"
        )

    vo2max_estimate = st.number_input(
        t("vo2max"),
        min_value=30.0,
        max_value=90.0,
        value=float(current_profile['vo2max_estimate']) if current_profile and current_profile['vo2max_estimate'] else 50.0,
        step=1.0,
        help="Pots obtenir-lo de rellotges Garmin/Polar o calculadores online"
    )

    st.divider()
    st.subheader(t("current_goals"))

    col1, col2 = st.columns(2)

    with col1:
        current_goal = st.text_area(
            t("current_goal"),
            value=current_profile['current_goal'] if current_profile and current_profile['current_goal'] else "",
            placeholder=t("goal_placeholder"),
            height=100
        )

        goal_race_distance = st.selectbox(
            t("goal_race_distance"),
            options=["", "5K", "10K", "15K", "Mitja Marató", "Marató", "Altra"],
            index=0 if not current_profile or not current_profile['goal_race_distance'] else
                  ["", "5K", "10K", "15K", "Mitja Marató", "Marató", "Altra"].index(current_profile['goal_race_distance']) if current_profile['goal_race_distance'] in ["", "5K", "10K", "15K", "Mitja Marató", "Marató", "Altra"] else 0
        )

    with col2:
        goal_race_date = st.date_input(
            t("goal_race_date"),
            value=datetime.fromisoformat(current_profile['goal_race_date']).date() if current_profile and current_profile['goal_race_date'] else None,
            help="Deixa en blanc si no tens data definida"
        )

        training_philosophy = st.text_area(
            t("training_philosophy_label"),
            value=current_profile['training_philosophy'] if current_profile and current_profile['training_philosophy'] else "",
            placeholder=t("training_philosophy_placeholder"),
            height=100,
            help="Descriu el teu enfocament: dies disponibles, prioritats, restriccions..."
        )

    st.divider()
    st.subheader(t("personal_records_section"))

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        pr_5k = st.text_input(
            t("pr_5k_label"),
            value=current_profile['pr_5k'] if current_profile and current_profile['pr_5k'] else "",
            placeholder=t("pr_5k_placeholder")
        )

    with col2:
        pr_10k = st.text_input(
            t("pr_10k_label"),
            value=current_profile['pr_10k'] if current_profile and current_profile['pr_10k'] else "",
            placeholder=t("pr_10k_placeholder")
        )

    with col3:
        pr_half = st.text_input(
            t("pr_half_label"),
            value=current_profile['pr_half'] if current_profile and current_profile['pr_half'] else "",
            placeholder=t("pr_half_placeholder")
        )

    with col4:
        pr_marathon = st.text_input(
            t("pr_marathon_label"),
            value=current_profile['pr_marathon'] if current_profile and current_profile['pr_marathon'] else "",
            placeholder=t("pr_marathon_placeholder")
        )

    st.divider()

    # Botons
    col1, col2 = st.columns([1, 5])

    with col1:
        submitted = st.form_submit_button(t("save_profile"), use_container_width=True, type="primary")

    with col2:
        if current_profile:
            st.caption(t("profile_updated_at", date=current_profile['updated_at'][:16]))

    if submitted:
        # Validar dades bàsiques
        if not name:
            st.error("El nom és obligatori")
        else:
            profile_data = {
                'name': name,
                'height_cm': height_cm,
                'weight_kg': weight_kg,
                'age': age,
                'vo2max_estimate': vo2max_estimate if vo2max_estimate > 30 else None,
                'threshold_pace': threshold_pace if threshold_pace else None,
                'easy_pace_min': easy_pace_min if easy_pace_min else None,
                'easy_pace_max': easy_pace_max if easy_pace_max else None,
                'training_philosophy': training_philosophy if training_philosophy else None,
                'current_goal': current_goal if current_goal else None,
                'goal_race_date': goal_race_date.isoformat() if goal_race_date else None,
                'goal_race_distance': goal_race_distance if goal_race_distance else None,
                'pr_5k': pr_5k if pr_5k else None,
                'pr_10k': pr_10k if pr_10k else None,
                'pr_half': pr_half if pr_half else None,
                'pr_marathon': pr_marathon if pr_marathon else None
            }

            save_profile(profile_data)
            st.success(t("profile_saved"))
            st.rerun()


# Sidebar amb resum
with st.sidebar:
    st.markdown(f"### {t('current_profile')}")

    if current_profile and current_profile['name']:
        st.success("Perfil configurat")

        if current_profile['current_goal']:
            st.markdown(f"**Objectiu:**")
            st.caption(current_profile['current_goal'])

        if current_profile['goal_race_date']:
            from datetime import datetime
            race_date = datetime.fromisoformat(current_profile['goal_race_date'])
            days_to_race = (race_date.date() - datetime.now().date()).days
            if days_to_race > 0:
                st.metric("Dies per l'objectiu", days_to_race)

        # PRs
        prs = []
        if current_profile['pr_5k']:
            prs.append(f"5K: {current_profile['pr_5k']}")
        if current_profile['pr_10k']:
            prs.append(f"10K: {current_profile['pr_10k']}")
        if current_profile['pr_half']:
            prs.append(f"Mitja: {current_profile['pr_half']}")
        if current_profile['pr_marathon']:
            prs.append(f"Marató: {current_profile['pr_marathon']}")

        if prs:
            st.markdown("**Rècords personals:**")
            for pr in prs:
                st.caption(f"🏆 {pr}")

    else:
        st.warning(t("no_profile"))
        st.caption("Completa el formulari perquè el Coach IA pugui donar-te recomanacions personalitzades")

    st.divider()

    st.markdown("### 💡 Per a què serveix?")
    st.caption("""
    El Coach IA utilitzarà aquesta informació per:
    - Personalitzar plans d'entrenament
    - Calcular zones de ritme adequades
    - Predir temps de cursa
    - Adaptar recomanacions a la teva filosofia
    - Fer seguiment del teu progrés cap a l'objectiu
    """)
