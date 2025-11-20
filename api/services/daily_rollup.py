"""
Servicio de Rollup Diario
Agrupa las 24 lecturas del día en un único hash merkle y lo envía a blockchain
Reduce costos de blockchain en ~96%
"""
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_

from api.database.models import ReadingHistory, SensorHistory
from api.services.merkle_tree import MerkleTree, create_rollup_merkle
# from api.blockchain.client import BlockchainClient  # TODO: Implementar cliente blockchain


class DailyRollupService:
    """
    Servicio para crear y procesar rollups diarios de lecturas
    """

    def __init__(self, db: Session, blockchain_client: Optional[object] = None):
        """
        Inicializa el servicio de rollup

        Args:
            db: Sesión de base de datos
            blockchain_client: Cliente de blockchain (opcional para testing)
        """
        self.db = db
        self.blockchain_client = blockchain_client

    def get_pending_readings(self, sensor_id: str, date: datetime) -> List[Dict]:
        """
        Obtiene todas las lecturas de un sensor para un día específico que aún no están en rollup

        Args:
            sensor_id: ID del sensor
            date: Fecha del día a procesar

        Returns:
            Lista de lecturas pendientes
        """
        # Definir rango del día (00:00:00 a 23:59:59)
        start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1) - timedelta(microseconds=1)

        # Buscar lecturas que:
        # 1. No estén en blockchain todavía (on_chain=False)
        # 2. No estén en un rollup (rollup_batch_id IS NULL)
        # 3. Sean del sensor y fecha especificados
        readings = self.db.query(ReadingHistory).filter(
            and_(
                ReadingHistory.sensor_id == sensor_id,
                ReadingHistory.timestamp >= start_of_day,
                ReadingHistory.timestamp <= end_of_day,
                ReadingHistory.on_chain == False,
                ReadingHistory.rollup_batch_id.is_(None)
            )
        ).order_by(ReadingHistory.timestamp).all()

        # Convertir a lista de diccionarios
        return [
            {
                "id": r.id,
                "sensor_id": r.sensor_id,
                "humidity": r.humidity_percentage,
                "temperature": r.temperature_celsius,
                "timestamp": r.timestamp.isoformat()
            }
            for r in readings
        ]

    def get_all_sensors(self) -> List[str]:
        """
        Obtiene lista de todos los sensores activos

        Returns:
            Lista de IDs de sensores
        """
        # Obtener sensores registrados en sensors_history
        registered_sensors = self.db.query(SensorHistory.sensor_id).filter(
            SensorHistory.is_current == True
        ).distinct().all()

        # Obtener sensores con lecturas pendientes (on_chain=False)
        sensors_with_pending = self.db.query(ReadingHistory.sensor_id).filter(
            and_(
                ReadingHistory.on_chain == False,
                ReadingHistory.rollup_batch_id.is_(None)
            )
        ).distinct().all()

        # Combinar ambas listas y eliminar duplicados
        all_sensors = set([s.sensor_id for s in registered_sensors] + [s.sensor_id for s in sensors_with_pending])

        return list(all_sensors)

    def create_rollup(self, sensor_id: str, date: datetime) -> Optional[Dict]:
        """
        Crea un rollup para un sensor y fecha específicos

        Args:
            sensor_id: ID del sensor
            date: Fecha del día a procesar

        Returns:
            Diccionario con información del rollup creado o None si no hay lecturas
        """
        # Obtener lecturas pendientes
        readings = self.get_pending_readings(sensor_id, date)

        if not readings:
            print(f"No hay lecturas pendientes para {sensor_id} en {date.date()}")
            return None

        print(f"Creando rollup para {sensor_id}: {len(readings)} lecturas")

        # Crear merkle tree y obtener metadata
        rollup_data = create_rollup_merkle(readings)

        # Agregar información adicional
        rollup_data["reading_ids"] = [r["id"] for r in readings]
        rollup_data["created_at"] = datetime.now().isoformat()

        return rollup_data

    def send_rollup_to_blockchain(self, rollup_data: Dict) -> Optional[str]:
        """
        Envía el rollup a blockchain

        Args:
            rollup_data: Datos del rollup (merkle_root, estadísticas, etc)

        Returns:
            Transaction hash o None si falla
        """
        if not self.blockchain_client:
            print("[WARN] Blockchain client no disponible, simulando envío...")
            return f"simulated_tx_{rollup_data['merkle_root'][:16]}"

        try:
            # Preparar datum para blockchain
            datum = {
                "sensor_id": rollup_data["sensor_id"],
                "merkle_root": rollup_data["merkle_root"],
                "readings_count": rollup_data["readings_count"],
                "date": rollup_data["date"],
                "humidity_min": int(rollup_data["statistics"]["humidity_min"]),
                "humidity_max": int(rollup_data["statistics"]["humidity_max"]),
                "humidity_avg": int(rollup_data["statistics"]["humidity_avg"]),
                "temperature_min": int(rollup_data["statistics"]["temperature_min"]),
                "temperature_max": int(rollup_data["statistics"]["temperature_max"]),
                "temperature_avg": int(rollup_data["statistics"]["temperature_avg"]),
                "first_reading": rollup_data["first_reading"],
                "last_reading": rollup_data["last_reading"],
                "rollup_type": "daily"
            }

            # Enviar a blockchain
            tx_hash = self.blockchain_client.submit_rollup(datum)
            print(f"[OK] Rollup enviado a blockchain: {tx_hash}")

            return tx_hash

        except Exception as e:
            print(f"[ERROR] Error enviando rollup a blockchain: {e}")
            return None

    def mark_readings_as_rolled_up(self, reading_ids: List[int], batch_id: str, tx_hash: Optional[str]):
        """
        Marca las lecturas como incluidas en un rollup

        Args:
            reading_ids: IDs de las lecturas incluidas
            batch_id: ID del batch (merkle_root)
            tx_hash: Hash de la transacción en blockchain
        """
        self.db.query(ReadingHistory).filter(
            ReadingHistory.id.in_(reading_ids)
        ).update({
            "rollup_batch_id": batch_id,
            "on_chain": True if tx_hash else False,
            "tx_hash": tx_hash
        }, synchronize_session=False)

        self.db.commit()
        print(f"[OK] Marcadas {len(reading_ids)} lecturas como parte del rollup {batch_id[:16]}...")

    def process_daily_rollup(self, sensor_id: Optional[str] = None, date: Optional[datetime] = None) -> Dict:
        """
        Procesa rollups diarios para uno o todos los sensores

        Args:
            sensor_id: ID del sensor (opcional, si None procesa todos)
            date: Fecha a procesar (opcional, si None usa ayer)

        Returns:
            Diccionario con resumen del procesamiento
        """
        # Usar ayer por defecto (día completo más reciente)
        if date is None:
            date = datetime.now() - timedelta(days=1)

        # Determinar sensores a procesar
        if sensor_id:
            sensors = [sensor_id]
        else:
            sensors = self.get_all_sensors()

        results = {
            "date": date.date().isoformat(),
            "sensors_processed": 0,
            "total_readings": 0,
            "successful_rollups": 0,
            "failed_rollups": 0,
            "rollups": []
        }

        # Procesar cada sensor
        for sensor in sensors:
            try:
                # Crear rollup
                rollup_data = self.create_rollup(sensor, date)

                if rollup_data is None:
                    continue

                results["sensors_processed"] += 1
                results["total_readings"] += rollup_data["readings_count"]

                # Enviar a blockchain
                tx_hash = self.send_rollup_to_blockchain(rollup_data)

                if tx_hash:
                    # Marcar lecturas como procesadas
                    self.mark_readings_as_rolled_up(
                        rollup_data["reading_ids"],
                        rollup_data["merkle_root"],
                        tx_hash
                    )
                    results["successful_rollups"] += 1

                    results["rollups"].append({
                        "sensor_id": sensor,
                        "merkle_root": rollup_data["merkle_root"],
                        "tx_hash": tx_hash,
                        "readings_count": rollup_data["readings_count"],
                        "status": "success"
                    })
                else:
                    results["failed_rollups"] += 1
                    results["rollups"].append({
                        "sensor_id": sensor,
                        "merkle_root": rollup_data["merkle_root"],
                        "status": "failed",
                        "error": "Failed to submit to blockchain"
                    })

            except Exception as e:
                results["failed_rollups"] += 1
                results["rollups"].append({
                    "sensor_id": sensor,
                    "status": "error",
                    "error": str(e)
                })
                print(f"[ERROR] Error procesando rollup para {sensor}: {e}")

        return results

    def verify_reading_in_rollup(self, reading_id: int) -> Dict:
        """
        Verifica que una lectura específica esté correctamente incluida en su rollup

        Args:
            reading_id: ID de la lectura a verificar

        Returns:
            Diccionario con resultado de la verificación
        """
        # Obtener la lectura
        reading = self.db.query(ReadingHistory).filter(
            ReadingHistory.id == reading_id
        ).first()

        if not reading:
            return {"valid": False, "error": "Lectura no encontrada"}

        if not reading.rollup_batch_id:
            return {"valid": False, "error": "Lectura no está en un rollup"}

        # Obtener todas las lecturas del mismo rollup
        rollup_readings = self.db.query(ReadingHistory).filter(
            ReadingHistory.rollup_batch_id == reading.rollup_batch_id
        ).order_by(ReadingHistory.timestamp).all()

        # Reconstruir merkle tree
        readings_data = [
            {
                "sensor_id": r.sensor_id,
                "humidity": r.humidity_percentage,
                "temperature": r.temperature_celsius,
                "timestamp": r.timestamp.isoformat()
            }
            for r in rollup_readings
        ]

        tree = MerkleTree(readings_data)

        # Encontrar índice de la lectura
        reading_index = next(
            (i for i, r in enumerate(rollup_readings) if r.id == reading_id),
            None
        )

        if reading_index is None:
            return {"valid": False, "error": "No se pudo encontrar la lectura en el rollup"}

        # Obtener prueba merkle
        proof = tree.get_proof(reading_index)

        # Verificar
        leaf_hash = tree.leaves[reading_index]
        is_valid = MerkleTree.verify_proof(leaf_hash, proof, reading.rollup_batch_id)

        return {
            "valid": is_valid,
            "reading_id": reading_id,
            "rollup_batch_id": reading.rollup_batch_id,
            "merkle_root": tree.get_root(),
            "tx_hash": reading.tx_hash,
            "proof": proof,
            "leaf_hash": leaf_hash
        }
