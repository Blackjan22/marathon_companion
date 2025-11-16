# utils/gemini_tools.py
"""
Declaraciones de herramientas (tools) para Gemini Function Calling.
Define el schema de cada función que el modelo puede invocar.
"""

from google.generativeai.types import FunctionDeclaration, Tool


# Declaración de herramientas individuales
get_recent_activities_declaration = FunctionDeclaration(
    name="get_recent_activities",
    description="Obtiene las actividades de running de los últimos N días con sus estadísticas (distancia, ritmo, etc.)",
    parameters={
        "type": "object",
        "properties": {
            "days": {
                "type": "integer",
                "description": "Número de días hacia atrás para buscar actividades. Por defecto 7 días."
            }
        },
        "required": []
    }
)

get_weekly_stats_declaration = FunctionDeclaration(
    name="get_weekly_stats",
    description="Obtiene estadísticas agregadas por semana de las últimas N semanas (kilómetros totales, número de entrenamientos, ritmo medio por semana)",
    parameters={
        "type": "object",
        "properties": {
            "weeks": {
                "type": "integer",
                "description": "Número de semanas hacia atrás para analizar. Por defecto 4 semanas."
            }
        },
        "required": []
    }
)

get_activity_details_declaration = FunctionDeclaration(
    name="get_activity_details",
    description="Obtiene los detalles completos de una actividad específica, incluyendo TODOS los laps/intervalos (series, repeticiones, etc.). Analiza los laps para entender la estructura del entrenamiento. IMPORTANTE: Usa el ID exacto (como string) que obtienes de get_recent_activities.",
    parameters={
        "type": "object",
        "properties": {
            "activity_id": {
                "type": "string",
                "description": "ID de la actividad en Strava (debe ser el ID completo obtenido de get_recent_activities, como string para preservar precisión numérica)"
            }
        },
        "required": ["activity_id"]
    }
)

get_current_plan_declaration = FunctionDeclaration(
    name="get_current_plan",
    description="Obtiene el plan de entrenamiento activo actual con todos sus entrenamientos planificados (pendientes, completados, saltados)",
    parameters={
        "type": "object",
        "properties": {},
        "required": []
    }
)


create_training_plan_declaration = FunctionDeclaration(
    name="create_training_plan",
    description="Crea un nuevo plan de entrenamiento semanal con los entrenamientos especificados. Úsalo cuando el usuario pida crear/planificar entrenamientos.",
    parameters={
        "type": "object",
        "properties": {
            "week_start_date": {
                "type": "string",
                "description": "Fecha de inicio de la semana en formato YYYY-MM-DD (lunes de la semana a planificar)"
            },
            "workouts": {
                "type": "array",
                "description": "Lista de entrenamientos a incluir en el plan",
                "items": {
                    "type": "object",
                    "properties": {
                        "date": {
                            "type": "string",
                            "description": "Fecha del entrenamiento en formato YYYY-MM-DD"
                        },
                        "workout_type": {
                            "type": "string",
                            "description": "Tipo de entrenamiento: 'calidad', 'tirada_larga', 'rodaje', 'recuperacion', 'tempo', 'series'"
                        },
                        "distance_km": {
                            "type": "number",
                            "description": "Distancia planificada en kilómetros"
                        },
                        "description": {
                            "type": "string",
                            "description": "Descripción detallada del entrenamiento (objetivo, estructura, etc.)"
                        },
                        "pace_objective": {
                            "type": "string",
                            "description": "Ritmo objetivo en formato min/km (ej: '5:00' o '4:30-5:00')"
                        },
                        "notes": {
                            "type": "string",
                            "description": "Notas adicionales sobre el entrenamiento"
                        }
                    },
                    "required": ["date", "workout_type", "distance_km"]
                }
            },
            "goal": {
                "type": "string",
                "description": "Objetivo del plan (ej: 'Preparación media maratón', 'Mantenimiento', 'Aumentar volumen')"
            },
            "notes": {
                "type": "string",
                "description": "Notas adicionales sobre el plan completo"
            }
        },
        "required": ["week_start_date", "workouts"]
    }
)

update_workout_declaration = FunctionDeclaration(
    name="update_workout",
    description="Actualiza/modifica un entrenamiento planificado existente. Úsalo para cambiar fecha, distancia, ritmo o cualquier otro campo de un entreno ya planificado.",
    parameters={
        "type": "object",
        "properties": {
            "workout_id": {
                "type": "string",
                "description": "ID del entrenamiento planificado a actualizar (como string)"
            },
            "changes": {
                "type": "object",
                "description": "Diccionario con los campos a actualizar",
                "properties": {
                    "date": {
                        "type": "string",
                        "description": "Nueva fecha en formato YYYY-MM-DD"
                    },
                    "workout_type": {
                        "type": "string",
                        "description": "Nuevo tipo de entrenamiento"
                    },
                    "distance_km": {
                        "type": "number",
                        "description": "Nueva distancia en kilómetros"
                    },
                    "description": {
                        "type": "string",
                        "description": "Nueva descripción"
                    },
                    "pace_objective": {
                        "type": "string",
                        "description": "Nuevo ritmo objetivo"
                    },
                    "notes": {
                        "type": "string",
                        "description": "Nuevas notas"
                    },
                    "status": {
                        "type": "string",
                        "description": "Nuevo estado: 'pending', 'completed', 'skipped'"
                    }
                }
            }
        },
        "required": ["workout_id", "changes"]
    }
)

