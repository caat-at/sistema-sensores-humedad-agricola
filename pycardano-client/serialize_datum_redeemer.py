# -*- coding: utf-8 -*-
"""
Script para serializar datum y redeemer a CBOR hex
Python serializa correctamente, Lucid construye la transacción
"""

import json
import sys
import time
from pycardano_tx import CardanoTransactionBuilder
from contract_types import create_sensor_config, RegisterSensor, HumiditySensorDatum


def serialize_for_lucid(sensor_id: str, latitude: float, longitude: float,
                        zone_name: str, min_humidity: int, max_humidity: int,
                        reading_interval: int):
    """
    Serializa el nuevo datum y redeemer a CBOR hex para Lucid

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

    # 3. Crear nuevo sensor
    timestamp_now = int(time.time() * 1000)

    new_sensor = create_sensor_config(
        sensor_id=sensor_id,
        latitude=latitude,
        longitude=longitude,
        zone_name=zone_name,
        min_humidity=min_humidity,
        max_humidity=max_humidity,
        reading_interval=reading_interval,
        owner_pkh=builder.wallet_pkh,
        installed_timestamp=timestamp_now
    )

    # 4. Crear nuevo datum con sensor agregado
    new_datum = HumiditySensorDatum(
        sensors=[*current_datum.sensors, new_sensor],
        recent_readings=current_datum.recent_readings,
        admin=builder.wallet_pkh,
        last_updated=timestamp_now,
        total_sensors=current_datum.total_sensors + 1
    )

    # 5. Crear redeemer
    redeemer = RegisterSensor(config=new_sensor)

    # 6. Serializar a CBOR hex
    datum_cbor_hex = new_datum.to_cbor_hex()
    redeemer_cbor_hex = redeemer.to_cbor_hex()

    # 7. Retornar como JSON
    result = {
        "datum_cbor_hex": datum_cbor_hex,
        "redeemer_cbor_hex": redeemer_cbor_hex,
        "sensor_id": sensor_id,
        "total_sensors": current_datum.total_sensors + 1
    }

    return result


if __name__ == "__main__":
    # Configuración del sensor
    sensor_id = "SENSOR_003"
    latitude = -34.62
    longitude = -58.50
    zone_name = "Campo Este - Parcela C"
    min_humidity = 40
    max_humidity = 80
    reading_interval = 120

    try:
        result = serialize_for_lucid(
            sensor_id, latitude, longitude, zone_name,
            min_humidity, max_humidity, reading_interval
        )

        # Imprimir JSON para que Lucid lo lea
        print(json.dumps(result))

    except Exception as e:
        error_result = {
            "error": str(e)
        }
        print(json.dumps(error_result), file=sys.stderr)
        sys.exit(1)
