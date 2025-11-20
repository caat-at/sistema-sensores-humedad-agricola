"""
Script para agregar columna rollup_batch_id a la tabla readings_history
Debe ejecutarse con permisos de administrador de PostgreSQL
"""
import psycopg2
import sys

def add_rollup_column():
    """Agregar columna rollup_batch_id a readings_history"""

    # Intentar diferentes configuraciones de conexión
    connection_configs = [
        {
            'host': 'localhost',
            'port': 5432,
            'database': 'sensor_system',
            'user': 'sensor_app',
            'password': 'change_this_password'
        },
        {
            'host': 'localhost',
            'port': 5432,
            'database': 'sensor_system',
            'user': 'postgres',
            'password': 'admin'
        },
        {
            'host': 'localhost',
            'port': 5432,
            'database': 'sensor_system',
            'user': 'postgres',
            'password': 'postgres'
        },
    ]

    for config in connection_configs:
        try:
            print(f"\n[+] Intentando conectar a {config['database']} como {config['user']}...")
            conn = psycopg2.connect(**config)

            print("[OK] Conectado exitosamente")
            print(f"    Base de datos: {config['database']}")
            print(f"    Usuario: {config['user']}")

            cursor = conn.cursor()

            # Verificar si la columna ya existe
            cursor.execute("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name='readings_history'
                AND column_name='rollup_batch_id'
            """)

            if cursor.fetchone():
                print("[INFO] La columna rollup_batch_id ya existe")
                cursor.close()
                conn.close()
                return True

            # Agregar la columna
            print("[+] Agregando columna rollup_batch_id...")
            cursor.execute("""
                ALTER TABLE readings_history
                ADD COLUMN rollup_batch_id VARCHAR(64);
            """)

            # Crear índice
            print("[+] Creando índice para rollup_batch_id...")
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_readings_rollup_batch_id
                ON readings_history(rollup_batch_id);
            """)

            conn.commit()

            print("[OK] Columna rollup_batch_id agregada exitosamente")
            print("    Tipo: VARCHAR(64)")
            print("    Nullable: True")
            print("    Índice: idx_readings_rollup_batch_id")

            # Verificar
            cursor.execute("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name='readings_history'
                AND column_name='rollup_batch_id'
            """)

            result = cursor.fetchone()
            if result:
                print("\n[VERIFICACION]")
                print(f"    Columna: {result[0]}")
                print(f"    Tipo: {result[1]}")
                print(f"    Nullable: {result[2]}")

            cursor.close()
            conn.close()
            return True

        except psycopg2.OperationalError as e:
            print(f"[ERROR] No se pudo conectar: {e}")
            continue

        except psycopg2.Error as e:
            print(f"[ERROR] Error de PostgreSQL: {e}")
            if conn:
                conn.rollback()
                conn.close()
            continue

    print("\n[FAILED] No se pudo agregar la columna con ninguna configuración")
    print("\nPor favor, ejecuta manualmente:")
    print("  psql -U postgres -d sensor_system")
    print("  ALTER TABLE readings_history ADD COLUMN rollup_batch_id VARCHAR(64);")
    print("  CREATE INDEX idx_readings_rollup_batch_id ON readings_history(rollup_batch_id);")
    return False

if __name__ == "__main__":
    success = add_rollup_column()
    sys.exit(0 if success else 1)
