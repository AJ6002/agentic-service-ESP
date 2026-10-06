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
    r"what\s+data\s+(did\s+you|was)\s+(use|used|look\s+at|looked\s+at|check|checked|review|reviewed|rely\s+on|consult|consulted)|"
    r"how\s+did\s+you\s+(figure\s+that\s+out|come\s+to\s+that|arrive\s+at\s+that)|"
    r"explain\s+(the\s+graph|the\s+chart|your\s+reasoning|the\s+diagnosis)|"
    r"what\s+does\s+(that|the)\s+(mean|chart|graph|diagnosis|plot|trend)(\s+(mean|show|indicate|represent))?|"
    r"can\s+you\s+elaborate\s+on\s+that)\b",
    re.IGNORECASE,
)
AMBIGUOUS_FOLLOWUP_PATTERNS = re.compile(
    r"^\s*(why\s+did\s+that\s+happen|how\s+did\s+that\s+occur|what\s+happened\s+there|explain\s+that)\??\s*$",
    re.IGNORECASE,
)

DEFINITIONAL_PATTERNS = re.compile(
    r"^\s*(what\s+(is|does|are|\'?s)\b|explain\s+(what\s+|how\s+)?|how\s+(do\s+i|can\s+i|to)\b|procedure\s+(for|to)|define\s+|describe\s+"
    r"|what(\'?s)?\s+the\s+(difference|meaning)|tell\s+me\s+(what|about)|what\s+causes)",
    re.IGNORECASE,
)

GREETING_PATTERNS = re.compile(
    r"^\s*(hi|hii|hello|hey|greetings|good\s+(morning|afternoon|evening)|howdy)\b",
    re.IGNORECASE,
)

IDENTITY_PATTERNS = re.compile(
    r"\b(who\s+(are\s+you|are\s+u)|what\s+(are\s+you|are\s+u)|what\s+(do\s+you|do\s+u)\s+do|"
    r"what\s+(can\s+you|can\s+u)\s+do|what\s+(can\'t\s+you|cannot\s+you|can\s+you\s+not)\s+do|"
    r"what\s+are\s+your\s+(limits|limitations|capabilities|features|functions)|"
    r"what\s+(features|capabilities)\s+do\s+you\s+have|"
    r"about\s+(yourself|this\s+assistant|this\s+system|this\s+copilot)|"
    r"explain\s+your\s+(role|architecture|purpose|capabilities))\b",
    re.IGNORECASE,
)

PLATFORM_GUIDE_PATTERNS = re.compile(
    r"\b("
    r"what\s+(is|does)\s+(this|the)\s+(page|screen|tab|widget|chart|view|dashboard|interface)|"
    r"explain\s+(this|the)\s+(page|screen|tab|widget|chart|view|dashboard|interface)|"
    r"how\s+do\s+i\s+(get\s+to|find|navigate\s+to)|"
    r"where\s+(is|can\s+i\s+find)\b(?!.*\b(well|fs-\d+|fnw-\d+|fws-\d+|ulfa-\d+)\b)|"
    r"what\s+is\s+the\s+.*(page|screen|tab|widget|view|dashboard|interface)|"
    r"what\s+does\s+the\s+subsystem\s+equalizer\s+show|"
    r"what\s+(does|is)\s+the\s+.*preset|" 
    r"what\s+does\s+.*preset\s+simulate|" 
    r"what\s+(does|is)\s+the\s+.*equalizer|"
    r"how\s+do\s+i\s+get\s+to\s+[a-zA-Z0-9_\-]+"
    r")\b",
    re.IGNORECASE,
)

FLEET_PATTERNS = re.compile(
    r"\b("
    r"which\s+wells?\b|"
    r"list\s+(all\s+)?wells\b|"
    r"rank\s+(the\s+)?(wells|fleet)\b|"
    r"fleet\s+(summary|health|production|status|overview|inventory|opportunity)\b|"
    r"show\s+(me\s+)?fleet(\s+summary|\s+status|\s+overview)?\b|"
    r"how\s+many\s+wells\b"
    r")",
    re.IGNORECASE,
)

