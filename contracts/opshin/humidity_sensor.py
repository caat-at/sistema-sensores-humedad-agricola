"""
Sistema de Sensores de Humedad Agrícola - OpShin (Plutus V2)
Smart contract para monitorear sensores de humedad en blockchain Cardano
"""

from opshin.prelude import *


# ========================================
# TIPOS DE DATOS
# ========================================

@dataclass
class Location(PlutusData):
    """Información de ubicación geográfica"""
    CONSTR_ID = 0
    latitude: int  # Coordenada * 1000000 para decimales
    longitude: int  # Coordenada * 1000000 para decimales
    zone_name: bytes  # Nombre de la zona agrícola


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
class Error(PlutusData):
    """Estado: Sensor en error"""
    CONSTR_ID = 3


# Tipo unión para estados del sensor
SensorStatus = Union[Active, Inactive, Maintenance, Error]


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
]


# ========================================
# FUNCIONES DE UTILIDAD
# ========================================

def find_sensor_config(sensors: List[SensorConfig], sensor_id: bytes) -> SensorConfig:
    """Encontrar sensor por ID"""
    matching_sensors = [s for s in sensors if s.sensor_id == sensor_id]
    assert len(matching_sensors) > 0, "Sensor not found"
    return matching_sensors[0]


def validate_reading(reading: HumidityReading, config: SensorConfig) -> bool:
    """Validar que la lectura sea consistente"""
    # El sensor debe existir y estar activo
    if reading.sensor_id != config.sensor_id:
        return False

    if not isinstance(config.status, Active):
        return False

    # Valores dentro de rangos válidos
    if reading.humidity_percentage < 0 or reading.humidity_percentage > 100:
        return False

    if reading.temperature_celsius < -30 or reading.temperature_celsius > 60:
        return False

    # Timestamp no puede ser negativo
    if reading.timestamp <= 0:
        return False

    return True


def validate_sensor_config(config: SensorConfig, max_sensors: int, current_sensors: int) -> bool:
    """Validar configuración de nuevo sensor"""
    # No exceder el máximo de sensores
    if current_sensors >= max_sensors:
        return False

    # El sensor debe estar activo al registrarse
    if not isinstance(config.status, Active):
        return False

    # Validaciones básicas
    if config.min_humidity_threshold < 0 or config.min_humidity_threshold > 100:
        return False

    if config.max_humidity_threshold < config.min_humidity_threshold:
        return False

    if config.max_humidity_threshold > 100:
        return False

    if config.reading_interval_minutes <= 0:
        return False

    return True


def validate_admin_update(datum: HumiditySensorDatum, new_admin: bytes) -> bool:
    """Validar actualización de administrador"""
    # El nuevo admin debe ser diferente
    if new_admin == datum.admin:
        return False

    # El nuevo admin no debe estar vacío
    if new_admin == b"":
        return False

    return True


# ========================================
# VALIDADOR PRINCIPAL
# ========================================

def validator(
    datum: HumiditySensorDatum,
    redeemer: HumiditySensorRedeemer,
    context: ScriptContext,
) -> None:
    """
    Validador principal del sistema de sensores de humedad
    """
    # Configuración hardcodeada
    max_sensors = 100

    # Validar según el tipo de redeemer
    if isinstance(redeemer, RegisterSensor):
        # Validar registro de nuevo sensor
        assert validate_sensor_config(
            redeemer.config,
            max_sensors,
            datum.total_sensors
        ), "Invalid sensor configuration"

    elif isinstance(redeemer, AddReading):
        # Validar adición de lectura
        config = find_sensor_config(datum.sensors, redeemer.reading.sensor_id)
        assert validate_reading(redeemer.reading, config), "Invalid reading"

        # Validaciones adicionales
        assert redeemer.reading.humidity_percentage >= 0, "Humidity cannot be negative"
        assert redeemer.reading.humidity_percentage <= 100, "Humidity cannot exceed 100"
        assert redeemer.reading.timestamp > 0, "Invalid timestamp"

    elif isinstance(redeemer, UpdateAdmin):
        # Validar actualización de admin
        assert validate_admin_update(datum, redeemer.new_admin), "Invalid admin update"

    elif isinstance(redeemer, UpdateSensorConfig):
        # Validar que el sensor exista
        _ = find_sensor_config(datum.sensors, redeemer.sensor_id)
        # Validar nueva configuración
        assert validate_sensor_config(
            redeemer.new_config,
            max_sensors,
            datum.total_sensors
        ), "Invalid sensor configuration"

    elif isinstance(redeemer, DeactivateSensor):
        # Validar que el sensor exista
        _ = find_sensor_config(datum.sensors, redeemer.sensor_id)

    elif isinstance(redeemer, AddMultipleReadings):
        # Validar todas las lecturas
        for reading in redeemer.readings:
            config = find_sensor_config(datum.sensors, reading.sensor_id)
            assert validate_reading(reading, config), "Invalid reading in batch"

    elif isinstance(redeemer, SetMaintenanceMode):
        # Validar que el sensor exista
        _ = find_sensor_config(datum.sensors, redeemer.sensor_id)

    elif isinstance(redeemer, EmergencyStop):
        # El emergency stop requiere firma del admin
        # Esta validación se haría normalmente verificando firmas
        # En este ejemplo simplificado, solo verificamos que el reason no esté vacío
        assert redeemer.reason != b"", "Emergency stop requires a reason"

    else:
        assert False, "Unknown redeemer type"
