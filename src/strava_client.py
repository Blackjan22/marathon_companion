from datetime import datetime
import os
import requests
from dotenv import load_dotenv
from time import sleep
import sys

# Añadir directorio actual al path para imports
sys.path.insert(0, os.path.dirname(__file__))
from utils.db_config import get_connection

load_dotenv(override=True)

CLIENT_ID = os.getenv("STRAVA_CLIENT_ID")
CLIENT_SECRET = os.getenv("STRAVA_CLIENT_SECRET")
REFRESH_TOKEN = os.getenv("STRAVA_REFRESH_TOKEN")
PROXY_CERT = os.path.expanduser("~/Credentials/rootcaCert.pem")


def get_access_token():
    url = "https://www.strava.com/api/v3/oauth/token"
    payload = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "refresh_token": REFRESH_TOKEN,
        "grant_type": "refresh_token",
    }
    response = requests.post(url, data=payload, verify=PROXY_CERT)
    response.raise_for_status()
    return response.json()["access_token"]


def init_db(db_path: str):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS activities (
            id INTEGER PRIMARY KEY,
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
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS splits (
            activity_id INTEGER,
            split INTEGER,
            distance REAL,
            elapsed_time INTEGER,
            elevation_difference REAL,
            average_speed REAL,
            FOREIGN KEY (activity_id) REFERENCES activities(id)
        )
    """)
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS laps (
            activity_id INTEGER NOT NULL,
            lap_id INTEGER,               -- id único del lap en Strava (siempre que exista)
            lap_index INTEGER,            -- índice del lap dentro de la actividad
            name TEXT,                    -- p.ej. "Interval 3", "Recovery", "Warm up"
            split INTEGER,                -- a veces Strava rellena este entero
            start_date_local TEXT,
            elapsed_time INTEGER,
            moving_time INTEGER,
            distance REAL,
            average_speed REAL,
            max_speed REAL,
            start_index INTEGER,          -- índice sobre streams
            end_index INTEGER,            -- índice sobre streams
            total_elevation_gain REAL,
            pace_zone INTEGER,
            PRIMARY KEY (activity_id, lap_index),
            FOREIGN KEY (activity_id) REFERENCES activities(id)
        )
    """)

    # Tablas para planificación de entrenamientos
    cur.execute("""
        CREATE TABLE IF NOT EXISTS training_plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            week_start_date TEXT NOT NULL,
            week_number INTEGER,
            goal TEXT,
            notes TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'active'
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS planned_workouts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plan_id INTEGER,
            date TEXT NOT NULL,
            workout_type TEXT,
            distance_km REAL,
            description TEXT,
            pace_objective TEXT,
            notes TEXT,
            status TEXT DEFAULT 'pending',
            linked_activity_id INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (plan_id) REFERENCES training_plans(id),
            FOREIGN KEY (linked_activity_id) REFERENCES activities(id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS workout_feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            planned_workout_id INTEGER,
            activity_id INTEGER,
            sensations TEXT,
            completed_as_planned INTEGER DEFAULT 1,
            notes TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (planned_workout_id) REFERENCES planned_workouts(id),
            FOREIGN KEY (activity_id) REFERENCES activities(id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role TEXT NOT NULL,
            content TEXT,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
            context_summary TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS runner_profile (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
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
        )
    """)

    # Migración "suave": añade columnas si la tabla ya existía
    cur.execute("PRAGMA table_info(activities)")
    cols = [row[1] for row in cur.fetchall()]
    if "description" not in cols:
        cur.execute("ALTER TABLE activities ADD COLUMN description TEXT")
    if "private_note" not in cols:
        cur.execute("ALTER TABLE activities ADD COLUMN private_note TEXT")

    conn.commit()
    conn.close()

def fetch_laps(headers, activity_id: int):
    url = f"https://www.strava.com/api/v3/activities/{activity_id}/laps"
    resp = requests.get(url, headers=headers, verify=PROXY_CERT)
    resp.raise_for_status()
    return resp.json()  # lista de Laps

