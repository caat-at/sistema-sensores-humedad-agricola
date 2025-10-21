// main.js - Frontend integrado con backend + blockchain
import api, { ws } from './api.js';
import dashboard from './dashboard.js';

// Configuración
const CONTRACT_ADDRESS = "addr_test1wqlqg52urfvmhfnaz87xve2wwjp6c99geqwtres5weqra8q2vsuee";
const BLOCKFROST_API_KEY = "previewOm862VCGwCOrgyt0QwxsVq8aRdoVQUUT";
const NETWORK = "preview";

// Estado global
let walletAPI = null;
let walletName = '';
let backendConnected = false;

// Elementos del DOM
const connectWalletBtn = document.getElementById('connectWalletBtn');
const walletStatus = document.getElementById('walletStatus');
const walletInfo = document.getElementById('walletInfo');
const contractSection = document.getElementById('contractSection');
const registerSection = document.getElementById('registerSection');
const refreshBtn = document.getElementById('refreshBtn');
const contractStatus = document.getElementById('contractStatus');
const sensorsList = document.getElementById('sensorsList');
const registerForm = document.getElementById('registerForm');
const registerStatus = document.getElementById('registerStatus');

// Inicialización
document.addEventListener('DOMContentLoaded', async () => {
    console.log('🚀 Iniciando aplicación...');

    // Verificar backend
    await checkBackend();

    // Verificar wallets
    checkWalletAvailability();

    // Conectar WebSocket
    setupWebSocket();
});

// Verificar si hay wallets disponibles
function checkWalletAvailability() {
    console.log('🔍 Buscando wallets instaladas...');

    // Verificar wallets CIP-30 disponibles
    const availableWallets = [];

    if (window.cardano) {
        // Nami
        if (window.cardano.nami) availableWallets.push('Nami');
        // Eternl
        if (window.cardano.eternl) availableWallets.push('Eternl');
        // Lace
        if (window.cardano.lace) availableWallets.push('Lace');
        // Flint
        if (window.cardano.flint) availableWallets.push('Flint');
        // Typhon
        if (window.cardano.typhon) availableWallets.push('Typhon');
    }

    console.log('💼 Wallets encontradas:', availableWallets);

    if (availableWallets.length === 0) {
        walletStatus.className = 'status warning';
        walletStatus.innerHTML = `
            ⚠️ No se detectaron wallets instaladas.<br>
            <small>
                Instala una wallet para continuar:<br>
                • <a href="https://namiwallet.io/" target="_blank">Nami</a> (Recomendada)<br>
                • <a href="https://eternl.io/" target="_blank">Eternl</a> (Avanzada)<br>
                • <a href="https://www.lace.io/" target="_blank">Lace</a> (Oficial IOG)
            </small>
        `;
        connectWalletBtn.disabled = true;
        return;
    }

    walletStatus.className = 'status success';
    walletStatus.innerHTML = `
        ✅ Wallets disponibles: <strong>${availableWallets.join(', ')}</strong><br>
        <small>Haz clic en "Conectar Wallet" para continuar.</small>
    `;
}

