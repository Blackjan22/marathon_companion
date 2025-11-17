# pages/3_Planificacion.py
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import sys
import os

# Añadir el directorio src al path para importar módulos
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.planning import (
    get_current_plan, get_upcoming_workouts, get_unlinked_activities,
    link_activity_to_workout, update_workout_status,
    reset_workout_to_pending, delete_workout, update_workout
)
from utils.formatting import format_time, format_pace
from i18n import t, WORKOUT_TYPES_DISPLAY, DAY_NAMES_ES_TO_CA
from auth import check_password, add_logout_button

st.set_page_config(layout="wide")

# Verificar autenticació
if not check_password():
    st.stop()

# Afegir botó de logout a la sidebar
add_logout_button()

st.title(t("planning_title"))

# Tabs para organizar la información
tab1, tab2 = st.tabs([t("calendar_tab"), t("link_activities_tab")])

with tab1:
    st.header(t("planned_workouts"))

    # Controles de rango de fechas
    col_past, col_future = st.columns(2)
    with col_past:
        past_weeks = st.number_input(t("weeks_past"), min_value=0, max_value=12, value=1, key="past_weeks")
    with col_future:
        future_weeks = st.number_input(t("weeks_future"), min_value=1, max_value=12, value=4, key="future_weeks")

    # Obtener entrenamientos planificados en el rango
    upcoming = get_upcoming_workouts(weeks=future_weeks, include_past_weeks=past_weeks)

    if upcoming.empty:
        st.info(t("no_planned_workouts"))
    else:
        # Agrupar por semana
        upcoming['date'] = pd.to_datetime(upcoming['date'])
        upcoming['week'] = upcoming['date'].dt.to_period('W').astype(str)

        for week, week_workouts in upcoming.groupby('week'):
            st.subheader(t("week_label", week=week))

            # Mostrar entrenamientos de la semana en columnas
            cols = st.columns(len(week_workouts))

            for idx, (_, workout) in enumerate(week_workouts.iterrows()):
                with cols[idx]:
                    # Determinar color según estado
                    if workout['status'] == 'completed':
                        status_emoji = "✅"
                        status_color = "green"
                    elif workout['status'] == 'skipped':
                        status_emoji = "⏭️"
                        status_color = "orange"
                    else:
                        status_emoji = "⏳"
                        status_color = "blue"

                    # Card del entrenamiento - formato de fecha en Catalan
                    day_name_en = workout['date'].strftime('%A')
                    day_name_ca = DAY_NAMES_ES_TO_CA.get(day_name_en, day_name_en)
                    st.markdown(f"**{status_emoji} {day_name_ca}, {workout['date'].strftime('%d %b')}**")

                    # Mostrar tipo de entreno usando el diccionario de display
                    workout_type = workout['workout_type'] or 'easy_run'
                    workout_type_display = WORKOUT_TYPES_DISPLAY.get(workout_type, workout_type.replace('_', ' ').title())
                    st.markdown(f"**{t('type_label')}** {workout_type_display}")
                    st.markdown(f"**{t('distance_label')}** {workout['distance_km']:.1f} km")

                    if workout['pace_objective']:
                        st.markdown(f"**{t('pace_objective_label')}** {workout['pace_objective']}")

                    if workout['description']:
                        st.markdown(f"_{workout['description']}_")

                    # Si está completado, mostrar info de la actividad
                    if workout['status'] == 'completed' and workout['activity_name']:
                        st.success(t("completed_activity", name=workout['activity_name']))
                        if pd.notna(workout['activity_distance_km']):
                            st.caption(t("actual_distance", km=workout['activity_distance_km']))

                    # Botones de acción según estado
                    if workout['status'] == 'pending':
                        col_a, col_b = st.columns(2)
                        with col_a:
                            if st.button(t("mark_completed"), key=f"complete_{workout['id']}"):
                                update_workout_status(workout['id'], 'completed')
                                st.rerun()
                        with col_b:
                            if st.button(t("skip_workout"), key=f"skip_{workout['id']}"):
                                update_workout_status(workout['id'], 'skipped')
                                st.rerun()
                    elif workout['status'] in ['completed', 'skipped']:
                        # Opción para desmarcar y volver a pending
                        if st.button(t("unmark_pending"), key=f"reset_{workout['id']}", type="secondary"):
                            reset_workout_to_pending(workout['id'])
                            st.rerun()

                    # Botones de gestión (editar y eliminar) - siempre disponibles
                    st.markdown("---")
                    col_edit, col_delete = st.columns(2)

                    with col_edit:
                        edit_key = f"edit_{workout['id']}"
                        if st.button(t("edit_workout"), key=edit_key, use_container_width=True):
                            if f"editing_{workout['id']}" not in st.session_state:
                                st.session_state[f"editing_{workout['id']}"] = True
                            else:
                                st.session_state[f"editing_{workout['id']}"] = not st.session_state.get(f"editing_{workout['id']}", False)
                            st.rerun()

                    with col_delete:
                        delete_key = f"delete_{workout['id']}"
                        if st.button(t("delete_workout_button"), key=delete_key, use_container_width=True, type="secondary"):
                            if f"confirm_delete_{workout['id']}" not in st.session_state:
                                st.session_state[f"confirm_delete_{workout['id']}"] = True
                            else:
                                st.session_state[f"confirm_delete_{workout['id']}"] = not st.session_state.get(f"confirm_delete_{workout['id']}", False)
                            st.rerun()

                    # Confirmación de eliminación
                    if st.session_state.get(f"confirm_delete_{workout['id']}", False):
                        st.warning(t("confirm_delete_workout"))
                        col_yes, col_no = st.columns(2)
                        with col_yes:
                            if st.button(t("yes_delete"), key=f"confirm_yes_{workout['id']}", type="primary"):
                                delete_workout(workout['id'])
                                st.session_state[f"confirm_delete_{workout['id']}"] = False
                                st.success(t("workout_deleted"))
                                st.rerun()
                        with col_no:
                            if st.button(t("cancel"), key=f"confirm_no_{workout['id']}"):
                                st.session_state[f"confirm_delete_{workout['id']}"] = False
                                st.rerun()

                    # Formulario de edición
                    if st.session_state.get(f"editing_{workout['id']}", False):
                        with st.form(key=f"edit_form_{workout['id']}"):
                            st.markdown(t("edit_workout_title"))

                            new_date = st.date_input(
                                t("date_label"),
                                value=pd.to_datetime(workout['date']).date(),
                                key=f"new_date_{workout['id']}"
                            )

                            # Workout types en inglés (database values)
                            workout_types = ['easy_run', 'quality', 'long_run', 'recovery', 'tempo', 'intervals']
                            current_type_idx = workout_types.index(workout['workout_type']) if workout['workout_type'] in workout_types else 0

                            # Crear opciones de display en Catalan
                            workout_type_options = {wt: WORKOUT_TYPES_DISPLAY.get(wt, wt) for wt in workout_types}

                            new_type = st.selectbox(
                                t("type_label"),
                                options=workout_types,
                                format_func=lambda x: workout_type_options[x],
                                index=current_type_idx,
                                key=f"new_type_{workout['id']}"
                            )

                            new_distance = st.number_input(
                                t("distance_label") + " (km):",
                                min_value=0.5,
                                max_value=50.0,
                                value=float(workout['distance_km']),
                                step=0.5,
                                key=f"new_distance_{workout['id']}"
                            )

                            new_pace = st.text_input(
                                t("pace_objective_label"),
                                value=workout['pace_objective'] or "",
                                placeholder=t("example_pace"),
                                key=f"new_pace_{workout['id']}"
                            )

                            new_description = st.text_area(
                                t("description_label"),
                                value=workout['description'] or "",
                                key=f"new_description_{workout['id']}"
                            )

                            new_notes = st.text_area(
                                t("notes_label"),
                                value=workout['notes'] or "",
                                key=f"new_notes_{workout['id']}"
                            )

                            col_save, col_cancel = st.columns(2)
                            with col_save:
                                save_button = st.form_submit_button(t("save_changes"), use_container_width=True)
                            with col_cancel:
                                cancel_button = st.form_submit_button(t("cancel"), use_container_width=True)

                            if save_button:
                                update_workout(
                                    workout_id=workout['id'],
                                    date=new_date.isoformat(),
                                    workout_type=new_type,
                                    distance_km=new_distance,
                                    pace_objective=new_pace if new_pace else None,
                                    description=new_description if new_description else None,
                                    notes=new_notes if new_notes else None
                                )
                                st.session_state[f"editing_{workout['id']}"] = False
                                st.success(t("changes_saved"))
                                st.rerun()

                            if cancel_button:
                                st.session_state[f"editing_{workout['id']}"] = False
                                st.rerun()

                    st.divider()

