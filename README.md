# 🏃 Running Analytics con Coach IA

Aplicación local completa para descargar, analizar y visualizar entrenamientos de running desde Strava, con planificación inteligente mediante IA.

---

## 📦 Estructura del proyecto

```
running_analytics/
├── data/                           # Base de datos SQLite
│   └── strava_activities.db
├── src/                            # Código fuente principal
│   ├── pages/                      # Páginas de Streamlit
│   │   ├── 1_Dashboard_General.py      # Dashboard con métricas y análisis
│   │   ├── 2_Histórico_Completo.py     # Vista detallada de actividades
│   │   ├── 3_Planificacion.py          # Gestión de planes de entrenamiento
│   │   └── 4_Coach_IA.py               # Chatbot con IA para entrenamiento
│   ├── utils/                      # Utilidades
│   │   ├── data_processing.py          # Procesamiento de datos
│   │   ├── formatting.py               # Formateo de valores
│   │   ├── planning.py                 # Gestión de planes
│   │   ├── ai_functions.py             # Funciones para Gemini
│   │   └── ai_context.py               # Sistema de contexto/memoria IA
│   ├── My Runs Analytics.py        # Página principal
│   ├── strava_client.py            # Cliente API Strava
│   ├── sync_strava.py              # Script de sincronización
│   ├── run_app.py                  # Script para lanzar la app
│   └── delete_activity.py          # Utilidad para eliminar actividades
├── .env                            # Variables sensibles (no versionar)
├── requirements.txt
└── README.md
```

---

## 🚀 Funcionalidad actual

### ✅ Autenticación con Strava API
- Conexión vía OAuth2 usando Client ID, Client Secret y Refresh Token.
- Renovación automática del `access_token` mediante el `refresh_token`.

### ✅ Sincronización de actividades
- Descarga automática de todas las actividades de tipo `Run` desde Strava.
- Acceso al detalle completo de cada actividad incluyendo splits y laps.
- Sincronización incremental: solo descarga actividades nuevas.

### ✅ Almacenamiento estructurado en SQLite
- Base de datos local en `data/strava_activities.db`.
- Tablas para actividades: `activities`, `splits` y `laps`.
- Tablas para planificación: `training_plans`, `planned_workouts`, `workout_feedback`.
- Tabla para historial de IA: `chat_history`.

### ✅ Dashboard interactivo con Streamlit
- **Dashboard General**: Métricas clave, gráficos de progreso y recomendaciones de entrenamiento.
- **Histórico Completo**: Tabla detallada con filtros, análisis de actividades individuales y visualización de laps.
- **Planificación**: Vista de calendario con entrenamientos planificados vs realizados.
- **Perfil del Corredor**: Configura tus objetivos, PRs y filosofía de entrenamiento.
- **Coach IA**: Chatbot con Gemini para análisis profundo y planificación personalizada.
- Botón de sincronización integrado para actualizar actividades desde Strava.

### 🆕 Sistema de Planificación de Entrenamientos
- **Vista de calendario semanal**: Visualiza entrenamientos planificados de las próximas semanas.
- **Vinculación automática**: Conecta actividades de Strava con entrenamientos planificados.
- **Gestión de estados**: Marca entrenamientos como completados, pendientes o saltados.
- **Seguimiento de progreso**: Estadísticas de cumplimiento del plan.
- **Feedback integrado**: Las notas privadas de Strava se sincronizan automáticamente con la app.

### 👤 Perfil del Corredor (NUEVO)
- **Configuración completa**: Define tu nombre, altura, peso, edad y VO2max estimado
- **Zonas de entrenamiento**: Configura tus ritmos (umbral, fácil min/max) para recomendaciones personalizadas
- **Objetivo actual**: Define tu carrera objetivo, distancia y fecha
- **Filosofía de entrenamiento**: Describe tu enfoque (días disponibles, prioridades, restricciones)
- **Records personales (PRs)**: Almacena tus mejores marcas en 5K, 10K, Media Maratón y Maratón
- **Integración con Coach IA**: El Coach consulta automáticamente tu perfil para personalizar recomendaciones
- **Calculadora de días hasta objetivo**: Visualiza cuánto tiempo tienes hasta tu carrera

