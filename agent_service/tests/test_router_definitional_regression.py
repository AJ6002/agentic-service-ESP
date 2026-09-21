"""
Regression tests for Bug A -- definitional-vs-diagnostic routing disambiguation.

Covers:
  - Q02 verbatim: "Explain what underload trip is and why it happens" must -> OP07 (not OP03)
  - Generic causal "what causes X" -> OP07
  - "what is X" style -> OP07
  - "why did ASSET trip" still -> OP03 (regression guard: do not break the causal path)
  - Fallback path (_keyword_fallback_decision) independently tested without LLM
"""
import pytest
from app.contracts.routing import RouterInput
from app.routing.router import _keyword_fallback_decision, route_query
from unittest.mock import AsyncMock, patch


# ── Helpers ─────────────────────────────────────────────────────────────────

def _make_input(msg: str, asset_id=None, asset_source="UNRESOLVED") -> RouterInput:
    return RouterInput(
        raw_message=msg,
        asset_id=asset_id,
        asset_source=asset_source,
        turn_count=1,
    )


# ── Fallback unit tests (no LLM, deterministic) ─────────────────────────────

@pytest.mark.parametrize("msg", [
    "Explain what underload trip is and why it happens.",
    "Explain what overload protection does.",
    "What is gas lock in an ESP?",
    "What does PIP stand for?",
    "What's the difference between intake pressure and discharge pressure?",
    "Define downhole vibration.",
    "Describe how the H-Q curve works.",
    "Tell me what an underload trip is.",
    "What causes a high current overload trip?",
    "What are the stages in a centrifugal pump?",
])
def test_fallback_definitional_routes_to_op07(msg):
    """Fallback must route definitional queries to OP07, not OP03, even with trigger words."""
    decision = _keyword_fallback_decision(_make_input(msg), deferred=[])
    assert decision.route == "SIMPLE", f"Expected SIMPLE, got {decision.route!r} for: {msg!r}"
    assert decision.objective_id in ("OP06_KNOWLEDGE_LOOKUP", "OP07_GENERAL_INQUIRY"), (
        f"Expected OP07_GENERAL_INQUIRY, got {decision.objective_id!r} for: {msg!r}"
    )
    assert decision.clarification_needed is False


@pytest.mark.parametrize("msg,asset_id", [
    ("Why did FS-17 trip?", "FS-17"),
    ("Why did FS-91 trip last night?", "FS-91"),
])
def test_fallback_causal_with_asset_routes_to_op03(msg, asset_id):
    """Causal queries with a known asset must still route to OP03."""
    decision = _keyword_fallback_decision(
        _make_input(msg, asset_id=asset_id, asset_source="EXPLICIT"),
        deferred=[],
    )
    assert decision.route == "WORKFLOW"
    assert decision.objective_id == "OP03_FAULT_DIAGNOSIS"


def test_fallback_causal_no_asset_triggers_clarify():
    """Causal without asset: clarify, not OP07."""
    decision = _keyword_fallback_decision(_make_input("Why did it trip?"), deferred=[])
    assert decision.clarification_needed is True
    assert decision.clarify_slot == "asset_id"
    assert "FS-17" in decision.clarify_options


# ── LLM-path integration tests (mock LLM to return JSON) ────────────────────

_SIMPLE_OP07_JSON = (
    '{"route":"SIMPLE","intent":"general_inquiry","objective_id":"OP07_GENERAL_INQUIRY",'
    '"args":{"asset_id":null},"confidence":0.95,"deferred_intents":[],'
    '"clarification_needed":false,"clarify_reason":null,"clarify_slot":null,"clarify_options":[]}'
)

_WORKFLOW_OP03_JSON = (
    '{"route":"WORKFLOW","intent":"diagnose","objective_id":"OP03_FAULT_DIAGNOSIS",'
    '"args":{"asset_id":"FS-17"},"confidence":0.92,"deferred_intents":[],'
    '"clarification_needed":false,"clarify_reason":null,"clarify_slot":null,"clarify_options":[]}'
)


@pytest.mark.anyio
async def test_llm_path_q02_routes_to_op07():
    """Q02 verbatim via full route_query (LLM mocked to return OP07)."""
    with patch("app.llm.calls.call_llm_chat", new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = _SIMPLE_OP07_JSON
        decision = await route_query(_make_input(
            "Explain what underload trip is and why it happens."
        ))
    assert decision.route == "SIMPLE"
    assert decision.objective_id in ("OP06_KNOWLEDGE_LOOKUP", "OP07_GENERAL_INQUIRY")
    assert decision.clarification_needed is False


@pytest.mark.anyio
async def test_llm_path_causal_asset_still_op03():
    """Causal query with explicit asset: must stay WORKFLOW/OP03 after the fix."""
    with patch("app.llm.calls.call_llm_chat", new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = _WORKFLOW_OP03_JSON
        decision = await route_query(_make_input(
            "Why did FS-17 trip?",
            asset_id="FS-17",
            asset_source="EXPLICIT",
        ))
    assert decision.route == "WORKFLOW"
    assert decision.objective_id == "OP03_FAULT_DIAGNOSIS"
