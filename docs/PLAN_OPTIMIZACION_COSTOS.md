# 💰 Plan de Optimización de Costos Blockchain

## 📊 Análisis de Situación Actual

### Arquitectura Actual
- **Modelo**: 1 Transacción por Lectura (1:1)
- **Frecuencia**: 1 lectura cada 60-120 minutos por sensor
- **Sensores activos**: 4 sensores
- **Costo por transacción**: ~0.17 ADA

### Proyección de Costos Actuales

```
Escenario: 4 sensores, 1 lectura/hora cada uno

├─ Por Hora:    4 sensores × 1 lectura   = 4 tx    → ~0.68 ADA/hora
├─ Por Día:     4 × 24                    = 96 tx   → ~16.32 ADA/día
├─ Por Mes:     96 × 30                   = 2,880 tx → ~489.60 ADA/mes
└─ Por Año:     2,880 × 12                = 34,560 tx → ~5,875.20 ADA/año

💸 Costo Anual Estimado: ~5,875 ADA (~$2,350 USD a $0.40/ADA)
```

---

## 🎯 Estrategia de Optimización: Batch Transactions

### Concepto
Agrupar múltiples lecturas en una sola transacción blockchain, manteniendo cada lectura individual en PostgreSQL para consultas rápidas.

### Arquitectura Propuesta

```
┌─────────────────────────────────────────────────────────────┐
│                    FLUJO OPTIMIZADO                          │
└─────────────────────────────────────────────────────────────┘

1. RECEPCIÓN DE LECTURA
   └─> API recibe lectura del sensor
       └─> Guarda en PostgreSQL (on_chain=False)
       └─> Agrega a cola de batch

2. COLA DE BATCH (En memoria o Redis)
   └─> Acumula lecturas hasta:
       - Alcanzar tamaño de batch (10-20 lecturas)
       - Timeout (15-30 minutos)
       - Alerta crítica detectada (flush inmediato)

3. PROCESAMIENTO DE BATCH
   └─> Scheduler ejecuta cada 15-30 min
       └─> Toma todas las lecturas pendientes
       └─> Crea UNA transacción blockchain con todas
       └─> Marca lecturas como on_chain=True

4. MANEJO DE ALERTAS CRÍTICAS
   └─> Si lectura es Critical:
       └─> Envía inmediatamente a blockchain (bypass batch)
       └─> Garantiza registro rápido de eventos importantes
```

---

## 💡 Modelo Híbrido Propuesto

### Estrategia 1: Batch Completo (Máximo Ahorro)
- **Todas las lecturas en batches** de 20 lecturas
- **Scheduler**: Cada 30 minutos
- **Ahorro**: 95%

```
Costos con Batch de 20 lecturas:

├─ Lecturas por día:     96
├─ Batch size:           20
├─ Transacciones/día:    96 ÷ 20 = 5 tx
├─ Costo por día:        5 × 0.17 = ~0.85 ADA/día
├─ Costo por mes:        ~25.50 ADA/mes
└─ Costo por año:        ~306 ADA/año

💰 AHORRO ANUAL: ~5,569 ADA (95%)
```

### Estrategia 2: Híbrido (Balance Ahorro/Tiempo Real)
- **Lecturas normales**: Batches de 10 cada 15 min
- **Alertas críticas**: Inmediato (individual)
- **Ahorro**: 85-90%

```
Costos Híbridos (90% en batch, 10% inmediato):

├─ Lecturas normales/día:  86 (90%)
├─ Lecturas críticas/día:  10 (10%)
│
├─ Batch size:            10 lecturas
├─ Tx de batches/día:     86 ÷ 10 = 9 tx
├─ Tx críticas/día:       10 tx
├─ Total tx/día:          19 tx
│
├─ Costo por día:         19 × 0.17 = ~3.23 ADA/día
├─ Costo por mes:         ~96.90 ADA/mes
└─ Costo por año:         ~1,162.80 ADA/año

💰 AHORRO ANUAL: ~4,712 ADA (80%)
```

