import subprocess
import sys
import os

def main():
    # Verificar que existe la base de datos
    if not os.path.exists('data/strava_activities.db'):
        print("⚠️  No se encontró la base de datos. Ejecuta primero el script de descarga de Strava.")
        return
    
    # Ejecutar Streamlit
    print("🚀 Iniciando Running Analytics...")
    subprocess.run([sys.executable, "-m", "streamlit", "run", "src/my_runs_analytics.py"])

if __name__ == "__main__":
    main()