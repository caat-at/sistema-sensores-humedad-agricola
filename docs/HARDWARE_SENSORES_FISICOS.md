# Guía: Conectar Sensores Físicos Reales

Esta guía te muestra cómo conectar sensores físicos de humedad de suelo y temperatura al sistema para que envíen datos automáticamente.

---

## 📟 Opciones de Hardware

### Opción 1: Arduino + Sensor de Humedad (Principiantes)

**Hardware necesario:**
- Arduino Uno/Nano/ESP32 (~$10-30)
- Sensor de humedad de suelo capacitivo (~$3-5)
- Sensor de temperatura DHT22 (~$5)
- Cable USB
- Internet WiFi (para ESP32)

**Ventajas:**
- ✅ Fácil de programar
- ✅ Económico
- ✅ Gran comunidad

### Opción 2: Raspberry Pi Zero W (Intermedio)

**Hardware necesario:**
- Raspberry Pi Zero W (~$15)
- Sensor I2C (AHT20 o BME280) (~$8)
- Sensor de humedad de suelo analógico (~$3)
- Convertidor ADC MCP3008 (~$5)

**Ventajas:**
- ✅ Linux completo
- ✅ WiFi integrado
- ✅ Puede correr Python directamente

### Opción 3: ESP32/ESP8266 (Avanzado)

**Hardware necesario:**
- ESP32 DevKit (~$8)
- Sensores varios
- Batería solar (opcional)

**Ventajas:**
- ✅ WiFi integrado
- ✅ Bajo consumo
- ✅ Perfecto para campo

---

## 🔧 Ejemplo 1: Arduino + ESP32

### Hardware Setup

```
ESP32 DevKit v1
├── GPIO 34 ──> Sensor Humedad (Analógico)
├── GPIO 4  ──> DHT22 Data Pin
├── 3.3V    ──> Sensores VCC
└── GND     ──> Sensores GND
```

### Código Arduino (C++)

```cpp
#include <WiFi.h>
#include <HTTPClient.h>
#include <DHT.h>

// ============ CONFIGURACION ============
const char* ssid = "TU_WIFI_SSID";
const char* password = "TU_WIFI_PASSWORD";
const char* apiUrl = "http://TU_IP:8000/api/readings";
const char* sensorId = "SENSOR_001";

// Pines
#define DHT_PIN 4
#define HUMEDAD_PIN 34

// Configuracion de sensores
#define DHT_TYPE DHT22
DHT dht(DHT_PIN, DHT_TYPE);

// Intervalo de lectura (milisegundos)
const unsigned long INTERVALO = 60000; // 1 minuto
unsigned long ultimaLectura = 0;

void setup() {
  Serial.begin(115200);

  // Conectar WiFi
  Serial.println("Conectando a WiFi...");
  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("\nWiFi conectado!");
  Serial.print("IP: ");
  Serial.println(WiFi.localIP());

  // Iniciar sensor DHT
  dht.begin();
}

void loop() {
  unsigned long tiempoActual = millis();

  // Leer cada INTERVALO
  if (tiempoActual - ultimaLectura >= INTERVALO) {
    ultimaLectura = tiempoActual;

    // 1. Leer sensor de humedad de suelo
    int humedadRaw = analogRead(HUMEDAD_PIN);
    int humedadPorcentaje = map(humedadRaw, 4095, 0, 0, 100); // ESP32 ADC es 12-bit
    humedadPorcentaje = constrain(humedadPorcentaje, 0, 100);

    // 2. Leer sensor de temperatura
    float temp = dht.readTemperature();

    // Verificar lecturas validas
    if (isnan(temp)) {
      Serial.println("Error leyendo DHT22");
      return;
    }

    // 3. Enviar a API
    enviarLectura(sensorId, humedadPorcentaje, (int)temp);
  }
}

void enviarLectura(const char* sensor, int humedad, int temperatura) {
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;

    http.begin(apiUrl);
    http.addHeader("Content-Type", "application/json");

    // Crear JSON
    String json = "{";
    json += "\"sensor_id\":\"" + String(sensor) + "\",";
    json += "\"humidity_percentage\":" + String(humedad) + ",";
    json += "\"temperature_celsius\":" + String(temperatura);
    json += "}";

    Serial.println("Enviando: " + json);

    int httpCode = http.POST(json);

    if (httpCode > 0) {
      String response = http.getString();
      Serial.println("Respuesta: " + response);

      if (httpCode == 200) {
        Serial.println("[OK] Lectura enviada exitosamente");
      }
    } else {
      Serial.println("[ERROR] Error HTTP: " + String(httpCode));
    }

    http.end();
  } else {
    Serial.println("[ERROR] WiFi desconectado");
  }
}
```