### Estrategia 3: Time-Based Rollup (Óptimo)
- **Cada hora**: Agrupa todas las lecturas de esa hora
- **Metadata en blockchain**: Hash merkle de todas las lecturas
- **Datos completos**: PostgreSQL
- **Ahorro**: 96%

```
Costos con Rollup Horario:

├─ Transacciones/día:     24 (una por hora)
├─ Costo por día:         24 × 0.17 = ~4.08 ADA/día
├─ Costo por mes:         ~122.40 ADA/mes
└─ Costo por año:         ~1,469 ADA/año

💰 AHORRO ANUAL: ~4,406 ADA (75%)
```

---

## 🏗️ Plan de Implementación

### Fase 1: Infraestructura Base (2-3 horas)
**Objetivo**: Preparar el sistema para batch transactions

#### 1.1 Crear Tabla de Cola de Batches
```sql
CREATE TABLE batch_queue (
    id SERIAL PRIMARY KEY,
    reading_id INTEGER REFERENCES readings_history(id),
    added_at TIMESTAMP DEFAULT NOW(),
    processed BOOLEAN DEFAULT FALSE,
    batch_id UUID,
    processed_at TIMESTAMP
);

CREATE INDEX idx_batch_queue_unprocessed
ON batch_queue(processed) WHERE processed = FALSE;
```

#### 1.2 Modificar Endpoint de Lecturas
```python
# api/routers/readings.py

@router.post("/batch")
async def add_reading_to_batch(
    reading_data: ReadingCreate,
    db: Session = Depends(get_db)
):
    """
    Agrega lectura a PostgreSQL y cola de batch
    (NO envía a blockchain inmediatamente)
    """
    # 1. Guardar en PostgreSQL (on_chain=False)
    reading = ReadingHistory(
        sensor_id=reading_data.sensor_id,
        humidity_percentage=reading_data.humidity_percentage,
        temperature_celsius=reading_data.temperature_celsius,
        timestamp=datetime.now(),
        on_chain=False  # ← No está en blockchain aún
    )
    db.add(reading)
    db.commit()

    # 2. Calcular nivel de alerta
    alert_level = calculate_alert_level(...)

    # 3. Si es crítica, enviar inmediato
    if alert_level == "Critical":
        return await send_immediate_to_blockchain(reading)

    # 4. Agregar a cola de batch
    batch_item = BatchQueue(reading_id=reading.id)
    db.add(batch_item)
    db.commit()

    return {
        "success": True,
        "reading_id": reading.id,
        "queued_for_batch": True,
        "alert_level": alert_level
    }
```

#### 1.3 Crear Servicio de Batch Processor
```python
# api/services/batch_processor.py

class BatchProcessor:
    def __init__(self, batch_size=10, timeout_minutes=15):
        self.batch_size = batch_size
        self.timeout = timeout_minutes

    async def process_pending_batches(self):
        """
        Procesa todas las lecturas pendientes en batches
        """
        db = SessionLocal()

        # Obtener lecturas pendientes
        pending = db.query(BatchQueue).filter(
            BatchQueue.processed == False
        ).order_by(BatchQueue.added_at).all()

        if len(pending) == 0:
            return {"batches_processed": 0}

        # Dividir en batches
        batches = [
            pending[i:i + self.batch_size]
            for i in range(0, len(pending), self.batch_size)
        ]

        results = []
        for batch in batches:
            tx_hash = await self._send_batch_to_blockchain(batch)
            results.append({
                "batch_id": str(uuid.uuid4()),
                "readings_count": len(batch),
                "tx_hash": tx_hash
            })

        return {
            "batches_processed": len(batches),
            "total_readings": len(pending),
            "results": results
        }

    async def _send_batch_to_blockchain(self, batch_items):
        """
        Envía un batch de lecturas a blockchain
        """
        # Obtener datos de lecturas
        readings = []
        for item in batch_items:
            reading = db.query(ReadingHistory).get(item.reading_id)
            readings.append(reading)

        # Construir transacción con múltiples lecturas
        blockchain_service = BlockchainService()
        tx_hash = await blockchain_service.submit_batch_readings(readings)

        # Marcar lecturas como procesadas
        for item in batch_items:
            item.processed = True
            item.batch_id = batch_id
            item.processed_at = datetime.now()

            # Actualizar reading como on_chain=True
            reading = db.query(ReadingHistory).get(item.reading_id)
            reading.on_chain = True
            reading.tx_hash = tx_hash

        db.commit()
        return tx_hash
```

