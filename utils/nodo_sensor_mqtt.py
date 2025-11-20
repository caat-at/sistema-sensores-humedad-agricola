"""
Simulador de Nodo Sensor con MQTT
Simula un ESP32/Arduino enviando datos via MQTT
"""

import paho.mqtt.client as mqtt
import json
import random
import time
from datetime import datetime

# ============ CONFIGURACION ============
# Sensor
SENSOR_ID = "SENSOR_001"
SENSOR_NAME = "Campo Norte - Parcela A"

# MQTT
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC = "sensores/humedad/sensor001"
MQTT_CLIENT_ID = f"nodo_{SENSOR_ID}"

# Intervalo de lectura (segundos)
INTERVALO = 10  # 10 segundos para demo (en produccion: 3600 = 1 hora)

# =======================================

class NodoSensor:
    """Simula un nodo sensor IoT con MQTT"""

    def __init__(self, sensor_id, nombre):
        self.sensor_id = sensor_id
        self.nombre = nombre
        self.client = mqtt.Client(client_id=MQTT_CLIENT_ID)
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_publish = self.on_publish

        self.conectado = False
        self.lecturas_enviadas = 0

    def on_connect(self, client, userdata, flags, rc):
        """Callback cuando se conecta al broker"""
        if rc == 0:
            self.conectado = True
            print("[OK] Nodo conectado al broker MQTT")
            print(f"     Broker: {MQTT_BROKER}:{MQTT_PORT}")
            print(f"     Topic: {MQTT_TOPIC}\n")
        else:
            print(f"[ERROR] Fallo conexion, codigo: {rc}")
            self.conectado = False

    def on_disconnect(self, client, userdata, rc):
        """Callback cuando se desconecta"""
        self.conectado = False
        if rc != 0:
            print(f"\n[WARN] Desconectado del broker (rc={rc})")
            print("       Intentando reconectar...")

    def on_publish(self, client, userdata, mid):
        """Callback cuando se publica un mensaje"""
        # Opcional: confirmacion de publicacion
        pass

    def leer_humedad_suelo(self):
        """Simula lectura de sensor de humedad de suelo"""
        # En hardware real:
        # int valor = analogRead(HUMEDAD_PIN);
        # return map(valor, 0, 1023, 0, 100);

        # Simulacion: valores realistas entre 35% y 85%
        base = 60
        variacion = random.uniform(-25, 25)
        humedad = base + variacion

        # Limitar al rango valido
        return max(0, min(100, int(humedad)))

    def leer_temperatura(self):
        """Simula lectura de sensor de temperatura DHT22"""
        # En hardware real:
        # float temp = dht.readTemperature();
        # return (int)temp;

        # Simulacion: temperatura entre 15°C y 32°C
        base = 23
        variacion = random.uniform(-8, 9)
        temperatura = base + variacion

        return int(temperatura)

    def crear_mensaje(self, humedad, temperatura):
        """Crea el mensaje JSON para enviar"""
        mensaje = {
            "sensor_id": self.sensor_id,
            "humidity_percentage": humedad,
            "temperature_celsius": temperatura,
            "timestamp": datetime.now().isoformat(),
            "node_info": {
                "name": self.nombre,
                "type": "soil_humidity",
                "firmware_version": "1.0.0"
            }
        }

        return json.dumps(mensaje)

    def publicar_lectura(self):
        """Lee sensores y publica via MQTT"""
        if not self.conectado:
            print("[WARN] No conectado al broker, saltando lectura")
            return False

        try:
            # 1. Leer sensores fisicos (simulado)
            humedad = self.leer_humedad_suelo()
            temperatura = self.leer_temperatura()

            # 2. Crear mensaje
            mensaje = self.crear_mensaje(humedad, temperatura)

            # 3. Publicar via MQTT
            result = self.client.publish(
                topic=MQTT_TOPIC,
                payload=mensaje,
                qos=1,  # QoS 1 = Al menos una vez
                retain=False
            )

            # 4. Verificar publicacion
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                self.lecturas_enviadas += 1

                print(f"[{self.lecturas_enviadas}] Lectura publicada")
                print(f"    Humedad: {humedad}%")
                print(f"    Temperatura: {temperatura}°C")
                print(f"    Topic: {MQTT_TOPIC}")
                print(f"    Timestamp: {datetime.now().strftime('%H:%M:%S')}\n")

                return True
            else:
                print(f"[ERROR] Fallo al publicar (rc={result.rc})")
                return False

        except Exception as e:
            print(f"[ERROR] Excepcion en publicacion: {e}")
            return False

    def conectar(self):
        """Conecta al broker MQTT"""
        try:
            print("=" * 60)
            print(f"  NODO SENSOR: {self.sensor_id}")
            print(f"  {self.nombre}")
            print("=" * 60)
            print(f"\nConectando a broker MQTT...")
            print(f"Broker: {MQTT_BROKER}:{MQTT_PORT}\n")

            self.client.connect(MQTT_BROKER, MQTT_PORT, 60)
            self.client.loop_start()  # Iniciar loop en background

            # Esperar conexion
            timeout = 5
            for i in range(timeout):
                if self.conectado:
                    break
                time.sleep(1)

            if not self.conectado:
                print("[ERROR] Timeout esperando conexion")
                return False

            return True

        except ConnectionRefusedError:
            print("[ERROR] No se pudo conectar al broker MQTT")
            print("\n   El broker Mosquitto debe estar corriendo.")
            print("\n   Instalacion:")
            print("   - Windows: Descargar desde https://mosquitto.org/download/")
            print("   - Linux: sudo apt-get install mosquitto")
            print("\n   Iniciar broker:")
            print("   mosquitto -v")
            return False

        except Exception as e:
            print(f"[ERROR] Fallo conexion: {e}")
            return False

    def ejecutar_ciclo_continuo(self):
        """Ciclo principal del nodo sensor"""
        if not self.conectar():
            return

        print("[OK] Nodo sensor iniciado")
        print(f"     Intervalo de lectura: {INTERVALO} segundos")
        print("     (Presiona Ctrl+C para detener)\n")

        try:
            while True:
                # Publicar lectura
                self.publicar_lectura()

                # Esperar intervalo
                print(f"    Proxima lectura en {INTERVALO} segundos...")
                print("-" * 60)
                time.sleep(INTERVALO)

        except KeyboardInterrupt:
            print("\n\n" + "=" * 60)
            print("  DETENIENDO NODO SENSOR")
            print("=" * 60)
            print(f"\n  Total de lecturas enviadas: {self.lecturas_enviadas}")
            print("\nDesconectando del broker...")

            self.client.loop_stop()
            self.client.disconnect()

            print("[OK] Nodo sensor detenido correctamente\n")

