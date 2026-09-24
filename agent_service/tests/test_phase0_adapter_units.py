"""
Phase 0 — per-adapter unit tests (GAP-P0-02).

Every adapter in app/gateway/adapters/ is exercised against the fixture
files in tests/fixtures/server184/ via httpx.MockTransport. No live server,
no Redis, no LLM — these run entirely offline.

What these lock down that nothing did before:
  - exact URL formation per adapter (a typo'd path can no longer pass silently)
  - query-parameter serialization (well_id / start / end / signals / limit / output)
  - spec §6 error-envelope parsing, including the structured error CODE
  - 200-but-empty is treated as valid data, not an error
  - the anti-fabrication rule: every number an adapter returns is traceable
    to a fixture file
"""

import json
from pathlib import Path

import httpx
import pytest

from app.gateway.adapters import cards, events, historian, kb, kpi, live, ml
from app.gateway.adapters.common import AdapterError

FIXTURES = Path(__file__).parent / "fixtures" / "server184"


def load_fixture(name: str) -> dict:
    with open(FIXTURES / name, encoding="utf-8") as f:
        return json.load(f)


def mock_client(
    expect_path: str,
    fixture: str | None = None,
    status_code: int = 200,
    body: dict | None = None,
    capture: dict | None = None,
) -> httpx.AsyncClient:
    """
    Builds an AsyncClient whose transport asserts the requested path and
    returns the given fixture/body. `capture` (if provided) receives the
    actual URL and params so a test can assert on them.
    """
    payload = body if body is not None else load_fixture(fixture)  # type: ignore[arg-type]

    def handler(request: httpx.Request) -> httpx.Response:
        if capture is not None:
            capture["url"] = str(request.url)
            capture["path"] = request.url.path
            capture["params"] = dict(request.url.params)
        assert request.url.path == expect_path, (
            f"Adapter called wrong path: expected {expect_path}, got {request.url.path}"
        )
        return httpx.Response(status_code, json=payload)

    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


# ---------------------------------------------------------------------------
# Live adapter
# ---------------------------------------------------------------------------

class TestLiveAdapter:
    @pytest.mark.anyio
    async def test_telemetry_url_and_payload(self):
        cap: dict = {}
        async with mock_client(
            "/live/telemetry/FS-17", fixture="live_telemetry_nominal.json", capture=cap
        ) as c:
            data = await live.fetch_live_telemetry("FS-17", client=c)

        assert cap["path"] == "/live/telemetry/FS-17"
        # Values must come from the fixture — never invented.
        fixture = load_fixture("live_telemetry_nominal.json")
        assert data["measurements"]["STD_MOTOR_TEMP_C"] == fixture["measurements"]["STD_MOTOR_TEMP_C"]
        assert data["age_sec"] == fixture["age_sec"]

    @pytest.mark.anyio
    async def test_telemetry_503_mqtt_down_raises_with_code(self):
        """503 MQTT_DISCONNECTED must surface the structured code, not just a string."""
        async with mock_client(
            "/live/telemetry/FS-17",
            fixture="live_telemetry_503_mqtt_down.json",
            status_code=503,
        ) as c:
            with pytest.raises(AdapterError) as ei:
                await live.fetch_live_telemetry("FS-17", client=c)

        assert ei.value.status_code == 503
        assert ei.value.code == "MQTT_DISCONNECTED"

    @pytest.mark.anyio
    async def test_asset_url_and_payload(self):
        async with mock_client("/live/asset/FS-17", fixture="live_asset_nominal.json") as c:
            data = await live.fetch_live_asset("FS-17", client=c)
        assert data["asset"]["pump_type"] == "B400-400"
        assert data["asset"]["stages"] == 342

    @pytest.mark.anyio
    async def test_vfm_path(self):
        cap: dict = {}
        async with mock_client(
            "/live/vfm/FS-17", body={"well_id": "FS-17", "age_sec": 0.8}, capture=cap
        ) as c:
            await live.fetch_live_vfm("FS-17", client=c)
        assert cap["path"] == "/live/vfm/FS-17"

    @pytest.mark.anyio
    async def test_wells_path(self):
        cap: dict = {}
        async with mock_client("/live/wells", body={"wells": []}, capture=cap) as c:
            await live.fetch_live_wells(client=c)
        assert cap["path"] == "/live/wells"


