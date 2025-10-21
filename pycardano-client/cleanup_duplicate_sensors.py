# -*- coding: utf-8 -*-
"""
Script para limpiar sensores duplicados del datum
Elimina versiones duplicadas de SENSOR_002, dejando solo la versión Inactive más antigua
"""

import sys
from pycardano_tx import CardanoTransactionBuilder
from contract_types import HumiditySensorDatum, UpdateAdmin


def cleanup_duplicate_sensors():
    """
    Limpia sensores duplicados del datum
    Para SENSOR_002: mantiene solo la versión Inactive (la más antigua)
    """
    print("\n[+] Inicializando limpieza de sensores duplicados...")

    # 1. Inicializar builder
    builder = CardanoTransactionBuilder()

    # 2. Obtener datum actual
    contract_utxo = builder.get_contract_utxo_with_datum()
    if not contract_utxo:
        raise Exception("No UTxO with datum found")

    current_datum = builder.decode_datum(contract_utxo.output.datum)

    print(f"[+] Sensores actuales en datum: {len(current_datum.sensors)}")

    # 3. Mostrar sensores actuales
    print("\n[INFO] Sensores antes de la limpieza:")
    for i, sensor in enumerate(current_datum.sensors):
        sensor_id = sensor.sensor_id.decode('utf-8', errors='ignore')
        status = type(sensor.status).__name__
        date = sensor.installed_date
        print(f"  {i+1}. {sensor_id} - {status} - Date: {date}")

    # 4. Deduplicar SENSOR_002 - mantener solo el Inactive (el más antiguo)
    cleaned_sensors = []
    sensor_002_inactive = None

    for sensor in current_datum.sensors:
        sensor_id = sensor.sensor_id.decode('utf-8', errors='ignore')
        is_active = type(sensor.status).__name__ == 'Active'

        if sensor_id == "SENSOR_002":
            # Para SENSOR_002, solo queremos el Inactive
            if not is_active:
                if sensor_002_inactive is None:
                    # Guardamos el primer Inactive que encontremos
                    sensor_002_inactive = sensor
                    print(f"\n[+] Manteniendo SENSOR_002 Inactive (Date: {sensor.installed_date})")
                else:
                    print(f"[!] Omitiendo SENSOR_002 Inactive duplicado (Date: {sensor.installed_date})")
            else:
                print(f"[!] Eliminando SENSOR_002 Active (Date: {sensor.installed_date})")
        else:
            # Otros sensores los mantenemos
            cleaned_sensors.append(sensor)

    # Agregar el SENSOR_002 Inactive al final
    if sensor_002_inactive:
        cleaned_sensors.append(sensor_002_inactive)

    # 5. Mostrar resultado
    print(f"\n[INFO] Sensores después de la limpieza: {len(cleaned_sensors)}")
    print("\n[INFO] Sensores limpiados:")
    for i, sensor in enumerate(cleaned_sensors):
        sensor_id = sensor.sensor_id.decode('utf-8', errors='ignore')
        status = type(sensor.status).__name__
        date = sensor.installed_date
        print(f"  {i+1}. {sensor_id} - {status} - Date: {date}")

    # 6. Crear nuevo datum con sensores limpiados
    import time
    timestamp_now = int(time.time() * 1000)

    new_datum = HumiditySensorDatum(
        sensors=cleaned_sensors,
        recent_readings=current_datum.recent_readings,
        admin=current_datum.admin,
        last_updated=timestamp_now,
        total_sensors=current_datum.total_sensors  # Mantener el contador
    )

    print("\n[+] Nuevo datum creado con sensores limpiados")
    print(f"[INFO] Total de sensores en nuevo datum: {len(new_datum.sensors)}")

    # 7. Crear redeemer UpdateAdmin (usamos este para actualizar el datum completo)
    # Mantenemos el mismo admin
    redeemer = UpdateAdmin(new_admin=current_datum.admin)

    # 8. Construir y enviar transacción
    print("\n[+] Construyendo transacción para actualizar datum...")

    from tx_builder_hybrid import HybridTransactionBuilder

    hybrid_builder = HybridTransactionBuilder()

    # Serializar datum y redeemer
    datum_cbor_hex = new_datum.to_cbor_hex()
    redeemer_cbor_hex = redeemer.to_cbor_hex()

    print("[OK] Datum y redeemer serializados")

    # Llamar al script Lucid para update-datum
    import subprocess
    import json
    from pathlib import Path

    lucid_script = Path(__file__).parent.parent / "mesh-client" / "update-datum-lucid.js"

    result = subprocess.run(
        ["node", str(lucid_script), datum_cbor_hex, redeemer_cbor_hex],
        capture_output=True,
        text=True,
        timeout=120,
        cwd=str(lucid_script.parent)
    )

    if result.returncode != 0:
        print(f"\n[ERROR] Script Lucid falló:")
        print(f"Stdout: {result.stdout}")
        print(f"Stderr: {result.stderr}")
        raise Exception("Failed to execute Lucid script")

    # Parsear resultado
    output_lines = result.stdout.strip().split('\n')
    json_output = output_lines[-1]
    result_data = json.loads(json_output)

    if not result_data.get("success"):
        raise Exception(f"Transaction failed: {result_data.get('error', 'Unknown error')}")

    tx_hash = result_data["txHash"]
    explorer_url = result_data["explorer"]

    print("\n[OK] ✅ Transacción enviada exitosamente!")
    print(f"    TxHash: {tx_hash}")
    print(f"    Explorer: {explorer_url}")
    print("\n[INFO] Espera ~20 segundos para que la transacción se confirme en la blockchain")

    return tx_hash


if __name__ == "__main__":
    try:
        tx_hash = cleanup_duplicate_sensors()
        print(f"\n✅ Limpieza completada exitosamente!")
        print(f"TxHash: {tx_hash}")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error durante la limpieza: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
