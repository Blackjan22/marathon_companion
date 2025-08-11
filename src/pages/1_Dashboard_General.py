# pages/1_📊_Dashboard_General.py
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

# Importar utilidades
from utils.data_processing import load_data, get_timezone_aware_datetime
from utils.formatting import format_time, format_pace

# Cargar datos (usará la caché)
activities, splits = load_data()

st.title("📊 Dashboard General")

if activities.empty:
    st.warning("No hay datos de carreras disponibles. Sincroniza tus actividades primero.")
    st.stop()

# --- FILTROS EN SIDEBAR ---
st.sidebar.header("Filtros del Dashboard")
min_date = activities['start_date_local'].min().date()
max_date = activities['start_date_local'].max().date()
date_range = st.sidebar.date_input(
    "Rango de fechas:",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
    key="dash_date_range"
)
min_distance = st.sidebar.slider(
    "Distancia mínima (km):", 0.0, float(activities['distance_km'].max()), 0.0, 0.5, key="dash_dist_slider"
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

# --- MÉTRICAS PRINCIPALES ---
col1, col2, col3, col4 = st.columns(4)
thirty_days_ago = get_timezone_aware_datetime(datetime.now() - timedelta(days=30))
recent_activities = filtered_activities[filtered_activities['start_date_local'] >= thirty_days_ago]

with col1:
    st.metric(label="Total Carreras", value=len(filtered_activities), delta=f"{len(recent_activities)} últimos 30d")
with col2:
    total_km = filtered_activities['distance_km'].sum()
    recent_km = recent_activities['distance_km'].sum()
    st.metric(label="Total Kilómetros", value=f"{total_km:.1f} km", delta=f"{recent_km:.1f} km últimos 30d")
with col3:
    avg_pace = filtered_activities['pace_min_km'].mean()
    st.metric(label="Ritmo Promedio", value=format_pace(avg_pace))
with col4:
    total_time = filtered_activities['moving_time'].sum()
    st.metric(label="Tiempo Total Corriendo", value=format_time(total_time))

# --- GRÁFICOS PRINCIPALES ---
col1, col2 = st.columns(2)
with col1:
    st.subheader("Evolución de la Distancia Mensual")
    monthly_data = filtered_activities.groupby('month_year').agg(distance_km=('distance_km', 'sum')).reset_index()
    fig = px.bar(monthly_data, x='month_year', y='distance_km', labels={'distance_km': 'Kilómetros', 'month_year': 'Mes'})
    st.plotly_chart(fig, use_container_width=True)
with col2:
    st.subheader("Distribución de Distancias")
    fig = px.histogram(filtered_activities, x='distance_km', nbins=20, labels={'distance_km': 'Distancia (km)', 'count': 'Frecuencia'})
    st.plotly_chart(fig, use_container_width=True)

# --- ANÁLISIS POR DÍA DE LA SEMANA ---
st.subheader("Análisis por Día de la Semana")
col1, col2 = st.columns(2)
day_analysis = filtered_activities.groupby('day_of_week').agg(id=('id', 'count'), distance_km=('distance_km', 'mean')).reset_index()
day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
day_analysis['day_of_week'] = pd.Categorical(day_analysis['day_of_week'], categories=day_order, ordered=True)
day_analysis = day_analysis.sort_values('day_of_week')
with col1:
    fig = px.bar(day_analysis, x='day_of_week', y='id', title="Carreras por Día", labels={'id': '# Carreras', 'day_of_week': 'Día'})
    st.plotly_chart(fig, use_container_width=True)
with col2:
    fig = px.bar(day_analysis, x='day_of_week', y='distance_km', title="Distancia Promedio por Día", labels={'distance_km': 'Distancia Media (km)', 'day_of_week': 'Día'})
    st.plotly_chart(fig, use_container_width=True)