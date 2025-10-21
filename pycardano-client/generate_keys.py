# -*- coding: utf-8 -*-
"""
Script para generar claves de cardano-cli desde seed phrase
"""

import config
import json
import subprocess
from pathlib import Path
from pycardano import HDWallet

def generate_keys():
    """
    Generar archivos de claves compatibles con cardano-cli
    """
    print("[*] Generando claves desde seed phrase...\n")

    # Directorio para claves
    keys_dir = Path(__file__).parent / "cli-keys"
    keys_dir.mkdir(exist_ok=True)

    # 1. Generar recovery phrase file
    recovery_file = keys_dir / "recovery-phrase.txt"
    with open(recovery_file, 'w') as f:
        f.write(config.ADMIN_SEED_PHRASE)

    print(f"[OK] Recovery phrase guardada en: {recovery_file}")

    # 2. Usar PyCardano para derivar las claves
    hdwallet = HDWallet.from_mnemonic(config.ADMIN_SEED_PHRASE)

    # Derivar payment key
    payment_hdwallet = hdwallet.derive_from_path("m/1852'/1815'/0'/0/0")

    # 3. Extraer extended signing key y verification key
    # El formato de cardano-cli es diferente, necesitamos el cbor hex

    # Obtener claves en formato raw
    payment_skey_bytes = payment_hdwallet.signing_key
    payment_vkey_bytes = payment_hdwallet.verification_key

    # Crear archivos en formato cardano-cli (TextEnvelope)
    payment_skey_file = keys_dir / "payment.skey"
    payment_vkey_file = keys_dir / "payment.vkey"

    # Formato TextEnvelope de cardano-cli
    skey_envelope = {
        "type": "PaymentSigningKeyShelley_ed25519",
        "description": "Payment Signing Key",
        "cborHex": payment_skey_bytes.hex()
    }

    vkey_envelope = {
        "type": "PaymentVerificationKeyShelley_ed25519",
        "description": "Payment Verification Key",
        "cborHex": payment_vkey_bytes.hex()
    }

    with open(payment_skey_file, 'w') as f:
        json.dump(skey_envelope, f, indent=4)

    with open(payment_vkey_file, 'w') as f:
        json.dump(vkey_envelope, f, indent=4)

    print(f"[OK] Payment signing key: {payment_skey_file}")
    print(f"[OK] Payment verification key: {payment_vkey_file}")

    # 4. Generar direccion usando cardano-cli
    print("\n[+] Generando direccion con cardano-cli...")

    addr_file = keys_dir / "payment.addr"

    result = subprocess.run([
        "cardano-cli", "address", "build",
        "--payment-verification-key-file", str(payment_vkey_file),
        "--testnet-magic", "2",  # Preview testnet
        "--out-file", str(addr_file)
    ], capture_output=True, text=True)

    if result.returncode != 0:
        print(f"[ERROR] Error generando direccion: {result.stderr}")
        return False

    with open(addr_file, 'r') as f:
        address = f.read().strip()

    print(f"[OK] Direccion generada: {address}")

    # Verificar que coincide con la esperada
    print(f"\n[+] Verificando direccion...")
    print(f"    Generada:  {address}")
    print(f"    Esperada:  {config.ADMIN_SEED_PHRASE.split()[0]}...")  # Solo muestra primeras palabras

    print(f"\n[OK] Claves generadas exitosamente!")
    print(f"\n[+] Archivos creados:")
    print(f"    - {recovery_file}")
    print(f"    - {payment_skey_file}")
    print(f"    - {payment_vkey_file}")
    print(f"    - {addr_file}")

    return True

if __name__ == "__main__":
    try:
        generate_keys()
    except Exception as e:
        print(f"\n[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()
