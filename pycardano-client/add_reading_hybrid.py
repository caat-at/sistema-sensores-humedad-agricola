# -*- coding: utf-8 -*-
"""
Script principal para agregar lectura de sensor - Approach Híbrido
Usa PyCardano para serialización y Lucid para transacciones
"""

import config
from pycardano_tx import CardanoTransactionBuilder
from tx_builder_hybrid import HybridTransactionBuilder


def main():
    print("="*70)
    print(" AGREGAR LECTURA DE SENSOR - Approach Híbrido Python + Lucid")
    print("="*70)

    # 1. Inicializar builder (para queries)
    print("[+] Inicializando CardanoTransactionBuilder...")
    builder = CardanoTransactionBuilder()

    # 2. Configuración de la lectura
    print("\n[+] Configuracion de la lectura:")
    print()

    sensor_id = "SENSOR_003"  # Sensor a leer
    humidity = 88  # 88% humedad (Critical - Exceso agua)
    temperature = 16  # 16°C

    print(f"    Sensor ID: {sensor_id}")
    print(f"    Humedad: {humidity}%")
    print(f"    Temperatura: {temperature}°C")

    # 3. Verificar estado del contrato
    print("\n[+] Verificando estado del contrato...")
    print()

    contract_utxo = builder.get_contract_utxo_with_datum()

    if not contract_utxo:
        print("[ERROR] No se encontro UTxO del contrato con datum")
        return

    current_datum = builder.decode_datum(contract_utxo.output.datum)

    print("[OK] Estado actual del contrato:")
    print(f"    Sensores registrados: {len(current_datum.sensors)}")
    print(f"    Lecturas actuales: {len(current_datum.recent_readings)}")
    print(f"    Total sensores: {current_datum.total_sensors}")

    # 4. Verificar que el sensor existe
    sensor_id_bytes = sensor_id.encode('utf-8')
    matching_sensors = [s for s in current_datum.sensors if s.sensor_id == sensor_id_bytes]

    if len(matching_sensors) == 0:
        print(f"\n[ERROR] Sensor {sensor_id} no encontrado en el contrato")
        print("\nSensores disponibles:")
        for s in current_datum.sensors:
            print(f"  - {s.sensor_id.decode('utf-8')}")
        return

    sensor_config = matching_sensors[0]

    print(f"\n[OK] Sensor encontrado:")
    print(f"    ID: {sensor_config.sensor_id.decode('utf-8')}")
    print(f"    Ubicacion: {sensor_config.location.zone_name.decode('utf-8')}")
    print(f"    Umbrales: {sensor_config.min_humidity_threshold}% - {sensor_config.max_humidity_threshold}%")
    print(f"    Estado: Active")

    # 5. Usar HybridTransactionBuilder
    print("\n[+] Usando HybridTransactionBuilder...")

    hybrid_builder = HybridTransactionBuilder()

    # 6. Mostrar resumen
    print("\n" + "="*70)
    print(" RESUMEN DE TRANSACCION")
    print("="*70)
    print()
    print(f"Operacion: AddReading")
    print(f"Sensor ID: {sensor_id}")
    print(f"Humedad: {humidity}%")
    print(f"Temperatura: {temperature}°C")
    print()
    print("IMPORTANTE: Esto enviara una transaccion REAL a Preview Testnet")
    print()

    # 7. Enviar transacción usando Lucid (sin confirmación para testing)
    try:
        tx_hash = hybrid_builder.add_reading(
            sensor_id=sensor_id,
            humidity=humidity,
            temperature=temperature
        )

        # 8. Mostrar resultado
        print("\n" + "="*70)
        print(" LECTURA AGREGADA EXITOSAMENTE!")
        print("="*70)
        print()
        print(f"TxHash: {tx_hash}")
        print()
        print(f"Explorer:")
        print(f"  https://preview.cardanoscan.io/transaction/{tx_hash}")
        print()
        print("="*70)
        print()
        print("Espera 1-2 minutos para confirmacion en blockchain")
        print()
        print("Luego ejecuta:")
        print("  python decode_datum.py")
        print()
        print("Deberias ver:")
        print(f"  - Lecturas registradas: {len(current_datum.recent_readings) + 1}")
        print(f"  - Nueva lectura de {sensor_id}: {humidity}% humedad, {temperature}°C")
        print()

    except Exception as e:
        print(f"\n[ERROR] Error agregando lectura: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
