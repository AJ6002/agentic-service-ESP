"""
Gap-Fill (Slice 2.5) — one bounded retry for missing required evidence.

Called by runner.py when Seal Check returns INSUFFICIENT and the
objective manifest has max_gapfill_rounds >= 1.

Pipeline position:
    Pack v1 -> Seal Check (INSUFFICIENT) -> run_gapfill() -> Pack v2 -> Seal Check v2

Design constraints (karpathy rules):
  - No loops. Called once. Cap enforced structurally by the caller.
  - Re-uses unchanged v1 items by evidence_id (no re-dispatch).
  - Delta plan bypasses Policy Gate (already approved via original plan).
  - build_and_save() called with version=2 so the pack is distinguishable.
  - ABSENT gaps are NOT retried (WELL_NOT_FOUND, unknown tool, etc. are permanent).
    Only DEGRADED/TIMEOUT gaps are transient and worth one retry.
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from app.contracts.evidence import EvidencePack, SealResult
from app.contracts.plan import PlanArtifact, PlanCall
from app.contracts.objective_manifest import ObjectiveManifest
from app.evidence.pack import build_and_save
from app.evidence.qod import validate
from app.evidence.seal_check import seal
from app.gateway.tool_gateway import dispatch_plan_calls
from app.llm.calls import gapfill

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

# Gap reasons that are permanent — retrying them wastes a round and still fails.
# ABSENT means the source structurally cannot serve this asset/tool.
_PERMANENT_GAP_REASONS = {"ABSENT"}


async def run_gapfill(
    run_id: str,
    seal_res: SealResult,
    plan: PlanArtifact,
    manifest: ObjectiveManifest,
    existing_pack: EvidencePack,
) -> tuple[EvidencePack, SealResult]:
    """
    Attempt one gap-fill retry for missing required tools.

    Returns (pack_v2, new_seal_result).
    If gap-fill itself fails entirely (e.g. all retries still DEGRADED),
    new_seal_result.status will be 'INSUFFICIENT' and the caller's honest
    refusal path fires normally — no exception is raised here.

    Tools with Gap.reason == ABSENT are skipped (permanent failures like
    WELL_NOT_FOUND are not worth retrying — they will always fail again).
    """
    # Build the set of permanently-absent tool names from v1 gaps.
    permanent_absent = {
        g.source_domain
        for g in existing_pack.gaps
        if g.reason in _PERMANENT_GAP_REASONS
    }

    # Filter missing_required to only transient failures worth retrying.
    retryable_missing = [
        t for t in seal_res.missing_required
        if t not in permanent_absent
    ]

    # 1. Determine which tools to retry (deterministic passthrough for Slice 2.5)
    candidate_tools = manifest.required_evidence
    tools_to_retry = await gapfill(
        missing_tools=retryable_missing,
        candidate_tools=candidate_tools,
    )

    logger.info(
        "gap_fill_attempt",
        extra={
            "run_id": run_id,
            "round": 1,
            "tools": tools_to_retry,
            "missing_required": seal_res.missing_required,
            "skipped_permanent": list(permanent_absent),
        },
    )

    if not tools_to_retry:
        # Nothing retryable (all missing tools are permanently absent, e.g. WELL_NOT_FOUND).
        # Return the original pack and seal result unchanged — caller will refuse.
        logger.info("gap_fill_no_retryable_tools run_id=%s", run_id)
        return existing_pack, seal_res

    # 2. Build a delta PlanArtifact with only the retryable READ calls.
    delta_calls: list[PlanCall] = []
    for seq, tool_name in enumerate(tools_to_retry, start=1):
        delta_calls.append(
            PlanCall(
                seq=seq,
                kind="READ",
                tool=tool_name,
                args=plan.args,
                status="PENDING",
            )
        )

    delta_plan = PlanArtifact(
        run_id=run_id,
        session_id=plan.session_id,
        objective_id=plan.objective_id,
        args=plan.args,
        confidence=plan.confidence,
        calls=delta_calls,
        requires_approval=False,  # subset of already-approved plan
    )

    # 3. Dispatch only the delta calls (no Policy Gate — already approved).
    delta_results = await dispatch_plan_calls(delta_plan)

    # 4. QoD-validate each delta result.
    delta_qod = []
    delta_tool_names = []
    for call, cr in zip(delta_calls, delta_results):
        qod = validate(cr, run_id=run_id, tool=call.tool)
        delta_qod.append(qod)
        delta_tool_names.append(call.tool)

    # 5. Merge: start from v1 items, replace/add delta items for retried tools.
    #    Items from v1 that were already OK are preserved by identity — no re-dispatch.
    retried_tool_set = set(tools_to_retry)
    # Keep all v1 items that were NOT in the retry set (they were already OK).
    kept_items = [item for item in existing_pack.items if item.tool not in retried_tool_set]
    kept_gaps  = [gap  for gap  in existing_pack.gaps  if gap.source_domain not in retried_tool_set]

    # Build delta portion via standard builder so evidence_ids are stable.
    delta_pack = build_and_save(
        run_id=run_id,
        version=2,
        qod_results=delta_qod,
        call_results=delta_results,
        tool_names=delta_tool_names,
        required_tools=manifest.required_evidence,
    )

    # Merge: v2 items = kept v1 items + new delta items.
    merged_items = kept_items + delta_pack.items
    merged_gaps  = kept_gaps  + delta_pack.gaps
    merged_conflicts = existing_pack.conflicts + delta_pack.conflicts

    pack_v2 = EvidencePack(
        run_id=run_id,
        version=2,
        items=merged_items,
        gaps=merged_gaps,
        conflicts=merged_conflicts,
    )

    # 6. Re-seal Pack v2.
    new_seal = seal(pack_v2, required_tools=manifest.required_evidence)

    logger.info(
        "gap_fill_result",
        extra={
            "run_id": run_id,
            "round": 1,
            "pack_version": 2,
            "seal_status": new_seal.status,
            "still_missing": new_seal.missing_required,
        },
    )

    return pack_v2, new_seal
