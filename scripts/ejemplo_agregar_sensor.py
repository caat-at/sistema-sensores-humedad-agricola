#!/usr/bin/env python3
"""
Script de Ejemplo: Registrar Sensor y Agregar Lecturas
Sistema de Sensores de Humedad Agrícola con Cardano Blockchain
"""

import requests
import time
import random
from datetime import datetime

# Configuración
BASE_URL = "http://localhost:8000/api"

def print_header(text):
    """Imprime un encabezado decorado"""
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60)

def registrar_sensor(sensor_id, zona, lat, lon, min_hum=30, max_hum=75, intervalo=60):
    """
    Registra un nuevo sensor en la blockchain de Cardano

    Args:
        sensor_id: ID único del sensor (ej: "SENSOR_010")
        zona: Nombre de la zona (ej: "Campo Norte")
        lat: Latitud (ej: -34.62)
        lon: Longitud (ej: -58.50)
        min_hum: Umbral mínimo de humedad (%)
        max_hum: Umbral máximo de humedad (%)
        intervalo: Intervalo de lectura (minutos)
    """
    print_header(f"📝 Registrando Sensor: {sensor_id}")

    data = {
        "sensor_id": sensor_id,
        "location": {
            "latitude": lat,
            "longitude": lon,
            "zone_name": zona
        },
        "min_humidity_threshold": min_hum,
        "max_humidity_threshold": max_hum,
        "reading_interval_minutes": intervalo
    }

    try:
        print(f"📍 Ubicación: {zona} ({lat}, {lon})")
        print(f"💧 Umbrales: {min_hum}% - {max_hum}%")
        print(f"⏱️  Intervalo: cada {intervalo} minutos")
        print("\n⏳ Enviando transacción a blockchain...")

        response = requests.post(f"{BASE_URL}/sensors", json=data, timeout=60)
        response.raise_for_status()

        result = response.json()
        print(f"\n✅ Sensor registrado exitosamente!")
        print(f"🔗 TX Hash: {result.get('tx_hash', 'N/A')}")
        print(f"📋 Mensaje: {result.get('message', '')}")

        return result

    except requests.exceptions.RequestException as e:
        print(f"\n❌ Error al registrar sensor: {e}")
        return None

def agregar_lectura(sensor_id, humedad, temperatura):
    """
    Agrega una lectura de humedad y temperatura

    Args:
        sensor_id: ID del sensor
        humedad: Porcentaje de humedad (0-100)
        temperatura: Temperatura en Celsius
    """
    data = {
        "sensor_id": sensor_id,
        "humidity_percentage": humedad,
        "temperature_celsius": temperatura
    }

    try:
        response = requests.post(f"{BASE_URL}/readings", json=data, timeout=30)
        response.raise_for_status()

        result = response.json()

        # Determinar emoji según nivel de alerta
        alert_emojis = {
            "Normal": "🟢",
            "Low": "🟡",
            "High": "🟠",
            "Critical": "🔴"
        }
        alert_level = result.get('alert_level', 'Normal')
        emoji = alert_emojis.get(alert_level, "⚪")

        print(f"  {emoji} {humedad}% humedad, {temperatura}°C - Nivel: {alert_level}")

        return result

    except requests.exceptions.RequestException as e:
        print(f"  ❌ Error: {e}")
        return None

def simular_lecturas(sensor_id, num_lecturas=5, intervalo_segundos=2):
    """
    Simula múltiples lecturas de un sensor con valores aleatorios

    Args:
        sensor_id: ID del sensor
        num_lecturas: Cantidad de lecturas a simular
        intervalo_segundos: Segundos entre cada lectura
    """
    print_header(f"📊 Simulando {num_lecturas} Lecturas para {sensor_id}")

    for i in range(1, num_lecturas + 1):
        # Generar valores aleatorios realistas
        humedad = random.randint(35, 85)
        temperatura = random.randint(18, 32)

        print(f"\n[{i}/{num_lecturas}] {datetime.now().strftime('%H:%M:%S')}")
        agregar_lectura(sensor_id, humedad, temperatura)

        if i < num_lecturas:
            time.sleep(intervalo_segundos)

    print("\n✅ Simulación completada")

def ver_sensores():
    """Muestra todos los sensores registrados"""
    print_header("📋 Listando Sensores Registrados")

    try:
        response = requests.get(f"{BASE_URL}/sensors", timeout=10)
        response.raise_for_status()

        sensores = response.json()

        if not sensores:
            print("⚠️  No hay sensores registrados")
            return

        print(f"\n🌱 Total de sensores: {len(sensores)}\n")

        for sensor in sensores:
            print(f"  • {sensor['sensor_id']}")
            print(f"    📍 {sensor['location']['zone_name']}")
            print(f"    💧 Umbrales: {sensor['min_humidity_threshold']}%-{sensor['max_humidity_threshold']}%")
            print(f"    📅 Instalado: {sensor['installed_date']}")
            print()

    except requests.exceptions.RequestException as e:
        print(f"❌ Error al obtener sensores: {e}")

