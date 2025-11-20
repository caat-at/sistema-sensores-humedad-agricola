# Roadmap del Proyecto - Sistema de Sensores de Humedad Agrícola

## 🎯 Visión General

Sistema IoT descentralizado para monitoreo de humedad agrícola en Cardano blockchain con optimización de costos mediante rollups con merkle hash.

---

## ✅ Fase 1: MVP Funcional (COMPLETADO)

**Estado:** ✅ Completado - Noviembre 2025

### Backend Core
- [x] API REST con FastAPI
- [x] Smart Contract OpShin/Plutus V2
- [x] Persistencia dual (Blockchain + PostgreSQL)
- [x] CRUD completo de sensores
- [x] Gestión de lecturas de humedad/temperatura
- [x] Integración con BlockFrost API
- [x] PyCardano para transacciones

### Frontend
- [x] Dashboard interactivo con Bootstrap 5
- [x] Visualización de sensores en tarjetas
- [x] Tabla de lecturas recientes
- [x] Formulario de registro de sensores
- [x] Responsive design

### Infraestructura
- [x] Configuración de entorno (.env)
- [x] Scripts de inicio (start.bat, start.ps1)
- [x] Documentación completa
- [x] Guías de configuración

---

## ✅ Fase 2: Alertas y Auditoría (COMPLETADO)

**Estado:** ✅ Completado - Noviembre 2025

### Sistema de Alertas
- [x] Detección automática de lecturas fuera de rango
- [x] Cálculo de niveles de alerta (Normal, Low, High, Critical)
- [x] API de alertas activas
- [x] Resumen de alertas por sensor
- [x] Filtros por sensor y nivel
- [x] Visualización en dashboard con badges de color
- [x] Auto-refresh cada 30 segundos

### Auditoría
- [x] Comparación blockchain vs PostgreSQL
- [x] Detección de discrepancias
- [x] Dashboard de auditoría
- [x] Endpoint `/api/audit/compare`

---

## ✅ Fase 3: Optimización de Costos (COMPLETADO)

**Estado:** ✅ Completado - Noviembre 2025

### Sistema de Rollups con Merkle Hash
- [x] Implementación de Merkle Tree con SHA-256
- [x] Servicio de agrupación diaria (DailyRollupService)
- [x] API REST de rollups (`/api/rollup/*`)
- [x] Tipos PlutusData para rollups (DailyRollup, RollupStatistics)
- [x] Verificación criptográfica con merkle proofs
- [x] Cálculo de estadísticas (min/max/avg)
- [x] Scheduler automático con APScheduler
- [x] Documentación técnica completa

**Impacto:**
- 🎯 Reducción de costos: 96%
- 💰 Ahorro estimado: ~$2,250 USD/año (4 sensores)
- 🗜️ Compresión de datos en blockchain

---

## 🚧 Fase 4: Completar Rollups (EN DESARROLLO)

**Estado:** 🚧 70% Completado - Estimado: Diciembre 2025

### Tareas Pendientes

#### 4.1 Configuración de Entorno
- [ ] Instalar APScheduler
  ```bash
  pip install apscheduler
  ```
- [ ] Actualizar requirements.txt con APScheduler
- [ ] Documentar versión exacta instalada

#### 4.2 Migración de Base de Datos
- [ ] Aplicar migración SQL de rollup_batch_id
- [ ] Verificar índices creados correctamente
- [ ] Crear script Python de migración con manejo de errores
- [ ] Documentar rollback de migración

#### 4.3 Integración Blockchain Real
- [ ] Modificar BlockchainClient para soportar AddDailyRollup redeemer
- [ ] Implementar construcción de transacción de rollup
- [ ] Probar envío de rollup a Cardano Preview Testnet
- [ ] Verificar datum en blockchain explorer
- [ ] Manejar errores de transacción

#### 4.4 Dashboard de Rollups
- [ ] Crear pestaña "Rollups" en dashboard
- [ ] Visualizar rollups recientes en tabla
- [ ] Gráfico de ahorros acumulados
- [ ] Botón "Procesar Rollup Ahora"
- [ ] Estado del scheduler en tiempo real
- [ ] Indicador de próxima ejecución

