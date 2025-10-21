# -*- coding: utf-8 -*-
"""
Router para endpoints de sensores
"""

import sys
from pathlib import Path
from fastapi import APIRouter, HTTPException, status, Depends
from typing import List, Optional
from sqlalchemy.orm import Session

# Agregar pycardano-client al path
pycardano_path = Path(__file__).parent.parent.parent / "pycardano-client"
sys.path.insert(0, str(pycardano_path))

from api.models import (
    SensorCreate,
    SensorUpdate,
    SensorResponse,
    LocationResponse,
    TransactionResponse
)
from api.services.blockchain_service import BlockchainService
from datetime import datetime

# Importar database (opcional)
try:
    from api.database.connection import get_db
    from api.database.middleware import save_sensor_to_db
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False
    print("[WARN] PostgreSQL middleware no disponible. Continuando solo con blockchain.")

router = APIRouter(
    prefix="/api/sensors",
    tags=["sensors"]
)


def get_db_optional():
    """Dependency opcional para DB - retorna None si DB no está disponible"""
    if DB_AVAILABLE:
        return Depends(get_db)
    return None


def sensor_to_response(sensor) -> SensorResponse:
    """Convierte un SensorConfig de PlutusData a SensorResponse"""
    return SensorResponse(
        sensor_id=sensor.sensor_id.decode('utf-8', errors='ignore'),
        location=LocationResponse(
            latitude=sensor.location.latitude / 1_000_000,
            longitude=sensor.location.longitude / 1_000_000,
            zone_name=sensor.location.zone_name.decode('utf-8', errors='ignore')
        ),
        min_humidity_threshold=sensor.min_humidity_threshold,
        max_humidity_threshold=sensor.max_humidity_threshold,
        reading_interval_minutes=sensor.reading_interval_minutes,
        status=type(sensor.status).__name__,
        owner=sensor.owner.hex(),
        installed_date=datetime.fromtimestamp(sensor.installed_date / 1000).isoformat()
    )


@router.get("", response_model=List[SensorResponse])
async def list_sensors():
    """
    Lista todos los sensores registrados en el contrato
    Deduplica sensores por sensor_id, devolviendo la versión más reciente
    """
    try:
        blockchain = BlockchainService()
        all_sensors = blockchain.get_all_sensors()

        # Deduplicar sensores
        sensors_dict = blockchain.deduplicate_sensors(all_sensors)

        # Convertir a lista de respuestas
        sensors = [sensor_to_response(s) for s in sensors_dict.values()]
        return sensors

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener sensores: {str(e)}"
        )


@router.get("/{sensor_id}", response_model=SensorResponse)
async def get_sensor(sensor_id: str):
    """
    Obtiene los detalles de un sensor específico
    """
    try:
        blockchain = BlockchainService()
        sensor = blockchain.get_sensor_by_id(sensor_id)

        if not sensor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Sensor '{sensor_id}' no encontrado"
            )

        return sensor_to_response(sensor)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener sensor: {str(e)}"
        )


@router.post("", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
async def register_sensor(
    sensor_data: SensorCreate,
    db: Optional[Session] = Depends(get_db) if DB_AVAILABLE else None
):
    """
    Registra un nuevo sensor en el contrato

    El sensor_id se genera automáticamente de forma secuencial (SENSOR_001, SENSOR_002, etc.)
    Si el usuario proporciona un sensor_id manualmente, se valida que no exista ya.

    IMPORTANTE: No se pueden reutilizar IDs de sensores existentes,
    incluso si están Inactive. Cada sensor_id debe ser único.
    """
    try:
        blockchain = BlockchainService()

        # Obtener IDs existentes
        existing_ids = blockchain.get_existing_sensor_ids()

        # AUTO-GENERAR sensor_id si no se proporcionó
        if not sensor_data.sensor_id:
            generated_sensor_id = blockchain.auto_generate_sensor_id()
            sensor_data.sensor_id = generated_sensor_id
            print(f"[INFO] Sensor ID auto-generado: {generated_sensor_id}")

        # VALIDACIÓN: Verificar que el sensor_id no exista ya (ni Active ni Inactive)
        if sensor_data.sensor_id in existing_ids:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"El sensor_id '{sensor_data.sensor_id}' ya existe en el sistema. "
                       f"No se pueden reutilizar IDs de sensores, incluso si están Inactive. "
                       f"El sistema genera IDs automáticamente para evitar duplicados."
            )

        # Registrar en blockchain
        tx_hash = blockchain.register_sensor(
            sensor_id=sensor_data.sensor_id,
            latitude=sensor_data.location.latitude,
            longitude=sensor_data.location.longitude,
            zone_name=sensor_data.location.zone_name,
            min_humidity=sensor_data.min_humidity_threshold,
            max_humidity=sensor_data.max_humidity_threshold,
            reading_interval=sensor_data.reading_interval_minutes
        )

        # GUARDAR EN POSTGRESQL (si está disponible)
        if DB_AVAILABLE and db is not None:
            try:
                timestamp_now = int(datetime.now().timestamp() * 1000)
                datetime_now = datetime.fromtimestamp(timestamp_now / 1000)

                save_sensor_to_db(
                    db=db,
                    sensor_id=sensor_data.sensor_id,
                    location_latitude=sensor_data.location.latitude,
                    location_longitude=sensor_data.location.longitude,
                    location_zone_name=sensor_data.location.zone_name,
                    min_humidity_threshold=sensor_data.min_humidity_threshold,
                    max_humidity_threshold=sensor_data.max_humidity_threshold,
                    reading_interval_minutes=sensor_data.reading_interval_minutes,
                    status="Active",
                    owner_pkh=blockchain.builder.payment_vkey.hash().to_primitive().hex(),
                    installed_date=datetime_now,
                    tx_hash=tx_hash
                )
                print(f"[DB] Sensor {sensor_data.sensor_id} guardado en PostgreSQL")
            except Exception as db_error:
                print(f"[WARN] No se pudo guardar en PostgreSQL: {db_error}")
                # No lanzar error - la transacción blockchain fue exitosa

        return TransactionResponse(
            success=True,
            tx_hash=tx_hash,
            explorer_url=f"https://preview.cardanoscan.io/transaction/{tx_hash}",
            message=f"Sensor {sensor_data.sensor_id} registrado exitosamente"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al registrar sensor: {str(e)}"
        )


@router.put("/{sensor_id}", response_model=TransactionResponse)
async def update_sensor(sensor_id: str, update_data: SensorUpdate):
    """
    Actualiza la configuración de un sensor existente

    TODO: Implementar UpdateSensorConfig en BlockchainService
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Endpoint de actualización en desarrollo. Use deactivate + register como workaround."
    )


@router.delete("/{sensor_id}", response_model=TransactionResponse)
async def deactivate_sensor(sensor_id: str):
    """
    Desactiva un sensor (cambia estado a Inactive)
    Un sensor desactivado no puede recibir nuevas lecturas

    TODO: Implementar DeactivateSensor en BlockchainService
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Endpoint de desactivación en desarrollo."
    )
