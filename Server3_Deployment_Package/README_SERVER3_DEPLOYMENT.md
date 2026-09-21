# ESP APM Platform — Server 3 Deployment & Update Manual

This package deploys and updates the **Operations Dashboard (React UI)**, the **Platform Backend with ML Diagnostic Layers**, and the **SQLite SCADA Historian Databases** on **Windows Server (Server 3)** as background Windows Services wrapped via **WinSW**.

---

## 1. Package Structure

```
Server3_Deployment_Package/
├── .venv/                      # Portable Python 3.12 runtime with all dependencies installed
├── config/
│   └── config.env              # Central configuration (Server 1 MQTT IP, Server 2 Agent URL, Ports)
├── backend_service/
│   ├── app/                    # Backend FastAPI app, ML models & calibration registry
│   │   ├── models/             # Trained Isolation Forest models & dynamic well setpoints
│   │   └── src/                # Pipeline orchestrator, MQTT collector, REST APIs
│   ├── data/                   # Compacted SQLite historian databases (<1.5 GB each)
│   │   ├── unlabelled.db       # Ingested telemetry archive (~1.2 GB, >704k records)
│   │   ├── labelled.db         # Fault-annotated incident dataset (~1.2 GB)
│   │   ├── normalized.db       # Scaled physics features
│   │   └── mlresults.db        # Live anomaly scoring history
│   ├── logs/                   # Automatic rotating stdout/stderr logs
│   ├── winsw/
│   │   ├── esp-backend-service.exe # WinSW Service Wrapper
│   │   └── esp-backend-service.xml # Service configuration definition
│   ├── prune_databases.py      # Database compaction & 1.5 GB quota maintenance script
│   └── run_backend.py          # Backend entry point
├── frontend_service/
│   ├── dist/                   # Production-compiled React SPA bundle (Vite)
│   ├── logs/                   # Automatic rotating stdout/stderr logs
│   ├── winsw/
│   │   ├── esp-frontend-service.exe # WinSW Service Wrapper
│   │   └── esp-frontend-service.xml # Service configuration definition
│   └── serve_frontend.py       # High-performance static & reverse-proxy server
├── prune_databases.py          # Root database compaction utility
├── install_services.bat        # [Admin] One-click Windows Service installer & firewall setup
├── uninstall_services.bat      # [Admin] One-click Windows Service uninstaller
├── status_services.bat         # Health check and port status monitor
├── run_local_debug.bat         # Instant console launcher for testing without installing services
└── README_SERVER3_DEPLOYMENT.md# This documentation
```

---

## 2. Multi-Server Architecture

| Server | Role | Operating System | Host / Port | Key Services |
| :--- | :--- | :--- | :--- | :--- |
| **Server 1** | Digital Twin & Telemetry Streamer | Linux / Windows | `192.168.1.155:1883` | Eclipse Mosquitto MQTT Broker, OPG Telemetry Generator |
| **Server 2** | AI Multi-Agent Specialist Gateway | Ubuntu 24.04 LTS | `192.168.1.191:8090` | LangGraph / FastAPI Agent Gateway |
| **Server 3** | Operations Dashboard & ML Platform | Windows Server | `Port 3000` (UI)<br>`Port 8090` (Backend) | React SPA (Vite/serve), FastAPI ML Engine, SQLite Historians |

---

## 3. Database Architecture & Health Connections

### Automatic Table Initialization
- On startup, the backend automatically runs `CREATE TABLE IF NOT EXISTS` and `CREATE INDEX IF NOT EXISTS` across all databases (`unlabelled.db`, `labelled.db`, `normalized.db`, `mlresults.db`).
- All connections utilize SQLite WAL (Write-Ahead Logging) mode for concurrent read/write throughput during continuous MQTT streaming.

### Verifying Database Connectivity
Run from `Server3_Deployment_Package`:
```powershell
.\.venv\Scripts\python.exe -c "import sqlite3; [print(db, sqlite3.connect('backend_service/data/' + db).execute('SELECT COUNT(*), MAX(id) FROM opg_well_telemetry').fetchone()) for db in ['unlabelled.db', 'labelled.db']]"
```

---

## 4. 1.5 GB Storage Quota & Pruning Calculation

### The Math: Rows Required for 1.5 GB
- Each `opg_well_telemetry` record consumes approximately **4,214 bytes** (34 numeric sensor columns, timestamp, asset ID, raw SCADA JSON string, and B-tree indexes).
- **Target Quota**:
  $$1.5\text{ GB} = 1,610,612,736\text{ bytes}$$
  $$\text{Row Capacity} = \frac{1,610,612,736\text{ bytes}}{4,214\text{ bytes/row}} \approx \mathbf{382,200\text{ records}}$$
