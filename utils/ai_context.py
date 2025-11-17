# utils/ai_context.py
"""
Sistema de gestió de context i memòria per al chatbot d'IA.
Proporciona context rellevant automàticament a l'iniciar converses.
"""

import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List
from . import ai_functions
from .db_config import get_connection


def generate_initial_context() -> str:
    """
    Genera un context inicial complet per al chatbot a l'iniciar una conversa.

    Returns:
        String amb el context formatat per incloure al system prompt
    """
    context_parts = []

    # 0. Perfil del corredor
    try:
        profile = ai_functions.get_runner_profile()
        if profile.get('has_profile') and profile['profile']:
            p = profile['profile']
            context_parts.append(f"**Perfil del Corredor:**")
            if p.get('name'):
                context_parts.append(f"- Nom: {p['name']}")
            if p.get('current_goal'):
                context_parts.append(f"- Objectiu: {p['current_goal']}")
            if p.get('goal_race_date'):
                from datetime import datetime
                race_date = datetime.fromisoformat(p['goal_race_date'])
                days_to_race = (race_date.date() - datetime.now().date()).days
                if days_to_race > 0:
                    context_parts.append(f"- Data objectiu: {race_date.strftime('%d/%m/%Y')} (en {days_to_race} dies)")
            if p.get('training_philosophy'):
                context_parts.append(f"- Filosofia: {p['training_philosophy']}")

            # PRs
            prs = []
            if p.get('pr_5k'):
                prs.append(f"5K: {p['pr_5k']}")
            if p.get('pr_10k'):
                prs.append(f"10K: {p['pr_10k']}")
            if p.get('pr_half'):
                prs.append(f"Mitja: {p['pr_half']}")
            if prs:
                context_parts.append(f"- PRs: {', '.join(prs)}")
        else:
            context_parts.append("**Perfil:** No configurat (recomana anar a la pàgina de Perfil)")
    except Exception as e:
        context_parts.append(f"(Error carregant perfil: {str(e)})")

    # 1. Resum d'activitat recent
    try:
        recent = ai_functions.get_recent_activities(days=7)
        if recent['count'] > 0:
            context_parts.append(f"**Últims 7 dies:**")
            context_parts.append(f"- {recent['count']} entrenaments realitzats")
            context_parts.append(f"- {recent['total_km']} km totals")
            context_parts.append(f"- Ritme mitjà: {recent['avg_pace']:.2f} min/km")

            # Llistar entrenaments recents
            if recent['activities']:
                context_parts.append("\nEntrenaments recents:")
                for act in recent['activities'][:3]:  # Només els 3 més recents
                    date = pd.to_datetime(act['start_date_local']).strftime('%d/%m')
                    # IMPORTANT: Incloure l'ID perquè el model pugui usar-lo amb get_activity_details
                    context_parts.append(
                        f"  - {date}: {act['name']}, {act['distance_km']:.1f}km, {act['pace_min_km']:.2f} min/km (ID: {act['id']})"
                    )
    except Exception as e:
        context_parts.append(f"(Error carregant activitats recents: {str(e)})")

    # 2. Pla actual
    try:
        plan = ai_functions.get_current_plan()
        if plan['plan']:
            plan_info = plan['plan']
            context_parts.append(f"\n**Pla actiu:**")
            context_parts.append(f"- Setmana inici: {plan_info['week_start_date']}")
            if plan_info['goal']:
                context_parts.append(f"- Objectiu: {plan_info['goal']}")

            # Estat d'entrenaments del pla
            if plan['workouts']:
                completed = sum(1 for w in plan['workouts'] if w['status'] == 'completed')
                pending = sum(1 for w in plan['workouts'] if w['status'] == 'pending')
                context_parts.append(f"- Entrenaments: {completed}/{plan['num_workouts']} completats, {pending} pendents")
        else:
            context_parts.append("\n**Pla actiu:** No hi ha pla actiu actualment")
    except Exception as e:
        context_parts.append(f"(Error carregant pla actual: {str(e)})")

    # 3. Estadístiques de les últimes setmanes
    try:
        stats = ai_functions.get_weekly_stats(weeks=4)
        if stats['total_weeks'] > 0:
            context_parts.append(f"\n**Últimes 4 setmanes:**")
            context_parts.append(f"- Mitjana setmanal: {stats['avg_weekly_km']:.1f} km/setmana")

            # Tendència
            if len(stats['weeks']) >= 2:
                last_week_km = stats['weeks'][0]['total_km']
                prev_week_km = stats['weeks'][1]['total_km']
                if last_week_km > prev_week_km * 1.1:
                    context_parts.append("- Tendència: ⬆️ Volum creixent")
                elif last_week_km < prev_week_km * 0.9:
                    context_parts.append("- Tendència: ⬇️ Volum decreixent")
                else:
                    context_parts.append("- Tendència: ➡️ Volum estable")
    except Exception as e:
        context_parts.append(f"(Error carregant estadístiques: {str(e)})")

    # 4. Notes privades recents de Strava
    try:
        notes_summary = get_recent_private_notes_summary()
        if notes_summary:
            context_parts.append(f"\n**Últimes notes d'entrenaments:**")
            context_parts.append(notes_summary)
    except Exception as e:
        context_parts.append(f"(Error carregant notes: {str(e)})")

    # 5. Anàlisi de rendiment
    try:
        trends = ai_functions.analyze_performance_trends(weeks=4)
        if trends.get('status') != 'insufficient_data' and trends.get('trends'):
            context_parts.append(f"\n**Anàlisi de Rendiment (últimes 4 setmanes):**")
            for trend in trends['trends']:
                context_parts.append(f"  {trend['message']}")
    except Exception as e:
        pass  # No mostrar error si no hi ha suficients dades

    return "\n".join(context_parts)