# ---------------------------------------------------------------------------
# Historian adapter
# ---------------------------------------------------------------------------

class TestHistorianAdapter:
    @pytest.mark.anyio
    async def test_window_serializes_all_query_params(self):
        cap: dict = {}
        async with mock_client(
            "/historian/window", fixture="historian_window_nominal.json", capture=cap
        ) as c:
            data = await historian.fetch_historian_window(
                "FS-17",
                start="2026-08-01T00:00:00Z",
                end="2026-08-30T00:00:00Z",
                signals="amp_a,motor_temp_c",
                limit=10,
                client=c,
            )

        p = cap["params"]
        assert p["well_id"] == "FS-17"
        assert p["start"] == "2026-08-01T00:00:00Z"
        assert p["end"] == "2026-08-30T00:00:00Z"
        assert p["signals"] == "amp_a,motor_temp_c"
        assert p["limit"] == "10"
        assert data["row_count"] == 2

    @pytest.mark.anyio
    async def test_window_omits_signals_when_not_given(self):
        cap: dict = {}
        async with mock_client(
            "/historian/window", fixture="historian_window_nominal.json", capture=cap
        ) as c:
            await historian.fetch_historian_window(
                "FS-17", start="2026-08-01T00:00:00Z", end="2026-08-30T00:00:00Z", client=c
            )
        assert "signals" not in cap["params"]

    @pytest.mark.anyio
    async def test_window_200_empty_is_valid_not_an_error(self):
        """
        row_count=0 / rows=[] is a legitimate empty window per spec §6 —
        it must return data, NOT raise.
        """
        async with mock_client(
            "/historian/window", fixture="historian_window_200_empty.json"
        ) as c:
            data = await historian.fetch_historian_window(
                "FS-17", start="2026-08-01T00:00:00Z", end="2026-08-30T00:00:00Z", client=c
            )
        assert data["row_count"] == 0
        assert data["rows"] == []

    @pytest.mark.anyio
    async def test_window_404_well_not_found_raises_with_code(self):
        async with mock_client(
            "/historian/window",
            fixture="historian_window_404_well_not_found.json",
            status_code=404,
        ) as c:
            with pytest.raises(AdapterError) as ei:
                await historian.fetch_historian_window(
                    "FWS-04", start="2026-08-01T00:00:00Z", end="2026-08-30T00:00:00Z", client=c
                )
        assert ei.value.status_code == 404
        assert ei.value.code == "WELL_NOT_FOUND"

    @pytest.mark.anyio
    async def test_latest_path_and_params(self):
        cap: dict = {}
        async with mock_client(
            "/historian/latest", body={"well_id": "FS-17", "values": {}}, capture=cap
        ) as c:
            await historian.fetch_historian_latest("FS-17", client=c)
        assert cap["path"] == "/historian/latest"
        assert cap["params"]["well_id"] == "FS-17"


# ---------------------------------------------------------------------------
# Events adapter
# ---------------------------------------------------------------------------

class TestEventsAdapter:
    @pytest.mark.anyio
    async def test_timeline_with_window_params(self):
        cap: dict = {}
        async with mock_client(
            "/events/timeline", fixture="events_timeline_nominal.json", capture=cap
        ) as c:
            data = await events.fetch_events_timeline(
                "FNW-01", start="2026-09-01T00:00:00Z", end="2026-09-30T00:00:00Z", client=c
            )
        assert cap["params"]["well_id"] == "FNW-01"
        assert cap["params"]["start"] == "2026-09-01T00:00:00Z"
        assert data["events"][0]["trip_cause"] == "UNDERLOAD_PUMP_OFF"

    @pytest.mark.anyio
    async def test_timeline_empty_is_valid(self):
        """A healthy well with zero events returns 200 + events: [] — not an error."""
        async with mock_client(
            "/events/timeline", fixture="events_timeline_200_empty.json"
        ) as c:
            data = await events.fetch_events_timeline("FS-17", client=c)
        assert data["event_count"] == 0
        assert data["events"] == []

    @pytest.mark.anyio
    async def test_trips_path(self):
        cap: dict = {}
        async with mock_client(
            "/events/trips", body={"event_count": 0, "events": []}, capture=cap
        ) as c:
            await events.fetch_events_trips("FS-17", client=c)
        assert cap["path"] == "/events/trips"
        assert cap["params"]["well_id"] == "FS-17"


