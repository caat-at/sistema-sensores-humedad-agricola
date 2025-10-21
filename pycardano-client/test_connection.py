# -*- coding: utf-8 -*-
"""
Script para probar la conexion con Blockfrost
"""

import config
from pycardano import *

def test_connection():
    print("[*] Probando conexion con Blockfrost...\n")

    # Determinar la red basada en el prefijo del project_id
    project_id = config.BLOCKFROST_PROJECT_ID

    if project_id.startswith('preview'):
        print("[+] Detectada red: Preview Testnet")
        network = Network.TESTNET
    elif project_id.startswith('preprod'):
        print("[+] Detectada red: Preprod Testnet")
        network = Network.TESTNET
    elif project_id.startswith('mainnet'):
        print("[+] Detectada red: Mainnet")
        network = Network.MAINNET
    else:
        print("[ERROR] No se pudo detectar la red del project_id")
        return

    try:
        # Crear contexto - Blockfrost auto-detecta la URL segun el project_id
        context = BlockFrostChainContext(project_id=project_id)

        print("[OK] Conexion establecida con Blockfrost")

        # Obtener informacion de la epoca actual
        print("\n[+] Informacion de la red:")
        print(f"    Epoca actual: {context._epoch_info.epoch}")
        print(f"    Slot actual: ~{context._epoch_info.start_time}")

        # Probar consultando los UTxOs del contrato
        print(f"\n[+] Consultando contrato: {config.CONTRACT_ADDRESS}")

        contract_addr = Address.from_primitive(config.CONTRACT_ADDRESS)
        utxos = context.utxos(contract_addr)

        print(f"[OK] Encontrados {len(utxos)} UTxOs en el contrato")

        total_lovelace = sum(utxo.output.amount.coin for utxo in utxos)
        total_ada = total_lovelace / 1_000_000

        print(f"    Total bloqueado: {total_ada:.2f} ADA")

        print("\n[OK] Todas las pruebas de conexion exitosas!")
        return True

    except Exception as e:
        print(f"\n[ERROR] Error de conexion: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_connection()