### Configuración:

1. **Instala Arduino IDE**: https://www.arduino.cc/en/software
2. **Instala librerías**:
   - DHT sensor library (by Adafruit)
   - HTTPClient (incluida)
3. **Modifica el código**:
   - `ssid`: Nombre de tu WiFi
   - `password`: Contraseña de tu WiFi
   - `apiUrl`: Tu IP local (ej: `http://192.168.1.100:8000/api/readings`)
   - `sensorId`: "SENSOR_001" (o el que tengas registrado)
4. **Sube el código** al ESP32
5. **Abre Serial Monitor** (115200 baud) para ver el log

---

## 🍓 Ejemplo 2: Raspberry Pi + Python

### Hardware Setup

```
Raspberry Pi Zero W
├── GPIO 4  ──> DHT22 Data Pin
├── SDA     ──> Sensor I2C
├── SCL     ──> Sensor I2C
├── 3.3V    ──> Sensores VCC
└── GND     ──> Sensores GND
```

### Código Python

```python
#!/usr/bin/env python3
"""
Sensor IoT para Raspberry Pi
Lee sensores fisicos y envia datos al sistema
"""

import RPi.GPIO as GPIO
import Adafruit_DHT
import requests
import time
from datetime import datetime

# ============ CONFIGURACION ============
API_URL = "http://192.168.1.100:8000/api/readings"  # Cambia por tu IP
SENSOR_ID = "SENSOR_001"
INTERVALO = 60  # segundos

# Pines GPIO
DHT_PIN = 4
DHT_TYPE = Adafruit_DHT.DHT22

# Configuracion GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

def leer_dht22():
    """Lee temperatura y humedad del DHT22"""
    humedad, temperatura = Adafruit_DHT.read_retry(DHT_TYPE, DHT_PIN)

    if humedad is not None and temperatura is not None:
        return int(humedad), int(temperatura)
    else:
        return None, None

def leer_humedad_suelo():
    """
    Lee sensor de humedad de suelo
    Si usas sensor analogico, necesitas MCP3008 (ADC)
    """
    # Implementa segun tu sensor
    # Por ahora, simulacion
    import random
    return random.randint(40, 80)

def enviar_lectura(sensor_id, humedad_suelo, temperatura):
    """Envia lectura a la API"""
    data = {
        "sensor_id": sensor_id,
        "humidity_percentage": humedad_suelo,
        "temperature_celsius": temperatura
    }

    try:
        response = requests.post(API_URL, json=data, timeout=10)

        if response.status_code == 200:
            result = response.json()
            return True, result
        else:
            return False, f"HTTP {response.status_code}"

    except Exception as e:
        return False, str(e)

def main():
    print("=" * 60)
    print(f"Sensor IoT - Raspberry Pi")
    print(f"Sensor ID: {SENSOR_ID}")
    print(f"Intervalo: {INTERVALO} segundos")
    print("=" * 60)

    contador = 0

    try:
        while True:
            contador += 1
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            print(f"\n[Lectura #{contador}] {timestamp}")

            # Leer sensor de humedad de suelo
            humedad_suelo = leer_humedad_suelo()
            print(f"  Humedad suelo: {humedad_suelo}%")

            # Leer DHT22
            humedad_aire, temperatura = leer_dht22()

            if temperatura is not None:
                print(f"  Temperatura: {temperatura}°C")

                # Enviar a API
                exito, resultado = enviar_lectura(SENSOR_ID, humedad_suelo, temperatura)

                if exito:
                    print(f"  [OK] Datos enviados - Alerta: {resultado.get('alert_level')}")
                else:
                    print(f"  [ERROR] {resultado}")
            else:
                print("  [ERROR] No se pudo leer DHT22")

            # Esperar
            time.sleep(INTERVALO)

    except KeyboardInterrupt:
        print("\n\nDeteniendo sensor...")
        GPIO.cleanup()
        print(f"Total de lecturas: {contador}")

if __name__ == "__main__":
    main()
```

### Instalación en Raspberry Pi:

```bash
# Actualizar sistema
sudo apt-get update
sudo apt-get upgrade

# Instalar dependencias
sudo apt-get install python3-pip python3-dev

# Instalar librerías Python
pip3 install RPi.GPIO
pip3 install Adafruit_DHT
pip3 install requests

# Ejecutar
python3 sensor_raspberry.py
```

