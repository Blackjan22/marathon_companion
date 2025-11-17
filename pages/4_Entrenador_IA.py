# pages/4_Coach_IA.py
import streamlit as st
import os
import sys
from datetime import datetime
from i18n import t
from auth import check_password, add_logout_button

# Configurar certificado SSL ANTES de importar genai (para VPN corporativa)
proxy_cert = os.path.expanduser("~/Credentials/rootcaCert.pem")
combined_cert_path = None

if os.path.exists(proxy_cert):
    # Intentar combinar el certificado proxy con los certificados del sistema
    system_certs = None

    # Buscar certificados del sistema en macOS
    possible_system_certs = [
        '/etc/ssl/cert.pem',
        '/usr/local/etc/openssl/cert.pem',
        '/System/Library/OpenSSL/cert.pem'
    ]

    for cert_path in possible_system_certs:
        if os.path.exists(cert_path):
            system_certs = cert_path
            break

    # Crear certificado combinado temporal
    if system_certs:
        try:
            combined_cert_path = os.path.expanduser("~/.config/combined_cert.pem")
            os.makedirs(os.path.dirname(combined_cert_path), exist_ok=True)

            # Leer y combinar certificados
            with open(combined_cert_path, 'w') as outfile:
                # Primero el proxy cert
                with open(proxy_cert, 'r') as infile:
                    outfile.write(infile.read())
                    outfile.write('\n')
                # Luego los certificados del sistema
                with open(system_certs, 'r') as infile:
                    outfile.write(infile.read())

            # Usar el certificado combinado
            os.environ['GRPC_DEFAULT_SSL_ROOTS_FILE_PATH'] = combined_cert_path
            os.environ['SSL_CERT_FILE'] = combined_cert_path
            os.environ['REQUESTS_CA_BUNDLE'] = combined_cert_path
            os.environ['CURL_CA_BUNDLE'] = combined_cert_path
        except Exception as e:
            # Si falla, usar solo el proxy cert
            print(f"No se pudo crear certificado combinado: {e}")
            os.environ['GRPC_DEFAULT_SSL_ROOTS_FILE_PATH'] = proxy_cert
            os.environ['SSL_CERT_FILE'] = proxy_cert
            os.environ['REQUESTS_CA_BUNDLE'] = proxy_cert
    else:
        # Si no hay certificados del sistema, usar solo el proxy
        os.environ['GRPC_DEFAULT_SSL_ROOTS_FILE_PATH'] = proxy_cert
        os.environ['SSL_CERT_FILE'] = proxy_cert
        os.environ['REQUESTS_CA_BUNDLE'] = proxy_cert

    # Para gRPC específicamente
    os.environ['GRPC_TRACE'] = ''  # Deshabilitar logging verbose de gRPC
    os.environ['GRPC_VERBOSITY'] = 'ERROR'  # Solo mostrar errores

import google.generativeai as genai

# Añadir el directorio src al path para importar módulos
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils import ai_functions
from utils import ai_context
from utils import gemini_tools
from utils.db_config import get_connection

st.set_page_config(layout="wide")

# Verificar autenticació
if not check_password():
    st.stop()

# Afegir botó de logout a la sidebar
add_logout_button()

st.title(t("coach_title"))
st.markdown(t("coach_subtitle"))

# Inicializar session state
if "messages" not in st.session_state:
    st.session_state.messages = []
    # Carregar context inicial automàticament
    initial_context = ai_context.generate_initial_context()
    if initial_context:
        greeting = ai_context.get_contextual_greeting()
        welcome_message = f"{greeting}\n\n**Context actual:**\n{initial_context}\n\nEn què et puc ajudar avui?"
        st.session_state.messages.append({"role": "assistant", "content": welcome_message})

if "gemini_configured" not in st.session_state:
    # Verificar API key (primer a st.secrets, després a variables d'entorn)
    try:
        gemini_api_key = st.secrets.get("GEMINI_API_KEY")
    except:
        gemini_api_key = os.getenv("GEMINI_API_KEY")

    if not gemini_api_key:
        st.error(t("no_api_key"))
        st.info(t("api_key_info"))
        st.stop()

    # Mostrar info de l'API key (només primers i últims caràcters per seguretat)
    if len(gemini_api_key) > 10:
        masked_key = f"{gemini_api_key[:6]}...{gemini_api_key[-4:]}"
        st.sidebar.caption(t("api_key_label") + f" {masked_key}")

    # Configurar Gemini
    try:
        genai.configure(api_key=gemini_api_key)
        st.session_state.gemini_configured = True
        st.sidebar.success(t("gemini_configured"))
    except Exception as e:
        st.error(t("gemini_config_error", error=str(e)))
        st.stop()

