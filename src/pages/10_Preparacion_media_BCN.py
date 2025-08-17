# pages/7_🤖_Coach_IA.py
import streamlit as st
import pandas as pd
from datetime import datetime, date, time, timedelta, timezone
import os
import json
import re
from openai import OpenAI

# Importar nuestras utilidades
from utils.data_processing import load_data
from utils.formatting import format_pace

# --- MODELO LLM ---
model = "openai/gpt-oss-120b"

def _comentarios_de_actividad(row, max_len=220):
    """
    Combina description y private_note, normaliza espacios y trunca para no inflar el prompt.
    """
    partes = []
    for key in ("description", "private_note"):
        val = row.get(key) if hasattr(row, "get") else row[key] if key in row else None
        if val:
            txt = str(val).strip()
            if txt:
                partes.append(txt)
    if not partes:
        return ""
    txt = " | ".join(partes)
    # normaliza saltos de línea/espacios
    txt = re.sub(r"\s+", " ", txt).strip()
    if len(txt) > max_len:
        return txt[:max_len].rstrip() + "…"
    return txt

# --- Configuración de la Página y Carga de Datos ---
st.set_page_config(layout="wide")
st.title("🤖 Coach con Inteligencia Artificial")
st.markdown("Tu entrenador personal basado en datos y IA. Analiza tu progreso y diseña tu plan de carrera.")

# Usamos st.cache_data para cargar los datos una sola vez por sesión
@st.cache_data
def load_all_data():
    activities, splits = load_data()
    activities['start_date_local'] = pd.to_datetime(activities['start_date_local'])
    return activities, splits

activities, splits = load_all_data()

# --- 1. CONFIGURACIÓN DE CONEXIÓN ---
st.sidebar.header("Configuración de Conexión")
cert_path = os.path.expanduser("~/Credentials/rootcaCert.pem")
if os.path.exists(cert_path):
    os.environ["SSL_CERT_FILE"] = cert_path
    os.environ["GRPC_DEFAULT_SSL_ROOTS_FILE_PATH"] = cert_path
    st.sidebar.success("Certificado SSL corporativo cargado.", icon="🛡️")

try:
    api_key = st.secrets["DEEPINFRA_API_KEY"]
    client = OpenAI(api_key=api_key, base_url="https://api.deepinfra.com/v1/openai")
    st.sidebar.success("API Key de DeepInfra cargada.", icon="✅")
except KeyError:
    st.sidebar.error("API Key de DeepInfra no encontrada.", icon="🚨")
    api_key = None
    client = None

# --- 2. LLM: helper ---
def get_llm_response(chat_history):
    if not client:
        st.error("❌ Cliente de API no inicializado")
        return None
    try:
        chat_completion = client.chat.completions.create(
            model=model,
            messages=chat_history,
            temperature=0.5,
            max_tokens=3000
        )
        response = chat_completion.choices[0].message.content
        return response
    except Exception as e:
        st.error(f"❌ Error detallado al contactar con la API: {str(e)}")
        return None

# --- 3. PROMPTS (ajustados a meta fija y 3 sesiones) ---
SYSTEM_PROMPT = """
Eres "Coach IA", un entrenador de running de élite, científico del deporte y estratega.
Pilares:
1) Periodización inversa + polarizada según tiempo restante al objetivo fijo.
2) Todo análisis y recomendación se basan EXCLUSIVAMENTE en los datos y memoria proporcionados.
3) Prioriza sostenibilidad y prevención de lesiones (regla del 10-15%).
4) Comunicación clara y didáctica en Markdown (titulares, listas, negritas).
5) Enfoque en ritmos y zonas (no solo distancias).
6) Restricción: 3 sesiones por semana como norma general salvo contraindicación explícita por datos.
"""

PROMPT_ANALISIS_INICIAL = """
Analiza el paquete de contexto y memoria que te doy y entrega:
1. **Diagnóstico General**: fase (Base/Construcción/Pico/Taper) en función de días restantes; viabilidad del objetivo.
2. **Puntos Fuertes**.
3. **Áreas de Mejora Clave**.
4. **Veredicto y Siguientes Pasos** (claro y accionable).
"""

