# Arquitecturas para Capturar Datos de Nodos Sensores

Esta guía muestra las diferentes formas de capturar datos de nodos sensores IoT y enviarlos al sistema blockchain.

---

## Arquitectura Actual del Sistema

```
┌─────────────────────────────────────────────────────────────┐
│                    NODOS SENSORES                            │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│  │ESP32     │  │Raspberry │  │Arduino   │  │Otro IoT  │    │
│  │+ DHT22   │  │Pi Zero   │  │+ WiFi    │  │Device    │    │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘    │
└───────┼─────────────┼─────────────┼─────────────┼──────────┘
        │             │             │             │
        │  HTTP POST  │  HTTP POST  │  MQTT       │  WebSocket
        │  (WiFi)     │  (WiFi)     │  (WiFi)     │  (4G/LoRa)
        │             │             │             │
        v             v             v             v
┌─────────────────────────────────────────────────────────────┐
│                   GATEWAY / API SERVER                       │
│                   (Este proyecto actual)                     │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  API REST FastAPI (Puerto 8000)                      │   │
│  │  ┌─────────────┐  ┌──────────────┐  ┌────────────┐  │   │
│  │  │POST /sensors│  │POST /readings│  │GET /sensors│  │   │
│  │  └─────────────┘  └──────────────┘  └────────────┘  │   │
│  └──────────────────────────────────────────────────────┘   │
│                          │                                   │
│                          v                                   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Blockchain Service (PyCardano)                      │   │
│  │  - Valida datos                                      │   │
│  │  - Crea transacciones                                │   │
│  │  - Firma con wallet                                  │   │
│  │  - Envia a Cardano                                   │   │
│  └────────────────┬───────────────────────────────────┬─┘   │
└───────────────────┼───────────────────────────────────┼─────┘
                    │                                   │
                    v                                   v
      ┌─────────────────────────┐      ┌──────────────────────┐
      │  Cardano Blockchain     │      │  PostgreSQL DB       │
      │  (Preview Testnet)      │      │  (Cache local)       │
      │  - Inmutable            │      │  - Queries rapidas   │
      │  - Descentralizado      │      │  - Backup           │
      └─────────────────────────┘      └──────────────────────┘
```

---

## 🎯 Método 1: HTTP REST (Actual - Implementado)

### Arquitectura

```
Nodo Sensor (ESP32)
    │
    │ 1. Lee sensores (DHT22, Humedad suelo)
    │ 2. Crea JSON
    │ 3. HTTP POST
    │
    v
API FastAPI :8000
    │
    │ 4. Valida datos
    │ 5. Blockchain transaction
    │
    v
Cardano + PostgreSQL
```

### Código del Nodo (ESP32/Arduino)

```cpp
#include <WiFi.h>
#include <HTTPClient.h>
#include <DHT.h>

// Config
const char* apiUrl = "http://192.168.1.100:8000/api/readings";
const char* sensorId = "SENSOR_001";

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

    // Enviar
    int httpCode = http.POST(json);

    if (httpCode == 200) {
        Serial.println("[OK] Datos enviados");
    } else {
        Serial.println("[ERROR] HTTP " + String(httpCode));
    }

    http.end();
}

void loop() {
    int humedad = leerHumedad();
    int temp = leerTemperatura();

    enviarDatos(humedad, temp);

    delay(60000); // Cada minuto
}
```

### Ventajas
- ✅ Simple de implementar
- ✅ Compatible con cualquier dispositivo WiFi
- ✅ Ya implementado en el proyecto
- ✅ Trabaja sobre HTTP estandar

### Desventajas
- ❌ Consume más batería (WiFi siempre activo)
- ❌ Requiere conexión directa a internet
- ❌ No escala bien con miles de sensores

---

## 🎯 Método 2: MQTT (Recomendado para producción)

### Arquitectura

```
Nodo Sensor (ESP32)
    │
    │ 1. Lee sensores
    │ 2. Publica a topic MQTT
    │
    v
Broker MQTT (Mosquitto)
    │
    │ 3. Recibe mensaje
    │ 4. Distribuye a suscriptores
    │
    v
Gateway/Listener Python
    │
    │ 5. Procesa mensaje
    │ 6. POST a API REST
    │
    v
API FastAPI :8000
    │
    v
Cardano + PostgreSQL
```

### 1. Configurar Broker MQTT

```bash
# Instalar Mosquitto (Windows)
# Descargar desde: https://mosquitto.org/download/

# Instalar Mosquitto (Linux)
sudo apt-get install mosquitto mosquitto-clients

# Iniciar broker
mosquitto -v
```

### 2. Código del Nodo (ESP32)

```cpp
#include <WiFi.h>
#include <PubSubClient.h>
#include <DHT.h>

// Config MQTT
const char* mqtt_server = "192.168.1.100";
const int mqtt_port = 1883;
const char* mqtt_topic = "sensores/humedad";

WiFiClient espClient;
PubSubClient client(espClient);

void setup() {
    Serial.begin(115200);

    // Conectar WiFi
    WiFi.begin(ssid, password);
    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
    }

    // Configurar MQTT
    client.setServer(mqtt_server, mqtt_port);
}

void enviarMQTT(String sensorId, int humedad, int temp) {
    // Crear JSON
    String mensaje = "{";
    mensaje += "\"sensor_id\":\"" + sensorId + "\",";
    mensaje += "\"humidity_percentage\":" + String(humedad) + ",";
    mensaje += "\"temperature_celsius\":" + String(temp) + ",";
    mensaje += "\"timestamp\":\"" + obtenerTimestamp() + "\"";
    mensaje += "}";

    // Publicar
    if (client.publish(mqtt_topic, mensaje.c_str())) {
        Serial.println("[OK] Publicado en MQTT");
    } else {
        Serial.println("[ERROR] Fallo MQTT");
    }
}

void loop() {
    if (!client.connected()) {
        reconectar();
    }
    client.loop();

    // Leer y enviar
    int humedad = leerHumedad();
    int temp = leerTemperatura();

    enviarMQTT("SENSOR_001", humedad, temp);

    delay(60000); // 1 minuto
}
```

### 3. Gateway MQTT Listener (Python)

Voy a crear este script ahora...