# Carregar System prompt del fitxer markdown
CURRENT_DATE = datetime.now().strftime('%Y-%m-%d')
CURRENT_YEAR = datetime.now().year

def load_coach_prompt() -> str:
    """Carrega el prompt del coach des del fitxer markdown."""
    prompt_path = os.path.join(os.path.dirname(__file__), '..', 'prompts', 'coach_prompt_ca.md')
    try:
        with open(prompt_path, 'r', encoding='utf-8') as f:
            prompt_template = f.read()
        # Reemplaçar les variables de data
        return prompt_template.format(current_date=CURRENT_DATE, current_year=CURRENT_YEAR)
    except Exception as e:
        st.error(f"Error carregant el prompt del coach: {e}")
        # Fallback a un prompt bàsic
        return f"Ets un entrenador personal especialitzat en running. Data actual: {CURRENT_DATE}"

SYSTEM_PROMPT = load_coach_prompt()


def save_chat_to_db(role: str, content: str):
    """Guarda un missatge a l'historial de xat a la BD."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO chat_history (role, content, timestamp)
        VALUES (?, ?, ?)
    """, (role, content, datetime.now().isoformat()))
    conn.commit()
    conn.close()


def load_chat_history(limit: int = 50):
    """Carrega l'historial de xat des de la BD."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT role, content, timestamp
        FROM chat_history
        ORDER BY timestamp DESC
        LIMIT ?
    """, (limit,))
    rows = cur.fetchall()
    conn.close()

    # Invertir para tener orden cronológico
    return [{"role": row[0], "content": row[1], "timestamp": row[2]} for row in reversed(rows)]


def get_context_summary():
    """Genera un resum del context actual per al chatbot."""
    try:
        # Últimes activitats
        recent = ai_functions.get_recent_activities(days=7)
        recent_summary = f"Últims 7 dies: {recent['count']} entrenaments, {recent['total_km']} km totals."

        # Pla actual
        plan = ai_functions.get_current_plan()
        if plan['plan']:
            plan_summary = f"Pla actiu per setmana {plan['plan']['week_start_date']} amb {plan['num_workouts']} entrenaments."
        else:
            plan_summary = "No hi ha pla actiu."

        return f"{recent_summary} {plan_summary}"
    except Exception as e:
        return f"No s'ha pogut carregar el context: {str(e)}"