PROMPT_PROXIMOS_ENTRENOS = """
Diseña TRES (3) entrenamientos clave para la próxima semana, acordes a la fase actual (estamos en Fase de Base si faltan >120 días).
REGLAS:
- Sobrecarga progresiva: la tirada larga no debe subir >10-15% sobre la más larga reciente.
- Base aeróbica: prioriza volumen cómodo; si hay intensidad, que sea muy dosificada e introductoria.
- Realismo para atleta amateur (consistencia > intensidad).
ENTREGA PARA CADA SESIÓN:
- **Título**
- **Objetivo Fisiológico**
- **Estructura Detallada** (calentamiento, parte principal con distancias/tiempos y ritmos RPE/FC/ritmo), enfriamiento.
- **Justificación de la Progresión** enlazando con historial reciente (ej.: última TL de X km → propongo Y km por regla del 10-15%).
"""

PROMPT_OBJETIVO_MENSUAL = """
Propón un micro-objetivo SMART para 30 días que sea un indicador claro de progreso hacia HM en 4:30/km con 3 sesiones/semana.
Ejemplos: volumen semanal sostenido, TL objetivo, bloque continuo a ritmo objetivo, etc.
Justifica brevemente por qué ese objetivo es crítico en esta fase.
"""

# --- 4. META FIJA + utilidades de ritmo/tiempo ---
def seconds_to_time(total_seconds):
    if total_seconds < 0: total_seconds = 0
    hours, remainder = divmod(int(total_seconds), 3600)
    minutes, seconds = divmod(remainder, 60)
    return time(hour=min(23, hours), minute=minutes, second=seconds)

def time_to_seconds(time_obj):
    return time_obj.hour * 3600 + time_obj.minute * 60 + time_obj.second

def seconds_to_pace_time(pace_seconds):
    if pace_seconds < 0: pace_seconds = 0
    minutes, seconds = divmod(int(pace_seconds), 60)
    capped_minutes = min(minutes, 23)
    
    return time(hour=capped_minutes, minute=seconds)

def update_from_time():
    dist = st.session_state.goal_dist
    if dist > 0:
        total_seconds = time_to_seconds(st.session_state.goal_time)
        pace_seconds = total_seconds / dist
        st.session_state.goal_pace = seconds_to_pace_time(pace_seconds)

def update_from_pace():
    dist = st.session_state.goal_dist
    if dist > 0:
        pace_obj = st.session_state.goal_pace
        pace_seconds = pace_obj.hour * 60 + pace_obj.minute
        total_seconds = pace_seconds * dist
        st.session_state.goal_time = seconds_to_time(total_seconds)

# --- 5. ESTADO DE SESIÓN (añadimos memoria y perfil fijo) ---
if 'goal_dist' not in st.session_state:
    st.session_state.goal_dist = 21.1
if 'goal_time' not in st.session_state:
    st.session_state.goal_time = time(1, 34, 56)
if 'goal_pace' not in st.session_state:
    pace_seconds = time_to_seconds(st.session_state.goal_time) / st.session_state.goal_dist
    st.session_state.goal_pace = seconds_to_pace_time(pace_seconds)
if 'input_method' not in st.session_state:
    st.session_state.input_method = "Ritmo"
if "messages" not in st.session_state:
    st.session_state.messages = []
if "editable_context" not in st.session_state:
    st.session_state.editable_context = ""
if "context_auto_generated" not in st.session_state:
    st.session_state.context_auto_generated = True

# >>> NUEVO: Perfil fijo y memoria
if "fixed_profile" not in st.session_state:
    st.session_state.fixed_profile = {
        "runner_since": "Principios de 2025",
        "sessions_per_week": 3,
        "race_name": "Media Maratón de Barcelona",
        "race_date": date(2026, 2, 15).isoformat(),
        "target_pace_str": "04:30",
    }
if "memory_log" not in st.session_state:
    st.session_state.memory_log = []  # lista de dicts: {ts, type, content}
if "last_llm_payload" not in st.session_state:
    st.session_state.last_llm_payload = ""  # para previsualizar exactamente lo que vio el LLM

