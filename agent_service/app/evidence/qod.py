"""
Quality of Data (QoD) Engine — Step 1.1.
Table-driven inbound validation per CallResult.
Four checks (all table lookups):
  1. Completeness — [REQ] fields per domain
  2. Freshness   — config/qod_freshness.yaml
  3. Unit consistency — cross-checks any upstream-supplied "units" map
                         (historian/aggregates/recent responses) against
                         config/signal_bounds.yaml's expected unit. A
                         mismatch REJECTS — a value in the wrong unit is
                         not usable data, not a warning-only concern.
  4. Range sanity — min_plausible / max_plausible from signal_bounds.yaml
                     ALARM thresholds are NOT rejection criteria.
Reference: SLICE_2_PLAN.md §1.1, ESP_APM_AGENT_APIS_COMPLETE_SPECIFICATION.md §2-3.
"""

from __future__ import annotations

import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from app.contracts.evidence import CallResult, EvidenceItem, QoDResult
from app.gateway.signal_names import normalize_measurements_dict

# ---------------------------------------------------------------------------
# Load config tables once at import time
# ---------------------------------------------------------------------------
_CONFIG_DIR = Path(__file__).resolve().parent.parent.parent / "config"

with open(_CONFIG_DIR / "qod_freshness.yaml", encoding="utf-8") as _f:
    _FRESHNESS_CFG: dict = yaml.safe_load(_f)["domains"]

with open(_CONFIG_DIR / "signal_bounds.yaml", encoding="utf-8") as _f:
    _SIGNAL_BOUNDS: dict = yaml.safe_load(_f)["signals"]

# ---------------------------------------------------------------------------
# Required fields per tool (completeness check).
# Only fields that MUST be present for the pack to be useful.
# ---------------------------------------------------------------------------
_REQUIRED_FIELDS: dict[str, list[str]] = {
    "get_live_telemetry": ["well_id", "measurements"],
    "get_asset_context":  ["well_id"],
    "get_vfm":            ["well_id"],
    "get_historian_window": ["well_id"],
    "get_historian_latest": ["well_id"],
    "get_events":         ["well_id"],
    "get_events_timeline": ["well_id"],
    "get_trips":          ["well_id"],
    "diagnose_fault":     ["well_id"],
    "get_ml_results":     ["well_id"],
    "get_anomaly":        ["well_id"],
    "get_explanation":    ["well_id"],
    "get_current_status": ["well_id"],
    "get_historian_aggregates": ["well_id"],
    "get_health_index":   ["well_id"],
    "get_degradation":    ["well_id"],
    "get_card":           [],
    "get_cards_catalog":  [],
    "get_live_wells":     [],
    # KB search returns {"query": ..., "hits": [...], "total_found": ...}
    # per esp_kb_service spec §3 — "hits" is the one field that must be
    # present (an empty list is a valid zero-result search, not missing data).
    "search_knowledge":   ["hits"],
}

# Map tool name → freshness domain key in qod_freshness.yaml
_TOOL_TO_DOMAIN: dict[str, str] = {
    "get_live_telemetry":   "live_telemetry",
    "get_vfm":              "live_vfm",
    "get_current_status":   "kpi",
    "get_card":             "cards",
    "get_cards_catalog":    "cards",
    "get_events":           "events",
    "get_events_timeline":   "events",
    "get_trips":            "events",
    "diagnose_fault":       "ml",
    "get_ml_results":       "ml",
    "get_anomaly":          "ml",
    "get_explanation":      "ml",
    "get_health_index":     "ml",
    "get_degradation":      "ml",
    "get_historian_window": "historian",
    "get_historian_aggregates": "historian",
    "get_historian_latest": "historian",
    "get_historian_coverage": "historian",
    "get_asset_context":    "asset",           # /live/asset → static pump curves & nameplate
    "get_live_wells":       "live_telemetry",
    "search_knowledge":     "kb",
}


# ---------------------------------------------------------------------------
# evidence_id counter — simple per-process sequence.
# In production this is fine: pack.py stamps evidence_id when building the pack.
# ---------------------------------------------------------------------------

_EV_SEQ: list[int] = [0]