# ---------------------------------------------------------------------------
# ML adapter
# ---------------------------------------------------------------------------

class TestMLAdapter:
    @pytest.mark.anyio
    async def test_fault_url_and_payload(self):
        async with mock_client("/ml/fault/FS-17", fixture="ml_fault_nominal.json") as c:
            data = await ml.fetch_ml_fault("FS-17", client=c)
        assert data["fault_class"] == "MOTOR_OVERLOAD"
        assert data["probability"] == 0.78

    @pytest.mark.anyio
    async def test_per_well_health_url(self):
        """
        /ml/health/{well} (per-well composite) is a DIFFERENT endpoint from
        /ml/health (domain liveness). This asserts the adapter hits the
        per-well one — the gap DISC-P0-01 flagged in the probe script.
        """
        async with mock_client("/ml/health/FS-17", fixture="ml_health_nominal.json") as c:
            data = await ml.fetch_ml_health("FS-17", client=c)
        assert data["health_score"] == 71.4
        assert data["band"] == "DEGRADED"

    @pytest.mark.anyio
    async def test_anomaly_url(self):
        cap: dict = {}
        async with mock_client(
            "/ml/anomaly/FS-17", body={"well_id": "FS-17", "score": 0.72}, capture=cap
        ) as c:
            await ml.fetch_ml_anomaly("FS-17", client=c)
        assert cap["path"] == "/ml/anomaly/FS-17"

    @pytest.mark.anyio
    async def test_explain_passes_output_param(self):
        cap: dict = {}
        async with mock_client(
            "/ml/explain/FS-17", fixture="ml_explain_nominal.json", capture=cap
        ) as c:
            data = await ml.fetch_ml_explain("FS-17", output="fault", client=c)
        assert cap["params"]["output"] == "fault"
        assert data["contributions"][0]["feature"] == "amp_a"


# ---------------------------------------------------------------------------
# KPI + Cards adapters
# ---------------------------------------------------------------------------

class TestKpiAndCardsAdapters:
    @pytest.mark.anyio
    async def test_kpi_well_url_and_payload(self):
        async with mock_client("/kpi/FS-17", fixture="kpi_well_nominal.json") as c:
            data = await kpi.fetch_kpi("FS-17", client=c)
        assert data["kpis"]["health_score"] == 71.4
        assert data["status"] == "running"

    @pytest.mark.anyio
    async def test_fleet_kpi_url(self):
        cap: dict = {}
        async with mock_client(
            "/kpi/fleet", body={"well_count": 14, "wells": []}, capture=cap
        ) as c:
            await kpi.fetch_fleet_kpi(client=c)
        assert cap["path"] == "/kpi/fleet"

    @pytest.mark.anyio
    async def test_card_url_and_payload(self):
        async with mock_client(
            "/cards/FS-17/health-score", fixture="card_health_score_nominal.json"
        ) as c:
            data = await cards.fetch_card("FS-17", "health-score", client=c)
        assert data["card_id"] == "health-score"
        assert data["value"] == 71.4

    @pytest.mark.anyio
    async def test_card_404_raises_with_code(self):
        async with mock_client(
            "/cards/FS-17/nope",
            body={"error": {"code": "CARD_NOT_FOUND", "message": "Unknown card_id"}},
            status_code=404,
        ) as c:
            with pytest.raises(AdapterError) as ei:
                await cards.fetch_card("FS-17", "nope", client=c)
        assert ei.value.code == "CARD_NOT_FOUND"

    @pytest.mark.anyio
    async def test_catalog_url(self):
        cap: dict = {}
        async with mock_client(
            "/cards/catalog", fixture="cards_catalog_nominal.json", capture=cap
        ) as c:
            data = await cards.fetch_cards_catalog(client=c)
        assert cap["path"] == "/cards/catalog"
        assert data["card_count"] == 17


