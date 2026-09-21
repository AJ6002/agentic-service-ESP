"""
Unified FastAPI REST Gateway for ESP Agentic Platform
Grounded in ESP_APM_PHASE_5_FINAL_Service_Tool_MCP_Implementation_Design.docx §12, §14

Mounts:
- GET /health, /readiness, /version
- /api/v1/assets (AssetContextService)
- /api/v1/telemetry (TelemetryService)
- /api/v1/engineering (EngineeringService)
- /api/v1/twin (DigitalTwinService)
- /api/v1/cases (CaseOutcomeService)
- /api/v1/audit (AuditService)
"""

import json
import asyncio
import sqlite3
import uuid
import time
import threading
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Any, Optional, List

logger = logging.getLogger("gateway")
from fastapi import FastAPI, Request, Response, HTTPException, Depends, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from shared.schemas.envelope import RESTEnvelope, ResponseMeta
from shared.schemas.errors import ServiceErrorPayload, ErrorDetail

from src.services.asset_context_service import AssetContextService
from src.services.telemetry_service import TelemetryService
from src.services.engineering_service import EngineeringService
from src.services.twin_service import DigitalTwinService
from src.services.case_service import CaseOutcomeService
from src.services.audit_service import AuditService
from src.policy.policy_engine import PolicyEngine

from shared.schemas.telemetry import IngestTelemetryRequest
from shared.schemas.engineering import TDHRequest, BEPRequest, DrawdownRequest
from shared.schemas.twin import FrequencyWhatIfRequest, WaterCutWhatIfRequest, OptimizationRequest
from shared.schemas.case import CaseSearchRequest, OutcomeCapturePayload
from shared.schemas.audit import AdvisoryAuditPayload, ToolCallAuditPayload

from src.api.rest.evidence_routes import router as evidence_router
from src.api.rest.bff_routes import router as bff_router
from src.mcp.rest_facade import router as mcp_router
from src.api.rest.esp_routes import router as esp_router
from src.api.rest.agent_ws_routes import router as agent_ws_router

app = FastAPI(
    title="ESP APM Application Services Gateway",
    version="1.0.0",
    description="Unified REST Gateway exposing versioned domain application services."
)

app.include_router(evidence_router)
app.include_router(bff_router)
app.include_router(mcp_router)
app.include_router(esp_router)
app.include_router(agent_ws_router)

@app.api_route("/warmup", methods=["GET", "POST"])
@app.api_route("/api/agent/warmup", methods=["GET", "POST"])
async def agent_warmup_endpoint():
    return {"status": "ok", "message": "Agent gateway ready."}

# Mount the native MCP server (streamable-HTTP) when the optional `mcp` package is present.
# The REST facade at /api/mcp always works; this adds an MCP-protocol endpoint at /mcp for
# MCP-native clients (Claude Desktop, Kiro, etc.). Gracefully skipped if `mcp` is unavailable.
try:
    from src.mcp.mcp_server import build_streamable_http_app
    _mcp_app = build_streamable_http_app()
    if _mcp_app is not None:
        app.mount("/mcp", _mcp_app)
except Exception as _mcp_exc:  # pragma: no cover - defensive, never block gateway startup
    import logging as _logging
    _logging.getLogger(__name__).warning("MCP native server not mounted: %s", _mcp_exc)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def rewrite_agent_path_middleware(request: Request, call_next):
    # Support both /api/agent/* and /api/ui/* seamlessly
    path = request.url.path
    if path.startswith("/api/agent/") and path != "/api/agent/warmup":
        sub = path[len("/api/agent/"):]
        if not sub.startswith("agent/") and not sub.startswith("ui/"):
            new_path = f"/api/ui/{sub}"
        elif sub.startswith("agent/"):
            new_path = f"/api/ui/{sub}"
        else:
            new_path = f"/api/{sub}"
        request.scope["path"] = new_path
    response = await call_next(request)
    return response


