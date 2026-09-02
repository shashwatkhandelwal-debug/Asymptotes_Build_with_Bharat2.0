"""
Real-time instrumentation and telemetry collector.
Maintains a thread-safe rolling sliding window of request latencies, CPU time,
RPS, and endpoint concentration ratios for dynamic classification.
"""
import time
import threading
import psutil
from collections import deque
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import numpy as np
from backend.config import config

@dataclass
class RequestRecord:
    timestamp: float
    endpoint: str
    latency_ms: float
    cpu_time_ms: float
    client_ip: str
    pow_required: bool
    pow_difficulty: int
    pow_solved: bool
    status_code: int

class TelemetryCollector:
    def __init__(self, window_seconds: int = None):
        self.window_seconds = window_seconds or config.TELEMETRY_WINDOW_SECONDS
        self.records: deque[RequestRecord] = deque()
        self.recent_logs: deque[Dict[str, Any]] = deque(maxlen=50)
        self.last_cpu_percent = 12.0
        self._lock = threading.Lock()
        
        # Initialize psutil CPU reading
        try:
            psutil.cpu_percent(interval=None)
        except Exception:
            pass

    def record_request(
        self,
        endpoint: str,
        latency_ms: float,
        cpu_time_ms: float,
        client_ip: str = "127.0.0.1",
        pow_required: bool = False,
        pow_difficulty: int = 0,
        pow_solved: bool = False,
        status_code: int = 200
    ) -> RequestRecord:
        now = time.time()
        record = RequestRecord(
            timestamp=now,
            endpoint=endpoint,
            latency_ms=latency_ms,
            cpu_time_ms=cpu_time_ms,
            client_ip=client_ip,
            pow_required=pow_required,
            pow_difficulty=pow_difficulty,
            pow_solved=pow_solved,
            status_code=status_code
        )
        
        with self._lock:
            self.records.append(record)
            self.recent_logs.appendleft({
                "id": f"{int(now * 1000)}-{len(self.records)}",
                "timestamp": now,
                "endpoint": endpoint,
                "latency_ms": round(latency_ms, 2),
                "cpu_time_ms": round(cpu_time_ms, 2),
                "client_ip": client_ip,
                "pow_difficulty": pow_difficulty,
                "pow_solved": pow_solved,
                "status": status_code
            })
            self._prune_old_records_locked(now)

        return record

    def _prune_old_records_locked(self, current_time: float):
        cutoff = current_time - self.window_seconds
        while self.records and self.records[0].timestamp < cutoff:
            self.records.popleft()

    def flush_metrics(self):
        """
        Clears all rolling telemetry history and reset metrics.
        Used for instant demo resets between takes.
        """
        with self._lock:
            self.records.clear()
            self.recent_logs.clear()
            self.last_cpu_percent = 10.0

    def get_metrics(self) -> Dict[str, Any]:
        now = time.time()
        
        with self._lock:
            self._prune_old_records_locked(now)
            records_list = list(self.records)
            logs_snapshot = list(self.recent_logs)[:15]

        try:
            current_cpu_pct = psutil.cpu_percent(interval=None)
            if current_cpu_pct > 0:
                self.last_cpu_percent = current_cpu_pct
        except Exception:
            pass

        total_reqs = len(records_list)
        effective_window = max(1.0, self.window_seconds)
        rps = round(total_reqs / effective_window, 2)

        if total_reqs == 0:
            return {
                "timestamp": now,
                "total_requests_in_window": 0,
                "rps": 0.0,
                "crypto_rps": 0.0,
                "benign_rps": 0.0,
                "crypto_concentration": 0.0,
                "mean_latency_ms": 1.0,
                "p95_latency_ms": 1.0,
                "p99_latency_ms": 1.0,
                "max_latency_ms": 1.0,
                "mean_cpu_time_ms": 0.0,
                "system_cpu_percent": self.last_cpu_percent,
                "latency_slope": 0.0,
                "pow_challenges_issued": 0,
                "pow_challenges_solved": 0,
                "recent_logs": logs_snapshot
            }

        latencies = [r.latency_ms for r in records_list]
        cpu_times = [r.cpu_time_ms for r in records_list]
        crypto_reqs = [r for r in records_list if "/verify-crypto" in r.endpoint]
        benign_reqs = [r for r in records_list if "/verify-crypto" not in r.endpoint]

        crypto_rps = round(len(crypto_reqs) / effective_window, 2)
        benign_rps = round(len(benign_reqs) / effective_window, 2)
        crypto_concentration = round(len(crypto_reqs) / total_reqs, 4) if total_reqs > 0 else 0.0

        mean_latency = float(np.mean(latencies))
        p95_latency = float(np.percentile(latencies, 95))
        p99_latency = float(np.percentile(latencies, 99))
        max_latency = float(np.max(latencies))
        mean_cpu_time = float(np.mean(cpu_times))

        # Calculate latency slope (rate of latency degradation ms / sec)
        latency_slope = self._calculate_latency_slope(records_list)

        pow_issued = sum(1 for r in records_list if r.pow_required)
        pow_solved = sum(1 for r in records_list if r.pow_solved)

        return {
            "timestamp": now,
            "total_requests_in_window": total_reqs,
            "rps": rps,
            "crypto_rps": crypto_rps,
            "benign_rps": benign_rps,
            "crypto_concentration": crypto_concentration,
            "mean_latency_ms": round(mean_latency, 2),
            "p95_latency_ms": round(p95_latency, 2),
            "p99_latency_ms": round(p99_latency, 2),
            "max_latency_ms": round(max_latency, 2),
            "mean_cpu_time_ms": round(mean_cpu_time, 2),
            "system_cpu_percent": round(self.last_cpu_percent, 1),
            "latency_slope": round(latency_slope, 3),
            "pow_challenges_issued": pow_issued,
            "pow_challenges_solved": pow_solved,
            "recent_logs": logs_snapshot
        }

    def _calculate_latency_slope(self, records: List[RequestRecord]) -> float:
        """
        Fits a linear trend line (least squares) over timestamps and latencies
        to measure degradation slope in ms / second.
        """
        if len(records) < 5:
            return 0.0

        bins = {}
        for r in records:
            bucket = round(r.timestamp * 2) / 2.0  # 0.5s bucket
            bins.setdefault(bucket, []).append(r.latency_ms)

        if len(bins) < 3:
            return 0.0

        sorted_times = sorted(bins.keys())
        x = np.array(sorted_times) - sorted_times[0]  # relative seconds
        y = np.array([np.mean(bins[t]) for t in sorted_times])

        if np.std(x) == 0:
            return 0.0
        slope, _ = np.polyfit(x, y, 1)
        return float(slope)

telemetry = TelemetryCollector()
