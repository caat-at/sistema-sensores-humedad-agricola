// api.js - Servicio para comunicación con el backend
const API_BASE_URL = 'http://localhost:3002';

// Cliente HTTP con manejo de errores
class APIClient {
    constructor(baseURL) {
        this.baseURL = baseURL;
    }

    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;

        try {
            const response = await fetch(url, {
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers,
                },
                ...options,
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.message || `HTTP ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error(`API Error [${endpoint}]:`, error);
            throw error;
        }
    }

    async get(endpoint) {
        return this.request(endpoint, { method: 'GET' });
    }

    async post(endpoint, data) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(data),
        });
    }

    async put(endpoint, data) {
        return this.request(endpoint, {
            method: 'PUT',
            body: JSON.stringify(data),
        });
    }

    async delete(endpoint) {
        return this.request(endpoint, { method: 'DELETE' });
    }
}

const api = new APIClient(API_BASE_URL);

// ===== SENSORES =====
export const sensorsAPI = {
    // Obtener todos los sensores
    async getAll(filters = {}) {
        const params = new URLSearchParams(filters);
        return api.get(`/api/sensors?${params}`);
    },

    // Obtener sensor por ID
    async getById(sensorId) {
        return api.get(`/api/sensors/${sensorId}`);
    },

    // Crear nuevo sensor
    async create(sensorData) {
        return api.post('/api/sensors', sensorData);
    },

    // Actualizar sensor
    async update(sensorId, updates) {
        return api.put(`/api/sensors/${sensorId}`, updates);
    },

    // Eliminar sensor (desactivar)
    async delete(sensorId) {
        return api.delete(`/api/sensors/${sensorId}`);
    },

    // Obtener estadísticas del sensor
    async getStats(sensorId, period = '24h') {
        return api.get(`/api/sensors/${sensorId}/stats?period=${period}`);
    },

    // Activar/Desactivar sensor
    async toggleStatus(sensorId) {
        return api.put(`/api/sensors/${sensorId}/toggle-status`, {});
    },

    // Obtener lecturas recientes del sensor
    async getReadings(sensorId, limit = 10) {
        return api.get(`/api/sensors/${sensorId}/readings?limit=${limit}`);
    },
};

// ===== LECTURAS =====
export const readingsAPI = {
    // Obtener lecturas recientes
    async getRecent(limit = 20) {
        return api.get(`/api/readings?limit=${limit}`);
    },

    // Obtener lecturas por sensor
    async getBySensor(sensorId, filters = {}) {
        const params = new URLSearchParams({ sensor_id: sensorId, ...filters });
        return api.get(`/api/readings?${params}`);
    },

    // Crear nueva lectura
    async create(readingData) {
        return api.post('/api/readings', readingData);
    },

    // Obtener lectura por ID
    async getById(readingId) {
        return api.get(`/api/readings/${readingId}`);
    },

    // Obtener estadísticas de período
    async getStats(filters = {}) {
        const params = new URLSearchParams(filters);
        return api.get(`/api/readings/stats?${params}`);
    },
};

// ===== ALERTAS =====
export const alertsAPI = {
    // Obtener alertas activas
    async getActive() {
        return api.get('/api/alerts?status=active');
    },

    // Obtener todas las alertas
    async getAll(filters = {}) {
        const params = new URLSearchParams(filters);
        return api.get(`/api/alerts?${params}`);
    },

    // Obtener alertas por sensor
    async getBySensor(sensorId) {
        return api.get(`/api/alerts?sensor_id=${sensorId}`);
    },

    // Marcar alerta como resuelta
    async resolve(alertId) {
        return api.put(`/api/alerts/${alertId}/resolve`, {});
    },

    // Marcar alerta como reconocida
    async acknowledge(alertId) {
        return api.put(`/api/alerts/${alertId}/acknowledge`, {});
    },
};

// ===== HEALTH CHECK =====
export const healthAPI = {
    async check() {
        return api.get('/health');
    },
};

// ===== WEBSOCKET =====
export class SensorWebSocket {
    constructor(url = 'http://localhost:3002') {
        this.url = url;
        this.socket = null;
        this.listeners = {
            reading: [],
            alert: [],
            sensor: [],
            connect: [],
            disconnect: [],
        };
    }

    connect() {
        if (this.socket?.connected) {
            console.log('WebSocket ya está conectado');
            return;
        }

        // Usar socket.io-client (debe estar incluido en el HTML)
        if (typeof io === 'undefined') {
            console.error('socket.io-client no está cargado. Incluye el script en index.html');
            return;
        }

        this.socket = io(this.url);

        this.socket.on('connect', () => {
            console.log('✅ WebSocket conectado');
            this.listeners.connect.forEach(cb => cb());
        });

        this.socket.on('disconnect', () => {
            console.log('❌ WebSocket desconectado');
            this.listeners.disconnect.forEach(cb => cb());
        });

        this.socket.on('new_reading', (reading) => {
            console.log('📊 Nueva lectura:', reading);
            this.listeners.reading.forEach(cb => cb(reading));
        });

        this.socket.on('new_alert', (alert) => {
            console.log('🚨 Nueva alerta:', alert);
            this.listeners.alert.forEach(cb => cb(alert));
        });

        this.socket.on('sensor_created', (sensor) => {
            console.log('➕ Sensor creado:', sensor);
            this.listeners.sensor.forEach(cb => cb({ type: 'created', sensor }));
        });

        this.socket.on('sensor_updated', (sensor) => {
            console.log('🔄 Sensor actualizado:', sensor);
            this.listeners.sensor.forEach(cb => cb({ type: 'updated', sensor }));
        });
    }

    disconnect() {
        if (this.socket) {
            this.socket.disconnect();
            this.socket = null;
        }
    }

    // Suscribirse a eventos de un sensor específico
    subscribeSensor(sensorId) {
        if (this.socket) {
            this.socket.emit('subscribe_sensor', sensorId);
            console.log(`📡 Suscrito a sensor: ${sensorId}`);
        }
    }

    unsubscribeSensor(sensorId) {
        if (this.socket) {
            this.socket.emit('unsubscribe_sensor', sensorId);
            console.log(`📡 Desuscrito de sensor: ${sensorId}`);
        }
    }

    // Registrar listeners
    on(event, callback) {
        if (this.listeners[event]) {
            this.listeners[event].push(callback);
        }
    }

    off(event, callback) {
        if (this.listeners[event]) {
            this.listeners[event] = this.listeners[event].filter(cb => cb !== callback);
        }
    }
}

// Exportar instancia única de WebSocket
export const ws = new SensorWebSocket();

// Exportar todo como objeto por defecto
export default {
    sensors: sensorsAPI,
    readings: readingsAPI,
    alerts: alertsAPI,
    health: healthAPI,
    ws,
};
