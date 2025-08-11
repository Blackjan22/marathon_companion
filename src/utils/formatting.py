# utils/formatting.py
import pandas as pd

def format_time(seconds):
    """Convierte segundos a formato HH:MM:SS"""
    if pd.isna(seconds):
        return "N/A"
    hours, remainder = divmod(int(seconds), 3600)
    minutes, seconds = divmod(remainder, 60)
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    else:
        return f"{minutes:02d}:{seconds:02d}"

def format_pace(pace_min_km):
    """Convierte pace a formato MM:SS"""
    if pd.isna(pace_min_km) or pace_min_km <= 0:
        return "N/A"
    minutes = int(pace_min_km)
    seconds = int((pace_min_km - minutes) * 60)
    return f"{minutes:02d}:{seconds:02d}"