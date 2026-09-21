"""
User Entry Adapter for Phase 7 Supervisor Graph
Grounded in ESP_APM_PHASE_7_LangGraph_Supervisor_MultiAgent_Architecture_Design.docx §8, §24
"""

import logging
from datetime import datetime
from typing import Optional, Dict, Any

from src.schemas.advisory import StandardAdvisoryPayload
from src.agent.intent_router import IntentRouter
from src.agent.supervisor.state import create_initial_agent_state
from src.agent.supervisor.graph import supervisor_graph
from src.memory.conversation_store import ConversationStore
from src.memory.well_memory import WellEpisodicMemoryStore

logger = logging.getLogger(__name__)


class ClarificationNeeded(Exception):
    """
    B3.T2 — Raised by UserEntryAdapter.run() when the graph hit an interrupt()
    inside clarification_node and is waiting for the operator's answer.

    Attributes:
        question:   The question text to display to the operator.
        thread_id:  The LangGraph thread_id to pass to Command(resume=) on the next call.
        asset_id:   The (possibly unresolved) asset_id at the time of interrupt.
    """
    def __init__(self, question: str, thread_id: str, asset_id: str):
        super().__init__(question)
        self.question = question
        self.thread_id = thread_id
        self.asset_id = asset_id


class UserEntryAdapter:
    """
    Adapter processing HTTP REST / MCP user queries through the Phase 7 LangGraph Supervisor.
    """

    def __init__(
        self,
        intent_router: Optional[IntentRouter] = None,
        conversation_store: Optional[ConversationStore] = None,
        well_memory_store: Optional[WellEpisodicMemoryStore] = None,
    ):
        self.intent_router = intent_router or IntentRouter()
        self.conv_store = conversation_store or ConversationStore()
        self.well_memory = well_memory_store or WellEpisodicMemoryStore()

    def run(
        self,
        user_query: str,
        asset_id: Optional[str] = None,
        request_id: str = "REQ-001",
        tenant_id: Optional[str] = None,
        session_id: Optional[str] = None,
        telemetry_override: Optional[Dict[str, Any]] = None,
    ) -> StandardAdvisoryPayload:
        """
        Classify intent, initialize AgentState, and execute Supervisor Graph.

        A3.T1 additions:
        - When asset_id is blank/None, resolve from ConversationStore.get_last_well().
        - Build conversation_context and pass it into route().
        - Thread recent_turns into state context.history so the LLM narrative sees them.
        - Persist user and assistant turns to ConversationStore if session_id is active.

        B1.T2 addition:
        - Pass thread_id in LangGraph config (= session_id if set, else request_id).
          This enables MemorySaver cross-turn checkpointing and interrupt/resume.

        B3.T2 addition:
        - If the graph hits interrupt() inside clarification_node, raises ClarificationNeeded
          instead of returning an advisory. The BFF catches this and streams the question.
        """
        # ── Resolve operational context via canonical resolver (Zero Split-Brain) ──
        from src.agent.context import OperationalContextResolver
        op_ctx = OperationalContextResolver.resolve(
            user_query=user_query,
            view_context={"asset_id": asset_id, "selected_asset": asset_id},
            session_id=session_id,
            conv_store=self.conv_store,
        )
        resolved_asset_id = op_ctx.target_asset or (asset_id if asset_id not in ("UNKNOWN", "None", "") else "")
        recent_turns: list = []
        last_objective: Optional[str] = None

        if session_id:
            recent_turns = self.conv_store.get_history(session_id, limit=10)
            # Most recent assistant turn's intent becomes last_objective
            for turn in reversed(recent_turns):
                if turn.get("role") == "assistant" and turn.get("intent_detected"):
                    last_objective = turn["intent_detected"]
                    break
            # Record user turn before running so history is available this run
            self.conv_store.append(
                session_id=session_id,
                role="user",
                content=user_query,
                well_id=resolved_asset_id or None,
            )

        conversation_context: Optional[Dict[str, Any]] = None
        if session_id:
            conversation_context = {
                "last_well": resolved_asset_id or None,
                "last_objective": last_objective,
                "recent_turns": recent_turns,
            }

        # ── Route intent (A2 signature — backwards-compat when no ctx) ────────
        route_result = self.intent_router.route(
            user_query,
            conversation_context=conversation_context,
        )
        obj_id, conf, path, is_ambiguous = route_result[0], route_result[1], route_result[2], route_result[3]
        obj_def = self.intent_router.registry.get(obj_id)
        if obj_def and obj_def.scope == "fleet":
            resolved_asset_id = "FLEET"
        elif obj_id == "CLARIFICATION":
            resolved_asset_id = "UNKNOWN"

        logger.info(
            "UserEntryAdapter: Query '%s' -> objective '%s' via %s (conf=%.2f, ambiguous=%s) session=%s",
            user_query[:40], obj_id, path, conf, is_ambiguous, session_id or "none",
        )

        initial_state = create_initial_agent_state(
            run_id=request_id,
            asset_id=resolved_asset_id or "UNKNOWN",
            user_query=user_query,
            objective_id=obj_id,
            trigger_type="user",
        )
        # Thread conversation history into state so the LLM narrative node can see it
        initial_state["context"]["history"] = recent_turns
        # Thread conversation_context into state so graph's resolve_objective_node can read it
        initial_state["context"]["conversation_context"] = conversation_context  # type: ignore[index]
        # C1.T2: Thread episodic well memory into state for CompactContextBuilder
        if resolved_asset_id:
            initial_state["context"]["episodic_memory"] = self.well_memory.get_memory(resolved_asset_id)
        if telemetry_override:
            initial_state["context"]["telemetry_override"] = telemetry_override
        initial_state["is_ambiguous"] = is_ambiguous

        # B1.T2: thread_id = session_id when available; fall back to request_id.
        # This is the LangGraph checkpoint key — must be stable across turns for resume to work.
        thread_id = session_id or request_id
        lg_config = {"configurable": {"thread_id": thread_id}}

        final_state = supervisor_graph.invoke(initial_state, config=lg_config)

        # B3.T2: Detect interrupt — LangGraph surfaces interrupts via __interrupt__ in the state
        interrupts = final_state.get("__interrupt__", ())
        if interrupts:
            interrupt_val = interrupts[0].value if hasattr(interrupts[0], "value") else interrupts[0]
            question = interrupt_val.get("question", str(interrupt_val)) if isinstance(interrupt_val, dict) else str(interrupt_val)
            logger.info("UserEntryAdapter: Graph interrupted for clarification (thread_id=%s)", thread_id)
            if session_id:
                self.conv_store.append(
                    session_id=session_id,
                    role="assistant",
                    content=question[:500],
                    well_id=None,
                    intent="CLARIFICATION",
                )
            raise ClarificationNeeded(question=question, thread_id=thread_id, asset_id=resolved_asset_id or "UNKNOWN")

        advisory_dict = final_state.get("advisory_draft")

        if advisory_dict:
            advisory = StandardAdvisoryPayload(**advisory_dict)
            advisory.provenance.append(f"User Entry Adapter v7.0 ({path})")
            advisory._route_result = route_result
            if session_id:
                agent_content = (getattr(advisory, "assessment", None)
                                 or getattr(advisory, "diagnosis", None)
                                 or advisory.objective_id)
                self.conv_store.append(
                    session_id=session_id,
                    role="assistant",
                    content=str(agent_content)[:500],
                    well_id=resolved_asset_id or None,
                    intent=advisory.objective_id,
                )
            # C1.T1: Record completed advisory into per-well episodic memory
            if resolved_asset_id:
                self.well_memory.record_advisory(resolved_asset_id, advisory)
            return advisory

        raise RuntimeError(f"Supervisor Graph execution failed to produce advisory for request '{request_id}'.")

    def resume(
        self,
        thread_id: str,
        operator_answer: str,
        session_id: Optional[str] = None,
        asset_id: Optional[str] = None,
    ) -> StandardAdvisoryPayload:
        """
        B3.T2 — Resume a paused graph run after the operator answered a clarification question.
        Passes Command(resume=operator_answer) to LangGraph; the graph continues from
        the interrupt() call inside clarification_node.
        """
        from langgraph.types import Command  # local import avoids circular at module level

        logger.info(
            "UserEntryAdapter.resume: thread_id=%s answer='%s...'",
            thread_id, operator_answer[:40],
        )
        lg_config = {"configurable": {"thread_id": thread_id}}
        final_state = supervisor_graph.invoke(
            Command(resume=operator_answer),
            config=lg_config,
        )

        # Detect nested interrupt (shouldn't happen but guard anyway)
        interrupts = final_state.get("__interrupt__", ())
        if interrupts:
            interrupt_val = interrupts[0].value if hasattr(interrupts[0], "value") else interrupts[0]
            question = interrupt_val.get("question", str(interrupt_val)) if isinstance(interrupt_val, dict) else str(interrupt_val)
            raise ClarificationNeeded(question=question, thread_id=thread_id, asset_id=asset_id or "")

        advisory_dict = final_state.get("advisory_draft")
        if advisory_dict:
            advisory = StandardAdvisoryPayload(**advisory_dict)
            advisory.provenance.append("User Entry Adapter v7.0 (resume)")
            if session_id:
                agent_content = (getattr(advisory, "assessment", None)
                                 or getattr(advisory, "diagnosis", None)
                                 or advisory.objective_id)
                self.conv_store.append(
                    session_id=session_id,
                    role="assistant",
                    content=str(agent_content)[:500],
                    well_id=asset_id or None,
                    intent=advisory.objective_id,
                )
            if asset_id:
                self.well_memory.record_advisory(asset_id, advisory)
            return advisory

        raise RuntimeError(f"Supervisor Graph resume failed to produce advisory for thread '{thread_id}'.")
