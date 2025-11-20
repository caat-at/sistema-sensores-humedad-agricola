@echo off
echo ========================================
echo Sistema de Sensores de Humedad Agricola
echo ========================================
echo.

REM Activar entorno virtual
echo [1/2] Activando entorno virtual...
call .venv\Scripts\activate.bat

REM Iniciar servidor
echo [2/2] Iniciando servidor FastAPI...
echo.
echo Dashboard: http://localhost:8000/dashboard
echo API Docs:  http://localhost:8000/docs
echo Health:    http://localhost:8000/api/health
echo.
echo Presiona Ctrl+C para detener el servidor
echo ========================================
echo.

python -m uvicorn api.main:app --reload --port 8000
