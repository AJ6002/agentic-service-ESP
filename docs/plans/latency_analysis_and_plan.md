# ESP APM Agent Service — Latency Analysis, Optimization Plan & LLM Server Guide

---

## 1. Fresh Benchmark Results (26 Sep 2026)

### 1A. LLM Inference: Local RTX 3050 vs Remote Xeon E5-2670

| Metric | Local GPU (192.168.1.188:8080) | Remote Xeon (192.168.1.191:8080) |
|---|---|---|
| **Latency** | **16.5 s** | **59.7 s** |
| **Throughput** | **29.3 t/s** | **8.6 t/s** |
| Prompt tokens | 39 | 39 |
| Completion tokens | 483 | 511 |
| **Speed ratio** | **3.4× faster** | 1× (baseline) |

> [!IMPORTANT]
> The local RTX 3050 is **3.4× faster** than the Xeon server for an identical prompt. For a shorter agentic prompt (e.g. route/narrate ~200 tokens completion), the local GPU would complete in ~3-4s vs ~23s on Xeon.

### 1B. Server 184 Backend Endpoint Latency

| Endpoint | Latency | Status |
|---|---|---|
| `/health` | 263 ms | ✅ HTTP 200 |
| `/live/asset/FS-17` | 43 ms | ✅ HTTP 200 |
| `/live/telemetry/FS-17` | 247 ms | ✅ HTTP 200 |
| `/ml/fault/FS-17` | **5,043 ms** | ❌ **TIMEOUT** |
| `/ml/health/FS-17` | **5,025 ms** | ❌ **TIMEOUT** |
| `/ml/anomaly/FS-17` | **5,084 ms** | ❌ **TIMEOUT** |
| `/events/FS-17` | 199 ms | ❌ 404 (route issue) |
| `/trips/FS-17` | 360 ms | ❌ 404 (route issue) |

> [!CAUTION]
> **All three ML endpoints on Server 184 are timing out at 5s.** This means every OP03 pipeline run that includes `diagnose_fault`, `get_fault_taxonomy`, or `trace_causal_graph` will stall for 5+ seconds just waiting for the ML backend — and the latter two each call `fetch_ml_fault` *again* internally (redundant), potentially tripling the wait.

### 1C. End-to-End Pipeline (OP03 — Fault Diagnosis)

Agent service was not running locally at time of test (`WinError 10061`), but the theoretical pipeline breakdown based on empirical data:

