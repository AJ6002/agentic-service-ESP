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

from app.audit.audit_sink import record_audit
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
from app.synthesis.citation_check import check_citation_provenance, CitationCheckResult
from app.synthesis.gapfill import run_gapfill
from app.synthesis.xai import synthesize_advisory
from app.visualization.planner import plan_visualization
from app.stores.run_store import save_pack, save_run_artifacts


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
    llm_available: bool = True


# ---------------------------------------------------------------------------
# Objective-to-header mapping — fixes the wrong "Diagnostic run" label (Bug #3)
# ---------------------------------------------------------------------------
_OBJECTIVE_HEADERS: dict[str, str] = {
    "OP01": "Status check for {asset}:",
    "OP02": "Production trend for {asset}:",
    "OP03": "Fault diagnosis for {asset}:",
    "OP04": "Health assessment for {asset}:",
    "OP05": "Early-warning assessment for {asset}:",
    "OP06": "Knowledge lookup:",
    "OP14": "Historical review for {asset}:",
}


def _objective_header(objective_id: str, asset_id: str) -> str:
    """Returns the correct human-readable header line for an objective."""
    for prefix, tmpl in _OBJECTIVE_HEADERS.items():
        if prefix in objective_id:
            return tmpl.format(asset=asset_id)
    # Fallback — still identifies objective
    return f"Diagnostic run for {asset_id} (objective: {objective_id}):"


def _format_advisory_text(
    objective_id: str,
    args: dict,
    advisory: Optional[Advisory],
    pack: Optional[EvidencePack],
    provenance: Optional[ProvenanceResult],
    results: list[CallResult],
    citation_res: Optional[CitationCheckResult] = None,
) -> str:
    """
    Renders human-readable text for WorkflowResult.text.
    Includes Advisory findings if available, provenance warnings, and data source statuses.
    """
    asset_id = args.get("asset_id", "the selected asset")
    lines = [_objective_header(objective_id, asset_id)]
    if pack:
        for item in pack.items:
            tm = item.payload.get("temporal_meta") if isinstance(item.payload, dict) else None
            if tm and isinstance(tm, dict) and tm.get("query_window", {}).get("start"):
                qw = tm["query_window"]
                db = tm.get("data_bounds", {})
                span_desc = f" ({qw.get('span_seconds')}s span)" if qw.get('span_seconds') else ""
                lines.append(f"\nTemporal Scope: {qw.get('start')} to {qw.get('end')}{span_desc}")
                if db.get("earliest_ts"):
                    # P2 fix: if point_count == 10000 it's a row cap — say so
                    pc = db.get('point_count')
                    cap_note = " (row cap — actual count may be higher)" if pc == 10000 else ""
                    lines.append(f"Data Found: {pc}{cap_note} records ({db.get('earliest_ts')} to {db.get('latest_ts')})")
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
        if advisory.troubleshooting_steps:
            lines.append("\nTroubleshooting Steps:")
            for s in advisory.troubleshooting_steps:
                lines.append(f" - {s}")
    if advisory and advisory.cited_evidence_ids:
        unique_ids = list(dict.fromkeys(advisory.cited_evidence_ids))
        lines.append(f"\nCited Evidence: {', '.join(unique_ids)}")

    if provenance and not provenance.passed and provenance.unattributed_numbers:
        count = len(provenance.unattributed_numbers)
        lines.append(f"\n[WARNING: {count} unverified figure(s) removed from assessment]")

    if citation_res and not citation_res.passed and citation_res.unverified_citations:
        count = len(citation_res.unverified_citations)
        lines.append(f"\n[WARNING: {count} unverified citation(s) removed]")

    return "\n".join(lines).strip()


def strip_unverified_provenance(text: str, unattributed_numbers: list[str]) -> str:
    """
    Surgically strips unattributed numbers from prose.
    First attempts clause-level removal (e.g. relative clauses, parentheticals, baselines)
    to preserve valid telemetry numbers in the main clause.
    Falls back to dropping the sentence if the main predicate itself contains the unverified number.
    """
    if not text or not unattributed_numbers:
        return text

    import re as _re
    sents = _re.split(r"(?<=[.!?])\s+", text)
    filtered_sents = []

    for s in sents:
        modified_s = s
        for num in unattributed_numbers:
            escaped_num = _re.escape(num)
            if not _re.search(rf"\b{escaped_num}\b", modified_s):
                continue

            # 1. Try stripping parenthetical containing the unverified number: e.g. (expected 70-80°C)
            paren_pattern = rf"\s*\([^)]*\b{escaped_num}\b[^)]*\)"
            if _re.search(paren_pattern, modified_s):
                modified_s = _re.sub(paren_pattern, "", modified_s).strip()
                continue

            # 2. Try stripping relative/subordinate clause containing the unverified number:
            # e.g. ", which is below the recommended baseline of 500 BOPD"
            clause_pattern = rf",\s*(?:which\s+is|which\s+was|exceeding|below|above|target|baseline|threshold|norm|nominal|expected)\b[^.,;?!]*\b{escaped_num}\b[^.,;?!]*"
            if _re.search(clause_pattern, modified_s, _re.IGNORECASE):
                modified_s = _re.sub(clause_pattern, "", modified_s, flags=_re.IGNORECASE).strip()
                if not modified_s.endswith((".", "!", "?")) and s.endswith((".", "!", "?")):
                    modified_s += s[-1]
                continue

        # If any unattributed number still remains in modified_s, drop the whole sentence
        if any(_re.search(rf"\b{_re.escape(num)}\b", modified_s) for num in unattributed_numbers):
            continue

        if modified_s.strip():
            filtered_sents.append(modified_s.strip())

    return " ".join(filtered_sents).strip()


