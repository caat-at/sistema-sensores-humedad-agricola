# -*- coding: utf-8 -*-
"""
Modelos SQLAlchemy para PostgreSQL
"""

from sqlalchemy import (
    Column, Integer, String, DECIMAL, Boolean,
    TIMESTAMP, Text, CheckConstraint, Index
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from .connection import Base

class SensorHistory(Base):
    """Histórico de configuraciones de sensores"""
    __tablename__ = "sensors_history"

    id = Column(Integer, primary_key=True, index=True)
    sensor_id = Column(String(50), nullable=False, index=True)
    location_latitude = Column(DECIMAL(10, 6), nullable=False)
    location_longitude = Column(DECIMAL(10, 6), nullable=False)
    location_zone_name = Column(String(200), nullable=False)
    min_humidity_threshold = Column(Integer, nullable=False)
    max_humidity_threshold = Column(Integer, nullable=False)
    reading_interval_minutes = Column(Integer, nullable=False)
    status = Column(String(20), nullable=False, index=True)
    owner_pkh = Column(String(56), nullable=False)
    installed_date = Column(TIMESTAMP, nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    tx_hash = Column(String(64), index=True)
    is_current = Column(Boolean, default=True, index=True)

    __table_args__ = (
        CheckConstraint(
            'min_humidity_threshold >= 0 AND min_humidity_threshold <= 100',
            name='chk_min_humidity'
        ),
        CheckConstraint(
            'max_humidity_threshold >= 0 AND max_humidity_threshold <= 100',
            name='chk_max_humidity'
        ),
        CheckConstraint(
            'min_humidity_threshold < max_humidity_threshold',
            name='chk_humidity_range'
        ),
        CheckConstraint(
            "status IN ('Active', 'Inactive', 'Maintenance', 'Error')",
            name='chk_status'
        ),
    )

class ReadingHistory(Base):
    """Histórico de lecturas de sensores"""
    __tablename__ = "readings_history"

    id = Column(Integer, primary_key=True, index=True)
    sensor_id = Column(String(50), nullable=False, index=True)
    humidity_percentage = Column(Integer, nullable=False)
    temperature_celsius = Column(Integer, nullable=False)
    timestamp = Column(TIMESTAMP, nullable=False, index=True)
    tx_hash = Column(String(64), index=True)
    on_chain = Column(Boolean, default=True, index=True)
    rollup_batch_id = Column(String(64), index=True)  # Merkle root hash del rollup
    created_at = Column(TIMESTAMP, server_default=func.now())

    __table_args__ = (
        CheckConstraint(
            'humidity_percentage >= 0 AND humidity_percentage <= 100',
            name='chk_humidity_pct'
        ),
        CheckConstraint(
            'temperature_celsius >= -50 AND temperature_celsius <= 100',
            name='chk_temperature'
        ),
        Index('idx_sensor_timestamp', 'sensor_id', 'timestamp'),
    )

class TransactionLog(Base):
    """Log de transacciones blockchain"""
    __tablename__ = "transactions_log"

    id = Column(Integer, primary_key=True, index=True)
    tx_hash = Column(String(64), unique=True, nullable=False, index=True)
    tx_type = Column(String(50), nullable=False, index=True)
    status = Column(String(20), nullable=False, default='Pending', index=True)
    submitted_at = Column(TIMESTAMP, server_default=func.now(), index=True)
    confirmed_at = Column(TIMESTAMP)
    error_message = Column(Text)
    datum_snapshot = Column(JSONB)
    request_data = Column(JSONB)

    __table_args__ = (
        CheckConstraint(
            "tx_type IN ('RegisterSensor', 'AddReading', 'UpdateSensor', 'DeactivateSensor', 'UpdateAdmin')",
            name='chk_tx_type'
        ),
        CheckConstraint(
            "status IN ('Pending', 'Confirmed', 'Failed')",
            name='chk_status'
        ),
    )

class SensorAlert(Base):
    """Histórico de alertas de sensores"""
    __tablename__ = "sensor_alerts"

    id = Column(Integer, primary_key=True, index=True)
    sensor_id = Column(String(50), nullable=False, index=True)
    reading_id = Column(Integer)  # FK a readings_history
    alert_type = Column(String(50), nullable=False, index=True)
    alert_level = Column(String(20), nullable=False)
    message = Column(Text)
    created_at = Column(TIMESTAMP, server_default=func.now(), index=True)
    resolved_at = Column(TIMESTAMP, index=True)
    resolved_by = Column(String(56))

    __table_args__ = (
        CheckConstraint(
            "alert_type IN ('HumidityTooLow', 'HumidityTooHigh', 'TemperatureTooLow', 'TemperatureTooHigh', 'SensorOffline')",
            name='chk_alert_type'
        ),
        CheckConstraint(
            "alert_level IN ('Warning', 'Critical')",
            name='chk_alert_level'
        ),
    )


class RollupError(Base):
    """Registro de errores en rollups"""
    __tablename__ = "rollup_errors"

    id = Column(Integer, primary_key=True, index=True)
    sensor_id = Column(String(50), nullable=False, index=True)
    execution_date = Column(TIMESTAMP, nullable=False, index=True)
    error_type = Column(String(50), nullable=False, index=True)  # blockchain_error, validation_error, network_error, etc.
    error_message = Column(Text, nullable=False)
    error_details = Column(JSONB, nullable=True)  # Detalles adicionales en JSON
    readings_count = Column(Integer, nullable=True)  # Cuántas lecturas intentó procesar
    rollup_batch_id = Column(String(64), nullable=True)  # Si llegó a crear el batch
    tx_hash = Column(String(64), nullable=True, index=True)  # Si llegó a crear tx
    retry_count = Column(Integer, default=0)  # Número de reintentos
    resolved = Column(Boolean, default=False, index=True)  # Si el error fue resuelto
    resolved_at = Column(TIMESTAMP, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())

    __table_args__ = (
        Index('idx_rollup_errors_unresolved', 'sensor_id', 'resolved'),
        Index('idx_rollup_errors_date', 'execution_date'),
    )
