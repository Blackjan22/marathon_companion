# -*- coding: utf-8 -*-
"""
Sistema d'internacionalització per a Marathon Companion.
Tots els strings de la interfície d'usuari en català.
"""

# Diccionari principal amb tots els strings
STRINGS_CA = {
    # === APP PRINCIPAL (app.py) ===
    "app_title": "Running Analytics",
    "app_page_icon": "🏃‍♂️",
    "welcome_title": "🏃‍♂️ My Runs Analytics",
    "welcome_header": "Benvingut al teu panell d'anàlisi de curses",
    "select_page_info": "Selecciona una de les pàgines del menú de l'esquerra per començar l'anàlisi.",
    "app_description": """Aquesta aplicació et permet visualitzar i analitzar totes les curses que has sincronitzat des de Strava,
amb planificació intel·ligent d'entrenaments mitjançant IA.

**Característiques principals:**
- **📊 Dashboard General:** Resum de les teves mètriques clau i anàlisi de progrés.
- **📋 Històric Complet:** Taula amb totes les teves activitats per cercar, filtrar i analitzar en detall.
- **📅 Planificació:** Gestiona els teus plans d'entrenament setmanals i vincula activitats.
- **🤖 Coach IA:** Chatbot intel·ligent que analitza el teu progrés i crea plans personalitzats.

Utilitza el menú de l'esquerra per navegar!""",

    # Sidebar
    "sidebar_options": "Opcions",
    "refresh_activities": "🔄 Actualitzar activitats",
    "syncing_activities": "Sincronitzant noves activitats des de Strava...",
    "activities_updated": "✅ Activitats actualitzades!",
    "sync_error": "No s'ha pogut sincronitzar: {error}",

    # Debug BD
    "debug_bd": "🔍 Debug BD",
    "db_detection": "**Detecció de BD:**",
    "db_url_found": "✅ URL trobada ({length} chars)",
    "db_host": "Host: {host}",
    "db_host_error": "Host: error parseant",
    "db_url_not_found": "⚠️ No s'ha detectat DATABASE_URL",
    "secrets_available": "**Secrets disponibles:**",
    "database_key_found": "✅ clau 'database' trobada",
    "database_key_not_found": "❌ clau 'database' NO trobada",
    "secrets_error": "Error llegint secrets: {error}",
    "test_connection": "🔌 Test connexió PostgreSQL",
    "no_db_url": "No hi ha URL de base de dades configurada",
    "connecting_to": "Intentant connectar a: {url}...",
    "connection_success": "✅ Connexió exitosa!",
    "postgres_version": "PostgreSQL version: {version}...",
    "connection_error": "❌ Error de connexió: {error_type}",

    # === DASHBOARD GENERAL (pages/1_Dashboard_General.py) ===
    "dashboard_title": "📊 Dashboard General",
    "no_data_warning": "No hi ha dades de curses disponibles. Sincronitza les teves activitats primer.",

    # Filtros
    "filters_header": "Filtres del Dashboard",
    "date_range": "Rang de dates:",
    "min_distance": "Distància mínima (km):",
    "group_by": "Agrupar per:",
    "group_weeks": "Setmanes",
    "group_months": "Mesos",
    "long_run_definition": "Definició de 'tirada llarga' (km):",
    "show_coach_tips": "Mostrar insights d'entrenador",
    "no_data_with_filters": "No hi ha dades per mostrar amb els filtres aplicats.",

    # Métricas principales
    "training_metrics": "Mètriques d'entrenament",
    "total_runs": "Total Curses",
    "last_30d": "últims 30d",
    "total_km": "Total Quilòmetres",
    "avg_pace": "Ritme Promig",
    "vs_prev_30d": "vs prev. 30d",
    "longest_run": "Cursa Més Llarga",
    "current_streak": "Ratxa Actual",
    "max_streak": "Ratxa Màxima",
    "days": "dies",

    # Sección volumen
    "volume_section": "Volum d'entrenament",
    "weekly_avg_4w": "Mitjana setmanal (últimes 4 setmanes)",
    "runs_per_week_8w": "Curses per setmana (últimes 8 setmanes)",
    "long_runs_4w": "Tirades llargues (últimes 4 setmanes)",
    "volume_change": "Canvi de volum (vs 4 setm. anteriors)",
    "increase": "augment",
    "decrease": "disminució",

    # Gráficos
    "weekly_volume_chart": "Volum setmanal (km) i mitjana de 4 setmanes",
    "week": "Setmana",
    "distance_km": "Distància (km)",
    "avg_4w": "Mitjana 4 setm.",
    "runs_per_week_chart": "Curses per setmana",
    "runs": "Curses",
    "pace_distribution_chart": "Distribució de ritmes",
    "pace_min_km": "Ritme (min/km)",
    "frequency": "Freqüència",
    "long_runs_distance_chart": "Distància de tirades llargues",
    "date": "Data",

    # Análisis adicional
    "additional_analysis": "Anàlisi addicional",
    "training_by_day": "Entrenament per dia de la setmana",
    "day_of_week": "Dia de la setmana",
    "total_distance": "Distància total",
    "avg_runs_per_day": "Mitjana curses per dia",
    "training_by_hour": "Entrenament per franja horària",
    "hour_of_day": "Hora del dia",
    "morning_label": "Matinada (0-6)",
    "morning_early_label": "Matí (6-10)",
    "midday_label": "Migdia (10-14)",
    "afternoon_label": "Tarda (14-18)",
    "evening_label": "Vespre (18-22)",
    "night_label": "Nit (22-24)",

    # Zonas de entrenamiento
    "training_zones": "Zones d'entrenament (basades en ritme)",
    "zone_easy": "Fàcil",
    "zone_moderate": "Moderat",
    "zone_tempo": "Tempo",
    "zone_fast": "Ràpid",
    "zone": "Zona",
    "run_count": "Nombre de curses",

    # Personal records
    "personal_records": "Rècords personals (estimacions)",
    "pr_5k": "5K",
    "pr_10k": "10K",
    "pr_half": "Mitja Marató",
    "pr_marathon": "Marató",
    "no_pr_data": "No hi ha suficients dades",
    "time": "Temps",

    # Coach tips
    "coach_tips": "💡 Insights d'entrenador",

    # === HISTÓRICO COMPLETO (pages/2_Histórico_Completo.py) ===
    "history_title": "📋 Històric Complet",
    "history_filters": "Filtres de l'històric",
    "sport_type": "Tipus d'esport:",
    "all_sports": "Tots",
    "sort_by": "Ordenar per:",
    "sort_date_desc": "Data (més recent)",
    "sort_date_asc": "Data (més antic)",
    "sort_distance_desc": "Distància (major)",
    "sort_pace_asc": "Ritme (més ràpid)",
    "search_activity": "Cercar activitat:",
    "showing_activities": "Mostrant {count} activitats",
    "activity_name": "Activitat",
    "distance": "Distància (km)",
    "time_label": "Temps",
    "avg_pace_label": "Ritme (min/km)",
    "avg_hr": "FC Mitjana",
    "elevation": "Desnivell (m)",
    "activity_details": "Detalls de l'activitat",
    "no_activity_selected": "Selecciona una activitat de la taula per veure els seus detalls",
    "activity_info": "Informació de l'activitat",
    "view_on_strava": "Veure a Strava",
    "laps_analysis": "Anàlisi de voltes",
    "no_laps": "Aquesta activitat no té voltes enregistrades",
    "lap": "Volta",
    "lap_time": "Temps",
    "lap_pace": "Ritme",
    "lap_hr": "FC",
    "lap_pace_chart": "Ritme per volta",
    "lap_number": "Número de volta",

    # === PLANIFICACIÓN (pages/3_Planificacion.py) ===
    "planning_title": "📅 Planificació",
    "planning_description": "Gestiona els teus plans d'entrenament setmanals i vincula activitats de Strava.",
    "create_plan_section": "Crear nou pla",
    "week_start_date": "Data d'inici de setmana (dilluns):",
    "week_description": "Descripció de la setmana:",
    "week_description_placeholder": "Ex: Setmana de construcció de base, Setmana de descàrrega...",
    "create_plan_button": "Crear pla setmanal",
    "plan_created": "✅ Pla creat amb èxit!",
    "plan_creation_error": "Error creant el pla: {error}",
    "current_plan_section": "Pla actual",
    "no_active_plan": "No hi ha cap pla actiu. Crea un pla nou o activa un pla existent.",
    "plan_for_week": "Pla per la setmana del {date}",
    "plan_description_label": "Descripció:",
    "workouts_section": "Entrenaments planificats",
    "add_workout": "Afegir entrenament",
    "workout_type": "Tipus d'entrenament:",
    "planned_date": "Data planificada:",
    "workout_description": "Descripció de l'entrenament:",
    "workout_description_placeholder": "Ex: 5km rodatge suau, 10x400m sèries...",
    "target_pace": "Ritme objectiu (min/km):",
    "target_pace_placeholder": "Ex: 5:00",
    "add_workout_button": "Afegir entrenament",
    "workout_added": "✅ Entrenament afegit!",
    "workout_add_error": "Error afegint entrenament: {error}",
    "edit_workout": "Editar entrenament",
    "delete_workout": "Eliminar entrenament",
    "link_activity": "Vincular activitat",
    "unlink_activity": "Desvincular",
    "planned": "Planificat",
    "completed": "Completat",
    "linked_activity": "Activitat vinculada:",
    "no_workouts": "No hi ha entrenaments planificats per aquesta setmana.",
    "available_activities": "Activitats disponibles per vincular",
    "no_activities_to_link": "No hi ha activitats sense vincular per aquestes dates",
    "link_activity_button": "Vincular",
    "activity_linked": "✅ Activitat vinculada!",
    "activity_link_error": "Error vinculant activitat: {error}",

    # Workout types
    "workout_type_easy_run": "Rodatge suau",
    "workout_type_long_run": "Tirada llarga",
    "workout_type_intervals": "Sèries",
    "workout_type_tempo": "Tempo",
    "workout_type_recovery": "Recuperació",
    "workout_type_quality": "Qualitat",

    # === COACH IA (pages/4_Coach_IA.py) ===
    "coach_title": "🤖 Coach amb Intel·ligència Artificial",
    "coach_subtitle": "El teu entrenador personal basat en dades i IA. Analitza el teu progrés i dissenya el teu pla d'entrenament.",
    "coach_options": "⚙️ Opcions",
    "coach_model": "🤖 Model: **gemini-2.0-flash-exp**",
    "coach_model_note": "(Més estable per function calling)",
    "api_key_label": "🔑 API Key:",
    "gemini_configured": "✅ Gemini configurat",
    "gemini_config_error": "Error configurant Gemini: {error}",
    "no_api_key": "⚠️ No s'ha trobat la API key de Gemini. Si us plau, afegeix GEMINI_API_KEY al teu arxiu .env o secrets",
    "api_key_info": "La API key ha de començar amb 'AIza...'",

    # SSL Configuration
    "ssl_config": "🔧 Configuració SSL (Només desenvolupament local)",
    "ssl_combined_cert": "🔒 Utilitzant certificat combinat (proxy + sistema)",
    "ssl_proxy_only": "🔒 Utilitzant només certificat proxy",
    "disable_ssl_verify": "Desactivar verificació SSL (només VPN)",
    "disable_ssl_help": "Activa això si tens problemes de SSL amb la VPN corporativa. Només per desenvolupament.",
    "ssl_verification_disabled": "⚠️ Verificació SSL desactivada",
    "test_gemini_connection": "🔌 Test de Connexió a Gemini",
    "testing_connection": "Provant connexió...",
    "connection_successful": "✅ Connexió exitosa amb Gemini!",
    "connection_response": "Resposta: {response}",
    "connection_timeout": "❌ Timeout: La VPN està bloquejant Gemini",
    "connection_timeout_note": "No podràs utilitzar el Coach IA amb la VPN connectada",
    "connection_error_label": "❌ Error de connexió: {error}",
    "cert_status": "**Estat de certificats:**",
    "proxy_cert_found": "✓ Proxy cert: {path}",
    "proxy_cert_not_found": "✗ Proxy cert no trobat",
    "combined_cert_found": "✓ Certificat combinat: {path}",
    "combined_cert_size": "Mida: {size} bytes",
    "combined_cert_not_found": "✗ Certificat combinat no creat",
    "ssl_env_vars": "**Variables d'entorn SSL:**",
    "ssl_solutions": "**Solucions si persisteix l'error:**",
    "ssl_solutions_text": """
1. Activa 'Desactivar verificació SSL' a dalt
2. Desconnecta't de la VPN corporativa
3. Verifica que el proxy cert sigui vàlid
4. Reinicia Streamlit després dels canvis
    """,

    # Chat
    "new_conversation": "🆕 Nova Conversa",
    "load_history": "📥 Carregar historial",
    "reload_context": "🔄 Recarregar context",
    "history_loaded": "Carregats {count} missatges",
    "context_reloaded": "Context recarregat",
    "quick_summary": "📊 Resum Ràpid",
    "loading": "Carregant...",
    "load_analysis": "📈 Anàlisi de càrrega",
    "load_warning": "Compte amb la progressió",
    "load_ok": "Progressió adequada: {percentage:.1f}%",
    "load_low": "Volum reduït",
    "available_functions": "🔧 Funcions disponibles (12 funcions)",
    "function_calling_active": "**✅ Function calling actiu**",
    "functions_description": """
El coach pot executar automàticament aquestes funcions:

**Consulta de dades:**
- `get_runner_profile`: Veure el teu perfil complet (objectius, PRs, filosofia)
- `get_recent_activities`: Veure els teus últims entrenaments
- `get_weekly_stats`: Estadístiques setmanals agregades
- `get_activity_details`: Detalls complets d'un entrenament (incloent notes privades)
- `get_current_plan`: Consultar el teu pla actiu

**Anàlisi avançat:**
- `analyze_performance_trends`: Detectar millores o fatiga (FC vs ritme)
- `predict_race_times`: Calculadora d'equivalències de temps (Fórmula de Riegel)
- `analyze_training_load_advanced`: Detectar sobreentrenament

**Accions:**
- `create_training_plan`: Crear plans d'entrenament complets
- `add_workout_to_current_plan`: Afegir entrenaments al pla actiu
- `update_workout`: Modificar entrenaments planificats
- `delete_workout`: Eliminar entrenaments del pla

El model decidirà automàticament quan utilitzar cada funció segons
la teva pregunta. Veuràs un indicador cada vegada que s'executi una funció.
""",

    # Chat messages
    "chat_input_placeholder": "Escriu el teu missatge al coach...",
    "thinking": "Pensant...",
    "processing_functions": "Processant funcions ({count} executades)...",
    "timeout_error": "⏱️ Timeout: La VPN corporativa està bloquejant les peticions a Gemini.",
    "timeout_options": "💡 Opcions:\n- Prova des de casa sense VPN\n- Desconnecta't de la VPN temporalment",
    "no_candidates": "No hi ha candidats en la resposta del model",
    "no_text_response": "⚠️ El model no ha pogut generar una resposta textual.",
    "function_data_obtained": "🔧 Però sí hem obtingut aquestes dades de les funcions executades:",
    "debug_info": "🔍 Debug info",
    "finish_reason": "Finish reason:",
    "safety_ratings": "Safety ratings:",
    "functions_executed": "Funcions executades:",
    "not_available": "No disponible",
    "possible_causes": "Possibles causes:\n- Resposta bloquejada per filtres de seguretat\n- Error intern del model\n- Massa dades per processar",
    "executing_function": "🔧 Executant: {function}",
    "function_completed": "✅ {function} completat",
    "data_consulted": "🔍 Dades consultades ({count} funcions)",
    "max_iterations_reached": "S'ha arribat al límit d'iteracions. El model pot estar tenint problemes.",
    "gemini_error": "❌ Error en comunicar-se amb Gemini:",
    "malformed_function_call": "⚠️ **El model ha intentat cridar una funció però ha generat JSON invàlid.**",
    "malformed_solutions": """
**Solucions recomanades:**
1. 🔄 Reformula la teva sol·licitud de forma més simple
2. ⚙️ Canvia a `gemini-2.0-flash-exp` (més estable per function calling)
3. 🔧 Si el problema persisteix, reporta aquest error

**Nota tècnica:** `gemini-2.5-flash` és més recent però pot ser menys estable amb crides a funcions complexes.
""",
    "technical_details": "🔍 Veure detalls tècnics de l'error",
    "candidate_info": "**Candidate info:**",
    "content_parts": "**Content parts:**",
    "could_not_extract_info": "No s'ha pogut extreure informació addicional: {error}",
    "full_stack_trace": "📋 Stack trace complet",

    # Quick actions
    "quick_actions": "💡 Accions Ràpides",
    "view_recent_activities": "📊 Veure les meves últimes activitats",
    "plan_next_week": "📅 Planificar propera setmana",
    "view_current_plan": "🎯 Veure pla actual",
    "quick_recent_prompt": "Mostra'm un resum dels meus últims 7 dies d'entrenament",
    "quick_plan_prompt": "Necessito que em proposis un pla d'entrenaments per la propera setmana. Primer revisa els meus últims entrenaments i pregunta'm per les meves sensacions.",
    "quick_current_prompt": "Quin és el meu pla d'entrenament actual? Com vaig?",

    # How to use
    "how_to_use": "ℹ️ Com utilitzar el Coach IA",
    "how_to_use_content": """
**Consells per interactuar amb el teu coach:**

1. **Sigues específic**: Explica'li els teus objectius, sensacions i dubtes
2. **Comparteix feedback**: Després de cada entrenament, explica-li com et vas sentir
3. **Pregunta lliurement**: El coach té accés a totes les teves dades de Strava
4. **Planificació setmanal**: Demana-li que revisi la teva setmana abans de planificar la següent

**Exemples de preguntes:**
- "Com ha estat el meu progrés en les últimes 4 setmanes?"
- "Avui he fet 10km i em vaig sentir molt cansat, quin entrenament em recomanes per demà?"
- "Vull preparar una mitja marató en 3 mesos, quin pla em suggereixes?"
- "Mostra'm els detalls del meu últim entrenament de sèries"
""",

    # === PERFIL CORREDOR (pages/5_Perfil_Corredor.py) ===
    "profile_title": "👤 Perfil del Corredor",
    "profile_description": """
Configura el teu perfil perquè el Coach IA pugui personalitzar les seves recomanacions.
Totes aquestes dades són opcionals, però com més complet estigui el teu perfil, millors seran les recomanacions.
""",
    "basic_info": "📝 Informació Bàsica",
    "name": "Nom:",
    "height": "Alçada (cm):",
    "weight": "Pes (kg):",
    "age": "Edat:",
    "training_zones": "🎯 Zones d'Entrenament",
    "vo2max": "VO2max estimat:",
    "threshold_pace": "Ritme de llindar (min/km):",
    "threshold_pace_placeholder": "Ex: 4:30",
    "easy_pace_min": "Ritme fàcil mínim (min/km):",
    "easy_pace_max": "Ritme fàcil màxim (min/km):",
    "training_philosophy_label": "🏃 Filosofia d'Entrenament",
    "training_philosophy_placeholder": "Ex: Prefereixo qualitat sobre volum, m'agrada entrenar matins...",
    "current_goals": "🎯 Objectius Actuals",
    "current_goal": "Objectiu actual:",
    "goal_placeholder": "Ex: Millorar temps de 10K, córrer primera marató...",
    "goal_race_date": "Data de cursa objectiu:",
    "goal_race_distance": "Distància de cursa objectiu (km):",
    "goal_distance_placeholder": "Ex: 10, 21.0975, 42.195",
    "personal_records_section": "🏆 Rècords Personals",
    "pr_5k_label": "5K (mm:ss):",
    "pr_5k_placeholder": "Ex: 20:30",
    "pr_10k_label": "10K (mm:ss):",
    "pr_10k_placeholder": "Ex: 42:15",
    "pr_half_label": "Mitja Marató (hh:mm:ss):",
    "pr_half_placeholder": "Ex: 1:35:20",
    "pr_marathon_label": "Marató (hh:mm:ss):",
    "pr_marathon_placeholder": "Ex: 3:25:00",
    "save_profile": "💾 Guardar Perfil",
    "profile_saved": "✅ Perfil guardat correctament!",
    "profile_save_error": "❌ Error guardant el perfil: {error}",
    "current_profile": "📊 Perfil Actual",
    "no_profile": "Encara no hi ha cap perfil configurat. Omple el formulari de dalt per crear-ne un.",
    "profile_updated_at": "Última actualització: {date}",

    # === UTILS ===
    # formatting.py
    "not_available": "N/D",

    # ai_context.py - Se manejarán directamente en el archivo ya que son strings dinámicos

    # === PLANIFICACION (pages/3_Planificacion.py) ===
    "planning_title": "📅 Planificació d'Entrenaments",
    "calendar_tab": "📆 Calendari",
    "link_activities_tab": "🔗 Vincular Activitats",
    "planned_workouts": "Entrenaments Planificats",
    "weeks_past": "Setmanes passades:",
    "weeks_future": "Setmanes futures:",
    "no_planned_workouts": "No hi ha entrenaments planificats. Ves a la pàgina del Coach IA per crear un pla.",
    "week_label": "Setmana {week}",
    "type_label": "Tipus:",
    "distance_label": "Distància:",
    "pace_objective_label": "Ritme objectiu:",
    "completed_activity": "Completat: {name}",
    "actual_distance": "Distància real: {km:.2f} km",
    "mark_completed": "✅ Marcar completat",
    "skip_workout": "⏭️ Saltar",
    "unmark_pending": "🔄 Desmarcar (tornar a pendent)",
    "edit_workout": "✏️ Editar",
    "delete_workout_button": "🗑️ Eliminar",
    "confirm_delete_workout": "⚠️ Confirmes que vols eliminar aquest entrenament?",
    "yes_delete": "✅ Sí, eliminar",
    "workout_deleted": "Entrenament eliminat",
    "edit_workout_title": "**Editar entrenament:**",
    "date_label": "Data:",
    "save_changes": "💾 Guardar canvis",
    "changes_saved": "✅ Canvis guardats",
    "link_strava_activities": "🔗 Vincular Activitats de Strava",
    "link_strava_desc": "Connecta les teves activitats de Strava amb els entrenaments planificats.",
    "all_activities_linked": "Totes les activitats recents estan vinculades!",
    "unlinked_activities": "Activitats sense vincular (últims 14 dies)",
    "date_time_label": "**Data:**",
    "time_label": "**Temps:**",
    "description_label": "Descripció:",
    "notes_label": "Notes:",
    "link_with": "Vincular amb:",
    "link_button": "Vincular",
    "activity_linked": "Activitat vinculada!",
    "no_pending_workouts_near": "No hi ha entrenaments pendents propers a aquesta data.",
    "summary_sidebar": "### 📊 Resum",
    "active_plan": "Pla actiu",
    "week_start": "Setmana: {date}",
    "objective_label": "Objectiu: {goal}",
    "no_active_plan": "Sense pla actiu",
    "create_plan_in_coach": "Crea'n un a la pàgina del Coach IA",
    "total_planned": "Total planificats ({label})",
    "completed_workouts": "Completats",
    "pending_workouts": "Pendents",
    "example_pace": "ex: 5:00 o 5:00-5:15",

    # === GENERAL ===
    "yes": "Sí",
    "no": "No",
    "cancel": "Cancel·lar",
    "save": "Guardar",
    "edit": "Editar",
    "delete": "Eliminar",
    "close": "Tancar",
    "confirm": "Confirmar",
    "back": "Tornar",
    "next": "Següent",
    "previous": "Anterior",
    "search": "Cercar",
    "filter": "Filtrar",
    "export": "Exportar",
    "import": "Importar",
    "refresh": "Actualitzar",
    "loading_label": "Carregant...",
    "error": "Error",
    "success": "Èxit",
    "warning": "Avís",
    "info": "Informació",

    # Day names
    "monday": "Dilluns",
    "tuesday": "Dimarts",
    "wednesday": "Dimecres",
    "thursday": "Dijous",
    "friday": "Divendres",
    "saturday": "Dissabte",
    "sunday": "Diumenge",
    "mon": "Dil",
    "tue": "Dim",
    "wed": "Dix",
    "thu": "Dij",
    "fri": "Div",
    "sat": "Dis",
    "sun": "Diu",

    # Month names
    "january": "Gener",
    "february": "Febrer",
    "march": "Març",
    "april": "Abril",
    "may": "Maig",
    "june": "Juny",
    "july": "Juliol",
    "august": "Agost",
    "september": "Setembre",
    "october": "Octubre",
    "november": "Novembre",
    "december": "Desembre",
}


