# -*- coding: utf-8 -*-
"""
Router para auditoría de integridad
"""

import sys
from pathlib import Path
from fastapi import APIRouter, HTTPException, status, Query
from typing import List, Dict, Optional
from datetime import datetime, timedelta

# Agregar pycardano-client al path
pycardano_path = Path(__file__).parent.parent.parent / "pycardano-client"
sys.path.insert(0, str(pycardano_path))

from api.services.blockchain_service import BlockchainService

# Importar database (opcional)
try:
    from api.database.connection import get_db
    from api.database.models import ReadingHistory
    from sqlalchemy.orm import Session
    from fastapi import Depends
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False

router = APIRouter(
    prefix="/api/audit",
    tags=["audit"]
)


def encontrar_match(lectura_bc: Dict, lecturas_db: List[Dict], tolerancia_seg: int = 15) -> Optional[Dict]:
    """Encuentra la lectura más cercana en tiempo"""
    mejor_match = None
    menor_diff = timedelta(seconds=999999)

    for lectura_db in lecturas_db:
        if lectura_bc['sensor_id'] != lectura_db['sensor_id']:
            continue

        diff = abs(lectura_bc['timestamp'] - lectura_db['timestamp'])

        if diff <= timedelta(seconds=tolerancia_seg) and diff < menor_diff:
            menor_diff = diff
            mejor_match = {**lectura_db, 'time_diff_seconds': diff.total_seconds()}

    return mejor_match


@router.get("/compare")
async def compare_blockchain_sql(
    limit: Optional[int] = Query(20, ge=1, le=100, description="Límite de lecturas a comparar"),
    db: Session = Depends(get_db) if DB_AVAILABLE else None
):
    """
    Compara lecturas entre Blockchain y PostgreSQL

    Retorna comparación lado a lado de las últimas lecturas
    """

    if not DB_AVAILABLE or db is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="PostgreSQL no disponible. Solo se puede consultar blockchain."
        )

    try:
        # Obtener datos blockchain
        blockchain_service = BlockchainService()
        bc_readings = blockchain_service.get_all_readings()

        lecturas_bc = []
        for r in bc_readings:
            lecturas_bc.append({
                'sensor_id': r.sensor_id.decode('utf-8', errors='ignore'),
                'humidity': r.humidity_percentage,
                'temperature': r.temperature_celsius,
                'timestamp': datetime.fromtimestamp(r.timestamp / 1000),
                'alert_level': type(r.alert_level).__name__
            })

        # Ordenar por timestamp descendente
        lecturas_bc = sorted(lecturas_bc, key=lambda x: x['timestamp'], reverse=True)

        # Obtener datos PostgreSQL
        db_readings = db.query(ReadingHistory).order_by(
            ReadingHistory.timestamp.desc()
        ).all()

        lecturas_db = []
        for r in db_readings:
            lecturas_db.append({
                'sensor_id': r.sensor_id,
                'humidity': r.humidity_percentage,
                'temperature': r.temperature_celsius,
                'timestamp': r.timestamp,
                'tx_hash': r.tx_hash,
                'on_chain': r.on_chain
            })

        # Comparar y generar resultado
        comparaciones = []
        matches = 0
        diferencias = 0
        solo_bc = 0

        for bc_reading in lecturas_bc[:limit]:
            sql_match = encontrar_match(bc_reading, lecturas_db, tolerancia_seg=15)

            comparacion = {
                'sensor_id': bc_reading['sensor_id'],
                'timestamp_bc': bc_reading['timestamp'].isoformat(),
                'blockchain': {
                    'humidity': bc_reading['humidity'],
                    'temperature': bc_reading['temperature']
                },
                'postgresql': None,
                'match_status': 'solo_blockchain',
                'time_diff': None,
                'tx_hash': None
            }

            if sql_match:
                comparacion['postgresql'] = {
                    'humidity': sql_match['humidity'],
                    'temperature': sql_match['temperature'],
                    'on_chain': sql_match['on_chain']
                }
                comparacion['timestamp_db'] = sql_match['timestamp'].isoformat()
                comparacion['time_diff'] = round(sql_match['time_diff_seconds'], 2)
                comparacion['tx_hash'] = sql_match['tx_hash']

                # Verificar si coinciden los valores
                if (bc_reading['humidity'] == sql_match['humidity'] and
                    bc_reading['temperature'] == sql_match['temperature']):
                    comparacion['match_status'] = 'match'
                    matches += 1
                else:
                    comparacion['match_status'] = 'different_values'
                    diferencias += 1
            else:
                solo_bc += 1

            comparaciones.append(comparacion)

        # Resumen
        resumen = {
            'total_comparadas': limit,
            'matches': matches,
            'diferentes': diferencias,
            'solo_blockchain': solo_bc,
            'integridad_porcentaje': round((matches / (matches + diferencias) * 100) if (matches + diferencias) > 0 else 0, 2)
        }

        return {
            'success': True,
            'resumen': resumen,
            'comparaciones': comparaciones,
            'timestamp': datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error en auditoría: {str(e)}"
        )


@router.get("/summary")
async def audit_summary(
    db: Session = Depends(get_db) if DB_AVAILABLE else None
):
    """
    Resumen rápido de integridad
    """

    if not DB_AVAILABLE or db is None:
        return {
            'success': False,
            'message': 'PostgreSQL no disponible'
        }

    try:
        blockchain_service = BlockchainService()
        bc_readings = blockchain_service.get_all_readings()

        db_total = db.query(ReadingHistory).count()
        db_on_chain = db.query(ReadingHistory).filter(
            ReadingHistory.on_chain == True
        ).count()

        return {
            'success': True,
            'blockchain_total': len(bc_readings),
            'postgresql_total': db_total,
            'postgresql_on_chain': db_on_chain,
            'postgresql_archived': db_total - db_on_chain,
            'timestamp': datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error: {str(e)}"
        )
