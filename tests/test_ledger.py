import os
import time
import gc
from backend.ledger import AuditLedger

def test_ledger_tamper_evidence():
    print("=== Testing Hash-Chained Audit Ledger ===")
    test_db = f"backend/test_ledger_{int(time.time())}.db"

    test_ledger = AuditLedger(db_path=test_db)

    v1 = test_ledger.verify_chain()
    print(f"Genesis Verification: {v1['message']} (Valid: {v1['is_valid']})")
    assert v1["is_valid"] is True
    assert v1["total_blocks"] == 1

    print("\nAppending 5 valid challenge blocks...")
    for i in range(1, 6):
        test_ledger.append_entry(
            client_ip=f"192.168.1.{10+i}",
            difficulty_bits=8 + i,
            challenge_id=f"challenge_uuid_{i}",
            nonce=f"nonce_val_{i*100}",
            status="SOLVED" if i % 2 == 0 else "DROPPED_UNSOLVED"
        )

    v2 = test_ledger.verify_chain()
    print(f"6-Block Chain Verification: {v2['message']} (Valid: {v2['is_valid']})")
    assert v2["is_valid"] is True
    assert v2["total_blocks"] == 6

    print("\n[Tamper Attack Simulation] Modifying Block #3 status in SQLite directly...")
    tamper_res = test_ledger.tamper_block_for_demo(block_index=3, new_status="MALICIOUS_SOLVED")
    assert tamper_res["success"] is True

    v3 = test_ledger.verify_chain()
    print(f"\nVerification after tampering: Valid={v3['is_valid']}")
    print(f"Caught Error: {v3['message']}")
    print(f"Tampered Block Index: #{v3['tampered_block_index']}")

    assert v3["is_valid"] is False
    assert v3["tampered_block_index"] == 3
    assert v3["error_type"] == "ALTERED_PAYLOAD"
    print("[PASS] Cryptographic hash verification successfully caught the exact tampered block!")

    del test_ledger
    gc.collect()
    try:
        if os.path.exists(test_db):
            os.remove(test_db)
    except Exception:
        pass

if __name__ == "__main__":
    test_ledger_tamper_evidence()
    print("\n[SUCCESS] All Ledger tests passed successfully!")
