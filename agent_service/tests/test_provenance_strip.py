"""
Unit tests for numeric sentence stripping and count-only warning banners (U5).
"""
import pytest

import app.contracts  # break circular import
from app.contracts.advisory import Advisory, ProvenanceResult
from app.contracts.evidence import EvidencePack, EvidenceItem
from app.evidence.formatter import FormattedEvidence, FormattedValue
from app.synthesis.citation_check import CitationCheckResult
from app.workflow.runner import _format_advisory_text


def _make_evidence_with_values(values: list[tuple[str, float]]) -> FormattedEvidence:
    fe = FormattedEvidence(run_id="test-strip-ev", pack_version=1)
    for i, (sig, val) in enumerate(values):
        fe.values.append(
            FormattedValue(
                value_str=f"{val:.2f}",
                unit="",
                evidence_id=f"EV-VAL-{i:04d}",
                signal=sig,
                raw=val,
            )
        )
    return fe


def test_format_advisory_text_count_only_banners():
    """Warning banners must only display counts, never raw unverified numbers or step texts."""
    advisory = Advisory(
        objective_id="OP04_HEALTH_ASSESSMENT",
        assessment="Health score is degraded.",
        hypotheses=[],
        recommendation="Inspect pump.",
        verification_steps=[],
        cited_evidence_ids=[],
    )
    prov = ProvenanceResult(
        passed=False,
        unattributed_numbers=["2000", "150.5"],
        attributed_numbers=[],
    )
    cite = CitationCheckResult(
        passed=False,
        unverified_citations=["Missing citation in step: Inspect intake pressure...", "[FAKE_DOC §1.1] (document not in pack)"],
        verified_citations=[],
        flagged_steps=[],
        flagged_verification_steps=[],
    )

    text = _format_advisory_text(
        objective_id="OP04_HEALTH_ASSESSMENT",
        args={"asset_id": "FS-17"},
        advisory=advisory,
        pack=None,
        provenance=prov,
        results=[],
        citation_res=cite,
    )

    # Must contain count notices
    assert "[WARNING: 2 unverified figure(s) removed from assessment]" in text
    assert "[WARNING: 2 unverified citation(s) removed]" in text

    # Must NOT contain raw unverified numbers or unverified citation step strings
    assert "2000" not in text
    assert "150.5" not in text
    assert "Inspect intake pressure" not in text
    assert "FAKE_DOC" not in text


def test_strip_unverified_provenance_removes_unverified_sentence():
    """When a sentence contains an unverified figure without subordinate clause, it is dropped."""
    from app.workflow.runner import strip_unverified_provenance
    raw = "The normal operating pressure is around 2000 psi. Motor current is 35.00 A which is within operating limits."
    unattributed = ["2000"]
    result = strip_unverified_provenance(raw, unattributed)
    assert "2000" not in result
    assert "Motor current is 35.00 A" in result



def test_clause_level_provenance_stripping_preserves_valid_telemetry():
    """Clause-level stripping removes unverified comparison/baseline while preserving verified telemetry."""
    from app.workflow.runner import strip_unverified_provenance
    raw = "The oil rate is 399.10 BOPD, which is below the recommended baseline of 500 BOPD."
    unattributed = ["500"]
    result = strip_unverified_provenance(raw, unattributed)
    assert "399.10" in result
    assert "500" not in result
    assert "399.10 BOPD" in result

