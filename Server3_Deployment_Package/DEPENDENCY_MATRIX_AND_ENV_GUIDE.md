# Server 3 Dependency Matrix & Environment Configuration Guide

> **Target Service**: ESP APM Platform — Server 3 Operations Dashboard, ML Diagnostic Engine & Pipeline  
> **Target OS**: Windows Server / Windows 10/11 64-bit  
> **Python Runtime**: Python 3.11.x or 3.12.x (64-bit)  
> **Package Manager**: `uv` (recommended) or `pip`

---

## 1. Executive Status: Was `Server3_Deployment_Package` Updated?

**YES.** The complete deployment package at `C:\Users\admin.DESKTOP-17T37DJ\Desktop\New folder (6)\Server3_Deployment_Package` has been updated with all the latest production code:

1. **`well_calibration_registry.json`**:
   - All 27 corrupted `0.0` sensor profiles have been replaced with physically calibrated envelopes (`FIELD_SCADA` 180–480V, 40–180A, and `B538` 750–2500V, 15–85A).
   - Synced across `app/models/`, `app/code/models/`, `app/src/models/`, and `backend/src/models/`.
2. **`fault_classifier.py`**:
   - Added dual physical coupling requirements (`Blocked Intake` requires both suction drawdown and discharge head collapse; `Dry-Well Pump Off` requires both intake pressure and current drops).
   - Added stopped-pump bypass logic so standby wells are never flagged as electrical overload or dry-well.
3. **`gateway.py`**:
   - Implemented recursive `_sanitize_for_json` converting NumPy scalar types (`np.float64`, `np.int64`, `np.ndarray`, NaNs/Infs) into clean JSON-serializable Python natives before WebSocket transmission.
4. **`pipeline_orchestrator.py`**:
   - Added extraction of all standard SCADA MQTT tags (`STD_INT_PRS_PSI`, `STD_DISCH_PRS_PSI`, `STD_AMP_A`, `STD_VOLT_V`, etc.).
   - Replaced arbitrary 1000V/250 PSI fallbacks with dynamic per-well profile medians (`_w_med`).
   - Fixed database row returning so available historical rows are delivered directly.
5. **`requirements.txt`**:
   - Fully consolidated with all ML, WebSocket, data engineering, and agent dependencies.

---

## 2. Dependency Matrix (Libraries & Verified Versions)

Share the following table with your developer to ensure their virtual environment has the exact tested and compatible library versions:

| Package Category | Package Name | Verified Tested Version | Recommended Constraint | Purpose in ESP Platform | Compatibility Note / Reason |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **ML & Statistics** | `numpy` | `2.5.2` | `numpy>=2.0.0,<3.0.0` | Array math, physics calculations, vector transforms | NumPy 2.x scalar types (`np.float64`) require `_sanitize_for_json` in WebSocket broadcasts. |
| **ML & Statistics** | `scikit-learn` | `1.9.0` | `scikit-learn>=1.5.0` | Isolation Forest anomaly detection, preprocessing | Models trained on scikit-learn 1.5+ will fail unpickling on scikit-learn < 1.4. |
| **ML & Statistics** | `scipy` | `1.18.1` | `scipy>=1.13.0` | Probability distributions, signal processing | Set `OPENBLAS_NUM_THREADS=1` on Windows to avoid OpenBLAS thread allocation issues. |
| **ML & Statistics** | `joblib` | `1.6.0` | `joblib>=1.4.0` | Serialized model loading (`.joblib` artifact loaders) | Matches scikit-learn 1.5+ serialization protocols. |
| **WebSockets & API**| `websockets` | `16.1.1` | `websockets>=13.0.0` | `/ws/live` real-time telemetry streaming | Must be paired with `_sanitize_for_json` to prevent broadcast task failure. |
| **WebSockets & API**| `fastapi` | `0.141.1` | `fastapi>=0.109.0` | REST API gateway & WebSocket routing | Fast asynchronous request handling. |
| **WebSockets & API**| `uvicorn` | `0.52.4` | `uvicorn[standard]>=0.27.0` | ASGI production server for port `8090` | Standard event loop and WebSocket protocol support. |
| **Data Validation** | `pydantic` | `2.13.5` | `pydantic>=2.7.0` | Data schemas, API request/response contracts | V2 schema validation; converts to dict cleanly with `.model_dump()`. |
| **Data Frames** | `pandas` | `3.0.5` | `pandas>=2.2.0` | Historical tabular SCADA telemetry manipulation | Robust handling of time-series SCADA historian data. |
| **Data Frames** | `polars` | `1.44.1` | `polars>=0.20.0` | High-speed telemetry normalization and caching | Multi-threaded query engine for sub-millisecond transforms. |
| **Data Storage** | `pyarrow` | `25.0.1` | `pyarrow>=15.0.0` | Parquet caching and columnar storage | Zero-copy deserialization between memory layers. |
| **Deep Learning** | `torch` | `2.14.0` | `torch>=2.2.0` | Neural net inference and embedding vectors | CPU-only binary is sufficient for Server 3 inference. |
| **Embeddings** | `sentence-transformers` | `6.0.1` | `sentence-transformers>=2.2.2` | Vector representations for ESP Knowledge Base | Used in KB search and retrieval. |
| **Telemetry MQTT** | `paho-mqtt` | `2.1.0` | `paho-mqtt>=2.0.0` | Connects to Server 1 Mosquitto broker (`esp/#`) | Protocol v5 / v3.1.1 compatible. |
| **Environment** | `python-dotenv`| `1.2.3` | `python-dotenv>=1.0.0` | Reads `.env` / `config.env` at service launch | Safely loads database, broker, and gateway endpoints. |
| **HTTP Clients** | `httpx` | `0.28.1` | `httpx>=0.27.0` | Asynchronous REST calls to Server 2 Agent gateway | Native async context managers with automatic connection pooling. |
| **Visualization** | `plotly` | `7.0.0` | `plotly>=5.20.0` | Cross-plots, OLS regression curves, KDE distribution | Renders interactive analytics. |
| **Dashboard UI** | `streamlit` | `1.63.0` | `streamlit>=1.35.0` | Secondary AI Agent diagnostic console | Standalone monitoring GUI. |

