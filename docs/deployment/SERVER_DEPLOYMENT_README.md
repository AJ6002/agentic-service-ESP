# ESP APM Platform — Server 3 Updating & Deployment Manual

This guide provides step-by-step instructions and command-line scripts to update, maintain, and deploy the **Operations Dashboard (React UI)**, **FastAPI Core Backend**, **Machine Learning Diagnostic Engine**, and **SQLite SCADA Historian Databases** on **Server 3 (Windows Server)**.

---

## 1. Multi-Server Production Architecture

| Server | Role | Operating System | Host / Port | Key Services |
| :--- | :--- | :--- | :--- | :--- |
| **Server 1** | Digital Twin & Telemetry Streamer | Linux / Windows | `192.168.1.155:1883` | Eclipse Mosquitto MQTT Broker, OPG Telemetry Generator |
| **Server 2** | AI Multi-Agent Specialist Gateway | Ubuntu 24.04 LTS | `192.168.1.191:8090` | LangGraph / FastAPI Agent Gateway |
| **Server 3** | Operations Dashboard & ML Platform | Windows Server | `Port 3000` (UI)<br>`Port 8090` (Backend) | React SPA (Vite/serve), FastAPI ML Engine, SQLite Historians |

---

## 2. Database Architecture & Health Connections

### SQLite Database Topology
The platform maintains 4 persistent database tiers located in `data/`:
1. **`unlabelled.db` (`opg_well_telemetry`)**: Zero-loss 34-column SCADA historian for all incoming telemetry.
2. **`labelled.db` (`opg_well_telemetry`)**: Ground-truth annotated fault records and incident events.
3. **`normalized.db` (`opg_normalized_telemetry`)**: 42-column [0,1] scaled features + derived physics dynamics ($\Delta P$, $A/Hz$, $kVA$, $\Delta T$).
4. **`mlresults.db` (`ml_results`)**: Per-packet Isolation Forest anomaly scores, 13-mode fault diagnoses, and canonical verdicts.
5. **`esp_events.db`**: State machine alarms, high-vibration trips, and operator action logs.
6. **`conversations.db`**: Chat history and diagnostic report checkpoints.

### Automated Bootstrapping & Connection Verification
- Upon backend startup, `pipeline_orchestrator.py` automatically checks all database files and runs `CREATE TABLE IF NOT EXISTS` and `CREATE INDEX IF NOT EXISTS`.
- All database paths are dynamically discovered across candidate directories (`data/`, `../data/`, etc.) prioritizing existing databases with historical records (>1 MB).
- To verify database connectivity from the command line:
  ```powershell
  python -c "import sqlite3; [print(db, sqlite3.connect('data/' + db).execute('SELECT COUNT(*) FROM opg_well_telemetry').fetchone()[0]) for db in ['unlabelled.db', 'labelled.db']]"
  ```

---

## 3. Database Size Quota & 1.5 GB Auto-Flush Utility

### The Math: Rows Required for 1.5 GB
- Each telemetry record in `opg_well_telemetry` contains **34 sensor numeric columns**, timestamps, well identifiers, and a full raw SCADA JSON payload string (`raw_payload`), plus **B-tree indexes** (`idx_unlab_well_ts`, etc.).
- **Empirical Storage Consumption**:
  $$\frac{2,969,030,656\text{ bytes}}{704,447\text{ records}} \approx 4,214\text{ bytes per record}$$
- **1.5 GB Storage Quota**:
  $$\text{Target Quota} = 1.5 \times 1024 \times 1024 \times 1024 = 1,610,612,736\text{ bytes}$$
  $$\text{Row Threshold} = \frac{1,610,612,736\text{ bytes}}{4,214\text{ bytes/row}} \approx \mathbf{382,200\text{ rows}}$$
- **Retention Strategy**:
  - Threshold: When a database reaches **1.5 GB** (or row count > 360,000).
  - Retention Window: Retain the most recent **300,000 records** ($\approx 1.2\text{ GB}$).
  - Disk Reclamation: Immediately executes SQLite `VACUUM;` to reclaim freed pages and return physical drive space to the Windows NTFS filesystem.
  - **Preserved Lineage Metrics**: The UI continues tracking total lifetime processed packets via `MAX(id)` (e.g. 704,000+), ensuring counter continuity while keeping disk footprint small.

