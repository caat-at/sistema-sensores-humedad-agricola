# -*- coding: utf-8 -*-
"""
Constructor manual de transacciones para evitar BlockFrostChainContext
Construye transacciones Plutus sin depender de ChainContext
"""

from typing import List
from pycardano import (
    Transaction,
    TransactionBody,
    TransactionInput,
    TransactionOutput,
    TransactionWitnessSet,
    VerificationKeyWitness,
    Value,
    PlutusV2Script,
    Redeemer,
    UTxO,
    Address,
    PaymentSigningKey,
    PaymentVerificationKey,
    ExecutionUnits,
    PlutusData,
    RawCBOR,
    Network,
)


def build_plutus_spending_tx(
    script_utxo: UTxO,
    script: PlutusV2Script,
    redeemer: PlutusData,
    output_to_script: TransactionOutput,
    wallet_utxos: List[UTxO],
    wallet_address: Address,
    signing_key: PaymentSigningKey,
    verification_key: PaymentVerificationKey,
    collateral_utxo: UTxO = None,
) -> Transaction:
    """
    Construir transacción Plutus manualmente

    Args:
        script_utxo: UTxO del script a consumir
        script: Script Plutus V2
        redeemer: Redeemer para el script
        output_to_script: Output de vuelta al script
        wallet_utxos: UTxOs de la wallet para fees
        wallet_address: Address de la wallet
        signing_key: Signing key para firmar
        verification_key: Verification key
        collateral_utxo: UTxO para collateral (opcional)

    Returns:
        Transaction firmada y lista para submit
    """

    # 1. Construir inputs
    inputs = []

    # Input del script
    script_input = TransactionInput(
        transaction_id=script_utxo.input.transaction_id,
        index=script_utxo.input.index
    )
    inputs.append(script_input)

    # Inputs de la wallet para fees (usar los primeros 2)
    total_wallet_input = 0
    for utxo in wallet_utxos[:2]:
        inputs.append(utxo.input)
        total_wallet_input += utxo.output.amount.coin

    # 2. Construir outputs
    outputs = [output_to_script]

    # 3. Calcular change
    # Total input = script + wallet inputs
    total_input = script_utxo.output.amount.coin + total_wallet_input

    # Total output = script output
    total_output = output_to_script.amount.coin

    # Fee estimado (conservador)
    estimated_fee = 500000  # 0.5 ADA (conservador para script Plutus)

    # Change = input - output - fee
    change_amount = total_input - total_output - estimated_fee

    if change_amount > 1000000:  # Si hay más de 1 ADA de change
        change_output = TransactionOutput(
            address=wallet_address,
            amount=Value(coin=change_amount)
        )
        outputs.append(change_output)

    # 4. Construir redeemers
    # Redeemer con execution units conservadores
    redeemers = [
        Redeemer(
            data=redeemer,
            ex_units=ExecutionUnits(
                mem=14000000,  # 14M memory units
                steps=10000000000  # 10B CPU steps (conservador)
            )
        )
    ]

    # 5. Script data hash
    # PyCardano calculará esto automáticamente si lo dejamos None
    # O podemos calcularlo manualmente más tarde
    script_data_hash = None  # Se calculará automáticamente

    # 6. Collateral
    collateral = []
    if collateral_utxo:
        collateral.append(collateral_utxo.input)
    elif wallet_utxos:
        # Usar primer UTxO de wallet como collateral
        collateral.append(wallet_utxos[0].input)

    # 7. Required signers (wallet PKH)
    required_signers = [verification_key.hash()]

    # 8. TTL (time to live) - slot actual + 1000 slots (~16 minutos)
    # Para Preview podemos usar un valor alto
    ttl = 50000000  # Slot conservador

    # 9. Construir TransactionBody
    tx_body = TransactionBody(
        inputs=inputs,
        outputs=outputs,
        fee=estimated_fee,
        ttl=ttl,
        script_data_hash=script_data_hash,
        collateral=collateral,
        required_signers=required_signers,
        network_id=Network.TESTNET,  # Campo requerido para Plutus V2
    )

    # 10. Firmar transacción
    signature = signing_key.sign(tx_body.hash())
    vkey_witness = VerificationKeyWitness(verification_key, signature)

    # 11. Construir witness set
    witness_set = TransactionWitnessSet(
        vkey_witnesses=[vkey_witness],
        plutus_v2_script=[script],
        redeemer=redeemers,
    )

    # 12. Construir transacción completa
    tx = Transaction(
        transaction_body=tx_body,
        transaction_witness_set=witness_set,
    )

    return tx


def estimate_tx_fee(tx: Transaction) -> int:
    """
    Estimar fee de transacción

    Args:
        tx: Transacción a estimar

    Returns:
        Fee estimado en lovelace
    """
    # Fórmula: base_fee + (fee_per_byte * tx_size)
    base_fee = 155381
    fee_per_byte = 44

    tx_cbor = tx.to_cbor()
    tx_size = len(tx_cbor)

    fee = base_fee + (fee_per_byte * tx_size)

    # Agregar extra para scripts Plutus
    plutus_overhead = 300000

    return fee + plutus_overhead


def rebuild_tx_with_correct_fee(
    tx: Transaction,
    signing_key: PaymentSigningKey,
    verification_key: PaymentVerificationKey,
) -> Transaction:
    """
    Reconstruir transacción con fee correcto

    Args:
        tx: Transacción inicial
        signing_key: Signing key
        verification_key: Verification key

    Returns:
        Transacción con fee ajustado
    """
    # Calcular fee correcto
    correct_fee = estimate_tx_fee(tx)

    # Ajustar change en el output
    tx_body = tx.transaction_body
    outputs = list(tx_body.outputs)

    # El último output es el change
    if len(outputs) > 1:
        change_output = outputs[-1]
        # Ajustar amount
        old_change = change_output.amount.coin
        fee_diff = correct_fee - tx_body.fee
        new_change = old_change - fee_diff

        if new_change > 1000000:
            outputs[-1] = TransactionOutput(
                address=change_output.address,
                amount=Value(coin=new_change)
            )
        else:
            # Si el change es muy pequeño, eliminarlo y aumentar fee
            outputs = outputs[:-1]
            correct_fee += new_change

    # Crear nuevo body con fee correcto
    new_body = TransactionBody(
        inputs=tx_body.inputs,
        outputs=outputs,
        fee=correct_fee,
        ttl=tx_body.ttl,
        script_data_hash=tx_body.script_data_hash,
        collateral=tx_body.collateral,
        required_signers=tx_body.required_signers,
        network_id=tx_body.network_id,  # Preservar network_id
    )

    # Re-firmar
    signature = signing_key.sign(new_body.hash())
    vkey_witness = VerificationKeyWitness(verification_key, signature)

    witness_set = TransactionWitnessSet(
        vkey_witnesses=[vkey_witness],
        plutus_v2_script=tx.transaction_witness_set.plutus_v2_script,
        redeemer=tx.transaction_witness_set.redeemer,
    )

    return Transaction(
        transaction_body=new_body,
        transaction_witness_set=witness_set,
    )
