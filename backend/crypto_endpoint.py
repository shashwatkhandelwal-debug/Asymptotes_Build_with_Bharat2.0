import hashlib
import time
import asyncio
from typing import Dict, Any
from backend.config import config

def perform_cpu_heavy_verification(payload: str, signature_hint: str = "", iterations: int = None) -> Dict[str, Any]:
    if iterations is None:
        iterations = config.CRYPTO_PBKDF2_ITERATIONS

    start_cpu = time.process_time()
    start_wall = time.perf_counter()

    salt = b"asymptotes-pow-defense-salt-2026"
    derived_key = hashlib.pbkdf2_hmac(
        'sha256',
        payload.encode('utf-8'),
        salt,
        iterations=iterations,
        dklen=32
    )
    final_digest = hashlib.sha256(derived_key + payload.encode('utf-8')).hexdigest()

    end_cpu = time.process_time()
    end_wall = time.perf_counter()

    return {
        "verified": True,
        "digest": final_digest[:16],
        "iterations": iterations,
        "cpu_time_ms": round((end_cpu - start_cpu) * 1000.0, 2),
        "wall_time_ms": round((end_wall - start_wall) * 1000.0, 2)
    }

def perform_light_operation(payload: str) -> Dict[str, Any]:
    start_cpu = time.process_time()
    start_wall = time.perf_counter()

    digest = hashlib.sha256(payload.encode('utf-8')).hexdigest()

    end_cpu = time.process_time()
    end_wall = time.perf_counter()

    return {
        "verified": True,
        "digest": digest[:16],
        "cpu_time_ms": round((end_cpu - start_cpu) * 1000.0, 2),
        "wall_time_ms": round((end_wall - start_wall) * 1000.0, 2)
    }

async def perform_db_stall_operation(delay_ms: float = 280.0) -> Dict[str, Any]:
    start_cpu = time.process_time()
    start_wall = time.perf_counter()

    await asyncio.sleep(delay_ms / 1000.0)

    end_cpu = time.process_time()
    end_wall = time.perf_counter()

    return {
        "status": "db_query_completed",
        "records_fetched": 42,
        "cpu_time_ms": round((end_cpu - start_cpu) * 1000.0, 2),
        "wall_time_ms": round((end_wall - start_wall) * 1000.0, 2)
    }
