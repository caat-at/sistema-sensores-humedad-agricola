# -*- coding: utf-8 -*-
"""
Script para consultar el estado del contrato
"""

import config
import cardano_utils as cu

def main():
    print("="*70)
    print(" CONSULTA DE CONTRATO - Sistema de Sensores de Humedad")
    print("="*70)
    print()

    # 1. Informacion basica
    print(f"[+] Red: {config.NETWORK}")
    print(f"[+] Contrato: {config.CONTRACT_ADDRESS}")
    print()

    # 2. UTxOs del contrato
    print("[+] Consultando UTxOs del contrato...")
    try:
        utxos = cu.get_contract_utxos()
        total_ada = cu.print_utxo_summary(utxos)

        print()
        print("="*70)
        print(f" RESUMEN: {len(utxos)} UTxOs con {total_ada:.2f} ADA bloqueados")
        print("="*70)

        # 3. Detalles de datums (si existen)
        print()
        print("[+] Analizando datums...")

        utxos_con_datum = 0
        utxos_sin_datum = 0

        for i, utxo in enumerate(utxos, 1):
            if hasattr(utxo, 'inline_datum') and utxo.inline_datum:
                utxos_con_datum += 1
                print(f"    UTxO #{i}: CON datum inline")
                # Mostrar contenido del datum
                try:
                    datum_cbor = utxo.inline_datum
                    print(f"        CBOR: {datum_cbor[:100]}...")
                except Exception as e:
                    print(f"        Error leyendo datum: {e}")
            elif hasattr(utxo, 'data_hash') and utxo.data_hash:
                utxos_con_datum += 1
                print(f"    UTxO #{i}: CON datum hash")
            else:
                utxos_sin_datum += 1
                print(f"    UTxO #{i}: SIN datum (solo fondos)")

        print()
        print(f"[+] UTxOs con datum: {utxos_con_datum}")
        print(f"[+] UTxOs sin datum: {utxos_sin_datum}")

        if utxos_sin_datum == len(utxos):
            print()
            print("[!] NOTA: Todos los UTxOs son solo fondos.")
            print("[!] El contrato aun no ha sido inicializado con un datum valido.")
            print("[!] Ejecuta: python init.py")

        print()
        print("[OK] Consulta completada exitosamente!")

    except Exception as e:
        print(f"\n[ERROR] Error consultando contrato: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
