# -*- coding: utf-8 -*-
"""
Constructor de transacciones usando PyCardano
Maneja la construcción manual de transacciones para el contrato OpShin
"""

import config
import time
from pathlib import Path
from typing import Optional, List

from pycardano import (
    PlutusV2Script,
    PlutusData,
    Redeemer,
    TransactionBuilder,
    TransactionOutput,
    UTxO,
    Address,
    PaymentSigningKey,
    PaymentVerificationKey,
    HDWallet,
)
from blockfrost import BlockFrostApi, ApiUrls, ApiError

from contract_types import HumiditySensorDatum


class CardanoTransactionBuilder:
    """Constructor de transacciones para el contrato de sensores"""

    def __init__(self):
        """Inicializar el builder con Blockfrost y wallet"""
        print("[+] Inicializando TransactionBuilder...")

        # 1. Setup Blockfrost API
        self.api = BlockFrostApi(
            project_id=config.BLOCKFROST_PROJECT_ID,
            base_url=ApiUrls.preview.value
        )
        print("[OK] Blockfrost API configurada")

        # 2. Cargar script del contrato
        self.script = self._load_contract_script()
        print(f"[OK] Script cargado: {config.CONTRACT_ADDRESS[:20]}...")

        # 3. Derivar wallet desde seed phrase
        self.payment_skey, self.payment_vkey, self.wallet_address, self.wallet_pkh = self._setup_wallet()
        print(f"[OK] Wallet configurada: {self.wallet_address}")
        print(f"[OK] PKH: {self.wallet_pkh.hex()}")

    def _load_contract_script(self) -> PlutusV2Script:
        """Cargar el script Plutus compilado"""
        import json

        script_path = config.SCRIPT_PATH

        if not script_path.exists():
            raise FileNotFoundError(f"Script no encontrado: {script_path}")

        with open(script_path, 'r') as f:
            script_json = json.load(f)

        # El script está en formato CBOR hex
        cbor_hex = script_json.get('cborHex')
        if not cbor_hex:
            raise ValueError("Script JSON no contiene 'cborHex'")

        return PlutusV2Script(bytes.fromhex(cbor_hex))

    def _setup_wallet(self):
        """Derivar wallet desde seed phrase usando HDWallet"""
        from pycardano import Network

        # Derivar desde mnemonic
        hdwallet = HDWallet.from_mnemonic(config.ADMIN_SEED_PHRASE)

        # Derivar clave de pago (m/1852'/1815'/0'/0/0 - formato Cardano estándar)
        payment_hdwallet = hdwallet.derive_from_path("m/1852'/1815'/0'/0/0")

        # Obtener la private key correctamente
        # xprivate_key es Extended Private Key de 96 bytes
        # Los primeros 64 bytes son: 32 bytes key + 32 bytes chain code
        # Solo necesitamos los primeros 32 bytes para ed25519
        skey_bytes = payment_hdwallet.xprivate_key[:32]
        payment_skey = PaymentSigningKey(skey_bytes)

        # Derivar verification key desde signing key
        payment_vkey = payment_skey.to_verification_key()

        # TEMPORAL: Usar address y PKH conocidos (los mismos que Lucid)
        # Esto evita problemas de derivación inconsistente entre Lucid y PyCardano
        wallet_address = Address.from_primitive(config.WALLET_ADDRESS)
        wallet_pkh = config.WALLET_PKH

        return payment_skey, payment_vkey, wallet_address, wallet_pkh

    def get_contract_utxo_with_datum(self) -> Optional[UTxO]:
        """
        Obtener el UTxO del contrato que tiene datum inline

        Returns:
            UTxO con datum inline, o None si no se encuentra
        """
        print("\n[+] Buscando UTxO del contrato con datum...")

        try:
            utxos = self.api.address_utxos(config.CONTRACT_ADDRESS)

            if not utxos:
                print("[!] No se encontraron UTxOs en el contrato")
                return None

            # Filtrar solo los que tienen inline_datum
            utxos_with_datum = [u for u in utxos if hasattr(u, 'inline_datum') and u.inline_datum]

            if not utxos_with_datum:
                print(f"[!] Se encontraron {len(utxos)} UTxOs pero ninguno tiene datum inline")
                return None

            # Tomar el primero
            utxo = utxos_with_datum[0]

            print(f"[OK] UTxO encontrado:")
            print(f"    TxHash: {utxo.tx_hash[:16]}...")
            print(f"    Index: {utxo.tx_index}")

            # Obtener amount
            amount_lovelace = int(utxo.amount[0].quantity)
            amount_ada = amount_lovelace / 1_000_000
            print(f"    Amount: {amount_ada:.2f} ADA")

            # Construir UTxO de PyCardano
            from pycardano import TransactionInput, TransactionOutput, Value

            tx_in = TransactionInput.from_primitive([utxo.tx_hash, utxo.tx_index])

            # Construir Value
            value = Value(coin=amount_lovelace)

            # Construir Address del script
            script_address = Address.from_primitive(config.CONTRACT_ADDRESS)

            # Decodificar datum inline
            datum_bytes = bytes.fromhex(utxo.inline_datum)

            # Crear TransactionOutput
            tx_out = TransactionOutput(
                address=script_address,
                amount=value,
                datum=datum_bytes  # datum inline raw
            )

            # Crear UTxO
            pycardano_utxo = UTxO(tx_in, tx_out)

            return pycardano_utxo

        except ApiError as e:
            print(f"[ERROR] Error de Blockfrost: {e}")
            return None
        except Exception as e:
            print(f"[ERROR] Error inesperado: {e}")
            import traceback
            traceback.print_exc()
            return None

    def decode_datum(self, datum_bytes: bytes) -> HumiditySensorDatum:
        """
        Decodificar datum desde CBOR bytes

        Args:
            datum_bytes: Datum en formato CBOR

        Returns:
            HumiditySensorDatum decodificado
        """
        return HumiditySensorDatum.from_cbor(datum_bytes)

    def get_wallet_utxos(self) -> List[UTxO]:
        """
        Obtener UTxOs disponibles en la wallet

        Returns:
            Lista de UTxOs
        """
        print("\n[+] Consultando UTxOs de la wallet...")

        try:
            utxos_api = self.api.address_utxos(str(self.wallet_address))

            if not utxos_api:
                print("[!] No hay UTxOs en la wallet")
                return []

            # Convertir a PyCardano UTxOs
            from pycardano import TransactionInput, TransactionOutput, Value

            pycardano_utxos = []

            for utxo in utxos_api:
                tx_in = TransactionInput.from_primitive([utxo.tx_hash, utxo.tx_index])
                amount_lovelace = int(utxo.amount[0].quantity)
                value = Value(coin=amount_lovelace)

                tx_out = TransactionOutput(
                    address=self.wallet_address,
                    amount=value
                )

                pycardano_utxos.append(UTxO(tx_in, tx_out))

            total_ada = sum(u.output.amount.coin for u in pycardano_utxos) / 1_000_000
            print(f"[OK] Encontrados {len(pycardano_utxos)} UTxOs")
            print(f"[OK] Balance total: {total_ada:.2f} ADA")

            return pycardano_utxos

        except ApiError as e:
            print(f"[ERROR] Error de Blockfrost: {e}")
            return []

    def get_protocol_parameters(self):
        """Obtener parámetros del protocolo desde Blockfrost"""
        print("\n[+] Obteniendo parametros del protocolo...")

        try:
            # Blockfrost API para parámetros
            params = self.api.epoch_latest_parameters()

            # Construir objeto de parámetros para PyCardano
            # (simplificado - en producción necesitarías todos los parámetros)
            from pycardano import ProtocolParameters

            protocol_params = ProtocolParameters(
                min_fee_a=int(params.min_fee_a),
                min_fee_b=int(params.min_fee_b),
                max_tx_size=int(params.max_tx_size),
                max_block_header_size=int(params.max_block_header_size),
                key_deposit=int(params.key_deposit),
                pool_deposit=int(params.pool_deposit),
                min_pool_cost=int(params.min_pool_cost),
                price_memory=float(params.price_mem),
                price_steps=float(params.price_step),
                max_tx_execution_units={
                    "memory": int(params.max_tx_ex_mem),
                    "steps": int(params.max_tx_ex_steps)
                },
                max_block_execution_units={
                    "memory": int(params.max_block_ex_mem),
                    "steps": int(params.max_block_ex_steps)
                },
                max_value_size=int(params.max_val_size),
                collateral_percentage=int(params.collateral_percent),
                max_collateral_inputs=int(params.max_collateral_inputs),
                coins_per_utxo_byte=int(params.coins_per_utxo_size),
            )

            print("[OK] Parametros del protocolo obtenidos")
            return protocol_params

        except Exception as e:
            print(f"[ERROR] Error obteniendo parametros: {e}")
            # Retornar parámetros por defecto para Preview
            print("[WARN] Usando parametros por defecto para Preview")
            from pycardano import ProtocolParameters
            return ProtocolParameters(
                min_fee_a=44,
                min_fee_b=155381,
                max_tx_size=16384,
                max_block_header_size=1100,
                key_deposit=2000000,
                pool_deposit=500000000,
                min_pool_cost=340000000,
                price_memory=0.0577,
                price_steps=0.0000721,
                max_tx_execution_units={"memory": 14000000, "steps": 10000000000},
                max_block_execution_units={"memory": 62000000, "steps": 40000000000},
                max_value_size=5000,
                collateral_percentage=150,
                max_collateral_inputs=3,
                coins_per_utxo_byte=4310,
            )

    def submit_tx(self, tx_cbor_hex: str) -> str:
        """
        Enviar transacción a la blockchain

        Args:
            tx_cbor_hex: Transacción en formato CBOR hex

        Returns:
            TxHash de la transacción enviada
        """
        print("\n[+] Enviando transaccion a blockchain...")

        try:
            # Blockfrost API espera bytes, no hex string
            import tempfile
            import os

            # Crear archivo temporal con la transacción
            with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.tx') as f:
                f.write(bytes.fromhex(tx_cbor_hex))
                temp_file = f.name

            try:
                # Submit usando el archivo temporal
                tx_hash = self.api.transaction_submit(temp_file)
                print(f"[OK] Transaccion enviada exitosamente!")
                print(f"    TxHash: {tx_hash}")
                return tx_hash
            finally:
                # Limpiar archivo temporal
                if os.path.exists(temp_file):
                    os.unlink(temp_file)

        except ApiError as e:
            print(f"[ERROR] Error al enviar transaccion: {e}")
            raise
