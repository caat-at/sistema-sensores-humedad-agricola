# -*- coding: utf-8 -*-
"""
Script principal para desactivar sensores
usando el approach híbrido Python + Lucid

Este script cambia el estado de un sensor a Inactive,
lo que previene que se puedan agregar nuevas lecturas.

Uso:
    python deactivate_sensor_hybrid.py
"""

import subprocess
import json
import sys
from pathlib import Path
from pycardano_tx import CardanoTransactionBuilder


class HybridTransactionBuilder:
    """
    Orquesta el flujo híbrido Python + Lucid para DeactivateSensor

    Flujo:
    1. Python serializa el datum con sensor desactivado y redeemer -> CBOR hex
    2. Lucid recibe CBOR hex y construye/firma/envía transacción
    """

    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.serialize_script = Path(__file__).parent / "serialize_deactivate.py"
        self.lucid_script = self.project_root / "mesh-client" / "deactivate-sensor-lucid.js"

    def deactivate_sensor(self, sensor_id: str) -> str:
        """
        Desactiva un sensor (cambia estado a Inactive)

        Args:
            sensor_id: ID del sensor a desactivar

        Returns:
            Transaction hash
        """

        print("======================================================================")
        print(" DESACTIVAR SENSOR - Approach Hibrido Python + Lucid")
        print("======================================================================")
        print()

        # 1. Construir comando para serialize_deactivate.py
        cmd = ["python", str(self.serialize_script), sensor_id]

        # 2. Ejecutar serialización con Python
        print("[+] Serializando datum con sensor desactivado y redeemer con PyCardano...")
        print()

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )

            # Buscar el JSON en el output (puede estar en múltiples líneas)
            output = result.stdout.strip()

            # Encontrar donde empieza el JSON
            json_start = output.find('{')
            if json_start == -1:
                print("[ERROR] No se encontro JSON en el output de serialize_deactivate.py")
                print("Output completo:")
                print(result.stdout)
                sys.exit(1)

            # Extraer el JSON completo
            json_output = output[json_start:]

            # Buscar el último } que cierre el JSON principal
            brace_count = 0
            json_end = -1
            for i, char in enumerate(json_output):
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        json_end = i + 1
                        break

            if json_end > 0:
                json_output = json_output[:json_end]

            serialized_data = json.loads(json_output)
            datum_cbor_hex = serialized_data["datum_cbor_hex"]
            redeemer_cbor_hex = serialized_data["redeemer_cbor_hex"]
            old_status = serialized_data.get("old_status", "Unknown")
            new_status = serialized_data.get("new_status", "Inactive")

            print("[OK] Serialization exitosa:")
            print(f"    Datum CBOR length: {len(datum_cbor_hex)} chars")
            print(f"    Redeemer CBOR length: {len(redeemer_cbor_hex)} chars")
            print(f"    Estado: {old_status} -> {new_status}")
            print()

        except subprocess.CalledProcessError as e:
            print(f"[ERROR] Fallo en serializacion:")
            print(e.stderr)
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"[ERROR] No se pudo parsear JSON:")
            print(f"    {e}")
            print(f"Output: {result.stdout}")
            sys.exit(1)

        # 3. Construir transacción con Lucid
        print("[+] Construyendo transaccion con Lucid...")
        print()

        try:
            result = subprocess.run(
                ["node", str(self.lucid_script), datum_cbor_hex, redeemer_cbor_hex],
                capture_output=True,
                text=True,
                check=True,
                cwd=str(self.lucid_script.parent)
            )

            # Buscar el JSON con el resultado en el output
            output_lines = result.stdout.strip().split('\n')
            json_result = None

            for line in output_lines:
                if line.strip().startswith('{') and 'success' in line:
                    json_result = line.strip()
                    break

            if not json_result:
                print("[ERROR] No se encontro JSON de resultado")
                print("Output completo:")
                print(result.stdout)
                sys.exit(1)

            tx_result = json.loads(json_result)

            if not tx_result.get("success"):
                print(f"[ERROR] Transaccion fallo: {tx_result.get('error')}")
                sys.exit(1)

            tx_hash = tx_result["txHash"]
            explorer_url = tx_result["explorerUrl"]

            print("[OK] Transaccion construida y enviada")
            print()

            # 4. Mostrar resumen
            print("======================================================================")
            print(" RESUMEN DE DESACTIVACION")
            print("======================================================================")
            print()
            print(f"Operacion: DeactivateSensor")
            print(f"Sensor ID: {sensor_id}")
            print(f"Estado: {old_status} -> Inactive")
            print()
            print()
            print("======================================================================")
            print(" SENSOR DESACTIVADO EXITOSAMENTE!")
            print("======================================================================")
            print()
            print(f"TxHash: {tx_hash}")
            print()
            print("Explorer:")
            print(f"  {explorer_url}")
            print()
            print("======================================================================")
            print()
            print("IMPORTANTE: Un sensor desactivado NO puede recibir nuevas lecturas.")
            print()
            print("Espera 1-2 minutos para confirmacion en blockchain")
            print()
            print("Luego ejecuta:")
            print(f"  python decode_datum_enhanced.py --sensor {sensor_id}")
            print()
            print("Deberias ver:")
            print(f"  - Sensor {sensor_id} con Estado: Inactive")
            print()

            return tx_hash

        except subprocess.CalledProcessError as e:
            print(f"[ERROR] Fallo en construccion de transaccion con Lucid:")
            print(e.stderr)
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"[ERROR] No se pudo parsear resultado JSON:")
            print(f"    {e}")
            sys.exit(1)


