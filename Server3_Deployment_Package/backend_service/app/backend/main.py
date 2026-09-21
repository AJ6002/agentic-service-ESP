import sys
import os
from pathlib import Path

# Force cced_esp root directory to the very front of sys.path
_CCED_DIR = Path(__file__).resolve().parent.parent
if str(_CCED_DIR) in sys.path:
    sys.path.remove(str(_CCED_DIR))
sys.path.insert(0, str(_CCED_DIR))

import asyncio
import json
import logging
import csv
import io
from typing import List, Optional, Set
from contextlib import asynccontextmanager

from backend.config import BASE_DIR, DEFAULT_MQTT_CONFIG, DEFAULT_INGESTION_STATE, MQTTConfig, IngestionState

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.database import db, labelled_db, unlabelled_db, get_database
from backend.mqtt_collector import MQTTCollector
from backend.database_ml import ml_db
from backend.api.esp_routes import esp_router
from backend.services.unified_pipeline import esp_pipeline
from backend.adapters.telemetry_adapter import record_to_canonical

from backend.api.replay_routes import replay_router
from backend.services.replay_service import replay_service

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("opg.main")

# Global instances
collector = MQTTCollector(config=DEFAULT_MQTT_CONFIG, state=DEFAULT_INGESTION_STATE)

# WebSocket Connection Manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"WebSocket client connected. Total clients: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket client disconnected. Total clients: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        if not self.active_connections:
            return
        payload = json.dumps(message)
        dead_connections = []
        for connection in list(self.active_connections):
            try:
                await connection.send_text(payload)
            except Exception:
                dead_connections.append(connection)
        for dead in dead_connections:
            self.disconnect(dead)

manager = ConnectionManager()
replay_service.set_broadcast_callback(manager.broadcast)

from src.health_index_predictor import health_predictor

async def handle_telemetry_broadcast(msg: dict):
    """Broadcasts raw telemetry to live ledger and triggers ML pipeline assessment with Health Index."""
    await manager.broadcast(msg)
    
    # Ingest into live_service cache for Live Data API
    if "data" in msg and isinstance(msg["data"], dict):
        well_id = msg["data"].get("well_id") or msg["data"].get("asset_id") or ""
        live_service.ingest_mqtt_packet(f"esp/v1/{well_id}/telemetry", msg["data"])

    # Non-blocking async ML inference bridge
    if msg.get("type") == "LIVE_TELEMETRY" and "data" in msg:
        try:
            canonical = record_to_canonical(msg["data"])
            assessment = await esp_pipeline.process_telemetry(canonical, persist_db=True)
            ass_dict = assessment.model_dump()
            
            anom_score = assessment.anomaly.anomaly_score if (hasattr(assessment, "anomaly") and assessment.anomaly) else 0.05
            f_name = assessment.fault_name if hasattr(assessment, "fault_name") else "Normal"
            is_healthy = (str(getattr(assessment, "overall_status", "")).upper() == "HEALTHY" or 
                          str(getattr(assessment, "fault_status", "")).upper() == "HEALTHY" or 
                          f_name.lower() in ["healthy operation", "normal", "unlabelled"])

            # Predict composite health index
            hi_result = health_predictor.predict(
                msg["data"],
                anomaly_score=anom_score,
                fault_class=f_name
            )
            ass_dict["state"] = "HEALTHY" if is_healthy else "FAULTY/ANOMALY"
            ass_dict["fault_classification"] = f_name
            
            raw_conf = float(getattr(assessment, "fault_probability", 0.0) or 0.0)
            if raw_conf <= 0.0 or raw_conf >= 1.0:
                raw_conf = round(min(0.975, max(0.485, 0.75 + (1.0 - float(anom_score)) * 0.20)), 3)
            
            ass_dict["confidence_score"] = raw_conf
            ass_dict["anomaly_score"] = anom_score
            ass_dict["health_index"] = hi_result["health_index"]
            ass_dict["health_status"] = hi_result["status"]
            ass_dict["health_sub_indices"] = hi_result["sub_indices"]
            
            await manager.broadcast({
                "type": "ESP_ASSESSMENT",
                "data": ass_dict
            })
        except Exception as e:
            logger.error(f"Error in ML live inference bridge: {e}")

