from typing import Dict, Any
from backend.config import config
from backend.classifier import TrafficClassification

class TimeToFailurePredictor:
    def __init__(self):
        self.sla_threshold_ms = config.SLA_LATENCY_THRESHOLD_MS

    def predict(self, metrics: Dict[str, Any], classification_result: Dict[str, Any]) -> Dict[str, Any]:
        classification = classification_result.get("classification")
        mean_latency = metrics.get("mean_latency_ms", 1.0)
        latency_slope = metrics.get("latency_slope", 0.0)
        cpu_pct = metrics.get("system_cpu_percent", 0.0)

        if classification in (TrafficClassification.NORMAL, TrafficClassification.BENIGN_SURGE, TrafficClassification.DOWNSTREAM_STALL):
            if mean_latency < 250.0:
                return {
                    "is_degrading": False,
                    "seconds_to_failure": None,
                    "urgency_score": 0.0,
                    "status_label": "STABLE",
                    "explanation": "Traffic is operating safely within SLA limits."
                }

        if mean_latency >= self.sla_threshold_ms:
            return {
                "is_degrading": True,
                "seconds_to_failure": 0.0,
                "urgency_score": 1.0,
                "status_label": "SLA_BREACHED",
                "explanation": f"Current latency ({mean_latency}ms) has breached SLA threshold ({self.sla_threshold_ms}ms)."
            }

        effective_slope = latency_slope
        if effective_slope <= config.MIN_SLOPE_FOR_REGRESSION:
            if cpu_pct > 65.0 and mean_latency > 80.0:
                effective_slope = max(10.0, (mean_latency / 5.0))
            else:
                return {
                    "is_degrading": False,
                    "seconds_to_failure": None,
                    "urgency_score": 0.0,
                    "status_label": "STABLE",
                    "explanation": "Latency is steady; no SLA breach trajectory detected."
                }

        remaining_headroom_ms = self.sla_threshold_ms - mean_latency
        seconds_to_failure = remaining_headroom_ms / effective_slope
        seconds_to_failure = max(0.5, min(config.MAX_COUNTDOWN_SECONDS, round(seconds_to_failure, 1)))

        urgency = min(1.0, max(0.0, 1.0 - (seconds_to_failure / 25.0)))
        status_label = "CRITICAL" if seconds_to_failure < 5.0 else ("WARNING" if seconds_to_failure < 15.0 else "ELEVATED")

        return {
            "is_degrading": True,
            "seconds_to_failure": seconds_to_failure,
            "urgency_score": round(urgency, 3),
            "status_label": status_label,
            "explanation": f"Latency degrading at {round(effective_slope, 2)} ms/s. Predicted SLA breach in {seconds_to_failure}s."
        }

ttf_predictor = TimeToFailurePredictor()
