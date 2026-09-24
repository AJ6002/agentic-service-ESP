"""
Citation Provenance Check — Phase 4.5.
Validates that every troubleshooting step cites an approved KB document ID
that exists in the sealed EvidencePack.
Sibling to numeric_check.py.
"""

from __future__ import annotations

import re
from typing import Set, Tuple
from pydantic import BaseModel, Field

from app.contracts.advisory import Advisory
from app.contracts.evidence import EvidencePack


class CitationCheckResult(BaseModel):
    passed: bool
    unverified_citations: list[str] = Field(default_factory=list)
    verified_citations: list[str] = Field(default_factory=list)
    flagged_steps: list[str] = Field(default_factory=list)


# Matches inline citations like:
# [API_RP_11S §5.4] or [API_RP_11S (LEVEL_A) §3.1] or [Takacs_ESP_Manual_2nd_Ed §4.2]
_CITATION_REGEX = re.compile(
    r"\[([A-Za-z0-9_\-\.\+]+)(?:\s*\([A-Za-z0-9_\s]+\))?(?:\s*§?[A-Za-z0-9_\.\-\s]+)?\]"
)


def _canonicalize_doc_id(doc_id: str) -> str:
    """Normalizes document ID for robust matching (e.g. API-RP-11S -> API_RP_11S)."""
    return re.sub(r"[^A-Za-z0-9]", "", doc_id).upper()


def extract_pack_doc_ids(pack: EvidencePack) -> Set[str]:
    """Extracts all document IDs present in the sealed pack's KB evidence items."""
    doc_ids: Set[str] = set()
    for item in pack.items:
        payload = item.payload
        if not isinstance(payload, dict):
            continue
        # 1. search_knowledge hits
        hits = payload.get("hits", [])
        if isinstance(hits, list):
            for h in hits:
                if isinstance(h, dict) and h.get("doc_id"):
                    doc_ids.add(str(h["doc_id"]))
        # 2. get_fault_taxonomy
        if payload.get("applicable_manual"):
            doc_ids.add(str(payload["applicable_manual"]))
        if payload.get("fault_id"):
            doc_ids.add(str(payload["fault_id"]))
        # 3. trace_causal_graph
        paths = payload.get("paths", [])
        if isinstance(paths, list):
            for p in paths:
                if isinstance(p, dict):
                    sop = p.get("recommended_sop", {})
                    if sop.get("standard_ref"):
                        std_ref = str(sop["standard_ref"])
                        doc_ids.add(std_ref)
                        if "Section" in std_ref:
                            doc_ids.add(std_ref.split("Section")[0].strip())
                        if "+" in std_ref:
                            for part in std_ref.split("+"):
                                doc_ids.add(part.strip())
                    if sop.get("sop_id"):
                        doc_ids.add(str(sop["sop_id"]))
    return doc_ids


def check_citation_provenance(advisory: Advisory, pack: EvidencePack) -> CitationCheckResult:
    """
    Verifies that every troubleshooting step in advisory cites a doc_id that exists in pack.
    """
    if not advisory.troubleshooting_steps:
        return CitationCheckResult(passed=True)

    pack_doc_ids = extract_pack_doc_ids(pack)
    pack_canonical = {_canonicalize_doc_id(d) for d in pack_doc_ids if d}

    unverified = []
    verified = []
    flagged_steps = []

    for step in advisory.troubleshooting_steps:
        matches = _CITATION_REGEX.findall(step)
        if not matches:
            unverified.append(f"Missing citation in step: {step[:60]}...")
            flagged_steps.append(step)
            continue

        step_has_valid_citation = False
        for raw_citation in matches:
            clean_citation = raw_citation.strip()
            canon_cite = _canonicalize_doc_id(clean_citation)
            # Check direct or prefix/suffix containment
            if any(canon_cite in p_canon or p_canon in canon_cite for p_canon in pack_canonical):
                verified.append(clean_citation)
                step_has_valid_citation = True
            else:
                unverified.append(clean_citation)

        if not step_has_valid_citation:
            flagged_steps.append(step)

    passed = len(unverified) == 0
    return CitationCheckResult(
        passed=passed,
        unverified_citations=unverified,
        verified_citations=verified,
        flagged_steps=flagged_steps,
    )
