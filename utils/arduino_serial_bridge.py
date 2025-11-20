"""
Puente Serial Arduino -> API REST
Lee datos del Arduino via USB Serial y los envia a la API
"""

import serial
import json
import requests
import time
from datetime import datetime

# ========== CONFIGURACION ==========
PUERTO_COM = "COM3"  # CAMBIA esto por tu puerto (ej: COM3, COM4)
BAUD_RATE = 9600
API_URL = "http://localhost:8000/api/readings"
# ===================================

class ArduinoSerialBridge:
    """Puente entre Arduino Serial y API REST"""

    def __init__(self, puerto, baud_rate):
        self.puerto = puerto
        self.baud_rate = baud_rate
        self.serial = None
        self.lecturas_enviadas = 0
        self.lecturas_fallidas = 0

    def conectar(self):
        """Conecta al puerto serial del Arduino"""
        try:
            print("=" * 60)
            print("  PUENTE SERIAL: Arduino -> API REST")
            print("=" * 60)
            print(f"\nConectando a {self.puerto} @ {self.baud_rate} baud...")

            self.serial = serial.Serial(
                port=self.puerto,
                baudrate=self.baud_rate,
                timeout=1
            )

            # Esperar que el Arduino se reinicie (DTR reset)
            print("Esperando que Arduino se reinicie...")
            time.sleep(2)

            # Limpiar buffer
            self.serial.reset_input_buffer()

            print(f"[OK] Conectado a {self.puerto}\n")
            return True

        except serial.SerialException as e:
            print(f"\n[ERROR] No se pudo abrir {self.puerto}")
            print(f"Error: {e}\n")
            print("Posibles causas:")
            print("  - Puerto incorrecto (verifica en Device Manager)")
            print("  - Arduino no conectado")
            print("  - Driver CH340 no instalado")
            print("  - Puerto ocupado por otro programa (cierra Serial Monitor)")
            return False

    def leer_linea(self):
        """Lee una línea del serial"""
        try:
            if self.serial.in_waiting > 0:
                linea = self.serial.readline().decode('utf-8', errors='ignore').strip()
                return linea
            return None

        except Exception as e:
            print(f"[ERROR] Leyendo serial: {e}")
            return None

    def es_json(self, linea):
        """Verifica si la línea es un JSON válido"""
        return linea.startswith('{') and linea.endswith('}')

    def enviar_a_api(self, data):
        """Envía datos a la API REST"""
        try:
            response = requests.post(API_URL, json=data, timeout=60)

            # 200 OK y 201 Created son ambos códigos de éxito
            if response.status_code in [200, 201]:
                result = response.json()
                tx_hash = result.get('tx_hash', 'N/A')

                print(f"    [OK] Lectura guardada en blockchain")
                print(f"         TX Hash: {tx_hash[:16]}...{tx_hash[-8:] if len(tx_hash) > 24 else ''}")

                self.lecturas_enviadas += 1
                return True
            else:
                print(f"    [ERROR] API respondió con código {response.status_code}")
                self.lecturas_fallidas += 1
                return False

        except requests.exceptions.ConnectionError:
            print(f"    [ERROR] No se pudo conectar a la API")
            print(f"            Verifica que el servidor esté corriendo")
            self.lecturas_fallidas += 1
            return False

        except Exception as e:
            print(f"    [ERROR] {e}")
            self.lecturas_fallidas += 1
            return False

    def procesar_linea(self, linea):
        """Procesa una línea recibida del Arduino"""
        # Mostrar todas las líneas (logs del Arduino)
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {linea}")

        # Si es JSON, enviar a API
        if self.es_json(linea):
            try:
                data = json.loads(linea)

                # Verificar campos requeridos
                if all(k in data for k in ['sensor_id', 'humidity_percentage', 'temperature_celsius']):
                    print(f"\n    [->] JSON detectado:")
                    print(f"         Sensor: {data['sensor_id']}")
                    print(f"         Humedad: {data['humidity_percentage']}%")
                    print(f"         Temperatura: {data['temperature_celsius']}°C")

                    # Enviar a API
                    self.enviar_a_api(data)
                    print()  # Línea en blanco

            except json.JSONDecodeError:
                # No es un JSON válido, ignorar
                pass

    def mostrar_estadisticas(self):
        """Muestra estadísticas del puente"""
        print("\n" + "=" * 60)
        print("  ESTADISTICAS")
        print("=" * 60)
        print(f"  Lecturas enviadas a API:  {self.lecturas_enviadas}")
        print(f"  Lecturas fallidas:        {self.lecturas_fallidas}")

        if self.lecturas_enviadas + self.lecturas_fallidas > 0:
            total = self.lecturas_enviadas + self.lecturas_fallidas
            tasa_exito = (self.lecturas_enviadas / total) * 100
            print(f"  Tasa de éxito:            {tasa_exito:.1f}%")

        print("=" * 60 + "\n")

    def iniciar(self):
        """Inicia el puente en modo escucha"""
        if not self.conectar():
            return

        print("[OK] Puente iniciado")
        print("     Esperando datos del Arduino...")
        print("     (Presiona Ctrl+C para detener)\n")

        try:
            while True:
                linea = self.leer_linea()

                if linea:
                    self.procesar_linea(linea)

                # Pequeño delay para no saturar CPU
                time.sleep(0.01)

        except KeyboardInterrupt:
            print("\n\n" + "=" * 60)
            print("  DETENIENDO PUENTE")
            print("=" * 60)

            self.mostrar_estadisticas()

            if self.serial:
                self.serial.close()
                print("Puerto serial cerrado")

            print("[OK] Puente detenido correctamente\n")

def listar_puertos_disponibles():
    """Lista los puertos COM disponibles"""
    import serial.tools.list_ports

    puertos = list(serial.tools.list_ports.comports())

    if not puertos:
        print("[!] No se detectaron puertos COM")
        print("    Verifica que el Arduino esté conectado")
        return

    print("\nPuertos COM detectados:")
    print("-" * 60)

    for puerto in puertos:
        print(f"  Puerto: {puerto.device}")
        print(f"  Descripción: {puerto.description}")
        if "CH340" in puerto.description.upper():
            print(f"  >>> Este parece ser tu Arduino Uno <<<")
        print()

def verificar_api():
    """Verifica que la API esté disponible"""
    try:
        response = requests.get("http://localhost:8000/api/health", timeout=5)
        if response.status_code == 200:
            print("[OK] API disponible\n")
            return True
        else:
            print(f"[WARN] API respondió con código {response.status_code}\n")
            return False
    except:
        print("[ERROR] No se pudo conectar a la API")
        print("        Asegúrate de que el servidor esté corriendo:")
        print("        PowerShell: .\\start.ps1\n")
        return False

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  PUENTE SERIAL: Arduino Uno -> API REST")
    print("  Sistema de Sensores Agrícolas")
    print("=" * 60)

    # Listar puertos disponibles
    print("\n[1/3] Detectando puertos COM...")
    listar_puertos_disponibles()

    # Verificar puerto configurado
    print(f"[2/3] Puerto configurado: {PUERTO_COM}")
    print(f"      (Si es incorrecto, edita PUERTO_COM en el script)\n")

    # Verificar API
    print("[3/3] Verificando API REST...")
    if not verificar_api():
        print("\n[!] ¿Continuar de todas formas? (y/n): ", end='')
        respuesta = input().strip().lower()
        if respuesta != 'y':
            print("\nAbortando...")
            exit(1)

    # Iniciar puente
    print("\nIniciando puente serial...\n")

    puente = ArduinoSerialBridge(PUERTO_COM, BAUD_RATE)
    puente.iniciar()