with tab2:
    st.header(t("link_strava_activities"))
    st.markdown(t("link_strava_desc"))

    # Actividades recientes sin vincular
    unlinked = get_unlinked_activities(days=14)

    if unlinked.empty:
        st.success(t("all_activities_linked"))
    else:
        st.subheader(t("unlinked_activities"))

        for _, activity in unlinked.iterrows():
            with st.expander(f"🏃 {activity['name']} - {pd.to_datetime(activity['start_date_local']).strftime('%d/%m/%Y')}"):
                col1, col2 = st.columns([2, 1])

                with col1:
                    st.markdown(t("date_time_label") + f" {pd.to_datetime(activity['start_date_local']).strftime('%d/%m/%Y %H:%M')}")
                    st.markdown(f"**{t('distance_label')}** {activity['distance']/1000:.2f} km")
                    st.markdown(t("time_label") + f" {format_time(activity['moving_time'])}")

                    if pd.notna(activity['description']):
                        st.caption(f"{t('description_label')} {activity['description']}")

                with col2:
                    # Obtener entrenamientos pendientes cercanos
                    activity_date = pd.to_datetime(activity['start_date_local']).date()
                    date_range_start = (activity_date - timedelta(days=2)).isoformat()
                    date_range_end = (activity_date + timedelta(days=2)).isoformat()

                    # Buscar entrenamientos pendientes en rango de fecha - incluir semanas pasadas para vincular
                    pending_workouts = get_upcoming_workouts(weeks=4, include_past_weeks=4)
                    if not pending_workouts.empty:
                        pending_workouts['date'] = pd.to_datetime(pending_workouts['date'])
                        nearby_workouts = pending_workouts[
                            (pending_workouts['date'].dt.date >= pd.to_datetime(date_range_start).date()) &
                            (pending_workouts['date'].dt.date <= pd.to_datetime(date_range_end).date()) &
                            (pending_workouts['status'] == 'pending')
                        ]

                        if not nearby_workouts.empty:
                            workout_options = {}
                            for _, row in nearby_workouts.iterrows():
                                workout_type_display = WORKOUT_TYPES_DISPLAY.get(row['workout_type'], row['workout_type'])
                                workout_options[f"{row['date'].strftime('%d/%m')} - {workout_type_display} - {row['distance_km']:.1f} km"] = row['id']

                            selected_workout = st.selectbox(
                                t("link_with"),
                                options=list(workout_options.keys()),
                                key=f"link_{activity['id']}"
                            )

                            if st.button(t("link_button"), key=f"btn_link_{activity['id']}"):
                                workout_id = workout_options[selected_workout]
                                link_activity_to_workout(workout_id, activity['id'])
                                st.success(t("activity_linked"))
                                st.rerun()
                        else:
                            st.info(t("no_pending_workouts_near"))