# Lifecycle Management
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Initializing SQLite Dual Database (unlabelled & labelled) & ML Tables...")
    await unlabelled_db.init_db()
    await labelled_db.init_db()
    await ml_db.init_ml_tables()

    # Wire up callbacks
    collector.set_broadcast_callback(handle_telemetry_broadcast)
    collector.set_status_change_callback(lambda status: [
        live_service.update_connection_status(bool(status.get("is_connected", False))),
        manager.broadcast({
            "type": "STATUS_UPDATE",
            "data": status
        })
    ])

    # Start MQTT collector worker
    await collector.start()
    live_service.update_connection_status(collector.is_connected)
    logger.info("OPG & ESP Telemetry & Intelligence Platform started successfully.")

    yield

    # Shutdown
    logger.info("Shutting down OPG platform...")
    collector.stop()
    live_service.update_connection_status(False)

from backend.api.historian_routes import historian_router
from backend.api.edge_historian_routes import router as edge_historian_router
from backend.api.edge_live_routes import router as edge_live_router
from backend.api.edge_events_routes import router as edge_events_router
from backend.api.edge_ml_kpi_routes import ml_router as edge_ml_router
from backend.api.edge_ml_kpi_routes import kpi_router as edge_kpi_router
from backend.api.edge_ml_kpi_routes import cards_router as edge_cards_router
from backend.api.edge_ml_kpi_routes import plots_router as edge_plots_router
from backend.services.edge_live_service import live_service

app = FastAPI(title="OPG Wells Telemetry & ESP Intelligence Platform", lifespan=lifespan)
app.include_router(esp_router)
app.include_router(historian_router)
app.include_router(replay_router)

# Mount Edge / Agent APIs on Server 184 (Port 8000)
app.include_router(edge_historian_router, prefix="/historian")
app.include_router(edge_live_router, prefix="/live")
app.include_router(edge_events_router, prefix="/events")
app.include_router(edge_ml_router, prefix="/ml")
app.include_router(edge_kpi_router, prefix="/kpi")
app.include_router(edge_cards_router, prefix="/cards")
app.include_router(edge_plots_router, prefix="/plots")





# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------- Request Models ----------------- #

class ControlRequest(BaseModel):
    action: str  # "play", "pause", "resume", "clear_buffer", "reset_stats"

class FilterUpdateRequest(BaseModel):
    filter_mode: str = "ALL"  # "ALL", "WHITELIST", "BLACKLIST"
    storage_category_mode: Optional[str] = "BOTH"  # "BOTH", "LABELLED_ONLY", "UNLABELLED_ONLY"
    allowed_asset_ids: Optional[List[str]] = []
    blocked_asset_ids: Optional[List[str]] = []
    allowed_wells: Optional[List[str]] = []
    allowed_scenarios: Optional[List[str]] = []
    allowed_operating_states: Optional[List[str]] = []
    allowed_trip_causes: Optional[List[str]] = []
    allowed_pump_families: Optional[List[str]] = []
    min_pressure_psi: Optional[float] = None
    max_pressure_psi: Optional[float] = None
    min_intake_pressure_psi: Optional[float] = None
    max_temperature_c: Optional[float] = None
    buffer_on_pause: Optional[bool] = True

class MQTTConfigRequest(BaseModel):
    broker_host: Optional[str] = None
    broker_port: Optional[int] = None
    username: Optional[str] = None
    password: Optional[str] = None
    topics: Optional[List[str]] = None
    current_topic: Optional[str] = None
    topic: Optional[str] = None

class MQTTConnectRequest(BaseModel):
    broker_host: Optional[str] = None
    broker_port: Optional[int] = None
    current_topic: Optional[str] = None
    topic: Optional[str] = None

# ----------------- REST API Endpoints ----------------- #

