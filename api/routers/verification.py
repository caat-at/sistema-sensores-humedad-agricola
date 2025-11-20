# -*- coding: utf-8 -*-
"""
Router para endpoint de verificación blockchain vs PostgreSQL
"""

import sys
from pathlib import Path
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime
from typing import Dict, List

# Agregar pycardano-client al path
pycardano_path = Path(__file__).parent.parent.parent / "pycardano-client"
sys.path.insert(0, str(pycardano_path))

from api.services.blockchain_service import BlockchainService
from api.database.connection import get_db
from api.database.models import ReadingHistory

router = APIRouter(
    prefix="/api/verification",
    tags=["verification"]
)


@router.get("/blockchain-vs-db")
async def verify_blockchain_vs_db(db: Session = Depends(get_db)):
    """
    Verifica que los datos en blockchain coinciden con PostgreSQL

    Retorna:
    - Lecturas en PostgreSQL (on_chain=True)
    - Lecturas en Blockchain
    - Rollups creados
    - Comparación de datos
    """

    # Obtener lecturas de PostgreSQL con on_chain=True
    db_readings = db.query(ReadingHistory).filter(
        ReadingHistory.on_chain == True
    ).order_by(ReadingHistory.timestamp.desc()).limit(50).all()

    # Agrupar por rollup_batch_id
    rollup_groups = {}
    individual_readings = []

    for reading in db_readings:
        if reading.rollup_batch_id:
            batch_id = reading.rollup_batch_id
            if batch_id not in rollup_groups:
                rollup_groups[batch_id] = {
                    'tx_hash': reading.tx_hash,
                    'readings': []
                }
            rollup_groups[batch_id]['readings'].append({
                'sensor_id': reading.sensor_id,
                'humidity': reading.humidity_percentage,
                'temperature': reading.temperature_celsius,
                'timestamp': reading.timestamp.isoformat()
            })
        else:
            individual_readings.append({
                'sensor_id': reading.sensor_id,
                'humidity': reading.humidity_percentage,
                'temperature': reading.temperature_celsius,
                'timestamp': reading.timestamp.isoformat(),
                'tx_hash': reading.tx_hash
            })

    # Formatear rollups para respuesta
    rollups = [
        {
            'batch_id': batch_id,
            'tx_hash': data['tx_hash'],
            'readings_count': len(data['readings']),
            'readings': data['readings']
        }
        for batch_id, data in rollup_groups.items()
    ]

    # Obtener lecturas de blockchain
    blockchain_readings = []
    blockchain_count = 0
    blockchain_error = None

    try:
        blockchain = BlockchainService()
        bc_readings = blockchain.get_all_readings()
        blockchain_count = len(bc_readings)

        # Convertir a formato simple (solo las primeras 20 para no sobrecargar)
        for r in bc_readings[:20]:
            blockchain_readings.append({
                'sensor_id': r.sensor_id.decode('utf-8', errors='ignore'),
                'humidity': r.humidity_percentage,
                'temperature': r.temperature_celsius,
                'timestamp': datetime.fromtimestamp(r.timestamp / 1000).isoformat(),
                'alert_level': type(r.alert_level).__name__
            })
    except Exception as e:
        blockchain_error = str(e)

    # Calcular estadísticas
    total_db_readings = len(db_readings)
    total_rollup_readings = sum(len(g['readings']) for g in rollup_groups.values())

    return {
        'database': {
            'total_readings': total_db_readings,
            'rollups': rollups,
            'rollup_count': len(rollups),
            'readings_in_rollups': total_rollup_readings,
            'individual_readings': individual_readings,
            'individual_count': len(individual_readings)
        },
        'blockchain': {
            'total_readings': blockchain_count,
            'sample_readings': blockchain_readings,
            'error': blockchain_error
        },
        'comparison': {
            'db_total': total_db_readings,
            'blockchain_total': blockchain_count,
            'difference': blockchain_count - total_db_readings if blockchain_count > 0 else None,
            'matches': blockchain_count == total_db_readings if blockchain_count > 0 else False
        }
    }
