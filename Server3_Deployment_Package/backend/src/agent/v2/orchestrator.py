"""
Native Tool-Calling Orchestrator for V2 Architecture
Handles query routing to 17 canonical operational tools via:
1. Deterministic fast-path matchers (Greetings, Agent Self-Inquiry, Actuation Commands)
2. Native LLM tool-calling with JSON schema enforcement
3. Deterministic semantic keyword fallback safety net
"""

import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from src.agent.context import OperationalContextResolver, OperationalContext, ContextSource

logger = logging.getLogger(__name__)

TOOL_DEFINITIONS_PATH: Path = Path(__file__).parent / "tool_definitions.json"


class ToolCall(BaseModel):
    """
    Typed contract for agent tool invocation requests.
    """
    model_config = ConfigDict(populate_by_name=True)

    name: str = Field(description="Name of the selected operational tool")
    args: Dict[str, Any] = Field(default_factory=dict, description="Arguments dictionary for the tool")
    confidence: float = Field(default=1.0, description="Routing confidence score (0.0 - 1.0)")

    def dict(self, *args, **kwargs) -> Dict[str, Any]:
        """Pydantic v1 backwards compatibility alias."""
        return self.model_dump(*args, **kwargs)


def _load_tool_definitions() -> List[Dict[str, Any]]:
    """Loads canonical tool definitions from the JSON registry."""
    try:
        with open(TOOL_DEFINITIONS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as exc:
        logger.error("Failed to load tool_definitions.json from %s: %s", TOOL_DEFINITIONS_PATH, exc)
        return []


def _extract_asset_id(query: str, default: Optional[str] = None) -> Optional[str]:
    """Extracts target asset identifier from query string if present."""
    wells = OperationalContextResolver.extract_explicit_wells(query)
    if wells:
        return wells[0]
    return default



def _match_greeting(query: str) -> Optional[ToolCall]:
    """Fast-path matcher for greetings."""
    q_clean = re.sub(r"[?!.,;]+$", "", query.strip().lower()).strip()
    greeting_patterns = [
        r"^(?:hi|hello|hey|greetings|howdy)(?:\s+(?:there|jane|esp|assistant|agent))?$",
        r"^good\s+(?:morning|afternoon|evening|day)$",
    ]
    for pat in greeting_patterns:
        if re.match(pat, q_clean):
            return ToolCall(name="general_inquiry", args={"query": query}, confidence=1.0)
    return None


def _match_agent_profile(query: str) -> Optional[ToolCall]:
    """Fast-path matcher for agent self-inquiry, capabilities, and standards."""
    q = query.strip().lower()
    profile_patterns = [
        r"\bwho are you\b",
        r"\bwhat can you do\b",
        r"\bwhat standards do you (?:refer to|use|follow|know)\b",
        r"\bwhat manuals do you (?:refer to|use|follow|know)\b",
        r"\bwhat are your capabilities\b",
        r"\btell me about yourself\b",
        r"\babout yourself\b",
        r"\babout (?:the )?agent\b",
        r"\bagent (?:profile|metadata|manifest|info)\b",
        r"\bwhat do you do\b",
        r"\bwhat is your role\b",
    ]
    for pat in profile_patterns:
        if re.search(pat, q):
            return ToolCall(name="get_agent_profile", args={"topic": "all"}, confidence=1.0)
    return None


def _match_actuation(query: str, asset_id: Optional[str] = None) -> Optional[ToolCall]:
    """Fast-path matcher for actuation commands (frequency adjustment, shutdown, pump stop)."""
    q = query.strip().lower()
    actuation_triggers = [
        r"\bincrease\s+(?:the\s+)?(?:operating\s+)?frequency\b",
        r"\bdecrease\s+(?:the\s+)?(?:operating\s+)?frequency\b",
        r"\bset\s+(?:the\s+)?(?:operating\s+)?frequency\b",
        r"\bset\s+(?:the\s+)?speed\s+(?:to\s+)?",
        r"\bchange\s+(?:the\s+)?(?:operating\s+)?frequency\b",
        r"\bshutdown\b",
        r"\bshut\s+down\b",
        r"\bstop\s+pump\b",
        r"\bkill\s+pump\b",
        r"\btrip\s+pump\b",
    ]
    matched = any(re.search(pat, q) for pat in actuation_triggers)
    if not matched:
        return None

    # Determine target frequency
    freq: float = 55.0
    m_hz = re.search(r"(\d+(?:\.\d+)?)\s*(?:hz|hertz)", q)
    if m_hz:
        freq = float(m_hz.group(1))
    else:
        m_to = re.search(r"(?:to|at|speed)\s+(\d+(?:\.\d+)?)", q)
        if m_to:
            freq = float(m_to.group(1))
        elif any(kw in q for kw in ("shutdown", "shut down", "stop pump", "kill pump", "trip pump")):
            freq = 0.0

    target_asset = asset_id or _extract_asset_id(query) or ""
    return ToolCall(
        name="set_operating_frequency",
        args={"asset_id": target_asset, "target_frequency_hz": freq},
        confidence=1.0,
    )


def _match_render_visual(
    query: str, asset_id: Optional[str] = None, session_id: Optional[str] = None
) -> Optional[ToolCall]:
    """Fast-path matcher for explicit visual referencing and chart rendering."""
    q = query.strip().lower()

    visual_patterns = [
        r"\b(?:show|render|display|view|open|bring\s+up|draw)\s+(?:me\s+)?(?:the\s+)?visual\s*(?:#|no\.?)?\s*([1-4]|one|two|three|four)\b",
        r"\bvisual\s*(?:#|no\.?)?\s*([1-4]|one|two|three|four)\b",
        r"\b(?:show|render|display|view)\s+(?:me\s+)?(?:the\s+)?(?:incident\s+)?(?:dynamic\s+)?tipping\s+timeline\b",
        r"\b(?:show|render|display|view)\s+(?:me\s+)?(?:the\s+)?(?:temporal\s+causation\s+)?forensics\s+(?:timeline|chart)\b",
        r"\b(?:show|render|display|view)\s+(?:me\s+)?(?:the\s+)?(?:subsystem\s+)?equalizer\b",
        r"\b(?:show|render|display|view)\s+(?:me\s+)?(?:the\s+)?(?:well\s+)?(?:depth|pressure)\s+profile\b",
        r"\b(?:show|render|display|view)\s+(?:me\s+)?(?:the\s+)?subsystem\s+health\b",
        r"\b(?:show|render|display|view)\s+(?:me\s+)?(?:the\s+)?(?:h-q|hq|pump)\s+curve\b",
        r"\b(?:show|render|display|view)\s+(?:me\s+)?(?:the\s+)?operating\s+envelope\b",
        r"\b(?:show|render|display|view)\s+(?:me\s+)?(?:the\s+)?synchronized\s+trends\b",
        r"\b(?:show|render|display|view)\s+(?:me\s+)?(?:the\s+)?well\s+schematic\b",
    ]

    matched = any(re.search(pat, q) for pat in visual_patterns)
    if not matched:
        return None

    target_asset = asset_id or _extract_asset_id(query) or "FS-031"

    # Determine canonical widget_id from query
    widget_id = "forensics-timeline"
    m_vis = re.search(r"visual\s*(?:#|no\.?)?\s*([1-4]|one|two|three|four)", q)
    if m_vis:
        val = m_vis.group(1).lower()
        if val in ("1", "one"):
            widget_id = "forensics-timeline"
        elif val in ("2", "two"):
            widget_id = "subsystem-equalizer"
        elif val in ("3", "three"):
            widget_id = "pump-curve"
        elif val in ("4", "four"):
            widget_id = "operating-envelope"
    elif "tipping" in q or "forensic" in q or "timeline" in q:
        widget_id = "forensics-timeline"
    elif "equalizer" in q or "subsystem" in q or "depth profile" in q or "pressure profile" in q:
        widget_id = "subsystem-equalizer"
    elif "pump" in q or "curve" in q or "h-q" in q or "hq" in q:
        widget_id = "pump-curve"
    elif "envelope" in q or "boundary" in q or "p10" in q or "p90" in q:
        widget_id = "operating-envelope"
    elif "trend" in q or "sync" in q:
        widget_id = "synchronized-trends"
    elif "schematic" in q or "twin" in q:
        widget_id = "well-schematic"

    focus = None
    if "breakout" in q:
        focus = "breakout"
    elif "trip" in q:
        focus = "trip"
    elif "bep" in q or "best efficiency" in q:
        focus = "bep"
    elif "corridor" in q:
        focus = "corridor"

    args = {"widget_id": widget_id, "asset_id": target_asset}
    if focus:
        args["focus"] = focus

    return ToolCall(
        name="render_visual",
        args=args,
        confidence=1.0,
    )


def _match_explain_widget(
    query: str, asset_id: Optional[str] = None, session_id: Optional[str] = None
) -> Optional[ToolCall]:
    """Fast-path matcher for on-screen chart and visualization explanations."""
    q = query.strip().lower()
    chart_triggers = [
        r"\bexplain\s+(?:the\s+|this\s+)?(?:pump\s+performance\s+curve|pump\s+curve|hq\s+curve|h-q|operating\s+envelope|tipping\s+timeline|forensics|timeline|trends?|chart|graph|widget|visualization)\b",
        r"\bwhat\s+(?:does|is)\s+(?:this|the)\s+(?:chart|curve|graph|timeline|envelope|screen)\s+(?:show|mean|display|indicating)\b",
        r"\bwhat\s+is\s+on\s+my\s+screen\b",
        r"\bexplain\s+this\s+curve\b",
        r"\bexplain\s+this\s+chart\b",
        r"\bexplain\s+(?:the\s+)?(?:chart|graph|curve)\b",
        r"\bwhat\s+chart\s+is\s+this\b",
    ]
    if any(re.search(pat, q) for pat in chart_triggers):
        target_asset = asset_id or _extract_asset_id(query) or ""
        active_view = None
        if session_id:
            try:
                from src.api.rest.agent_ws_routes import get_cached_view
                active_view = get_cached_view(session_id)
            except Exception:
                active_view = None

        if not target_asset and active_view:
            target_asset = active_view.get("target_asset", "")

        from src.services.chart_catalog import resolve_chart_from_title
        spec = resolve_chart_from_title(query)
        if not spec and active_view:
            if active_view.get("active_title"):
                spec = resolve_chart_from_title(active_view["active_title"])
            if not spec and active_view.get("active_widget"):
                from src.services.chart_catalog import get_chart_spec
                spec = get_chart_spec(active_view["active_widget"])

        widget_id = spec["id"] if spec else (active_view.get("active_widget") if active_view else "pump-curve")
        return ToolCall(
            name="explain_widget",
            args={"widget_id": widget_id, "asset_id": target_asset, "topic": "all"},
            confidence=1.0,
        )
    return None


def _match_ml_results(query: str, asset_id: Optional[str] = None) -> Optional[ToolCall]:
    """Fast-path matcher for querying ML model output from mlresults.db."""
    q = query.strip().lower()
    ml_triggers = [
        r"\b(?:show|get|view|check|fetch)\s+(?:the\s+)?ml\s+(?:model\s+)?(?:results?|verdict|predictions?|output)\b",
        r"\bwhat\s+does\s+(?:the\s+)?ml\s+(?:model\s+)?(?:say|predict|diagnose|output)\b",
        r"\bml\s+(?:model\s+)?(?:results?|verdict|prediction|score)\b",
        r"\bml\s+results\b",
    ]
    if any(re.search(pat, q) for pat in ml_triggers):
        target_asset = asset_id or _extract_asset_id(query) or ""
        return ToolCall(
            name="get_ml_results",
            args={"asset_id": target_asset, "limit": 10},
            confidence=1.0,
        )
    return None


def _route_via_llm(user_query: str, asset_id: Optional[str] = None) -> Optional[ToolCall]:
    """
    Attempts native LLM tool-calling via LLMAdapter with JSON schema validation.
    Returns ToolCall on success, or None on failure to trigger fallback.
    """
    try:
        from src.llm.adapter import LLMAdapter

        tools = _load_tool_definitions()
        if not tools:
            return None

        adapter = LLMAdapter()
        # Enforce structured ToolCallSchema from LLM
        tool_call_res = adapter.tool_call(user_query, tools=tools, run_id="ORCH-V2")
        if tool_call_res and getattr(tool_call_res, "tool", None):
            tool_name = tool_call_res.tool
            tool_args = dict(getattr(tool_call_res, "arguments", {}) or {})

            valid_names = {t["function"]["name"] for t in tools if "function" in t}
            if tool_name in valid_names:
                if asset_id and "asset_id" not in tool_args:
                    tool_args["asset_id"] = asset_id
                return ToolCall(name=tool_name, args=tool_args, confidence=0.9)
    except Exception as exc:
        logger.info("Native LLM tool-calling bypass/fallback: %s", exc)

    return None


def _semantic_fallback(user_query: str, asset_id: Optional[str] = None) -> ToolCall:
    """
    Deterministic semantic keyword mapping fallback conforming to tool_definitions.json.
    Guarantees reliable routing when LLM is unavailable or outputs non-conforming JSON.
    """
    q = user_query.strip().lower()
    target_asset = asset_id or _extract_asset_id(user_query) or ""

    # 1. Fault Diagnosis (OP03)
    fault_keywords = [
        "gas lock", "gas locking", "gas interference", "overheating", "underload",
        "overload", "fault", "diagnose", "diagnosis", "vibration", "broken",
        "leak", "cavitation", "broken shaft", "electrical fault", "mechanical fault",
        "trip", "abnormal"
    ]
    for kw in fault_keywords:
        if kw in q:
            symptom = "gas locking" if "gas lock" in q else kw
            return ToolCall(
                name="diagnose_fault",
                args={"asset_id": target_asset, "symptom": symptom},
                confidence=0.85,
            )

    # 2. Production Decline RCA (OP02)
    decline_keywords = [
        "production decline", "decline", "drawdown", "drop in production",
        "liquid rate drop", "bep", "head degradation", "rca"
    ]
    for kw in decline_keywords:
        if kw in q:
            return ToolCall(
                name="analyze_production_decline",
                args={"asset_id": target_asset},
                confidence=0.85,
            )

    # 3. Fleet Operations (OP08 - OP13)
    if any(kw in q for kw in ("all wells in fleet", "wells in fleet", "fleet inventory", "fleet overview", "show all wells", "fleet status", "list wells", "all wells")):
        return ToolCall(
            name="get_fleet_inventory",
            args={},
            confidence=0.9,
        )
    if any(kw in q for kw in ("production optimization", "fleet optimization", "uplift")):
        return ToolCall(
            name="get_fleet_production_optimization",
            args={},
            confidence=0.85,
        )
    if any(kw in q for kw in ("design sizing", "sizing", "pump stage")):
        return ToolCall(
            name="get_fleet_design_sizing",
            args={},
            confidence=0.85,
        )
    if any(kw in q for kw in ("maintenance priority", "workover urgency", "maintenance ranking")):
        return ToolCall(
            name="get_fleet_maintenance_priority",
            args={},
            confidence=0.85,
        )
    if any(kw in q for kw in ("case analytics", "mtbf", "incident patterns")):
        return ToolCall(
            name="get_fleet_case_analytics",
            args={},
            confidence=0.85,
        )
    if any(kw in q for kw in ("executive report", "executive summary", "fleet report")):
        return ToolCall(
            name="get_fleet_executive_report",
            args={},
            confidence=0.85,
        )

    # 4. Health Index (OP04)
    if any(kw in q for kw in ("health index", "rul", "remaining useful life", "composite health")):
        return ToolCall(
            name="get_health_index",
            args={"asset_id": target_asset},
            confidence=0.85,
        )

    # 5. Early Warnings (OP05)
    if any(kw in q for kw in ("early warning", "leading indicator", "warning signals", "pre-trip")):
        return ToolCall(
            name="check_early_warnings",
            args={"asset_id": target_asset},
            confidence=0.85,
        )

    # 6. SOP & Procedures (OP06)
    if any(kw in q for kw in ("sop", "procedure", "standard", "protocol", "api rp", "guideline", "operating standard")):
        return ToolCall(
            name="lookup_sop_procedure",
            args={"query": user_query, "standard": "API_RP_11S"},
            confidence=0.85,
        )

    # 7. Operational History (OP14)
    if any(kw in q for kw in ("history", "historical", "historian", "time series", "trend")):
        return ToolCall(
            name="get_operational_history",
            args={"asset_id": target_asset, "range": "24h"},
            confidence=0.85,
        )

    # 8. Asset Status (OP01)
    if any(kw in q for kw in ("status", "telemetry", "metrics", "condition", "how is", "operating status")):
        return ToolCall(
            name="get_asset_status",
            args={"asset_id": target_asset},
            confidence=0.85,
        )

    # 9. Visual Referencing & Chart Rendering (OP_RENDER_VISUAL)
    vis_tool = _match_render_visual(user_query, asset_id=target_asset)
    if vis_tool:
        return vis_tool

    # 10. Chart / Widget Explanation (OP_EXPLAIN_WIDGET)
    chart_tool = _match_explain_widget(user_query, asset_id=target_asset)
    if chart_tool:
        return chart_tool

    # 11. ML Model Results Query (OP_ML_RESULTS)
    ml_tool = _match_ml_results(user_query, asset_id=target_asset)
    if ml_tool:
        return ml_tool

    # Default fallback: General Inquiry (OP07)
    return ToolCall(
        name="general_inquiry",
        args={"query": user_query},
        confidence=0.75,
    )


def _match_clarification(query: str, asset_id: Optional[str] = None) -> Optional[ToolCall]:
    """Fast-path matcher for ambiguous, unanchored pronoun queries requiring asset clarification."""
    if asset_id or _extract_asset_id(query):
        return None

    q_clean = query.strip().lower()
    ambiguous_patterns = [
        r"\bcheck\s+on\s+it\b",
        r"\bcheck\s+it\b",
        r"\bhow\s+is\s+it\b",
        r"\bwhat\s+is\s+wrong\s+with\s+it\b",
        r"\bwhat's\s+wrong\s+with\s+it\b",
        r"\bdiagnose\s+it\b",
        r"\blook\s+into\s+it\b",
        r"\bwhat\s+about\s+it\b",
        r"\binspect\s+it\b",
        r"\brun\s+diagnostics\s+on\s+it\b",
    ]
    if any(re.search(pat, q_clean) for pat in ambiguous_patterns):
        return ToolCall(
            name="ask_clarification",
            args={
                "question": "Which well or asset would you like me to inspect?",
                "missing_context": "asset_id",
            },
            confidence=1.0,
        )
    return None


def route_query(
    user_query: str,
    asset_id: Optional[str] = None,
    context: Optional[OperationalContext] = None,
    session_id: Optional[str] = None,
    conv_store: Optional[Any] = None,
) -> ToolCall:
    """
    Route a natural language query to an operational ToolCall.
    Evaluation pipeline:
    1. Fast-path matchers (Greetings, Agent Self-Inquiry)
    2. Canonical Operational Context Resolution (Precedence P0 -> P1 -> P2 -> P3)
    3. Fast-path: Clarification for ambiguous or unanchored queries
    4. Fast-path: Actuation commands
    5. Fast-path: Visual Referencing & Chart Rendering
    6. Fast-path: Chart / Widget Explanations
    7. Fast-path: ML Model Results
    8. Native LLM tool-calling via local inference runtime
    9. Deterministic semantic keyword fallback safety net
    """
    # 1. Fast-path: Greetings
    greeting = _match_greeting(user_query)
    if greeting:
        return greeting

    # 2. Fast-path: Agent Self-Inquiry
    profile = _match_agent_profile(user_query)
    if profile:
        return profile

    # 3. Canonical Operational Context Resolution (P0 -> P1 -> P2 -> P3)
    if context is None:
        context = OperationalContextResolver.resolve(
            user_query=user_query,
            view_context={"asset_id": asset_id, "selected_asset": asset_id},
            session_id=session_id,
            conv_store=conv_store,
        )

    target_asset = context.target_asset or asset_id

    # 4. Fast-path: Actuation Commands (Safety Gate protected)
    actuation = _match_actuation(user_query, asset_id=target_asset)
    if actuation:
        return actuation

    # 5. Fast-path: Visual Referencing & Chart Rendering
    vis_tool = _match_render_visual(user_query, asset_id=target_asset, session_id=session_id)
    if vis_tool:
        return vis_tool

    # 6. Fast-path: Chart / Widget Explanations
    chart_tool = _match_explain_widget(user_query, asset_id=target_asset, session_id=session_id)
    if chart_tool:
        return chart_tool

    # 6. Fast-path: ML Model Results
    ml_tool = _match_ml_results(user_query, asset_id=target_asset)
    if ml_tool:
        return ml_tool

    # 7. Fast-path: Clarification for ambiguous or unanchored queries
    if context.is_clarification_needed:
        return ToolCall(
            name="ask_clarification",
            args={
                "question": context.clarification_prompt or "Which well or asset would you like me to inspect?",
                "missing_context": "asset_id_ambiguity" if context.candidate_assets else "asset_id",
                "candidate_assets": context.candidate_assets,
            },
            confidence=1.0,
        )

    # Fallback check for unanchored pronouns when context was pre-supplied without ambiguity flag
    clarification = _match_clarification(user_query, asset_id=target_asset)
    if clarification:
        return clarification

    # 8. Native LLM tool-calling
    llm_tool = _route_via_llm(user_query, asset_id=target_asset)
    if llm_tool:
        return llm_tool

    # 9. Deterministic semantic fallback
    return _semantic_fallback(user_query, asset_id=target_asset)

