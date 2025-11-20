"""
Script interactivo para agregar columna rollup_batch_id a la tabla readings_history
Solicita la contraseña de postgres al usuario
"""
import psycopg2
import sys
import getpass

def add_rollup_column_interactive():
    """Agregar columna rollup_batch_id a readings_history de forma interactiva"""

    print("=" * 60)
    print("AGREGAR COLUMNA rollup_batch_id A readings_history")
    print("=" * 60)
    print()

    # Solicitar información de conexión
    print("Por favor, proporciona la información de conexión a PostgreSQL:")
    print()

    host = input("Host [localhost]: ").strip() or "localhost"
    port = input("Puerto [5432]: ").strip() or "5432"
    database = input("Base de datos [sensor_system]: ").strip() or "sensor_system"
    user = input("Usuario [postgres]: ").strip() or "postgres"
    password = getpass.getpass("Contraseña: ")

    print()
    print("[+] Intentando conectar a PostgreSQL...")
    print(f"    Host: {host}")
    print(f"    Puerto: {port}")
    print(f"    Base de datos: {database}")
    print(f"    Usuario: {user}")
    print()

    try:
        # Conectar a PostgreSQL
        conn = psycopg2.connect(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password
        )

        print("[OK] Conectado exitosamente a PostgreSQL")
        print()

        cursor = conn.cursor()

        # Verificar si la columna ya existe
        print("[+] Verificando si la columna rollup_batch_id ya existe...")
        cursor.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name='readings_history'
            AND column_name='rollup_batch_id'
        """)

        if cursor.fetchone():
            print("[INFO] La columna rollup_batch_id ya existe en la tabla readings_history")
            print()

            # Mostrar información de la columna
            cursor.execute("""
                SELECT column_name, data_type, is_nullable, character_maximum_length
                FROM information_schema.columns
                WHERE table_name='readings_history'
                AND column_name='rollup_batch_id'
            """)

            result = cursor.fetchone()
            if result:
                print("[INFORMACION DE LA COLUMNA]")
                print(f"    Nombre: {result[0]}")
                print(f"    Tipo: {result[1]}({result[3]})")
                print(f"    Nullable: {result[2]}")

            cursor.close()
            conn.close()
            return True

        print("[INFO] La columna rollup_batch_id NO existe. Procediendo a crearla...")
        print()

        # Agregar la columna
        print("[+] Agregando columna rollup_batch_id...")
        cursor.execute("""
            ALTER TABLE readings_history
            ADD COLUMN rollup_batch_id VARCHAR(64);
        """)
        print("[OK] Columna agregada exitosamente")

        # Crear índice
        print("[+] Creando índice idx_readings_rollup_batch_id...")
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_readings_rollup_batch_id
            ON readings_history(rollup_batch_id);
        """)
        print("[OK] Índice creado exitosamente")

        # Dar permisos al usuario sensor_app
        print("[+] Otorgando permisos al usuario sensor_app...")
        try:
            cursor.execute("""
                GRANT SELECT, INSERT, UPDATE ON readings_history TO sensor_app;
            """)
            print("[OK] Permisos otorgados")
        except Exception as e:
            print(f"[WARN] No se pudieron otorgar permisos: {e}")

        # Commit de todos los cambios
        conn.commit()
        print()
        print("[+] Cambios confirmados (COMMIT)")

        # Verificar que todo se creó correctamente
        print()
        print("[+] Verificando creación...")
        cursor.execute("""
            SELECT column_name, data_type, is_nullable, character_maximum_length
            FROM information_schema.columns
            WHERE table_name='readings_history'
            AND column_name='rollup_batch_id'
        """)

        result = cursor.fetchone()
        if result:
            print()
            print("=" * 60)
            print("[VERIFICACION EXITOSA]")
            print("=" * 60)
            print(f"Columna: {result[0]}")
            print(f"Tipo: {result[1]}({result[3]})")
            print(f"Nullable: {result[2]}")
            print()

        # Verificar índice
        cursor.execute("""
            SELECT indexname, indexdef
            FROM pg_indexes
            WHERE tablename = 'readings_history'
            AND indexname = 'idx_readings_rollup_batch_id'
        """)

        index_result = cursor.fetchone()
        if index_result:
            print(f"Índice: {index_result[0]}")
            print(f"Definición: {index_result[1]}")
            print()

        print("=" * 60)
        print("[COMPLETADO]")
        print("La columna rollup_batch_id ha sido agregada exitosamente")
        print("Ahora puedes reiniciar el servidor para usar los rollups")
        print("=" * 60)

        cursor.close()
        conn.close()
        return True

    except psycopg2.OperationalError as e:
        print()
        print("[ERROR] No se pudo conectar a PostgreSQL")
        print(f"Detalle: {e}")
        print()
        print("Posibles soluciones:")
        print("1. Verifica que PostgreSQL esté corriendo")
        print("2. Verifica que la contraseña sea correcta")
        print("3. Verifica que el usuario tenga permisos")
        return False

    except psycopg2.Error as e:
        print()
        print("[ERROR] Error de PostgreSQL")
        print(f"Detalle: {e}")
        if conn:
            conn.rollback()
            conn.close()
        return False

    except Exception as e:
        print()
        print("[ERROR] Error inesperado")
        print(f"Detalle: {e}")
        if conn:
            conn.rollback()
            conn.close()
        return False

if __name__ == "__main__":
    print()
    success = add_rollup_column_interactive()
    print()
    sys.exit(0 if success else 1)
