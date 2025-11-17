# Troubleshooting - Marathon Companion

Guía de solución de problemas comunes.

---

## Error de conexión a Supabase (PostgreSQL)

### Síntoma
La aplicación no puede conectarse a la base de datos Supabase, mostrando errores como:
- `connection refused`
- `SSL connection error`
- `timeout`

### Causa
Supabase requiere conexiones SSL obligatorias para seguridad. Si la URL de conexión no especifica `sslmode=require`, psycopg2 intentará conectar sin SSL y fallará.

### Solución

#### Opción A - URL única con SSL (RECOMENDADA)

Añade `?sslmode=require` al final de la URL de conexión:

**En `.streamlit/secrets.toml` local:**
```toml
[database]
url = "postgresql://postgres.wwxrfxesismqcsrqfbnc:TU_PASSWORD@aws-1-eu-north-1.pooler.supabase.com:6543/postgres?sslmode=require"
```

**En Streamlit Cloud (Secrets):**
```toml
[database]
url = "postgresql://postgres.wwxrfxesismqcsrqfbnc:TU_PASSWORD@aws-1-eu-north-1.pooler.supabase.com:6543/postgres?sslmode=require"
```

#### Opción B - Separar componentes

Si prefieres separar los componentes de la conexión:

```toml
[database]
host = "aws-1-eu-north-1.pooler.supabase.com"
port = 6543
database = "postgres"
user = "postgres.wwxrfxesismqcsrqfbnc"
password = "TU_PASSWORD"
sslmode = "require"
```

Luego modifica `db_config.py` para construir la conexión con estos parámetros.

---

## Verificar conexión desde Python

Puedes probar la conexión directamente desde Python:

```python
import psycopg2

# URL con SSL
conn_str = "postgresql://postgres.wwxrfxesismqcsrqfbnc:TU_PASSWORD@aws-1-eu-north-1.pooler.supabase.com:6543/postgres?sslmode=require"

try:
    conn = psycopg2.connect(conn_str)
    cur = conn.cursor()
    cur.execute("SELECT NOW();")
    print("✅ Conexión exitosa:", cur.fetchone())
    cur.close()
    conn.close()
except Exception as e:
    print("❌ Error:", e)
```

---

## Problemas con SQLAlchemy

Si usas SQLAlchemy (para crear engines con `create_engine`), el formato de URL es ligeramente diferente:

```python
from sqlalchemy import create_engine, text

# Nota el driver específico: postgresql+psycopg2://
url = "postgresql+psycopg2://postgres.wwxrfxesismqcsrqfbnc:TU_PASSWORD@aws-1-eu-north-1.pooler.supabase.com:6543/postgres?sslmode=require"

engine = create_engine(url, pool_pre_ping=True)

with engine.connect() as conn:
    result = conn.execute(text("SELECT NOW()"))
    print("✅ Conexión exitosa:", result.fetchone())
```

**Diferencias clave:**
- `postgresql://` → para psycopg2 directo
- `postgresql+psycopg2://` → para SQLAlchemy con driver psycopg2

---

## Variables de entorno alternativas

Si prefieres usar variables de entorno en lugar de secrets.toml:

```bash
# .env
DATABASE_URL="postgresql://postgres.wwxrfxesismqcsrqfbnc:TU_PASSWORD@aws-1-eu-north-1.pooler.supabase.com:6543/postgres?sslmode=require"
```

El código en `db_config.py` ya está preparado para leer desde:
1. Variable de entorno `DATABASE_URL`
2. Streamlit secrets `st.secrets['database']['url']`

---

## Protección automática de SSL

El archivo `db_config.py:175-180` ahora incluye protección automática que añade `sslmode=require` si no está presente:

```python
if '?' not in db_url:
    db_url = f"{db_url}?sslmode=require"
elif 'sslmode' not in db_url:
    db_url = f"{db_url}&sslmode=require"
```

Esto significa que incluso si olvidas añadir `?sslmode=require` en la URL, la aplicación lo añadirá automáticamente.

---

## Verificar configuración actual

Ejecuta este script para diagnosticar tu configuración:

```bash
python -c "from src.utils.db_config import *; print(f'DB Type: {get_db_type()}'); print(f'PostgreSQL: {is_postgres()}'); print(f'psycopg2 available: {POSTGRES_AVAILABLE}')"
```

---

## Problemas de red corporativa / Firewall

### Síntoma
Desde Google Colab o conexiones externas funciona, pero desde tu red local (especialmente redes corporativas) da timeout al conectar al puerto 6543.

### Causa
Las redes corporativas suelen bloquear puertos no estándar como el 6543 (connection pooler de Supabase) por seguridad.

