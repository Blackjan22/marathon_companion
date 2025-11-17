# src/delete_activity.py
# como usar: python src/delete_activity.py 123456789
# Funciona con SQLite local o PostgreSQL (Supabase)

import sys
from utils.db_config import get_connection

def delete_activity_by_id(activity_id: int):
    conn = get_connection()
    cur = conn.cursor()

    # Eliminar splits primero (por FK)
    cur.execute("DELETE FROM splits WHERE activity_id = ?", (activity_id,))
    # Eliminar actividad principal
    cur.execute("DELETE FROM activities WHERE id = ?", (activity_id,))
    conn.commit()
    conn.close()

    print(f"✅ Actividad {activity_id} eliminada de la base de datos.")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("❌ Uso: python src/delete_activity.py <activity_id>")
        sys.exit(1)

    try:
        activity_id = int(sys.argv[1])
        delete_activity_by_id(activity_id)
    except ValueError:
        print("❌ El ID debe ser un número entero.")
        sys.exit(1)