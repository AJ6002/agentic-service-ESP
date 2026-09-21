"""
Evidence Pack builder — Step 1.2.
Assembles a versioned EvidencePack from accepted QoDResults and FAILED/TIMEOUT
CallResults (which become Gaps), then persists it to Redis.
Reference: SLICE_2_PLAN.md §1.2, contracts/evidence.py.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Sequence

from app.contracts.evidence import (
    CallResult,
    Conflict,
    EvidencePack,
    Gap,
    QoDResult,
)
from app.stores.run_store import save_pack

# Tools whose CallResult failure produces a required Gap vs optional Gap.
# Populated from the objective YAMLs; callers pass required_tools explicitly.

# Error codes that mean "this source structurally cannot serve this request"
# (as opposed to "the source exists but is impaired right now").
#   ABSENT          — no endpoint exists at all (e.g. Knowledge Base)
#   WELL_NOT_FOUND  — the asset is unknown to this domain; it will never answer
#   UNKNOWN_TOOL    — no adapter wired for this tool
#   COVERAGE_EXCEEDED — requested window exceeds Historian historical coverage
#   WINDOW_TOO_LARGE  — requested window exceeds 30-day API limit
_ABSENT_CODES = {
    "ABSENT",
    "WELL_NOT_FOUND",
    "UNKNOWN_TOOL",
    "CARD_NOT_FOUND",
    "PLOT_NOT_FOUND",
    "COVERAGE_EXCEEDED",
    "WINDOW_TOO_LARGE",
}


def classify_gap_reason(call: CallResult) -> str:
    """
    Maps a failed CallResult onto a Gap.reason, using the structured
    error_code carried through from the adapter (spec §6 error envelope).

    Before error_code existed on CallResult, every non-timeout failure was
    flattened to DEGRADED and ABSENT was unreachable — meaning a genuinely
    missing source (KB) looked identical to a temporarily impaired one
    (MQTT down). This function is what restores that distinction.

    DEGRADED covers the impaired-but-real cases: MQTT_DISCONNECTED (503),
    NO_DATA / NO_LIVE_DATA (404 but the domain does serve this asset),
    unreachable host, unexpected errors.
    """
    if call.status == "TIMEOUT" or call.error_code == "TIMEOUT":
        return "TIMEOUT"
    if call.error_code in _ABSENT_CODES:
        return "ABSENT"
    return "DEGRADED"


def build_and_save(
    run_id: str,
    version: int,
    qod_results: Sequence[QoDResult],
    call_results: Sequence[CallResult],
    tool_names: Sequence[str],       # same length as qod_results / call_results
    required_tools: Sequence[str],   # from objective required_evidence
) -> EvidencePack:
    """
    Builds an EvidencePack from QoD-validated results and saves it to Redis.

    Args:
        run_id:        Workflow run identifier.
        version:       Pack version number (increment on re-fetch).
        qod_results:   QoDResult per tool call (accepted or rejected).
        call_results:  Corresponding raw CallResult (for status / error access).
        tool_names:    Tool name per entry (parallel to the above two).
        required_tools: Tool names that are required by the objective.

    Returns:
        The sealed-ready EvidencePack (sealed=False; seal_check() sets it).
    """
    required_set = set(required_tools)
    items = []
    gaps = []

    for qod, call, tool in zip(qod_results, call_results, tool_names):
        if qod.accepted and qod.evidence_item is not None:
            items.append(qod.evidence_item)
        else:
            gaps.append(
                Gap(
                    source_domain=tool,
                    reason=classify_gap_reason(call),
                    required=tool in required_set,
                )
            )

    # Conflict detection: cross-signal sanity between telemetry and events.
    # Slice 2 detects one concrete conflict pattern: VFD_STS=running but
    # a recent TRIP event exists — a real contradiction.
    conflicts = _detect_conflicts(items)

    pack = EvidencePack(
        run_id=run_id,
        version=version,
        items=items,
        gaps=gaps,
        conflicts=conflicts,
    )

    save_pack(run_id, version, pack.model_dump(mode="json"), ttl_sec=86400)
    return pack


def _detect_conflicts(items) -> list[Conflict]:
    """
    Detects cross-signal contradictions in the assembled evidence.
    Currently checks: vfd_sts=running (1) while a TRIP event exists.
    """
    conflicts: list[Conflict] = []
    telemetry_item = None
    events_item = None

    for item in items:
        if item.tool == "get_live_telemetry":
            telemetry_item = item
        if item.tool in ("get_events", "get_trips"):
            events_item = item

    if telemetry_item and events_item:
        measurements = telemetry_item.payload.get("measurements", {})
        # Accept both SCADA and canonical key
        vfd = measurements.get("STD_VFD_STS") or measurements.get("vfd_sts")
        trip_events = events_item.payload.get("trips") or events_item.payload.get("events", [])
        if vfd and trip_events:
            conflicts.append(
                Conflict(
                    description=(
                        "VFD status indicates running but trip events are present"
                    ),
                    evidence_ids=[
                        telemetry_item.evidence_id,
                        events_item.evidence_id,
                    ],
                )
            )

    return conflicts
