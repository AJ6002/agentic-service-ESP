"""
Unit tests for citation provenance check covering both troubleshooting_steps and verification_steps (U4).
"""
import pytest

import app.contracts  # break circular import
from app.contracts.advisory import Advisory
from app.contracts.evidence import EvidencePack, EvidenceItem
from app.synthesis.citation_check import check_citation_provenance, CitationCheckResult


def _make_test_pack(doc_id: str = "API_RP_11S", section: str = "5.4") -> EvidencePack:
    return EvidencePack(
        run_id="test-cite-pack",
        items=[
            EvidenceItem(
                evidence_id="EV-KB-001",
                source_domain="KNOWLEDGE",
                source="knowledge_base",
                tool="search_knowledge",
                fetched_at="2026-09-26T00:00:00Z",
                payload={
                    "hits": [
                        {
                            "doc_id": doc_id,
                            "section": section,
                            "snippet": "API RP 11S section 5.4 covers gas lock mitigation procedures.",
                        }
                    ]
                },
            )
        ],
    )


def test_verification_steps_with_valid_citation_passes():
    """A verification step with a valid cited document and section in pack passes."""
    pack = _make_test_pack(doc_id="API_RP_11S", section="5.4")
    advisory = Advisory(
        objective_id="OP03_FAULT_DIAGNOSIS",
        assessment="Gas lock detected.",
        hypotheses=[],
        recommendation="Follow SOP.",
        troubleshooting_steps=["[API_RP_11S §5.4] Check intake pressure."],
        verification_steps=["[API_RP_11S §5.4] Verify fluid level recovery."],
        cited_evidence_ids=["EV-KB-001"],
    )

    res = check_citation_provenance(advisory, pack)
    assert res.passed
    assert len(res.unverified_citations) == 0
    assert len(res.flagged_steps) == 0
    assert len(res.flagged_verification_steps) == 0


def test_verification_steps_with_uncited_step_fails_and_flags():
    """An uncited verification step is flagged in flagged_verification_steps."""
    pack = _make_test_pack(doc_id="API_RP_11S", section="5.4")
    advisory = Advisory(
        objective_id="OP03_FAULT_DIAGNOSIS",
        assessment="Gas lock detected.",
        hypotheses=[],
        recommendation="Follow SOP.",
        troubleshooting_steps=["[API_RP_11S §5.4] Check intake pressure."],
        verification_steps=["Verify fluid level recovery manually without standard reference."],
        cited_evidence_ids=["EV-KB-001"],
    )

    res = check_citation_provenance(advisory, pack)
    assert not res.passed
    assert len(res.flagged_steps) == 0
    assert len(res.flagged_verification_steps) == 1
    assert "Verify fluid level recovery" in res.flagged_verification_steps[0]


def test_troubleshooting_empty_verification_uncited_flags_only_verification():
    """When troubleshooting_steps is empty but verification_steps is uncited, verification is flagged."""
    pack = _make_test_pack(doc_id="API_RP_11S", section="5.4")
    advisory = Advisory(
        objective_id="OP03_FAULT_DIAGNOSIS",
        assessment="Gas lock detected.",
        hypotheses=[],
        recommendation="Follow SOP.",
        troubleshooting_steps=[],
        verification_steps=["Step without citation."],
        cited_evidence_ids=["EV-KB-001"],
    )

    res = check_citation_provenance(advisory, pack)
    assert not res.passed
    assert len(res.flagged_steps) == 0
    assert len(res.flagged_verification_steps) == 1


def test_both_fields_uncited_flagged_independently():
    """When both fields have uncited steps, both are flagged independently."""
    pack = _make_test_pack(doc_id="API_RP_11S", section="5.4")
    advisory = Advisory(
        objective_id="OP03_FAULT_DIAGNOSIS",
        assessment="Gas lock detected.",
        hypotheses=[],
        recommendation="Follow SOP.",
        troubleshooting_steps=["Troubleshoot without doc."],
        verification_steps=["Verify without doc."],
        cited_evidence_ids=["EV-KB-001"],
    )

    res = check_citation_provenance(advisory, pack)
    assert not res.passed
    assert len(res.flagged_steps) == 1
    assert len(res.flagged_verification_steps) == 1
    assert "Troubleshoot without doc" in res.flagged_steps[0]
    assert "Verify without doc" in res.flagged_verification_steps[0]


def test_section_not_in_pack_fails():
    """Citing a section not present in pack document fails."""
    pack = _make_test_pack(doc_id="API_RP_11S", section="5.4")
    advisory = Advisory(
        objective_id="OP03_FAULT_DIAGNOSIS",
        assessment="Gas lock detected.",
        hypotheses=[],
        recommendation="Follow SOP.",
        troubleshooting_steps=["[API_RP_11S §9.9] Check intake pressure."],
        verification_steps=[],
        cited_evidence_ids=["EV-KB-001"],
    )

    res = check_citation_provenance(advisory, pack)
    assert not res.passed
    assert len(res.flagged_steps) == 1
    assert any("section not in pack" in unv for unv in res.unverified_citations)