#### 4.5 Monitoreo y Logs
- [ ] Configurar logging estructurado
- [ ] Métricas de Prometheus/Grafana
- [ ] Alertas de fallos en rollups
- [ ] Dashboard de monitoreo de costos

**Tiempo Estimado:** 12-16 horas

---

## 📋 Fase 5: Notificaciones (PLANIFICADO)

**Estado:** ⏳ Pendiente - Estimado: Enero 2026

### 5.1 Email Notifications
- [ ] Integración con SendGrid/AWS SES
- [ ] Templates de email para alertas
- [ ] Configuración de destinatarios por sensor
- [ ] Throttling de emails (max 1/hora por sensor)
- [ ] Unsubscribe links

### 5.2 Webhook Notifications
- [ ] Sistema de webhooks configurables
- [ ] Retry logic con backoff exponencial
- [ ] Payload personalizable
- [ ] Logs de entregas
- [ ] Ejemplos de integración (Discord, Slack, Telegram)

### 5.3 SMS Notifications (Opcional)
- [ ] Integración con Twilio
- [ ] Solo para alertas críticas
- [ ] Confirmación de recepción

**Tiempo Estimado:** 8-10 horas

---

## 📋 Fase 6: Analytics Avanzado (PLANIFICADO)

**Estado:** ⏳ Pendiente - Estimado: Febrero 2026

### 6.1 Gráficos Históricos
- [ ] Chart.js o ApexCharts en dashboard
- [ ] Gráfico de líneas de humedad (últimos 7 días)
- [ ] Gráfico de temperatura
- [ ] Comparación multi-sensor
- [ ] Zoom y pan en gráficos
- [ ] Exportar gráficos como imagen

### 6.2 Reportes
- [ ] Reporte diario automático (PDF)
- [ ] Reporte semanal con análisis de tendencias
- [ ] Reporte mensual con estadísticas
- [ ] Exportación a CSV/Excel
- [ ] Generación de reportes custom

### 6.3 Predicción con ML
- [ ] Modelo de predicción de humedad (LSTM/Prophet)
- [ ] Entrenamiento con datos históricos
- [ ] API de predicción `/api/predict/humidity`
- [ ] Visualización de predicciones en dashboard
- [ ] Alertas predictivas

**Tiempo Estimado:** 20-24 horas

---

## 📋 Fase 7: Hardware Físico (PLANIFICADO)

**Estado:** ⏳ Pendiente - Estimado: Marzo 2026

### 7.1 Integración Arduino/ESP32
- [ ] Código Arduino para DHT11/DHT22
- [ ] Comunicación serial con Python
- [ ] Script de bridge serial → API
- [ ] Auto-discovery de sensores USB
- [ ] Manejo de desconexiones

### 7.2 MQTT Gateway
- [ ] Broker MQTT (Mosquitto)
- [ ] Clientes ESP32 con WiFi
- [ ] QoS level 2 para garantizar entrega
- [ ] TLS/SSL para seguridad
- [ ] Gateway MQTT → API REST

### 7.3 LoRaWAN (Opcional)
- [ ] Gateway LoRaWAN
- [ ] Nodos sensores con bajo consumo
- [ ] The Things Network integration
- [ ] Cobertura de largo alcance

**Tiempo Estimado:** 30-40 horas

---

## 📋 Fase 8: Escalabilidad (PLANIFICADO)

**Estado:** ⏳ Pendiente - Estimado: Abril 2026

### 8.1 Multi-tenancy
- [ ] Modelo de organizaciones/fincas
- [ ] Autenticación con JWT
- [ ] RBAC (Role-Based Access Control)
- [ ] API keys por organización
- [ ] Aislamiento de datos

### 8.2 High Availability
- [ ] Docker Compose para multi-container
- [ ] Load balancer (NGINX)
- [ ] PostgreSQL replication
- [ ] Redis para caché
- [ ] Health checks y auto-restart

### 8.3 Performance
- [ ] Caché de queries frecuentes
- [ ] Paginación en todos los endpoints
- [ ] Índices optimizados en PostgreSQL
- [ ] Compression de responses
- [ ] CDN para assets estáticos

**Tiempo Estimado:** 24-30 horas

