# pages/7_🤖_Coach_IA.py
import streamlit as st
import pandas as pd
from datetime import datetime, time, timedelta, timezone
import os
from openai import OpenAI

# Importar nuestras utilidades
from utils.data_processing import load_data
from utils.formatting import format_pace

model = "openai/gpt-oss-120b"
#"openai/gpt-oss-120b", #"mistralai/Mixtral-8x7B-Instruct-v0.1",

# --- Configuración de la Página y Carga de Datos ---
st.set_page_config(layout="wide")
st.title("🤖 Coach con Inteligencia Artificial")
st.markdown("Tu entrenador personal basado en datos y IA. Analiza tu progreso y diseña tu plan de carrera.")

# Usamos st.cache_data para cargar los datos una sola vez por sesión
@st.cache_data
def load_all_data():
    activities, splits = load_data()
    # Asegurarnos de que la fecha es datetime para poder operar
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

def get_llm_response(chat_history):
    if not client: 
        st.error("❌ Cliente de API no inicializado")
        return None
    
    try:
        # Debug: Mostrar info de la request (solo en desarrollo)
        if st.checkbox("🐛 Modo Debug", key="debug_mode"):
            st.json({
                "model": model,
                "messages_count": len(chat_history),
                "last_message": chat_history[-1] if chat_history else None
            })
        
        chat_completion = client.chat.completions.create(
            model=model,
            messages=chat_history,
            temperature=0.5,
            max_tokens=1500
        )
        
        response = chat_completion.choices[0].message.content
        
        # Debug: Verificar respuesta
        if st.session_state.get("debug_mode", False):
            st.text(f"Response length: {len(response) if response else 0}")
        
        return response
        
    except Exception as e:
        st.error(f"❌ Error detallado al contactar con la API: {str(e)}")
        return None

