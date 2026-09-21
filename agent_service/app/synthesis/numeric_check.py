"""
Numeric Provenance Check - Step 2.2.
Consumes: Advisory + EvidencePack (or FormattedEvidence).
Produces: ProvenanceResult(passed: bool, unattributed_numbers: list[str]).

Explicit ignore rules (documented, not silent per SLICE_2_PLAN SS2.2):
  - Dates (e.g. 2026-09-17) and timestamps (14:18:00).
  - Numbered list prefixes (e.g. "1. ", "2) ").
  - Evidence IDs (e.g. EV-run-001-0001).
  - Well IDs (e.g. FS-17, FNW-01, ULFA-5, FSWS-001-A) — the numeric suffix
    is an identifier, not a measured value. Without this, an advisory that
    mentions the well by name (which every advisory does) always trips a
    false-positive unattributed-number flag on its own well ID's digits.
  - Small safe integers 0-10, 100 (scale values, step counts).
  - Numbers directly attached to unit letters are pre-normalised with a
    space before extraction (e.g. "412.7PSI" -> "412.7 PSI") so the
    negative lookahead in _NUMERIC_TOKEN_REGEX fires correctly.
  - Comma-separated thousands (e.g. "1,883.1") are normalised to their
    plain form ("1883.1") before comparison, preventing false positives.

Reference: SLICE_2_PLAN.md SS2.2.
"""

from __future__ import annotations

import re
from typing import Set, Union
from app.contracts.advisory import Advisory, ProvenanceResult
from app.contracts.evidence import EvidencePack
from app.evidence.formatter import FormattedEvidence, format_pack


# Matches integers or floats NOT part of an identifier.
# Callers must normalise unit-attached strings and comma-thousands BEFORE
# calling findall - see _normalise_text().
_NUMERIC_TOKEN_REGEX = re.compile(r"(?<![A-Za-z0-9_])(\d+(?:\.\d+)?)(?![A-Za-z0-9_])")

# Well IDs (e.g. "FS-17", "FNW-01", "ULFA-5", "FSWS-001-A") — same pattern
# family as app.context.resolver.WELL_ID_REGEX, duplicated here (not
# imported) to keep this module's only dependency direction on
# app.context flowing the other way already; small, stable regex, low
# duplication risk.
_WELL_ID_REGEX = re.compile(r"\b(?:FSWS-\d+-[A-Za-z0-9]+|FNW-\d+|FWS-\d+|ULFA-\d+|FS-\d+)\b", re.IGNORECASE)

# Standard prose integers to ignore: enumeration indexes, boolean flags,
# percentage scale endpoints. Must be explicit and documented (Rule C).
_IGNORED_NUMBERS = {"0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "100"}


def _normalise_text(text: str) -> str:
    """
    Two-step canonical normalisation applied to BOTH advisory prose and
    evidence value_str before any numeric extraction.

    Step 1 - Comma-separated thousands:
        "1,883.1 PSI" -> "1883.1 PSI"
        Only commas between digit groups are removed; prose commas are safe.

    Step 2 - Unit-attached numbers:
        "412.7PSI" -> "412.7 PSI"
        "53.1Hz"   -> "53.1 Hz"
        Inserts a space between a digit and an immediately following ASCII
        letter so the lookahead in _NUMERIC_TOKEN_REGEX fires correctly.
        Excludes E/e when used as a scientific-notation exponent (e.g. 1.2e5).
    """
    # Step 1: strip thousands-separator commas (loop handles multi-group).
    prev = None
    while prev != text:
        prev = text
        text = re.sub(r"(\d),(\d{3})(?!\d)", r"\1\2", text)

    # Step 2: digit immediately followed by ASCII letter that is NOT part
    # of scientific notation (E/e followed by optional sign and digits).
    text = re.sub(r"(\d)([A-DF-Za-df-z])", r"\1 \2", text)       # all letters except E/e
    text = re.sub(r"(\d)([Ee])(?![+\-]?\d)", r"\1 \2", text)     # E/e only if not sci-notation

    return text


def _clean_text_for_provenance(text: str) -> str:
    """
    Strips noise tokens to prevent false-positive unattributed numbers.
    Applied AFTER _normalise_text.

    Noise removed (each documented, not silent per SLICE_2_PLAN SS2.2):
      1. Evidence IDs: EV-run-123-0001
      2. ISO dates:    2026-09-17 or 2026/09/17
      3. Timestamps:   12:34 or 12:34:56
      4. Numbered list prefixes: "1. step", "2) do"
      5. Well IDs:     FS-17, FNW-01, ULFA-5, FSWS-001-A
    """
    text = re.sub(r"EV-[\w\-]+", " ", text)
    text = _WELL_ID_REGEX.sub(" ", text)
    text = re.sub(r"\b\d{4}[-/]\d{2}[-/]\d{2}\b", " ", text)
    text = re.sub(r"\b\d{1,2}:\d{2}(?::\d{2})?\b", " ", text)
    text = re.sub(r"\b\d+\s*(?:minutes?|hours?|days?|seconds?|mins?|secs?)\b", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"(?:^|\n)\s*\d+[\.)] ?", " ", text)
    return text


def _extract_pack_numbers(source: Union[EvidencePack, FormattedEvidence]) -> Set[float]:
    """
    Gathers all numbers present in verified evidence at multiple rounding
    levels (raw, 1dp, 2dp) for tolerant matching against LLM output.
    """
    if isinstance(source, EvidencePack):
        fe = format_pack(source)
    else:
        fe = source

    numbers: Set[float] = set()
    for fv in fe.values:
        if fv.raw is not None and isinstance(fv.raw, (int, float)) and not isinstance(fv.raw, bool):
            v = float(fv.raw)
            numbers.update({v, round(v, 1), round(v, 2)})

        # Extract from value_str using same normalisation so "87.71 degC" works too.
        norm_str = _normalise_text(fv.value_str)
        for token in _NUMERIC_TOKEN_REGEX.findall(norm_str):
            try:
                v = float(token)
                numbers.update({v, round(v, 1), round(v, 2)})
            except ValueError:
                pass

    return numbers


def check_numeric_provenance(
    advisory: Advisory,
    evidence_source: Union[EvidencePack, FormattedEvidence],
) -> ProvenanceResult:
    """
    Extracts numbers from advisory prose (assessment, hypotheses,
    recommendation, verification_steps) and checks every non-ignored number
    is grounded in evidence_source.

    Flag-and-show per SLICE_2_PLAN SS2.2 decision 3: unverified numbers are
    listed in ProvenanceResult.unattributed_numbers; no auto-regeneration.
    """
    valid_numbers = _extract_pack_numbers(evidence_source)

    text_blocks = [advisory.assessment, advisory.recommendation]
    text_blocks.extend(advisory.hypotheses)
    text_blocks.extend(advisory.verification_steps)

    full_text = " \n ".join(text_blocks)

    # Normalise first (comma-thousands, unit-attachment), then strip noise
    normalised = _normalise_text(full_text)
    cleaned = _clean_text_for_provenance(normalised)

    unattributed: list[str] = []
    seen: Set[str] = set()

    for token in _NUMERIC_TOKEN_REGEX.findall(cleaned):
        if token in _IGNORED_NUMBERS:
            continue
        try:
            val = float(token)
            if (
                val not in valid_numbers
                and round(val, 1) not in valid_numbers
                and round(val, 2) not in valid_numbers
            ):
                if token not in seen:
                    seen.add(token)
                    unattributed.append(token)
        except ValueError:
            continue

    return ProvenanceResult(passed=len(unattributed) == 0, unattributed_numbers=unattributed)
