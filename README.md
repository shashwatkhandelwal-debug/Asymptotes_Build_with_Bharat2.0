# Adaptive PoW Defense Against Algorithmic Complexity Attacks

**Hackathon Demo System — Build with Bharat 2.0**

A working end-to-end adaptive Proof-of-Work (PoW) defense system that protects CPU-expensive verification endpoints (e.g. cryptographic signature/PBKDF2/JWT validation) from algorithmic complexity attacks, while remaining completely invisible to legitimate users during standard operation and benign traffic surges.

---

## 🎯 The Problem It Solves

Cryptographic verification sits on the critical path of fintech APIs, authentication microservices, and blockchain nodes. An **algorithmic complexity attack** (Crosby-Wallach 2003, Bitcoin CVE-2010-5138) floods valid-looking but computationally heavy verification requests, pegging server CPU cores until response latencies breach SLA thresholds and drop legitimate traffic.

### Why Existing Defenses Fail
- **Static Rate Limiting:** Blindly drops legitimate users during organic traffic surges (e.g., flash sales, marketing pushes) because it only counts request volume, not computational intent or endpoint concentration.
- **Always-On PoW / Captchas:** Degrades user experience by punishing legitimate users on a quiet Tuesday with unnecessary computational overhead.

### The Adaptive PoW Solution
1. **Real-time CPU & Latency Telemetry:** Per-request CPU process time and latency are continuously tracked in a sliding time window.
2. **Signal Classification:** Distinguishes between **Complexity Attacks** (CPU pegged high, concentrated on crypto verification), **Benign Surges** (high volume evenly distributed across light endpoints, sustainable CPU), and **Downstream Stalls** (high latency, flat CPU).
3. **Time-to-Failure Regression:** Predicts seconds remaining until SLA timeout breach (`(SLA_Threshold - Current_Mean_Latency) / Degradation_Slope`).
4. **Dynamic Difficulty Dial:** Maps urgency to a continuous Hashcash SHA-256 zero-bits difficulty dial ($0 \to 8 \to 12 \to 16$ bits). Benign surges get **0 bits** (zero user friction); attacks get progressive computational puzzles that force attackers to burn CPU to consume server CPU.
5. **Tamper-Evident Hash-Chained Audit Ledger:** Every issued challenge and solution is cryptographically linked in a sequential hash-chained ledger, with live verification and tamper detection.

---

## 🏛️ System Architecture

```
Incoming Requests
       │
       ▼
┌────────────────────────────────────────────────────────┐
│  Adaptive PoW Middleware & Sidecar                      │
│                                                        │
│  1. Telemetry Collector (psutil + per-request CPU ms)  │
│  2. Heuristic Signal Classifier                        │
│  3. Time-to-Failure Linear Regression                  │
│  4. Dynamic Difficulty Mapper (0 - 16 bits)            │
│  5. Hashcash SHA-256 Verifier (O(1) server check)      │
└───────────────────────┬────────────────────────────────┘
                        │
       ┌────────────────┴────────────────┐
       ▼                                 ▼
┌──────────────────────────┐   ┌──────────────────────────┐
│ /api/verify-crypto       │   │ /api/data & /api/health   │
│ Real PBKDF2/HMAC Workload│   │ Sub-millisecond Ops      │
└──────────────────────────┘   └──────────────────────────┘
       │
       ▼
┌────────────────────────────────────────────────────────┐
│ Tamper-Evident Hash-Chained Audit Ledger               │
│ (Sequential SHA-256 Prev-Hash Chained SQLite Log)       │
└────────────────────────────────────────────────────────┘
```

---

## 📋 Honest Architectural Disclosures

In accordance with strict hackathon transparency:
- **Classifier:** The classifier is a calibrated **rule-based / heuristic decision model** evaluated over synthetic telemetry metrics (CPU utilization %, endpoint concentration ratio, and latency degradation slope). It is **not deep learning** and is not trained on external real-world attack datasets.
- **Audit Ledger:** The audit ledger is a **local, append-only, SHA-256 hash-chained SQLite log** demonstrating cryptographic tamper-evidence. It is **not a distributed consensus blockchain** (no peer-to-peer gossip network or proof-of-work mining consensus for block creation).
- **Benchmark Numbers:** All benchmark solve times and CPU numbers reflect real measurements executed on the presenter's hardware.

