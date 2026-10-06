import json
import pytest

from app.contracts.routing import RouterInput
from app.routing.router import route_query, route_query_full
from app.synthesis import identity_handler as id_mod
from app.llm.client import LLMUnavailableError


# ---------------------------------------------------------------------------
# 1. Deterministic Router Matching Tests
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "query",
    [
        "what are you",
        "what are you?",
        "what are u ?",
        "who are you",
        "who are you?",
        "what can you do",
        "what can you do?",
        "what do you do",
        "what can't you do",
        "what are your limits",
        "what are your capabilities",
        "what are your all capabilties ?",
        "what are all your capabilities ?",
        "what is your all capabilities",
        "what are your capablities",
        "what all can you do",
        "what all do you do",
        "what all capabilities do you have",
        "tell me all your capabilities",
        "list your all capabilities",
        "tell me about yourself",
        "explain your role",
        "explain your architecture",
    ],
)
@pytest.mark.anyio
async def test_router_identifies_self_knowledge_queries(query: str):
    r_in = RouterInput(raw_message=query)
    result = await route_query_full(r_in)
    assert result.decision.route == "IDENTITY"
    assert result.decision.confidence == 1.0
    assert result.decision.clarification_needed is False
    assert result.fallback_used is False


# ---------------------------------------------------------------------------
# 2. Boundary & Negative Routing Tests (Preserve existing routes)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "query,expected_route,expected_obj",
    [
        ("What is gas lock?", "SIMPLE", "OP06_KNOWLEDGE_LOOKUP"),
        ("What is PIP?", "SIMPLE", "OP06_KNOWLEDGE_LOOKUP"),
        ("Explain water cut.", "SIMPLE", "OP06_KNOWLEDGE_LOOKUP"),
        ("Why did FS-17 trip?", "WORKFLOW", "OP03_FAULT_DIAGNOSIS"),
        ("What is the current status of FS-91?", "WORKFLOW", "OP01_CURRENT_STATUS"),
        ("How do I restart an ESP?", "SIMPLE", "OP06_KNOWLEDGE_LOOKUP"),
    ],
)
@pytest.mark.anyio
async def test_router_negative_preserves_other_routes(query: str, expected_route: str, expected_obj: str):
    r_in = RouterInput(raw_message=query)
    decision = await route_query(r_in)
    assert decision.route == expected_route
    assert decision.objective_id == expected_obj


# ---------------------------------------------------------------------------
# 3. Identity Synthesis Handler Tests
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_identity_handler_returns_model_answer_when_live(monkeypatch):
    async def fake_identity_answer(query, static_self_model, live_capabilities):
        assert "ESP APM Operations Copilot" in static_self_model
        assert "Active Objectives:" in live_capabilities
        return "I am the ESP APM Operations Copilot, an advisory-only assistant for Farha South."

    monkeypatch.setattr(id_mod, "identity_answer", fake_identity_answer)

    res = await id_mod.handle_identity_query("what are you?")
    assert res.llm_available is True
    assert "ESP APM Operations Copilot" in res.text
    assert "advisory-only" in res.text



@pytest.mark.anyio
async def test_identity_handler_offline_fallback(monkeypatch):
    async def fake_identity_answer(*args, **kwargs):
        raise LLMUnavailableError("simulated LLM outage")

    monkeypatch.setattr(id_mod, "identity_answer", fake_identity_answer)

    res = await id_mod.handle_identity_query("what can you do?")
    assert res.llm_available is False
    # Derived deterministically from agent_identity.yaml
    assert "ESP APM Operations Copilot" in res.text
    assert "Farha South" in res.text
    assert "advisory" in res.text.lower()


# ---------------------------------------------------------------------------
# 4. Pipeline Isolation Guarantee
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_identity_route_never_touches_workflow_pipeline(monkeypatch):
    """
    Guarantees that IDENTITY never invokes PlanBuilder, PolicyGate, ToolGateway,
    or EvidencePack sealing.
    """
    import app.planning.plan_builder as pb
    import app.policy.policy_gate as pg
    import app.gateway.tool_gateway as tg
    import app.workflow.runner as wr

    intercepted: list[str] = []

    def trap_pb(*a, **kw):
        intercepted.append("plan_builder")

    def trap_pg(*a, **kw):
        intercepted.append("policy_gate")

    async def trap_tg(*a, **kw):
        intercepted.append("tool_gateway")

    async def trap_wr(*a, **kw):
        intercepted.append("workflow_runner")

    monkeypatch.setattr(pb, "build_plan", trap_pb)
    monkeypatch.setattr(pg, "validate_plan", trap_pg)
    monkeypatch.setattr(tg, "execute_tool_call", trap_tg)
    monkeypatch.setattr(wr, "run_workflow", trap_wr)

    async def fake_identity_answer(*args, **kwargs):
        return "I am an advisory assistant."

    monkeypatch.setattr(id_mod, "identity_answer", fake_identity_answer)

    from httpx import AsyncClient, ASGITransport
    from app.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/query", json={"session_id": "S-test-ident", "message": "What are you?"})
        assert resp.status_code == 200

        lines = [json.loads(line) for line in resp.text.strip().split("\n") if line.strip()]
        # Verify text_delta and done
        assert any(l.get("type") == "text_delta" for l in lines)
        assert any(l.get("type") == "done" and l.get("status") == "OK" for l in lines)
        # Verify zero visual / advisory / evidence frames
        assert not any(l.get("type") in ("advisory", "visual", "evidence") for l in lines)

    # Workflow pipeline must not have been entered
    assert intercepted == []


@pytest.mark.anyio
async def test_router_decision_logging(monkeypatch):
    import app.routing.router as router_mod
    recorded = []

    def mock_record_audit(event_type, payload=None, run_id=None):
        if event_type == "router_decided":
            recorded.append(payload)

    monkeypatch.setattr(router_mod, "record_audit", mock_record_audit)

    # Test deterministic identity
    res1 = await route_query_full(RouterInput(raw_message="what are your all capabilties ?"))
    assert res1.decision.route == "IDENTITY"
    assert len(recorded) >= 1
    latest1 = recorded[-1]
    assert latest1["path_fired"] == "deterministic_identity"
    assert latest1["llm_said"] is None
    assert latest1["final_route"]["route"] == "IDENTITY"
    assert latest1["final_route"]["intent"] == "self_knowledge"

    # Test deterministic greeting
    res2 = await route_query_full(RouterInput(raw_message="hello there"))
    assert res2.decision.route == "SIMPLE"
    latest2 = recorded[-1]
    assert latest2["path_fired"] == "deterministic_greeting"
    assert latest2["llm_said"] is None
    assert latest2["final_route"]["route"] == "SIMPLE"
    assert latest2["final_route"]["intent"] == "greeting"

