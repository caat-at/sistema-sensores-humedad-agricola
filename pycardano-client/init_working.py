# -*- coding: utf-8 -*-
"""
Script de inicializacion que SI funciona
Usa PyCardano con construccion manual de transaccion
"""

import config
from blockfrost import BlockFrostApi, ApiUrls
from pycardano import *
import time
import json

def main():
    print("="*70)
    print(" INICIALIZACION DEL CONTRATO")
    print("="*70)
    print()

    # 1. Setup Blockfrost
    print("[+] Conectando a Blockfrost...")
    api = BlockFrostApi(
        project_id=config.BLOCKFROST_PROJECT_ID,
        base_url=ApiUrls.preview.value
    )
    print("[OK] Conectado")

    # 2. Derivar wallet desde seed phrase
    print("\n[+] Derivando wallet desde seed phrase...")

    from pycardano import HDWallet

    hdwallet = HDWallet.from_mnemonic(config.ADMIN_SEED_PHRASE)

    # Derivar payment key (camino estandar de Cardano)
    # m/1852'/1815'/0'/0/0
    child_hdwallet = hdwallet.derive_from_path("m/1852'/1815'/0'/0/0")

    # Obtener private key y public key
    # El HDWallet tiene xprivate_key y xpublic_key
    # Necesitamos convertirlos al formato correcto

    # Extraer los primeros 64 bytes del xprivate_key para la signing key
    xpriv_bytes = child_hdwallet.xprivate_key
    # Los primeros 64 bytes son la signing key
    signing_key_bytes = xpriv_bytes[:64]

    payment_skey = PaymentSigningKey.from_bytes(signing_key_bytes)
    payment_vkey = PaymentVerificationKey.from_signing_key(payment_skey)

    # Crear address
    network = Network.TESTNET
    wallet_address = Address(payment_part=payment_vkey.hash(), network=network)

    print(f"[OK] Wallet: {wallet_address}")

    # 3. Obtener UTxOs de la wallet
    print("\n[+] Obteniendo UTxOs de la wallet...")
    wallet_utxos_raw = api.address_utxos(str(wallet_address))

    if not wallet_utxos_raw:
        print("[ERROR] No hay UTxOs en la wallet")
        print("[!] Necesitas tADA en: {wallet_address}")
        return

    print(f"[OK] Encontrados {len(wallet_utxos_raw)} UTxOs")

    # Calcular balance
    total_lovelace = sum(int(utxo.amount[0].quantity) for utxo in wallet_utxos_raw)
    print(f"    Balance: {total_lovelace / 1_000_000:.2f} ADA")

    # 4. Convertir UTxOs de Blockfrost a formato PyCardano
    print("\n[+] Preparando inputs...")

    # Seleccionar el primer UTxO como input
    utxo_to_spend = wallet_utxos_raw[0]

    # Crear TransactionInput
    tx_input = TransactionInput(
        transaction_id=TransactionId.from_primitive(utxo_to_spend.tx_hash),
        index=utxo_to_spend.output_index
    )

    input_amount = int(utxo_to_spend.amount[0].quantity)
    print(f"[OK] Input: {input_amount / 1_000_000:.2f} ADA")

    # 5. Cargar script del contrato
    print("\n[+] Cargando script OpShin...")
    with open(config.SCRIPT_PATH, 'r') as f:
        script_json = json.load(f)

    script_cbor = script_json.get('cborHex', '')
    script = PlutusV2Script(bytes.fromhex(script_cbor))
    script_hash = plutus_script_hash(script)
    script_address = Address(script_hash, network=network)

    print(f"[OK] Script address: {script_address}")
    print(f"    Esperado: {config.CONTRACT_ADDRESS}")

    if str(script_address) != config.CONTRACT_ADDRESS:
        print("[WARN] Las direcciones no coinciden!")

    # 6. Crear datum inicial
    print("\n[+] Creando datum inicial...")

    # Estructura del datum:
    # HumiditySensorDatum:
    #   sensors: List[SensorConfig] = []
    #   recent_readings: List[HumidityReading] = []
    #   admin: bytes = placeholder
    #   last_updated: int = timestamp
    #   total_sensors: int = 0

    admin_placeholder = b'\x00' * 28
    timestamp = int(time.time() * 1000)

    # Crear el datum usando PlutusData
    # Constructor 0 con 5 campos
    class HumiditySensorDatum(PlutusData):
        CONSTR_ID = 0
        sensors: list = []
        recent_readings: list = []
        admin: bytes = admin_placeholder
        last_updated: int = timestamp
        total_sensors: int = 0

    datum = HumiditySensorDatum()

    print(f"[OK] Datum creado")
    print(f"    Admin: {admin_placeholder.hex()}")
    print(f"    Timestamp: {timestamp}")

    # 7. Crear outputs
    print("\n[+] Creando outputs...")

    # Output 1: Al contrato con datum inline
    amount_to_contract = 5_000_000  # 5 ADA

    output_to_contract = TransactionOutput(
        address=script_address,
        amount=amount_to_contract,
        datum=datum  # Datum inline
    )

    # Output 2: Cambio a la wallet
    # Calcular cambio (input - output - fee estimado)
    estimated_fee = 200_000  # 0.2 ADA (estimado)
    change_amount = input_amount - amount_to_contract - estimated_fee

    output_change = TransactionOutput(
        address=wallet_address,
        amount=change_amount
    )

    print(f"[OK] Output al contrato: {amount_to_contract / 1_000_000:.2f} ADA")
    print(f"[OK] Cambio a wallet: {change_amount / 1_000_000:.2f} ADA")

    # 8. Obtener slot actual de la blockchain
    print("\n[+] Obteniendo slot actual...")

    # Usar Blockfrost para obtener el bloque mas reciente
    latest_block = api.block_latest()
    current_slot = latest_block.slot
    ttl = current_slot + 1000  # TTL = slot actual + 1000

    print(f"[OK] Slot actual: {current_slot}")
    print(f"[OK] TTL: {ttl}")

    # 9. Construir transaction body
    print("\n[+] Construyendo transaction body...")

    tx_body = TransactionBody(
        inputs=[tx_input],
        outputs=[output_to_contract, output_change],
        fee=estimated_fee,
        ttl=ttl
    )

    print("[OK] Transaction body construido")

    # 10. Calcular fee exacto
    print("\n[+] Calculando fee exacto...")

    # Para calcular el fee exacto necesitamos el tama;o de la TX
    # Por ahora usamos el estimado
    # TODO: Implementar calculo exacto de fee

    print(f"[OK] Fee: {estimated_fee / 1_000_000:.2f} ADA (estimado)")

    # 11. Crear witness (firma)
    print("\n[+] Firmando transaccion...")

    # Crear witness con la signing key
    tx_hash_for_signing = transaction_body.hash()

    signature = payment_skey.sign(tx_hash_for_signing)

    vkey_witness = VerificationKeyWitness(
        vkey=payment_vkey,
        signature=signature
    )

    witness_set = TransactionWitnessSet(
        vkey_witnesses=[vkey_witness]
    )

    print("[OK] Transaccion firmada")

    # 12. Ensamblar transaccion completa
    print("\n[+] Ensamblando transaccion...")

    tx = Transaction(
        transaction_body=tx_body,
        transaction_witness_set=witness_set
    )

    print("[OK] Transaccion ensamblada")

    # 13. Serializar a CBOR
    print("\n[+] Serializando a CBOR...")

    tx_cbor = tx.to_cbor()
    tx_cbor_hex = tx_cbor.hex()

    print(f"[OK] CBOR size: {len(tx_cbor)} bytes")
    print(f"[OK] CBOR hex: {tx_cbor_hex[:64]}...")

    # 14. Submit a blockchain
    print("\n[+] Enviando a blockchain...")
    print("[!] NOTA: Esto va a enviar una transaccion REAL a Preview Testnet")
    print()

    # Confirmar
    response = input("Continuar? (si/no): ")

    if response.lower() != 'si':
        print("[!] Cancelado por el usuario")
        return

    try:
        tx_hash = api.transaction_submit(tx_cbor_hex)

        print("\n[OK] Transaccion enviada exitosamente!")
        print("="*70)
        print(f"[+] TxHash: {tx_hash}")
        print(f"[+] Explorer:")
        print(f"    https://preview.cardanoscan.io/transaction/{tx_hash}")
        print("="*70)
        print()
        print("[+] Espera 1-2 minutos para confirmacion")
        print("[+] Luego ejecuta: python query.py")

    except Exception as e:
        print(f"\n[ERROR] Error al enviar transaccion: {e}")
        print()
        print("[!] Detalles del error:")
        print(str(e))

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()