# Sidebar amb opcions
with st.sidebar:
    st.markdown(f"### {t('coach_options')}")

    # Informació del model
    st.caption(t("coach_model"))
    st.caption(t("coach_model_note"))

    st.divider()

    # Mostrar opciones SSL solo en entorno local (cuando existe certificado proxy)
    proxy_cert = os.path.expanduser("~/Credentials/rootcaCert.pem")
    if os.path.exists(proxy_cert):
        with st.expander("🔧 Configuración SSL (Solo desarrollo local)"):
            combined_cert = os.path.expanduser("~/.config/combined_cert.pem")

            if os.path.exists(combined_cert):
                st.caption("🔒 Usando certificado combinado (proxy + sistema)")
            elif os.path.exists(proxy_cert):
                st.caption("🔒 Usando solo certificado proxy")

            # Opción para desactivar verificación SSL (solo para desarrollo)
            if "disable_ssl_verify" not in st.session_state:
                st.session_state.disable_ssl_verify = False

            st.session_state.disable_ssl_verify = st.checkbox(
                "Desactivar verificación SSL (solo VPN)",
                value=st.session_state.disable_ssl_verify,
                help="Activa esto si tienes problemas de SSL con la VPN corporativa. Solo para desarrollo."
            )

            if st.session_state.disable_ssl_verify:
                st.warning("⚠️ Verificación SSL desactivada")
                # Configurar para no verificar SSL
                os.environ['GRPC_SSL_CIPHER_SUITES'] = 'HIGH'
                import ssl
                ssl._create_default_https_context = ssl._create_unverified_context

            # Test de conexión
            if st.button("🔌 Test de Conexión a Gemini"):
                with st.spinner("Probando conexión..."):
                    try:
                        from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError

                        test_model = genai.GenerativeModel('gemini-2.0-flash-exp')

                        def test_connection():
                            return test_model.generate_content("Responde solo: OK")

                        # Ejecutar con timeout de 10 segundos
                        with ThreadPoolExecutor(max_workers=1) as executor:
                            future = executor.submit(test_connection)
                            try:
                                test_response = future.result(timeout=10)
                                st.success("✅ Conexión exitosa con Gemini!")
                                st.caption(f"Respuesta: {test_response.text[:50]}")
                            except FuturesTimeoutError:
                                st.error("❌ Timeout: La VPN está bloqueando Gemini")
                                st.warning("No podrás usar el Coach IA con la VPN conectada")
                    except Exception as e:
                        st.error(f"❌ Error de conexión: {str(e)}")

            # Diagnóstico SSL
            st.caption("**Estado de certificados:**")
            if os.path.exists(proxy_cert):
                st.text(f"✓ Proxy cert: {proxy_cert}")
            else:
                st.text(f"✗ Proxy cert no encontrado")

            if os.path.exists(combined_cert):
                st.text(f"✓ Certificado combinado: {combined_cert}")
                # Mostrar tamaño para verificar que se creó bien
                size = os.path.getsize(combined_cert)
                st.text(f"  Tamaño: {size} bytes")
            else:
                st.text(f"✗ Certificado combinado no creado")

            st.caption("**Variables de entorno SSL:**")
            ssl_vars = ['GRPC_DEFAULT_SSL_ROOTS_FILE_PATH', 'SSL_CERT_FILE', 'REQUESTS_CA_BUNDLE']
            for var in ssl_vars:
                value = os.environ.get(var, 'No configurada')
                st.text(f"{var}: {value}")

            if st.session_state.disable_ssl_verify:
                st.warning("⚠️ Verificación SSL desactivada")

            st.caption("**Soluciones si persiste el error:**")
            st.text("""
1. Activa 'Desactivar verificación SSL' arriba
2. Desconéctate de la VPN corporativa
3. Verifica que el proxy cert sea válido
4. Reinicia Streamlit después de cambios
            """)

        st.divider()

    if st.button("🆕 Nova Conversa"):
        st.session_state.messages = []
        st.rerun()

    if st.button("📥 Carregar historial"):
        history = load_chat_history(limit=20)
        st.session_state.messages = [
            {"role": msg["role"], "content": msg["content"]}
            for msg in history
        ]
        st.success(f"Carregats {len(history)} missatges")
        st.rerun()

    if st.button("🔄 Recarregar context"):
        initial_context = ai_context.generate_initial_context()
        greeting = ai_context.get_contextual_greeting()
        welcome_message = f"{greeting}\n\n**Context actualitzat:**\n{initial_context}\n\nEn què et puc ajudar?"
        st.session_state.messages = [{"role": "assistant", "content": welcome_message}]
        st.success("Context recarregat")
        st.rerun()

    st.divider()

    # Context actual
    st.markdown("### 📊 Resum Ràpid")
    with st.spinner("Carregant..."):
        context = get_context_summary()
        st.caption(context)

    # Anàlisi de càrrega
    with st.expander("📈 Anàlisi de càrrega"):
        load_analysis = ai_context.check_training_load_progression()
        if load_analysis.get('status') == 'warning':
            st.warning(load_analysis.get('warning', 'Compte amb la progressió'))
        elif load_analysis.get('status') == 'ok':
            st.success(f"Progressió adequada: {load_analysis.get('increase_percentage', 0):.1f}%")
        elif load_analysis.get('status') == 'low':
            st.info(load_analysis.get('warning', 'Volum reduït'))

    st.divider()

    # Informació sobre funcions disponibles
    with st.expander("🔧 Funcions disponibles (12 funcions)"):
        st.markdown("""
        **✅ Function calling actiu**

        L'entrenador pot executar automàticament aquestes funcions:

        **Consulta de dades:**
        - `get_runner_profile`: Veure el teu perfil complet (objectius, PRs, filosofia)
        - `get_recent_activities`: Veure els teus últims entrenaments
        - `get_weekly_stats`: Estadístiques setmanals agregades
        - `get_activity_details`: Detalls complets d'un entrenament (incloent notes privades)
        - `get_current_plan`: Consultar el teu pla actiu

        **Anàlisi avançat:**
        - `analyze_performance_trends`: Detectar millores o fatiga (FC vs ritme)
        - `predict_race_times`: Calculadora d'equivalències de temps (Fórmula de Riegel)
        - `analyze_training_load_advanced`: Detectar sobreentrament

        **Accions:**
        - `create_training_plan`: Crear plans d'entrenament complets
        - `add_workout_to_current_plan`: Afegir entrenaments al pla actiu
        - `update_workout`: Modificar entrenaments planificats
        - `delete_workout`: Eliminar entrenaments del pla

        El model decidirà automàticament quan utilitzar cada funció segons
        la teva pregunta. Veuràs un indicador cada vegada que s'executi una funció.
        """)

