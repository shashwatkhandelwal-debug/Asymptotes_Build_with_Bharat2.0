from pydantic import BaseModel

class SystemConfig(BaseModel):
    SLA_LATENCY_THRESHOLD_MS: float = 800.0
    CRITICAL_LATENCY_THRESHOLD_MS: float = 1200.0
    CRYPTO_PBKDF2_ITERATIONS: int = 25_000
    TELEMETRY_WINDOW_SECONDS: int = 15
    METRICS_TICK_INTERVAL_SEC: float = 0.5
    MIN_DIFFICULTY_BITS: int = 8
    MAX_DIFFICULTY_BITS: int = 16
    POW_EXPIRY_SECONDS: int = 60
    POW_SECRET_KEY: str = "adaptive-pow-defense-secret-key-2026"
    ATTACK_CPU_THRESHOLD_PCT: float = 55.0
    ATTACK_CRYPTO_CONCENTRATION: float = 0.70
    ATTACK_LATENCY_GROWTH_SLOPE: float = 15.0
    SURGE_MIN_RPS: float = 12.0
    SURGE_MAX_CRYPTO_CONCENTRATION: float = 0.45
    MIN_SLOPE_FOR_REGRESSION: float = 0.05
    MAX_COUNTDOWN_SECONDS: float = 60.0

config = SystemConfig()
