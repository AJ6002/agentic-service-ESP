# ADVAIT ESP-PMM / OTConnex — Industrial APM & Agentic Service Suite

Enterprise Artificial Lift Asset Performance Management (APM) & Autonomous Agentic Decision Support Platform for Electric Submersible Pumps (ESPs) across production oilfields.

---

## 1. Repository Overview

This repository contains the complete end-to-end industrial software suite for real-time ESP telemetry ingestion, machine learning diagnostics, first-principles physics calculation, governed engineering master data (Asset ConneX), and an autonomous natural-language operational co-pilot.

```
ESP/
├── agent_service/                 # Autonomous AI Agent & Decision Engine (FastAPI, Redis, Local LLM)
│   ├── app/                       # Core application (Routing, Gateway, LLM, Synthesis, Workflows)
│   ├── tests/                     # 439-test automated regression & acceptance suite
│   ├── scripts/                   # Developer CLI tools, test runners & benchmarks
│   └── config/                    # Environment & configuration
├── Server3_Deployment_Package/    # Production ML & SCADA Ingestion Backend (FastAPI, SQLite, React UI)
├── lovable-code-legacy/           # ADVAIT ESP-PMM Enterprise Frontend & UI Reference
├── docker/                        # Mosquitto MQTT broker configuration
├── docs/                          # Centralized Specifications, Architecture, Plans & Reports
│   ├── api/                       # REST API & Postman/curl specifications
│   ├── architecture/              # Agent service architecture & design docs
│   ├── deployment/                # Server 184 deployment guides
│   ├── guides/                    # Local startup & environment guides
│   ├── plans/                     # Milestone implementation & seal plans
│   ├── reports/                   # Official seal reports & benchmark logs
│   └── history/                   # Chronological development history
├── scripts/                       # Root utilities (backup, migration tools)
├── edge_live_service.py           # Field edge simulator & live telemetry publisher
└── docker-compose.yml             # Local container orchestration
```

---

## 2. Core Subsystems

### 1. `agent_service/` — Autonomous AI Co-Pilot & Decision Engine
- **Framework:** FastAPI service exposing REST interfaces (`POST /query`, `POST /decision`).
- **State Management:** Redis-backed session and Human-in-the-Loop (HITL) execution planner.
- **LLM Layer:** Local OpenAI-compatible gateway (`llama-server`) running `Qwen2.5-Coder-3B-Instruct` with zero external cloud dependencies.
- **Tool Selection Registry:** Deterministic tool orchestration querying telemetry, historian databases, and engineering curves without unbounded agentic hallucination loops.

### 2. `Server3_Deployment_Package/` — Real-Time SCADA & ML Backend
- **Ingestion:** MQTT subscriber capturing 14 canonical sensor tags (`esp/v1/{well}/telemetry`) with 2-second scan resolution.
- **Historian Pipeline:** 6-tier data architecture (`unlabelled` $\to$ `labelled` $\to$ `normalized` $\to$ `ML-Layers` $\to$ `mlresults`).
- **Machine Learning Engine:** Real-time Isolation Forest anomaly detection, 14-class ESP failure mode probabilistic ranking, and SHAP attribution.
- **Operations Dashboard:** React SPA with Virtual Flow Metering (VFM), synchronized multi-tag trend canvas, in-situ pump degradation tracker, and 4-subsystem physical health equalizers.

### 3. `lovable-code-legacy/` — ADVAIT ESP-PMM Enterprise Frontend
- **Framework:** TanStack Router + Tailwind CSS enterprise dashboard.
- **Dual Workspace Separation:**
  - **Operations Workspace (`/`)**: Fleet Cockpit, Well Directory, Well Monitor (6 tabs + Advisor drawer), Exceptions Triage Desk, Troubleshooting Assistant, Reliability & Run Life, Management Scorecard.
  - **Engineering & Configuration Workspace (`/engineering`)**: Governed master data (Asset ConneX), Equipment Catalog (Pumps, Motors, Seals, Cables, VSDs, Sensors), Installation Registry, Wellbore Geometries, Fluid PVT, Engineering Workbench, and Validation Matrix.

---

## 3. Specifications & Architectural Guides

| Document | Purpose |
| :--- | :--- |
| [`docs/api/ESP_APM_AGENT_APIS_COMPLETE_SPECIFICATION.md`](docs/api/ESP_APM_AGENT_APIS_COMPLETE_SPECIFICATION.md) | Complete OpenAPI/REST API specification for agent service endpoints. |
| [`docs/api/ESP_KB_SERVICE_COMPLETE_API_SPECIFICATION.md`](docs/api/ESP_KB_SERVICE_COMPLETE_API_SPECIFICATION.md) | Vector Knowledge Base (Qdrant) query and ingestion API specification. |
| [`docs/api/MQTT_LIVE_DATA_AND_EVENTS_SPECIFICATION.md`](docs/api/MQTT_LIVE_DATA_AND_EVENTS_SPECIFICATION.md) | SCADA MQTT topic structure, JSON packet schema, and 14-parameter tag dictionary. |
| [`docs/api/AGENT_APIS_POSTMAN_AND_CURL_GUIDE.md`](docs/api/AGENT_APIS_POSTMAN_AND_CURL_GUIDE.md) | Postman collection & cURL command verification guide for Agent APIs. |
| [`docs/architecture/AGENT_SERVICE_ARCHITECTURE.md`](docs/architecture/AGENT_SERVICE_ARCHITECTURE.md) | Master architectural guide for Agent Service routing, gateway, and synthesis. |
| [`docs/guides/STARTUP_GUIDE.md`](docs/guides/STARTUP_GUIDE.md) | End-to-end setup and local testing guide for server configurations. |
| [`docs/deployment/SERVER_DEPLOYMENT_README.md`](docs/deployment/SERVER_DEPLOYMENT_README.md) | Step-by-step production deployment guide for Server 184. |
| [`docs/reports/FINAL_PHASE4_SEAL_AND_REGRESSION_REPORT.md`](docs/reports/FINAL_PHASE4_SEAL_AND_REGRESSION_REPORT.md) | Comprehensive Phase 4 & Pre-Phase 5 Seal & Regression Report. |

---

## 4. Port & Service Topology

| Port | Host | Service | Description |
| :---: | :---: | :--- | :--- |
| `1883` | `192.168.1.184` | Mosquitto MQTT Broker | Live SCADA telemetry ingest |
| `8090` | `192.168.1.184` | Server 3 Backend API | FastAPI backend for telemetry, historian & ML inferencing |
| `8085` | `192.168.1.184` | KB Qdrant Service | Vector Knowledge Base semantic search |
| `8091` | `127.0.0.1` | Agent Service API | FastAPI agent co-pilot & decision gateway |
| `8080` | `192.168.1.188` | Local LLM Server | `llama-server` running Qwen2.5-Coder-3B-Instruct |
| `6379` | `192.168.1.184` | Redis | Session state, audit trails & HITL approvals |

---

## 5. Getting Started

### Agent Service Setup (Python)
```bash
cd agent_service
# Activate virtual environment
..\.venv\Scripts\Activate.ps1   # Windows PowerShell

# Run full regression suite (439 tests)
pytest tests/ -q

# Start Agent Service
uvicorn app.main:app --host 0.0.0.0 --port 8091 --reload
```

---

## 6. License & Enterprise Notice

Proprietary enterprise artificial lift surveillance software. All rights reserved.
