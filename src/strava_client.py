from datetime import datetime
import os
import requests
import sqlite3
from dotenv import load_dotenv
from time import sleep

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
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS activities (
            id INTEGER PRIMARY KEY,
            name TEXT,
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

    conn.commit()
    conn.close()

def download_and_store_runs(db_path="data/strava_activities.db", max_pages=50):
    access_token = get_access_token()
    headers = {"Authorization": f"Bearer {access_token}"}

    init_db(db_path)
    conn = sqlite3.connect(db_path)
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

            # Insertar actividad
            cur.execute("""
                INSERT OR REPLACE INTO activities VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                detail["id"],
                detail["name"],
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

            # Insertar splits (si existen)
            for split in detail.get("splits_metric", []):
                cur.execute("""
                    INSERT INTO splits VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    detail["id"],
                    split["split"],
                    split["distance"],
                    split["elapsed_time"],
                    split.get("elevation_difference"),
                    split["average_speed"]
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
    conn = sqlite3.connect(db_path)
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

            cur.execute("""
                INSERT OR IGNORE INTO activities VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                detail["id"],
                detail["name"],
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

            for split in detail.get("splits_metric", []):
                cur.execute("""
                    INSERT INTO splits VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    detail["id"],
                    split["split"],
                    split["distance"],
                    split["elapsed_time"],
                    split.get("elevation_difference"),
                    split["average_speed"]
                ))

            total_new += 1
            sleep(0.2)

        page += 1

    conn.commit()
    conn.close()
    print(f"✅ Sincronización completa. Nuevas actividades insertadas: {total_new}")