---

## 🖥️ Ejemplo 3: Script Python Simulado (Para Testing)

Para probar el sistema **sin hardware real**, usa el script que creé:

```powershell
# Activar entorno virtual
.\.venv\Scripts\Activate.ps1

# Ejecutar sensor simulado
python sensor_fisico_simulado.py
```

Este script:
- ✅ Simula un sensor físico real
- ✅ Genera valores realistas de humedad/temperatura
- ✅ Envía datos cada 60 segundos al SENSOR_001
- ✅ Muestra niveles de alerta en tiempo real
- ✅ Maneja errores de conexión

---

## 📊 Monitoreo en Tiempo Real

Una vez que el sensor físico está enviando datos:

### 1. Ver en Dashboard
```
http://localhost:8000/dashboard
```
- Pestaña "Lecturas por Sensor"
- Selecciona SENSOR_001
- Verás gráficos actualizados

### 2. Ver en API
```bash
# Ultimas 10 lecturas
curl "http://localhost:8000/api/readings?sensor_id=SENSOR_001&limit=10"
```

### 3. Ver logs del sensor
El sensor imprime en consola cada lectura y su estado

---

## 🔋 Alimentación en Campo

### Opción Solar (Recomendado)

```
Panel Solar 6V 1W
    ↓
Regulador de Carga
    ↓
Batería LiPo 3.7V 2000mAh
    ↓
ESP32 / Raspberry Pi Zero
```

**Duración estimada:**
- ESP32 en deep sleep: 1-3 meses
- Raspberry Pi Zero: 2-5 días (con panel solar continuo)

---

## 📡 Conectividad

### WiFi (Más fácil)
```cpp
WiFi.begin(ssid, password);
```

### LoRa (Para larga distancia)
- Alcance: hasta 10 km en campo abierto
- Bajo consumo
- Requiere gateway LoRa

### GSM/4G (Sin WiFi disponible)
- Módulo SIM800L o SIM7600
- Requiere SIM card con datos
- Mayor consumo

---

## 🔒 Seguridad

### 1. Autenticación API (Recomendado para producción)

Agrega autenticación JWT a la API:

```python
headers = {
    "Authorization": "Bearer TU_TOKEN_JWT",
    "Content-Type": "application/json"
}

response = requests.post(API_URL, json=data, headers=headers)
```

### 2. HTTPS

Usa certificados SSL para comunicación segura:

```cpp
// Arduino/ESP32
http.begin("https://tu-dominio.com/api/readings");
```

### 3. Validación de Datos

El sistema ya valida:
- Humedad: 0-100%
- Temperatura: -30°C a 60°C
- Sensor debe existir

---

## 🐛 Troubleshooting

### Sensor no envía datos

**Verificar:**
1. WiFi conectado: `WiFi.status()`
2. API accesible: Ping a la IP del servidor
3. Sensor ID correcto: Debe estar registrado
4. Firewall: Puerto 8000 abierto

### Lecturas erróneas

**Soluciones:**
1. **DHT22 da NaN**: Agregar resistencia pull-up 10kΩ
2. **Humedad siempre 100%**: Calibrar sensor con tierra seca/húmeda
3. **Valores inestables**: Promediar 3-5 lecturas

### Consumo de batería alto

**Optimizar:**
1. Usar Deep Sleep entre lecturas
2. Reducir frecuencia de envío
3. Apagar WiFi entre transmisiones

---

## 📈 Próximos Pasos

1. **Instala el hardware** según tu opción elegida
2. **Prueba primero** con el script simulado
3. **Adapta el código** para tu sensor específico
4. **Despliega en campo** con alimentación solar
5. **Monitorea** en el dashboard en tiempo real

---

## 📚 Recursos

### Documentación de Sensores
- **DHT22**: https://learn.adafruit.com/dht
- **Sensor Humedad Capacitivo**: Guías en internet
- **BME280**: https://github.com/adafruit/Adafruit_BME280_Library

### Tutoriales ESP32
- **ESP32 + WiFi**: https://randomnerdtutorials.com/esp32-wifi-manager/
- **ESP32 Deep Sleep**: https://randomnerdtutorials.com/esp32-deep-sleep-arduino-ide-wake-up-sources/

### Comunidad
- **Arduino Forum**: https://forum.arduino.cc/
- **Raspberry Pi Forum**: https://forums.raspberrypi.com/

---

**¡Tu sistema está listo para recibir datos de sensores reales! 🌱**
