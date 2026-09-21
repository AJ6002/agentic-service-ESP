"""
LLM Observability & Audit Tracing — Phase 10: LLM Layer Architecture
Grounded in ESP APM LLM Architecture Design §9

Records structured, auditable traces for every LLM invocation:
  - run_id, agent_id, objective_id
  - model, model_version, prompt_version
  - prompt_tokens, completion_tokens, total_tokens
  - latency_ms, finish_reason, is_mock
  - validation_passed, repair_attempts
  - error_message

Ensures full compliance with industrial APM audit requirements.
"""

import json
import logging
import time
import uuid
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class LLMTraceRecord:
    trace_id: str = field(default_factory=lambda: f"TRACE-LLM-{uuid.uuid4().hex[:8]}")
    timestamp: str = field(default_factory=lambda: time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
    run_id: str = "RUN-001"
    agent_id: str = "AgentJane"
    objective_id: str = "OP01_PRODUCTION_DECLINE"
    model_name: str = "qwen2.5:3b"
    prompt_version: str = "v1.0"
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    latency_ms: float = 0.0
    finish_reason: str = "stop"
    is_mock: bool = False
    validation_passed: bool = True
    repair_attempts: int = 0
    tool_calls_count: int = 0
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class LLMObservabilityTracer:
    """
    In-memory audit tracer for LLM invocations.
    Records trace records and provides retrieval methods.
    """

    def __init__(self):
        self._traces: List[LLMTraceRecord] = []

    def record_trace(self, trace: LLMTraceRecord) -> LLMTraceRecord:
        """Store trace record and log structured metrics."""
        self._traces.append(trace)
        logger.info(
            f"LLMObservabilityTracer: [TRACE {trace.trace_id}] "
            f"model={trace.model_name} tokens={trace.total_tokens} "
            f"latency={trace.latency_ms:.0f}ms valid={trace.validation_passed} "
            f"repairs={trace.repair_attempts}"
        )
        return trace

    def get_traces_for_run(self, run_id: str) -> List[LLMTraceRecord]:
        """Fetch all LLM trace records for a specific run_id."""
        return [t for t in self._traces if t.run_id == run_id]

    def get_all_traces(self) -> List[LLMTraceRecord]:
        """Return all recorded LLM trace records."""
        return list(self._traces)

    def get_summary_stats(self) -> Dict[str, Any]:
        """Return aggregated operational metrics across all LLM runs."""
        if not self._traces:
            return {"total_calls": 0, "total_tokens": 0, "avg_latency_ms": 0.0}

        total_tokens = sum(t.total_tokens for t in self._traces)
        avg_latency = sum(t.latency_ms for t in self._traces) / len(self._traces)
        valid_count = sum(1 for t in self._traces if t.validation_passed)

        return {
            "total_calls": len(self._traces),
            "total_tokens": total_tokens,
            "avg_latency_ms": round(avg_latency, 2),
            "validation_success_rate": round(valid_count / len(self._traces), 3),
        }


# Global tracer instance
tracer = LLMObservabilityTracer()
