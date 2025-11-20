"""
Script para Multiples Sensores Fisicos - SENSOR_001 y SENSOR_002
Captura lecturas de 2 sensores reales de humedad de suelo y temperatura
En produccion, esto correria en un dispositivo IoT (Arduino, Raspberry Pi, ESP32)
"""

import requests
import time
import random
from datetime import datetime
import threading

# Configuracion
API_URL = "http://localhost:8000/api"
INTERVALO_LECTURA = 3600  # segundos (1 hora)

# Configuracion de Sensores
SENSORES = [
    {
        "sensor_id": "SENSOR_001",
        "nombre": "Sensor Norte",
        "ubicacion": "Campo Norte - Parcela A",
        "pin_humedad": 34,  # Pin analogico para humedad (ej: GPIO34 en ESP32)
        "pin_temperatura": 4,  # Pin digital para DHT22 (ej: GPIO4)
        "humedad_base": 50,  # Rango base para simulacion
        "temp_base": 24
    },
    {
        "sensor_id": "SENSOR_002",
        "nombre": "Sensor Sur",
        "ubicacion": "Campo Sur - Parcela B",
        "pin_humedad": 35,  # Pin analogico diferente
        "pin_temperatura": 5,  # Pin digital diferente
        "humedad_base": 55,  # Rango diferente para simular condiciones distintas
        "temp_base": 26
    }
]

def leer_sensor_humedad(config):
    """
    Simula la lectura de un sensor de humedad de suelo

    En un sensor REAL (ej: Arduino + sensor capacitivo):
    -------------------------------------------------------
    int humedad_raw = analogRead(config['pin_humedad']);
    int humedad_porcentaje = map(humedad_raw, 0, 1023, 0, 100);
    return humedad_porcentaje;

    O con Raspberry Pi + sensor I2C/SPI o ESP32:
    import Adafruit_DHT
    humidity, temperature = Adafruit_DHT.read_retry(DHT22, config['pin_humedad'])
    """
    # SIMULACION: En produccion, aqui leerias el sensor fisico
    humedad = config['humedad_base'] + random.uniform(-10, 10)
    humedad = max(0, min(100, humedad))
    return int(humedad)

def leer_sensor_temperatura(config):
    """
    Simula la lectura de un sensor de temperatura

    En un sensor REAL (ej: DHT22, DS18B20):
    -------------------------------------------------------
    // Arduino:
    float temperatura = dht.readTemperature();
    return temperatura;

    // ESP32 con sensor DS18B20:
    sensors.requestTemperatures();
    float tempC = sensors.getTempCByIndex(config['pin_temperatura']);
    """
    # SIMULACION: En produccion, aqui leerias el sensor fisico
    temperatura = config['temp_base'] + random.uniform(-3, 3)
    return int(temperatura)

def enviar_lectura_a_api(sensor_id, humedad, temperatura):
    """
    Envia la lectura al sistema via API REST
    Esta funcion se ejecutaria cada X minutos desde el dispositivo IoT
    """
    data = {
        "sensor_id": sensor_id,
        "humidity_percentage": humedad,
        "temperature_celsius": temperatura
    }

    try:
        response = requests.post(
            f"{API_URL}/readings",
            json=data,
            timeout=30
        )

        if response.status_code in [200, 201]:
            result = response.json()
            return True, result
        else:
            return False, f"Error HTTP {response.status_code}"

    except requests.exceptions.ConnectionError:
        return False, "No se pudo conectar al servidor"
    except requests.exceptions.Timeout:
        return False, "Timeout - servidor no responde"
    except Exception as e:
        return False, str(e)

def monitorear_sensor(config, estadisticas):
    """
    Monitorea un sensor individual en un thread separado
    """
    sensor_id = config['sensor_id']
    nombre = config['nombre']

    print(f"[{nombre}] Iniciado - {config['ubicacion']}")

    contador = 0

    try:
        while True:
            contador += 1
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            print(f"\n[{nombre}] Lectura #{contador} - {timestamp}")

            # 1. Leer sensor de humedad
            print(f"  [{nombre}] Leyendo humedad (Pin {config['pin_humedad']})...")
            humedad = leer_sensor_humedad(config)
            print(f"  [{nombre}] Humedad: {humedad}%")

            # 2. Leer sensor de temperatura
            print(f"  [{nombre}] Leyendo temperatura (Pin {config['pin_temperatura']})...")
            temperatura = leer_sensor_temperatura(config)
            print(f"  [{nombre}] Temperatura: {temperatura}°C")

            # 3. Enviar datos a la API
            print(f"  [{nombre}] Enviando a API...")
            exito, resultado = enviar_lectura_a_api(sensor_id, humedad, temperatura)

            if exito:
                estadisticas[sensor_id]['exitosas'] += 1

                # Mostrar mensaje del servidor
                mensaje = resultado.get('message', 'Lectura guardada')
                print(f"  [{nombre}] [OK] {mensaje}")

                # Verificar si hay TX hash (modo inmediato)
                tx_hash = resultado.get('tx_hash')
                if tx_hash and tx_hash != "null":
                    print(f"  [{nombre}] TX Hash: {tx_hash[:16]}...")

            else:
                estadisticas[sensor_id]['fallidas'] += 1
                print(f"  [{nombre}] [ERROR] {resultado}")

            # Esperar antes de la siguiente lectura
            time.sleep(INTERVALO_LECTURA)

    except Exception as e:
        print(f"\n[{nombre}] ERROR: {e}")

