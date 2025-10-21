# -*- coding: utf-8 -*-
"""
Serializa DeactivateSensor datum y redeemer a CBOR hex para Lucid

Este script:
1. Lee el datum actual del contrato
2. Busca el sensor a desactivar
3. Cambia el estado del sensor a Inactive
4. Crea el redeemer DeactivateSensor
5. Serializa ambos a CBOR hex
6. Retorna JSON con los CBOR hex para Lucid
"""

import sys
import json
from datetime import datetime
from pycardano_tx import CardanoTransactionBuilder
from contract_types import (
    HumiditySensorDatum,
    SensorConfig,
    DeactivateSensor,
    Inactive
)


def find_sensor_index(sensors: list, sensor_id: bytes) -> int:
    """
    Encuentra el índice de un sensor en la lista

    Args:
        sensors: Lista de SensorConfig
        sensor_id: ID del sensor a buscar

    Returns:
        Índice del sensor o -1 si no existe
    """
    for i, sensor in enumerate(sensors):
        if sensor.sensor_id == sensor_id:
            return i
    return -1


def serialize_deactivate_for_lucid(sensor_id: str) -> dict:
    """
    Serializa DeactivateSensor datum y redeemer

    Args:
        sensor_id: ID del sensor a desactivar

    Returns:
        dict con datum_cbor_hex y redeemer_cbor_hex
    """

    # 1. Inicializar builder
    builder = CardanoTransactionBuilder()

    # 2. Obtener UTxO actual del contrato
    print(f"[+] Obteniendo UTxO del contrato...")
    contract_utxo = builder.get_contract_utxo_with_datum()

    # 3. Decodificar datum actual
    print(f"[+] Decodificando datum actual...")
    current_datum = builder.decode_datum(contract_utxo.output.datum)

    print(f"[+] Estado actual del contrato:")
    print(f"    Sensores registrados: {len(current_datum.sensors)}")
    print(f"    Total sensores: {current_datum.total_sensors}")
    print()

    # 4. Buscar el sensor a desactivar
    sensor_id_bytes = sensor_id.encode('utf-8')
    sensor_index = find_sensor_index(current_datum.sensors, sensor_id_bytes)

    if sensor_index == -1:
        available_sensors = [s.sensor_id.decode('utf-8', errors='ignore') for s in current_datum.sensors]
        raise ValueError(
            f"Sensor '{sensor_id}' no encontrado. "
            f"Sensores disponibles: {', '.join(available_sensors)}"
        )

    old_sensor = current_datum.sensors[sensor_index]

    # Obtener nombre del estado actual
    old_status_name = type(old_sensor.status).__name__

    print(f"[+] Sensor encontrado: {sensor_id}")
    print(f"    Ubicacion: {old_sensor.location.zone_name.decode('utf-8', errors='ignore')}")
    print(f"    Estado actual: {old_status_name}")
    print()

    # 5. Verificar que no esté ya inactivo
    if isinstance(old_sensor.status, Inactive):
        raise ValueError(f"El sensor {sensor_id} ya está desactivado (estado: Inactive)")

    # 6. Crear nueva configuración del sensor con estado Inactive
    timestamp_now = int(datetime.now().timestamp() * 1000)

    deactivated_sensor = SensorConfig(
        sensor_id=sensor_id_bytes,
        location=old_sensor.location,
        min_humidity_threshold=old_sensor.min_humidity_threshold,
        max_humidity_threshold=old_sensor.max_humidity_threshold,
        reading_interval_minutes=old_sensor.reading_interval_minutes,
        status=Inactive(),  # Cambiar a Inactive
        owner=old_sensor.owner,
        installed_date=old_sensor.installed_date
    )

    print(f"[+] Desactivando sensor...")
    print(f"    Estado: {old_status_name} -> Inactive")
    print()

    # 7. Actualizar lista de sensores
    updated_sensors = current_datum.sensors.copy()
    updated_sensors[sensor_index] = deactivated_sensor

    # 8. Crear nuevo datum con sensor desactivado
    new_datum = HumiditySensorDatum(
        sensors=updated_sensors,
        recent_readings=current_datum.recent_readings,  # Readings no cambian
        admin=builder.wallet_pkh,
        last_updated=timestamp_now,
        total_sensors=current_datum.total_sensors  # Total no cambia
    )

    # 9. Crear redeemer DeactivateSensor
    redeemer = DeactivateSensor(
        sensor_id=sensor_id_bytes
    )

    # 10. Serializar a CBOR hex
    print(f"[+] Serializando datum y redeemer a CBOR...")
    datum_cbor_hex = new_datum.to_cbor_hex()
    redeemer_cbor_hex = redeemer.to_cbor_hex()

    print(f"[OK] Serialization exitosa")
    print(f"    Datum CBOR length: {len(datum_cbor_hex)} chars")
    print(f"    Redeemer CBOR length: {len(redeemer_cbor_hex)} chars")
    print()

    return {
        "datum_cbor_hex": datum_cbor_hex,
        "redeemer_cbor_hex": redeemer_cbor_hex,
        "sensor_id": sensor_id,
        "old_status": old_status_name,
        "new_status": "Inactive"
    }


def main():
    """
    CLI para serializar DeactivateSensor

    Uso:
        python serialize_deactivate.py SENSOR_ID
    """

    if len(sys.argv) < 2:
        print("Error: Se requiere sensor_id")
        print()
        print("Uso: python serialize_deactivate.py SENSOR_ID")
        print()
        print("Ejemplo:")
        print("  python serialize_deactivate.py SENSOR_002")
        sys.exit(1)

    sensor_id = sys.argv[1]

    try:
        result = serialize_deactivate_for_lucid(sensor_id)

        # Output como JSON para Lucid
        print(json.dumps(result, indent=2))

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
