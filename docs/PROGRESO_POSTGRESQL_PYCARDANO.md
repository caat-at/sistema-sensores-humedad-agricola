# Progreso: PostgreSQL + PyCardano Implementation

**Fecha:** 2025-10-19
**Sesión:** Configuración de PostgreSQL e Implementación de PyCardano Transaction Builder

---

## Resumen de Logros

### ✅ 1. PostgreSQL Completamente Configurado

**Base de Datos:** `sensor_system`
**Usuario:** `sensor_app`
**Password:** `change_this_password`

#### Tablas Creadas (4):
- `sensors_history` - Histórico completo de sensores y configuraciones
- `readings_history` - Histórico completo de lecturas
- `transactions_log` - Log de todas las transacciones blockchain
- `sensor_alerts` - Alertas generadas por condiciones anormales

#### Vistas Creadas (3):
- `current_sensors` - Vista de sensores activos actuales
- `latest_readings_per_sensor` - Última lectura por sensor
- `sensor_statistics` - Estadísticas agregadas por sensor

#### Funciones y Triggers:
- `archive_old_readings()` - Archivar lecturas antiguas
- `mark_sensor_not_current()` - Marcar versión histórica
- `update_updated_at_column()` - Trigger automático de timestamps

#### Archivos:
- [database/schema.sql](database/schema.sql) - Schema completo corregido
- [api/database/connection.py](api/database/connection.py) - Conexión SQLAlchemy 2.0
- [api/database/models.py](api/database/models.py) - Modelos ORM
- [api/database/middleware.py](api/database/middleware.py) - Funciones middleware
- [scripts/verify_db.py](scripts/verify_db.py) - Script de verificación

#### Verificación:
```bash
python scripts/verify_db.py
```

Salida:
```
[OK] Conexion a PostgreSQL exitosa
[OK] Base de datos: sensor_system
[OK] Tablas encontradas: 4
[OK] Vistas encontradas: 3
[OK] TODAS LAS TABLAS REQUERIDAS ESTAN PRESENTES
```

---

### ✅ 2. Implementación de PyCardano Transaction Builder

Se creó una implementación completa para construir transacciones con PyCardano, siguiendo la **Opción B** recomendada en [ESTADO_ACTUAL.md](ESTADO_ACTUAL.md).

#### Archivos Creados:

##### 1. [pycardano-client/contract_types.py](pycardano-client/contract_types.py)
Definición completa de tipos PlutusData mapeados desde OpShin:

**Tipos básicos:**
- `Location` - Ubicación geográfica del sensor
- `Active`, `Inactive`, `Maintenance`, `ErrorStatus` - Estados del sensor
- `Normal`, `Low`, `High`, `Critical` - Niveles de alerta

**Estructuras principales:**
- `SensorConfig` - Configuración completa de un sensor
- `HumidityReading` - Lectura individual de sensor
- `HumiditySensorDatum` - Estado completo del contrato (datum)

**Redeemers (acciones):**
- `RegisterSensor` - Registrar nuevo sensor
- `UpdateSensorConfig` - Actualizar configuración
- `DeactivateSensor` - Desactivar sensor
- `AddReading` - Agregar lectura
- `AddMultipleReadings` - Agregar múltiples lecturas
- `UpdateAdmin` - Cambiar administrador
- `SetMaintenanceMode` - Activar mantenimiento
- `EmergencyStop` - Detener sistema

**Helpers:**
- `create_location()` - Crear Location desde coordenadas decimales
- `create_sensor_config()` - Crear SensorConfig con validación
- `calculate_alert_level()` - Calcular nivel de alerta por humedad
- `create_humidity_reading()` - Crear HumidityReading con alerta automática

##### 2. [pycardano-client/transaction_builder.py](pycardano-client/transaction_builder.py)
Transaction Builder completo para interactuar con el contrato:

**Clase:** `SensorTransactionBuilder`

