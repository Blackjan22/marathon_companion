# pages/7_🤖_Coach_IA.py
import streamlit as st
import pandas as pd
from datetime import datetime, time
import os
from openai import OpenAI

# Importar nuestras utilidades
from utils.data_processing import load_data
from utils.formatting import format_pace

# --- Configuración de la Página y Carga de Datos ---
st.set_page_config(layout="wide")
st.title("🤖 Coach con Inteligencia Artificial")
st.markdown("Tu entrenador personal basado en datos y IA, potenciado por Llama 3.1 vía DeepInfra.")

# Usamos st.cache_data para cargar los datos una sola vez por sesión
@st.cache_data
def load_all_data():
    return load_data()

activities, splits = load_all_data()

# --- 1. CONFIGURACIÓN DE CONEXIÓN (Sin cambios) ---
st.sidebar.header("Configuración de Conexión")
# (El código para el certificado y la API key se mantiene igual)
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
    if not client: return None
    try:
        chat_completion = client.chat.completions.create(model="meta-llama/Meta-Llama-3.1-8B-Instruct", messages=chat_history)
        return chat_completion.choices[0].message.content
    except Exception as e:
        st.error(f"Error al contactar con la API: {e}")
        return None

# --- FUNCIÓN DE CONTEXTO MEJORADA ---
def generar_contexto_completo(goal_info, df_activities, df_splits, num_entrenos=10):
    contexto = ""
    # 1. Objetivo del Atleta
    goal_time_seconds = goal_info['time'].hour * 3600 + goal_info['time'].minute * 60 + goal_info['time'].second
    goal_pace_min_km = (goal_time_seconds / 60) / goal_info['dist']
    contexto += f"OBJETIVO DEL ATLETA:\n"
    contexto += f"- Carrera: {goal_info['name']}\n- Distancia: {goal_info['dist']} km\n- Tiempo Objetivo: {goal_info['time'].strftime('%H:%M:%S')}\n- Ritmo Requerido: {format_pace(goal_pace_min_km)} /km\n- Días Restantes: {goal_info['days_left']} días\n\n"
    
    if df_activities.empty:
        contexto += "No hay datos de entrenamiento disponibles."
        return contexto

    # 2. Métricas Clave del Historial Completo
    all_time_longest_run = df_activities['distance_km'].max()
    long_runs_df = df_activities[df_activities['distance_km'] > 10]
    best_perf_run = long_runs_df.loc[long_runs_df['pace_min_km'].idxmin()] if not long_runs_df.empty else None
    
    contexto += "MÉTRICAS CLAVE HISTÓRICAS:\n"
    contexto += f"- Tirada más larga jamás registrada: {all_time_longest_run:.2f} km.\n"
    if best_perf_run is not None:
        contexto += f"- Mejor rendimiento (distancia/ritmo): carrera de {best_perf_run['distance_km']:.2f} km a un ritmo de {format_pace(best_perf_run['pace_min_km'])}/km.\n\n"
    else:
        contexto += "- No hay carreras de más de 10km para determinar el mejor rendimiento.\n\n"

    # 3. Historial de los últimos entrenamientos con splits
    contexto += f"HISTORIAL DE LOS ÚLTIMOS {num_entrenos} ENTRENAMIENTOS:\n"
    for index, entreno in df_activities.head(num_entrenos).iterrows():
        contexto += f"\n- Fecha: {entreno['start_date_local'].strftime('%Y-%m-%d')}, Dist: {entreno['distance_km']:.2f} km, Ritmo: {format_pace(entreno['pace_min_km'])}/km\n"
        splits_entreno = df_splits[df_splits['activity_id'] == entreno['id']]
        if not splits_entreno.empty:
            splits_str = ", ".join([f"Km{int(s['split'])}: {format_pace(s['pace_min_km'])}" for _, s in splits_entreno.iterrows()])
            contexto += f"  - Splits: [{splits_str}]\n"
            
    return contexto

# --- Interfaz de Usuario ---
with st.container(border=True):
    st.subheader("Define tu Meta")
    col1, col2, col3 = st.columns(3)
    with col1:
        goal_name = st.text_input("Nombre del objetivo", "Media Maratón", key="goal_name")
        goal_dist = st.number_input("Distancia (km)", min_value=0.1, value=21.1, step=0.1, format="%.2f", key="goal_dist")
    with col2:
        default_date = datetime.now().date() + pd.DateOffset(months=6)
        goal_date = st.date_input("Fecha de la carrera", default_date, key="goal_date")
        default_time = time(1, 34, 56)
        goal_time = st.time_input("Tiempo objetivo", default_time, key="goal_time")
    with col3:
        days_left = (goal_date - datetime.now().date()).days
        st.metric(label="⏳ Días hasta el Desafío", value=days_left if days_left >= 0 else "¡Ya pasó!")

