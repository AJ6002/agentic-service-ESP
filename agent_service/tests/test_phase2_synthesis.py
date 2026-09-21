"""
Tests for Phase 2 — Synthesis & Enforcement (LLM #3).
Covers Step 2.1 (XAI Synthesizer) and Step 2.2 (Numeric Provenance Check).
Exit Criteria:
1. Live LLM produces a schema-valid Advisory given FormattedEvidence.
2. Injected fake numbers are detected and flagged in ProvenanceResult.
3. LLM-down produces a clear flagged failure, never fabricated advisory.
"""

import pytest
from app.contracts.advisory import Advisory
from app.contracts.evidence import EvidenceItem, EvidencePack
from app.evidence.formatter import format_pack, FormattedEvidence, FormattedValue
from app.llm.client import LLMUnavailableError
from app.llm.calls import AdvisoryOutputInvalid
from app.synthesis.xai import synthesize_advisory, format_evidence_for_prompt
from app.synthesis.numeric_check import check_numeric_provenance


def _sample_formatted_evidence() -> FormattedEvidence:
    return FormattedEvidence(
        run_id="R-test-phase2",
        pack_version=1,
        values=[
            FormattedValue(value_str="87.71 °C", unit="°C", evidence_id="EV-test-0001", signal="motor_temp_c", raw=87.71),
            FormattedValue(value_str="395.40 PSI", unit="PSI", evidence_id="EV-test-0002", signal="int_prs_psi", raw=395.4),
            FormattedValue(value_str="35.70 A", unit="A", evidence_id="EV-test-0003", signal="amp_a", raw=35.7),
            FormattedValue(value_str="53.10 Hz", unit="Hz", evidence_id="EV-test-0004", signal="freq_hz", raw=53.1),
            FormattedValue(value_str="1883.10 PSI", unit="PSI", evidence_id="EV-test-0005", signal="whp_psi", raw=1883.1),
        ],
    )


# ---------------------------------------------------------------------------
# Step 2.1 — XAI Synthesizer Tests
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_xai_synthesizer_live_llm_schema_valid():
    """
    Exit Criterion 1: Real call to LLM produces a schema-valid Advisory.
    Gracefully skips if local LLM gateway is unreachable.
    """
    evidence = _sample_formatted_evidence()
    try:
        advisory, _alarm_result = await synthesize_advisory(
            objective_id="OP03_FAULT_DIAGNOSIS",
            evidence=evidence,
            user_query="Why did FNW-01 trip?",
        )
    except LLMUnavailableError as exc:
        pytest.skip(f"LLM gateway is offline: {exc}")

    assert isinstance(advisory, Advisory)
    assert advisory.objective_id == "OP03_FAULT_DIAGNOSIS"
    assert len(advisory.assessment) > 0
    assert isinstance(advisory.hypotheses, list)
    assert len(advisory.recommendation) > 0
    assert isinstance(advisory.verification_steps, list)
    assert 0.0 <= advisory.confidence <= 1.0
    assert isinstance(advisory.cited_evidence_ids, list)


@pytest.mark.anyio
async def test_xai_synthesizer_llm_down_raises():
    """
    Exit Criterion 3: LLM gateway outage produces clear LLMUnavailableError, not fake text.
    """
    evidence = _sample_formatted_evidence()
    import app.llm.calls as calls_mod

    async def _mock_down(*args, **kwargs):
        raise LLMUnavailableError("simulated llm down")

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(calls_mod, "call_llm_chat", _mock_down)
        with pytest.raises(LLMUnavailableError):
            await synthesize_advisory(
                objective_id="OP03_FAULT_DIAGNOSIS",
                evidence=evidence,
                user_query="Why did FNW-01 trip?",
            )


@pytest.mark.anyio
async def test_xai_synthesizer_malformed_json_retries_and_raises():
    """
    Malformed output after strict retry raises AdvisoryOutputInvalid.
    """
    evidence = _sample_formatted_evidence()
    import app.llm.calls as calls_mod

    async def _mock_bad_json(*args, **kwargs):
        return "I am not returning JSON here."

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(calls_mod, "call_llm_chat", _mock_bad_json)
        with pytest.raises(AdvisoryOutputInvalid):
            await synthesize_advisory(
                objective_id="OP03_FAULT_DIAGNOSIS",
                evidence=evidence,
                user_query="Why did FNW-01 trip?",
            )


# ---------------------------------------------------------------------------
# Step 2.2 — Numeric Provenance Tests
# ---------------------------------------------------------------------------

