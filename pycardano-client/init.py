# -*- coding: utf-8 -*-
"""
Script para inicializar el contrato con PyCardano
Envia ADA al contrato con el datum inicial
"""

from pycardano import *
import config
import json
import time

def load_script():
    """Cargar el script compilado de OpShin"""
    with open(config.SCRIPT_PATH, 'r') as f:
        script_json = json.load(f)

    # El script esta en formato CBOR hex
    script_cbor = script_json.get('cborHex', script_json.get('cbor', ''))

    if not script_cbor:
        raise ValueError("No se encontro cborHex en el script")

    return PlutusV2Script(bytes.fromhex(script_cbor))

def create_initial_datum():
    """
    Crear datum inicial del contrato

    Estructura:
    - sensors: List[SensorConfig] = []
    - recent_readings: List[HumidityReading] = []
    - admin: bytes (PubKeyHash)
    - last_updated: int (timestamp)
    - total_sensors: int = 0
    """
    admin_placeholder = bytes.fromhex("00" * 28)  # 28 bytes de ceros

    datum = PlutusData()
    datum.constructor = 0
    datum.fields = [
        [],  # sensors: lista vacia
        [],  # recent_readings: lista vacia
        admin_placeholder,  # admin
        int(time.time() * 1000),  # last_updated (milisegundos)
        0  # total_sensors
    ]

    return datum

def main():
    print("[*] Inicializando contrato con PyCardano...\n")

    # 1. Configurar red
    if config.NETWORK == "preview":
        network = Network.TESTNET
    else:
        network = Network.MAINNET

    # BlockFrost detecta automaticamente la red del project_id
    # Si empieza con "preview", usa testnet
    # Si empieza con "mainnet", usa mainnet
    context = BlockFrostChainContext(
        project_id=config.BLOCKFROST_PROJECT_ID,
        base_url=None  # Auto-detectar
    )

    print(f"[+] Conectado a {config.NETWORK}")

    # 2. Cargar wallet desde seed phrase
    print("[+] Cargando wallet...")

    # Convertir seed phrase a clave HD
    from pycardano import HDWallet

    hdwallet = HDWallet.from_mnemonic(config.ADMIN_SEED_PHRASE)
    payment_key = hdwallet.derive_from_path("m/1852'/1815'/0'/0/0")
    stake_key = hdwallet.derive_from_path("m/1852'/1815'/0'/2/0")

    payment_signing_key = payment_key.signing_key
    payment_verification_key = payment_key.verification_key

    stake_signing_key = stake_key.signing_key
    stake_verification_key = stake_key.verification_key

    # Crear direccion
    wallet_address = Address(
        payment_part=payment_verification_key.hash(),
        staking_part=stake_verification_key.hash(),
        network=network
    )

    print(f"[OK] Wallet: {wallet_address}")

    # 3. Verificar balance
    print("\n[+] Verificando balance...")
    utxos = context.utxos(wallet_address)

    if not utxos:
        print("[ERROR] No hay UTxOs en la wallet")
        return

    total_lovelace = sum(utxo.output.amount.coin for utxo in utxos)
    total_ada = total_lovelace / 1_000_000

    print(f"Balance: {total_ada:.2f} ADA")

    if total_ada < 10:
        print("[WARN] Advertencia: Balance bajo para produccion")

    # 4. Cargar script
    print("\n[+] Cargando script OpShin...")
    script = load_script()
    script_hash_val = plutus_script_hash(script)

    # Direccion del script
    script_address = Address(script_hash_val, network=network)
    print(f"[OK] Direccion del script: {script_address}")

    # Verificar que coincida con CONTRACT_ADDRESS
    if str(script_address) != config.CONTRACT_ADDRESS:
        print(f"[WARN] ADVERTENCIA: La direccion calculada no coincide!")
        print(f"   Calculada: {script_address}")
        print(f"   En .env:   {config.CONTRACT_ADDRESS}")
        print(f"   Continuando de todas formas...")

    # 5. Crear datum
    print("\n[+] Creando datum inicial...")
    datum = create_initial_datum()

    print(f"Datum: {datum}")

    # 6. Construir transaccion
    print("\n[+] Construyendo transaccion...")

    builder = TransactionBuilder(context)
    builder.add_input_address(wallet_address)

    # Output al contrato con datum inline
    builder.add_output(
        TransactionOutput(
            address=script_address,
            amount=5_000_000,  # 5 ADA
            datum=datum
        )
    )

    # 7. Firmar y enviar
    print("[+] Firmando transaccion...")

    signed_tx = builder.build_and_sign(
        signing_keys=[payment_signing_key],
        change_address=wallet_address
    )

    print("[+] Enviando a blockchain...")

    tx_hash = context.submit_tx(signed_tx.to_cbor())

    print("\n[OK] Contrato inicializado exitosamente!")
    print("=" * 70)
    print(f"[+] TxHash: {tx_hash}")
    print(f"[+] Explorer:")
    if config.NETWORK == "preview":
        print(f"    https://preview.cardanoscan.io/transaction/{tx_hash}")
    else:
        print(f"    https://cardanoscan.io/transaction/{tx_hash}")
    print("=" * 70)
    print("\n[+] Espera 1-2 minutos para confirmacion")
    print("[+] Luego consulta con: python query.py")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()
