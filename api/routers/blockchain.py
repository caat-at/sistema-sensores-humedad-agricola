"""
Router de API para transacciones blockchain
Endpoints para consultar el historial de transacciones en Cardano
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from api.database.connection import get_db
from api.database.models import TransactionLog

router = APIRouter(
    prefix="/api/blockchain",
    tags=["Blockchain"]
)


class TransactionResponse(BaseModel):
    """Response de transacción blockchain"""
    id: int
    tx_hash: str
    tx_type: str
    status: str
    submitted_at: datetime
    confirmed_at: Optional[datetime]
    error_message: Optional[str]
    explorer_url: str

    class Config:
        from_attributes = True


@router.get("/transactions", response_model=List[TransactionResponse])
async def get_blockchain_transactions(
    limit: int = Query(default=20, ge=1, le=100),
    tx_type: Optional[str] = Query(default=None, description="Filtrar por tipo: RegisterSensor, AddReading, etc."),
    status: Optional[str] = Query(default=None, description="Filtrar por estado: Pending, Confirmed, Failed"),
    db: Session = Depends(get_db)
):
    """
    Obtiene el historial de transacciones enviadas a blockchain

    - **limit**: Número de transacciones a retornar (1-100)
    - **tx_type**: Filtrar por tipo de transacción
    - **status**: Filtrar por estado

    Retorna las transacciones más recientes primero.
    """
    try:
        query = db.query(TransactionLog)

        # Filtros opcionales
        if tx_type:
            query = query.filter(TransactionLog.tx_type == tx_type)

        if status:
            query = query.filter(TransactionLog.status == status)

        # Ordenar por más reciente primero
        query = query.order_by(TransactionLog.submitted_at.desc())

        # Límite
        transactions = query.limit(limit).all()

        # Agregar URL del explorador
        result = []
        for tx in transactions:
            tx_dict = {
                "id": tx.id,
                "tx_hash": tx.tx_hash,
                "tx_type": tx.tx_type,
                "status": tx.status,
                "submitted_at": tx.submitted_at,
                "confirmed_at": tx.confirmed_at,
                "error_message": tx.error_message,
                "explorer_url": f"https://preview.cardanoscan.io/transaction/{tx.tx_hash}"
            }
            result.append(TransactionResponse(**tx_dict))

        return result

    except Exception as e:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener transacciones: {str(e)}"
        )


@router.get("/transactions/stats")
async def get_blockchain_stats(db: Session = Depends(get_db)):
    """
    Obtiene estadísticas de transacciones blockchain

    Retorna contadores por tipo y estado de transacciones.
    """
    try:
        from sqlalchemy import func

        # Total de transacciones
        total_tx = db.query(func.count(TransactionLog.id)).scalar()

        # Por estado
        confirmed = db.query(func.count(TransactionLog.id)).filter(
            TransactionLog.status == "Confirmed"
        ).scalar()

        pending = db.query(func.count(TransactionLog.id)).filter(
            TransactionLog.status == "Pending"
        ).scalar()

        failed = db.query(func.count(TransactionLog.id)).filter(
            TransactionLog.status == "Failed"
        ).scalar()

        # Por tipo
        by_type = db.query(
            TransactionLog.tx_type,
            func.count(TransactionLog.id).label('count')
        ).group_by(TransactionLog.tx_type).all()

        type_counts = {tx_type: count for tx_type, count in by_type}

        # Última transacción
        last_tx = db.query(TransactionLog).order_by(
            TransactionLog.submitted_at.desc()
        ).first()

        last_tx_info = None
        if last_tx:
            last_tx_info = {
                "tx_hash": last_tx.tx_hash,
                "tx_type": last_tx.tx_type,
                "status": last_tx.status,
                "submitted_at": last_tx.submitted_at.isoformat()
            }

        return {
            "total_transactions": total_tx or 0,
            "confirmed": confirmed or 0,
            "pending": pending or 0,
            "failed": failed or 0,
            "by_type": type_counts,
            "last_transaction": last_tx_info,
            "network": "Cardano Preview Testnet",
            "contract_address": "addr_test1wz873sjp5wenffd4x8jusc94kek42w4mwpuevnagkzkwsqg0j0aty"
        }

    except Exception as e:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener estadísticas: {str(e)}"
        )


@router.get("/transactions/{tx_hash}")
async def get_transaction_detail(
    tx_hash: str,
    db: Session = Depends(get_db)
):
    """
    Obtiene detalles de una transacción específica por su hash

    - **tx_hash**: Hash de la transacción en blockchain
    """
    try:
        tx = db.query(TransactionLog).filter(
            TransactionLog.tx_hash == tx_hash
        ).first()

        if not tx:
            from fastapi import HTTPException
            raise HTTPException(
                status_code=404,
                detail=f"Transacción {tx_hash} no encontrada"
            )

        return {
            "id": tx.id,
            "tx_hash": tx.tx_hash,
            "tx_type": tx.tx_type,
            "status": tx.status,
            "submitted_at": tx.submitted_at.isoformat(),
            "confirmed_at": tx.confirmed_at.isoformat() if tx.confirmed_at else None,
            "error_message": tx.error_message,
            "datum_snapshot": tx.datum_snapshot,
            "request_data": tx.request_data,
            "explorer_url": f"https://preview.cardanoscan.io/transaction/{tx.tx_hash}"
        }

    except Exception as e:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener detalle de transacción: {str(e)}"
        )
