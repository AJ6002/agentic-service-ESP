import pytest
from unittest.mock import AsyncMock, patch
import httpx

from app.gateway.adapters import historian
from app.gateway.tool_gateway import execute_tool_call
from app.contracts.plan import PlanCall
from app.evidence.qod import validate
from app.contracts.evidence import CallResult


@pytest.mark.anyio
async def test_fetch_historian_aggregates_adapter():
    sample_payload = {
        "well_id": "FS-17",
        "bucket": "1h",
        "agg": "avg",
        "start": "2026-09-18T00:00:00Z",
        "end": "2026-09-19T00:00:00Z",
        "columns": ["bucket", "amp_a", "motor_temp_c"],
        "units": {"amp_a": "A", "motor_temp_c": "°C"},
        "rows": [
            ["2026-09-18 00:00:00Z", 35.7, 87.6],
            ["2026-09-18 01:00:00Z", 35.8, 87.7],
        ],
    }

    mock_resp = httpx.Response(
        status_code=200,
        json=sample_payload,
        request=httpx.Request("GET", "http://test/historian/aggregates"),
    )

    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.get.return_value = mock_resp

    res = await historian.fetch_historian_aggregates(
        well_id="FS-17",
        start="2026-09-18T00:00:00Z",
        end="2026-09-19T00:00:00Z",
        signals="amp_a,motor_temp_c",
        bucket="1h",
        agg="avg",
        client=mock_client,
    )

    assert res["well_id"] == "FS-17"
    assert res["bucket"] == "1h"
    assert len(res["rows"]) == 2
    assert "temporal_meta" in res
    assert res["temporal_meta"]["data_bounds"]["point_count"] == 2


@pytest.mark.anyio
async def test_tool_gateway_dispatches_aggregates():
    sample_payload = {
        "well_id": "FS-17",
        "bucket": "1h",
        "agg": "avg",
        "start": "2026-09-18T00:00:00Z",
        "end": "2026-09-19T00:00:00Z",
        "columns": ["bucket", "amp_a"],
        "units": {"amp_a": "A"},
        "rows": [["2026-09-18 00:00:00Z", 35.5]],
    }
    sample_cov = {
        "well_id": "FS-17",
        "first_ts": "2026-09-17T00:00:00Z",
        "last_ts": "2026-09-20T00:00:00Z",
        "row_count": 5000,
    }

    with patch.object(historian, "fetch_historian_aggregates", new_callable=AsyncMock) as mock_fetch, \
         patch.object(historian, "fetch_historian_coverage", new_callable=AsyncMock) as mock_cov:
        mock_fetch.return_value = sample_payload
        mock_cov.return_value = sample_cov

        call = PlanCall(
            seq=1,
            kind="READ",
            tool="get_historian_aggregates",
            args={"asset_id": "FS-17", "start": "2026-09-18T00:00:00Z", "end": "2026-09-19T00:00:00Z"},
        )
        result = await execute_tool_call(call)
        assert result.status == "OK"
        assert result.raw_response["well_id"] == "FS-17"


@pytest.mark.anyio
async def test_tool_gateway_refuses_when_window_exceeds_coverage():
    sample_cov = {
        "well_id": "FS-17",
        "first_ts": "2026-09-17T00:00:00Z",
        "last_ts": "2026-09-20T00:00:00Z",
        "row_count": 5000,
    }

    with patch.object(historian, "fetch_historian_coverage", new_callable=AsyncMock) as mock_cov:
        mock_cov.return_value = sample_cov

        # Query asking for 2025 (clearly before first_ts)
        call = PlanCall(
            seq=1,
            kind="READ",
            tool="get_historian_window",
            args={"asset_id": "FS-17", "start": "2025-01-01T00:00:00Z", "end": "2025-01-02T00:00:00Z"},
        )
        result = await execute_tool_call(call)
        assert result.status == "FAILED"
        assert result.error_code == "COVERAGE_EXCEEDED"


def test_qod_validates_aggregates():
    sample_payload = {
        "well_id": "FS-17",
        "bucket": "1h",
        "agg": "avg",
        "start": "2026-08-01T00:00:00Z",
        "end": "2026-08-02T00:00:00Z",
        "columns": ["bucket", "amp_a", "motor_temp_c"],
        "units": {"amp_a": "A", "motor_temp_c": "°C"},
        "rows": [["2026-08-01 00:00:00Z", 35.5, 87.0]],
    }
    call_res = CallResult(seq=1, status="OK", raw_response=sample_payload, latency_ms=10.0)
    qod = validate(call_res, run_id="run-agg-1", tool="get_historian_aggregates")
    assert qod.accepted is True
    assert qod.evidence_item is not None
    assert qod.evidence_item.source_domain == "historian"
