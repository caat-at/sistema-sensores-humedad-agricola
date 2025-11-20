"""
Script para Sensor Fisico - SENSOR_001
Simula lecturas de un sensor real de humedad de suelo y temperatura
En produccion, esto correria en un dispositivo IoT (Arduino, Raspberry Pi, ESP32)
"""

import requests
import time
import random
from datetime import datetime

# Configuracion
API_URL = "http://localhost:8000/api"
SENSOR_ID = "SENSOR_001"  # El sensor ya registrado
INTERVALO_LECTURA = 60  # segundos (1 minuto para demo, en produccion seria 1 hora)

def leer_sensor_humedad():
    """
    Simula la lectura de un sensor de humedad de suelo

    En un sensor REAL (ej: Arduino + sensor capacitivo):
    -------------------------------------------------------
    int humedad_raw = analogRead(SENSOR_PIN);
    int humedad_porcentaje = map(humedad_raw, 0, 1023, 0, 100);
    return humedad_porcentaje;

    O con Raspberry Pi + sensor I2C/SPI
    """
    # SIMULACION: En produccion, aqui leerias el sensor fisico
    # Simulamos valores realistas entre 40% y 80%
    humedad = random.randint(40, 80)

    # Agregar algo de variacion natural
    variacion = random.uniform(-5, 5)
    humedad = max(0, min(100, humedad + variacion))

    return int(humedad)

def leer_sensor_temperatura():
    """
    Simula la lectura de un sensor de temperatura

    En un sensor REAL (ej: DHT22, DS18B20):
    -------------------------------------------------------
    float temperatura = dht.readTemperature();
    return temperatura;
    """
    # SIMULACION: En produccion, aqui leerias el sensor fisico
    # Simulamos temperatura entre 18°C y 30°C
    temperatura = random.randint(18, 30)

    # Agregar variacion
    variacion = random.uniform(-2, 2)
    temperatura = temperatura + variacion

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

        if response.status_code == 200:
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

def ciclo_lectura_continuo():
    """
    Ciclo principal que lee el sensor y envia datos periodicamente
    Este seria el loop() en Arduino o el main loop en Raspberry Pi
    """
    print("=" * 70)
    print(f"  SENSOR FISICO: {SENSOR_ID}")
    print(f"  Ubicacion: Campo Norte - Parcela A")
    print(f"  Intervalo de lectura: {INTERVALO_LECTURA} segundos")
    print("=" * 70)
    print("\nIniciando monitoreo continuo...")
    print("(Presiona Ctrl+C para detener)\n")

    contador_lecturas = 0
    lecturas_exitosas = 0
    lecturas_fallidas = 0

    try:
        while True:
            contador_lecturas += 1
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            print(f"[Lectura #{contador_lecturas}] {timestamp}")

            # 1. Leer sensor de humedad (hardware fisico)
            print("  [1/3] Leyendo sensor de humedad del suelo...")
            humedad = leer_sensor_humedad()
            print(f"        Humedad: {humedad}%")

            # 2. Leer sensor de temperatura (hardware fisico)
            print("  [2/3] Leyendo sensor de temperatura...")
            temperatura = leer_sensor_temperatura()
            print(f"        Temperatura: {temperatura}°C")

            # 3. Enviar datos a la nube/API
            print("  [3/3] Enviando datos al sistema...")
            exito, resultado = enviar_lectura_a_api(SENSOR_ID, humedad, temperatura)

            if exito:
                lecturas_exitosas += 1
                alert_level = resultado.get('alert_level', 'Unknown')

                # Emojis segun nivel de alerta
                if alert_level == "Normal":
                    emoji = "OK"
                elif alert_level == "Low":
                    emoji = "ALERTA BAJA"
                elif alert_level == "High":
                    emoji = "ALERTA ALTA"
                elif alert_level == "Critical":
                    emoji = "CRITICO"
                else:
                    emoji = "?"

                print(f"        [{emoji}] Lectura guardada exitosamente")
                print(f"        Nivel de alerta: {alert_level}")

                # En un sistema real, podrias activar riego automatico aqui
                if alert_level == "Low":
                    print("        >> Recomendacion: Activar riego")
                elif alert_level == "Critical":
                    print("        >> ACCION REQUERIDA: Riego inmediato!")

            else:
                lecturas_fallidas += 1
                print(f"        [ERROR] No se pudo enviar: {resultado}")
                print(f"        >> Reintentando en el proximo ciclo...")

            # Estadisticas
            print(f"\n  Estadisticas: {lecturas_exitosas} exitosas | {lecturas_fallidas} fallidas")

            # Esperar antes de la siguiente lectura
            print(f"\n  Proxima lectura en {INTERVALO_LECTURA} segundos...\n")
            print("-" * 70)

            time.sleep(INTERVALO_LECTURA)

    except KeyboardInterrupt:
        print("\n\n" + "=" * 70)
        print("  DETENIENDO SENSOR")
        print("=" * 70)
        print(f"\n  Total de lecturas: {contador_lecturas}")
        print(f"  Exitosas: {lecturas_exitosas}")
        print(f"  Fallidas: {lecturas_fallidas}")
        print(f"  Tasa de exito: {(lecturas_exitosas/contador_lecturas*100):.1f}%")
        print("\n  Sensor detenido correctamente.")
        print("=" * 70)

def verificar_sensor_registrado():
    """Verifica que el sensor este registrado en el sistema"""
    try:
        response = requests.get(f"{API_URL}/sensors", timeout=10)
        sensores = response.json()

        for sensor in sensores:
            if sensor['sensor_id'] == SENSOR_ID:
                print("\n[OK] Sensor encontrado en el sistema:")
                print(f"     ID: {sensor['sensor_id']}")
                print(f"     Zona: {sensor['location']['zone_name']}")
                print(f"     Ubicacion: ({sensor['location']['latitude']}, {sensor['location']['longitude']})")
                print(f"     Umbrales: {sensor['min_humidity_threshold']}% - {sensor['max_humidity_threshold']}%")
                print(f"     Estado: {sensor['status']}")
                return True

        print(f"\n[ERROR] Sensor {SENSOR_ID} no encontrado en el sistema")
        print("        Registralo primero usando el dashboard o la API")
        return False

    except Exception as e:
        print(f"\n[ERROR] No se pudo verificar el sensor: {e}")
        return False

if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("  SISTEMA DE MONITOREO - SENSOR FISICO")
    print("  Sensor de Humedad de Suelo + Temperatura")
    print("=" * 70)

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

    # Verificar que el sensor este registrado
    print(f"\n[2/2] Verificando sensor {SENSOR_ID}...")
    if not verificar_sensor_registrado():
        exit(1)

    print("\n[OK] Todo listo para comenzar el monitoreo\n")

    # Iniciar ciclo de lectura continuo
    ciclo_lectura_continuo()
