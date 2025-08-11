# pages/2_📈_Análisis_de_Rendimiento.py
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# Importar utilidades
from utils.data_processing import load_data, get_timezone_aware_datetime
from utils.formatting import format_pace

# Cargar datos
activities, _ = load_data()

st.title("📈 Análisis de Rendimiento")

if activities.empty:
    st.warning("No hay datos de carreras disponibles.")
    st.stop()

# --- FILTROS EN SIDEBAR ---
st.sidebar.header("Filtros de Rendimiento")
min_date = activities['start_date_local'].min().date()
max_date = activities['start_date_local'].max().date()
date_range = st.sidebar.date_input(
    "Rango de fechas:",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
    key="perf_date_range"
)
min_distance = st.sidebar.slider(
    "Distancia mínima (km):", 0.0, float(activities['distance_km'].max()), 0.0, 0.5, key="perf_dist_slider"
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

# --- ANÁLISIS DE RENDIMIENTO ---
st.subheader("Evolución del Ritmo en el Tiempo")
activities_clean = filtered_activities.dropna(subset=['pace_min_km'])
activities_clean = activities_clean[activities_clean['pace_min_km'] < 10]  # Filtrar outliers

if not activities_clean.empty:
    fig = px.scatter(activities_clean,
                     x='start_date_local',
                     y='pace_min_km',
                     size='distance_km',
                     color='distance_km',
                     title="Ritmo de cada carrera (tamaño por distancia)",
                     labels={'pace_min_km': 'Ritmo (min/km)', 'start_date_local': 'Fecha'},
                     hover_name='name',
                     hover_data={'distance_km': ':.1f'})
    # Invertir el eje Y para que los ritmos más rápidos (menores) estén arriba
    fig.update_yaxes(autorange="reversed")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No hay datos de ritmo para mostrar.")


st.subheader("Rendimiento por Rangos de Distancia")
# Crear rangos de distancia
filtered_activities['distance_range'] = pd.cut(filtered_activities['distance_km'],
                                             bins=[0, 5, 10, 15, 21, 42, 100],
                                             labels=['< 5km', '5-10km', '10-15km', '15-21km', '21-42km', '> 42km'])
col1, col2 = st.columns(2)
with col1:
    range_analysis = filtered_activities.groupby('distance_range').agg(avg_pace=('pace_min_km', 'mean'), count=('id', 'count')).reset_index()
    range_analysis = range_analysis[range_analysis['count'] > 0]
    fig = px.bar(range_analysis, x='distance_range', y='avg_pace', title="Ritmo Promedio por Rango", labels={'avg_pace': 'Ritmo Promedio (min/km)', 'distance_range': 'Rango de Distancia'})
    fig.update_yaxes(autorange="reversed")
    st.plotly_chart(fig, use_container_width=True)
with col2:
    activities_clean = filtered_activities.dropna(subset=['pace_min_km', 'distance_range'])
    activities_clean = activities_clean[activities_clean['pace_min_km'] < 10]
    fig = px.box(activities_clean, x='distance_range', y='pace_min_km', title="Distribución de Ritmos por Rango", labels={'pace_min_km': 'Ritmo (min/km)', 'distance_range': 'Rango de Distancia'})
    fig.update_yaxes(autorange="reversed")
    st.plotly_chart(fig, use_container_width=True)


if 'average_heartrate' in filtered_activities.columns and filtered_activities['average_heartrate'].notna().sum() > 0:
    st.subheader("Análisis de Frecuencia Cardíaca")
    hr_data = filtered_activities.dropna(subset=['average_heartrate', 'pace_min_km'])
    col1, col2 = st.columns(2)
    with col1:
        fig = px.scatter(hr_data, x='average_heartrate', y='pace_min_km', size='distance_km', color='distance_km', title="Relación FC vs Ritmo", labels={'average_heartrate': 'FC Promedio (bpm)', 'pace_min_km': 'Ritmo (min/km)'})
        fig.update_yaxes(autorange="reversed")
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        fig = px.histogram(hr_data, x='average_heartrate', nbins=20, title="Distribución de FC Promedio", labels={'average_heartrate': 'FC Promedio (bpm)', 'count': 'Frecuencia'})
        st.plotly_chart(fig, use_container_width=True)