# --- Inicialización del Estado ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "last_analysis_context" not in st.session_state:
    st.session_state.last_analysis_context = ""

# Botón principal para generar el análisis base
if st.button("Generar Análisis del Coach IA", type="primary", disabled=(not api_key)):
    st.session_state.messages = [] # Reiniciar chat
    st.session_state.pop('next_workouts_plan', None) # Borrar planes anteriores
    st.session_state.pop('monthly_goal_plan', None)
    
    goal_info = {'name': goal_name, 'dist': goal_dist, 'time': goal_time, 'date': goal_date, 'days_left': days_left}
    contexto = generar_contexto_completo(goal_info, activities, splits)
    st.session_state.last_analysis_context = contexto # Guardamos el contexto para usarlo en las acciones rápidas
    
    system_prompt = "Actúa como 'Coach AI', un entrenador de running de élite, positivo y experto. Analiza el contexto proporcionado y da un análisis inicial con puntos fuertes, áreas de mejora y un plan de acción. Luego, responde a las preguntas de seguimiento del usuario."
    st.session_state.messages.append({"role": "system", "content": system_prompt})
    st.session_state.messages.append({"role": "user", "content": f"Hola Coach, aquí tienes mi objetivo y mi historial. ¿Cuál es tu análisis?\n\n{contexto}"})
    
    with st.spinner("Analizando tu perfil completo..."):
        response = get_llm_response(st.session_state.messages)
        st.session_state.messages.append({"role": "assistant", "content": response})
    st.rerun()

# --- NUEVA SECCIÓN: ACCIONES RÁPIDAS ---
st.subheader("Acciones Rápidas del Coach")
col1, col2 = st.columns(2)

with col1:
    if st.button("Sugerir Próximos Entrenamientos", disabled=(not st.session_state.last_analysis_context)):
        prompt_entrenos = "Basado en todo el contexto anterior sobre mi objetivo y mi estado de forma, sugiéreme los dos próximos entrenamientos clave para esta semana: una tirada larga y una sesión de series. Describe la distancia, el ritmo objetivo para cada parte y el propósito de cada entrenamiento."
        action_history = [{"role": "system", "content": st.session_state.messages[0]['content']}, {"role": "user", "content": st.session_state.last_analysis_context}, {"role": "user", "content": prompt_entrenos}]
        with st.spinner("Diseñando tus próximos entrenos..."):
            st.session_state.next_workouts_plan = get_llm_response(action_history)
        st.rerun()

with col2:
    if st.button("Plantear Objetivo Mensual", disabled=(not st.session_state.last_analysis_context)):
        prompt_objetivo = f"Considerando mi objetivo final ({goal_name}) y mi progreso actual, establece un 'mini-objetivo' realista y medible para el final del mes actual. Por ejemplo, ¿qué volumen semanal debería alcanzar, o qué ritmo debería poder mantener en una carrera de 10km para saber que voy por buen camino?"
        action_history = [{"role": "system", "content": st.session_state.messages[0]['content']}, {"role": "user", "content": st.session_state.last_analysis_context}, {"role": "user", "content": prompt_objetivo}]
        with st.spinner("Calculando tu objetivo mensual..."):
            st.session_state.monthly_goal_plan = get_llm_response(action_history)
        st.rerun()
        
# Mostrar resultados de las acciones rápidas
if 'next_workouts_plan' in st.session_state and st.session_state.next_workouts_plan:
    with st.expander("🗓️ Plan de Próximos Entrenamientos", expanded=True):
        st.markdown(st.session_state.next_workouts_plan)
if 'monthly_goal_plan' in st.session_state and st.session_state.monthly_goal_plan:
    with st.expander("🎯 Tu Objetivo para Final de Mes", expanded=True):
        st.markdown(st.session_state.monthly_goal_plan)

# --- CHAT ABIERTO ---
st.subheader("Conversa con tu Coach")
# Mostrar historial de chat visible
for message in st.session_state.messages[2:]: # Omitir system y el contexto inicial
     with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Haz una pregunta de seguimiento...", disabled=(not api_key)):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)
    with st.chat_message("assistant"):
        with st.spinner("Pensando..."):
            response = get_llm_response(st.session_state.messages)
            st.markdown(response)
    st.session_state.messages.append({"role": "assistant", "content": response})
    st.rerun()