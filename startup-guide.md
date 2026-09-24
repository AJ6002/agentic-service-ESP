# ESP APM Platform — Startup & Configuration Guide

Comprehensive setup, configuration, and verification guide for deploying the ESP APM platform on a fresh workstation or server.

---

## 1. System Architecture & Service Topology

| Service | Host / Address | Port | Description |
| :--- | :--- | :--- | :--- |
| **Frontend UI** | `http://localhost` | `3000` / Vite | React / TanStack Router / Tailwind UI (`esp-insight-suite`) |
| **Agent Service** | `http://127.0.0.1` | `8091` | FastAPI APM Reasoning Agent (`agent_service`) |
| **Redis Cache** | `127.0.0.1` | `6381` | Dedicated session / evidence store (`esp-apm-redis` container) |
| **LLM Server** | `http://192.168.1.191` | `8080` | Always-on `llama-server` running `Qwen2.5-Coder-3B-Instruct-Q4_K_M` |
| **Server 184 (Core APM)** | `http://192.168.1.184` | `8090` | Telemetry, live data, ML fault models, physics cards |
| **KB Service** | `http://192.168.1.184` | `8085` | Knowledge Base search, causal graphs, standards |

---

## 2. Prerequisites

### Windows (PowerShell as Admin)
```powershell
# Enable PowerShell script execution
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser -Force

# Install dependencies via winget
winget install --id Git.Git -e --source winget
winget install --id Python.Python.3.11 -e --source winget
winget install --id OpenJS.NodeJS.LTS -e --source winget
winget install --id Docker.DockerDesktop -e --source winget
winget install --id jqlang.jq -e --source winget
```

### macOS / Linux
```bash
brew install git python@3.11 node docker jq
```

---

## 3. Remote LLM Server (Host: `192.168.1.191`)

The LLM server is deployed as a high-performance, always-on `systemd` daemon on the 60-vCPU Intel Xeon server (`192.168.1.191`).

### Systemd Service Configuration (`/etc/systemd/system/llama.service`)
```ini
[Unit]
Description=Optimized Llama Server LLM Service
After=network.target

[Service]
Type=simple
User=tas-esp-ai
WorkingDirectory=/home/tas-esp-ai/llama-b10715
LimitMEMLOCK=infinity
LimitNOFILE=65535

ExecStart=/usr/bin/numactl --cpunodebind=0 --membind=0 /home/tas-esp-ai/llama-b10715/llama-server \
  -m /home/tas-esp-ai/models/Qwen2.5-Coder-3B-Instruct-Q4_K_M.gguf \
  --host 0.0.0.0 \
  --port 8080 \
  -c 8192 \
  -t 20 \
  --threads-batch 20 \
  -b 512 \
  -ub 512 \
  --parallel 1 \
  --load-mode mlock \
  --flash-attn on \
  --alias Qwen2.5-Coder-3B-Instruct-Q4_K_M

Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

### Control Commands on Server 191
```bash
sudo systemctl status llama --no-pager
sudo systemctl restart llama
sudo journalctl -u llama -f
```

---

## 4. Local Workstation Setup & Configuration

### Step 4.1: Clone Repositories
```bash
git clone <REPO_URL>
cd <PROJECT_DIR>
```

### Step 4.2: Start Local Redis
Start dedicated Redis container on port `6381`:
```bash
docker run -d --name esp-apm-redis -p 6381:6379 --restart unless-stopped redis:7-alpine
```

### Step 4.3: Configure Backend Environment (`agent_service/.env`)
Create `agent_service/.env`:
```env
# ESP APM Agent Service Configuration
LLM_GATEWAY_URL=http://192.168.1.191:8080/v1
LLM_MODEL_NAME=Qwen2.5-Coder-3B-Instruct-Q4_K_M
LLM_TIMEOUT_SEC=30
# Port 6381: dedicated esp-apm-redis container
REDIS_URL=redis://127.0.0.1:6381/0
CONFIDENCE_THRESHOLD=0.6
PENDING_TTL_SEC=900
RUN_TTL_SEC=86400
PORT=8091
HOST=0.0.0.0
SERVER3_BASE_URL=http://192.168.1.184:8090
KB_SERVICE_BASE_URL=http://192.168.1.184:8085
```

### Step 4.4: Install & Run Backend (`agent_service`)
```bash
cd agent_service

# Create and activate Python virtual environment
python -m venv .venv

# Windows:
.\.venv\Scripts\Activate.ps1
# Linux / macOS:
# source .venv/bin/activate

# Install dependencies
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install pytest pytest-asyncio anyio

# Start Agent Service
python -m uvicorn app.main:app --host 0.0.0.0 --port 8091 --reload
```

### Step 4.5: Configure & Run Frontend (`esp-insight-suite`)
Create `esp-insight-suite/.env`:
```env
SUPABASE_PROJECT_ID="yltjjjfqlspdfvzrtnvl"
SUPABASE_PUBLISHABLE_KEY="sb_publishable_j72K_8T5jKZRRY7i9dnJHg_FxfbNjl6"
SUPABASE_URL="https://yltjjjfqlspdfvzrtnvl.supabase.co"
VITE_SUPABASE_PROJECT_ID="yltjjjfqlspdfvzrtnvl"
VITE_SUPABASE_PUBLISHABLE_KEY="sb_publishable_j72K_8T5jKZRRY7i9dnJHg_FxfbNjl6"
VITE_SUPABASE_URL="https://yltjjjfqlspdfvzrtnvl.supabase.co"
```

Install and start UI:
```bash
cd ../esp-insight-suite
npm install
npm run dev
```

---

## 5. Verification & Testing

### 5.1 Quick Health Probes
```bash
# 1. LLM Server Probe (Server 191)
curl http://192.168.1.191:8080/health

# 2. KB Service Probe (Server 184)
curl http://192.168.1.184:8085/health

# 3. Core APM Service Probe (Server 184)
curl http://192.168.1.184:8090/health

# 4. Agent API Health
curl http://127.0.0.1:8091/health
```

### 5.2 Run Agent Automated Test Suite
```bash
cd agent_service
pytest tests/ -q --tb=short
```

### 5.3 Live Agent Query Test (NDJSON Stream)
```bash
curl -N -s -X POST http://127.0.0.1:8091/query \
  -H "Content-Type: application/json" \
  -d '{"session_id":"test-session","message":"Troubleshoot FS-17"}'
```