def _resolve_fleet_objective(raw_message: str) -> tuple[str, str]:
    msg = raw_message.lower()
    if any(w in msg for w in ['underperform', 'opportunity', 'rank', 'ranking', 'potential', 'recovery', 'defer', 'deferment', 'optimize', 'gain']):
        return 'OP09_FLEET_PRODUCTION_OPTIMIZATION', 'fleet_optimization'
    if any(w in msg for w in ['executive', 'kpi ribbon', 'leadership', 'management report', 'executive report']):
        return 'OP13_FLEET_EXECUTIVE_REPORT', 'fleet_executive_report'
    return 'OP08_FLEET_INVENTORY', 'fleet_inventory'




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
    raw_lower = router_input.raw_message.lower()

    # Greeting guard: conversational greetings -> SIMPLE direct answer
    if GREETING_PATTERNS.search(router_input.raw_message):
        return RouteDecision(
            route="SIMPLE",
            scope="GLOBAL",
            intent="greeting",
            objective_id=None,
            args={},
            confidence=0.95,
            deferred_intents=deferred,
            clarification_needed=False,
        )

    # Identity / self-knowledge guard: questions about the agent itself -> IDENTITY
    if IDENTITY_PATTERNS.search(router_input.raw_message):
        return RouteDecision(
            route="IDENTITY",
            scope="GLOBAL",
            intent="self_knowledge",
            objective_id=None,
            args={},
            confidence=1.0,
            deferred_intents=deferred,
            clarification_needed=False,
        )

    # Fleet guard: fleet-wide / multi-well queries -> WORKFLOW with scope="FLEET"
    if FLEET_PATTERNS.search(router_input.raw_message) and not router_input.asset_id:
        fleet_obj, fleet_intent = _resolve_fleet_objective(router_input.raw_message)
        return RouteDecision(
            route="WORKFLOW",
            scope="FLEET",
            intent=fleet_intent,
            objective_id=fleet_obj,
            args={"user_query": router_input.raw_message},
            confidence=0.95,
            deferred_intents=deferred,
            clarification_needed=False,
        )

    # Platform guide guard: UI elements, routes, components -> OP15_PLATFORM_GUIDE
    is_platform_ask = bool(PLATFORM_GUIDE_PATTERNS.search(router_input.raw_message)) or bool(
        router_input.selected_route and re.search(r"\b(explain|what is|what does|show)\s+(this|the)\s+(chart|plot|graph|screen|page|widget|view|dashboard)\b", router_input.raw_message, re.IGNORECASE)
    )
    if is_platform_ask:
        op15_args = {"query": router_input.raw_message}
        if router_input.selected_route:
            op15_args["selected_route"] = router_input.selected_route
            if re.search(r"\b(this|the)\s+(page|screen|view|dashboard)\b", router_input.raw_message, re.IGNORECASE) or re.search(r"\bwhat\s+(is|does)\s+this\s+page\b", router_input.raw_message, re.IGNORECASE):
                op15_args["entry_id"] = router_input.selected_route
        return RouteDecision(
            route="WORKFLOW",
            scope="GLOBAL",
            intent="platform_guide",
            objective_id="OP15_PLATFORM_GUIDE",
            args=op15_args,
            confidence=0.9,
            deferred_intents=deferred,
            clarification_needed=False,
        )

    # Recheck / rerun guard: re-verifying a diagnosis -> OP03 or prior objective
    if any(w in raw_lower for w in ["recheck", "re-check", "rerun", "re-run", "check again"]):
        return RouteDecision(
            route="WORKFLOW",
            intent="diagnose",
            objective_id=router_input.prior_objective or "OP03_FAULT_DIAGNOSIS",
            args={"asset_id": router_input.asset_id},
            confidence=0.9,
            deferred_intents=deferred,
        )

    # Ambiguity guard: "Why did that happen?" or "Explain that" in empty session -> CLARIFY
    if AMBIGUOUS_FOLLOWUP_PATTERNS.search(router_input.raw_message) and not router_input.has_prior:
        return RouteDecision(
            route="WORKFLOW",
            intent="diagnose",
            objective_id="OP03_FAULT_DIAGNOSIS",
            args={"asset_id": router_input.asset_id},
            confidence=0.4,
            deferred_intents=deferred,
            clarification_needed=True,
            clarify_reason="CLARIFY",
            clarify_slot="asset_id",
            clarify_options=["FS-17", "FS-91", "FNW-01", "FWS-06"],
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
            scope="GLOBAL",
            intent="general_inquiry",
            objective_id="OP06_KNOWLEDGE_LOOKUP",
            args={},
            confidence=0.9,
            deferred_intents=deferred,
            clarification_needed=False,
        )

    raw_lower = router_input.raw_message.lower()
    is_fleet_ask = bool(FLEET_PATTERNS.search(router_input.raw_message))
    needs_asset_clarify = (
        router_input.asset_id is None
        and not is_fleet_ask
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
    lines = [
        f"Resolved Asset: {router_input.asset_id} (Source: {router_input.asset_source})",
    ]
    if router_input.selected_route:
        lines.append(f"Current UI Route Context: {router_input.selected_route}")
    lines.extend([
        f"Available Objectives: {available_objectives}",
        f"Candidate Tools: {router_input.candidate_tools}",
    ])
    return "\n".join(lines)


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

    # Fast deterministic rules before LLM invocation:
    from app.context.resolver import WELL_ID_REGEX
    is_telemetry_ask = any(w in router_input.raw_message.lower() for w in ['telemetry', 'status', 'reading', 'sensor', 'live'])

    # 0. Deterministic greeting guard: conversational greetings -> SIMPLE direct answer
    if GREETING_PATTERNS.search(router_input.raw_message):
        return RouteResult(
            decision=RouteDecision(
                route="SIMPLE",
                scope="GLOBAL",
                intent="greeting",
                objective_id=None,
                args={},
                confidence=0.95,
                deferred_intents=deferred,
                clarification_needed=False,
            ),
            llm_available=True,
            fallback_used=False,
        )

    # 0.1 Deterministic identity guard: self-knowledge questions -> IDENTITY
    if IDENTITY_PATTERNS.search(router_input.raw_message):
        return RouteResult(
            decision=RouteDecision(
                route="IDENTITY",
                scope="GLOBAL",
                intent="self_knowledge",
                objective_id=None,
                args={},
                confidence=1.0,
                deferred_intents=deferred,
                clarification_needed=False,
            ),
            llm_available=True,
            fallback_used=False,
        )

    # 0.15 Deterministic fleet guard: fleet-wide / multi-well queries -> WORKFLOW with scope="FLEET"
    if FLEET_PATTERNS.search(router_input.raw_message) and not router_input.asset_id:
        fleet_obj, fleet_intent = _resolve_fleet_objective(router_input.raw_message)
        return RouteResult(
            decision=RouteDecision(
                route="WORKFLOW",
                scope="FLEET",
                intent=fleet_intent,
                objective_id=fleet_obj,
                args={"user_query": router_input.raw_message},
                confidence=0.95,
                deferred_intents=deferred,
                clarification_needed=False,
            ),
            llm_available=True,
            fallback_used=False,
        )

    # 0.2 Deterministic platform guide guard: UI elements, routes, screens -> OP15_PLATFORM_GUIDE
    is_platform_ask = bool(PLATFORM_GUIDE_PATTERNS.search(router_input.raw_message)) or bool(
        router_input.selected_route and re.search(r"\b(explain|what is|what does|show)\s+(this|the)\s+(chart|plot|graph|screen|page|widget|view|dashboard)\b", router_input.raw_message, re.IGNORECASE)
    )
    if is_platform_ask and not WELL_ID_REGEX.search(router_input.raw_message):
        op15_args = {"query": router_input.raw_message}
        if router_input.selected_route:
            op15_args["selected_route"] = router_input.selected_route
            if re.search(r"\b(this|the)\s+(page|screen|view|dashboard)\b", router_input.raw_message, re.IGNORECASE) or re.search(r"\bwhat\s+(is|does)\s+this\s+page\b", router_input.raw_message, re.IGNORECASE):
                op15_args["entry_id"] = router_input.selected_route
        return RouteResult(
            decision=RouteDecision(
                route="WORKFLOW",
                scope="GLOBAL",
                intent="platform_guide",
                objective_id="OP15_PLATFORM_GUIDE",
                args=op15_args,
                confidence=0.95,
                deferred_intents=deferred,
                clarification_needed=False,
            ),
            llm_available=True,
            fallback_used=False,
        )


    # 1. Deterministic follow-up guard: questions referencing past statement/graph/data -> FOLLOW_UP
    if FOLLOWUP_PATTERNS.search(router_input.raw_message):
        return RouteResult(
            decision=RouteDecision(
                route="FOLLOW_UP",
                scope="ASSET" if router_input.asset_id else "GLOBAL",
                intent="explain_prior",
                objective_id=None,
                args={"asset_id": router_input.asset_id},
                confidence=0.95,
                deferred_intents=deferred,
                clarification_needed=False,
            ),
            llm_available=True,
            fallback_used=False,
        )

    # 2. Ambiguous follow-up guard: pronoun-only queries with no prior -> CLARIFY
    if AMBIGUOUS_FOLLOWUP_PATTERNS.search(router_input.raw_message) and not router_input.has_prior:
        return RouteResult(
            decision=RouteDecision(
                route="WORKFLOW",
                scope="ASSET",
                intent="diagnose",
                objective_id="OP03_FAULT_DIAGNOSIS",
                args={"asset_id": router_input.asset_id},
                confidence=0.4,
                deferred_intents=deferred,
                clarification_needed=True,
                clarify_reason="CLARIFY",
                clarify_slot="asset_id",
                clarify_options=["FS-17", "FS-91", "FNW-01", "FWS-06"],
            ),
            llm_available=True,
            fallback_used=False,
        )

    # 3. Rule 0 guard: Definitional intent with no asset in text must route to SIMPLE (OP06)
    if DEFINITIONAL_PATTERNS.search(router_input.raw_message) and not WELL_ID_REGEX.search(router_input.raw_message) and not (router_input.asset_id and is_telemetry_ask):
        return RouteResult(
            decision=RouteDecision(
                route="SIMPLE",
                scope="GLOBAL",
                intent="general_inquiry",
                objective_id="OP06_KNOWLEDGE_LOOKUP",
                args={},
                confidence=0.95,
                deferred_intents=deferred,
                clarification_needed=False,
            ),
            llm_available=True,
            fallback_used=False,
        )

    try:
        decision = await llm_route(router_input.raw_message, context_block)
        if deferred and not decision.deferred_intents:
            decision.deferred_intents = deferred
        if decision.confidence < conf_threshold:
            decision.clarification_needed = True
            decision.clarify_reason = "CLARIFY"

        # Health query disambiguation: queries mentioning health/condition on an asset route to OP04, not OP01
        if any(w in router_input.raw_message.lower() for w in ["health", "degradation", "condition"]) and router_input.asset_id:
            if decision.objective_id == "OP01_CURRENT_STATUS":
                decision.objective_id = "OP04_HEALTH_ASSESSMENT"
                decision.intent = "health"

        # Recheck / rerun guard: re-verifying a diagnosis -> OP03 or prior objective, NOT OP01
        if any(w in router_input.raw_message.lower() for w in ["recheck", "re-check", "rerun", "re-run", "check again"]):
            decision.route = "WORKFLOW"
            decision.intent = "diagnose"
            decision.objective_id = router_input.prior_objective or "OP03_FAULT_DIAGNOSIS"
            decision.confidence = 0.95
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
