# -*- coding: utf-8 -*-
"""
Probar blockfrost-python directamente
"""

import config
from blockfrost import BlockFrostApi, ApiError, ApiUrls

def test_blockfrost():
    print("[*] Probando blockfrost-python directamente...\n")

    api_key = config.BLOCKFROST_PROJECT_ID
    print(f"[+] API Key: {api_key[:20]}...")

    try:
        # Crear API para preview testnet
        api = BlockFrostApi(
            project_id=api_key,
            base_url=ApiUrls.preview.value  # Usar URL de preview explicitamente
        )

        print("[OK] API inicializada")

        # Probar obteniendo info de epoca
        epoch_info = api.epoch_latest()
        print(f"\n[+] Epoca actual: {epoch_info.epoch}")
        print(f"    Bloques: {epoch_info.block_count}")
        print(f"    Transacciones: {epoch_info.tx_count}")

        # Obtener UTxOs directamente
        utxos = api.address_utxos(config.CONTRACT_ADDRESS)
        print(f"\n[OK] Encontrados {len(utxos)} UTxOs")

        for i, utxo in enumerate(utxos[:3], 1):  # Mostrar solo los primeros 3
            ada = int(utxo.amount[0].quantity) / 1_000_000
            print(f"    UTxO {i}: {ada:.2f} ADA")

        print("\n[OK] Todas las pruebas exitosas con blockfrost-python!")
        return True

    except ApiError as e:
        print(f"\n[ERROR] ApiError: {e}")
        return False
    except Exception as e:
        print(f"\n[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_blockfrost()
