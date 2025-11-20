# Cómo Capturar Datos de un Nodo Sensor

Guía completa para conectar sensores IoT físicos al sistema blockchain.

---

## 🎯 Respuesta Rápida

Para capturar datos de un nodo sensor tienes **3 opciones**:

### 1. **HTTP REST** (El más simple - Ya implementado) ✅

El nodo sensor envía directamente a la API:

```
Sensor IoT → WiFi → POST http://tu-ip:8000/api/readings → API → Blockchain
```

**Ejecutar ahora:**
```powershell
# Simular un nodo sensor
python sensor_fisico_simulado.py
```

### 2. **MQTT** (El más escalable - Profesional) 📡

Los sensores publican a un broker, un gateway escucha y reenvía a la API:

```
Sensor IoT → MQTT Broker → Gateway Listener → API → Blockchain
```

**Ejecutar:**
```powershell
# Terminal 1: Broker MQTT
mosquitto -v

# Terminal 2: Gateway
python mqtt_gateway.py

# Terminal 3: Nodo sensor simulado
python nodo_sensor_mqtt.py
```

### 3. **Hardware Real** (Producción) 🔧

Código Arduino/ESP32 que lee sensores físicos y envía datos.

**Ver:** [HARDWARE_SENSORES_FISICOS.md](HARDWARE_SENSORES_FISICOS.md)

---

## 📋 Archivos Creados Para Ti

| Archivo | Descripción | Cómo Usar |
|---------|-------------|-----------|
| **sensor_fisico_simulado.py** | Simula un sensor enviando datos via HTTP | `python sensor_fisico_simulado.py` |
| **mqtt_gateway.py** | Gateway que convierte MQTT → API REST | `python mqtt_gateway.py` |
| **nodo_sensor_mqtt.py** | Simula nodo sensor con protocolo MQTT | `python nodo_sensor_mqtt.py` |
| **ARQUITECTURAS_CAPTURA_DATOS.md** | Guía completa de 5 métodos diferentes | Leer para decidir arquitectura |
| **HARDWARE_SENSORES_FISICOS.md** | Código para Arduino/ESP32/Raspberry Pi | Copiar código a tu dispositivo |

---

## 🚀 Ejemplo Práctico: SENSOR_001 con HTTP REST

El método más simple ya está funcionando. Sigue estos pasos:

### Paso 1: Verificar que el servidor esté corriendo

El servidor ya está corriendo en: http://localhost:8000

Verifica:
```powershell
curl http://localhost:8000/api/health
```

### Paso 2: Ejecutar el nodo sensor simulado

En una **nueva terminal** PowerShell:

```powershell
cd c:\Proyectos\WINDOWS\PYTHON\sistema-sensores-humedad-agricola
.\.venv\Scripts\Activate.ps1
python sensor_fisico_simulado.py
```

### Paso 3: Ver qué pasa

El script simulará un sensor físico que:
1. Lee humedad del suelo (simulado)
2. Lee temperatura (simulado)
3. Envía a la API cada 60 segundos
4. Muestra el nivel de alerta

**Salida esperada:**
```
======================================================================
  SENSOR FISICO: SENSOR_001
  Ubicacion: Campo Norte - Parcela A
  Intervalo de lectura: 60 segundos
======================================================================

[OK] Sensor encontrado en el sistema:
     ID: SENSOR_001
     Zona: Campo Norte - Parcela A
     Ubicacion: (-34.58, -58.45)
     Umbrales: 25% - 75%
     Estado: Active

[OK] Todo listo para comenzar el monitoreo

======================================================================
  SENSOR FISICO: SENSOR_001
  Ubicacion: Campo Norte - Parcela A
  Intervalo de lectura: 60 segundos
======================================================================

Iniciando monitoreo continuo...
(Presiona Ctrl+C para detener)

[Lectura #1] 2025-10-29 18:30:00
  [1/3] Leyendo sensor de humedad del suelo...
        Humedad: 65%
  [2/3] Leyendo sensor de temperatura...
        Temperatura: 23°C
  [3/3] Enviando datos al sistema...
        [OK] Lectura guardada exitosamente
        Nivel de alerta: Normal

  Estadisticas: 1 exitosas | 0 fallidas

  Proxima lectura en 60 segundos...
```

### Paso 4: Ver los datos en el dashboard

Abre: http://localhost:8000/dashboard

1. Ve a la pestaña "Lecturas por Sensor"
2. Selecciona "SENSOR_001"
3. Verás el gráfico actualizándose con las nuevas lecturas