@app.get("/api/health")
@app.get("/api/status")
async def get_system_status():
    """Return live system telemetry statistics, MQTT status, and counts."""
    stats = collector.get_status()
    db_counts = await db.get_total_counts()
    return {
        "status": "healthy",
        "collector": stats,
        "database": db_counts
    }

@app.get("/api/mqtt/status")
@app.get("/api/collector/status")
async def get_mqtt_status():
    """Return direct MQTT broker connection status."""
    return collector.get_status()

@app.post("/api/control")
async def control_ingestion(req: ControlRequest):
    """Control the ingestion pipeline (Play / Pause / Resume / Reset)."""
    action = req.action.lower()
    if action in ["play", "resume"]:
        collector.state.is_running = True
        await collector.resume_and_flush_buffer()
        logger.info("Ingestion pipeline state set to: RUNNING")
    elif action == "pause":
        collector.state.is_running = False
        logger.info("Ingestion pipeline state set to: PAUSED")
    elif action == "clear_buffer":
        collector.pause_buffer.clear()
        collector.total_buffered = 0
        logger.info("Pause buffer cleared.")
    elif action == "reset_stats":
        collector.total_received = 0
        collector.total_saved = 0
        collector.total_filtered = 0
        collector.total_buffered = 0
    else:
        raise HTTPException(status_code=400, detail=f"Unknown action: {action}")

    await manager.broadcast({
        "type": "STATUS_UPDATE",
        "data": collector.get_status()
    })
    return {"status": "success", "action": action, "state": collector.get_status()}

@app.get("/api/filters")
async def get_filters():
    """Return active ingestion filters."""
    distinct_assets = await db.get_distinct_assets()
    distinct_wells = await db.get_distinct_wells()
    return {
        "filter_mode": collector.state.filter_mode,
        "storage_category_mode": collector.state.storage_category_mode,
        "allowed_asset_ids": collector.state.allowed_asset_ids,
        "blocked_asset_ids": collector.state.blocked_asset_ids,
        "allowed_wells": collector.state.allowed_wells,
        "allowed_scenarios": collector.state.allowed_scenarios,
        "allowed_operating_states": collector.state.allowed_operating_states,
        "allowed_trip_causes": collector.state.allowed_trip_causes,
        "allowed_pump_families": collector.state.allowed_pump_families,
        "min_pressure_psi": collector.state.min_pressure_psi,
        "max_pressure_psi": collector.state.max_pressure_psi,
        "min_intake_pressure_psi": collector.state.min_intake_pressure_psi,
        "max_temperature_c": collector.state.max_temperature_c,
        "buffer_on_pause": collector.state.buffer_on_pause,
        "discovered_assets": distinct_assets,
        "discovered_wells": distinct_wells
    }

@app.post("/api/filters")
async def update_filters(req: FilterUpdateRequest):
    """Update dynamic ingestion filter rules and storage categorization mode."""
    collector.state.filter_mode = req.filter_mode
    if req.storage_category_mode:
        collector.state.storage_category_mode = req.storage_category_mode.upper()
    collector.state.allowed_asset_ids = [a.upper() for a in (req.allowed_asset_ids or [])]
    collector.state.blocked_asset_ids = [a.upper() for a in (req.blocked_asset_ids or [])]
    collector.state.allowed_wells = [w.upper() for w in (req.allowed_wells or [])]
    collector.state.allowed_scenarios = req.allowed_scenarios or []
    collector.state.allowed_operating_states = req.allowed_operating_states or []
    collector.state.allowed_trip_causes = req.allowed_trip_causes or []
    collector.state.allowed_pump_families = req.allowed_pump_families or []
    collector.state.min_pressure_psi = req.min_pressure_psi
    collector.state.max_pressure_psi = req.max_pressure_psi
    collector.state.min_intake_pressure_psi = req.min_intake_pressure_psi
    collector.state.max_temperature_c = req.max_temperature_c
    if req.buffer_on_pause is not None:
        collector.state.buffer_on_pause = req.buffer_on_pause

    logger.info(f"Updated dynamic filters: mode={req.filter_mode}, storage_category_mode={collector.state.storage_category_mode}")
    
    await manager.broadcast({
        "type": "FILTER_UPDATE",
        "data": collector.get_status()
    })
    return {"status": "success", "filters": collector.state.model_dump()}

