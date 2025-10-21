# -*- coding: utf-8 -*-
"""
Script para decodificar y mostrar el datum del contrato
"""

import config
import cardano_utils as cu
from pycardano import PlutusData, RawCBOR
from typing import List
import cbor2

# Definir la estructura del datum (debe coincidir con OpShin)
class SensorConfig(PlutusData):
    CONSTR_ID = 0
    sensor_id: bytes
    location: bytes
    min_humidity: int
    max_humidity: int
    is_active: bool

class HumidityReading(PlutusData):
    CONSTR_ID = 0
    sensor_id: bytes
    humidity: int
    temperature: int
    timestamp: int
    reporter: bytes

class HumiditySensorDatum(PlutusData):
    CONSTR_ID = 0
    sensors: List[SensorConfig]
    recent_readings: List[HumidityReading]
    admin: bytes
    last_updated: int
    total_sensors: int

def main():
    print("="*70)
    print(" DECODIFICADOR DE DATUM - Sistema de Sensores de Humedad")
    print("="*70)
    print()

    try:
        # 1. Obtener UTxOs
        print("[+] Consultando UTxOs del contrato...")
        utxos = cu.get_contract_utxos()

        # 2. Buscar el UTxO con datum
        datum_utxo = None
        for i, utxo in enumerate(utxos, 1):
            if hasattr(utxo, 'inline_datum') and utxo.inline_datum:
                datum_utxo = utxo
                print(f"[+] Encontrado UTxO #{i} con datum inline")
                print(f"    TxHash: {utxo.tx_hash[:16]}...")
                print(f"    Amount: {int(utxo.amount[0].quantity) / 1_000_000:.2f} ADA")
                break

        if not datum_utxo:
            print("[!] No se encontro ningun UTxO con datum")
            return

        # 3. Decodificar datum
        print()
        print("[+] Decodificando datum CBOR...")

        datum_cbor = datum_utxo.inline_datum
        print(f"    CBOR hex: {datum_cbor[:64]}...")
        print()

        # Intentar decodificar como PlutusData generico
        try:
            datum_bytes = bytes.fromhex(datum_cbor)

            # Decodificar CBOR
            decoded_cbor = cbor2.loads(datum_bytes)

            print("[+] Datum decodificado (estructura raw CBOR):")
            print(f"    {decoded_cbor}")
            print()

            # Intentar parsear como HumiditySensorDatum
            try:
                typed_datum = HumiditySensorDatum.from_primitive(decoded_cbor)

                print("="*70)
                print(" CONTENIDO DEL DATUM")
                print("="*70)
                print()
                print(f"[+] Sensores registrados: {len(typed_datum.sensors)}")
                print(f"[+] Lecturas recientes: {len(typed_datum.recent_readings)}")
                print(f"[+] Admin: {typed_datum.admin.hex()}")
                print(f"[+] Ultima actualizacion: {typed_datum.last_updated}")
                print(f"[+] Total de sensores: {typed_datum.total_sensors}")
                print()

                if typed_datum.sensors:
                    print("[+] Detalles de sensores:")
                    for i, sensor in enumerate(typed_datum.sensors, 1):
                        print(f"    Sensor #{i}:")
                        print(f"      ID: {sensor.sensor_id.hex()}")
                        print(f"      Ubicacion: {sensor.location.decode('utf-8', errors='ignore')}")
                        print(f"      Humedad min/max: {sensor.min_humidity}% / {sensor.max_humidity}%")
                        print(f"      Activo: {sensor.is_active}")
                        print()

                if typed_datum.recent_readings:
                    print("[+] Lecturas recientes:")
                    for i, reading in enumerate(typed_datum.recent_readings, 1):
                        print(f"    Lectura #{i}:")
                        print(f"      Sensor ID: {reading.sensor_id.hex()}")
                        print(f"      Humedad: {reading.humidity}%")
                        print(f"      Temperatura: {reading.temperature}C")
                        print(f"      Timestamp: {reading.timestamp}")
                        print()

                print("="*70)

            except Exception as e:
                print(f"[WARN] No se pudo parsear como HumiditySensorDatum: {e}")
                print("[+] Mostrando estructura raw del datum:")
                print()
                print(decoded_cbor)

        except Exception as e:
            print(f"[ERROR] Error decodificando CBOR: {e}")
            import traceback
            traceback.print_exc()

    except Exception as e:
        print(f"\n[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
