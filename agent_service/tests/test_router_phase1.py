import pytest
from app.contracts.routing import RouterInput
from app.routing.router import route_query
from app.audit.audit_sink import get_audit_records, clear_audit_records

@pytest.mark.anyio
async def test_router_simple_inquiry():
    r_in = RouterInput(
        raw_message="What is Best Efficiency Point (BEP)?",
        asset_id=None,
        asset_source="UNRESOLVED",
        turn_count=1,
    )
    decision = await route_query(r_in)
    assert decision.route == "SIMPLE"
    assert decision.clarification_needed is False

@pytest.mark.anyio
async def test_router_workflow_with_explicit_asset():
    r_in = RouterInput(
        raw_message="Why did FS-017 trip?",
        asset_id="FS-017",
        asset_source="EXPLICIT",
        turn_count=1,
    )
    decision = await route_query(r_in)
    assert decision.route == "WORKFLOW"
    assert decision.objective_id == "OP03_FAULT_DIAGNOSIS"
    assert decision.args.get("asset_id") == "FS-017"
    assert decision.clarification_needed is False

@pytest.mark.anyio
async def test_router_workflow_missing_asset_triggers_clarify():
    r_in = RouterInput(
        raw_message="Why did it trip?",
        asset_id=None,
        asset_source="UNRESOLVED",
        turn_count=1,
    )
    decision = await route_query(r_in)
    assert decision.route == "WORKFLOW"
    assert decision.clarification_needed is True
    assert decision.clarify_slot == "asset_id"
    assert "FS-17" in decision.clarify_options

@pytest.mark.anyio
async def test_router_multi_intent_defers_actuation():
    r_in = RouterInput(
        raw_message="Why did FS-017 trip and please bump speed to 58 Hz",
        asset_id="FS-017",
        asset_source="EXPLICIT",
        turn_count=1,
    )
    decision = await route_query(r_in)
    assert decision.route == "WORKFLOW"
    assert len(decision.deferred_intents) > 0
    assert any("actuation" in d or "58" in d or "frequency" in d for d in decision.deferred_intents)

def test_audit_sink_integration():
    clear_audit_records()
    from app.audit.audit_sink import record_audit
    record_audit("test_event", run_id="R-audit-1", payload={"foo": "bar"})
    records = get_audit_records(count=10)
    assert len(records) >= 1
    assert records[-1]["event_type"] == "test_event"
    assert records[-1]["run_id"] == "R-audit-1"


# ---------------------------------------------------------------------------
# LLM-down flagging — previously swallowed silently (`except Exception:
# pass`). Now routed through app.llm.client, which raises
# LLMUnavailableError distinctly, and route_query_full() reports it via
# RouteResult.llm_available / fallback_used instead of hiding it.
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_router_flags_llm_unavailable(monkeypatch):
    from app.routing import router as router_mod
    import app.llm.calls as llm_calls_mod
    from app.llm.client import LLMUnavailableError

    async def fake_call_llm_chat(*args, **kwargs):
        raise LLMUnavailableError("simulated gateway down")

    # Patch at the true source (app.llm.calls holds the actual HTTP call
    # now, inside llm_route()) — router.py itself no longer imports
    # call_llm_chat directly since the LLM-gateway refactor.
    monkeypatch.setattr(llm_calls_mod, "call_llm_chat", fake_call_llm_chat)

    r_in = RouterInput(
        raw_message="Why did FS-017 trip?",
        asset_id="FS-017",
        asset_source="EXPLICIT",
        turn_count=1,
    )
    result = await router_mod.route_query_full(r_in)
    assert result.llm_available is False
    assert result.fallback_used is True
    # Fallback still produces a usable decision, just a degraded one.
    assert result.decision.route == "WORKFLOW"
    assert result.decision.objective_id == "OP03_FAULT_DIAGNOSIS"

@pytest.mark.anyio
async def test_router_available_when_llm_responds(monkeypatch):
    from app.routing import router as router_mod
    import app.llm.calls as llm_calls_mod

    async def fake_call_llm_chat(*args, **kwargs):
        return (
            '{"route": "SIMPLE", "intent": "general_inquiry", "objective_id": "OP07_GENERAL_INQUIRY", '
            '"args": {}, "confidence": 0.95, "deferred_intents": [], "clarification_needed": false, '
            '"clarify_reason": null, "clarify_slot": null, "clarify_options": []}'
        )

    monkeypatch.setattr(llm_calls_mod, "call_llm_chat", fake_call_llm_chat)

    r_in = RouterInput(raw_message="What is TDH?", asset_id=None, asset_source="UNRESOLVED", turn_count=1)
    result = await router_mod.route_query_full(r_in)
    assert result.llm_available is True
    assert result.fallback_used is False
    assert result.decision.route == "SIMPLE"


# ---------------------------------------------------------------------------
# SLICE_1_PLAN §5.2 — RouterInput must never carry internal pipeline state.
# Regression guard: if anyone adds flags/pending/resolution/needs_clarify to
# RouterInput in the future, this test fails immediately, making the violation
# visible rather than silently changing LLM routing behaviour.
# ---------------------------------------------------------------------------

def test_router_input_excludes_internal_flags():
    forbidden = {"flags", "pending", "pending_ref", "resolution", "needs_clarify", "clarify_reason"}
    current_fields = set(RouterInput.model_fields.keys())
    leaked = current_fields & forbidden
    assert not leaked, (
        f"RouterInput has leaked internal state fields: {leaked}. "
        "Per SLICE_1_PLAN §5.2, these must never be in RouterInput — "
        "the LLM must not be able to short-circuit itself on pipeline flags."
    )


# ---------------------------------------------------------------------------
# Regression: LLM emitting explicit JSON `null` for empty list/dict fields
# (a reasonable model choice, not malformed output) was being rejected by
# strict Pydantic validation, silently demoting a correct, live LLM
# decision to the degraded keyword fallback — misreported as
# "llm_available=True, fallback_used=True", masking a real live-LLM
# response as if the router's own logic had failed. This drives the exact
# payload shape seen in production audit logs through the real validator.
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_router_accepts_null_lists_from_llm_without_falling_back(monkeypatch):
    from app.routing import router as router_mod
    import app.llm.calls as llm_calls_mod

    async def fake_call_llm_chat(*args, **kwargs):
        return (
            '{"route": "WORKFLOW", "intent": "status", "objective_id": "OP01_CURRENT_STATUS", '
            '"args": {"asset_id": "FS-091"}, "confidence": 0.9, "deferred_intents": null, '
            '"clarification_needed": false, "clarify_reason": null, "clarify_slot": null, '
            '"clarify_options": null}'
        )

    monkeypatch.setattr(llm_calls_mod, "call_llm_chat", fake_call_llm_chat)

    r_in = RouterInput(
        raw_message="what's the pressure at FS-091 right now?",
        asset_id="FS-091",
        asset_source="EXPLICIT",
        turn_count=1,
    )
    result = await router_mod.route_query_full(r_in)

    assert result.llm_available is True
    assert result.fallback_used is False  # must NOT be silently demoted
    assert result.decision.route == "WORKFLOW"
    assert result.decision.objective_id == "OP01_CURRENT_STATUS"
    assert result.decision.clarify_options == []
    assert result.decision.deferred_intents == []
