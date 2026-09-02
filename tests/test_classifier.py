from backend.classifier import classifier, TrafficClassification
from backend.time_to_failure import ttf_predictor

def test_classifier_and_regression():
    print("=== Testing Traffic Classifier & Time-to-Failure Predictor ===")

    normal_metrics = {
        "rps": 2.5,
        "crypto_rps": 0.5,
        "crypto_concentration": 0.20,
        "system_cpu_percent": 15.0,
        "mean_cpu_time_ms": 1.2,
        "mean_latency_ms": 12.0,
        "latency_slope": 0.01
    }
    c_res = classifier.classify(normal_metrics)
    ttf_res = ttf_predictor.predict(normal_metrics, c_res)
    print(f"Normal profile -> {c_res['classification'].value} | TTF: {ttf_res['seconds_to_failure']}")
    assert c_res["classification"] == TrafficClassification.NORMAL
    assert ttf_res["is_degrading"] is False

    surge_metrics = {
        "rps": 28.0,
        "crypto_rps": 3.0,
        "crypto_concentration": 0.15,
        "system_cpu_percent": 38.0,
        "mean_cpu_time_ms": 2.5,
        "mean_latency_ms": 45.0,
        "latency_slope": 1.2
    }
    c_res = classifier.classify(surge_metrics)
    ttf_res = ttf_predictor.predict(surge_metrics, c_res)
    print(f"Benign Surge profile -> {c_res['classification'].value} | TTF: {ttf_res['seconds_to_failure']}")
    assert c_res["classification"] == TrafficClassification.BENIGN_SURGE
    assert ttf_res["is_degrading"] is False

    attack_metrics = {
        "rps": 45.0,
        "crypto_rps": 42.0,
        "crypto_concentration": 0.93,
        "system_cpu_percent": 88.0,
        "mean_cpu_time_ms": 22.0,
        "mean_latency_ms": 320.0,
        "latency_slope": 28.5
    }
    c_res = classifier.classify(attack_metrics)
    ttf_res = ttf_predictor.predict(attack_metrics, c_res)
    print(f"Complexity Attack profile -> {c_res['classification'].value} | TTF: {ttf_res['seconds_to_failure']}s | Urgency: {ttf_res['urgency_score']}")
    assert c_res["classification"] == TrafficClassification.COMPLEXITY_ATTACK
    assert ttf_res["is_degrading"] is True
    assert ttf_res["seconds_to_failure"] is not None
    assert ttf_res["seconds_to_failure"] > 0

    stall_metrics = {
        "rps": 8.0,
        "crypto_rps": 1.0,
        "crypto_concentration": 0.12,
        "system_cpu_percent": 18.0,
        "mean_cpu_time_ms": 1.1,
        "mean_latency_ms": 450.0,
        "latency_slope": 0.5
    }
    c_res = classifier.classify(stall_metrics)
    ttf_res = ttf_predictor.predict(stall_metrics, c_res)
    print(f"Downstream Stall profile -> {c_res['classification'].value} | TTF: {ttf_res['seconds_to_failure']}")
    assert c_res["classification"] == TrafficClassification.DOWNSTREAM_STALL

    print("[PASS] All classifier and regression profiles correctly identified!")

if __name__ == "__main__":
    test_classifier_and_regression()
    print("[SUCCESS] All classifier tests passed successfully!")
