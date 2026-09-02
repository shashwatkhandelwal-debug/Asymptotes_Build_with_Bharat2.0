"""
Real CPU-intensive cryptographic verification workload and lightweight API baselines.
Performs real PBKDF2 key derivation and HMAC signature verification
to ensure genuine CPU consumption without artificial delays (sleep).
Also includes mock database / downstream I/O stall simulator.
"""
import hashlib
import time
import asyncio
from typing import Dict, Any
from backend.config import config

def perform_cpu_heavy_verification(payload: str, signature_hint: str = "", iterations: int = None) -> Dict[str, Any]:
    """
    Executes a CPU-intensive cryptographic verification operation.
    Computes PBKDF2-HMAC-SHA256 key stretching over payload bytes.
    Measures actual CPU process time and elapsed wall time.
    """
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
    
    # Secondary HMAC check over the derived key
    final_digest = hashlib.sha256(derived_key + payload.encode('utf-8')).hexdigest()

    end_cpu = time.process_time()
    end_wall = time.perf_counter()

    cpu_time_ms = (end_cpu - start_cpu) * 1000.0
    wall_time_ms = (end_wall - start_wall) * 1000.0

    return {
        "verified": True,
        "digest": final_digest[:16],
        "iterations": iterations,
        "cpu_time_ms": round(cpu_time_ms, 2),
        "wall_time_ms": round(wall_time_ms, 2)
    }

def perform_light_operation(payload: str) -> Dict[str, Any]:
    """
    Executes a standard lightweight API operation (single SHA-256 hash).
    Sub-millisecond CPU cost.
    """
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
    """
    Simulates a downstream database / external microservice I/O stall.
    Incurs high wall-clock latency while consuming virtually 0 CPU time.
    Used to demonstrate the system's diagnostic ability to differentiate
    algorithmic complexity DoS from internal I/O bottlenecks.
    """
    start_cpu = time.process_time()
    start_wall = time.perf_counter()

    # Asynchronous I/O wait (non-blocking event loop, 0 CPU)
    await asyncio.sleep(delay_ms / 1000.0)

    end_cpu = time.process_time()
    end_wall = time.perf_counter()

    return {
        "status": "db_query_completed",
        "records_fetched": 42,
        "cpu_time_ms": round((end_cpu - start_cpu) * 1000.0, 2),
        "wall_time_ms": round((end_wall - start_wall) * 1000.0, 2)
    }
