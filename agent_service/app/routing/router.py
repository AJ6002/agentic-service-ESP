import os
import re
from dataclasses import dataclass
from typing import Optional

from app.audit.audit_sink import record_audit
from app.contracts.routing import RouteDecision, RouterInput
from app.llm.calls import RouterOutputInvalid, route as llm_route
from app.llm.client import LLMUnavailableError
from app.routing.objective_registry import list_objectives

# Regex for common actuation requests (e.g., bump frequency, set Hz, change choke)
ACTUATION_REGEX = re.compile(r"\b(set|bump|change|increase|decrease|speed up)\b.*\b(\d+\s*hz|frequency|choke|speed)\b", re.IGNORECASE)

# Regex for definitional/explanatory intent -- matches before any diagnostic keyword scan.
# Mirrors Rule 0 in router_v1.txt: "explain what X is" must win over trigger words inside X.
# Regex for follow-up explanatory intent
FOLLOWUP_PATTERNS = re.compile(
    r"\b(why\s+(did\s+you|you)\s+(say|said|conclude|concluded|flag|flagged|choose|chose|diagnose|diagnosed)|"
    r"what\s+data\s+(did\s+you|was)\s+use|"
    r"explain\s+(that|the\s+graph|the\s+chart|your\s+reasoning|the\s+diagnosis)|"
    r"what\s+does\s+(that|the)\s+(mean|chart|graph|diagnosis|plot|trend)(\s+(mean|show|indicate|represent))?|"
    r"can\s+you\s+elaborate\s+on\s+that)\b",
    re.IGNORECASE,
)
AMBIGUOUS_FOLLOWUP_PATTERNS = re.compile(
    r"^\s*(why\s+did\s+that\s+happen|how\s+did\s+that\s+occur|what\s+happened\s+there)\??\s*$",
    re.IGNORECASE,
)

DEFINITIONAL_PATTERNS = re.compile(
    r"^\s*(what\s+(is|does|are|\'?s)\b|explain\s+(what\s+|how\s+)?|how\s+(do\s+i|can\s+i|to)\b|procedure\s+(for|to)|define\s+|describe\s+"
    r"|what(\'?s)?\s+the\s+(difference|meaning)|tell\s+me\s+(what|about)|what\s+causes)",
    re.IGNORECASE,
)


@dataclass
class RouteResult:
    decision: RouteDecision
    llm_available: bool = True
    fallback_used: bool = False