# ---------------------------------------------------------------------------
# Anti-fabrication guard across all fixtures
# ---------------------------------------------------------------------------

def test_all_fixtures_are_valid_json_and_present():
    """
    Every fixture the adapter tests rely on must exist and parse. This stops
    a test silently passing because a fixture was renamed or deleted.
    """
    required = [
        "live_telemetry_nominal.json",
        "live_telemetry_503_mqtt_down.json",
        "live_asset_nominal.json",
        "historian_window_nominal.json",
        "historian_window_200_empty.json",
        "historian_window_404_well_not_found.json",
        "events_timeline_nominal.json",
        "events_timeline_200_empty.json",
        "ml_fault_nominal.json",
        "ml_health_nominal.json",
        "ml_explain_nominal.json",
        "kpi_well_nominal.json",
        "card_health_score_nominal.json",
        "cards_catalog_nominal.json",
        "kb_search_nominal.json",
        "kb_search_empty.json",
        "kb_health_nominal.json",
    ]
    for name in required:
        path = FIXTURES / name
        assert path.exists(), f"Missing required fixture: {name}"
        with open(path, encoding="utf-8") as f:
            json.load(f)  # raises if malformed


# ---------------------------------------------------------------------------
# GAP-P0-03 — structured error codes must survive into Gap.reason
# ---------------------------------------------------------------------------

