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
        # Crear servicio de rollup
        rollup_service = DailyRollupService(db)

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
            status_emoji = "✅" if rollup['status'] == 'success' else "❌"
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


def start_scheduler():
    """
    Inicia el scheduler con las tareas programadas

    Tareas configuradas:
    - Rollup diario: Ejecuta a las 00:05 AM todos los días
    """
    # Tarea 1: Rollup diario a las 00:05 AM
    scheduler.add_job(
        run_daily_rollup_job,
        trigger=CronTrigger(hour=0, minute=5),  # 00:05 AM (12:05 AM)
        id='daily_rollup',
        name='Rollup diario de lecturas',
        replace_existing=True,
        misfire_grace_time=3600  # Permitir 1 hora de retraso si el servidor estaba apagado
    )

    logger.info("=" * 60)
    logger.info("SCHEDULER INICIADO")
    logger.info("=" * 60)
    logger.info("Tareas programadas:")
    logger.info("  - Rollup diario: Todos los días a las 00:05 AM (12:05 AM)")
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
