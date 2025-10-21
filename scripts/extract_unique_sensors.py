# -*- coding: utf-8 -*-
"""
Extraer sensores únicos del datum actual
Prepara datos para migración a PostgreSQL
"""

import sys
from pathlib import Path
from datetime import datetime
import json

# Agregar paths
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "pycardano-client"))

from pycardano_tx import CardanoTransactionBuilder

def extract_unique_sensors():
    """Extraer sensores únicos con deduplicación"""

    print("\n=== EXTRAYENDO SENSORES UNICOS ===\n")

    try:
        tx_builder = CardanoTransactionBuilder()
        print("[+] Obteniendo datum actual...")

        utxo = tx_builder.get_contract_utxo_with_datum()

        if not utxo:
            print("[ERROR] No se pudo obtener UTxO del contrato")
            return None

        # Decodificar datum desde el UTxO
        datum_bytes = utxo.output.datum
        current_datum = tx_builder.decode_datum(datum_bytes)

        print(f"[OK] Datum obtenido: {len(current_datum.sensors)} sensores totales\n")

        # Deduplicar sensores
        sensors_dict = {}

        for sensor in current_datum.sensors:
            sensor_id = sensor.sensor_id.decode('utf-8', errors='ignore')
            is_active = type(sensor.status).__name__ == 'Active'
            installed_date = sensor.installed_date

            if sensor_id not in sensors_dict:
                sensors_dict[sensor_id] = sensor
            else:
                existing = sensors_dict[sensor_id]
                existing_is_active = type(existing.status).__name__ == 'Active'
                existing_date = existing.installed_date

                # Preferir Active sobre Inactive
                if is_active and not existing_is_active:
                    sensors_dict[sensor_id] = sensor
                # Si ambos tienen mismo estado, preferir más reciente
                elif is_active == existing_is_active and installed_date > existing_date:
                    sensors_dict[sensor_id] = sensor

        print(f"[OK] Sensores únicos encontrados: {len(sensors_dict)}\n")

        # Convertir a formato exportable
        export_data = []

        for sensor_id, sensor in sensors_dict.items():
            status_name = type(sensor.status).__name__

            sensor_data = {
                "sensor_id": sensor_id,
                "location_latitude": float(sensor.location.latitude) / 1_000_000,
                "location_longitude": float(sensor.location.longitude) / 1_000_000,
                "location_zone_name": sensor.location.zone_name.decode('utf-8', errors='ignore'),
                "min_humidity_threshold": int(sensor.min_humidity_threshold),
                "max_humidity_threshold": int(sensor.max_humidity_threshold),
                "reading_interval_minutes": int(sensor.reading_interval_minutes),
                "status": status_name,
                "owner_pkh": sensor.owner.hex(),
                "installed_date": datetime.fromtimestamp(sensor.installed_date / 1000).isoformat()
            }

            export_data.append(sensor_data)

            print(f"  [{sensor_id}]")
            print(f"    Status: {status_name}")
            print(f"    Location: {sensor_data['location_zone_name']}")
            print(f"    Installed: {sensor_data['installed_date']}")
            print()

        # Guardar a archivo JSON
        output_file = Path(__file__).parent / "sensors_export.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)

        print(f"[OK] Datos exportados a: {output_file}")
        print(f"\n[RESUMEN]")
        print(f"  Total sensores en datum: {len(current_datum.sensors)}")
        print(f"  Sensores unicos: {len(sensors_dict)}")
        print(f"  Duplicados eliminados: {len(current_datum.sensors) - len(sensors_dict)}")

        return export_data

    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    extract_unique_sensors()