def download_and_store_runs(db_path="data/strava_activities.db", max_pages=50):
    access_token = get_access_token()
    headers = {"Authorization": f"Bearer {access_token}"}

    init_db(db_path)
    conn = get_connection()
    cur = conn.cursor()

    page = 1
    total_inserted = 0

    while page <= max_pages:
        print(f"🔄 Descargando página {page}...")
        url = "https://www.strava.com/api/v3/athlete/activities"
        params = {"per_page": 100, "page": page}
        response = requests.get(url, headers=headers, params=params, verify=PROXY_CERT)
        response.raise_for_status()
        activities = response.json()

        if not activities:
            break

        for activity in activities:
            if activity["type"] != "Run":
                continue

            act_id = activity["id"]
            print(f"➡️  Actividad {act_id} - {activity['name']}")

            # Detalle de la actividad
            detail_url = f"https://www.strava.com/api/v3/activities/{act_id}"
            detail_resp = requests.get(detail_url, headers=headers, verify=PROXY_CERT)
            detail_resp.raise_for_status()
            detail = detail_resp.json()

            # Insertar actividad (incluye description y private_note)
            cur.execute("""
                INSERT OR REPLACE INTO activities (
                    id, name, description, private_note, start_date_local, distance, moving_time, elapsed_time, average_speed, average_heartrate, total_elevation_gain, type, sport_type
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                detail["id"],
                detail["name"],
                detail.get("description"),
                detail.get("private_note"),
                detail["start_date_local"],
                detail["distance"],
                detail["moving_time"],
                detail["elapsed_time"],
                detail.get("average_speed"),
                detail.get("average_heartrate"),
                detail.get("total_elevation_gain"),
                detail["type"],
                detail["sport_type"]
            ))

            # --- SPLITS (kilómetro automático) ---
            cur.execute("DELETE FROM splits WHERE activity_id = ?", (detail["id"],))
            for split in detail.get("splits_metric", []):
                cur.execute("""
                    INSERT INTO splits (activity_id, split, distance, elapsed_time, elevation_difference, average_speed)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    detail["id"],
                    split["split"],
                    split["distance"],
                    split["elapsed_time"],
                    split.get("elevation_difference"),
                    split["average_speed"]
                ))

            # --- LAPS (parciales/intervalos) ---
            laps = fetch_laps(headers, detail["id"])
            cur.execute("DELETE FROM laps WHERE activity_id = ?", (detail["id"],))
            for lap in laps:
                cur.execute("""
                    INSERT INTO laps (
                        activity_id, lap_id, lap_index, name, split, start_date_local, elapsed_time, moving_time,
                        distance, average_speed, max_speed, start_index, end_index, total_elevation_gain, pace_zone
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    detail["id"],
                    lap.get("id"),
                    lap.get("lap_index"),
                    lap.get("name"),
                    lap.get("split"),
                    lap.get("start_date_local"),
                    lap.get("elapsed_time"),
                    lap.get("moving_time"),
                    lap.get("distance"),
                    lap.get("average_speed"),
                    lap.get("max_speed"),
                    lap.get("start_index"),
                    lap.get("end_index"),
                    lap.get("total_elevation_gain"),
                    lap.get("pace_zone"),
                ))

            total_inserted += 1
            sleep(0.2)  # evitar rate limit

        page += 1

    conn.commit()
    conn.close()
    print(f"✅ Proceso completo. Actividades almacenadas: {total_inserted}")
    

def sync_new_activities(db_path="data/strava_activities.db"):
    access_token = get_access_token()
    headers = {"Authorization": f"Bearer {access_token}"}
    init_db(db_path)
    conn = get_connection()
    cur = conn.cursor()
    # Obtener fecha de última actividad
    cur.execute("SELECT MAX(start_date_local) FROM activities")
    result = cur.fetchone()
    last_date = result[0] if result[0] else "1970-01-01T00:00:00Z"
    after_timestamp = int(datetime.fromisoformat(last_date.replace("Z", "+00:00")).timestamp())

    page = 1
    total_new = 0

    while True:
        url = "https://www.strava.com/api/v3/athlete/activities"
        params = {
            "per_page": 100,
            "page": page,
            "after": after_timestamp
        }
        response = requests.get(url, headers=headers, params=params, verify=PROXY_CERT)
        response.raise_for_status()
        activities = response.json()

        if not activities:
            break

        for activity in activities:
            if activity["type"] != "Run":
                continue

            act_id = activity["id"]
            print(f"➡️  Nueva actividad {act_id} - {activity['name']}")

            detail_url = f"https://www.strava.com/api/v3/activities/{act_id}"
            detail_resp = requests.get(detail_url, headers=headers, verify=PROXY_CERT)
            detail_resp.raise_for_status()
            detail = detail_resp.json()

            # Insertar/actualizar actividad (igual que ya tienes)
            cur.execute("""
                INSERT OR REPLACE INTO activities (
                    id, name, description, private_note, start_date_local, distance, moving_time, elapsed_time, average_speed,
                    average_heartrate, total_elevation_gain, type, sport_type
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                detail["id"],
                detail["name"],
                detail.get("description"),
                detail.get("private_note"),
                detail["start_date_local"],
                detail["distance"],
                detail["moving_time"],
                detail["elapsed_time"],
                detail.get("average_speed"),
                detail.get("average_heartrate"),
                detail.get("total_elevation_gain"),
                detail["type"],
                detail["sport_type"]
            ))

            # --- SPLITS (kilómetro automático) ---
            cur.execute("DELETE FROM splits WHERE activity_id = ?", (detail["id"],))
            for split in detail.get("splits_metric", []):
                cur.execute("""
                    INSERT INTO splits (activity_id, split, distance, elapsed_time, elevation_difference, average_speed)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    detail["id"],
                    split["split"],
                    split["distance"],
                    split["elapsed_time"],
                    split.get("elevation_difference"),
                    split["average_speed"]
                ))

            # --- LAPS (parciales/intervalos) ---
            laps = fetch_laps(headers, detail["id"])
            cur.execute("DELETE FROM laps WHERE activity_id = ?", (detail["id"],))
            for lap in laps:
                cur.execute("""
                    INSERT INTO laps (
                        activity_id, lap_id, lap_index, name, split, start_date_local, elapsed_time, moving_time,
                        distance, average_speed, max_speed, start_index, end_index, total_elevation_gain, pace_zone
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    detail["id"],
                    lap.get("id"),
                    lap.get("lap_index"),
                    lap.get("name"),
                    lap.get("split"),
                    lap.get("start_date_local"),
                    lap.get("elapsed_time"),
                    lap.get("moving_time"),
                    lap.get("distance"),
                    lap.get("average_speed"),
                    lap.get("max_speed"),
                    lap.get("start_index"),
                    lap.get("end_index"),
                    lap.get("total_elevation_gain"),
                    lap.get("pace_zone"),
                ))

            total_new += 1
            sleep(0.2)

        page += 1

    conn.commit()
    conn.close()
    print(f"✅ Sincronización completa. Nuevas actividades insertadas: {total_new}")
    
    