# --- 2. CONSTANTES DE PROMPTS (Sin cambios) ---
SYSTEM_PROMPT = """
Eres "Coach IA", un entrenador de running de élite, científico del deporte y estratega. Tu metodología se basa en los siguientes pilares:
1.  **Periodización Inversa y Polarizada:** Adaptas el plan según el tiempo restante hasta el objetivo. Priorizas la base aeróbica lejos del objetivo y el trabajo de alta intensidad cerca de la competición.
2.  **Análisis Basado en Datos:** Todas tus recomendaciones se fundamentan EXCLUSIVAMENTE en el contexto de datos proporcionado (objetivo, historial, métricas). No inventas información.
3.  **Sostenibilidad y Prevención de Lesiones:** Priorizas la consistencia sobre la intensidad desmedida. Exploras los datos en busca de signos de fatiga o sobreentrenamiento.
4.  **Comunicación Clara y Motivadora:** Eres directo, profesional y didáctico. Explicas el "porqué" de cada entrenamiento (propósito fisiológico) y cómo encaja en el plan general. Utilizas Markdown (títulos, negritas, listas) para estructurar tus respuestas y hacerlas fáciles de leer.
5.  **Enfoque en Ritmos, no solo en Distancias:** Siempre asocias las distancias con ritmos objetivo, zonas de frecuencia cardíaca o esfuerzo percibido (RPE).
"""
PROMPT_ANALISIS_INICIAL = """
Analiza en profundidad el contexto completo que te he proporcionado y presenta tus conclusiones en el siguiente formato estructurado:

1.  **Diagnóstico General:** Basado en la fase de entrenamiento actual (Base, Construcción, Pico, Tapering) y los días restantes, evalúa la viabilidad del objetivo.
2.  **Puntos Fuertes:** Identifica las fortalezas del atleta basándote en su historial (ej. buena base de km, buen ritmo en tiradas largas, consistencia).
3.  **Áreas de Mejora Clave:** Señala las debilidades o áreas prioritarias a trabajar para alcanzar el objetivo (ej. mejorar la resistencia a la velocidad, aumentar el volumen semanal, trabajar la consistencia en los splits).
4.  **Veredicto y Siguientes Pasos:** Ofrece una conclusión (ej. "Vas por excelente camino", "Objetivo ambicioso pero alcanzable con un plan enfocado", "Necesitamos reajustar el plan"). Finaliza abriendo la puerta a preguntas.
"""
PROMPT_PROXIMOS_ENTRENOS = """
Basado en el análisis previo y la fase actual de entrenamiento, diseña los dos (2) entrenamientos clave para la próxima semana.

**REGLAS DE PROGRESIÓN OBLIGATORIAS:**
1.  **Principio de Sobrecarga Progresiva:** La tirada larga de esta semana no debe suponer un salto drástico. Como regla general, no debería aumentar más de un 10-15% sobre la tirada más larga registrada en el historial reciente. La seguridad y la prevención de lesiones son la máxima prioridad.
2.  **Adecuación a la Fase:** El contexto indica que el atleta está en "Fase de Base" (con más de 4 meses para el objetivo). El foco principal es construir una base aeróbica. Por tanto, prioriza la consistencia y el volumen a ritmos cómodos sobre la alta intensidad. Las series o trabajos de velocidad, si se incluyen, deben ser introductorios y muy cortos.
3.  **Realismo:** Las propuestas deben ser seguras y realistas para un atleta amateur que busca una mejora gradual.

Para cada entrenamiento, detalla:
- **Título del Entrenamiento:** (Ej: "Tirada Larga Cómoda", "Fartlek Introductorio")
- **Objetivo Principal:** Explica brevemente el propósito fisiológico en esta fase del plan.
- **Estructura Detallada:** Describe las fases (calentamiento, parte principal, enfriamiento) con distancias y/o duraciones y ritmos/esfuerzos realistas.
- **Justificación de la Progresión:** Explica por qué este nivel de volumen e intensidad es el paso lógico y seguro siguiente para el atleta, conectando directamente con su historial (ej. "Como tu última tirada fue de 14.5km, proponemos una de 16km para seguir la regla del 10-15%...").
"""
PROMPT_OBJETIVO_MENSUAL = """
Teniendo en cuenta el objetivo final y el progreso actual, define un micro-objetivo SMART (Específico, Medible, Alcanzable, Relevante, Temporal) para los próximos 30 días.
El objetivo debe ser un indicador claro de progreso.
Ejemplos: "Ser capaz de correr 10km a un ritmo X:XX/km de forma sostenida", "Alcanzar un volumen semanal de XX km durante al menos dos semanas consecutivas".
Justifica por qué este micro-objetivo es crucial en la fase actual del plan.
"""

# --- 3. FUNCIÓN DE CONTEXTO (Sin cambios) ---
def generar_contexto_experto(goal_info, df_activities, df_splits, num_entrenos=10):
    hoy = datetime.now().date()
    contexto = f"# CONTEXTO DEL ATLETA - Fecha del Análisis: {hoy.strftime('%Y-%m-%d')}\n\n"

    goal_time_seconds = goal_info['time'].hour * 3600 + goal_info['time'].minute * 60 + goal_info['time'].second
    goal_pace_min_km = (goal_time_seconds / 60) / goal_info['dist'] if goal_info['dist'] > 0 else 0
    contexto += "## 1. EL OBJETIVO\n"
    contexto += f"- **Carrera:** {goal_info['name']}\n"
    contexto += f"- **Distancia:** {goal_info['dist']} km\n"
    contexto += f"- **Tiempo Objetivo:** {goal_info['time'].strftime('%H:%M:%S')}\n"
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
        contexto += f"- **Fecha: {entreno['start_date_local'].strftime('%Y-%m-%d')}** | Dist: {entreno['distance_km']:.2f} km | Ritmo: {format_pace(entreno['pace_min_km'])}/km | Desnivel: {entreno['total_elevation_gain']} m\n"
        splits_entreno = df_splits[df_splits['activity_id'] == entreno['id']]
        if not splits_entreno.empty:
            splits_str = ", ".join([f"Km{int(s['split'])}: {format_pace(s['pace_min_km'])}" for _, s in splits_entreno.iterrows()])
            contexto += f"  - `Splits: [{splits_str}]`\n"

    return contexto

