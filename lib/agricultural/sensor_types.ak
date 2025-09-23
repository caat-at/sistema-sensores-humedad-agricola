// Tipos de datos para sensores agrícolas
// Usando tipos builtin de Aiken v1.1.19

// Coordenadas GPS del sensor
pub type GpsCoordinates {
  latitude: Int,
  // Latitud multiplicada por 1,000,000
  longitude: Int,
}

// Longitud multiplicada por 1,000,000

// Estado operativo del sensor
pub type SensorStatus {
  Active
  Maintenance
  Error
  Offline
}

// Datos del sensor de humedad
pub type HumiditySensorData {
  sensor_id: ByteArray,
  // ID único del sensor
  timestamp: Int,
  // Timestamp Unix en milisegundos
  humidity_level: Int,
  // Porcentaje de humedad (0-100)
  soil_temperature: Int,
  // Temperatura en grados Celsius * 10
  battery_level: Int,
  // Nivel de batería (0-100)
  gps_location: GpsCoordinates,
  // Ubicación GPS
  status: SensorStatus,
  // Estado del sensor
  signature: ByteArray,
}

// Firma criptográfica

// Configuración del sensor
pub type SensorConfig {
  sensor_id: ByteArray,
  owner_key: ByteArray,
  // Clave pública del propietario
  min_humidity: Int,
  // Umbral mínimo de humedad
  max_humidity: Int,
  // Umbral máximo de humedad
  alert_threshold: Int,
  // Umbral para alertas críticas
  measurement_interval: Int,
  // Intervalo entre mediciones (segundos)
  calibration_factor: Int,
}

// Factor de calibración

// Alerta generada por el sistema
pub type HumidityAlert {
  sensor_id: ByteArray,
  alert_type: AlertType,
  severity: AlertSeverity,
  timestamp: Int,
  // Timestamp Unix en milisegundos
  humidity_value: Int,
  message: ByteArray,
}

pub type AlertType {
  LowHumidity
  HighHumidity
  SensorMalfunction
  BatteryLow
  CommunicationLost
}

pub type AlertSeverity {
  Info
  Warning
  Critical
  Emergency
}