class TestGapReasonClassification:
    """
    Before CallResult carried error_code, every non-timeout failure collapsed
    to Gap(reason="DEGRADED") and ABSENT was unreachable — a genuinely missing
    source (Knowledge Base) looked identical to a temporarily impaired one
    (MQTT down). These tests lock in the distinction.
    """

    def test_absent_code_maps_to_absent_gap(self):
        from app.contracts.evidence import CallResult
        from app.evidence.pack import classify_gap_reason

        call = CallResult(
            seq=1, status="FAILED",
            error="Knowledge Base is ABSENT (no backend endpoint)",
            error_code="ABSENT",
        )
        assert classify_gap_reason(call) == "ABSENT"

    def test_well_not_found_maps_to_absent_gap(self):
        from app.contracts.evidence import CallResult
        from app.evidence.pack import classify_gap_reason

        call = CallResult(
            seq=1, status="FAILED", error="unknown well",
            error_code="WELL_NOT_FOUND", status_code=404,
        )
        assert classify_gap_reason(call) == "ABSENT"

    def test_mqtt_disconnected_maps_to_degraded_gap(self):
        """MQTT down = source exists but impaired → DEGRADED, not ABSENT."""
        from app.contracts.evidence import CallResult
        from app.evidence.pack import classify_gap_reason

        call = CallResult(
            seq=1, status="FAILED", error="broker unreachable",
            error_code="MQTT_DISCONNECTED", status_code=503,
        )
        assert classify_gap_reason(call) == "DEGRADED"

    def test_no_data_maps_to_degraded_gap(self):
        from app.contracts.evidence import CallResult
        from app.evidence.pack import classify_gap_reason

        call = CallResult(
            seq=1, status="FAILED", error="no rows",
            error_code="NO_DATA", status_code=404,
        )
        assert classify_gap_reason(call) == "DEGRADED"

    def test_timeout_maps_to_timeout_gap(self):
        from app.contracts.evidence import CallResult
        from app.evidence.pack import classify_gap_reason

        call = CallResult(seq=1, status="TIMEOUT", error="timed out", error_code="TIMEOUT")
        assert classify_gap_reason(call) == "TIMEOUT"

    def test_unknown_code_defaults_to_degraded(self):
        """An unrecognized failure must degrade safely, not be called ABSENT."""
        from app.contracts.evidence import CallResult
        from app.evidence.pack import classify_gap_reason

        call = CallResult(seq=1, status="FAILED", error="???", error_code=None)
        assert classify_gap_reason(call) == "DEGRADED"

    @pytest.mark.anyio
    async def test_search_knowledge_dispatches_when_kb_unreachable_yields_degraded(self):
        """
        esp_kb_service (:8085) now exists — search_knowledge is no longer
        hardcoded to ABSENT. If the KB host is unreachable right now, that
        is DEGRADED (the source exists, we just can't reach it), the same
        as any other Server 184 domain being temporarily down. ABSENT is
        reserved for sources with genuinely no backing service at all.
        """
        import os
        from app.contracts.plan import PlanCall
        from app.evidence.pack import classify_gap_reason
        from app.gateway.tool_gateway import execute_tool_call

        prev_kb = os.environ.get("KB_SERVICE_BASE_URL")
        try:
            os.environ["KB_SERVICE_BASE_URL"] = "http://127.0.0.1:59998"

            call = PlanCall(seq=1, kind="READ", tool="search_knowledge", args={"asset_id": "FS-17"})
            res = await execute_tool_call(call)

            assert res.status in ("FAILED", "TIMEOUT")
            assert res.error_code != "ABSENT"
            assert classify_gap_reason(res) in ("DEGRADED", "TIMEOUT")
        finally:
            if prev_kb is not None:
                os.environ["KB_SERVICE_BASE_URL"] = prev_kb
            else:
                os.environ.pop("KB_SERVICE_BASE_URL", None)

    @pytest.mark.anyio
    async def test_unreachable_server_yields_degraded_not_absent(self):
        """
        An unreachable Server 184 is DEGRADED (it exists, we just can't
        reach it right now) — it must not be misreported as ABSENT.
        Also re-asserts the anti-fabrication rule: no invented measurements.
        """
        import os
        from app.contracts.plan import PlanCall
        from app.evidence.pack import classify_gap_reason
        from app.gateway.tool_gateway import execute_tool_call

        prev_184 = os.environ.get("SERVER184_BASE_URL")
        prev_3 = os.environ.get("SERVER3_BASE_URL")
        try:
            os.environ["SERVER184_BASE_URL"] = "http://127.0.0.1:59999"
            os.environ["SERVER3_BASE_URL"] = "http://127.0.0.1:59999"

            call = PlanCall(seq=1, kind="READ", tool="get_live_telemetry", args={"asset_id": "FS-17"})
            res = await execute_tool_call(call)

            assert res.status in ("FAILED", "TIMEOUT")
            assert classify_gap_reason(res) in ("DEGRADED", "TIMEOUT")
            assert classify_gap_reason(res) != "ABSENT"
            # Anti-fabrication: nothing invented on the failure path.
            assert res.raw_response is None or "measurements" not in res.raw_response
        finally:
            for key, prev in (("SERVER184_BASE_URL", prev_184), ("SERVER3_BASE_URL", prev_3)):
                if prev is not None:
                    os.environ[key] = prev
                else:
                    os.environ.pop(key, None)


# ---------------------------------------------------------------------------
# Knowledge Base adapter (esp_kb_service, :8085 — separate service from
# Server 184's :8090 domains). POST-based, not GET; own base URL.
# Reference: ESP_KB_SERVICE_COMPLETE_API_SPECIFICATION.md v2.1.0.
# ---------------------------------------------------------------------------