def main():
    """
    Script principal para desactivar sensor

    IMPORTANTE:
    - Modifica la variable sensor_id abajo con el sensor que quieras desactivar
    - El sensor debe existir y no estar ya desactivado
    - Un sensor desactivado NO puede recibir nuevas lecturas
    """

    print()
    print("[+] Inicializando CardanoTransactionBuilder...")

    # Inicializar para validar wallet
    builder = CardanoTransactionBuilder()
    print(f"[OK] Wallet inicializado")
    print(f"    Address: {builder.wallet_address}")
    print()

    # ===================================================================
    # CONFIGURACIÓN - EDITA ESTE VALOR
    # ===================================================================

    # ID del sensor a desactivar (REQUERIDO)
    sensor_id = "SENSOR_002"

    # ===================================================================

    print("[+] Configuracion de desactivacion:")
    print()
    print(f"    Sensor ID: {sensor_id}")
    print()

    print("[+] Verificando estado del contrato...")
    contract_utxo = builder.get_contract_utxo_with_datum()
    current_datum = builder.decode_datum(contract_utxo.output.datum)

    print()
    print("[OK] Estado actual del contrato:")
    print(f"    Sensores registrados: {len(current_datum.sensors)}")
    print(f"    Total sensores: {current_datum.total_sensors}")
    print()

    # Verificar que el sensor existe
    sensor_exists = False
    for sensor in current_datum.sensors:
        if sensor.sensor_id.decode('utf-8', errors='ignore') == sensor_id:
            sensor_exists = True
            # Mostrar estado actual del sensor
            zone_name = sensor.location.zone_name.decode('utf-8', errors='ignore')
            status_name = type(sensor.status).__name__

            print(f"[+] Sensor encontrado:")
            print(f"    ID: {sensor_id}")
            print(f"    Ubicacion: {zone_name}")
            print(f"    Estado actual: {status_name}")
            print()

            # Advertir si ya está inactivo
            if status_name == "Inactive":
                print("[WARNING] El sensor ya esta desactivado (estado: Inactive)")
                print()
                response = input("¿Deseas continuar de todos modos? (y/n): ")
                if response.lower() != 'y':
                    print("Operacion cancelada")
                    sys.exit(0)
            break

    if not sensor_exists:
        print(f"[ERROR] Sensor '{sensor_id}' no encontrado en el contrato")
        print()
        print("Sensores disponibles:")
        for sensor in current_datum.sensors:
            sid = sensor.sensor_id.decode('utf-8', errors='ignore')
            status = type(sensor.status).__name__
            print(f"  - {sid} (Estado: {status})")
        sys.exit(1)

    # Confirmar antes de enviar
    print("IMPORTANTE: Esto enviara una transaccion REAL a Preview Testnet")
    print("           Un sensor desactivado NO puede recibir nuevas lecturas")
    print()

    # Para uso en scripts automatizados, comenta esta linea:
    # input("Presiona Enter para continuar o Ctrl+C para cancelar...")
    # print()

    # Usar HybridTransactionBuilder
    print("[+] Usando HybridTransactionBuilder...")
    print()

    hybrid_builder = HybridTransactionBuilder()

    try:
        tx_hash = hybrid_builder.deactivate_sensor(sensor_id=sensor_id)

        print(f"[SUCCESS] Sensor desactivado: {tx_hash}")

    except Exception as e:
        print()
        print(f"[ERROR] Fallo al desactivar sensor: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
