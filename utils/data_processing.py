# utils/data_processing.py
import streamlit as st
import pandas as pd
import pytz
from datetime import datetime
from .db_config import get_connection

# La decoración de caché se queda con la función
@st.cache_data
def load_data():
    """Carga y procesa los datos desde la base de datos (SQLite o PostgreSQL)"""
    try:
        conn = get_connection()

        # Cargar actividades
        activities_query = "SELECT * FROM activities WHERE type = 'Run' ORDER BY start_date_local DESC"
        activities = pd.read_sql_query(activities_query, conn)

        # Cargar SPLITS (km automáticos con elevation_difference con signo)
        splits_query = "SELECT * FROM splits"
        splits = pd.read_sql_query(splits_query, conn)

        # Cargar LAPS (parciales/intervalos con total_elevation_gain)
        laps_query = "SELECT * FROM laps"
        laps = pd.read_sql_query(laps_query, conn)

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

        # Procesar SPLITS (km automáticos)
        if not splits.empty:
            splits['distance_km'] = splits['distance'] / 1000
            splits['elapsed_time_min'] = splits['elapsed_time'] / 60

            # Calcular ritmo (min/km) solo para splits con distancia > 0
            splits['pace_min_km'] = None
            mask = (splits['distance'] > 0) & (splits['elapsed_time'] > 0)
            splits.loc[mask, 'pace_min_km'] = (splits.loc[mask, 'elapsed_time'] / 60) / (splits.loc[mask, 'distance'] / 1000)

            # También podemos usar average_speed si está disponible
            speed_mask = splits['average_speed'] > 0
            splits.loc[speed_mask, 'pace_from_speed'] = (1000 / splits.loc[speed_mask, 'average_speed']) / 60

        # Procesar LAPS (parciales/intervalos)
        if not laps.empty:
            laps['distance_km'] = laps['distance'] / 1000
            laps['moving_time_min'] = laps['moving_time'] / 60

            # Calcular ritmo (min/km) solo para laps con distancia > 0
            laps['pace_min_km'] = None
            mask = (laps['distance'] > 0) & (laps['moving_time'] > 0)
            laps.loc[mask, 'pace_min_km'] = (laps.loc[mask, 'moving_time'] / 60) / (laps.loc[mask, 'distance'] / 1000)

            # También podemos usar average_speed si está disponible
            speed_mask = laps['average_speed'] > 0
            laps.loc[speed_mask, 'pace_from_speed'] = (1000 / laps.loc[speed_mask, 'average_speed']) / 60

        return activities, splits, laps  # Retornar TOTS TRES

    except Exception as e:
        st.error(f"Error cargando datos: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

# Puedes mover get_timezone_aware_datetime aquí también si quieres
def get_timezone_aware_datetime(dt):
    """Convierte datetime a timezone-aware UTC"""
    if dt.tzinfo is None:
        return pytz.UTC.localize(dt)
    return dt.astimezone(pytz.UTC)