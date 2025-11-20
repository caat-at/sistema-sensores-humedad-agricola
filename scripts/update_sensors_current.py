# -*- coding: utf-8 -*-
"""
Script para marcar todos los sensores como is_current=True
"""

import sys
from pathlib import Path

# Agregar el directorio raíz al path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

import psycopg2
from dotenv import load_dotenv
import os

# Cargar variables de entorno
load_dotenv()

def update_all_sensors():
    """Marca todos los sensores con is_current=True"""

    # Conectar a PostgreSQL como sensor_app
    conn = psycopg2.connect(
        host="localhost",
        database="sensor_system",
        user="sensor_app",
        password="change_this_password"
    )

    try:
        cursor = conn.cursor()

        # Actualizar todos los sensores para marcarlos como is_current=True
        print("[+] Actualizando sensores...")
        cursor.execute("""
            UPDATE sensors_history
            SET is_current = TRUE
            WHERE sensor_id IN ('SENSOR_001', 'SENSOR_002', 'SENSOR_003', 'SENSOR_004');
        """)

        conn.commit()

        # Verificar resultados
        cursor.execute("""
            SELECT sensor_id, is_current, status
            FROM sensors_history
            WHERE is_current = TRUE
            ORDER BY sensor_id;
        """)

        sensors = cursor.fetchall()
        print(f"\n[OK] Sensores actualizados: {len(sensors)}")
        for sensor_id, is_current, status in sensors:
            print(f"  - {sensor_id}: is_current={is_current}, status={status}")

        cursor.close()
        print("\n[OK] Actualización completada exitosamente")

    except Exception as e:
        print(f"[ERROR] Error actualizando sensores: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    update_all_sensors()
