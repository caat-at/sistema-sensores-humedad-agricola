# -*- coding: utf-8 -*-
"""
Servicio de integración con blockchain Cardano usando PyCardano
Centraliza todas las operaciones blockchain para el API REST
"""

import sys
from pathlib import Path
from typing import Optional
from datetime import datetime

# Agregar pycardano-client al path
pycardano_path = Path(__file__).parent.parent.parent / "pycardano-client"
sys.path.insert(0, str(pycardano_path))

from transaction_builder import SensorTransactionBuilder
from contract_types import create_sensor_config, create_humidity_reading


class BlockchainService:
    """
    Servicio para interactuar con el smart contract en Cardano
    Usa SensorTransactionBuilder (PyCardano) para todas las operaciones
    """

    def __init__(self):
        """Inicializa el transaction builder"""
        self.builder = SensorTransactionBuilder()

    def get_all_sensors(self):
        """
        Obtiene todos los sensores del datum
        Retorna la lista de sensores sin deduplicar
        """
        utxo = self.builder.get_datum_utxo()
        datum = self.builder.decode_datum(utxo)
        return datum.sensors

    def get_sensor_by_id(self, sensor_id: str):
        """
        Busca un sensor específico por ID
        Retorna el primer sensor encontrado con ese ID
        """
        sensors = self.get_all_sensors()
        for sensor in sensors:
            if sensor.sensor_id.decode('utf-8', errors='ignore') == sensor_id:
                return sensor
        return None

    def get_all_readings(self):
        """Obtiene todas las lecturas recientes del datum"""
        utxo = self.builder.get_datum_utxo()
        datum = self.builder.decode_datum(utxo)
        return datum.recent_readings

    def register_sensor(
        self,
        sensor_id: str,
        latitude: float,
        longitude: float,
        zone_name: str,
        min_humidity: int,
        max_humidity: int,
        reading_interval: int
    ) -> str:
        """
        Registra un nuevo sensor en blockchain

        Args:
            sensor_id: ID del sensor (ej: SENSOR_001)
            latitude: Latitud en grados decimales
            longitude: Longitud en grados decimales
            zone_name: Nombre de la zona agrícola
            min_humidity: Umbral mínimo de humedad (%)
            max_humidity: Umbral máximo de humedad (%)
            reading_interval: Intervalo de lecturas (minutos)

        Returns:
            Transaction hash (hex string)
        """
        timestamp_now = int(datetime.now().timestamp() * 1000)

        sensor_config = create_sensor_config(
            sensor_id=sensor_id,
            latitude=latitude,
            longitude=longitude,
            zone_name=zone_name,
            min_humidity=min_humidity,
            max_humidity=max_humidity,
            reading_interval=reading_interval,
            owner_pkh=self.builder.payment_vkey.hash().to_primitive(),
            installed_timestamp=timestamp_now
        )

        tx_hash = self.builder.build_register_sensor_tx(sensor_config)
        return tx_hash

    def add_reading(
        self,
        sensor_id: str,
        humidity: int,
        temperature: int
    ) -> str:
        """
        Agrega una lectura a un sensor existente

        Args:
            sensor_id: ID del sensor
            humidity: Humedad en porcentaje (0-100)
            temperature: Temperatura en Celsius

        Returns:
            Transaction hash (hex string)
        """
        timestamp_now = int(datetime.now().timestamp() * 1000)

        reading = create_humidity_reading(
            sensor_id=sensor_id,
            humidity=humidity,
            temperature=temperature,
            timestamp=timestamp_now
        )

        tx_hash = self.builder.build_add_reading_tx(reading)
        return tx_hash

    def get_existing_sensor_ids(self) -> set:
        """
        Obtiene todos los IDs de sensores existentes (incluyendo duplicados)
        Útil para validación de IDs únicos
        """
        sensors = self.get_all_sensors()
        return {s.sensor_id.decode('utf-8', errors='ignore') for s in sensors}

    def auto_generate_sensor_id(self) -> str:
        """
        Genera automáticamente el próximo ID de sensor disponible
        Formato: SENSOR_001, SENSOR_002, etc.
        """
        existing_ids = self.get_existing_sensor_ids()

        # Extraer números de IDs existentes
        sensor_numbers = []
        for sensor_id in existing_ids:
            if sensor_id.startswith("SENSOR_"):
                try:
                    num = int(sensor_id.replace("SENSOR_", ""))
                    sensor_numbers.append(num)
                except ValueError:
                    continue

        # Calcular el próximo número
        if sensor_numbers:
            next_number = max(sensor_numbers) + 1
        else:
            next_number = 1

        return f"SENSOR_{next_number:03d}"

    def deduplicate_sensors(self, sensors):
        """
        Deduplica sensores por sensor_id
        Preferencia: 1) Active sobre Inactive, 2) Fecha más reciente

        Args:
            sensors: Lista de SensorConfig

        Returns:
            Dict de sensores deduplicados {sensor_id: SensorConfig}
        """
        sensors_dict = {}

        for sensor in sensors:
            sensor_id = sensor.sensor_id.decode('utf-8', errors='ignore')
            is_active = type(sensor.status).__name__ == 'Active'
            installed_date = sensor.installed_date

            # Si no existe, agregar
            if sensor_id not in sensors_dict:
                sensors_dict[sensor_id] = sensor
            else:
                # Si existe, comparar
                existing = sensors_dict[sensor_id]
                existing_is_active = type(existing.status).__name__ == 'Active'
                existing_date = existing.installed_date

                # Preferir Active sobre Inactive
                if is_active and not existing_is_active:
                    sensors_dict[sensor_id] = sensor
                # Si ambos tienen el mismo estado, preferir el más reciente
                elif is_active == existing_is_active and installed_date > existing_date:
                    sensors_dict[sensor_id] = sensor

        return sensors_dict

    def submit_rollup(self, rollup_datum: dict) -> str:
        """
        Envía un rollup (múltiples lecturas) a blockchain usando AddMultipleReadings

        Args:
            rollup_datum: Diccionario con datos del rollup incluyendo:
                - sensor_id: ID del sensor
                - merkle_root: Root del merkle tree
                - readings_count: Número de lecturas
                - statistics: Estadísticas agregadas
                - Información de las lecturas individuales (si están disponibles)

        Returns:
            Transaction hash (hex string)
        """
        # Extraer las lecturas del rollup
        # El rollup_datum debería contener una lista de lecturas individuales
        # Por ahora, vamos a crear una lectura resumen basada en las estadísticas

        # Crear una lectura con los promedios del rollup
        timestamp_now = int(datetime.now().timestamp() * 1000)

        # Crear lectura resumen del rollup
        rollup_reading = create_humidity_reading(
            sensor_id=rollup_datum["sensor_id"],
            humidity=int(rollup_datum["statistics"]["humidity_avg"]),
            temperature=int(rollup_datum["statistics"]["temperature_avg"]),
            timestamp=timestamp_now
        )

        # Por ahora, enviar una sola lectura resumen
        # En una implementación completa, podrías enviar todas las lecturas individuales
        readings = [rollup_reading]

        print(f"\n[ROLLUP] Enviando rollup para {rollup_datum['sensor_id']}")
        print(f"    Lecturas agregadas: {rollup_datum['readings_count']}")
        print(f"    Merkle Root: {rollup_datum['merkle_root'][:16]}...")
        print(f"    Humedad promedio: {rollup_datum['statistics']['humidity_avg']}%")
        print(f"    Temperatura promedio: {rollup_datum['statistics']['temperature_avg']}°C")

        tx_hash = self.builder.build_add_multiple_readings_tx(readings)
        return tx_hash
