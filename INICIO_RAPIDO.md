# Inicio Rápido del Proyecto

## ✅ El proyecto ya está configurado y listo para usar

### Forma 1: Usar el script de inicio (Recomendado)

**Si usas CMD (Command Prompt):**
```bash
start.bat
```

**Si usas PowerShell:**
```powershell
.\start.ps1
```

O también:
```powershell
.\start.bat
```

### Forma 2: Comando manual

```bash
# Activar entorno virtual
.venv\Scripts\activate

# Iniciar servidor
python -m uvicorn api.main:app --reload --port 8000
```

---

## 🌐 Acceder a la Aplicación

Una vez iniciado el servidor, abre tu navegador en:

### Dashboard Principal
```
http://localhost:8000/dashboard
```

Aquí puedes:
- Ver todos los sensores registrados
- Visualizar lecturas de humedad y temperatura en gráficos
- Registrar nuevos sensores

### API Documentation (Swagger)
```
http://localhost:8000/docs
```

Documentación interactiva de todos los endpoints disponibles.

### Health Check
```
http://localhost:8000/api/health
```

Verificar que la API esté funcionando correctamente.

---

## 📊 Datos Actuales del Sistema

El sistema ya tiene **4 sensores registrados** en blockchain:

1. **SENSOR_001** - Campo Norte - Parcela A
2. **SENSOR_002** - Test Zone
3. **SENSOR_003** - Campo Este - Parcela C
4. **SENSOR_004** - API Test Zone

Y múltiples lecturas de humedad/temperatura almacenadas.

---

## 🧪 Probar la API

### Listar todos los sensores
```bash
curl http://localhost:8000/api/sensors
```

### Listar lecturas
```bash
curl http://localhost:8000/api/readings?limit=10
```

### Registrar nuevo sensor
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

### Agregar lectura de humedad
```bash
curl -X POST http://localhost:8000/api/readings \
  -H "Content-Type: application/json" \
  -d '{
    "sensor_id": "SENSOR_001",
    "humidity_percentage": 58,
    "temperature_celsius": 24
  }'
```

---

## 🛠️ Configuración del Sistema

### Base de Datos
- **PostgreSQL**: Configurado en `.env`
- **URL**: `postgresql://sensor_app:change_this_password@localhost:5432/sensor_system`

### Blockchain
- **Red**: Cardano Preview Testnet
- **Smart Contract**: OpShin/Plutus V2
- **Persistencia Dual**: Blockchain + PostgreSQL

---

## 🔧 Solución de Problemas

### El servidor no inicia

**Verifica que el entorno virtual esté activado:**
```bash
.venv\Scripts\activate
```

**Reinstala dependencias si es necesario:**
```bash
pip install -r api/requirements.txt
pip install sqlalchemy psycopg2-binary pycardano blockfrost-python
```

### Error de conexión a base de datos

El sistema funciona **sin PostgreSQL** usando solo blockchain. Si no tienes PostgreSQL instalado, el sistema seguirá funcionando normalmente.

### Puerto 8000 ya en uso

Cambia el puerto en el comando:
```bash
python -m uvicorn api.main:app --reload --port 8001
```

---

## 📦 Dependencias Instaladas

- ✅ FastAPI 0.120.0
- ✅ Uvicorn 0.38.0
- ✅ Pydantic 2.12.3
- ✅ SQLAlchemy 2.0.44
- ✅ PyCardano 0.16.0
- ✅ BlockFrost-Python 0.6.0
- ✅ Python-dotenv 1.1.1

---

## 🎯 Próximos Pasos

1. **Explorar el Dashboard**: http://localhost:8000/dashboard
2. **Revisar la API**: http://localhost:8000/docs
3. **Probar endpoints** con curl o Postman
4. **Registrar nuevos sensores**
5. **Agregar lecturas de humedad**

---

## 🚀 Nuevas Funcionalidades

### Sistema de Alertas en Tiempo Real
El dashboard ahora incluye un **sistema de alertas** que detecta automáticamente lecturas fuera de rango:

```bash
# Ver alertas activas
curl http://localhost:8000/api/alerts/active

# Ver resumen de alertas
curl http://localhost:8000/api/alerts/summary
```

**Niveles de alerta:**
- 🟢 **Normal**: Dentro de umbrales
- 🟡 **Low/High**: Ligeramente fuera de rango
- 🔴 **Critical**: Requiere atención inmediata

### Sistema de Rollups con Merkle Hash (Nuevo!)
Reduce costos de blockchain en **96%** agrupando 24 lecturas diarias en un único hash merkle.

```bash
# Ver estadísticas de ahorro
curl http://localhost:8000/api/rollup/stats

# Procesar rollup manualmente
curl -X POST "http://localhost:8000/api/rollup/daily" \
     -H "Content-Type: application/json" \
     -d '{}'

# Verificar lectura con merkle proof
curl -X POST "http://localhost:8000/api/rollup/verify" \
     -H "Content-Type: application/json" \
     -d '{"reading_id": 123}'
```

**Ahorro estimado:** ~$2,250 USD/año con 4 sensores

📖 **Documentación completa:** [SISTEMA_ROLLUPS_MERKLE.md](SISTEMA_ROLLUPS_MERKLE.md)

### Auditoría Blockchain vs PostgreSQL
El dashboard incluye una pestaña de **Auditoría** que compara los datos en blockchain con PostgreSQL:

```bash
# Ver comparación de datos
curl http://localhost:8000/api/audit/compare?limit=20
```

---

## 📚 Documentación Completa

Para más detalles, consulta:
- [README.md](README.md) - Documentación completa del proyecto
- [SISTEMA_ROLLUPS_MERKLE.md](SISTEMA_ROLLUPS_MERKLE.md) - Sistema de rollups con merkle hash
- [COMO_PROBAR_ROLLUPS.md](COMO_PROBAR_ROLLUPS.md) - Guía de pruebas de rollups
- [PLAN_OPTIMIZACION_COSTOS.md](PLAN_OPTIMIZACION_COSTOS.md) - Plan de optimización de costos
- [GUIA_CONFIGURACION_CREDENCIALES.md](GUIA_CONFIGURACION_CREDENCIALES.md) - Configurar BlockFrost/Wallet

---

## 🎯 Roadmap de Desarrollo

### Completado ✅
- [x] API REST completa con FastAPI
- [x] Smart Contract OpShin en Cardano
- [x] Dashboard interactivo con Bootstrap 5
- [x] Persistencia dual (Blockchain + PostgreSQL)
- [x] Sistema de alertas en tiempo real
- [x] Auditoría blockchain vs base de datos
- [x] Sistema de rollups con merkle hash

### En Desarrollo 🚧
- [ ] Scheduler automático de rollups (requiere APScheduler)
- [ ] Migración de base de datos para rollup_batch_id
- [ ] Integración de rollups con blockchain real

### Próximas Mejoras 📋
- [ ] Dashboard de rollups con visualización de ahorros
- [ ] Notificaciones de alertas (email/webhook)
- [ ] Exportación de datos a CSV/Excel
- [ ] Gráficos históricos de lecturas
- [ ] API de predicción de humedad con ML
- [ ] Integración con hardware físico (Arduino/ESP32)

---

**¡El sistema está 100% funcional y listo para usar!**

Última actualización: 2025-11-10
