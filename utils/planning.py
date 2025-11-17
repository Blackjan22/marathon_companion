# utils/planning.py
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from .db_config import get_connection


def get_current_plan(db_path='data/strava_activities.db') -> Optional[Dict]:
    """Obtiene el plan de entrenamiento activo actual."""
    conn = get_connection()
    query = """
        SELECT * FROM training_plans
        WHERE status = 'active'
        ORDER BY week_start_date DESC
        LIMIT 1
    """
    df = pd.read_sql_query(query, conn)
    conn.close()

    if df.empty:
        return None
    return df.iloc[0].to_dict()


def get_planned_workouts(plan_id: int, db_path='data/strava_activities.db') -> pd.DataFrame:
    """Obtiene todos los entrenamientos planificados de un plan."""
    conn = get_connection()
    query = """
        SELECT pw.*, a.name as activity_name, a.distance/1000 as activity_distance_km,
               a.moving_time, a.start_date_local
        FROM planned_workouts pw
        LEFT JOIN activities a ON pw.linked_activity_id = a.id
        WHERE pw.plan_id = ?
        ORDER BY pw.date
    """
    df = pd.read_sql_query(query, conn, params=(plan_id,))
    conn.close()
    return df


def get_upcoming_workouts(weeks=4, include_past_weeks=0, start_date=None, end_date=None,
                          db_path='data/strava_activities.db') -> pd.DataFrame:
    """
    Obtiene entrenamientos planificados SOLO del plan activo en un rango de fechas.

    Args:
        weeks: Número de semanas hacia el futuro (por defecto 4)
        include_past_weeks: Número de semanas hacia el pasado a incluir (por defecto 0)
        start_date: Fecha de inicio específica en formato YYYY-MM-DD (opcional, sobrescribe include_past_weeks)
        end_date: Fecha de fin específica en formato YYYY-MM-DD (opcional, sobrescribe weeks)
        db_path: Ruta a la base de datos

    Returns:
        DataFrame con los entrenamientos del plan activo en el rango de fechas
    """
    conn = get_connection()

    # Calcular fechas del rango
    if start_date is None:
        start_date = (datetime.now().date() - timedelta(weeks=include_past_weeks)).isoformat()

    if end_date is None:
        end_date = (datetime.now().date() + timedelta(weeks=weeks)).isoformat()

    query = """
        SELECT pw.*, a.name as activity_name, a.distance/1000 as activity_distance_km,
               a.moving_time, a.start_date_local
        FROM planned_workouts pw
        JOIN training_plans tp ON pw.plan_id = tp.id
        LEFT JOIN activities a ON pw.linked_activity_id = a.id
        WHERE tp.status = 'active'
        AND pw.date BETWEEN ? AND ?
        ORDER BY pw.date
    """
    df = pd.read_sql_query(query, conn, params=(start_date, end_date))
    conn.close()
    return df


def create_training_plan(week_start_date: str, goal: str = None,
                        notes: str = None, db_path='data/strava_activities.db') -> int:
    """Crea un nuevo plan de entrenamiento."""
    conn = get_connection()
    cur = conn.cursor()

    # Calcular número de semana
    week_start = datetime.fromisoformat(week_start_date)
    week_number = week_start.isocalendar()[1]

    cur.execute("""
        INSERT INTO training_plans (week_start_date, week_number, goal, notes, status)
        VALUES (?, ?, ?, ?, 'active')
    """, (week_start_date, week_number, goal, notes))

    plan_id = cur.lastrowid
    conn.commit()
    conn.close()
    return plan_id


