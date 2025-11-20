-- Script SQL para agregar columna rollup_batch_id a la tabla readings_history
-- Ejecutar como usuario postgres con permisos de superusuario
--
-- Opción 1: Desde la línea de comandos
--   psql -U postgres -d sensor_system -f add_rollup_column.sql
--
-- Opción 2: Desde pgAdmin o cualquier cliente SQL
--   Copiar y pegar este script y ejecutarlo

-- Conectarse a la base de datos correcta
\c sensor_system

-- Verificar si la columna ya existe
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name='readings_history'
        AND column_name='rollup_batch_id'
    ) THEN
        -- Agregar columna
        ALTER TABLE readings_history
        ADD COLUMN rollup_batch_id VARCHAR(64);

        RAISE NOTICE 'Columna rollup_batch_id agregada exitosamente';
    ELSE
        RAISE NOTICE 'La columna rollup_batch_id ya existe';
    END IF;
END $$;

-- Crear índice para la columna
CREATE INDEX IF NOT EXISTS idx_readings_rollup_batch_id
ON readings_history(rollup_batch_id);

-- Dar permisos al usuario sensor_app
GRANT SELECT, INSERT, UPDATE ON readings_history TO sensor_app;

-- Verificar que la columna se agregó correctamente
SELECT
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_name = 'readings_history'
AND column_name = 'rollup_batch_id';

-- Mostrar información del índice
SELECT
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename = 'readings_history'
AND indexname = 'idx_readings_rollup_batch_id';

\echo ''
\echo '================================================'
\echo 'Columna rollup_batch_id agregada exitosamente'
\echo '================================================'
