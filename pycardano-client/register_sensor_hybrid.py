# -*- coding: utf-8 -*-
"""
Script para registrar un nuevo sensor usando el approach híbrido
Python para lógica de negocio + Lucid para construcción de TX
"""

import time
from pycardano_tx import CardanoTransactionBuilder
from contract_types import create_sensor_config
from tx_builder_hybrid import HybridTransactionBuilder


def main():
    print("="*70)
    print(" REGISTRAR NUEVO SENSOR - Approach Híbrido Python + Lucid")
    print("="*70)
    print()

    # 1. Inicializar builder (para queries y wallet info)
    print("[+] Inicializando CardanoTransactionBuilder...")
    builder = CardanoTransactionBuilder()

    # 2. Configuración del sensor a registrar
    print("\n[+] Configuracion del sensor:")
    print()

    sensor_id = "SENSOR_003"  # Testing con Lucid Evolution
    latitude = -34.62  # Buenos Aires, Argentina (ejemplo)
    longitude = -58.50
    zone_name = "Campo Este - Parcela C"
    min_humidity = 40
    max_humidity = 80
    reading_interval = 120  # minutos

    print(f"    ID: {sensor_id}")
    print(f"    Ubicacion: {zone_name}")
    print(f"    Coordenadas: {latitude}, {longitude}")
    print(f"    Umbral humedad: {min_humidity}% - {max_humidity}%")
    print(f"    Intervalo lecturas: {reading_interval} minutos")
    print()

    # 3. Obtener UTxO del contrato (verificación)
    print("[+] Verificando estado del contrato...")
    contract_utxo = builder.get_contract_utxo_with_datum()

    if not contract_utxo:
        print("[ERROR] No se encontro UTxO del contrato con datum")
        print("[!] Ejecuta primero: node ../mesh-client/init-lucid.js")
        return

    # 4. Decodificar datum actual (verificación)
    current_datum_bytes = contract_utxo.output.datum
    current_datum = builder.decode_datum(current_datum_bytes)

    print(f"[OK] Estado actual del contrato:")
    print(f"    Sensores actuales: {len(current_datum.sensors)}")
    print(f"    Lecturas actuales: {len(current_datum.recent_readings)}")
    print(f"    Total sensores: {current_datum.total_sensors}")

    # 5. Crear configuración del nuevo sensor
    print("\n[+] Creando configuracion del sensor...")

    timestamp_now = int(time.time() * 1000)  # Milisegundos

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

    print("[OK] Sensor configurado")
    print(f"    Owner PKH: {builder.wallet_pkh.hex()[:16]}...")

    # 6. Usar HybridTransactionBuilder para enviar TX
    print("\n[+] Usando HybridTransactionBuilder...")

    hybrid_builder = HybridTransactionBuilder()

    # 7. Mostrar resumen
    print("\n" + "="*70)
    print(" RESUMEN DE TRANSACCION")
    print("="*70)
    print()
    print(f"Operacion: RegisterSensor")
    print(f"Sensor ID: {sensor_id}")
    print(f"Ubicacion: {zone_name}")
    print(f"Owner: {builder.wallet_pkh.hex()[:16]}...")
    print()
    print("IMPORTANTE: Esto enviara una transaccion REAL a Preview Testnet")
    print()

    # 8. Enviar transacción usando Lucid (sin confirmación para testing)
    try:
        tx_hash = hybrid_builder.register_sensor(
            sensor=new_sensor,
            owner_pkh=builder.wallet_pkh
        )

        print("\n" + "="*70)
        print(" SENSOR REGISTRADO EXITOSAMENTE!")
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
        print("  - Sensores registrados: 1")
        print("  - Sensor #1: SENSOR_001")
        print("  - Estado: Active")
        print()

    except Exception as e:
        print(f"\n[ERROR] Error registrando sensor: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