# Inicializar bandera de procesamiento pendiente
if "pending_message" not in st.session_state:
    st.session_state.pending_message = False

# Mostrar historial de chat
for message in st.session_state.messages:
    if message["role"] in ["user", "assistant"]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# Mapeo de nombres de funciones a las funciones reales
FUNCTION_HANDLERS = {
    "get_recent_activities": ai_functions.get_recent_activities,
    "get_weekly_stats": ai_functions.get_weekly_stats,
    "get_activity_details": ai_functions.get_activity_details,
    "get_current_plan": ai_functions.get_current_plan,
    "create_training_plan": ai_functions.create_training_plan,
    "update_workout": ai_functions.update_workout,
    "add_workout_to_current_plan": ai_functions.add_workout_to_current_plan,
    "delete_workout": ai_functions.delete_workout,
    "get_runner_profile": ai_functions.get_runner_profile,
    "analyze_performance_trends": ai_functions.analyze_performance_trends,
    "predict_race_times": ai_functions.predict_race_times,
    "analyze_training_load_advanced": ai_functions.analyze_training_load_advanced,
}


def execute_function_call(function_name: str, function_args: dict):
    """
    Ejecuta una función llamada por el modelo.

    Args:
        function_name: Nombre de la función a ejecutar
        function_args: Argumentos de la función

    Returns:
        Resultado de la función
    """
    if function_name not in FUNCTION_HANDLERS:
        return {"error": f"Función desconocida: {function_name}"}

    try:
        function = FUNCTION_HANDLERS[function_name]
        result = function(**function_args)
        return result
    except Exception as e:
        return {"error": f"Error ejecutando {function_name}: {str(e)}"}