# Información adicional en sidebar
with st.sidebar:
    st.markdown(t("summary_sidebar"))

    # Plan actual
    current_plan = get_current_plan()
    if current_plan:
        st.success(t("active_plan"))
        st.caption(t("week_start", date=current_plan['week_start_date']))
        if current_plan['goal']:
            st.caption(t("objective_label", goal=current_plan['goal']))
    else:
        st.warning(t("no_active_plan"))
        st.caption(t("create_plan_in_coach"))

    st.divider()

    # Estadísticas rápidas - usar mismo rango que la vista principal
    if 'past_weeks' in st.session_state and 'future_weeks' in st.session_state:
        stat_past = st.session_state.past_weeks
        stat_future = st.session_state.future_weeks
    else:
        stat_past = 1
        stat_future = 4

    upcoming_all = get_upcoming_workouts(weeks=stat_future, include_past_weeks=stat_past)
    if not upcoming_all.empty:
        total_workouts = len(upcoming_all)
        completed = len(upcoming_all[upcoming_all['status'] == 'completed'])
        pending = len(upcoming_all[upcoming_all['status'] == 'pending'])

        # Label dinámico basado en el rango seleccionado
        range_label = f"-{stat_past}sem, +{stat_future}sem" if stat_past > 0 else f"{stat_future} sem"
        st.metric(t("total_planned", label=range_label), total_workouts)
        st.metric(t("completed_workouts"), completed)
        st.metric(t("pending_workouts"), pending)
