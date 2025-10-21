-- Schema de Base de Datos para Sistema de Sensores Híbrido
-- Versión: 1.1 (Corregido para PostgreSQL)
-- Descripción: Almacena histórico off-chain de sensores y lecturas

-- ============================================================================
-- TABLA: sensors_history
-- Propósito: Histórico completo de todos los sensores y sus configuraciones
-- ============================================================================

CREATE TABLE IF NOT EXISTS sensors_history (
    id SERIAL PRIMARY KEY,
    sensor_id VARCHAR(50) NOT NULL,
    location_latitude DECIMAL(10, 6) NOT NULL,
    location_longitude DECIMAL(10, 6) NOT NULL,
    location_zone_name VARCHAR(200) NOT NULL,
    min_humidity_threshold INTEGER NOT NULL CHECK (min_humidity_threshold >= 0 AND min_humidity_threshold <= 100),
    max_humidity_threshold INTEGER NOT NULL CHECK (max_humidity_threshold >= 0 AND max_humidity_threshold <= 100),
    reading_interval_minutes INTEGER NOT NULL CHECK (reading_interval_minutes > 0),
    status VARCHAR(20) NOT NULL CHECK (status IN ('Active', 'Inactive', 'Maintenance', 'Error')),
    owner_pkh VARCHAR(56) NOT NULL,
    installed_date TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    tx_hash VARCHAR(64),
    is_current BOOLEAN DEFAULT TRUE,

    -- Constraints
    CONSTRAINT chk_humidity_range CHECK (min_humidity_threshold < max_humidity_threshold)
);

-- Índices para sensors_history
CREATE INDEX IF NOT EXISTS idx_sensors_sensor_id ON sensors_history(sensor_id);
CREATE INDEX IF NOT EXISTS idx_sensors_tx_hash ON sensors_history(tx_hash);
CREATE INDEX IF NOT EXISTS idx_sensors_is_current ON sensors_history(is_current);
CREATE INDEX IF NOT EXISTS idx_sensors_status ON sensors_history(status);
CREATE INDEX IF NOT EXISTS idx_sensors_updated_at ON sensors_history(updated_at DESC);

COMMENT ON TABLE sensors_history IS 'Histórico completo de configuraciones de sensores';
COMMENT ON COLUMN sensors_history.is_current IS 'TRUE solo para la versión actual del sensor';
COMMENT ON COLUMN sensors_history.tx_hash IS 'Hash de la transacción blockchain que creó/actualizó este registro';

-- ============================================================================
-- TABLA: readings_history
-- Propósito: Histórico completo de todas las lecturas de sensores
-- ============================================================================

