# pages/4_📅_Tendencias_Temporales.py
import streamlit as st
import plotly.express as px
from datetime import datetime

# Importar utilidades
from utils.data_processing import load_data, get_timezone_aware_datetime

# Cargar datos
activities, _ = load_data()

st.title("📅 Tendencias Temporales")

if activities.empty:
    st.warning("No hay datos de carreras disponibles.")
    st.stop()

# --- FILTROS EN SIDEBAR ---
st.sidebar.header("Filtros de Tendencias")
min_date = activities['start_date_local'].min().date()
max_date = activities['start_date_local'].max().date()
date_range = st.sidebar.date_input(
    "Rango de fechas:",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
    key="trends_date_range"
)

# Aplicar filtros de fecha
if len(date_range) == 2:
    start_date = get_timezone_aware_datetime(datetime.combine(date_range[0], datetime.min.time()))
    end_date = get_timezone_aware_datetime(datetime.combine(date_range[1], datetime.max.time()))
    mask = (activities['start_date_local'] >= start_date) & (activities['start_date_local'] <= end_date)
    filtered_activities = activities[mask].copy()
else:
    filtered_activities = activities.copy()

if filtered_activities.empty:
    st.warning("No hay datos para mostrar con los filtros aplicados.")
    st.stop()

# --- ANÁLISIS TEMPORAL ---
st.subheader("Patrón de Entrenamiento por Hora del Día")
col1, col2 = st.columns(2)
with col1:
    hour_analysis = filtered_activities.groupby('hour').size().reset_index(name='count')
    fig = px.bar(hour_analysis, x='hour', y='count', title="Carreras por Hora del Día", labels={'hour': 'Hora (0-23)', 'count': 'Número de Carreras'})
    st.plotly_chart(fig, use_container_width=True)
with col2:
    hour_distance = filtered_activities.groupby('hour')['distance_km'].mean().reset_index()
    fig = px.line(hour_distance, x='hour', y='distance_km', title="Distancia Promedio por Hora", labels={'hour': 'Hora (0-23)', 'distance_km': 'Distancia Promedio (km)'}, markers=True)
    st.plotly_chart(fig, use_container_width=True)

st.subheader("Tendencias Semanales")
weekly_data = filtered_activities.groupby('week_year').agg(distance_km=('distance_km', 'sum'), id=('id', 'count')).reset_index()
col1, col2 = st.columns(2)
with col1:
    fig = px.line(weekly_data, x='week_year', y='distance_km', title="Kilómetros Totales por Semana", labels={'week_year': 'Semana del Año', 'distance_km': 'Kilómetros'})
    st.plotly_chart(fig, use_container_width=True)
with col2:
    fig = px.bar(weekly_data, x='week_year', y='id', title="Número de Carreras por Semana", labels={'week_year': 'Semana del Año', 'id': 'Número de Carreras'})
    st.plotly_chart(fig, use_container_width=True)