def _keyword_fallback_decision(router_input: RouterInput, deferred: list[str]) -> RouteDecision:
    """
    Deterministic keyword heuristic used ONLY when the LLM gateway is
    unavailable, or the LLM answered but never produced valid JSON even
    after a retry. This is a degraded, lower-quality stand-in for real
    classification, not a replacement for it — every caller of
    route_query() is told via RouteResult.llm_available=False /
    fallback_used=True that this path was used, so it can be surfaced to
    the user and to audit rather than silently trusted as normal routing.
    """
    # Ambiguity guard: "Why did that happen?" -> CLARIFY
    if AMBIGUOUS_FOLLOWUP_PATTERNS.search(router_input.raw_message):
        return RouteDecision(
            route="WORKFLOW",
            intent="diagnose",
            objective_id="OP03_FAULT_DIAGNOSIS",
            args={"asset_id": router_input.asset_id},
            confidence=0.4,
            deferred_intents=deferred,
            clarification_needed=True,
            clarify_reason="CLARIFY",
            clarify_slot="followup_or_new",
            clarify_options=["Explain previous diagnosis", "Run new diagnosis on current telemetry"],
        )

    # Follow-up intent check: past-tense explanatory inquiries
    if FOLLOWUP_PATTERNS.search(router_input.raw_message):
        return RouteDecision(
            route="FOLLOW_UP",
            intent="explain_prior",
            objective_id=None,
            args={"asset_id": router_input.asset_id},
            confidence=0.9,
            deferred_intents=deferred,
            clarification_needed=False,
        )

    # Rule 0 guard: definitional intent wins over any diagnostic keyword when no asset is named.
    # Mirrors router_v1.txt Rule 0 so the fallback cannot misclassify during LLM outages.
    if router_input.asset_id is None and DEFINITIONAL_PATTERNS.search(router_input.raw_message):
        return RouteDecision(
            route="SIMPLE",
            intent="general_inquiry",
            objective_id="OP06_KNOWLEDGE_LOOKUP",
            args={},
            confidence=0.9,
            deferred_intents=deferred,
            clarification_needed=False,
        )

    raw_lower = router_input.raw_message.lower()
    needs_asset_clarify = (
        router_input.asset_id is None
        and any(w in raw_lower for w in ["trip", "status", "vibration", "temp", "amps", "hz", "pressure", "why did", "health", "early warning", "warning", "anomaly", "history", "runtime"])
    )

    if needs_asset_clarify:
        obj_id = "OP03_FAULT_DIAGNOSIS"
        if any(w in raw_lower for w in ["health", "rul", "degradation", "condition"]):
            obj_id = "OP04_HEALTH_ASSESSMENT"
        elif any(w in raw_lower for w in ["early warning", "warning sign", "anomaly"]):
            obj_id = "OP05_EARLY_WARNING"
        elif any(w in raw_lower for w in ["history", "operational history", "runtime", "historical"]):
            obj_id = "OP14_OPERATIONAL_HISTORY"
        elif any(w in raw_lower for w in ["decline", "drop in production", "dropped", "producing less", "production drop", "production decline", "production analysis"]):
            obj_id = "OP02_PRODUCTION_DECLINE_RCA" 
        elif any(w in raw_lower for w in ["status", "reading", "sensor", "telemetry"]):
            obj_id = "OP01_CURRENT_STATUS"

        return RouteDecision(
            route="WORKFLOW",
            intent="diagnose",
            objective_id=obj_id,
            args={"asset_id": None},
            confidence=0.5,
            deferred_intents=deferred,
            clarification_needed=True,
            clarify_reason="CLARIFY",
            clarify_slot="asset_id",
            clarify_options=["FS-17", "FS-91", "FNW-01", "FWS-06"],
        )
    if any(w in raw_lower for w in ["decline", "drop in production", "dropped", "producing less", "production drop", "production decline", "production analysis"]):
        needs_clarify = not bool(router_input.asset_id)
        return RouteDecision(
            route="WORKFLOW",
            intent="decline_rca",
            objective_id="OP02_PRODUCTION_DECLINE_RCA",
            args={"asset_id": router_input.asset_id},
            confidence=0.5 if not needs_clarify else 0.4,
            deferred_intents=deferred,
            clarification_needed=needs_clarify,
            clarify_reason="CLARIFY" if needs_clarify else None,
            clarify_slot="asset_id" if needs_clarify else None,
            clarify_options=["FS-17", "FS-91", "FNW-01", "FWS-06"] if needs_clarify else [],
        )
    if any(w in raw_lower for w in ["health", "condition", "rul", "remaining useful", "degradation"]):
        needs_clarify = not bool(router_input.asset_id)
        return RouteDecision(
            route="WORKFLOW",
            intent="health",
            objective_id="OP04_HEALTH_ASSESSMENT",
            args={"asset_id": router_input.asset_id},
            confidence=0.5 if not needs_clarify else 0.4,
            deferred_intents=deferred,
            clarification_needed=needs_clarify,
            clarify_reason="CLARIFY" if needs_clarify else None,
            clarify_slot="asset_id" if needs_clarify else None,
            clarify_options=["FS-17", "FS-91", "FNW-01", "FWS-06"] if needs_clarify else [],
        )
    if any(w in raw_lower for w in ["early warning", "warning sign", "anomaly", "subtle"]):
        needs_clarify = not bool(router_input.asset_id)
        return RouteDecision(
            route="WORKFLOW",
            intent="early_warning",
            objective_id="OP05_EARLY_WARNING",
            args={"asset_id": router_input.asset_id},
            confidence=0.5 if not needs_clarify else 0.4,
            deferred_intents=deferred,
            clarification_needed=needs_clarify,
            clarify_reason="CLARIFY" if needs_clarify else None,
            clarify_slot="asset_id" if needs_clarify else None,
            clarify_options=["FS-17", "FS-91", "FNW-01", "FWS-06"] if needs_clarify else [],
        )
    if any(w in raw_lower for w in ["history", "operational history", "historical", "past performance", "runtime hours", "runtime"]):
        needs_clarify = not bool(router_input.asset_id)
        return RouteDecision(
            route="WORKFLOW",
            intent="history",
            objective_id="OP14_OPERATIONAL_HISTORY",
            args={"asset_id": router_input.asset_id},
            confidence=0.5 if not needs_clarify else 0.4,
            deferred_intents=deferred,
            clarification_needed=needs_clarify,
            clarify_reason="CLARIFY" if needs_clarify else None,
            clarify_slot="asset_id" if needs_clarify else None,
            clarify_options=["FS-17", "FS-91", "FNW-01", "FWS-06"] if needs_clarify else [],
        )
    if any(w in raw_lower for w in ["trip", "alarm", "fault", "why did", "recheck", "re-check", "rerun", "re-run", "diagnose", "diagnosis", "troubleshoot", "troubleshooting", "wrong", "issue", "problem"]):
        needs_clarify = not bool(router_input.asset_id)
        return RouteDecision(
            route="WORKFLOW",
            intent="diagnose",
            objective_id="OP03_FAULT_DIAGNOSIS",
            args={"asset_id": router_input.asset_id},
            confidence=0.5 if not needs_clarify else 0.4,
            deferred_intents=deferred,
            clarification_needed=needs_clarify,
            clarify_reason="CLARIFY" if needs_clarify else None,
            clarify_slot="asset_id" if needs_clarify else None,
            clarify_options=["FS-17", "FS-91", "FNW-01", "FWS-06"] if needs_clarify else [],
        )
    if any(w in raw_lower for w in ["status", "reading", "sensor", "telemetry"]):
        needs_clarify = not bool(router_input.asset_id)
        return RouteDecision(
            route="WORKFLOW",
            intent="status",
            objective_id="OP01_CURRENT_STATUS",
            args={"asset_id": router_input.asset_id},
            confidence=0.5 if not needs_clarify else 0.4,
            deferred_intents=deferred,
            clarification_needed=needs_clarify,
            clarify_reason="CLARIFY" if needs_clarify else None,
            clarify_slot="asset_id" if needs_clarify else None,
            clarify_options=["FS-17", "FS-91", "FNW-01", "FWS-06"] if needs_clarify else [],
        )
    return RouteDecision(
        route="SIMPLE",
        intent="general_inquiry",
        objective_id="OP06_KNOWLEDGE_LOOKUP",
        args={},
        confidence=0.5,
        deferred_intents=deferred,
        clarification_needed=False,
    )


