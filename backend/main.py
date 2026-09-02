"""
FastAPI Main Application.
Provides REST APIs, WebSocket real-time telemetry streaming,
and stage demo control endpoints for the Adaptive PoW Defense System.
Also serves the built single-page frontend dashboard directly.
"""
import asyncio
import json
import time
import os
from contextlib import asynccontextmanager
from typing import Dict, Any, Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, Response, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from backend.config import config
from backend.crypto_endpoint import perform_cpu_heavy_verification, perform_light_operation
from backend.telemetry import telemetry
from backend.classifier import classifier, TrafficClassification
from backend.time_to_failure import ttf_predictor
from backend.pow_engine import pow_engine, PoWEngine
from backend.ledger import ledger
from backend.simulator import simulator

# WebSockets Connection Manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        if not self.active_connections:
            return
        payload = json.dumps(message)
        dead_connections = []
        for connection in self.active_connections:
            try:
                await connection.send_text(payload)
            except Exception:
                dead_connections.append(connection)
        for dead in dead_connections:
            self.disconnect(dead)

manager = ConnectionManager()

# Background Telemetry & Classification Loop
async def telemetry_broadcast_loop():
    while True:
        try:
            metrics = telemetry.get_metrics()
            classification_res = classifier.classify(metrics)
            classification = classification_res["classification"].value
            
            # Predict Time to Failure & Urgency
            ttf_res = ttf_predictor.predict(metrics, classification_res)
            urgency = ttf_res.get("urgency_score", 0.0)

            # Update PoW Difficulty Dial
            active_difficulty = pow_engine.calculate_difficulty(classification, urgency)

            # Check Ledger Integrity Status
            ledger_status = ledger.verify_chain()

            # Package State for Real-Time Streaming
            state_payload = {
                "type": "TELEMETRY_UPDATE",
                "timestamp": time.time(),
                "metrics": metrics,
                "classification": classification_res,
                "time_to_failure": ttf_res,
                "pow_state": {
                    "difficulty_bits": active_difficulty,
                    "expected_hashes": 2 ** active_difficulty if active_difficulty > 0 else 0,
                    "is_active": active_difficulty > 0,
                    "min_bits": config.MIN_DIFFICULTY_BITS,
                    "max_bits": config.MAX_DIFFICULTY_BITS
                },
                "ledger_status": {
                    "is_valid": ledger_status["is_valid"],
                    "total_blocks": ledger_status["total_blocks"],
                    "tampered_block_index": ledger_status.get("tampered_block_index"),
                    "message": ledger_status["message"]
                },
                "simulator": {
                    "mode": simulator.mode,
                    "is_running": simulator.is_running,
                    "stats": simulator.stats
                }
            }

            await manager.broadcast(state_payload)
        except asyncio.CancelledError:
            break
        except Exception as e:
            pass

        await asyncio.sleep(config.METRICS_TICK_INTERVAL_SEC)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Start simulator and telemetry broadcaster
    simulator.start()
    broadcast_task = asyncio.create_task(telemetry_broadcast_loop())
    yield
    # Shutdown
    broadcast_task.cancel()
    simulator.stop()

