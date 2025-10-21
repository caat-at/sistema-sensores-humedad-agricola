# -*- coding: utf-8 -*-
"""
Script para configurar wallet con cardano-cli
"""

import config
import subprocess
from pathlib import Path

def setup_wallet():
    """
    Configurar wallet usando cardano-cli desde recovery phrase
    """
    print("[*] Configurando wallet con cardano-cli...\n")

    keys_dir = Path(__file__).parent / "cli-keys"
    keys_dir.mkdir(exist_ok=True)

    # 1. Guardar recovery phrase
    recovery_file = keys_dir / "recovery-phrase.txt"
    with open(recovery_file, 'w') as f:
        f.write(config.ADMIN_SEED_PHRASE)

    print(f"[OK] Recovery phrase guardada")

    # 2. Generar root key desde recovery phrase
    print("\n[+] Generando root key...")

    root_key_file = keys_dir / "root.prv"

    cmd = [
        "cardano-cli", "address", "key-gen",
        "--verification-key-file", str(keys_dir / "root.vkey"),
        "--signing-key-file", str(root_key_file)
    ]

    # Nota: cardano-cli key-gen genera claves aleatorias
    # Para usar recovery phrase necesitamos un enfoque diferente

    print("\n[!] NOTA: cardano-cli no puede derivar directamente desde recovery phrase")
    print("[!] Necesitamos usar cardano-address o un enfoque alternativo")
    print()
    print("[+] Alternativa recomendada:")
    print("    1. Usar la wallet que ya tienes configurada en Mesh")
    print("    2. Exportar las claves desde esa wallet")
    print("    3. O usar PyCardano para firmar (sin cardano-cli)")
    print()
    print("[+] Por simplicidad, vamos a usar un enfoque hibrido:")
    print("    - cardano-cli para construir transacciones")
    print("    - PyCardano para firmar")
    print("    - cardano-cli para submit")

    return True

if __name__ == "__main__":
    try:
        setup_wallet()
    except Exception as e:
        print(f"\n[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()