### Solución: Modo desarrollo dual (SQLite local + PostgreSQL en producción)

Tu aplicación ya está preparada para funcionar con ambas bases de datos automáticamente. Puedes desarrollar localmente con SQLite y desplegar con PostgreSQL sin cambios en el código.

**Para trabajar en local con SQLite:**

1. **Comenta temporalmente DATABASE_URL en .env:**
   ```bash
   # DATABASE_URL=postgresql://postgres.wwxrfxesismqcsrqfbnc:PASSWORD@aws-1-eu-north-1.pooler.supabase.com:6543/postgres?sslmode=require
   ```

2. **La app detectará automáticamente que no hay PostgreSQL y usará SQLite:**
   ```
   DB Type: sqlite
   Using PostgreSQL: False
   ```

3. **Trabaja normalmente con tu base de datos local** en `data/strava_activities.db`

**Para desplegar en Streamlit Cloud con PostgreSQL:**

1. **Configura los secrets en Streamlit Cloud** (Advanced Settings) con la DATABASE_URL sin comentar

2. **La app detectará automáticamente PostgreSQL en producción:**
   ```
   DB Type: postgresql
   Using PostgreSQL: True
   ```

3. **Sincroniza datos desde Strava** usando el botón "🔄 Refrescar actividades" la primera vez

**Soluciones alternativas si necesitas PostgreSQL en local:**

- **Usar hotspot móvil**: Conectarte desde tu teléfono móvil (4G/5G) que no tiene restricciones de firewall
- **Solicitar desbloqueo del puerto 6543** a tu departamento de IT
- **Probar con puerto 5432** (conexión directa en lugar de pooler):
  ```
  postgresql://...@aws-1-eu-north-1.pooler.supabase.com:5432/postgres?sslmode=require
  ```
- **Usar VPN personal** si tu empresa lo permite

**Verificar qué base de datos estás usando:**
```bash
python -c "from src.utils.db_config import *; print(f'DB Type: {get_db_type()}'); print(f'PostgreSQL: {is_postgres()}')"
```

---

## Errores comunes

### Error: `No module named 'psycopg2'`

**Solución:** Instala psycopg2-binary

```bash
pip install psycopg2-binary
```

Asegúrate de que esté en `requirements.txt`:
```
psycopg2-binary>=2.9.9
```

### Error: `password authentication failed`

**Causa:** Contraseña incorrecta en la URL

**Solución:**
1. Ve a Supabase → Settings → Database
2. Copia la contraseña que guardaste al crear el proyecto
3. Reemplaza `TU_PASSWORD` en la URL con la contraseña real

### Error: `could not connect to server`

**Causas posibles:**
1. URL incorrecta (verifica host, puerto, database)
2. Firewall bloqueando puerto 6543
3. Proyecto de Supabase pausado (plan gratuito)

**Solución:**
1. Verifica que el proyecto esté activo en Supabase
2. Copia la URL exacta desde Supabase → Settings → Database → Connection String
3. Usa el modo "Session" (puerto 6543), NO "Transaction" (puerto 6543)

---

## Deployment en Streamlit Cloud

### Checklist para deployment exitoso

- [ ] Base de datos PostgreSQL creada en Supabase
- [ ] Esquema de BD inicializado (ejecutar script SQL del README)
- [ ] URL de conexión incluye `?sslmode=require`
- [ ] Secrets configurados en Streamlit Cloud (Advanced Settings)
- [ ] `psycopg2-binary` incluido en `requirements.txt`
- [ ] Primera sincronización de datos realizada

### Formato correcto de secrets en Streamlit Cloud

```toml
[database]
url = "postgresql://postgres.xxxxx:PASSWORD@aws-0-eu-central-1.pooler.supabase.com:6543/postgres?sslmode=require"

STRAVA_CLIENT_ID = "12345"
STRAVA_CLIENT_SECRET = "abcdef123456"
STRAVA_REFRESH_TOKEN = "xyz789"
GEMINI_API_KEY = "AIza..."
```

**IMPORTANTE:**
- NO uses comillas simples dentro de valores TOML
- NO añadas espacios extra antes/después del `=`
- NO olvides reemplazar `PASSWORD` con tu contraseña real de Supabase

---

## Logs de debugging

Para ver logs detallados de la conexión, añade estas líneas temporalmente:

```python
# En db_config.py, después de import psycopg2
import logging
logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
```

Esto mostrará todas las queries SQL en tiempo real.

---

## Contacto y soporte

Si el problema persiste:
1. Verifica que la URL funcione desde Google Colab primero
2. Comprueba los logs de Streamlit Cloud
3. Revisa la sección de Issues en GitHub