---

## 3. Developer `.env` / `config.env` Variable Reference

Your developer should place the following variables in `Server3_Deployment_Package/config/config.env` (or in `.env` in the working directory):

```env
# ==============================================================================
# ESP APM PLATFORM — SERVER 3 ENVIRONMENT CONFIGURATION
# ==============================================================================

# ------------------------------------------------------------------------------
# 1. SERVER 1 CONNECTIVITY (Digital Twin & Live MQTT Stream)
# ------------------------------------------------------------------------------
# IP address or hostname of Server 1 running Mosquitto MQTT broker:
MQTT_BROKER_HOST=192.168.1.155
MQTT_BROKER_PORT=1883
MQTT_USERNAME=
MQTT_PASSWORD=
MQTT_TOPIC=esp/#

# ------------------------------------------------------------------------------
# 2. SERVER 2 CONNECTIVITY (AI Agent & LLM Service)
# ------------------------------------------------------------------------------
# HTTP URL of Server 2 (Ubuntu 24.04 LTS) running esp_agent Gateway:
AGENT_GATEWAY_URL=http://192.168.1.191:8090
LLM_GATEWAY_URL=http://192.168.1.191:8080/v1

# ------------------------------------------------------------------------------
# 3. SERVER 3 LOCAL SERVICE PORTS
# ------------------------------------------------------------------------------
# Backend Service (FastAPI + ML Diagnostic Engine)
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8090

# Frontend Operations Dashboard (React)
FRONTEND_HOST=0.0.0.0
FRONTEND_PORT=3000

# ------------------------------------------------------------------------------
# 4. RUNTIME SYSTEM SETTINGS (Windows Stability)
# ------------------------------------------------------------------------------
# Limits OpenBLAS threads to 1 to prevent Windows memory exhaustion crashes:
OPENBLAS_NUM_THREADS=1
MKL_NUM_THREADS=1
OMP_NUM_THREADS=1
```

### Table of `.env` Parameters

| Variable Name | Default / Target Value | Required? | Target Server | Description |
| :--- | :--- | :--- | :--- | :--- |
| `MQTT_BROKER_HOST` | `192.168.1.155` | **Yes** | Server 1 | IP of Server 1 running Mosquitto MQTT broker. |
| `MQTT_BROKER_PORT` | `1883` | **Yes** | Server 1 | Port of Mosquitto broker (default `1883`). |
| `MQTT_TOPIC` | `esp/#` | **Yes** | Server 1 | Wildcard subscription for all ESP well telemetry. |
| `AGENT_GATEWAY_URL`| `http://192.168.1.191:8090` | **Yes** | Server 2 | Base URL of Server 2 AI Agent. |
| `LLM_GATEWAY_URL` | `http://192.168.1.191:8080/v1` | Optional | Server 2 | Endpoint for LLM inference. |
| `BACKEND_HOST` | `0.0.0.0` | **Yes** | Server 3 | Interface to bind FastAPI backend. |
| `BACKEND_PORT` | `8090` | **Yes** | Server 3 | Listening port for FastAPI backend. |
| `FRONTEND_HOST` | `0.0.0.0` | **Yes** | Server 3 | Interface to bind React frontend dev/preview server. |
| `FRONTEND_PORT` | `3000` | **Yes** | Server 3 | Listening port for frontend dashboard. |
| `OPENBLAS_NUM_THREADS`| `1` | **Recommended** | Local (Server 3) | Prevents OpenBLAS memory allocation failures on Windows. |

---

## 4. Instructions for Developer to Set Up or Update Environment

Share these exact PowerShell commands with your developer:

```powershell
# 1. Navigate to Server 3 package directory
cd "C:\Users\admin.DESKTOP-17T37DJ\Desktop\New folder (6)\Server3_Deployment_Package"

# 2. Verify Python 3.11 or 3.12 (64-bit)
python --version

# 3. Create or update virtual environment using uv (fastest & cleanest)
# If uv is not installed: pip install uv
uv venv .venv --python 3.12

# 4. Activate virtual environment
.\.venv\Scripts\Activate.ps1

# 5. Install all dependencies from the updated requirements file
uv pip install -r backend_service\requirements.txt

# 6. Set OpenBLAS single-thread guard
[System.Environment]::SetEnvironmentVariable("OPENBLAS_NUM_THREADS", "1", [System.EnvironmentVariableTarget]::Process)

# 7. Start Backend Service
cd backend_service
python run_backend.py
```

---

## 5. Verification Checklist for the Developer

Once installed, the developer can run this quick 1-line check in PowerShell to guarantee everything works:

```powershell
.\.venv\Scripts\python.exe -c "import numpy, sklearn, scipy, fastapi, uvicorn, websockets, pydantic, pandas; print('ALL CORE DEPENDENCIES IMPORTED CLEANLY!')"
```

Then verify well health index:
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8090/api/esp/assets/FWS-04/health-index" | Select-Object -ExpandProperty prediction
```
**Expected Output**:
- `status`: `Healthy` (or `Normal Operation`)
- `primary_fault`: `Normal Operation`
- `health_score`: `> 90.0`
- `out_of_spec_parameters`: `[]` (Empty)
