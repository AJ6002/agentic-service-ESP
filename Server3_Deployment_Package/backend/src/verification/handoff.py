"""
Handoff Verification Layer — §3 of Agent_Debugging/debug_methods.md.

Detects when a value crossing a layer boundary is actually a hardcoded fallback/mock
rather than genuine live data, and returns a structured verdict (status + reason +
provenance tag) that the pipeline surfaces live — in the advisory `provenance` list and
the audit trail — every run.

This is the production, always-on version of the fallback-detection logic that
real_pipeline_verification.py performs after-the-fact as a test.

IMPORTANT: the fallback signature constants below are the SINGLE SOURCE OF TRUTH. They
must exactly mirror the hardcoded fallback constants in the producing layers
(telemetry_service.py, graph.py, bff_routes.py). Those producing sites are tagged with
`# MOCK_SCAFFOLD:` markers (§4) that reference this module.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class HandoffStatus(str, Enum):
    LIVE = "LIVE"                # genuine data from an upstream real source
    FALLBACK = "FALLBACK"        # matched a known hardcoded fallback signature
    MOCK = "MOCK"               # explicitly flagged mock output (e.g. offline LLM mock)
    DEGRADED = "DEGRADED"        # partially live (some fields fell back)
    UNVERIFIED = "UNVERIFIED"    # could not determine (no signature / empty input)


@dataclass
class HandoffVerdict:
    layer: str
    status: HandoffStatus
    reason: str = ""
    details: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_live(self) -> bool:
        return self.status == HandoffStatus.LIVE

    def provenance_tag(self) -> str:
        """Compact string suitable for appending to an advisory's provenance list."""
        return f"{self.layer}_source: {self.status.value}"

    def to_dict(self) -> Dict[str, Any]:
        return {"layer": self.layer, "status": self.status.value, "reason": self.reason, "details": self.details}


# ---------------------------------------------------------------------------
# Fallback signatures — SINGLE SOURCE OF TRUTH (mirror the tagged constants in producers)
# ---------------------------------------------------------------------------
# Mirrors TelemetryService.get_latest() fallback block (telemetry_service.py).
TELEMETRY_FALLBACK: Dict[str, float] = {
    "motor_temperature": 135.0,
    "intake_pressure": 350.0,
    "discharge_pressure": 2100.0,
    "flow_rate": 1450.0,
    "drive_current_average": 62.0,
    "frequency": 50.0,
    "vibration_x": 1.2,
}

# Mirrors the default Plotly traces in bff_routes.py stream endpoint.
CHART_FALLBACK_PRODUCTION: List[float] = [1750, 1720, 1680, 1550, 1490, 1420, 1380]
CHART_FALLBACK_TDH: List[float] = [4100, 4080, 4050, 3950, 3900, 3850, 3800]

_FLOAT_TOL = 1e-6


def _close(a: Any, b: Any, tol: float = _FLOAT_TOL) -> bool:
    try:
        return abs(float(a) - float(b)) <= tol
    except (TypeError, ValueError):
        return False


# ---------------------------------------------------------------------------
# Verifiers
# ---------------------------------------------------------------------------
def verify_telemetry(values: Optional[Dict[str, Any]]) -> HandoffVerdict:
    """
    Classify a telemetry dict as LIVE / FALLBACK / DEGRADED / UNVERIFIED.

    FALLBACK  : every overlapping field exactly equals the known fallback constant.
    DEGRADED  : some (but not all) fields equal the fallback constant.
    LIVE      : no field matches the fallback constant.
    """
    if not values:
        return HandoffVerdict("telemetry", HandoffStatus.UNVERIFIED, "no telemetry values provided")

    overlap = [k for k in TELEMETRY_FALLBACK if k in values]
    if not overlap:
        return HandoffVerdict("telemetry", HandoffStatus.UNVERIFIED,
                              "no comparable fields against the fallback signature")

    matched = [k for k in overlap if _close(values.get(k), TELEMETRY_FALLBACK[k])]
    if len(matched) == len(overlap):
        return HandoffVerdict("telemetry", HandoffStatus.FALLBACK,
                              "all telemetry fields equal the hardcoded fallback constants "
                              "(cced_esp live telemetry unavailable)",
                              {"matched_fields": matched})
    if matched:
        return HandoffVerdict("telemetry", HandoffStatus.DEGRADED,
                              "some telemetry fields equal the hardcoded fallback constants",
                              {"fallback_fields": matched, "live_fields": [k for k in overlap if k not in matched]})
    return HandoffVerdict("telemetry", HandoffStatus.LIVE,
                          "telemetry differs from all fallback constants -> genuine live data")


def verify_model_output(models: Optional[Dict[str, Any]]) -> HandoffVerdict:
    """
    Classify normalized model context ({predicted_fault, confidence, health_index}).

    Detects the deterministic mock signatures from ModelAdapter.get_mock_model_output():
    the high-temp branch (MOTOR_OVERHEATING / conf 0.87 / hi 45) and the nominal branch
    (NORMAL_OPERATION / conf 0.98 / hi 95).
    """
    if not models:
        return HandoffVerdict("model", HandoffStatus.UNVERIFIED, "no model output provided")

    fault = str(models.get("predicted_fault", ""))
    conf = models.get("confidence")
    hi = models.get("health_index")

    mock_hi = (fault == "MOTOR_OVERHEATING" and _close(conf, 0.87) and _close(hi, 45))
    mock_norm = (fault == "NORMAL_OPERATION" and _close(conf, 0.98) and _close(hi, 95))
    if mock_hi or mock_norm:
        return HandoffVerdict("model", HandoffStatus.MOCK,
                              "model output exactly matches ModelAdapter deterministic mock signature "
                              "(no live ML source reached)",
                              {"predicted_fault": fault, "confidence": conf, "health_index": hi})
    return HandoffVerdict("model", HandoffStatus.LIVE,
                          "model output does not match the deterministic mock signature")


def verify_chart_series(traces: Optional[List[Dict[str, Any]]]) -> HandoffVerdict:
    """
    Classify Plotly chart traces. FALLBACK if the production series exactly equals the
    hardcoded demo array from bff_routes.py.
    """
    if not traces:
        return HandoffVerdict("chart", HandoffStatus.UNVERIFIED, "no chart traces provided")

    production = next((t.get("y") for t in traces if "Production" in (t.get("name") or "")), None)
    if production is None:
        return HandoffVerdict("chart", HandoffStatus.UNVERIFIED, "no production series found in chart")

    if list(production) == CHART_FALLBACK_PRODUCTION:
        return HandoffVerdict("chart", HandoffStatus.FALLBACK,
                              "chart production series equals the hardcoded demo fallback array "
                              "(no live cced_esp timeseries)")
    return HandoffVerdict("chart", HandoffStatus.LIVE,
                          "chart production series differs from the fallback array -> live timeseries")
