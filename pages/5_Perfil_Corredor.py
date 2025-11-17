# pages/5_Perfil_Corredor.py
import streamlit as st
import sys
import os
from datetime import datetime

# Añadir el directorio src al path para importar módulos
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.db_config import get_connection

st.set_page_config(layout="wide")
st.title("👤 Perfil del Corredor")

st.markdown("""
Configura tu perfil para que el Coach IA pueda personalizar sus recomendaciones.
Todos estos datos son opcionales, pero cuanto más completo esté tu perfil, mejores serán las recomendaciones.
""")


def get_current_profile():
    """Obtiene el perfil actual de la base de datos."""
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
    """Guarda o actualiza el perfil en la base de datos."""
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

# Formulario
with st.form("profile_form"):
    st.subheader("📝 Información Básica")

    col1, col2, col3 = st.columns(3)

    with col1:
        name = st.text_input(
            "Nombre",
            value=current_profile['name'] if current_profile else "",
            placeholder="Tu nombre"
        )

    with col2:
        height_cm = st.number_input(
            "Altura (cm)",
            min_value=140.0,
            max_value=220.0,
            value=float(current_profile['height_cm']) if current_profile and current_profile['height_cm'] else 175.0,
            step=1.0
        )

    with col3:
        weight_kg = st.number_input(
            "Peso (kg)",
            min_value=40.0,
            max_value=150.0,
            value=float(current_profile['weight_kg']) if current_profile and current_profile['weight_kg'] else 70.0,
            step=0.5
        )

    age = st.number_input(
        "Edad",
        min_value=15,
        max_value=100,
        value=int(current_profile['age']) if current_profile and current_profile['age'] else 30,
        step=1
    )

    st.divider()
    st.subheader("🏃 Zonas de Entrenamiento")

    col1, col2, col3 = st.columns(3)

    with col1:
        threshold_pace = st.text_input(
            "Ritmo umbral (min/km)",
            value=current_profile['threshold_pace'] if current_profile and current_profile['threshold_pace'] else "",
            placeholder="ej: 4:30",
            help="Ritmo que puedes mantener ~1 hora a esfuerzo alto"
        )

    with col2:
        easy_pace_min = st.text_input(
            "Ritmo fácil MIN (min/km)",
            value=current_profile['easy_pace_min'] if current_profile and current_profile['easy_pace_min'] else "",
            placeholder="ej: 5:30"
        )

    with col3:
        easy_pace_max = st.text_input(
            "Ritmo fácil MAX (min/km)",
            value=current_profile['easy_pace_max'] if current_profile and current_profile['easy_pace_max'] else "",
            placeholder="ej: 6:00"
        )

    vo2max_estimate = st.number_input(
        "VO2max estimado (ml/kg/min) - Opcional",
        min_value=30.0,
        max_value=90.0,
        value=float(current_profile['vo2max_estimate']) if current_profile and current_profile['vo2max_estimate'] else 50.0,
        step=1.0,
        help="Puedes obtenerlo de relojes Garmin/Polar o calculadoras online"
    )

    st.divider()
    st.subheader("🎯 Objetivo Actual")

    col1, col2 = st.columns(2)

    with col1:
        current_goal = st.text_area(
            "Objetivo principal",
            value=current_profile['current_goal'] if current_profile and current_profile['current_goal'] else "",
            placeholder="ej: Correr Media Maratón Barcelona < 1:35",
            height=100
        )

        goal_race_distance = st.selectbox(
            "Distancia del objetivo",
            options=["", "5K", "10K", "15K", "Media Maratón", "Maratón", "Otra"],
            index=0 if not current_profile or not current_profile['goal_race_distance'] else
                  ["", "5K", "10K", "15K", "Media Maratón", "Maratón", "Otra"].index(current_profile['goal_race_distance']) if current_profile['goal_race_distance'] in ["", "5K", "10K", "15K", "Media Maratón", "Maratón", "Otra"] else 0
        )

    with col2:
        goal_race_date = st.date_input(
            "Fecha de la carrera objetivo",
            value=datetime.fromisoformat(current_profile['goal_race_date']).date() if current_profile and current_profile['goal_race_date'] else None,
            help="Deja en blanco si no tienes fecha definida"
        )

        training_philosophy = st.text_area(
            "Filosofía de entrenamiento",
            value=current_profile['training_philosophy'] if current_profile and current_profile['training_philosophy'] else "",
            placeholder="ej: 3 días de running a la semana, prioridad en salud y consistencia",
            height=100,
            help="Describe tu enfoque: días disponibles, prioridades, restricciones..."
        )

    st.divider()
    st.subheader("🏆 Records Personales (PRs)")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        pr_5k = st.text_input(
            "PR 5K",
            value=current_profile['pr_5k'] if current_profile and current_profile['pr_5k'] else "",
            placeholder="MM:SS (ej: 19:30)"
        )

    with col2:
        pr_10k = st.text_input(
            "PR 10K",
            value=current_profile['pr_10k'] if current_profile and current_profile['pr_10k'] else "",
            placeholder="MM:SS (ej: 43:20)"
        )

    with col3:
        pr_half = st.text_input(
            "PR Media Maratón",
            value=current_profile['pr_half'] if current_profile and current_profile['pr_half'] else "",
            placeholder="H:MM:SS (ej: 1:35:00)"
        )

    with col4:
        pr_marathon = st.text_input(
            "PR Maratón",
            value=current_profile['pr_marathon'] if current_profile and current_profile['pr_marathon'] else "",
            placeholder="H:MM:SS (ej: 3:30:00)"
        )

    st.divider()

    # Botones
    col1, col2 = st.columns([1, 5])

    with col1:
        submitted = st.form_submit_button("💾 Guardar Perfil", use_container_width=True, type="primary")

    with col2:
        if current_profile:
            st.caption(f"Última actualización: {current_profile['updated_at'][:16]}")

    if submitted:
        # Validar datos básicos
        if not name:
            st.error("El nombre es obligatorio")
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
            st.success("✅ Perfil guardado correctamente")
            st.rerun()


