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


import re


def sanitize_relational_comparisons(text: str) -> str:
    """
    Detects and corrects/strips hallucinated inverted numeric comparisons in prose.
    E.g.:
      "350.40 PSI, which is below the recommended baseline of 150 psi"
      -> "350.40 PSI, which is above the recommended baseline of 150 psi"
    """
    if not text:
        return text

    pattern = re.compile(
        r"(\b\d+(?:\.\d+)?)\s*(?:PSI|psi|BOPD|bpd|BPD|A|V|Hz|°C|g)?\s*(?:,\s*which\s+is|\s+is|\s+was)\s+"
        r"(below|less than|under|lower than|above|greater than|over|higher than|exceeds)\s+"
        r"(?:the\s+)?(?:recommended\s+|minimum\s+|maximum\s+|nominal\s+)?(?:baseline|threshold|limit|target|norm|value|standard)?\s*(?:of\s+)?(\b\d+(?:\.\d+)?\b)",
        re.IGNORECASE,
    )

    def _fix_match(m: re.Match) -> str:
        full_match = m.group(0)
        v1_str = m.group(1)
        comp = m.group(2).lower()
        v2_str = m.group(3)
        try:
            v1 = float(v1_str)
            v2 = float(v2_str)
        except ValueError:
            return full_match

        if comp in ("below", "less than", "under", "lower than"):
            if v1 > v2:
                fixed_comp = "above" if comp in ("below", "under", "lower than") else "greater than"
                return full_match[:m.start(2) - m.start(0)] + fixed_comp + full_match[m.end(2) - m.start(0):]
        elif comp in ("above", "greater than", "over", "higher than", "exceeds"):
            if v1 < v2:
                fixed_comp = "below" if comp in ("above", "over", "exceeds", "higher than") else "less than"
                return full_match[:m.start(2) - m.start(0)] + fixed_comp + full_match[m.end(2) - m.start(0):]
        return full_match

    return pattern.sub(_fix_match, text)


def sanitize_positive_production_contradictions(text: str, evidence: Optional[FormattedEvidence] = None) -> str:
    """
    Strips sentences claiming zero production, 'not producing', or 'flow rates are zero'
    when evidence or the text itself confirms positive flow/oil/liquid rates.
    """
    if not text:
        return text

    has_positive_flow = False
    if evidence:
        for sig in ("oil_rate_bopd", "liquid_rate_bpd", "flow_rate", "flow_rate_bpd", "gross_rate", "oil_rate", "liquid_rate"):
            item = evidence.by_signal(sig)
            if item and item.raw is not None:
                try:
                    if float(item.raw) > 0.0:
                        has_positive_flow = True
                        break
                except (ValueError, TypeError):
                    pass

    # Also check if text itself asserts positive flow rate (e.g. 'flow rate is 400.00 BOPD')
    if not has_positive_flow:
        flow_match = re.search(r"\b(?:flow|oil|liquid|production)\s*(?:rate)?\s*(?:is|of|measured at)?\s*([1-9]\d*(?:\.\d+)?)\s*(?:BOPD|BPD|bpd|bopd)\b", text, re.IGNORECASE)
        if flow_match:
            has_positive_flow = True

    if has_positive_flow:
        sents = re.split(r"(?<=[.!?])\s+", text)
        filtered_sents = []
        for s in sents:
            s_lower = s.lower()
            if any(p in s_lower for p in [
                "not producing",
                "zero production",
                "no liquid production",
                "no oil production",
                "flow rates are zero",
                "flow rate is zero",
                "shut-in",
                "shut in",
            ]):
                continue
            filtered_sents.append(s)
        return " ".join(filtered_sents).strip() if filtered_sents else text

    return text