---

### Fase 2: Scheduler Automático (1 hora)

#### 2.1 Scheduler con APScheduler
```python
# api/scheduler.py

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from api.services.batch_processor import BatchProcessor

scheduler = AsyncIOScheduler()
processor = BatchProcessor(batch_size=10, timeout_minutes=15)

@scheduler.scheduled_job('interval', minutes=15)
async def process_batches():
    """
    Ejecuta cada 15 minutos
    """
    print(f"[{datetime.now()}] Procesando batches...")
    result = await processor.process_pending_batches()
    print(f"  ✓ {result['batches_processed']} batches procesados")
    print(f"  ✓ {result['total_readings']} lecturas enviadas")

def start_scheduler():
    scheduler.start()
    print("[OK] Scheduler de batches iniciado (cada 15 min)")
```

#### 2.2 Integrar en main.py
```python
# api/main.py

from api.scheduler import start_scheduler

@app.on_event("startup")
async def startup_event():
    """Inicia scheduler al arrancar el servidor"""
    start_scheduler()
```

---

### Fase 3: Modificar Smart Contract (2-3 horas)

#### 3.1 Actualizar Datum para Batches
```python
# contracts/opshin/humidity_sensor.py

@dataclass
class BatchReading:
    sensor_id: bytes
    humidity: int
    temperature: int
    timestamp: int
    alert_level: AlertLevel

@dataclass
class SensorDatum:
    # ... campos existentes ...
    batch_readings: List[BatchReading]  # ← Nueva: lista de lecturas
    batch_count: int                     # ← Nuevo: contador de batches
```

#### 3.2 Validador para Batches
```python
def validator(datum: SensorDatum, redeemer: SensorAction, ctx: ScriptContext):

    if isinstance(redeemer, AddBatchReadings):
        # Validar que todas las lecturas son válidas
        for reading in redeemer.readings:
            assert 0 <= reading.humidity <= 100
            assert -50 <= reading.temperature <= 100

        # Actualizar datum con nuevas lecturas
        new_datum = datum.copy()
        new_datum.batch_readings.extend(redeemer.readings)
        new_datum.batch_count += 1

        # Validar output
        assert ctx.tx_info.outputs[0].datum == new_datum
```

---

### Fase 4: Dashboard y Monitoreo (1 hora)

#### 4.1 Endpoint de Estado de Batches
```python
@router.get("/batch/status")
async def get_batch_status(db: Session = Depends(get_db)):
    """
    Muestra estado actual de la cola de batches
    """
    pending_count = db.query(BatchQueue).filter(
        BatchQueue.processed == False
    ).count()

    oldest_pending = db.query(BatchQueue).filter(
        BatchQueue.processed == False
    ).order_by(BatchQueue.added_at).first()

    last_batch = db.query(BatchQueue).filter(
        BatchQueue.processed == True
    ).order_by(BatchQueue.processed_at.desc()).first()

    return {
        "pending_readings": pending_count,
        "next_batch_in": calculate_time_to_next_batch(),
        "oldest_pending_age": (
            datetime.now() - oldest_pending.added_at
        ).seconds if oldest_pending else 0,
        "last_batch": {
            "processed_at": last_batch.processed_at,
            "batch_id": last_batch.batch_id
        } if last_batch else None
    }
```

#### 4.2 Agregar Panel en Dashboard
```html
<!-- Panel de Estado de Batches -->
<div class="card mb-3">
    <div class="card-header">
        <h5>📦 Estado de Batches</h5>
    </div>
    <div class="card-body">
        <div class="row">
            <div class="col-md-3">
                <h4 id="pendingReadings">0</h4>
                <small>Lecturas Pendientes</small>
            </div>
            <div class="col-md-3">
                <h4 id="nextBatchIn">--</h4>
                <small>Próximo Batch En</small>
            </div>
            <div class="col-md-3">
                <h4 id="batchSavings">0%</h4>
                <small>Ahorro vs Individual</small>
            </div>
            <div class="col-md-3">
                <button class="btn btn-warning" onclick="flushBatchNow()">
                    Procesar Ahora
                </button>
            </div>
        </div>
    </div>
</div>
```