# Función para procesar mensaje del usuario
def process_user_message(prompt):
    """Procesa un mensaje del usuario y obtiene respuesta del modelo con function calling."""
    # Preparar historial de chat para Gemini
    history = []
    for msg in st.session_state.messages[:-1]:  # Todos menos el último (que es el prompt actual)
        if msg["role"] == "user":
            history.append({"role": "user", "parts": [msg["content"]]})
        elif msg["role"] in ["assistant", "model"]:
            history.append({"role": "model", "parts": [msg["content"]]})

    # Obtener respuesta del modelo
    with st.chat_message("assistant"):
        try:
            # Crear modelo con system instruction y herramientas
            # Aumentar max_output_tokens para análisis completos de entrenamientos
            generation_config = {
                "temperature": 0.7,
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": 4096,
            }

            # Usar gemini-2.0-flash-exp que es más estable para function calling
            # gemini-2.5-flash puede generar MALFORMED_FUNCTION_CALL con estructuras complejas
            model = genai.GenerativeModel(
                model_name='gemini-2.0-flash-exp',
                generation_config=generation_config,
                system_instruction=SYSTEM_PROMPT,
                tools=[gemini_tools.running_coach_tools]
            )

            # Iniciar chat con historial
            chat = model.start_chat(history=history)

            # Loop de function calling
            from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError

            max_iterations = 5  # Prevenir loops infinitos
            iteration = 0
            current_prompt = prompt
            functions_executed = []
            last_function_result = None  # Para guardar el último resultado de función

            while iteration < max_iterations:
                iteration += 1

                # Actualizar spinner con información de progreso
                if iteration == 1:
                    spinner_text = "Pensando..."
                else:
                    spinner_text = f"Procesando funciones ({len(functions_executed)} ejecutadas)..."

                with st.spinner(spinner_text):
                    def send_message():
                        return chat.send_message(current_prompt)

                    # Ejecutar con timeout de 30 segundos
                    with ThreadPoolExecutor(max_workers=1) as executor:
                        future = executor.submit(send_message)
                        try:
                            response = future.result(timeout=30)
                        except FuturesTimeoutError:
                            st.error("⏱️ Timeout: La VPN corporativa está bloqueando las peticiones a Gemini.")
                            st.info("💡 Opciones:\n- Prueba desde casa sin VPN\n- Desconéctate de la VPN temporalmente")
                            raise TimeoutError("La petición a Gemini tardó demasiado (probablemente bloqueada por VPN)")

                    # Verificar si el modelo quiere llamar funciones
                    if not response.candidates:
                        st.error("No hay candidatos en la respuesta del modelo")
                        st.json({"response": str(response)})
                        return

                    candidate = response.candidates[0]

                    # Verificar si hay contenido
                    if not candidate.content or not candidate.content.parts:
                        st.warning("⚠️ El modelo no pudo generar una respuesta textual.")

                        # Si ejecutamos funciones, mostrar al menos los datos raw
                        if functions_executed and iteration > 1 and last_function_result:
                            st.info("🔧 Pero sí obtuvimos estos datos de las funciones ejecutadas:")

                            # Formatear los datos de forma user-friendly
                            if 'activity' in last_function_result:
                                act = last_function_result['activity']
                                st.subheader(f"📊 {act.get('name', 'Actividad')}")
                                st.write(f"**Fecha:** {act.get('start_date_local', 'N/A')[:10]}")
                                st.write(f"**Distancia:** {act.get('distance_km', 0):.2f} km")
                                st.write(f"**Tiempo:** {act.get('moving_time', 0) // 60} minutos")
                                st.write(f"**Ritmo medio:** {(act.get('moving_time', 0) / 60) / act.get('distance_km', 1):.2f} min/km")
                                if act.get('average_heartrate'):
                                    st.write(f"**FC media:** {act.get('average_heartrate', 0):.1f} bpm")
                                if act.get('description'):
                                    st.write(f"**Descripción:** {act.get('description')}")
                                if act.get('private_note'):
                                    st.write(f"**Notas:** {act.get('private_note')}")

                                # Mostrar info de laps
                                if 'laps' in last_function_result and last_function_result['laps']:
                                    num_laps = len(last_function_result['laps'])
                                    st.write(f"\n**Laps:** {num_laps} laps registrados")

                                    # Calcular estadísticas de laps
                                    laps = last_function_result['laps']
                                    avg_lap_pace = sum(lap.get('moving_time', 0) / 60 / lap.get('distance_km', 1) for lap in laps if lap.get('distance_km', 0) > 0) / num_laps if num_laps > 0 else 0
                                    fastest_lap = min(laps, key=lambda x: x.get('moving_time', float('inf')) / x.get('distance_km', 1) if x.get('distance_km', 0) > 0 else float('inf'))
                                    slowest_lap = max(laps, key=lambda x: x.get('moving_time', 0) / x.get('distance_km', 1) if x.get('distance_km', 0) > 0 else 0)

                                    st.write(f"  - Ritmo medio de laps: {avg_lap_pace:.2f} min/km")
                                    if fastest_lap.get('distance_km', 0) > 0:
                                        st.write(f"  - Lap más rápido: Lap {fastest_lap['lap_index']} - {(fastest_lap['moving_time'] / 60) / fastest_lap['distance_km']:.2f} min/km")
                                    if slowest_lap.get('distance_km', 0) > 0:
                                        st.write(f"  - Lap más lento: Lap {slowest_lap['lap_index']} - {(slowest_lap['moving_time'] / 60) / slowest_lap['distance_km']:.2f} min/km")

                                    with st.expander(f"Ver detalles de los {num_laps} laps"):
                                        for lap in laps[:20]:  # Mostrar primeros 20 en la UI
                                            pace = (lap['moving_time'] / 60) / lap['distance_km'] if lap.get('distance_km', 0) > 0 else 0
                                            st.text(f"Lap {lap['lap_index']}: {lap['distance_km']:.2f}km - {pace:.2f} min/km - {lap['moving_time']//60}:{lap['moving_time']%60:02d}")
                                        if num_laps > 20:
                                            st.caption(f"... y {num_laps - 20} laps más")
                            else:
                                st.json(last_function_result)

                        # Mostrar información de debug
                        with st.expander("🔍 Debug info"):
                            st.write("Finish reason:", candidate.finish_reason if hasattr(candidate, 'finish_reason') else "No disponible")
                            st.write("Safety ratings:", candidate.safety_ratings if hasattr(candidate, 'safety_ratings') else "No disponible")
                            st.write("Funciones ejecutadas:", functions_executed)
                            st.info("Posibles causas:\n- Respuesta bloqueada por filtros de seguridad\n- Error interno del modelo\n- Demasiados datos para procesar")

                        return

                    # IMPORTANTE: Procesar TODAS las parts (puede haber múltiples function calls)
                    parts = candidate.content.parts

                    # Separar function calls y texto
                    function_calls_in_turn = []
                    text_parts = []

                    for part in parts:
                        if hasattr(part, 'function_call') and part.function_call:
                            function_calls_in_turn.append(part)
                        elif hasattr(part, 'text') and part.text:
                            text_parts.append(part)

                    # Si hay function calls, ejecutar TODAS
                    if function_calls_in_turn:
                        from google.generativeai.types import content_types
                        function_response_parts = []

                        for part in function_calls_in_turn:
                            function_call = part.function_call
                            function_name = function_call.name
                            function_args = dict(function_call.args)

                            # Registrar función ejecutada
                            functions_executed.append(function_name)

                            # Mostrar indicador de que se está ejecutando una función
                            with st.status(f"🔧 Ejecutando: {function_name}", expanded=False) as status:
                                st.json(function_args)

                                # Ejecutar la función
                                function_result = execute_function_call(function_name, function_args)
                                last_function_result = function_result  # Guardar para fallback

                                status.update(label=f"✅ {function_name} completado", state="complete")

                            # Añadir respuesta para esta función
                            function_response_parts.append(content_types.to_part({
                                "function_response": {
                                    "name": function_name,
                                    "response": function_result
                                }
                            }))

                        # Enviar TODAS las respuestas de función al modelo
                        current_prompt = function_response_parts
                        continue

                    # Si hay texto, es la respuesta final
                    elif text_parts:
                        # Combinar todas las partes de texto
                        response_text = "".join([part.text for part in text_parts])

                        # Mostrar respuesta
                        st.markdown(response_text)

                        # Mostrar funciones ejecutadas si hubo alguna
                        if functions_executed:
                            with st.expander(f"🔍 Datos consultados ({len(functions_executed)} funciones)", expanded=False):
                                for func in functions_executed:
                                    st.caption(f"• {func}")

                        # Guardar en session state y BD
                        st.session_state.messages.append({"role": "assistant", "content": response_text})
                        save_chat_to_db("assistant", response_text)

                        return  # Salir del loop

                    # Si no hay ni function call ni texto, algo salió mal
                    else:
                        st.warning("El modelo no generó ni texto ni function call")
                        with st.expander("🔍 Debug - tipo de part"):
                            st.write("Part type:", type(part))
                            st.write("Part attributes:", dir(part))
                            st.json({"part": str(part)})
                        return

            # Si llegamos aquí, excedimos el máximo de iteraciones
            st.warning("Se alcanzó el límite de iteraciones. El modelo puede estar teniendo problemas.")

        except Exception as e:
            st.error(f"❌ Error al comunicarse con Gemini:")
            st.code(f"Tipo: {type(e).__name__}\nMensaje: {str(e)}")

            # Manejo específico para MALFORMED_FUNCTION_CALL
            if "MALFORMED_FUNCTION_CALL" in str(e):
                st.warning("⚠️ **El modelo intentó llamar a una función pero generó JSON inválido.**")
                st.info("""
**Soluciones recomendadas:**
1. 🔄 Reformula tu solicitud de forma más simple
2. ⚙️ Cambia a `gemini-2.0-flash-exp` (más estable para function calling)
3. 🔧 Si el problema persiste, reporta este error

**Nota técnica:** `gemini-2.5-flash` es más reciente pero puede ser menos estable con llamadas a funciones complejas.
                """)

                # Intentar mostrar el candidate si está disponible
                try:
                    from google.generativeai.types.generation_types import StopCandidateException
                    if isinstance(e, StopCandidateException):
                        with st.expander("🔍 Ver detalles técnicos del error"):
                            candidate = e.args[0] if e.args else None
                            if candidate:
                                st.write("**Candidate info:**")
                                st.write(f"- Finish reason: {candidate.finish_reason}")
                                st.write(f"- Safety ratings: {candidate.safety_ratings}")
                                if hasattr(candidate, 'content') and candidate.content:
                                    st.write("**Content parts:**")
                                    for i, part in enumerate(candidate.content.parts):
                                        st.write(f"Part {i}: {type(part).__name__}")
                                        if hasattr(part, 'function_call'):
                                            st.json({
                                                "function_name": part.function_call.name if hasattr(part.function_call, 'name') else "N/A",
                                                "args_raw": str(part.function_call.args) if hasattr(part.function_call, 'args') else "N/A"
                                            })
                except Exception as debug_error:
                    st.caption(f"No se pudo extraer información adicional: {debug_error}")

            # Información adicional de debug
            import traceback
            with st.expander("📋 Stack trace completo"):
                st.code(traceback.format_exc())

