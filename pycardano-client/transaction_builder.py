# -*- coding: utf-8 -*-
"""
Transaction Builder para PyCardano
Construcción manual de transacciones para el contrato de sensores
"""

import time
from typing import List, Optional
from pycardano import (
    Address,
    TransactionBuilder,
    TransactionOutput,
    PlutusV2Script,
    plutus_script_hash,
    Redeemer,
    UTxO,
    Value,
    Network,
    HDWallet,
    PaymentSigningKey,
    PaymentVerificationKey,
    BlockFrostChainContext,
)
from blockfrost import ApiUrls

import config
from contract_types import *
from cardano_utils import get_contract_utxos, load_wallet


class SensorTransactionBuilder:
    """
    Constructor de transacciones para el contrato de sensores
    """

    def __init__(self):
        """Inicializar builder con configuración y contexto"""
        print("[+] Inicializando Transaction Builder...")

        # Configuración
        self.network = Network.TESTNET if config.NETWORK == "preview" else Network.MAINNET

        # Determinar base_url según la red
        if config.NETWORK == "preview":
            base_url = ApiUrls.preview.value
        else:
            base_url = ApiUrls.mainnet.value

        # Contexto de blockchain (Blockfrost)
        self.context = BlockFrostChainContext(
            project_id=config.BLOCKFROST_PROJECT_ID,
            base_url=base_url
        )

        # Cargar script del contrato
        self.load_script()

        # Derivar wallet desde seed phrase
        self.setup_wallet()

        print("[OK] Transaction Builder listo")

    def load_script(self):
        """Cargar el script Plutus compilado"""
        print(f"[+] Cargando script desde: {config.SCRIPT_PATH}")

        if not config.SCRIPT_PATH.exists():
            raise FileNotFoundError(f"Script no encontrado: {config.SCRIPT_PATH}")

        # Leer script CBOR
        with open(config.SCRIPT_CBOR_PATH, 'r') as f:
            script_cbor_hex = f.read().strip()

        # Crear PlutusV2Script
        self.script = PlutusV2Script(bytes.fromhex(script_cbor_hex))
        self.script_hash = plutus_script_hash(self.script)
        self.script_address = Address(self.script_hash, network=self.network)

        print(f"[OK] Script cargado")
        print(f"    Script Hash: {self.script_hash}")
        print(f"    Script Address: {self.script_address}")

        # Verificar que coincide con CONTRACT_ADDRESS de config
        expected_addr = config.CONTRACT_ADDRESS
        actual_addr = str(self.script_address)

        if expected_addr != actual_addr:
            print(f"[WARN] Address mismatch!")
            print(f"       Esperada: {expected_addr}")
            print(f"       Actual:   {actual_addr}")

    def setup_wallet(self):
        """Derivar wallet desde seed phrase usando BIP39/BIP44"""
        print("[+] Derivando wallet desde seed phrase...")

        # Usar la función load_wallet de cardano_utils que ya funciona
        self.payment_address, self.payment_skey, stake_skey = load_wallet(self.network)
        self.payment_vkey = PaymentVerificationKey.from_signing_key(self.payment_skey)

        # PKH (Payment Key Hash) - 28 bytes
        self.payment_pkh = bytes(self.payment_vkey.hash())

        print(f"[OK] Wallet derivada")
        print(f"    Address: {self.payment_address}")
        print(f"    PKH: {self.payment_pkh.hex()}")

        # Verificar que coincide con WALLET_ADDRESS de config
        expected_addr = config.WALLET_ADDRESS
        actual_addr = str(self.payment_address)

        if expected_addr != actual_addr:
            print(f"[WARN] Wallet address mismatch!")
            print(f"       Esperada: {expected_addr}")
            print(f"       Actual:   {actual_addr}")

    def get_datum_utxo(self) -> Optional[UTxO]:
        """
        Obtener el UTxO del contrato que contiene el datum con el estado actual

        Returns:
            UTxO con inline_datum o None si no existe
        """
        print("[+] Buscando UTxO con datum...")

        # Usar el contexto de PyCardano para obtener UTxOs correctamente
        utxos = self.context.utxos(self.script_address)

        for utxo in utxos:
            if utxo.output.datum:
                print(f"[OK] UTxO con datum encontrado")
                print(f"    TxHash: {utxo.input.transaction_id}")
                print(f"    Index: {utxo.input.index}")
                return utxo

        print("[WARN] No se encontró UTxO con datum")
        return None

    def decode_datum(self, utxo: UTxO):
        """
        Decodificar el datum de un UTxO

        Args:
            utxo: UTxO que contiene el datum

        Returns:
            Datum decodificado (puede ser HumiditySensorDatum u otro tipo)
        """
        if not utxo.output.datum:
            raise ValueError("UTxO no tiene datum")

        # El datum puede venir como RawCBOR o PlutusData
        datum = utxo.output.datum

        # Si ya es HumiditySensorDatum, retornar directamente
        if isinstance(datum, HumiditySensorDatum):
            return datum

        # Si es RawCBOR, decodificar desde CBOR bytes
        from pycardano import RawCBOR
        if isinstance(datum, RawCBOR):
            # RawCBOR tiene un atributo .cbor que contiene los bytes
            return HumiditySensorDatum.from_cbor(datum.cbor)

        # Si es otro tipo de PlutusData, intentar convertir desde CBOR
        if hasattr(datum, 'to_cbor'):
            return HumiditySensorDatum.from_cbor(datum.to_cbor())

        # Si ya es bytes, decodificar directamente
        if isinstance(datum, bytes):
            return HumiditySensorDatum.from_cbor(datum)

        # Último recurso: asumir que ya está en el formato correcto
        return datum

    def build_register_sensor_tx(
        self,
        sensor_config: SensorConfig,
        collateral_utxo: Optional[UTxO] = None
    ) -> str:
        """
        Construir y enviar transacción para registrar un nuevo sensor

        Args:
            sensor_config: Configuración del sensor a registrar
            collateral_utxo: UTxO para colateral (opcional, se selecciona auto)

        Returns:
            Transaction hash (hex string)
        """
        print("\n" + "="*70)
        print(" CONSTRUYENDO TRANSACCION: RegisterSensor")
        print("="*70)

        # 1. Obtener UTxO con datum actual
        datum_utxo = self.get_datum_utxo()
        if not datum_utxo:
            raise ValueError("No se encontró UTxO con datum. Ejecuta init primero.")

        # 2. Decodificar datum actual
        current_datum = self.decode_datum(datum_utxo)
        print(f"\n[+] Datum actual:")
        print(f"    Sensores: {current_datum.total_sensors}")
        print(f"    Lecturas: {len(current_datum.recent_readings)}")

        # 3. Crear nuevo datum con el sensor agregado
        new_sensors = list(current_datum.sensors) + [sensor_config]
        new_datum = HumiditySensorDatum(
            sensors=new_sensors,
            recent_readings=current_datum.recent_readings,
            admin=current_datum.admin,
            last_updated=int(time.time() * 1000),  # Timestamp actual
            total_sensors=current_datum.total_sensors + 1
        )

        print(f"\n[+] Nuevo datum:")
        print(f"    Sensores: {new_datum.total_sensors}")

        # 4. Crear redeemer
        redeemer_data = RegisterSensor(config=sensor_config)
        redeemer = Redeemer(redeemer_data)

        # 5. Construir transacción
        builder = TransactionBuilder(self.context)

        # Agregar script como input (consumir UTxO del contrato)
        builder.add_script_input(
            utxo=datum_utxo,
            script=self.script,
            redeemer=redeemer
        )

        # Output: Devolver fondos al contrato con nuevo datum
        # El datum es grande, necesitamos agregar más ADA para cumplir con min UTxO
        output_value = datum_utxo.output.amount

        # Agregar 1 ADA extra para asegurar que cumple con el mínimo
        # (El datum con 14 sensores es grande y requiere más ADA)
        from pycardano import Value
        output_value = Value(output_value.coin + 1_000_000)  # +1 ADA

        builder.add_output(
            TransactionOutput(
                address=self.script_address,
                amount=output_value,
                datum=new_datum
            )
        )

        # Agregar inputs de la wallet para fees
        # Obtener UTxOs de la wallet para pagar fees
        print("[+] Obteniendo UTxOs de la wallet para fees...")
        wallet_utxos = self.context.utxos(self.payment_address)
        if not wallet_utxos:
            raise ValueError("No hay UTxOs en la wallet para pagar fees. Necesitas fondos en tu wallet.")

        print(f"    Encontrados {len(wallet_utxos)} UTxOs en wallet")

        # Agregar UTxOs de la wallet como inputs adicionales
        for utxo in wallet_utxos:
            builder.add_input(utxo)

        # Collateral (requerido para scripts Plutus)
        if collateral_utxo:
            builder.collaterals = [collateral_utxo]
        else:
            # Seleccionar un UTxO de la wallet como collateral
            # Buscar un UTxO pequeño (>= 5 ADA) para collateral
            for utxo in wallet_utxos:
                if utxo.output.amount.coin >= 5_000_000:  # >= 5 ADA
                    builder.collaterals = [utxo]
                    break

        # Firma requerida del admin
        builder.required_signers = [self.payment_vkey.hash()]

        # 6. Construir y firmar
        print("\n[+] Construyendo transacción...")
        signed_tx = builder.build_and_sign(
            signing_keys=[self.payment_skey],
            change_address=self.payment_address
        )

        # 7. Enviar
        print("[+] Enviando transacción...")
        tx_hash = self.context.submit_tx(signed_tx.to_cbor())

        print(f"\n[OK] Transacción enviada!")
        print(f"    TxHash: {tx_hash}")
        print(f"    Explorer: https://preview.cardanoscan.io/transaction/{tx_hash}")

        return tx_hash

    def build_add_reading_tx(
        self,
        reading: HumidityReading,
        collateral_utxo: Optional[UTxO] = None
    ) -> str:
        """
        Construir y enviar transacción para agregar una lectura

        Args:
            reading: Lectura a agregar
            collateral_utxo: UTxO para colateral (opcional)

        Returns:
            Transaction hash (hex string)
        """
        print("\n" + "="*70)
        print(" CONSTRUYENDO TRANSACCION: AddReading")
        print("="*70)

        # 1. Obtener UTxO con datum actual
        datum_utxo = self.get_datum_utxo()
        if not datum_utxo:
            raise ValueError("No se encontró UTxO con datum.")

        # 2. Decodificar datum actual
        current_datum = self.decode_datum(datum_utxo)

        # 3. Agregar lectura y mantener solo las últimas 10 por sensor
        MAX_READINGS_PER_SENSOR = 10
        new_readings = list(current_datum.recent_readings) + [reading]

        # Filtrar: mantener solo últimas 10 lecturas por sensor
        # TODO: Implementar lógica de filtrado por sensor_id
        if len(new_readings) > MAX_READINGS_PER_SENSOR * current_datum.total_sensors:
            new_readings = new_readings[-MAX_READINGS_PER_SENSOR * current_datum.total_sensors:]

        new_datum = HumiditySensorDatum(
            sensors=current_datum.sensors,
            recent_readings=new_readings,
            admin=current_datum.admin,
            last_updated=int(time.time() * 1000),
            total_sensors=current_datum.total_sensors
        )

        # 4. Crear redeemer
        redeemer_data = AddReading(reading=reading)
        redeemer = Redeemer(redeemer_data)

        # 5. Construir transacción
        builder = TransactionBuilder(self.context)

        builder.add_script_input(
            utxo=datum_utxo,
            script=self.script,
            redeemer=redeemer
        )

        # El nuevo datum puede ser más grande, agregar 0.5 ADA extra
        from pycardano import Value
        output_value = Value(datum_utxo.output.amount.coin + 500_000)  # +0.5 ADA

        builder.add_output(
            TransactionOutput(
                address=self.script_address,
                amount=output_value,
                datum=new_datum
            )
        )

        # Agregar inputs de la wallet para fees
        print("[+] Obteniendo UTxOs de la wallet para fees...")
        wallet_utxos = self.context.utxos(self.payment_address)
        if not wallet_utxos:
            raise ValueError("No hay UTxOs en la wallet para pagar fees. Necesitas fondos en tu wallet.")

        print(f"    Encontrados {len(wallet_utxos)} UTxOs en wallet")

        # Agregar UTxOs de la wallet como inputs adicionales
        for utxo in wallet_utxos:
            builder.add_input(utxo)

        # Collateral (requerido para scripts Plutus)
        if collateral_utxo:
            builder.collaterals = [collateral_utxo]
        else:
            # Seleccionar un UTxO de la wallet como collateral
            for utxo in wallet_utxos:
                if utxo.output.amount.coin >= 5_000_000:  # >= 5 ADA
                    builder.collaterals = [utxo]
                    break

        builder.required_signers = [self.payment_vkey.hash()]

        # 6. Construir y firmar
        print("\n[+] Construyendo transacción...")
        signed_tx = builder.build_and_sign(
            signing_keys=[self.payment_skey],
            change_address=self.payment_address
        )

        # 7. Enviar
        print("[+] Enviando transacción...")
        tx_hash = self.context.submit_tx(signed_tx.to_cbor())

        print(f"\n[OK] Transacción enviada!")
        print(f"    TxHash: {tx_hash}")
        print(f"    Explorer: https://preview.cardanoscan.io/transaction/{tx_hash}")

        return tx_hash

    def build_add_multiple_readings_tx(
        self,
        readings,
        collateral_utxo=None
    ):
        """
        Construir y enviar transacción para agregar múltiples lecturas (ROLLUP)

        Args:
            readings: Lista de lecturas a agregar
            collateral_utxo: UTxO para colateral (opcional)

        Returns:
            Transaction hash (hex string)
        """
        print('\n' + '='*70)
        print(f' CONSTRUYENDO TRANSACCION: AddMultipleReadings ({len(readings)} lecturas)')
        print('='*70)

        if not readings:
            raise ValueError('La lista de lecturas no puede estar vacía')

        # 1. Obtener UTxO con datum actual
        datum_utxo = self.get_datum_utxo()
        if not datum_utxo:
            raise ValueError('No se encontró UTxO con datum.')

        # 2. Decodificar datum actual
        current_datum = self.decode_datum(datum_utxo)

        # 3. Agregar todas las lecturas
        MAX_READINGS_PER_SENSOR = 10
        new_readings = list(current_datum.recent_readings) + readings

        # Filtrar: mantener solo últimas 10 lecturas por sensor
        if len(new_readings) > MAX_READINGS_PER_SENSOR * current_datum.total_sensors:
            new_readings = new_readings[-MAX_READINGS_PER_SENSOR * current_datum.total_sensors:]

        new_datum = HumiditySensorDatum(
            sensors=current_datum.sensors,
            recent_readings=new_readings,
            admin=current_datum.admin,
            last_updated=int(time.time() * 1000),
            total_sensors=current_datum.total_sensors
        )

        # 4. Crear redeemer con AddMultipleReadings
        redeemer_data = AddMultipleReadings(readings=readings)
        redeemer = Redeemer(redeemer_data)

        # 5. Construir transacción
        builder = TransactionBuilder(self.context)

        builder.add_script_input(
            utxo=datum_utxo,
            script=self.script,
            redeemer=redeemer
        )

        # El nuevo datum será más grande con múltiples lecturas, agregar más ADA
        from pycardano import Value
        extra_ada = 500_000 + (len(readings) * 100_000)  # +0.5 ADA base + 0.1 ADA por lectura
        output_value = Value(datum_utxo.output.amount.coin + extra_ada)

        builder.add_output(
            TransactionOutput(
                address=self.script_address,
                amount=output_value,
                datum=new_datum
            )
        )

        # Agregar inputs de la wallet para fees
        print('[+] Obteniendo UTxOs de la wallet para fees...')
        wallet_utxos = self.context.utxos(self.payment_address)
        if not wallet_utxos:
            raise ValueError('No hay UTxOs en la wallet para pagar fees. Necesitas fondos en tu wallet.')

        print(f'    Encontrados {len(wallet_utxos)} UTxOs en wallet')

        # Agregar UTxOs de la wallet como inputs adicionales
        for utxo in wallet_utxos:
            builder.add_input(utxo)

        # Configurar collateral
        if collateral_utxo:
            builder.collaterals = [collateral_utxo]
        else:
            # Seleccionar un UTxO de la wallet como collateral
            for utxo in wallet_utxos:
                if utxo.output.amount.coin >= 5_000_000:  # >= 5 ADA
                    builder.collaterals = [utxo]
                    break

        builder.required_signers = [self.payment_vkey.hash()]

        # 6. Construir y firmar
        print('\n[+] Construyendo transacción...')
        signed_tx = builder.build_and_sign(
            signing_keys=[self.payment_skey],
            change_address=self.payment_address
        )

        # 7. Enviar
        print('[+] Enviando transacción...')
        tx_hash = self.context.submit_tx(signed_tx.to_cbor())

        print(f'\n[OK] Transacción de rollup enviada!')
        print(f'    TxHash: {tx_hash}')
        print(f'    Lecturas: {len(readings)}')
        print(f'    Explorer: https://preview.cardanoscan.io/transaction/{tx_hash}')

        return tx_hash

