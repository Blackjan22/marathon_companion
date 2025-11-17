# utils/ai_functions.py
"""
Funciones que el modelo Gemini puede llamar para acceder a datos y realizar acciones.
Estas funciones están diseñadas para ser usadas con Gemini Function Calling.
"""

import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List
from .db_config import get_connection


def get_recent_activities(days: int = 7) -> dict:
    """
    Obtiene las actividades de running de los últimos N días.

    Args:
        days: Número de días hacia atrás para buscar actividades (por defecto 7)

    Returns:
        Un diccionario con las actividades recientes y sus estadísticas
    """
    conn = get_connection()
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
    conn = get_connection()
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

    conn = get_connection()

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
    conn = get_connection()

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
    conn = get_connection()
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

    conn = get_connection()
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

    conn = get_connection()
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


def get_runner_profile() -> dict:
    """
    Obtiene el perfil completo del corredor para personalizar recomendaciones.

    Returns:
        Diccionario con toda la información del perfil del corredor
    """
    conn = get_connection()

    query = """
        SELECT * FROM runner_profile
        ORDER BY updated_at DESC
        LIMIT 1
    """
    df = pd.read_sql_query(query, conn)
    conn.close()

    if df.empty:
        return {
            "profile": None,
            "message": "No hay perfil configurado. Ve a la página de Perfil para crear uno."
        }

    profile_info = df.iloc[0].to_dict()

    return {
        "profile": profile_info,
        "has_profile": True
    }


def analyze_performance_trends(weeks: int = 4) -> dict:
    """
    Analiza tendencias de rendimiento para detectar mejoras o fatiga.

    Examina la evolución de ritmo vs FC en entrenamientos similares,
    detecta inconsistencias que puedan indicar fatiga o mejora de forma.

    Args:
        weeks: Número de semanas hacia atrás para analizar (por defecto 4)

    Returns:
        Diccionario con análisis de tendencias y recomendaciones
    """
    conn = get_connection()
    cutoff_date = (datetime.now() - timedelta(weeks=weeks)).isoformat()

    # Obtener actividades recientes con FC
    query = """
        SELECT
            start_date_local,
            distance/1000 as distance_km,
            moving_time,
            (moving_time/60)/(distance/1000) as pace_min_km,
            average_heartrate as avg_hr,
            description,
            private_note
        FROM activities
        WHERE type = 'Run'
        AND start_date_local >= ?
        AND average_heartrate IS NOT NULL
        AND distance > 3000
        ORDER BY start_date_local ASC
    """
    df = pd.read_sql_query(query, conn, params=(cutoff_date,))
    conn.close()

    if df.empty or len(df) < 3:
        return {
            "status": "insufficient_data",
            "message": "Se necesitan al menos 3 entrenamientos con FC en las últimas semanas"
        }

    # Analizar rodajes fáciles (ritmo > 5:00/km)
    easy_runs = df[df['pace_min_km'] > 5.0].copy()

    analysis = {
        "total_runs": len(df),
        "weeks_analyzed": weeks,
        "trends": []
    }

    if len(easy_runs) >= 3:
        # Dividir en primera mitad vs segunda mitad del período
        mid_point = len(easy_runs) // 2
        first_half = easy_runs.iloc[:mid_point]
        second_half = easy_runs.iloc[mid_point:]

        avg_hr_first = first_half['avg_hr'].mean()
        avg_hr_second = second_half['avg_hr'].mean()
        avg_pace_first = first_half['pace_min_km'].mean()
        avg_pace_second = second_half['pace_min_km'].mean()

        hr_change = ((avg_hr_second - avg_hr_first) / avg_hr_first) * 100
        pace_change = ((avg_pace_second - avg_pace_first) / avg_pace_first) * 100

        analysis["easy_runs_analysis"] = {
            "first_half_avg_hr": round(avg_hr_first, 1),
            "second_half_avg_hr": round(avg_hr_second, 1),
            "first_half_avg_pace": round(avg_pace_first, 2),
            "second_half_avg_pace": round(avg_pace_second, 2),
            "hr_change_pct": round(hr_change, 1),
            "pace_change_pct": round(pace_change, 1),
            "num_runs_analyzed": len(easy_runs),
            "first_half_runs": len(first_half),
            "second_half_runs": len(second_half)
        }

        # Interpretación con más detalle
        if hr_change < -3 and pace_change < -2:
            analysis["trends"].append({
                "type": "positive",
                "message": f"🟢 Mejora aeróbica clara: FC bajó de {round(avg_hr_first, 1)} a {round(avg_hr_second, 1)} ppm ({hr_change:+.1f}%) mientras el ritmo mejoró de {avg_pace_first:.2f} a {avg_pace_second:.2f} min/km ({pace_change:+.1f}%)"
            })
        elif hr_change < -3 and abs(pace_change) < 2:
            analysis["trends"].append({
                "type": "positive",
                "message": f"🟢 Mejora en eficiencia: FC bajó de {round(avg_hr_first, 1)} a {round(avg_hr_second, 1)} ppm ({hr_change:+.1f}%) manteniendo ritmo estable ~{avg_pace_first:.2f} min/km"
            })
        elif hr_change > 3 and pace_change > 2:
            analysis["trends"].append({
                "type": "warning",
                "message": f"🟡 Posible fatiga: FC subió de {round(avg_hr_first, 1)} a {round(avg_hr_second, 1)} ppm ({hr_change:+.1f}%) mientras el ritmo empeoró de {avg_pace_first:.2f} a {avg_pace_second:.2f} min/km ({pace_change:+.1f}%). Considera semana de descarga."
            })
        elif hr_change > 3 and abs(pace_change) < 2:
            analysis["trends"].append({
                "type": "warning",
                "message": f"🟡 FC elevada: Subió de {round(avg_hr_first, 1)} a {round(avg_hr_second, 1)} ppm ({hr_change:+.1f}%) manteniendo ritmo ~{avg_pace_first:.2f} min/km. Posible fatiga acumulada."
            })
        elif abs(hr_change) < 2 and abs(pace_change) < 2:
            analysis["trends"].append({
                "type": "neutral",
                "message": f"⚪ Forma estable: FC ~{round(avg_hr_first, 1)} ppm y ritmo ~{avg_pace_first:.2f} min/km consistentes"
            })

    # Analizar entrenamientos de calidad (ritmo < 4:45/km)
    quality_runs = df[df['pace_min_km'] < 4.75].copy()

    if len(quality_runs) >= 2:
        analysis["quality_runs_count"] = len(quality_runs)
        analysis["avg_quality_pace"] = round(quality_runs['pace_min_km'].mean(), 2)

        if len(quality_runs) >= 2:
            recent_quality = quality_runs.iloc[-1]
            analysis["last_quality"] = {
                "date": recent_quality['start_date_local'][:10],
                "pace": round(recent_quality['pace_min_km'], 2),
                "avg_hr": round(recent_quality['avg_hr'], 1) if pd.notna(recent_quality['avg_hr']) else None
            }

    return analysis


