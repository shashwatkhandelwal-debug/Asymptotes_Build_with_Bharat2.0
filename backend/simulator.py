import asyncio
import time
import random
import uuid
from typing import Dict, Any, Optional
from backend.telemetry import telemetry
from backend.pow_engine import pow_engine, PoWEngine
from backend.crypto_endpoint import perform_cpu_heavy_verification, perform_light_operation, perform_db_stall_operation
from backend.ledger import ledger

class TrafficSimulator:
    def __init__(self):
        self.mode: str = "IDLE"
        self.is_running: bool = False
        self.task: Optional[asyncio.Task] = None
        self.stats = {
            "total_simulated": 0,
            "blocked_attack_reqs": 0,
            "solved_reqs": 0,
            "current_mode": "IDLE"
        }

    def start(self):
        if not self.is_running:
            self.is_running = True
            self.task = asyncio.create_task(self._simulation_loop())

    def stop(self):
        self.is_running = False
        self.mode = "IDLE"
        if self.task:
            self.task.cancel()
            self.task = None

    def reset(self):
        self.set_mode("IDLE")
        self.stats = {
            "total_simulated": 0,
            "blocked_attack_reqs": 0,
            "solved_reqs": 0,
            "current_mode": "IDLE"
        }
        pow_engine.current_difficulty_bits = 0
        telemetry.flush_metrics()
        ledger.reset_demo_ledger()

    def set_mode(self, mode: str):
        mode = mode.upper()
        if mode in ("IDLE", "BENIGN_SURGE", "COMPLEXITY_ATTACK", "DOWNSTREAM_STALL"):
            self.mode = mode
            self.stats["current_mode"] = mode

    async def _simulation_loop(self):
        while self.is_running:
            try:
                if self.mode == "IDLE":
                    await self._simulate_normal_tick()
                    await asyncio.sleep(0.4)

                elif self.mode == "BENIGN_SURGE":
                    tasks = [self._simulate_surge_request() for _ in range(random.randint(8, 14))]
                    await asyncio.gather(*tasks)
                    await asyncio.sleep(0.3)

                elif self.mode == "COMPLEXITY_ATTACK":
                    tasks = [self._simulate_attack_request() for _ in range(random.randint(10, 18))]
                    await asyncio.gather(*tasks)
                    await asyncio.sleep(0.2)

                elif self.mode == "DOWNSTREAM_STALL":
                    tasks = [self._simulate_db_stall_request() for _ in range(random.randint(4, 8))]
                    await asyncio.gather(*tasks)
                    await asyncio.sleep(0.3)

            except asyncio.CancelledError:
                break
            except Exception:
                await asyncio.sleep(0.5)

    async def _simulate_normal_tick(self):
        endpoint = random.choice(["/api/data", "/api/health", "/api/data", "/api/verify-crypto"])
        client_ip = f"192.168.1.{random.randint(10, 50)}"

        if endpoint == "/api/verify-crypto":
            start = time.perf_counter()
            res = await asyncio.to_thread(perform_cpu_heavy_verification, "normal_token", iterations=8000)
            elapsed_ms = (time.perf_counter() - start) * 1000.0
            telemetry.record_request(
                endpoint=endpoint,
                latency_ms=elapsed_ms,
                cpu_time_ms=res["cpu_time_ms"],
                client_ip=client_ip,
                pow_required=False,
                pow_difficulty=0,
                pow_solved=False,
                status_code=200
            )
        else:
            res = perform_light_operation("normal_payload")
            telemetry.record_request(
                endpoint=endpoint,
                latency_ms=res["wall_time_ms"],
                cpu_time_ms=res["cpu_time_ms"],
                client_ip=client_ip,
                pow_required=False,
                pow_difficulty=0,
                pow_solved=False,
                status_code=200
            )
        self.stats["total_simulated"] += 1

    async def _simulate_surge_request(self):
        is_crypto = random.random() < 0.15
        endpoint = "/api/verify-crypto" if is_crypto else random.choice(["/api/data", "/api/health", "/api/status", "/api/feed"])
        client_ip = f"10.0.{random.randint(1, 20)}.{random.randint(1, 250)}"

        if is_crypto:
            start = time.perf_counter()
            res = await asyncio.to_thread(perform_cpu_heavy_verification, "surge_crypto_check", iterations=10000)
            elapsed_ms = (time.perf_counter() - start) * 1000.0
            telemetry.record_request(
                endpoint=endpoint,
                latency_ms=elapsed_ms,
                cpu_time_ms=res["cpu_time_ms"],
                client_ip=client_ip,
                pow_required=False,
                pow_difficulty=0,
                pow_solved=False,
                status_code=200
            )
        else:
            res = perform_light_operation("surge_light_payload")
            telemetry.record_request(
                endpoint=endpoint,
                latency_ms=res["wall_time_ms"] + random.uniform(0.5, 3.0),
                cpu_time_ms=res["cpu_time_ms"],
                client_ip=client_ip,
                pow_required=False,
                pow_difficulty=0,
                pow_solved=False,
                status_code=200
            )
        self.stats["total_simulated"] += 1

    async def _simulate_attack_request(self):
        endpoint = "/api/verify-crypto"
        attacker_ip = f"45.33.{random.randint(10, 99)}.{random.randint(1, 254)}"
        current_diff = pow_engine.current_difficulty_bits

        if current_diff == 0:
            start = time.perf_counter()
            res = await asyncio.to_thread(perform_cpu_heavy_verification, f"attack_sig_{uuid.uuid4().hex}")
            elapsed_ms = (time.perf_counter() - start) * 1000.0
            telemetry.record_request(
                endpoint=endpoint,
                latency_ms=elapsed_ms,
                cpu_time_ms=res["cpu_time_ms"],
                client_ip=attacker_ip,
                pow_required=False,
                pow_difficulty=0,
                pow_solved=False,
                status_code=200
            )
        else:
            challenge = pow_engine.generate_challenge(client_ip=attacker_ip)
            will_attempt_solve = (random.random() < 0.40)

            if not will_attempt_solve:
                telemetry.record_request(
                    endpoint=endpoint,
                    latency_ms=random.uniform(0.5, 2.0),
                    cpu_time_ms=0.1,
                    client_ip=attacker_ip,
                    pow_required=True,
                    pow_difficulty=current_diff,
                    pow_solved=False,
                    status_code=428
                )
                self.stats["blocked_attack_reqs"] += 1
                ledger.append_entry(
                    client_ip=attacker_ip,
                    difficulty_bits=current_diff,
                    challenge_id=challenge["challenge_id"],
                    nonce="",
                    status="DROPPED_UNSOLVED"
                )
            else:
                nonce, attempts, solve_time_ms = await asyncio.to_thread(
                    PoWEngine.solve_challenge, challenge, max_attempts=500_000
                )

                if nonce:
                    res = await asyncio.to_thread(perform_cpu_heavy_verification, "solved_crypto_check", iterations=12000)
                    total_latency = solve_time_ms + res["wall_time_ms"]
                    telemetry.record_request(
                        endpoint=endpoint,
                        latency_ms=total_latency,
                        cpu_time_ms=res["cpu_time_ms"],
                        client_ip=attacker_ip,
                        pow_required=True,
                        pow_difficulty=current_diff,
                        pow_solved=True,
                        status_code=200
                    )
                    self.stats["solved_reqs"] += 1
                    ledger.append_entry(
                        client_ip=attacker_ip,
                        difficulty_bits=current_diff,
                        challenge_id=challenge["challenge_id"],
                        nonce=nonce,
                        status="SOLVED"
                    )
                else:
                    telemetry.record_request(
                        endpoint=endpoint,
                        latency_ms=solve_time_ms,
                        cpu_time_ms=0.2,
                        client_ip=attacker_ip,
                        pow_required=True,
                        pow_difficulty=current_diff,
                        pow_solved=False,
                        status_code=408
                    )
                    self.stats["blocked_attack_reqs"] += 1

        self.stats["total_simulated"] += 1

    async def _simulate_db_stall_request(self):
        endpoint = "/api/data/db-query"
        client_ip = f"172.16.{random.randint(1, 10)}.{random.randint(1, 200)}"
        res = await perform_db_stall_operation(delay_ms=random.uniform(220.0, 320.0))
        telemetry.record_request(
            endpoint=endpoint,
            latency_ms=res["wall_time_ms"],
            cpu_time_ms=res["cpu_time_ms"],
            client_ip=client_ip,
            pow_required=False,
            pow_difficulty=0,
            pow_solved=False,
            status_code=200
        )
        self.stats["total_simulated"] += 1

simulator = TrafficSimulator()