### 🤖 Coach con Inteligencia Artificial (Gemini) - MEJORADO
- **Entrenador analítico y data-driven**: Prioriza salud y consistencia sobre rendimiento puro
- **Modelo robusto**: Usa `gemini-2.5-flash` optimizado para function calling y análisis complejo
- **Razonamiento fisiológico**: Explica el "por qué" de cada entrenamiento (sistemas energéticos, adaptaciones)
- **Análisis profundo de tendencias**: Detecta mejoras aeróbicas o señales de fatiga analizando FC vs ritmo
- **Predicciones de tiempos**: Fórmula de Riegel para estimar rendimiento en otras distancias
- **Detección de sobreentrenamiento**: Analiza volumen, FC, y palabras clave de fatiga en notas privadas
- **Respuestas estructuradas**: Formato claro con secciones (Filosofía → Análisis → Plan → Estrategia → Notas)
- **Personalización total**: Consulta tu perfil (objetivos, PRs, filosofía) para adaptar recomendaciones
- **Análisis de laps ilimitado**: Procesa todos los laps de entrenamientos (series, intervalos) sin limitaciones
- **Memoria contextual mejorada**: Carga automáticamente perfil, notas recientes, y análisis de tendencias
- **Conversaciones persistentes**: Historial guardado en base de datos
- **Transparencia**: Puedes ver qué funciones ejecuta el coach en cada respuesta

**12 Funciones disponibles para el Coach IA:**

*Perfil y contexto:*
- `get_runner_profile()`: Ver perfil completo (objetivos, PRs, filosofía de entrenamiento)

*Consulta de datos:*
- `get_recent_activities(days)`: Ver entrenamientos de los últimos N días
- `get_weekly_stats(weeks)`: Estadísticas agregadas por semana
- `get_activity_details(activity_id)`: Detalles completos con laps y notas privadas

*Análisis avanzado (NUEVO):*
- `analyze_performance_trends(weeks)`: Detecta mejoras aeróbicas o fatiga (FC vs ritmo)
- `predict_race_times(current_dist, current_time, target_dist)`: Calculadora de equivalencias
- `analyze_training_load_advanced()`: Detección de sobreentrenamiento con warnings y recomendaciones

*Planificación:*
- `get_current_plan()`: Consultar plan activo
- `create_training_plan(...)`: Crear planes completos nuevos
- `add_workout_to_current_plan(...)`: Añadir entrenamientos al plan activo
- `update_workout(workout_id, changes)`: Modificar entrenamientos planificados
- `delete_workout(workout_id)`: Eliminar entrenamientos del plan

El coach decide automáticamente qué funciones ejecutar según tu pregunta. Ejemplos:
- "¿Cómo voy respecto a hace un mes?" → Ejecuta `analyze_performance_trends(4)` y analiza evolución
- "Si corro 10k en 43:20, ¿qué tiempo puedo hacer en media?" → Ejecuta `predict_race_times(10, 43.33, 21.0975)`
- "Planifica las próximas 2 semanas" → Ejecuta `get_runner_profile()`, `analyze_training_load_advanced()`, `analyze_performance_trends()` y crea el plan
- "¿Tengo señales de sobreentrenamiento?" → Ejecuta `analyze_training_load_advanced()` y da recomendaciones

---

## ⚙️ Instalación y configuración

### 1. Clonar el proyecto
```bash
git clone git@github.com:tuusuario/running_analytics.git
cd running_analytics
```

### 2. Crear entorno virtual
```bash
python -m venv .venv
source .venv/bin/activate  # En Windows: .venv\Scripts\activate
```

### 3. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 4. Configurar credenciales
Crea un archivo `.env` en la raíz del proyecto con tus credenciales:
```
# Credenciales de Strava
STRAVA_CLIENT_ID=tu_client_id
STRAVA_CLIENT_SECRET=tu_client_secret
STRAVA_REFRESH_TOKEN=tu_refresh_token

# API Key de Gemini (para el Coach IA)
GEMINI_API_KEY=tu_gemini_api_key
```