def _next_ev_id(run_id: str) -> str:
    _EV_SEQ[0] += 1
    return f"EV-{run_id}-{_EV_SEQ[0]:04d}"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def validate(result: CallResult, run_id: str, tool: str) -> QoDResult:
    """
    Runs all four QoD checks on a single CallResult.
    Returns QoDResult(accepted=True, evidence_item=...) on pass,
    or QoDResult(accepted=False, rejection_reason=...) on fail.
    """
    # Immediately reject non-OK results — nothing to validate
    if result.status != "OK" or result.raw_response is None:
        return QoDResult(
            accepted=False,
            rejection_reason=f"CallResult status={result.status}, error={result.error}",
        )

    payload: dict[str, Any] = result.raw_response

    # 1. Completeness check
    completeness_err = _check_completeness(payload, tool)
    if completeness_err:
        return QoDResult(accepted=False, rejection_reason=completeness_err)

    # Empty KB search results must fail with NO_KB_COVERAGE so seal triggers honest refusal
    if tool == "search_knowledge":
        hits = payload.get("hits", [])
        if not hits or len(hits) == 0:
            return QoDResult(accepted=False, rejection_reason="NO_KB_COVERAGE: Knowledge base has 0 matching documents for query")

    # 2. Freshness check
    domain_key = _TOOL_TO_DOMAIN.get(tool)
    freshness_status, freshness_err = _check_freshness(payload, domain_key)
    if freshness_err:
        return QoDResult(accepted=False, rejection_reason=freshness_err)

    # 3. Unit consistency — historian/aggregates/recent responses carry
    # their own explicit "units" map (per spec §4). If the upstream unit
    # disagrees with the expected canonical unit in signal_bounds.yaml
    # (e.g. pressure reported in "bar" instead of "PSI"), the numeric
    # value is meaningless even though it's structurally present — this
    # must reject, not just log a warning, otherwise a unit mismatch
    # silently gets re-labeled with the WRONG-but-expected unit in step 5.
    unit_err = _check_unit_consistency(payload)
    if unit_err:
        return QoDResult(accepted=False, rejection_reason=unit_err)

    # 4. Range sanity — on the nested measurements dict (live/historian) AND
    # on top-level ML numeric fields (health_score, score, probability),
    # which are NOT nested under "measurements" in their responses. Before
    # this, an ML endpoint returning e.g. health_score=-999 or score=47.0
    # (score is bounded 0.0-1.0) passed QoD unconditionally — the exact
    # "sensor/model failure" case this check exists to catch.
    measurements = payload.get("measurements", {})
    if measurements and isinstance(measurements, dict):
        normalized = normalize_measurements_dict(measurements)
        range_err = _check_range_sanity(normalized)
        if range_err:
            return QoDResult(accepted=False, rejection_reason=range_err)

    kpis = payload.get("kpis", {})
    if kpis and isinstance(kpis, dict):
        normalized_kpis = normalize_measurements_dict(kpis)
        range_err = _check_range_sanity(normalized_kpis)
        if range_err:
            return QoDResult(accepted=False, rejection_reason=range_err)

    toplevel_err = _check_toplevel_range_sanity(payload)
    if toplevel_err:
        return QoDResult(accepted=False, rejection_reason=toplevel_err)

    # 5. Build unit_map from signal bounds
    unit_map: dict[str, str] = {}
    if measurements and isinstance(measurements, dict):
        normalized = normalize_measurements_dict(measurements)
        for sig in normalized:
            if sig in _SIGNAL_BOUNDS:
                unit_map[sig] = _SIGNAL_BOUNDS[sig]["unit"]
    if kpis and isinstance(kpis, dict):
        normalized_kpis = normalize_measurements_dict(kpis)
        for sig in normalized_kpis:
            if sig in _SIGNAL_BOUNDS:
                unit_map[sig] = _SIGNAL_BOUNDS[sig]["unit"]

    if payload.get("units") and isinstance(payload["units"], dict):
        for sig, u in payload["units"].items():
            unit_map[sig] = str(u)

    evidence_id = _next_ev_id(run_id)
    fetched_at = datetime.now(timezone.utc)
    source_domain = domain_key or tool

    item = EvidenceItem(
        evidence_id=evidence_id,
        tool=tool,
        source_domain=source_domain,
        fetched_at=fetched_at,
        status=freshness_status,
        payload=payload,
        unit_map=unit_map,
    )
    return QoDResult(accepted=True, evidence_item=item)


# ---------------------------------------------------------------------------
# Internal check helpers
# ---------------------------------------------------------------------------

def _check_completeness(payload: dict[str, Any], tool: str) -> str | None:
    """Returns error string if required fields are missing, else None."""
    required = _REQUIRED_FIELDS.get(tool, [])
    for field in required:
        if field not in payload:
            return f"Completeness: required field '{field}' missing in {tool} response"
    return None


def _normalize_unit_str(u: str) -> str:
    """Case/whitespace-insensitive comparison only — not a unit converter."""
    norm = u.strip().lower().replace(" ", "").replace("_", "")
    if norm in ("g", "grms"):
        return "g"
    if norm in ("bool", "discrete", "boolean"):
        return "discrete"
    return norm


def _check_unit_consistency(payload: dict[str, Any]) -> str | None:
    """
    Cross-checks an upstream-supplied "units" map (historian/window,
    historian/aggregates, live/telemetry/recent all carry one per spec §4)
    against the expected canonical unit in signal_bounds.yaml.

    Responses with no "units" key (e.g. /live/telemetry, /ml/*) have
    nothing to cross-check and pass through — those fields get their unit
    assigned from signal_bounds.yaml directly in step 5, which is correct
    by construction, not something to validate here.
    """
    units = payload.get("units")
    if not units or not isinstance(units, dict):
        return None

    for raw_signal, upstream_unit in units.items():
        canonical = normalize_measurements_dict({raw_signal: None})
        signal = next(iter(canonical.keys()), raw_signal)
        if signal not in _SIGNAL_BOUNDS:
            continue
        expected_unit = _SIGNAL_BOUNDS[signal]["unit"]
        if _normalize_unit_str(str(upstream_unit)) != _normalize_unit_str(expected_unit):
            return (
                f"Unit mismatch: {signal} reported in '{upstream_unit}', "
                f"expected '{expected_unit}' — value is not trustworthy"
            )
    return None