# Verificar si hay un mensaje pendiente de procesar (de acciones rápidas)
if st.session_state.pending_message:
    # Obtener el último mensaje del usuario
    if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
        prompt = st.session_state.messages[-1]["content"]
        process_user_message(prompt)
        st.session_state.pending_message = False

# Input de l'usuari
if prompt := st.chat_input("Escriu el teu missatge a l'entrenador..."):
    # Afegir missatge de l'usuari
    st.session_state.messages.append({"role": "user", "content": prompt})
    save_chat_to_db("user", prompt)

    # Mostrar missatge de l'usuari
    with st.chat_message("user"):
        st.markdown(prompt)

    # Processar el missatge
    process_user_message(prompt)

# Botons d'acció ràpida
st.divider()
st.markdown("### 💡 Accions Ràpides")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("📊 Veure les meves últimes activitats"):
        quick_prompt = "Mostra'm un resum dels meus últims 7 dies d'entrenament"
        st.session_state.messages.append({"role": "user", "content": quick_prompt})
        save_chat_to_db("user", quick_prompt)
        st.session_state.pending_message = True
        st.rerun()

with col2:
    if st.button("📅 Planificar propera setmana"):
        quick_prompt = "Necessito que em proposis un pla d'entrenaments per la propera setmana. Primer revisa els meus últims entrenos i pregunta'm per les meves sensacions."
        st.session_state.messages.append({"role": "user", "content": quick_prompt})
        save_chat_to_db("user", quick_prompt)
        st.session_state.pending_message = True
        st.rerun()

with col3:
    if st.button("🎯 Veure pla actual"):
        quick_prompt = "Quin és el meu pla d'entrenament actual? Com vaig?"
        st.session_state.messages.append({"role": "user", "content": quick_prompt})
        save_chat_to_db("user", quick_prompt)
        st.session_state.pending_message = True
        st.rerun()

# Informació addicional
with st.expander("ℹ️ Com utilitzar l'Entrenador IA"):
    st.markdown("""
    **Consells per interactuar amb el teu entrenador:**

    1. **Sigues específic**: Explica'li els teus objectius, sensacions i dubtes
    2. **Comparteix feedback**: Després de cada entreno, explica-li com et vas sentir
    3. **Pregunta lliurement**: L'entrenador té accés a totes les teves dades de Strava
    4. **Planificació setmanal**: Demana-li que revisi la teva setmana abans de planificar la següent

    **Exemples de preguntes:**
    - "Com ha estat el meu progrés en les últimes 4 setmanes?"
    - "Avui vaig fer 10km i em vaig sentir molt cansat, quin entrenament em recomaneu per demà?"
    - "Vull preparar una mitja marató en 3 mesos, quin pla em suggereixes?"
    - "Mostra'm els detalls del meu últim entreno de sèries"
    """)
