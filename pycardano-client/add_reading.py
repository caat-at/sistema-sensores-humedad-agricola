# -*- coding: utf-8 -*-
"""
Agregar una lectura de sensor al contrato
"""

import time
import sys
import argparse
from transaction_builder import SensorTransactionBuilder
from contract_types import create_humidity_reading
import config


def add_reading_example(sensor_id=None, humidity=None, temperature=None, auto_confirm=False):
    """
    Agregar una lectura de ejemplo a un sensor existente
    """
    print("\n" + "="*70)
    print(" AGREGAR LECTURA - Sistema de Sensores de Humedad")
    print("="*70)

    # Configuración de la lectura (usar parámetros o valores por defecto)
    SENSOR_ID = sensor_id or "SENSOR_001"
    HUMIDITY = int(humidity) if humidity is not None else 55  # Porcentaje (convertir a int)
    TEMPERATURE = int(temperature) if temperature is not None else 24  # Celsius (convertir a int)

    print(f"\n[+] Configuración de la lectura:")
    print(f"    Sensor ID: {SENSOR_ID}")
    print(f"    Humedad: {HUMIDITY}%")
    print(f"    Temperatura: {TEMPERATURE}°C")
    print(f"    Umbrales automáticos: Critical (<20% o >85%), Low (<40%), High (>70%), Normal (40-70%)")

    try:
        # Inicializar transaction builder
        builder = SensorTransactionBuilder()

        # Timestamp actual
        timestamp_now = int(time.time() * 1000)

        # Crear lectura con alerta automática
        # La función calculate_alert_level usa estos umbrales:
        # Critical: <20% o >85%
        # Low: <40%
        # High: >70%
        # Normal: 40-70%
        reading = create_humidity_reading(
            sensor_id=SENSOR_ID,
            humidity=HUMIDITY,
            temperature=TEMPERATURE,
            timestamp=timestamp_now
        )

        # Determinar estado de alerta
        if HUMIDITY < 20 or HUMIDITY > 85:
            alert_status = "Critical"
        elif HUMIDITY < 40:
            alert_status = "Low (Humedad Baja)"
        elif HUMIDITY > 70:
            alert_status = "High (Humedad Alta)"
        else:
            alert_status = "Normal"

        print(f"\n[+] Lectura creada:")
        print(f"    Timestamp: {timestamp_now}")
        print(f"    Estado: {alert_status}")

        # Confirmar antes de enviar
        print(f"\n[?] Enviar transacción para agregar lectura? (y/n): ", end="")
        if auto_confirm:
            response = "y"
            print("y (auto)")
        else:
            response = input().lower()

        if response != 'y':
            print("\n[!] Cancelado por el usuario")
            return

        # Construir y enviar transacción
        tx_hash = builder.build_add_reading_tx(reading)

        print(f"\n" + "="*70)
        print(f" LECTURA AGREGADA EXITOSAMENTE!")
        print(f"="*70)
        print(f"\nTxHash: {tx_hash}")
        print(f"\nMonitorea la transacción en:")
        print(f"https://preview.cardanoscan.io/transaction/{tx_hash}")
        print(f"\nEspera ~20 segundos para confirmación en blockchain.")
        print(f"\nVerifica el estado con: python decode_datum.py")

    except Exception as e:
        print(f"\n[ERROR] Error agregando lectura: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Agregar lectura de sensor')
    parser.add_argument('--sensor-id', type=str, help='ID del sensor (ej: SENSOR_001)')
    parser.add_argument('--humidity', type=float, help='Humedad en porcentaje (0-100)')
    parser.add_argument('--temperature', type=float, help='Temperatura en Celsius')
    parser.add_argument('--yes', action='store_true', help='Confirmar automáticamente')

    args = parser.parse_args()

    add_reading_example(
        sensor_id=args.sensor_id,
        humidity=args.humidity,
        temperature=args.temperature,
        auto_confirm=args.yes
    )
