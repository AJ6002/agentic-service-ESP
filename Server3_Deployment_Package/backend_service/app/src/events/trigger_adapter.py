"""
Event-to-LangGraph Trigger Adapter
Grounded in Phase 6 Event-Driven Architecture Spec §12, §13, §27
"""

import logging
from typing import Dict, Any, Optional

from shared.schemas.event import ESPEvent
from src.schemas.advisory import StandardAdvisoryPayload
from src.agent.objective_registry import ObjectiveRegistry
from src.events.event_objective_router import EventObjectiveRouter

logger = logging.getLogger(__name__)


class EventTriggerAdapter:
    """
    Adapter executing LangGraph workflow triggered by an actionable ESPEvent.
    """

    def __init__(self, registry: Optional[ObjectiveRegistry] = None):
        self.router = EventObjectiveRouter(registry)

    def execute_event_workflow(self, event: ESPEvent) -> Optional[StandardAdvisoryPayload]:
        """
        Map event to target Objective ID and execute supervisor workflow.
        """
        return self.router.route_and_execute(event)