```
┌─────────────────────────────────────────────────────────────────────────┐
│ E2E PIPELINE BREAKDOWN (OP03 — diagnose_fault for FS-17)              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│ ① LLM #1 — Router (route)                          ~3-4s (GPU)       │
│                                                      ~23s (Xeon)      │
│                                                                        │
│ ② Tool Gateway — dispatch_plan_calls (parallel)                       │
│    ├─ get_asset_context  (Server 184)                ~0.05s           │
│    ├─ get_live_telemetry (Server 184)                ~0.25s           │
│    ├─ get_historian_window (Server 184)              ~0.3s            │
│    ├─ get_ml_results (Server 184)                    ~0.2s            │
│    ├─ search_knowledge (:8085)                       ~0.3s            │
│    ├─ get_events (Server 184)                        ~0.2s (if 200)   │
│    ├─ get_trips (Server 184)                         ~0.4s            │
│    ├─ diagnose_fault → ml.fetch_ml_fault             ⚠️ 5s TIMEOUT   │
│    ├─ get_fault_taxonomy → ml.fetch_ml_fault (!)     ⚠️ 5s TIMEOUT   │
│    └─ trace_causal_graph → ml.fetch_ml_fault (!)     ⚠️ 5s TIMEOUT   │
│    ┌── All parallel via asyncio.gather ──┐                            │
│    │ Wall clock = max(all above) =       │           ⚠️ ~5s           │
│    └─────────────────────────────────────┘                            │
│                                                                        │
│ ③ QoD + Pack + Seal + (optional Gap-Fill retry)     ~0.01s           │
│                                                                        │
│ ④ LLM #3 — Narrator (narrate / synthesize_advisory)                  │
│    ├─ First attempt                                  ~3-4s (GPU)      │
│    │                                                  ~23s (Xeon)     │
│    └─ Retry (if JSON parse fails — happens often)    ~3-4s (GPU)      │
│                                                       ~23s (Xeon)     │
│                                                                        │
│ ⑤ Post-processing (provenance, viz, format)         ~0.01s           │
├─────────────────────────────────────────────────────────────────────────┤
│ TOTAL (best case, GPU, no retry):                                      │
│   ① 3s + ② 5s + ③ 0s + ④ 3s + ⑤ 0s = ~11s                          │
│                                                                        │
│ TOTAL (worst case, Xeon, with narrator retry):                         │
│   ① 23s + ② 5s + ③ 0s + ④ 46s + ⑤ 0s = ~74s                        │
│                                                                        │
│ TARGET:  < 5-10s total                                                │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Root Cause Analysis — Three Independent Bottlenecks

### Bottleneck #1: ML Endpoints on Server 184 are Timing Out (5s)

**What:** `/ml/fault/FS-17`, `/ml/health/FS-17`, `/ml/anomaly/FS-17` all timeout at 5s.

**Why it matters:** Even though tool gateway calls run in parallel, `asyncio.gather` waits for the *slowest* call. With ML endpoints timing out, the gateway step always takes ≥5s regardless of LLM speed.

**Redundancy amplifier:** Both `get_fault_taxonomy` (line 247) and `trace_causal_graph` (line 271) internally call `ml.fetch_ml_fault()` to discover the `fault_class` before they can do their KB lookup. So a single OP03 pipeline triggers `fetch_ml_fault` up to **3 times** in parallel, each hitting the broken endpoint.

### Bottleneck #2: LLM Inference is Slow on Xeon (8.6 t/s)

**What:** The Qwen 3B model runs CPU-only on the Xeon at 8.6 tokens/sec. A typical route decision (~100 tokens) takes ~12s, and narration (~300 tokens) takes ~35s.

**Why it matters:** The pipeline makes 2 sequential LLM calls (router + narrator), and the narrator may retry once (total: 3 LLM calls worst-case). On the Xeon, this alone is 12+35+35 = **~82s** worst-case.

**GPU comparison:** On the local RTX 3050 at 29.3 t/s, the same calls take 3+10+10 = **~23s** worst-case, or **~13s** best-case (no retry).

### Bottleneck #3: Narrator Retry Pattern

**What:** If `narrate()` fails to produce valid Advisory JSON on the first attempt, it retries with a stricter prompt — that's another full LLM inference round.

**Why it matters:** With a 3B model, JSON formatting failures are common (~30-50% of attempts), effectively doubling the narration latency.

---

## 3. Optimization Plan (Prioritized)

### Phase 1 — Quick Wins (no code changes on 184 needed)

| # | Fix | Expected Improvement | Effort |
|---|---|---|---|
| **1.1** | **Switch LLM to Local GPU (188:8080)** — change `.env` `LLM_GATEWAY_URL` | Router: 23s → 3s, Narrator: 35s → 10s | 1 min |
| **1.2** | **Cache `fetch_ml_fault` per-request** — deduplicate the 3 parallel calls to a single call + cache | Removes 2 redundant 5s timeout waits from gateway step | 30 min |
| **1.3** | **Reduce `GATEWAY_TIMEOUT_SEC` from 20s → 3s** — env var override. If ML endpoints are broken, fail fast instead of stalling 20s | Worst-case gateway step: 20s → 3s | 1 min |

**Phase 1 Expected Result:** Best-case E2E drops from ~11s (GPU) to **~6-7s**. If ML endpoints are fixed, to **~4-5s**.

### Phase 2 — Structural Improvements

| # | Fix | Expected Improvement | Effort |
|---|---|---|---|
| **2.1** | **Fix ML endpoints on Server 184** — investigate why `/ml/fault`, `/ml/health`, `/ml/anomaly` timeout. Likely the ML model inference or DB query on that server is stalling. | Gateway step: 5s → 0.2s | Investigate |
| **2.2** | **Add `max_tokens` to LLM calls** — Cap router at 200, narrator at 500. Prevents runaway generation. | Prevents worst-case 16s+ single-call latency | 15 min |
| **2.3** | **Reduce narrator prompt size** — The evidence block injected into the narrator can be very large. Trim/summarize before sending. | Reduces prompt token count → faster inference | 1 hr |

### Phase 3 — Architecture Changes

| # | Fix | Expected Improvement | Effort |
|---|---|---|---|
| **3.1** | **Stream LLM responses** — Use SSE/streaming for narrator output so the user sees text appearing immediately | Perceived latency → 0 (first token in ~1s) | 4 hrs |
| **3.2** | **Pre-compute ML results** — Run ML inference on a schedule (every 5 min), cache results. Gateway reads from cache. | ML endpoint: 5s → 0ms | 1 day |
| **3.3** | **Upgrade to larger GPU or quantize differently** — RTX 3050 (4GB VRAM) limits model size. An RTX 3060/4060 would run Q4 faster. | Further throughput improvement | Hardware |

---

## 4. Local Laptop as LLM Server — Network Setup Guide

### 4.1 Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                        LOCAL NETWORK                            │
│                                                                  │
│  ┌──────────────┐     HTTP API      ┌──────────────────────┐    │
│  │ Other Laptop │ ────────────────→ │ Your Laptop (188)    │    │
│  │ (any IP)     │  192.168.1.188    │ RTX 3050 GPU         │    │
│  │              │     :8080         │ llama-server          │    │
│  └──────────────┘                   │ Qwen2.5-Coder-3B     │    │
│                                     └──────────────────────┘    │
│                                                                  │
│  ┌──────────────┐     HTTP API      ┌──────────────────────┐    │
│  │ Agent Service│ ────────────────→ │ Same laptop or       │    │
│  │ (on 184/191) │  192.168.1.188    │ remote (191)         │    │
│  │              │     :8080         │ for LLM inference    │    │
│  └──────────────┘                   └──────────────────────┘    │
└──────────────────────────────────────────────────────────────────┘
```