add_workout_to_current_plan_declaration = FunctionDeclaration(
    name="add_workout_to_current_plan",
    description="Añade UN SOLO entrenamiento al plan activo existente sin crear un plan nuevo. Úsalo cuando el usuario quiera añadir entrenos adicionales al plan que ya tiene. IMPORTANTE: NO uses esta función para crear planes completos desde cero, usa create_training_plan para eso.",
    parameters={
        "type": "object",
        "properties": {
            "date": {
                "type": "string",
                "description": "Fecha del entrenamiento en formato YYYY-MM-DD"
            },
            "workout_type": {
                "type": "string",
                "description": "Tipo de entrenamiento: 'calidad', 'tirada_larga', 'rodaje', 'recuperacion', 'tempo', 'series'"
            },
            "distance_km": {
                "type": "number",
                "description": "Distancia planificada en kilómetros"
            },
            "description": {
                "type": "string",
                "description": "Descripción detallada del entrenamiento"
            },
            "pace_objective": {
                "type": "string",
                "description": "Ritmo objetivo en formato min/km (ej: '5:00' o '4:30-5:00')"
            },
            "notes": {
                "type": "string",
                "description": "Notas adicionales sobre el entrenamiento"
            }
        },
        "required": ["date", "workout_type", "distance_km"]
    }
)

delete_workout_declaration = FunctionDeclaration(
    name="delete_workout",
    description="Elimina un entrenamiento planificado del plan actual. Úsalo cuando el usuario quiera borrar/eliminar un entreno específico o limpiar entrenamientos pendientes.",
    parameters={
        "type": "object",
        "properties": {
            "workout_id": {
                "type": "string",
                "description": "ID del entrenamiento a eliminar (como string). Obtén este ID usando get_current_plan()."
            }
        },
        "required": ["workout_id"]
    }
)

get_runner_profile_declaration = FunctionDeclaration(
    name="get_runner_profile",
    description="Obtiene el perfil completo del corredor (antropometría, PRs, objetivos, filosofía de entrenamiento). IMPORTANTE: Usa esta función al inicio de cada conversación para personalizar tus recomendaciones.",
    parameters={
        "type": "object",
        "properties": {},
        "required": []
    }
)

analyze_performance_trends_declaration = FunctionDeclaration(
    name="analyze_performance_trends",
    description="Analiza tendencias de rendimiento (FC vs ritmo) para detectar mejoras aeróbicas o señales de fatiga. Examina la evolución de ritmo y FC en entrenamientos similares. Úsalo para evaluar el estado de forma antes de planificar.",
    parameters={
        "type": "object",
        "properties": {
            "weeks": {
                "type": "integer",
                "description": "Número de semanas hacia atrás para analizar. Por defecto 4 semanas."
            }
        },
        "required": []
    }
)

predict_race_times_declaration = FunctionDeclaration(
    name="predict_race_times",
    description="Predice tiempos de carrera usando la fórmula de Riegel (T2 = T1 * (D2/D1)^1.06). Útil para estimar rendimiento en otras distancias basándote en una marca real. Por ejemplo: 10k en 43:20 → predecir tiempo en media maratón.",
    parameters={
        "type": "object",
        "properties": {
            "current_race_distance_km": {
                "type": "number",
                "description": "Distancia de la marca actual en kilómetros (ej: 10.0 para 10k, 21.0975 para media)"
            },
            "current_time_minutes": {
                "type": "number",
                "description": "Tiempo en la distancia actual en minutos decimales (ej: 43.33 para 43:20)"
            },
            "target_race_distance_km": {
                "type": "number",
                "description": "Distancia objetivo para la predicción en kilómetros (ej: 21.0975 para media maratón)"
            }
        },
        "required": ["current_race_distance_km", "current_time_minutes", "target_race_distance_km"]
    }
)

analyze_training_load_advanced_declaration = FunctionDeclaration(
    name="analyze_training_load_advanced",
    description="Análisis avanzado de carga de entrenamiento con detección de sobreentrenamiento. Examina volumen, intensidad, FC, y palabras clave de fatiga en notas privadas. Proporciona warnings y recomendaciones específicas. Úsalo antes de proponer planes exigentes.",
    parameters={
        "type": "object",
        "properties": {},
        "required": []
    }
)


# Agrupar todas las herramientas en un Tool
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