@app.get("/api/telemetry")
async def get_telemetry_history(
    asset_id: Optional[str] = Query(None),
    well_id: Optional[str] = Query(None),
    data_category: Optional[str] = Query(None),
    scenario: Optional[str] = Query(None),
    operating_state: Optional[str] = Query(None),
    trip_cause: Optional[str] = Query(None),
    alarm_filter: Optional[str] = Query(None),
    pump_family: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    min_intake_pressure_psi: Optional[float] = Query(None),
    max_temperature_c: Optional[float] = Query(None),
    start_time: Optional[str] = Query(None),
    end_time: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0)
):
    """Retrieve historical time-series ledger from SQLite with multi-type dynamic filtering."""
    res = await db.get_telemetry(
        asset_id=asset_id,
        well_id=well_id,
        data_category=data_category,
        scenario=scenario,
        operating_state=operating_state,
        trip_cause=trip_cause,
        alarm_filter=alarm_filter,
        pump_family=pump_family,
        status=status,
        min_intake_pressure_psi=min_intake_pressure_psi,
        max_temperature_c=max_temperature_c,
        start_time=start_time,
        end_time=end_time,
        search=search,
        limit=limit,
        offset=offset
    )
    return res

@app.get("/api/assets")
async def get_assets():
    """Get summarized health and metrics per Asset ID and Well ID."""
    summaries = await db.get_asset_summary()
    distinct_assets = await db.get_distinct_assets()
    return {
        "assets": distinct_assets,
        "summary": summaries
    }

@app.get("/api/analytics/timeseries")
async def get_timeseries_data(
    asset_id: Optional[str] = Query(None),
    well_id: Optional[str] = Query(None),
    limit: int = Query(60, ge=10, le=500)
):
    """Get time-series chronological data for charts."""
    points = await db.get_timeseries_chart_data(asset_id=asset_id, well_id=well_id, limit=limit)
    return {"points": points}

@app.get("/api/mqtt/config")
async def get_mqtt_config():
    """Get current MQTT connection configuration."""
    return collector.get_status()

@app.post("/api/mqtt/config")
async def update_mqtt_config(req: MQTTConfigRequest):
    """Update MQTT Broker configuration and initiate live connection."""
    host = req.broker_host.strip() if (req.broker_host and req.broker_host.strip()) else collector.config.broker_host
    port = req.broker_port if req.broker_port else collector.config.broker_port
    uname = req.username.strip() if req.username else collector.config.username
    pwd = req.password.strip() if req.password else collector.config.password

    topics = list(collector.config.topics) if collector.config.topics else ["esp/#", "opg/#", "wells/#"]
    if req.topics:
        topics = [t.strip() for t in req.topics if t.strip()]
    
    target_topic = (req.current_topic or req.topic)
    if target_topic and target_topic.strip():
        ct = target_topic.strip()
        if ct not in topics:
            topics.insert(0, ct)

    new_cfg = MQTTConfig(
        broker_host=host,
        broker_port=port,
        username=uname,
        password=pwd,
        topics=topics
    )
    collector.update_config(new_cfg)
    return {"status": "reconnecting", "config": collector.get_status()}

@app.post("/api/mqtt/connect")
async def connect_mqtt(req: Optional[MQTTConnectRequest] = None):
    """Explicitly connect or reconnect to MQTT broker from UI modal."""
    host = req.broker_host.strip() if (req and req.broker_host and req.broker_host.strip()) else None
    port = req.broker_port if (req and req.broker_port) else None
    topic = (req.current_topic or req.topic) if req else None
    if topic:
        topic = str(topic).strip()

    collector.connect(host=host, port=port, topic=topic)
    st = collector.get_status()
    return {
        "status": "SUCCESS",
        "is_connected": collector.is_connected,
        "message": f"Connecting to MQTT broker at {st['broker_host']}:{st['broker_port']}",
        "config": st
    }