// Conectar wallet
connectWalletBtn.addEventListener('click', async () => {
    try {
        connectWalletBtn.disabled = true;
        connectWalletBtn.textContent = 'Conectando...';
        walletStatus.className = 'status info';
        walletStatus.textContent = '⏳ Conectando con wallet...';

        // Intentar conectar con cada wallet disponible
        let connected = false;

        // Intentar Nami primero
        if (window.cardano?.nami) {
            try {
                console.log('🔄 Intentando conectar con Nami...');
                walletAPI = await window.cardano.nami.enable();
                walletName = 'Nami';
                connected = true;
            } catch (e) {
                console.log('⚠️ Nami rechazó la conexión o canceló');
            }
        }

        // Si no conectó con Nami, intentar Eternl
        if (!connected && window.cardano?.eternl) {
            try {
                console.log('🔄 Intentando conectar con Eternl...');
                walletAPI = await window.cardano.eternl.enable();
                walletName = 'Eternl';
                connected = true;
            } catch (e) {
                console.log('⚠️ Eternl rechazó la conexión o canceló');
            }
        }

        // Si no conectó, intentar Lace
        if (!connected && window.cardano?.lace) {
            try {
                console.log('🔄 Intentando conectar con Lace...');
                walletAPI = await window.cardano.lace.enable();
                walletName = 'Lace';
                connected = true;
            } catch (e) {
                console.log('⚠️ Lace rechazó la conexión o canceló');
            }
        }

        if (!connected) {
            throw new Error('No se pudo conectar con ninguna wallet. Asegúrate de aprobar la conexión en el popup de la wallet.');
        }

        console.log(`✅ Conectado a ${walletName}`);

        // Obtener información de la wallet
        const networkId = await walletAPI.getNetworkId();
        const usedAddresses = await walletAPI.getUsedAddresses();
        const changeAddress = await walletAPI.getChangeAddress();
        const balance = await walletAPI.getBalance();

        // Decodificar dirección
        const addressHex = changeAddress || usedAddresses[0];

        // Convertir balance de CBOR hex a número
        let balanceAda = 0;
        try {
            // El balance viene en formato CBOR hex
            // Necesitamos decodificarlo correctamente
            const balanceBytes = hexToBytes(balance);
            const balanceValue = decodeCBORBalance(balanceBytes);
            balanceAda = balanceValue / 1_000_000;
            console.log('💰 Balance parseado:', balanceValue, 'lovelace =', balanceAda.toFixed(2), 'ADA');
        } catch(e) {
            console.log('⚠️ No se pudo parsear balance CBOR:', e);
            console.log('Balance hex:', balance);
            balanceAda = 0; // Mostrar 0 si falla
        }

        // Mostrar información
        walletStatus.className = 'status success';
        walletStatus.innerHTML = `✅ Conectado a <strong>${walletName}</strong>`;

        walletInfo.className = 'wallet-info';
        walletInfo.innerHTML = `
            <div><strong>Wallet:</strong> ${walletName}</div>
            <div><strong>Red:</strong> ${networkId === 0 ? 'Testnet (Preview)' : networkId === 1 ? 'Mainnet' : 'Unknown'}</div>
            <div><strong>Balance:</strong> ${balanceAda.toFixed(2)} ADA</div>
            <div style="font-size: 12px; color: #666; margin-top: 5px;">
                <strong>Dirección:</strong> ${addressHex.slice(0, 40)}...
            </div>
        `;

        connectWalletBtn.textContent = `Conectado a ${walletName} ✓`;

        // Verificar que esté en testnet
        if (networkId !== 0) {
            walletStatus.className = 'status warning';
            walletStatus.innerHTML = `
                ⚠️ Wallet conectada pero en red incorrecta<br>
                <small>Por favor cambia tu wallet a <strong>Preview Testnet</strong></small>
            `;
            return;
        }

        // Mostrar secciones
        document.getElementById('dashboardSection').classList.remove('hidden');
        document.getElementById('sensorsSection').classList.remove('hidden');
        contractSection.classList.remove('hidden');
        registerSection.classList.remove('hidden');

        // Inicializar dashboard
        await dashboard.init();

        // Cargar estado del contrato
        await loadContractState();

    } catch (error) {
        console.error('❌ Error conectando wallet:', error);
        walletStatus.className = 'status error';
        walletStatus.innerHTML = `
            ❌ Error: ${error.message}<br>
            <small>Asegúrate de aprobar la conexión en el popup de la wallet</small>
        `;
        connectWalletBtn.disabled = false;
        connectWalletBtn.textContent = 'Conectar Wallet';
    }
});

