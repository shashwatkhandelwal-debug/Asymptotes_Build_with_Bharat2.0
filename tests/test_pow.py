"""
Test Proof-of-Work (Hashcash SHA-256) Mechanism and Hardware Timing
"""
import time
from backend.pow_engine import PoWEngine, pow_engine

def test_pow_generation_and_solving():
    print("=== Testing PoW Generation & Solving Across Difficulties ===")
    test_difficulties = [0, 8, 10, 12, 14, 16]

    for bits in test_difficulties:
        challenge = pow_engine.generate_challenge(client_ip="192.168.1.50", forced_difficulty=bits)
        assert challenge["difficulty_bits"] == bits

        start = time.perf_counter()
        nonce, attempts, solve_ms = PoWEngine.solve_challenge(challenge)
        elapsed = (time.perf_counter() - start) * 1000.0

        print(f"Difficulty {bits:2d} bits | Solved in {solve_ms:6.2f}ms | Attempts: {attempts:6d} | Nonce: {nonce}")

        assert nonce is not None

        # Verify on server
        is_valid, msg = pow_engine.verify_solution(
            challenge_id=challenge["challenge_id"],
            timestamp=challenge["timestamp"],
            difficulty_bits=bits,
            salt=challenge["salt"],
            client_ip=challenge["client_ip"],
            signature=challenge["signature"],
            nonce=nonce
        )
        assert is_valid is True, f"Server rejected valid solution: {msg}"

    print("[PASS] All difficulty levels solved and verified successfully!")

def test_tampered_challenge_rejection():
    print("\n=== Testing Tampered Challenge Rejection ===")
    challenge = pow_engine.generate_challenge(client_ip="192.168.1.50", forced_difficulty=8)
    nonce, _, _ = PoWEngine.solve_challenge(challenge)

    # Tamper with IP
    is_valid, msg = pow_engine.verify_solution(
        challenge_id=challenge["challenge_id"],
        timestamp=challenge["timestamp"],
        difficulty_bits=8,
        salt=challenge["salt"],
        client_ip="10.0.0.1",  # Altered IP
        signature=challenge["signature"],
        nonce=nonce
    )
    assert is_valid is False
    print(f"[PASS] Tampered IP correctly rejected: {msg}")

    # Invalid nonce
    is_valid, msg = pow_engine.verify_solution(
        challenge_id=challenge["challenge_id"],
        timestamp=challenge["timestamp"],
        difficulty_bits=8,
        salt=challenge["salt"],
        client_ip=challenge["client_ip"],
        signature=challenge["signature"],
        nonce="invalid_nonce_999999"
    )
    assert is_valid is False
    print(f"[PASS] Invalid Nonce correctly rejected: {msg}")

if __name__ == "__main__":
    test_pow_generation_and_solving()
    test_tampered_challenge_rejection()
    print("\n[SUCCESS] All PoW tests passed successfully!")