- **Retention Policy**:
  - Threshold: Enforced whenever database exceeds **1.5 GB**.
  - Retention Window: Keeps the latest **300,000 records** ($\approx \mathbf{1.2\text{ GB}}$), leaving $\approx 300\text{ MB}$ of safety headroom.
  - Page Defragmentation: Automatically executes `VACUUM;` to reclaim physical disk space and return it to the Windows NTFS filesystem.
  - Counter Preservation: Deletion uses indexed `id < cutoff_id`, preserving `MAX(id)` so UI lifetime processed counters (>704,000) remain continuous.

### Running the Pruning Script Manually
```powershell
# Check size and prune if over 1.5 GB
.\.venv\Scripts\python.exe prune_databases.py --max-mb 1500 --retain 300000

# Force compaction immediately regardless of file size
.\.venv\Scripts\python.exe prune_databases.py --max-mb 1500 --retain 300000 --force
```

### Scheduling Automated Pruning via Windows Task Scheduler
To automatically run compaction every Sunday at 02:00 AM:
```powershell
schtasks /create /tn "ESP_Database_AutoFlush" /tr "powershell -WindowStyle Hidden -Command \"C:\Server3_Deployment_Package\.venv\Scripts\python.exe C:\Server3_Deployment_Package\prune_databases.py --max-mb 1500 --retain 300000\"" /sc weekly /d SUN /st 02:00 /ru "SYSTEM"
```

---

## 5. Deployment & Update Instructions (Server 3)

### Updating an Already Deployed Server 3

If Server 3 is already deployed and running, follow these steps to apply code and frontend updates:

#### Step 1: Open Administrator PowerShell or CMD
Press `Win + X` and select **Terminal (Admin)** or **PowerShell (Run as Administrator)**.

#### Step 2: Stop Existing Windows Services
Stop the services to release file locks on executable and database files:
```cmd
net stop esp-frontend-service
net stop esp-backend-service
```

#### Step 3: Copy Updated Files to Server 3
Copy the updated files from your development machine to `C:\Server3_Deployment_Package`:
- `backend_service\app\` (updated backend APIs, dynamic DB resolution, and health thresholds)
- `frontend_service\dist\` (updated React production bundle)
- `prune_databases.py` (database maintenance script)

*Note: You do NOT need to overwrite `config\config.env` if your IP addresses are already configured.*

#### Step 4: Run Database Compaction (if needed)
```cmd
cd C:\Server3_Deployment_Package
.\.venv\Scripts\python.exe prune_databases.py --max-mb 1500 --retain 300000
```

#### Step 5: Start Windows Services
```cmd
net start esp-backend-service
net start esp-frontend-service
```

#### Step 6: Verify Service Health
Check status of both services:
```cmd
status_services.bat
```
Or test the endpoints:
```powershell
# 1. Pipeline status and lifetime counters (>704,000 records)
curl http://localhost:8090/api/esp/pipeline/status

# 2. 57 Fleet well health statuses
curl http://localhost:8090/api/esp/assets

# 3. Bivariate Cross-Plot (OLS regression)
curl "http://localhost:8090/api/esp/eda/cross-plot?asset_id=FS-031"

# 4. Sensor Distribution & Gaussian KDE
curl "http://localhost:8090/api/esp/eda/distributions?asset_id=FS-031"
```

---

### Fresh Deployment on a New Server 3

If deploying on a brand-new Windows Server:

1. **Copy Package**: Copy the entire `Server3_Deployment_Package` folder to `C:\Server3_Deployment_Package`.
2. **Configure IPs**: Open `config\config.env` and set `MQTT_BROKER_HOST=192.168.1.155` and `AGENT_GATEWAY_URL=http://192.168.1.191:8090`.
3. **Install & Start Services**: Right-click `install_services.bat` and select **Run as administrator**.
4. **Open Browser**: Navigate to `http://localhost:3000` (or `http://<SERVER3_IP>:3000`).

---

## 6. Service Management Commands

| Action | Command / Script | Description |
| :--- | :--- | :--- |
| **Check Status** | Double-click `status_services.bat` | Displays Windows service states and port connectivity (3000, 8090) |
| **Stop Services** | `net stop esp-frontend-service`<br>`net stop esp-backend-service` | Pauses background execution |
| **Start Services** | `net start esp-backend-service`<br>`net start esp-frontend-service` | Resumes background execution |
| **Restart Services** | `net stop esp-*-service && net start esp-*-service` | Restarts services after configuration updates |
| **Uninstall Services** | Right-click `uninstall_services.bat` -> Run as Admin | Removes services and firewall rules cleanly |
| **Local Debug** | Double-click `run_local_debug.bat` | Runs both services in visible console windows without WinSW |

---

## 7. Log Locations & Diagnostics

- **Backend Logs**: `backend_service\logs\esp-backend-service.out.log` / `esp-backend-service.err.log`
- **Frontend Logs**: `frontend_service\logs\esp-frontend-service.out.log` / `esp-frontend-service.err.log`
- **Swagger Documentation**: Accessible at `http://localhost:8090/docs`
