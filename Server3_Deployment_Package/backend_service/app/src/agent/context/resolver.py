"""
Operational Context Resolver — Unified Dialogue State Tracking (DST) & Entity Grounding
Grounded in Karpathy Guidelines: Think Before Coding, Simplicity First, Zero Split-Brain.

Enforces deterministic context precedence across Orchestrator, BFF Routes, and Supervisor:
P0 (Fleet / Non-Asset) -> P1 (Explicit Query) -> P2 (Deictic View-Context) -> P3 (Session Anaphora Stack)
"""

import re
import logging
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger(__name__)

# Canonical well regex matching certified Block 3/4 designations
WELL_REGEX = re.compile(
    r"\b(FSWS-[A-Za-z0-9\-]+|FS-\d+[A-Za-z0-9\-]*|FNW-[A-Za-z0-9\-]+|FWS-[A-Za-z0-9\-]+|ULFA-[A-Za-z0-9\-]+|ESP-WELL-\d+|WELL-\d+)\b",
    re.IGNORECASE,
)

# Secondary fallback regex for natural language like "well 31" or "on FS-31"
WELL_NL_REGEX = re.compile(
    r"\b(?:well|asset)\s+([A-Za-z0-9_-]+)\b",
    re.IGNORECASE,
)

DEICTIC_REGEX = re.compile(
    r"\b(this well|the current well|this asset|the active well|on[- ]screen well|the well on[- ]screen|currently viewing|what i am looking at|what i'm looking at|active visualization|on-screen visualization)\b",
    re.IGNORECASE,
)

ANAPHORA_REGEX = re.compile(
    r"\b(it|its|it's|the pump|this pump|the unit|the esp|that well|that pump)\b",
    re.IGNORECASE,
)

FLEET_PATTERNS = [
    r"\ball wells\b",
    r"\bwells in fleet\b",
    r"\bfleet inventory\b",
    r"\bfleet overview\b",
    r"\bshow all wells\b",
    r"\bfleet status\b",
    r"\blist wells\b",
    r"\bproduction optimization\b",
    r"\bfleet optimization\b",
    r"\bdesign sizing\b",
    r"\bmaintenance priority\b",
    r"\bworkover urgency\b",
    r"\bcase analytics\b",
    r"\bexecutive report\b",
    r"\bfleet report\b",
    r"\bacross the field\b",
]

NON_ASSET_PATTERNS = [
    r"^(?:hi|hello|hey|greetings|howdy)(?:\s+(?:there|jane|esp|assistant|agent))?$",
    r"^good\s+(?:morning|afternoon|evening|day)$",
    r"\bwho are you\b",
    r"\bwhat can you do\b",
    r"\bwhat standards do you (?:refer to|use|follow|know)\b",
    r"\bwhat manuals do you (?:refer to|use|follow|know)\b",
    r"\bwhat are your capabilities\b",
    r"\btell me about yourself\b",
    r"\babout yourself\b",
    r"\bagent (?:profile|metadata|manifest|info)\b",
]

STOP_WORDS = {
    "THE", "FREQUENCY", "SPEED", "PUMP", "ALL", "THIS", "MY", "IT", "THAT",
    "WHICH", "WHAT", "A", "AN", "ME", "US", "YOU", "HIM", "HER", "THEM", "ITS",
    "HERE", "THERE", "NOW", "TODAY", "YESTERDAY", "SCHEDULE", "SITE", "FLEET", "HEAD"
}


class ContextSource(str, Enum):
    """Origin of the resolved operational asset context."""
    EXPLICIT_QUERY = "EXPLICIT_QUERY"      # Operator explicitly typed asset name in prompt
    VIEW_CONTEXT   = "VIEW_CONTEXT"        # Deictic reference to current SCADA viewport
    SESSION_STACK  = "SESSION_STACK"       # Anaphoric reference bound to single active session asset
    AMBIGUOUS      = "AMBIGUOUS"           # Multi-asset collision on stack; requires clarification
    UNANCHORED     = "UNANCHORED"          # Diagnostic prompt with no asset anywhere; requires clarification
    GLOBAL_FLEET   = "GLOBAL_FLEET"        # Cross-asset fleet query; single-asset stack evicted
    NON_ASSET      = "NON_ASSET"           # Greeting, profile, or pure conceptual inquiry


