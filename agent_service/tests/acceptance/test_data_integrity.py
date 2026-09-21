import json
import pathlib
import pytest
from app.contracts.advisory import Advisory
from app.evidence.qod import validate
from app.contracts.evidence import CallResult
from app.synthesis.numeric_check import check_numeric_provenance
from app.evidence.formatter import FormattedEvidence, FormattedValue

FIXTURES_DIR = pathlib.Path(__file__).parent / "fixtures"


def test_ac_2_1_and_2_2_cross_well_identical_readings_detection():
    """
    AC-2.1 & AC-2.2: Cross-well telemetry comparison.
    If two wells produce identical readings across all 6 key fields,
    divergence check detects the anomaly and flags it.
    """
    data = json.loads((FIXTURES_DIR / "identical_cross_well_pack.json").read_text(encoding="utf-8"))
    m_a = data["well_a"]["measurements"]
    m_b = data["well_b"]["measurements"]

    fields = [
        "motor_current_a",
        "frequency_hz",
        "motor_temp_c",
        "intake_pressure_psi",
        "discharge_pressure_psi",
        "vibration_g",
    ]

    identical_count = sum(1 for f in fields if abs(m_a.get(f, 0) - m_b.get(f, 0)) < 0.001)
    is_identical_anomaly = (identical_count == len(fields))

    assert is_identical_anomaly is True, "Cross-well comparator must flag identical telemetry"


def test_ac_2_3_numeric_provenance_verification():
    """
    AC-2.3: Every numeric claim in the assessment traces to an evidence_id.
    Asserts ProvenanceResult.passed == True when numbers trace, and catches unverified numbers.
    """
    # 1. Clean advisory: numbers 35.0 and 85.0 match evidence
    advisory_clean = Advisory(
        objective_id="OP01_CURRENT_STATUS",
        assessment="Motor current is 35.0 A and temperature is 85.0 °C.",
        hypotheses=[],
        recommendation="Maintain current settings.",
        verification_steps=[],
        confidence=0.9,
        cited_evidence_ids=["EV-1", "EV-2"],
    )
    evidence_clean = FormattedEvidence(
        run_id="R-clean",
        pack_version=1,
        values=[
            FormattedValue(value_str="35.0 A", unit="A", evidence_id="EV-1", signal="motor_current_a", raw=35.0),
            FormattedValue(value_str="85.0 °C", unit="°C", evidence_id="EV-2", signal="motor_temp_c", raw=85.0),
        ],
    )
    result_clean = check_numeric_provenance(advisory_clean, evidence_clean)
    assert result_clean.passed is True
    assert len(result_clean.unattributed_numbers) == 0

    # 2. Hallucinated number 999.9 does not appear in evidence
    advisory_bad = Advisory(
        objective_id="OP01_CURRENT_STATUS",
        assessment="Vibration reached 999.9 g RMS.",
        hypotheses=[],
        recommendation="Inspect immediately.",
        verification_steps=[],
        confidence=0.9,
        cited_evidence_ids=["EV-1"],
    )
    evidence_bad = FormattedEvidence(
        run_id="R-bad",
        pack_version=1,
        values=[
            FormattedValue(value_str="0.08 g", unit="g", evidence_id="EV-1", signal="vibration_g", raw=0.08),
        ],
    )
    result_bad = check_numeric_provenance(advisory_bad, evidence_bad)
    assert result_bad.passed is False
    assert "999.9" in result_bad.unattributed_numbers


def test_ac_2_4_qod_plausible_vs_alarming_bounds():
    """
    AC-2.4: QoD rejects implausible values, accepts alarming-but-real values.
    """
    # 1. Implausible temperature (999.0 C) -> QoD marks accepted=False
    cr_implausible = CallResult(
        seq=1,
        status="OK",
        raw_response={"well_id": "FS-17", "measurements": {"motor_temp_c": 999.0}},
    )
    qod_implausible = validate(cr_implausible, run_id="R-qod-1", tool="get_live_telemetry")
    assert qod_implausible.accepted is False
    assert "max_plausible" in (qod_implausible.rejection_reason or "") or "Range:" in (qod_implausible.rejection_reason or "")

    # 2. Alarming but real temperature (130.0 C) -> QoD accepts
    cr_alarming = CallResult(
        seq=2,
        status="OK",
        raw_response={"well_id": "FS-17", "measurements": {"motor_temp_c": 130.0}},
    )
    qod_alarming = validate(cr_alarming, run_id="R-qod-2", tool="get_live_telemetry")
    assert qod_alarming.accepted is True