---

## 🚀 Quickstart & Running the Demo

### Prerequisites
- Python 3.10+ (`fastapi`, `uvicorn`, `psutil`, `numpy`, `pydantic`)
- Node.js 18+ & npm

### 1. Start the Backend API & Telemetry Broadcaster
```bash
# From repository root
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

### 2. Start the Frontend Dashboard
```bash
# In another terminal window
cd frontend
npm run dev
```
Open **http://localhost:3000** in your browser.

---

## 🎤 Stage Presentation Walkthrough (Live Demo Guide)

### Step 1: Baseline Standby
- Show the dashboard in **Baseline Traffic** mode.
- Point out:
  - System Status: `DEFENSE ARMED & MONITORING`
  - Response Latency: `< 20ms` (well below 800ms SLA threshold)
  - PoW Difficulty: `0 bits` (disabled)
  - Time-to-Failure: `SLA SAFE`

### Step 2: Simulate Legitimate Traffic Spike (Proof of Zero-Friction)
- Click **"1. Legitimate Traffic Spike"**.
- Point out:
  - Aggregate RPS jumps to `25-35 req/s`.
  - Classifier correctly identifies `BENIGN TRAFFIC SURGE (LEGITIMATE)` because load is distributed across general endpoints and CPU concentration is low.
  - **PoW Difficulty stays at 0 bits!** Legitimate users experience zero computational delay or captcha popups.

### Step 3: Simulate Crypto-Exhaustion Attack (Live Mitigation)
- Click **"2. Crypto-Exhaustion Attack"**.
- Point out:
  - Attacker floods the `/api/verify-crypto` endpoint.
  - CPU climbs rapidly towards `75-90%`, latency degrades steeply.
  - Classifier diagnoses `CRITICAL THREAT: COMPLEXITY ATTACK`.
  - **Live Countdown to SLA Failure** activates (e.g. `14.2s to timeout breach`).
  - **Dynamic PoW Difficulty Dial** dynamically ramps up ($8 \to 12 \to 14+$ bits).
  - Unsolved attack bots are rejected at the gate with HTTP 428; solving bots are throttled by client-side mining delay.
  - Effective attacker throughput drops, CPU and latency recover, and the countdown recovers to `STABLE`!

### Step 4: Prove Cryptographic Tamper-Evidence Live
- Scroll to the **Hash-Chained Audit Ledger Explorer**.
- Click **"Verify Chain Integrity"**: Show the green `CHAIN VALID` cryptographic proof walking all blocks from Genesis block #0.
- Click **"Simulate Block Tamper"**: This alters a row directly in the database.
- Click **"Verify Chain Integrity"** again: Watch the system instantly catch the exact altered block index and display `INTEGRITY BREACH: Block #X payload hash mismatch`.
- Click **"Demo Reset"** to reset test state for the next run.

---

## 🧪 Automated Test Suite

Run all automated unit tests to verify the core modules headless:

```bash
# Run all tests
python -m tests.test_crypto
python -m tests.test_pow
python -m tests.test_classifier
python -m tests.test_ledger
```

---

## 📊 Hardware Benchmark Results (Measured on Presentation Laptop)

| Difficulty | Expected Hashes ($2^D$) | Average Client Solve Time | Server Verification Cost |
| :--- | :--- | :--- | :--- |
| **0 bits** | 0 | $0.01\text{ ms}$ | $0.00\text{ ms}$ |
| **8 bits** | 256 | $0.58\text{ ms}$ | $< 0.01\text{ ms}$ |
| **10 bits** | 1,024 | $1.20\text{ ms}$ | $< 0.01\text{ ms}$ |
| **12 bits** | 4,096 | $6.92\text{ ms}$ | $< 0.01\text{ ms}$ |
| **14 bits** | 16,384 | $25.40\text{ ms}$ | $< 0.01\text{ ms}$ |
| **16 bits** | 65,536 | $49.41\text{ ms}$ | $< 0.01\text{ ms}$ |