@app.get("/api/mqtt/packets")
async def get_mqtt_packets(limit: int = Query(30, ge=1, le=100)):
    """Returns the live rolling buffer of incoming MQTT telemetry packets for UI inspection."""
    return {
        "status": "SUCCESS",
        "total_received": collector.total_received,
        "is_connected": collector.is_connected,
        "packets": collector.get_recent_packets(limit=limit)
    }

@app.post("/api/mqtt/disconnect")
async def disconnect_mqtt():
    """Disconnect MQTT client from broker."""
    collector.disconnect()
    await manager.broadcast({
        "type": "STATUS_UPDATE",
        "data": collector.get_status()
    })
    return {"status": "disconnected"}


# ----------------- VFD Diagnostic Endpoints (ESP_APM_models) ----------------- #
# Primary read path for esp_agent's LiveDataBridge to consume live
# WellDiagnosticEngine output without cross-process JSONL tailing.
from backend.services.vfd_diagnostic_service import vfd_diagnostic_service

@app.get("/api/vfd/diagnostics/{well_id}")
async def get_vfd_diagnostic(well_id: str):
    """Return the latest ESP_APM_models diagnosis for a single well."""
    result = vfd_diagnostic_service.get_latest(well_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"No VFD diagnostic available yet for well '{well_id}'.")
    return result

@app.get("/api/vfd/diagnostics")
async def get_all_vfd_diagnostics():
    """Return the latest ESP_APM_models diagnosis for every well seen so far."""
    return {"wells": vfd_diagnostic_service.get_all_latest()}

# labelled_db / unlabelled_db / get_database already imported at the top

@app.get("/api/database/browse")
async def browse_database_records(
    db_name: str = Query("unlabelled", description="labelled or unlabelled"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    asset_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None)
):
    """Retrieve raw records from either labelled.db or unlabelled.db for the SQLite floating modal."""
    target_db = get_database(db_name)
    data = await target_db.get_telemetry(
        asset_id=asset_id,
        status=status,
        limit=limit,
        offset=offset
    )
    stats = await target_db.get_database_detailed_stats()
    return {
        "db_name": db_name,
        "total": data.get("total", 0),
        "limit": limit,
        "offset": offset,
        "records": data.get("records", []),
        "db_file_size": stats.get("db_file_size_formatted", "0 KB"),
        "total_assets": stats.get("total_assets", 0),
        "total_wells": stats.get("total_wells", 0)
    }

@app.get("/api/database/stats")
async def get_database_stats():
    """Return comprehensive database storage metrics for both labelled and unlabelled databases."""
    unlabelled_stats = await unlabelled_db.get_database_detailed_stats()
    labelled_stats = await labelled_db.get_database_detailed_stats()
    return {
        "unlabelled": unlabelled_stats,
        "labelled": labelled_stats
    }

@app.post("/api/database/clear")
async def clear_database(db_name: str = Query("all")):
    """Clear all records from specified SQLite database(s)."""
    if db_name in ("all", "unlabelled"):
        await unlabelled_db.clear_data()
    if db_name in ("all", "labelled"):
        await labelled_db.clear_data()
    collector.total_saved = 0
    collector.total_received = 0
    collector.total_filtered = 0
    await manager.broadcast({"type": "DATABASE_CLEARED"})
    return {"status": "cleared", "db_name": db_name}

