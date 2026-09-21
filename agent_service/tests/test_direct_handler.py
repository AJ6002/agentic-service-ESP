import pytest

from app.synthesis import direct_handler as dh_mod
from app.llm.client import LLMUnavailableError


@pytest.mark.anyio
async def test_direct_handler_flags_llm_unavailable(monkeypatch):
    async def fake_direct_answer(*args, **kwargs):
        raise LLMUnavailableError("simulated gateway down")

    monkeypatch.setattr(dh_mod, "direct_answer", fake_direct_answer)

    answer = await dh_mod.handle_direct_query("what does underload mean?")
    assert answer.llm_available is False
    # Falls back to the deterministic glossary, not a crash / blank answer.
    assert "current" in answer.text.lower() or "underload" in answer.text.lower()


@pytest.mark.anyio
async def test_direct_handler_available_when_llm_responds(monkeypatch):
    async def fake_direct_answer(*args, **kwargs):
        return "Total Dynamic Head is the equivalent height a fluid is pumped against."

    monkeypatch.setattr(dh_mod, "direct_answer", fake_direct_answer)

    answer = await dh_mod.handle_direct_query("what is TDH?")
    assert answer.llm_available is True
    assert "Total Dynamic Head" in answer.text


@pytest.mark.anyio
async def test_direct_handler_unavailable_with_no_glossary_match(monkeypatch):
    async def fake_direct_answer(*args, **kwargs):
        raise LLMUnavailableError("simulated gateway down")

    monkeypatch.setattr(dh_mod, "direct_answer", fake_direct_answer)

    answer = await dh_mod.handle_direct_query("what is the capital of France?")
    assert answer.llm_available is False
    assert "temporarily unavailable" in answer.text.lower()


# ---------------------------------------------------------------------------
# Bypass guarantee (SLICE_1_PLAN Step 2.2 / IMPLEMENTATION_SEQUENCE Stage 15):
# Direct Handler must NEVER touch Plan Builder, Policy Gate, Tool Gateway,
# or the workflow runner. This was documented as a requirement twice but
# never actually enforced by a test — a future edit could silently wire
# one of these in and nothing would catch it. This test makes that
# regression impossible to introduce quietly.
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_direct_handler_never_calls_workflow_pipeline(monkeypatch):
    import app.planning.plan_builder as plan_builder_mod
    import app.policy.policy_gate as policy_gate_mod
    import app.gateway.tool_gateway as tool_gateway_mod
    import app.workflow.runner as workflow_runner_mod

    calls: list[str] = []

    def make_sync_spy(name):
        def _inner(*args, **kwargs):
            calls.append(name)
            raise AssertionError(f"Direct Handler must never call {name}")
        return _inner

    def make_async_spy(name):
        async def _inner(*args, **kwargs):
            calls.append(name)
            raise AssertionError(f"Direct Handler must never call {name}")
        return _inner

    monkeypatch.setattr(plan_builder_mod, "build_plan", make_sync_spy("build_plan"))
    monkeypatch.setattr(policy_gate_mod, "validate_plan", make_sync_spy("validate_plan"))
    monkeypatch.setattr(tool_gateway_mod, "dispatch_plan_calls", make_async_spy("dispatch_plan_calls"))
    monkeypatch.setattr(workflow_runner_mod, "run_workflow", make_async_spy("run_workflow"))

    async def fake_direct_answer(*args, **kwargs):
        return "Total Dynamic Head is the equivalent height a fluid is pumped against."

    monkeypatch.setattr(dh_mod, "direct_answer", fake_direct_answer)

    answer = await dh_mod.handle_direct_query("what is TDH?")

    assert answer.llm_available is True
    assert calls == []  # none of the workflow-pipeline functions were ever invoked
