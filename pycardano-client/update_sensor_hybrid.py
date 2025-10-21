# -*- coding: utf-8 -*-
"""
Script principal para actualizar configuración de sensores
usando el approach híbrido Python + Lucid

Este script permite actualizar:
- Umbrales de humedad (min/max)
- Intervalo de lectura
- Ubicación (coordenadas + zona)
- Estado del sensor (Active/Inactive/Maintenance/Error)

Uso:
    python update_sensor_hybrid.py
"""

import subprocess
import json
import sys
from pathlib import Path
from pycardano_tx import CardanoTransactionBuilder


class HybridTransactionBuilder:
    """
    Orquesta el flujo híbrido Python + Lucid para UpdateSensorConfig

    Flujo:
    1. Python serializa el datum actualizado y redeemer → CBOR hex
    2. Lucid recibe CBOR hex y construye/firma/envía transacción
    """

    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.serialize_script = Path(__file__).parent / "serialize_update.py"
        self.lucid_script = self.project_root / "mesh-client" / "update-sensor-lucid.js"

    def update_sensor(
        self,
        sensor_id: str,
        new_min_humidity: int = None,
        new_max_humidity: int = None,
        new_reading_interval: int = None,
        new_latitude: float = None,
        new_longitude: float = None,
        new_zone_name: str = None,
        new_status: str = None
    ) -> str:
        """
        Actualiza la configuración de un sensor

        Args:
            sensor_id: ID del sensor a actualizar
            new_min_humidity: Nuevo umbral mínimo (opcional)
            new_max_humidity: Nuevo umbral máximo (opcional)
            new_reading_interval: Nuevo intervalo en minutos (opcional)
            new_latitude: Nueva latitud (opcional)
            new_longitude: Nueva longitud (opcional)
            new_zone_name: Nuevo nombre de zona (opcional)
            new_status: Nuevo estado (opcional)

        Returns:
            Transaction hash
        """

        print("======================================================================")
        print(" ACTUALIZAR SENSOR - Approach Híbrido Python + Lucid")
        print("======================================================================")
        print()

        # 1. Construir comando para serialize_update.py
        cmd = ["python", str(self.serialize_script), sensor_id]

        if new_min_humidity is not None:
            cmd.extend(["--min-humidity", str(new_min_humidity)])

        if new_max_humidity is not None:
            cmd.extend(["--max-humidity", str(new_max_humidity)])

        if new_reading_interval is not None:
            cmd.extend(["--interval", str(new_reading_interval)])

        if new_latitude is not None:
            cmd.extend(["--latitude", str(new_latitude)])

        if new_longitude is not None:
            cmd.extend(["--longitude", str(new_longitude)])

        if new_zone_name is not None:
            cmd.extend(["--zone-name", new_zone_name])

        if new_status is not None:
            cmd.extend(["--status", new_status])

        # 2. Ejecutar serialización con Python
        print("[+] Serializando datum actualizado y redeemer con PyCardano...")
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
                print("[ERROR] No se encontró JSON en el output de serialize_update.py")
                print("Output completo:")
                print(result.stdout)
                sys.exit(1)

            # Extraer el JSON completo (desde { hasta el final o hasta el siguiente line break vacío)
            json_output = output[json_start:]

            # Si hay contenido después del JSON, intentar limpiarlo
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
            changes = serialized_data.get("changes", {})

            print("[OK] Serialization exitosa:")
            print(f"    Datum CBOR length: {len(datum_cbor_hex)} chars")
            print(f"    Redeemer CBOR length: {len(redeemer_cbor_hex)} chars")
            print()

            # Mostrar cambios
            if changes:
                print("[+] Cambios detectados:")
                for field, change in changes.items():
                    if change["old"] != change["new"]:
                        print(f"    {field}: {change['old']} -> {change['new']}")
                print()

        except subprocess.CalledProcessError as e:
            print(f"[ERROR] Fallo en serialización:")
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
                print("[ERROR] No se encontró JSON de resultado")
                print("Output completo:")
                print(result.stdout)
                sys.exit(1)

            tx_result = json.loads(json_result)

            if not tx_result.get("success"):
                print(f"[ERROR] Transacción falló: {tx_result.get('error')}")
                sys.exit(1)

            tx_hash = tx_result["txHash"]
            explorer_url = tx_result["explorerUrl"]

            print("[OK] Transacción construida y enviada")
            print()

            # 4. Mostrar resumen
            print("======================================================================")
            print(" RESUMEN DE ACTUALIZACION")
            print("======================================================================")
            print()
            print(f"Operacion: UpdateSensorConfig")
            print(f"Sensor ID: {sensor_id}")
            print()

            if changes:
                print("Cambios aplicados:")
                for field, change in changes.items():
                    if change["old"] != change["new"]:
                        print(f"  - {field}: {change['old']} -> {change['new']}")
                print()

            print()
            print("======================================================================")
            print(" SENSOR ACTUALIZADO EXITOSAMENTE!")
            print("======================================================================")
            print()
            print(f"TxHash: {tx_hash}")
            print()
            print("Explorer:")
            print(f"  {explorer_url}")
            print()
            print("======================================================================")
            print()
            print("Espera 1-2 minutos para confirmacion en blockchain")
            print()
            print("Luego ejecuta:")
            print(f"  python decode_datum_enhanced.py --sensor {sensor_id}")
            print()
            print("Deberias ver:")
            print(f"  - Sensor {sensor_id} con nueva configuracion")

            if new_min_humidity is not None or new_max_humidity is not None:
                min_val = new_min_humidity if new_min_humidity is not None else "sin cambios"
                max_val = new_max_humidity if new_max_humidity is not None else "sin cambios"
                print(f"  - Umbrales: {min_val}% - {max_val}%")

            if new_reading_interval is not None:
                print(f"  - Intervalo: {new_reading_interval} minutos")

            if new_status is not None:
                print(f"  - Estado: {new_status}")

            print()

            return tx_hash

        except subprocess.CalledProcessError as e:
            print(f"[ERROR] Fallo en construcción de transacción con Lucid:")
            print(e.stderr)
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"[ERROR] No se pudo parsear resultado JSON:")
            print(f"    {e}")
            sys.exit(1)


