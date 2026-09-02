# Adaptive PoW Defense Against Algorithmic Complexity Attacks

**Team Asymptotes — Build with Bharat 2.0**

[Live Demo](https://asymptotes-defnse.onrender.com/) 

A working, deployed system that defends CPU-expensive verification endpoints & signature checks, PBKDF2 hashing, JWT validation against algorithmic complexity attacks, while staying completely invisible to legitimate users during normal traffic and genuine surges.

---

## The problem

Most API defenses count *requests*. They don't account for how expensive each request actually is to process. That gap matters a lot on endpoints that do real cryptographic work especially for the kind that sit on the critical path of payment authentication and identity verification.

This is a known attack class, not a hypothetical one: Crosby and Wallach described it back in 2003, and Bitcoin shipped a real version of it as CVE-2010-5138. The idea is to send requests that look legitimate but cost the server far more CPU than a normal one, and aim enough of them at one expensive endpoint to peg every core. A rate limiter counting requests-per-second never sees it coming, because the request *volume* can look completely ordinary.

**Why this matters for India specifically:** UPI and digital payment platforms already see extreme, entirely legitimate traffic spikes during festival sales, salary-day surges, marketing pushes, etc. That's exactly the kind of pattern an attacker would want to hide inside. A static rate limiter can't tell "real Diwali sale traffic hitting our payment auth" apart from "someone deliberately flooding our signature verification endpoint," and it will either miss the attack or throttle real customers trying to pay. Our system is built to tell the two apart, in real time, without a human in the loop.

## Why the usual fixes fall short

- **Static rate limiting** blocks legitimate users the moment traffic gets heavy, because it only knows volume, not which endpoint is being hit or how much CPU each request actually costs.
- **Always-on PoW or CAPTCHA** solves the attack problem by punishing everyone, all the time, including on a completely ordinary Tuesday. That's a bad trade for user experience.

We wanted something that does nothing until it actually needs to, and then responds proportionally to how serious the threat is.

## How it works

1. **Telemetry.** Every request's CPU time and latency get tracked continuously in a sliding window.
2. **Classification.** A rule-based classifier looks at the shape of what's happening and sorts it into one of three buckets: a complexity attack (CPU pegged, concentrated on one expensive endpoint), a benign surge (high volume, spread across normal endpoints, CPU still sustainable), or a downstream stall (latency's bad but CPU is flat so something else, like a slow database, is actually the problem, and PoW would do nothing to help).
3. **Time-to-failure prediction.** When it looks like an attack, we run a simple linear regression on the latency trend to estimate how many seconds remain until the SLA threshold breaches: `(SLA_Threshold − Current_Mean_Latency) / Degradation_Slope`.
4. **Adaptive difficulty.** Based on that urgency, a Hashcash-style SHA-256 proof-of-work dial turns — from 0 bits (no friction, used for benign traffic) up to 16 bits for a confirmed attack. The attacker now has to burn real CPU solving puzzles just to get a request through, which is the whole point: make the attack expensive for the attacker instead of just expensive for us.
5. **Tamper-evident logging.** Every challenge issued and every verdict made gets written into a SHA-256 hash-chained log. If a record is edited after the fact, re-verifying the chain immediately shows which entry broke.

```
Incoming Requests
       │
       ▼
┌────────────────────────────────────────────────────────┐
│  Adaptive PoW Middleware & Sidecar                      │
│                                                          │
│  1. Telemetry Collector (psutil + per-request CPU ms)   │
│  2. Heuristic Signal Classifier                          │
│  3. Time-to-Failure Linear Regression                    │
│  4. Dynamic Difficulty Mapper (0 – 16 bits)               │
│  5. Hashcash SHA-256 Verifier (O(1) server check)         │
└───────────────────────┬──────────────────────────────────┘
                         │
        ┌────────────────┴────────────────┐
        ▼                                  ▼
┌──────────────────────────┐    ┌──────────────────────────┐
│ /api/verify-crypto        │    │ /api/data & /api/health   │
│ Real PBKDF2/HMAC Workload │    │ Sub-millisecond Ops       │
└──────────────────────────┘    └──────────────────────────┘
        │
        ▼
┌────────────────────────────────────────────────────────┐
│ Tamper-Evident Hash-Chained Audit Ledger                │
│ (Sequential SHA-256 Prev-Hash Chained SQLite Log)         │
└────────────────────────────────────────────────────────┘
```

