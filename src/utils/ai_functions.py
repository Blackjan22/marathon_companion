# utils/ai_functions.py
"""
Funciones que el modelo Gemini puede llamar para acceder a datos y realizar acciones.
Estas funciones están diseñadas para ser usadas con Gemini Function Calling.
"""

import sqlite3
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List


def get_recent_activities(days: int = 7) -> dict:
    """
    Obtiene las actividades de running de los últimos N días.

    Args:
        days: Número de días hacia atrás para buscar actividades (por defecto 7)

    Returns:
        Un diccionario con las actividades recientes y sus estadísticas
    """
    conn = sqlite3.connect('data/strava_activities.db')
    cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()

    query = """
        SELECT
            id, name, start_date_local,
            distance/1000 as distance_km,
            moving_time/60 as moving_time_min,
            (moving_time/60)/(distance/1000) as pace_min_km,
            average_heartrate,
            total_elevation_gain,
            description, private_note
        FROM activities
        WHERE type = 'Run'
        AND start_date_local >= ?
        ORDER BY start_date_local DESC
    """
    df = pd.read_sql_query(query, conn, params=(cutoff_date,))
    conn.close()

    if df.empty:
        return {"activities": [], "count": 0, "total_km": 0}

    # Convertir a dict y asegurarse de que los IDs son strings para evitar pérdida de precisión
    activities = df.to_dict('records')
    for activity in activities:
        activity['id'] = str(activity['id'])  # Convertir ID a string

    return {
        "activities": activities,
        "count": len(activities),
        "total_km": round(df['distance_km'].sum(), 2),
        "avg_pace": round(df['pace_min_km'].mean(), 2)
    }


def get_weekly_stats(weeks: int = 4) -> dict:
    """
    Obtiene estadísticas agregadas por semana de las últimas N semanas.

    Args:
        weeks: Número de semanas hacia atrás (por defecto 4)

    Returns:
        Diccionario con estadísticas semanales
    """
    conn = sqlite3.connect('data/strava_activities.db')
    cutoff_date = (datetime.now() - timedelta(weeks=weeks)).isoformat()

    query = """
        SELECT
            strftime('%Y-%W', start_date_local) as week,
            COUNT(*) as num_runs,
            SUM(distance)/1000 as total_km,
            AVG((moving_time/60)/(distance/1000)) as avg_pace_min_km,
            AVG(average_heartrate) as avg_hr
        FROM activities
        WHERE type = 'Run'
        AND start_date_local >= ?
        GROUP BY week
        ORDER BY week DESC
    """
    df = pd.read_sql_query(query, conn, params=(cutoff_date,))
    conn.close()

    if df.empty:
        return {"weeks": [], "total_weeks": 0}

    weeks_data = df.to_dict('records')
    return {
        "weeks": weeks_data,
        "total_weeks": len(weeks_data),
        "avg_weekly_km": round(df['total_km'].mean(), 2)
    }


def get_activity_details(activity_id) -> dict:
    """
    Obtiene los detalles completos de una actividad específica, incluyendo laps.

    Args:
        activity_id: ID de la actividad en Strava (puede ser int o string)

    Returns:
        Diccionario con información detallada de la actividad y sus laps
    """
    # Convertir a int si viene como string (para compatibilidad con Gemini)
    if isinstance(activity_id, str):
        try:
            activity_id = int(activity_id)
        except ValueError:
            return {"error": f"ID inválido: {activity_id}"}

    conn = sqlite3.connect('data/strava_activities.db')

    # Información de la actividad
    activity_query = """
        SELECT
            id, name, start_date_local,
            distance/1000 as distance_km,
            moving_time, elapsed_time,
            average_speed, average_heartrate,
            total_elevation_gain,
            description, private_note
        FROM activities
        WHERE id = ?
    """
    activity_df = pd.read_sql_query(activity_query, conn, params=(activity_id,))

    if activity_df.empty:
        conn.close()
        return {"error": f"Activity {activity_id} not found"}

    # Laps de la actividad
    laps_query = """
        SELECT
            lap_index, name,
            distance/1000 as distance_km,
            moving_time, elapsed_time,
            average_speed, max_speed,
            total_elevation_gain
        FROM laps
        WHERE activity_id = ?
        ORDER BY lap_index
    """
    laps_df = pd.read_sql_query(laps_query, conn, params=(activity_id,))
    conn.close()

    activity_info = activity_df.iloc[0].to_dict()
    # Convertir ID a string para evitar pérdida de precisión
    activity_info['id'] = str(activity_info['id'])

    laps_info = laps_df.to_dict('records') if not laps_df.empty else []

    return {
        "activity": activity_info,
        "laps": laps_info,
        "num_laps": len(laps_info)
    }


