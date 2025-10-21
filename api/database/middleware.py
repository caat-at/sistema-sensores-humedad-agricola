# -*- coding: utf-8 -*-
"""
Middleware para guardar datos en PostgreSQL
"""

from datetime import datetime
from sqlalchemy.orm import Session
from .models import SensorHistory, ReadingHistory, TransactionLog

def save_sensor_to_db(
    db: Session,
    sensor_id: str,
    location_latitude: float,
    location_longitude: float,
    location_zone_name: str,
    min_humidity_threshold: int,
    max_humidity_threshold: int,
    reading_interval_minutes: int,
    status: str,
    owner_pkh: str,
    installed_date: datetime,
    tx_hash: str
) -> SensorHistory:
    """
    Guardar sensor en PostgreSQL
    Marca el anterior como is_current=False
    """
    # Marcar versión anterior como no actual
    db.query(SensorHistory).filter(
        SensorHistory.sensor_id == sensor_id,
        SensorHistory.is_current == True
    ).update({"is_current": False})

    # Crear nuevo registro
    sensor = SensorHistory(
        sensor_id=sensor_id,
        location_latitude=location_latitude,
        location_longitude=location_longitude,
        location_zone_name=location_zone_name,
        min_humidity_threshold=min_humidity_threshold,
        max_humidity_threshold=max_humidity_threshold,
        reading_interval_minutes=reading_interval_minutes,
        status=status,
        owner_pkh=owner_pkh,
        installed_date=installed_date,
        tx_hash=tx_hash,
        is_current=True
    )

    db.add(sensor)
    db.commit()
    db.refresh(sensor)

    print(f"[DB] Sensor {sensor_id} guardado en PostgreSQL")
    return sensor

def save_reading_to_db(
    db: Session,
    sensor_id: str,
    humidity_percentage: int,
    temperature_celsius: int,
    timestamp: datetime,
    tx_hash: str,
    on_chain: bool = True
) -> ReadingHistory:
    """
    Guardar lectura en PostgreSQL
    """
    reading = ReadingHistory(
        sensor_id=sensor_id,
        humidity_percentage=humidity_percentage,
        temperature_celsius=temperature_celsius,
        timestamp=timestamp,
        tx_hash=tx_hash,
        on_chain=on_chain
    )

    db.add(reading)
    db.commit()
    db.refresh(reading)

    print(f"[DB] Lectura de {sensor_id} guardada en PostgreSQL (on_chain={on_chain})")
    return reading

def save_transaction_log(
    db: Session,
    tx_hash: str,
    tx_type: str,
    status: str = 'Pending',
    request_data: dict = None
) -> TransactionLog:
    """
    Guardar log de transacción
    """
    tx_log = TransactionLog(
        tx_hash=tx_hash,
        tx_type=tx_type,
        status=status,
        request_data=request_data
    )

    db.add(tx_log)
    db.commit()
    db.refresh(tx_log)

    print(f"[DB] TX {tx_hash[:16]}... logged ({tx_type})")
    return tx_log

def update_transaction_status(
    db: Session,
    tx_hash: str,
    status: str,
    error_message: str = None,
    datum_snapshot: dict = None
):
    """
    Actualizar estado de transacción
    """
    tx_log = db.query(TransactionLog).filter(
        TransactionLog.tx_hash == tx_hash
    ).first()

    if tx_log:
        tx_log.status = status
        if status == 'Confirmed':
            tx_log.confirmed_at = datetime.now()
        if error_message:
            tx_log.error_message = error_message
        if datum_snapshot:
            tx_log.datum_snapshot = datum_snapshot

        db.commit()
        print(f"[DB] TX {tx_hash[:16]}... actualizada: {status}")

def archive_old_readings(
    db: Session,
    sensor_id: str,
    keep_count: int = 10
) -> int:
    """
    Marcar lecturas antiguas como on_chain=False
    Mantiene solo las últimas 'keep_count' lecturas on-chain
    """
    # Obtener IDs de lecturas a archivar
    subquery = db.query(ReadingHistory.id).filter(
        ReadingHistory.sensor_id == sensor_id,
        ReadingHistory.on_chain == True
    ).order_by(ReadingHistory.timestamp.desc()).offset(keep_count)

    # Marcar como archivadas
    archived_count = db.query(ReadingHistory).filter(
        ReadingHistory.id.in_(subquery)
    ).update({"on_chain": False}, synchronize_session=False)

    db.commit()

    if archived_count > 0:
        print(f"[DB] Archivadas {archived_count} lecturas antiguas de {sensor_id}")

    return archived_count
