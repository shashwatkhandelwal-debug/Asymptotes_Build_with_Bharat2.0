import json
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from backend.pow_engine import pow_engine
from backend.ledger import ledger
from backend.telemetry import telemetry

PROTECTED_PREFIXES = ("/api/verify-crypto",)

class AdaptivePoWMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, protected_prefixes=PROTECTED_PREFIXES):
        super().__init__(app)
        self.protected_prefixes = protected_prefixes

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        is_protected = any(path.startswith(prefix) for prefix in self.protected_prefixes)

        current_diff = pow_engine.current_difficulty_bits
        if not is_protected or current_diff == 0:
            return await call_next(request)

        client_ip = request.client.host if request.client else "127.0.0.1"
        
        pow_nonce = request.headers.get("X-PoW-Nonce")
        pow_challenge_id = request.headers.get("X-PoW-Challenge-ID")
        pow_timestamp_str = request.headers.get("X-PoW-Timestamp")
        pow_diff_str = request.headers.get("X-PoW-Difficulty")
        pow_salt = request.headers.get("X-PoW-Salt")
        pow_signature = request.headers.get("X-PoW-Signature")

        if not pow_nonce:
            try:
                if request.headers.get("content-type", "").startswith("application/json"):
                    body_bytes = await request.body()
                    if body_bytes:
                        body_json = json.loads(body_bytes.decode("utf-8"))
                        pow_nonce = body_json.get("pow_nonce")
                        pow_challenge_id = body_json.get("pow_challenge_id")
                        pow_timestamp_str = body_json.get("pow_timestamp")
                        pow_diff_str = body_json.get("pow_difficulty_bits")
                        pow_salt = body_json.get("pow_salt")
                        pow_signature = body_json.get("pow_signature")
                        
                        async def receive():
                            return {"type": "http.request", "body": body_bytes}
                        request._receive = receive
            except Exception:
                pass

        if not pow_nonce or not pow_challenge_id:
            challenge = pow_engine.generate_challenge(client_ip=client_ip)
            
            telemetry.record_request(
                endpoint=path,
                latency_ms=0.5,
                cpu_time_ms=0.05,
                client_ip=client_ip,
                pow_required=True,
                pow_difficulty=current_diff,
                pow_solved=False,
                status_code=428
            )

            ledger.append_entry(
                client_ip=client_ip,
                difficulty_bits=current_diff,
                challenge_id=challenge["challenge_id"],
                nonce="",
                status="CHALLENGE_ISSUED"
            )

            return JSONResponse(
                status_code=428,
                headers={
                    "X-PoW-Required": "true",
                    "X-PoW-Difficulty": str(current_diff),
                    "X-PoW-Challenge-ID": challenge["challenge_id"],
                    "X-PoW-Salt": challenge["salt"],
                    "X-PoW-Timestamp": str(challenge["timestamp"]),
                    "X-PoW-Signature": challenge["signature"]
                },
                content={
                    "error": "PoW Challenge Required",
                    "status": 428,
                    "message": "Adaptive defense is active due to detected complexity attack.",
                    "challenge": challenge
                }
            )

        try:
            pow_timestamp = int(pow_timestamp_str) if pow_timestamp_str else 0
            pow_diff = int(pow_diff_str) if pow_diff_str else current_diff
        except ValueError:
            pow_timestamp = 0
            pow_diff = current_diff

        is_valid, msg = pow_engine.verify_solution(
            challenge_id=pow_challenge_id,
            timestamp=pow_timestamp,
            difficulty_bits=pow_diff,
            salt=pow_salt or "",
            client_ip=client_ip,
            signature=pow_signature or "",
            nonce=pow_nonce
        )

        if not is_valid:
            ledger.append_entry(
                client_ip=client_ip,
                difficulty_bits=current_diff,
                challenge_id=pow_challenge_id,
                nonce=pow_nonce,
                status="FAILED_VERIFICATION"
            )
            return JSONResponse(
                status_code=403,
                content={
                    "error": "Forbidden",
                    "status": 403,
                    "message": f"PoW proof verification failed: {msg}"
                }
            )

        ledger.append_entry(
            client_ip=client_ip,
            difficulty_bits=current_diff,
            challenge_id=pow_challenge_id,
            nonce=pow_nonce,
            status="SOLVED"
        )

        response = await call_next(request)
        response.headers["X-PoW-Verified"] = "true"
        return response