---

## 🔧 Hardware Real: ESP32 + Sensores

### Lo que necesitas comprar:

| Componente | Precio aprox | Link ejemplo |
|------------|-------------|--------------|
| ESP32 DevKit | $8-12 | AliExpress/Amazon |
| Sensor DHT22 | $5 | AliExpress |
| Sensor Humedad Suelo Capacitivo | $3 | AliExpress |
| Cables Dupont | $2 | AliExpress |
| **Total** | **~$20** | |

### Conexiones:

```
ESP32 DevKit
├── GPIO 34 ─────> Sensor Humedad Suelo (Analog Out)
├── GPIO 4  ─────> DHT22 (Data Pin)
├── 3.3V    ─────> Sensores (VCC)
└── GND     ─────> Sensores (GND)
```

### Código Arduino (ESP32):

```cpp
#include <WiFi.h>
#include <HTTPClient.h>
#include <DHT.h>

// WiFi
const char* ssid = "TU_WIFI";
const char* password = "TU_PASSWORD";

// API
const char* apiUrl = "http://192.168.1.100:8000/api/readings";
const char* sensorId = "SENSOR_001";

// Pines
#define DHT_PIN 4
#define HUMEDAD_PIN 34

DHT dht(DHT_PIN, DHT22);

void setup() {
    Serial.begin(115200);

    // Conectar WiFi
    WiFi.begin(ssid, password);
    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }
    Serial.println("\nWiFi conectado!");

    dht.begin();
}

void loop() {
    // 1. Leer sensor de humedad de suelo
    int humedadRaw = analogRead(HUMEDAD_PIN);
    int humedad = map(humedadRaw, 4095, 0, 0, 100);
    humedad = constrain(humedad, 0, 100);

    // 2. Leer DHT22
    float temp = dht.readTemperature();

    if (isnan(temp)) {
        Serial.println("Error leyendo DHT22");
        delay(60000);
        return;
    }

    // 3. Enviar a API
    enviarDatos(humedad, (int)temp);

    // 4. Esperar 1 minuto
    delay(60000);
}

void enviarDatos(int humedad, int temp) {
    HTTPClient http;

    http.begin(apiUrl);
    http.addHeader("Content-Type", "application/json");

    // Crear JSON
    String json = "{";
    json += "\"sensor_id\":\"" + String(sensorId) + "\",";
    json += "\"humidity_percentage\":" + String(humedad) + ",";
    json += "\"temperature_celsius\":" + String(temp);
    json += "}";

    Serial.println("Enviando: " + json);

    int httpCode = http.POST(json);

    if (httpCode == 200) {
        String response = http.getString();
        Serial.println("[OK] Enviado: " + response);
    } else {
        Serial.println("[ERROR] HTTP " + String(httpCode));
    }

    http.end();
}
```

### Pasos:

1. **Instalar Arduino IDE**: https://www.arduino.cc/en/software
2. **Agregar soporte ESP32**:
   - File → Preferences → Additional Board Manager URLs
   - Agregar: `https://dl.espressif.com/dl/package_esp32_index.json`
3. **Instalar librerías**:
   - Tools → Manage Libraries → Buscar "DHT sensor library" by Adafruit
   - Instalar también "Adafruit Unified Sensor"
4. **Configurar**:
   - Tools → Board → ESP32 Arduino → ESP32 Dev Module
   - Tools → Port → (Seleccionar puerto COM)
5. **Subir código**: Click en Upload (→)

---

## 📡 Arquitectura MQTT (Avanzado)

Si tienes **muchos sensores** (>10), usa MQTT:

### Ventajas:
- ✅ Escala a miles de sensores
- ✅ Menor consumo de batería
- ✅ Buffer automático (mensajes no se pierden)
- ✅ Desacoplado (sensores independientes de la API)

### Componentes:

```
Sensores (1-N)
    │
    │ Publican a topic "sensores/humedad/{sensor_id}"
    │
    v
Broker MQTT (Mosquitto)
    │
    │ Almacena mensajes temporalmente
    │
    v
Gateway Listener (Python)
    │
    │ Escucha mensajes MQTT
    │ Convierte MQTT → HTTP POST
    │
    v
API REST :8000
    │
    v
Blockchain + DB
```

### Instalación:

#### Windows:
1. Descargar Mosquitto: https://mosquitto.org/download/
2. Instalar
3. Abrir CMD como Admin:
```cmd
cd "C:\Program Files\mosquitto"
mosquitto -v
```

