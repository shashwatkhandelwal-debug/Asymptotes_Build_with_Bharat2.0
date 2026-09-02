from backend.crypto_endpoint import perform_cpu_heavy_verification, perform_light_operation

def test_cpu_heavy_verification():
    res = perform_cpu_heavy_verification("test_payload_123", iterations=20000)
    assert res["verified"] is True
    assert res["cpu_time_ms"] > 0
    assert res["wall_time_ms"] > 0
    assert len(res["digest"]) == 16
    print("[PASS] CPU Heavy Verification Passed!")

def test_light_operation():
    res = perform_light_operation("test_light_payload")
    assert res["verified"] is True
    assert res["wall_time_ms"] < 10.0
    print("[PASS] Light Operation Passed!")

if __name__ == "__main__":
    test_cpu_heavy_verification()
    test_light_operation()
    print("[SUCCESS] All Crypto tests passed successfully!")