_ACTIVE_CLIENTS: Dict[WebSocket, asyncio.Queue] = {}
_ACTIVE_WEBSOCKETS = set()
_MAIN_ASYNCIO_LOOP = None
_LIVE_COUNTS_CACHE = None
_LIVE_COUNTS_CACHE_TIME = 0.0
_LIVE_COUNTS_LOCK = threading.Lock()

def _enqueue_ws_payload(q: asyncio.Queue, payload: str):
    """Safely enqueues a payload for a websocket client, dropping oldest message if full."""
    try:
        if q.full():
            try:
                q.get_nowait()
            except Exception:
                pass
        q.put_nowait(payload)
    except Exception:
        pass

async def _ws_client_sender_worker(ws: WebSocket, q: asyncio.Queue):
    """Dedicated single sender task per WebSocket to eliminate concurrent send_text race conditions."""
    try:
        while True:
            payload = await q.get()
            await ws.send_text(payload)
            q.task_done()
    except Exception:
        pass
    finally:
        _ACTIVE_CLIENTS.pop(ws, None)
        _ACTIVE_WEBSOCKETS.discard(ws)

def _to_json_primitives(val: Any) -> Any:
    """Recursively converts NumPy scalar numbers, ndarrays, and non-primitive types to native Python primitives."""
    if isinstance(val, dict):
        return {k: _to_json_primitives(v) for k, v in val.items()}
    if isinstance(val, (list, tuple, set)):
        return [_to_json_primitives(x) for x in val]
    if hasattr(val, "tolist") and callable(val.tolist):
        return _to_json_primitives(val.tolist())
    if hasattr(val, "item") and callable(val.item):
        try:
            return val.item()
        except Exception:
            pass
    if isinstance(val, float):
        return float(val)
    if isinstance(val, bool):
        return bool(val)
    if isinstance(val, int):
        return int(val)
    return val

def broadcast_live_ws_packet(pipeline_result: dict):
    """Called from MQTT collector background thread when a telemetry packet is ingested."""
    global _ACTIVE_CLIENTS, _ACTIVE_WEBSOCKETS, _MAIN_ASYNCIO_LOOP
    if not _ACTIVE_CLIENTS or _MAIN_ASYNCIO_LOOP is None:
        return

    # 1. Direct specialized messages (e.g. VFM_UPDATE, ASSET_SPEC_UPDATE, SIMULATOR_EVENT, SIMULATOR_STATUS)
    if "type" in pipeline_result and ("data" in pipeline_result or "well_id" in pipeline_result):
        encoded = json.dumps(_to_json_primitives(pipeline_result))
        for ws, q in list(_ACTIVE_CLIENTS.items()):
            try:
                _MAIN_ASYNCIO_LOOP.call_soon_threadsafe(_enqueue_ws_payload, q, encoded)
            except Exception:
                _ACTIVE_CLIENTS.pop(ws, None)
                _ACTIVE_WEBSOCKETS.discard(ws)
        return

    live_pkt = pipeline_result.get("live_packet")
    if not live_pkt:
        return
    live_msg = {
        "type": "LIVE_TELEMETRY",
        "data": _to_json_primitives(live_pkt)
    }
    try:
        encoded = json.dumps(live_msg)
    except Exception as exc:
        logger.error("[Gateway] Failed to serialize live telemetry packet: %s", exc)
        return

    # Optional VFD diagnostic message
    eval_res = pipeline_result.get("live_evaluation", {})
    pred = eval_res.get("prediction", {}) if isinstance(eval_res, dict) else {}
    vfd_msg = None
    if pred:
        try:
            vfd_msg = json.dumps(_to_json_primitives({
                "type": "VFD_DIAGNOSTIC",
                "well_id": live_pkt.get("well_id") or live_pkt.get("asset_id"),
                "family": "FS",
                "timestamp": live_pkt.get("timestamp"),
                "diagnostic": {
                    "health_score": pred.get("health_score", 92.0),
                    "primary_fault": pred.get("primary_fault", "Nominal Steady-State"),
                    "status": pred.get("status", "Healthy"),
                    "is_healthy": pred.get("is_healthy", pred.get("health_score", 92.0) >= 75.0),
                    "model_output": pred.get("model_output"),
                    "canonical_verdict": pred.get("model_output")
                },
                "dynamics": pred.get("dynamics", {}),
                "raw_measurements": live_pkt
            }))
        except Exception as exc:
            logger.error("[Gateway] Failed to serialize VFD diagnostic packet: %s", exc)

    for ws, q in list(_ACTIVE_CLIENTS.items()):
        try:
            _MAIN_ASYNCIO_LOOP.call_soon_threadsafe(_enqueue_ws_payload, q, encoded)
            if vfd_msg:
                _MAIN_ASYNCIO_LOOP.call_soon_threadsafe(_enqueue_ws_payload, q, vfd_msg)
        except Exception:
            _ACTIVE_CLIENTS.pop(ws, None)
            _ACTIVE_WEBSOCKETS.discard(ws)


