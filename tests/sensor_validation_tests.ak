use agricultural/sensor_types.{
  HumiditySensorData, SensorConfig, GpsCoordinates, SensorStatus
}
use humidity_sensor_validator

let test_config = SensorConfig {
  sensor_id: #"0123456789abcdef0123456789abcdef",
  owner_key: #"fedcba9876543210fedcba9876543210",
  min_humidity: 30,
  max_humidity: 80,
  alert_threshold: 25,
  measurement_interval: 300,
  calibration_factor: 100,
}

let test_data = HumiditySensorData {
  sensor_id: #"0123456789abcdef0123456789abcdef",
  timestamp: 1692800000000,  // Unix timestamp en milisegundos
  humidity_level: 45,
  soil_temperature: 220,
  battery_level: 85,
  gps_location: GpsCoordinates { 
    latitude: 6244000, 
    longitude: -75581000 
  },
  status: Active,
  signature: #"1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
}

test test_validate_config() {
  humidity_sensor_validator.validate_sensor_config(test_config) == True
}

test test_validate_data_ranges() {
  humidity_sensor_validator.validate_data_ranges(test_data) == True
}

test test_invalid_humidity() {
  let invalid_data = HumiditySensorData {
    ..test_data,
    humidity_level: 150,
  }
  humidity_sensor_validator.validate_data_ranges(invalid_data) == False
}