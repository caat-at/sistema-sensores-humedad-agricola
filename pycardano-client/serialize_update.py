# -*- coding: utf-8 -*-
"""
Serializa UpdateSensorConfig datum y redeemer a CBOR hex para Lucid

Este script:
1. Lee el datum actual del contrato
2. Busca el sensor a actualizar
3. Crea la nueva configuración del sensor
4. Actualiza el datum con el sensor modificado
5. Crea el redeemer UpdateSensorConfig
6. Serializa ambos a CBOR hex
7. Retorna JSON con los CBOR hex para Lucid
"""

import sys
import json
from datetime import datetime
from pycardano_tx import CardanoTransactionBuilder
from contract_types import (
    HumiditySensorDatum,
    SensorConfig,
    UpdateSensorConfig,
    Location,
    Active, Inactive, Maintenance, ErrorStatus
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


def parse_status(status_str: str):
    """
    Convierte string a tipo SensorStatus

    Args:
        status_str: "Active", "Inactive", "Maintenance", o "Error"

    Returns:
        Instancia del tipo apropiado
    """
    status_map = {
        "Active": Active(),
        "Inactive": Inactive(),
        "Maintenance": Maintenance(),
        "Error": ErrorStatus()
    }

    status = status_map.get(status_str)
    if status is None:
        raise ValueError(f"Estado inválido: {status_str}. Debe ser: Active, Inactive, Maintenance, o Error")

    return status


def serialize_update_for_lucid(
    sensor_id: str,
    new_min_humidity: int = None,
    new_max_humidity: int = None,
    new_reading_interval: int = None,
    new_latitude: float = None,
    new_longitude: float = None,
    new_zone_name: str = None,
    new_status: str = None
) -> dict:
    """
    Serializa UpdateSensorConfig datum y redeemer

    Args:
        sensor_id: ID del sensor a actualizar
        new_min_humidity: Nuevo umbral mínimo (opcional)
        new_max_humidity: Nuevo umbral máximo (opcional)
        new_reading_interval: Nuevo intervalo en minutos (opcional)
        new_latitude: Nueva latitud (opcional)
        new_longitude: Nueva longitud (opcional)
        new_zone_name: Nuevo nombre de zona (opcional)
        new_status: Nuevo estado: "Active", "Inactive", "Maintenance", "Error" (opcional)

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

    # 4. Buscar el sensor a actualizar
    sensor_id_bytes = sensor_id.encode('utf-8')
    sensor_index = find_sensor_index(current_datum.sensors, sensor_id_bytes)

    if sensor_index == -1:
        available_sensors = [s.sensor_id.decode('utf-8', errors='ignore') for s in current_datum.sensors]
        raise ValueError(
            f"Sensor '{sensor_id}' no encontrado. "
            f"Sensores disponibles: {', '.join(available_sensors)}"
        )

    old_sensor = current_datum.sensors[sensor_index]

    print(f"[+] Sensor encontrado: {sensor_id}")
    print(f"    Ubicacion actual: {old_sensor.location.zone_name.decode('utf-8', errors='ignore')}")
    print(f"    Umbrales actuales: {old_sensor.min_humidity_threshold}% - {old_sensor.max_humidity_threshold}%")
    print(f"    Intervalo actual: {old_sensor.reading_interval_minutes} minutos")
    print()

    # 5. Crear nueva configuración del sensor (mantener valores anteriores si no se especifican nuevos)

    # Umbrales
    final_min_humidity = new_min_humidity if new_min_humidity is not None else old_sensor.min_humidity_threshold
    final_max_humidity = new_max_humidity if new_max_humidity is not None else old_sensor.max_humidity_threshold

    # Validar umbrales
    if final_min_humidity < 0 or final_min_humidity > 100:
        raise ValueError(f"Umbral mínimo inválido: {final_min_humidity}. Debe estar entre 0-100%")
    if final_max_humidity < 0 or final_max_humidity > 100:
        raise ValueError(f"Umbral máximo inválido: {final_max_humidity}. Debe estar entre 0-100%")
    if final_min_humidity >= final_max_humidity:
        raise ValueError(f"Umbral mínimo ({final_min_humidity}%) debe ser menor que máximo ({final_max_humidity}%)")

    # Intervalo
    final_reading_interval = new_reading_interval if new_reading_interval is not None else old_sensor.reading_interval_minutes
    if final_reading_interval <= 0:
        raise ValueError(f"Intervalo inválido: {final_reading_interval}. Debe ser mayor a 0")

    # Ubicación
    if new_latitude is not None and new_longitude is not None and new_zone_name is not None:
        # Nueva ubicación completa
        new_location = Location(
            latitude=int(new_latitude * 1_000_000),
            longitude=int(new_longitude * 1_000_000),
            zone_name=new_zone_name.encode('utf-8')
        )
    else:
        # Mantener ubicación anterior
        new_location = old_sensor.location

    # Estado
    if new_status is not None:
        final_status = parse_status(new_status)
    else:
        final_status = old_sensor.status

    # 6. Crear nuevo SensorConfig con valores actualizados
    timestamp_now = int(datetime.now().timestamp() * 1000)

    updated_sensor = SensorConfig(
        sensor_id=sensor_id_bytes,
        location=new_location,
        min_humidity_threshold=final_min_humidity,
        max_humidity_threshold=final_max_humidity,
        reading_interval_minutes=final_reading_interval,
        status=final_status,
        owner=old_sensor.owner,  # Owner no cambia
        installed_date=old_sensor.installed_date  # Installed date no cambia
    )

    print(f"[+] Nueva configuracion:")
    print(f"    Ubicacion: {new_location.zone_name.decode('utf-8', errors='ignore')}")
    print(f"    Umbrales: {final_min_humidity}% - {final_max_humidity}%")
    print(f"    Intervalo: {final_reading_interval} minutos")

    # Mostrar cambios
    status_name = "Active" if isinstance(final_status, Active) else \
                  "Inactive" if isinstance(final_status, Inactive) else \
                  "Maintenance" if isinstance(final_status, Maintenance) else "Error"
    print(f"    Estado: {status_name}")
    print()

    # 7. Actualizar lista de sensores
    updated_sensors = current_datum.sensors.copy()
    updated_sensors[sensor_index] = updated_sensor

    # 8. Crear nuevo datum con sensor actualizado
    new_datum = HumiditySensorDatum(
        sensors=updated_sensors,
        recent_readings=current_datum.recent_readings,  # Readings no cambian
        admin=builder.wallet_pkh,
        last_updated=timestamp_now,
        total_sensors=current_datum.total_sensors  # Total no cambia en update
    )

    # 9. Crear redeemer UpdateSensorConfig
    redeemer = UpdateSensorConfig(
        sensor_id=sensor_id_bytes,
        new_config=updated_sensor
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
        "changes": {
            "min_humidity": {
                "old": old_sensor.min_humidity_threshold,
                "new": final_min_humidity
            },
            "max_humidity": {
                "old": old_sensor.max_humidity_threshold,
                "new": final_max_humidity
            },
            "reading_interval": {
                "old": old_sensor.reading_interval_minutes,
                "new": final_reading_interval
            },
            "status": {
                "old": type(old_sensor.status).__name__,
                "new": status_name
            }
        }
    }


def main():
    """
    CLI para serializar UpdateSensorConfig

    Uso:
        python serialize_update.py SENSOR_ID [opciones]

    Opciones:
        --min-humidity INT        Nuevo umbral mínimo (0-100)
        --max-humidity INT        Nuevo umbral máximo (0-100)
        --interval INT            Nuevo intervalo en minutos
        --latitude FLOAT          Nueva latitud
        --longitude FLOAT         Nueva longitud
        --zone-name STR           Nuevo nombre de zona
        --status STR              Nuevo estado (Active/Inactive/Maintenance/Error)
    """

    if len(sys.argv) < 2:
        print("Error: Se requiere sensor_id")
        print()
        print("Uso: python serialize_update.py SENSOR_ID [opciones]")
        print()
        print("Opciones:")
        print("  --min-humidity INT     Nuevo umbral mínimo (0-100)")
        print("  --max-humidity INT     Nuevo umbral máximo (0-100)")
        print("  --interval INT         Nuevo intervalo en minutos")
        print("  --latitude FLOAT       Nueva latitud")
        print("  --longitude FLOAT      Nueva longitud")
        print("  --zone-name STR        Nuevo nombre de zona")
        print("  --status STR           Nuevo estado (Active/Inactive/Maintenance/Error)")
        print()
        print("Ejemplo:")
        print("  python serialize_update.py SENSOR_001 --min-humidity 25 --max-humidity 75")
        sys.exit(1)

    sensor_id = sys.argv[1]

    # Parsear argumentos opcionales
    args = {}
    i = 2
    while i < len(sys.argv):
        if sys.argv[i] == '--min-humidity' and i + 1 < len(sys.argv):
            args['new_min_humidity'] = int(sys.argv[i + 1])
            i += 2
        elif sys.argv[i] == '--max-humidity' and i + 1 < len(sys.argv):
            args['new_max_humidity'] = int(sys.argv[i + 1])
            i += 2
        elif sys.argv[i] == '--interval' and i + 1 < len(sys.argv):
            args['new_reading_interval'] = int(sys.argv[i + 1])
            i += 2
        elif sys.argv[i] == '--latitude' and i + 1 < len(sys.argv):
            args['new_latitude'] = float(sys.argv[i + 1])
            i += 2
        elif sys.argv[i] == '--longitude' and i + 1 < len(sys.argv):
            args['new_longitude'] = float(sys.argv[i + 1])
            i += 2
        elif sys.argv[i] == '--zone-name' and i + 1 < len(sys.argv):
            args['new_zone_name'] = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == '--status' and i + 1 < len(sys.argv):
            args['new_status'] = sys.argv[i + 1]
            i += 2
        else:
            print(f"Warning: Argumento desconocido '{sys.argv[i]}'")
            i += 1

    # Validar que al menos un parámetro se esté actualizando
    if not args:
        print("Error: Debe especificar al menos un parámetro a actualizar")
        sys.exit(1)

    try:
        result = serialize_update_for_lucid(sensor_id, **args)

        # Output como JSON para Lucid
        print(json.dumps(result, indent=2))

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