**Cómo obtener las credenciales:**
- **Strava API**: Crea una aplicación en [Strava Developers](https://developers.strava.com/)
- **Gemini API**: Obtén tu key en [Google AI Studio](https://aistudio.google.com/apikey)

### 5. Ejecutar la aplicación
```bash
python src/run_app.py
```

La aplicación se abrirá automáticamente en tu navegador en `http://localhost:8501`.

---

## ☁️ Despliegue en Streamlit Cloud (Acceso móvil)

La aplicación puede desplegarse gratuitamente en Streamlit Cloud para acceder desde cualquier dispositivo.

### Arquitectura de despliegue

- **Local**: SQLite (`data/strava_activities.db`)
- **Cloud**: PostgreSQL (Supabase) - base de datos persistente gratuita

La aplicación detecta automáticamente el entorno y usa la base de datos apropiada.

### Pasos para desplegar

#### 1. Crear base de datos en Supabase (5 min)

1. Ve a [https://supabase.com](https://supabase.com) y crea una cuenta gratuita
2. Crea un nuevo proyecto:
   - Nombre: `running-analytics` (o el que prefieras)
   - Contraseña: **guárdala bien**, la necesitarás después
   - Región: Europe West (Frankfurt) - más cercana a España
3. Espera a que se cree el proyecto (~2 minutos)
4. Ve a **Settings > Database**
5. En **Connection String**, copia la **URI** en modo "Session" (no "Transaction")
   - Formato: `postgresql://postgres.xxxxx:[YOUR-PASSWORD]@aws-0-eu-central-1.pooler.supabase.com:6543/postgres`
   - Reemplaza `[YOUR-PASSWORD]` con tu contraseña real

#### 2. Inicializar esquema de base de datos (5 min)

Supabase necesita que creemos las tablas manualmente la primera vez:

1. En Supabase, ve a **SQL Editor**
2. Ejecuta este script para crear todas las tablas:

```sql
CREATE TABLE IF NOT EXISTS activities (
    id BIGINT PRIMARY KEY,
    name TEXT,
    description TEXT,
    private_note TEXT,
    start_date_local TEXT,
    distance REAL,
    moving_time INTEGER,
    elapsed_time INTEGER,
    average_speed REAL,
    average_heartrate REAL,
    total_elevation_gain REAL,
    type TEXT,
    sport_type TEXT
);

CREATE TABLE IF NOT EXISTS splits (
    activity_id BIGINT,
    split INTEGER,
    distance REAL,
    elapsed_time INTEGER,
    elevation_difference REAL,
    average_speed REAL,
    FOREIGN KEY (activity_id) REFERENCES activities(id)
);

CREATE TABLE IF NOT EXISTS laps (
    activity_id BIGINT NOT NULL,
    lap_id BIGINT,
    lap_index INTEGER,
    name TEXT,
    split INTEGER,
    start_date_local TEXT,
    elapsed_time INTEGER,
    moving_time INTEGER,
    distance REAL,
    average_speed REAL,
    max_speed REAL,
    start_index INTEGER,
    end_index INTEGER,
    total_elevation_gain REAL,
    pace_zone INTEGER,
    PRIMARY KEY (activity_id, lap_index),
    FOREIGN KEY (activity_id) REFERENCES activities(id)
);

CREATE TABLE IF NOT EXISTS training_plans (
    id SERIAL PRIMARY KEY,
    week_start_date TEXT NOT NULL,
    week_number INTEGER,
    goal TEXT,
    notes TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'active'
);

CREATE TABLE IF NOT EXISTS planned_workouts (
    id SERIAL PRIMARY KEY,
    plan_id INTEGER,
    date TEXT NOT NULL,
    workout_type TEXT,
    distance_km REAL,
    description TEXT,
    pace_objective TEXT,
    notes TEXT,
    status TEXT DEFAULT 'pending',
    linked_activity_id BIGINT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (plan_id) REFERENCES training_plans(id),
    FOREIGN KEY (linked_activity_id) REFERENCES activities(id)
);

CREATE TABLE IF NOT EXISTS workout_feedback (
    id SERIAL PRIMARY KEY,
    planned_workout_id INTEGER,
    activity_id BIGINT,
    sensations TEXT,
    completed_as_planned INTEGER DEFAULT 1,
    notes TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (planned_workout_id) REFERENCES planned_workouts(id),
    FOREIGN KEY (activity_id) REFERENCES activities(id)
);

CREATE TABLE IF NOT EXISTS chat_history (
    id SERIAL PRIMARY KEY,
    role TEXT NOT NULL,
    content TEXT,
    timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
    context_summary TEXT
);

CREATE TABLE IF NOT EXISTS runner_profile (
    id SERIAL PRIMARY KEY,
    name TEXT,
    height_cm REAL,
    weight_kg REAL,
    age INTEGER,
    vo2max_estimate REAL,
    threshold_pace TEXT,
    easy_pace_min TEXT,
    easy_pace_max TEXT,
    training_philosophy TEXT,
    current_goal TEXT,
    goal_race_date TEXT,
    goal_race_distance TEXT,
    pr_5k TEXT,
    pr_10k TEXT,
    pr_half TEXT,
    pr_marathon TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);
```

3. Haz clic en **Run** para ejecutar el script

#### 3. Desplegar en Streamlit Cloud (10 min)

1. **Sube tu código a GitHub** (si no lo has hecho):
   ```bash
   git add .
   git commit -m "Preparar para deploy en Streamlit Cloud"
   git push origin main
   ```

2. **Ve a [https://share.streamlit.io](https://share.streamlit.io)** e inicia sesión con GitHub

3. **Crea una nueva app**:
   - Repository: `tu-usuario/marathon_companion`
   - Branch: `main`
   - Main file path: `src/My Runs Analytics.py`

4. **Configura los secrets**:
   - Haz clic en **Advanced settings**
   - En **Secrets**, pega esto (con tus valores reales):

```toml
[database]
url = "postgresql://postgres.xxxxx:TU_PASSWORD_REAL@aws-0-eu-central-1.pooler.supabase.com:6543/postgres"

STRAVA_CLIENT_ID = "tu_client_id"
STRAVA_CLIENT_SECRET = "tu_client_secret"
STRAVA_REFRESH_TOKEN = "tu_refresh_token"
GEMINI_API_KEY = "tu_gemini_api_key"
```

5. Haz clic en **Deploy**

6. Espera ~3 minutos a que se despliegue

#### 4. Sincronizar datos inicialmente

**IMPORTANTE**: La primera vez que uses la app en Streamlit Cloud, la base de datos estará vacía. Debes sincronizar tus actividades desde Strava:

1. Abre tu app en Streamlit Cloud
2. Usa el botón **"🔄 Refrescar actividades"** en el sidebar
3. Espera a que descargue todas tus actividades (puede tardar varios minutos la primera vez)
4. Una vez completado, todos tus datos estarán en Supabase y podrás usar la app normalmente

### Notas importantes

- **Plan gratuito de Streamlit Cloud**: 2 apps públicas, recursos compartidos (suficiente para uso personal)
- **Plan gratuito de Supabase**: 500MB de base de datos, 2GB de transferencia/mes (más que suficiente para running analytics)
- **Persistencia de datos**: Los datos están en Supabase, **no** en Streamlit Cloud. Aunque reinicies la app, tus datos permanecen
- **Sincronización**: Debes sincronizar manualmente desde la app cuando tengas nuevas actividades en Strava
- **Acceso móvil**: Una vez desplegado, accede desde cualquier dispositivo con la URL de Streamlit Cloud

### Solución de problemas

**Error de conexión a la base de datos:**
- Verifica que la URL de Supabase sea correcta y tenga la contraseña real (no `[YOUR-PASSWORD]`)
- Comprueba que el esquema de base de datos se haya creado correctamente

**La app no se despliega:**
- Verifica que `requirements.txt` incluya `psycopg2-binary`
- Comprueba que el path al archivo principal sea correcto: `src/My Runs Analytics.py`

**No aparecen actividades:**
- Usa el botón "🔄 Refrescar actividades" la primera vez
- Verifica que tus credenciales de Strava sean correctas

---

## 🗃️ Estructura de la base de datos

La base de datos se crea automáticamente en `data/strava_activities.db` la primera vez que se sincroniza con Strava.

**Tecnología:** SQLite - Base de datos local, ligera y sin servidor (módulo `sqlite3` integrado en Python)

**Ubicación:** `data/strava_activities.db`

---

### Tabla `activities`

Contiene una fila por cada entrenamiento de tipo `Run`.

| Columna               | Tipo       | Descripción                                 |
|-----------------------|------------|---------------------------------------------|
| id                    | INTEGER PK | ID único de la actividad (Strava)           |
| name                  | TEXT       | Nombre de la actividad                      |
| description           | TEXT       | Descripción de la actividad                 |
| private_note          | TEXT       | Nota privada                                |
| start_date_local      | TEXT       | Fecha y hora local de inicio                |
| distance              | REAL       | Distancia en metros                         |
| moving_time           | INTEGER    | Tiempo en movimiento (segundos)             |
| elapsed_time          | INTEGER    | Tiempo total (segundos)                     |
| average_speed         | REAL       | Velocidad media (m/s)                       |
| average_heartrate     | REAL       | FC media (si disponible)                    |
| total_elevation_gain  | REAL       | Desnivel positivo acumulado (metros)        |
| type                  | TEXT       | Tipo de actividad (`Run`, etc.)             |
| sport_type            | TEXT       | Subtipo específico (`TrailRun`, etc.)       |

### Tabla `splits`

Contiene los parciales por kilómetro asociados a cada actividad.

| Columna              | Tipo     | Descripción                                      |
|----------------------|----------|--------------------------------------------------|
| activity_id          | INTEGER  | ID de la actividad (FK → `activities.id`)       |
| split                | INTEGER  | Número de parcial (1, 2, 3...)                   |
| distance             | REAL     | Distancia del split en metros                    |
| elapsed_time         | INTEGER  | Tiempo del parcial (segundos)                    |
| elevation_difference | REAL     | Diferencia de altitud                            |
| average_speed        | REAL     | Velocidad media del parcial (m/s)                |

### Tabla `laps`

Contiene los laps (vueltas/intervalos) de cada actividad según lo definido en Strava.

| Columna              | Tipo     | Descripción                                      |
|----------------------|----------|--------------------------------------------------|
| activity_id          | INTEGER  | ID de la actividad (FK → `activities.id`)       |
| lap_index            | INTEGER  | Número de lap                                     |
| name                 | TEXT     | Nombre del lap                                    |
| elapsed_time         | INTEGER  | Tiempo total del lap (segundos)                  |
| moving_time          | INTEGER  | Tiempo en movimiento del lap (segundos)          |
| distance             | REAL     | Distancia del lap (metros)                       |
| average_speed        | REAL     | Velocidad media (m/s)                            |
| max_speed            | REAL     | Velocidad máxima (m/s)                           |
| start_index          | INTEGER  | Índice de inicio                                  |
| end_index            | INTEGER  | Índice de fin                                     |
| total_elevation_gain | REAL     | Desnivel del lap (metros)                        |
| pace_zone            | INTEGER  | Zona de ritmo                                     |

### Tabla `training_plans`

Planes de entrenamiento semanales.

| Columna           | Tipo       | Descripción                                      |
|-------------------|------------|--------------------------------------------------|
| id                | INTEGER PK | ID único del plan                                |
| week_start_date   | TEXT       | Fecha de inicio de la semana                     |
| week_number       | INTEGER    | Número de semana del año                         |
| goal              | TEXT       | Objetivo del plan                                |
| notes             | TEXT       | Notas adicionales                                |
| created_at        | TEXT       | Fecha de creación                                |
| status            | TEXT       | Estado: active, completed                        |

### Tabla `planned_workouts`

Entrenamientos individuales planificados.

| Columna             | Tipo       | Descripción                                      |
|---------------------|------------|--------------------------------------------------|
| id                  | INTEGER PK | ID único del entreno                             |
| plan_id             | INTEGER    | FK → `training_plans.id`                         |
| date                | TEXT       | Fecha planificada                                |
| workout_type        | TEXT       | Tipo: calidad, tirada_larga, rodaje, etc.       |
| distance_km         | REAL       | Distancia planificada en km                      |
| description         | TEXT       | Descripción del entreno                          |
| pace_objective      | TEXT       | Ritmo objetivo                                   |
| notes               | TEXT       | Notas adicionales                                |
| status              | TEXT       | Estado: pending, completed, skipped              |
| linked_activity_id  | INTEGER    | FK → `activities.id` (si está completado)        |
| created_at          | TEXT       | Fecha de creación                                |

### Tabla `workout_feedback`

Feedback post-entrenamiento.

| Columna               | Tipo       | Descripción                                      |
|-----------------------|------------|--------------------------------------------------|
| id                    | INTEGER PK | ID único del feedback                            |
| planned_workout_id    | INTEGER    | FK → `planned_workouts.id`                       |
| activity_id           | INTEGER    | FK → `activities.id`                             |
| sensations            | TEXT       | Descripción de sensaciones                       |
| completed_as_planned  | INTEGER    | 1 si se completó según plan, 0 si no             |
| notes                 | TEXT       | Notas adicionales                                |
| created_at            | TEXT       | Fecha de creación                                |

### Tabla `chat_history`

Historial de conversaciones con el Coach IA.

| Columna          | Tipo       | Descripción                                      |
|------------------|------------|--------------------------------------------------|
| id               | INTEGER PK | ID único del mensaje                             |
| role             | TEXT       | Rol: user, assistant, system                     |
| content          | TEXT       | Contenido del mensaje                            |
| timestamp        | TEXT       | Fecha y hora del mensaje                         |
| context_summary  | TEXT       | Resumen del contexto (opcional)                  |

---

## 🔧 Scripts disponibles

- **`python src/run_app.py`**: Lanza la aplicación Streamlit
- **`python src/sync_strava.py`**: Sincroniza actividades desde Strava (script CLI)
- **`python src/delete_activity.py`**: Elimina una actividad de la base de datos

---

## 📖 Cómo usar el sistema completo

### Workflow típico semanal

#### 1️⃣ Sincronizar actividades
- Abre la aplicación y usa el botón "🔄 Refrescar actividades" en el sidebar
- O ejecuta `python src/sync_strava.py` desde terminal

#### 2️⃣ Consultar con el Coach IA
- Ve a la página "🤖 Coach IA"
- El sistema cargará automáticamente contexto de tus últimos entrenos
- Pregúntale por tus estadísticas: _"¿Cómo ha sido mi semana?"_
- Comparte tus sensaciones: _"Hoy me sentí muy cansado en el entreno"_

#### 3️⃣ Planificar la siguiente semana
- Pídele al coach que planifique: _"Necesito un plan para la próxima semana"_
- El coach te hará preguntas sobre tu disponibilidad y objetivos
- Creará un plan con 3 entrenamientos (típicamente)
- El plan se guardará automáticamente en la base de datos

#### 4️⃣ Seguir el plan
- Ve a "📅 Planificación" para ver tu calendario
- Visualiza los entrenamientos planificados de las próximas semanas
- Cada card muestra: tipo, distancia, ritmo objetivo

#### 5️⃣ Completar entrenamientos
- Realiza el entreno y sube la actividad a Strava
- **Añade tus sensaciones en las notas privadas de Strava** (se sincronizarán automáticamente)
- Sincroniza la app
- En la pestaña "🔗 Vincular Actividades":
  - Verás actividades recientes no vinculadas
  - Vincula cada actividad con su entreno planificado
- El estado cambiará automáticamente a "Completado"

#### 6️⃣ Iterar y ajustar
- Vuelve al Coach IA para discutir cómo fue la semana
- El coach puede leer tus notas privadas de Strava para entender tu feedback
- Ajusta el plan si es necesario
- Planifica la siguiente semana

### Ejemplos de preguntas al Coach IA

**Análisis:**
- "¿Cuál ha sido mi progresión en las últimas 4 semanas?"
- "Muéstrame mis mejores entrenos del último mes"
- "¿Cómo han sido mis ritmos en las tiradas largas?"

**Planificación:**
- "Quiero preparar una media maratón en 3 meses, crea un plan progresivo"
- "Esta semana solo puedo entrenar 2 días, ajusta el plan"
- "Necesito una semana de descarga, ¿qué me propones?"

**Análisis y ajustes:**
- "Revisa las notas de mi último entreno, ¿qué te parecen mis sensaciones?"
- "Hoy hice el entreno de series pero me costó mucho, ¿qué hacemos?"
- "Me he lesionado el gemelo, modifica el plan para esta semana"
- "Me sentí genial en la tirada larga, ¿puedo aumentar el volumen?"

### Tips para mejores resultados

1. **Usa las notas privadas de Strava**: Añade tus sensaciones en cada entreno, el coach las leerá automáticamente
2. **Vincula todas las actividades**: Esto permite al coach ver el cumplimiento del plan
3. **Pregunta el "por qué"**: El coach puede explicar el razonamiento detrás de cada entreno
4. **Usa el análisis de carga**: Revisa el sidebar en Coach IA para evitar sobreentrenamiento
5. **Recarga el contexto**: Si has hecho cambios, usa "🔄 Recargar contexto"

---

## 🚀 Próximas mejoras

- [x] **Function Calling para el Coach IA** ✅ (implementado)
- [ ] Gráficos de progresión en la página de Planificación
- [ ] Exportar planes a calendario (iCal)
- [ ] Notificaciones de entrenamientos pendientes
- [ ] Análisis de zonas de FC con IA
- [ ] Predictor de tiempos de carrera
- [ ] Integración con más plataformas (Garmin, Polar)
- [ ] Modo offline/sin IA para el chatbot