class TestKbAdapter:
    @pytest.mark.anyio
    async def test_search_posts_query_body(self):
        cap: dict = {}

        def handler(request: httpx.Request) -> httpx.Response:
            cap["path"] = request.url.path
            cap["method"] = request.method
            cap["json"] = json.loads(request.content)
            return httpx.Response(200, json=load_fixture("kb_search_nominal.json"))

        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as c:
            data = await kb.search_kb("underload trip fluid starvation current drop", top_k=3, client=c)

        assert cap["method"] == "POST"
        assert cap["path"] == "/api/kb/search"
        assert cap["json"]["query"] == "underload trip fluid starvation current drop"
        assert cap["json"]["top_k"] == 3
        assert data["hits"][0]["authority"] == "LEVEL_A_STANDARD"

    @pytest.mark.anyio
    async def test_search_empty_hits_is_valid_not_an_error(self):
        """Zero corpus matches is a legitimate result, not a failure."""

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json=load_fixture("kb_search_empty.json"))

        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as c:
            data = await kb.search_kb("nonsense query", client=c)

        assert data["hits"] == []
        assert data["total_found"] == 0

    @pytest.mark.anyio
    async def test_search_optional_filters_included_when_given(self):
        cap: dict = {}

        def handler(request: httpx.Request) -> httpx.Response:
            cap["json"] = json.loads(request.content)
            return httpx.Response(200, json=load_fixture("kb_search_nominal.json"))

        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as c:
            await kb.search_kb("x", min_authority="LEVEL_A_STANDARD", category="troubleshooting", client=c)

        assert cap["json"]["min_authority"] == "LEVEL_A_STANDARD"
        assert cap["json"]["category"] == "troubleshooting"

    @pytest.mark.anyio
    async def test_fault_by_id_url(self):
        cap: dict = {}

        def handler(request: httpx.Request) -> httpx.Response:
            cap["path"] = request.url.path
            return httpx.Response(200, json={"fault_id": "MOTOR_OVERHEATING"})

        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as c:
            data = await kb.get_kb_fault("MOTOR_OVERHEATING", client=c)

        assert cap["path"] == "/api/kb/faults/MOTOR_OVERHEATING"
        assert data["fault_id"] == "MOTOR_OVERHEATING"

    @pytest.mark.anyio
    async def test_fault_by_id_404_raises_with_code(self):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                404, json={"detail": "Fault taxonomy ID 'UNKNOWN_FAULT_XYZ' not found"}
            )

        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as c:
            with pytest.raises(AdapterError) as ei:
                await kb.get_kb_fault("UNKNOWN_FAULT_XYZ", client=c)
        assert ei.value.status_code == 404

    @pytest.mark.anyio
    async def test_standard_by_id_url(self):
        cap: dict = {}

        def handler(request: httpx.Request) -> httpx.Response:
            cap["path"] = request.url.path
            return httpx.Response(200, json={"standard_id": "API_RP_11S"})

        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as c:
            await kb.get_kb_standard("API_RP_11S", client=c)
        assert cap["path"] == "/api/kb/standards/API_RP_11S"

    @pytest.mark.anyio
    async def test_health_url(self):
        cap: dict = {}

        def handler(request: httpx.Request) -> httpx.Response:
            cap["path"] = request.url.path
            return httpx.Response(200, json=load_fixture("kb_health_nominal.json"))

        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as c:
            data = await kb.check_kb_health(client=c)
        assert cap["path"] == "/health"
        assert data["indexed_documents"] == 3657

    def test_kb_base_url_is_separate_from_server184(self):
        """
        KB is a different service on a different port. If someone
        accidentally routes it through get_gateway_base_url() (:8090),
        every KB call would silently hit the wrong server.
        """
        from app.gateway.adapters.common import get_gateway_base_url
        assert kb.get_kb_base_url() != get_gateway_base_url()
        assert ":8085" in kb.get_kb_base_url()


# ---------------------------------------------------------------------------
# search_knowledge end-to-end through the real tool_gateway dispatch
# ---------------------------------------------------------------------------

class TestSearchKnowledgeToolDispatch:
    @pytest.mark.anyio
    async def test_search_knowledge_dispatches_to_kb_not_absent(self, monkeypatch):
        """
        Before this task, tool_gateway intercepted search_knowledge and
        always returned error_code="ABSENT" without attempting a call.
        Now that esp_kb_service exists, it must actually dispatch.
        """
        from app.contracts.plan import PlanCall
        from app.gateway import tool_gateway as tg_mod

        async def fake_search_kb(query, top_k=5, min_authority=None, category=None, client=None):
            assert "FS-17" in query or query  # deterministic query built from args
            return load_fixture("kb_search_nominal.json")

        monkeypatch.setattr(tg_mod.kb, "search_kb", fake_search_kb)

        call = PlanCall(seq=1, kind="READ", tool="search_knowledge", args={"asset_id": "FS-17"})
        res = await tg_mod.execute_tool_call(call)

        assert res.status == "OK"
        assert res.error_code is None
        assert res.raw_response["hits"][0]["doc_id"] == "API_RP_11S1_Dismantle_Failure_Analysis_2022"