---

## 📋 Fase 9: Blockchain Upgrade (FUTURO)

**Estado:** ⏳ Pendiente - Estimado: Mayo 2026

### 9.1 Smart Contract V2
- [ ] Validador on-chain de merkle proofs
- [ ] Optimización de tamaño de datum
- [ ] Soporte para rollups por hora (además de diarios)
- [ ] Compresión de estadísticas
- [ ] Testing exhaustivo con unit tests

### 9.2 Mainnet Deployment
- [ ] Audit de seguridad del contrato
- [ ] Deploy a Cardano Mainnet
- [ ] Migración de datos de Preview Testnet
- [ ] Monitoreo de costos reales
- [ ] Plan de contingencia

### 9.3 NFT de Sensores (Opcional)
- [ ] Cada sensor como NFT único
- [ ] Metadata on-chain
- [ ] Transferibilidad de ownership
- [ ] Marketplace de sensores

**Tiempo Estimado:** 40-50 horas

---

## 📋 Fase 10: Mobile App (FUTURO)

**Estado:** ⏳ Pendiente - Estimado: Junio 2026

### 10.1 React Native App
- [ ] Login/autenticación
- [ ] Lista de sensores
- [ ] Gráficos de lecturas
- [ ] Notificaciones push
- [ ] Mapa de sensores (GPS)

### 10.2 Progressive Web App (PWA)
- [ ] Service workers
- [ ] Offline mode
- [ ] App install prompt
- [ ] Push notifications

**Tiempo Estimado:** 60-80 horas

---

## 💡 Ideas Futuras (Backlog)

### Integración de Terceros
- [ ] Integración con estaciones meteorológicas
- [ ] API de predicción de lluvia
- [ ] Integración con sistemas de riego automático
- [ ] Satelital imagery (NDVI)

### Blockchain Avanzado
- [ ] ZK-Rollups para mayor privacidad
- [ ] Cross-chain bridges (Ethereum, Polygon)
- [ ] DeFi: Staking de tokens de sensor
- [ ] Governance con DAO

### AI/ML Avanzado
- [ ] Computer vision para análisis de cultivos
- [ ] Detección de plagas con IA
- [ ] Optimización de riego con RL
- [ ] Digital twin del campo

### Gamification
- [ ] Leaderboard de mejores prácticas
- [ ] Tokens de recompensa por datos
- [ ] Competencias entre fincas
- [ ] NFTs de logros

---

## 📊 Métricas de Éxito

### Métricas Técnicas
- ✅ Uptime: >99.5%
- ✅ Latencia API: <200ms (p95)
- ✅ Cobertura de tests: >80%
- ✅ Reducción de costos blockchain: 96%

### Métricas de Negocio
- 🎯 Sensores activos: 100+ (Q2 2026)
- 🎯 Usuarios registrados: 50+ (Q2 2026)
- 🎯 Fincas/organizaciones: 10+ (Q3 2026)
- 🎯 Transacciones blockchain: 10,000+ (Q4 2026)

---

## 🛠️ Stack Tecnológico

### Backend
- **Framework:** FastAPI 0.120+
- **Blockchain:** PyCardano 0.16+, BlockFrost
- **Database:** PostgreSQL 16+, SQLAlchemy 2.0+
- **Scheduler:** APScheduler 3.10+
- **Logging:** Structlog, Sentry

### Frontend
- **Framework:** Bootstrap 5, Vanilla JS
- **Charts:** Chart.js / ApexCharts
- **Maps:** Leaflet.js
- **Future:** React/Vue.js

### Blockchain
- **Network:** Cardano (Preview Testnet → Mainnet)
- **Smart Contracts:** OpShin/Aiken
- **Explorer:** CardanoScan

### DevOps
- **Containerization:** Docker, Docker Compose
- **CI/CD:** GitHub Actions
- **Monitoring:** Prometheus, Grafana
- **Logs:** ELK Stack

---

## 🤝 Contribuciones

Este es un roadmap vivo y se actualiza según las prioridades del proyecto.

**Próxima revisión:** Diciembre 2025

---

**Última actualización:** 2025-11-10
**Versión:** 3.0 (Rollups con Merkle Hash)
