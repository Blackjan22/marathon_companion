# utils/ai_context.py
"""
Sistema de gestión de contexto y memoria para el chatbot de IA.
Proporciona contexto relevante automáticamente al iniciar conversaciones.
"""

import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List
from . import ai_functions
from .db_config import get_connection


def generate_initial_context() -> str:
    """
    Genera un contexto inicial completo para el chatbot al iniciar una conversación.

    Returns:
        String con el contexto formateado para incluir en el system prompt
    """
    context_parts = []

    # 0. Perfil del corredor (NUEVO)
    try:
        profile = ai_functions.get_runner_profile()
        if profile.get('has_profile') and profile['profile']:
            p = profile['profile']
            context_parts.append(f"**Perfil del Corredor:**")
            if p.get('name'):
                context_parts.append(f"- Nombre: {p['name']}")
            if p.get('current_goal'):
                context_parts.append(f"- Objetivo: {p['current_goal']}")
            if p.get('goal_race_date'):
                from datetime import datetime
                race_date = datetime.fromisoformat(p['goal_race_date'])
                days_to_race = (race_date.date() - datetime.now().date()).days
                if days_to_race > 0:
                    context_parts.append(f"- Fecha objetivo: {race_date.strftime('%d/%m/%Y')} (en {days_to_race} días)")
            if p.get('training_philosophy'):
                context_parts.append(f"- Filosofía: {p['training_philosophy']}")

            # PRs
            prs = []
            if p.get('pr_5k'):
                prs.append(f"5K: {p['pr_5k']}")
            if p.get('pr_10k'):
                prs.append(f"10K: {p['pr_10k']}")
            if p.get('pr_half'):
                prs.append(f"Media: {p['pr_half']}")
            if prs:
                context_parts.append(f"- PRs: {', '.join(prs)}")
        else:
            context_parts.append("**Perfil:** No configurado (recomienda ir a la página de Perfil)")
    except Exception as e:
        context_parts.append(f"(Error cargando perfil: {str(e)})")

    # 1. Resumen de actividad reciente
    try:
        recent = ai_functions.get_recent_activities(days=7)
        if recent['count'] > 0:
            context_parts.append(f"**Últimos 7 días:**")
            context_parts.append(f"- {recent['count']} entrenamientos realizados")
            context_parts.append(f"- {recent['total_km']} km totales")
            context_parts.append(f"- Ritmo medio: {recent['avg_pace']:.2f} min/km")

            # Listar entrenamientos recientes
            if recent['activities']:
                context_parts.append("\nEntrenos recientes:")
                for act in recent['activities'][:3]:  # Solo los 3 más recientes
                    date = pd.to_datetime(act['start_date_local']).strftime('%d/%m')
                    # IMPORTANTE: Incluir el ID para que el modelo pueda usarlo con get_activity_details
                    context_parts.append(
                        f"  - {date}: {act['name']}, {act['distance_km']:.1f}km, {act['pace_min_km']:.2f} min/km (ID: {act['id']})"
                    )
    except Exception as e:
        context_parts.append(f"(Error cargando actividades recientes: {str(e)})")

    # 2. Plan actual
    try:
        plan = ai_functions.get_current_plan()
        if plan['plan']:
            plan_info = plan['plan']
            context_parts.append(f"\n**Plan activo:**")
            context_parts.append(f"- Semana inicio: {plan_info['week_start_date']}")
            if plan_info['goal']:
                context_parts.append(f"- Objetivo: {plan_info['goal']}")

            # Estado de entrenamientos del plan
            if plan['workouts']:
                completed = sum(1 for w in plan['workouts'] if w['status'] == 'completed')
                pending = sum(1 for w in plan['workouts'] if w['status'] == 'pending')
                context_parts.append(f"- Entrenamientos: {completed}/{plan['num_workouts']} completados, {pending} pendientes")
        else:
            context_parts.append("\n**Plan activo:** No hay plan activo actualmente")
    except Exception as e:
        context_parts.append(f"(Error cargando plan actual: {str(e)})")

    # 3. Estadísticas de las últimas semanas
    try:
        stats = ai_functions.get_weekly_stats(weeks=4)
        if stats['total_weeks'] > 0:
            context_parts.append(f"\n**Últimas 4 semanas:**")
            context_parts.append(f"- Promedio semanal: {stats['avg_weekly_km']:.1f} km/semana")

            # Tendencia
            if len(stats['weeks']) >= 2:
                last_week_km = stats['weeks'][0]['total_km']
                prev_week_km = stats['weeks'][1]['total_km']
                if last_week_km > prev_week_km * 1.1:
                    context_parts.append("- Tendencia: ⬆️ Volumen creciente")
                elif last_week_km < prev_week_km * 0.9:
                    context_parts.append("- Tendencia: ⬇️ Volumen decreciente")
                else:
                    context_parts.append("- Tendencia: ➡️ Volumen estable")
    except Exception as e:
        context_parts.append(f"(Error cargando estadísticas: {str(e)})")

    # 4. Notas privadas recientes de Strava
    try:
        notes_summary = get_recent_private_notes_summary()
        if notes_summary:
            context_parts.append(f"\n**Últimas notas de entrenamientos:**")
            context_parts.append(notes_summary)
    except Exception as e:
        context_parts.append(f"(Error cargando notas: {str(e)})")

    # 5. Análisis de rendimiento (NUEVO)
    try:
        trends = ai_functions.analyze_performance_trends(weeks=4)
        if trends.get('status') != 'insufficient_data' and trends.get('trends'):
            context_parts.append(f"\n**Análisis de Rendimiento (últimas 4 semanas):**")
            for trend in trends['trends']:
                context_parts.append(f"  {trend['message']}")
    except Exception as e:
        pass  # No mostrar error si no hay suficientes datos

    return "\n".join(context_parts)


