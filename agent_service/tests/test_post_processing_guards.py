import pytest
from app.contracts.advisory import Advisory
from app.evidence.formatter import FormattedEvidence, FormattedValue, FormattedEventRecord
from app.synthesis.post_processing_guards import (
    enforce_number_provenance,
    enforce_cause_provenance,
    enforce_no_contradictions,
    apply_post_processing_guards,
)


@pytest.fixture
def mock_evidence():
    return FormattedEvidence(
        run_id="R-TEST",
        pack_version=1,
        values=[
            FormattedValue(value_str="60.2", unit="", evidence_id="EV-1", signal="fleet_health_score", raw=60.2),
            FormattedValue(value_str="42.0", unit="", evidence_id="EV-2", signal="health_score", raw=42.0, well_id="FS-004"),
            FormattedValue(value_str="68.0", unit="", evidence_id="EV-3", signal="health_score", raw=68.0, well_id="FNW-001"),
            FormattedValue(value_str="7250.0 BPD", unit="BPD", evidence_id="EV-4", signal="flow_rate_bpd", raw=7250.0),
        ],
        events=[
            FormattedEventRecord(
                evidence_id="EV-5",
                well_id="FS-004",
                trip_cause="UNDERLOAD_PUMP_OFF",
                alarms=["OUTSIDE_RECOMMENDED_OPERATING_RANGE"],
                scenario="dry_well_pump_off",
                operating_state="STOPPED",
            )
        ],
    )


def test_guard1_rejects_unverified_numbers_in_hypotheses(mock_evidence):
    adv = Advisory(
        objective_id="OP08_FLEET_INVENTORY",
        assessment="The fleet health score is 60.20 with total rate 7250.0 BPD.",
        hypotheses=[
            "FS-004 has a critical health score of 45.0.",  # 45.0 is unverified -> REJECT
            "FS-004 has health score of 42.0.",            # 42.0 is verified -> KEEP
            "FS-006 has score 55.0.",                      # 55.0 is unverified -> REJECT
        ],
        recommendation="Surveillance on FS-004.",
        confidence=0.9,
    )
    res = enforce_number_provenance(adv, mock_evidence)
    assert len(res.hypotheses) == 1
    assert "42.0" in res.hypotheses[0]
    assert not any("45.0" in h for h in res.hypotheses)
    assert not any("55.0" in h for h in res.hypotheses)


def test_guard2_rejects_ungrounded_causal_claims(mock_evidence):
    adv = Advisory(
        objective_id="OP13_FLEET_EXECUTIVE_REPORT",
        assessment="Fleet evaluation.",
        hypotheses=[
            "The well is tripped due to UNDERLOAD_PUMP_OFF.",  # Grounded -> KEEP
            "The well is tripped due to severe overload and high oil viscosity.",  # Ungrounded -> REJECT
            "The well is experiencing dry well pump off condition.",  # Grounded -> KEEP
            "The well failed because of sand ingress and casing leak.",  # Ungrounded -> REJECT
        ],
        recommendation="Action plan.",
        confidence=0.9,
    )
    res = enforce_cause_provenance(adv, mock_evidence)
    assert len(res.hypotheses) == 2
    assert any("UNDERLOAD_PUMP_OFF" in h for h in res.hypotheses)
    assert any("dry well pump off" in h for h in res.hypotheses)
    assert not any("casing leak" in h for h in res.hypotheses)


def test_guard3_resolves_self_contradictions():
    adv = Advisory(
        objective_id="OP13_FLEET_EXECUTIVE_REPORT",
        assessment="The fleet health score is 60.20, indicating a moderate health status. The fleet health status is not operating normally, within acceptable ranges, or functioning as expected due to critical wells.",
        hypotheses=[
            "The fleet health score is below the recommended threshold of 50.",  # Contradicts 60.20 > 50
            "Critical wells FS-004 is tripped due to underload.",
        ],
        recommendation="Surveillance.",
        confidence=0.9,
    )
    res = enforce_no_contradictions(adv, is_fleet_scope=True)
    assert "below the recommended threshold of 50" not in res.hypotheses[0]
    assert "operating normally, within acceptable ranges" not in res.assessment


def test_composite_guards_pipeline(mock_evidence):
    adv = Advisory(
        objective_id="OP08_FLEET_INVENTORY",
        assessment="The fleet health score is 60.20 (DEGRADED). FS-004 is tripped with health score 42.0. Unverified fake value 999.9.",
        hypotheses=[
            "FS-004 has score 45.0.",  # Guard 1 rejects
            "FS-004 is stopped due to random corrosion.",  # Guard 2 rejects
            "FS-004 has score 42.0 due to UNDERLOAD_PUMP_OFF.",  # Passes both
        ],
        recommendation="Check FS-004.",
        confidence=0.9,
    )
    res = apply_post_processing_guards(adv, mock_evidence, is_fleet_scope=True)
    assert res is not None
    assert "999.9" not in res.assessment
    assert len(res.hypotheses) == 1
    assert "UNDERLOAD_PUMP_OFF" in res.hypotheses[0]
