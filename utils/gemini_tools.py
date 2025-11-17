# utils/gemini_tools.py
"""
Declaracions d'eines (tools) per Gemini Function Calling.
Defineix l'esquema de cada funció que el model pot invocar.
"""

from google.generativeai.types import FunctionDeclaration, Tool


# Declaració d'eines individuals
get_recent_activities_declaration = FunctionDeclaration(
    name="get_recent_activities",
    description="Obté les activitats de running dels últims N dies amb les seves estadístiques (distància, ritme, etc.)",
    parameters={
        "type": "object",
        "properties": {
            "days": {
                "type": "integer",
                "description": "Nombre de dies enrere per buscar activitats. Per defecte 7 dies."
            }
        },
        "required": []
    }
)

get_weekly_stats_declaration = FunctionDeclaration(
    name="get_weekly_stats",
    description="Obté estadístiques agregades per setmana de les últimes N setmanes (quilòmetres totals, nombre d'entrenaments, ritme mitjà per setmana)",
    parameters={
        "type": "object",
        "properties": {
            "weeks": {
                "type": "integer",
                "description": "Nombre de setmanes enrere per analitzar. Per defecte 4 setmanes."
            }
        },
        "required": []
    }
)

get_activity_details_declaration = FunctionDeclaration(
    name="get_activity_details",
    description="Obté els detalls complets d'una activitat específica, incloent TOTS els laps/intervals (sèries, repeticions, etc.). Analitza els laps per entendre l'estructura de l'entrenament. IMPORTANT: Usa l'ID exacte (com a string) que obtens de get_recent_activities.",
    parameters={
        "type": "object",
        "properties": {
            "activity_id": {
                "type": "string",
                "description": "ID de l'activitat a Strava (ha de ser l'ID complet obtingut de get_recent_activities, com a string per preservar precisió numèrica)"
            }
        },
        "required": ["activity_id"]
    }
)

get_current_plan_declaration = FunctionDeclaration(
    name="get_current_plan",
    description="Obté el pla d'entrenament actiu actual amb tots els seus entrenaments planificats (pendents, completats, saltats)",
    parameters={
        "type": "object",
        "properties": {},
        "required": []
    }
)


create_training_plan_declaration = FunctionDeclaration(
    name="create_training_plan",
    description="Crea un nou pla d'entrenament setmanal amb els entrenaments especificats. Usa-ho quan l'usuari demani crear/planificar entrenaments.",
    parameters={
        "type": "object",
        "properties": {
            "week_start_date": {
                "type": "string",
                "description": "Data d'inici de la setmana en format YYYY-MM-DD (dilluns de la setmana a planificar)"
            },
            "workouts": {
                "type": "array",
                "description": "Llista d'entrenaments a incloure al pla",
                "items": {
                    "type": "object",
                    "properties": {
                        "date": {
                            "type": "string",
                            "description": "Data de l'entrenament en format YYYY-MM-DD"
                        },
                        "workout_type": {
                            "type": "string",
                            "description": "Tipus d'entrenament: 'calidad', 'tirada_larga', 'rodaje', 'recuperacion', 'tempo', 'series'"
                        },
                        "distance_km": {
                            "type": "number",
                            "description": "Distància planificada en quilòmetres"
                        },
                        "description": {
                            "type": "string",
                            "description": "Descripció detallada de l'entrenament (objectiu, estructura, etc.)"
                        },
                        "pace_objective": {
                            "type": "string",
                            "description": "Ritme objectiu en format min/km (ex: '5:00' o '4:30-5:00')"
                        },
                        "notes": {
                            "type": "string",
                            "description": "Notes addicionals sobre l'entrenament"
                        }
                    },
                    "required": ["date", "workout_type", "distance_km"]
                }
            },
            "goal": {
                "type": "string",
                "description": "Objectiu del pla (ex: 'Preparació mitja marató', 'Manteniment', 'Augmentar volum')"
            },
            "notes": {
                "type": "string",
                "description": "Notes addicionals sobre el pla complet"
            }
        },
        "required": ["week_start_date", "workouts"]
    }
)

update_workout_declaration = FunctionDeclaration(
    name="update_workout",
    description="Actualitza/modifica un entrenament planificat existent. Usa-ho per canviar data, distància, ritme o qualsevol altre camp d'un entrenament ja planificat.",
    parameters={
        "type": "object",
        "properties": {
            "workout_id": {
                "type": "string",
                "description": "ID de l'entrenament planificat a actualitzar (com a string)"
            },
            "changes": {
                "type": "object",
                "description": "Diccionari amb els camps a actualitzar",
                "properties": {
                    "date": {
                        "type": "string",
                        "description": "Nova data en format YYYY-MM-DD"
                    },
                    "workout_type": {
                        "type": "string",
                        "description": "Nou tipus d'entrenament"
                    },
                    "distance_km": {
                        "type": "number",
                        "description": "Nova distància en quilòmetres"
                    },
                    "description": {
                        "type": "string",
                        "description": "Nova descripció"
                    },
                    "pace_objective": {
                        "type": "string",
                        "description": "Nou ritme objectiu"
                    },
                    "notes": {
                        "type": "string",
                        "description": "Noves notes"
                    },
                    "status": {
                        "type": "string",
                        "description": "Nou estat: 'pending', 'completed', 'skipped'"
                    }
                }
            }
        },
        "required": ["workout_id", "changes"]
    }
)