def t(key: str, **kwargs) -> str:
    """
    Funció helper per obtenir strings traduïts.

    Args:
        key: Clau del string a obtenir
        **kwargs: Arguments per substituir en el string (format amb {})

    Returns:
        String traduït amb substitucions aplicades

    Example:
        >>> t("sync_error", error="Connection timeout")
        "No s'ha pogut sincronitzar: Connection timeout"
    """
    string = STRINGS_CA.get(key, f"[MISSING: {key}]")

    if kwargs:
        try:
            return string.format(**kwargs)
        except KeyError as e:
            return f"[FORMAT ERROR in '{key}': missing {e}]"

    return string


# Diccionaris específics per a mapeos de dades
DAY_NAMES_ES_TO_CA = {
    'Monday': 'Dilluns',
    'Tuesday': 'Dimarts',
    'Wednesday': 'Dimecres',
    'Thursday': 'Dijous',
    'Friday': 'Divendres',
    'Saturday': 'Dissabte',
    'Sunday': 'Diumenge',
}

DAY_NAMES_SHORT = {
    'Monday': 'Dil',
    'Tuesday': 'Dim',
    'Wednesday': 'Dix',
    'Thursday': 'Dij',
    'Friday': 'Div',
    'Saturday': 'Dis',
    'Sunday': 'Diu',
}

# Workout types mapping (database value -> display name)
WORKOUT_TYPES_DISPLAY = {
    'easy_run': 'Rodatge suau',
    'long_run': 'Tirada llarga',
    'intervals': 'Sèries',
    'tempo': 'Tempo',
    'recovery': 'Recuperació',
    'quality': 'Qualitat',
}

# Training zones
TRAINING_ZONES_CA = {
    'easy': 'Fàcil',
    'moderate': 'Moderat',
    'tempo': 'Tempo',
    'fast': 'Ràpid',
}