---

## 📈 Comparativa de Estrategias

| Estrategia | Tx/Día | Costo/Mes | Ahorro | Latencia | Complejidad |
|-----------|--------|-----------|--------|----------|-------------|
| **Actual** | 96 | 490 ADA | 0% | Inmediata | Baja |
| **Batch 20** | 5 | 26 ADA | 95% | 30 min | Media |
| **Híbrido** | 19 | 97 ADA | 80% | 0-15 min | Media |
| **Rollup** | 24 | 122 ADA | 75% | 60 min | Alta |

---

## ✅ Recomendación Final

### **Estrategia Híbrida (Opción 2)**

#### Por qué:
✅ **Balance óptimo** entre ahorro (80%) y tiempo real
✅ **Alertas críticas inmediatas** (sin delay)
✅ **Complejidad moderada** (implementación 6-8 horas)
✅ **Flexible** (fácil ajustar batch_size y timeout)
✅ **Compatible** con sistema actual

#### Configuración Recomendada:
```python
BATCH_CONFIG = {
    "batch_size": 10,           # Agrupar cada 10 lecturas
    "timeout_minutes": 15,      # O cada 15 minutos
    "critical_bypass": True,    # Alertas críticas → inmediato
    "scheduler_interval": 15    # Revisar cada 15 min
}
```

#### ROI (Return on Investment):
- **Tiempo de implementación**: 6-8 horas
- **Ahorro mensual**: ~393 ADA (~$157 USD)
- **Ahorro anual**: ~4,712 ADA (~$1,885 USD)
- **Recuperación**: Inmediata

---

## 📋 Checklist de Implementación

### Preparación
- [ ] Backup de base de datos actual
- [ ] Backup de contratos actuales
- [ ] Documentar arquitectura actual
- [ ] Crear branch `feature/batch-optimization`

### Base de Datos
- [ ] Crear tabla `batch_queue`
- [ ] Crear índices necesarios
- [ ] Modificar campo `on_chain` en lecturas existentes

### Backend
- [ ] Crear `BatchProcessor` service
- [ ] Modificar endpoint `/api/readings`
- [ ] Crear endpoint `/api/readings/batch`
- [ ] Crear endpoint `/api/batch/status`
- [ ] Integrar APScheduler
- [ ] Agregar logging de batches

### Smart Contract
- [ ] Actualizar datum para batches
- [ ] Modificar validador
- [ ] Compilar nuevo contrato
- [ ] Desplegar en testnet
- [ ] Validar funcionamiento

### Frontend
- [ ] Agregar panel de estado de batches
- [ ] Agregar botón "Procesar Ahora"
- [ ] Mostrar estadísticas de ahorro
- [ ] Indicador visual de lecturas pendientes

### Testing
- [ ] Test unitario de BatchProcessor
- [ ] Test de scheduler
- [ ] Test de bypass de alertas críticas
- [ ] Test de transacciones batch en testnet
- [ ] Validar integridad de datos

### Monitoreo
- [ ] Dashboard de métricas de batches
- [ ] Alertas si cola crece demasiado
- [ ] Logging de todas las transacciones
- [ ] Comparativa de costos antes/después

---

## 🎯 Próximos Pasos

1. **Revisar y aprobar** este plan
2. **Decidir estrategia** (recomiendo Híbrida)
3. **Crear branch** de desarrollo
4. **Implementar Fase 1** (infraestructura)
5. **Testing en testnet**
6. **Deployment a producción**

---

**Fecha de creación**: 2025-11-10
**Última actualización**: 2025-11-10
**Autor**: Sistema de Sensores Agrícolas
**Estado**: Pendiente de aprobación