def get_recent_private_notes_summary(days: int = 7) -> str:
    """
    Obtiene las notas privadas de las actividades recientes de Strava.

    Args:
        days: Número de días hacia atrás para buscar notas

    Returns:
        String con resumen de las notas privadas o None si no hay
    """
    conn = get_connection()
    cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()

    query = """
        SELECT
            name,
            start_date_local,
            distance/1000 as distance_km,
            private_note,
            description
        FROM activities
        WHERE type = 'Run'
        AND start_date_local >= ?
        AND (private_note IS NOT NULL AND private_note != '' OR description IS NOT NULL AND description != '')
        ORDER BY start_date_local DESC
        LIMIT 2
    """

    df = pd.read_sql_query(query, conn, params=(cutoff_date,))
    conn.close()

    if df.empty:
        return None

    summary_parts = []
    for _, activity in df.iterrows():
        date = pd.to_datetime(activity['start_date_local']).strftime('%d/%m')
        summary_parts.append(f"- {date}: {activity['name']}, {activity['distance_km']:.1f}km")

        if activity['private_note']:
            summary_parts.append(f"  📝 {activity['private_note']}")
        elif activity['description']:
            summary_parts.append(f"  📝 {activity['description']}")

    return "\n".join(summary_parts) if summary_parts else None


def summarize_conversation_turn(messages: List[Dict]) -> str:
    """
    Crea un resumen de un turno de conversación para guardar contexto.

    Args:
        messages: Lista de mensajes del turno

    Returns:
        String con resumen del turno
    """
    # Para implementación futura: podríamos usar Gemini para generar resúmenes
    # Por ahora, simplemente concatenamos los últimos mensajes
    if not messages:
        return ""

    summary_parts = []
    for msg in messages[-3:]:  # Últimos 3 mensajes
        role = "Usuario" if msg['role'] == 'user' else "Coach"
        content_preview = msg['content'][:100] + "..." if len(msg['content']) > 100 else msg['content']
        summary_parts.append(f"{role}: {content_preview}")

    return " | ".join(summary_parts)