def ver_lecturas(sensor_id=None, limit=5):
    """
    Muestra las últimas lecturas

    Args:
        sensor_id: ID del sensor (opcional, None = todas)
        limit: Cantidad de lecturas a mostrar
    """
    titulo = f"📈 Últimas {limit} Lecturas"
    if sensor_id:
        titulo += f" de {sensor_id}"

    print_header(titulo)

    try:
        url = f"{BASE_URL}/readings?limit={limit}"
        if sensor_id:
            url += f"&sensor_id={sensor_id}"

        response = requests.get(url, timeout=10)
        response.raise_for_status()

        lecturas = response.json()

        if not lecturas:
            print("⚠️  No hay lecturas disponibles")
            return

        print()
        for lectura in lecturas:
            alert_emojis = {
                "Normal": "🟢",
                "Low": "🟡",
                "High": "🟠",
                "Critical": "🔴"
            }
            emoji = alert_emojis.get(lectura.get('alert_level', 'Normal'), "⚪")

            print(f"  {emoji} {lectura['sensor_id']}")
            print(f"     💧 {lectura['humidity_percentage']}% | 🌡️  {lectura['temperature_celsius']}°C")
            print(f"     📅 {lectura['timestamp']}")
            print()

    except requests.exceptions.RequestException as e:
        print(f"❌ Error al obtener lecturas: {e}")

def menu_principal():
    """Menú interactivo principal"""
    while True:
        print_header("🌾 Sistema de Sensores de Humedad Agrícola")
        print("\n¿Qué deseas hacer?")
        print("\n  1. Registrar un nuevo sensor")
        print("  2. Agregar lectura a un sensor existente")
        print("  3. Simular múltiples lecturas")
        print("  4. Ver todos los sensores")
        print("  5. Ver lecturas recientes")
        print("  6. Ejemplo completo automático")
        print("  7. Salir")

        opcion = input("\n👉 Opción (1-7): ").strip()

        if opcion == "1":
            sensor_id = input("\n  Sensor ID (ej: SENSOR_010): ").strip()
            zona = input("  Nombre de zona (ej: Campo Norte): ").strip()
            lat = float(input("  Latitud (ej: -34.62): ").strip())
            lon = float(input("  Longitud (ej: -58.50): ").strip())

            registrar_sensor(sensor_id, zona, lat, lon)
            input("\n[Presiona Enter para continuar]")

        elif opcion == "2":
            sensor_id = input("\n  Sensor ID: ").strip()
            humedad = int(input("  Humedad (0-100%): ").strip())
            temperatura = int(input("  Temperatura (°C): ").strip())

            print()
            agregar_lectura(sensor_id, humedad, temperatura)
            input("\n[Presiona Enter para continuar]")

        elif opcion == "3":
            sensor_id = input("\n  Sensor ID: ").strip()
            num = int(input("  Cantidad de lecturas (ej: 5): ").strip())

            simular_lecturas(sensor_id, num_lecturas=num)
            input("\n[Presiona Enter para continuar]")

        elif opcion == "4":
            ver_sensores()
            input("\n[Presiona Enter para continuar]")

        elif opcion == "5":
            sensor_id = input("\n  Sensor ID (Enter = todas): ").strip() or None
            limit = int(input("  Cantidad (ej: 10): ").strip() or "10")

            ver_lecturas(sensor_id, limit)
            input("\n[Presiona Enter para continuar]")

        elif opcion == "6":
            ejemplo_completo()
            input("\n[Presiona Enter para continuar]")

        elif opcion == "7":
            print("\n👋 ¡Hasta luego!")
            break

        else:
            print("\n⚠️  Opción inválida")
            time.sleep(1)

def ejemplo_completo():
    """Ejecuta un ejemplo completo automático"""
    print_header("🚀 Ejemplo Completo Automático")

    # 1. Registrar sensor
    sensor_id = f"SENSOR_AUTO_{int(time.time())}"
    print(f"\n1️⃣  Paso 1: Registrando sensor {sensor_id}...")

    resultado = registrar_sensor(
        sensor_id=sensor_id,
        zona="Campo Automático - Demo",
        lat=-34.65,
        lon=-58.52,
        min_hum=35,
        max_hum=70,
        intervalo=60
    )

    if not resultado:
        print("\n❌ No se pudo registrar el sensor. Abortando ejemplo.")
        return

    # 2. Esperar confirmación de blockchain
    print("\n2️⃣  Paso 2: Esperando confirmación de blockchain...")
    print("⏳ (Esto puede tardar 20-30 segundos...)")
    time.sleep(30)

    # 3. Agregar lecturas
    print("\n3️⃣  Paso 3: Agregando lecturas de prueba...")
    simular_lecturas(sensor_id, num_lecturas=3, intervalo_segundos=2)

    # 4. Ver resultados
    print("\n4️⃣  Paso 4: Verificando resultados...")
    time.sleep(2)
    ver_lecturas(sensor_id, limit=3)

    # 5. Dashboard
    print("\n5️⃣  Paso 5: ¡Abre el dashboard para ver los datos!")
    print(f"\n🌐 Dashboard: http://localhost:8000/dashboard")
    print(f"📊 Busca el sensor: {sensor_id}")

    print("\n✅ ¡Ejemplo completado exitosamente!")

if __name__ == "__main__":
    print("""
    ============================================================
      Sistema de Sensores de Humedad Agricola
      Blockchain Cardano + API REST + Dashboard
    ============================================================
    """)

    # Verificar que el servidor esté corriendo
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        response.raise_for_status()
        print("✅ Servidor conectado correctamente\n")
    except requests.exceptions.RequestException:
        print("❌ Error: El servidor no está corriendo")
        print("\n💡 Inicia el servidor primero:")
        print("   PowerShell: .\\start.ps1")
        print("   CMD: start.bat")
        exit(1)

    # Iniciar menú
    try:
        menu_principal()
    except KeyboardInterrupt:
        print("\n\n👋 Interrumpido por el usuario. ¡Hasta luego!")
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