# --- 6. MÉTRICAS/KPIs simples de progreso (últ. 4 semanas) ---
def compute_recent_kpis(df_activities: pd.DataFrame):
    # Alinear zonas horarias para la comparación
    col = df_activities['start_date_local']
    tz = getattr(col.dt, 'tz', None)                 # None si es naive, tzinfo si es aware
    now = pd.Timestamp.now(tz=tz)                    # now naive o aware a juego con la serie
    four_weeks_ago = now - pd.Timedelta(weeks=4)

    recent = df_activities[col >= four_weeks_ago]

    kpis = {
        "avg_weekly_km": 0.0,
        "avg_sessions_per_week": 0.0,
        "longest_run_km_all_time": float(df_activities['distance_km'].max()) if not df_activities.empty else 0.0,
        "longest_run_km_recent": 0.0,
        "best_perf_over_10k": None,
    }

    if not recent.empty:
        tmp = recent.copy()
        iso = tmp['start_date_local'].dt.isocalendar()
        tmp['iso_year'] = iso.year
        tmp['iso_week'] = iso.week
        weekly_km = tmp.groupby(['iso_year', 'iso_week'])['distance_km'].sum()
        weekly_sessions = tmp.groupby(['iso_year', 'iso_week']).size()
        if len(weekly_km) > 0:
            kpis["avg_weekly_km"] = float(weekly_km.mean())
        if len(weekly_sessions) > 0:
            kpis["avg_sessions_per_week"] = float(weekly_sessions.mean())
        kpis["longest_run_km_recent"] = float(recent['distance_km'].max())

    long_runs_df = df_activities[df_activities['distance_km'] > 10]
    if not long_runs_df.empty:
        best_row = long_runs_df.loc[long_runs_df['pace_min_km'].idxmin()]
        kpis["best_perf_over_10k"] = (float(best_row['distance_km']), float(best_row['pace_min_km']))

    return kpis

def kpis_markdown(k):
    lines = []
    lines.append(f"- **Volumen semanal promedio (4s):** {k['avg_weekly_km']:.1f} km/semana")
    lines.append(f"- **Sesiones promedio (4s):** {k['avg_sessions_per_week']:.1f} /semana")
    lines.append(f"- **Tirada más larga (histórico):** {k['longest_run_km_all_time']:.1f} km")
    lines.append(f"- **Tirada más larga (4s):** {k['longest_run_km_recent']:.1f} km")
    if k['best_perf_over_10k']:
        dist, pace = k['best_perf_over_10k']
        lines.append(f"- **Mejor rendimiento (>10k):** {dist:.1f} km a {format_pace(pace)}/km")
    else:
        lines.append("- **Mejor rendimiento (>10k):** sin datos suficientes")
    return "\n".join(lines)