# --- 4. LÓGICA DE CÁLCULO DINÁMICO ---
def seconds_to_time(total_seconds):
    if total_seconds < 0: total_seconds = 0
    hours, remainder = divmod(int(total_seconds), 3600)
    minutes, seconds = divmod(remainder, 60)
    return time(hour=min(23, hours), minute=minutes, second=seconds)

def time_to_seconds(time_obj):
    return time_obj.hour * 3600 + time_obj.minute * 60 + time_obj.second

## CORRECCIÓN: Nueva función para convertir segundos a un objeto 'time' que represente el ritmo.
def seconds_to_pace_time(pace_seconds):
    """Convierte segundos de ritmo a un objeto time para el widget (MM:SS)."""
    if pace_seconds < 0: pace_seconds = 0
    # Usamos el campo 'hour' para guardar los minutos y 'minute' para los segundos.
    minutes, seconds = divmod(int(pace_seconds), 60)
    return time(hour=minutes, minute=seconds)

def update_from_time():
    dist = st.session_state.goal_dist
    if dist > 0:
        total_seconds = time_to_seconds(st.session_state.goal_time)
        pace_seconds = total_seconds / dist
        ## CORRECCIÓN: Usar la nueva función para almacenar el ritmo correctamente.
        st.session_state.goal_pace = seconds_to_pace_time(pace_seconds)

def update_from_pace():
    dist = st.session_state.goal_dist
    if dist > 0:
        pace_obj = st.session_state.goal_pace
        ## CORRECCIÓN: Interpretar el input del ritmo correctamente (HH:MM -> MM:SS).
        pace_seconds = pace_obj.hour * 60 + pace_obj.minute
        total_seconds = pace_seconds * dist
        st.session_state.goal_time = seconds_to_time(total_seconds)

# --- 5. INICIALIZACIÓN DEL ESTADO DE SESIÓN ---
# --- 5. INICIALIZACIÓN DEL ESTADO DE SESIÓN ---
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
if "last_analysis_context" not in st.session_state:
    st.session_state.last_analysis_context = ""
# NUEVO: Contexto editable por el usuario
if "editable_context" not in st.session_state:
    st.session_state.editable_context = ""
if "context_auto_generated" not in st.session_state:
    st.session_state.context_auto_generated = True

# --- 6. INTERFAZ DE USUARIO ---
with st.container(border=True):
    st.subheader("Define tu Meta")

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
            ## CORRECCIÓN: Formatear la métrica del ritmo manualmente.
            pace_obj = st.session_state.goal_pace
            pace_display = f"{pace_obj.hour:02d}:{pace_obj.minute:02d}"
            st.metric("Ritmo Calculado", value=f"{pace_display} min/km")
    else: # input_method es "Ritmo"
        with col2:
            # El step de 1 minuto es más usable para el ritmo
            st.time_input("Ritmo objetivo (min/km)", key="goal_pace", on_change=update_from_pace, step=timedelta(minutes=1))
        with col3:
            st.metric("Tiempo Calculado", value=f"{st.session_state.goal_time.strftime('%H:%M:%S')}")

    goal_date = st.date_input("Fecha de la carrera", datetime(2026, 2, 15).date())
    days_left = (goal_date - datetime.now().date()).days
    st.metric(label="⏳ Días hasta el Desafío", value=f"{days_left} días" if days_left >= 0 else "¡Ya pasó!")

# NUEVA SECCIÓN: Contexto Editable
st.subheader("🔧 Contexto para el Coach IA")

# Tabs para organizar mejor
tab1, tab2 = st.tabs(["📊 Contexto Automático", "✏️ Contexto Personalizado"])