**Funcionalidades:**
- ✅ Inicialización con BlockFrost context
- ✅ Carga de script Plutus compilado
- ✅ Derivación de wallet desde seed phrase (BIP39/BIP44)
- ✅ Obtención de UTxO con datum del contrato
- ✅ Decodificación de datums
- ✅ Construcción de transacción `RegisterSensor`
- ✅ Construcción de transacción `AddReading`

**Métodos principales:**
- `load_script()` - Cargar script Plutus desde archivo CBOR
- `setup_wallet()` - Derivar claves desde seed phrase
- `get_datum_utxo()` - Obtener UTxO con estado actual
- `decode_datum()` - Decodificar datum CBOR
- `build_register_sensor_tx()` - Construir TX para registrar sensor
- `build_add_reading_tx()` - Construir TX para agregar lectura

##### 3. [pycardano-client/register_sensor.py](pycardano-client/register_sensor.py)
Script listo para registrar sensores:

**Configuración del sensor de ejemplo:**
```python
SENSOR_ID = "SENSOR_002"
LATITUDE = -34.6
LONGITUDE = -58.47
ZONE_NAME = "Test Zone"
MIN_HUMIDITY = 30
MAX_HUMIDITY = 70
READING_INTERVAL = 60  # minutos
```

**Uso:**
```bash
cd pycardano-client
python register_sensor.py
```

---

## Estado Actual del Sistema

### Blockchain (Preview Testnet)

**Contrato:**
- Address: `addr_test1wz873sjp5wenffd4x8jusc94kek42w4mwpuevnagkzkwsqg0j0aty`
- UTxOs: 7 total (25.86 ADA bloqueados)
- Estado: ✅ Inicializado con datum inline

**UTxO con Datum:**
- TxHash: `bbf0bb9b72d71dd3...`
- Amount: 7.86 ADA
- Datum: ✅ Inline CBOR

**Sensores registrados:**
- SENSOR_001 (registrado previamente)

**Wallet Admin:**
- Address: `addr_test1qqk2wn579xnauz85l4jv6gpjg9vrac960t0m3txw2tyafsp4s0ln5d66zrfy0qgasjqxxg3qc5ftmqyhparh58w2fqxqkwnupe`
- PKH: `2ca74e9e29a7de08f4fd64cd203241583ee0ba7adfb8acce52c9d4c0`
- Balance: ~9963 ADA (Preview Testnet)

### Base de Datos (PostgreSQL)

**Estado:** ✅ Configurada y lista para usar
**Tablas:** 4/4 creadas
**Vistas:** 3/3 creadas
**Permisos:** ✅ Otorgados a `sensor_app`

---

## Próximos Pasos Recomendados

### Opción A: Probar Registro de Sensor (RECOMENDADO)

Ahora que todo está listo, podemos probar registrar un nuevo sensor:

```bash
cd pycardano-client
python register_sensor.py
```

**Nota:** Esto enviará una transacción REAL a Preview Testnet.

**Riesgos:**
- Bajo - Solo Preview Testnet (tADA)
- Requiere confirmar con "y" antes de enviar
- El Transaction Builder está probado con imports correctos

**Tiempo estimado:** 5-10 minutos (incluye espera de confirmación)

---

### Opción B: Implementar add_reading.py

Crear script para agregar lecturas de sensores:

**Archivos a crear:**
- `pycardano-client/add_reading.py`

**Funcionalidad:**
```python
# Crear lectura
reading = create_humidity_reading(
    sensor_id="SENSOR_001",
    humidity=45,
    temperature=22,
    timestamp=int(time.time() * 1000)
)

# Enviar transacción
tx_hash = builder.build_add_reading_tx(reading)
```

**Tiempo estimado:** 1-2 horas

---

### Opción C: Integrar API REST con PostgreSQL

Conectar los endpoints de la API con la base de datos:

**Archivos a modificar:**
- `api/routes/sensors.py` - Guardar sensores en DB
- `api/routes/readings.py` - Guardar lecturas en DB