# --- 7. CONTEXTO EXPERTO (CAMBIADO: ahora toma las últimas 20 carreras) ---
def generar_contexto_experto(goal_info, df_activities, df_splits, num_entrenos=20):
    hoy = datetime.now().date()
    contexto = f"# CONTEXTO DEL ATLETA - Fecha del Análisis: {hoy.strftime('%Y-%m-%d')}\n\n"

    goal_time_seconds = goal_info['time'].hour * 3600 + goal_info['time'].minute * 60 + goal_info['time'].second
    goal_pace_min_km = (goal_time_seconds / 60) / goal_info['dist'] if goal_info['dist'] > 0 else 0
    contexto += "## 1. EL OBJETIVO\n"
    contexto += f"- **Carrera:** {goal_info['name']}\n"
    contexto += f"- **Distancia:** {goal_info['dist']} km\n"
    contexto += f"- **Tiempo Objetivo:** {goal_info['time'].strftime('%H:%M:%S')}\n"
    contexto += f"- **Fecha Objetivo:** {goal_info['date'].strftime('%Y-%m-%d')}\n"
    contexto += f"- **Ritmo Requerido:** {format_pace(goal_pace_min_km)} /km\n"
    contexto += f"- **Días Restantes:** {goal_info['days_left']} días\n\n"

    if df_activities.empty:
        contexto += "## 2. SITUACIÓN ACTUAL\n"
        contexto += "**Alerta:** No hay datos de entrenamiento disponibles para analizar.\n"
        return contexto

    contexto += "## 2. SITUACIÓN ACTUAL\n"
    if goal_info['days_left'] > 120: fase = "Fase de Base (más de 4 meses)"
    elif 60 < goal_info['days_left'] <= 120: fase = "Fase de Construcción (2-4 meses)"
    elif 14 < goal_info['days_left'] <= 60: fase = "Fase de Pico (1-2 meses)"
    else: fase = "Fase de Tapering/Competición (últimas 2 semanas)"
    contexto += f"- **Fase de Entrenamiento Actual:** {fase}\n\n"

    contexto += "### Resumen de Carga (Últimas 4 Semanas)\n"
    four_weeks_ago = datetime.now(timezone.utc) - timedelta(weeks=4)
    recent_activities = df_activities[df_activities['start_date_local'] >= four_weeks_ago]
    if not recent_activities.empty:
        total_dist_4_weeks = recent_activities['distance_km'].sum()
        num_entrenos_4_weeks = len(recent_activities)
        avg_weekly_dist = total_dist_4_weeks / 4
        contexto += f"- **Volumen Semanal Promedio:** {avg_weekly_dist:.2f} km/semana\n"
        contexto += f"- **Entrenamientos por Semana (promedio):** {num_entrenos_4_weeks / 4:.1f}\n\n"
    else:
        contexto += "- No se han registrado entrenamientos en las últimas 4 semanas.\n\n"

    contexto += "### Hitos Históricos y Mejor Rendimiento\n"
    all_time_longest_run = df_activities['distance_km'].max()
    long_runs_df = df_activities[df_activities['distance_km'] > 10]
    best_perf_run = long_runs_df.loc[long_runs_df['pace_min_km'].idxmin()] if not long_runs_df.empty else None
    contexto += f"- **Tirada más larga registrada:** {all_time_longest_run:.2f} km.\n"
    if best_perf_run is not None:
        contexto += f"- **Mejor rendimiento (>10k):** Carrera de {best_perf_run['distance_km']:.2f} km a un ritmo de {format_pace(best_perf_run['pace_min_km'])}/km.\n\n"
    else:
        contexto += "- Sin registros de carreras de más de 10km para determinar el mejor rendimiento.\n\n"

    contexto += f"## 3. HISTORIAL DETALLADO DE LOS ÚLTIMOS {num_entrenos} ENTRENAMIENTOS\n"
    df_activities_sorted = df_activities.sort_values(by='start_date_local', ascending=False)
    for _, entreno in df_activities_sorted.head(num_entrenos).iterrows():
        fecha = entreno['start_date_local'].strftime('%Y-%m-%d')
        dist_km = entreno['distance_km']
        ritmo = format_pace(entreno['pace_min_km'])
        desnivel_m = entreno.get('total_elevation_gain', None)
        desnivel_txt = f"{desnivel_m:.0f} m" if pd.notnull(desnivel_m) else "–"
        fc = entreno.get('average_heartrate', None)
        fc_txt = f"{fc:.0f} ppm" if pd.notnull(fc) else "–"

        contexto += f"- **Fecha: {fecha}** | Dist: {dist_km:.2f} km | Ritmo: {ritmo}/km | FC media: {fc_txt} | Desnivel: {desnivel_txt}\n"

        comentario = _comentarios_de_actividad(entreno)
        if comentario:
            contexto += f"  - Comentarios: {comentario}\n"

        splits_entreno = df_splits[df_splits['activity_id'] == entreno['id']]
        if not splits_entreno.empty:
            splits_str = ", ".join([f"Km{int(s['split'])}: {format_pace(s['pace_min_km'])}" for _, s in splits_entreno.iterrows()])
            contexto += f"  - `Splits: [{splits_str}]`\n"

    return contexto

# --- 8. Funciones de memoria visible ---
def static_memory_block():
    fp = st.session_state.fixed_profile
    return (
        "## MEMORIA FIJA\n"
        f"- Inicio en running: {fp['runner_since']}\n"
        f"- Frecuencia preferida: {fp['sessions_per_week']} sesiones/semana\n"
        f"- Objetivo: {fp['race_name']} ({fp['race_date']}) a {fp['target_pace_str']}/km\n"
        "- Regla de seguridad: progresión 10-15% en TL\n"
    )

def session_memory_block(max_items=5):
    # últimas N interacciones resumidas (solo cabecera)
    lines = ["## MEMORIA DE SESIÓN (resumen últimas interacciones)"]
    if not st.session_state.memory_log:
        lines.append("- (vacío)")
    else:
        for item in st.session_state.memory_log[-max_items:]:
            ts = item["ts"]
            kind = item["type"]
            content = item["content"].strip().replace("\n", " ")
            if len(content) > 160: content = content[:160] + "..."
            lines.append(f"- [{ts}] {kind}: {content}")
    return "\n".join(lines)

