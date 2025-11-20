@echo off
echo ========================================
echo LIMPIEZA DEL PROYECTO
echo ========================================
echo.

REM Mover scripts de debug y test
echo [1/6] Moviendo scripts de debug...
if exist debug_sensor_004.py move /Y debug_sensor_004.py backup_limpieza\
if exist cleanup_datum.py move /Y cleanup_datum.py backup_limpieza\
if exist cleanup_datum_pycardano.py move /Y cleanup_datum_pycardano.py backup_limpieza\
if exist cleanup_datum_simple.py move /Y cleanup_datum_simple.py backup_limpieza\
if exist analyze_datum_content.py move /Y analyze_datum_content.py backup_limpieza\
if exist test_rollup_system.py move /Y test_rollup_system.py backup_limpieza\
if exist apply_rollup_migration.py move /Y apply_rollup_migration.py backup_limpieza\
if exist check_pendientes.py move /Y check_pendientes.py backup_limpieza\
if exist ejecutar_rollup_manual.py move /Y ejecutar_rollup_manual.py backup_limpieza\
if exist actualizar_intervalo_60min.py move /Y actualizar_intervalo_60min.py backup_limpieza\
if exist actualizar_intervalos_api.py move /Y actualizar_intervalos_api.py backup_limpieza\
if exist update_intervals_direct.py move /Y update_intervals_direct.py backup_limpieza\
if exist audit_data_integrity.py move /Y audit_data_integrity.py backup_limpieza\
if exist compare_blockchain_sql.py move /Y compare_blockchain_sql.py backup_limpieza\
if exist verificar_blockchain_vs_db.py move /Y verificar_blockchain_vs_db.py backup_limpieza\
echo OK - Scripts movidos

echo.
echo [2/6] Moviendo documentacion obsoleta...
for %%f in (LIMPIEZA_COMPLETADA.md MIGRACION_OPSHIN.md MVP_OPCION_B_RESUMEN.md RUTA_PRACTICA_MVP.md EXITO_INICIALIZACION.md ESTADO_ACTUAL.md RESUMEN_SESION_2025-10-14.md PROGRESO_REGISTER_SENSOR.md INVESTIGACION_PYCARDANO_TX.md EXITO_REGISTRO_SENSORES.md LUCID_VS_LUCID_EVOLUTION.md EXITO_ADD_READING.md RESUMEN_FINAL_MVP.md DECODE_DATUM_ENHANCED.md GUIA_DEMO.md MEJORAS_DECODE_DATUM.md RESUMEN_MEJORAS_DECODE.md EXITO_UPDATE_SENSOR.md RESUMEN_CRUD_COMPLETADO.md EXITO_DEACTIVATE_SENSOR.md RESUMEN_FINAL_CRUD_100.md API_REST_COMPLETADA.md RESUMEN_FINAL_API_REST.md QUICK_START.md FRONTEND_DASHBOARD_COMPLETADO.md TXHASH_DISPLAY_AGREGADO.md TXHASH_EN_HISTORIAL_COMPLETADO.md) do if exist %%f move /Y %%f backup_limpieza\
echo OK - Documentacion movida

echo.
echo [3/6] Creando carpetas organizadas...
if not exist scripts mkdir scripts
if not exist utils mkdir utils
if not exist docs mkdir docs
echo OK - Carpetas creadas

echo.
echo [4/6] Organizando scripts de produccion...
if exist sensor_fisico_simulado.py move /Y sensor_fisico_simulado.py scripts\
if exist ejemplo_agregar_sensor.py move /Y ejemplo_agregar_sensor.py scripts\
if exist demo_rapido.py move /Y demo_rapido.py scripts\
echo OK - Scripts organizados

echo.
echo [5/6] Organizando utilidades...
if exist audit_data_integrity_v2.py move /Y audit_data_integrity_v2.py utils\
if exist mqtt_gateway.py move /Y mqtt_gateway.py utils\
if exist nodo_sensor_mqtt.py move /Y nodo_sensor_mqtt.py utils\
if exist arduino_serial_bridge.py move /Y arduino_serial_bridge.py utils\
echo OK - Utilidades organizadas

echo.
echo [6/6] Organizando documentacion tecnica...
if exist API_EJEMPLOS.md move /Y API_EJEMPLOS.md docs\
if exist SISTEMA_ROLLUPS_MERKLE.md move /Y SISTEMA_ROLLUPS_MERKLE.md docs\
if exist ARQUITECTURAS_CAPTURA_DATOS.md move /Y ARQUITECTURAS_CAPTURA_DATOS.md docs\
if exist CAPTURA_DATOS_NODOS_SENSORES.md move /Y CAPTURA_DATOS_NODOS_SENSORES.md docs\
if exist PLAN_OPTIMIZACION_COSTOS.md move /Y PLAN_OPTIMIZACION_COSTOS.md docs\
if exist DEMO_SISTEMA_COMPLETO.md move /Y DEMO_SISTEMA_COMPLETO.md docs\
if exist DASHBOARD_COMPLETADO.md move /Y DASHBOARD_COMPLETADO.md docs\
if exist PROGRESO_POSTGRESQL_PYCARDANO.md move /Y PROGRESO_POSTGRESQL_PYCARDANO.md docs\
if exist HARDWARE_SENSORES_FISICOS.md move /Y HARDWARE_SENSORES_FISICOS.md docs\
echo OK - Documentacion organizada

echo.
echo ========================================
echo LIMPIEZA COMPLETADA
echo ========================================
echo Archivos respaldados en: backup_limpieza\
echo Proyecto organizado y listo!
echo.
pause
