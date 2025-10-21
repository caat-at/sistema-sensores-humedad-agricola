"""
Configuración para PyCardano Client
Sistema de Sensores de Humedad Agrícola
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno del mesh-client
env_path = Path(__file__).parent.parent / "mesh-client" / ".env"
load_dotenv(env_path)

# Configuración de red
NETWORK = "preview"  # "preview" o "mainnet"
BLOCKFROST_PROJECT_ID = os.getenv("BLOCKFROST_PROJECT_ID")

# Dirección del contrato
CONTRACT_ADDRESS = os.getenv("CONTRACT_ADDRESS")

# Wallet admin (seed phrase)
ADMIN_SEED_PHRASE = os.getenv("ADMIN_SEED_PHRASE")

# Ruta al script compilado
SCRIPT_PATH = Path(__file__).parent.parent / "contracts" / "opshin" / "build" / "humidity_sensor" / "script.plutus"
SCRIPT_CBOR_PATH = Path(__file__).parent.parent / "contracts" / "opshin" / "build" / "humidity_sensor" / "script.cbor"

# Wallet info (derivada de ADMIN_SEED_PHRASE con path m/1852'/1815'/0'/0/0)
# Esta es la misma address que usa Lucid-Cardano
WALLET_ADDRESS = "addr_test1qqk2wn579xnauz85l4jv6gpjg9vrac960t0m3txw2tyafsp4s0ln5d66zrfy0qgasjqxxg3qc5ftmqyhparh58w2fqxqkwnupe"
WALLET_PKH = bytes.fromhex("2ca74e9e29a7de08f4fd64cd203241583ee0ba7adfb8acce52c9d4c0")

# Validar configuración
if not BLOCKFROST_PROJECT_ID:
    raise ValueError("BLOCKFROST_PROJECT_ID no configurado en .env")

if not ADMIN_SEED_PHRASE:
    raise ValueError("ADMIN_SEED_PHRASE no configurado en .env")

if not CONTRACT_ADDRESS:
    raise ValueError("CONTRACT_ADDRESS no configurado en .env")

print(f"[OK] Configuracion cargada:")
print(f"   Red: {NETWORK}")
print(f"   Contrato: {CONTRACT_ADDRESS}")
print(f"   Script: {SCRIPT_PATH.exists() and 'Encontrado' or 'No encontrado'}")
