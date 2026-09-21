"""
XAI Synthesizer — Step 2.1.
Consumes: objective_id + FormattedEvidence (never the raw pack) + user_query.
Produces: Advisory (assessment, hypotheses, recommendation, verification_steps, confidence, cited_evidence_ids).
Reference: SLICE_2_PLAN.md §2.1.
"""

from __future__ import annotations

from typing import Optional
from app.contracts.advisory import Advisory
from app.evidence.formatter import FormattedEvidence
from app.llm.calls import narrate, AdvisoryOutputInvalid
from app.llm.client import LLMUnavailableError
from app.synthesis.kpi_alarm_check import check_kpi_alarms, KpiAlarmResult


def format_evidence_for_prompt(evidence: FormattedEvidence) -> str:
    """
    Renders FormattedEvidence into a clean, structured string block for prompt injection.
    Delineates both discrete event facts and numeric sensor values with exact evidence IDs.
    """
    sections = []

    # 0. Temporal Audit & Query Timestamps
    if evidence.temporal and evidence.temporal.has_data():
        temp = evidence.temporal
        t_lines = ["--- TEMPORAL AUDIT & QUERY TIMESTAMPS ---"]
        if temp.query_window_start and temp.query_window_end:
            span_str = f" ({temp.query_span_seconds}s span)" if temp.query_span_seconds is not None else ""
            t_lines.append(f"- Query Window Requested: {temp.query_window_start} to {temp.query_window_end}{span_str}")
        if temp.executed_at:
            t_lines.append(f"- API Call Executed At (UTC): {temp.executed_at}")
        if temp.data_earliest_ts and temp.data_latest_ts:
            t_lines.append(f"- Data Bounds Found ({temp.data_point_count} records): From {temp.data_earliest_ts} to {temp.data_latest_ts}")
        sections.append("\n".join(t_lines))

    # 1. Discrete Events & Trip History
    if evidence.events:
        ev_lines = ["--- OPERATIONAL EVENTS & TRIP RECORDS ---"]
        for ev in evidence.events:
            if ev.is_empty_window:
                w_info = f"({ev.window_start} to {ev.window_end})" if ev.window_start and ev.window_end else ""
                ev_lines.append(f"- [{ev.evidence_id}] Events in window {w_info}: 0 events recorded (quiescent).")
            else:
                alarms_str = ", ".join(ev.alarms) if ev.alarms else "None"
                ev_lines.append(
                    f"- [{ev.evidence_id}] Event ID: {ev.event_id} | Timestamp: {ev.timestamp} | "
                    f"State: {ev.operating_state} | Cause: {ev.trip_cause or 'N/A'} | "
                    f"Scenario: {ev.scenario or 'N/A'} | Alarms: [{alarms_str}]"
                )
        sections.append("\n".join(ev_lines))

    # 2. Numeric Sensor & KPI Measurements
    if evidence.values:
        val_lines = ["--- SENSOR & KPI MEASUREMENTS ---"]
        for item in evidence.values:
            val_lines.append(f"- [{item.evidence_id}] {item.signal}: {item.value_str} (Unit: {item.unit})")
        sections.append("\n".join(val_lines))


    # 3. Approved Knowledge Base Citations
    if hasattr(evidence, "kb_hits") and evidence.kb_hits:
        kb_lines = ["--- APPROVED KNOWLEDGE BASE CITATIONS & STANDARDS ---"]
        for hit in evidence.kb_hits:
            kb_lines.append(
                f"- [{hit.evidence_id}] Document: {hit.doc_id} | Section: {hit.section} | "
                f"Authority: {hit.authority} | Page: {hit.page or 'N/A'} | Relevance Score: {hit.score:.2f}\n"
                f"  Snippet: \"{hit.snippet}\""
            )
        sections.append("\n".join(kb_lines))

    if not sections:
        return "No evidence available in this pack."

    return "\n\n".join(sections)


def format_evidence_with_alarms(evidence: FormattedEvidence) -> tuple[str, KpiAlarmResult]:
    """
    Extends format_evidence_for_prompt with a deterministic KPI alarm pre-check.
    The alarm summary is prepended to the evidence block so the narrator LLM
    sees it as the first section — before any numeric measurement data.
    Returns (evidence_text, alarm_result) so callers can use alarm_result
    for the post-synthesis guard in runner.py.
    """
    alarm_result = check_kpi_alarms(evidence)
    base_text = format_evidence_for_prompt(evidence)
    alarm_block = alarm_result.alarm_summary()
    if alarm_block:
        evidence_text = alarm_block + "\n\n" + base_text
    else:
        evidence_text = base_text
    return evidence_text, alarm_result


async def synthesize_advisory(
    objective_id: str,
    evidence: FormattedEvidence,
    user_query: str = "",
) -> tuple["Advisory", KpiAlarmResult]:
    """
    Invokes LLM #3 with formatted evidence block to produce a structured Advisory.
    Now also runs the deterministic KPI alarm pre-check and injects the alarm summary
    as the first section of the evidence block before calling the LLM.
    Returns (Advisory, KpiAlarmResult) so runner.py can apply the post-synthesis guard.
    """
    evidence_text, alarm_result = format_evidence_with_alarms(evidence)
    advisory = await narrate(
        objective_id=objective_id,
        formatted_evidence_text=evidence_text,
        user_query=user_query,
    )

    # Post-synthesis health band guarantee for OP04
    if "OP04" in objective_id and advisory is not None:
        assessment_upper = advisory.assessment.upper()
        bands = ["HEALTHY", "DEGRADED", "CRITICAL"]
        if not any(b in assessment_upper for b in bands):
            band = None
            band_item = evidence.by_signal("health_band")
            if band_item and band_item.value_str:
                band = band_item.value_str.upper()
            else:
                score_item = evidence.by_signal("health_score")
                if score_item and score_item.raw is not None:
                    try:
                        s = float(score_item.raw)
                        if s >= 75.0:
                            band = "HEALTHY"
                        elif s >= 50.0:
                            band = "DEGRADED"
                        else:
                            band = "CRITICAL"
                    except (ValueError, TypeError):
                        band = "DEGRADED"
                else:
                    band = "DEGRADED"
            advisory.assessment = f"Operating condition is categorized in the {band} band. " + advisory.assessment


    # Post-synthesis decline rate & truth-telling guarantee for OP02
    if "OP02" in objective_id and advisory is not None:
        trend_item = evidence.by_signal("production_trend")
        trend = str(trend_item.raw) if (trend_item and trend_item.raw) else "STABLE"
        rate_item = evidence.by_signal("decline_rate_bpd_per_day")

        if trend == "DECLINING":
            # 1. Ensure decline rate with BPD/day is named
            if rate_item and "BPD/day" not in advisory.assessment:
                advisory.assessment = f"Production has declined at an estimated rate of {rate_item.value_str}. " + advisory.assessment
            # 2. Strip any forbidden 'normal' claims
            for phrase in ["operating normally", "is normal", "normal operation", "normal conditions", "healthy"]:
                if phrase in advisory.assessment.lower():
                    import re as _re
                    advisory.assessment = _re.sub(rf"\b{_re.escape(phrase)}\b", "abnormal production decline", advisory.assessment, flags=_re.IGNORECASE)
        else:
            # Stable well: ensure assessment explicitly states stability and no fake decline is forced
            if "stable" not in advisory.assessment.lower() and "no decline" not in advisory.assessment.lower():
                advisory.assessment = "Production rate is stable with no abnormal decline detected. " + advisory.assessment

    return advisory, alarm_result
