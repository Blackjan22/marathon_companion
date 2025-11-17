# utils/formatting.py
import pandas as pd
from i18n import t


def format_time(seconds):
    """Converteix segons a format HH:MM:SS"""
    if pd.isna(seconds):
        return t("not_available")
    hours, remainder = divmod(int(seconds), 3600)
    minutes, seconds = divmod(remainder, 60)
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    else:
        return f"{minutes:02d}:{seconds:02d}"


def format_pace(pace_min_km):
    """Converteix pace a format MM:SS"""
    if pd.isna(pace_min_km) or pace_min_km <= 0:
        return t("not_available")
    minutes = int(pace_min_km)
    seconds = int((pace_min_km - minutes) * 60)
    return f"{minutes:02d}:{seconds:02d}"