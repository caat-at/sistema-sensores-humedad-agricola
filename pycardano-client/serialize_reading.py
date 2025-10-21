# -*- coding: utf-8 -*-
"""
Script para serializar AddReading a CBOR hex
Agrega una nueva lectura de humedad al sistema
"""

import json
import sys
import time
from pycardano_tx import CardanoTransactionBuilder
from contract_types import (
    HumidityReading, AddReading, HumiditySensorDatum,
    Normal, Low, High, Critical
)


def calculate_alert_level(humidity: int, min_threshold: int, max_threshold: int):
    """
    Calcular nivel de alerta basado en humedad y umbrales

    Normal: 40-70%
    Low: <40% - Necesita riego
    High: >70% - Riesgo de hongos
    Critical: <20% o >85% - Acción inmediata
    """
    if humidity < 20 or humidity > 85:
        return Critical()
    elif humidity < 40:
        return Low()
    elif humidity > 70:
        return High()
    else:
        return Normal()


def serialize_reading_for_lucid(
    sensor_id: str,
    humidity_percentage: int,
    temperature_celsius: int
):
    """
    Serializa una nueva lectura y actualiza el datum con el redeemer

    Args:
        sensor_id: ID del sensor (ej: "SENSOR_001")
        humidity_percentage: Humedad 0-100%
        temperature_celsius: Temperatura en Celsius

    Returns:
        JSON con datum_cbor_hex y redeemer_cbor_hex
    """
    # 1. Inicializar builder
    builder = CardanoTransactionBuilder()

    # 2. Obtener datum actual del contrato
    contract_utxo = builder.get_contract_utxo_with_datum()
    if not contract_utxo:
        raise Exception("No UTxO with datum found")

    current_datum_bytes = contract_utxo.output.datum
    current_datum = builder.decode_datum(current_datum_bytes)

    # 3. Verificar que el sensor existe y elegir la versión más reciente/activa
    sensor_id_bytes = sensor_id.encode('utf-8')
    matching_sensors = [s for s in current_datum.sensors if s.sensor_id == sensor_id_bytes]

    if len(matching_sensors) == 0:
        raise Exception(f"Sensor {sensor_id} not found in contract")

    # Deduplicar: preferir Active sobre Inactive, luego el más reciente
    sensor_config = None
    for sensor in matching_sensors:
        is_active = type(sensor.status).__name__ == 'Active'

        if sensor_config is None:
            sensor_config = sensor
        else:
            existing_is_active = type(sensor_config.status).__name__ == 'Active'

            # Preferir Active sobre Inactive
            if is_active and not existing_is_active:
                sensor_config = sensor
            # Si ambos tienen el mismo estado, preferir el más reciente
            elif is_active == existing_is_active and sensor.installed_date > sensor_config.installed_date:
                sensor_config = sensor

    # Verificar que el sensor seleccionado esté activo
    if type(sensor_config.status).__name__ != 'Active':
        raise Exception(f"Sensor {sensor_id} is not active (status: {type(sensor_config.status).__name__}). Cannot add readings to inactive sensors.")

    # 4. Calcular nivel de alerta
    alert_level = calculate_alert_level(
        humidity_percentage,
        sensor_config.min_humidity_threshold,
        sensor_config.max_humidity_threshold
    )

    # 5. Crear nueva lectura
    timestamp_now = int(time.time() * 1000)

    new_reading = HumidityReading(
        sensor_id=sensor_id_bytes,
        humidity_percentage=humidity_percentage,
        temperature_celsius=temperature_celsius,
        timestamp=timestamp_now,
        alert_level=alert_level
    )

    # 6. Crear nuevo datum con lectura agregada
    # Mantener las últimas N lecturas (ej: 10)
    max_readings = 10
    updated_readings = [*current_datum.recent_readings, new_reading]

    # Si excedemos el máximo, remover las más antiguas
    if len(updated_readings) > max_readings:
        updated_readings = updated_readings[-max_readings:]

    new_datum = HumiditySensorDatum(
        sensors=current_datum.sensors,  # Sensores sin cambios
        recent_readings=updated_readings,
        admin=current_datum.admin,
        last_updated=timestamp_now,
        total_sensors=current_datum.total_sensors
    )

    # 7. Crear redeemer AddReading
    redeemer = AddReading(reading=new_reading)

    # 8. Serializar a CBOR hex
    datum_cbor_hex = new_datum.to_cbor_hex()
    redeemer_cbor_hex = redeemer.to_cbor_hex()

    # 9. Retornar como JSON
    result = {
        "datum_cbor_hex": datum_cbor_hex,
        "redeemer_cbor_hex": redeemer_cbor_hex,
        "sensor_id": sensor_id,
        "humidity": humidity_percentage,
        "temperature": temperature_celsius,
        "alert_level": alert_level.__class__.__name__,
        "total_readings": len(updated_readings),
        "timestamp": timestamp_now
    }

    return result


if __name__ == "__main__":
    # Configuración de la lectura desde argumentos o valores por defecto
    if len(sys.argv) >= 4:
        sensor_id = sys.argv[1]
        humidity_percentage = int(sys.argv[2])
        temperature_celsius = int(sys.argv[3])
    else:
        # Valores por defecto para testing
        sensor_id = "SENSOR_001"
        humidity_percentage = 55
        temperature_celsius = 24

    try:
        result = serialize_reading_for_lucid(
            sensor_id,
            humidity_percentage,
            temperature_celsius
        )

        # Imprimir JSON para que Lucid lo lea
        print(json.dumps(result))

    except Exception as e:
        error_result = {
            "error": str(e)
        }
        print(json.dumps(error_result), file=sys.stderr)
        sys.exit(1)