def sanitize_api_timestamp_leaks(text: str) -> str:
    """
    Strips raw API execution timestamps regurgitated by the LLM from prompts,
    such as 'The API call was executed at 2026-09-26T17:39:11.438377Z, and'.
    """
    if not text:
        return text
    text = re.sub(r"(?i)\bthe\s+api\s+call\s+was\s+executed\s+at\s+[^,;\.]+[,\.;]?\s*(?:and\s+)?", "", text)
    text = re.sub(r"(?i)\bapi\s+call\s+executed\s+at\s+[^,;\.]+[,\.;]?\s*(?:and\s+)?", "", text)
    return text.strip()


def sanitize_normal_parameter_contradictions(text: str) -> str:
    """
    Purges 'normal parameters' and 'operating within normal parameters' from diagnostic outputs.
    Replaces with accurate engineering phrasing: 'operational thresholds' or 'steady sensor readings'.
    """
    if not text:
        return text
    text = re.sub(r"(?i)\boperating\s+within\s+normal\s+parameters\b", "within operational thresholds", text)
    text = re.sub(r"(?i)\bwithin\s+normal\s+parameters\b", "within operational thresholds", text)
    text = re.sub(r"(?i)\bnormal\s+parameters\b", "operational thresholds", text)
    text = re.sub(r"(?i)\boperating\s+normally\b", "operating stably", text)
    return text


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

    # Fact-checking against physical evidence & relational comparisons
    if advisory is not None:
        advisory.assessment = sanitize_positive_production_contradictions(advisory.assessment, evidence)
        advisory.assessment = sanitize_relational_comparisons(advisory.assessment)
        advisory.assessment = sanitize_api_timestamp_leaks(advisory.assessment)
        if "OP03" in objective_id:
            advisory.assessment = sanitize_normal_parameter_contradictions(advisory.assessment)
        if advisory.recommendation:
            advisory.recommendation = sanitize_positive_production_contradictions(advisory.recommendation, evidence)
            advisory.recommendation = sanitize_relational_comparisons(advisory.recommendation)
            advisory.recommendation = sanitize_api_timestamp_leaks(advisory.recommendation)
            if "OP03" in objective_id:
                advisory.recommendation = sanitize_normal_parameter_contradictions(advisory.recommendation)

    # Post-synthesis decline rate & truth-telling guarantee for OP02
    if "OP02" in objective_id and advisory is not None:
        import re as _re
        trend_item = evidence.by_signal("production_trend")
        trend = str(trend_item.raw).upper() if (trend_item and trend_item.raw) else "STABLE"
        rate_item = evidence.by_signal("decline_rate_bpd_per_day")

        if trend == "DECLINING":
            # 1. Strip any sentence claiming stability
            sents = _re.split(r"(?<=[.!?])\s+", advisory.assessment)
            filtered_sents = []
            for s in sents:
                s_lower = s.lower()
                if any(p in s_lower for p in ["stable", "no abnormal decline", "no decline"]):
                    continue
                filtered_sents.append(s)
            advisory.assessment = " ".join(filtered_sents) if filtered_sents else advisory.assessment

            # 2. Ensure decline rate with BPD/day is named
            if rate_item and "BPD/day" not in advisory.assessment:
                advisory.assessment = f"Production has declined at an estimated rate of {rate_item.value_str}. " + advisory.assessment

            # 3. Strip any forbidden 'normal' claims
            for phrase in ["operating normally", "is normal", "normal operation", "normal conditions", "healthy"]:
                if phrase in advisory.assessment.lower():
                    advisory.assessment = _re.sub(rf"\b{_re.escape(phrase)}\b", "abnormal production decline", advisory.assessment, flags=_re.IGNORECASE)
        else:
            # Stable well: strip any sentence claiming decline
            sents = _re.split(r"(?<=[.!?])\s+", advisory.assessment)
            filtered_sents = []
            for s in sents:
                if _re.search(r"\b(declin\w+|falling|drop\w+|loss of production)\b", s, _re.IGNORECASE):
                    continue
                filtered_sents.append(s)
            cleaned_text = " ".join(filtered_sents).strip()

            # Ensure assessment explicitly states stability and no fake decline is forced
            if "stable" not in cleaned_text.lower() and "no decline" not in cleaned_text.lower():
                cleaned_text = ("Production rate is stable with no abnormal decline detected. " + cleaned_text).strip()
            advisory.assessment = cleaned_text

    # Post-synthesis anti-contradiction guarantee for OP03 (Fault Diagnosis)
    if "OP03" in objective_id and advisory is not None:
        import re as _re
        health_item = evidence.by_signal("health_score")
        health_val = None
        if health_item and health_item.raw is not None:
            try:
                health_val = float(health_item.raw)
            except (ValueError, TypeError):
                pass

        anom_item = evidence.by_signal("anomaly_score")
        anom_val = None
        if anom_item and anom_item.raw is not None:
            try:
                anom_val = float(anom_item.raw)
            except (ValueError, TypeError):
                pass

        is_abnormal = (
            (alarm_result is not None and alarm_result.has_critical)
            or (health_val is not None and health_val < 50.0)
            or (anom_val is not None and anom_val >= 0.65)
        )

        if is_abnormal:
            # Strip contradictory claims of normal operating parameters
            sents = _re.split(r"(?<=[.!?])\s+", advisory.assessment)
            filtered_sents = []
            for s in sents:
                s_lower = s.lower()
                if any(p in s_lower for p in [
                    "operating within normal parameters",
                    "within normal parameters",
                    "operating normally",
                    "operating quiescently",
                    "no immediate issues",
                    "no events or alarms were recorded",
                    "no events or alarms recorded",
                ]):
                    continue
                filtered_sents.append(s)
            cleaned_text = " ".join(filtered_sents).strip()
            if not cleaned_text or len(cleaned_text) < 25:
                h_desc = f"health score {health_val:.2f}" if health_val is not None else "degraded health index"
                cleaned_text = f"The well is in an abnormal operating condition with {h_desc}. Immediate diagnostic inspection is recommended."
            advisory.assessment = cleaned_text

    # Post-synthesis troubleshooting grounding & standardization guarantee for OP03 & OP06 (Cleanup Item 3)
    if advisory is not None and ("OP03" in objective_id or "OP06" in objective_id):
        import re as _re
        text = advisory.assessment
        has_numbered_steps = bool(_re.search(r"(?:^|\s+)(?:1\.|Step\s+1:?)\s+", text) and _re.search(r"(?:^|\s+)(?:2\.|Step\s+2:?)\s+", text))
        if has_numbered_steps:
            match = _re.search(r"(?:^|\s+)(?:1\.|Step\s+1:?)\s+", text)
            if match:
                intro = text[:match.start()].strip()
                rest = text[match.start():]
                step_chunks = _re.split(r"(?:^|\s+)(?:\d+\.|\bStep\s+\d+:?)\s+", rest)
                extracted = []
                for sc in step_chunks:
                    sc_clean = sc.strip().rstrip(".").strip()
                    if not sc_clean:
                        continue
                    for header in ["**Verification Steps**:", "Verification Steps:", "**Recommendation**:", "Recommendation:"]:
                        if header in sc_clean:
                            sc_clean = sc_clean.split(header)[0].strip()
                    if sc_clean:
                        extracted.append(sc_clean)
                if extracted and not advisory.troubleshooting_steps:
                    advisory.troubleshooting_steps = extracted
                if intro:
                    advisory.assessment = intro
                else:
                    advisory.assessment = "Approved standard operating procedure steps are detailed in the structured troubleshooting steps below."

        # Clean inline troubleshooting phrases dumped into assessment prose
        text = _re.sub(r"(?i),?\s*and\s+(?:the\s+)?troubleshooting\s+steps\s+are\s+to\s+[^,\.]+", "", text).strip()
        advisory.assessment = text

        if not evidence.kb_hits and "OP03" in objective_id:
            advisory.troubleshooting_steps = []
        elif evidence.kb_hits:
            # NOTE: The auto-populate fallback (synthesizing steps from KB hit snippets
            # when the LLM returned none) is intentionally REMOVED. KB hit snippets are
            # abstract/summary text, not actionable procedure steps, and this fallback
            # produced garbage like "The main objective was to develop a troubleshooting
            # manual..." as step text. The LLM's own steps are used directly.
            #
            # If the LLM returned steps without citations, ground them to evidence docs.
            grounded_steps = []
            for step in advisory.troubleshooting_steps:
                if "[" in step and "]" in step:
                    grounded_steps.append(step)
                else:
                    best_hit = None
                    best_overlap = 0
                    step_lower = step.lower()
                    for hit in evidence.kb_hits:
                        overlap = sum(1 for word in hit.snippet.lower().split() if len(word) > 3 and word in step_lower)
                        if overlap > best_overlap:
                            best_overlap = overlap
                            best_hit = hit
                    if best_hit is None and evidence.kb_hits:
                        best_hit = evidence.kb_hits[0]
                    if best_hit:
                        sec_str = f" §{best_hit.section}" if best_hit.section and not str(best_hit.section).startswith("§") else (f" {best_hit.section}" if best_hit.section else "")
                        grounded_steps.append(f"[{best_hit.doc_id}{sec_str}] {step}")
                    else:
                        grounded_steps.append(step)
            advisory.troubleshooting_steps = grounded_steps[:7]

    # Terminology correction: PIP stands for Pump Intake Pressure, not Pump Inlet Pressure
    if advisory is not None and "Pump Inlet Pressure" in advisory.assessment:
        advisory.assessment = advisory.assessment.replace("Pump Inlet Pressure", "Pump Intake Pressure")

    # -------------------------------------------------------------------------
    # P0/P1 POST-SYNTHESIS FILTER FOR OP06 (code-level safety net)
    # Even if the LLM ignores the prompt, we enforce:
    #   1. No raw KB dump garbage in troubleshooting_steps / verification_steps
    #   2. For DEFINITIONAL queries both lists must be []
    #   3. For PROCEDURAL queries verification_steps must be non-empty
    # -------------------------------------------------------------------------
    if advisory is not None and "OP06" in objective_id:
        import re as _re

        _RAW_DUMP_PATTERNS = [
            r"<!--",                          # HTML/markdown artifacts
            r"-->",
            r"\|.*\|",                        # pipe-table rows
            r"formula-not-decoded",           # math blocks not parsed
            r"-\s+[A-Z][a-z]{1,4}\s*$",       # mid-word truncations e.g. "- Chang"
            r"\s+-\s*$",                      # trailing dash
        ]

        def _is_garbage_step(s: str) -> bool:
            for pat in _RAW_DUMP_PATTERNS:
                if _re.search(pat, s):
                    return True
            # also reject very short or purely whitespace entries
            return len(s.strip()) < 10

        advisory.troubleshooting_steps = [
            s for s in advisory.troubleshooting_steps if not _is_garbage_step(s)
        ]
        advisory.verification_steps = [
            s for s in advisory.verification_steps if not _is_garbage_step(s)
        ]

        # Detect if query is definitional (no procedural verb)
        _query_lower = (user_query or "").lower()
        _procedural_verbs = (
            "how do i", "how to", "steps for", "what are the steps",
            "procedure for", "troubleshoot", "restart", "fix it", "repair",
        )
        _is_procedural = any(v in _query_lower for v in _procedural_verbs)

        if not _is_procedural:
            # Pure definitional — both lists must be empty
            advisory.troubleshooting_steps = []
            advisory.verification_steps = []
        else:
            # Procedural — ensure at least one verification step
            if not advisory.verification_steps:
                advisory.verification_steps = [
                    "Confirm the system is back online and nominal operating parameters "
                    "are re-established before resuming production."
                ]

    return advisory, alarm_result

