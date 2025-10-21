# -*- coding: utf-8 -*-
"""
Verificar conexión y estado de la base de datos PostgreSQL
"""

import sys
from pathlib import Path
from sqlalchemy import text

# Agregar api al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from api.database.connection import SessionLocal, engine

def verify_database():
    """
    Verificar conexión y tablas de la base de datos
    """
    print("\n=== VERIFICACIÓN DE BASE DE DATOS POSTGRESQL ===\n")

    try:
        # Probar conexión
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        print("[OK] Conexion a PostgreSQL exitosa")

        # Verificar tablas existentes
        result = db.execute(text("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """))

        tables = [row[0] for row in result]

        print(f"\n[OK] Base de datos: sensor_system")
        print(f"[OK] Tablas encontradas: {len(tables)}")
        for table in tables:
            print(f"   - {table}")

        # Verificar vistas
        result = db.execute(text("""
            SELECT table_name
            FROM information_schema.views
            WHERE table_schema = 'public'
            ORDER BY table_name
        """))

        views = [row[0] for row in result]

        if views:
            print(f"\n[OK] Vistas encontradas: {len(views)}")
            for view in views:
                print(f"   - {view}")

        # Verificar que las tablas principales existen
        expected_tables = ['sensors_history', 'readings_history', 'transactions_log', 'sensor_alerts']
        missing_tables = [t for t in expected_tables if t not in tables]

        if missing_tables:
            print(f"\n[WARN] Tablas faltantes: {missing_tables}")
            return False

        print("\n[OK] TODAS LAS TABLAS REQUERIDAS ESTAN PRESENTES")
        print("\n=== BASE DE DATOS LISTA PARA USAR ===\n")

        db.close()
        return True

    except Exception as e:
        print(f"\n[ERROR] Error: {e}")
        print("\nVerifica:")
        print("1. PostgreSQL esta instalado y corriendo")
        print("2. DATABASE_URL en .env es correcto")
        print("3. Usuario/password son correctos")
        return False

if __name__ == "__main__":
    success = verify_database()
    sys.exit(0 if success else 1)
