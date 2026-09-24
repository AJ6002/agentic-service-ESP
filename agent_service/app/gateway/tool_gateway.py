

"""
Tool Gateway.
Dispatches plan calls to domain adapters against Server 184 (:8090).
Zero hardcoded measurement fallback data. Partial failures tolerated.
Reference: ESP_APM_AGENT_APIS_COMPLETE_SPECIFICATION.md v2.0.0 & SLICE_2_PLAN.md §0.5.
"""

import asyncio
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Optional
import httpx

from app.contracts.enums import AdapterStatus
from app.contracts.evidence import CallResult
from app.contracts.plan import PlanArtifact, PlanCall
from app.context.well_ids import normalize_well_id
from .adapters import cards, events, historian, kb, kpi, live, ml
from .adapters.common import AdapterError, DEFAULT_TIMEOUT_SEC, get_gateway_base_url, handle_adapter_response

_FAULT_MAPPING_CACHE: Optional[dict[str, Any]] = None

def _get_fault_mapping(fault_class: str) -> Optional[dict[str, Any]]:
    global _FAULT_MAPPING_CACHE
    if _FAULT_MAPPING_CACHE is None:
        from pathlib import Path as _Path
        import yaml as _yaml
        cfg_path = _Path(__file__).resolve().parent.parent.parent / "config" / "fault_taxonomy_mapping.yaml"
        if cfg_path.exists():
            try:
                with open(cfg_path, "r", encoding="utf-8") as f:
                    data = _yaml.safe_load(f) or {}
                    _FAULT_MAPPING_CACHE = data.get("mappings", {})
            except Exception:
                _FAULT_MAPPING_CACHE = {}
        else:
            _FAULT_MAPPING_CACHE = {}
    clean_cls = str(fault_class).strip().upper().replace(" ", "_")
    return _FAULT_MAPPING_CACHE.get(clean_cls)


# Fallback window span (seconds) used only when a call needs a start/end
# and the caller supplied neither — i.e. the user asked no explicit time
# phrase and there was no UI selection. Anchored at "now" so the window
# always tracks the present, never a stale hardcoded calendar date.
_DEFAULT_WINDOW_SEC = int(2 * 3600)  # 2 hours (anchored to rolling 1-Hz retention window)


def _default_window() -> tuple[str, str]:
    """Returns (start_iso, end_iso) for a now-relative default window."""
    now = datetime.now(timezone.utc)
    start = now - timedelta(seconds=_DEFAULT_WINDOW_SEC)
    return (
        start.isoformat().replace("+00:00", "Z"),
        now.isoformat().replace("+00:00", "Z"),
    )


def _build_kb_query(well_id: Optional[str], args: dict[str, Any]) -> str:
    """
    Builds a natural-language KB search query from the plan's bound args
    when no explicit query was supplied. Deterministic string composition,
    no LLM — the KB service itself does the semantic matching.
    """
    parts = ["troubleshooting"]
    if well_id:
        parts.append(f"well {well_id}")
    trip_ts = args.get("trip_ts")
    if trip_ts:
        parts.append(f"trip at {trip_ts}")
    return " ".join(parts) if len(parts) > 1 else "ESP fault diagnosis general troubleshooting"