def get_current_plan() -> dict:
    """
    Obtiene el plan de entrenamiento activo actual con todos sus entrenamientos.

    Returns:
        Diccionario con el plan actual y sus entrenamientos planificados
    """
    conn = sqlite3.connect('data/strava_activities.db')

    # Plan activo
    plan_query = """
        SELECT * FROM training_plans
        WHERE status = 'active'
        ORDER BY week_start_date DESC
        LIMIT 1
    """
    plan_df = pd.read_sql_query(plan_query, conn)

    if plan_df.empty:
        conn.close()
        return {"plan": None, "workouts": [], "message": "No active plan found"}

    # Convertir explícitamente a int para evitar problemas con numpy types
    plan_id = int(plan_df.iloc[0]['id'])

    # Entrenamientos del plan
    workouts_query = """
        SELECT
            pw.id, pw.date, pw.workout_type, pw.distance_km,
            pw.description, pw.pace_objective, pw.notes,
            pw.status, pw.linked_activity_id,
            a.name as activity_name
        FROM planned_workouts pw
        LEFT JOIN activities a ON pw.linked_activity_id = a.id
        WHERE pw.plan_id = ?
        ORDER BY pw.date
    """
    workouts_df = pd.read_sql_query(workouts_query, conn, params=(plan_id,))
    conn.close()

    plan_info = plan_df.iloc[0].to_dict()
    workouts_info = workouts_df.to_dict('records') if not workouts_df.empty else []

    return {
        "plan": plan_info,
        "workouts": workouts_info,
        "num_workouts": len(workouts_info)
    }




def create_training_plan(week_start_date: str, workouts: List[Dict], goal: str = None, notes: str = None) -> dict:
    """
    Crea un nuevo plan de entrenamiento con los entrenamientos especificados.
    IMPORTANTE: Desactiva automáticamente cualquier plan activo anterior.

    Args:
        week_start_date: Fecha de inicio de la semana (formato YYYY-MM-DD)
        workouts: Lista de entrenamientos, cada uno con {date, workout_type, distance_km, description, pace_objective, notes}
        goal: Objetivo del plan (opcional)
        notes: Notas adicionales sobre el plan (opcional)

    Returns:
        Diccionario con el plan creado y sus entrenamientos
    """
    conn = sqlite3.connect('data/strava_activities.db')
    cur = conn.cursor()

    # IMPORTANTE: Desactivar todos los planes activos anteriores
    cur.execute("""
        UPDATE training_plans
        SET status = 'completed'
        WHERE status = 'active'
    """)

    # Calcular número de semana
    week_start = datetime.fromisoformat(week_start_date)
    week_number = week_start.isocalendar()[1]

    # Crear el plan
    cur.execute("""
        INSERT INTO training_plans (week_start_date, week_number, goal, notes, status)
        VALUES (?, ?, ?, ?, 'active')
    """, (week_start_date, week_number, goal, notes))

    plan_id = cur.lastrowid

    # Crear los entrenamientos
    workout_ids = []
    for workout in workouts:
        cur.execute("""
            INSERT INTO planned_workouts
            (plan_id, date, workout_type, distance_km, description, pace_objective, notes, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'pending')
        """, (
            plan_id,
            workout['date'],
            workout.get('workout_type', 'rodaje'),
            workout['distance_km'],
            workout.get('description', ''),
            workout.get('pace_objective', ''),
            workout.get('notes', ''),
        ))
        workout_ids.append(cur.lastrowid)

    conn.commit()
    conn.close()

    return {
        "success": True,
        "plan_id": plan_id,
        "workout_ids": workout_ids,
        "num_workouts": len(workout_ids),
        "message": f"Plan created for week starting {week_start_date} with {len(workout_ids)} workouts"
    }


