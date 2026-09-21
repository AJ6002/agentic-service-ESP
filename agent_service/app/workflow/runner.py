"""
Full Slice 2 Workflow Execution Runner.
Wires:
Plan Builder -> Policy Gate -> Tool Gateway -> QoD -> Evidence Pack -> Seal Check -> Formatted Evidence -> XAI Synthesizer -> Numeric Provenance -> Visualization Planner.
Zero fake numbers. Complete provenance and status surfacing.
Reference: SLICE_2_PLAN.md §3.2.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from app.contracts.advisory import Advisory, ProvenanceResult
from app.contracts.evidence import CallResult, EvidencePack, SealResult
from app.contracts.plan import PlanArtifact
from app.contracts.routing import RouteDecision
from app.contracts.visualization import VisualizationSpec
from app.evidence.formatter import format_pack, FormattedEvidence
from app.evidence.pack import build_and_save
from app.evidence.qod import validate
from app.evidence.seal_check import seal
from app.gateway.tool_gateway import dispatch_plan_calls
from app.llm.client import LLMUnavailableError
from app.planning.plan_builder import build_plan
from app.policy.policy_gate import validate_plan
from app.routing.objective_registry import get_objective
from app.synthesis.kpi_alarm_check import KpiAlarmResult
from app.synthesis.numeric_check import check_numeric_provenance
from app.synthesis.gapfill import run_gapfill
from app.synthesis.xai import synthesize_advisory
from app.visualization.planner import plan_visualization


# Phrases that indicate a "healthy/normal" assessment — used by the post-synthesis
# alarm guard. If CRITICAL KPI alarms are active and the LLM assessment contains
# any of these, the assessment is silently replaced with the alarm summary.
_NORMAL_PHRASES = (
    "functioning as expected",
    "operating within normal",
    "within acceptable ranges",
    "operating normally",
    "no issues detected",
    "no anomalies detected",
    "all measurements are within",
    "performing normally",
)


@dataclass
class WorkflowResult:
    text: str
    ok: bool
    plan: PlanArtifact | None = None
    call_results: list[CallResult] = field(default_factory=list)
    violations: list[str] = field(default_factory=list)
    pack: EvidencePack | None = None
    seal_result: SealResult | None = None
    advisory: Advisory | None = None
    provenance: ProvenanceResult | None = None
    visualization: VisualizationSpec | None = None
    insufficient_evidence: bool = False
    missing_required: list[str] = field(default_factory=list)


def _format_advisory_text(
    objective_id: str,
    args: dict,
    advisory: Optional[Advisory],
    pack: Optional[EvidencePack],
    provenance: Optional[ProvenanceResult],
    results: list[CallResult],
) -> str:
    """
    Renders human-readable text for WorkflowResult.text.
    Includes Advisory findings if available, provenance warnings, and data source statuses.
    Preserves backwards compatibility for assertions expecting 'Diagnostic run for ...'.
    """
    asset_id = args.get("asset_id", "the selected asset")
    lines = [f"Diagnostic run for {asset_id} (objective: {objective_id}):"]
    if pack:
        for item in pack.items:
            tm = item.payload.get("temporal_meta") if isinstance(item.payload, dict) else None
            if tm and isinstance(tm, dict) and tm.get("query_window", {}).get("start"):
                qw = tm["query_window"]
                db = tm.get("data_bounds", {})
                span_desc = f" ({qw.get('span_seconds')}s span)" if qw.get('span_seconds') else ""
                lines.append(f"\nTemporal Scope: {qw.get('start')} to {qw.get('end')}{span_desc}")
                if db.get("earliest_ts"):
                    lines.append(f"Data Found: {db.get('point_count')} records ({db.get('earliest_ts')} to {db.get('latest_ts')})")
                break

    if advisory:
        lines.append(f"\nAssessment: {advisory.assessment}")
        if advisory.hypotheses:
            lines.append("\nHypotheses:")
            for h in advisory.hypotheses:
                lines.append(f" - {h}")
        lines.append(f"\nRecommendation: {advisory.recommendation}")
        if advisory.verification_steps:
            lines.append("\nVerification Steps:")
            for s in advisory.verification_steps:
                lines.append(f" - {s}")
        if advisory.cited_evidence_ids:
            lines.append(f"\nCited Evidence: {', '.join(advisory.cited_evidence_ids)}")

    if provenance and not provenance.passed:
        lines.append(f"\n[WARNING: Numeric Provenance Unverified for: {', '.join(provenance.unattributed_numbers)}]")

    if pack and pack.gaps:
        lines.append(f"\nData source status notes:")
        for g in pack.gaps:
            req_str = " (Required)" if g.required else " (Optional)"
            lines.append(f" - {g.source_domain}: {g.reason}{req_str}")

    return "\n".join(lines).strip()


async def run_workflow(
    run_id: str,
    session_id: str,
    objective_id: str,
    args: dict,
    confidence: float = 0.9,
    user_query: str = "",
) -> WorkflowResult:
    """
    Executes end-to-end Slice 2 workflow pipeline.
    """
    manifest = get_objective(objective_id)
    if manifest is None:
        return WorkflowResult(
            text=f"Unknown objective '{objective_id}' — cannot run diagnosis.",
            ok=False,
            violations=[f"unknown_objective:{objective_id}"],
        )

    decision = RouteDecision(
        route="WORKFLOW",
        objective_id=objective_id,
        args=args,
        confidence=confidence,
    )
    plan = build_plan(run_id=run_id, session_id=session_id, decision=decision, manifest=manifest)

    # 1. Policy Gate
    policy_result = validate_plan(plan)
    if not policy_result.approved:
        return WorkflowResult(
            text="I can't run this diagnosis yet — " + "; ".join(policy_result.violations),
            ok=False,
            plan=plan,
            violations=policy_result.violations,
        )

    # 2. Tool Gateway dispatch
    results = await dispatch_plan_calls(plan)

    # 3. QoD per CallResult
    qod_results = []
    tool_names = []
    read_calls = [c for c in plan.calls if c.kind == "READ"]
    for call, cr in zip(read_calls, results):
        qod = validate(cr, run_id=run_id, tool=call.tool)
        qod_results.append(qod)
        tool_names.append(call.tool)

    # 4. Evidence Pack build & save
    pack = build_and_save(
        run_id=run_id,
        version=1,
        qod_results=qod_results,
        call_results=results,
        tool_names=tool_names,
        required_tools=manifest.required_evidence or [],
    )

    # 5. Seal Check
    seal_res = seal(pack, required_tools=manifest.required_evidence or [])
    allow_partial = bool(args.get("allow_partial", False))

    # 5a. Gap-Fill (one bounded round if objective opts in via max_gapfill_rounds >= 1)
    if seal_res.status == "INSUFFICIENT" and manifest.max_gapfill_rounds >= 1:
        pack, seal_res = await run_gapfill(
            run_id=run_id,
            seal_res=seal_res,
            plan=plan,
            manifest=manifest,
            existing_pack=pack,
        )
    if seal_res.status == "INSUFFICIENT" and not allow_partial:
        missing_text = ", ".join(seal_res.missing_required)
        status_notes = []
        if pack and pack.gaps:
            status_notes = [f"{g.source_domain}: {g.reason}" for g in pack.gaps]
        notes_str = f" Status notes: {'; '.join(status_notes)}." if status_notes else ""
        target = args.get('asset_id') or ('knowledge lookup' if 'OP06' in objective_id else 'well')
        text = f"Diagnostic run for {target} (objective: {objective_id}) could not be completed: required evidence missing ({missing_text}).{notes_str}"
        viz_spec = VisualizationSpec(widget_id="cards", card_ids=[], evidence_ids=[])
        return WorkflowResult(
            text=text,
            ok=False,
            plan=plan,
            call_results=results,
            pack=pack,
            seal_result=seal_res,
            visualization=viz_spec,
            insufficient_evidence=True,
            missing_required=seal_res.missing_required,
        )

    # 6. Formatted Evidence
    formatted_evidence = format_pack(pack)

    # 7. XAI Synthesizer (LLM #3)
    advisory: Optional[Advisory] = None
    alarm_result: Optional[KpiAlarmResult] = None
    try:
        advisory, alarm_result = await synthesize_advisory(
            objective_id=objective_id,
            evidence=formatted_evidence,
            user_query=user_query or f"Diagnose well {args.get('asset_id', '')}",
        )
    except (LLMUnavailableError, Exception):
        advisory = None
        alarm_result = None

    # 7a. Post-synthesis alarm override guard.
    # If CRITICAL KPI alarms are active but the LLM assessment still claims
    # the well is "normal", silently replace the assessment with the alarm
    # summary. This is a last-resort safety net — the injected evidence block
    # should prevent this from firing, but we cannot trust the LLM fully.
    if (
        advisory is not None
        and alarm_result is not None
        and alarm_result.has_critical
    ):
        assessment_lower = advisory.assessment.lower()
        if any(phrase in assessment_lower for phrase in _NORMAL_PHRASES):
            alarm_desc = alarm_result.alarm_summary().replace(
                "--- KPI ALARM PRE-CHECK (DETERMINISTIC) ---\n", ""
            ).split("\n\u26a0")[0].strip()  # take just the alarm lines
            advisory.assessment = (
                f"WARNING — Active KPI alarms detected: {alarm_desc} "
                f"The well is NOT in a normal operating state. "
                f"Original assessment: {advisory.assessment}"
            )
            record_audit("kpi_alarm_override", payload={
                "run_id": run_id,
                "asset_id": args.get("asset_id"),
                "alarms": [a.signal for a in alarm_result.alarms if a.severity == "CRITICAL"],
            })

    # 8. Numeric Provenance Check
    provenance: Optional[ProvenanceResult] = None
    if advisory:
        provenance = check_numeric_provenance(advisory, formatted_evidence)

    # 9. Visualization Planner
    viz_spec = plan_visualization(objective_id, pack, formatted_evidence)

    # 10. Assemble Text
    text = _format_advisory_text(objective_id, args, advisory, pack, provenance, results)

    return WorkflowResult(
        text=text,
        ok=True,
        plan=plan,
        call_results=results,
        pack=pack,
        seal_result=seal_res,
        advisory=advisory,
        provenance=provenance,
        visualization=viz_spec,
        insufficient_evidence=False if allow_partial else (seal_res.status == "INSUFFICIENT"),
        missing_required=seal_res.missing_required if seal_res.status == "INSUFFICIENT" else [],
    )

