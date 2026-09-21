"""
Data Quality Gate for ESP Agentic Platform
Grounded in PHASE_4_Objective_Layer_Implementation_Plan_ESP_APM.docx §15

Performs pre-workflow data validation:
1. Signal completeness check against objective.required_signals
2. Telemetry freshness check (max threshold e.g. 300s)
3. Discloses gaps in output advisory confidence & disclosure message
4. Enforces Phase 4 policy: operating ranges from seed data are NOT approved limits
"""

import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

from src.schemas.contracts import DataQualityReport

logger = logging.getLogger(__name__)

# Canonical alias dictionary mapping required signal names to telemetry keys
SIGNAL_ALIASES = {
    "motor_temperature": ["motor_temperature", "r_motor_temp", "primary_thermal_metric", "temp"],
    "intake_pressure": ["intake_pressure", "pip", "r_intake_press"],
    "discharge_pressure": ["discharge_pressure", "pdp", "r_disch_press"],
    "flowline_pressure": ["flowline_pressure", "r_pit_003"],
    "frequency": ["frequency", "r_frequency", "speed"],
    "drive_current_average": ["drive_current_average", "current", "r_drv_curr_avg"],
    "vibration_x": ["vibration_x", "vibration", "r_vibration_x"],
    "tool_current": ["tool_current", "r_tool_current"],
    "intake_temperature": ["intake_temperature", "r_intake_temp"]
}


class DataQualityGate:
    """
    Data-Quality Gate service that enforces signal availability, freshness, and quality of data.
    """

    def __init__(self, max_age_seconds: float = 300.0):
        self.max_age_seconds = max_age_seconds

    def evaluate(
        self,
        required_signals: List[str],
        telemetry_data: Dict[str, Any],
        telemetry_timestamp: Optional[str] = None
    ) -> DataQualityReport:
        """
        Evaluate telemetry payload against required signals list.
        """
        missing = []
        stale = []
        freshness_sec = 0.0

        # Calculate data age if timestamp provided
        if telemetry_timestamp:
            try:
                # Remove trailing Z for parsing if ISO format
                ts_str = telemetry_timestamp.rstrip("Z")
                dt = datetime.fromisoformat(ts_str)
                age = (datetime.utcnow() - dt).total_seconds()
                freshness_sec = max(0.0, age)
            except Exception:
                freshness_sec = 0.0

        if freshness_sec > self.max_age_seconds:
            stale.extend(required_signals)

        # Check signal presence
        telemetry_keys_lower = {k.lower(): k for k in telemetry_data.keys()}
        for req_sig in required_signals:
            aliases = SIGNAL_ALIASES.get(req_sig, [req_sig])
            found = any(alias.lower() in telemetry_keys_lower for alias in aliases)
            if not found:
                missing.append(req_sig)

        # Determine status & gate pass/fail
        if not missing and freshness_sec <= self.max_age_seconds:
            status = "COMPLETE"
            gate_passed = True
            disclosure = "All required telemetry signals present and fresh."
        elif len(missing) < len(required_signals) and freshness_sec <= self.max_age_seconds:
            status = "PARTIAL"
            gate_passed = True  # Partial evidence allows advisory generation with disclosure
            disclosure = f"PARTIAL TELEMETRY: Missing required signals: {', '.join(missing)}. Confidence adjusted."
        else:
            status = "STALE" if freshness_sec > self.max_age_seconds else "INCOMPLETE"
            gate_passed = len(missing) < len(required_signals)  # Fail if ALL missing
            disclosure = f"DATA QUALITY GATE FAILURE: Telemetry is {status}. Missing: {', '.join(missing)}."

        logger.info(f"DataQualityGate evaluation: status={status}, missing={len(missing)}, gate_passed={gate_passed}")

        return DataQualityReport(
            status=status,
            missing_signals=missing,
            stale_signals=stale,
            freshness_seconds=freshness_sec,
            gate_passed=gate_passed,
            disclosure_message=disclosure,
            operating_range_note="Operating ranges from seed data are NOT approved limits."
        )
