# -*- coding: utf-8 -*-
"""
Probar conexión a PostgreSQL
"""

import sys
from pathlib import Path

# Agregar api al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from api.database.connection import test_connection, init_db

if __name__ == "__main__":
    print("\n=== PRUEBA DE CONEXION A POSTGRESQL ===\n")

    if test_connection():
        print("\n[OK] Conexion exitosa!")
        print("\nInicializar tablas? (y/n): ", end="")
        resp = input().lower()

        if resp == 'y':
            init_db()
            print("\n[OK] Tablas inicializadas")
    else:
        print("\n[ERROR] Error de conexion")
        print("\nVerifica:")
        print("1. PostgreSQL esta instalado y corriendo")
        print("2. DATABASE_URL en .env es correcto")
        print("3. Usuario/password son correctos")
