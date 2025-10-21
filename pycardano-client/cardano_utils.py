# -*- coding: utf-8 -*-
"""
Utilidades para interactuar con Cardano usando PyCardano + Blockfrost
"""

import config
import json
from pathlib import Path
from blockfrost import BlockFrostApi, ApiUrls
from pycardano import *

def get_blockfrost_api():
    """Crear instancia de Blockfrost API"""
    return BlockFrostApi(
        project_id=config.BLOCKFROST_PROJECT_ID,
        base_url=ApiUrls.preview.value
    )

def get_network():
    """Obtener la red de Cardano"""
    if config.NETWORK == "preview":
        return Network.TESTNET
    else:
        return Network.MAINNET

def load_wallet(network=None):
    """
    Cargar wallet desde seed phrase
    Retorna: (address, payment_signing_key, stake_signing_key)
    """
    if network is None:
        network = get_network()

    from pycardano import HDWallet, PaymentSigningKey, PaymentVerificationKey
    from pycardano import StakeSigningKey, StakeVerificationKey

    hdwallet = HDWallet.from_mnemonic(config.ADMIN_SEED_PHRASE)

    # Derivar claves - HDWallet.derive retorna otro HDWallet, necesitamos las claves
    # Payment: m/1852'/1815'/0'/0/0 (external chain, index 0)
    # Stake: m/1852'/1815'/0'/2/0 (chimeric account, index 0)
    payment_hdwallet = hdwallet.derive_from_path("m/1852'/1815'/0'/0/0")
    stake_hdwallet = hdwallet.derive_from_path("m/1852'/1815'/0'/2/0")

    # Obtener signing keys y verification keys
    # xprivate_key es de 64 bytes: primeros 32 son private key, últimos 32 son chain code
    payment_signing_key = PaymentSigningKey.from_primitive(payment_hdwallet.xprivate_key[:32])
    payment_verification_key = PaymentVerificationKey.from_signing_key(payment_signing_key)

    stake_signing_key = StakeSigningKey.from_primitive(stake_hdwallet.xprivate_key[:32])
    stake_verification_key = StakeVerificationKey.from_signing_key(stake_signing_key)

    # Crear direccion CON stake key
    wallet_address = Address(
        payment_part=payment_verification_key.hash(),
        staking_part=stake_verification_key.hash(),
        network=network
    )

    return wallet_address, payment_signing_key, stake_signing_key

def load_script():
    """Cargar el script OpShin compilado"""
    with open(config.SCRIPT_PATH, 'r') as f:
        script_json = json.load(f)

    script_cbor = script_json.get('cborHex', script_json.get('cbor', ''))

    if not script_cbor:
        raise ValueError("No se encontro cborHex en el script")

    return PlutusV2Script(bytes.fromhex(script_cbor))

def get_script_address(network=None):
    """Obtener la direccion del script"""
    if network is None:
        network = get_network()

    script = load_script()
    script_hash_val = plutus_script_hash(script)

    return Address(script_hash_val, network=network)

def get_wallet_utxos(wallet_address):
    """Obtener UTxOs de una wallet usando Blockfrost"""
    api = get_blockfrost_api()
    utxos_data = api.address_utxos(str(wallet_address))

    # Convertir a formato PyCardano
    utxos = []
    for utxo_data in utxos_data:
        # TODO: Convertir formato blockfrost a PyCardano UTxO
        # Por ahora retornamos los datos crudos
        utxos.append(utxo_data)

    return utxos_data

def get_contract_utxos():
    """Obtener UTxOs del contrato"""
    api = get_blockfrost_api()
    return api.address_utxos(config.CONTRACT_ADDRESS)

def print_utxo_summary(utxos):
    """Imprimir resumen de UTxOs"""
    print(f"[+] Encontrados {len(utxos)} UTxOs")

    total_lovelace = 0
    for i, utxo in enumerate(utxos, 1):
        lovelace = int(utxo.amount[0].quantity)
        ada = lovelace / 1_000_000
        total_lovelace += lovelace

        print(f"    #{i}: {ada:.2f} ADA - TxHash: {utxo.tx_hash[:16]}...")

    total_ada = total_lovelace / 1_000_000
    print(f"\n    Total: {total_ada:.2f} ADA")

    return total_ada
