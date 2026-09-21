"""
Minimal per-stage logging — plain log lines, not a metrics system.

One line per major hop: stage name, how long it took, and how it ended.
No counters, no histograms, no external exporter — just enough to grep
a log file and answer "which stage was slow / which stage failed" for a
given request, before a real metrics stack exists.
"""

import logging

logger = logging.getLogger("esp_stage")


def log_stage(stage: str, latency_ms: float, outcome: str, **extra) -> None:
    """
    Emits one structured log line for a completed stage.

    stage:      short stage name, e.g. "context_resolver", "router",
                "workflow_runner", "response_assembler"
    latency_ms: how long the stage took, in milliseconds
    outcome:    "OK" | "ERROR" | "CLARIFY" | "FALLBACK" | any short label
    extra:      optional key=value context (run_id, session_id, route, ...)
    """
    context = " ".join(f"{k}={v}" for k, v in extra.items() if v is not None)
    logger.info(
        "[STAGE] %s latency_ms=%.1f outcome=%s %s",
        stage,
        latency_ms,
        outcome,
        context,
    )
