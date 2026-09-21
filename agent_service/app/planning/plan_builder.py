from typing import Any
from app.contracts.objective_manifest import ObjectiveManifest
from app.contracts.plan import PlanArtifact, PlanCall
from app.contracts.routing import RouteDecision

def build_plan(
    run_id: str,
    session_id: str,
    decision: RouteDecision,
    manifest: ObjectiveManifest,
) -> PlanArtifact:
    """
    Deterministic plan builder from manifest + bound args.
    Pure function: no LLM, no network.
    """
    calls: list[PlanCall] = []
    seq = 1

    # 1. Evidence gathering READ calls from required_evidence
    for tool_name in manifest.required_evidence:
        calls.append(
            PlanCall(
                seq=seq,
                kind="READ",
                tool=tool_name,
                args=decision.args,
                status="PENDING",
            )
        )
        seq += 1

    # 1.5 Optional evidence — best-effort READ calls. A failure here never
    # blocks Seal Check (seal() only checks required_tools), so these are
    # safe to always attempt: if the source is ABSENT/DEGRADED it just
    # becomes a Gap(required=False). Before this, optional_evidence was
    # declared in every objective YAML but never turned into a call at
    # all — e.g. OP03's `search_knowledge` was silently never fetched,
    # regardless of whether a KB service existed.
    for tool_name in manifest.optional_evidence:
        calls.append(
            PlanCall(
                seq=seq,
                kind="READ",
                tool=tool_name,
                args=decision.args,
                status="PENDING",
            )
        )
        seq += 1

    # 2. Main objective execution call (avoid redundant duplicate if already in required/optional)
    main_kind = "WRITE" if manifest.safety_class == "WRITE" else "READ"
    if not any(c.tool == manifest.tool for c in calls):
        calls.append(
            PlanCall(
                seq=seq,
                kind=main_kind,
                tool=manifest.tool,
                args=decision.args,
                status="PENDING",
            )
        )

    # requires_approval is true iff any call.kind == WRITE
    requires_approval = any(c.kind == "WRITE" for c in calls)

    return PlanArtifact(
        run_id=run_id,
        session_id=session_id,
        objective_id=manifest.objective_id,
        args=decision.args,
        confidence=decision.confidence,
        calls=calls,
        requires_approval=requires_approval,
    )
