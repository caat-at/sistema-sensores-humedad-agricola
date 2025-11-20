# -*- coding: utf-8 -*-
"""
Router para endpoints de lecturas
"""

import sys
import os
from pathlib import Path
from fastapi import APIRouter, HTTPException, status, Query, Depends
from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import datetime
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Agregar pycardano-client al path
pycardano_path = Path(__file__).parent.parent.parent / "pycardano-client"
sys.path.insert(0, str(pycardano_path))

from api.models import (
    ReadingCreate,
    ReadingResponse,
    TransactionResponse
)
from api.services.blockchain_service import BlockchainService

# Importar database (opcional)
try:
    from api.database.connection import get_db
    from api.database.middleware import save_reading_to_db, archive_old_readings
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False
    print("[WARN] PostgreSQL middleware no disponible para readings. Continuando solo con blockchain.")

router = APIRouter(
    prefix="/api/readings",
    tags=["readings"]
)


def reading_to_response(reading) -> ReadingResponse:
    """Convierte un HumidityReading de PlutusData a ReadingResponse"""
    return ReadingResponse(
        sensor_id=reading.sensor_id.decode('utf-8', errors='ignore'),
        humidity_percentage=reading.humidity_percentage,
        temperature_celsius=reading.temperature_celsius,
        timestamp=datetime.fromtimestamp(reading.timestamp / 1000).isoformat(),
        alert_level=type(reading.alert_level).__name__
    )


@router.get("", response_model=List[ReadingResponse])
async def list_readings(
    sensor_id: Optional[str] = Query(None, description="Filtrar por ID de sensor"),
    limit: Optional[int] = Query(None, ge=1, le=100, description="Límite de resultados"),
    db: Optional[Session] = Depends(get_db) if DB_AVAILABLE else None
):
    """
    Lista todas las lecturas recientes

    - **sensor_id**: Opcional - Filtrar por sensor específico
    - **limit**: Opcional - Limitar cantidad de resultados (máx 100)
    """
    try:
        # Si PostgreSQL está disponible, consultar desde ahí (incluye tx_hash)
        if DB_AVAILABLE and db is not None:
            from api.database.models import ReadingHistory

            # Mostrar TODAS las lecturas (tanto pendientes como on-chain)
            query = db.query(ReadingHistory)

            # Filtrar por sensor si se especifica
            if sensor_id:
                query = query.filter(ReadingHistory.sensor_id == sensor_id)

            # Ordenar por timestamp descendente
            query = query.order_by(ReadingHistory.timestamp.desc())

            # Aplicar límite
            if limit:
                query = query.limit(limit)

            db_readings = query.all()

            # Calcular alert_level basado en umbrales
            def calculate_alert_level(humidity: int) -> str:
                if humidity < 20 or humidity > 85:
                    return "Critical"
                elif humidity < 40:
                    return "Low"
                elif humidity > 70:
                    return "High"
                else:
                    return "Normal"

            return [
                ReadingResponse(
                    sensor_id=r.sensor_id,
                    humidity_percentage=r.humidity_percentage,
                    temperature_celsius=r.temperature_celsius,
                    timestamp=r.timestamp.isoformat(),
                    alert_level=calculate_alert_level(r.humidity_percentage),
                    tx_hash=r.tx_hash
                )
                for r in db_readings
            ]

        # Fallback: consultar desde blockchain (sin tx_hash)
        blockchain = BlockchainService()
        readings = blockchain.get_all_readings()

        # Filtrar por sensor si se especifica
        if sensor_id:
            readings = [
                r for r in readings
                if r.sensor_id.decode('utf-8', errors='ignore') == sensor_id
            ]

        # Ordenar por timestamp descendente (más reciente primero)
        readings = sorted(readings, key=lambda r: r.timestamp, reverse=True)

        # Aplicar límite si se especifica
        if limit:
            readings = readings[:limit]

        return [reading_to_response(r) for r in readings]

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener lecturas: {str(e)}"
        )


@router.post("", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
async def add_reading(
    reading_data: ReadingCreate,
    db: Optional[Session] = Depends(get_db) if DB_AVAILABLE else None
):
    """
    Agrega una nueva lectura de sensor

    El nivel de alerta se calcula automáticamente basado en los umbrales del sensor:
    - **Normal**: Humedad entre umbrales configurados
    - **Low**: Humedad < 40%
    - **High**: Humedad > 70%
    - **Critical**: Humedad < 20% o > 85%
    """
    try:
        # Verificar modo de operación
        use_rollup_mode = os.getenv('USE_ROLLUP_MODE', 'false').lower() == 'true'

        tx_hash = None
        on_chain = False

        if not use_rollup_mode:
            # MODO INMEDIATO: Enviar transacción a blockchain ahora
            blockchain = BlockchainService()
            tx_hash = blockchain.add_reading(
                sensor_id=reading_data.sensor_id,
                humidity=reading_data.humidity_percentage,
                temperature=reading_data.temperature_celsius
            )
            on_chain = True
        else:
            # MODO ROLLUP: Marcar como PENDIENTE
            tx_hash = "PENDIENTE"

        # GUARDAR EN POSTGRESQL (si está disponible)
        if DB_AVAILABLE and db is not None:
            try:
                timestamp_now = datetime.now()

                save_reading_to_db(
                    db=db,
                    sensor_id=reading_data.sensor_id,
                    humidity_percentage=reading_data.humidity_percentage,
                    temperature_celsius=reading_data.temperature_celsius,
                    timestamp=timestamp_now,
                    tx_hash=tx_hash,
                    on_chain=on_chain
                )

                # Archivar lecturas antiguas (mantener solo las últimas 10 on-chain)
                archived_count = archive_old_readings(
                    db=db,
                    sensor_id=reading_data.sensor_id,
                    keep_count=10
                )

                if archived_count > 0:
                    print(f"[DB] Archivadas {archived_count} lecturas antiguas de {reading_data.sensor_id}")

            except Exception as db_error:
                print(f"[WARN] No se pudo guardar en PostgreSQL: {db_error}")
                # No lanzar error - la transacción blockchain fue exitosa

        # Preparar respuesta según el modo
        if use_rollup_mode:
            return TransactionResponse(
                success=True,
                tx_hash="PENDIENTE",
                explorer_url=None,
                message=f"Lectura guardada para sensor {reading_data.sensor_id}. Será enviada a blockchain en el próximo rollup diario."
            )
        else:
            return TransactionResponse(
                success=True,
                tx_hash=tx_hash,
                explorer_url=f"https://preview.cardanoscan.io/transaction/{tx_hash}",
                message=f"Lectura agregada para sensor {reading_data.sensor_id}"
            )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al agregar lectura: {str(e)}"
        )