## What's real and what isn't

We'd rather say this upfront than have a judge catch it in Q&A.

- **The classifier is rule-based, not a trained model.** It works off calibrated thresholds on CPU utilization, endpoint concentration, and latency slope, not deep learning, and not trained on external attack datasets. We think this is actually the right call for a system where you need to explain *why* it flagged something, not just that it did.
- **The audit ledger is a hash-chained log, not a blockchain.** It's a local, append-only, SHA-256-linked SQLite log. There's no consensus mechanism, no peer network, no mining. It gives you real tamper-evidence on a single machine and nothing more, nothing less.
- **The benchmark numbers below are real**, measured on our own hardware during testing. They'll shift a little depending on what machine you run this on.

## Running it locally

Needs Python 3.10+ (`fastapi`, `uvicorn`, `psutil`, `numpy`, `pydantic`) and Node.js 18+.

```bash
# backend, from repository root
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload

# frontend, separate terminal
cd frontend
npm run dev
```

Then open `http://localhost:3000`. Or skip all of this and use the [live deployment](https://asymptotes-defnse.onrender.com/) directly.

## Demo walkthrough

**1. Baseline.** Dashboard sits in `DEFENSE ARMED & MONITORING`. Latency's under 20ms against an 800ms SLA threshold, PoW difficulty is 0, time-to-failure reads `SLA SAFE`.

**2. Legitimate traffic spike.** Trigger a benign surge — aggregate RPS jumps to 25–35 req/s, spread across normal endpoints. This is our UPI-festival-sale scenario: the classifier correctly reads it as `BENIGN TRAFFIC SURGE`, and PoW difficulty stays at 0. Real users never feel a thing. This is the moment that matters most in the pitch — a naive rate limiter would already be blocking people here.

**3. Complexity attack.** Trigger the crypto-exhaustion attack — traffic floods `/api/verify-crypto` specifically. CPU climbs toward 75–90%, latency degrades fast, the classifier flags `CRITICAL THREAT: COMPLEXITY ATTACK`, and the time-to-failure countdown starts ticking. Watch the PoW dial ramp from 8 to 12 to 14+ bits in response — unsolved requests get rejected with HTTP 428, and effective attacker throughput drops as CPU and latency recover back to `STABLE`.

**4. Tamper-evidence check.** Open the ledger explorer, click "Verify Chain Integrity" (comes back clean), then "Simulate Block Tamper" to directly alter a row in the database, then verify again — it should immediately name the exact block that broke.

Click "Demo Reset" between runs.

## Tests

```bash
python -m tests.test_crypto
python -m tests.test_pow
python -m tests.test_classifier
python -m tests.test_ledger
python -m tests.test_middleware
python -m tests.test_e2e_integration
```

## Benchmark results (measured, not estimated)

| Difficulty | Expected hashes (2^D) | Avg. client solve time | Server verification cost |
|---|---|---|---|
| 0 bits | 0 | 0.01 ms | 0.00 ms |
| 8 bits | 256 | 0.58 ms | < 0.01 ms |
| 10 bits | 1,024 | 1.20 ms | < 0.01 ms |
| 12 bits | 4,096 | 6.92 ms | < 0.01 ms |
| 14 bits | 16,384 | 25.40 ms | < 0.01 ms |
| 16 bits | 65,536 | 49.41 ms | < 0.01 ms |

---

Built for Build with Bharat 2.0, NIT Delhi.
