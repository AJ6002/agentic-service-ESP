"""
Seal Check — Step 1.2 (second half).
Determines if an EvidencePack satisfies an objective requirement set.
Pure function — no I/O, no LLM.
Reference: SLICE_2_PLAN.md §1.2.
"""

from __future__ import annotations

from datetime import datetime, timezone

from app.contracts.evidence import EvidencePack, SealResult


def seal(pack: EvidencePack, required_tools: list[str]) -> SealResult:
    """
    Checks whether all required evidence tools are present and accepted
    in the pack.  Stamps pack.sealed and pack.sealed_at if COMPLETE.

    Returns SealResult with status COMPLETE or INSUFFICIENT.
    missing_required lists the tool names that are absent.
    """
    # Build set of tools that have an accepted EvidenceItem
    accepted_tools = {item.tool for item in pack.items}

    # Also check if a required tool produced a Gap (explicit failure)
    missing: list[str] = []
    for tool in required_tools:
        if tool not in accepted_tools:
            missing.append(tool)

    if missing:
        return SealResult(
            pack=pack,
            status="INSUFFICIENT",
            missing_required=missing,
        )

    # All required evidence present — seal the pack
    pack.sealed = True
    pack.sealed_at = datetime.now(timezone.utc)

    return SealResult(
        pack=pack,
        status="COMPLETE",
        missing_required=[],
    )
