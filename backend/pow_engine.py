import hashlib
import hmac
import time
import uuid
from typing import Dict, Any, Tuple, Optional
from backend.config import config
from backend.classifier import TrafficClassification

class PoWEngine:
    def __init__(self):
        self.secret_key = config.POW_SECRET_KEY.encode('utf-8')
        self.current_difficulty_bits: int = 0
        self.last_adjustment_time: float = time.time()
        self.min_bits = config.MIN_DIFFICULTY_BITS
        self.max_bits = config.MAX_DIFFICULTY_BITS

    def calculate_difficulty(self, classification: str, urgency_score: float) -> int:
        now = time.time()

        if classification != TrafficClassification.COMPLEXITY_ATTACK.value:
            if self.current_difficulty_bits > 0:
                if now - self.last_adjustment_time >= 1.0:
                    self.current_difficulty_bits = max(0, self.current_difficulty_bits - 2)
                    self.last_adjustment_time = now
            return self.current_difficulty_bits

        target_bits = int(self.min_bits + round(urgency_score * (self.max_bits - self.min_bits)))
        target_bits = max(self.min_bits, min(self.max_bits, target_bits))

        if target_bits > self.current_difficulty_bits:
            self.current_difficulty_bits = target_bits
            self.last_adjustment_time = now
        elif target_bits < self.current_difficulty_bits:
            if now - self.last_adjustment_time >= 1.5:
                self.current_difficulty_bits = max(target_bits, self.current_difficulty_bits - 1)
                self.last_adjustment_time = now

        return self.current_difficulty_bits

    def generate_challenge(self, client_ip: str = "127.0.0.1", forced_difficulty: Optional[int] = None) -> Dict[str, Any]:
        difficulty = forced_difficulty if forced_difficulty is not None else self.current_difficulty_bits
        challenge_id = uuid.uuid4().hex
        timestamp = int(time.time())
        salt = uuid.uuid4().hex[:12]

        payload = f"{challenge_id}:{timestamp}:{difficulty}:{salt}:{client_ip}"
        signature = hmac.new(self.secret_key, payload.encode('utf-8'), hashlib.sha256).hexdigest()

        return {
            "challenge_id": challenge_id,
            "timestamp": timestamp,
            "difficulty_bits": difficulty,
            "expected_hashes": 2 ** difficulty if difficulty > 0 else 0,
            "salt": salt,
            "client_ip": client_ip,
            "signature": signature
        }

    def verify_solution(
        self,
        challenge_id: str,
        timestamp: int,
        difficulty_bits: int,
        salt: str,
        client_ip: str,
        signature: str,
        nonce: str
    ) -> Tuple[bool, str]:
        now = int(time.time())
        if now - timestamp > config.POW_EXPIRY_SECONDS:
            return False, "Challenge has expired"

        expected_payload = f"{challenge_id}:{timestamp}:{difficulty_bits}:{salt}:{client_ip}"
        expected_sig = hmac.new(self.secret_key, expected_payload.encode('utf-8'), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected_sig):
            return False, "Invalid challenge signature or tampered parameters"

        if difficulty_bits == 0:
            return True, "Valid (Difficulty 0)"

        candidate = f"{challenge_id}:{salt}:{nonce}".encode('utf-8')
        digest = hashlib.sha256(candidate).digest()

        zero_bits = self._count_leading_zero_bits(digest)
        if zero_bits < difficulty_bits:
            return False, f"Insufficient PoW: found {zero_bits} zero bits, required {difficulty_bits}"

        return True, "Valid PoW Solution"

    @staticmethod
    def _count_leading_zero_bits(digest_bytes: bytes) -> int:
        count = 0
        for byte in digest_bytes:
            if byte == 0:
                count += 8
            else:
                count += (8 - byte.bit_length())
                break
        return count

    @staticmethod
    def solve_challenge(challenge: Dict[str, Any], max_attempts: int = 2_000_000) -> Tuple[Optional[str], int, float]:
        challenge_id = challenge["challenge_id"]
        salt = challenge["salt"]
        difficulty_bits = challenge["difficulty_bits"]

        if difficulty_bits == 0:
            return "0", 1, 0.01

        start = time.perf_counter()
        prefix = f"{challenge_id}:{salt}:"

        for nonce_int in range(max_attempts):
            nonce_str = str(nonce_int)
            candidate = f"{prefix}{nonce_str}".encode('utf-8')
            digest = hashlib.sha256(candidate).digest()

            if PoWEngine._count_leading_zero_bits(digest) >= difficulty_bits:
                elapsed_ms = (time.perf_counter() - start) * 1000.0
                return nonce_str, nonce_int + 1, round(elapsed_ms, 2)

        elapsed_ms = (time.perf_counter() - start) * 1000.0
        return None, max_attempts, round(elapsed_ms, 2)

pow_engine = PoWEngine()
