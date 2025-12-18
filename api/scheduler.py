"""
Scheduler para ejecutar rollups diarios automáticamente
Usa APScheduler para ejecutar tareas periódicas
"""
import logging
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from api.database.connection import SessionLocal
from api.services.daily_rollup import DailyRollupService

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Crear scheduler global
scheduler = AsyncIOScheduler()


async def run_daily_rollup_job():
    """
    Tarea que ejecuta el rollup diario para todos los sensores
    Se ejecuta automáticamente a medianoche
    """
    logger.info("=" * 60)
    logger.info("INICIANDO ROLLUP DIARIO AUTOMÁTICO")
    logger.info(f"Timestamp: {datetime.now().isoformat()}")
    logger.info("=" * 60)

    db = SessionLocal()
    try:
        # Crear servicio de blockchain
        from api.services.blockchain_service import BlockchainService
        blockchain_service = BlockchainService()

        # Crear servicio de rollup con blockchain client
        rollup_service = DailyRollupService(db, blockchain_service)

        # Procesar rollup de ayer (día completo más reciente)
        yesterday = datetime.now() - timedelta(days=1)

        logger.info(f"Procesando lecturas del día: {yesterday.date()}")

        # Ejecutar rollup para todos los sensores
        result = rollup_service.process_daily_rollup(
            sensor_id=None,  # Procesar todos los sensores
            date=yesterday
        )

        # Log de resultados
        logger.info("-" * 60)
        logger.info("RESULTADOS DEL ROLLUP:")
        logger.info(f"  Fecha: {result['date']}")
        logger.info(f"  Sensores procesados: {result['sensors_processed']}")
        logger.info(f"  Total de lecturas: {result['total_readings']}")
        logger.info(f"  Rollups exitosos: {result['successful_rollups']}")
        logger.info(f"  Rollups fallidos: {result['failed_rollups']}")

        # Log detallado de cada rollup
        for rollup in result['rollups']:
            status_emoji = "[OK]" if rollup['status'] == 'success' else "[FAIL]"
            logger.info(f"  {status_emoji} {rollup['sensor_id']}: {rollup.get('readings_count', 0)} lecturas")
            if rollup['status'] == 'success':
                logger.info(f"     TX Hash: {rollup.get('tx_hash', 'N/A')[:16]}...")
                logger.info(f"     Merkle Root: {rollup.get('merkle_root', 'N/A')[:16]}...")

        logger.info("=" * 60)
        logger.info("ROLLUP DIARIO COMPLETADO")
        logger.info("=" * 60)

        return result

    except Exception as e:
        logger.error("=" * 60)
        logger.error("ERROR EN ROLLUP DIARIO")
        logger.error(f"Error: {str(e)}")
        logger.error("=" * 60)
        raise

    finally:
        db.close()


async def retry_failed_rollups():
    """
    Tarea que reintenta errores de rollup no resueltos
    Se ejecuta automáticamente cada 6 horas
    """
    logger.info("=" * 60)
    logger.info("INICIANDO REINTENTOS DE ROLLUPS FALLIDOS")
    logger.info(f"Timestamp: {datetime.now().isoformat()}")
    logger.info("=" * 60)

    db = SessionLocal()
    try:
        from api.database.models import RollupError
        from api.services.blockchain_service import BlockchainService

        # Buscar errores no resueltos con menos de 3 reintentos
        unresolved_errors = db.query(RollupError).filter(
            RollupError.resolved == False,
            RollupError.retry_count < 3
        ).all()

        if not unresolved_errors:
            logger.info("No hay errores pendientes de reintento")
            logger.info("=" * 60)
            return {"retries": 0, "successful": 0, "failed": 0}

        logger.info(f"Encontrados {len(unresolved_errors)} errores para reintentar")

        blockchain_service = BlockchainService()
        rollup_service = DailyRollupService(db, blockchain_service)

        successful_retries = 0
        failed_retries = 0

        for error in unresolved_errors:
            logger.info("-" * 60)
            logger.info(f"Reintentando error ID {error.id} - Sensor: {error.sensor_id}")
            logger.info(f"  Tipo: {error.error_type}")
            logger.info(f"  Fecha original: {error.execution_date}")
            logger.info(f"  Reintentos previos: {error.retry_count}")

            try:
                # Incrementar contador de reintentos
                error.retry_count += 1

                # Si el error tiene rollup_batch_id, significa que se creó el rollup pero falló el envío
                if error.rollup_batch_id and error.readings_count:
                    logger.info(f"  Reintentando envío de rollup existente: {error.rollup_batch_id[:16]}...")

                    # Aquí podríamos reintentar el envío del rollup existente
                    # Por ahora, marcamos como no resuelto pero con más reintentos
                    # TODO: Implementar reenvío de rollup existente

                else:
                    # Recrear rollup desde cero
                    logger.info(f"  Recreando rollup desde cero...")

                    rollup_data = rollup_service.create_rollup(
                        sensor_id=error.sensor_id,
                        date=error.execution_date
                    )

                    if rollup_data:
                        tx_hash = rollup_service.send_rollup_to_blockchain(rollup_data)

                        if tx_hash:
                            # Marcar lecturas como procesadas
                            rollup_service.mark_readings_as_rolled_up(
                                rollup_data["reading_ids"],
                                rollup_data["merkle_root"],
                                tx_hash
                            )

                            # Marcar error como resuelto
                            error.resolved = True
                            error.resolved_at = datetime.now()

                            successful_retries += 1
                            logger.info(f"  [OK] Reintento exitoso! TX: {tx_hash[:16]}...")

                        else:
                            failed_retries += 1
                            logger.info(f"  [FAIL] Reintento falló en envío a blockchain")
                    else:
                        failed_retries += 1
                        logger.info(f"  [FAIL] No hay lecturas para procesar")

                db.commit()

            except Exception as retry_error:
                failed_retries += 1
                logger.error(f"  [ERROR] Error en reintento: {str(retry_error)}")
                db.rollback()

        logger.info("-" * 60)
        logger.info("RESULTADOS DE REINTENTOS:")
        logger.info(f"  Total procesados: {len(unresolved_errors)}")
        logger.info(f"  Exitosos: {successful_retries}")
        logger.info(f"  Fallidos: {failed_retries}")
        logger.info("=" * 60)
        logger.info("REINTENTOS COMPLETADOS")
        logger.info("=" * 60)

        return {
            "retries": len(unresolved_errors),
            "successful": successful_retries,
            "failed": failed_retries
        }

    except Exception as e:
        logger.error("=" * 60)
        logger.error("ERROR EN REINTENTOS")
        logger.error(f"Error: {str(e)}")
        logger.error("=" * 60)
        raise

    finally:
        db.close()