@app.websocket("/ws/live")
async def websocket_live_endpoint(websocket: WebSocket):
    """Real-time live telemetry stream and collector status broadcast."""
    global _ACTIVE_CLIENTS, _ACTIVE_WEBSOCKETS, _MAIN_ASYNCIO_LOOP
    await websocket.accept()
    _MAIN_ASYNCIO_LOOP = asyncio.get_running_loop()
    client_queue: asyncio.Queue = asyncio.Queue(maxsize=100)
    _ACTIVE_CLIENTS[websocket] = client_queue
    _ACTIVE_WEBSOCKETS.add(websocket)
    sender_task = asyncio.create_task(_ws_client_sender_worker(websocket, client_queue))

    from src.pipeline.pipeline_orchestrator import get_orchestrator, LABELLED_DB_PATH, UNLABELLED_DB_PATH, MLRESULTS_DB_PATH
    from src.pipeline.mqtt_collector import get_mqtt_collector

    orch = get_orchestrator()
    collector = get_mqtt_collector()
    # Register live event-driven broadcast hook
    collector.register_broadcast_callback(broadcast_live_ws_packet)

    def _get_live_counts(need_recent: bool = True):
        global _LIVE_COUNTS_CACHE, _LIVE_COUNTS_CACHE_TIME
        now = time.time()
        # 5-second in-memory cache to eliminate repeated SQLite hits across loops and sockets
        if not need_recent and _LIVE_COUNTS_CACHE is not None and (now - _LIVE_COUNTS_CACHE_TIME < 5.0):
            return _LIVE_COUNTS_CACHE

        lab_count = 0  # labelled.db decoupled from live runtime to eliminate 20GB file I/O contention
        unlab_count = 0
        ml_count = 0
        recent = []
        try:
            if UNLABELLED_DB_PATH.exists():
                with sqlite3.connect(str(UNLABELLED_DB_PATH), timeout=2.0) as conn:
                    conn.row_factory = sqlite3.Row
                    row = conn.execute("SELECT MAX(id) FROM opg_well_telemetry").fetchone()
                    unlab_count = (row[0] or 0) if row else 0
                    if need_recent:
                        has_mlr = False
                        if MLRESULTS_DB_PATH.exists():
                            try:
                                safe_mlr = str(MLRESULTS_DB_PATH).replace('\\', '/')
                                conn.execute(f"ATTACH DATABASE '{safe_mlr}' AS mlr")
                                has_mlr = True
                            except Exception:
                                has_mlr = False

                        if has_mlr:
                            # CTE restricts rows before joining ml_results, eliminating O(N*M) table scans
                            query = """
                                WITH recent_u AS (
                                    SELECT * FROM opg_well_telemetry ORDER BY id DESC LIMIT 40
                                )
                                SELECT u.*,
                                       m.health_score AS ml_health_score,
                                       m.fault_diagnosis AS ml_fault_diagnosis,
                                       m.canonical_verdict AS ml_canonical_verdict,
                                       m.is_anomalous AS ml_is_anomalous
                                FROM recent_u u
                                LEFT JOIN mlr.ml_results m
                                    ON (u.asset_id = m.asset_id OR u.well_id = m.well_id)
                                   AND u.timestamp = m.timestamp
                                ORDER BY u.id DESC
                            """
                            rows = conn.execute(query).fetchall()
                        else:
                            rows = conn.execute("SELECT * FROM opg_well_telemetry ORDER BY id DESC LIMIT 40").fetchall()

                        for r in rows:
                            d = dict(r)
                            pip = d.get("intake_pressure_psi") if d.get("intake_pressure_psi") is not None else (d.get("Inp bar/psi") or 450.0)
                            pdp = d.get("pressure_psi") if d.get("pressure_psi") is not None else (d.get("Disch pr. Bar/psi") or 1950.0)
                            amps = d.get("motor_current_a") if d.get("motor_current_a") is not None else (d.get("VSD Amps/Load") or 85.0)
                            freq = d.get("frequency_hz") if d.get("frequency_hz") is not None else (d.get("Frequency") or 50.0)
                            temp = d.get("temperature_c") if d.get("temperature_c") is not None else (d.get("Motor temp °C") or 75.0)
                            int_temp = d.get("intake_temperature_c") if d.get("intake_temperature_c") is not None else (d.get("Int temp °C") or 55.0)
                            vib = d.get("vibration_g") if d.get("vibration_g") is not None else (d.get("Vibration G's-Vx") or 0.08)
                            flow = d.get("flow_rate_bpd") if d.get("flow_rate_bpd") is not None else (d.get("Liquid Rate (BPD)") or 800.0)

                            ml_fault = d.get("ml_fault_diagnosis") or d.get("fault_diagnosis") or "Normal Operation"
                            ml_score = float(d.get("ml_health_score") if d.get("ml_health_score") is not None else 95.0)
                            ml_verdict = d.get("ml_canonical_verdict") or d.get("canonical_verdict") or ("Healthy" if ml_score >= 75.0 else f"Anomaly is Detected: {ml_fault}")
                            is_ml_anom = bool(d.get("ml_is_anomalous")) if d.get("ml_is_anomalous") is not None else (ml_score < 75.0)
                            is_healthy = (not is_ml_anom) and (ml_score >= 75.0) and (ml_fault.lower() in ["normal", "normal operation", "healthy", "nominal steady-state"])

                            recent.append({
                                "id": d.get("id"),
                                "timestamp": d.get("timestamp"),
                                "well_id": d.get("well_id") or d.get("asset_id"),
                                "asset_id": d.get("asset_id"),
                                "pressure_psi": float(pdp),
                                "intake_pressure_psi": float(pip),
                                "motor_current_a": float(amps),
                                "frequency_hz": float(freq),
                                "temperature_c": float(temp),
                                "intake_temperature_c": float(int_temp),
                                "vibration_g": float(vib),
                                "flow_rate_bpd": float(flow),
                                "R_DISCH_PRESS": float(pdp),
                                "R_INTAKE_PRESS": float(pip),
                                "R_DRV_CURR_AVG": float(amps),
                                "R_FREQUENCY": float(freq),
                                "R_MOTOR_TEMP": float(temp),
                                "R_INTAKE_TEMP": float(int_temp),
                                "R_VIBRATION_X": float(vib),
                                "R_LIQ_RATE": float(flow),
                                "scenario": ml_fault,
                                "ml_diagnosis": ml_fault,
                                "fault_diagnosis": ml_fault,
                                "canonical_verdict": ml_verdict,
                                "model_output": ml_verdict,
                                "health_score": ml_score,
                                "is_healthy": is_healthy,
                                "status": "HEALTHY" if is_healthy else "FAULTY/ANOMALY"
                            })
        except Exception:
            pass
        try:
            if MLRESULTS_DB_PATH.exists():
                with sqlite3.connect(str(MLRESULTS_DB_PATH), timeout=2.0) as conn:
                    row = conn.execute("SELECT MAX(id) FROM ml_results").fetchone()
                    ml_count = (row[0] or 0) if row else 0
        except Exception:
            pass
        result = (lab_count, unlab_count, ml_count, recent)
        with _LIVE_COUNTS_LOCK:
            _LIVE_COUNTS_CACHE = result
            _LIVE_COUNTS_CACHE_TIME = time.time()
        return result

    try:
        # Offload blocking sqlite reads to a worker thread so they never freeze the
        # asyncio event loop (which would stall every other HTTP request server-wide).
        lab_cnt, unlab_cnt, ml_cnt, rec_list = await asyncio.to_thread(_get_live_counts, need_recent=True)
        c_status = collector.get_status()
        init_payload = {
            "type": "INITIAL_STATE",
            "status": {
                "is_running": c_status["is_running"],
                "total_received": c_status["total_received"],
                "total_saved": unlab_cnt,
                "total_filtered": 0,
                "total_buffered": len(collector.get_recent_packets(50)),
                "msg_rate_per_sec": c_status["msg_rate_per_sec"],
                "is_connected": c_status["is_connected"],
                "current_topic": c_status["current_topic"],
                "storage_category_mode": "BOTH",
                "last_packet_time": c_status["last_packet_time"]
            },
            "counts": {
                "total_records": lab_cnt + unlab_cnt,
                "labelled_records": lab_cnt,
                "unlabelled_records": unlab_cnt,
                "mlresults_records": ml_cnt,
                "wells_count": 27,
                "assets_count": 27
            },
            "recent_records": rec_list
        }
        await client_queue.put(json.dumps(init_payload))

        while True:
            await asyncio.sleep(2.0)
            lab_cnt, unlab_cnt, ml_cnt, _ = await asyncio.to_thread(_get_live_counts, need_recent=False)
            c_status = collector.get_status()
            update_payload = {
                "type": "STATUS_UPDATE",
                "data": {
                    "is_running": c_status["is_running"],
                    "msg_rate_per_sec": c_status["msg_rate_per_sec"],
                    "is_connected": c_status["is_connected"],
                    "total_saved": unlab_cnt,
                    "total_received": c_status["total_received"],
                    "mlresults_records": ml_cnt
                }
            }
            await client_queue.put(json.dumps(update_payload))
    except WebSocketDisconnect:
        pass
    except Exception:
        pass
    finally:
        _ACTIVE_CLIENTS.pop(websocket, None)
        _ACTIVE_WEBSOCKETS.discard(websocket)
        sender_task.cancel()
        try:
            await sender_task
        except asyncio.CancelledError:
            pass


