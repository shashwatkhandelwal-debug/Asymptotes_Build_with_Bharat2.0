from enum import Enum
from typing import Dict, Any
from backend.config import config

class TrafficClassification(str, Enum):
    NORMAL = "NORMAL"
    BENIGN_SURGE = "BENIGN_SURGE"
    COMPLEXITY_ATTACK = "COMPLEXITY_ATTACK"
    DOWNSTREAM_STALL = "DOWNSTREAM_STALL"

class TrafficClassifier:
    def __init__(self):
        pass

    def classify(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        rps = metrics.get("rps", 0.0)
        crypto_concentration = metrics.get("crypto_concentration", 0.0)
        cpu_pct = metrics.get("system_cpu_percent", 0.0)
        mean_cpu_time = metrics.get("mean_cpu_time_ms", 0.0)
        mean_latency = metrics.get("mean_latency_ms", 0.0)
        latency_slope = metrics.get("latency_slope", 0.0)
        crypto_rps = metrics.get("crypto_rps", 0.0)

        if rps < 4.0 and mean_latency < 60.0 and cpu_pct < 40.0:
            return {
                "classification": TrafficClassification.NORMAL,
                "confidence": 0.95,
                "rationale": "Traffic volume and CPU utilization within baseline parameters.",
                "advisory": None,
                "indicators": {
                    "cpu_stress": "Low",
                    "traffic_pattern": "Balanced Baseline",
                    "threat_level": "None",
                    "pow_recommended": False
                }
            }

        if mean_latency > 150.0 and cpu_pct < 45.0 and mean_cpu_time < 5.0:
            return {
                "classification": TrafficClassification.DOWNSTREAM_STALL,
                "confidence": 0.90,
                "rationale": f"Elevated latency ({mean_latency}ms) observed with low CPU utilization ({cpu_pct}%). Characteristic of downstream database / I/O latency, not algorithmic CPU exhaustion.",
                "advisory": {
                    "code": "IO_BOTTLENECK_POW_SUPPRESSED",
                    "severity": "WARNING",
                    "title": "Downstream DB / I/O Stall Detected",
                    "root_cause": "System latency is elevated due to waiting on downstream I/O/database response, while host CPU remains idle.",
                    "defense_action": "Proof-of-Work is SUPPRESSED. Enforcing PoW on I/O stalls would punish legitimate users without resolving database wait states.",
                    "remediation": "Inspect database slow query log, scale read replicas, or expand connection pool limits."
                },
                "indicators": {
                    "cpu_stress": "Low (Idle Wait)",
                    "traffic_pattern": "I/O Bound Stall",
                    "threat_level": "Internal Bottleneck (Non-Attack)",
                    "pow_recommended": False
                }
            }

        is_high_cpu = (cpu_pct >= config.ATTACK_CPU_THRESHOLD_PCT) or (mean_cpu_time >= 10.0 and crypto_rps >= 6.0)
        is_concentrated = crypto_concentration >= config.ATTACK_CRYPTO_CONCENTRATION
        is_degrading = latency_slope > config.ATTACK_LATENCY_GROWTH_SLOPE or mean_latency > 140.0

        if (is_high_cpu and is_concentrated) or (is_concentrated and is_degrading and crypto_rps >= 5.0):
            return {
                "classification": TrafficClassification.COMPLEXITY_ATTACK,
                "confidence": 0.94,
                "rationale": f"High CPU utilization ({cpu_pct}% / {mean_cpu_time}ms per req) heavily concentrated on /verify-crypto ({round(crypto_concentration*100, 1)}% traffic share) causing steep latency degradation ({round(latency_slope, 2)} ms/s).",
                "advisory": {
                    "code": "COMPLEXITY_ATTACK_MITIGATION_ACTIVE",
                    "severity": "CRITICAL",
                    "title": "Algorithmic Complexity Flood Detected",
                    "root_cause": "Unauthenticated attackers flooding computationally heavy cryptographic signature endpoint to exhaust CPU cores.",
                    "defense_action": "Adaptive Hashcash PoW challenge active. Forcing client computational expenditure to throttle inbound throughput.",
                    "remediation": "Adaptive PoW is automatically active. Telemetry will automatically taper difficulty as attacker throughput normalizes."
                },
                "indicators": {
                    "cpu_stress": "Critical (Pegged)",
                    "traffic_pattern": "Concentrated Crypto Flood",
                    "threat_level": "Active DoS Attack",
                    "pow_recommended": True
                }
            }

        if rps >= config.SURGE_MIN_RPS and crypto_concentration <= config.SURGE_MAX_CRYPTO_CONCENTRATION:
            return {
                "classification": TrafficClassification.BENIGN_SURGE,
                "confidence": 0.90,
                "rationale": f"High aggregate request rate ({rps} RPS) evenly distributed across endpoints ({round(crypto_concentration*100, 1)}% crypto share). CPU and latency within sustainable operating limits.",
                "advisory": {
                    "code": "BENIGN_SURGE_ZERO_POW",
                    "severity": "INFO",
                    "title": "Legitimate Traffic Surge",
                    "root_cause": "Organic multi-endpoint traffic volume increase (marketing surge / active user spike).",
                    "defense_action": "PoW difficulty remains 0 bits. Zero friction for legitimate users.",
                    "remediation": "No action required. Traffic is healthy."
                },
                "indicators": {
                    "cpu_stress": "Moderate/Sustainable",
                    "traffic_pattern": "Distributed Surge",
                    "threat_level": "None (Legitimate)",
                    "pow_recommended": False
                }
            }

        return {
            "classification": TrafficClassification.NORMAL,
            "confidence": 0.85,
            "rationale": f"System operating within normal parameters (RPS: {rps}, CPU: {cpu_pct}%).",
            "advisory": None,
            "indicators": {
                "cpu_stress": "Nominal",
                "traffic_pattern": "Balanced",
                "threat_level": "None",
                "pow_recommended": False
            }
        }

classifier = TrafficClassifier()
