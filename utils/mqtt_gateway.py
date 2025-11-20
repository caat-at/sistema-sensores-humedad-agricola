"""
Gateway MQTT para Nodos Sensores
Recibe datos de sensores via MQTT y los envia a la API REST
"""

import paho.mqtt.client as mqtt
import json
import requests
from datetime import datetime
import time

# ============ CONFIGURACION ============
# MQTT Broker
MQTT_BROKER = "localhost"  # Cambia por IP del broker
MQTT_PORT = 1883
MQTT_TOPIC = "sensores/humedad/#"  # # = wildcard para todos los subtopics
MQTT_CLIENT_ID = "gateway_mqtt_001"

# API REST
API_URL = "http://localhost:8000/api/readings"

# =======================================

class SensorGateway:
    """Gateway que convierte mensajes MQTT a llamadas API REST"""

    def __init__(self):
        self.client = mqtt.Client(client_id=MQTT_CLIENT_ID)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect

        self.mensajes_recibidos = 0
        self.mensajes_enviados = 0
        self.mensajes_fallidos = 0

    def on_connect(self, client, userdata, flags, rc):
        """Callback cuando se conecta al broker MQTT"""
        if rc == 0:
            print("[OK] Conectado al broker MQTT")
            print(f"     Broker: {MQTT_BROKER}:{MQTT_PORT}")
            print(f"     Topic: {MQTT_TOPIC}")

            # Suscribirse al topic
            client.subscribe(MQTT_TOPIC)
            print(f"[OK] Suscrito a: {MQTT_TOPIC}\n")
        else:
            print(f"[ERROR] Fallo en conexion, codigo: {rc}")

    def on_disconnect(self, client, userdata, rc):
        """Callback cuando se desconecta del broker"""
        if rc != 0:
            print(f"[WARN] Desconexion inesperada del broker (rc={rc})")
            print("       Intentando reconectar...")

    def on_message(self, client, userdata, msg):
        """Callback cuando llega un mensaje MQTT"""
        self.mensajes_recibidos += 1

        try:
            # Decodificar mensaje
            topic = msg.topic
            payload = msg.payload.decode('utf-8')

            print(f"\n[{self.mensajes_recibidos}] Mensaje recibido")
            print(f"    Topic: {topic}")
            print(f"    Payload: {payload}")

            # Parsear JSON
            data = json.loads(payload)

            # Validar campos requeridos
            required_fields = ['sensor_id', 'humidity_percentage', 'temperature_celsius']
            for field in required_fields:
                if field not in data:
                    raise ValueError(f"Campo requerido faltante: {field}")

            # Extraer datos
            sensor_id = data['sensor_id']
            humedad = int(data['humidity_percentage'])
            temperatura = int(data['temperature_celsius'])

            print(f"    Sensor: {sensor_id}")
            print(f"    Humedad: {humedad}%")
            print(f"    Temperatura: {temperatura}°C")

            # Enviar a API REST
            self.enviar_a_api(sensor_id, humedad, temperatura)

        except json.JSONDecodeError as e:
            print(f"    [ERROR] JSON invalido: {e}")
            self.mensajes_fallidos += 1

        except ValueError as e:
            print(f"    [ERROR] Validacion: {e}")
            self.mensajes_fallidos += 1

        except Exception as e:
            print(f"    [ERROR] Inesperado: {e}")
            self.mensajes_fallidos += 1

    def enviar_a_api(self, sensor_id, humedad, temperatura):
        """Envia los datos a la API REST"""
        try:
            # Preparar payload
            payload = {
                "sensor_id": sensor_id,
                "humidity_percentage": humedad,
                "temperature_celsius": temperatura
            }

            # Enviar POST
            print(f"    [->] Enviando a API...")
            response = requests.post(API_URL, json=payload, timeout=10)

            if response.status_code == 200:
                result = response.json()
                alert_level = result.get('alert_level', 'Unknown')

                print(f"    [OK] Enviado exitosamente")
                print(f"         Nivel de alerta: {alert_level}")

                self.mensajes_enviados += 1

                # Mostrar estadisticas cada 10 mensajes
                if self.mensajes_enviados % 10 == 0:
                    self.mostrar_estadisticas()

            else:
                print(f"    [ERROR] API respondio con codigo {response.status_code}")
                print(f"            Respuesta: {response.text}")
                self.mensajes_fallidos += 1

        except requests.exceptions.ConnectionError:
            print(f"    [ERROR] No se pudo conectar a la API")
            print(f"            Verifica que el servidor este corriendo")
            self.mensajes_fallidos += 1

        except requests.exceptions.Timeout:
            print(f"    [ERROR] Timeout esperando respuesta de API")
            self.mensajes_fallidos += 1

        except Exception as e:
            print(f"    [ERROR] Fallo enviando a API: {e}")
            self.mensajes_fallidos += 1

    def mostrar_estadisticas(self):
        """Muestra estadisticas del gateway"""
        print("\n" + "=" * 60)
        print("  ESTADISTICAS DEL GATEWAY")
        print("=" * 60)
        print(f"  Mensajes MQTT recibidos:  {self.mensajes_recibidos}")
        print(f"  Enviados a API exitosos:  {self.mensajes_enviados}")
        print(f"  Fallidos:                 {self.mensajes_fallidos}")

        if self.mensajes_recibidos > 0:
            tasa_exito = (self.mensajes_enviados / self.mensajes_recibidos) * 100
            print(f"  Tasa de exito:            {tasa_exito:.1f}%")

        print("=" * 60 + "\n")

    def conectar(self):
        """Conecta al broker MQTT"""
        try:
            print("=" * 60)
            print("  GATEWAY MQTT -> API REST")
            print("  Sistema de Sensores de Humedad Agricola")
            print("=" * 60)
            print(f"\nConectando a broker MQTT en {MQTT_BROKER}:{MQTT_PORT}...")

            self.client.connect(MQTT_BROKER, MQTT_PORT, 60)
            return True

        except ConnectionRefusedError:
            print(f"\n[ERROR] No se pudo conectar al broker MQTT")
            print(f"        Verifica que Mosquitto este corriendo")
            print(f"\n        Instalacion:")
            print(f"        - Windows: https://mosquitto.org/download/")
            print(f"        - Linux: sudo apt-get install mosquitto")
            print(f"\n        Iniciar broker:")
            print(f"        mosquitto -v")
            return False

        except Exception as e:
            print(f"\n[ERROR] Fallo en conexion: {e}")
            return False

    def iniciar(self):
        """Inicia el gateway en modo escucha"""
        if not self.conectar():
            return

        print("\n[OK] Gateway iniciado correctamente")
        print("     Esperando mensajes MQTT...")
        print("     (Presiona Ctrl+C para detener)\n")

        try:
            # Loop infinito escuchando mensajes
            self.client.loop_forever()

        except KeyboardInterrupt:
            print("\n\n" + "=" * 60)
            print("  DETENIENDO GATEWAY")
            print("=" * 60)

            self.mostrar_estadisticas()

            print("\nDesconectando del broker...")
            self.client.disconnect()
            print("[OK] Gateway detenido correctamente\n")

def verificar_api():
    """Verifica que la API este disponible"""
    try:
        response = requests.get("http://localhost:8000/api/health", timeout=5)
        if response.status_code == 200:
            print("[OK] API disponible\n")
            return True
        else:
            print(f"[WARN] API respondio con codigo {response.status_code}\n")
            return False
    except:
        print("[ERROR] No se pudo conectar a la API")
        print("        Asegurate de que el servidor este corriendo:")
        print("        PowerShell: .\\start.ps1\n")
        return False

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  GATEWAY MQTT PARA NODOS SENSORES")
    print("=" * 60)

    # Verificar API
    print("\n[1/2] Verificando API REST...")
    if not verificar_api():
        print("\n[!] Continuar de todas formas? (y/n): ", end='')
        respuesta = input().strip().lower()
        if respuesta != 'y':
            print("\nAbortando...")
            exit(1)

    # Iniciar gateway
    print("[2/2] Iniciando gateway MQTT...\n")

    gateway = SensorGateway()
    gateway.iniciar()
