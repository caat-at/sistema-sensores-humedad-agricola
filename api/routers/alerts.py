# -*- coding: utf-8 -*-
"""
Router para alertas en tiempo real
"""

import sys
from pathlib import Path
from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel
from sqlalchemy.orm import Session

from api.database.connection import get_db
from api.database.models import ReadingHistory, SensorHistory

router = APIRouter(
    prefix="/api/alerts",
    tags=["alerts"]
)


class AlertResponse(BaseModel):
    """Modelo de respuesta para alertas"""
    alert_id: str
    sensor_id: str
    zone_name: str
    alert_level: str
    humidity_percentage: int
    temperature_celsius: int
    threshold_min: int
    threshold_max: int
    timestamp: str
    duration_minutes: Optional[int] = None
    message: str


class AlertSummary(BaseModel):
    """Resumen de alertas"""
    total_alerts: int
    critical_alerts: int
    high_alerts: int
    low_alerts: int
    affected_sensors: int


def calculate_alert_level(humidity: int, min_threshold: int, max_threshold: int) -> str:
    """Calcula el nivel de alerta basado en umbrales"""
    if humidity < min_threshold:
        diff = min_threshold - humidity
        if diff >= 20:
            return "Critical"
        else:
            return "Low"
    elif humidity > max_threshold:
        diff = humidity - max_threshold
        if diff >= 20:
            return "Critical"
        else:
            return "High"
    else:
        return "Normal"


def generate_alert_message(humidity: int, min_threshold: int, max_threshold: int, zone_name: str) -> str:
    """Genera mensaje descriptivo de la alerta"""
    if humidity < min_threshold:
        diff = min_threshold - humidity
        return f"Humedad baja en {zone_name}: {humidity}% (mínimo: {min_threshold}%). Diferencia: -{diff}%"
    elif humidity > max_threshold:
        diff = humidity - max_threshold
        return f"Humedad alta en {zone_name}: {humidity}% (máximo: {max_threshold}%). Diferencia: +{diff}%"
    else:
        return f"Humedad normal en {zone_name}: {humidity}%"


@router.get("/active", response_model=List[AlertResponse])
async def get_active_alerts(
    level: Optional[str] = Query(None, description="Filtrar por nivel: Critical, High, Low"),
    sensor_id: Optional[str] = Query(None, description="Filtrar por sensor"),
    db: Session = Depends(get_db)
):
    """
    Obtiene alertas activas (lecturas recientes con humedad fuera de rango)

    Retorna solo las lecturas on_chain=True de las últimas 24 horas
    """

    try:
        # Obtener lecturas de los últimos 8 días
        time_8days_ago = datetime.now() - timedelta(days=8)

        query = db.query(ReadingHistory, SensorHistory).join(
            SensorHistory, ReadingHistory.sensor_id == SensorHistory.sensor_id
        ).filter(
            ReadingHistory.timestamp >= time_8days_ago,
            SensorHistory.is_current == True
        )

        if sensor_id:
            query = query.filter(ReadingHistory.sensor_id == sensor_id)

        results = query.order_by(ReadingHistory.timestamp.desc()).all()

        # Procesar alertas
        alerts = []
        for reading, sensor in results:
            alert_level = calculate_alert_level(
                reading.humidity_percentage,
                sensor.min_humidity_threshold,
                sensor.max_humidity_threshold
            )

            # Solo incluir si hay alerta (no Normal)
            if alert_level != "Normal":
                # Filtrar por nivel si se especificó
                if level and alert_level != level:
                    continue

                # Calcular duración desde la lectura
                duration = (datetime.now() - reading.timestamp).total_seconds() / 60

                alert = AlertResponse(
                    alert_id=f"{reading.sensor_id}_{reading.timestamp.strftime('%Y%m%d%H%M%S')}",
                    sensor_id=reading.sensor_id,
                    zone_name=sensor.location_zone_name,
                    alert_level=alert_level,
                    humidity_percentage=reading.humidity_percentage,
                    temperature_celsius=reading.temperature_celsius,
                    threshold_min=sensor.min_humidity_threshold,
                    threshold_max=sensor.max_humidity_threshold,
                    timestamp=reading.timestamp.isoformat(),
                    duration_minutes=int(duration),
                    message=generate_alert_message(
                        reading.humidity_percentage,
                        sensor.min_humidity_threshold,
                        sensor.max_humidity_threshold,
                        sensor.location_zone_name
                    )
                )
                alerts.append(alert)

        return alerts

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error obteniendo alertas: {str(e)}"
        )


@router.get("/summary", response_model=AlertSummary)
async def get_alerts_summary(
    db: Session = Depends(get_db)
):
    """
    Resumen de alertas activas
    """

    try:
        # Obtener lecturas de los últimos 8 días
        time_8days_ago = datetime.now() - timedelta(days=8)

        results = db.query(ReadingHistory, SensorHistory).join(
            SensorHistory, ReadingHistory.sensor_id == SensorHistory.sensor_id
        ).filter(
            ReadingHistory.timestamp >= time_8days_ago,
            SensorHistory.is_current == True
        ).all()

        # Contar alertas por nivel
        total = 0
        critical = 0
        high = 0
        low = 0
        affected_sensors = set()

        for reading, sensor in results:
            alert_level = calculate_alert_level(
                reading.humidity_percentage,
                sensor.min_humidity_threshold,
                sensor.max_humidity_threshold
            )

            if alert_level != "Normal":
                total += 1
                affected_sensors.add(reading.sensor_id)

                if alert_level == "Critical":
                    critical += 1
                elif alert_level == "High":
                    high += 1
                elif alert_level == "Low":
                    low += 1

        return AlertSummary(
            total_alerts=total,
            critical_alerts=critical,
            high_alerts=high,
            low_alerts=low,
            affected_sensors=len(affected_sensors)
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generando resumen: {str(e)}"
        )


@router.get("/latest")
async def get_latest_alerts(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """
    Obtiene las alertas más recientes (últimas N alertas)
    """

    try:
        # Obtener lecturas más recientes
        results = db.query(ReadingHistory, SensorHistory).join(
            SensorHistory, ReadingHistory.sensor_id == SensorHistory.sensor_id
        ).filter(
            ReadingHistory.on_chain == True,
            SensorHistory.is_current == True
        ).order_by(
            ReadingHistory.timestamp.desc()
        ).limit(limit * 3).all()  # Obtener más para filtrar

        # Filtrar solo alertas
        alerts = []
        for reading, sensor in results:
            if len(alerts) >= limit:
                break

            alert_level = calculate_alert_level(
                reading.humidity_percentage,
                sensor.min_humidity_threshold,
                sensor.max_humidity_threshold
            )

            if alert_level != "Normal":
                duration = (datetime.now() - reading.timestamp).total_seconds() / 60

                alert = {
                    'alert_id': f"{reading.sensor_id}_{reading.timestamp.strftime('%Y%m%d%H%M%S')}",
                    'sensor_id': reading.sensor_id,
                    'zone_name': sensor.location_zone_name,
                    'alert_level': alert_level,
                    'humidity_percentage': reading.humidity_percentage,
                    'temperature_celsius': reading.temperature_celsius,
                    'timestamp': reading.timestamp.isoformat(),
                    'duration_minutes': int(duration),
                    'message': generate_alert_message(
                        reading.humidity_percentage,
                        sensor.min_humidity_threshold,
                        sensor.max_humidity_threshold,
                        sensor.location_zone_name
                    )
                }
                alerts.append(alert)

        return {
            'success': True,
            'count': len(alerts),
            'alerts': alerts
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error: {str(e)}"
        )