### Running the Auto-Flush Utility Manually
Run the maintenance script located in `backend/scripts/prune_databases.py` (or root `prune_databases.py`):
```powershell
# Enforce 1.5 GB limit and retain latest 300,000 rows
python backend\scripts\prune_databases.py --max-mb 1500 --retain 300000

# To force pruning immediately regardless of current size:
python backend\scripts\prune_databases.py --max-mb 1500 --retain 300000 --force
```

### Scheduling Automated Flush via Windows Task Scheduler
To automatically run the maintenance every Sunday at 02:00 AM:
```powershell
schtasks /create /tn "ESP_Database_AutoFlush" /tr "powershell -WindowStyle Hidden -Command \"python c:\Server3_Deployment_Package\backend_service\prune_databases.py --max-mb 1500 --retain 300000\"" /sc weekly /d SUN /st 02:00 /ru "SYSTEM"
```

---

## 4. Step-by-Step Instructions to Update Existing Deployment

Since Server 3 is already deployed, follow these steps to apply code updates and restart services without disrupting settings:

### Step 1: Open Administrator PowerShell or CMD
Press `Win + X` and select **Terminal (Admin)** or **PowerShell (Run as Administrator)**.

### Step 2: Stop Existing Windows Services
Stop the frontend and backend services to release file locks:
```cmd
net stop esp-frontend-service
net stop esp-backend-service
```
*(Or navigate to `Server3_Deployment_Package` and run `uninstall_services.bat` if performing a complete redeployment).*

### Step 3: Deploy the Updated Code & Packages
If updating via Git:
```cmd
cd "C:\Users\admin.DESKTOP-17T37DJ\Desktop\New folder (6)"
git pull origin main
```
If updating via `Server3_Deployment_Package`:
- Copy the updated `Server3_Deployment_Package` to Server 3.
- Ensure `config\config.env` preserves your server IP settings:
  ```properties
  MQTT_BROKER_HOST=192.168.1.155
  MQTT_BROKER_PORT=1883
  AGENT_GATEWAY_URL=http://192.168.1.191:8090
  BACKEND_PORT=8090
  FRONTEND_PORT=3000
  ```

### Step 4: Build & Synchronize Frontend Production Bundle
Compile the optimized React production bundle:
```cmd
cd frontend
npm run build
```
Copy `frontend\dist\*` into the frontend service directory:
```powershell
Copy-Item -Path "frontend\dist\*" -Destination "Server3_Deployment_Package\frontend_service\dist\" -Recurse -Force
```

### Step 5: Enforce Database Size Limits
Run the space reclamation utility:
```cmd
python backend\scripts\prune_databases.py --max-mb 1500 --retain 300000
```

### Step 6: Start Windows Services
Start the background services:
```cmd
net start esp-backend-service
net start esp-frontend-service
```
*(Or right-click `install_services.bat` and select **Run as Administrator**).*

### Step 7: Verify Service Health & Port Availability
Check the status of both services:
```cmd
status_services.bat
```
Alternatively, test the REST endpoints directly:
```powershell
# 1. Check system pipeline & database counters (>704,000 records)
curl http://localhost:8090/api/esp/pipeline/status

# 2. Check 57 fleet asset statuses and sensor parameters
curl http://localhost:8090/api/esp/assets

# 3. Check bivariate cross-plot regression fit
curl "http://localhost:8090/api/esp/eda/cross-plot?asset_id=FS-031"

# 4. Check Gaussian KDE sensor distribution
curl "http://localhost:8090/api/esp/eda/distributions?asset_id=FS-031"
```

---

## 5. Troubleshooting & Log Locations

| Component | Log File Location | What to Inspect |
| :--- | :--- | :--- |
| **Backend Service** | `backend_service\logs\esp-backend-service.out.log`<br>`backend_service\logs\esp-backend-service.err.log` | MQTT packet ingestion, ML inferences, SQLite inserts |
| **Frontend Service** | `frontend_service\logs\esp-frontend-service.out.log`<br>`frontend_service\logs\esp-frontend-service.err.log` | Static asset serving, proxy request routing to :8090 |
| **Database Locks** | `data\*.db-wal`, `data\*.db-shm` | Ensure backend is stopped before manual SQLite migrations |