def ciclo_multisensor():
    """
    Gestiona multiples sensores simultaneamente usando threads
    """
    print("=" * 80)
    print("  SISTEMA DE MONITOREO MULTI-SENSOR")
    print("  Sensores de Humedad de Suelo + Temperatura")
    print("=" * 80)
    print(f"\n  Sensores configurados: {len(SENSORES)}")
    for s in SENSORES:
        print(f"    - {s['sensor_id']}: {s['nombre']} ({s['ubicacion']})")
    print(f"\n  Intervalo de lectura: {INTERVALO_LECTURA} segundos")
    print("=" * 80)
    print("\nIniciando monitoreo continuo...")
    print("(Presiona Ctrl+C para detener)\n")

    # Estadisticas por sensor
    estadisticas = {}
    for sensor in SENSORES:
        estadisticas[sensor['sensor_id']] = {
            'exitosas': 0,
            'fallidas': 0
        }

    # Crear un thread por cada sensor
    threads = []
    for config in SENSORES:
        thread = threading.Thread(
            target=monitorear_sensor,
            args=(config, estadisticas),
            daemon=True
        )
        thread.start()
        threads.append(thread)

    try:
        # Mantener el programa principal corriendo
        while True:
            time.sleep(10)

            # Mostrar estadisticas cada 10 segundos
            print("\n" + "=" * 80)
            print("  ESTADISTICAS GENERALES")
            print("=" * 80)
            for sensor_id, stats in estadisticas.items():
                total = stats['exitosas'] + stats['fallidas']
                tasa = (stats['exitosas'] / total * 100) if total > 0 else 0
                print(f"  {sensor_id}: {stats['exitosas']} exitosas | {stats['fallidas']} fallidas | {tasa:.1f}% exito")
            print("=" * 80)

    except KeyboardInterrupt:
        print("\n\n" + "=" * 80)
        print("  DETENIENDO SENSORES")
        print("=" * 80)

        total_exitosas = sum(s['exitosas'] for s in estadisticas.values())
        total_fallidas = sum(s['fallidas'] for s in estadisticas.values())
        total_lecturas = total_exitosas + total_fallidas

        print(f"\n  Total de lecturas (todos los sensores): {total_lecturas}")
        print(f"  Exitosas: {total_exitosas}")
        print(f"  Fallidas: {total_fallidas}")
        if total_lecturas > 0:
            print(f"  Tasa de exito global: {(total_exitosas/total_lecturas*100):.1f}%")

        print("\n  Detalle por sensor:")
        for sensor_id, stats in estadisticas.items():
            print(f"    {sensor_id}: {stats['exitosas']} exitosas, {stats['fallidas']} fallidas")

        print("\n  Sensores detenidos correctamente.")
        print("=" * 80)

def verificar_sensores_registrados():
    """Verifica que todos los sensores esten registrados en el sistema"""
    try:
        response = requests.get(f"{API_URL}/sensors", timeout=10)
        sensores_sistema = response.json()

        print("\n[OK] Verificando sensores en el sistema:")

        sensores_encontrados = []
        for config in SENSORES:
            sensor_id = config['sensor_id']
            encontrado = False

            for sensor in sensores_sistema:
                if sensor['sensor_id'] == sensor_id:
                    encontrado = True
                    sensores_encontrados.append(sensor_id)
                    print(f"\n  [{sensor_id}] Encontrado:")
                    print(f"     Zona: {sensor['location']['zone_name']}")
                    print(f"     Ubicacion: ({sensor['location']['latitude']}, {sensor['location']['longitude']})")
                    print(f"     Umbrales: {sensor['min_humidity_threshold']}% - {sensor['max_humidity_threshold']}%")
                    print(f"     Estado: {sensor['status']}")
                    break

            if not encontrado:
                print(f"\n  [ERROR] {sensor_id} no encontrado")
                print(f"          Registralo usando: python ejemplo_agregar_sensor.py")
                return False

        if len(sensores_encontrados) == len(SENSORES):
            print(f"\n[OK] Todos los {len(SENSORES)} sensores estan registrados")
            return True
        else:
            return False

    except Exception as e:
        print(f"\n[ERROR] No se pudo verificar sensores: {e}")
        return False

if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("  SISTEMA DE MONITOREO MULTI-SENSOR")
    print("  Sensor de Humedad de Suelo + Temperatura")
    print("=" * 80)

    # Verificar conexion al servidor
    print("\n[1/2] Verificando conexion al servidor...")
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        if response.status_code == 200:
            print("      [OK] Servidor disponible")
        else:
            print(f"      [ERROR] Servidor respondio con codigo {response.status_code}")
            exit(1)
    except Exception as e:
        print(f"      [ERROR] No se pudo conectar al servidor: {e}")
        print("\n      Asegurate de que el servidor este corriendo:")
        print("      PowerShell: .\\start.ps1")
        exit(1)

    # Verificar que los sensores esten registrados
    print(f"\n[2/2] Verificando sensores ({len(SENSORES)} configurados)...")
    if not verificar_sensores_registrados():
        exit(1)

    print("\n[OK] Todo listo para comenzar el monitoreo multi-sensor\n")

    # Iniciar ciclo de monitoreo multi-sensor
    ciclo_multisensor()
