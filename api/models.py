# -*- coding: utf-8 -*-
"""
Modelos Pydantic para la API REST
"""

from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime


# ========================================
# REQUEST MODELS
# ========================================

class LocationCreate(BaseModel):
    """Modelo para crear ubicación"""
    latitude: float = Field(..., ge=-90, le=90, description="Latitud en grados decimales")
    longitude: float = Field(..., ge=-180, le=180, description="Longitud en grados decimales")
    zone_name: str = Field(..., min_length=1, max_length=100, description="Nombre de la zona")

    class Config:
        json_schema_extra = {
            "example": {
                "latitude": -34.58,
                "longitude": -58.45,
                "zone_name": "Campo Norte - Parcela A"
            }
        }


class SensorCreate(BaseModel):
    """Modelo para registrar un nuevo sensor

    NOTA: El campo sensor_id es OPCIONAL. Si no se proporciona,
    el sistema generará automáticamente el próximo ID secuencial disponible.
    """
    sensor_id: Optional[str] = Field(None, min_length=1, max_length=50, description="ID único del sensor (opcional, se auto-genera si no se proporciona)")
    location: LocationCreate
    min_humidity_threshold: int = Field(..., ge=0, le=100, description="Umbral mínimo de humedad (%)")
    max_humidity_threshold: int = Field(..., ge=0, le=100, description="Umbral máximo de humedad (%)")
    reading_interval_minutes: int = Field(..., gt=0, description="Intervalo de lectura en minutos")

    class Config:
        json_schema_extra = {
            "example": {
                "location": {
                    "latitude": -34.58,
                    "longitude": -58.45,
                    "zone_name": "Campo Norte - Parcela A"
                },
                "min_humidity_threshold": 30,
                "max_humidity_threshold": 70,
                "reading_interval_minutes": 60
            }
        }


class SensorUpdate(BaseModel):
    """Modelo para actualizar configuración de sensor"""
    min_humidity_threshold: Optional[int] = Field(None, ge=0, le=100)
    max_humidity_threshold: Optional[int] = Field(None, ge=0, le=100)
    reading_interval_minutes: Optional[int] = Field(None, gt=0)
    location: Optional[LocationCreate] = None
    status: Optional[Literal["Active", "Inactive", "Maintenance", "Error"]] = None

    class Config:
        json_schema_extra = {
            "example": {
                "min_humidity_threshold": 25,
                "max_humidity_threshold": 75,
                "reading_interval_minutes": 120
            }
        }


class ReadingCreate(BaseModel):
    """Modelo para agregar una lectura"""
    sensor_id: str = Field(..., min_length=1, max_length=50)
    humidity_percentage: int = Field(..., ge=0, le=100, description="Porcentaje de humedad")
    temperature_celsius: int = Field(..., ge=-30, le=60, description="Temperatura en Celsius")

    class Config:
        json_schema_extra = {
            "example": {
                "sensor_id": "SENSOR_001",
                "humidity_percentage": 65,
                "temperature_celsius": 22
            }
        }


# ========================================
# RESPONSE MODELS
# ========================================

class LocationResponse(BaseModel):
    """Modelo de respuesta para ubicación"""
    latitude: float
    longitude: float
    zone_name: str


class SensorResponse(BaseModel):
    """Modelo de respuesta para sensor"""
    sensor_id: str
    location: LocationResponse
    min_humidity_threshold: int
    max_humidity_threshold: int
    reading_interval_minutes: int
    status: str
    owner: str
    installed_date: str


class ReadingResponse(BaseModel):
    """Modelo de respuesta para lectura"""
    id: Optional[int] = None  # ID de la lectura en la base de datos
    sensor_id: str
    humidity_percentage: int
    temperature_celsius: int
    timestamp: str
    alert_level: str
    tx_hash: Optional[str] = None  # TxHash de la transacción que creó la lectura

    class Config:
        from_attributes = True


class StatsResponse(BaseModel):
    """Modelo de respuesta para estadísticas"""
    total_sensors: int
    active_sensors: int
    inactive_sensors: int
    total_readings: int
    sensor_status_distribution: dict
    alert_level_distribution: dict
    humidity_stats: dict
    temperature_stats: dict
    readings_per_sensor: dict


class ContractStateResponse(BaseModel):
    """Modelo de respuesta para estado del contrato"""
    contract_address: str
    balance_ada: float
    last_updated: str
    total_sensors: int
    sensors: list[SensorResponse]
    recent_readings: list[ReadingResponse]


class TransactionResponse(BaseModel):
    """Modelo de respuesta para transacciones"""
    success: bool
    tx_hash: Optional[str] = None
    explorer_url: Optional[str] = None
    message: str


class ErrorResponse(BaseModel):
    """Modelo de respuesta para errores"""
    error: str
    detail: Optional[str] = None