CREATE TABLE IF NOT EXISTS readings_history (
    id SERIAL PRIMARY KEY,
    sensor_id VARCHAR(50) NOT NULL,
    humidity_percentage INTEGER NOT NULL CHECK (humidity_percentage >= 0 AND humidity_percentage <= 100),
    temperature_celsius INTEGER NOT NULL CHECK (temperature_celsius >= -50 AND temperature_celsius <= 100),
    timestamp TIMESTAMP NOT NULL,
    tx_hash VARCHAR(64),
    on_chain BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para readings_history
CREATE INDEX IF NOT EXISTS idx_readings_sensor_id ON readings_history(sensor_id);
CREATE INDEX IF NOT EXISTS idx_readings_timestamp ON readings_history(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_readings_tx_hash ON readings_history(tx_hash);
CREATE INDEX IF NOT EXISTS idx_readings_on_chain ON readings_history(on_chain);
CREATE INDEX IF NOT EXISTS idx_readings_sensor_timestamp ON readings_history(sensor_id, timestamp DESC);

COMMENT ON TABLE readings_history IS 'Histórico completo de lecturas de todos los sensores';
COMMENT ON COLUMN readings_history.on_chain IS 'TRUE si la lectura está actualmente en el datum blockchain, FALSE si fue archivada';
COMMENT ON COLUMN readings_history.tx_hash IS 'Hash de la transacción blockchain que registró esta lectura';

-- ============================================================================
-- TABLA: transactions_log
-- Propósito: Log de todas las transacciones enviadas al smart contract
-- ============================================================================

CREATE TABLE IF NOT EXISTS transactions_log (
    id SERIAL PRIMARY KEY,
    tx_hash VARCHAR(64) UNIQUE NOT NULL,
    tx_type VARCHAR(50) NOT NULL CHECK (tx_type IN (
        'RegisterSensor',
        'AddReading',
        'UpdateSensor',
        'DeactivateSensor',
        'UpdateAdmin'
    )),
    status VARCHAR(20) NOT NULL DEFAULT 'Pending' CHECK (status IN ('Pending', 'Confirmed', 'Failed')),
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    confirmed_at TIMESTAMP,
    error_message TEXT,
    datum_snapshot JSONB,
    request_data JSONB
);

-- Índices para transactions_log
CREATE INDEX IF NOT EXISTS idx_transactions_tx_hash ON transactions_log(tx_hash);
CREATE INDEX IF NOT EXISTS idx_transactions_tx_type ON transactions_log(tx_type);
CREATE INDEX IF NOT EXISTS idx_transactions_status ON transactions_log(status);
CREATE INDEX IF NOT EXISTS idx_transactions_submitted_at ON transactions_log(submitted_at DESC);

COMMENT ON TABLE transactions_log IS 'Log de todas las transacciones blockchain';
COMMENT ON COLUMN transactions_log.datum_snapshot IS 'Snapshot del datum después de confirmar la transacción';
COMMENT ON COLUMN transactions_log.request_data IS 'Datos de la solicitud original';

-- ============================================================================
-- TABLA: sensor_alerts
-- Propósito: Historial de alertas generadas por lecturas fuera de rango
-- ============================================================================

CREATE TABLE IF NOT EXISTS sensor_alerts (
    id SERIAL PRIMARY KEY,
    sensor_id VARCHAR(50) NOT NULL,
    reading_id INTEGER REFERENCES readings_history(id),
    alert_type VARCHAR(50) NOT NULL CHECK (alert_type IN (
        'HumidityTooLow',
        'HumidityTooHigh',
        'TemperatureTooLow',
        'TemperatureTooHigh',
        'SensorOffline'
    )),
    alert_level VARCHAR(20) NOT NULL CHECK (alert_level IN ('Warning', 'Critical')),
    message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP,
    resolved_by VARCHAR(56)
);

-- Índices para sensor_alerts
CREATE INDEX IF NOT EXISTS idx_alerts_sensor_id ON sensor_alerts(sensor_id);
CREATE INDEX IF NOT EXISTS idx_alerts_alert_type ON sensor_alerts(alert_type);
CREATE INDEX IF NOT EXISTS idx_alerts_created_at ON sensor_alerts(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_alerts_resolved ON sensor_alerts(resolved_at);

COMMENT ON TABLE sensor_alerts IS 'Histórico de alertas generadas por condiciones anormales';

-- ============================================================================
-- VISTAS ÚTILES
-- ============================================================================

-- Vista: Sensores actuales (solo versiones activas)
CREATE OR REPLACE VIEW current_sensors AS
SELECT
    sensor_id,
    location_latitude,
    location_longitude,
    location_zone_name,
    min_humidity_threshold,
    max_humidity_threshold,
    reading_interval_minutes,
    status,
    owner_pkh,
    installed_date,
    updated_at,
    tx_hash
FROM sensors_history
WHERE is_current = TRUE
ORDER BY sensor_id;

COMMENT ON VIEW current_sensors IS 'Configuración actual de todos los sensores activos';

-- Vista: Últimas lecturas por sensor
CREATE OR REPLACE VIEW latest_readings_per_sensor AS
SELECT DISTINCT ON (sensor_id)
    sensor_id,
    humidity_percentage,
    temperature_celsius,
    timestamp,
    on_chain,
    created_at
FROM readings_history
ORDER BY sensor_id, timestamp DESC;

COMMENT ON VIEW latest_readings_per_sensor IS 'Última lectura registrada para cada sensor';

-- Vista: Estadísticas por sensor
CREATE OR REPLACE VIEW sensor_statistics AS
SELECT
    sensor_id,
    COUNT(*) as total_readings,
    AVG(humidity_percentage) as avg_humidity,
    MIN(humidity_percentage) as min_humidity,
    MAX(humidity_percentage) as max_humidity,
    AVG(temperature_celsius) as avg_temperature,
    MIN(temperature_celsius) as min_temperature,
    MAX(temperature_celsius) as max_temperature,
    MIN(timestamp) as first_reading,
    MAX(timestamp) as last_reading
FROM readings_history
GROUP BY sensor_id;

COMMENT ON VIEW sensor_statistics IS 'Estadísticas agregadas de lecturas por sensor';

-- ============================================================================
-- FUNCIONES ÚTILES
-- ============================================================================

-- Función: Archivar lecturas antiguas del datum
CREATE OR REPLACE FUNCTION archive_old_readings(p_sensor_id VARCHAR, p_keep_count INTEGER DEFAULT 10)
RETURNS INTEGER AS $$
DECLARE
    v_archived_count INTEGER;
BEGIN
    -- Marcar como archivadas (on_chain=FALSE) las lecturas más antiguas
    WITH ranked_readings AS (
        SELECT id, ROW_NUMBER() OVER (ORDER BY timestamp DESC) as rn
        FROM readings_history
        WHERE sensor_id = p_sensor_id AND on_chain = TRUE
    )
    UPDATE readings_history r
    SET on_chain = FALSE
    FROM ranked_readings rr
    WHERE r.id = rr.id AND rr.rn > p_keep_count;

    GET DIAGNOSTICS v_archived_count = ROW_COUNT;
    RETURN v_archived_count;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION archive_old_readings IS 'Marca lecturas antiguas como archivadas (fuera del datum blockchain)';

-- Función: Marcar sensor como no actual
CREATE OR REPLACE FUNCTION mark_sensor_not_current(p_sensor_id VARCHAR)
RETURNS VOID AS $$
BEGIN
    UPDATE sensors_history
    SET is_current = FALSE
    WHERE sensor_id = p_sensor_id AND is_current = TRUE;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION mark_sensor_not_current IS 'Marca la versión actual de un sensor como histórica';

-- ============================================================================
-- DATOS INICIALES
-- ============================================================================

-- Trigger: Actualizar updated_at automáticamente
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_sensors_history_updated_at
    BEFORE UPDATE ON sensors_history
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- PERMISOS
-- ============================================================================

-- Otorgar permisos al usuario sensor_app
GRANT SELECT, INSERT, UPDATE, DELETE ON sensors_history TO sensor_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON readings_history TO sensor_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON transactions_log TO sensor_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON sensor_alerts TO sensor_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO sensor_app;

-- Vistas de solo lectura
GRANT SELECT ON current_sensors TO sensor_app;
GRANT SELECT ON latest_readings_per_sensor TO sensor_app;
GRANT SELECT ON sensor_statistics TO sensor_app;

-- Funciones
GRANT EXECUTE ON FUNCTION archive_old_readings TO sensor_app;
GRANT EXECUTE ON FUNCTION mark_sensor_not_current TO sensor_app;
