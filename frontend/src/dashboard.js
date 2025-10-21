// dashboard.js - Funcionalidad del dashboard de monitoreo
import api from './api.js';

let humidityChart = null;

// Inicializar dashboard
export async function initDashboard() {
    console.log('🎨 Inicializando dashboard...');

    try {
        // Cargar datos iniciales
        await Promise.all([
            loadStats(),
            loadSensors(),
            loadRecentReadings(),
            loadActiveAlerts(),
        ]);

        // Crear gráfico de humedad
        createHumidityChart();

        // Configurar actualización automática cada 30 segundos
        setInterval(refreshDashboard, 30000);

        console.log('✅ Dashboard inicializado');
    } catch (error) {
        console.error('❌ Error inicializando dashboard:', error);
    }
}

// Refrescar dashboard
async function refreshDashboard() {
    console.log('🔄 Actualizando dashboard...');
    await Promise.all([
        loadStats(),
        loadRecentReadings(),
        loadActiveAlerts(),
    ]);
}

// Cargar estadísticas
async function loadStats() {
    try {
        const [sensorsRes, readingsRes, alertsRes] = await Promise.all([
            api.sensors.getAll({ status: 'active' }),
            api.readings.getRecent(100),
            api.alerts.getActive(),
        ]);

        // Contar sensores activos
        const activeSensors = sensorsRes.data.filter(s => s.status === 'active').length;
        document.getElementById('activeSensorsCount').textContent = activeSensors;

        // Contar lecturas de hoy
        const today = new Date().setHours(0, 0, 0, 0);
        const todayReadings = readingsRes.data.filter(r => {
            const readingDate = new Date(r.timestamp).setHours(0, 0, 0, 0);
            return readingDate === today;
        }).length;
        document.getElementById('todayReadingsCount').textContent = todayReadings;

        // Contar alertas activas
        const activeAlerts = alertsRes.data.filter(a => a.status === 'active').length;
        document.getElementById('activeAlertsCount').textContent = activeAlerts;

        // Actualizar gráfico
        if (humidityChart) {
            updateHumidityChart(readingsRes.data);
        }
    } catch (error) {
        console.error('Error cargando estadísticas:', error);
    }
}

// Cargar sensores
async function loadSensors() {
    try {
        const response = await api.sensors.getAll();
        const sensorsListEl = document.getElementById('sensorsList');

        if (response.data.length === 0) {
            sensorsListEl.innerHTML = '<p style="text-align: center; color: #666;">No hay sensores registrados</p>';
            return;
        }

        sensorsListEl.innerHTML = response.data.map(sensor => `
            <div class="sensor-card">
                <h3>${sensor.sensor_id}</h3>
                <div class="sensor-info">
                    <span>Zona:</span>
                    <strong>${sensor.zone_name}</strong>
                </div>
                <div class="sensor-info">
                    <span>Estado:</span>
                    <strong style="color: ${sensor.status === 'active' ? '#28a745' : '#dc3545'}">
                        ${sensor.status === 'active' ? '✅ Activo' : '⚠️ Inactivo'}
                    </strong>
                </div>
                <div class="sensor-info">
                    <span>Umbrales:</span>
                    <strong>${sensor.min_humidity_threshold}% - ${sensor.max_humidity_threshold}%</strong>
                </div>
                <div class="sensor-info">
                    <span>Intervalo:</span>
                    <strong>${sensor.reading_interval_minutes} min</strong>
                </div>
                <div class="sensor-info">
                    <span>Ubicación:</span>
                    <small>${sensor.latitude.toFixed(6)}, ${sensor.longitude.toFixed(6)}</small>
                </div>
            </div>
        `).join('');
    } catch (error) {
        console.error('Error cargando sensores:', error);
        document.getElementById('sensorsList').innerHTML =
            '<p style="text-align: center; color: #dc3545;">Error cargando sensores</p>';
    }
}