def _build_context_block(router_input: RouterInput, available_objectives: list[str]) -> str:
    """
    Pre-formats the resolved-context portion of the router's user turn.
    Kept here (routing-domain shape) rather than in app/llm/calls.py
    (prompting/parsing-only), so the LLM call module stays domain-agnostic
    about what a RouterInput even is.
    """
    return (
        f"Resolved Asset: {router_input.asset_id} (Source: {router_input.asset_source})\n"
        f"Available Objectives: {available_objectives}\n"
        f"Candidate Tools: {router_input.candidate_tools}"
    )


async def route_query(router_input: RouterInput) -> RouteDecision:
    """
    Back-compat wrapper — returns just the RouteDecision.
    Prefer route_query_full() for callers that need to know whether the
    LLM was actually reachable.
    """
    result = await route_query_full(router_input)
    return result.decision


async def route_query_full(router_input: RouterInput) -> RouteResult:
    conf_threshold = float(os.getenv("CONFIDENCE_THRESHOLD", "0.6"))
    available_objectives = router_input.candidate_objectives or list_objectives()
    context_block = _build_context_block(router_input, available_objectives)

    # Check for multi-intent actuation in the message.
    deferred: list[str] = []
    if ACTUATION_REGEX.search(router_input.raw_message):
        deferred.append("actuation_set_frequency")

    decision: Optional[RouteDecision] = None
    llm_available = True

    try:
        decision = await llm_route(router_input.raw_message, context_block)
        if deferred and not decision.deferred_intents:
            decision.deferred_intents = deferred
        if decision.confidence < conf_threshold:
            decision.clarification_needed = True
            decision.clarify_reason = "CLARIFY"
        # Rule 0 guard: Definitional intent with no asset in text must route to SIMPLE (OP06)
        from app.context.resolver import WELL_ID_REGEX
        is_telemetry_ask = any(w in router_input.raw_message.lower() for w in ['telemetry', 'status', 'reading', 'sensor', 'live'])
        if DEFINITIONAL_PATTERNS.search(router_input.raw_message) and not WELL_ID_REGEX.search(router_input.raw_message) and not (router_input.asset_id and is_telemetry_ask):
            decision.route = "SIMPLE"
            decision.intent = "general_inquiry"
            decision.objective_id = "OP06_KNOWLEDGE_LOOKUP"
            decision.args = {}
            decision.clarification_needed = False
            decision.clarify_reason = None
            decision.clarify_slot = None
            decision.clarify_options = []
            decision.confidence = 0.95

        # Health query disambiguation: queries mentioning health/condition on an asset route to OP04, not OP01
        if any(w in router_input.raw_message.lower() for w in ["health", "degradation", "condition"]) and router_input.asset_id:
            if decision.objective_id == "OP01_CURRENT_STATUS":
                decision.objective_id = "OP04_HEALTH_ASSESSMENT"
                decision.intent = "health"

        # Ambiguous follow-up guard: "Why did that happen?" -> CLARIFY
        if AMBIGUOUS_FOLLOWUP_PATTERNS.search(router_input.raw_message):
            decision.route = "WORKFLOW"
            decision.intent = "diagnose"
            decision.objective_id = "OP03_FAULT_DIAGNOSIS"
            decision.args = {"asset_id": router_input.asset_id}
            decision.confidence = 0.4
            decision.clarification_needed = True
            decision.clarify_reason = "CLARIFY"
            decision.clarify_slot = "followup_or_new"
            decision.clarify_options = ["Explain previous diagnosis", "Run new diagnosis on current telemetry"]

        # Deterministic follow-up guard: questions referencing past statement/graph/data -> FOLLOW_UP
        elif FOLLOWUP_PATTERNS.search(router_input.raw_message):
            decision.route = "FOLLOW_UP"
            decision.intent = "explain_prior"
            decision.objective_id = None
            decision.args = {"asset_id": router_input.asset_id}
            decision.confidence = 0.95
            decision.clarification_needed = False
            decision.clarify_reason = None
            decision.clarify_slot = None
            decision.clarify_options = []
    except LLMUnavailableError:
        llm_available = False
    except RouterOutputInvalid as ex:
        # LLM responded (available), but never produced valid JSON even
        # after the retry inside llm_route() — a router/prompt defect,
        # not an outage. Flagged distinctly from llm_available=False.
        record_audit("router_malformed_output", payload={"error": str(ex)})
    except Exception as ex:
        llm_available = False
        record_audit("router_llm_exception", payload={"error": str(ex)})

    fallback_used = decision is None
    if decision is None:
        decision = _keyword_fallback_decision(router_input, deferred)

    record_audit(
        event_type="router_decided",
        payload={
            "route": decision.route,
            "intent": decision.intent,
            "objective_id": decision.objective_id,
            "confidence": decision.confidence,
            "clarification_needed": decision.clarification_needed,
            "deferred_intents": decision.deferred_intents,
            "llm_available": llm_available,
            "fallback_used": fallback_used,
        },
    )

    return RouteResult(decision=decision, llm_available=llm_available, fallback_used=fallback_used)