def test_lectura_unica():
    """Modo de prueba: envia una sola lectura"""
    print("\n" + "=" * 60)
    print("  MODO DE PRUEBA: LECTURA UNICA")
    print("=" * 60)

    nodo = NodoSensor(SENSOR_ID, SENSOR_NAME)

    if nodo.conectar():
        print("\n[TEST] Enviando lectura unica...\n")
        time.sleep(1)

        if nodo.publicar_lectura():
            print("[OK] Test exitoso")
        else:
            print("[ERROR] Test fallido")

        time.sleep(2)
        nodo.client.loop_stop()
        nodo.client.disconnect()

if __name__ == "__main__":
    import sys

    print("\n" + "=" * 60)
    print("  SIMULADOR DE NODO SENSOR IoT")
    print("  Protocolo: MQTT")
    print("=" * 60)

    # Verificar si hay broker corriendo
    print("\nVerificando broker MQTT...")

    try:
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(2)
        result = s.connect_ex((MQTT_BROKER, MQTT_PORT))
        s.close()

        if result != 0:
            print("[ERROR] No hay broker MQTT escuchando en puerto 1883")
            print("\n  Necesitas instalar y ejecutar Mosquitto:")
            print("  1. Instalar: https://mosquitto.org/download/")
            print("  2. Ejecutar: mosquitto -v")
            print("\n  O cambiar MQTT_BROKER en el codigo si esta en otra maquina")
            exit(1)
        else:
            print("[OK] Broker MQTT detectado\n")

    except Exception as e:
        print(f"[WARN] No se pudo verificar broker: {e}\n")

    # Modo de ejecucion
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        test_lectura_unica()
    else:
        # Modo continuo
        nodo = NodoSensor(SENSOR_ID, SENSOR_NAME)
        nodo.ejecutar_ciclo_continuo()