def update_workout(workout_id, changes: Dict) -> dict:
    """
    Actualiza un entrenamiento planificado con los cambios especificados.

    Args:
        workout_id: ID del entrenamiento a actualizar (puede ser int o string)
        changes: Diccionario con los campos a actualizar (date, distance_km, description, pace_objective, notes, status)

    Returns:
        Diccionario confirmando la actualización
    """
    # Convertir a int si viene como string
    if isinstance(workout_id, str):
        try:
            workout_id = int(workout_id)
        except ValueError:
            return {"error": f"ID inválido: {workout_id}"}

    conn = sqlite3.connect('data/strava_activities.db')
    cur = conn.cursor()

    # Construir query dinámicamente basándose en los campos a actualizar
    allowed_fields = ['date', 'workout_type', 'distance_km', 'description', 'pace_objective', 'notes', 'status']
    updates = []
    values = []

    for field, value in changes.items():
        if field in allowed_fields:
            updates.append(f"{field} = ?")
            values.append(value)

    if not updates:
        conn.close()
        return {"success": False, "message": "No valid fields to update"}

    values.append(workout_id)
    query = f"UPDATE planned_workouts SET {', '.join(updates)} WHERE id = ?"

    cur.execute(query, values)
    conn.commit()
    conn.close()

    return {
        "success": True,
        "workout_id": workout_id,
        "updated_fields": list(changes.keys()),
        "message": f"Workout {workout_id} updated successfully"
    }


def delete_workout(workout_id) -> dict:
    """
    Elimina un entrenamiento planificado del plan actual.

    Args:
        workout_id: ID del entrenamiento a eliminar (puede ser int o string)

    Returns:
        Diccionario con el resultado de la operación
    """
    # Convertir a int si viene como string
    if isinstance(workout_id, str):
        try:
            workout_id = int(workout_id)
        except ValueError:
            return {"success": False, "error": f"ID inválido: {workout_id}"}

    conn = sqlite3.connect('data/strava_activities.db')
    cur = conn.cursor()

    # Verificar que el workout existe
    cur.execute("SELECT id FROM planned_workouts WHERE id = ?", (workout_id,))
    if not cur.fetchone():
        conn.close()
        return {"success": False, "error": f"Workout {workout_id} no encontrado"}

    # Eliminar feedback asociado si existe
    cur.execute("DELETE FROM workout_feedback WHERE planned_workout_id = ?", (workout_id,))

    # Eliminar el entrenamiento
    cur.execute("DELETE FROM planned_workouts WHERE id = ?", (workout_id,))

    conn.commit()
    conn.close()

    return {
        "success": True,
        "workout_id": workout_id,
        "message": f"Workout {workout_id} eliminado correctamente"
    }


def add_workout_to_current_plan(date: str, workout_type: str, distance_km: float,
                                  description: str = None, pace_objective: str = None,
                                  notes: str = None) -> dict:
    """
    Añade un entrenamiento al plan activo existente sin crear un plan nuevo.
    Útil para añadir entrenamientos individuales o modificar el plan actual.

    Args:
        date: Fecha del entrenamiento (formato YYYY-MM-DD)
        workout_type: Tipo de entrenamiento (calidad, rodaje, tirada_larga, etc.)
        distance_km: Distancia en kilómetros
        description: Descripción del entrenamiento (opcional)
        pace_objective: Ritmo objetivo (opcional)
        notes: Notas adicionales (opcional)

    Returns:
        Diccionario con el resultado de la operación
    """
    conn = sqlite3.connect('data/strava_activities.db')
    cur = conn.cursor()

    # Obtener el plan activo
    cur.execute("SELECT id FROM training_plans WHERE status = 'active' LIMIT 1")
    result = cur.fetchone()

    if not result:
        conn.close()
        return {
            "success": False,
            "error": "No hay ningún plan activo. Usa create_training_plan para crear uno primero."
        }

    plan_id = result[0]

    # Añadir el entrenamiento
    cur.execute("""
        INSERT INTO planned_workouts
        (plan_id, date, workout_type, distance_km, description, pace_objective, notes, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, 'pending')
    """, (plan_id, date, workout_type, distance_km, description, pace_objective, notes))

    workout_id = cur.lastrowid
    conn.commit()
    conn.close()

    return {
        "success": True,
        "workout_id": workout_id,
        "plan_id": plan_id,
        "message": f"Entrenamiento añadido al plan activo (workout_id: {workout_id})"
    }
