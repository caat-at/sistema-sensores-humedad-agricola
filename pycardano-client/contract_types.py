# -*- coding: utf-8 -*-
"""
Definiciones de tipos PlutusData para el contrato de sensores de humedad
Estos tipos deben coincidir EXACTAMENTE con los del contrato OpShin
"""

from pycardano import PlutusData
from dataclasses import dataclass
from typing import List, Union


# ========================================
# TIPOS DE DATOS - Ubicación
# ========================================

@dataclass
class Location(PlutusData):
    """Información de ubicación geográfica"""
    CONSTR_ID = 0
    latitude: int  # Coordenada * 1000000 para decimales
    longitude: int  # Coordenada * 1000000 para decimales
    zone_name: bytes  # Nombre de la zona agrícola


# ========================================
# TIPOS DE DATOS - Estados del Sensor
# ========================================

@dataclass
class Active(PlutusData):
    """Estado: Sensor activo"""
    CONSTR_ID = 0


@dataclass
class Inactive(PlutusData):
    """Estado: Sensor inactivo"""
    CONSTR_ID = 1


@dataclass
class Maintenance(PlutusData):
    """Estado: Sensor en mantenimiento"""
    CONSTR_ID = 2


@dataclass
class ErrorStatus(PlutusData):
    """Estado: Sensor en error"""
    CONSTR_ID = 3


# Tipo unión para estados del sensor
SensorStatus = Union[Active, Inactive, Maintenance, ErrorStatus]


# ========================================
# TIPOS DE DATOS - Niveles de Alerta
# ========================================

@dataclass
class Normal(PlutusData):
    """Nivel de alerta: Normal (40-70%)"""
    CONSTR_ID = 0


@dataclass
class Low(PlutusData):
    """Nivel de alerta: Bajo (<40%) - Necesita riego"""
    CONSTR_ID = 1


@dataclass
class High(PlutusData):
    """Nivel de alerta: Alto (>70%) - Riesgo de hongos"""
    CONSTR_ID = 2


@dataclass
class Critical(PlutusData):
    """Nivel de alerta: Crítico (<20% o >85%) - Acción inmediata"""
    CONSTR_ID = 3


# Tipo unión para niveles de alerta
HumidityAlert = Union[Normal, Low, High, Critical]


# ========================================
# TIPOS DE DATOS - Sensor y Lecturas
# ========================================

@dataclass
class SensorConfig(PlutusData):
    """Configuración de un sensor individual"""
    CONSTR_ID = 0
    sensor_id: bytes
    location: Location
    min_humidity_threshold: int
    max_humidity_threshold: int
    reading_interval_minutes: int
    status: SensorStatus
    owner: bytes  # PubKeyHash
    installed_date: int  # Timestamp


@dataclass
class HumidityReading(PlutusData):
    """Registro individual de lectura de humedad"""
    CONSTR_ID = 0
    sensor_id: bytes
    humidity_percentage: int
    temperature_celsius: int
    timestamp: int
    alert_level: HumidityAlert


@dataclass
class RollupStatistics(PlutusData):
    """Estadísticas agregadas de un rollup diario"""
    CONSTR_ID = 0
    humidity_min: int
    humidity_max: int
    humidity_avg: int
    temperature_min: int
    temperature_max: int
    temperature_avg: int


@dataclass
class DailyRollup(PlutusData):
    """Rollup diario de lecturas con merkle hash"""
    CONSTR_ID = 0
    sensor_id: bytes
    merkle_root: bytes  # Hash raíz SHA-256 (32 bytes)
    readings_count: int
    date: bytes  # Fecha en formato YYYY-MM-DD
    statistics: RollupStatistics
    first_reading_timestamp: int
    last_reading_timestamp: int
    rollup_type: bytes  # "daily", "hourly", etc.


@dataclass
class HumiditySensorDatum(PlutusData):
    """Datum principal - Estado del sistema"""
    CONSTR_ID = 0
    sensors: List[SensorConfig]
    recent_readings: List[HumidityReading]
    admin: bytes  # PubKeyHash
    last_updated: int  # Timestamp
    total_sensors: int


# ========================================
# REDEEMERS - Acciones permitidas
# ========================================

@dataclass
class RegisterSensor(PlutusData):
    """Registrar nuevo sensor"""
    CONSTR_ID = 0
    config: SensorConfig


@dataclass
class UpdateSensorConfig(PlutusData):
    """Actualizar configuración de sensor"""
    CONSTR_ID = 1
    sensor_id: bytes
    new_config: SensorConfig


@dataclass
class DeactivateSensor(PlutusData):
    """Desactivar sensor"""
    CONSTR_ID = 2
    sensor_id: bytes


@dataclass
class AddReading(PlutusData):
    """Agregar lectura de humedad"""
    CONSTR_ID = 3
    reading: HumidityReading


@dataclass
class AddMultipleReadings(PlutusData):
    """Agregar múltiples lecturas"""
    CONSTR_ID = 4
    readings: List[HumidityReading]


@dataclass
class UpdateAdmin(PlutusData):
    """Cambiar administrador"""
    CONSTR_ID = 5
    new_admin: bytes


@dataclass
class SetMaintenanceMode(PlutusData):
    """Activar modo mantenimiento"""
    CONSTR_ID = 6
    sensor_id: bytes


@dataclass
class EmergencyStop(PlutusData):
    """Detener sistema en emergencia"""
    CONSTR_ID = 7
    reason: bytes


