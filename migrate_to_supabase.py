#!/usr/bin/env python
"""
Script de migración de SQLite local a PostgreSQL (Supabase)
Migra todas las actividades excepto las últimas N (para probar sincronización)
"""

import sqlite3
import sys
import os
from dotenv import load_dotenv

# Añadir src al path
sys.path.insert(0, 'src')
from utils.db_config import get_connection, is_postgres

load_dotenv()

# IDs a excluir (últimas 2 actividades)
EXCLUDE_IDS = [16473993143, 16435421117]

def migrate_data():
    """Migra datos de SQLite a PostgreSQL"""

    if not is_postgres():
        print("❌ Error: DATABASE_URL no está configurada o psycopg2 no disponible")
        print("   Asegúrate de estar conectado a una red que permita acceso a Supabase")
        return False

    print("=" * 70)
    print("MIGRACIÓN SQLite → PostgreSQL (Supabase)")
    print("=" * 70)

    # Conectar a SQLite (origen)
    print("\n📂 Conectando a SQLite local...")
    conn_sqlite = sqlite3.connect('data/strava_activities.db')
    cur_sqlite = conn_sqlite.cursor()

    # Conectar a PostgreSQL (destino)
    print("🔌 Conectando a Supabase PostgreSQL...")
    conn_pg = get_connection()
    cur_pg = conn_pg.cursor()

    # Verificar datos en SQLite
    cur_sqlite.execute("SELECT COUNT(*) FROM activities WHERE id NOT IN ({})".format(
        ','.join(map(str, EXCLUDE_IDS))
    ))
    total_activities = cur_sqlite.fetchone()[0]

    print(f"\n📊 Datos a migrar:")
    print(f"   - Actividades: {total_activities}")
    print(f"   - Excluidas (últimas 2): {EXCLUDE_IDS}")

    # 1. MIGRAR ACTIVIDADES
    print(f"\n🏃 Migrando {total_activities} actividades...")
    cur_sqlite.execute("""
        SELECT id, name, description, private_note, start_date_local,
               distance, moving_time, elapsed_time, average_speed,
               average_heartrate, total_elevation_gain, type, sport_type
        FROM activities
        WHERE id NOT IN ({})
        ORDER BY start_date_local ASC
    """.format(','.join(map(str, EXCLUDE_IDS))))

    activities = cur_sqlite.fetchall()
    count = 0
    for act in activities:
        # Borrar si existe (por si acaso)
        cur_pg.execute("DELETE FROM activities WHERE id = %s", (act[0],))

        # Insertar
        cur_pg.execute("""
            INSERT INTO activities (
                id, name, description, private_note, start_date_local,
                distance, moving_time, elapsed_time, average_speed,
                average_heartrate, total_elevation_gain, type, sport_type
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, act)

        count += 1
        if count % 10 == 0:
            conn_pg.commit()
            print(f"   ✓ {count}/{total_activities} actividades...")

    conn_pg.commit()
    print(f"   ✅ {count} actividades migradas")

    # 2. MIGRAR SPLITS
    print(f"\n📏 Migrando splits...")
    cur_sqlite.execute("""
        SELECT activity_id, split, distance, elapsed_time,
               elevation_difference, average_speed
        FROM splits
        WHERE activity_id NOT IN ({})
    """.format(','.join(map(str, EXCLUDE_IDS))))

    splits = cur_sqlite.fetchall()
    if splits:
        # Limpiar splits de actividades migradas
        cur_pg.execute("""
            DELETE FROM splits
            WHERE activity_id NOT IN (%s, %s)
        """, EXCLUDE_IDS)

        count = 0
        for split in splits:
            cur_pg.execute("""
                INSERT INTO splits (
                    activity_id, split, distance, elapsed_time,
                    elevation_difference, average_speed
                ) VALUES (%s, %s, %s, %s, %s, %s)
            """, split)
            count += 1

            if count % 100 == 0:
                conn_pg.commit()
                print(f"   ✓ {count}/{len(splits)} splits...")

        conn_pg.commit()
        print(f"   ✅ {count} splits migrados")
    else:
        print(f"   ⚠️  No hay splits para migrar")

    # 3. MIGRAR LAPS
    print(f"\n⏱️  Migrando laps...")
    cur_sqlite.execute("""
        SELECT activity_id, lap_id, lap_index, name, split, start_date_local,
               elapsed_time, moving_time, distance, average_speed, max_speed,
               start_index, end_index, total_elevation_gain, pace_zone
        FROM laps
        WHERE activity_id NOT IN ({})
    """.format(','.join(map(str, EXCLUDE_IDS))))

    laps = cur_sqlite.fetchall()
    if laps:
        # Limpiar laps de actividades migradas
        cur_pg.execute("""
            DELETE FROM laps
            WHERE activity_id NOT IN (%s, %s)
        """, EXCLUDE_IDS)

        count = 0
        for lap in laps:
            cur_pg.execute("""
                INSERT INTO laps (
                    activity_id, lap_id, lap_index, name, split, start_date_local,
                    elapsed_time, moving_time, distance, average_speed, max_speed,
                    start_index, end_index, total_elevation_gain, pace_zone
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (activity_id, lap_index) DO UPDATE SET
                    lap_id = EXCLUDED.lap_id,
                    name = EXCLUDED.name,
                    split = EXCLUDED.split,
                    start_date_local = EXCLUDED.start_date_local,
                    elapsed_time = EXCLUDED.elapsed_time,
                    moving_time = EXCLUDED.moving_time,
                    distance = EXCLUDED.distance,
                    average_speed = EXCLUDED.average_speed,
                    max_speed = EXCLUDED.max_speed,
                    start_index = EXCLUDED.start_index,
                    end_index = EXCLUDED.end_index,
                    total_elevation_gain = EXCLUDED.total_elevation_gain,
                    pace_zone = EXCLUDED.pace_zone
            """, lap)
            count += 1

            if count % 100 == 0:
                conn_pg.commit()
                print(f"   ✓ {count}/{len(laps)} laps...")

        conn_pg.commit()
        print(f"   ✅ {count} laps migrados")
    else:
        print(f"   ⚠️  No hay laps para migrar")

    # 4. MIGRAR TRAINING PLANS
    print(f"\n📅 Migrando planes de entrenamiento...")
    cur_sqlite.execute("SELECT * FROM training_plans")
    plans = cur_sqlite.fetchall()

    if plans:
        for plan in plans:
            plan_id = plan[0]
            # Comprobar si existe
            cur_pg.execute("SELECT id FROM training_plans WHERE id = %s", (plan_id,))
            exists = cur_pg.fetchone()

            if not exists:
                cur_pg.execute("""
                    INSERT INTO training_plans (
                        id, week_start_date, week_number, goal, notes, created_at, status
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, plan)

        conn_pg.commit()
        print(f"   ✅ {len(plans)} planes migrados")
    else:
        print(f"   ⚠️  No hay planes de entrenamiento para migrar")

    # 5. MIGRAR PLANNED WORKOUTS
    print(f"\n💪 Migrando entrenamientos planificados...")
    cur_sqlite.execute("SELECT * FROM planned_workouts")
    workouts = cur_sqlite.fetchall()

    if workouts:
        for workout in workouts:
            workout_id = workout[0]
            cur_pg.execute("SELECT id FROM planned_workouts WHERE id = %s", (workout_id,))
            exists = cur_pg.fetchone()

            if not exists:
                cur_pg.execute("""
                    INSERT INTO planned_workouts (
                        id, plan_id, date, workout_type, distance_km, description,
                        pace_objective, notes, status, linked_activity_id, created_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, workout)

        conn_pg.commit()
        print(f"   ✅ {len(workouts)} entrenamientos planificados migrados")
    else:
        print(f"   ⚠️  No hay entrenamientos planificados para migrar")

    # 6. MIGRAR RUNNER PROFILE
    print(f"\n👤 Migrando perfil del corredor...")
    cur_sqlite.execute("SELECT * FROM runner_profile")
    profile = cur_sqlite.fetchone()

    if profile:
        cur_pg.execute("DELETE FROM runner_profile")
        cur_pg.execute("""
            INSERT INTO runner_profile (
                id, name, height_cm, weight_kg, age, vo2max_estimate,
                threshold_pace, easy_pace_min, easy_pace_max, training_philosophy,
                current_goal, goal_race_date, goal_race_distance,
                pr_5k, pr_10k, pr_half, pr_marathon, created_at, updated_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, profile)

        conn_pg.commit()
        print(f"   ✅ Perfil migrado")
    else:
        print(f"   ⚠️  No hay perfil para migrar")

    # 7. MIGRAR CHAT HISTORY
    print(f"\n💬 Migrando historial del Coach IA...")
    cur_sqlite.execute("SELECT * FROM chat_history")
    chats = cur_sqlite.fetchall()

    if chats:
        for chat in chats:
            chat_id = chat[0]
            cur_pg.execute("SELECT id FROM chat_history WHERE id = %s", (chat_id,))
            exists = cur_pg.fetchone()

            if not exists:
                cur_pg.execute("""
                    INSERT INTO chat_history (
                        id, role, content, timestamp, context_summary
                    ) VALUES (%s, %s, %s, %s, %s)
                """, chat)

        conn_pg.commit()
        print(f"   ✅ {len(chats)} mensajes del chat migrados")
    else:
        print(f"   ⚠️  No hay historial de chat para migrar")

    # Cerrar conexiones
    conn_sqlite.close()
    conn_pg.close()

    print("\n" + "=" * 70)
    print("✅ MIGRACIÓN COMPLETADA")
    print("=" * 70)
    print(f"\n📊 Resumen:")
    print(f"   - {total_activities} actividades migradas")
    print(f"   - Splits y laps incluidos")
    print(f"   - Planes, perfil y chat incluidos")
    print(f"\n⚠️  Actividades NO migradas (para probar sincronización):")
    print(f"   - {EXCLUDE_IDS[0]}")
    print(f"   - {EXCLUDE_IDS[1]}")
    print(f"\n🎯 Próximo paso: Sincroniza estas 2 actividades desde Streamlit")

    return True

if __name__ == "__main__":
    try:
        success = migrate_data()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Error durante la migración: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
