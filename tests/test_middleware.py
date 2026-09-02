"""
Test Adaptive PoW Interceptor Middleware.
Verifies header inspection, bypass on difficulty 0, challenge issuance (428),
and successful passage on valid X-PoW-* headers.
"""
from fastapi.testclient import TestClient
from backend.main import app
from backend.pow_engine import pow_engine, PoWEngine

def test_pow_middleware_lifecycle():
    print("=== Testing Adaptive PoW Middleware Interceptor ===")
    client = TestClient(app)

    # 1. When PoW difficulty is 0 (NORMAL / BENIGN_SURGE)
    pow_engine.current_difficulty_bits = 0
    res = client.post("/api/verify-crypto", json={"payload": "unprotected_call_at_0_diff"})
    assert res.status_code == 200
    assert res.json()["status"] == "verified"
    print("   [PASS] Difficulty == 0: Immediate pass-through with zero friction")

    # 2. When PoW difficulty is elevated to 8 bits (COMPLEXITY_ATTACK active)
    pow_engine.current_difficulty_bits = 8

    # Request without headers should be intercepted immediately with HTTP 428
    res = client.post("/api/verify-crypto", json={"payload": "attacker_flood_request"})
    assert res.status_code == 428
    assert res.headers.get("X-PoW-Required") == "true"
    assert res.headers.get("X-PoW-Challenge-ID") is not None
    challenge_data = res.json()["challenge"]
    print("   [PASS] Difficulty > 0: Missing headers intercepted with HTTP 428 (0 CPU consumed on handler!)")

    # 3. Request with forged / invalid nonce
    bad_headers = {
        "X-PoW-Nonce": "fake_invalid_nonce_99999",
        "X-PoW-Challenge-ID": challenge_data["challenge_id"],
        "X-PoW-Timestamp": str(challenge_data["timestamp"]),
        "X-PoW-Difficulty": str(challenge_data["difficulty_bits"]),
        "X-PoW-Salt": challenge_data["salt"],
        "X-PoW-Signature": challenge_data["signature"]
    }
    res = client.post("/api/verify-crypto", json={"payload": "attacker_bad_nonce"}, headers=bad_headers)
    assert res.status_code == 403
    print("   [PASS] Invalid/Forged Nonce rejected with HTTP 403")

    # 4. Request with valid solved nonce header
    nonce, attempts, solve_ms = PoWEngine.solve_challenge(challenge_data)
    valid_headers = {
        "X-PoW-Nonce": nonce,
        "X-PoW-Challenge-ID": challenge_data["challenge_id"],
        "X-PoW-Timestamp": str(challenge_data["timestamp"]),
        "X-PoW-Difficulty": str(challenge_data["difficulty_bits"]),
        "X-PoW-Salt": challenge_data["salt"],
        "X-PoW-Signature": challenge_data["signature"]
    }
    res = client.post("/api/verify-crypto", json={"payload": "legit_solved_request"}, headers=valid_headers)
    assert res.status_code == 200
    assert res.headers.get("X-PoW-Verified") == "true"
    assert res.json()["status"] == "verified"
    print(f"   [PASS] Valid X-PoW-* Nonce allowed through with HTTP 200 OK (Solved in {solve_ms}ms)")

    # 5. Non-protected endpoints under high difficulty
    res = client.get("/api/data")
    assert res.status_code == 200
    assert res.json()["status"] == "success"
    print("   [PASS] Non-protected /api/data bypassed middleware seamlessly")

    # Reset
    pow_engine.current_difficulty_bits = 0
    print("\n[SUCCESS] Middleware Interceptor tests passed completely!")

if __name__ == "__main__":
    test_pow_middleware_lifecycle()
