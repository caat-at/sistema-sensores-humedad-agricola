# -*- coding: utf-8 -*-
"""
Wrapper para operaciones con cardano-cli + PyCardano
Enfoque hibrido: usa lo mejor de ambas herramientas
"""

import config
import cardano_utils as cu
import subprocess
import json
import time
from pathlib import Path
from blockfrost import BlockFrostApi, ApiUrls

class CardanoCLI:
    """Wrapper para cardano-cli con soporte de PyCardano"""

    def __init__(self):
        self.keys_dir = Path(__file__).parent / "cli-keys"
        self.keys_dir.mkdir(exist_ok=True)

        self.temp_dir = Path(__file__).parent / "temp"
        self.temp_dir.mkdir(exist_ok=True)

        self.network_magic = "2"  # Preview testnet
        self.api = BlockFrostApi(
            project_id=config.BLOCKFROST_PROJECT_ID,
            base_url=ApiUrls.preview.value
        )

    def query_tip(self):
        """Obtener el tip de la blockchain"""
        result = subprocess.run([
            "cardano-cli", "query", "tip",
            "--testnet-magic", self.network_magic
        ], capture_output=True, text=True)

        if result.returncode != 0:
            raise Exception(f"Error querying tip: {result.stderr}")

        return json.loads(result.stdout)

    def query_protocol_parameters(self):
        """Obtener parametros del protocolo"""
        protocol_file = self.temp_dir / "protocol.json"

        result = subprocess.run([
            "cardano-cli", "query", "protocol-parameters",
            "--testnet-magic", self.network_magic,
            "--out-file", str(protocol_file)
        ], capture_output=True, text=True)

        if result.returncode != 0:
            # Si falla con cardano-cli, usar valores por defecto
            print(f"[WARN] No se pudo obtener protocol parameters con CLI")
            print(f"[+] Usando valores por defecto")

            default_params = {
                "txFeePerByte": 44,
                "txFeeFixed": 155381,
                "minUTxOValue": 1000000,
                "monetaryExpansion": 0.003,
                "treasuryGrowthRate": 0.2,
                "decentralization": 0,
                "extraPraosEntropy": None,
                "protocolMajorVersion": 8,
                "protocolMinorVersion": 0,
                "minPoolCost": 340000000,
                "priceMemory": 0.0577,
                "priceSteps": 0.0000721,
                "maxTxSize": 16384,
                "maxBlockHeaderSize": 1100,
                "maxValueSize": 5000,
                "collateralPercentage": 150,
                "maxCollateralInputs": 3,
                "coinsPerUTxOByte": 4310
            }

            with open(protocol_file, 'w') as f:
                json.dump(default_params, f, indent=2)

        with open(protocol_file, 'r') as f:
            return json.load(f)

    def get_wallet_utxos(self, address):
        """Obtener UTxOs de una direccion usando Blockfrost"""
        return self.api.address_utxos(str(address))

    def calculate_min_fee(self, tx_file, tx_in_count, tx_out_count, witness_count=1):
        """Calcular fee minimo para una transaccion"""
        protocol_file = self.temp_dir / "protocol.json"

        # Asegurar que existan los parametros
        if not protocol_file.exists():
            self.query_protocol_parameters()

        result = subprocess.run([
            "cardano-cli", "transaction", "calculate-min-fee",
            "--tx-body-file", str(tx_file),
            "--tx-in-count", str(tx_in_count),
            "--tx-out-count", str(tx_out_count),
            "--witness-count", str(witness_count),
            "--testnet-magic", self.network_magic,
            "--protocol-params-file", str(protocol_file)
        ], capture_output=True, text=True)

        if result.returncode != 0:
            # Calcular fee estimado manualmente
            # Formula aproximada: 155381 + 44 * tx_size
            estimated_size = 200 + (tx_in_count * 100) + (tx_out_count * 50)
            estimated_fee = 155381 + (44 * estimated_size)
            print(f"[WARN] No se pudo calcular fee exacto, usando estimado: {estimated_fee}")
            return estimated_fee

        # Parse output: "123456 Lovelace"
        fee_str = result.stdout.split()[0]
        return int(fee_str)

# Instancia global
cli = CardanoCLI()
