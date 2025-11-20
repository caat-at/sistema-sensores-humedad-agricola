# -*- coding: utf-8 -*-
"""
API REST para Sistema de Sensores de Humedad Agrícola
Cardano Blockchain

Esta API expone todas las operaciones CRUD del contrato inteligente OpShin.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import sys
from pathlib import Path

# Agregar pycardano-client al path
pycardano_path = Path(__file__).parent.parent / "pycardano-client"
sys.path.insert(0, str(pycardano_path))

from api.routers import sensors, readings, stats, audit, blockchain, verification
try:
    from api.routers import alerts
    ALERTS_AVAILABLE = True
except ImportError:
    ALERTS_AVAILABLE = False

try:
    from api.routers import rollups
    ROLLUPS_AVAILABLE = True
except ImportError:
    ROLLUPS_AVAILABLE = False

# Crear aplicación FastAPI
app = FastAPI(
    title="Sensores de Humedad Agrícola API",
    description="""
    API REST para gestionar sensores de humedad agrícola en Cardano Blockchain.

    ## Características

    * **CRUD Completo de Sensores**: Registrar, listar, actualizar y desactivar sensores
    * **Gestión de Lecturas**: Agregar y consultar lecturas de humedad y temperatura
    * **Estadísticas en Tiempo Real**: Análisis automático de datos
    * **Niveles de Alerta**: Cálculo automático (Normal, Low, High, Critical)
    * **Blockchain**: Todas las operaciones se registran en Cardano Preview Testnet

    ## Tecnologías

    * **Backend**: FastAPI + Python
    * **Blockchain**: Cardano (OpShin smart contracts)
    * **Transaction Builder**: Hybrid Python (PyCardano) + JavaScript (Lucid)

    ## Enlaces

    * [Documentación del Proyecto](https://github.com/...)
    * [Cardano Explorer](https://preview.cardanoscan.io/)
    """,
    version="1.0.0",
    contact={
        "name": "Sistema de Sensores Agrícolas",
        "url": "https://github.com/..."
    },
    license_info={
        "name": "MIT",
    }
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar dominios permitidos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
app.include_router(sensors.router)
app.include_router(readings.router)
app.include_router(stats.router)
app.include_router(audit.router)
app.include_router(blockchain.router)
app.include_router(verification.router)
if ALERTS_AVAILABLE:
    app.include_router(alerts.router)
if ROLLUPS_AVAILABLE:
    app.include_router(rollups.router)

# Servir dashboard estático
frontend_path = Path(__file__).parent.parent / "frontend" / "dashboard"
app.mount("/static", StaticFiles(directory=str(frontend_path)), name="static")


@app.get("/", include_in_schema=False)
async def root():
    """Redirige al dashboard"""
    return RedirectResponse(url="/dashboard")


@app.get("/dashboard", include_in_schema=False)
async def dashboard():
    """Servir dashboard interactivo"""
    dashboard_file = frontend_path / "index.html"
    return FileResponse(dashboard_file)


@app.get("/api/health")
async def health_check():
    """
    Health check endpoint

    Verifica que la API esté funcionando correctamente
    """
    # Obtener estado del scheduler si está disponible
    scheduler_status = {}
    if ROLLUPS_AVAILABLE:
        try:
            from api.scheduler import get_scheduler_status
            scheduler_status = get_scheduler_status()
        except:
            scheduler_status = {"running": False, "error": "Scheduler not initialized"}

    return {
        "status": "healthy",
        "version": "1.0.0",
        "blockchain": "Cardano Preview Testnet",
        "scheduler": scheduler_status
    }


@app.on_event("startup")
async def startup_event():
    """
    Evento que se ejecuta al iniciar la aplicación
    Inicia el scheduler de rollups diarios
    """
    if ROLLUPS_AVAILABLE:
        try:
            from api.scheduler import start_scheduler
            start_scheduler()
            print("[OK] Scheduler de rollups iniciado correctamente")
        except Exception as e:
            print(f"[WARN] No se pudo iniciar el scheduler: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """
    Evento que se ejecuta al detener la aplicación
    Detiene el scheduler gracefully
    """
    if ROLLUPS_AVAILABLE:
        try:
            from api.scheduler import stop_scheduler
            stop_scheduler()
            print("[OK] Scheduler detenido correctamente")
        except Exception as e:
            print(f"[WARN] Error deteniendo scheduler: {e}")


# Manejo de errores global
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Manejo de errores de validación"""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation Error",
            "detail": exc.errors()
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Manejo de errores generales"""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal Server Error",
            "detail": str(exc)
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
