# 🏃 marathon_companion

Aplicación local para descargar, analizar y visualizar entrenamientos de running desde Strava, con el objetivo de preparar una media maratón y generar resúmenes automáticos con GPT.

---

## 📦 Estructura del proyecto

marathon_companion/
├── data/                    # Entrenos descargados (SQLite)
│   └── strava_activities.db
├── notebooks/              # Análisis y pruebas
│   ├── explore_strava_db.ipynb
│   └── test_strava_api.ipynb
├── src/                    # Código fuente principal
│   └── strava_client.py
├── .env                    # Variables sensibles (no versionar)
├── requirements.txt
├── README.md

---

## 🚀 Funcionalidad actual

### ✅ Autenticación con Strava API
- Conexión vía OAuth2 usando Client ID, Client Secret y Refresh Token.
- Renovación automática del `access_token` mediante el `refresh_token`.

### ✅ Descarga completa de entrenamientos de carrera (`Run`)
- Se descargan **todas las actividades** del usuario autenticado de tipo `Run`.
- Se accede al detalle completo de cada actividad vía `/activities/{id}`.

### ✅ Almacenamiento estructurado en SQLite
- Actividades y splits se guardan en `data/strava_activities.db`.
- Dos tablas: `activities` y `splits`, relacionadas por `activity_id`.

### ✅ Exploración de datos en Jupyter
- Notebook `explore_strava_db.ipynb` para visualizar y analizar los entrenamientos descargados.

---

## ⚙️ Instalación

# 1. Clonar el proyecto
git clone git@github.com:tuusuario/marathon_companion.git
cd marathon_companion

# 2. Crear entorno virtual
python -m venv .venv
source .venv/bin/activate

# 3. Instalar dependencias
pip install -r requirements.txt
	-- Alternativa: pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org -r requirements.txt
pip freeze -> requirements.txt  

---

## 🗃️ Estructura de la base de datos

La base de datos se crea automáticamente en data/strava_activities.db la primera vez que se ejecuta download_and_store_runs().

📌 Tecnología usada
	•	SQLite: Base de datos local, ligera y sin servidor.
	•	Librería usada: sqlite3 (integrada en Python estándar).

📂 Ubicación
marathon_companion/data/strava_activities.db

---

### Tabla `activities`

Contiene una fila por cada entrenamiento de tipo `Run`.

| Columna               | Tipo       | Descripción                                 |
|-----------------------|------------|---------------------------------------------|
| id                    | INTEGER PK | ID único de la actividad (Strava)           |
| name                  | TEXT       | Nombre de la actividad                      |
| start_date_local      | TEXT       | Fecha y hora local de inicio                |
| distance              | REAL       | Distancia en metros                         |
| moving_time           | INTEGER    | Tiempo en movimiento (segundos)             |
| elapsed_time          | INTEGER    | Tiempo total (segundos)                     |
| average_speed         | REAL       | Velocidad media (m/s)                       |
| average_heartrate     | REAL       | FC media (si disponible)                    |
| total_elevation_gain  | REAL       | Desnivel positivo acumulado (metros)        |
| type                  | TEXT       | Tipo de actividad (`Run`, etc.)             |
| sport_type            | TEXT       | Subtipo específico (`TrailRun`, etc.)       |

---

### Tabla `splits`

Contiene los parciales por kilómetro (splits) asociados a cada actividad.

| Columna              | Tipo     | Descripción                                 |
|----------------------|----------|---------------------------------------------|
| activity_id          | INTEGER  | ID de la actividad (relación con `activities`) |
| split                | INTEGER  | Número de parcial (1, 2, 3...)              |
| distance             | REAL     | Distancia del split en metros               |
| elapsed_time         | INTEGER  | Tiempo del parcial (segundos)               |
| elevation_difference | REAL     | Diferencia de altitud                       |
| average_speed        | REAL     | Velocidad media del parcial (m/s)           |

---

### Cómo se crea

La función `init_db()` en `src/strava_client.py`:

- Crea la carpeta `data/` si no existe.
- Crea las tablas `activities` y `splits` si no existen.
- Inserta datos con `INSERT OR REPLACE` para evitar duplicados.