with tab1:
    st.markdown("*Este contexto se genera automáticamente basado en tus datos y objetivo:*")
    
    # Generar contexto automático para mostrar
    if st.session_state.goal_dist and st.session_state.goal_time and goal_date:
        goal_info = {
            'name': goal_name,
            'dist': st.session_state.goal_dist,
            'time': st.session_state.goal_time,
            'date': goal_date,
            'days_left': days_left
        }
        auto_context = generar_contexto_experto(goal_info, activities, splits)
        
        # Mostrar en un expander para no ocupar mucho espacio
        with st.expander("Ver contexto automático completo", expanded=False):
            st.code(auto_context, language="markdown")
        
        # Botón para usar el contexto automático
        if st.button("📋 Usar Contexto Automático", type="secondary"):
            st.session_state.editable_context = auto_context
            st.session_state.context_auto_generated = True
            st.success("Contexto automático cargado!")
            st.rerun()

with tab2:
    st.markdown("*Personaliza el contexto que recibirá el Coach IA:*")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Área de texto editable
        edited_context = st.text_area(
            "Contexto personalizado:",
            value=st.session_state.editable_context,
            height=300,
            help="Edita aquí la información que quieres que el Coach IA tenga en cuenta",
            placeholder="Puedes escribir información adicional sobre tu experiencia, lesiones previas, preferencias de entrenamiento, etc."
        )
    
    with col2:
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
                st.session_state.editable_context = generar_contexto_experto(goal_info, activities, splits)
                st.session_state.context_auto_generated = True
                st.success("Contexto regenerado!")
                st.rerun()
        
        if st.button("🗑️ Limpiar", use_container_width=True):
            st.session_state.editable_context = ""
            st.session_state.context_auto_generated = False
            st.success("Contexto limpiado!")
            st.rerun()
    
    # Mostrar estadísticas del contexto
    if st.session_state.editable_context:
        word_count = len(st.session_state.editable_context.split())
        char_count = len(st.session_state.editable_context)
        st.caption(f"📊 Estadísticas: {word_count} palabras, {char_count} caracteres")

# Indicador visual del estado del contexto
if st.session_state.editable_context:
    context_type = "automático" if st.session_state.context_auto_generated else "personalizado"
    st.info(f"✅ Contexto {context_type} cargado y listo para usar", icon="ℹ️")
else:
    st.warning("⚠️ No hay contexto definido. El Coach IA necesita contexto para funcionar correctamente.", icon="⚠️")

# --- 7. LÓGICA DE BOTONES Y CHAT (Sin cambios) ---
if st.button("Generar Análisis del Coach IA", type="primary", use_container_width=True, 
             disabled=(not api_key or not st.session_state.editable_context)):
    
    st.session_state.messages = []
    st.session_state.pop('next_workouts_plan', None)
    st.session_state.pop('monthly_goal_plan', None)

    # Usar el contexto editable en lugar de generar uno nuevo
    contexto_final = st.session_state.editable_context
    st.session_state.last_analysis_context = contexto_final

    st.session_state.messages.append({"role": "system", "content": SYSTEM_PROMPT})
    user_request = f"{PROMPT_ANALISIS_INICIAL}\n\n--- INICIO DEL CONTEXTO ---\n{contexto_final}\n--- FIN DEL CONTEXTO ---"
    st.session_state.messages.append({"role": "user", "content": user_request})

    with st.spinner("Coach IA está analizando tu perfil completo..."):
        response = get_llm_response(st.session_state.messages)
        st.session_state.messages.append({"role": "assistant", "content": response})
    st.rerun()

# --- ACCIONES RÁPIDAS ---
st.subheader("Plan de Acción del Coach")
col1, col2 = st.columns(2)

def handle_action(prompt_template, session_state_key):
    if st.session_state.editable_context:
        action_history = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Este es mi contexto completo:\n{st.session_state.editable_context}"},
            {"role": "user", "content": prompt_template}
        ]
        spinner_message = " ".join(session_state_key.replace('_', ' ').capitalize().split()[:-1])
        with st.spinner(f"Diseñando tu {spinner_message}..."):
            st.session_state[session_state_key] = get_llm_response(action_history)
        st.rerun()

