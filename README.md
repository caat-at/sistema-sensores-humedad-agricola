# Sistema de Monitoreo de Sensores de Humedad Agrícola

## Blockchain Cardano + API REST + Dashboard Interactivo

Sistema completo de monitoreo de sensores de humedad para agricultura con smart contracts en Cardano (OpShin/Plutus V2), API REST con FastAPI, persistencia dual (blockchain + PostgreSQL) y dashboard web interactivo.

![Python](https://img.shields.io/badge/python-3.11-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104-green)
![Cardano](https://img.shields.io/badge/Cardano-Preview-orange)
![OpShin](https://img.shields.io/badge/OpShin-0.26-purple)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-blue)

---

## Estado del Proyecto

**COMPLETAMENTE FUNCIONAL**

- Smart contract OpShin compilado a Plutus V2
- API REST con 4 endpoints principales
- Dashboard web interactivo con 3 pestañas
- Persistencia dual: Blockchain + PostgreSQL
- Cliente PyCardano para transacciones
- Sistema de deduplicación de sensores
- Visualización con gráficos Chart.js

---

## Quick Start

### 1. Clonar Repositorio

```bash
git clone https://github.com/TU-USUARIO/sistema-sensores-humedad-agricola.git
cd sistema-sensores-humedad-agricola
```

### 2. Instalar Dependencias

```bash
# Crear entorno virtual
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# Instalar dependencias
pip install -r requirements.txt
```

### 3. Configurar Variables de Entorno

```bash
# Copiar plantilla
cp .env.example .env

# Editar .env con tus credenciales
# - BLOCKFROST_PROJECT_ID
# - SEED_PHRASE (24 palabras)
# - NETWORK (preview o preprod)
# - DATABASE_URL (opcional)
```

### 4. Configurar Base de Datos (Opcional)

```bash
# Instalar PostgreSQL 15+
# Ver: https://www.postgresql.org/download/

# Crear base de datos
psql -U postgres
CREATE DATABASE humidity_sensors;
\c humidity_sensors
\i database/schema.sql
\q
```

### 5. Iniciar API + Dashboard

```bash
python -m uvicorn api.main:app --reload --port 8000
```

Dashboard disponible en: **http://localhost:8000/dashboard**

API docs en: **http://localhost:8000/docs**

---

## Arquitectura

```
┌─────────────────────────────────────────────────────────────┐
│                     FRONTEND DASHBOARD                       │
│              Bootstrap 5 + Chart.js + Vanilla JS            │
│   [Sensores] [Lecturas por Sensor] [Registrar Sensor]      │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP Requests
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                      API REST (FastAPI)                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ GET /sensors │  │ POST /sensors│  │ GET /readings│      │
│  │ GET /readings│  │POST /readings│  │ GET /health  │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└───────────┬────────────────────────────────┬────────────────┘
            │                                │
            ▼                                ▼
┌──────────────────────┐         ┌─────────────────────────┐
│  Blockchain Service  │         │   PostgreSQL Database   │
│    (PyCardano)       │         │  (Persistencia local)   │
└──────────┬───────────┘         └─────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────────┐
│              CARDANO PREVIEW TESTNET                         │
│  ┌────────────────────────────────────────────────┐         │
│  │    Smart Contract OpShin (Plutus V2)           │         │
│  │  addr_test1wz873sjp5wenffd4x8jusc94kek42...    │         │
│  │                                                 │         │
│  │  Datum: {                                       │         │
│  │    sensors: List[SensorConfig]                 │         │
│  │    readings: List[HumidityReading]             │         │
│  │    admin: PubKeyHash                            │         │
│  │  }                                              │         │
│  └────────────────────────────────────────────────┘         │
└─────────────────────────────────────────────────────────────┘
```

---

## Estructura del Proyecto

```
sistema-sensores-humedad-agricola/
│
├── api/                              # API REST con FastAPI
│   ├── main.py                       # Servidor principal + rutas dashboard
│   ├── routers/
│   │   ├── sensors.py               # Endpoints de sensores
│   │   └── readings.py              # Endpoints de lecturas
│   ├── services/
│   │   └── blockchain_service.py    # Servicio de blockchain (PyCardano)
│   ├── models/
│   │   ├── sensor.py                # Modelos Pydantic para sensores
│   │   └── reading.py               # Modelos Pydantic para lecturas
│   └── schemas/
│       └── response.py              # Esquemas de respuesta API
│
├── contracts/                        # Smart Contracts
│   └── opshin/
│       ├── humidity_sensor.py       # Contrato OpShin (Python)
│       └── build/
│           └── humidity_sensor/
│               ├── script.plutus    # Plutus V2 compilado
│               ├── blueprint.json   # CIP-57
│               └── testnet.addr     # Dirección del contrato
│
├── database/                         # PostgreSQL
│   ├── schema.sql                   # Esquema de base de datos
│   └── db_manager.py                # Gestor de conexiones y queries
│
├── frontend/                         # Dashboard Web
│   └── dashboard/
│       └── index.html               # Dashboard interactivo (Bootstrap 5 + Chart.js)
│
├── pycardano-client/                # Cliente Blockchain
│   ├── config.py                    # Configuración de red Cardano
│   ├── tx_builder.py                # Constructor de transacciones
│   ├── models.py                    # Modelos de datos (Sensor, Reading, Datum)
│   ├── utils.py                     # Utilidades (alertas, timestamps)
│   └── test_tx_builder.py           # Tests
│
├── scripts/                          # Scripts de utilidad
│   └── test_api.py                  # Tests de API REST
│
├── .env.example                      # Plantilla de variables de entorno
├── .gitignore                        # Exclusiones de Git
├── requirements.txt                  # Dependencias Python
├── README.md                         # Este archivo
└── DEPLOY_GITHUB.md                 # Guía de despliegue en GitHub
```

---

## Funcionalidades

### API REST

#### Endpoints de Sensores

**GET /api/sensors**
- Lista todos los sensores registrados
- Deduplicación automática (prefiere Active sobre Inactive, más reciente)
- Response: `List[SensorResponse]`

**POST /api/sensors**
- Registra un nuevo sensor en blockchain
- Genera `sensor_id` automáticamente si no se proporciona
- Guarda en PostgreSQL (si está configurado)
- Request body:
  ```json
  {
    "sensor_id": "SENSOR_005",
    "location": {
      "latitude": -34.58,
      "longitude": -58.45,
      "zone_name": "Campo Norte"
    },
    "min_humidity_threshold": 30,
    "max_humidity_threshold": 70,
    "reading_interval_minutes": 60
  }
  ```
- Response: `TransactionResponse` con `tx_hash`

#### Endpoints de Lecturas

**GET /api/readings**
- Lista lecturas de humedad
- Parámetros opcionales: `sensor_id`, `limit`
- Response: `List[ReadingResponse]`

**POST /api/readings**
- Agrega lectura de humedad/temperatura
- Guarda en blockchain + PostgreSQL
- Request body:
  ```json
  {
    "sensor_id": "SENSOR_001",
    "humidity_percentage": 55,
    "temperature_celsius": 23
  }
  ```
- Response: `TransactionResponse` con `tx_hash`

### Dashboard Interactivo

Accede en: `http://localhost:8000/dashboard`

#### Pestaña 1: Sensores

Tabla detallada con:
- ID del sensor
- Zona/Ubicación
- Coordenadas (latitud, longitud)
- Umbrales de humedad (min-max %)
- Intervalo de lectura (minutos)
- Estado (Active/Inactive)
- **Fecha de Instalación** (formato español)
- Owner (hash abreviado)

#### Pestaña 2: Lecturas por Sensor

- Dropdown para filtrar por sensor específico
- Gráfico Chart.js con dos datasets:
  - Línea azul: Humedad (%)
  - Línea roja: Temperatura (°C)
- Tabla de lecturas recientes con:
  - Sensor ID
  - Humedad (%)
  - Temperatura (°C)
  - Fecha/hora
  - Nivel de alerta (badge con color)

#### Pestaña 3: Registrar Sensor

Formulario para registrar nuevos sensores con validación en tiempo real.

### Smart Contract (OpShin/Plutus V2)

**Dirección Testnet:**
```
addr_test1wz873sjp5wenffd4x8jusc94kek42w4mwpuevnagkzkwsqg0j0aty
```

**Operaciones Soportadas:**

1. **RegisterSensor** - Registrar nuevo sensor
2. **UpdateSensorConfig** - Actualizar configuración
3. **DeactivateSensor** - Desactivar sensor
4. **AddReading** - Agregar lectura de humedad/temperatura
5. **AddMultipleReadings** - Batch de lecturas
6. **UpdateAdmin** - Cambiar administrador
7. **SetMaintenanceMode** - Modo mantenimiento
8. **EmergencyStop** - Detención de emergencia

**Validaciones On-Chain:**

- Máximo 100 sensores por contrato
- Humedad: 0-100%
- Temperatura: -30°C a 60°C
- Solo admin puede modificar configuraciones críticas
- Sensor debe existir para agregar lecturas

### Niveles de Alerta

| Nivel | Rango | Badge | Acción |
|-------|-------|-------|--------|
| **Normal** | 40-70% | Verde | Ninguna |
| **Low** | < 40% | Amarillo | Riego recomendado |
| **High** | > 70% | Naranja | Riesgo de hongos |
| **Critical** | < 20% o > 85% | Rojo | Acción inmediata |

---

## Tecnologías

### Backend
- **FastAPI** 0.104+ - Framework web moderno y rápido
- **PyCardano** 0.11+ - Biblioteca Python para Cardano
- **OpShin** 0.26+ - Smart contracts en Python
- **Pydantic** 2.0+ - Validación de datos
- **Uvicorn** - Servidor ASGI

### Blockchain
- **Cardano** Preview Testnet
- **Plutus V2** - Smart contract runtime
- **BlockFrost API** - Acceso a blockchain
- **CIP-57** - Plutus Blueprints

### Base de Datos
- **PostgreSQL** 15+
- **psycopg2** - Driver PostgreSQL para Python

### Frontend
- **Bootstrap 5.3** - Framework CSS
- **Chart.js 4.4** - Gráficos interactivos
- **Font Awesome 6.5** - Iconos
- **Vanilla JavaScript** - Sin dependencias pesadas

---

## Configuración Detallada

### Variables de Entorno (.env)

```bash
# Blockchain
BLOCKFROST_PROJECT_ID=previewXXXXXXXXXXXXXXXXXX
NETWORK=preview  # o preprod
SEED_PHRASE=word1 word2 word3 ... word24

# Base de Datos (Opcional)
DATABASE_URL=postgresql://postgres:password@localhost:5432/humidity_sensors

# Smart Contract
SCRIPT_ADDRESS=addr_test1wz873sjp5wenffd4x8jusc94kek42w4mwpuevnagkzkwsqg0j0aty
PLUTUS_SCRIPT_PATH=contracts/opshin/build/humidity_sensor/script.plutus
```

### Compilar Smart Contract

```bash
cd contracts/opshin
python -m opshin build spending humidity_sensor.py
```

Esto genera:
- `build/humidity_sensor/script.plutus` - Contrato compilado
- `build/humidity_sensor/blueprint.json` - Metadatos CIP-57
- `build/humidity_sensor/testnet.addr` - Dirección del contrato

---

## Uso

### 1. Iniciar Servidor

```bash
python -m uvicorn api.main:app --reload --port 8000
```

### 2. Verificar Salud de API

```bash
curl http://localhost:8000/api/health
```

Response:
```json
{
  "status": "healthy",
  "timestamp": "2025-10-21T15:30:00",
  "blockchain": "connected",
  "database": "connected"
}
```

### 3. Listar Sensores

```bash
curl http://localhost:8000/api/sensors
```

### 4. Registrar Sensor

```bash
curl -X POST http://localhost:8000/api/sensors \
  -H "Content-Type: application/json" \
  -d '{
    "sensor_id": "SENSOR_005",
    "location": {
      "latitude": -34.62,
      "longitude": -58.50,
      "zone_name": "Parcela Sur"
    },
    "min_humidity_threshold": 35,
    "max_humidity_threshold": 75,
    "reading_interval_minutes": 90
  }'
```

Response:
```json
{
  "success": true,
  "tx_hash": "a1b2c3d4e5f6...",
  "message": "Sensor SENSOR_005 registrado exitosamente",
  "sensor_id": "SENSOR_005",
  "timestamp": "2025-10-21T15:45:00"
}
```

### 5. Agregar Lectura

```bash
curl -X POST http://localhost:8000/api/readings \
  -H "Content-Type: application/json" \
  -d '{
    "sensor_id": "SENSOR_005",
    "humidity_percentage": 58,
    "temperature_celsius": 24
  }'
```

### 6. Filtrar Lecturas por Sensor

```bash
curl "http://localhost:8000/api/readings?sensor_id=SENSOR_005&limit=10"
```

### 7. Acceder al Dashboard

Abre en navegador: `http://localhost:8000/dashboard`

---

## Tests

### Test de Transaction Builder

```bash
cd pycardano-client
python test_tx_builder.py
```

### Test de API

```bash
python scripts/test_api.py
```

### Test Manual con cURL

```bash
# Listar sensores
curl http://localhost:8000/api/sensors | python -m json.tool

# Listar lecturas
curl http://localhost:8000/api/readings?limit=5 | python -m json.tool
```

---

## Base de Datos PostgreSQL

### Tablas

#### sensors_history

Almacena historial completo de todos los estados de sensores.

```sql
CREATE TABLE sensors_history (
    id SERIAL PRIMARY KEY,
    sensor_id VARCHAR(50) NOT NULL,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    zone_name VARCHAR(100),
    min_humidity_threshold INTEGER,
    max_humidity_threshold INTEGER,
    reading_interval_minutes INTEGER,
    status VARCHAR(20),
    owner VARCHAR(64),
    installed_date TIMESTAMP,
    tx_hash VARCHAR(64),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### readings_history

Almacena todas las lecturas de humedad/temperatura.

```sql
CREATE TABLE readings_history (
    id SERIAL PRIMARY KEY,
    sensor_id VARCHAR(50) NOT NULL,
    humidity_percentage INTEGER NOT NULL,
    temperature_celsius INTEGER NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    alert_level VARCHAR(20),
    tx_hash VARCHAR(64),
    on_chain BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Consultas Útiles

```sql
-- Ver sensores activos
SELECT sensor_id, zone_name, status
FROM sensors_history
WHERE status = 'Active'
ORDER BY updated_at DESC;

-- Ver lecturas recientes
SELECT sensor_id, humidity_percentage, temperature_celsius, timestamp
FROM readings_history
WHERE on_chain = TRUE
ORDER BY timestamp DESC
LIMIT 10;

-- Promedio de humedad por sensor
SELECT sensor_id,
       AVG(humidity_percentage) as avg_humidity,
       COUNT(*) as total_readings
FROM readings_history
WHERE timestamp > NOW() - INTERVAL '24 hours'
GROUP BY sensor_id;
```

---

## Persistencia Dual: Blockchain + Base de Datos

Este sistema implementa **doble persistencia** para combinar las ventajas de ambos mundos:

### Blockchain (Cardano)
- **Inmutabilidad**: Los datos nunca pueden ser alterados
- **Transparencia**: Auditoría pública de todas las operaciones
- **Descentralización**: No depende de un servidor central
- **Trazabilidad**: Cada transacción tiene un hash único

### PostgreSQL
- **Velocidad**: Consultas rápidas sin esperar confirmaciones blockchain
- **Flexibilidad**: Queries complejas, joins, agregaciones
- **Reportes**: Generación de informes y análisis histórico
- **Disponibilidad**: No requiere conexión a blockchain para consultas

### Flujo de Datos

1. **Escritura** (POST):
   - Datos → API → Blockchain (transacción)
   - Blockchain confirma → Guardar en PostgreSQL con tx_hash
   - Response con tx_hash al cliente

2. **Lectura** (GET):
   - Opción A: Leer desde blockchain (fuente de verdad)
   - Opción B: Leer desde PostgreSQL (más rápido)
   - Dashboard usa principalmente blockchain para garantizar datos actualizados

---

## Sistema de Deduplicación de Sensores

El sistema maneja automáticamente duplicados de sensores en el datum blockchain:

### Estrategia

Cuando hay múltiples entradas del mismo `sensor_id`:

1. **Prioridad por Estado:**
   - `Active` tiene preferencia sobre `Inactive`

2. **Prioridad por Fecha:**
   - Si tienen el mismo estado, se prefiere el más reciente (`installed_date`)

### Código

```python
def deduplicate_sensors(self, sensors):
    sensors_dict = {}
    for sensor in sensors:
        sensor_id = sensor.sensor_id.decode('utf-8', errors='ignore')
        is_active = type(sensor.status).__name__ == 'Active'

        if sensor_id not in sensors_dict:
            sensors_dict[sensor_id] = (sensor, is_active)
        else:
            existing_sensor, existing_is_active = sensors_dict[sensor_id]

            # Preferir Active sobre Inactive
            if is_active and not existing_is_active:
                sensors_dict[sensor_id] = (sensor, is_active)
            elif is_active == existing_is_active:
                # Mismo estado, preferir más reciente
                if sensor.installed_date > existing_sensor.installed_date:
                    sensors_dict[sensor_id] = (sensor, is_active)

    return [sensor for sensor, _ in sensors_dict.values()]
```

---

## Seguridad

### Smart Contract
- Validaciones on-chain de todos los parámetros
- Solo admin puede modificar configuraciones críticas
- Límite de 100 sensores para prevenir ataques DoS
- Rangos validados (humedad 0-100%, temperatura -30 a 60°C)

### API
- Validación de datos con Pydantic
- Sanitización de inputs
- Rate limiting (recomendado para producción)

### Credenciales
- `.env` nunca se versiona (está en .gitignore)
- Seed phrases y claves privadas nunca se exponen
- Personal Access Tokens para GitHub

### Base de Datos
- Conexiones con autenticación
- Queries parametrizadas (prevención SQL injection)
- Índices para optimización

---

## Roadmap

- [x] Smart contract en OpShin/Plutus V2
- [x] Cliente PyCardano funcional
- [x] API REST con FastAPI
- [x] Persistencia dual (Blockchain + PostgreSQL)
- [x] Dashboard web interactivo
- [x] Gráficos con Chart.js
- [x] Sistema de deduplicación
- [ ] Sistema de alertas por email/SMS
- [ ] Autenticación JWT en API
- [ ] Exportación de reportes (CSV/PDF)
- [ ] Integración con dispositivos IoT reales
- [ ] Mapas interactivos (Leaflet.js)
- [ ] Auto-refresh del dashboard
- [ ] Tests end-to-end automatizados
- [ ] CI/CD con GitHub Actions
- [ ] Deploy en producción (Mainnet)

---

## Solución de Problemas

### Error: "BabbageOutputTooSmallUTxO"

**Solución:** Aumentar el ADA enviado al script. El mínimo es ~1.2 ADA.

```python
# En tx_builder.py
value_to_script = Value(
    coin=2_000_000  # 2 ADA (antes era 1 ADA)
)
```

### Error: "UTxO no encontrado"

**Causa:** No hay fondos en el contrato.

**Solución:**
1. Verificar dirección del contrato en Cardano Explorer
2. Enviar tADA desde faucet
3. Esperar confirmación (1-2 minutos)

### Error: "Database connection failed"

**Solución:**
1. Verificar que PostgreSQL esté corriendo: `pg_ctl status`
2. Revisar credenciales en `.env`
3. Probar conexión: `psql -U postgres -d humidity_sensors`

### Error: "BlockFrost 403 Forbidden"

**Causa:** Project ID inválido o límite de requests excedido.

**Solución:**
1. Verificar `BLOCKFROST_PROJECT_ID` en `.env`
2. Revisar cuota en https://blockfrost.io/dashboard
3. Esperar reset de cuota (plan gratis: 50K requests/día)

### Dashboard no carga datos

**Solución:**
1. Verificar que API esté corriendo: `curl http://localhost:8000/api/health`
2. Abrir consola del navegador (F12) para ver errores JavaScript
3. Verificar CORS si usas dominio diferente

---

## Documentación Adicional

- [DEPLOY_GITHUB.md](DEPLOY_GITHUB.md) - Guía paso a paso para subir a GitHub
- [contracts/opshin/humidity_sensor.py](contracts/opshin/humidity_sensor.py) - Código fuente del contrato comentado
- [api/README.md](api/README.md) - Documentación específica de la API
- [pycardano-client/README.md](pycardano-client/README.md) - Guía del cliente blockchain

---

## Contribuir

¡Las contribuciones son bienvenidas!

1. Fork el proyecto
2. Crea una rama feature (`git checkout -b feature/MejoraMaestra`)
3. Commit tus cambios (`git commit -m 'feat: Agregar funcionalidad X'`)
4. Push a la rama (`git push origin feature/MejoraMaestra`)
5. Abre un Pull Request

### Convención de Commits

Usamos [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` Nueva funcionalidad
- `fix:` Corrección de bug
- `docs:` Cambios en documentación
- `style:` Formato, espacios, etc.
- `refactor:` Refactorización de código
- `test:` Agregar tests
- `chore:` Tareas de mantenimiento

---

## Licencia

Apache-2.0 License

---

## Autor

**Carlos Aristizabal**
- Ingeniero de Sistemas
- Desarrollador Blockchain
- Especialista en Cardano

---

## Enlaces Útiles

### Documentación Oficial
- [OpShin Documentation](https://opshin.dev/)
- [PyCardano Docs](https://pycardano.readthedocs.io/)
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [Cardano Developer Portal](https://developers.cardano.org/)
- [Plutus Documentation](https://plutus.readthedocs.io/)

### Herramientas
- [BlockFrost API](https://blockfrost.io/)
- [Cardano Explorer (Preview)](https://preview.cardanoscan.io/)
- [Cardano Testnet Faucet](https://docs.cardano.org/cardano-testnet/tools/faucet/)

### Estándares
- [CIP-57 (Plutus Blueprints)](https://cips.cardano.org/cip/CIP-0057)
- [CIP-30 (dApp Connector)](https://cips.cardano.org/cip/CIP-0030)

### Comunidad
- [Cardano Forum](https://forum.cardano.org/)
- [Cardano Stack Exchange](https://cardano.stackexchange.com/)
- [IOG Discord](https://discord.gg/inputoutput)

---

**Implementación completamente funcional con persistencia dual blockchain + base de datos!**

**Ideal para agricultura de precisión, monitoreo ambiental y trazabilidad alimentaria.**