def start_scheduler():
    """
    Inicia el scheduler con las tareas programadas

    Tareas configuradas:
    - Rollup diario: Ejecuta a las 00:05 AM (12:05 AM) todos los días
    - Reintentos de rollups fallidos: Cada 6 horas

    Si el servidor estaba apagado cuando debía ejecutarse una tarea:
    - La tarea se ejecutará INMEDIATAMENTE al iniciar el servidor
    - Luego continuará con el horario normal
    """
    # Tarea 1: Rollup diario a las 00:05 AM (12:05 AM)
    scheduler.add_job(
        run_daily_rollup_job,
        trigger=CronTrigger(hour=0, minute=5),  # 00:05 AM (12:05 AM)
        id='daily_rollup',
        name='Rollup diario de lecturas',
        replace_existing=True,
        misfire_grace_time=None,  # Sin límite - ejecutar sin importar cuánto tiempo pasó
        coalesce=True,  # Combinar múltiples ejecuciones perdidas en una sola
        max_instances=1  # Solo una instancia a la vez
    )

    # Tarea 2: Reintentos de rollups fallidos cada 6 horas
    scheduler.add_job(
        retry_failed_rollups,
        trigger=CronTrigger(hour='*/6'),  # Cada 6 horas (00:00, 06:00, 12:00, 18:00)
        id='retry_failed_rollups',
        name='Reintentos de rollups fallidos',
        replace_existing=True,
        misfire_grace_time=None,  # Sin límite - ejecutar sin importar cuánto tiempo pasó
        coalesce=True,  # Combinar múltiples ejecuciones perdidas en una sola
        max_instances=1  # Solo una instancia a la vez
    )

    logger.info("=" * 60)
    logger.info("SCHEDULER INICIADO")
    logger.info("=" * 60)
    logger.info("Tareas programadas:")
    logger.info("  - Rollup diario: Todos los días a las 00:05 AM (12:05 AM)")
    logger.info("  - Reintentos de errores: Cada 6 horas (00:00, 06:00, 12:00, 18:00)")
    logger.info("")
    logger.info("Configuración de recuperación:")
    logger.info("  - Si el servidor estaba apagado, las tareas perdidas se ejecutan INMEDIATAMENTE")
    logger.info("  - Luego continúan con su horario normal")
    logger.info("=" * 60)

    # Iniciar scheduler
    scheduler.start()

    return scheduler


def stop_scheduler():
    """
    Detiene el scheduler gracefully
    """
    if scheduler.running:
        scheduler.shutdown(wait=True)
        logger.info("Scheduler detenido")


def get_scheduler_status():
    """
    Obtiene el estado actual del scheduler

    Returns:
        dict: Información sobre el scheduler y sus tareas
    """
    if not scheduler.running:
        return {
            "running": False,
            "jobs": []
        }

    jobs = []
    for job in scheduler.get_jobs():
        next_run = job.next_run_time
        jobs.append({
            "id": job.id,
            "name": job.name,
            "next_run": next_run.isoformat() if next_run else None,
            "trigger": str(job.trigger)
        })

    return {
        "running": True,
        "jobs": jobs
    }


def run_manual_rollup():
    """
    Ejecuta el rollup manualmente (para testing o forzar ejecución)

    Returns:
        dict: Resultado del rollup
    """
    import asyncio

    logger.info("Ejecutando rollup manual...")

    # Ejecutar la tarea de rollup
    result = asyncio.run(run_daily_rollup_job())

    return result