def get_recent_private_notes_summary(days: int = 7) -> str:
    """
    Obté les notes privades de les activitats recents de Strava.

    Args:
        days: Nombre de dies enrere per cercar notes

    Returns:
        String amb resum de les notes privades o None si no n'hi ha
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
    Crea un resum d'un torn de conversa per guardar context.

    Args:
        messages: Llista de missatges del torn

    Returns:
        String amb resum del torn
    """
    # Per implementació futura: podríem usar Gemini per generar resums
    # Per ara, simplement concatenem els últims missatges
    if not messages:
        return ""

    summary_parts = []
    for msg in messages[-3:]:  # Últims 3 missatges
        role = "Usuari" if msg['role'] == 'user' else "Coach"
        content_preview = msg['content'][:100] + "..." if len(msg['content']) > 100 else msg['content']
        summary_parts.append(f"{role}: {content_preview}")

    return " | ".join(summary_parts)


def get_contextual_greeting() -> str:
    """
    Genera una salutació contextual basada en l'estat actual de l'atleta.

    Returns:
        String amb salutació personalitzada
    """
    greetings = []

    # Verificar última activitat
    try:
        recent = ai_functions.get_recent_activities(days=1)
        if recent['count'] > 0:
            greetings.append("Veig que has entrenat avui! 💪")
        else:
            recent_week = ai_functions.get_recent_activities(days=7)
            if recent_week['count'] == 0:
                greetings.append("Com va tot? Fa uns dies que no et veig entrenar.")
            else:
                greetings.append(f"Hola! Portes {recent_week['count']} entrenaments aquesta setmana.")
    except:
        greetings.append("Hola! En què et puc ajudar avui?")

    # Verificar pla pendent
    try:
        plan = ai_functions.get_current_plan()
        if plan['plan'] and plan['workouts']:
            pending = sum(1 for w in plan['workouts'] if w['status'] == 'pending')
            if pending > 0:
                greetings.append(f"Tens {pending} entrenaments pendents al teu pla.")
    except:
        pass

    return " ".join(greetings) if greetings else "Hola! Estic aquí per ajudar-te amb el teu entrenament."


def save_context_snapshot(summary: str):
    """
    Guarda un snapshot del context a la base de dades.

    Args:
        summary: Resum del context a guardar
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
    Obté informació rellevant d'activitats per planificació.

    Args:
        weeks_back: Setmanes enrere per analitzar

    Returns:
        Diccionari amb mètriques i recomanacions
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

        # Generar recomanació simple
        if analysis['avg_weekly_km'] < 20:
            analysis['recommendation'] = "Volum baix: centra't en construir base aeròbica"
        elif analysis['avg_weekly_km'] < 40:
            analysis['recommendation'] = "Volum moderat: bon moment per afegir qualitat"
        else:
            analysis['recommendation'] = "Volum alt: mantén equilibri entre volum i recuperació"

        return analysis
    except Exception as e:
        return {"error": str(e)}


def check_training_load_progression() -> Dict:
    """
    Analitza la progressió de càrrega d'entrenament per prevenir sobreentrenament.

    Returns:
        Diccionari amb anàlisi de càrrega
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
            warning = f"Augment de volum del {increase_pct:.1f}%. Recomanat: màxim 10-15% setmanal."
        elif increase_pct < -20:
            status = "low"
            warning = f"Reducció de volum del {abs(increase_pct):.1f}%. Setmana de descàrrega?"

        return {
            "status": status,
            "current_week_km": current_week,
            "avg_previous_weeks": previous_weeks_avg,
            "increase_percentage": increase_pct,
            "warning": warning
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}