class TestPhase45KbToolDispatch:
    @pytest.mark.anyio
    async def test_trace_kb_graph_url_and_payload(self):
        cap: dict = {}

        def handler(request: httpx.Request) -> httpx.Response:
            cap["path"] = request.url.path
            cap["method"] = request.method
            cap["json"] = json.loads(request.content)
            return httpx.Response(200, json={
                "symptom_ids": ["high_motor_temperature"],
                "paths": [
                    {
                        "fault_id": "MOTOR_OVERHEATING",
                        "fault_name": "Motor Overheating",
                        "confidence": 0.9,
                        "chain": ["symptom -> fault"],
                        "recommended_sop": {"sop_id": "SOP_1", "action": "Inspect cooling"}
                    }
                ],
                "total_paths": 1
            })

        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as c:
            data = await kb.trace_kb_graph(["high_motor_temperature"], client=c)

        assert cap["method"] == "POST"
        assert cap["path"] == "/api/kb/graph/trace"
        assert cap["json"]["symptom_ids"] == ["high_motor_temperature"]
        assert data["total_paths"] == 1
        assert data["paths"][0]["fault_id"] == "MOTOR_OVERHEATING"

    @pytest.mark.anyio
    async def test_get_fault_taxonomy_tool_dispatch(self, monkeypatch):
        from app.contracts.plan import PlanCall
        from app.gateway import tool_gateway as tg_mod

        async def fake_get_kb_fault(fault_id, client=None):
            assert fault_id == "MOTOR_OVERHEATING"
            return {
                "fault_id": "MOTOR_OVERHEATING",
                "name": "Motor Overheating",
                "applicable_manual": "API_RP_11S",
                "recommended_actions": ["Verify thermal baseline"]
            }

        monkeypatch.setattr(tg_mod.kb, "get_kb_fault", fake_get_kb_fault)

        call = PlanCall(seq=1, kind="READ", tool="get_fault_taxonomy", args={"fault_id": "MOTOR_OVERHEATING"})
        res = await tg_mod.execute_tool_call(call)

        assert res.status == "OK"
        assert res.raw_response["fault_id"] == "MOTOR_OVERHEATING"
        assert res.raw_response["name"] == "Motor Overheating"

    @pytest.mark.anyio
    async def test_trace_causal_graph_tool_dispatch(self, monkeypatch):
        from app.contracts.plan import PlanCall
        from app.gateway import tool_gateway as tg_mod

        async def fake_trace_kb_graph(symptom_ids, observed_parameters=None, client=None):
            return {
                "symptom_ids": symptom_ids,
                "paths": [{"fault_id": "GAS_LOCK", "confidence": 0.85}],
                "total_paths": 1
            }

        monkeypatch.setattr(tg_mod.kb, "trace_kb_graph", fake_trace_kb_graph)

        call = PlanCall(seq=1, kind="READ", tool="trace_causal_graph", args={"symptoms": ["low_intake_pressure"]})
        res = await tg_mod.execute_tool_call(call)

        assert res.status == "OK"
        assert res.raw_response["total_paths"] == 1

    @pytest.mark.anyio
    async def test_unmapped_fault_class_graceful_skip(self):
        from app.contracts.plan import PlanCall
        from app.gateway import tool_gateway as tg_mod

        call = PlanCall(seq=1, kind="READ", tool="get_fault_taxonomy", args={"fault_class": "COMPLETELY_FICTIONAL_FAULT_CLASS_999"})
        res = await tg_mod.execute_tool_call(call)

        assert res.status == "OK"
        assert res.raw_response.get("unmapped") is True
