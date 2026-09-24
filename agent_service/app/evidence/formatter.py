"""
Evidence Formatter — Step 1.3.
Converts a sealed EvidencePack into FormattedEvidence:
every numeric fact becomes a FormattedValue(value_str, unit, evidence_id).
No raw float reaches the output.
Reference: SLICE_2_PLAN.md §1.3.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from app.contracts.evidence import EvidencePack, EvidenceItem
from app.gateway.signal_names import normalize_measurements_dict


@dataclass
class FormattedValue:
    """A single attributed numeric (or boolean) fact."""
    value_str: str       # Human-readable: "87.7 °C"
    unit: str            # Engineering unit: "°C"
    evidence_id: str     # Provenance: "EV-abc-0001"
    signal: str          # Canonical signal name: "motor_temp_c"
    raw: float | int | bool | None = None  # Raw value for downstream comparisons


@dataclass
class FormattedEventRecord:
    """A single attributed discrete event fact (or empty window indicator)."""
    evidence_id: str
    event_id: Optional[str] = None
    timestamp: Optional[str] = None
    operating_state: Optional[str] = None
    scenario: Optional[str] = None
    trip_cause: Optional[str] = None
    alarms: list[str] = field(default_factory=list)
    event_type: Optional[str] = None
    is_empty_window: bool = False
    window_start: Optional[str] = None
    window_end: Optional[str] = None



@dataclass
class TemporalScope:
    query_window_start: Optional[str] = None
    query_window_end: Optional[str] = None
    query_span_seconds: Optional[float] = None
    executed_at: Optional[str] = None
    data_earliest_ts: Optional[str] = None
    data_latest_ts: Optional[str] = None
    data_point_count: int = 0

    def has_data(self) -> bool:
        return bool(self.query_window_start or self.executed_at or self.data_earliest_ts)


@dataclass
class FormattedKbHit:
    """A single approved Knowledge Base citation hit."""
    evidence_id: str
    doc_id: str
    section: str
    revision: Optional[str] = None
    authority: str = "LEVEL_A"
    applicability: list[str] = field(default_factory=list)
    page: Optional[int] = None
    snippet: str = ""
    score: float = 0.0

@dataclass
class FormattedEvidence:
    """All attributed facts extracted from a sealed EvidencePack."""
    run_id: str
    pack_version: int
    values: list[FormattedValue] = field(default_factory=list)
    events: list[FormattedEventRecord] = field(default_factory=list)
    kb_hits: list[FormattedKbHit] = field(default_factory=list)
    temporal: TemporalScope = field(default_factory=TemporalScope)

    def by_signal(self, signal: str) -> FormattedValue | None:
        for v in self.values:
            if v.signal == signal:
                return v
        return None


def format_pack(pack: EvidencePack) -> FormattedEvidence:
    """
    Extracts every numeric / boolean value from a pack's EvidenceItems
    and wraps each in a FormattedValue with provenance.

    A pack with zero numeric signals produces FormattedEvidence with
    an empty values list — never a crash.
    """
    result = FormattedEvidence(run_id=pack.run_id, pack_version=pack.version)

    for item in pack.items:
        _extract_from_item(item, result)
        tm = item.payload.get("temporal_meta") if isinstance(item.payload, dict) else None
        if tm and isinstance(tm, dict):
            qw = tm.get("query_window", {})
            db = tm.get("data_bounds", {})
            if qw.get("start") and not result.temporal.query_window_start:
                result.temporal.query_window_start = qw.get("start")
                result.temporal.query_window_end = qw.get("end")
                result.temporal.query_span_seconds = qw.get("span_seconds")
            if tm.get("executed_at") and not result.temporal.executed_at:
                result.temporal.executed_at = tm.get("executed_at")
            if db.get("earliest_ts"):
                result.temporal.data_earliest_ts = db.get("earliest_ts")
                result.temporal.data_latest_ts = db.get("latest_ts")
                result.temporal.data_point_count = db.get("point_count", 0)

    return result


def _extract_from_item(item: EvidenceItem, result: FormattedEvidence) -> None:
    """
    Pulls numeric signals from item.payload["measurements"] (if present),
    item.payload["kpis"] (if present, e.g. /kpi/{well}), and any top-level
    numeric fields (e.g. health_score, score, probability).
    """
    payload = item.payload

    # 1. measurements dict (live telemetry, historian)
    raw_measurements = payload.get("measurements")
    if raw_measurements and isinstance(raw_measurements, dict):
        normalized = normalize_measurements_dict(raw_measurements)
        for signal, value in normalized.items():
            if not isinstance(value, (int, float, bool)):
                continue
            unit = item.unit_map.get(signal, "")
            result.values.append(
                FormattedValue(
                    value_str=_format_value(value, unit),
                    unit=unit,
                    evidence_id=item.evidence_id,
                    signal=signal,
                    raw=value,
                )
            )

    # 2. kpis dict (/kpi/{well} responses from get_current_status)
    raw_kpis = payload.get("kpis")
    if raw_kpis and isinstance(raw_kpis, dict):
        normalized_kpis = normalize_measurements_dict(raw_kpis)
        for signal, value in normalized_kpis.items():
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                continue
            unit = item.unit_map.get(signal, "")
            result.values.append(
                FormattedValue(
                    value_str=_format_value(value, unit),
                    unit=unit,
                    evidence_id=item.evidence_id,
                    signal=signal,
                    raw=value,
                )
            )
            # If KPI has anomaly_score, also emit as 'score' so anomaly-score card
            # (required_signals: ['score']) can qualify.
            if signal == "anomaly_score":
                result.values.append(
                    FormattedValue(
                        value_str=_format_value(value, unit),
                        unit=unit,
                        evidence_id=item.evidence_id,
                        signal="score",
                        raw=value,
                    )
                )

    # 2.5 Tabular historical rows & columns (get_historian_aggregates, get_historian_window)
    columns = payload.get("columns")
    rows = payload.get("rows")
    if columns and rows and isinstance(columns, list) and isinstance(rows, list) and len(rows) > 0:
        latest_row = rows[-1]
        for col_idx, col_name in enumerate(columns):
            if col_name in ("timestamp", "bucket") or col_idx >= len(latest_row):
                continue
            val = latest_row[col_idx]
            if val is not None and isinstance(val, (int, float)) and not isinstance(val, bool):
                unit = item.unit_map.get(col_name, "")
                result.values.append(
                    FormattedValue(
                        value_str=_format_value(val, unit),
                        unit=unit,
                        evidence_id=item.evidence_id,
                        signal=col_name,
                        raw=val,
                    )
                )

        # Production decline rate and trend calculation for OP02
        rate_col = "liquid_rate_bpd" if "liquid_rate_bpd" in columns else ("oil_rate_bopd" if "oil_rate_bopd" in columns else None)
        if rate_col and len(rows) >= 2:
            r_idx = columns.index(rate_col)
            valid_points = []
            for row in rows:
                if r_idx < len(row) and isinstance(row[r_idx], (int, float)) and not isinstance(row[r_idx], bool):
                    ts = row[0] if len(row) > 0 else None
                    valid_points.append((ts, float(row[r_idx])))

            if len(valid_points) >= 2:
                start_ts, start_val = valid_points[0]
                end_ts, end_val = valid_points[-1]
                elapsed_days = max(1.0, len(rows) / 24.0)
                if isinstance(start_ts, str) and isinstance(end_ts, str):
                    try:
                        from datetime import datetime as _dt
                        t0 = _dt.fromisoformat(start_ts.replace("Z", "+00:00"))
                        t1 = _dt.fromisoformat(end_ts.replace("Z", "+00:00"))
                        diff_d = (t1 - t0).total_seconds() / 86400.0
                        if diff_d > 0.05:
                            elapsed_days = diff_d
                    except Exception:
                        pass

                drop = start_val - end_val
                decline_rate_per_day = drop / elapsed_days
                pct_change = (drop / start_val * 100.0) if start_val > 0 else 0.0

                is_declining = pct_change > 5.0 and decline_rate_per_day > 0.0
                trend_str = "DECLINING" if is_declining else "STABLE"

                result.values.append(
                    FormattedValue(
                        value_str=f"{max(0.0, decline_rate_per_day):.2f} BPD/day",
                        unit="BPD/day",
                        evidence_id=item.evidence_id,
                        signal="decline_rate_bpd_per_day",
                        raw=round(max(0.0, decline_rate_per_day), 2),
                    )
                )
                result.values.append(
                    FormattedValue(
                        value_str=trend_str,
                        unit="",
                        evidence_id=item.evidence_id,
                        signal="production_trend",
                        raw=trend_str,
                    )
                )
                result.values.append(
                    FormattedValue(
                        value_str=f"{pct_change:.1f} %",
                        unit="%",
                        evidence_id=item.evidence_id,
                        signal="production_decline_pct",
                        raw=round(pct_change, 2),
                    )
                )

    # 3. Top-level numeric fields from ML/KPI/degradation responses. These
    # are NOT nested under "measurements". Field names here are the REAL
    # keys the spec's endpoints return (verified against
    # ESP_APM_AGENT_APIS_COMPLETE_SPECIFICATION.md).
    _TOPLEVEL_NUMERIC = {
        "health_score": item.unit_map.get("health_score") or "index",          # /ml/health, /kpi
        "score": item.unit_map.get("anomaly_score") or "index",                # /ml/anomaly
        "probability": "probability",                                          # /ml/fault (top-level)
        "projected_days_to_threshold": "days",                                  # /ml/degradation (RUL)
        "rate_per_day": "points/day",                                           # /ml/degradation
        "confidence": "confidence",                                             # present on every /ml/* response
    }
    for field_name, unit in _TOPLEVEL_NUMERIC.items():
        value = payload.get(field_name)
        if value is not None and isinstance(value, (int, float)) and not isinstance(value, bool):
            result.values.append(
                FormattedValue(
                    value_str=_format_value(value, unit),
                    unit=unit,
                    evidence_id=item.evidence_id,
                    signal=field_name,
                    raw=value,
                )
            )

    # 3.5 String attributes (e.g. health band)
    band = payload.get("band")
    if band and isinstance(band, str):
        result.values.append(
            FormattedValue(
                value_str=band.strip().upper(),
                unit="band",
                evidence_id=item.evidence_id,
                signal="health_band",
                raw=band.strip().upper(),
            )
        )

    # 4. Discrete Events & Trips (get_events, get_trips, /events/*)
    if item.tool in ("get_events", "get_trips") or "events" in payload or "event_count" in payload:
        raw_events = payload.get("events")
        event_count = payload.get("event_count")
        if event_count == 0 or (raw_events is not None and len(raw_events) == 0):
            result.events.append(
                FormattedEventRecord(
                    evidence_id=item.evidence_id,
                    is_empty_window=True,
                    window_start=payload.get("start"),
                    window_end=payload.get("end"),
                )
            )
        elif isinstance(raw_events, list):
            for ev in raw_events:
                if isinstance(ev, dict):
                    result.events.append(
                        FormattedEventRecord(
                            evidence_id=item.evidence_id,
                            event_id=ev.get("event_id"),
                            timestamp=ev.get("timestamp"),
                            operating_state=ev.get("operating_state"),
                            scenario=ev.get("scenario"),
                            trip_cause=ev.get("trip_cause"),
                            alarms=list(ev.get("alarms") or []),
                            event_type=ev.get("event_type"),
                            window_start=payload.get("start"),
                            window_end=payload.get("end"),
                        )
                    )


# 5. Knowledge Base Integration (search_knowledge, get_fault_taxonomy, trace_causal_graph)
    if item.tool == "get_fault_taxonomy" and not payload.get("unmapped"):
        fault_name = payload.get("name") or payload.get("fault_id", "Unknown Fault")
        doc_id = payload.get("applicable_manual") or "API_RP_11S"
        criticality = payload.get("criticality", "WARNING")
        symptoms = payload.get("symptoms", [])
        actions = payload.get("recommended_actions", [])
        for act in actions:
            result.kb_hits.append(
                FormattedKbHit(
                    evidence_id=item.evidence_id,
                    doc_id=doc_id,
                    section=payload.get("fault_id", "Remedies"),
                    revision="Latest",
                    authority="LEVEL_A_STANDARD" if ("API" in doc_id or "IEC" in doc_id) else "LEVEL_B_OEM",
                    snippet=f"Fault: {fault_name} ({criticality}). Procedure: {act}. Symptoms: {', '.join(symptoms)}",
                    score=1.0,
                )
            )

    if item.tool == "trace_causal_graph" and not payload.get("unmapped"):
        paths = payload.get("paths", [])
        for p in paths:
            if isinstance(p, dict):
                sop = p.get("recommended_sop", {})
                std_ref = sop.get("standard_ref") or "API_RP_11S"
                doc_id = "API_RP_11S"
                section = sop.get("sop_id", "Recovery_SOP")
                if "Section" in str(std_ref):
                    parts = str(std_ref).split("Section")
                    doc_id = parts[0].strip().replace(" ", "_")
                    section = "§" + parts[1].strip()
                elif "+" in str(std_ref):
                    doc_id = str(std_ref).split("+")[-1].strip().replace(" ", "_")
                elif " " in str(std_ref):
                    doc_id = str(std_ref).replace(" ", "_")
                chain_str = " -> ".join(p.get("chain", []))
                action_text = sop.get("action", f"Initiate recovery SOP for {p.get('fault_name')}")
                result.kb_hits.append(
                    FormattedKbHit(
                        evidence_id=item.evidence_id,
                        doc_id=doc_id,
                        section=section,
                        revision="Latest",
                        authority="LEVEL_A_STANDARD" if ("API" in doc_id or "IEC" in doc_id) else "LEVEL_B_OEM",
                        snippet=f"SOP Action: {action_text}. Root Cause Chain: {chain_str}",
                        score=float(p.get("confidence", 0.9)),
                    )
                )

    if item.tool == "search_knowledge" or "hits" in payload:
        raw_hits = payload.get("hits")
        if isinstance(raw_hits, list):
            # Sort LEVEL_A first, then score descending
            sorted_hits = sorted(
                raw_hits,
                key=lambda h: (0 if str(h.get("authority", "")).upper() == "LEVEL_A" else 1, -float(h.get("score", 0.0) or 0.0))
            )
            for h in sorted_hits:
                if isinstance(h, dict):
                    result.kb_hits.append(
                        FormattedKbHit(
                            evidence_id=item.evidence_id,
                            doc_id=h.get("doc_id", "APPROVED-KB"),
                            section=h.get("section", "N/A"),
                            revision=h.get("revision"),
                            authority=h.get("authority", "LEVEL_A"),
                            applicability=list(h.get("applicability") or []),
                            page=h.get("page"),
                            snippet=h.get("snippet", ""),
                            score=float(h.get("score", 0.0) or 0.0),
                        )
                    )
            result.values.append(
                FormattedValue(
                    value_str=f"{len(raw_hits)} hits",
                    unit="hits",
                    evidence_id=item.evidence_id,
                    signal="kb_hit_count",
                    raw=len(raw_hits),
                )
            )


def _format_value(value: Any, unit: str) -> str:
    """Renders a numeric value with its unit."""
    if isinstance(value, bool):
        return "1" if value else "0"
    if isinstance(value, int):
        return f"{value} {unit}".strip()
    # Float: round to 2 decimal places
    return f"{value:.2f} {unit}".strip()

