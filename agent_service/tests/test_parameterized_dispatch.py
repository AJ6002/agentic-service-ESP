import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.context.resolver import parse_query_limit, parse_anomaly_filter, resolve_context
from app.gateway.adapters.ml import query_mlresults
from app.gateway.tool_gateway import execute_tool_call
from app.contracts.plan import PlanCall

def test_parse_query_limit_and_filter():
    # 1. Parameterized query
    text = "show top 50 anomalies for FS-17"
    assert parse_query_limit(text) == 50
    assert parse_anomaly_filter(text) is True

    # 2. Time query: should NOT mistake 30 mins for row limit
    time_text = "status of FS-17 in the last 30 mins"
    assert parse_query_limit(time_text) is None
    assert parse_anomaly_filter(time_text) is None

    # 3. Simple query with no params
    simple_text = "why did FNW-01 trip?"
    assert parse_query_limit(simple_text) is None
    assert parse_anomaly_filter(simple_text) is None

def test_resolve_context_query_params():
    frame = resolve_context("test_session", "show 25 anomalous records for FS-17")
    assert frame.query_params.get("limit") == 25
    assert frame.query_params.get("anomalous_only") is True

    # Empty/normal query has empty query_params
    frame_normal = resolve_context("test_session", "check status of FS-17")
    assert frame_normal.query_params == {}

@pytest.mark.anyio
async def test_query_mlresults_param_omission():
    mock_client = MagicMock()
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"status": "success", "count": 0, "results": []}
    mock_client.get = AsyncMock(return_value=mock_resp)

    # With params
    res = await query_mlresults("FS-17", limit=50, anomalous_only=True, client=mock_client)
    mock_client.get.assert_called_once()
    called_url, called_kwargs = mock_client.get.call_args
    assert called_kwargs["params"] == {"asset_id": "FS-17", "limit": 50, "anomalous_only": "true"}

    # Without params (None values omitted)
    mock_client.get.reset_mock()
    res2 = await query_mlresults("FS-17", limit=None, anomalous_only=None, client=mock_client)
    mock_client.get.assert_called_once()
    called_url2, called_kwargs2 = mock_client.get.call_args
    assert called_kwargs2["params"] == {"asset_id": "FS-17"}

@pytest.mark.anyio
async def test_tool_gateway_dispatch_get_ml_results():
    with patch("app.gateway.adapters.ml.query_mlresults", new_callable=AsyncMock) as mock_ml:
        mock_ml.return_value = {"status": "success", "results": []}

        # Case 1: Parameterized call
        call = PlanCall(seq=1, kind="READ", tool="get_ml_results", args={"asset_id": "FS-17", "limit": 50, "anomalous_only": True})
        res = await execute_tool_call(call)
        assert res.status == "OK"
        mock_ml.assert_called_with("FS-17", limit=50, anomalous_only=True, client=None)

        # Case 2: Unparameterized call (fallback/defaults preserved)
        call_clean = PlanCall(seq=2, kind="READ", tool="get_ml_results", args={"asset_id": "FS-17"})
        res_clean = await execute_tool_call(call_clean)
        assert res_clean.status == "OK"
        mock_ml.assert_called_with("FS-17", limit=None, anomalous_only=None, client=None)