def _check_freshness(
    payload: dict[str, Any], domain_key: str | None
) -> tuple[str, str | None]:
    """
    Returns (evidence_status, rejection_reason_or_None).
    evidence_status is 'OK' or 'STALE'.
    Rejection (critical staleness) returns ('STALE', reason).
    Warning-level staleness returns ('STALE', None) — accepted but marked.
    Never-stale domains always return ('OK', None).
    """
    if not domain_key or domain_key not in _FRESHNESS_CFG:
        return "OK", None

    cfg = _FRESHNESS_CFG[domain_key]

    if cfg.get("never_stale"):
        return "OK", None

    # Prefer age_key if present in payload
    age_key = cfg.get("age_key")
    if age_key and age_key in payload:
        age_sec = float(payload[age_key])
    else:
        # Derive age from timestamp key
        ts_key = cfg.get("timestamp_key")
        if not ts_key or ts_key not in payload:
            return "OK", None  # Can't compute age, accept
        try:
            ts = datetime.fromisoformat(str(payload[ts_key]).replace("Z", "+00:00"))
            age_sec = (datetime.now(timezone.utc) - ts).total_seconds()
        except (ValueError, TypeError):
            return "OK", None

    warn = cfg.get("warning_staleness_sec")
    crit = cfg.get("critical_staleness_sec")

    if crit is not None and age_sec > crit:
        return "STALE", f"Freshness: {domain_key} age={age_sec:.1f}s exceeds critical threshold {crit}s"

    if warn is not None and age_sec > warn:
        return "STALE", None  # Warning — accepted, marked STALE

    return "OK", None


# Top-level ML/KPI numeric fields that are NOT nested under "measurements".
# Maps the field name as it actually appears in the response to either a
# key in signal_bounds.yaml (reuse existing bounds) or an inline
# (min_plausible, max_plausible) pair for fields with no signal_bounds
# entry — probabilities and confidences are always physically 0.0-1.0
# regardless of which endpoint they came from.
_TOPLEVEL_RANGE_FIELDS: dict[str, tuple[str, tuple[float, float] | None]] = {
    "health_score": ("health_score", None),      # -> _SIGNAL_BOUNDS["health_score"]
    "score": ("anomaly_score", None),             # /ml/anomaly -> _SIGNAL_BOUNDS["anomaly_score"]
    "anomaly_score": ("anomaly_score", None),
    "probability": (None, (0.0, 1.0)),            # /ml/fault
    "confidence": (None, (0.0, 1.0)),             # present on every /ml/* response
    "projected_days_to_threshold": (None, (0.0, 3650.0)),  # RUL: 0-10yr sanity ceiling
    "rate_per_day": (None, (-100.0, 100.0)),
}


def _check_toplevel_range_sanity(payload: dict[str, Any]) -> str | None:
    """
    Range-checks top-level numeric fields (ML/KPI responses) that are not
    nested under "measurements". Same rule as _check_range_sanity: outside
    physical bounds -> rejected as sensor/model failure, not a value
    judgement on whether the result is "good news".
    """
    for field_name, (bounds_key, inline_bounds) in _TOPLEVEL_RANGE_FIELDS.items():
        if field_name not in payload:
            continue
        value = payload[field_name]
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            continue

        if bounds_key and bounds_key in _SIGNAL_BOUNDS:
            lo = _SIGNAL_BOUNDS[bounds_key].get("min_plausible")
            hi = _SIGNAL_BOUNDS[bounds_key].get("max_plausible")
        elif inline_bounds:
            lo, hi = inline_bounds
        else:
            continue

        if lo is not None and value < lo:
            return f"Range: {field_name}={value} below min_plausible={lo} (likely sensor/model failure)"
        if hi is not None and value > hi:
            return f"Range: {field_name}={value} above max_plausible={hi} (likely sensor/model failure)"
    return None


def _check_range_sanity(normalized_measurements: dict[str, Any]) -> str | None:
    """
    Checks all numeric measurements against min_plausible / max_plausible.
    Alarm thresholds are NOT rejection criteria — an alarming value is real data.
    Returns error string on first out-of-physical-range detection, else None.
    """
    for signal, value in normalized_measurements.items():
        if signal not in _SIGNAL_BOUNDS:
            continue
        if not isinstance(value, (int, float)):
            continue
        bounds = _SIGNAL_BOUNDS[signal]
        lo = bounds.get("min_plausible")
        hi = bounds.get("max_plausible")
        if lo is not None and value < lo:
            return (
                f"Range: {signal}={value} below min_plausible={lo}"
                f" (likely sensor failure)"
            )
        if hi is not None and value > hi:
            return (
                f"Range: {signal}={value} above max_plausible={hi}"
                f" (likely sensor failure)"
            )
    return None