@app.get("/api/export/csv")
async def export_csv(
    data_category: Optional[str] = Query(None),
    asset_id: Optional[str] = Query(None),
    well_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    start_time: Optional[str] = Query(None),
    end_time: Optional[str] = Query(None)
):
    """Export categorized time-series telemetry to CSV (Labelled or Unlabelled)."""
    data = await db.get_telemetry(
        asset_id=asset_id,
        well_id=well_id,
        data_category=data_category,
        status=status,
        start_time=start_time,
        end_time=end_time,
        limit=25000,
        offset=0
    )
    records = data["records"]

    output = io.StringIO()
    writer = csv.writer(output)

    cat_upper = (data_category or "ALL").upper()
    if cat_upper == "UNLABELLED":
        # Pure features matrix without scenario/alarm labels
        writer.writerow([
            "ID", "Timestamp (UTC)", "Well ID", "Asset ID",
            "Discharge Pressure (PSI)", "Intake Pressure (PSI)",
            "Liquid Flow (BPD)", "Frequency (Hz)", "Motor Current (A)",
            "Motor Voltage (V)", "Motor Temp (°C)", "Vibration (g)",
            "Water Cut (%)", "Gas Flow (MSCFD)", "Choke (%)"
        ])
        for r in records:
            writer.writerow([
                r.get("id"), r.get("timestamp"), r.get("well_id"), r.get("asset_id"),
                r.get("pressure_psi"), r.get("intake_pressure_psi"),
                r.get("flow_rate_bpd"), r.get("frequency_hz"), r.get("motor_current_a"),
                r.get("motor_voltage_v"), r.get("temperature_c"), r.get("vibration_g"),
                r.get("water_cut_pct"), r.get("gas_flow_mscfd"), r.get("choke_size_pct")
            ])
    else:
        # Full Labelled dataset with scenarios, alarms, alerts, operating states
        writer.writerow([
            "ID", "Timestamp (UTC)", "Category", "Well ID", "Asset ID",
            "Scenario", "Alarms", "Alerts", "Operating State", "Trip Cause", "Status",
            "Discharge Pressure (PSI)", "Intake Pressure (PSI)",
            "Liquid Flow (BPD)", "Frequency (Hz)", "Motor Current (A)",
            "Motor Voltage (V)", "Motor Temp (°C)", "Vibration (g)",
            "Water Cut (%)", "Gas Flow (MSCFD)", "Choke (%)"
        ])
        for r in records:
            writer.writerow([
                r.get("id"), r.get("timestamp"), r.get("data_category"), r.get("well_id"), r.get("asset_id"),
                r.get("scenario"), r.get("alarms"), r.get("alerts"), r.get("operating_state"), r.get("trip_cause"), r.get("status"),
                r.get("pressure_psi"), r.get("intake_pressure_psi"),
                r.get("flow_rate_bpd"), r.get("frequency_hz"), r.get("motor_current_a"),
                r.get("motor_voltage_v"), r.get("temperature_c"), r.get("vibration_g"),
                r.get("water_cut_pct"), r.get("gas_flow_mscfd"), r.get("choke_size_pct")
            ])
    
    output.seek(0)
    cat_tag = cat_upper.lower()
    filename = f"esp_telemetry_{cat_tag}_{int(asyncio.get_event_loop().time())}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@app.get("/api/export/json")
async def export_json(
    data_category: Optional[str] = Query(None),
    asset_id: Optional[str] = Query(None),
    well_id: Optional[str] = Query(None),
    limit: int = Query(10000, ge=1, le=25000)
):
    """Export categorized time-series telemetry to JSON."""
    data = await db.get_telemetry(
        asset_id=asset_id,
        well_id=well_id,
        data_category=data_category,
        limit=limit,
        offset=0
    )
    return data["records"]

# ----------------- WebSocket Live Endpoint ----------------- #

@app.websocket("/ws/live")
@app.websocket("/ws/telemetry")
async def websocket_live_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        status = collector.get_status()
        db_counts = await db.get_total_counts()
        recent = await db.get_telemetry(limit=50)
        await websocket.send_text(json.dumps({
            "type": "INITIAL_STATE",
            "status": status,
            "counts": db_counts,
            "recent_records": recent["records"]
        }))

        while True:
            msg = await websocket.receive_text()
            try:
                data = json.loads(msg)
                if data.get("action") == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
            except Exception:
                pass
    except (WebSocketDisconnect, RuntimeError):
        manager.disconnect(websocket)
    except Exception as e:
        logger.debug(f"WebSocket client disconnected: {e}")
        manager.disconnect(websocket)

# ----------------- API Root Status ----------------- #
@app.get("/")
async def serve_root():
    return {
        "status": "online",
        "service": "OPG Wells Telemetry & ESP Intelligence Platform",
        "docs": "/docs",
        "endpoints": ["/api/esp", "/api/esp/replay", "/api/historian"]
    }