async def execute_tool_call(call: PlanCall, client: Optional[httpx.AsyncClient] = None) -> CallResult:
    """
    Executes a single PlanCall against Server 184 domain adapters.
    Returns CallResult with status OK, FAILED, or TIMEOUT.
    Zero fabricated numbers.
    """
    start_time = time.time()
    tool = call.tool
    args = call.args or {}

    raw_asset = args.get("asset_id")
    well_id = normalize_well_id(raw_asset) if raw_asset else None
    if not well_id and raw_asset:
        well_id = raw_asset.strip().upper()

    try:
        # 1. Knowledge Base — esp_kb_service (:8085), real endpoint now.
        if tool == "search_knowledge":
            query = args.get("query") or _build_kb_query(well_id, args)
            data = await kb.search_kb(query, top_k=5, client=client)
            latency = round((time.time() - start_time) * 1000, 2)
            return CallResult(seq=call.seq, status="OK", raw_response=data, latency_ms=latency)

        if not well_id and tool not in ("get_cards_catalog", "get_fleet_kpi", "get_live_wells", "get_fault_taxonomy", "trace_causal_graph", "search_knowledge"):
            latency = round((time.time() - start_time) * 1000, 2)
            return CallResult(
                seq=call.seq,
                status="FAILED",
                error=f"Tool {tool} requires asset_id, but none provided",
                error_code="MISSING_ASSET_ID",
                latency_ms=latency,
            )

        # 2. Domain Dispatch Map
        data: dict[str, Any] = {}
        if tool == "get_live_telemetry":
            data = await live.fetch_live_telemetry(well_id, client=client)

        elif tool == "get_asset_context":
            data = await live.fetch_live_asset(well_id, client=client)

        elif tool == "get_vfm":
            data = await live.fetch_live_vfm(well_id, client=client)

        elif tool == "get_live_wells":
            data = await live.fetch_live_wells(client=client)

        elif tool == "get_historian_window":
            _def_start, _def_end = _default_window()
            start = args.get("start") or _def_start
            end = args.get("end") or _def_end
            signals = args.get("signals")
            limit = int(args.get("limit", 10000))

            # Coverage verification for OP14 / explicit window queries:
            if args.get("start") or args.get("end"):
                try:
                    cov = await historian.fetch_historian_coverage(well_id, client=client)
                    if cov and isinstance(cov, dict):
                        first_ts = cov.get("first_ts")
                        last_ts = cov.get("last_ts")
                        row_count = cov.get("row_count", 0)
                        if row_count == 0 or (first_ts and start < first_ts) or (last_ts and end > last_ts):
                            raise AdapterError(
                                code="COVERAGE_EXCEEDED",
                                status_code=400,
                                message=f"Requested window ({start} to {end}) exceeds Historian coverage ({first_ts} to {last_ts}) for well {well_id}",
                            )
                except AdapterError as ex:
                    if ex.code == "COVERAGE_EXCEEDED":
                        raise
                except Exception:
                    pass

            data = await historian.fetch_historian_window(well_id, start, end, signals, limit, client=client)

        elif tool == "get_historian_aggregates":
            _def_start, _def_end = _default_window()
            start = args.get("start") or _def_start
            end = args.get("end") or _def_end
            signals = args.get("signals") or "amp_a,motor_temp_c,int_prs_psi,disch_prs_psi,freq_hz,liquid_rate_bpd,oil_rate_bopd,water_cut_pct"
            bucket = args.get("bucket", "1h")
            agg = args.get("agg", "avg")

            if args.get("start") or args.get("end"):
                try:
                    cov = await historian.fetch_historian_coverage(well_id, client=client)
                    if cov and isinstance(cov, dict):
                        first_ts = cov.get("first_ts")
                        last_ts = cov.get("last_ts")
                        row_count = cov.get("row_count", 0)
                        if row_count == 0 or (first_ts and start < first_ts) or (last_ts and end > last_ts):
                            raise AdapterError(
                                code="COVERAGE_EXCEEDED",
                                status_code=400,
                                message=f"Requested window ({start} to {end}) exceeds Historian coverage ({first_ts} to {last_ts}) for well {well_id}",
                            )
                except AdapterError as ex:
                    if ex.code == "COVERAGE_EXCEEDED":
                        raise
                except Exception:
                    pass

            data = await historian.fetch_historian_aggregates(
                well_id, start, end, signals=signals, bucket=bucket, agg=agg, client=client
            )

        elif tool == "get_historian_latest":
            signals = args.get("signals")
            data = await historian.fetch_historian_latest(well_id, signals, client=client)

        elif tool == "get_historian_coverage":
            data = await historian.fetch_historian_coverage(well_id, client=client)

        elif tool in ("get_events", "get_events_timeline"):
            _def_start, _def_end = _default_window()
            start = args.get("start") or _def_start
            end = args.get("end") or _def_end
            data = await events.fetch_events_timeline(well_id, start, end, client=client)

        elif tool == "get_trips":
            data = await events.fetch_events_trips(well_id, client=client)

        elif tool == "diagnose_fault":
            data = await ml.fetch_ml_fault(well_id, client=client)

        elif tool == "get_ml_results":
            limit = args.get("limit")
            anomalous_only = args.get("anomalous_only")
            data = await ml.query_mlresults(well_id, limit=limit, anomalous_only=anomalous_only, client=client)

        elif tool == "get_anomaly":
            data = await ml.fetch_ml_anomaly(well_id, client=client)

        elif tool == "get_health_index":
            data = await ml.fetch_ml_health(well_id, client=client)

        elif tool == "get_degradation":
            try:
                base = get_gateway_base_url()
                url = f"{base}/ml/degradation/{well_id}"
                if client:
                    resp = await client.get(url, timeout=DEFAULT_TIMEOUT_SEC)
                    data = handle_adapter_response(resp, "ml", f"/ml/degradation/{well_id}")
                else:
                    async with httpx.AsyncClient() as c:
                        resp = await c.get(url, timeout=DEFAULT_TIMEOUT_SEC)
                        data = handle_adapter_response(resp, "ml", f"/ml/degradation/{well_id}")
            except Exception:
                data = await ml.fetch_ml_health(well_id, client=client)

        elif tool == "get_explanation":
            output = args.get("output", "fault")
            data = await ml.fetch_ml_explain(well_id, output, client=client)

        elif tool == "get_current_status":
            data = await kpi.fetch_kpi(well_id, client=client)

        elif tool == "get_card":
            card_id = args.get("card_id", "health-score")
            data = await cards.fetch_card(well_id, card_id, client=client)

        elif tool == "get_cards_catalog":
            data = await cards.fetch_cards_catalog(client=client)

        elif tool == "get_fault_taxonomy":
            fault_id = args.get("fault_id")
            if not fault_id:
                fault_class = args.get("fault_class")
                if not fault_class and well_id:
                    try:
                        ml_fault = await ml.fetch_ml_fault(well_id, client=client)
                        fault_class = ml_fault.get("fault_class")
                    except Exception:
                        pass
                if fault_class:
                    mapping = _get_fault_mapping(fault_class)
                    if mapping:
                        fault_id = mapping.get("primary_fault_id")
            if not fault_id:
                latency = round((time.time() - start_time) * 1000, 2)
                return CallResult(
                    seq=call.seq,
                    status="OK",
                    raw_response={"unmapped": True, "note": "No fault taxonomy mapping found for fault class"},
                    latency_ms=latency,
                )
            data = await kb.get_kb_fault(fault_id, client=client)

        elif tool == "trace_causal_graph":
            symptom_ids = args.get("symptom_ids") or args.get("symptoms")
            if not symptom_ids:
                fault_class = args.get("fault_class")
                if not fault_class and well_id:
                    try:
                        ml_fault = await ml.fetch_ml_fault(well_id, client=client)
                        fault_class = ml_fault.get("fault_class")
                    except Exception:
                        pass
                if fault_class:
                    mapping = _get_fault_mapping(fault_class)
                    if mapping:
                        symptom_ids = mapping.get("symptoms", [])
            if not symptom_ids:
                latency = round((time.time() - start_time) * 1000, 2)
                return CallResult(
                    seq=call.seq,
                    status="OK",
                    raw_response={"unmapped": True, "note": "No symptom mapping found for fault class"},
                    latency_ms=latency,
                )
            observed_params = args.get("observed_parameters")
            data = await kb.trace_kb_graph(symptom_ids, observed_parameters=observed_params, client=client)

        else:
            latency = round((time.time() - start_time) * 1000, 2)
            return CallResult(
                seq=call.seq,
                status="FAILED",
                error=f"Unknown tool: {tool}",
                error_code="UNKNOWN_TOOL",
                latency_ms=latency,
            )

        latency = round((time.time() - start_time) * 1000, 2)
        return CallResult(
            seq=call.seq,
            status="OK",
            raw_response=data,
            latency_ms=latency,
        )

    except httpx.TimeoutException:
        latency = round((time.time() - start_time) * 1000, 2)
        return CallResult(
            seq=call.seq,
            status="TIMEOUT",
            error=f"Timeout contacting Server 184 for tool {tool}",
            error_code="TIMEOUT",
            latency_ms=latency,
        )
    except AdapterError as ex:
        latency = round((time.time() - start_time) * 1000, 2)
        return CallResult(
            seq=call.seq,
            status="FAILED",
            error=str(ex),
            error_code=ex.code,
            status_code=ex.status_code,
            latency_ms=latency,
        )
    except httpx.ConnectError as ex:
        latency = round((time.time() - start_time) * 1000, 2)
        return CallResult(
            seq=call.seq,
            status="FAILED",
            error=f"Cannot reach Server 184 for tool {tool}: {ex}",
            error_code="UNREACHABLE",
            latency_ms=latency,
        )
    except Exception as ex:
        latency = round((time.time() - start_time) * 1000, 2)
        return CallResult(
            seq=call.seq,
            status="FAILED",
            error=f"Unexpected error executing {tool}: {type(ex).__name__}: {str(ex)}",
            error_code="UNEXPECTED",
            latency_ms=latency,
        )


async def dispatch_plan_calls(plan: PlanArtifact) -> list[CallResult]:
    """
    Executes all READ calls in parallel via asyncio.gather.
    Tolerates partial failures.
    """
    read_calls = [c for c in plan.calls if c.kind == "READ"]
    if not read_calls:
        return []

    async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT_SEC) as client:
        tasks = [execute_tool_call(call, client=client) for call in read_calls]
        results = await asyncio.gather(*tasks, return_exceptions=True)

    formatted_results: list[CallResult] = []
    for call, res in zip(read_calls, results):
        if isinstance(res, Exception):
            formatted_results.append(
                CallResult(
                    seq=call.seq,
                    status="FAILED",
                    error=f"Exception during dispatch: {type(res).__name__}: {str(res)}",
                    latency_ms=0.0,
                )
            )
        else:
            formatted_results.append(res)

    return formatted_results
