# utils/db_config.py
"""
Capa de abstracción para base de datos.
Soporta SQLite (desarrollo local) y PostgreSQL (producción en Streamlit Cloud).
"""

import os
import sqlite3
from typing import Any, Optional

# Intentar importar psycopg2 (solo necesario en producción)
try:
    import psycopg2
    import psycopg2.extras
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False


def get_database_url() -> Optional[str]:
    """
    Obtiene la URL de la base de datos desde variables de entorno o secrets de Streamlit.

    Returns:
        URL de la base de datos o None si no está configurada (usa SQLite por defecto)
    """
    # Intentar obtener desde variable de entorno
    db_url = os.getenv("DATABASE_URL")

    if db_url:
        print(f"[DB_CONFIG] Using DATABASE_URL from environment")
        return db_url

    # Intentar obtener desde Streamlit secrets
    try:
        import streamlit as st
        if hasattr(st, 'secrets'):
            print(f"[DB_CONFIG] Streamlit secrets available: {list(st.secrets.keys())}")
            if 'database' in st.secrets:
                url = st.secrets['database']['url']
                print(f"[DB_CONFIG] Using database URL from Streamlit secrets (length: {len(url)})")
                return url
            else:
                print("[DB_CONFIG] 'database' key not found in Streamlit secrets")
        else:
            print("[DB_CONFIG] Streamlit secrets not available")
    except Exception as e:
        print(f"[DB_CONFIG] Error reading Streamlit secrets: {e}")

    print("[DB_CONFIG] No database URL found, will use SQLite")
    return None


def is_postgres() -> bool:
    """
    Determina si estamos usando PostgreSQL o SQLite.

    Returns:
        True si estamos usando PostgreSQL, False si SQLite
    """
    return get_database_url() is not None and POSTGRES_AVAILABLE


class CursorWrapper:
    """
    Wrapper para cursor que convierte placeholders ? a %s automáticamente en PostgreSQL.
    """
    def __init__(self, cursor, is_postgres: bool):
        self.cursor = cursor
        self.is_postgres = is_postgres

    def execute(self, query: str, params=None):
        """Ejecuta query adaptando placeholders si es necesario."""
        if self.is_postgres and '?' in query:
            # Convertir ? a %s para PostgreSQL
            query = query.replace('?', '%s')

        if params:
            return self.cursor.execute(query, params)
        return self.cursor.execute(query)

    def executemany(self, query: str, params_list):
        """Ejecuta query múltiples veces adaptando placeholders."""
        if self.is_postgres and '?' in query:
            query = query.replace('?', '%s')
        return self.cursor.executemany(query, params_list)

    def fetchone(self):
        return self.cursor.fetchone()

    def fetchall(self):
        return self.cursor.fetchall()

    def fetchmany(self, size=None):
        if size:
            return self.cursor.fetchmany(size)
        return self.cursor.fetchmany()

    @property
    def lastrowid(self):
        return self.cursor.lastrowid

    @property
    def rowcount(self):
        return self.cursor.rowcount

    @property
    def description(self):
        """Expone description del cursor para pandas.read_sql_query()"""
        return self.cursor.description

    @property
    def arraysize(self):
        """Expone arraysize del cursor"""
        return self.cursor.arraysize

    @arraysize.setter
    def arraysize(self, value):
        self.cursor.arraysize = value

    def close(self):
        return self.cursor.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class ConnectionWrapper:
    """
    Wrapper para conexión que devuelve CursorWrapper en lugar de cursor normal.
    """
    def __init__(self, connection, is_postgres: bool):
        self.connection = connection
        self.is_postgres = is_postgres

    def cursor(self):
        """Devuelve un cursor wrapeado que adapta placeholders."""
        return CursorWrapper(self.connection.cursor(), self.is_postgres)

    def commit(self):
        return self.connection.commit()

    def rollback(self):
        return self.connection.rollback()

    def close(self):
        return self.connection.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


def get_connection():
    """
    Crea y devuelve una conexión a la base de datos apropiada.

    - Si DATABASE_URL está configurada → PostgreSQL (Supabase)
    - Si no → SQLite local (desarrollo)

    Returns:
        ConnectionWrapper que adapta placeholders automáticamente
    """
    db_url = get_database_url()

    if db_url and POSTGRES_AVAILABLE:
        # Producción: PostgreSQL (Supabase)
        conn = psycopg2.connect(db_url)
        return ConnectionWrapper(conn, is_postgres=True)
    else:
        # Desarrollo: SQLite local
        db_path = 'data/strava_activities.db'
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        conn = sqlite3.connect(db_path)
        return ConnectionWrapper(conn, is_postgres=False)


def adapt_query(query: str) -> str:
    """
    Adapta una query SQL para que funcione en PostgreSQL o SQLite.

    - SQLite usa ? como placeholder
    - PostgreSQL usa %s como placeholder

    Args:
        query: Query SQL con placeholders de SQLite (?)

    Returns:
        Query adaptada según la BD activa
    """
    if is_postgres():
        # Convertir ? a %s para PostgreSQL
        return query.replace('?', '%s')
    return query


def execute_query(query: str, params: tuple = None, fetch: str = None) -> Any:
    """
    Ejecuta una query de forma agnóstica a la BD.

    Args:
        query: Query SQL (con placeholders ?)
        params: Parámetros de la query
        fetch: 'one', 'all', 'many' o None (para INSERT/UPDATE)

    Returns:
        Resultado de la query según el tipo de fetch
    """
    conn = get_connection()
    cur = conn.cursor()

    adapted_query = adapt_query(query)

    if params:
        cur.execute(adapted_query, params)
    else:
        cur.execute(adapted_query)

    result = None
    if fetch == 'one':
        result = cur.fetchone()
    elif fetch == 'all':
        result = cur.fetchall()
    elif fetch == 'many':
        result = cur.fetchmany()

    if query.strip().upper().startswith(('INSERT', 'UPDATE', 'DELETE', 'CREATE')):
        conn.commit()

    conn.close()
    return result


def get_placeholder() -> str:
    """
    Retorna el placeholder apropiado según la BD.

    Returns:
        '?' para SQLite, '%s' para PostgreSQL
    """
    return '%s' if is_postgres() else '?'


def get_db_type() -> str:
    """
    Retorna el tipo de base de datos activa.

    Returns:
        'postgresql' o 'sqlite'
    """
    return 'postgresql' if is_postgres() else 'sqlite'


# Información de debugging
if __name__ == "__main__":
    print(f"Tipo de BD: {get_db_type()}")
    print(f"¿PostgreSQL?: {is_postgres()}")
    print(f"Placeholder: {get_placeholder()}")
    print(f"psycopg2 disponible: {POSTGRES_AVAILABLE}")

    db_url = get_database_url()
    if db_url:
        # Ocultar password en logs
        safe_url = db_url.split('@')[1] if '@' in db_url else db_url
        print(f"DATABASE_URL configurada: ...@{safe_url}")
    else:
        print("DATABASE_URL no configurada → usando SQLite local")