// Cargar estado del contrato
async function loadContractState() {
    try {
        contractStatus.innerHTML = '<div class="loading">⏳ Cargando estado del contrato...</div>';

        // Obtener UTxOs del contrato usando Blockfrost
        const response = await fetch(
            `https://cardano-${NETWORK}.blockfrost.io/api/v0/addresses/${CONTRACT_ADDRESS}/utxos`,
            {
                headers: {
                    'project_id': BLOCKFROST_API_KEY
                }
            }
        );

        if (!response.ok) {
            throw new Error(`Error Blockfrost: ${response.status}`);
        }

        const utxos = await response.json();

        if (utxos.length === 0) {
            contractStatus.innerHTML = `
                <div class="status warning">
                    ⚠️ No hay UTxOs en el contrato
                </div>
            `;
            return;
        }

        // Calcular total ADA
        const totalAda = utxos.reduce((sum, utxo) => {
            const lovelace = utxo.amount.find(a => a.unit === 'lovelace');
            return sum + parseInt(lovelace?.quantity || 0);
        }, 0);

        contractStatus.innerHTML = `
            <div class="status success" style="margin-top: 15px;">
                ✅ Contrato activo en blockchain<br>
                <small>
                    📍 Dirección: ${CONTRACT_ADDRESS.slice(0, 40)}...<br>
                    💰 ${utxos.length} UTxO(s) - Total: ${(totalAda / 1_000_000).toFixed(2)} ADA
                </small>
            </div>
        `;

        // Mostrar información de sensores
        displaySensors(utxos.length);

    } catch (error) {
        console.error('❌ Error cargando estado:', error);
        contractStatus.innerHTML = `
            <div class="status error">
                ❌ Error cargando estado: ${error.message}
            </div>
        `;
    }
}

// Mostrar sensores
function displaySensors(utxoCount) {
    sensorsList.innerHTML = `
        <div class="sensor-card">
            <h3>📊 Estado General</h3>
            <div class="sensor-info">
                <span>Sensores Registrados:</span>
                <strong>0</strong>
            </div>
            <div class="sensor-info">
                <span>UTxOs en Contrato:</span>
                <strong>${utxoCount}</strong>
            </div>
            <div class="sensor-info">
                <span>Estado:</span>
                <strong style="color: #28a745;">✅ Activo</strong>
            </div>
        </div>
        <div class="sensor-card">
            <h3>ℹ️ Información</h3>
            <p style="color: #666; font-size: 14px; line-height: 1.6;">
                El datum del contrato contiene la lista de sensores registrados.
                La funcionalidad de lectura del datum será implementada próximamente.
            </p>
        </div>
    `;
}

// Botón refresh
refreshBtn.addEventListener('click', loadContractState);

// Registrar sensor (placeholder)
registerForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    if (!walletAPI) {
        registerStatus.innerHTML = '<div class="status error">❌ Conecta tu wallet primero</div>';
        return;
    }

    const registerBtn = document.getElementById('registerBtn');
    registerBtn.disabled = true;
    registerBtn.textContent = 'Preparando...';

    const sensorData = {
        sensorId: document.getElementById('sensorId').value,
        zoneName: document.getElementById('zoneName').value,
        latitude: parseInt(document.getElementById('latitude').value),
        longitude: parseInt(document.getElementById('longitude').value),
        minHumidity: parseInt(document.getElementById('minHumidity').value),
        maxHumidity: parseInt(document.getElementById('maxHumidity').value),
        readingInterval: parseInt(document.getElementById('readingInterval').value)
    };

    registerStatus.innerHTML = `
        <div class="status info">
            ✅ Datos del sensor preparados<br><br>
            <strong>Configuración:</strong><br>
            • Sensor: ${sensorData.sensorId}<br>
            • Zona: ${sensorData.zoneName}<br>
            • Umbrales: ${sensorData.minHumidity}% - ${sensorData.maxHumidity}%<br>
            • Intervalo: ${sensorData.readingInterval} min<br><br>
            <small style="color: #856404;">
                ⏳ La construcción de transacciones Plutus V3 está en desarrollo.<br>
                El formulario funciona correctamente y los datos están listos.
            </small>
        </div>
    `;

    registerBtn.disabled = false;
    registerBtn.textContent = 'Registrar Sensor';
});

// Utilidades para decodificación CBOR
function hexToBytes(hex) {
    const bytes = [];
    for (let i = 0; i < hex.length; i += 2) {
        bytes.push(parseInt(hex.substr(i, 2), 16));
    }
    return new Uint8Array(bytes);
}