@app.websocket("/ws/agent")
async def websocket_agent_gateway_endpoint(websocket: WebSocket):
    """
    Dedicated bidirectional Agent WebSocket connection.
    Decoupled from /ws/live telemetry broadcast to prevent throttling.
    """
    from src.api.rest.agent_ws_routes import websocket_agent_endpoint
    await websocket_agent_endpoint(websocket)


@app.on_event("startup")
async def startup_llm_warmup():
    """Pre-warm LLM Gateway & Supervisor graph, and auto-connect MQTT if broker is reachable."""
    import asyncio

    # Default asyncio executor caps at min(32, cpu_count+4) threads, shared by every sync `def`
    # route AND every asyncio.to_thread() call (e.g. the per-websocket /ws/live SQLite polling
    # loop, every 2s per connected client). With multiple browser tabs/reconnects each holding
    # a /ws/live socket, plus SQLite lock waits (up to 2s timeout per call) against the multi-GB
    # unlabelled.db, the pool can starve entirely -- new REST requests then queue forever with
    # zero bytes ever sent (matches the "0 KB pending" symptom across ALL endpoints at once).
    # Raise the ceiling here (inside startup, where the real running loop is bound) so DB-bound
    # background work can never fully block ordinary request handling.
    asyncio.get_running_loop().set_default_executor(ThreadPoolExecutor(max_workers=64))

    def _warmup_background():
        try:
            from src.llm.adapter import LLMAdapter
            adapter = LLMAdapter()
            adapter.generate(prompt="warmup", run_id="WARMUP-STARTUP")
        except Exception:
            pass
    
    def _mqtt_autoconnect():
        try:
            import socket
            import logging
            gw_logger = logging.getLogger("gateway")
            from src.pipeline.mqtt_collector import get_mqtt_collector
            c = get_mqtt_collector()
            with socket.create_connection((c.broker_host, c.broker_port), timeout=0.8):
                gw_logger.info(f"Detected open MQTT broker at {c.broker_host}:{c.broker_port}. Auto-connecting...")
                c.connect()
        except Exception as e:
            pass

    asyncio.create_task(asyncio.to_thread(_warmup_background))
    asyncio.create_task(asyncio.to_thread(_mqtt_autoconnect))

