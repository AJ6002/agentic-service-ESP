# 🐘 Centralized PostgreSQL Setup & Schema Summary (Server 184)

**Status**: Active & Verified  
**Host**: Server 184 (`192.168.1.184`)  
**Instance Type**: Native Windows Service (Non-Docker)  
**Port**: `5433`  
**Database**: `esp_apm_db`  

---

## 1. Access Credentials

| Parameter | Value | Notes |
| :--- | :--- | :--- |
| **Database** | `esp_apm_db` | Dedicated central APM database |
| **Application User** | `esp_admin` | Owner of all tables & sequences |
| **Password** | `EspApm2026!` | Dedicated password |
| **Default Port** | `5433` | Native service port |
| **Superuser** | `postgres` | Unmodified master account |

---

## 2. Connection Strings (`.env`)

### Local Server 184 Services (Loopback)
```ini
DATABASE_URL=postgresql://esp_admin:EspApm2026!@127.0.0.1:5433/esp_apm_db
ASYNC_DATABASE_URL=postgresql+asyncpg://esp_admin:EspApm2026!@127.0.0.1:5433/esp_apm_db
```

### LAN Network Clients (Server 191 Ubuntu Node / Dev Laptops)
```ini
DATABASE_URL=postgresql://esp_admin:EspApm2026!@192.168.1.184:5433/esp_apm_db
ASYNC_DATABASE_URL=postgresql+asyncpg://esp_admin:EspApm2026!@192.168.1.184:5433/esp_apm_db
```

---

## 3. Network & Security Configuration

1. **PostgreSQL Listening**:
   * Config file: `C:\Program Files\PostgreSQL\16\data\postgresql.conf`
   * Directive: `listen_addresses = '*'`
   * Port: `port = 5433`
2. **Subnet Access (`pg_hba.conf`)**:
   * Directive: `host all all 192.168.1.0/24 scram-sha-256`
   * Allows all workstations and Server 191 on `192.168.1.x` to connect using SCRAM password authentication.
3. **Windows Defender Firewall**:
   * Inbound Rule: `PostgreSQL Port 5433` (TCP 5433 - Allowed).

---

## 4. Database Schema Summary (6 Central Tables)

| # | Table Name | Purpose / Legacy Replacement | Key Columns |
| :--- | :--- | :--- | :--- |
| **1** | `opg_well_telemetry` | Raw SCADA historian & broker ingestion (replaces `unlabelled.db`) | `id`, `timestamp`, `asset_id`, `well_id`, 14 SCADA quoted sensor channels, standardized snake_case metrics, `operating_state`, `trip_cause`, `raw_payload`, `payload_json` |
| **2** | `opg_normalized_telemetry` | Pre-computed feature store & scaled sensors (replaces `normalized.db`) | `raw_id`, `Wells`, `Cluster`, `Source_File`, derived physics (`Delta_P_PSI`, `Torque_Proxy_A_Hz`, `Power_kVA`, `Thermal_Elevation_C`), scaled `[0, 1]` features, `health_index`, `fault_diagnosis` |
| **3** | `ml_results` | Real-time dual-tier ML model inferences (replaces `mlresults.db`) | `health_score`, `health_status`, `fault_diagnosis`, `canonical_verdict`, `is_anomalous`, `anomaly_score`, `confidence`, `root_cause_drivers`, `subsystem_scores`, snapshot metrics |
| **4** | `events` | Alarm logs, trips, deduplication, and sensor snapshots (replaces `esp_events.db`) | `event_id`, `trip_cause`, `alarms`, `severity`, `payload`, `snapshot_status`, `snapshot_pre_json`, `snapshot_post_json`, `ml_context_json` |
| **5** | `esp_agent_plans` | Agent Jane V2 dynamic execution plans & HITL governance (replaces `PlanRepository`) | `run_id`, `thread_id`, `query_intent`, `steps`, `run_card`, `requires_human_approval`, `approval_token`, `is_approved`, `audit_trail`, `synthesized_advisory`, `status` |
| **6** | `conversation_sessions` | Agent multi-turn conversation memory store | `session_id`, `turns` (JSONB), `updated_at` |

---

## 5. Useful Verification Commands

* **CLI Connect as `esp_admin`**:
  ```powershell
  & "C:\Program Files\PostgreSQL\16\bin\psql.exe" -U esp_admin -h 127.0.0.1 -p 5433 -d esp_apm_db
  ```
* **Restart Service**:
  ```powershell
  Restart-Service postgresql*
  ```
* **Verify Listening Port**:
  ```powershell
  netstat -ano | findstr 5433
  ```
