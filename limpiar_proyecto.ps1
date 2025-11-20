# Script para limpiar archivos innecesarios del proyecto
# Ejecutar con: .\limpiar_proyecto.ps1

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "LIMPIEZA DE PROYECTO" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Crear carpeta de respaldo
$backupFolder = "backup_$(Get-Date -Format 'yyyy-MM-dd_HHmmss')"
Write-Host "[1/4] Creando carpeta de respaldo: $backupFolder" -ForegroundColor Yellow
New-Item -ItemType Directory -Path $backupFolder -Force | Out-Null

# Lista de archivos a eliminar (mover a backup primero)
$archivosEliminar = @(
    # Scripts de debug/test
    "debug_sensor_004.py",
    "cleanup_datum.py",
    "cleanup_datum_pycardano.py",
    "cleanup_datum_simple.py",
    "analyze_datum_content.py",
    "test_rollup_system.py",
    "apply_rollup_migration.py",

    # Scripts utilitarios temporales
    "check_pendientes.py",
    "ejecutar_rollup_manual.py",
    "actualizar_intervalo_60min.py",
    "actualizar_intervalos_api.py",
    "update_intervals_direct.py",

    # Scripts de auditoría duplicados
    "audit_data_integrity.py",
    "compare_blockchain_sql.py",
    "verificar_blockchain_vs_db.py",

    # Documentación obsoleta
    "LIMPIEZA_COMPLETADA.md",
    "MIGRACION_OPSHIN.md",
    "MVP_OPCION_B_RESUMEN.md",
    "RUTA_PRACTICA_MVP.md",
    "EXITO_INICIALIZACION.md",
    "ESTADO_ACTUAL.md",
    "RESUMEN_SESION_2025-10-14.md",
    "PROGRESO_REGISTER_SENSOR.md",
    "INVESTIGACION_PYCARDANO_TX.md",
    "EXITO_REGISTRO_SENSORES.md",
    "LUCID_VS_LUCID_EVOLUTION.md",
    "EXITO_ADD_READING.md",
    "RESUMEN_FINAL_MVP.md",
    "DECODE_DATUM_ENHANCED.md",
    "GUIA_DEMO.md",
    "MEJORAS_DECODE_DATUM.md",
    "RESUMEN_MEJORAS_DECODE.md",
    "EXITO_UPDATE_SENSOR.md",
    "RESUMEN_CRUD_COMPLETADO.md",
    "EXITO_DEACTIVATE_SENSOR.md",
    "RESUMEN_FINAL_CRUD_100.md",
    "API_REST_COMPLETADA.md",
    "RESUMEN_FINAL_API_REST.md",
    "QUICK_START.md",
    "FRONTEND_DASHBOARD_COMPLETADO.md",
    "TXHASH_DISPLAY_AGREGADO.md",
    "TXHASH_EN_HISTORIAL_COMPLETADO.md",
    "DEDUPLICACION_SENSORES_COMPLETADA.md",
    "PREVENCION_DUPLICADOS_SENSOR_ID.md",
    "DISENO_OPTIMIZADO.md",
    "GUIA_IMPLEMENTACION_OPTIMIZADA.md",
    "RESUMEN_SESION.md",
    "IMPLEMENTACION_COMPLETA_CODIGO.md",
    "PASOS_INSTALACION_POSTGRES.md",
    "RESUMEN_BASE_DATOS_COMPLETA.md",
    "RESUMEN_SESION_ACTUAL.md",
    "INTEGRACION_POSTGRESQL_COMPLETA.md",
    "RESUMEN_FINAL_SESION.md",
    "DEPLOY_GITHUB.md",
    "PASOS_SUBIR_GITHUB.md",
    "GUIA_CONFIGURACION_CREDENCIALES.md",
    "GUIA_USO_SENSORES.md",
    "CONFIGURACION_SENSOR_USUARIO.md",
    "CONFIG_DHT11.md",
    "ARDUINO_UNO_DHT11.md",
    "COMO_PROBAR_ROLLUPS.md",
    "VERIFICAR_ROLLUPS.md",
    "GUIA_INICIO_RAPIDO.md",
    "INSTRUCCIONES_USO.md",
    "UBICACION_PROYECTO.md",
    "PASOS_SIGUIENTES.md",
    "ROADMAP.md"
)

