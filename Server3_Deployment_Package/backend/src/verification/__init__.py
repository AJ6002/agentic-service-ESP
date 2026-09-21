"""
Verification / Gating Layer (§3 of Agent_Debugging/debug_methods.md).

Provides handoff verification so that mocked/hardcoded/fallback values produced by one
layer are DETECTED and TAGGED (LIVE vs FALLBACK) as they cross a layer boundary, instead
of being accepted silently and propagating downstream. The detected provenance is surfaced
live in every run (advisory provenance + audit trail), not just in an after-the-fact test.
"""

from src.verification.handoff import (
    HandoffStatus,
    HandoffVerdict,
    verify_telemetry,
    verify_model_output,
    verify_chart_series,
    TELEMETRY_FALLBACK,
    CHART_FALLBACK_PRODUCTION,
    CHART_FALLBACK_TDH,
)

__all__ = [
    "HandoffStatus",
    "HandoffVerdict",
    "verify_telemetry",
    "verify_model_output",
    "verify_chart_series",
    "TELEMETRY_FALLBACK",
    "CHART_FALLBACK_PRODUCTION",
    "CHART_FALLBACK_TDH",
]