def main():
    """
    Script principal para actualizar sensor

    IMPORTANTE:
    - Modifica las variables abajo según el sensor que quieras actualizar
    - Solo especifica los campos que quieras cambiar
    - Los campos no especificados mantendrán su valor anterior
    """

    print()
    print("[+] Inicializando CardanoTransactionBuilder...")

    # Inicializar para validar wallet
    builder = CardanoTransactionBuilder()
    print(f"[OK] Wallet inicializado")
    print(f"    Address: {builder.wallet_address}")
    print()

    # ===================================================================
    # CONFIGURACIÓN - EDITA ESTOS VALORES
    # ===================================================================

    # ID del sensor a actualizar (REQUERIDO)
    sensor_id = "SENSOR_001"

    # Nuevos umbrales de humedad (opcional - solo cambia los que necesites)
    new_min_humidity = 25  # Cambiar de 30% a 25%
    new_max_humidity = 75  # Cambiar de 70% a 75%

    # Nuevo intervalo de lectura (opcional)
    new_reading_interval = 120  # Cambiar a 120 minutos (2 horas)

    # Nueva ubicación (opcional - debes especificar los 3 valores juntos o ninguno)
    new_latitude = None  # -34.58
    new_longitude = None  # -58.45
    new_zone_name = None  # "Campo Norte - Parcela A (Actualizada)"

    # Nuevo estado (opcional)
    # Valores posibles: "Active", "Inactive", "Maintenance", "Error"
    new_status = None  # "Maintenance"

    # ===================================================================

    print("[+] Configuracion de actualizacion:")
    print()
    print(f"    Sensor ID: {sensor_id}")
    print()

    if new_min_humidity is not None:
        print(f"    Nuevo umbral minimo: {new_min_humidity}%")

    if new_max_humidity is not None:
        print(f"    Nuevo umbral maximo: {new_max_humidity}%")

    if new_reading_interval is not None:
        print(f"    Nuevo intervalo: {new_reading_interval} minutos")

    if new_latitude is not None and new_longitude is not None and new_zone_name is not None:
        print(f"    Nueva ubicacion:")
        print(f"      Latitud: {new_latitude}")
        print(f"      Longitud: {new_longitude}")
        print(f"      Zona: {new_zone_name}")

    if new_status is not None:
        print(f"    Nuevo estado: {new_status}")

    print()

    # Verificar que al menos un campo se va a actualizar
    if all(v is None for v in [
        new_min_humidity,
        new_max_humidity,
        new_reading_interval,
        new_latitude,
        new_status
    ]):
        print("[ERROR] Debes especificar al menos un campo para actualizar")
        print()
        print("Edita las variables en update_sensor_hybrid.py:")
        print("  - new_min_humidity")
        print("  - new_max_humidity")
        print("  - new_reading_interval")
        print("  - new_latitude/longitude/zone_name")
        print("  - new_status")
        sys.exit(1)

    print("[+] Verificando estado del contrato...")
    contract_utxo = builder.get_contract_utxo_with_datum()
    current_datum = builder.decode_datum(contract_utxo.output.datum)

    print()
    print("[OK] Estado actual del contrato:")
    print(f"    Sensores registrados: {len(current_datum.sensors)}")
    print(f"    Total sensores: {current_datum.total_sensors}")
    print()

    # Confirmar antes de enviar
    print("IMPORTANTE: Esto enviara una transaccion REAL a Preview Testnet")
    print()

    # Para uso en scripts automatizados, comenta esta linea:
    # input("Presiona Enter para continuar o Ctrl+C para cancelar...")
    # print()

    # Usar HybridTransactionBuilder
    print("[+] Usando HybridTransactionBuilder...")
    print()

    hybrid_builder = HybridTransactionBuilder()

    try:
        tx_hash = hybrid_builder.update_sensor(
            sensor_id=sensor_id,
            new_min_humidity=new_min_humidity,
            new_max_humidity=new_max_humidity,
            new_reading_interval=new_reading_interval,
            new_latitude=new_latitude,
            new_longitude=new_longitude,
            new_zone_name=new_zone_name,
            new_status=new_status
        )

        print(f"[SUCCESS] Sensor actualizado: {tx_hash}")

    except Exception as e:
        print()
        print(f"[ERROR] Fallo al actualizar sensor: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
