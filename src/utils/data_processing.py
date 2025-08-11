# utils/data_processing.py
import streamlit as st
import pandas as pd
import pytz
import sqlite3
from datetime import datetime

# La decoración de caché se queda con la función
@st.cache_data
def load_data():
    """Carga y procesa los datos desde la base de datos SQLite"""
    try:
        conn = sqlite3.connect('data/strava_activities.db')
        
        # Cargar actividades
        activities_query = "SELECT * FROM activities WHERE type = 'Run' ORDER BY start_date_local DESC"
        activities = pd.read_sql_query(activities_query, conn)
        
        # Cargar splits
        splits_query = "SELECT * FROM splits"
        splits = pd.read_sql_query(splits_query, conn)
        
        conn.close()
        
        # Procesamiento de datos
        activities['start_date_local'] = pd.to_datetime(activities['start_date_local'], utc=True)
        activities['distance_km'] = activities['distance'] / 1000
        activities['pace_min_km'] = (activities['moving_time'] / 60) / activities['distance_km']
        activities['moving_time_min'] = activities['moving_time'] / 60
        activities['month_year'] = activities['start_date_local'].dt.to_period('M').astype(str)
        activities['week_year'] = activities['start_date_local'].dt.to_period('W').astype(str)
        activities['day_of_week'] = activities['start_date_local'].dt.day_name()
        activities['hour'] = activities['start_date_local'].dt.hour
        
        if not splits.empty:
            splits['pace_min_km'] = (splits['elapsed_time'] / 60) / (splits['distance'] / 1000)
        
        return activities, splits
    
    except Exception as e:
        st.error(f"Error cargando datos: {e}")
        return pd.DataFrame(), pd.DataFrame()

# Puedes mover get_timezone_aware_datetime aquí también si quieres
def get_timezone_aware_datetime(dt):
    """Convierte datetime a timezone-aware UTC"""
    if dt.tzinfo is None:
        return pytz.UTC.localize(dt)
    return dt.astimezone(pytz.UTC)