def sanitize_advisory_language(text: str) -> str:
    """
    Ensures non-actuating, strictly advisory phrasing across all agent communications.
    Transforms direct imperative commands into operator advisory recommendations.
    """
    if not text:
        return text
    import re as _re
    subs = [
        (r"(?i)\b(?:shutdown|shut\s+down)\s+(?:the\s+)?well\b", "recommend evaluating well shutdown with field operator"),
        (r"(?i)\brestart\s+immediately\b", "advise evaluating controlled restart sequence"),
        (r"(?i)\b(?:close|open)\s+(?:the\s+)?(?:choke|valve)\b", "recommend verifying valve/choke alignment with operator"),
        (r"(?i)\btrip\s+(?:the\s+)?breaker\b", "advise confirming electrical circuit breaker status"),
    ]
    res = text
    for pat, rep in subs:
        res = _re.sub(pat, rep, res)
    return res


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
    if seal_res.status == "COMPLETE" or pack.sealed:
        save_pack(run_id, pack.version, pack.model_dump(mode="json"), ttl_sec=86400)

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
    # ---------------------------------------------------------------------------
    # P0 FIX — OP03 pre-check: if events window is empty AND user is asking
    # "why did X trip / what caused trip", refuse rather than narrate a false trip.
    # ---------------------------------------------------------------------------
    if "OP03" in objective_id:
        import re as _re
        _trip_query = bool(_re.search(
            r"\b(trip(?:ped)?|fault|cause|why|what\s+happened|shut.?down|fail(?:ed|ure)?)\b",
            (user_query or ""), _re.IGNORECASE
        ))
        _has_events = any(
            (not ev.is_empty_window)
            for ev in (formatted_evidence.events or [])
        )
        _all_empty = not _has_events
        if _trip_query and _all_empty:
            asset = args.get("asset_id", "the requested well")
            _empty_text = (
                f"No trip or fault events recorded for {asset} in the requested time window. "
                "I cannot diagnose a trip that has not been recorded. "
                f"Try a status check ('How is {asset} running?') or health assessment ('How healthy is {asset}?') instead."
            )
            viz_spec = VisualizationSpec(widget_id="cards", card_ids=[], evidence_ids=[])
            save_run_artifacts(
                run_id=run_id,
                advisory={},
                visualization=viz_spec.model_dump(),
            )
            return WorkflowResult(
                text=_empty_text,
                ok=True,
                plan=plan,
                call_results=results,
                pack=pack,
                seal_result=seal_res,
                advisory=None,
                visualization=viz_spec,
                insufficient_evidence=False,
            )

    advisory: Optional[Advisory] = None
    alarm_result: Optional[KpiAlarmResult] = None
    llm_available = True
    try:
        advisory, alarm_result = await synthesize_advisory(
            objective_id=objective_id,
            evidence=formatted_evidence,
            user_query=user_query or f"Diagnose well {args.get('asset_id', '')}",
        )
    except LLMUnavailableError:
        advisory = None
        alarm_result = None
        llm_available = False
    except Exception as e:
        import logging
        logging.getLogger(__name__).exception("synthesize_advisory failed: %s", e)
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
        advisory.cited_evidence_ids = list(dict.fromkeys(advisory.cited_evidence_ids))
        provenance = check_numeric_provenance(advisory, formatted_evidence)
        if provenance and not provenance.passed and provenance.unattributed_numbers:
            # Zero-fabrication enforcement: surgically strip unverified clauses/sentences
            advisory.assessment = strip_unverified_provenance(advisory.assessment, provenance.unattributed_numbers)
            if not advisory.assessment:
                advisory.assessment = "Insufficient evidence to complete assessment — key figures are unverified."
            if advisory.recommendation:
                advisory.recommendation = strip_unverified_provenance(advisory.recommendation, provenance.unattributed_numbers)

    # 8b. Troubleshooting Citation & Zero-Fabrication Guard (Phase 4.5)
    citation_res: Optional[CitationCheckResult] = None
    if advisory:
        has_kb = any(
            item.tool in ("search_knowledge", "get_fault_taxonomy", "trace_causal_graph")
            and isinstance(item.payload, dict)
            and (item.payload.get("hits") or item.payload.get("name") or item.payload.get("paths"))
            for item in (pack.items if pack else [])
        )
        if not has_kb:
            advisory.troubleshooting_steps = []
            advisory.verification_steps = []
        elif (advisory.troubleshooting_steps or advisory.verification_steps) and pack:
            citation_res = check_citation_provenance(advisory, pack)
            if not citation_res.passed:
                record_audit("citation_provenance_flag", payload={
                    "run_id": run_id,
                    "unverified": citation_res.unverified_citations,
                    "flagged_steps": citation_res.flagged_steps,
                    "flagged_verification_steps": citation_res.flagged_verification_steps,
                })
                # Zero-fabrication enforcement: remove unverified steps so fake citations never reach user
                flagged_tb_set = set(citation_res.flagged_steps)
                advisory.troubleshooting_steps = [
                    s for s in advisory.troubleshooting_steps if s not in flagged_tb_set
                ]
                flagged_v_set = set(citation_res.flagged_verification_steps)
                advisory.verification_steps = [
                    s for s in advisory.verification_steps if s not in flagged_v_set
                ]

        # Populate structured warnings and degraded sources on advisory
        p_warnings: list[str] = []
        if provenance and not provenance.passed and provenance.unattributed_numbers:
            p_warnings.append(f"{len(provenance.unattributed_numbers)} unverified figure(s) removed from assessment.")
        if citation_res and not citation_res.passed and citation_res.unverified_citations:
            p_warnings.append(f"{len(citation_res.unverified_citations)} unverified citation(s) removed.")
        advisory.provenance_warnings = p_warnings

        d_sources: list[str] = []
        if pack and pack.gaps:
            for g in pack.gaps:
                d_sources.append(f"{g.source_domain}: {g.reason}")
        advisory.degraded_sources = d_sources

        # P1 enforcement: verification_steps must be non-empty for diagnostic objectives.
        # Also covers OP06 PROCEDURAL queries (detected by non-empty troubleshooting_steps —
        # if the LLM returned steps, it was a procedure query, not definitional).
        # Context-aware verification ensures realistic operational steps instead of static boilerplate.
        _needs_verif = "OP03" in objective_id or "OP04" in objective_id or "OP05" in objective_id
        _op06_procedural = "OP06" in objective_id and bool(advisory.troubleshooting_steps)
        if (_needs_verif or _op06_procedural) and not advisory.verification_steps:
            asset = args.get("asset_id", "the well")
            if "OP03" in objective_id:
                advisory.verification_steps = [
                    f"Verify {asset} surface controller trip codes and confirm electrical/mechanical isolation before proceeding with diagnostic checks."
                ]
            elif "OP04" in objective_id:
                advisory.verification_steps = [
                    f"Cross-reference {asset} real-time telemetry against baseline operating envelope and monitor downhole vibration/temperature trends."
                ]
            elif "OP05" in objective_id:
                advisory.verification_steps = [
                    f"Inspect {asset} high-frequency trend anomalies and confirm early warning threshold settings with the production engineer."
                ]
            elif "OP06" in objective_id:
                advisory.verification_steps = [
                    "Confirm approved procedure steps with the field operations supervisor and verify all pre-execution safety prerequisites are satisfied."
                ]
            else:
                advisory.verification_steps = [
                    f"Confirm {asset} telemetry stabilization and operating parameters with the field technician."
                ]

        if advisory.assessment:
            advisory.assessment = sanitize_advisory_language(advisory.assessment)
        if advisory.recommendation:
            advisory.recommendation = sanitize_advisory_language(advisory.recommendation)
        if advisory.troubleshooting_steps:
            advisory.troubleshooting_steps = [sanitize_advisory_language(s) for s in advisory.troubleshooting_steps]
        if advisory.verification_steps:
            advisory.verification_steps = [sanitize_advisory_language(s) for s in advisory.verification_steps]

    # 9. Visualization Planner
    viz_spec = plan_visualization(objective_id, pack, formatted_evidence, advisory=advisory)

    # 10. Assemble Text
    text = _format_advisory_text(objective_id, args, advisory, pack, provenance, results, citation_res=citation_res)

    # Persist artifacts for subsequent FOLLOW_UP route reuse
    if advisory or viz_spec:
        save_run_artifacts(
            run_id=run_id,
            advisory=advisory.model_dump() if advisory else {},
            visualization=viz_spec.model_dump() if viz_spec else {},
        )

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
        llm_available=llm_available,
    )