# Sidebar con resumen
with st.sidebar:
    st.markdown("### 📊 Resumen del Perfil")

    if current_profile and current_profile['name']:
        st.success("Perfil configurado")

        if current_profile['current_goal']:
            st.markdown(f"**Objetivo:**")
            st.caption(current_profile['current_goal'])

        if current_profile['goal_race_date']:
            from datetime import datetime
            race_date = datetime.fromisoformat(current_profile['goal_race_date'])
            days_to_race = (race_date.date() - datetime.now().date()).days
            if days_to_race > 0:
                st.metric("Días para el objetivo", days_to_race)

        # PRs
        prs = []
        if current_profile['pr_5k']:
            prs.append(f"5K: {current_profile['pr_5k']}")
        if current_profile['pr_10k']:
            prs.append(f"10K: {current_profile['pr_10k']}")
        if current_profile['pr_half']:
            prs.append(f"Media: {current_profile['pr_half']}")
        if current_profile['pr_marathon']:
            prs.append(f"Maratón: {current_profile['pr_marathon']}")

        if prs:
            st.markdown("**Records personales:**")
            for pr in prs:
                st.caption(f"🏆 {pr}")

    else:
        st.warning("Perfil no configurado")
        st.caption("Completa el formulario para que el Coach IA pueda darte recomendaciones personalizadas")

    st.divider()

    st.markdown("### 💡 ¿Para qué sirve?")
    st.caption("""
    El Coach IA usará esta información para:
    - Personalizar planes de entrenamiento
    - Calcular zonas de ritmo adecuadas
    - Predecir tiempos de carrera
    - Adaptar recomendaciones a tu filosofía
    - Hacer seguimiento de tu progreso hacia el objetivo
    """)