def backfill_missing_laps(db_path="data/strava_activities.db", limit=None):
    """
    Rellena la tabla 'laps' para actividades ya presentes en 'activities' que no tengan parciales insertados.
    Si 'limit' es un entero, procesa como máximo ese número de actividades (útil para pruebas).
    """
    access_token = get_access_token()
    headers = {"Authorization": f"Bearer {access_token}"}
    init_db(db_path)
    conn = get_connection()
    cur = conn.cursor()

    sql = """
        SELECT a.id
        FROM activities a
        LEFT JOIN laps l ON l.activity_id = a.id
        WHERE l.activity_id IS NULL
        ORDER BY a.start_date_local DESC
    """
    if limit is not None:
        cur.execute(sql + " LIMIT ?", (limit,))
    else:
        cur.execute(sql)

    rows = cur.fetchall()
    processed = 0

    for (act_id,) in rows:
        try:
            laps = fetch_laps(headers, act_id)
            cur.execute("DELETE FROM laps WHERE activity_id = ?", (act_id,))
            for lap in laps:
                cur.execute("""
                    INSERT INTO laps (
                        activity_id, lap_id, lap_index, name, split, start_date_local, elapsed_time, moving_time,
                        distance, average_speed, max_speed, start_index, end_index, total_elevation_gain, pace_zone
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    act_id,
                    lap.get("id"),
                    lap.get("lap_index"),
                    lap.get("name"),
                    lap.get("split"),
                    lap.get("start_date_local"),
                    lap.get("elapsed_time"),
                    lap.get("moving_time"),
                    lap.get("distance"),
                    lap.get("average_speed"),
                    lap.get("max_speed"),
                    lap.get("start_index"),
                    lap.get("end_index"),
                    lap.get("total_elevation_gain"),
                    lap.get("pace_zone"),
                ))
            processed += 1
            sleep(0.2)
        except Exception as e:
            print(f"Error al obtener laps de {act_id}: {e}")

    conn.commit()
    conn.close()
    print(f"Backfill de laps completado. Actividades procesadas: {processed}")