def test_provenance_clean_advisory_passes():
    """
    Advisory with numbers strictly matching evidence passes provenance.
    """
    evidence = _sample_formatted_evidence()
    advisory = Advisory(
        objective_id="OP03_FAULT_DIAGNOSIS",
        assessment="Intake pressure was 395.4 PSI with motor temperature at 87.71 °C on 2026-09-17.",
        hypotheses=["Normal operational conditions observed at 53.1 Hz."],
        recommendation="Maintain current current draw at 35.7 A.",
        verification_steps=["1. Monitor temperature trends", "2. Check intake gauge"],
        confidence=0.95,
        cited_evidence_ids=["EV-test-0001", "EV-test-0002"],
    )
    result = check_numeric_provenance(advisory, evidence)
    assert result.passed is True
    assert result.unattributed_numbers == []


def test_provenance_catches_hallucinated_number():
    """
    Exit Criterion 2: Injected fake number (e.g. 412.7) is caught and flagged.
    """
    evidence = _sample_formatted_evidence()
    advisory = Advisory(
        objective_id="OP03_FAULT_DIAGNOSIS",
        assessment="Intake pressure dropped unexpectedly to 412.7 PSI while motor temp was 87.71 °C.",
        hypotheses=["Underload trip caused by 999.5 RPM speed spike"],
        recommendation="Inspect surface valve.",
        verification_steps=["1. Verify choke setting"],
        confidence=0.7,
        cited_evidence_ids=["EV-test-0001"],
    )
    result = check_numeric_provenance(advisory, evidence)
    assert result.passed is False
    assert "412.7" in result.unattributed_numbers
    assert "999.5" in result.unattributed_numbers


def test_provenance_ignores_dates_and_list_indexes():
    """
    Dates (e.g. 2026-09-18) and numbered list headers ('1.', '2.') must not be flagged.
    """
    evidence = _sample_formatted_evidence()
    advisory = Advisory(
        objective_id="OP03_FAULT_DIAGNOSIS",
        assessment="Recorded on 2026-08-30 at 14:18 with motor temp 87.71 °C.",
        hypotheses=["No anomalous behavior."],
        recommendation="Continue operations.",
        verification_steps=["1. Verify gauge", "2. Log reading"],
        confidence=0.99,
        cited_evidence_ids=["EV-test-0001"],
    )
    result = check_numeric_provenance(advisory, evidence)
    assert result.passed is True
    assert result.unattributed_numbers == []


def test_provenance_catches_unit_attached_hallucinated_number():
    """
    Unit-attached numbers like '412.7PSI' or '999.5RPM' must be normalized and
    checked, not silently ignored due to negative lookahead blindspots.
    """
    evidence = _sample_formatted_evidence()
    advisory = Advisory(
        objective_id="OP03_FAULT_DIAGNOSIS",
        assessment="Intake pressure dropped to 412.7PSI with motor temp at 87.71°C.",
        hypotheses=["Speed spike of 999.5RPM detected."],
        recommendation="Verify choke setting.",
        verification_steps=["1. Check surface pressure at 395.4PSI"],
        confidence=0.8,
        cited_evidence_ids=["EV-test-0001"],
    )
    result = check_numeric_provenance(advisory, evidence)
    assert result.passed is False
    assert "412.7" in result.unattributed_numbers
    assert "999.5" in result.unattributed_numbers


def test_provenance_ignores_well_id_numeric_suffix():
    """
    Regression: mentioning the well by name (e.g. "FS-17") must never be
    flagged as an unattributed number just because the ID's numeric suffix
    ("17") isn't itself in the evidence pack. Found live: every OP01 advisory
    mentions the well ID, and "17" tripped a false-positive provenance
    warning before well IDs were added to the noise-stripping rules.
    """
    evidence = _sample_formatted_evidence()
    advisory = Advisory(
        objective_id="OP01_CURRENT_STATUS",
        assessment="Well FS-17 is operating normally with motor temperature at 87.71 °C.",
        hypotheses=["No anomalies detected on FNW-01 or ULFA-5."],
        recommendation="Continue monitoring FSWS-001-A per standard schedule.",
        verification_steps=["1. Re-check FS-17 shortly."],
        confidence=0.9,
        cited_evidence_ids=["EV-test-0001"],
    )
    result = check_numeric_provenance(advisory, evidence)
    assert result.passed is True
    assert result.unattributed_numbers == []


def test_provenance_accepts_comma_separated_thousands():
    """
    Comma-separated thousands (e.g. 1,883.1 PSI) matching raw evidence (1883.1)
    must pass without false-positive unattributed number warnings.
    """
    evidence = _sample_formatted_evidence()
    advisory = Advisory(
        objective_id="OP03_FAULT_DIAGNOSIS",
        assessment="Wellhead pressure stabilized at 1,883.1 PSI while motor temp was 87.71 °C.",
        hypotheses=["Normal pressure envelope."],
        recommendation="Continue current draw of 35.70 A.",
        verification_steps=["1. Monitor trends"],
        confidence=0.95,
        cited_evidence_ids=["EV-test-0001", "EV-test-0005"],
    )
    result = check_numeric_provenance(advisory, evidence)
    assert result.passed is True
    assert result.unattributed_numbers == []
