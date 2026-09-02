"""
End-to-End Integration Test Suite.
Tests all REST endpoints, simulator triggers, PoW challenge/response gate,
and ledger verification using FastAPI TestClient.
"""
from fastapi.testclient import TestClient
from backend.main import app
from backend.pow_engine import PoWEngine, pow_engine
from backend.ledger import ledger

def test_full_system_e2e():
    print("=== Running Full System E2E Integration Test ===")
    client = TestClient(app)

    # 1. Test Health & Data Endpoints
    print("\n1. Testing Baseline Endpoints...")
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"
    print("   [PASS] /api/health -> 200 OK")

    res = client.get("/api/data")
    assert res.status_code == 200
    assert res.json()["status"] == "success"
    print("   [PASS] /api/data -> 200 OK")

    # 2. Test Crypto Verification Endpoint (No PoW initially)
    print("\n2. Testing /api/verify-crypto when PoW is 0...")
    res = client.post("/api/verify-crypto", json={"payload": "sample_token_payload"})
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "verified"
    assert data["pow_solved"] is False
    print(f"   [PASS] /api/verify-crypto -> 200 OK (Digest: {data['digest']}, CPU: {data['cpu_time_ms']}ms)")

    # 3. Test Simulator Mode Transition: BENIGN_SURGE
    print("\n3. Testing Simulator Mode: BENIGN_SURGE...")
    res = client.post("/api/simulator/mode", json={"mode": "BENIGN_SURGE"})
    assert res.status_code == 200
    assert res.json()["current_mode"] == "BENIGN_SURGE"
    print("   [PASS] Simulator switched to BENIGN_SURGE")

    # 4. Test Simulator Mode Transition: COMPLEXITY_ATTACK
    print("\n4. Testing Simulator Mode: COMPLEXITY_ATTACK...")
    res = client.post("/api/simulator/mode", json={"mode": "COMPLEXITY_ATTACK"})
    assert res.status_code == 200
    assert res.json()["current_mode"] == "COMPLEXITY_ATTACK"
    print("   [PASS] Simulator switched to COMPLEXITY_ATTACK")

    # 5. Test PoW Challenge Issuance & Verification Gate
    print("\n5. Testing Adaptive PoW Gate under active difficulty...")
    # Force difficulty to 8 bits for testing gate
    pow_engine.current_difficulty_bits = 8

    # Unauthenticated request without PoW should get 428 Precondition Required
    res = client.post("/api/verify-crypto", json={"payload": "unprotected_request"})
    assert res.status_code == 428
    challenge_data = res.json()["challenge"]
    assert challenge_data["difficulty_bits"] == 8
    print("   [PASS] Unsolved request rejected with HTTP 428 and issued Hashcash challenge")

    # Client solves the challenge
    nonce, attempts, solve_ms = PoWEngine.solve_challenge(challenge_data)
    print(f"   [INFO] Solved 8-bit challenge in {solve_ms}ms ({attempts} attempts, nonce: {nonce})")

    # Request with valid solved nonce should pass with 200 OK
    res = client.post("/api/verify-crypto", json={
        "payload": "protected_request",
        "pow_challenge_id": challenge_data["challenge_id"],
        "pow_timestamp": challenge_data["timestamp"],
        "pow_difficulty_bits": challenge_data["difficulty_bits"],
        "pow_salt": challenge_data["salt"],
        "pow_signature": challenge_data["signature"],
        "pow_nonce": nonce
    })
    assert res.status_code == 200
    assert res.json()["pow_solved"] is True
    print("   [PASS] Solved PoW request allowed through with HTTP 200 OK")

    # Reset difficulty
    pow_engine.current_difficulty_bits = 0

    # 6. Test Ledger Integrity Verification Endpoint
    print("\n6. Testing Ledger Verification API...")
    res = client.get("/api/ledger/verify")
    assert res.status_code == 200
    assert res.json()["is_valid"] is True
    print(f"   [PASS] /api/ledger/verify -> Chain Valid (Blocks: {res.json()['total_blocks']})")

    # 7. Test Live Tamper Simulation Endpoint
    print("\n7. Testing Live Tamper Simulation API...")
    res = client.post("/api/ledger/tamper", json={"block_index": 1, "new_status": "MALICIOUS_TAMPER"})
    assert res.status_code == 200

    # Verify chain catches the tamper
    res = client.get("/api/ledger/verify")
    assert res.json()["is_valid"] is False
    print(f"   [PASS] Tampered block caught by verification API: {res.json()['message']}")

    # 8. Test Demo Reset Endpoint
    print("\n8. Testing Demo Reset API...")
    res = client.post("/api/ledger/reset")
    assert res.status_code == 200

    res = client.get("/api/ledger/verify")
    assert res.json()["is_valid"] is True
    assert res.json()["total_blocks"] == 1
    print("   [PASS] Demo ledger reset to clean Genesis state")

    # 9. Test Frontend Static Page Serving
    print("\n9. Testing Frontend Static Hosting...")
    res = client.get("/")
    assert res.status_code == 200
    assert "<!doctype html>" in res.text.lower()
    print("   [PASS] Root URL '/' serves compiled React single-page app HTML")

    print("\n[SUCCESS] Full End-to-End Integration Suite Passed Completely!")

if __name__ == "__main__":
    test_full_system_e2e()
