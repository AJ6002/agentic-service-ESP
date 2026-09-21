"""
V2 Architecture - Agent Contracts & Planning Subsystem
"""

import json
from pathlib import Path
from typing import Any, Dict, List

from .plan_schema import (
    PlanStepStatus,
    PlanStep,
    PlanArtifact,
    PlanApprovalRequest,
)
from .plan_repository import PlanRepository
from .orchestrator import ToolCall, route_query
from .plan_node import create_execution_plan
from .approval_gate_node import approval_gate
from .specialist_executor import SpecialistExecutor, execute_plan_steps
from .section_registry import (
    ALLOWED_SECTIONS_PER_OBJECTIVE,
    DEFAULT_ALLOWED_SECTIONS,
    ALL_KNOWN_SECTIONS,
    is_section_allowed,
    filter_advisory_sections,
)
from .synthesis_node import synthesize_advisory
from .tools import get_agent_profile, format_agent_profile_narrative

TOOL_DEFINITIONS_PATH: Path = Path(__file__).parent / "tool_definitions.json"


def get_tool_definitions() -> List[Dict[str, Any]]:
    """Load the canonical 17 tool definitions in OpenAI schema format."""
    with open(TOOL_DEFINITIONS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


__all__ = [
    "PlanStepStatus",
    "PlanStep",
    "PlanArtifact",
    "PlanApprovalRequest",
    "PlanRepository",
    "TOOL_DEFINITIONS_PATH",
    "get_tool_definitions",
    "ToolCall",
    "route_query",
    "create_execution_plan",
    "approval_gate",
    "SpecialistExecutor",
    "execute_plan_steps",
    "ALLOWED_SECTIONS_PER_OBJECTIVE",
    "DEFAULT_ALLOWED_SECTIONS",
    "ALL_KNOWN_SECTIONS",
    "is_section_allowed",
    "filter_advisory_sections",
    "synthesize_advisory",
    "get_agent_profile",
    "format_agent_profile_narrative",
]
