# Script de inicio para PowerShell
# Sistema de Sensores de Humedad Agrícola

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Sistema de Sensores de Humedad Agricola" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Activar entorno virtual
Write-Host "[1/2] Activando entorno virtual..." -ForegroundColor Yellow
& ".\.venv\Scripts\Activate.ps1"

# Iniciar servidor
Write-Host "[2/2] Iniciando servidor FastAPI..." -ForegroundColor Yellow
Write-Host ""
Write-Host "Dashboard: " -NoNewline -ForegroundColor Green
Write-Host "http://localhost:8000/dashboard" -ForegroundColor White
Write-Host "API Docs:  " -NoNewline -ForegroundColor Green
Write-Host "http://localhost:8000/docs" -ForegroundColor White
Write-Host "Health:    " -NoNewline -ForegroundColor Green
Write-Host "http://localhost:8000/api/health" -ForegroundColor White
Write-Host ""
Write-Host "Presiona Ctrl+C para detener el servidor" -ForegroundColor Red
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

python -m uvicorn api.main:app --reload --port 8000