# Instantiate Application Services & Policy Engine
asset_service = AssetContextService()
telemetry_service = TelemetryService()
engineering_service = EngineeringService()
twin_service = DigitalTwinService()
case_service = CaseOutcomeService()
audit_service = AuditService()
policy_engine = PolicyEngine()


# Global Tracing & Envelope Middleware
@app.middleware("http")
async def add_tracing_and_envelope_headers(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", f"REQ-{uuid.uuid4().hex[:8]}")
    correlation_id = request.headers.get("X-Correlation-ID", f"CORR-{uuid.uuid4().hex[:8]}")
    tenant_id = request.headers.get("X-Tenant-ID", "CCED")

    request.state.request_id = request_id
    request.state.correlation_id = correlation_id
    request.state.tenant_id = tenant_id

    response: Response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Correlation-ID"] = correlation_id
    response.headers["X-Service-Version"] = "1.0.0"
    return response


# Health & Infrastructure Endpoints
@app.get("/health")
def health_check():
    return {"status": "ok", "service": "esp_apm_gateway", "version": "1.0.0"}


@app.get("/readiness")
def readiness_check():
    return {"status": "ready", "services": {"asset": "ready", "telemetry": "ready", "engineering": "ready"}}


@app.get("/version")
def version_info():
    return {"platform": "ESP APM Service Platform", "api_version": "v1", "schema_version": "v2.1"}


# 12.1 Asset Context Service Endpoints
@app.get("/api/v1/assets", response_model=RESTEnvelope[List[str]])
def list_assets(request: Request):
    assets = asset_service.list_assets()
    return RESTEnvelope.success(
        data=assets,
        service="asset_context_service",
        request_id=request.state.request_id,
        correlation_id=request.state.correlation_id
    )


@app.get("/api/v1/assets/{asset_id}/context")
def get_asset_context(asset_id: str, request: Request):
    policy_engine.enforce_tenant_isolation(request.state.tenant_id, asset_id)
    try:
        ctx = asset_service.get_context(asset_id)
        return RESTEnvelope.success(
            data=ctx.model_dump(),
            service="asset_context_service",
            request_id=request.state.request_id,
            correlation_id=request.state.correlation_id
        )
    except ValueError as ex:
        err = ServiceErrorPayload.create("ASSET_NOT_FOUND", str(ex), target=asset_id)
        return JSONResponse(
            status_code=404,
            content=RESTEnvelope.error(err, service="asset_context_service", request_id=request.state.request_id).model_dump()
        )


@app.get("/api/v1/assets/{asset_id}/tags")
def get_asset_tags(asset_id: str, request: Request):
    try:
        mapping = asset_service.get_tag_mapping(asset_id)
        return RESTEnvelope.success(data=mapping, service="asset_context_service", request_id=request.state.request_id)
    except ValueError as ex:
        err = ServiceErrorPayload.create("ASSET_NOT_FOUND", str(ex), target=asset_id)
        return JSONResponse(status_code=404, content=RESTEnvelope.error(err, service="asset_context_service").model_dump())


# 12.2 Telemetry Endpoints
@app.get("/api/v1/telemetry/{asset_id}/latest")
def get_latest_telemetry(asset_id: str, request: Request):
    snap = telemetry_service.get_latest(asset_id)
    return RESTEnvelope.success(data=snap.model_dump(), service="telemetry_service", request_id=request.state.request_id)


@app.post("/api/v1/telemetry")
def ingest_telemetry(req: IngestTelemetryRequest, request: Request):
    res = telemetry_service.ingest_telemetry(req)
    return RESTEnvelope.success(data=res, service="telemetry_service", request_id=request.state.request_id)


# 12.3 Engineering Endpoints
@app.post("/api/v1/engineering/tdh")
def calculate_tdh(req: TDHRequest, request: Request):
    res = engineering_service.calculate_tdh(req)
    return RESTEnvelope.success(data=res.model_dump(), service="engineering_service", request_id=request.state.request_id)


@app.post("/api/v1/engineering/bep")
def calculate_bep(req: BEPRequest, request: Request):
    res = engineering_service.calculate_bep(req)
    return RESTEnvelope.success(data=res.model_dump(), service="engineering_service", request_id=request.state.request_id)


# 12.7 Digital Twin Endpoints
@app.post("/api/v1/twin/what-if/frequency")
def simulate_frequency_change(req: FrequencyWhatIfRequest, request: Request):
    res = twin_service.simulate_frequency_change(req)
    return RESTEnvelope.success(data=res.model_dump(), service="digital_twin_service", request_id=request.state.request_id)


@app.post("/api/v1/twin/optimize")
def optimize_speed(req: OptimizationRequest, request: Request):
    res = twin_service.optimize_vsd_speed(req)
    return RESTEnvelope.success(data=res.model_dump(), service="digital_twin_service", request_id=request.state.request_id)


# 12.6 Case & Outcome Endpoints
@app.post("/api/v1/cases/search")
def search_cases(req: CaseSearchRequest, request: Request):
    res = case_service.search_cases(req)
    return RESTEnvelope.success(data=res.model_dump(), service="case_outcome_service", request_id=request.state.request_id)


@app.get("/api/v1/cases/verification-checks")
def get_verification_checks(asset_id: str, request: Request):
    checks = case_service.get_verification_checks(asset_id)
    return RESTEnvelope.success(data=[c.model_dump() for c in checks], service="case_outcome_service", request_id=request.state.request_id)


@app.post("/api/v1/audit/outcome")
def capture_outcome(payload: OutcomeCapturePayload, request: Request):
    res = case_service.capture_outcome(payload)
    return RESTEnvelope.success(data=res, service="case_outcome_service", request_id=request.state.request_id)


# 12.8 Audit Endpoints
@app.post("/api/v1/audit/advisory")
def log_advisory(payload: AdvisoryAuditPayload, request: Request):
    res = audit_service.log_advisory(payload)
    return RESTEnvelope.success(data=res, service="audit_service", request_id=request.state.request_id)


@app.get("/api/v1/audit/{trace_id}")
def get_trace(trace_id: str, request: Request):
    trace = audit_service.get_execution_trace(trace_id)
    return RESTEnvelope.success(data=trace.model_dump(), service="audit_service", request_id=request.state.request_id)


# Phase 7 Supervisor Agent Endpoint
from pydantic import BaseModel, Field

class AgentRunRequest(BaseModel):
    user_query: str = Field(description="Natural language user query")
    asset_id: str = Field(description="Target ESP asset ID")

@app.post("/v1/agent/run")
def run_supervisor_agent(req: AgentRunRequest, request: Request):
    from src.agent.supervisor.user_entry import UserEntryAdapter
    adapter = UserEntryAdapter()
    advisory = adapter.run(
        user_query=req.user_query,
        asset_id=req.asset_id,
        request_id=request.state.request_id,
        tenant_id=request.state.tenant_id
    )
    return RESTEnvelope.success(
        data=advisory.model_dump(),
        service="supervisor_agent",
        request_id=request.state.request_id,
        correlation_id=request.state.correlation_id
    )
