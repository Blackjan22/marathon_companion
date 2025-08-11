# pages/5_🏃‍♂️_Análisis_de_Splits.py
import streamlit as st
import plotly.graph_objects as go

# Importar utilidades
from utils.data_processing import load_data
from utils.formatting import format_time, format_pace

# Cargar datos
activities, splits = load_data()

st.title("🏃‍♂️ Análisis de Splits")

if splits.empty:
    st.warning("No hay datos de splits disponibles en tu base de datos.")
    st.stop()
if activities.empty:
    st.warning("No hay actividades disponibles.")
    st.stop()

# --- SELECTOR DE ACTIVIDAD ---
st.subheader("Selecciona una Actividad")
activity_options = activities[['id', 'name', 'start_date_local', 'distance_km']].copy()
activity_options['display'] = activity_options.apply(
    lambda x: f"{x['start_date_local'].strftime('%Y-%m-%d')} - {x['name']} ({x['distance_km']:.1f} km)",
    axis=1
)
selected_activity_id = st.selectbox(
    "Elige una carrera para analizar sus splits:",
    options=activity_options['id'],
    format_func=lambda x: activity_options[activity_options['id'] == x]['display'].iloc[0]
)

if not selected_activity_id:
    st.info("Por favor, selecciona una actividad.")
    st.stop()

# --- ANÁLISIS DE LA ACTIVIDAD SELECCIONADA ---
activity_splits = splits[splits['activity_id'] == selected_activity_id].copy()
activity_info = activities[activities['id'] == selected_activity_id].iloc[0]

st.header(f"Análisis de: {activity_info['name']}")
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Distancia Total", f"{activity_info['distance_km']:.2f} km")
with col2:
    st.metric("Tiempo Total", format_time(activity_info['moving_time']))
with col3:
    st.metric("Ritmo Promedio", format_pace(activity_info['pace_min_km']))

if not activity_splits.empty:
    st.subheader("Gráfico de Ritmo por Split")
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=activity_splits['split'],
        y=activity_splits['pace_min_km'],
        mode='lines+markers',
        name='Ritmo por Split'
    ))
    avg_pace_val = activity_splits['pace_min_km'].mean()
    fig.add_hline(y=avg_pace_val, line_dash="dash", line_color="red", annotation_text=f"Ritmo promedio: {format_pace(avg_pace_val)}")
    fig.update_layout(title=f"Ritmo por Split - {activity_info['name']}", xaxis_title="Split (km)", yaxis_title="Ritmo (min/km)")
    fig.update_yaxes(autorange="reversed")
    st.plotly_chart(fig, use_container_width=True)
    
    st.subheader("Detalle de Splits")
    splits_display = activity_splits.copy()
    splits_display['Ritmo'] = splits_display['pace_min_km'].apply(format_pace)
    splits_display['Tiempo'] = splits_display['elapsed_time'].apply(format_time)
    splits_display['Distancia (m)'] = splits_display['distance'].round(0)
    st.dataframe(
        splits_display[['split', 'Distancia (m)', 'Tiempo', 'Ritmo']].rename(columns={'split': 'Split (km)'}),
        use_container_width=True,
        hide_index=True
    )
else:
    st.info("Esta actividad no tiene datos de splits disponibles.")