with col1:
    if st.button("Sugerir Próximos Entrenamientos", use_container_width=True, 
                 disabled=(not st.session_state.editable_context)):
        handle_action(PROMPT_PROXIMOS_ENTRENOS, 'next_workouts_plan')

with col2:
    if st.button("Plantear Objetivo Mensual", use_container_width=True, 
                 disabled=(not st.session_state.editable_context)):
        handle_action(PROMPT_OBJETIVO_MENSUAL, 'monthly_goal_plan')

if 'next_workouts_plan' in st.session_state and st.session_state.next_workouts_plan:
    with st.expander("🗓️ Plan de Próximos Entrenamientos Clave", expanded=True):
        st.markdown(st.session_state.next_workouts_plan)
if 'monthly_goal_plan' in st.session_state and st.session_state.monthly_goal_plan:
    with st.expander("🎯 Tu Micro-Objetivo para los Próximos 30 Días", expanded=True):
        st.markdown(st.session_state.monthly_goal_plan)

# --- CHAT ABIERTO ---
st.subheader("Conversa con tu Coach IA")

# Mostrar mensajes del chat (excluyendo el system prompt)
chat_display_messages = [msg for msg in st.session_state.messages if msg['role'] in ['assistant', 'user']]

# Mostrar el primer mensaje del asistente (análisis inicial)
if chat_display_messages:
    # Encontrar el primer mensaje del assistant
    first_assistant_msg = next((msg for msg in chat_display_messages if msg['role'] == 'assistant'), None)
    if first_assistant_msg:
        with st.chat_message("assistant"):
            st.markdown(first_assistant_msg['content'])

    # Mostrar el resto de mensajes (excluyendo el primer assistant message)
    remaining_messages = []
    first_assistant_found = False
    for message in chat_display_messages:
        if message['role'] == 'assistant' and not first_assistant_found:
            first_assistant_found = True
            continue
        elif first_assistant_found or message['role'] == 'user':
            remaining_messages.append(message)
    
    for message in remaining_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# Input del chat - Simplificar la condición
chat_disabled = not api_key or not st.session_state.editable_context or len(st.session_state.messages) < 2

if prompt := st.chat_input("Haz una pregunta de seguimiento...", disabled=chat_disabled):
    # Verificar que tengamos contexto
    if not st.session_state.editable_context:
        st.error("❌ Necesitas definir un contexto antes de hacer preguntas.")
        st.stop()
    
    # Verificar que ya se haya hecho un análisis inicial
    if len(st.session_state.messages) < 2:
        st.error("❌ Primero debes generar un análisis inicial.")
        st.stop()
    
    # Añadir mensaje del usuario
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Mostrar mensaje del usuario inmediatamente
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Generar respuesta del asistente
    with st.chat_message("assistant"):
        with st.spinner("Pensando..."):
            try:
                response = get_llm_response(st.session_state.messages)
                if response and response.strip():  # Verificar que la respuesta no esté vacía
                    st.markdown(response)
                    st.session_state.messages.append({"role": "assistant", "content": response})
                else:
                    error_msg = "❌ No recibí una respuesta válida del Coach IA. Inténtalo de nuevo."
                    st.error(error_msg)
                    # Remover el mensaje del usuario si no hay respuesta
                    st.session_state.messages.pop()
            except Exception as e:
                error_msg = f"❌ Error al obtener respuesta: {str(e)}"
                st.error(error_msg)
                # Remover el mensaje del usuario si hay error
                st.session_state.messages.pop()
    
    st.rerun()

# Mostrar ayuda si el chat está deshabilitado - ESTE BLOQUE VA AQUÍ AL FINAL
if chat_disabled:
    if not api_key:
        st.info("🔑 Configura tu API Key para usar el chat.", icon="ℹ️")
    elif not st.session_state.editable_context:
        st.info("📝 Define un contexto para empezar a chatear.", icon="ℹ️")
    elif len(st.session_state.messages) < 2:
        st.info("🚀 Genera un análisis inicial para empezar a chatear.", icon="ℹ️")