import pytest
from httpx import AsyncClient, ASGITransport

from app.contracts.api import UIContext, QueryRequest
from app.contracts.context import ContextFrame
from app.context.resolver import resolve_context
from app.main import app

def test_uicontext_model_accepts_selected_route():
    ctx = UIContext(selected_route="/working-status")
    assert ctx.selected_route == "/working-status"
    dump = ctx.model_dump(exclude_none=True)
    assert dump.get("selected_route") == "/working-status"

def test_queryrequest_model_accepts_ui_context_selected_route():
    req = QueryRequest(
        session_id="test-s1",
        message="check status",
        ui_context={"selected_route": "/wells/FS-17"},
    )
    assert req.ui_context.selected_route == "/wells/FS-17"

    # Typed UIContext
    req2 = QueryRequest(
        session_id="test-s2",
        message="check status",
        ui_context=UIContext(selected_route="/fleet"),
    )
    assert isinstance(req2.ui_context, UIContext)
    assert req2.ui_context.selected_route == "/fleet"

def test_resolve_context_carries_selected_route_from_dict():
    frame: ContextFrame = resolve_context(
        session_id="sess-route-1",
        message="test message",
        ui_context={"selected_route": "/working-status", "active_tab": "trends"},
    )
    assert frame.selected_route == "/working-status"
    assert frame.ui_context.get("selected_route") == "/working-status"
    assert frame.ui_context.get("active_tab") == "trends"

def test_resolve_context_carries_selected_route_from_uicontext_obj():
    ctx_obj = UIContext(selected_route="/events", active_tab="alarms")
    frame: ContextFrame = resolve_context(
        session_id="sess-route-2",
        message="test message",
        ui_context=ctx_obj,
    )
    assert frame.selected_route == "/events"
    assert frame.ui_context.get("selected_route") == "/events"
    assert frame.ui_context.get("active_tab") == "alarms"

def test_resolve_context_absent_ui_context():
    frame: ContextFrame = resolve_context(
        session_id="sess-route-3",
        message="test message",
        ui_context=None,
    )
    assert frame.selected_route is None

def test_resolve_context_fallback_branch_carries_selected_route(monkeypatch):
    # Force UIContext.model_validate to fail to test fallback branch
    def mock_validate(val):
        raise ValueError("Simulated validation failure")
    monkeypatch.setattr(UIContext, "model_validate", mock_validate)

    frame: ContextFrame = resolve_context(
        session_id="sess-route-4",
        message="test message",
        ui_context={"selected_route": "/fallback-route", "well_id": "FS-17"},
    )
    assert frame.selected_route == "/fallback-route"
    assert frame.asset.id == "FS-17"

@pytest.mark.anyio
async def test_api_endpoint_accepts_selected_route_200():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/query",
            json={
                "session_id": "test-endpoint-route",
                "message": "What are you?",
                "ui_context": {"selected_route": "/working-status"},
            },
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        assert resp.headers["content-type"].startswith("application/x-ndjson")
