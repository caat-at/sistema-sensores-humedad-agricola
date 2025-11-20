"""
Router de API para rollups diarios
Endpoints para procesar y verificar rollups con merkle hash
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime, timedelta
from pydantic import BaseModel

from api.database.connection import get_db
from api.services.daily_rollup import DailyRollupService


router = APIRouter(
    prefix="/api/rollup",
    tags=["Rollups"]
)


# ========================================
# MODELOS PYDANTIC
# ========================================

class RollupProcessRequest(BaseModel):
    """Request para procesar rollup"""
    sensor_id: Optional[str] = None
    date: Optional[str] = None  # YYYY-MM-DD format


class RollupProcessResponse(BaseModel):
    """Response del procesamiento de rollup"""
    date: str
    sensors_processed: int
    total_readings: int
    successful_rollups: int
    failed_rollups: int
    rollups: List[dict]


class RollupVerifyRequest(BaseModel):
    """Request para verificar lectura en rollup"""
    reading_id: int


class RollupVerifyResponse(BaseModel):
    """Response de verificación de lectura"""
    valid: bool
    reading_id: int
    rollup_batch_id: Optional[str]
    merkle_root: Optional[str]
    tx_hash: Optional[str]
    proof: Optional[List[tuple]]
    leaf_hash: Optional[str]
    error: Optional[str]


class RollupStatsResponse(BaseModel):
    """Estadísticas de rollups"""
    total_rollups: int
    total_readings_in_rollups: int
    pending_readings: int
    average_readings_per_rollup: float
    last_rollup_date: Optional[str]
    estimated_savings_ada: float


# ========================================
# ENDPOINTS
# ========================================

@router.post("/daily", response_model=RollupProcessResponse)
async def process_daily_rollup(
    request: RollupProcessRequest,
    db: Session = Depends(get_db)
):
    """
    Procesa rollup diario para un sensor específico o todos los sensores

    - Si no se especifica sensor_id, procesa todos los sensores activos
    - Si no se especifica date, usa ayer (último día completo)

    **Ejemplo de uso:**
    ```bash
    # Procesar todos los sensores de ayer
    curl -X POST "http://localhost:8000/api/rollup/daily" \\
         -H "Content-Type: application/json" \\
         -d '{}'

    # Procesar sensor específico de una fecha
    curl -X POST "http://localhost:8000/api/rollup/daily" \\
         -H "Content-Type: application/json" \\
         -d '{"sensor_id": "SENSOR_001", "date": "2025-11-09"}'
    ```
    """
    try:
        # Parsear fecha si se proporciona
        target_date = None
        if request.date:
            try:
                target_date = datetime.strptime(request.date, "%Y-%m-%d")
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Formato de fecha inválido. Use YYYY-MM-DD"
                )

        # Crear servicio de rollup con blockchain client
        from api.services.blockchain_service import BlockchainService
        blockchain_service = BlockchainService()
        rollup_service = DailyRollupService(db, blockchain_service)

        # Procesar rollup
        result = rollup_service.process_daily_rollup(
            sensor_id=request.sensor_id,
            date=target_date
        )

        return RollupProcessResponse(**result)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error procesando rollup: {str(e)}"
        )


@router.post("/verify", response_model=RollupVerifyResponse)
async def verify_reading_in_rollup(
    request: RollupVerifyRequest,
    db: Session = Depends(get_db)
):
    """
    Verifica que una lectura específica esté correctamente incluida en su rollup
    usando merkle proof

    **Ejemplo de uso:**
    ```bash
    curl -X POST "http://localhost:8000/api/rollup/verify" \\
         -H "Content-Type: application/json" \\
         -d '{"reading_id": 123}'
    ```
    """
    try:
        rollup_service = DailyRollupService(db)
        result = rollup_service.verify_reading_in_rollup(request.reading_id)

        return RollupVerifyResponse(**result)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error verificando lectura: {str(e)}"
        )


@router.get("/stats", response_model=RollupStatsResponse)
async def get_rollup_statistics(db: Session = Depends(get_db)):
    """
    Obtiene estadísticas generales del sistema de rollups

    **Ejemplo de uso:**
    ```bash
    curl "http://localhost:8000/api/rollup/stats"
    ```
    """
    try:
        from api.database.models import ReadingHistory
        from sqlalchemy import func

        # Total de lecturas en rollups
        total_in_rollups = db.query(func.count(ReadingHistory.id)).filter(
            ReadingHistory.rollup_batch_id.isnot(None)
        ).scalar() or 0

        # Total de rollups únicos
        total_rollups = db.query(func.count(func.distinct(ReadingHistory.rollup_batch_id))).filter(
            ReadingHistory.rollup_batch_id.isnot(None)
        ).scalar() or 0

        # Lecturas pendientes de rollup
        pending_readings = db.query(func.count(ReadingHistory.id)).filter(
            ReadingHistory.rollup_batch_id.is_(None),
            ReadingHistory.on_chain == False
        ).scalar() or 0

        # Promedio de lecturas por rollup
        avg_per_rollup = total_in_rollups / total_rollups if total_rollups > 0 else 0

        # Última fecha de rollup
        last_rollup = db.query(func.max(ReadingHistory.timestamp)).filter(
            ReadingHistory.rollup_batch_id.isnot(None)
        ).scalar()

        last_rollup_date = last_rollup.date().isoformat() if last_rollup else None

        # Calcular ahorro estimado
        # Sin rollup: 1 TX por lectura = total_in_rollups TXs
        # Con rollup: 1 TX por rollup = total_rollups TXs
        # Ahorro: (total_in_rollups - total_rollups) * 5.1 ADA
        tx_saved = total_in_rollups - total_rollups
        estimated_savings_ada = tx_saved * 5.1

        return RollupStatsResponse(
            total_rollups=total_rollups,
            total_readings_in_rollups=total_in_rollups,
            pending_readings=pending_readings,
            average_readings_per_rollup=round(avg_per_rollup, 2),
            last_rollup_date=last_rollup_date,
            estimated_savings_ada=round(estimated_savings_ada, 2)
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error obteniendo estadísticas: {str(e)}"
        )


@router.get("/list")
async def list_rollups(
    limit: int = Query(10, description="Número de rollups a retornar"),
    offset: int = Query(0, description="Offset para paginación"),
    db: Session = Depends(get_db)
):
    """
    Lista los rollups más recientes con sus estadísticas

    **Ejemplo de uso:**
    ```bash
    curl "http://localhost:8000/api/rollup/list?limit=5"
    ```
    """
    try:
        from api.database.models import ReadingHistory
        from sqlalchemy import func, and_

        # Obtener rollups únicos con estadísticas
        rollups_query = db.query(
            ReadingHistory.rollup_batch_id,
            ReadingHistory.sensor_id,
            ReadingHistory.tx_hash,
            func.count(ReadingHistory.id).label('readings_count'),
            func.min(ReadingHistory.humidity_percentage).label('humidity_min'),
            func.max(ReadingHistory.humidity_percentage).label('humidity_max'),
            func.avg(ReadingHistory.humidity_percentage).label('humidity_avg'),
            func.min(ReadingHistory.timestamp).label('first_reading'),
            func.max(ReadingHistory.timestamp).label('last_reading')
        ).filter(
            ReadingHistory.rollup_batch_id.isnot(None)
        ).group_by(
            ReadingHistory.rollup_batch_id,
            ReadingHistory.sensor_id,
            ReadingHistory.tx_hash
        ).order_by(
            func.max(ReadingHistory.timestamp).desc()
        ).limit(limit).offset(offset)

        rollups = rollups_query.all()

        result = []
        for rollup in rollups:
            result.append({
                "merkle_root": rollup.rollup_batch_id,
                "sensor_id": rollup.sensor_id,
                "tx_hash": rollup.tx_hash,
                "readings_count": rollup.readings_count,
                "humidity_min": rollup.humidity_min,
                "humidity_max": rollup.humidity_max,
                "humidity_avg": round(float(rollup.humidity_avg), 2) if rollup.humidity_avg else None,
                "first_reading": rollup.first_reading.isoformat() if rollup.first_reading else None,
                "last_reading": rollup.last_reading.isoformat() if rollup.last_reading else None,
                "date": rollup.first_reading.date().isoformat() if rollup.first_reading else None
            })

        return {
            "rollups": result,
            "count": len(result),
            "limit": limit,
            "offset": offset
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error listando rollups: {str(e)}"
        )


@router.get("/pending-readings")
async def get_pending_readings(
    sensor_id: Optional[str] = Query(None, description="Filtrar por sensor"),
    db: Session = Depends(get_db)
):
    """
    Obtiene lecturas pendientes de ser incluidas en un rollup

    **Ejemplo de uso:**
    ```bash
    curl "http://localhost:8000/api/rollup/pending-readings?sensor_id=SENSOR_001"
    ```
    """
    try:
        from api.database.models import ReadingHistory
        from sqlalchemy import and_

        query = db.query(ReadingHistory).filter(
            and_(
                ReadingHistory.rollup_batch_id.is_(None),
                ReadingHistory.on_chain == False
            )
        )

        if sensor_id:
            query = query.filter(ReadingHistory.sensor_id == sensor_id)

        pending = query.order_by(ReadingHistory.timestamp.desc()).limit(100).all()

        result = []
        for reading in pending:
            result.append({
                "id": reading.id,
                "sensor_id": reading.sensor_id,
                "humidity_percentage": reading.humidity_percentage,
                "temperature_celsius": reading.temperature_celsius,
                "timestamp": reading.timestamp.isoformat()
            })

        return {
            "pending_readings": result,
            "count": len(result)
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error obteniendo lecturas pendientes: {str(e)}"
        )
