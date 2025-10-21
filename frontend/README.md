# 🌐 Frontend - Sistema de Sensores de Humedad Agrícola

Frontend web para interactuar con el smart contract de sensores de humedad usando wallets de navegador.

## 🚀 Inicio Rápido

### 1. Instalar dependencias

```bash
npm install
```

### 2. Iniciar servidor de desarrollo

```bash
npm run dev
```

El navegador se abrirá automáticamente en `http://localhost:3000`

## 📋 Requisitos Previos

### Instalar una Wallet de Cardano

Necesitas una wallet de navegador compatible. Elige una:

- **[Nami](https://namiwallet.io/)** - Recomendada para principiantes
- **[Eternl](https://eternl.io/)** - Más features avanzadas
- **[Lace](https://www.lace.io/)** - Wallet oficial de IOG

### Configurar la Wallet

1. Instala la extensión del navegador
2. Crea o importa una wallet
3. **IMPORTANTE**: Cambia a **Preview Testnet** en la configuración
4. Obtén tADA gratis en: https://docs.cardano.org/cardano-testnets/tools/faucet/

## 🎮 Cómo Usar

### 1. Conectar Wallet

1. Abre la aplicación en el navegador
2. Haz clic en "Conectar Wallet"
3. Selecciona tu wallet (Nami, Eternl, etc.)
4. Aprueba la conexión

### 2. Ver Estado del Contrato

Una vez conectado, verás:
- Dirección del contrato
- UTxOs activos
- Balance total
- Estado general

Haz clic en "Actualizar Estado" para refrescar la información.

### 3. Registrar un Sensor

Completa el formulario con:

- **ID del Sensor**: Identificador único (ej: SENSOR-001)
- **Nombre de la Zona**: Ubicación (ej: Lote-Norte-A1)
- **Latitud/Longitud**: Coordenadas × 1,000,000
  - Ejemplo: 4.7110 → 4711000
  - Ejemplo: -74.0721 → -74072100
- **Humedad Mínima**: % mínimo antes de alerta (ej: 30)
- **Humedad Máxima**: % máximo antes de alerta (ej: 70)
- **Intervalo de Lectura**: Minutos entre lecturas (ej: 15)

## ⚠️ Limitación Actual

El frontend está **completamente funcional** excepto por la construcción de transacciones Plutus V3.

**Lo que funciona:**
- ✅ Conexión con wallet
- ✅ Consulta de UTxOs del contrato
- ✅ Interfaz de usuario completa
- ✅ Formularios de registro

**Lo que necesita completarse:**
- ⏳ Serialización CBOR para Plutus V3
- ⏳ Construcción de transacción con redeemer

**Razón**: Mesh SDK está mejorando soporte para Plutus V3. La estructura está lista, solo necesita la serialización correcta del redeemer.

## 🔧 Scripts Disponibles

```bash
# Desarrollo (con hot reload)
npm run dev

# Build para producción
npm run build

# Preview del build
npm run preview
```

## 📁 Estructura

```
frontend/
├── index.html          # HTML principal
├── src/
│   └── main.js         # Lógica de la aplicación
├── public/             # Archivos estáticos
├── package.json        # Dependencias
├── vite.config.js      # Configuración de Vite
└── README.md           # Este archivo
```

## 🛠️ Tecnologías

- **Vite** - Build tool y dev server
- **Mesh SDK** - Interacción con Cardano
- **Vanilla JavaScript** - Sin frameworks (ligero y rápido)
- **CSS Moderno** - Gradientes y animaciones

## 🔍 Debugging

Abre la consola del navegador (F12) para ver:
- Logs de conexión
- Estado de la aplicación
- Errores detallados

El estado global está disponible en:
```javascript
window.appState
```

## 🚀 Próximos Pasos

Para completar la funcionalidad de registro:

1. Implementar serialización correcta del redeemer Plutus V3
2. Construir transacción con script witness
3. Actualizar datum con nuevo sensor
4. Firmar y enviar transacción

**Alternativas mientras tanto:**
- Usar Lucid cuando salga v0.11.x
- Implementar con cardano-cli
- Esperar mejoras en Mesh SDK

## 📚 Referencias

- [Mesh SDK Docs](https://meshjs.dev/)
- [Cardano Developer Portal](https://developers.cardano.org/)
- [Blockfrost API](https://docs.blockfrost.io/)

## 💬 Notas

Este frontend demuestra la arquitectura completa de una dApp en Cardano:
- Conexión de wallet ✅
- Consulta de blockchain ✅
- Interfaz de usuario ✅
- Construcción de transacciones ⏳ (en desarrollo por limitación de librería)

El código está listo para funcionar completamente cuando las librerías tengan soporte completo para Plutus V3.

---

**Desarrollado con**: Vite + Mesh SDK
**Red**: Cardano Preview Testnet
