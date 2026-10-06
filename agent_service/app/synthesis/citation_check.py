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
    flagged_verification_steps: list[str] = Field(default_factory=list)


# Matches inline citations including full manual titles:
# [API_RP_11S §5.4] or [API_RP_11S (LEVEL_A) §3.1] or [Takacs_ESP_Manual_2nd_Ed §4.2] or [Baker Hughes FusionPro Manual ...] or [DOC-804612320-Electric-Submersible-Pumps §Troubleshooting ESP]
_CITATION_REGEX = re.compile(
    r"\[\s*([^\]\n§]+?)(?:[\s,]+(?:§|Section\s*|sec\.?\s*)([^\]\n]+))?\s*\]",
    re.IGNORECASE,
)


_IGNORE_DOC_TOKENS = {"UNVERIFIED", "WARNING", "NOTE", "TIP", "CAUTION", "IMPORTANT", "LEVELA", "LEVELB"}


def _canonicalize_doc_id(doc_id: str) -> str:
    """Normalizes document ID for robust matching (e.g. API-RP-11S -> APIRP11S)."""
    return re.sub(r"[^A-Za-z0-9]", "", str(doc_id)).upper()


def extract_pack_citations(pack: EvidencePack) -> tuple[set[str], dict[str, set[str]]]:
    """
    Extracts all document IDs, titles, and associated section identifiers from the sealed pack.
    Returns:
      (all_doc_ids, doc_to_sections)
      - all_doc_ids: set of canonical doc strings and aliases
      - doc_to_sections: canonical doc_id -> set of normalized section strings/numbers/tokens
    """
    doc_ids: set[str] = set()
    doc_to_sections: dict[str, set[str]] = {}

    def _add_doc_sec(doc: str | None, sec: str | None = None, title: str | None = None):
        entries = [d for d in [doc, title] if d]
        for entry in entries:
            canon = _canonicalize_doc_id(str(entry))
            if not canon:
                continue
            doc_ids.add(canon)
            stripped = re.sub(r"^DOC[_\-]?", "", str(entry), flags=re.IGNORECASE)
            canon_stripped = _canonicalize_doc_id(stripped)
            if canon_stripped:
                doc_ids.add(canon_stripped)

            for key in (canon, canon_stripped):
                if key not in doc_to_sections:
                    doc_to_sections[key] = set()
                if sec:
                    for num in re.findall(r"\b\d+(?:\.\d+)*\b", str(sec)):
                        doc_to_sections[key].add(num)
                    clean_sec = _canonicalize_doc_id(str(sec))
                    if clean_sec:
                        doc_to_sections[key].add(clean_sec)
                    for word in re.findall(r"[A-Za-z0-9]{3,}", str(sec)):
                        doc_to_sections[key].add(_canonicalize_doc_id(word))

    for item in pack.items:
        payload = item.payload
        if not isinstance(payload, dict):
            continue
        # 1. search_knowledge hits
        hits = payload.get("hits", [])
        if isinstance(hits, list):
            for h in hits:
                if isinstance(h, dict):
                    _add_doc_sec(h.get("doc_id"), h.get("section"), h.get("doc_title"))
        # 2. get_fault_taxonomy
        if payload.get("applicable_manual"):
            _add_doc_sec(str(payload["applicable_manual"]))
        if payload.get("fault_id"):
            _add_doc_sec(str(payload["fault_id"]))
        # 3. trace_causal_graph
        paths = payload.get("paths", [])
        if isinstance(paths, list):
            for p in paths:
                if isinstance(p, dict):
                    sop = p.get("recommended_sop", {})
                    if sop.get("standard_ref"):
                        std_ref = str(sop["standard_ref"])
                        sec = None
                        if "Section" in std_ref:
                            parts = std_ref.split("Section")
                            std_ref = parts[0].strip()
                            sec = parts[1].strip()
                        if "+" in std_ref:
                            for part in std_ref.split("+"):
                                _add_doc_sec(part.strip(), sec)
                        else:
                            _add_doc_sec(std_ref, sec)
                    if sop.get("sop_id"):
                        _add_doc_sec(str(sop["sop_id"]))

    # Also incorporate formatted hits
    try:
        from app.evidence.formatter import format_pack
        fmt = format_pack(pack)
        for kh in getattr(fmt, "kb_hits", []):
            if kh.doc_id:
                _add_doc_sec(kh.doc_id, kh.section)
    except Exception:
        pass

    return doc_ids, doc_to_sections


def extract_pack_doc_ids(pack: EvidencePack) -> Set[str]:
    """Backwards compatibility helper: extracts all raw doc IDs from pack."""
    doc_ids, _ = extract_pack_citations(pack)
    return doc_ids


