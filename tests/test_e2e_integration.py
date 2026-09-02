"""
End-to-End Integration Test Suite.
Tests all REST endpoints, simulator triggers, PoW challenge/response gate,
downstream I/O stall diagnostic advisory, and master reset.
"""
from fastapi.testclient import TestClient
from backend.main import app
from backend.pow_engine import PoWEngine, pow_engine
from backend.ledger import ledger

def test_full_system_e2e():
    print("=== Running Full System E2E Integration Test ===")
    client = TestClient(app)

    # 1. Test Baseline & Health Endpoints
    print("\n1. Testing Baseline Endpoints...")
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"
    print("   [PASS] /api/health -> 200 OK")

    res = client.get("/api/data")
    assert res.status_code == 200
    assert res.json()["status"] == "success"
    print("   [PASS] /api/data -> 200 OK")

    res = client.get("/api/data/db-query")
    assert res.status_code == 200
    assert res.json()["status"] == "db_query_completed"
    print("   [PASS] /api/data/db-query -> 200 OK (DB Query Simulated)")

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

    # 4. Test Simulator Mode Transition: DOWNSTREAM_STALL
    print("\n4. Testing Simulator Mode: DOWNSTREAM_STALL...")
    res = client.post("/api/simulator/mode", json={"mode": "DOWNSTREAM_STALL"})
    assert res.status_code == 200
    assert res.json()["current_mode"] == "DOWNSTREAM_STALL"
    print("   [PASS] Simulator switched to DOWNSTREAM_STALL")

    # 5. Test Simulator Mode Transition: COMPLEXITY_ATTACK
    print("\n5. Testing Simulator Mode: COMPLEXITY_ATTACK...")
    res = client.post("/api/simulator/mode", json={"mode": "COMPLEXITY_ATTACK"})
    assert res.status_code == 200
    assert res.json()["current_mode"] == "COMPLEXITY_ATTACK"
    print("   [PASS] Simulator switched to COMPLEXITY_ATTACK")

    # 6. Test PoW Challenge Issuance & Verification Gate (Middleware Interceptor)
    print("\n6. Testing Adaptive PoW Gate under active difficulty...")
    pow_engine.current_difficulty_bits = 8

    # Request without headers should get 428 Precondition Required
    res = client.post("/api/verify-crypto", json={"payload": "unprotected_request"})
    assert res.status_code == 428
    challenge_data = res.json()["challenge"]
    assert challenge_data["difficulty_bits"] == 8
    print("   [PASS] Unsolved request intercepted with HTTP 428 by AdaptivePoWMiddleware")

    # Client solves challenge
    nonce, attempts, solve_ms = PoWEngine.solve_challenge(challenge_data)
    print(f"   [INFO] Solved 8-bit challenge in {solve_ms}ms ({attempts} attempts, nonce: {nonce})")

    # Request with X-PoW-* headers should pass
    res = client.post(
        "/api/verify-crypto",
        json={"payload": "protected_request"},
        headers={
            "X-PoW-Nonce": nonce,
            "X-PoW-Challenge-ID": challenge_data["challenge_id"],
            "X-PoW-Timestamp": str(challenge_data["timestamp"]),
            "X-PoW-Difficulty": str(challenge_data["difficulty_bits"]),
            "X-PoW-Salt": challenge_data["salt"],
            "X-PoW-Signature": challenge_data["signature"]
        }
    )
    assert res.status_code == 200
    assert res.headers.get("X-PoW-Verified") == "true"
    assert res.json()["pow_solved"] is True
    print("   [PASS] Solved PoW request allowed through with HTTP 200 OK")

    pow_engine.current_difficulty_bits = 0

    # 7. Test Ledger Integrity Verification Endpoint
    print("\n7. Testing Ledger Verification API...")
    res = client.get("/api/ledger/verify")
    assert res.status_code == 200
    assert res.json()["is_valid"] is True
    print(f"   [PASS] /api/ledger/verify -> Chain Valid (Blocks: {res.json()['total_blocks']})")

    # 8. Test Live Tamper Simulation Endpoint
    print("\n8. Testing Live Tamper Simulation API...")
    res = client.post("/api/ledger/tamper", json={"block_index": 1, "new_status": "MALICIOUS_TAMPER"})
    assert res.status_code == 200

    # Verify chain catches the tamper
    res = client.get("/api/ledger/verify")
    assert res.json()["is_valid"] is False
    print(f"   [PASS] Tampered block caught by verification API: {res.json()['message']}")

    # 9. Test Master Demo Reset Endpoint
    print("\n9. Testing Master Demo Reset API...")
    res = client.post("/api/simulator/reset")
    assert res.status_code == 200

    res = client.get("/api/ledger/verify")
    assert res.json()["is_valid"] is True
    assert res.json()["total_blocks"] == 1
    print("   [PASS] Master demo reset successfully restored Genesis state and cleared metrics")

    # 10. Test Frontend Static Page Serving
    print("\n10. Testing Frontend Static Hosting...")
    res = client.get("/")
    assert res.status_code == 200
    assert "<!doctype html>" in res.text.lower()
    print("   [PASS] Root URL '/' serves compiled React single-page app HTML")

    print("\n[SUCCESS] Full End-to-End Integration Suite Passed Completely!")

if __name__ == "__main__":
    test_full_system_e2e()
