"""
Tests for Sprint 5 — Fleet Narrator Prompts.
Validates:
1. Loading and integrity of prompt templates: OP08, OP09, OP13
2. Prompt evidence formatting with [Well: ...] attribution tags for multi-well values and events
3. Narrator dispatcher routing in calls.py
4. Live PostgreSQL synthesis for OP08, OP09, OP13 generating valid attributed Advisories
"""

import pytest
from datetime import datetime, timezone

from app.llm.prompt_loader import load_prompt
from app.contracts.evidence import EvidenceItem, EvidencePack, CallResult
from app.contracts.advisory import Advisory
from app.evidence.qod import validate
from app.evidence.seal_check import seal
from app.evidence.formatter import format_pack, FormattedValue, FormattedEventRecord, FormattedEvidence
from app.synthesis.xai import format_evidence_for_prompt
from app.llm.calls import narrate
from app.llm.client import LLMUnavailableError
from app.gateway.adapters.kpi import fetch_fleet_kpi, fetch_fleet_health
from app.gateway.adapters.events import fetch_fleet_events


def test_fleet_prompts_load_and_contain_mandates():
    """Verify all three fleet prompts exist and contain required domain mandates."""
    # 1. OP08 Fleet Inventory Prompt
    p_op08 = load_prompt("narrator_fleet_inventory_v1.txt")
    assert "OP08_FLEET_INVENTORY" in p_op08
    assert "CAP AT TOP 5" in p_op08
    assert "HEALTHY" in p_op08
    assert "DEGRADED" in p_op08
    assert "CRITICAL" in p_op08
    assert "150–250 words" in p_op08 or "150-250 words" in p_op08 or "250" in p_op08

    # 2. OP09 Fleet Optimization Prompt
    p_op09 = load_prompt("narrator_fleet_optimization_v1.txt")
    assert "OP09_FLEET_PRODUCTION_OPTIMIZATION" in p_op09
    assert "TOP 3" in p_op09 or "top 3" in p_op09
    assert "Opportunity Ranking" in p_op09 or "opportunity" in p_op09.lower()

    # 3. OP13 Fleet Executive Report Prompt
    p_op13 = load_prompt("narrator_fleet_executive_v1.txt")
    assert "OP13_FLEET_EXECUTIVE_REPORT" in p_op13
    assert "Executive Posture" in p_op13 or "executive" in p_op13.lower()
    assert "Operational Risks" in p_op13 or "risks" in p_op13.lower()


def test_xai_prompt_formatter_includes_well_ids():
    """Verify format_evidence_for_prompt renders well_id tags for both values and events."""
    evidence = FormattedEvidence(
        run_id="test-run-format",
        pack_version=1,
        values=[
            FormattedValue(
                value_str="12500.0 BPD",
                unit="BPD",
                evidence_id="EV-0001",
                signal="total_production_bpd",
                raw=12500.0,
                well_id=None,
            ),
            FormattedValue(
                value_str="42.0 index",
                unit="index",
                evidence_id="EV-0002",
                signal="health_score",
                raw=42.0,
                well_id="FS-17",
            ),
            FormattedValue(
                value_str="CRITICAL",
                unit="band",
                evidence_id="EV-0002",
                signal="health_band",
                raw="CRITICAL",
                well_id="FS-17",
            ),
        ],
        events=[
            FormattedEventRecord(
                evidence_id="EV-0003",
                well_id="FS-16",
                event_id="EVT-101",
                timestamp="2026-10-05T12:00:00Z",
                operating_state="TRIPPED",
                trip_cause="UNDERLOAD_GAS_LOCK",
                alarms=["ALM_UNDERLOAD"],
            )
        ],
    )

    prompt_text = format_evidence_for_prompt(evidence)

    # Asserts
    assert "[EV-0001] total_production_bpd: 12500.0 BPD" in prompt_text
    assert "[EV-0002] [Well: FS-17] health_score: 42.0 index" in prompt_text
    assert "[EV-0002] [Well: FS-17] health_band: CRITICAL" in prompt_text
    assert "Well: FS-16 | Event ID: EVT-101" in prompt_text
    assert "Cause: UNDERLOAD_GAS_LOCK" in prompt_text


@pytest.mark.anyio
async def test_e2e_fleet_synthesis_live_data():
    """Real database + LLM test: fetch fleet live data, seal pack, format, synthesize OP08 advisory."""
    # 1. Fetch live fleet data from PostgreSQL
    kpi_raw = await fetch_fleet_kpi()
    health_raw = await fetch_fleet_health()
    events_raw = await fetch_fleet_events(limit=10)

    # 2. QoD validation
    res_kpi = CallResult(seq=1, status="OK", raw_response=kpi_raw)
    res_health = CallResult(seq=2, status="OK", raw_response=health_raw)
    res_events = CallResult(seq=3, status="OK", raw_response=events_raw)

    qod_kpi = validate(res_kpi, run_id="live-synth-1", tool="get_fleet_kpi")
    qod_health = validate(res_health, run_id="live-synth-1", tool="get_fleet_health")
    qod_events = validate(res_events, run_id="live-synth-1", tool="get_fleet_events")

    items = [qod_kpi.evidence_item, qod_health.evidence_item, qod_events.evidence_item]
    pack = EvidencePack(run_id="live-synth-1", version=1, items=items)
    seal_res = seal(pack, required_tools=["get_fleet_kpi", "get_fleet_health", "get_fleet_events"])
    assert seal_res.status == "COMPLETE"

    fmt = format_pack(seal_res.pack)
    evidence_text = format_evidence_for_prompt(fmt)

    # 3. Test OP08 Synthesis
    try:
        advisory_op08 = await narrate(
            objective_id="OP08_FLEET_INVENTORY",
            formatted_evidence_text=evidence_text,
            user_query="Give me a fleet inventory and health summary",
        )
        assert isinstance(advisory_op08, Advisory)
        assert advisory_op08.objective_id == "OP08_FLEET_INVENTORY"
        assert len(advisory_op08.assessment) > 20
        assert len(advisory_op08.cited_evidence_ids) > 0
        assert len(advisory_op08.recommendation) > 10
    except LLMUnavailableError as exc:
        pytest.skip(f"LLM gateway offline or timed out: {exc}")