def _doc_matches_pack(canon_doc: str, raw_doc: str, pack_doc_ids: set[str]) -> list[str]:
    """Matches a cited document string against pack document IDs and titles."""
    if canon_doc in pack_doc_ids:
        return [canon_doc]
    matches = [p for p in pack_doc_ids if canon_doc in p or p in canon_doc]
    if matches:
        return matches
    words = [w.upper() for w in re.findall(r"[A-Za-z0-9]{4,}", raw_doc)]
    if words:
        overlap_matches = [p for p in pack_doc_ids if any(w in p for w in words)]
        if overlap_matches:
            return overlap_matches
    return []


def _validate_step_list(
    steps: list[str],
    pack_doc_ids: set[str],
    doc_to_sections: dict[str, set[str]],
    is_verification: bool = False,
) -> tuple[list[str], list[str], list[str]]:
    unverified: list[str] = []
    verified: list[str] = []
    flagged: list[str] = []

    for step in steps:
        matches = list(_CITATION_REGEX.finditer(step))
        filtered_matches = []
        for m in matches:
            raw = m.group(1).strip()
            if raw.startswith("EV-") or raw.isdigit():
                continue
            canon = _canonicalize_doc_id(raw)
            if not canon or canon in _IGNORE_DOC_TOKENS:
                continue
            filtered_matches.append(m)

        if not filtered_matches:
            unverified.append(f"Missing citation in step: {step[:60]}...")
            flagged.append(step)
            continue

        step_has_valid_citation = False
        for m in filtered_matches:
            raw_doc = m.group(1).strip()
            raw_sec = m.group(2).strip() if m.group(2) else None
            canon_doc = _canonicalize_doc_id(raw_doc)

            matching_docs = _doc_matches_pack(canon_doc, raw_doc, pack_doc_ids)
            if not matching_docs:
                cite_str = f"[{raw_doc} §{raw_sec}]" if raw_sec else f"[{raw_doc}]"
                unverified.append(f"{cite_str} (document not in pack)")
                continue

            # If a specific section was cited, verify it exists in at least one matching doc's section set
            if raw_sec:
                sec_found = False
                for matched_doc in matching_docs:
                    known_secs = doc_to_sections.get(matched_doc, set())
                    if not known_secs:
                        # If the pack doc had no specific sections indexed, doc match is accepted
                        sec_found = True
                        break
                    canon_sec = _canonicalize_doc_id(raw_sec)
                    if raw_sec in known_secs or canon_sec in known_secs or any(raw_sec in s or s in raw_sec for s in known_secs):
                        sec_found = True
                        break
                    sec_words = [w.upper() for w in re.findall(r"[A-Za-z0-9]{3,}", raw_sec)]
                    if any(any(sw in ks for ks in known_secs) for sw in sec_words):
                        sec_found = True
                        break
                if not sec_found:
                    cite_str = f"[{raw_doc} §{raw_sec}]"
                    unverified.append(f"{cite_str} (section not in pack)")
                    continue

            cite_str = f"[{raw_doc} §{raw_sec}]" if raw_sec else f"[{raw_doc}]"
            verified.append(cite_str)
            step_has_valid_citation = True

        if not step_has_valid_citation:
            flagged.append(step)

    return unverified, verified, flagged


def check_citation_provenance(advisory: Advisory, pack: EvidencePack) -> CitationCheckResult:
    """
    Verifies that every troubleshooting step in advisory cites a doc_id/title AND section
    that exists in the sealed EvidencePack, and validates operational verification steps.
    """
    has_tb = bool(advisory.troubleshooting_steps)
    has_ver = bool(advisory.verification_steps)
    if not has_tb and not has_ver:
        return CitationCheckResult(passed=True)

    pack_doc_ids, doc_to_sections = extract_pack_citations(pack)

    all_unverified: list[str] = []
    all_verified: list[str] = []
    flagged_tb: list[str] = []
    flagged_ver: list[str] = []

    if has_tb:
        unv, ver, flg = _validate_step_list(advisory.troubleshooting_steps, pack_doc_ids, doc_to_sections, is_verification=False)
        all_unverified.extend(unv)
        all_verified.extend(ver)
        flagged_tb.extend(flg)

    if has_ver:
        unv, ver, flg = _validate_step_list(advisory.verification_steps, pack_doc_ids, doc_to_sections, is_verification=True)
        all_unverified.extend(unv)
        all_verified.extend(ver)
        flagged_ver.extend(flg)

    passed = len(all_unverified) == 0
    return CitationCheckResult(
        passed=passed,
        unverified_citations=all_unverified,
        verified_citations=all_verified,
        flagged_steps=flagged_tb,
        flagged_verification_steps=flagged_ver,
    )
