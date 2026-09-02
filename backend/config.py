"""
Configuration settings for Adaptive PoW Defense System.
Includes calibrated thresholds, difficulty scaling dials, and SLA timeouts.
"""
from pydantic import BaseModel

class SystemConfig(BaseModel):
    # SLA & Latency Limits (in milliseconds)
    SLA_LATENCY_THRESHOLD_MS: float = 800.0  # Max acceptable mean latency before SLA failure
    CRITICAL_LATENCY_THRESHOLD_MS: float = 1200.0  # Point where service fails/drops traffic
    
    # Real CPU Cryptographic Workload
    # PBKDF2 iterations for /api/verify-crypto: tuned to take ~15-25ms of pure CPU per call
    CRYPTO_PBKDF2_ITERATIONS: int = 25_000
    
    # Telemetry Window
    TELEMETRY_WINDOW_SECONDS: int = 15  # Sliding window size for metrics aggregation
    METRICS_TICK_INTERVAL_SEC: float = 0.5  # Telemetry broadcast / computation cadence
    
    # Proof-of-Work (Hashcash SHA-256) Difficulty Range
    # 0 = Disabled
    # 8 bits  ~ 256 hashes (~1-2 ms solve)
    # 10 bits ~ 1,024 hashes (~5-10 ms solve)
    # 12 bits ~ 4,096 hashes (~15-30 ms solve)
    # 14 bits ~ 16,384 hashes (~60-120 ms solve)
    # 16 bits ~ 65,536 hashes (~250-500 ms solve)
    MIN_DIFFICULTY_BITS: int = 8
    MAX_DIFFICULTY_BITS: int = 16
    POW_EXPIRY_SECONDS: int = 60
    POW_SECRET_KEY: str = "adaptive-pow-defense-secret-key-2026"
    
    # Traffic Classifier Calibrated Thresholds
    # (Tuned against synthetic attack profiles where crypto endpoint is flooded)
    ATTACK_CPU_THRESHOLD_PCT: float = 55.0  # CPU % above which complexity attack is indicated
    ATTACK_CRYPTO_CONCENTRATION: float = 0.70  # Ratio of requests hitting /verify-crypto vs other endpoints
    ATTACK_LATENCY_GROWTH_SLOPE: float = 15.0  # ms/sec latency slope degradation
    
    SURGE_MIN_RPS: float = 12.0  # Requests/sec threshold indicating high traffic
    SURGE_MAX_CRYPTO_CONCENTRATION: float = 0.45  # Legitimate surge is distributed across endpoints
    
    # Time-to-Failure Regression Limits
    MIN_SLOPE_FOR_REGRESSION: float = 0.05  # Minimum positive slope to trigger countdown
    MAX_COUNTDOWN_SECONDS: float = 60.0  # Max ceiling for countdown display

config = SystemConfig()