class OperationalContext(BaseModel):
    """
    Canonical typed contract for resolved operational context.
    Single source of truth passed to Orchestrator, BFF streaming routes, and Execution plans.
    """
    model_config = ConfigDict(populate_by_name=True)

    target_asset: Optional[str] = Field(default=None, description="Canonical resolved asset ID (e.g. FS-031)")
    source: ContextSource = Field(description="Resolution layer that determined the asset")
    active_chart: Optional[str] = Field(default=None, description="On-screen active visualization ID if any")
    candidate_assets: List[str] = Field(default_factory=list, description="Candidate wells if ambiguous or comparative")
    is_clarification_needed: bool = Field(default=False, description="True if resolution demands user clarification")
    clarification_prompt: Optional[str] = Field(default=None, description="Clarification question text if needed")
    session_id: Optional[str] = Field(default=None, description="Active session ID")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Diagnostic telemetry or UI context metadata")

    def dict(self, *args, **kwargs) -> Dict[str, Any]:
        return self.model_dump(*args, **kwargs)


class OperationalContextResolver:
    """
    Deterministic context resolver and Dialogue State Tracker.
    Implements:
    1. Language-invariant regex extraction
    2. Multi-asset stack resolution with turn-decay staleness (MAX_STALENESS_TURNS = 3)
    3. Topic-shift eviction on Fleet objectives
    4. Multi-asset ambiguous anaphora detection routing to ask_clarification
    """

    MAX_STALENESS_TURNS: int = 3

    @classmethod
    def extract_explicit_wells(cls, query: str) -> List[str]:
        """Extracts unique canonical well identifiers from query in appearance order."""
        extracted: List[str] = []
        for m in WELL_REGEX.finditer(query):
            raw = m.group(1).upper()
            if raw not in extracted:
                extracted.append(raw)

        if not extracted:
            for m in WELL_NL_REGEX.finditer(query):
                cand = m.group(1).upper()
                if cand not in STOP_WORDS and len(cand) > 1 and cand not in extracted:
                    extracted.append(cand)

        return extracted

    @classmethod
    def is_fleet_query(cls, query: str) -> bool:
        """Checks if query is fleet-wide rather than asset-specific."""
        q = query.strip().lower()
        return any(re.search(pat, q) for pat in FLEET_PATTERNS)

    @classmethod
    def is_non_asset_query(cls, query: str) -> bool:
        """Checks if query is social greeting or general agent introspection."""
        q = query.strip().lower()
        return any(re.search(pat, q) for pat in NON_ASSET_PATTERNS)

    @classmethod
    def has_deictic_reference(cls, query: str) -> bool:
        """Checks if query contains on-screen / deictic markers."""
        return bool(DEICTIC_REGEX.search(query))

    @classmethod
    def has_anaphoric_reference(cls, query: str) -> bool:
        """Checks if query contains anaphoric pronouns."""
        return bool(ANAPHORA_REGEX.search(query))

    @classmethod
    def resolve(
        cls,
        user_query: str,
        view_context: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
        conv_store: Optional[Any] = None,
    ) -> OperationalContext:
        """
        Main entrypoint: resolves operational context from query, screen, and session memory.
        Precedence:
        P0 (Fleet / Non-Asset) -> P1 (Explicit Query) -> P2 (Deictic View) -> P3 (Session Stack)
        """
        vc = view_context or {}
        active_chart = vc.get("active_chart") or (vc.get("ui_context") or {}).get("active_chart")
        selected_asset = vc.get("selected_asset") or vc.get("asset_id")
        if selected_asset in ("UNKNOWN", "NONE", "None", "", "FLEET"):
            selected_asset = None

        # ── P0: Fleet / Global / Non-Asset Gate ──────────────────────────────
        if cls.is_non_asset_query(user_query):
            return OperationalContext(
                target_asset=None,
                source=ContextSource.NON_ASSET,
                active_chart=active_chart,
                session_id=session_id,
            )

        if cls.is_fleet_query(user_query):
            # Topic shifted to fleet: evict single-asset stack if conv_store provided
            if session_id and conv_store and hasattr(conv_store, "evict_asset_stack"):
                conv_store.evict_asset_stack(session_id)

            return OperationalContext(
                target_asset=None,
                source=ContextSource.GLOBAL_FLEET,
                active_chart=active_chart,
                session_id=session_id,
            )

        # ── P1: Explicit Query Extraction (Highest Priority) ──────────────────
        explicit_wells = cls.extract_explicit_wells(user_query)
        if explicit_wells:
            primary_well = explicit_wells[0]
            # If conversation store is available, record newly grounded asset
            if session_id and conv_store and hasattr(conv_store, "push_asset"):
                conv_store.push_asset(session_id, primary_well)

            return OperationalContext(
                target_asset=primary_well,
                source=ContextSource.EXPLICIT_QUERY,
                active_chart=active_chart,
                candidate_assets=explicit_wells,
                session_id=session_id,
            )

        # ── P2: Deictic / On-Screen SCADA View Context ────────────────────────
        # If user explicitly refers to "this well" or "on-screen well"
        if cls.has_deictic_reference(user_query) and selected_asset:
            if session_id and conv_store and hasattr(conv_store, "push_asset"):
                conv_store.push_asset(session_id, selected_asset)

            return OperationalContext(
                target_asset=selected_asset,
                source=ContextSource.VIEW_CONTEXT,
                active_chart=active_chart,
                session_id=session_id,
            )

        # ── P3: Session Anaphora Stack & Ambiguity Resolution ─────────────────
        active_stack: List[str] = []
        if session_id and conv_store:
            if hasattr(conv_store, "get_active_asset_stack"):
                active_stack = conv_store.get_active_asset_stack(
                    session_id, max_staleness=cls.MAX_STALENESS_TURNS
                )
            elif hasattr(conv_store, "get_last_well"):
                lw = conv_store.get_last_well(session_id)
                if lw:
                    active_stack = [lw]

        is_anaphoric = cls.has_anaphoric_reference(user_query)

        # Case 3A: Multiple assets recently active on stack (Ambiguity)
        if len(active_stack) >= 2 and (is_anaphoric or cls._is_diagnostic_query(user_query)):
            candidates = active_stack[:2]
            return OperationalContext(
                target_asset=None,
                source=ContextSource.AMBIGUOUS,
                active_chart=active_chart,
                candidate_assets=candidates,
                is_clarification_needed=True,
                clarification_prompt=f"Are you asking about **{candidates[0]}** or **{candidates[1]}**?",
                session_id=session_id,
            )

        # Case 3B: Exactly one active asset on stack
        if len(active_stack) == 1:
            return OperationalContext(
                target_asset=active_stack[0],
                source=ContextSource.SESSION_STACK,
                active_chart=active_chart,
                session_id=session_id,
            )

        # Case 3C: Stack is empty / stale. Fall back to View Context if available
        if selected_asset:
            return OperationalContext(
                target_asset=selected_asset,
                source=ContextSource.VIEW_CONTEXT,
                active_chart=active_chart,
                session_id=session_id,
            )

        # Case 3D: Unanchored diagnostic query requiring clarification
        if is_anaphoric or cls._is_diagnostic_query(user_query):
            return OperationalContext(
                target_asset=None,
                source=ContextSource.UNANCHORED,
                active_chart=active_chart,
                is_clarification_needed=True,
                clarification_prompt="Which well or asset would you like me to inspect?",
                session_id=session_id,
            )

        # Default fallback for unclassified non-diagnostic query (e.g. standard lookup)
        return OperationalContext(
            target_asset=None,
            source=ContextSource.NON_ASSET,
            active_chart=active_chart,
            session_id=session_id,
        )

    @staticmethod
    def _is_diagnostic_query(query: str) -> bool:
        """Determines if query requires a specific asset to execute meaningful diagnosis."""
        q = query.strip().lower()
        diagnostic_markers = [
            "status", "telemetry", "diagnose", "diagnosis", "fault", "trip",
            "overheating", "gas lock", "underload", "vibration", "drawdown",
            "production decline", "frequency", "speed", "operating point",
            "pip", "pdp", "amps", "motor temp", "flow rate"
        ]
        return any(m in q for m in diagnostic_markers)