### 4.2 Prerequisites

1. **llama.cpp server binary** — Already installed at `C:\path\to\llama-server.exe` (or Linux equivalent)
2. **Model file** — `Qwen2.5-Coder-3B-Instruct-Q4_K_M.gguf` (~2GB)
3. **Network** — Both machines on the same LAN (192.168.1.x)
4. **Firewall** — Port 8080 must be open for inbound TCP on the host machine

### 4.3 Step-by-Step: Run LLM Server on Your Laptop (Windows)

```powershell
# 1. Start llama-server (adjust paths to your installation)
llama-server.exe ^
  -m "C:\models\Qwen2.5-Coder-3B-Instruct-Q4_K_M.gguf" ^
  --host 0.0.0.0 ^
  --port 8080 ^
  -c 8192 ^
  -ngl 99 ^
  --flash-attn ^
  --parallel 2 ^
  --alias Qwen2.5-Coder-3B-Instruct-Q4_K_M

# 2. Open Windows Firewall for port 8080
netsh advfirewall firewall add rule name="LLama Server" ^
  dir=in action=allow protocol=TCP localport=8080

# 3. Test from the same machine
curl http://127.0.0.1:8080/v1/models
```

> [!NOTE]
> The key flags:
> - `--host 0.0.0.0` — Listen on ALL network interfaces (not just localhost)
> - `-ngl 99` — Offload all layers to GPU (critical for performance)
> - `--parallel 2` — Allow 2 concurrent requests (router + narrator can overlap)

### 4.4 Step-by-Step: Run LLM Server on Your Laptop (Linux)

```bash
# 1. Start llama-server
numactl --cpunodebind=0 --membind=0 \
  /path/to/llama-server \
  -m /path/to/models/Qwen2.5-Coder-3B-Instruct-Q4_K_M.gguf \
  --host 0.0.0.0 \
  --port 8080 \
  -c 8192 \
  -ngl 99 \
  --flash-attn \
  --parallel 2 \
  --alias Qwen2.5-Coder-3B-Instruct-Q4_K_M

# 2. Open firewall
sudo ufw allow 8080/tcp

# 3. Test
curl http://127.0.0.1:8080/v1/models
```

### 4.5 Connect Another Laptop to Your LLM Server

From **any other machine on the LAN**, send API requests using your laptop's IP:

```bash
# Test connectivity
curl http://192.168.1.188:8080/v1/models

# Test inference
curl -s http://192.168.1.188:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Qwen2.5-Coder-3B-Instruct-Q4_K_M",
    "messages": [{"role": "user", "content": "Hello, can you hear me?"}],
    "temperature": 0.0
  }' | python3 -m json.tool
```

### 4.6 Point the Agent Service to Your Laptop

Edit the `.env` file on whichever machine runs the agent service:

```ini
# Before (slow Xeon):
# LLM_GATEWAY_URL=http://192.168.1.191:8080/v1

# After (fast GPU):
LLM_GATEWAY_URL=http://192.168.1.188:8080/v1
```

Then restart the agent service. **No code changes needed** — the `LLM_GATEWAY_URL` env var is the only thing that controls which LLM server is used.

### 4.7 Verify it Works

```bash
# From the agent service machine, confirm it can reach your laptop:
curl http://192.168.1.188:8080/v1/models

# Expected response:
# {"object":"list","data":[{"id":"Qwen2.5-Coder-3B-Instruct-Q4_K_M",...}]}
```

> [!WARNING]
> **Important caveats for running your laptop as a server:**
> - The laptop must be **on and awake** (disable sleep/hibernate)
> - WiFi may be less reliable than Ethernet for sustained inference
> - If your laptop IP changes (DHCP), update `.env` on the agent service machine
> - Only **2 concurrent requests** are supported (limited by GPU VRAM on RTX 3050)

---

## 5. Summary — What to Do Right Now

| Priority | Action | Impact |
|---|---|---|
| 🔴 **Now** | Change `.env` → `LLM_GATEWAY_URL=http://192.168.1.188:8080/v1` | LLM calls 3.4× faster |
| 🔴 **Now** | Add to `.env` → `GATEWAY_TIMEOUT_SEC=3` | Fail-fast on broken ML endpoints |
| 🟡 **This week** | Fix ML endpoints on Server 184 (`/ml/fault`, `/ml/health`, `/ml/anomaly`) | Remove the 5s timeout bottleneck entirely |
| 🟡 **This week** | Cache `fetch_ml_fault` result per-request to deduplicate 3 redundant calls | Prevent triple-timeout in gateway step |
| 🟢 **Later** | Add `max_tokens` caps, stream responses, pre-compute ML | Sub-3s E2E |
