# Developer Handoff Document: Server 3 APM Platform Deployment

**Project**: ESP APM Platform — Real-Time Telemetry, Digital Twin & Forensic Visuals Studio  
**Target Host**: Server 3 (IP: `192.168.1.155:8090` / `localhost:3000` / `localhost:8090`)  
**Deployment Directory**: `C:\TAS_AI\Server3_Deployment_Package`  
**Git Remote**: `https://github.com/Harshit777Git/esp-platform-clean.git` (`branch: main`)  
**Last Updated**: September 15, 2026  

---

## 1. Executive Deployment Architecture

Server 3 operates under a **Dual Windows Service** architecture orchestrated via WinSW executables or running standalone in PowerShell/Console:
- **Backend ML & Analytics Service (`esp-backend-service`)**: FastAPI / Uvicorn listening on **Port 8090**.
  - Path: `C:\TAS_AI\Server3_Deployment_Package\backend_service`
  - Subscribes to Server 1 Mosquitto MQTT Broker (`192.168.1.155:1883`) on `esp/v1/#`.
- **Frontend Dashboard Service (`esp-frontend-service`)**: Production Vite Static Build served via Python HTTP / reverse proxy on **Port 3000**.
  - Path: `C:\TAS_AI\Server3_Deployment_Package\frontend_service`
  - Dist location: `C:\TAS_AI\Server3_Deployment_Package\frontend_service\dist`

---

## 2. Step-by-Step Deployment Instructions

Choose **Method A** (Git Pull — Recommended) or **Method B** (Direct File Copy).

### Method A: Updating via Git (Recommended)

Open **PowerShell as Administrator** on Server 3:

```powershell
# 1. Navigate to the deployment folder
cd C:\TAS_AI\Server3_Deployment_Package

# 2. Add or set the fork remote containing all the latest commits:
git remote add fork https://github.com/Harshit777Git/esp-platform-clean.git 2>$null
git fetch fork main

# 3. Pull the latest commits into your branch
git pull fork main

# 4. Run the high-performance SQLite database indexer
# (Crucial: prevents 6+ second query locks and ensures instant sub-50ms analytics rendering)
python index_databases.py

# 5. Restart the Windows Services
.\restart_services.bat
```

---

### Method B: Updating via Direct File Copy / RDP

If Server 3 does not have direct Git access to GitHub:

1. Copy the 4.4 MB update archive from the development machine:
   - Source: `c:\Users\admin.DESKTOP-17T37DJ\Desktop\New folder (6)\Server3_Quick_Update.zip`
   - Paste to Server 3: `C:\TAS_AI\Server3_Deployment_Package\`
2. Extract all contents into `C:\TAS_AI\Server3_Deployment_Package\` and select **"Replace the files in the destination"**.
3. In Administrator PowerShell on Server 3, execute:
   ```powershell
   cd C:\TAS_AI\Server3_Deployment_Package
   python index_databases.py
   .\restart_services.bat
   ```

---

## 3. Alternative / Manual Service Restart Commands

If you prefer to restart the Windows Services manually without `.bat` files:

```powershell
# Using Native PowerShell Service Management (Run as Administrator):
Restart-Service esp-backend-service
Restart-Service esp-frontend-service

# OR using WinSW binaries:
cd C:\TAS_AI\Server3_Deployment_Package\backend_service\winsw
.\esp-backend-service.exe restart

cd C:\TAS_AI\Server3_Deployment_Package\frontend_service\winsw
.\esp-frontend-service.exe restart
```

To run in standalone debug console mode (visible console windows):
```powershell
cd C:\TAS_AI\Server3_Deployment_Package
.\run_local_debug.bat
```

---

## 4. Verification & Health Check

Run the built-in status checker:
```powershell
cd C:\TAS_AI\Server3_Deployment_Package
.\status_services.bat
```
Expected output:
```
[ONLINE] Backend ML Service is responding on port 8090.
[ONLINE] Frontend Dashboard Service is responding on port 3000.
```

### API Endpoint Health Checks (Curl or Browser)
1. **Live Forensics Aggregator**:
   ```bash
   curl http://localhost:8090/api/esp/assets/FS-031/forensics?source=live
   ```
   *Expected*: HTTP 200, `"status": "SUCCESS"`, 4 subsystems, 14 depth profile trajectory points, 6-channel SHAP attribution.
2. **Pearson Correlation Matrix**:
   ```bash
   curl http://localhost:8090/api/analytics/correlation-matrix?asset_id=FS-031
   ```
   *Expected*: HTTP 200, `"status": "SUCCESS"`, 14×14 matrix, non-empty `pairwise_insights`.
3. **Bivariate Cross-Plot OLS**:
   ```bash
   curl "http://localhost:8090/api/analytics/cross-plot?asset_id=FS-031&sensor_x=Inp%20bar/psi&sensor_y=Disch%20pr.%20Bar/psi"
   ```
   *Expected*: HTTP 200, `"status": "SUCCESS"`, regression slope, intercept, $r$, $R^2$, and trendline.

---

## 5. Key Architecture Constraints & Production Rules
- **No Mocking**: All data streams originate from Server 1 Mosquitto broker (`192.168.1.155:1883`). Do not re-introduce static mock fallbacks.
- **Anonymous MQTT**: The broker accepts anonymous connections. Never enable `username_pw_set("scada_operator", ...)` in `mqtt_collector.py`.
- **Database Indexing**: Always run `python index_databases.py` whenever new `.db` files are created or imported from raw SCADA dumps.
