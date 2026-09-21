import json
import logging
import aiosqlite
import os
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from backend.config import DB_PATH

logger = logging.getLogger("opg.database")

class Database:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._counts_cache = None
        self._counts_cache_time = 0.0

    async def _get_connection(self):
        conn = await aiosqlite.connect(self.db_path, timeout=10.0)
        await conn.execute("PRAGMA busy_timeout = 10000;")
        conn.row_factory = aiosqlite.Row
        return conn

    async def init_db(self):
        """Initialize SQLite tables and enable WAL mode for time-series optimization."""
        async with aiosqlite.connect(self.db_path, timeout=30.0) as db:
            await db.execute("PRAGMA journal_mode = WAL;")
            await db.execute("PRAGMA synchronous = NORMAL;")
            await db.execute("PRAGMA cache_size = -64000;")
            await db.execute("PRAGMA busy_timeout = 30000;")
            
            # Primary time-series telemetry table with full ESP parameters and Categorization (Labelled / Unlabelled)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS opg_well_telemetry (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    asset_id TEXT NOT NULL,
                    well_id TEXT NOT NULL,
                    topic TEXT DEFAULT '',
                    data_category TEXT DEFAULT 'LABELLED',   -- 'LABELLED' or 'UNLABELLED'
                    scenario TEXT DEFAULT 'normal',          -- scenario name (e.g. normal, undervoltage, gas_interference)
                    alarms TEXT DEFAULT '[]',                -- JSON list of alarms
                    alerts TEXT DEFAULT '[]',                -- JSON list of alerts
                    pressure_psi REAL DEFAULT 0.0,            -- Discharge Pressure legacy alias (PSI)
                    intake_pressure_psi REAL DEFAULT 0.0,     -- Inp bar/psi (PSI)
                    temperature_c REAL DEFAULT 0.0,           -- Legacy temperature alias (°C)
                    flow_rate_bpd REAL DEFAULT 0.0,           -- Liquid Flow Rate (BPD)
                    frequency_hz REAL DEFAULT 0.0,            -- Frequency (Hz)
                    motor_current_a REAL DEFAULT 0.0,         -- VSD Amps/Load (A)
                    motor_voltage_v REAL DEFAULT 0.0,         -- Volt (V)
                    vibration_g REAL DEFAULT 0.0,             -- Vibration G's-Vx (g)
                    water_cut_pct REAL DEFAULT 0.0,           -- Water Cut %
                    gas_flow_mscfd REAL DEFAULT 0.0,
                    choke_size_pct REAL DEFAULT 0.0,
                    operating_state TEXT DEFAULT 'running',   -- running / tripped / unlabelled
                    trip_cause TEXT DEFAULT '',               -- e.g. UNDER_VOLTAGE, GAS_LOCK_UNDERLOAD
                    status TEXT DEFAULT 'NORMAL',             -- NORMAL, WARNING, CRITICAL, UNLABELLED
                    raw_payload TEXT DEFAULT '{}',
                    created_at TEXT DEFAULT (STRFTIME('%Y-%m-%d %H:%M:%f', 'NOW')),
                    -- ── Native 14-parameter VFD columns (added for new broker schema) ──
                    discharge_pressure_psi REAL DEFAULT NULL, -- Disch pr. Bar/psi
                    intake_temperature_c REAL DEFAULT NULL,   -- Int temp °C
                    motor_temperature_c REAL DEFAULT NULL,    -- Motor temp °C
                    whp_psi REAL DEFAULT NULL,                -- WHP (PSI)
                    flp_psi REAL DEFAULT NULL,                -- FLP (PSI)
                    annulus_pressure_psi REAL DEFAULT NULL,   -- AP (PSI) — 14th parameter
                    leak_current_ct REAL DEFAULT NULL,        -- Leak Current Ct
                    dhg_current REAL DEFAULT NULL,            -- DHG Current
                    vfd_status INTEGER DEFAULT NULL           -- VFD STS (1=Running, 0=Stopped)
                );
            """)


            # Add any missing columns dynamically if upgrading existing table
            existing_cols = []
            async with db.execute("PRAGMA table_info(opg_well_telemetry)") as cursor:
                rows = await cursor.fetchall()
                existing_cols = [r[1] for r in rows]

            new_columns = [
                ("topic", "TEXT DEFAULT ''"),
                ("data_category", "TEXT DEFAULT 'LABELLED'"),
                ("scenario", "TEXT DEFAULT 'normal'"),
                ("alarms", "TEXT DEFAULT '[]'"),
                ("alerts", "TEXT DEFAULT '[]'"),
                ("pressure_psi", "REAL DEFAULT 0.0"),
                ("intake_pressure_psi", "REAL DEFAULT 0.0"),
                ("temperature_c", "REAL DEFAULT 0.0"),
                ("flow_rate_bpd", "REAL DEFAULT 0.0"),
                ("frequency_hz", "REAL DEFAULT 0.0"),
                ("motor_current_a", "REAL DEFAULT 0.0"),
                ("motor_voltage_v", "REAL DEFAULT 0.0"),
                ("vibration_g", "REAL DEFAULT 0.0"),
                ("water_cut_pct", "REAL DEFAULT 0.0"),
                ("gas_flow_mscfd", "REAL DEFAULT 0.0"),
                ("choke_size_pct", "REAL DEFAULT 0.0"),
                ("operating_state", "TEXT DEFAULT 'running'"),
                ("trip_cause", "TEXT DEFAULT ''"),
                ("status", "TEXT DEFAULT 'NORMAL'"),
                ("raw_payload", "TEXT DEFAULT '{}'"),
                ("created_at", "TEXT DEFAULT (STRFTIME('%Y-%m-%d %H:%M:%f', 'NOW'))"),
                # ── Native 14-parameter VFD columns (broker schema) ──
                # Present in CREATE TABLE above for fresh DBs, but older databases
                # (e.g. labelled.db) predate them; list here so init_db() self-heals
                # any existing table via idempotent ADD COLUMN. DEFAULT NULL preserves
                # every existing row untouched.
                ("discharge_pressure_psi", "REAL DEFAULT NULL"),
                ("intake_temperature_c", "REAL DEFAULT NULL"),
                ("motor_temperature_c", "REAL DEFAULT NULL"),
                ("whp_psi", "REAL DEFAULT NULL"),
                ("flp_psi", "REAL DEFAULT NULL"),
                ("annulus_pressure_psi", "REAL DEFAULT NULL"),
                ("leak_current_ct", "REAL DEFAULT NULL"),
                ("dhg_current", "REAL DEFAULT NULL"),
                ("vfd_status", "INTEGER DEFAULT NULL"),
            ]
            for col_name, col_def in new_columns:
                if col_name not in existing_cols:
                    try:
                        await db.execute(f"ALTER TABLE opg_well_telemetry ADD COLUMN {col_name} {col_def};")
                        logger.info(f"Added column {col_name} to opg_well_telemetry")
                    except Exception as e:
                        logger.debug(f"Column {col_name} migration note: {e}")

            # Indexes for fast asset-categorized queries
            await db.execute("CREATE INDEX IF NOT EXISTS idx_telemetry_asset_id_desc ON opg_well_telemetry(asset_id, id DESC);")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_telemetry_well_id_desc ON opg_well_telemetry(well_id, id DESC);")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_telemetry_cat_id_desc ON opg_well_telemetry(data_category, id DESC);")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_telemetry_asset_time ON opg_well_telemetry(asset_id, timestamp DESC);")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_telemetry_well_time ON opg_well_telemetry(well_id, timestamp DESC);")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_telemetry_category ON opg_well_telemetry(data_category, timestamp DESC);")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_telemetry_timestamp ON opg_well_telemetry(timestamp DESC);")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_telemetry_status ON opg_well_telemetry(status);")

            await db.commit()
            logger.info("Database schema initialized with ESP Time-Series structure and Categorization.")

    async def insert_telemetry_batch(self, records: List[Dict[str, Any]]) -> int:
        """Batch insert telemetry records for high throughput."""
        if not records:
            return 0
        async with aiosqlite.connect(self.db_path, timeout=30.0) as db:
            await db.execute("PRAGMA busy_timeout = 30000;")
            rows = []
            for r in records:
                alarms_val = r.get("alarms", [])
                alarms_str = alarms_val if isinstance(alarms_val, str) else json.dumps(alarms_val)

                alerts_val = r.get("alerts", [])
                alerts_str = alerts_val if isinstance(alerts_val, str) else json.dumps(alerts_val)

                raw_val = r.get("raw_payload", {})
                raw_str = raw_val if isinstance(raw_val, str) else json.dumps(raw_val)

                # Native VFD columns — safely coerce; None stays None (SQL NULL)
                def _f(v):
                    if v is None:
                        return None
                    try:
                        return float(v)
                    except (TypeError, ValueError):
                        return None

                rows.append((
                    r.get("timestamp", datetime.now(timezone.utc).isoformat()),
                    r.get("asset_id", "UNKNOWN"),
                    r.get("well_id", "UNKNOWN"),
                    r.get("topic", ""),
                    r.get("data_category", "LABELLED"),
                    r.get("scenario", "normal") or "normal",
                    alarms_str,
                    alerts_str,
                    float(r.get("pressure_psi", 0.0) or 0.0),
                    float(r.get("intake_pressure_psi", 0.0) or 0.0),
                    float(r.get("temperature_c", 0.0) or 0.0),
                    float(r.get("flow_rate_bpd", 0.0) or 0.0),
                    float(r.get("frequency_hz", 0.0) or 0.0),
                    float(r.get("motor_current_a", 0.0) or 0.0),
                    float(r.get("motor_voltage_v", 0.0) or 0.0),
                    float(r.get("vibration_g", 0.0) or 0.0),
                    float(r.get("water_cut_pct", 0.0) or 0.0),
                    float(r.get("gas_flow_mscfd", 0.0) or 0.0),
                    float(r.get("choke_size_pct", 0.0) or 0.0),
                    r.get("operating_state", "running"),
                    r.get("trip_cause", "") or "",
                    r.get("status", "NORMAL"),
                    raw_str,
                    # ── Native 14-parameter VFD columns (previously silently dropped) ──
                    _f(r.get("discharge_pressure_psi")),
                    _f(r.get("intake_temperature_c")),
                    _f(r.get("motor_temperature_c")),
                    _f(r.get("whp_psi")),
                    _f(r.get("flp_psi")),
                    _f(r.get("annulus_pressure_psi")),
                    _f(r.get("leak_current_ct")),
                    _f(r.get("dhg_current")),
                    int(r["vfd_status"]) if r.get("vfd_status") is not None else None,
                ))

            conn = await self._get_connection()
            try:
                await conn.executemany("""
                    INSERT INTO opg_well_telemetry (
                        timestamp, asset_id, well_id, topic,
                        data_category, scenario, alarms, alerts,
                        pressure_psi, intake_pressure_psi, temperature_c, flow_rate_bpd,
                        frequency_hz, motor_current_a, motor_voltage_v, vibration_g,
                        water_cut_pct, gas_flow_mscfd, choke_size_pct,
                        operating_state, trip_cause, status, raw_payload,
                        discharge_pressure_psi, intake_temperature_c, motor_temperature_c,
                        whp_psi, flp_psi, annulus_pressure_psi,
                        leak_current_ct, dhg_current, vfd_status
                    ) VALUES (
                        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                        ?, ?, ?, ?, ?, ?, ?, ?, ?
                    )
                """, rows)
                await conn.commit()
                return len(rows)
            finally:
                await conn.close()

    async def insert_telemetry(self, record: Dict[str, Any]) -> int:
        """Insert a single telemetry record."""
        return await self.insert_telemetry_batch([record])


    async def get_telemetry(
        self,
        asset_id: Optional[str] = None,
        well_id: Optional[str] = None,
        data_category: Optional[str] = None,
        scenario: Optional[str] = None,
        operating_state: Optional[str] = None,
        trip_cause: Optional[str] = None,
        alarm_filter: Optional[str] = None,
        pump_family: Optional[str] = None,
        status: Optional[str] = None,
        min_intake_pressure_psi: Optional[float] = None,
        max_temperature_c: Optional[float] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]:
        """Fetch telemetry with dynamic multi-type filters and pagination."""
        query = "SELECT * FROM opg_well_telemetry WHERE 1=1"
        count_query = "SELECT COUNT(*) FROM opg_well_telemetry WHERE 1=1"
        params = []
        count_params = []

        if data_category and data_category.strip() and data_category != "ALL":
            query += " AND data_category = ?"
            count_query += " AND data_category = ?"
            params.append(data_category.strip().upper())
            count_params.append(data_category.strip().upper())

        if scenario and scenario.strip() and scenario != "ALL":
            scen_val = scenario.strip()
            if scen_val.upper() in ["ANOMALIES_ONLY", "ANOMALIES", "FAULTS_ONLY"]:
                query += " AND (scenario != 'normal' AND scenario != '' AND scenario IS NOT NULL)"
                count_query += " AND (scenario != 'normal' AND scenario != '' AND scenario IS NOT NULL)"
            else:
                norm_scen = scen_val.lower().replace("-", "_").replace(" ", "_")
                query += " AND (scenario = ? OR LOWER(REPLACE(REPLACE(scenario, '-', '_'), ' ', '_')) = ?)"
                count_query += " AND (scenario = ? OR LOWER(REPLACE(REPLACE(scenario, '-', '_'), ' ', '_')) = ?)"
                params.extend([scen_val, norm_scen])
                count_params.extend([scen_val, norm_scen])

        if operating_state and operating_state.strip() and operating_state != "ALL":
            query += " AND LOWER(operating_state) = ?"
            count_query += " AND LOWER(operating_state) = ?"
            params.append(operating_state.strip().lower())
            count_params.append(operating_state.strip().lower())

        if trip_cause and trip_cause.strip() and trip_cause != "ALL":
            query += " AND trip_cause = ?"
            count_query += " AND trip_cause = ?"
            params.append(trip_cause.strip())
            count_params.append(trip_cause.strip())

        if alarm_filter and alarm_filter.strip() and alarm_filter != "ALL":
            af = alarm_filter.strip().upper()
            if af == "WITH_ALARMS":
                query += " AND alarms != '[]' AND alarms IS NOT NULL"
                count_query += " AND alarms != '[]' AND alarms IS NOT NULL"
            elif af == "NO_ALARMS":
                query += " AND (alarms = '[]' OR alarms IS NULL)"
                count_query += " AND (alarms = '[]' OR alarms IS NULL)"
            else:
                query += " AND alarms LIKE ?"
                count_query += " AND alarms LIKE ?"
                params.append(f"%{alarm_filter.strip()}%")
                count_params.append(f"%{alarm_filter.strip()}%")

        if pump_family and pump_family.strip() and pump_family != "ALL":
            pf = pump_family.strip()
            query += " AND asset_id LIKE ?"
            count_query += " AND asset_id LIKE ?"
            params.append(f"%{pf}%")
            count_params.append(f"%{pf}%")

        if asset_id and asset_id.strip() and asset_id != "ALL":
            query += " AND (asset_id = ? OR asset_id LIKE ?)"
            count_query += " AND (asset_id = ? OR asset_id LIKE ?)"
            params.extend([asset_id.strip(), f"%{asset_id.strip()}%"])
            count_params.extend([asset_id.strip(), f"%{asset_id.strip()}%"])

        if well_id and well_id.strip() and well_id != "ALL":
            query += " AND (well_id = ? OR well_id LIKE ? OR asset_id LIKE ?)"
            count_query += " AND (well_id = ? OR well_id LIKE ? OR asset_id LIKE ?)"
            params.extend([well_id.strip(), f"%{well_id.strip()}%", f"%{well_id.strip()}%"])
            count_params.extend([well_id.strip(), f"%{well_id.strip()}%", f"%{well_id.strip()}%"])

        if status and status.strip() and status != "ALL":
            query += " AND status = ?"
            count_query += " AND status = ?"
            params.append(status.strip())
            count_params.append(status.strip())

        if min_intake_pressure_psi is not None:
            query += " AND intake_pressure_psi >= ?"
            count_query += " AND intake_pressure_psi >= ?"
            params.append(min_intake_pressure_psi)
            count_params.append(min_intake_pressure_psi)

        if max_temperature_c is not None:
            query += " AND temperature_c <= ?"
            count_query += " AND temperature_c <= ?"
            params.append(max_temperature_c)
            count_params.append(max_temperature_c)

        if start_time and start_time.strip():
            query += " AND timestamp >= ?"
            count_query += " AND timestamp >= ?"
            params.append(start_time.strip())
            count_params.append(start_time.strip())

        if end_time and end_time.strip():
            query += " AND timestamp <= ?"
            count_query += " AND timestamp <= ?"
            params.append(end_time.strip())
            count_params.append(end_time.strip())

        if search and search.strip():
            search_param = f"%{search.strip()}%"
            query += " AND (asset_id LIKE ? OR well_id LIKE ? OR topic LIKE ? OR trip_cause LIKE ? OR operating_state LIKE ? OR scenario LIKE ?)"
            count_query += " AND (asset_id LIKE ? OR well_id LIKE ? OR topic LIKE ? OR trip_cause LIKE ? OR operating_state LIKE ? OR scenario LIKE ?)"
            params.extend([search_param, search_param, search_param, search_param, search_param, search_param])
            count_params.extend([search_param, search_param, search_param, search_param, search_param, search_param])

        query += " ORDER BY id DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        conn = await self._get_connection()
        try:
            total = 0
            if count_params:
                try:
                    async with conn.execute(count_query, count_params) as c_cursor:
                        row = await c_cursor.fetchone()
                        total = row[0] if row else 0
                except Exception:
                    total = 0
            else:
                try:
                    async with conn.execute("SELECT MAX(id) FROM opg_well_telemetry") as c_cursor:
                        row = await c_cursor.fetchone()
                        total = row[0] if (row and row[0] is not None) else 0
                except Exception:
                    total = 0

            async with conn.execute(query, params) as cursor:
                rows = await cursor.fetchall()
                data = [dict(r) for r in rows]

            return {
                "total": total,
                "limit": limit,
                "offset": offset,
                "records": data
            }
        finally:
            await conn.close()

    async def get_database_detailed_stats(self) -> Dict[str, Any]:
        """Compute file size and total records in O(1) microseconds."""
        import os
        size_bytes = 0
        if os.path.exists(self.db_path):
            size_bytes = os.path.getsize(self.db_path)
            
        size_formatted = f"{round(size_bytes / (1024 * 1024), 2)} MB" if size_bytes > 1024 * 1024 else f"{round(size_bytes / 1024, 1)} KB"
        
        conn = await self._get_connection()
        try:
            async with conn.execute("SELECT MAX(id) FROM opg_well_telemetry") as cur:
                row = await cur.fetchone()
                total_records = row[0] if (row and row[0] is not None) else 0
        except Exception:
            total_records = 0
        finally:
            await conn.close()
            
        return {
            "db_path": str(self.db_path),
            "db_file_size_bytes": size_bytes,
            "db_file_size_formatted": size_formatted,
            "total_records": total_records,
            "total_assets": 26,
            "total_wells": 26
        }

    async def get_asset_summary(self) -> List[Dict[str, Any]]:
        """Get summary metrics grouped by Asset ID and Well ID."""
        query = """
            SELECT 
                asset_id,
                well_id,
                COUNT(*) as total_records,
                SUM(CASE WHEN data_category = 'LABELLED' THEN 1 ELSE 0 END) as labelled_records,
                SUM(CASE WHEN data_category = 'UNLABELLED' THEN 1 ELSE 0 END) as unlabelled_records,
                MAX(timestamp) as last_seen,
                AVG(pressure_psi) as avg_pressure,
                AVG(intake_pressure_psi) as avg_intake_pressure,
                AVG(temperature_c) as avg_temperature,
                AVG(flow_rate_bpd) as avg_flow_rate,
                AVG(frequency_hz) as avg_frequency,
                AVG(motor_current_a) as avg_current,
                AVG(vibration_g) as avg_vibration,
                operating_state as latest_operating_state,
                trip_cause as latest_trip_cause,
                status as latest_status
            FROM opg_well_telemetry
            GROUP BY asset_id, well_id
            ORDER BY asset_id ASC, well_id ASC;
        """
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(query) as cursor:
                rows = await cursor.fetchall()
                return [dict(r) for r in rows]

    async def get_distinct_assets(self) -> List[str]:
        """Fetch distinct Asset IDs."""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT DISTINCT asset_id FROM opg_well_telemetry ORDER BY asset_id ASC") as cursor:
                rows = await cursor.fetchall()
                return [r[0] for r in rows if r[0]]

    async def get_distinct_wells(self, asset_id: Optional[str] = None) -> List[str]:
        """Fetch distinct Well IDs, optionally filtered by asset."""
        query = "SELECT DISTINCT well_id FROM opg_well_telemetry"
        params = []
        if asset_id and asset_id != "ALL":
            query += " WHERE asset_id = ?"
            params.append(asset_id)
        query += " ORDER BY well_id ASC"
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(query, params) as cursor:
                rows = await cursor.fetchall()
                return [r[0] for r in rows if r[0]]

    async def get_timeseries_chart_data(self, asset_id: Optional[str] = None, well_id: Optional[str] = None, limit: int = 60) -> List[Dict[str, Any]]:
        """Fetch chronological time-series points for dashboard charts."""
        query = """
            SELECT id, timestamp, asset_id, well_id, data_category, scenario, pressure_psi, intake_pressure_psi,
                   temperature_c, flow_rate_bpd, frequency_hz, motor_current_a, motor_voltage_v,
                   vibration_g, water_cut_pct, operating_state, trip_cause, status
            FROM opg_well_telemetry WHERE 1=1
        """
        params = []
        if asset_id and asset_id != "ALL":
            query += " AND asset_id = ?"
            params.append(asset_id)
        if well_id and well_id != "ALL":
            query += " AND well_id = ?"
            params.append(well_id)
            
        query += " ORDER BY id DESC LIMIT ?"
        params.append(limit)

        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(query, params) as cursor:
                rows = await cursor.fetchall()
                data = [dict(r) for r in rows]
                data.reverse()
                return data

    async def get_total_counts(self) -> Dict[str, Any]:
        """Fetch top-level KPI metrics with 5s caching to prevent disk locking on large DBs."""
        import time
        now = time.time()
        if self._counts_cache is not None and (now - self._counts_cache_time) < 5.0:
            return self._counts_cache

        try:
            async with aiosqlite.connect(self.db_path, timeout=5.0) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute("""
                    SELECT 
                        COUNT(*) as total_records,
                        SUM(CASE WHEN data_category = 'LABELLED' THEN 1 ELSE 0 END) as total_labelled,
                        SUM(CASE WHEN data_category = 'UNLABELLED' THEN 1 ELSE 0 END) as total_unlabelled,
                        COUNT(DISTINCT asset_id) as total_assets,
                        COUNT(DISTINCT well_id) as total_wells,
                        MAX(timestamp) as last_ingested_at,
                        SUM(CASE WHEN status != 'NORMAL' AND data_category = 'LABELLED' THEN 1 ELSE 0 END) as total_alerts
                    FROM opg_well_telemetry
                """) as cursor:
                    row = await cursor.fetchone()
                    result = dict(row) if row else {
                        "total_records": 0, "total_labelled": 0, "total_unlabelled": 0,
                        "total_assets": 0, "total_wells": 0, "last_ingested_at": None, "total_alerts": 0
                    }
                    self._counts_cache = result
                    self._counts_cache_time = now
                    return result
        except Exception as ex:
            logger.warning(f"Error querying get_total_counts: {ex}")
            if self._counts_cache is not None:
                return self._counts_cache
            return {
                "total_records": 0, "total_labelled": 0, "total_unlabelled": 0,
                "total_assets": 0, "total_wells": 0, "last_ingested_at": None, "total_alerts": 0
            }

    async def get_database_detailed_stats(self) -> Dict[str, Any]:
        """Fetch comprehensive database storage metrics, file size on disk, categorized counts, and asset-wise breakdown."""
        db_size_bytes = 0
        wal_size_bytes = 0
        try:
            if os.path.exists(self.db_path):
                db_size_bytes = os.path.getsize(self.db_path)
            wal_path = f"{self.db_path}-wal"
            if os.path.exists(wal_path):
                wal_size_bytes = os.path.getsize(wal_path)
        except Exception as e:
            logger.error(f"Error checking DB file size: {e}")

        total_bytes = db_size_bytes + wal_size_bytes
        if total_bytes < 1024:
            size_formatted = f"{total_bytes} B"
        elif total_bytes < 1024 * 1024:
            size_formatted = f"{total_bytes / 1024:.2f} KB"
        else:
            size_formatted = f"{total_bytes / (1024 * 1024):.2f} MB"

        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row

            async with db.execute("""
                SELECT 
                    COUNT(*) as total_records,
                    SUM(CASE WHEN data_category = 'LABELLED' THEN 1 ELSE 0 END) as total_labelled,
                    SUM(CASE WHEN data_category = 'UNLABELLED' THEN 1 ELSE 0 END) as total_unlabelled,
                    MIN(timestamp) as first_record_time,
                    MAX(timestamp) as latest_record_time,
                    COUNT(DISTINCT asset_id) as total_assets,
                    COUNT(DISTINCT well_id) as total_wells,
                    SUM(CASE WHEN status = 'NORMAL' THEN 1 ELSE 0 END) as count_normal,
                    SUM(CASE WHEN status = 'WARNING' THEN 1 ELSE 0 END) as count_warning,
                    SUM(CASE WHEN status = 'CRITICAL' THEN 1 ELSE 0 END) as count_critical
                FROM opg_well_telemetry
            """) as cursor:
                summary_row = await cursor.fetchone()
                summary = dict(summary_row) if summary_row else {}

            total_records = summary.get("total_records") or 0

            # Scenario breakdown for Labelled records
            async with db.execute("""
                SELECT scenario, COUNT(*) as scenario_count
                FROM opg_well_telemetry
                WHERE data_category = 'LABELLED' AND scenario IS NOT NULL AND scenario != ''
                GROUP BY scenario
                ORDER BY scenario_count DESC
            """) as cursor:
                scen_rows = await cursor.fetchall()
                scenario_breakdown = {r[0]: r[1] for r in scen_rows}

            async with db.execute("""
                SELECT 
                    asset_id,
                    COUNT(*) as record_count,
                    SUM(CASE WHEN data_category = 'LABELLED' THEN 1 ELSE 0 END) as labelled_count,
                    SUM(CASE WHEN data_category = 'UNLABELLED' THEN 1 ELSE 0 END) as unlabelled_count,
                    COUNT(DISTINCT well_id) as well_count,
                    MIN(timestamp) as first_seen,
                    MAX(timestamp) as last_seen,
                    AVG(pressure_psi) as avg_discharge_p,
                    AVG(intake_pressure_psi) as avg_intake_p,
                    AVG(flow_rate_bpd) as avg_flow,
                    AVG(temperature_c) as avg_temp,
                    AVG(frequency_hz) as avg_freq,
                    AVG(motor_current_a) as avg_current,
                    SUM(CASE WHEN status = 'NORMAL' THEN 1 ELSE 0 END) as normal_count,
                    SUM(CASE WHEN status = 'WARNING' THEN 1 ELSE 0 END) as warning_count,
                    SUM(CASE WHEN status = 'CRITICAL' THEN 1 ELSE 0 END) as critical_count
                FROM opg_well_telemetry
                GROUP BY asset_id
                ORDER BY record_count DESC
            """) as cursor:
                asset_rows = await cursor.fetchall()
                asset_breakdown = []
                for row in asset_rows:
                    item = dict(row)
                    rec_count = item.get("record_count", 0)
                    pct = round((rec_count / total_records * 100), 1) if total_records > 0 else 0.0
                    item["percent_of_total"] = pct
                    asset_breakdown.append(item)

        return {
            "total_records": total_records,
            "total_labelled": summary.get("total_labelled") or 0,
            "total_unlabelled": summary.get("total_unlabelled") or 0,
            "db_file_size_bytes": total_bytes,
            "db_file_size_formatted": size_formatted,
            "first_record_time": summary.get("first_record_time"),
            "latest_record_time": summary.get("latest_record_time"),
            "total_assets": summary.get("total_assets") or 0,
            "total_wells": summary.get("total_wells") or 0,
            "scenario_breakdown": scenario_breakdown,
            "status_counts": {
                "NORMAL": summary.get("count_normal") or 0,
                "WARNING": summary.get("count_warning") or 0,
                "CRITICAL": summary.get("count_critical") or 0
            },
            "asset_breakdown": asset_breakdown
        }

    async def clear_data(self):
        """Truncate telemetry data."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM opg_well_telemetry;")
            await db.execute("DELETE FROM sqlite_sequence WHERE name='opg_well_telemetry';")
            await db.commit()
            logger.info(f"Cleared all telemetry records from {self.db_path}.")

from backend.config import LABELLED_DB_PATH, UNLABELLED_DB_PATH
labelled_db = Database(LABELLED_DB_PATH)
unlabelled_db = Database(UNLABELLED_DB_PATH)
db = unlabelled_db  # Main operations use unlabelled ground truth

def get_database(db_type: str = "unlabelled") -> Database:
    if str(db_type).lower() in ("labelled", "label"):
        return labelled_db
    return unlabelled_db