def add_planned_workout(plan_id: int, date: str, workout_type: str,
                       distance_km: float, description: str = None,
                       pace_objective: str = None, notes: str = None,
                       db_path='data/strava_activities.db') -> int:
    """Añade un entrenamiento planificado a un plan."""
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO planned_workouts
        (plan_id, date, workout_type, distance_km, description, pace_objective, notes, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, 'pending')
    """, (plan_id, date, workout_type, distance_km, description, pace_objective, notes))

    workout_id = cur.lastrowid
    conn.commit()
    conn.close()
    return workout_id


def link_activity_to_workout(workout_id: int, activity_id: int,
                             db_path='data/strava_activities.db'):
    """Vincula una actividad de Strava con un entrenamiento planificado."""
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE planned_workouts
        SET linked_activity_id = ?, status = 'completed'
        WHERE id = ?
    """, (activity_id, workout_id))

    conn.commit()
    conn.close()




def get_unlinked_activities(days=7, db_path='data/strava_activities.db') -> pd.DataFrame:
    """Obtiene actividades recientes no vinculadas a ningún plan."""
    conn = get_connection()
    cutoff_date = (datetime.now().date() - timedelta(days=days)).isoformat()

    query = """
        SELECT a.*
        FROM activities a
        WHERE a.type = 'Run'
        AND DATE(a.start_date_local) >= ?
        AND a.id NOT IN (
            SELECT linked_activity_id
            FROM planned_workouts
            WHERE linked_activity_id IS NOT NULL
        )
        ORDER BY a.start_date_local DESC
    """
    df = pd.read_sql_query(query, conn, params=(cutoff_date,))
    conn.close()
    return df


def update_workout_status(workout_id: int, status: str, db_path='data/strava_activities.db'):
    """Actualiza el estado de un entrenamiento planificado."""
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE planned_workouts
        SET status = ?
        WHERE id = ?
    """, (status, workout_id))

    conn.commit()
    conn.close()


def reset_workout_to_pending(workout_id: int, db_path='data/strava_activities.db'):
    """Desmarca un entrenamiento, volviéndolo a estado 'pending' y desvinculando la actividad."""
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE planned_workouts
        SET status = 'pending', linked_activity_id = NULL
        WHERE id = ?
    """, (workout_id,))

    conn.commit()
    conn.close()


def close_training_plan(plan_id: int, db_path='data/strava_activities.db'):
    """Marca un plan de entrenamiento como completado."""
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE training_plans
        SET status = 'completed'
        WHERE id = ?
    """, (plan_id,))

    conn.commit()
    conn.close()


def delete_workout(workout_id: int, db_path='data/strava_activities.db'):
    """Elimina un entrenamiento planificado del plan."""
    conn = get_connection()
    cur = conn.cursor()

    # Primero eliminar feedback asociado si existe
    cur.execute("""
        DELETE FROM workout_feedback
        WHERE planned_workout_id = ?
    """, (workout_id,))

    # Luego eliminar el entrenamiento
    cur.execute("""
        DELETE FROM planned_workouts
        WHERE id = ?
    """, (workout_id,))

    conn.commit()
    conn.close()


def update_workout(workout_id: int, date: str = None, workout_type: str = None,
                   distance_km: float = None, description: str = None,
                   pace_objective: str = None, notes: str = None,
                   db_path='data/strava_activities.db'):
    """Actualiza los campos de un entrenamiento planificado."""
    conn = get_connection()
    cur = conn.cursor()

    # Construir query dinámicamente según los campos proporcionados
    updates = []
    values = []

    if date is not None:
        updates.append("date = ?")
        values.append(date)
    if workout_type is not None:
        updates.append("workout_type = ?")
        values.append(workout_type)
    if distance_km is not None:
        updates.append("distance_km = ?")
        values.append(distance_km)
    if description is not None:
        updates.append("description = ?")
        values.append(description)
    if pace_objective is not None:
        updates.append("pace_objective = ?")
        values.append(pace_objective)
    if notes is not None:
        updates.append("notes = ?")
        values.append(notes)

    if not updates:
        conn.close()
        return  # No hay nada que actualizar

    values.append(workout_id)
    query = f"UPDATE planned_workouts SET {', '.join(updates)} WHERE id = ?"

    cur.execute(query, values)
    conn.commit()
    conn.close()