def predict_race_times(current_race_distance_km: float, current_time_minutes: float,
                       target_race_distance_km: float) -> dict:
    """
    Predice tiempos de carrera usando la fórmula de Riegel y proporciona análisis.

    Fórmula: T2 = T1 * (D2/D1)^1.06
    donde T = tiempo, D = distancia

    Args:
        current_race_distance_km: Distancia de la marca actual (ej: 10)
        current_time_minutes: Tiempo en la distancia actual en minutos (ej: 43.33 para 43:20)
        target_race_distance_km: Distancia objetivo para predecir (ej: 21.0975)

    Returns:
        Diccionario con predicción de tiempo y análisis de viabilidad
    """
    # Fórmula de Riegel (exponente 1.06 es el estándar)
    predicted_time_minutes = current_time_minutes * ((target_race_distance_km / current_race_distance_km) ** 1.06)

    predicted_hours = int(predicted_time_minutes // 60)
    predicted_mins = int(predicted_time_minutes % 60)
    predicted_secs = int((predicted_time_minutes % 1) * 60)

    # Calcular ritmo previsto
    predicted_pace = predicted_time_minutes / target_race_distance_km

    # Distancias comunes
    distance_names = {
        5.0: "5K",
        10.0: "10K",
        15.0: "15K",
        21.0975: "Media Maratón",
        42.195: "Maratón"
    }

    current_distance_name = distance_names.get(current_race_distance_km, f"{current_race_distance_km}km")
    target_distance_name = distance_names.get(target_race_distance_km, f"{target_race_distance_km}km")

    # Calcular ritmo actual
    current_pace = current_time_minutes / current_race_distance_km

    return {
        "current_race": {
            "distance": current_distance_name,
            "time": f"{int(current_time_minutes // 60)}:{int(current_time_minutes % 60):02d}:{int((current_time_minutes % 1) * 60):02d}",
            "pace_per_km": f"{int(current_pace)}:{int((current_pace % 1) * 60):02d}"
        },
        "predicted_race": {
            "distance": target_distance_name,
            "predicted_time": f"{predicted_hours}:{predicted_mins:02d}:{predicted_secs:02d}",
            "predicted_pace_per_km": f"{int(predicted_pace)}:{int((predicted_pace % 1) * 60):02d}",
            "predicted_time_minutes": round(predicted_time_minutes, 2)
        },
        "analysis": {
            "formula": "Riegel (exponente 1.06)",
            "note": "Esta predicción asume un entrenamiento específico adecuado para la distancia objetivo"
        }
    }


def analyze_training_load_advanced() -> dict:
    """
    Análisis avanzado de carga de entrenamiento con detección de patrones de fatiga.

    Examina volumen, intensidad, RPE (de notas) y detecta señales de sobreentrenamiento.

    Returns:
        Diccionario con análisis detallado de carga y recomendaciones
    """
    conn = get_connection()

    # Últimas 6 semanas de datos
    cutoff_date = (datetime.now() - timedelta(weeks=6)).isoformat()

    query = """
        SELECT
            strftime('%Y-%W', start_date_local) as week,
            COUNT(*) as num_runs,
            SUM(distance)/1000 as total_km,
            AVG(average_heartrate) as avg_hr,
            AVG((moving_time/60)/(distance/1000)) as avg_pace,
            GROUP_CONCAT(private_note, ' | ') as notes
        FROM activities
        WHERE type = 'Run'
        AND start_date_local >= ?
        GROUP BY week
        ORDER BY week ASC
    """

    df = pd.read_sql_query(query, conn, params=(cutoff_date,))
    conn.close()

    if df.empty or len(df) < 2:
        return {
            "status": "insufficient_data",
            "message": "Se necesitan al menos 2 semanas de datos"
        }

    # Análisis de progresión de carga
    weeks = df['total_km'].tolist()
    current_week = weeks[-1]
    previous_week = weeks[-2] if len(weeks) > 1 else current_week
    avg_previous_weeks = sum(weeks[:-1]) / len(weeks[:-1]) if len(weeks) > 1 else current_week

    load_increase = ((current_week - previous_week) / previous_week * 100) if previous_week > 0 else 0

    analysis = {
        "weeks_analyzed": len(df),
        "current_week_km": round(current_week, 1),
        "previous_week_km": round(previous_week, 1),
        "avg_last_weeks_km": round(avg_previous_weeks, 1),
        "load_increase_pct": round(load_increase, 1),
        "warnings": [],
        "recommendations": []
    }

    # Detectar sobreentrenamiento
    if load_increase > 15:
        analysis["warnings"].append({
            "level": "high",
            "message": f"Aumento de volumen muy elevado ({load_increase:.1f}%). Riesgo de lesión aumentado."
        })
        analysis["recommendations"].append("Considera reducir volumen un 10-15% esta semana")
    elif load_increase > 10:
        analysis["warnings"].append({
            "level": "medium",
            "message": f"Aumento de volumen moderado-alto ({load_increase:.1f}%). Monitorea sensaciones."
        })
        analysis["recommendations"].append("Asegúrate de que los rodajes suaves sean realmente suaves (Z2)")

    # Analizar FC tendencia
    if len(df) >= 3:
        hr_recent = df['avg_hr'].iloc[-2:].mean()
        hr_older = df['avg_hr'].iloc[:-2].mean()

        if pd.notna(hr_recent) and pd.notna(hr_older):
            hr_change = ((hr_recent - hr_older) / hr_older) * 100

            if hr_change > 3:
                analysis["warnings"].append({
                    "level": "medium",
                    "message": f"FC media en aumento ({hr_change:.1f}%). Posible fatiga acumulada."
                })
                analysis["recommendations"].append("Prioriza recuperación y sueño esta semana")

    # Análisis de notas privadas (buscar keywords de fatiga)
    fatigue_keywords = ['cansado', 'pesadas', 'duro', 'mal', 'fatiga', 'agotado']
    notes_text = ' '.join(df['notes'].dropna().astype(str).tolist()).lower()

    fatigue_mentions = sum(1 for keyword in fatigue_keywords if keyword in notes_text)

    if fatigue_mentions >= 2:
        analysis["warnings"].append({
            "level": "medium",
            "message": f"Múltiples menciones de fatiga en tus notas ({fatigue_mentions} referencias)"
        })
        analysis["recommendations"].append("Considera semana de descarga (reducir 20-30% volumen)")

    # Estado general
    if not analysis["warnings"]:
        analysis["status"] = "good"
        analysis["summary"] = "Carga de entrenamiento controlada. Continúa con el plan."
    elif len([w for w in analysis["warnings"] if w["level"] == "high"]) > 0:
        analysis["status"] = "high_risk"
        analysis["summary"] = "Riesgo elevado de sobreentrenamiento. Acción inmediata recomendada."
    else:
        analysis["status"] = "caution"
        analysis["summary"] = "Señales de fatiga detectadas. Monitorea y ajusta si es necesario."

    return analysis


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
    conn = get_connection()
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
