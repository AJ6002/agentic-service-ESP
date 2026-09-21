import pytest
from unittest.mock import patch, AsyncMock
from app.contracts.advisory import Advisory
from app.evidence.formatter import FormattedEvidence, FormattedValue
from app.synthesis.xai import synthesize_advisory


@pytest.mark.anyio
async def test_op04_health_band_preserved_when_present():
    evidence = FormattedEvidence(
        run_id="run-1",
        pack_version=1,
        values=[
            FormattedValue(
                value_str="62.5",
                unit="score",
                evidence_id="EV-1",
                signal="health_score",
                raw=62.5,
            ),
        ]
    )
    mock_advisory = Advisory(
        objective_id="OP04_HEALTH_ASSESSMENT",
        assessment="Asset FS-17 is in a DEGRADED state with elevated temperature.",
        recommendation="Check cooling.",
        cited_evidence_ids=["EV-1"],
    )

    with patch("app.synthesis.xai.narrate", new_callable=AsyncMock) as mock_narrate:
        mock_narrate.return_value = mock_advisory
        advisory, _ = await synthesize_advisory("OP04_HEALTH_ASSESSMENT", evidence, "test query")
        assert "DEGRADED" in advisory.assessment
        assert advisory.assessment.startswith("Asset FS-17 is in a DEGRADED state")


@pytest.mark.anyio
async def test_op04_health_band_injected_when_llm_recites_only_numbers_healthy():
    evidence = FormattedEvidence(
        run_id="run-1",
        pack_version=1,
        values=[
            FormattedValue(
                value_str="88.0",
                unit="score",
                evidence_id="EV-1",
                signal="health_score",
                raw=88.0,
            ),
        ]
    )
    # LLM merely recited numbers without naming the band
    mock_advisory = Advisory(
        objective_id="OP04_HEALTH_ASSESSMENT",
        assessment="Health score is 88.0 with motor temperature at 85 C.",
        recommendation="Maintain current frequency.",
        cited_evidence_ids=["EV-1"],
    )

    with patch("app.synthesis.xai.narrate", new_callable=AsyncMock) as mock_narrate:
        mock_narrate.return_value = mock_advisory
        advisory, _ = await synthesize_advisory("OP04_HEALTH_ASSESSMENT", evidence, "test query")
        assert any(b in advisory.assessment for b in ["HEALTHY", "DEGRADED", "CRITICAL"])
        assert "HEALTHY" in advisory.assessment


@pytest.mark.anyio
async def test_op04_health_band_injected_critical_from_score():
    evidence = FormattedEvidence(
        run_id="run-1",
        pack_version=1,
        values=[
            FormattedValue(
                value_str="42.0",
                unit="score",
                evidence_id="EV-1",
                signal="health_score",
                raw=42.0,
            ),
        ]
    )
    mock_advisory = Advisory(
        objective_id="OP04_HEALTH_ASSESSMENT",
        assessment="Health score dropped to 42.0 due to high vibration.",
        recommendation="Shut down for inspection.",
        cited_evidence_ids=["EV-1"],
    )

    with patch("app.synthesis.xai.narrate", new_callable=AsyncMock) as mock_narrate:
        mock_narrate.return_value = mock_advisory
        advisory, _ = await synthesize_advisory("OP04_HEALTH_ASSESSMENT", evidence, "test query")
        assert "CRITICAL" in advisory.assessment


@pytest.mark.anyio
async def test_op04_health_band_injected_from_band_signal():
    evidence = FormattedEvidence(
        run_id="run-1",
        pack_version=1,
        values=[
            FormattedValue(
                value_str="DEGRADED",
                unit="band",
                evidence_id="EV-1",
                signal="health_band",
                raw="DEGRADED",
            ),
            FormattedValue(
                value_str="68.0",
                unit="score",
                evidence_id="EV-1",
                signal="health_score",
                raw=68.0,
            ),
        ]
    )
    mock_advisory = Advisory(
        objective_id="OP04_HEALTH_ASSESSMENT",
        assessment="Vibration is 0.45 in/s and score is 68.0.",
        recommendation="Monitor drive.",
        cited_evidence_ids=["EV-1"],
    )

    with patch("app.synthesis.xai.narrate", new_callable=AsyncMock) as mock_narrate:
        mock_narrate.return_value = mock_advisory
        advisory, _ = await synthesize_advisory("OP04_HEALTH_ASSESSMENT", evidence, "test query")
        assert "DEGRADED" in advisory.assessment
