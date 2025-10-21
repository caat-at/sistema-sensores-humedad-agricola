# -*- coding: utf-8 -*-
"""
Transaction Builder Híbrido - Python + Lucid
Usa Python para lógica de negocio y Lucid para construcción de TX
"""

import json
import subprocess
from pathlib import Path
from typing import Dict, Any
from contract_types import SensorConfig


class HybridTransactionBuilder:
    """
    Constructor de transacciones híbrido que usa Lucid-Cardano
    Python maneja la lógica de negocio, Lucid construye las TX
    """

    def __init__(self):
        """Inicializar builder híbrido"""
        self.lucid_scripts_dir = Path(__file__).parent.parent / "mesh-client"
        print("[+] HybridTransactionBuilder inicializado")
        print(f"    Lucid scripts: {self.lucid_scripts_dir}")

    def sensor_config_to_json(self, sensor: SensorConfig, owner_pkh: bytes) -> Dict[str, Any]:
        """
        Convertir SensorConfig a formato JSON para Lucid

        Args:
            sensor: Configuración del sensor
            owner_pkh: Public key hash del owner

        Returns:
            Dict con la configuración en formato JSON-serializable
        """
        return {
            "sensor_id": sensor.sensor_id.hex(),
            "location": {
                "latitude": sensor.location.latitude,
                "longitude": sensor.location.longitude,
                "zone_name": sensor.location.zone_name.hex()
            },
            "min_humidity_threshold": sensor.min_humidity_threshold,
            "max_humidity_threshold": sensor.max_humidity_threshold,
            "reading_interval_minutes": sensor.reading_interval_minutes,
            "owner": owner_pkh.hex(),
            "installed_date": sensor.installed_date
        }

    def register_sensor(self, sensor: SensorConfig, owner_pkh: bytes) -> str:
        """
        Registrar sensor usando Lucid-Cardano + PyCardano

        Strategy:
        - PyCardano serializa datum y redeemer a CBOR hex (funciona perfecto)
        - Lucid construye y envía la transacción (funciona perfecto)

        Args:
            sensor: Configuración del sensor a registrar
            owner_pkh: Public key hash del owner

        Returns:
            TxHash de la transacción enviada

        Raises:
            Exception: Si la transacción falla
        """
        print("\n[+] Serializando datum y redeemer con PyCardano...")

        # 1. Llamar al script de serialización Python
        serialize_script = Path(__file__).parent / "serialize_datum_redeemer.py"

        try:
            # Ejecutar script de serialización
            result = subprocess.run(
                ["python", str(serialize_script)],
                capture_output=True,
                text=True,
                timeout=90,
                cwd=str(self.lucid_scripts_dir.parent / "pycardano-client")
            )

            if result.returncode != 0:
                raise Exception(f"Serialization failed: {result.stderr}")

            # Parsear resultado (última línea es JSON)
            output_lines = result.stdout.strip().split('\n')
            json_output = output_lines[-1]
            serialized_data = json.loads(json_output)

            if "error" in serialized_data:
                raise Exception(f"Serialization error: {serialized_data['error']}")

            datum_cbor_hex = serialized_data["datum_cbor_hex"]
            redeemer_cbor_hex = serialized_data["redeemer_cbor_hex"]

            print("[OK] Datum y redeemer serializados")
            print(f"    Datum CBOR length: {len(datum_cbor_hex)} chars")
            print(f"    Redeemer CBOR length: {len(redeemer_cbor_hex)} chars")

        except subprocess.TimeoutExpired:
            raise Exception("Serialization timeout after 90 seconds")
        except json.JSONDecodeError as e:
            raise Exception(f"Failed to parse serialization output: {e}")

        # 2. Llamar al script Lucid con los CBOR hex
        lucid_script = self.lucid_scripts_dir / "register-sensor-lucid-v2.js"

        print(f"\n[+] Construyendo transaccion con Lucid: {lucid_script.name}")

        try:
            result = subprocess.run(
                ["node", str(lucid_script), datum_cbor_hex, redeemer_cbor_hex],
                capture_output=True,
                text=True,
                timeout=120,  # 2 minutos timeout
                cwd=str(self.lucid_scripts_dir)
            )

            # Parsear resultado
            if result.returncode != 0:
                error_data = json.loads(result.stderr) if result.stderr else {"error": "Unknown error"}
                raise Exception(f"Lucid script failed: {error_data.get('error', 'Unknown error')}")

            # La última línea es el JSON de resultado
            output_lines = result.stdout.strip().split('\n')
            json_output = output_lines[-1]
            result_data = json.loads(json_output)

            if not result_data.get("success"):
                raise Exception(f"Transaction failed: {result_data.get('error', 'Unknown error')}")

            tx_hash = result_data["txHash"]
            explorer_url = result_data["explorer"]

            print("[OK] Transaccion enviada exitosamente!")
            print(f"    TxHash: {tx_hash}")
            print(f"    Explorer: {explorer_url}")

            return tx_hash

        except subprocess.TimeoutExpired:
            raise Exception("Lucid script timeout after 2 minutes")
        except json.JSONDecodeError as e:
            print(f"[ERROR] Failed to parse Lucid output: {result.stdout}")
            print(f"[ERROR] Stderr: {result.stderr}")
            raise Exception(f"Failed to parse Lucid script output: {e}")
        except Exception as e:
            raise Exception(f"Failed to execute Lucid script: {e}")

    def add_reading(self, sensor_id: str, humidity: int, temperature: int) -> str:
        """
        Agregar lectura usando Lucid-Cardano + PyCardano

        Strategy:
        - PyCardano serializa datum y redeemer a CBOR hex
        - Lucid construye y envía la transacción

        Args:
            sensor_id: ID del sensor (ej: "SENSOR_001")
            humidity: Porcentaje de humedad (0-100)
            temperature: Temperatura en Celsius

        Returns:
            TxHash de la transacción enviada

        Raises:
            Exception: Si la transacción falla
        """
        print("\n[+] Serializando datum y redeemer para AddReading...")

        # 1. Llamar al script de serialización Python con argumentos
        serialize_script = Path(__file__).parent / "serialize_reading.py"

        try:
            # Ejecutar script de serialización con argumentos
            result = subprocess.run(
                ["python", str(serialize_script), sensor_id, str(humidity), str(temperature)],
                capture_output=True,
                text=True,
                timeout=90,
                cwd=str(self.lucid_scripts_dir.parent / "pycardano-client")
            )

            if result.returncode != 0:
                raise Exception(f"Serialization failed: {result.stderr}")

            # Parsear resultado (última línea es JSON)
            output_lines = result.stdout.strip().split('\n')
            json_output = output_lines[-1]
            serialized_data = json.loads(json_output)

            if "error" in serialized_data:
                raise Exception(f"Serialization error: {serialized_data['error']}")

            datum_cbor_hex = serialized_data["datum_cbor_hex"]
            redeemer_cbor_hex = serialized_data["redeemer_cbor_hex"]

            print("[OK] Datum y redeemer serializados")
            print(f"    Sensor: {serialized_data['sensor_id']}")
            print(f"    Humedad: {serialized_data['humidity']}%")
            print(f"    Temperatura: {serialized_data['temperature']}°C")
            print(f"    Nivel Alerta: {serialized_data['alert_level']}")

        except subprocess.TimeoutExpired:
            raise Exception("Serialization timeout after 90 seconds")
        except json.JSONDecodeError as e:
            raise Exception(f"Failed to parse serialization output: {e}")

        # 2. Llamar al script Lucid con los CBOR hex
        lucid_script = self.lucid_scripts_dir / "add-reading-lucid.js"

        print(f"\n[+] Construyendo transaccion con Lucid: {lucid_script.name}")

        try:
            result = subprocess.run(
                ["node", str(lucid_script), datum_cbor_hex, redeemer_cbor_hex],
                capture_output=True,
                text=True,
                timeout=120,  # 2 minutos timeout
                cwd=str(self.lucid_scripts_dir)
            )

            # Debug: Mostrar stdout y stderr completos
            print(f"[DEBUG] Lucid script returncode: {result.returncode}")
            if result.stdout:
                print(f"[DEBUG] Lucid stdout:\n{result.stdout}")
            if result.stderr:
                print(f"[DEBUG] Lucid stderr:\n{result.stderr}")

            # Parsear resultado
            if result.returncode != 0:
                try:
                    error_data = json.loads(result.stderr) if result.stderr else {"error": "Unknown error"}
                except json.JSONDecodeError:
                    error_data = {"error": result.stderr or "Unknown error"}
                print(f"[ERROR] Lucid script failed with error: {error_data}")
                raise Exception(f"Lucid script failed: {error_data.get('error', 'Unknown error')}")

            # La última línea es el JSON de resultado
            output_lines = result.stdout.strip().split('\n')
            json_output = output_lines[-1]
            result_data = json.loads(json_output)

            if not result_data.get("success"):
                raise Exception(f"Transaction failed: {result_data.get('error', 'Unknown error')}")

            tx_hash = result_data["txHash"]
            explorer_url = result_data["explorer"]

            print("[OK] Transaccion enviada exitosamente!")
            print(f"    TxHash: {tx_hash}")
            print(f"    Explorer: {explorer_url}")

            return tx_hash

        except subprocess.TimeoutExpired:
            raise Exception("Lucid script timeout after 2 minutes")
        except json.JSONDecodeError as e:
            print(f"[ERROR] Failed to parse Lucid output")
            print(f"[ERROR] Stdout: {result.stdout}")
            print(f"[ERROR] Stderr: {result.stderr}")
            raise Exception(f"Failed to parse Lucid script output: {e}")
        except Exception as e:
            raise Exception(f"Failed to execute Lucid script: {e}")

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
        Actualizar configuración de sensor usando Lucid-Cardano + PyCardano

        Strategy:
        - PyCardano serializa datum y redeemer a CBOR hex
        - Lucid construye y envía la transacción

        Args:
            sensor_id: ID del sensor (ej: "SENSOR_001")
            new_min_humidity: Nuevo umbral mínimo de humedad (opcional)
            new_max_humidity: Nuevo umbral máximo de humedad (opcional)
            new_reading_interval: Nuevo intervalo de lectura en minutos (opcional)
            new_latitude: Nueva latitud (opcional)
            new_longitude: Nueva longitud (opcional)
            new_zone_name: Nuevo nombre de zona (opcional)
            new_status: Nuevo estado (Active/Inactive/Maintenance/Error) (opcional)

        Returns:
            TxHash de la transacción enviada

        Raises:
            Exception: Si la transacción falla
        """
        print("\n[+] Serializando datum y redeemer para UpdateSensorConfig...")

        # 1. Construir argumentos para el script de serialización
        serialize_script = Path(__file__).parent / "serialize_update.py"

        args = ["python", str(serialize_script), sensor_id]

        # Agregar argumentos opcionales
        if new_min_humidity is not None:
            args.extend(["--min-humidity", str(new_min_humidity)])
        if new_max_humidity is not None:
            args.extend(["--max-humidity", str(new_max_humidity)])
        if new_reading_interval is not None:
            args.extend(["--reading-interval", str(new_reading_interval)])
        if new_latitude is not None:
            args.extend(["--latitude", str(new_latitude)])
        if new_longitude is not None:
            args.extend(["--longitude", str(new_longitude)])
        if new_zone_name is not None:
            args.extend(["--zone-name", new_zone_name])
        if new_status is not None:
            args.extend(["--status", new_status])

        try:
            # Ejecutar script de serialización
            result = subprocess.run(
                args,
                capture_output=True,
                text=True,
                timeout=90,
                cwd=str(Path(__file__).parent)
            )

            if result.returncode != 0:
                raise Exception(f"Serialization failed: {result.stderr}")

            # Parsear resultado JSON (puede estar mezclado con logs)
            serialized_data = self._parse_json_from_output(result.stdout)

            if "error" in serialized_data:
                raise Exception(f"Serialization error: {serialized_data['error']}")

            datum_cbor_hex = serialized_data["datum_cbor_hex"]
            redeemer_cbor_hex = serialized_data["redeemer_cbor_hex"]

            print("[OK] Datum y redeemer serializados")
            print(f"    Sensor: {sensor_id}")
            if "changes" in serialized_data:
                for change in serialized_data["changes"]:
                    print(f"    {change}")

        except subprocess.TimeoutExpired:
            raise Exception("Serialization timeout after 90 seconds")
        except json.JSONDecodeError as e:
            raise Exception(f"Failed to parse serialization output: {e}")

        # 2. Llamar al script Lucid con los CBOR hex
        lucid_script = self.lucid_scripts_dir / "update-sensor-lucid.js"

        print(f"\n[+] Construyendo transaccion con Lucid: {lucid_script.name}")

        try:
            result = subprocess.run(
                ["node", str(lucid_script), datum_cbor_hex, redeemer_cbor_hex],
                capture_output=True,
                text=True,
                timeout=120,  # 2 minutos timeout
                cwd=str(self.lucid_scripts_dir)
            )

            # Parsear resultado
            if result.returncode != 0:
                error_data = self._parse_json_from_output(result.stderr) if result.stderr else {"error": "Unknown error"}
                raise Exception(f"Lucid script failed: {error_data.get('error', 'Unknown error')}")

            # Extraer JSON del output (puede tener logs mezclados)
            result_data = self._parse_json_from_output(result.stdout)

            if not result_data.get("success"):
                raise Exception(f"Transaction failed: {result_data.get('error', 'Unknown error')}")

            tx_hash = result_data["txHash"]
            explorer_url = result_data["explorer"]

            print("[OK] Transaccion enviada exitosamente!")
            print(f"    TxHash: {tx_hash}")
            print(f"    Explorer: {explorer_url}")

            return tx_hash

        except subprocess.TimeoutExpired:
            raise Exception("Lucid script timeout after 2 minutes")
        except json.JSONDecodeError as e:
            print(f"[ERROR] Failed to parse Lucid output: {result.stdout}")
            print(f"[ERROR] Stderr: {result.stderr}")
            raise Exception(f"Failed to parse Lucid script output: {e}")
        except Exception as e:
            raise Exception(f"Failed to execute Lucid script: {e}")

    def deactivate_sensor(self, sensor_id: str) -> str:
        """
        Desactivar sensor usando Lucid-Cardano + PyCardano

        Strategy:
        - PyCardano serializa datum y redeemer a CBOR hex
        - Lucid construye y envía la transacción

        Args:
            sensor_id: ID del sensor (ej: "SENSOR_001")

        Returns:
            TxHash de la transacción enviada

        Raises:
            Exception: Si la transacción falla
        """
        print("\n[+] Serializando datum y redeemer para DeactivateSensor...")

        # 1. Llamar al script de serialización Python
        serialize_script = Path(__file__).parent / "serialize_deactivate.py"

        try:
            # Ejecutar script de serialización con sensor_id
            result = subprocess.run(
                ["python", str(serialize_script), sensor_id],
                capture_output=True,
                text=True,
                timeout=90,
                cwd=str(Path(__file__).parent)
            )

            if result.returncode != 0:
                raise Exception(f"Serialization failed: {result.stderr}")

            # Parsear resultado JSON (puede estar mezclado con logs)
            serialized_data = self._parse_json_from_output(result.stdout)

            if "error" in serialized_data:
                raise Exception(f"Serialization error: {serialized_data['error']}")

            datum_cbor_hex = serialized_data["datum_cbor_hex"]
            redeemer_cbor_hex = serialized_data["redeemer_cbor_hex"]

            print("[OK] Datum y redeemer serializados")
            print(f"    Sensor: {sensor_id}")
            print(f"    Nuevo estado: Inactive")

        except subprocess.TimeoutExpired:
            raise Exception("Serialization timeout after 90 seconds")
        except json.JSONDecodeError as e:
            raise Exception(f"Failed to parse serialization output: {e}")

        # 2. Llamar al script Lucid con los CBOR hex
        lucid_script = self.lucid_scripts_dir / "deactivate-sensor-lucid.js"

        print(f"\n[+] Construyendo transaccion con Lucid: {lucid_script.name}")

        try:
            result = subprocess.run(
                ["node", str(lucid_script), datum_cbor_hex, redeemer_cbor_hex],
                capture_output=True,
                text=True,
                timeout=120,  # 2 minutos timeout
                cwd=str(self.lucid_scripts_dir)
            )

            # Parsear resultado
            if result.returncode != 0:
                error_data = self._parse_json_from_output(result.stderr) if result.stderr else {"error": "Unknown error"}
                raise Exception(f"Lucid script failed: {error_data.get('error', 'Unknown error')}")

            # Extraer JSON del output (puede tener logs mezclados)
            result_data = self._parse_json_from_output(result.stdout)

            if not result_data.get("success"):
                raise Exception(f"Transaction failed: {result_data.get('error', 'Unknown error')}")

            tx_hash = result_data["txHash"]
            explorer_url = result_data["explorer"]

            print("[OK] Transaccion enviada exitosamente!")
            print(f"    TxHash: {tx_hash}")
            print(f"    Explorer: {explorer_url}")

            return tx_hash

        except subprocess.TimeoutExpired:
            raise Exception("Lucid script timeout after 2 minutes")
        except json.JSONDecodeError as e:
            print(f"[ERROR] Failed to parse Lucid output: {result.stdout}")
            print(f"[ERROR] Stderr: {result.stderr}")
            raise Exception(f"Failed to parse Lucid script output: {e}")
        except Exception as e:
            raise Exception(f"Failed to execute Lucid script: {e}")

    def _parse_json_from_output(self, output: str) -> Dict[str, Any]:
        """
        Extrae JSON de output que puede tener logs mezclados

        Args:
            output: String con output que contiene JSON

        Returns:
            Dict parseado del JSON

        Raises:
            json.JSONDecodeError: Si no se encuentra JSON válido
        """
        # Método 1: Intentar parsear la última línea (caso común)
        lines = output.strip().split('\n')
        if lines:
            try:
                return json.loads(lines[-1])
            except json.JSONDecodeError:
                pass

        # Método 2: Buscar el primer '{' y último '}' para extraer JSON completo
        start = output.find('{')
        if start != -1:
            # Contar llaves para encontrar el JSON completo
            brace_count = 0
            json_start = start
            json_end = -1

            for i in range(start, len(output)):
                if output[i] == '{':
                    brace_count += 1
                elif output[i] == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        json_end = i + 1
                        break

            if json_end != -1:
                try:
                    json_str = output[json_start:json_end]
                    return json.loads(json_str)
                except json.JSONDecodeError:
                    pass

        # Método 3: Buscar líneas que empiecen con '{'
        for line in reversed(lines):
            line = line.strip()
            if line.startswith('{'):
                try:
                    return json.loads(line)
                except json.JSONDecodeError:
                    continue

        # Si nada funciona, lanzar error con el output completo
        raise json.JSONDecodeError(
            f"No valid JSON found in output: {output[:500]}...",
            output,
            0
        )

    def build_update_datum_transaction(self, datum_cbor: str, redeemer_cbor: str) -> str:
        """
        Construir y enviar transacción de actualización de datum usando Lucid

        Args:
            datum_cbor: Datum serializado en CBOR hex
            redeemer_cbor: Redeemer serializado en CBOR hex

        Returns:
            TxHash de la transacción enviada

        Raises:
            Exception: Si la transacción falla
        """
        lucid_script = self.lucid_scripts_dir / "update-datum-lucid.js"

        print(f"\n[+] Construyendo transacción con Lucid: {lucid_script.name}")

        try:
            result = subprocess.run(
                ["node", str(lucid_script), datum_cbor, redeemer_cbor],
                capture_output=True,
                text=True,
                timeout=120,  # 2 minutos timeout
                cwd=str(self.lucid_scripts_dir)
            )

            # Parsear resultado
            if result.returncode != 0:
                error_data = self._parse_json_from_output(result.stderr) if result.stderr else {"error": "Unknown error"}
                raise Exception(f"Lucid script failed: {error_data.get('error', 'Unknown error')}")

            # Extraer JSON del output
            result_data = self._parse_json_from_output(result.stdout)

            if not result_data.get("success"):
                raise Exception(f"Transaction failed: {result_data.get('error', 'Unknown error')}")

            tx_hash = result_data["txHash"]
            explorer_url = result_data["explorer"]

            print("[OK] Transacción enviada exitosamente!")
            print(f"    TxHash: {tx_hash}")
            print(f"    Explorer: {explorer_url}")

            return tx_hash

        except subprocess.TimeoutExpired:
            raise Exception("Lucid script timeout after 2 minutes")
        except json.JSONDecodeError as e:
            print(f"[ERROR] Failed to parse Lucid output: {result.stdout}")
            print(f"[ERROR] Stderr: {result.stderr}")
            raise Exception(f"Failed to parse Lucid script output: {e}")
        except Exception as e:
            raise Exception(f"Failed to execute Lucid script: {e}")
