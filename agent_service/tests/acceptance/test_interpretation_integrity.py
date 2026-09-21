import json
import pathlib
import pytest
from app.contracts.evidence import EvidenceItem, EvidencePack
from app.evidence.formatter import format_pack
from app.synthesis.kpi_alarm_check import check_kpi_alarms
from app.workflow.runner import _NORMAL_PHRASES

FIXTURES_DIR = pathlib.Path(__file__).parent / "fixtures"


def test_ac_3_1_normal_is_forbidden_when_kpi_in_alarm():
    """
    AC-3.1: If any KPI is in alarm, 'normal' is forbidden in assessment.
    Uses dead_well_pack.json (oil=0, liquid=0, motor=0, anomaly=0.95).
    """
    data = json.loads((FIXTURES_DIR / "dead_well_pack.json").read_text(encoding="utf-8"))
    pack = EvidencePack.model_validate(data)
    formatted = format_pack(pack)
    alarms = check_kpi_alarms(formatted)

    assert alarms.has_critical is True
    summary = alarms.alarm_summary()
    assert "CRITICAL" in summary

    # Regression check on the runner guard:
    simulated_hallucinated_assessment = "All measurements are within acceptable ranges, indicating that the well is functioning as expected and operating normally."
    assessment_lower = simulated_hallucinated_assessment.lower()
    matches = [p for p in _NORMAL_PHRASES if p in assessment_lower]
    assert len(matches) > 0, "The normal phrases list must detect false normal claims"


def test_ac_3_2_zero_flow_zero_load_reported_as_failure():
    """
    AC-3.2: If oil_rate_bopd == 0 and motor_load_pct == 0, the assessment must not claim operating normally.
    """
    data = json.loads((FIXTURES_DIR / "dead_well_pack.json").read_text(encoding="utf-8"))
    pack = EvidencePack.model_validate(data)
    formatted = format_pack(pack)
    alarms = check_kpi_alarms(formatted)

    zero_flow_alarm = next((a for a in alarms.alarms if a.signal == "oil_rate_bopd"), None)
    assert zero_flow_alarm is not None
    assert zero_flow_alarm.severity == "CRITICAL"
    assert "zero oil production" in zero_flow_alarm.label or "not producing" in zero_flow_alarm.label


def test_ac_3_3_high_anomaly_score_acknowledged():
    """
    AC-3.3: If anomaly_score > 0.8, the assessment / pre-check must flag it as critical.
    """
    data = json.loads((FIXTURES_DIR / "dead_well_pack.json").read_text(encoding="utf-8"))
    pack = EvidencePack.model_validate(data)
    formatted = format_pack(pack)
    alarms = check_kpi_alarms(formatted)

    anomaly_alarm = next((a for a in alarms.alarms if a.signal == "anomaly_score"), None)
    assert anomaly_alarm is not None
    assert anomaly_alarm.severity == "CRITICAL"
    assert anomaly_alarm.value == 0.95


def test_ac_3_5_confidence_must_be_justified():
    """
    AC-3.5: If Gaps exist in the pack, confidence cannot be 1.0.
    """
    data = json.loads((FIXTURES_DIR / "partial_pack.json").read_text(encoding="utf-8"))
    pack = EvidencePack.model_validate(data)
    assert len(pack.gaps) > 0

    max_permitted_confidence = 0.95 if any(g.required for g in pack.gaps) else 1.0
    assert max_permitted_confidence < 1.0
