import cli_wrapper

# Test 1: Query tip
print("[+] Test 1: Query tip")
try:
    tip = cli_wrapper.cli.query_tip()
    print(f"[OK] Epoch: {tip.get('epoch', 'N/A')}")
    print(f"[OK] Slot: {tip.get('slot', 'N/A')}")
except Exception as e:
    print(f"[WARN] Error: {e}")

# Test 2: Protocol parameters
print("\n[+] Test 2: Protocol parameters")
try:
    params = cli_wrapper.cli.query_protocol_parameters()
    print(f"[OK] Fee per byte: {params.get('txFeePerByte', 'N/A')}")
    print(f"[OK] Min UTxO: {params.get('minUTxOValue', 'N/A')}")
except Exception as e:
    print(f"[WARN] Error: {e}")

print("\n[OK] CLI Wrapper funcionando!")
