# -*- coding: utf-8 -*-
"""
Script para registrar un nuevo sensor en el contrato
Usa PyCardano para construir la transacción
"""

import time
import sys
from transaction_builder import SensorTransactionBuilder
from contract_types import create_sensor_config
import config


def main():
    print("="*70)
    print(" REGISTRAR NUEVO SENSOR - Sistema de Sensores de Humedad")
    print("="*70)
    print()

    # Configuración del sensor a registrar
    sensor_id = "SENSOR_002"
    latitude = -34.6  # Buenos Aires, Argentina
    longitude = -58.47
    zone_name = "Test Zone"
    min_humidity = 30
    max_humidity = 70
    reading_interval = 60  # minutos

    print("[+] Configuracion del sensor:")
    print(f"    ID: {sensor_id}")
    print(f"    Ubicacion: {zone_name}")
    print(f"    Coordenadas: {latitude}, {longitude}")
    print(f"    Umbral humedad: {min_humidity}% - {max_humidity}%")
    print(f"    Intervalo lecturas: {reading_interval} minutos")
    print()

    try:
        # Inicializar transaction builder
        builder = SensorTransactionBuilder()

        # Crear configuración del sensor
        timestamp_now = int(time.time() * 1000)

        sensor_config = create_sensor_config(
            sensor_id=sensor_id,
            latitude=latitude,
            longitude=longitude,
            zone_name=zone_name,
            min_humidity=min_humidity,
            max_humidity=max_humidity,
            reading_interval=reading_interval,
            owner_pkh=builder.payment_pkh,
            installed_timestamp=timestamp_now
        )

        print(f"[+] Sensor config creado:")
        print(f"    Owner PKH: {builder.payment_pkh.hex()}")
        print(f"    Installed: {sensor_config.installed_date}")

        # Confirmar antes de enviar
        print(f"\n[?] Enviar transaccion para registrar {sensor_id}? (y/n): ", end="")
        if len(sys.argv) > 1 and sys.argv[1] == "--yes":
            response = "y"
            print("y (auto)")
        else:
            response = input().lower()

        if response != 'y':
            print("\n[!] Cancelado por el usuario")
            return

        # Construir y enviar transacción
        tx_hash = builder.build_register_sensor_tx(sensor_config)

        print(f"\n" + "="*70)
        print(f" SENSOR REGISTRADO EXITOSAMENTE!")
        print(f"="*70)
        print(f"\nTxHash: {tx_hash}")
        print(f"\nMonitorea la transaccion en:")
        print(f"https://preview.cardanoscan.io/transaction/{tx_hash}")
        print(f"\nEspera ~20 segundos para confirmacion en blockchain.")
        print(f"\nVerifica el estado con: python query.py")

    except Exception as e:
        print(f"\n[ERROR] Error registrando sensor: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
