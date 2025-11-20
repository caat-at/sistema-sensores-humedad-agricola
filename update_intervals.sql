-- Actualizar intervalos de lectura a 60 minutos
UPDATE sensors_history
SET reading_interval_minutes = 60
WHERE is_current = true;

-- Verificar cambios
SELECT sensor_id, reading_interval_minutes, location_zone_name
FROM sensors_history
WHERE is_current = true
ORDER BY sensor_id;
