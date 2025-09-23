use agricultural/sensor_types.{
  BatteryLow, CommunicationLost, HighHumidity, HumidityAlert, HumiditySensorData,
  LowHumidity, SensorConfig, SensorMalfunction,
}
use aiken/builtin.{length_of_bytearray}
use aiken/collection/list
use cardano/transaction.{OutputReference, Transaction}

// IMPORTANTE: Reemplaza este valor con tu clave pública real del administrador
// Debe ser un hash de 28 bytes en hexadecimal (56 caracteres)
const admin_pubkey: ByteArray =
  #"e07ade146aec142361d319b5a8ecc6b107c915bc1aadaf75d405361f333526c9"

// Acciones del contrato
pub type SensorRedeemer {
  RegisterSensor { config: SensorConfig }
  SubmitData { sensor_data: HumiditySensorData }
  UpdateConfig { sensor_id: ByteArray, new_config: SensorConfig }
  GenerateAlert { alert: HumidityAlert }
}

// Validador principal - AHORA SIN PARÁMETROS
validator humidity_sensor_validator {
  spend(
    datum_opt: Option<SensorConfig>,
    redeemer: SensorRedeemer,
    _input: OutputReference,
    transaction: Transaction,
  ) {
    expect Some(config) = datum_opt

    when redeemer is {
      RegisterSensor { config: new_cfg } ->
        verify_admin_signature(transaction, admin_pubkey) && validate_sensor_config(
          new_cfg,
        )

      SubmitData { sensor_data } ->
        sensor_data.sensor_id == config.sensor_id && validate_data_ranges(
          sensor_data,
        ) && verify_sensor_signature(sensor_data) && validate_timestamp(
          sensor_data.timestamp,
        )

      UpdateConfig { sensor_id, new_config } ->
        sensor_id == config.sensor_id && verify_admin_signature(
          transaction,
          admin_pubkey,
        ) && validate_sensor_config(new_config)

      GenerateAlert { alert } ->
        alert.sensor_id == config.sensor_id && validate_alert_conditions(
          alert,
          config,
        ) && validate_timestamp(alert.timestamp)
    }
  }

  else(_) {
    fail
  }
}

// Verifica firma del administrador
fn verify_admin_signature(
  transaction: Transaction,
  admin_pubkey: ByteArray,
) -> Bool {
  list.has(transaction.extra_signatories, admin_pubkey)
}

// Valida configuración de sensor
pub fn validate_sensor_config(config: SensorConfig) -> Bool {
  config.min_humidity >= 0 && config.max_humidity <= 100 && config.min_humidity < config.max_humidity && config.measurement_interval >= 60 && config.measurement_interval <= 86400 && config.alert_threshold >= 0 && config.alert_threshold <= 100
}

// Valida rangos de datos de sensor
pub fn validate_data_ranges(sensor_data: HumiditySensorData) -> Bool {
  sensor_data.humidity_level >= 0 && sensor_data.humidity_level <= 100 && sensor_data.soil_temperature >= -200 && sensor_data.soil_temperature <= 600 && sensor_data.battery_level >= 0 && sensor_data.battery_level <= 100 && sensor_data.gps_location.latitude >= -90000000 && sensor_data.gps_location.latitude <= 90000000 && sensor_data.gps_location.longitude >= -180000000 && sensor_data.gps_location.longitude <= 180000000
}

// Verifica longitud de firma Ed25519 (64 bytes)
fn verify_sensor_signature(sensor_data: HumiditySensorData) -> Bool {
  length_of_bytearray(sensor_data.signature) == 64
}

// Valida condiciones de alerta usando umbrales del config
fn validate_alert_conditions(alert: HumidityAlert, config: SensorConfig) -> Bool {
  when alert.alert_type is {
    LowHumidity -> alert.humidity_value < config.min_humidity
    HighHumidity -> alert.humidity_value > config.max_humidity
    SensorMalfunction -> True
    BatteryLow -> True
    CommunicationLost -> True
  }
}

// Valida timestamp Unix en ms (entre 2020 y 2040)
fn validate_timestamp(timestamp: Int) -> Bool {
  timestamp >= 1577836800000 && timestamp <= 2208988800000
}