def get_contextual_greeting() -> str:
    """
    Genera un saludo contextual basado en el estado actual del atleta.

    Returns:
        String con saludo personalizado
    """
    greetings = []

    # Verificar última actividad
    try:
        recent = ai_functions.get_recent_activities(days=1)
        if recent['count'] > 0:
            greetings.append("¡Veo que has entrenado hoy! 💪")
        else:
            recent_week = ai_functions.get_recent_activities(days=7)
            if recent_week['count'] == 0:
                greetings.append("¿Cómo va todo? Hace unos días que no te veo entrenar.")
            else:
                greetings.append(f"¡Hola! Llevas {recent_week['count']} entrenos esta semana.")
    except:
        greetings.append("¡Hola! ¿En qué puedo ayudarte hoy?")

    # Verificar plan pendiente
    try:
        plan = ai_functions.get_current_plan()
        if plan['plan'] and plan['workouts']:
            pending = sum(1 for w in plan['workouts'] if w['status'] == 'pending')
            if pending > 0:
                greetings.append(f"Tienes {pending} entrenos pendientes en tu plan.")
    except:
        pass

    return " ".join(greetings) if greetings else "¡Hola! Estoy aquí para ayudarte con tu entrenamiento."


def save_context_snapshot(summary: str):
    """
    Guarda un snapshot del contexto en la base de datos.

    Args:
        summary: Resumen del contexto a guardar
    """
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO chat_history (role, content, timestamp, context_summary)
        VALUES ('system', '', ?, ?)
    """, (datetime.now().isoformat(), summary))

    conn.commit()
    conn.close()


def get_relevant_activities_for_planning(weeks_back: int = 4) -> Dict:
    """
    Obtiene información relevante de actividades para planificación.

    Args:
        weeks_back: Semanas hacia atrás para analizar

    Returns:
        Diccionario con métricas y recomendaciones
    """
    try:
        stats = ai_functions.get_weekly_stats(weeks=weeks_back)
        recent = ai_functions.get_recent_activities(days=7)

        analysis = {
            "avg_weekly_km": stats.get('avg_weekly_km', 0),
            "recent_runs": recent.get('count', 0),
            "recent_km": recent.get('total_km', 0),
            "avg_pace": recent.get('avg_pace', 0),
            "recommendation": ""
        }

        # Generar recomendación simple
        if analysis['avg_weekly_km'] < 20:
            analysis['recommendation'] = "Volumen bajo: enfócate en construir base aeróbica"
        elif analysis['avg_weekly_km'] < 40:
            analysis['recommendation'] = "Volumen moderado: buen momento para añadir calidad"
        else:
            analysis['recommendation'] = "Volumen alto: mantén equilibrio entre volumen y recuperación"

        return analysis
    except Exception as e:
        return {"error": str(e)}


def check_training_load_progression() -> Dict:
    """
    Analiza la progresión de carga de entrenamiento para prevenir sobreentrenamiento.

    Returns:
        Diccionario con análisis de carga
    """
    try:
        stats = ai_functions.get_weekly_stats(weeks=4)

        if stats['total_weeks'] < 2:
            return {"status": "insufficient_data"}

        weeks = stats['weeks']
        current_week = weeks[0]['total_km']
        previous_weeks_avg = sum(w['total_km'] for w in weeks[1:]) / (len(weeks) - 1)

        increase_pct = ((current_week - previous_weeks_avg) / previous_weeks_avg * 100) if previous_weeks_avg > 0 else 0

        status = "ok"
        warning = None

        if increase_pct > 15:
            status = "warning"
            warning = f"Aumento de volumen del {increase_pct:.1f}%. Recomendado: máximo 10-15% semanal."
        elif increase_pct < -20:
            status = "low"
            warning = f"Reducción de volumen del {abs(increase_pct):.1f}%. ¿Semana de descarga?"

        return {
            "status": status,
            "current_week_km": current_week,
            "avg_previous_weeks": previous_weeks_avg,
            "increase_percentage": increase_pct,
            "warning": warning
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}
