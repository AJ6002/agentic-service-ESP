"""
Event-to-Supervisor Objective Router (Phase 6 → Phase 7 Bridge)
Grounded in ESP_APM_PHASE_7_LangGraph_Supervisor_MultiAgent_Architecture_Design.docx §8, §23, §24
"""

import logging
from typing import Optional, Dict, Any

from shared.schemas.event import ESPEvent
from src.schemas.advisory import StandardAdvisoryPayload
from src.agent.objective_registry import ObjectiveRegistry
from src.agent.supervisor.state import create_initial_agent_state
from src.agent.supervisor.graph import supervisor_graph

logger = logging.getLogger(__name__)


class EventObjectiveRouter:
    """
    Bridge connecting Phase 6 EventProcessor actionable streams to the Phase 7 LangGraph Supervisor.
    """

    def __init__(self, registry: Optional[ObjectiveRegistry] = None):
        self.registry = registry or ObjectiveRegistry()

    def route_and_execute(self, event: ESPEvent) -> Optional[StandardAdvisoryPayload]:
        """
        Map event to Level-2 objective ID and trigger Supervisor Graph execution.
        """
        target_obj_id = event.payload.get("target_objective_id") or self.registry.resolve_event_mapping(event.event_type)

        if not target_obj_id:
            logger.warning(f"EventObjectiveRouter: Event '{event.event_id}' (type={event.event_type}) has no target objective mapping.")
            return None

        logger.info(f"EventObjectiveRouter: Routing event '{event.event_id}' -> Supervisor objective '{target_obj_id}' (asset={event.asset_id})")

        initial_state = create_initial_agent_state(
            run_id=f"RUN-EVT-{event.event_id}",
            asset_id=event.asset_id,
            user_query=f"Proactive evaluation triggered by event '{event.event_type}' (Severity: {event.severity.value})",
            event_id=event.event_id,
            objective_id=target_obj_id,
            trigger_type="event",
            correlation_id=event.correlation_id or event.event_id
        )

        if event.payload.get("telemetry"):
            initial_state["context"]["telemetry"] = event.payload["telemetry"]

        final_state = supervisor_graph.invoke(initial_state)
        advisory_dict = final_state.get("advisory_draft")

        if advisory_dict:
            advisory = StandardAdvisoryPayload(**advisory_dict)
            advisory.provenance.append(f"Event ID: {event.event_id}")
            advisory.provenance.append(f"Correlation ID: {event.correlation_id}")
            logger.info(f"EventObjectiveRouter: Supervisor successfully generated advisory '{advisory.advisory_id}' for event '{event.event_id}'")
            return advisory

        logger.error(f"EventObjectiveRouter: Supervisor execution failed for event '{event.event_id}'")
        return None
