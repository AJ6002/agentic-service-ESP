"""
KPI Alarm Pre-Check -- deterministic gate, no LLM, no network.

Scans FormattedEvidence signal values against hard-coded ESP operational
alarm thresholds. Produces KpiAlarmResult with labeled per-signal alarms
and a pre-formatted summary block for injection into the narrator evidence
prompt.

Design intent: the same way check_numeric_provenance enforces number
attribution, this module enforces KPI semantic interpretation. The narrator
LLM cannot be trusted to independently infer that oil_rate_bopd=0 means
"not producing" without explicit guidance. This module injects that guidance
as ground truth before the LLM sees the evidence block.

Import note: FormattedEvidence is imported under TYPE_CHECKING only to
avoid the pre-existing circular import cycle in app.contracts.advisory.
At runtime the argument is accessed via duck-typing (.values attribute).

Reference: Bug B fix, SLICE_2_PLAN.md SS2.1 extension.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.evidence.formatter import FormattedEvidence


# ---------------------------------------------------------------------------
# Alarm rules -- each entry: (signal, condition_fn, severity, human_label)
# Severity: "CRITICAL" > "HIGH" > "WARN"
# ---------------------------------------------------------------------------

def _is_zero(v: float) -> bool:
    return abs(v) < 1e-6


_ALARM_RULES: list[tuple[str, object, str, str]] = [
    # Production rates: zero means well is not producing
    (
        "oil_rate_bopd", _is_zero, "CRITICAL",
        "zero oil production -- the well is not producing oil",
    ),
    (
        "liquid_rate_bpd", _is_zero, "CRITICAL",
        "zero liquid production -- the well is not producing",
    ),
    (
        "gas_rate_mscfd", _is_zero, "WARN",
        "zero gas production",
    ),
    # Motor: zero load = motor not running
    (
        "motor_load_pct", _is_zero, "CRITICAL",
        "motor load is 0%% -- motor is not running",
    ),
    # Anomaly score thresholds (CRITICAL takes priority over HIGH -- see dedup logic)
    (
        "anomaly_score", lambda v: v >= 0.95, "CRITICAL",
        "anomaly score >= 0.95 -- severe anomalous state detected by ML model",
    ),
    (
        "anomaly_score", lambda v: 0.85 <= v < 0.95, "HIGH",
        "anomaly score >= 0.85 -- anomaly alarm band (ML model flagged anomalous state)",
    ),
    # Water cut: near-total water cut is a production problem
    (
        "water_cut_pct", lambda v: v >= 95.0, "HIGH",
        "water cut >= 95%% -- near-total water production, minimal oil",
    ),
]


@dataclass
class KpiAlarm:
    signal: str
    value: float
    severity: str       # "CRITICAL" | "HIGH" | "WARN"
    label: str          # human-readable problem description
    evidence_id: str


@dataclass
class KpiAlarmResult:
    alarms: list[KpiAlarm] = field(default_factory=list)

    @property
    def has_critical(self) -> bool:
        return any(a.severity == "CRITICAL" for a in self.alarms)

    @property
    def has_high(self) -> bool:
        return any(a.severity in ("CRITICAL", "HIGH") for a in self.alarms)

    @property
    def is_clean(self) -> bool:
        return len(self.alarms) == 0

    def alarm_summary(self) -> str:
        """
        Pre-formatted block for injection into the narrator evidence prompt.
        Returns empty string if no alarms.
        """
        if not self.alarms:
            return ""

        lines = ["--- KPI ALARM PRE-CHECK (DETERMINISTIC) ---"]
        for alarm in self.alarms:
            lines.append(
                f"{alarm.severity}: {alarm.signal} = {alarm.value:.4g}"
                f" [{alarm.evidence_id}] -- {alarm.label}."
            )

        if self.has_critical:
            lines.append(
                "\n\u26a0 ASSESSMENT CONSTRAINT: One or more CRITICAL KPI alarms are active."
                "\n  Your assessment MUST NOT describe the well as \"operating normally\","
                "\n  \"within acceptable ranges\", or \"functioning as expected\"."
                "\n  The assessment MUST reflect the alarm state listed above."
            )
        elif self.has_high:
            lines.append(
                "\n\u26a0 ASSESSMENT CONSTRAINT: One or more HIGH-severity KPI alarms are active."
                "\n  Your assessment must acknowledge the alarm conditions listed above."
            )

        return "\n".join(lines)


def check_kpi_alarms(evidence: "FormattedEvidence") -> KpiAlarmResult:
    """
    Scans FormattedEvidence.values against _ALARM_RULES.

    Multiple rules can fire for the same signal (e.g. anomaly_score triggers
    the CRITICAL rule exclusively -- we take only the highest-severity match
    per signal to avoid duplicate alarms).

    evidence: any object with a .values attribute containing items with
              .signal (str) and .raw (float|None) attributes.
    """
    result = KpiAlarmResult()

    # Index by signal for O(1) lookup -- take the first value seen per signal
    signal_index: dict[str, tuple[float, str]] = {}  # signal -> (raw, evidence_id)
    for fv in evidence.values:
        if fv.signal not in signal_index and fv.raw is not None:
            try:
                signal_index[fv.signal] = (float(fv.raw), fv.evidence_id)
            except (TypeError, ValueError):
                pass

    # Track which signals have already fired at a given severity so we don't
    # emit CRITICAL + HIGH for the same signal simultaneously.
    fired: dict[str, str] = {}  # signal -> highest severity fired

    for signal, condition_fn, severity, label in _ALARM_RULES:
        if signal not in signal_index:
            continue
        value, ev_id = signal_index[signal]
        if not condition_fn(value):
            continue

        # Only emit the highest severity per signal
        existing = fired.get(signal)
        severity_rank = {"CRITICAL": 3, "HIGH": 2, "WARN": 1}
        if existing and severity_rank.get(existing, 0) >= severity_rank.get(severity, 0):
            continue

        fired[signal] = severity
        # Remove any lower-severity alarm for this signal that was already added
        result.alarms = [a for a in result.alarms if a.signal != signal]
        result.alarms.append(
            KpiAlarm(
                signal=signal,
                value=value,
                severity=severity,
                label=label,
                evidence_id=ev_id,
            )
        )

    # Sort: CRITICAL first, then HIGH, then WARN, then by signal name
    _RANK = {"CRITICAL": 0, "HIGH": 1, "WARN": 2}
    result.alarms.sort(key=lambda a: (_RANK.get(a.severity, 9), a.signal))
    return result