@dataclass
class AddDailyRollup(PlutusData):
    """Agregar rollup diario con merkle hash"""
    CONSTR_ID = 8
    rollup: DailyRollup


# Tipo unión para redeemers
HumiditySensorRedeemer = Union[
    RegisterSensor,
    UpdateSensorConfig,
    DeactivateSensor,
    AddReading,
    AddMultipleReadings,
    UpdateAdmin,
    SetMaintenanceMode,
    EmergencyStop,
    AddDailyRollup,
]


# ========================================
# FUNCIONES HELPER
# ========================================

def create_location(latitude: float, longitude: float, zone_name: str) -> Location:
    """
    Helper para crear Location desde coordenadas decimales

    Args:
        latitude: Latitud en grados decimales (ej: -34.58)
        longitude: Longitud en grados decimales (ej: -58.45)
        zone_name: Nombre de la zona

    Returns:
        Location con coordenadas convertidas a int
    """
    return Location(
        latitude=int(latitude * 1_000_000),
        longitude=int(longitude * 1_000_000),
        zone_name=zone_name.encode('utf-8')
    )


def create_sensor_config(
    sensor_id: str,
    latitude: float,
    longitude: float,
    zone_name: str,
    min_humidity: int,
    max_humidity: int,
    reading_interval: int,
    owner_pkh: bytes,
    installed_timestamp: int
) -> SensorConfig:
    """
    Helper para crear SensorConfig con valores por defecto

    Args:
        sensor_id: Identificador del sensor (ej: "SENSOR_001")
        latitude: Latitud en grados decimales
        longitude: Longitud en grados decimales
        zone_name: Nombre de la zona
        min_humidity: Umbral mínimo de humedad (%)
        max_humidity: Umbral máximo de humedad (%)
        reading_interval: Intervalo de lecturas en minutos
        owner_pkh: PubKeyHash del propietario
        installed_timestamp: Timestamp de instalación (ms)

    Returns:
        SensorConfig configurado
    """
    return SensorConfig(
        sensor_id=sensor_id.encode('utf-8'),
        location=create_location(latitude, longitude, zone_name),
        min_humidity_threshold=min_humidity,
        max_humidity_threshold=max_humidity,
        reading_interval_minutes=reading_interval,
        status=Active(),  # Siempre activo al crear
        owner=owner_pkh,
        installed_date=installed_timestamp
    )


def calculate_alert_level(humidity: int) -> HumidityAlert:
    """
    Calcula el nivel de alerta según el porcentaje de humedad

    Args:
        humidity: Porcentaje de humedad (0-100)

    Returns:
        Nivel de alerta apropiado
    """
    if humidity < 20 or humidity > 85:
        return Critical()
    elif humidity < 40:
        return Low()
    elif humidity > 70:
        return High()
    else:
        return Normal()


def create_humidity_reading(
    sensor_id: str,
    humidity: int,
    temperature: int,
    timestamp: int
) -> HumidityReading:
    """
    Helper para crear HumidityReading con nivel de alerta calculado

    Args:
        sensor_id: Identificador del sensor
        humidity: Porcentaje de humedad (0-100)
        temperature: Temperatura en Celsius
        timestamp: Timestamp de la lectura (ms)

    Returns:
        HumidityReading con alert_level calculado
    """
    return HumidityReading(
        sensor_id=sensor_id.encode('utf-8'),
        humidity_percentage=humidity,
        temperature_celsius=temperature,
        timestamp=timestamp,
        alert_level=calculate_alert_level(humidity)
    )


def create_daily_rollup(
    sensor_id: str,
    merkle_root: str,
    readings_count: int,
    date: str,
    humidity_min: int,
    humidity_max: int,
    humidity_avg: int,
    temperature_min: int,
    temperature_max: int,
    temperature_avg: int,
    first_reading_timestamp: int,
    last_reading_timestamp: int
) -> DailyRollup:
    """
    Helper para crear DailyRollup desde datos del servicio de rollup

    Args:
        sensor_id: Identificador del sensor
        merkle_root: Hash raíz SHA-256 (hex string de 64 caracteres)
        readings_count: Cantidad de lecturas en el rollup
        date: Fecha en formato YYYY-MM-DD
        humidity_min: Humedad mínima del día
        humidity_max: Humedad máxima del día
        humidity_avg: Humedad promedio del día
        temperature_min: Temperatura mínima del día
        temperature_max: Temperatura máxima del día
        temperature_avg: Temperatura promedio del día
        first_reading_timestamp: Timestamp de la primera lectura (ms)
        last_reading_timestamp: Timestamp de la última lectura (ms)

    Returns:
        DailyRollup configurado para blockchain
    """
    statistics = RollupStatistics(
        humidity_min=humidity_min,
        humidity_max=humidity_max,
        humidity_avg=humidity_avg,
        temperature_min=temperature_min,
        temperature_max=temperature_max,
        temperature_avg=temperature_avg
    )

    return DailyRollup(
        sensor_id=sensor_id.encode('utf-8'),
        merkle_root=bytes.fromhex(merkle_root),
        readings_count=readings_count,
        date=date.encode('utf-8'),
        statistics=statistics,
        first_reading_timestamp=first_reading_timestamp,
        last_reading_timestamp=last_reading_timestamp,
        rollup_type=b"daily"
    )
