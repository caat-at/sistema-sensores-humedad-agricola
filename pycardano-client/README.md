# PyCardano Client - Sistema de Sensores de Humedad Agricola

Cliente Python para interactuar con el smart contract OpShin de sensores de humedad.

## Estado del Proyecto

**Version:** MVP Testnet
**Red:** Cardano Preview Testnet
**Ultimo Update:** 2025-10-14

### Completado

- [x] Configuracion de entorno
- [x] Conexion con Blockfrost API
- [x] Modulo de utilidades (cardano_utils.py)
- [x] Script de consulta (query.py)
- [ ] Script de inicializacion (init.py) - En desarrollo
- [ ] Script de registro de sensor (register_sensor.py)
- [ ] Script de lectura de humedad (add_reading.py)

## Requisitos

```bash
pip install pycardano
pip install python-dotenv
pip install blockfrost-python
```

Todas las dependencias ya estan instaladas si instalaste OpShin.

## Configuracion

El cliente lee la configuracion del archivo `.env` ubicado en `../mesh-client/.env`:

```env
BLOCKFROST_PROJECT_ID=previewXXXXXXXXXXXXXX
NETWORK=preview
ADMIN_SEED_PHRASE="word1 word2 ... word24"
CONTRACT_ADDRESS=addr_test1wz873...
```

## Uso

### Consultar Estado del Contrato

```bash
python query.py
```

Muestra:
- Total de UTxOs en el contrato
- ADA bloqueados
- UTxOs con/sin datums
- Resumen del estado

**Salida esperada:**
```
======================================================================
 CONSULTA DE CONTRATO - Sistema de Sensores de Humedad
======================================================================

[+] Red: preview
[+] Contrato: addr_test1wz873...

[+] Consultando UTxOs del contrato...
[+] Encontrados 6 UTxOs
    #1: 5.00 ADA - TxHash: 9e776b34...
    #2: 2.00 ADA - TxHash: 852ed06a...
    ...

    Total: 18.00 ADA

======================================================================
 RESUMEN: 6 UTxOs con 18.00 ADA bloqueados
======================================================================
```

### Inicializar Contrato (Pendiente)

```bash
python init.py
```

Envia 5 ADA al contrato con el datum inicial vacio:
- sensors: []
- recent_readings: []
- admin: placeholder
- last_updated: timestamp
- total_sensors: 0

### Registrar Sensor (Pendiente)

```bash
python register_sensor.py
```

### Agregar Lectura (Pendiente)

```bash
python add_reading.py
```

## Arquitectura

```
pycardano-client/
├── config.py              # Configuracion global
├── cardano_utils.py       # Utilidades para Cardano
├── query.py               # Consultar estado
├── init.py                # Inicializar contrato (WIP)
├── register_sensor.py     # Registrar sensor (TODO)
├── add_reading.py         # Agregar lectura (TODO)
└── README.md              # Esta documentacion
```

### Modulos

**config.py**
- Carga variables de entorno
- Define rutas a archivos
- Valida configuracion

**cardano_utils.py**
- `get_blockfrost_api()` - Cliente Blockfrost
- `get_network()` - Red de Cardano
- `load_wallet()` - Cargar wallet desde seed
- `load_script()` - Cargar script OpShin
- `get_script_address()` - Direccion del contrato
- `get_contract_utxos()` - UTxOs del contrato
- `print_utxo_summary()` - Resumen de UTxOs

**query.py**
- Consulta estado del contrato
- Muestra UTxOs y balances
- Detecta datums

## Notas Tecnicas

### Por que PyCardano + Blockfrost directamente?

Inicialmente intentamos usar `BlockFrostChainContext` de PyCardano, pero encontramos
problemas de compatibilidad con la inicializacion de la red.

**Solucion:** Usamos `blockfrost-python` directamente para consultas y PyCardano
para construir/firmar transacciones. Esto nos da:

- Control total sobre las llamadas API
- Mejor debugging
- Misma funcionalidad

### Estado de Datums

Actualmente el contrato tiene 6 UTxOs (18 ADA) pero **ninguno tiene datum**.
Estos son solo fondos enviados antes de implementar datums correctamente.

Para usar el contrato necesitamos:
1. Ejecutar `init.py` para crear un UTxO con datum valido
2. Luego usar ese UTxO para operaciones (register, add_reading, etc.)

### Formato de Datums

El datum del contrato sigue la estructura definida en OpShin:

```python
HumiditySensorDatum:
    sensors: List[SensorConfig]           # Lista de sensores
    recent_readings: List[HumidityReading]  # Ultimas lecturas
    admin: bytes                          # PubKeyHash admin
    last_updated: int                     # Timestamp
    total_sensors: int                    # Contador
```

## Proximos Pasos

### Fase 1: Scripts Base (Esta Semana)
- [ ] Completar init.py usando PyCardano Transaction Builder
- [ ] Implementar register_sensor.py
- [ ] Implementar add_reading.py
- [ ] Probar flujo completo en testnet

### Fase 2: API REST (Proxima Semana)
- [ ] Crear API con FastAPI
- [ ] Endpoints: /query, /register, /add-reading
- [ ] Documentacion OpenAPI
- [ ] Testing con pytest

### Fase 3: Integracion Frontend (Semana 3)
- [ ] Conectar frontend React existente
- [ ] Dashboard de sensores en tiempo real
- [ ] Graficas de humedad
- [ ] Alertas visuales

### Fase 4: Produccion (Semana 4)
- [ ] Auditoria de seguridad
- [ ] Tests end-to-end
- [ ] Deploy en Mainnet
- [ ] Documentacion de usuario final

## Troubleshooting

### Error: "Network token mismatch"

Tu API key de Blockfrost no coincide con la red configurada. Verifica:

```bash
# El API key debe empezar con:
- "preview" para Preview Testnet
- "preprod" para Preprod Testnet
- "mainnet" para Mainnet
```

### Error: "No module named pycardano"

```bash
pip install pycardano
```

### Error: "BLOCKFROST_PROJECT_ID no configurado"

Crea el archivo `.env` en `../mesh-client/`:

```bash
cd ../mesh-client
cp .env.example .env
# Edita .env con tus credenciales
```

## Recursos

- [PyCardano Docs](https://pycardano.readthedocs.io/)
- [Blockfrost API](https://docs.blockfrost.io/)
- [OpShin Docs](https://opshin.dev/)
- [Cardano Preview Testnet Faucet](https://docs.cardano.org/cardano-testnet/tools/faucet/)

## Contacto

Para preguntas o reportar issues, ver el README principal del proyecto.

---

**Estado Actual:** MVP en desarrollo - Consultas funcionando, transacciones en implementacion
