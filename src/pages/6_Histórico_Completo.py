# pages/6_📋_Histórico_Completo.py
import streamlit as st
import pandas as pd

# Importar utilidades
from utils.data_processing import load_data
from utils.formatting import format_time, format_pace

# Cargar datos
activities, _ = load_data()

st.title("📋 Histórico Completo de Actividades")

if activities.empty:
    st.warning("No hay datos de carreras disponibles.")
    st.stop()

# --- PREPARAR DATOS PARA MOSTRAR ---
display_data = activities.copy()
display_data['Fecha'] = display_data['start_date_local'].dt.strftime('%Y-%m-%d %H:%M')
display_data['Distancia (km)'] = display_data['distance_km'].round(2)
display_data['Tiempo'] = display_data['moving_time'].apply(format_time)
display_data['Ritmo (min/km)'] = display_data['pace_min_km'].apply(format_pace)
display_data['FC Promedio'] = display_data['average_heartrate'].fillna(0).round(0).astype(int).astype(str).replace('0', 'N/A')
display_data['Desnivel (m)'] = display_data['total_elevation_gain'].fillna(0).round(0).astype(int)

# --- FILTROS EN EL CUERPO DE LA PÁGINA ---
st.header("Filtrar Histórico")
col1, col2, col3 = st.columns(3)
with col1:
    sport_types = ['Todos'] + list(display_data['sport_type'].unique())
    selected_sport = st.selectbox("Tipo de deporte:", sport_types)
with col2:
    min_dist_filter = st.number_input("Distancia mínima (km):", min_value=0.0, value=0.0, step=0.5)
with col3:
    max_dist_filter = st.number_input("Distancia máxima (km):", min_value=0.0, value=float(display_data['distance_km'].max()), step=1.0)

# Aplicar filtros
display_filtered = display_data.copy()
if selected_sport != 'Todos':
    display_filtered = display_filtered[display_filtered['sport_type'] == selected_sport]
mask_distance = (display_filtered['distance_km'] >= min_dist_filter) & (display_filtered['distance_km'] <= max_dist_filter)
display_filtered = display_filtered[mask_distance]

st.header("Resultados")
if display_filtered.empty:
    st.warning("No hay actividades que coincidan con los filtros.")
    st.stop()

# Mostrar estadísticas resumidas de los datos filtrados
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Actividades Filtradas", len(display_filtered))
with col2:
    st.metric("Total Kilómetros", f"{display_filtered['distance_km'].sum():.1f}")
with col3:
    st.metric("Tiempo Total", format_time(display_filtered['moving_time'].sum()))
with col4:
    st.metric("Ritmo Promedio", format_pace(display_filtered['pace_min_km'].mean()))

# --- TABLA INTERACTIVA ---
columns_to_show = ['Fecha', 'name', 'Distancia (km)', 'Tiempo', 'Ritmo (min/km)', 'FC Promedio', 'Desnivel (m)', 'sport_type']
column_names = {'name': 'Actividad', 'sport_type': 'Tipo'}
st.dataframe(
    display_filtered[columns_to_show].rename(columns=column_names),
    use_container_width=True,
    hide_index=True,
    height=500
)