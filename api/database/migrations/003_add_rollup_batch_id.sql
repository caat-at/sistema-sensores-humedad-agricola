-- Migración 003: Agregar soporte para rollups diarios con merkle hash
-- Permite agrupar 24 lecturas en un único hash y reducir costos de blockchain en 96%

BEGIN;

-- Agregar columna rollup_batch_id a readings_history
ALTER TABLE readings_history
ADD COLUMN IF NOT EXISTS rollup_batch_id VARCHAR(64);

-- Crear índice para búsquedas por rollup
CREATE INDEX IF NOT EXISTS idx_rollup_batch_id
ON readings_history(rollup_batch_id);

-- Crear índice compuesto para consultas de rollup por sensor y fecha
CREATE INDEX IF NOT EXISTS idx_sensor_rollup
ON readings_history(sensor_id, rollup_batch_id, timestamp);

-- Comentarios
COMMENT ON COLUMN readings_history.rollup_batch_id IS 'Merkle root hash del rollup diario que incluye esta lectura';

COMMIT;

-- Verificar migración
SELECT
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns
WHERE table_name = 'readings_history'
  AND column_name = 'rollup_batch_id';
