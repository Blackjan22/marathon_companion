# 🏃 Running Analytics

Aplicación local para descargar, analizar y visualizar entrenamientos de running desde Strava.

---

## 📦 Estructura del proyecto

```
running_analytics/
├── data/                           # Base de datos SQLite
│   └── strava_activities.db
├── src/                            # Código fuente principal
│   ├── pages/                      # Páginas de Streamlit
│   │   ├── 1_Dashboard_General.py
│   │   └── 2_Histórico_Completo.py
│   ├── utils/                      # Utilidades
│   │   ├── data_processing.py
│   │   └── formatting.py
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
- Tres tablas: `activities`, `splits` y `laps`, relacionadas por `activity_id`.

### ✅ Dashboard interactivo con Streamlit
- **Dashboard General**: Métricas clave, gráficos de progreso y recomendaciones de entrenamiento.
- **Histórico Completo**: Tabla detallada con filtros, análisis de actividades individuales y visualización de laps.
- Botón de sincronización integrado para actualizar actividades desde Strava.

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

### 4. Configurar credenciales de Strava
Crea un archivo `.env` en la raíz del proyecto con tus credenciales:
```
STRAVA_CLIENT_ID=tu_client_id
STRAVA_CLIENT_SECRET=tu_client_secret
STRAVA_REFRESH_TOKEN=tu_refresh_token
```

### 5. Ejecutar la aplicación
```bash
python src/run_app.py
```

La aplicación se abrirá automáticamente en tu navegador en `http://localhost:8501`.  

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

---

## 🔧 Scripts disponibles

- **`python src/run_app.py`**: Lanza la aplicación Streamlit
- **`python src/sync_strava.py`**: Sincroniza actividades desde Strava (script CLI)
- **`python src/delete_activity.py`**: Elimina una actividad de la base de datos
