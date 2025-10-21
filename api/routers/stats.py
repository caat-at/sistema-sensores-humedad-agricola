# -*- coding: utf-8 -*-
"""
Router para endpoints de estadísticas
"""

import sys
from pathlib import Path
from fastapi import APIRouter, HTTPException, status
from collections import Counter

# Agregar pycardano-client al path
pycardano_path = Path(__file__).parent.parent.parent / "pycardano-client"
sys.path.insert(0, str(pycardano_path))

from api.models import StatsResponse, ContractStateResponse, SensorResponse, ReadingResponse
from pycardano_tx import CardanoTransactionBuilder
from datetime import datetime

router = APIRouter(
    prefix="/api",
    tags=["stats"]
)


@router.get("/stats", response_model=StatsResponse)
async def get_stats():
    """
    Obtiene estadísticas generales del sistema

    Incluye:
    - Conteo de sensores por estado
    - Distribución de alertas
    - Estadísticas de humedad (min, max, promedio)
    - Estadísticas de temperatura (min, max, promedio)
    - Lecturas por sensor
    """
    try:
        builder = CardanoTransactionBuilder()
        contract_utxo = builder.get_contract_utxo_with_datum()
        current_datum = builder.decode_datum(contract_utxo.output.datum)

        sensors = current_datum.sensors
        readings = current_datum.recent_readings

        # Distribución de estados de sensores
        status_counts = Counter([type(s.status).__name__ for s in sensors])

        # Distribución de niveles de alerta
        alert_counts = Counter([type(r.alert_level).__name__ for r in readings])

        # Estadísticas de humedad
        if readings:
            humidities = [r.humidity_percentage for r in readings]
            humidity_stats = {
                "min": min(humidities),
                "max": max(humidities),
                "avg": round(sum(humidities) / len(humidities), 1)
            }
        else:
            humidity_stats = {"min": 0, "max": 0, "avg": 0}

        # Estadísticas de temperatura
        if readings:
            temps = [r.temperature_celsius for r in readings]
            temperature_stats = {
                "min": min(temps),
                "max": max(temps),
                "avg": round(sum(temps) / len(temps), 1)
            }
        else:
            temperature_stats = {"min": 0, "max": 0, "avg": 0}

        # Lecturas por sensor
        readings_per_sensor = Counter([r.sensor_id.decode('utf-8', errors='ignore') for r in readings])

        # Contar sensores activos
        active_count = sum(1 for s in sensors if type(s.status).__name__ == "Active")
        inactive_count = len(sensors) - active_count

        return StatsResponse(
            total_sensors=len(sensors),
            active_sensors=active_count,
            inactive_sensors=inactive_count,
            total_readings=len(readings),
            sensor_status_distribution=dict(status_counts),
            alert_level_distribution=dict(alert_counts),
            humidity_stats=humidity_stats,
            temperature_stats=temperature_stats,
            readings_per_sensor=dict(readings_per_sensor)
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener estadísticas: {str(e)}"
        )


@router.get("/contract", response_model=ContractStateResponse)
async def get_contract_state():
    """
    Obtiene el estado completo del contrato

    Incluye:
    - Información del contrato (address, balance)
    - Todos los sensores registrados
    - Todas las lecturas recientes
    """
    try:
        builder = CardanoTransactionBuilder()
        contract_utxo = builder.get_contract_utxo_with_datum()
        current_datum = builder.decode_datum(contract_utxo.output.datum)

        # Importar funciones de conversión
        from api.routers.sensors import sensor_to_response
        from api.routers.readings import reading_to_response

        sensors = [sensor_to_response(s) for s in current_datum.sensors]
        readings = [reading_to_response(r) for r in current_datum.recent_readings]

        # Ordenar lecturas por timestamp descendente
        readings = sorted(readings, key=lambda r: r.timestamp, reverse=True)

        return ContractStateResponse(
            contract_address=builder.contract_address,
            balance_ada=round(int(contract_utxo.amount[0].quantity) / 1_000_000, 2),
            last_updated=datetime.fromtimestamp(current_datum.last_updated / 1000).isoformat(),
            total_sensors=current_datum.total_sensors,
            sensors=sensors,
            recent_readings=readings
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener estado del contrato: {str(e)}"
        )
