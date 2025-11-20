"""
Script para verificar que el rollup diario se ejecutó correctamente
Ejecutar después de las 00:05 AM para verificar el rollup del día anterior
"""
import psycopg2
import requests
from datetime import datetime, timedelta
import sys

def verify_rollup():
    print("=" * 60)
    print("VERIFICACION DE ROLLUP DIARIO")
    print("=" * 60)
    print()

    success = True

    # 1. Verificar scheduler está corriendo
    print("[1/4] Verificando scheduler...")
    try:
        response = requests.get("http://localhost:8000/api/health", timeout=5)
        health = response.json()

        if health.get("scheduler", {}).get("running"):
            print("    [OK] Scheduler esta corriendo")
            jobs = health["scheduler"].get("jobs", [])
            if jobs:
                next_run = jobs[0]["next_run"]
                print(f"    Proxima ejecucion: {next_run}")
        else:
            print("    [ERROR] Scheduler NO esta corriendo")
            success = False
    except Exception as e:
        print(f"    [ERROR] No se pudo verificar scheduler: {e}")
        success = False

    print()

    # 2. Verificar lecturas procesadas en PostgreSQL
    print("[2/4] Verificando lecturas procesadas en PostgreSQL...")
    try:
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            database="sensor_system",
            user="sensor_app",
            password="change_this_password"
        )

        cursor = conn.cursor()

        # Lecturas de ayer con rollup_batch_id
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

        cursor.execute("""
            SELECT
                sensor_id,
                COUNT(*) as total,
                rollup_batch_id
            FROM readings_history
            WHERE DATE(timestamp) = %s
            AND rollup_batch_id IS NOT NULL
            GROUP BY sensor_id, rollup_batch_id
        """, (yesterday,))

        results = cursor.fetchall()

        if results:
            print(f"    [OK] Encontrados {len(results)} rollups para {yesterday}")
            for sensor_id, total, batch_id in results:
                batch_short = batch_id[:16] if batch_id else "N/A"
                print(f"        - {sensor_id}: {total} lecturas (batch: {batch_short}...)")
        else:
            print(f"    [WARN] No se encontraron rollups para {yesterday}")
            print(f"           Esto es normal si no hubo lecturas ese dia")

        # Total de lecturas con rollup
        cursor.execute("""
            SELECT COUNT(*) FROM readings_history
            WHERE rollup_batch_id IS NOT NULL
        """)
        total_with_rollup = cursor.fetchone()[0]
        print(f"    [INFO] Total de lecturas con rollup: {total_with_rollup}")

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"    [ERROR] Error consultando PostgreSQL: {e}")
        success = False

    print()

    # 3. Verificar estadísticas de rollups (si el endpoint existe)
    print("[3/4] Consultando estadisticas de rollups...")
    try:
        response = requests.get("http://localhost:8000/api/rollup/stats", timeout=5)

        if response.status_code == 200:
            stats = response.json()
            print(f"    Total rollups: {stats.get('total_rollups', 0)}")
            print(f"    Total lecturas procesadas: {stats.get('total_readings_in_rollups', 0)}")
            print(f"    Lecturas pendientes: {stats.get('pending_readings', 0)}")
            print(f"    Ultimo rollup: {stats.get('last_rollup_date', 'N/A')}")
            print(f"    Ahorro estimado: {stats.get('estimated_savings_ada', 0):.2f} ADA")
        else:
            print(f"    [WARN] Endpoint de estadisticas no disponible (status: {response.status_code})")

    except Exception as e:
        print(f"    [WARN] No se pudieron obtener estadisticas: {e}")

    print()

    # 4. Información para verificación manual
    print("[4/4] Verificar en Cardano Explorer:")
    print("    URL: https://preview.cardanoscan.io/address/addr_test1wz873sjp5wenffd4x8jusc94kek42w4mwpuevnagkzkwsqg0j0aty")
    print("    Busca transacciones alrededor de las 00:05 AM")
    print()

    print("=" * 60)
    if success:
        print("[COMPLETADO] Verificacion finalizada exitosamente")
    else:
        print("[ATENCION] Verificacion finalizada con advertencias")
    print("=" * 60)

    return success

if __name__ == "__main__":
    try:
        success = verify_rollup()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n[INFO] Verificacion cancelada por el usuario")
        sys.exit(0)
    except Exception as e:
        print(f"\n[ERROR] Error inesperado: {e}")
        sys.exit(1)