function decodeCBORBalance(bytes) {
    // Decodificación simple de CBOR para obtener el valor en lovelace
    // El formato típico es: unsigned integer (major type 0)
    let offset = 0;

    const firstByte = bytes[offset++];
    const majorType = (firstByte & 0b11100000) >> 5;
    const additionalInfo = firstByte & 0b00011111;

    if (majorType === 0) { // unsigned integer
        if (additionalInfo < 24) {
            return additionalInfo;
        } else if (additionalInfo === 24) {
            return bytes[offset];
        } else if (additionalInfo === 25) {
            return (bytes[offset] << 8) | bytes[offset + 1];
        } else if (additionalInfo === 26) {
            return (bytes[offset] << 24) | (bytes[offset + 1] << 16) |
                   (bytes[offset + 2] << 8) | bytes[offset + 3];
        } else if (additionalInfo === 27) {
            // 64-bit integer - usar BigInt
            let value = 0n;
            for (let i = 0; i < 8; i++) {
                value = (value << 8n) | BigInt(bytes[offset + i]);
            }
            return Number(value);
        }
    }

    throw new Error('Formato CBOR no soportado para balance');
}

// ===== BACKEND & WEBSOCKET =====

// Verificar conexión con backend
async function checkBackend() {
    try {
        const health = await api.health.check();
        console.log('✅ Backend conectado:', health);
        backendConnected = true;
    } catch (error) {
        console.error('❌ Backend no disponible:', error);
        backendConnected = false;

        walletStatus.className = 'status warning';
        walletStatus.innerHTML = `
            ⚠️ Backend no disponible<br>
            <small>Asegúrate de que el servidor backend esté ejecutándose en http://localhost:3002</small>
        `;
    }
}

// Configurar WebSocket
function setupWebSocket() {
    if (!backendConnected) {
        console.log('⚠️ No se puede conectar WebSocket: backend no disponible');
        return;
    }

    ws.connect();

    // Evento: Conexión establecida
    ws.on('connect', () => {
        console.log('🔌 WebSocket conectado');
        const indicator = document.getElementById('wsIndicator');
        if (indicator) {
            indicator.style.background = '#28a745';
        }
    });

    // Evento: Desconexión
    ws.on('disconnect', () => {
        console.log('🔌 WebSocket desconectado');
        const indicator = document.getElementById('wsIndicator');
        if (indicator) {
            indicator.style.background = '#dc3545';
        }
    });

    // Evento: Nueva lectura
    ws.on('reading', (reading) => {
        console.log('📊 Nueva lectura recibida:', reading);
        // Refrescar lecturas y estadísticas
        if (typeof dashboard.loadRecentReadings === 'function') {
            dashboard.loadRecentReadings();
        }
    });

    // Evento: Nueva alerta
    ws.on('alert', (alert) => {
        console.log('🚨 Nueva alerta recibida:', alert);
        // Refrescar alertas
        if (typeof dashboard.loadActiveAlerts === 'function') {
            dashboard.loadActiveAlerts();
        }

        // Mostrar notificación visual
        showNotification(`⚨ ${alert.alert_type}: ${alert.message}`, 'warning');
    });

    // Evento: Sensor actualizado
    ws.on('sensor', (data) => {
        console.log('🔄 Evento de sensor:', data);
        // Refrescar lista de sensores
        if (typeof dashboard.loadSensors === 'function') {
            dashboard.loadSensors();
        }
    });
}

// Mostrar notificación
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `status ${type}`;
    notification.style.position = 'fixed';
    notification.style.top = '20px';
    notification.style.right = '20px';
    notification.style.zIndex = '9999';
    notification.style.maxWidth = '400px';
    notification.style.boxShadow = '0 5px 15px rgba(0,0,0,0.3)';
    notification.innerHTML = message;

    document.body.appendChild(notification);

    setTimeout(() => {
        notification.remove();
    }, 5000);
}

// Debug info
console.log('✅ Aplicación cargada');
console.log('🔍 window.cardano:', window.cardano);
console.log('📍 Contrato:', CONTRACT_ADDRESS);
