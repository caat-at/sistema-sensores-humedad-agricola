# Solución Final - MVP Testnet

**Fecha:** 2025-10-14
**Decision:** Usar PyCardano 100% con Blockfrost (sin cardano-cli)

---

## Problema Encontrado

`cardano-cli` requiere un nodo local de Cardano corriendo (`--socket-path`), lo cual no es práctico para desarrollo rápido.

## Solución Adoptada

**Usar PyCardano directamente + Blockfrost API**

### Por qué esta es la mejor opción:

1. ✅ **No requiere nodo local**
2. ✅ **Blockfrost ya funciona perfectamente**
3. ✅ **PyCardano puede construir transacciones sin ChainContext**
4. ✅ **Más portable y fácil de desplegar**
5. ✅ **Ideal para API REST backend**

---

## Enfoque Técnico

### Construcción Manual de Transacciones

En lugar de usar `TransactionBuilder` (que requiere ChainContext), vamos a:

1. **Consultar UTxOs** con Blockfrost
2. **Construir TransactionBody** manualmente
3. **Calcular fees** manualmente
4. **Firmar** con PaymentSigningKey
5. **Submit** con Blockfrost

### Ejemplo de Flujo:

```python
from pycardano import *

# 1. Obtener UTxOs (ya funciona)
utxos = blockfrost_api.address_utxos(wallet_addr)

# 2. Construir transaction body manualmente
tx_body = TransactionBody(
    inputs=[...],
    outputs=[...],
    fee=fee_calculado,
    ttl=slot + 1000
)

# 3. Crear witness
witness = make_vkey_witness(tx_body, payment_skey)

# 4. Ensamblar transacción
tx = Transaction(
    transaction_body=tx_body,
    transaction_witness_set=TransactionWitnessSet(
        vkey_witnesses=[witness]
    )
)

# 5. Submit con Blockfrost
tx_cbor = tx.to_cbor()
tx_hash = blockfrost_api.transaction_submit(tx_cbor)
```

---

## Implementación

Vamos a crear `pycardano_tx.py` que contenga utilidades para construir transacciones manualmente.

**Tiempo estimado:** 3-4 horas para implementar init.py, register_sensor.py y add_reading.py

---

## Ventajas de Este Enfoque

1. **Más control** - Sabemos exactamente qué está pasando
2. **Mejor debugging** - Podemos inspeccionar cada paso
3. **Portable** - Funciona en cualquier lugar con acceso a internet
4. **Production-ready** - Blockfrost es usado en producción por muchos proyectos
5. **Documentado** - PyCardano tiene buenos ejemplos de construcción manual

---

## Próximo Paso Inmediato

Implementar `init.py` usando este enfoque.

**Archivo:** `init_final.py`

Características:
- Consulta UTxOs de wallet con Blockfrost
- Construye TransactionBody manualmente
- Calcula fee correcto
- Firma con claves derivadas del seed phrase
- Submitea con Blockfrost
- Verifica en blockchain explorer

---

**Status:** Listo para implementar
**ETA al MVP:** 4-6 horas