add_workout_to_current_plan_declaration = FunctionDeclaration(
    name="add_workout_to_current_plan",
    description="Afegeix UN SOL entrenament al pla actiu existent sense crear un pla nou. Usa-ho quan l'usuari vulgui afegir entrenos addicionals al pla que ja té. IMPORTANT: NO usis aquesta funció per crear plans complets des de zero, usa create_training_plan per això.",
    parameters={
        "type": "object",
        "properties": {
            "date": {
                "type": "string",
                "description": "Data de l'entrenament en format YYYY-MM-DD"
            },
            "workout_type": {
                "type": "string",
                "description": "Tipus d'entrenament: 'calidad', 'tirada_larga', 'rodaje', 'recuperacion', 'tempo', 'series'"
            },
            "distance_km": {
                "type": "number",
                "description": "Distància planificada en quilòmetres"
            },
            "description": {
                "type": "string",
                "description": "Descripció detallada de l'entrenament"
            },
            "pace_objective": {
                "type": "string",
                "description": "Ritme objectiu en format min/km (ex: '5:00' o '4:30-5:00')"
            },
            "notes": {
                "type": "string",
                "description": "Notes addicionals sobre l'entrenament"
            }
        },
        "required": ["date", "workout_type", "distance_km"]
    }
)

delete_workout_declaration = FunctionDeclaration(
    name="delete_workout",
    description="Elimina un entrenament planificat del pla actual. Usa-ho quan l'usuari vulgui esborrar/eliminar un entrenament específic o netejar entrenaments pendents.",
    parameters={
        "type": "object",
        "properties": {
            "workout_id": {
                "type": "string",
                "description": "ID de l'entrenament a eliminar (com a string). Obté aquest ID usant get_current_plan()."
            }
        },
        "required": ["workout_id"]
    }
)

get_runner_profile_declaration = FunctionDeclaration(
    name="get_runner_profile",
    description="Obté el perfil complet del corredor (antropometria, PRs, objectius, filosofia d'entrenament). IMPORTANT: Usa aquesta funció a l'inici de cada conversa per personalitzar les teves recomanacions.",
    parameters={
        "type": "object",
        "properties": {},
        "required": []
    }
)

analyze_performance_trends_declaration = FunctionDeclaration(
    name="analyze_performance_trends",
    description="Analitza tendències de rendiment (FC vs ritme) per detectar millores aeròbiques o senyals de fatiga. Examina l'evolució de ritme i FC en entrenaments similars. Usa-ho per avaluar l'estat de forma abans de planificar.",
    parameters={
        "type": "object",
        "properties": {
            "weeks": {
                "type": "integer",
                "description": "Nombre de setmanes enrere per analitzar. Per defecte 4 setmanes."
            }
        },
        "required": []
    }
)

predict_race_times_declaration = FunctionDeclaration(
    name="predict_race_times",
    description="Prediu temps de carrera usant la fórmula de Riegel (T2 = T1 * (D2/D1)^1.06). Útil per estimar rendiment en altres distàncies basant-te en una marca real. Per exemple: 10k en 43:20 → predir temps en mitja marató.",
    parameters={
        "type": "object",
        "properties": {
            "current_race_distance_km": {
                "type": "number",
                "description": "Distància de la marca actual en quilòmetres (ex: 10.0 per 10k, 21.0975 per mitja)"
            },
            "current_time_minutes": {
                "type": "number",
                "description": "Temps a la distància actual en minuts decimals (ex: 43.33 per 43:20)"
            },
            "target_race_distance_km": {
                "type": "number",
                "description": "Distància objectiu per la predicció en quilòmetres (ex: 21.0975 per mitja marató)"
            }
        },
        "required": ["current_race_distance_km", "current_time_minutes", "target_race_distance_km"]
    }
)

analyze_training_load_advanced_declaration = FunctionDeclaration(
    name="analyze_training_load_advanced",
    description="Anàlisi avançat de càrrega d'entrenament amb detecció de sobreentrament. Examina volum, intensitat, FC, i paraules clau de fatiga en notes privades. Proporciona avisos i recomanacions específiques. Usa-ho abans de proposar plans exigents.",
    parameters={
        "type": "object",
        "properties": {},
        "required": []
    }
)


# Agrupar totes les eines en un Tool
running_coach_tools = Tool(
    function_declarations=[
        get_recent_activities_declaration,
        get_weekly_stats_declaration,
        get_activity_details_declaration,
        get_current_plan_declaration,
        create_training_plan_declaration,
        update_workout_declaration,
        add_workout_to_current_plan_declaration,
        delete_workout_declaration,
        get_runner_profile_declaration,
        analyze_performance_trends_declaration,
        predict_race_times_declaration,
        analyze_training_load_advanced_declaration,
    ]
)