#### Linux:
```bash
sudo apt-get update
sudo apt-get install mosquitto mosquitto-clients
sudo systemctl start mosquitto
```

### Uso:

```powershell
# Terminal 1: Broker MQTT (dejar corriendo)
mosquitto -v

# Terminal 2: Gateway (convierte MQTT a API)
.\.venv\Scripts\Activate.ps1
pip install paho-mqtt
python mqtt_gateway.py

# Terminal 3: Nodo sensor (simula ESP32 enviando via MQTT)
python nodo_sensor_mqtt.py
```

---

## 🔄 Flujo Completo de Datos

```
1. Sensor Lee Hardware
   ├─ Sensor de humedad capacitivo
   ├─ Sensor DHT22 temperatura
   └─ Otros sensores

2. Nodo Procesa
   ├─ Valida rangos
   ├─ Crea JSON
   └─ Envía via WiFi/LoRa/4G

3. Gateway/API Recibe
   ├─ HTTP REST (directo)
   ├─ MQTT (via broker)
   └─ WebSocket (tiempo real)

4. API Valida
   ├─ Sensor existe?
   ├─ Humedad 0-100%?
   └─ Temperatura -30 a 60°C?

5. Blockchain Service
   ├─ Crea transacción Cardano
   ├─ Firma con wallet
   └─ Envía a Preview Testnet

6. Almacenamiento Dual
   ├─ Blockchain (inmutable)
   └─ PostgreSQL (cache rápido)

7. Dashboard Muestra
   ├─ Gráficos en tiempo real
   ├─ Alertas (Normal/Low/High/Critical)
   └─ Historial completo
```

---

## ⚡ Comparación de Métodos

| Característica | HTTP REST | MQTT | LoRa | 4G |
|----------------|-----------|------|------|-----|
| **Complejidad** | Baja ⭐ | Media ⭐⭐ | Alta ⭐⭐⭐ | Media ⭐⭐ |
| **Alcance** | 50m (WiFi) | 50m (WiFi) | 2-15 km | Ilimitado |
| **Consumo** | Alto | Medio | Muy bajo | Medio-Alto |
| **Escalabilidad** | <10 sensores | Cientos | Miles | Decenas |
| **Costo setup** | $20 | $40 | $150+ | $30+ mensual |
| **Ya funciona** | ✅ Sí | ✅ Sí (con scripts) | ❌ No | ❌ No |

---

## 🎯 Recomendación por Escenario

### Tienes 1-5 sensores en tu casa/oficina
**→ Usa HTTP REST**
- Simple, ya funciona
- Script: `sensor_fisico_simulado.py`

### Tienes 10-100 sensores en un campo con WiFi
**→ Usa MQTT**
- Escalable y eficiente
- Scripts: `mqtt_gateway.py` + `nodo_sensor_mqtt.py`

### Campo grande sin WiFi (varios km)
**→ Usa LoRaWAN**
- Ver: [HARDWARE_SENSORES_FISICOS.md](HARDWARE_SENSORES_FISICOS.md)

### Zona remota sin infraestructura
**→ Usa 4G/LTE**
- Ver: [HARDWARE_SENSORES_FISICOS.md](HARDWARE_SENSORES_FISICOS.md)

---

## 🎬 Demo Ahora Mismo

Quieres verlo funcionando? Ejecuta esto:

```powershell
# El servidor ya está corriendo...

# En una NUEVA terminal:
cd c:\Proyectos\WINDOWS\PYTHON\sistema-sensores-humedad-agricola
.\.venv\Scripts\Activate.ps1
python sensor_fisico_simulado.py
```

Luego abre: http://localhost:8000/dashboard

¡Verás las lecturas llegando en tiempo real! 📊

---

## 📚 Documentación Completa

1. **[HARDWARE_SENSORES_FISICOS.md](HARDWARE_SENSORES_FISICOS.md)** - Código Arduino/Raspberry Pi
2. **[ARQUITECTURAS_CAPTURA_DATOS.md](ARQUITECTURAS_CAPTURA_DATOS.md)** - 5 métodos diferentes
3. **[GUIA_USO_SENSORES.md](GUIA_USO_SENSORES.md)** - Cómo usar la API
4. **[INICIO_RAPIDO.md](INICIO_RAPIDO.md)** - Ejecutar el proyecto

---

**¡Tu sistema está listo para capturar datos de nodos sensores reales! 🌱📡**