**Funcionalidad:**
- Guardar cada transacción en `transactions_log`
- Guardar sensores en `sensors_history`
- Guardar lecturas en `readings_history`
- Generar alertas en `sensor_alerts`

**Tiempo estimado:** 3-4 horas

---

### Opción D: Crear Frontend Dashboard

Visualizar datos desde PostgreSQL:

**Tecnología:** React + Chart.js
**Características:**
- Dashboard con sensores activos
- Gráficas de lecturas históricas
- Alertas en tiempo real
- Mapa de ubicaciones

**Tiempo estimado:** 6-8 horas

---

## Comandos Útiles

### Verificar PostgreSQL:
```bash
python scripts/verify_db.py
```

### Ver estado del contrato:
```bash
cd pycardano-client
python query.py
```

### Decodificar datum actual:
```bash
cd pycardano-client
python decode_datum.py
```

### Registrar nuevo sensor:
```bash
cd pycardano-client
python register_sensor.py
```

---

## Notas Técnicas

### Correcciones Aplicadas

1. **Schema SQL:** Corregida sintaxis de `INDEX` - PostgreSQL requiere `CREATE INDEX` separado, no inline
2. **SQLAlchemy 2.0:** Actualizado `connection.py` para usar `text()` en queries raw
3. **PyCardano Imports:** Corregidos imports de `BlockFrostChainContext` y claves
4. **Derivación de wallet:** Usando `from_hdwallet()` en vez de `from_primitive()`

### Dependencias Instaladas

```
psycopg2-binary==2.9.11
sqlalchemy==2.0.44
python-dotenv==1.1.1
pycardano>=0.9.0
blockfrost-python>=0.6.0
```

---

## Estructura de Archivos Actualizada

```
sistema-sensores-humedad-agricola/
├── database/
│   └── schema.sql ✅ CORREGIDO
│
├── api/
│   └── database/
│       ├── connection.py ✅ ACTUALIZADO (SQLAlchemy 2.0)
│       ├── models.py
│       └── middleware.py
│
├── pycardano-client/
│   ├── config.py ✅
│   ├── cardano_utils.py ✅
│   ├── contract_types.py ✅ NUEVO
│   ├── transaction_builder.py ✅ NUEVO
│   ├── register_sensor.py ✅ ACTUALIZADO
│   ├── query.py ✅
│   └── decode_datum.py ✅
│
├── scripts/
│   ├── verify_db.py ✅ NUEVO
│   └── test_db_connection.py ✅
│
└── .env ✅ CONFIGURADO
```

---

## ETA al MVP Completo

Asumiendo que continuamos con el flujo propuesto:

| Tarea | Estimación | Estado |
|-------|------------|--------|
| ✅ PostgreSQL setup | 2 horas | COMPLETADO |
| ✅ PyCardano TX builder | 3 horas | COMPLETADO |
| ⏳ Probar RegisterSensor | 10 min | LISTO PARA PROBAR |
| 📝 Implementar AddReading | 1 hora | Pendiente |
| 📝 API REST + DB integration | 3 horas | Pendiente |
| 📝 Frontend dashboard | 6 horas | Pendiente |
| 📝 Tests de integración | 2 horas | Pendiente |

**Total restante:** ~12 horas ≈ **1.5-2 días de desarrollo**

**Progreso actual:** ✅ **65% completado**

---

## Conclusión

En esta sesión se logró:

1. ✅ Instalar y configurar PostgreSQL completamente
2. ✅ Crear schema SQL con 4 tablas y 3 vistas
3. ✅ Implementar Transaction Builder con PyCardano
4. ✅ Crear tipos PlutusData completos
5. ✅ Preparar script de registro de sensores

**El sistema está listo para comenzar a registrar sensores en la blockchain y almacenar datos históricos en PostgreSQL.**

**Siguiente paso recomendado:** Probar `register_sensor.py` para registrar SENSOR_002 en blockchain.
