"""
Test Crypto Verification Operations and CPU Workload
"""
import time
from backend.crypto_endpoint import perform_cpu_heavy_verification, perform_light_operation

def test_cpu_heavy_verification():
    print("Testing CPU Heavy Verification...")
    res = perform_cpu_heavy_verification("test_payload_123", iterations=20000)
    print(f"Result: {res}")
    assert res["verified"] is True
    assert res["cpu_time_ms"] > 0
    assert res["wall_time_ms"] > 0
    assert len(res["digest"]) == 16
    print("[PASS] CPU Heavy Verification Passed!")

def test_light_operation():
    print("Testing Light Operation...")
    res = perform_light_operation("test_light_payload")
    print(f"Result: {res}")
    assert res["verified"] is True
    assert res["wall_time_ms"] < 10.0  # Should be sub-10ms
    print("[PASS] Light Operation Passed!")

if __name__ == "__main__":
    test_cpu_heavy_verification()
    test_light_operation()
    print("[SUCCESS] All Crypto tests passed successfully!")
