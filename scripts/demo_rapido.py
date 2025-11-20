"""
Demo Rapido: Registrar un sensor y agregar lecturas
"""
import requests
import time

BASE_URL = "http://localhost:8000/api"

print("=" * 60)
print("  DEMO: Registrar Sensor y Agregar Lecturas")
print("=" * 60)

# 1. Registrar un sensor
print("\n[1/3] Registrando nuevo sensor...")
sensor_data = {
    "sensor_id": "SENSOR_DEMO_001",
    "location": {
        "latitude": -34.65,
        "longitude": -58.52,
        "zone_name": "Campo Demo - Prueba Rapida"
    },
    "min_humidity_threshold": 30,
    "max_humidity_threshold": 75,
    "reading_interval_minutes": 60
}

try:
    response = requests.post(f"{BASE_URL}/sensors", json=sensor_data, timeout=60)
    result = response.json()
    print(f"  OK Sensor registrado: {result.get('sensor_id')}")
    print(f"  TX Hash: {result.get('tx_hash')}")
except Exception as e:
    print(f"  Error: {e}")
    exit(1)

# 2. Esperar confirmacion
print("\n[2/3] Esperando confirmacion blockchain (30 segundos)...")
time.sleep(30)

# 3. Agregar lectura
print("\n[3/3] Agregando lectura de humedad...")
reading_data = {
    "sensor_id": "SENSOR_DEMO_001",
    "humidity_percentage": 58,
    "temperature_celsius": 24
}

try:
    response = requests.post(f"{BASE_URL}/readings", json=reading_data, timeout=30)
    result = response.json()
    print(f"  OK Lectura agregada")
    print(f"  Humedad: {reading_data['humidity_percentage']}%")
    print(f"  Temperatura: {reading_data['temperature_celsius']}C")
    print(f"  Nivel de alerta: {result.get('alert_level')}")
except Exception as e:
    print(f"  Error: {e}")

print("\n" + "=" * 60)
print("  COMPLETADO!")
print("  Abre el dashboard: http://localhost:8000/dashboard")
print("=" * 60)