def build_llm_payload(system_prompt: str, user_instructions: str, auto_context_md: str, kpis_md: str):
    mem_fija = static_memory_block()
    mem_sesion = session_memory_block()
    payload_user = (
        f"{user_instructions}\n\n"
        "--- MEMORIA FIJA ---\n"
        f"{mem_fija}\n"
        "--- CONTEXTO (DATOS) ---\n"
        f"{auto_context_md}\n"
        "--- KPIs (4 semanas) ---\n"
        f"{kpis_md}\n"
        "--- MEMORIA DE SESIÓN ---\n"
        f"{mem_sesion}\n"
        "--- FIN DEL PAQUETE ---"
    )
    
    # NUEVA VERIFICACIÓN: controlar longitud del contexto
    payload_length = len(payload_user.split())
    if payload_length > 4000:  # Si el contexto es muy largo
        st.warning(f"⚠️ Contexto muy extenso ({payload_length} palabras). La respuesta podría cortarse.")
    
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": payload_user}
    ], payload_user
    
def generar_contexto_experto_adaptativo(goal_info, df_activities, df_splits, max_words=3500):
    """
    Genera contexto adaptativo que se ajusta para no exceder un límite de palabras
    """
    # Empezamos con la info básica
    hoy = datetime.now().date()
    contexto = f"# CONTEXTO DEL ATLETA - Fecha del Análisis: {hoy.strftime('%Y-%m-%d')}\n\n"

    goal_time_seconds = goal_info['time'].hour * 3600 + goal_info['time'].minute * 60 + goal_info['time'].second
    goal_pace_min_km = (goal_time_seconds / 60) / goal_info['dist'] if goal_info['dist'] > 0 else 0
    contexto += "## 1. EL OBJETIVO\n"
    contexto += f"- **Carrera:** {goal_info['name']}\n"
    contexto += f"- **Distancia:** {goal_info['dist']} km\n"
    contexto += f"- **Tiempo Objetivo:** {goal_info['time'].strftime('%H:%M:%S')}\n"
    contexto += f"- **Fecha Objetivo:** {goal_info['date'].strftime('%Y-%m-%d')}\n"
    contexto += f"- **Ritmo Requerido:** {format_pace(goal_pace_min_km)} /km\n"
    contexto += f"- **Días Restantes:** {goal_info['days_left']} días\n\n"

    if df_activities.empty:
        contexto += "## 2. SITUACIÓN ACTUAL\n"
        contexto += "**Alerta:** No hay datos de entrenamiento disponibles para analizar.\n"
        return contexto

    # Añadir situación actual y KPIs
    contexto += "## 2. SITUACIÓN ACTUAL\n"
    if goal_info['days_left'] > 120: fase = "Fase de Base (más de 4 meses)"
    elif 60 < goal_info['days_left'] <= 120: fase = "Fase de Construcción (2-4 meses)"
    elif 14 < goal_info['days_left'] <= 60: fase = "Fase de Pico (1-2 meses)"
    else: fase = "Fase de Tapering/Competición (últimas 2 semanas)"
    contexto += f"- **Fase de Entrenamiento Actual:** {fase}\n\n"

    # Resumen de carga
    contexto += "### Resumen de Carga (Últimas 4 Semanas)\n"
    four_weeks_ago = datetime.now(timezone.utc) - timedelta(weeks=4)
    recent_activities = df_activities[df_activities['start_date_local'] >= four_weeks_ago]
    if not recent_activities.empty:
        total_dist_4_weeks = recent_activities['distance_km'].sum()
        num_entrenos_4_weeks = len(recent_activities)
        avg_weekly_dist = total_dist_4_weeks / 4
        contexto += f"- **Volumen Semanal Promedio:** {avg_weekly_dist:.2f} km/semana\n"
        contexto += f"- **Entrenamientos por Semana (promedio):** {num_entrenos_4_weeks / 4:.1f}\n\n"

    # Hitos históricos
    contexto += "### Hitos Históricos y Mejor Rendimiento\n"
    all_time_longest_run = df_activities['distance_km'].max()
    long_runs_df = df_activities[df_activities['distance_km'] > 10]
    best_perf_run = long_runs_df.loc[long_runs_df['pace_min_km'].idxmin()] if not long_runs_df.empty else None
    contexto += f"- **Tirada más larga registrada:** {all_time_longest_run:.2f} km.\n"
    if best_perf_run is not None:
        contexto += f"- **Mejor rendimiento (>10k):** {best_perf_run['distance_km']:.2f} km a {format_pace(best_perf_run['pace_min_km'])}/km.\n\n"

    # Añadir entrenamientos de forma adaptativa
    current_word_count = len(contexto.split())
    words_remaining = max_words - current_word_count - 200  # Buffer de 200 palabras
    
    # Estimamos ~30 palabras por entrenamiento
    max_entrenamientos = min(20, max(5, words_remaining // 30))
    
    contexto += f"## 3. HISTORIAL DETALLADO DE LOS ÚLTIMOS {max_entrenamientos} ENTRENAMIENTOS\n"
    df_activities_sorted = df_activities.sort_values(by='start_date_local', ascending=False)
    
    for _, entreno in df_activities_sorted.head(max_entrenamientos).iterrows():
        fecha = entreno['start_date_local'].strftime('%Y-%m-%d')
        dist_km = entreno['distance_km']
        ritmo = format_pace(entreno['pace_min_km'])
        desnivel_m = entreno.get('total_elevation_gain', None)
        desnivel_txt = f"{desnivel_m:.0f} m" if pd.notnull(desnivel_m) else "–"
        fc = entreno.get('average_heartrate', None)
        fc_txt = f"{fc:.0f} ppm" if pd.notnull(fc) else "–"

        contexto += f"- **{fecha}** | {dist_km:.2f} km | {ritmo}/km | FC: {fc_txt} | Desnivel: {desnivel_txt}\n"

        # Solo añadir comentarios si el contexto no es demasiado largo
        if len(contexto.split()) < max_words - 100:
            comentario = _comentarios_de_actividad(entreno, max_len=120)  # Reducimos comentarios
            if comentario:
                contexto += f"  - {comentario}\n"

    return contexto

def append_memory(kind: str, content: str):
    st.session_state.memory_log.append({
        "ts": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "type": kind,
        "content": content or ""
    })

# --- 9. FUNCIÓN PARA OBTENER CONTEXTO COMPLETO SIEMPRE ---
def get_current_context(goal_name, goal_date, days_left):
    """Genera el contexto completo que siempre se pasará al LLM"""
    goal_info = {
        'name': goal_name,
        'dist': st.session_state.goal_dist,
        'time': st.session_state.goal_time,
        'date': goal_date,
        'days_left': days_left
    }
    
    if st.session_state.editable_context:
        return st.session_state.editable_context
    else:
        return generar_contexto_experto_adaptativo(goal_info, activities, splits, max_words=3500)


# --- 10. UI: META FIJA + CONTEXTO + MEMORIA ---
# Dos columnas: principal y memoria visible
main_col, mem_col = st.columns([2.2, 1.0])

with main_col:
    with st.container(border=True):
        st.subheader("Define tu Meta (fija por defecto)")

        goal_name = st.text_input("Nombre de la carrera objetivo", "Media Maratón de Barcelona")

        st.radio(
            "¿Cómo quieres definir tu objetivo?",
            ["Tiempo", "Ritmo"],
            key="input_method",
            horizontal=True,
        )

        col1, col2, col3 = st.columns(3)

        with col1:
            st.number_input(
                "Distancia (km)", min_value=0.1, step=1.0, format="%.2f", key="goal_dist",
                on_change=update_from_time if st.session_state.input_method == "Tiempo" else update_from_pace,
            )

        if st.session_state.input_method == "Tiempo":
            with col2:
                st.time_input("Tiempo objetivo", key="goal_time", on_change=update_from_time)
            with col3:
                pace_obj = st.session_state.goal_pace
                pace_display = f"{pace_obj.hour:02d}:{pace_obj.minute:02d}"
                st.metric("Ritmo Calculado", value=f"{pace_display} min/km")
        else:
            with col2:
                st.time_input("Ritmo objetivo (min/km)", key="goal_pace", on_change=update_from_pace, step=timedelta(minutes=1))
            with col3:
                st.metric("Tiempo Calculado", value=f"{st.session_state.goal_time.strftime('%H:%M:%S')}")

        goal_date = st.date_input("Fecha de la carrera", datetime(2026, 2, 15).date())
        days_left = (goal_date - datetime.now().date()).days
        st.metric(label="⏳ Días hasta el Desafío", value=f"{days_left} días" if days_left >= 0 else "¡Ya pasó!")

    # CONTEXTO AUTOMÁTICO / PERSONALIZADO (sin cambios significativos)
    st.subheader("Contexto para el Coach IA")
    tab1, tab2 = st.tabs(["📊 Contexto Automático", "✏️ Contexto Personalizado"])

    with tab1:
        st.markdown("*Este contexto se genera automáticamente basado en tus datos y objetivo (últimas 20 carreras):*")
        if st.session_state.goal_dist and st.session_state.goal_time and goal_date:
            goal_info = {
                'name': goal_name,
                'dist': st.session_state.goal_dist,
                'time': st.session_state.goal_time,
                'date': goal_date,
                'days_left': days_left
            }
            auto_context = generar_contexto_experto(goal_info, activities, splits, num_entrenos=20)
            with st.expander("Ver contexto automático completo", expanded=False):
                st.code(auto_context, language="markdown")
            if st.button("📋 Usar Contexto Automático", type="secondary"):
                st.session_state.editable_context = auto_context
                st.session_state.context_auto_generated = True
                st.success("Contexto automático cargado!")
                st.rerun()

    with tab2:
        st.markdown("*Personaliza el contexto que recibirá el Coach IA:*")
        colA, colB = st.columns([3, 1])
        with colA:
            edited_context = st.text_area(
                "Contexto personalizado:",
                value=st.session_state.editable_context,
                height=300,
                help="Edita la información que el Coach IA debe tener en cuenta",
                placeholder="Añade experiencia, lesiones, preferencias, etc."
            )
        with colB:
            st.markdown("**Acciones rápidas:**")
            if st.button("💾 Guardar cambios", use_container_width=True):
                st.session_state.editable_context = edited_context
                st.session_state.context_auto_generated = False
                st.success("Contexto guardado!")
                st.rerun()
            if st.button("🔄 Generar automático", use_container_width=True):
                if st.session_state.goal_dist and st.session_state.goal_time and goal_date:
                    goal_info = {
                        'name': goal_name,
                        'dist': st.session_state.goal_dist,
                        'time': st.session_state.goal_time,
                        'date': goal_date,
                        'days_left': days_left
                    }
                    st.session_state.editable_context = generar_contexto_experto(goal_info, activities, splits, num_entrenos=20)
                    st.session_state.context_auto_generated = True
                    st.success("Contexto regenerado!")
                    st.rerun()
            if st.button("🗑️ Limpiar", use_container_width=True):
                st.session_state.editable_context = ""
                st.session_state.context_auto_generated = False
                st.success("Contexto limpiado!")
                st.rerun()

        if st.session_state.editable_context:
            word_count = len(st.session_state.editable_context.split())
            char_count = len(st.session_state.editable_context)
            st.caption(f"📊 Estadísticas: {word_count} palabras, {char_count} caracteres")

    # --- ACCIONES: Análisis / Próximos entrenos (3) / Objetivo mensual ---
    st.subheader("Plan de Acción del Coach")
    col1, col2 = st.columns(2)

    def handle_action(prompt_template, session_state_key, action_name):
        kpis = compute_recent_kpis(activities)
        kpis_md = kpis_markdown(kpis)
        auto_context_md = get_current_context(goal_name, goal_date, days_left)
        messages, user_payload = build_llm_payload(SYSTEM_PROMPT, prompt_template, auto_context_md, kpis_md)

        spinner_message = action_name
        with st.spinner(f"{spinner_message}..."):
            response = get_llm_response(messages)

        if response:
            st.session_state[session_state_key] = response
            st.session_state.last_llm_payload = f"### SYSTEM\n{SYSTEM_PROMPT}\n\n### USER\n{user_payload}"
            append_memory(action_name, response)
            st.rerun()

    with col1:
        if st.button("Sugerir Próximos Entrenamientos (3)", use_container_width=True, disabled=(not api_key)):
            handle_action(PROMPT_PROXIMOS_ENTRENOS, 'next_workouts_plan', "Próximos Entrenamientos")

    with col2:
        if st.button("Plantear Objetivo Mensual", use_container_width=True, disabled=(not api_key)):
            handle_action(PROMPT_OBJETIVO_MENSUAL, 'monthly_goal_plan', "Objetivo Mensual")

    # Botón de Análisis integral
    if st.button("Generar Análisis del Coach IA", type="primary", use_container_width=True, disabled=(not api_key)):
        kpis = compute_recent_kpis(activities)
        kpis_md = kpis_markdown(kpis)
        auto_context_md = get_current_context(goal_name, goal_date, days_left)
        
        messages_for_llm, user_payload = build_llm_payload(SYSTEM_PROMPT, PROMPT_ANALISIS_INICIAL, auto_context_md, kpis_md)

        with st.spinner("Coach IA está analizando tu perfil completo..."):
            response = get_llm_response(messages_for_llm)
            
            if response:
                st.session_state.messages = [
                    {"role": "user", "content": "Genera un análisis inicial de mi perfil de corredor."},
                    {"role": "assistant", "content": response}
                ]
                st.session_state.last_llm_payload = f"### SYSTEM\n{SYSTEM_PROMPT}\n\n### USER\n{user_payload}"
                append_memory("Análisis", response)
            else:
                st.error("No se pudo obtener una respuesta del análisis.")

        st.rerun()

    # Outputs
    if 'next_workouts_plan' in st.session_state and st.session_state.next_workouts_plan:
        with st.expander("🗓️ Plan de Próximos Entrenamientos (3)", expanded=True):
            st.markdown(st.session_state.next_workouts_plan)
    if 'monthly_goal_plan' in st.session_state and st.session_state.monthly_goal_plan:
        with st.expander("🎯 Micro-Objetivo para los Próximos 30 Días", expanded=True):
            st.markdown(st.session_state.monthly_goal_plan)

    # --- CHAT ABIERTO (ALTERNATIVA con st.chat_input nativo) ---
    st.subheader("Conversa con tu Coach IA")

    # Contenedor para el chat que se actualiza
    chat_container = st.container()
    
    with chat_container:
        # 1. Mostrar historial de chat
        for message in st.session_state.messages:
            if message["role"] in ["user", "assistant"]:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

    # 2. Chat input al final (fuera del contenedor)
    chat_disabled = not api_key
    
    if prompt := st.chat_input("Haz una pregunta al Coach IA...", disabled=chat_disabled):
        # Solo validamos que tengamos API key
        if not api_key:
            st.error("❌ Necesitas configurar tu API Key para hacer preguntas.")
            st.stop()

        # Añadimos el mensaje del usuario al historial
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Construimos el paquete completo para la API
        kpis = compute_recent_kpis(activities)
        kpis_md = kpis_markdown(kpis)
        auto_context_md = get_current_context(goal_name, goal_date, days_left)
        
        messages_for_llm, user_payload = build_llm_payload(SYSTEM_PROMPT, prompt, auto_context_md, kpis_md)
        st.session_state.last_llm_payload = f"### SYSTEM\n{SYSTEM_PROMPT}\n\n### USER\n{user_payload}"

        # Llamamos a la API
        with st.spinner("Pensando..."):
            try:
                response = get_llm_response(messages_for_llm)
                if response and response.strip():
                    # Añadimos la respuesta al historial
                    st.session_state.messages.append({"role": "assistant", "content": response})
                    append_memory("Chat", f"Q: {prompt}\nA: {response}")
                    # Rerun para mostrar la nueva respuesta
                    st.rerun()
                else:
                    st.error("❌ No recibí una respuesta válida del Coach IA. Inténtalo de nuevo.")
            except Exception as e:
                st.error(f"❌ Error al obtener respuesta: {str(e)}")

    # Mensaje de ayuda si el chat está deshabilitado
    if chat_disabled:
        if not api_key:
            st.info("🔑 Configura tu API Key para usar el chat.", icon="ℹ️")
        else:
            st.info("💬 Ya puedes empezar a chatear directamente con tu Coach IA.", icon="ℹ️")

# --- Panel derecho: Memoria, KPIs y depuración del prompt ---
# OJO: no hace falta 'with mem_col'; llamar a mem_col.xxx es suficiente.
mem_col.subheader("Memoria y Perfil")

# Perfil fijo
with mem_col.container(border=True):
    mem_col.markdown(static_memory_block())

# KPIs recientes
k = compute_recent_kpis(activities)
with mem_col.container(border=True):
    mem_col.subheader("KPIs (últimas 4 semanas)")
    mem_col.markdown(kpis_markdown(k))

# Memoria de sesión
with mem_col.container(border=True):
    mem_col.subheader("Memoria de sesión")
    mem_col.markdown(session_memory_block())

# Contexto efectivo que verá el LLM ahora mismo
ctx = get_current_context(goal_name, goal_date, days_left)
with mem_col.expander("Contexto efectivo enviado al LLM", expanded=False):
    mem_col.code(ctx, language="markdown")

# Último payload exacto (SYSTEM + USER) que recibió el LLM
if st.session_state.get("last_llm_payload"):
    with mem_col.expander("Último paquete enviado al LLM", expanded=False):
        mem_col.code(st.session_state.last_llm_payload, language="markdown")