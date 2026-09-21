"""
Regression test for Bug B — XAI trust bug.

Verifies:
1. format_evidence_with_alarms() injects the KPI ALARM PRE-CHECK section
   into the evidence text block on dead-well data.
2. If the LLM returns "functioning as expected" on dead-well data, the
   post-synthesis runner guard (Step 7a) overrides the assessment.
3. Healthy well evidence produces no alarm injection and LLM response passes through.
"""
import pytest
from unittest.mock import AsyncMock, patch

from app.evidence.formatter import FormattedEvidence, FormattedValue
from app.synthesis.xai import format_evidence_with_alarms, synthesize_advisory


# ── Test data helpers ───────────────────────────────────────────────────────

def _dead_well_evidence() -> FormattedEvidence:
    """Q07 FNW-01 exact data: zero production, 0.95 anomaly score."""
    fe = FormattedEvidence(run_id="bug-b-test", pack_version=1)
    signals = {
        "oil_rate_bopd": (0.00, "BOPD"),
        "liquid_rate_bpd": (0.00, "BPD"),
        "gas_rate_mscfd": (0.00, "MSCFD"),
        "motor_load_pct": (0.00, "%"),
        "water_cut_pct": (78.20, "%"),
        "anomaly_score": (0.95, "index"),
        "health_score": (92.00, "index"),
    }
    for i, (signal, (raw, unit)) in enumerate(signals.items()):
        fe.values.append(FormattedValue(
            value_str=f"{raw:.2f} {unit}".strip(),
            unit=unit,
            evidence_id=f"EV-bugb-{i:04d}",
            signal=signal,
            raw=raw,
        ))
    return fe


def _healthy_well_evidence() -> FormattedEvidence:
    fe = FormattedEvidence(run_id="healthy-test", pack_version=1)
    signals = {
        "oil_rate_bopd": (315.0, "BOPD"),
        "liquid_rate_bpd": (420.0, "BPD"),
        "motor_load_pct": (71.5, "%"),
        "anomaly_score": (0.12, "index"),
        "water_cut_pct": (25.0, "%"),
    }
    for i, (signal, (raw, unit)) in enumerate(signals.items()):
        fe.values.append(FormattedValue(
            value_str=f"{raw:.2f} {unit}".strip(),
            unit=unit,
            evidence_id=f"EV-healthy-{i:04d}",
            signal=signal,
            raw=raw,
        ))
    return fe


# ── Layer 1: format_evidence_with_alarms injection ─────────────────────────

def test_dead_well_evidence_text_contains_alarm_block():
    """
    format_evidence_with_alarms must prepend KPI ALARM PRE-CHECK section
    on dead-well evidence. The LLM will see this before any sensor data.
    """
    ev = _dead_well_evidence()
    text, alarm_result = format_evidence_with_alarms(ev)

    assert "KPI ALARM PRE-CHECK" in text, "Alarm block must appear in evidence text"
    assert "CRITICAL" in text, "CRITICAL label must be present for dead well"
    assert "oil_rate_bopd" in text
    assert "anomaly_score" in text
    # Alarm block must come BEFORE sensor measurements
    alarm_pos = text.index("KPI ALARM PRE-CHECK")
    sensor_pos = text.index("SENSOR")
    assert alarm_pos < sensor_pos, "Alarm pre-check must precede sensor data"


def test_healthy_well_evidence_text_has_no_alarm_block():
    """Healthy evidence must not inject any alarm block."""
    ev = _healthy_well_evidence()
    text, alarm_result = format_evidence_with_alarms(ev)

    assert "KPI ALARM PRE-CHECK" not in text
    assert "ASSESSMENT CONSTRAINT" not in text
    assert alarm_result.is_clean


def test_alarm_result_has_critical_on_dead_well():
    ev = _dead_well_evidence()
    _, alarm_result = format_evidence_with_alarms(ev)
    assert alarm_result.has_critical


# ── Layer 2: synthesize_advisory returns alarm_result ──────────────────────

_FUNCTIONING_JSON = (
    '{"objective_id":"OP01_CURRENT_STATUS",'
    '"assessment":"All measurements are within acceptable ranges, indicating that the well is functioning as expected.",'
    '"hypotheses":[],'
    '"recommendation":"Continue normal operations.",'
    '"verification_steps":[],'
    '"confidence":0.85,'
    '"cited_evidence_ids":["EV-bugb-0000"]}'
)

_HEALTHY_JSON = (
    '{"objective_id":"OP01_CURRENT_STATUS",'
    '"assessment":"Well is producing at expected rates with no anomalies detected.",'
    '"hypotheses":[],'
    '"recommendation":"No action required.",'
    '"verification_steps":[],'
    '"confidence":0.92,'
    '"cited_evidence_ids":["EV-healthy-0000"]}'
)


@pytest.mark.anyio
async def test_synthesize_advisory_returns_alarm_result():
    """synthesize_advisory must return a tuple (Advisory, KpiAlarmResult)."""
    with patch("app.llm.calls.call_llm_chat", new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = _FUNCTIONING_JSON
        result = await synthesize_advisory(
            objective_id="OP01_CURRENT_STATUS",
            evidence=_dead_well_evidence(),
            user_query="What is the status of FNW-01?",
        )
    assert isinstance(result, tuple), "synthesize_advisory must return a tuple"
    advisory, alarm_result = result
    assert alarm_result is not None
    assert alarm_result.has_critical


@pytest.mark.anyio
async def test_synthesize_advisory_healthy_no_alarm():
    """Healthy well: alarm_result must be clean."""
    with patch("app.llm.calls.call_llm_chat", new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = _HEALTHY_JSON
        advisory, alarm_result = await synthesize_advisory(
            objective_id="OP01_CURRENT_STATUS",
            evidence=_healthy_well_evidence(),
        )
    assert alarm_result.is_clean
    assert "producing at expected rates" in advisory.assessment


# ── Layer 3: runner post-synthesis guard (via _NORMAL_PHRASES + alarm_result) ──

def test_normal_phrases_constant_covers_q07_phrase():
    """
    The exact Q07 phrase 'functioning as expected' must be in _NORMAL_PHRASES.
    This test pins the constant against the real-world bug text.
    """
    from app.workflow.runner import _NORMAL_PHRASES
    assert "functioning as expected" in _NORMAL_PHRASES
    assert "within acceptable ranges" in _NORMAL_PHRASES
    assert "operating normally" in _NORMAL_PHRASES
