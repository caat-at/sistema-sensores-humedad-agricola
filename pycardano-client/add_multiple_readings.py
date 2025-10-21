# -*- coding: utf-8 -*-
"""
Script para agregar múltiples lecturas de prueba
Simula diferentes condiciones y niveles de alerta
"""

import time
from pycardano_tx import CardanoTransactionBuilder
from tx_builder_hybrid import HybridTransactionBuilder


# Lecturas de prueba que cubren todos los niveles de alerta
READINGS = [
    {
        "sensor_id": "SENSOR_002",
        "humidity": 35,
        "temperature": 28,
        "description": "Humedad BAJA - Necesita riego",
        "expected_alert": "Low"
    },
    {
        "sensor_id": "SENSOR_003",
        "humidity": 75,
        "temperature": 18,
        "description": "Humedad ALTA - Riesgo de hongos",
        "expected_alert": "High"
    },
    {
        "sensor_id": "SENSOR_001",
        "humidity": 15,
        "temperature": 32,
        "description": "Humedad CRÍTICA - Sequía extrema",
        "expected_alert": "Critical"
    },
    {
        "sensor_id": "SENSOR_002",
        "humidity": 55,
        "temperature": 22,
        "description": "Humedad NORMAL - Condiciones óptimas",
        "expected_alert": "Normal"
    },
    {
        "sensor_id": "SENSOR_003",
        "humidity": 88,
        "temperature": 16,
        "description": "Humedad CRÍTICA - Exceso de agua",
        "expected_alert": "Critical"
    }
]


def main():
    print("="*70)
    print(" AGREGAR MÚLTIPLES LECTURAS - Sistema de Prueba")
    print("="*70)

    # 1. Inicializar builders
    print("\n[+] Inicializando builders...")
    builder = CardanoTransactionBuilder()
    hybrid_builder = HybridTransactionBuilder()

    # 2. Verificar estado inicial
    print("\n[+] Estado inicial del contrato:")
    contract_utxo = builder.get_contract_utxo_with_datum()
    current_datum = builder.decode_datum(contract_utxo.output.datum)

    print(f"    Sensores: {len(current_datum.sensors)}")
    print(f"    Lecturas actuales: {len(current_datum.recent_readings)}")

    # 3. Procesar cada lectura
    results = []

    for i, reading in enumerate(READINGS, 1):
        print("\n" + "="*70)
        print(f" LECTURA {i}/{len(READINGS)}")
        print("="*70)
        print(f"\n[+] Datos:")
        print(f"    Sensor: {reading['sensor_id']}")
        print(f"    Humedad: {reading['humidity']}%")
        print(f"    Temperatura: {reading['temperature']}C")
        print(f"    Descripcion: {reading['description']}")
        print(f"    Alerta esperada: {reading['expected_alert']}")

        try:
            # Agregar lectura
            tx_hash = hybrid_builder.add_reading(
                sensor_id=reading['sensor_id'],
                humidity=reading['humidity'],
                temperature=reading['temperature']
            )

            result = {
                "success": True,
                "sensor_id": reading['sensor_id'],
                "humidity": reading['humidity'],
                "temperature": reading['temperature'],
                "tx_hash": tx_hash,
                "description": reading['description']
            }
            results.append(result)

            print(f"\n[OK] Lectura {i} registrada exitosamente!")
            print(f"    TxHash: {tx_hash}")

            # Esperar un poco entre transacciones
            if i < len(READINGS):
                print(f"\n[+] Esperando 30 segundos antes de la siguiente transaccion...")
                time.sleep(30)

        except Exception as e:
            print(f"\n[ERROR] Error en lectura {i}: {e}")
            result = {
                "success": False,
                "sensor_id": reading['sensor_id'],
                "error": str(e)
            }
            results.append(result)

            # Continuar con la siguiente lectura
            continue

    # 4. Resumen final
    print("\n" + "="*70)
    print(" RESUMEN FINAL")
    print("="*70)

    successful = [r for r in results if r.get("success")]
    failed = [r for r in results if not r.get("success")]

    print(f"\n[OK] Lecturas exitosas: {len(successful)}/{len(READINGS)}")
    print(f"[ERROR] Lecturas fallidas: {len(failed)}/{len(READINGS)}")

    if successful:
        print("\n[+] Lecturas registradas:")
        for i, r in enumerate(successful, 1):
            print(f"\n{i}. {r['sensor_id']}: {r['humidity']}% humedad, {r['temperature']}C")
            print(f"   Descripcion: {r['description']}")
            print(f"   TxHash: {r['tx_hash'][:16]}...")
            print(f"   Explorer: https://preview.cardanoscan.io/transaction/{r['tx_hash']}")

    if failed:
        print("\n[ERROR] Lecturas fallidas:")
        for i, r in enumerate(failed, 1):
            print(f"\n{i}. {r['sensor_id']}: {r['error']}")

    print("\n" + "="*70)
    print(" INSTRUCCIONES FINALES")
    print("="*70)
    print("\nEspera 2-3 minutos para que todas las transacciones se confirmen.")
    print("\nLuego ejecuta:")
    print("  python decode_datum.py")
    print("\nDeberías ver:")
    print(f"  - Lecturas registradas: {len(current_datum.recent_readings) + len(successful)}")
    print("  - Alertas: Normal, Low, High, Critical")
    print()


if __name__ == "__main__":
    main()
