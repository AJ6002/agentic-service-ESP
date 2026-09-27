"""
Unit tests for XAI post-synthesis guards and contradiction detection.
Tests OP02 stable vs declining contradiction handling and positive production rate guards.
"""
import pytest
from unittest.mock import AsyncMock, patch

import app.contracts  # break circular import
from app.contracts.advisory import Advisory
from app.evidence.formatter import FormattedEvidence, FormattedValue
from app.synthesis.xai import synthesize_advisory


def _make_op02_evidence(trend: str = "STABLE", decline_rate: float = 10.0) -> FormattedEvidence:
    fe = FormattedEvidence(run_id="test-op02", pack_version=1)
    fe.values.append(
        FormattedValue(
            value_str=trend,
            unit="",
            evidence_id="EV-0001",
            signal="production_trend",
            raw=trend,
        )
    )
    fe.values.append(
        FormattedValue(
            value_str=f"{decline_rate:.2f} BPD/day",
            unit="BPD/day",
            evidence_id="EV-0002",
            signal="decline_rate_bpd_per_day",
            raw=decline_rate,
        )
    )
    return fe


def _make_op01_evidence(oil_rate: float = 399.10, liquid_rate: float = 399.10) -> FormattedEvidence:
    fe = FormattedEvidence(run_id="test-op01", pack_version=1)
    fe.values.append(
        FormattedValue(
            value_str=f"{oil_rate:.2f} BOPD",
            unit="BOPD",
            evidence_id="EV-0001",
            signal="oil_rate_bopd",
            raw=oil_rate,
        )
    )
    fe.values.append(
        FormattedValue(
            value_str=f"{liquid_rate:.2f} BPD",
            unit="BPD",
            evidence_id="EV-0002",
            signal="liquid_rate_bpd",
            raw=liquid_rate,
        )
    )
    return fe


@pytest.mark.anyio
async def test_op02_stable_trend_strips_declining_sentence():
    """When trend is STABLE, any LLM sentence claiming decline is stripped."""
    mock_advisory = Advisory(
        objective_id="OP02_PRODUCTION_DECLINE_RCA",
        assessment="The production trend for FS-17 is DECLINING at a rate of 10.00 BPD/day. All other metrics normal.",
        hypotheses=[],
        recommendation="Monitor well.",
        verification_steps=[],
        cited_evidence_ids=["EV-0001"],
    )
    evidence = _make_op02_evidence(trend="STABLE")

    with patch("app.synthesis.xai.narrate", new=AsyncMock(return_value=mock_advisory)):
        adv, _ = await synthesize_advisory("OP02_PRODUCTION_DECLINE_RCA", evidence)

    assert adv is not None
    assert "declining" not in adv.assessment.lower()
    assert "10.00 bpd/day" not in adv.assessment.lower()
    assert "stable" in adv.assessment.lower()
    assert "All other metrics normal." in adv.assessment


@pytest.mark.anyio
async def test_op02_stable_trend_with_existing_stable_claim_unchanged():
    """When trend is STABLE and LLM already says stable, do not double-prepend."""
    mock_advisory = Advisory(
        objective_id="OP02_PRODUCTION_DECLINE_RCA",
        assessment="Production rate is stable with no abnormal decline detected. Oil rate is steady at 400 BOPD.",
        hypotheses=[],
        recommendation="Continue normal operation.",
        verification_steps=[],
        cited_evidence_ids=["EV-0001"],
    )
    evidence = _make_op02_evidence(trend="STABLE")

    with patch("app.synthesis.xai.narrate", new=AsyncMock(return_value=mock_advisory)):
        adv, _ = await synthesize_advisory("OP02_PRODUCTION_DECLINE_RCA", evidence)

    assert adv is not None
    assert adv.assessment.count("stable") == 1
    assert "declining" not in adv.assessment.lower()


@pytest.mark.anyio
async def test_op02_declining_trend_strips_stable_sentence():
    """When trend is DECLINING, any sentence claiming stability is stripped."""
    mock_advisory = Advisory(
        objective_id="OP02_PRODUCTION_DECLINE_RCA",
        assessment="Production rate is stable with no abnormal decline detected. Production has declined at an estimated rate of 10.00 BPD/day.",
        hypotheses=[],
        recommendation="Check choke valve.",
        verification_steps=[],
        cited_evidence_ids=["EV-0001"],
    )
    evidence = _make_op02_evidence(trend="DECLINING")

    with patch("app.synthesis.xai.narrate", new=AsyncMock(return_value=mock_advisory)):
        adv, _ = await synthesize_advisory("OP02_PRODUCTION_DECLINE_RCA", evidence)

    assert adv is not None
    assert "stable" not in adv.assessment.lower()
    assert "declined" in adv.assessment.lower() or "declining" in adv.assessment.lower()


@pytest.mark.anyio
async def test_positive_production_rate_strips_not_producing_claim():
    """When oil_rate > 0, false 'not producing' claims are stripped."""
    mock_advisory = Advisory(
        objective_id="OP01_CURRENT_STATUS",
        assessment="The oil rate is 399.10 BOPD. The well is not producing oil or liquid, and the motor is running at 102.50% load.",
        hypotheses=[],
        recommendation="Monitor.",
        verification_steps=[],
        cited_evidence_ids=["EV-0001"],
    )
    evidence = _make_op01_evidence(oil_rate=399.10, liquid_rate=399.10)

    with patch("app.synthesis.xai.narrate", new=AsyncMock(return_value=mock_advisory)):
        adv, _ = await synthesize_advisory("OP01_CURRENT_STATUS", evidence)

    assert adv is not None
    assert "not producing" not in adv.assessment.lower()
    assert "399.10 BOPD" in adv.assessment


@pytest.mark.anyio
async def test_relational_comparison_inverted_below_fixed():
    """When LLM says '350.40 PSI, which is below baseline of 150 psi', it is corrected to 'above'."""
    from app.synthesis.xai import sanitize_relational_comparisons
    raw = "The primary intake pressure was measured at 350.40 PSI, which is below the recommended baseline of 150 psi."
    fixed = sanitize_relational_comparisons(raw)
    assert "above" in fixed.lower()
    assert "below" not in fixed.lower()
    assert "350.40" in fixed
    assert "150" in fixed


@pytest.mark.anyio
async def test_universal_flow_contradiction_strips_flow_rates_zero_sentence():
    """When assessment has 400.00 BOPD, 'flow rates are zero' sentence is stripped."""
    from app.synthesis.xai import sanitize_positive_production_contradictions
    raw = "The flow rate is 400.00 BOPD and motor load is 102.50%. The well is not producing oil or liquid, as the flow rates are zero."
    sanitized = sanitize_positive_production_contradictions(raw)
    assert "400.00 BOPD" in sanitized
    assert "not producing" not in sanitized.lower()
    assert "flow rates are zero" not in sanitized.lower()

