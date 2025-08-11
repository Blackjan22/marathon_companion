# pages/3_🎯_Análisis_de_Ritmos.py
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# Importar utilidades
from utils.data_processing import load_data, get_timezone_aware_datetime
from utils.formatting import format_pace

# Cargar datos
activities, _ = load_data()

st.title("🎯 Análisis de Ritmos")

if activities.empty:
    st.warning("No hay datos de carreras disponibles.")
    st.stop()

# --- FILTROS EN SIDEBAR ---
st.sidebar.header("Filtros de Ritmos")
min_date = activities['start_date_local'].min().date()
max_date = activities['start_date_local'].max().date()
date_range = st.sidebar.date_input(
    "Rango de fechas:",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
    key="pace_date_range"
)
min_distance = st.sidebar.slider(
    "Distancia mínima (km):", 0.0, float(activities['distance_km'].max()), 0.0, 0.5, key="pace_dist_slider"
)

# Aplicar filtros
if len(date_range) == 2:
    start_date = get_timezone_aware_datetime(datetime.combine(date_range[0], datetime.min.time()))
    end_date = get_timezone_aware_datetime(datetime.combine(date_range[1], datetime.max.time()))
    mask = (
        (activities['start_date_local'] >= start_date) &
        (activities['start_date_local'] <= end_date) &
        (activities['distance_km'] >= min_distance)
    )
    filtered_activities = activities[mask].copy()
else:
    filtered_activities = activities[activities['distance_km'] >= min_distance].copy()

if filtered_activities.empty:
    st.warning("No hay datos para mostrar con los filtros aplicados.")
    st.stop()

# --- ANÁLISIS DE RITMOS ---
activities_clean = filtered_activities.dropna(subset=['pace_min_km'])
activities_clean = activities_clean[activities_clean['pace_min_km'] < 10]

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Ritmo Más Rápido", format_pace(activities_clean['pace_min_km'].min()))
with col2:
    st.metric("Ritmo Más Lento", format_pace(activities_clean['pace_min_km'].max()))
with col3:
    st.metric("Ritmo Promedio", format_pace(activities_clean['pace_min_km'].mean()))
with col4:
    st.metric("Desviación Estándar", f"{activities_clean['pace_min_km'].std():.2f} min/km")

st.subheader("Distribución de Ritmos")
fig = px.histogram(activities_clean, x='pace_min_km', nbins=30, title="Frecuencia de Ritmos en tus Carreras", labels={'pace_min_km': 'Ritmo (min/km)', 'count': 'Número de Carreras'})
st.plotly_chart(fig, use_container_width=True)

st.subheader("Análisis por Zonas de Entrenamiento (Estimadas por Ritmo)")
def get_training_zone(pace):
    if pace < 4.0: return "Zona 5: Intervalos Rápidos"
    elif pace < 4.5: return "Zona 4: Umbral"
    elif pace < 5.0: return "Zona 3: Tempo"
    elif pace < 5.75: return "Zona 2: Aeróbico"
    else: return "Zona 1: Recuperación"
activities_clean['training_zone'] = activities_clean['pace_min_km'].apply(get_training_zone)
zone_analysis = activities_clean['training_zone'].value_counts()
fig = px.pie(values=zone_analysis.values, names=zone_analysis.index, title="Distribución por Zonas de Entrenamiento")
st.plotly_chart(fig, use_container_width=True)

st.subheader("Evolución Mensual del Ritmo")
monthly_pace = activities_clean.groupby('month_year')['pace_min_km'].agg(['mean', 'min', 'max']).reset_index()
fig = go.Figure()
fig.add_trace(go.Scatter(x=monthly_pace['month_year'], y=monthly_pace['mean'], mode='lines+markers', name='Ritmo Promedio'))
fig.add_trace(go.Scatter(x=monthly_pace['month_year'], y=monthly_pace['min'], mode='markers', name='Mejor Ritmo', marker=dict(color='green', symbol='diamond')))
fig.add_trace(go.Scatter(x=monthly_pace['month_year'], y=monthly_pace['max'], mode='markers', name='Peor Ritmo', marker=dict(color='red', symbol='x')))
fig.update_layout(title="Evolución Mensual del Ritmo", xaxis_title="Mes", yaxis_title="Ritmo (min/km)")
fig.update_yaxes(autorange="reversed")
st.plotly_chart(fig, use_container_width=True)