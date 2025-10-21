# -*- coding: utf-8 -*-
"""
Script temporal para verificar sensores registrados en el datum
"""

from transaction_builder import SensorTransactionBuilder

builder = SensorTransactionBuilder()
utxo = builder.get_datum_utxo()
datum = builder.decode_datum(utxo)

print(f"\n{'='*70}")
print(f" SENSORES REGISTRADOS EN EL DATUM")
print(f"{'='*70}\n")

print(f"Total de sensores: {datum.total_sensors}")
print(f"Sensores en lista: {len(datum.sensors)}")
print(f"Lecturas totales: {len(datum.recent_readings)}\n")

for i, sensor in enumerate(datum.sensors, 1):
    status_type = type(sensor.status).__name__
    print(f"{i}. {sensor.sensor_id.decode('utf-8')}")
    print(f"   Status: {status_type}")
    print(f"   Owner PKH: {sensor.owner.hex()}")
    print(f"   Ubicación: {sensor.location.zone_name.decode('utf-8')}")
    print()