// Cargar lecturas recientes
async function loadRecentReadings() {
    try {
        const response = await api.readings.getRecent(20);
        const readingsEl = document.getElementById('recentReadings');

        if (response.data.length === 0) {
            readingsEl.innerHTML = '<p style="text-align: center; color: #666;">No hay lecturas disponibles</p>';
            return;
        }

        readingsEl.innerHTML = response.data.map(reading => {
            const alertClass = reading.alert_level || 'normal';
            const timestamp = new Date(reading.timestamp);
            const timeStr = timestamp.toLocaleTimeString('es-ES');

            return `
                <div class="reading-item ${alertClass}">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                        <strong>${reading.sensor_id}</strong>
                        <span class="alert-badge ${alertClass}">${alertClass.toUpperCase()}</span>
                    </div>
                    <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; font-size: 14px;">
                        <div>
                            <div style="color: #666;">Humedad</div>
                            <strong style="color: #667eea;">${reading.humidity_percentage}%</strong>
                        </div>
                        <div>
                            <div style="color: #666;">Temperatura</div>
                            <strong>${reading.temperature_celsius || '-'}°C</strong>
                        </div>
                        <div>
                            <div style="color: #666;">Batería</div>
                            <strong>${reading.battery_level || '-'}%</strong>
                        </div>
                    </div>
                    <div style="margin-top: 8px; font-size: 12px; color: #999;">${timeStr}</div>
                </div>
            `;
        }).join('');
    } catch (error) {
        console.error('Error cargando lecturas:', error);
        document.getElementById('recentReadings').innerHTML =
            '<p style="text-align: center; color: #dc3545;">Error cargando lecturas</p>';
    }
}

// Cargar alertas activas
async function loadActiveAlerts() {
    try {
        const response = await api.alerts.getActive();
        const alertsEl = document.getElementById('activeAlerts');

        if (response.data.length === 0) {
            alertsEl.innerHTML = '<p style="text-align: center; color: #28a745;">✅ No hay alertas activas</p>';
            return;
        }

        alertsEl.innerHTML = response.data.map(alert => {
            const timestamp = new Date(alert.created_at);
            const timeStr = timestamp.toLocaleString('es-ES');

            return `
                <div class="reading-item ${alert.severity || 'warning'}">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                        <strong>${alert.sensor_id}</strong>
                        <span class="alert-badge ${alert.severity}">${alert.alert_type.toUpperCase()}</span>
                    </div>
                    <p style="margin: 8px 0; font-size: 14px;">${alert.message}</p>
                    <div style="margin-top: 8px; font-size: 12px; color: #999;">${timeStr}</div>
                </div>
            `;
        }).join('');
    } catch (error) {
        console.error('Error cargando alertas:', error);
        document.getElementById('activeAlerts').innerHTML =
            '<p style="text-align: center; color: #dc3545;">Error cargando alertas</p>';
    }
}

// Crear gráfico de humedad
function createHumidityChart() {
    const ctx = document.getElementById('humidityChart');
    if (!ctx) return;

    humidityChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: []
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: 'Historial de Humedad por Sensor',
                    font: { size: 16 }
                },
                legend: {
                    display: true,
                    position: 'top',
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                    title: {
                        display: true,
                        text: 'Humedad (%)'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Tiempo'
                    }
                }
            }
        }
    });
}

// Actualizar gráfico de humedad
function updateHumidityChart(readings) {
    if (!humidityChart) return;

    // Agrupar por sensor
    const sensorData = {};
    readings.forEach(reading => {
        if (!sensorData[reading.sensor_id]) {
            sensorData[reading.sensor_id] = [];
        }
        sensorData[reading.sensor_id].push(reading);
    });

    // Crear datasets
    const colors = [
        { bg: 'rgba(102, 126, 234, 0.2)', border: 'rgba(102, 126, 234, 1)' },
        { bg: 'rgba(118, 75, 162, 0.2)', border: 'rgba(118, 75, 162, 1)' },
        { bg: 'rgba(40, 167, 69, 0.2)', border: 'rgba(40, 167, 69, 1)' },
    ];

    const datasets = Object.keys(sensorData).map((sensorId, idx) => {
        const data = sensorData[sensorId]
            .sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp))
            .slice(-20); // Últimas 20 lecturas

        return {
            label: sensorId,
            data: data.map(r => r.humidity_percentage),
            backgroundColor: colors[idx % colors.length].bg,
            borderColor: colors[idx % colors.length].border,
            borderWidth: 2,
            tension: 0.4,
        };
    });

    // Etiquetas de tiempo
    const allReadings = readings
        .sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp))
        .slice(-20);

    const labels = allReadings.map(r => {
        const time = new Date(r.timestamp);
        return time.toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' });
    });

    humidityChart.data.labels = labels;
    humidityChart.data.datasets = datasets;
    humidityChart.update();
}

// Exportar funciones
export default {
    init: initDashboard,
    refresh: refreshDashboard,
    loadSensors,
    loadRecentReadings,
    loadActiveAlerts,
};
