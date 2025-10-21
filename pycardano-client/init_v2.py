# -*- coding: utf-8 -*-
"""
Script para inicializar el contrato
Version 2: Construccion manual de transaccion
"""

import config
import cardano_utils as cu
from pycardano import *
import time

def create_datum():
    """
    Crear datum inicial del contrato

    Estructura OpShin:
    @dataclass
    class HumiditySensorDatum(PlutusData):
        sensors: List[SensorConfig]
        recent_readings: List[HumidityReading]
        admin: bytes  # PubKeyHash
        last_updated: int
        total_sensors: int
    """
    # Admin placeholder (28 bytes de ceros)
    admin_placeholder = b'\x00' * 28

    # Timestamp en milisegundos
    timestamp = int(time.time() * 1000)

    # Construir datum como lista (PlutusData constructor 0)
    datum = PlutusData()

    # El datum es un constructor con campos
    # Constructor 0 = HumiditySensorDatum
    datum = [
        [],  # sensors: lista vacia
        [],  # recent_readings: lista vacia
        admin_placeholder,  # admin
        timestamp,  # last_updated
        0  # total_sensors
    ]

    return datum

def build_tx_manually():
    """
    Construir transaccion manualmente sin ChainContext
    Usamos cardano-cli via subprocess como alternativa
    """
    print("[*] Inicializando contrato (Version Manual)...\n")

    # 1. Obtener info de la wallet
    print("[+] Cargando wallet...")
    network = cu.get_network()
    wallet_addr, payment_skey, stake_skey = cu.load_wallet(network)
    print(f"[OK] Wallet: {wallet_addr}")

    # 2. Obtener UTxOs de la wallet usando Blockfrost
    print("\n[+] Obteniendo UTxOs de la wallet...")
    api = cu.get_blockfrost_api()
    wallet_utxos = api.address_utxos(str(wallet_addr))

    if not wallet_utxos:
        print("[ERROR] No hay UTxOs en la wallet")
        return

    print(f"[OK] Encontrados {len(wallet_utxos)} UTxOs")

    # Calcular balance total
    total_lovelace = sum(int(utxo.amount[0].quantity) for utxo in wallet_utxos)
    total_ada = total_lovelace / 1_000_000
    print(f"    Balance total: {total_ada:.2f} ADA")

    # 3. Obtener direccion del script
    print("\n[+] Obteniendo direccion del contrato...")
    script_addr = cu.get_script_address(network)
    print(f"[OK] Script address: {script_addr}")

    # Verificar que coincide
    if str(script_addr) != config.CONTRACT_ADDRESS:
        print(f"[WARN] Direccion calculada != CONTRACT_ADDRESS")
        print(f"       Calculada: {script_addr}")
        print(f"       En .env:   {config.CONTRACT_ADDRESS}")

    # 4. Crear datum
    print("\n[+] Creando datum inicial...")
    datum = create_datum()
    print(f"[OK] Datum: {datum}")

    # 5. Mostrar que se haria
    print("\n[+] Plan de transaccion:")
    print(f"    Input: UTxO de wallet con ~{total_ada:.2f} ADA")
    print(f"    Output 1: {script_addr}")
    print(f"              5.00 ADA con datum inline")
    print(f"    Output 2: {wallet_addr}")
    print(f"              ~{total_ada - 5 - 0.2:.2f} ADA (cambio)")
    print(f"    Fee: ~0.2 ADA (estimado)")

    print("\n[!] NOTA: La construccion de transaccion completa requiere:")
    print("    1. Serializar datum a CBOR")
    print("    2. Construir transaction body")
    print("    3. Calcular fees exactos")
    print("    4. Firmar con payment_skey")
    print("    5. Submit a blockchain")
    print()
    print("    Esto requiere un ChainContext funcional o usar cardano-cli")
    print()
    print("[+] Alternativas para continuar:")
    print("    A) Usar cardano-cli via subprocess")
    print("    B) Implementar ChainContext custom")
    print("    C) Usar Koios API en lugar de Blockfrost")
    print("    D) Usar lucid-cardano desde mesh-client")
    print()
    print("    Recomendacion: Opcion D (ya esta configurado)")

def main():
    try:
        build_tx_manually()
    except Exception as e:
        print(f"\n[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