app = FastAPI(
    title="Adaptive PoW Defense API",
    description="Adaptive Proof-of-Work Defense against Complexity/DoS Attacks",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------- Request Models -----------------
class CryptoVerifyRequest(BaseModel):
    payload: str = "crypto_transaction_token_sample"
    signature_hint: Optional[str] = ""
    pow_challenge_id: Optional[str] = None
    pow_timestamp: Optional[int] = None
    pow_difficulty_bits: Optional[int] = None
    pow_salt: Optional[str] = None
    pow_signature: Optional[str] = None
    pow_nonce: Optional[str] = None

class ModeRequest(BaseModel):
    mode: str  # IDLE, BENIGN_SURGE, COMPLEXITY_ATTACK

class TamperRequest(BaseModel):
    block_index: int = 1
    new_status: str = "UNAUTHORIZED_ALTERATION"

# ----------------- API Endpoints -----------------

@app.get("/api/health")
async def health_check():
    res = perform_light_operation("health_check")
    return {"status": "ok", "service": "Adaptive PoW Defense", "wall_time_ms": res["wall_time_ms"]}

@app.get("/api/data")
async def get_data():
    res = perform_light_operation("get_data_payload")
    return {
        "status": "success",
        "data": {"account_id": "ACC-9921", "balance": 15420.50, "currency": "USD"},
        "cpu_time_ms": res["cpu_time_ms"]
    }

@app.post("/api/verify-crypto")
async def verify_crypto(req: CryptoVerifyRequest, request: Request):
    client_ip = request.client.host if request.client else "127.0.0.1"
    current_diff = pow_engine.current_difficulty_bits

    # If PoW is currently required
    if current_diff > 0:
        if not req.pow_nonce or not req.pow_challenge_id:
            # Issue challenge response (HTTP 428 Precondition Required)
            challenge = pow_engine.generate_challenge(client_ip=client_ip)
            return JSONResponse(
                status_code=status.HTTP_428_PRECONDITION_REQUIRED,
                content={
                    "error": "PoW Challenge Required",
                    "detail": "Adaptive defense is active due to detected complexity attack.",
                    "challenge": challenge
                }
            )

        # Validate submitted PoW solution
        is_valid, msg = pow_engine.verify_solution(
            challenge_id=req.pow_challenge_id,
            timestamp=req.pow_timestamp or 0,
            difficulty_bits=req.pow_difficulty_bits or current_diff,
            salt=req.pow_salt or "",
            client_ip=client_ip,
            signature=req.pow_signature or "",
            nonce=req.pow_nonce
        )

        if not is_valid:
            ledger.append_entry(
                client_ip=client_ip,
                difficulty_bits=current_diff,
                challenge_id=req.pow_challenge_id,
                nonce=req.pow_nonce,
                status="FAILED_VERIFICATION"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"PoW verification failed: {msg}"
            )

        # PoW is valid! Log to ledger
        ledger.append_entry(
            client_ip=client_ip,
            difficulty_bits=current_diff,
            challenge_id=req.pow_challenge_id,
            nonce=req.pow_nonce,
            status="SOLVED"
        )

    # Execute heavy cryptographic verification
    start = time.perf_counter()
    result = await asyncio.to_thread(perform_cpu_heavy_verification, req.payload)
    elapsed_ms = (time.perf_counter() - start) * 1000.0

    telemetry.record_request(
        endpoint="/api/verify-crypto",
        latency_ms=elapsed_ms,
        cpu_time_ms=result["cpu_time_ms"],
        client_ip=client_ip,
        pow_required=current_diff > 0,
        pow_difficulty=current_diff,
        pow_solved=current_diff > 0,
        status_code=200
    )

    return {
        "status": "verified",
        "digest": result["digest"],
        "iterations": result["iterations"],
        "cpu_time_ms": result["cpu_time_ms"],
        "wall_time_ms": round(elapsed_ms, 2),
        "pow_solved": current_diff > 0
    }

@app.get("/api/pow/challenge")
async def get_pow_challenge(request: Request):
    client_ip = request.client.host if request.client else "127.0.0.1"
    return pow_engine.generate_challenge(client_ip=client_ip)

@app.get("/api/telemetry/snapshot")
async def get_telemetry_snapshot():
    metrics = telemetry.get_metrics()
    classification_res = classifier.classify(metrics)
    ttf_res = ttf_predictor.predict(metrics, classification_res)
    ledger_status = ledger.verify_chain()
    return {
        "metrics": metrics,
        "classification": classification_res,
        "time_to_failure": ttf_res,
        "pow_difficulty_bits": pow_engine.current_difficulty_bits,
        "ledger_status": ledger_status
    }

# ----------------- Ledger Endpoints -----------------

@app.get("/api/ledger/blocks")
async def get_ledger_blocks(limit: int = 50, offset: int = 0):
    blocks = ledger.get_blocks(limit=limit, offset=offset)
    verification = ledger.verify_chain()
    return {
        "blocks": blocks,
        "verification": verification
    }

@app.get("/api/ledger/verify")
async def verify_ledger_chain():
    return ledger.verify_chain()

@app.post("/api/ledger/tamper")
async def tamper_ledger(req: TamperRequest):
    result = ledger.tamper_block_for_demo(block_index=req.block_index, new_status=req.new_status)
    return result

@app.post("/api/ledger/reset")
async def reset_ledger():
    ledger.reset_demo_ledger()
    return {"status": "success", "message": "Demo ledger environment reset to genesis state."}

# ----------------- Simulator Control Endpoints -----------------

@app.post("/api/simulator/mode")
async def set_simulator_mode(req: ModeRequest):
    simulator.set_mode(req.mode)
    return {
        "status": "success",
        "current_mode": simulator.mode,
        "message": f"Simulator mode updated to {simulator.mode}"
    }

@app.get("/api/simulator/status")
async def get_simulator_status():
    return {
        "mode": simulator.mode,
        "is_running": simulator.is_running,
        "stats": simulator.stats
    }

# ----------------- WebSocket Telemetry Stream -----------------

@app.websocket("/ws/telemetry")
async def websocket_telemetry_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                if msg.get("action") == "SET_MODE":
                    simulator.set_mode(msg.get("mode", "IDLE"))
            except Exception:
                pass
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception:
        manager.disconnect(websocket)

# ----------------- Static Frontend Hosting -----------------
dist_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "dist")
if os.path.exists(dist_dir):
    app.mount("/assets", StaticFiles(directory=os.path.join(dist_dir, "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        if full_path.startswith("api/") or full_path.startswith("ws/"):
            raise HTTPException(status_code=404, detail="Not found")
        index_file = os.path.join(dist_dir, "index.html")
        if os.path.exists(index_file):
            return FileResponse(index_file)
        return {"error": "Frontend build not found"}
