# ADVAIT ESP-PMM / OTConnex — Industrial APM & Agentic Service Suite

Enterprise Artificial Lift Asset Performance Management (APM) & Autonomous Agentic Decision Support Platform for Electric Submersible Pumps (ESPs) across production oilfields.

---

## 1. Repository Overview

This repository contains the complete end-to-end industrial software suite for real-time ESP telemetry ingestion, machine learning diagnostics, first-principles physics calculation, governed engineering master data (Asset ConneX), and an autonomous natural-language operational co-pilot.

```
ESP_APM_server/
├── agent_service/                 # Autonomous AI Agent & Decision Engine (FastAPI, Redis, Local LLM)
├── Server3_Deployment_Package/    # Production ML & SCADA Ingestion Backend (FastAPI, SQLite, React UI)
├── esp-insight-suite/             # ADVAIT ESP-PMM Enterprise Frontend (TanStack Router, Tailwind CSS)
├── edge_live_service.py           # Field edge simulator & live telemetry publisher
└── [Specifications & Docs]        # Comprehensive architectural, API, and enumeration specifications
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

### 3. `esp-insight-suite/` — ADVAIT ESP-PMM Enterprise Frontend
- **Framework:** TanStack Router + Tailwind CSS enterprise dashboard.
- **Dual Workspace Separation:**
  - **Operations Workspace (`/`)**: Fleet Cockpit, Well Directory, Well Monitor (6 tabs + Advisor drawer), Exceptions Triage Desk, Troubleshooting Assistant, Reliability & Run Life, Management Scorecard.
  - **Engineering & Configuration Workspace (`/engineering`)**: Governed master data (Asset ConneX), Equipment Catalog (Pumps, Motors, Seals, Cables, VSDs, Sensors), Installation Registry, Wellbore Geometries, Fluid PVT, Engineering Workbench, and Validation Matrix.

---

## 3. Specifications & Architectural Guides

| Document | Purpose |
| :--- | :--- |
| [`Enumeration-OTConnex_ML_Dashboard.md`](./esp-insight-suite/Enumeration-OTConnex_ML_Dashboard.md) | Exhaustive component-by-component enumeration of the Server 3 Production ML Dashboard. |
| [`OTConnex_Lovable_Mapping.md`](./esp-insight-suite/OTConnex_Lovable_Mapping.md) | Master architectural mapping, feature parity, and migration blueprint between Server 3 and Lovable. |
| [`enumeration.md`](./esp-insight-suite/enumeration.md) | Exhaustive enumeration of the Operations Workspace in the Lovable frontend. |
| [`Enumeration-Engineering_Configuration.md`](./esp-insight-suite/Enumeration-Engineering_Configuration.md) | Exhaustive enumeration of the governed Asset ConneX Engineering & Configuration Workspace. |
| [`OT-Connex-Component-list.md`](./esp-insight-suite/OT-Connex-Component-list.md) | Pure hierarchical top-to-bottom master component list across all pages and views. |
| [`ESP_APM_AGENT_APIS_COMPLETE_SPECIFICATION.md`](./ESP_APM_AGENT_APIS_COMPLETE_SPECIFICATION.md) | Complete OpenAPI/REST API specification for agent service endpoints. |
| [`MQTT_LIVE_DATA_AND_EVENTS_SPECIFICATION.md`](./MQTT_LIVE_DATA_AND_EVENTS_SPECIFICATION.md) | SCADA MQTT topic structure, JSON packet schema, and 14-parameter tag dictionary. |

---

## 4. Port & Service Topology

| Port | Service | Description |
| :---: | :--- | :--- |
| `1883` | Mosquitto MQTT Broker | Live SCADA telemetry ingest |
| `8090` | Server 3 Backend API | FastAPI backend for telemetry, historian & ML inferencing |
| `8000` | Agent Service API | FastAPI agent co-pilot & decision gateway |
| `8080` / `8081` | ESP-Insight Suite | Enterprise TanStack Start frontend application |
| `3000` | Server 3 Dashboard | Legacy React operations dashboard |
| `6379` | Redis | Session state, audit trails & HITL approvals |

---

## 5. Getting Started

### Backend & Agent Setup (Python)
```bash
# Agent Service
cd agent_service
python -m venv .venv
source .venv/bin/activate  # Or .venv\Scripts\Activate on Windows
pip install -r requirements.txt
uvicorn app.main:app --port 8000 --reload
```

### Frontend Setup (Node.js / Bun)
```bash
cd esp-insight-suite
bun install  # or npm install
bun dev      # or npm run dev
```

---

## 6. License & Enterprise Notice

Proprietary enterprise artificial lift surveillance software. All rights reserved.