Write-Host "[2/4] Moviendo archivos a backup..." -ForegroundColor Yellow
$movedCount = 0
foreach ($archivo in $archivosEliminar) {
    if (Test-Path $archivo) {
        Move-Item -Path $archivo -Destination $backupFolder -Force
        Write-Host "  ✓ $archivo" -ForegroundColor Green
        $movedCount++
    }
}
Write-Host "  Total: $movedCount archivos movidos a backup" -ForegroundColor Cyan

# Crear estructura de carpetas organizada
Write-Host ""
Write-Host "[3/4] Creando estructura de carpetas..." -ForegroundColor Yellow

# Crear carpeta scripts/
if (-not (Test-Path "scripts")) {
    New-Item -ItemType Directory -Path "scripts" -Force | Out-Null
}

# Mover scripts de producción a scripts/
$scriptsProduccion = @(
    "sensor_fisico_simulado.py",
    "ejemplo_agregar_sensor.py",
    "demo_rapido.py"
)

foreach ($script in $scriptsProduccion) {
    if (Test-Path $script) {
        Move-Item -Path $script -Destination "scripts\" -Force
        Write-Host "  ✓ scripts/$script" -ForegroundColor Green
    }
}

# Crear carpeta utils/
if (-not (Test-Path "utils")) {
    New-Item -ItemType Directory -Path "utils" -Force | Out-Null
}

# Mover utilidades a utils/
$utilidades = @(
    "audit_data_integrity_v2.py",
    "mqtt_gateway.py",
    "nodo_sensor_mqtt.py",
    "arduino_serial_bridge.py"
)

foreach ($util in $utilidades) {
    if (Test-Path $util) {
        Move-Item -Path $util -Destination "utils\" -Force
        Write-Host "  ✓ utils/$util" -ForegroundColor Green
    }
}

# Crear carpeta docs/
if (-not (Test-Path "docs")) {
    New-Item -ItemType Directory -Path "docs" -Force | Out-Null
}

# Mover documentación técnica a docs/
$documentacion = @(
    "API_EJEMPLOS.md",
    "HARDWARE_SENSORES_FISICOS.md",
    "SISTEMA_ROLLUPS_MERKLE.md",
    "ARQUITECTURAS_CAPTURA_DATOS.md",
    "CAPTURA_DATOS_NODOS_SENSORES.md",
    "PLAN_OPTIMIZACION_COSTOS.md",
    "DEMO_SISTEMA_COMPLETO.md",
    "DASHBOARD_COMPLETADO.md",
    "PROGRESO_POSTGRESQL_PYCARDANO.md"
)

foreach ($doc in $documentacion) {
    if (Test-Path $doc) {
        Move-Item -Path $doc -Destination "docs\" -Force
        Write-Host "  ✓ docs/$doc" -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "[4/4] Resumen de la limpieza:" -ForegroundColor Yellow
Write-Host "  • Archivos eliminados (en backup): $movedCount" -ForegroundColor Cyan
Write-Host "  • Backup creado en: $backupFolder" -ForegroundColor Cyan
Write-Host "  • Carpetas organizadas: scripts/, utils/, docs/" -ForegroundColor Cyan

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "✓ LIMPIEZA COMPLETADA" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "ESTRUCTURA FINAL:" -ForegroundColor Cyan
Write-Host "  sistema-sensores-humedad-agricola/" -ForegroundColor White
Write-Host "  ├── api/              (Backend FastAPI)" -ForegroundColor Gray
Write-Host "  ├── pycardano-client/ (Cliente Blockchain)" -ForegroundColor Gray
Write-Host "  ├── contracts/        (Smart Contracts)" -ForegroundColor Gray
Write-Host "  ├── frontend/         (Dashboard Web)" -ForegroundColor Gray
Write-Host "  ├── scripts/          (Scripts de producción)" -ForegroundColor Gray
Write-Host "  ├── utils/            (Utilidades)" -ForegroundColor Gray
Write-Host "  ├── docs/             (Documentación técnica)" -ForegroundColor Gray
Write-Host "  ├── multisensor_fisico.py (Script principal)" -ForegroundColor Gray
Write-Host "  ├── README.md         (Documentación principal)" -ForegroundColor Gray
Write-Host "  ├── INICIO_RAPIDO.md  (Guía de inicio)" -ForegroundColor Gray
Write-Host "  └── TROUBLESHOOTING.md" -ForegroundColor Gray
Write-Host ""
Write-Host "Nota: Los archivos eliminados estan en '$backupFolder' por seguridad" -ForegroundColor Yellow
