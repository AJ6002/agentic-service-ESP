"""
3-Path Intent Router for ESP Agentic Platform
Grounded in PHASE_4_Objective_Layer_Implementation_Plan_ESP_APM.docx §26

Routing Paths:
1. Path A (Deterministic): Keyword / exact phrase matching against objective intent_classes
2. Path B (Semantic): Concept & similarity matching against objective descriptions and intents
3. Path C (Event): Direct mapping from events via ObjectiveRegistry (Single Authority)
4. Path LLM (Fallback): LLM classifier when keyword+semantic both below confidence threshold
"""

import json
import logging
import re
from typing import NamedTuple, Optional, Dict, Any, List, Tuple

from src.agent.objective_registry import ObjectiveRegistry

logger = logging.getLogger(__name__)

# ── B2: Threshold below which we mark ambiguous and may ask a question ────────
_AMBIGUITY_CONFIDENCE_THRESHOLD = 0.65
# ── B4: Threshold below which we try the LLM fallback before giving up ───────
_LLM_FALLBACK_THRESHOLD = 0.78


class _RouteResultBase(NamedTuple):
    objective_id: str
    confidence: float
    path: str
    is_ambiguous: bool = False


class RouteResult(_RouteResultBase):
    """
    Result of IntentRouter.route().
    Unpacks as 4 items: (objective_id, confidence, path, is_ambiguous) for 100%
    backwards-compatibility with all callers and tests, while exposing
    .secondary_objectives and .matched_intents as named attributes.
    """
    def __new__(
        cls,
        objective_id: str,
        confidence: float,
        path: str,
        is_ambiguous: bool = False,
        secondary_objectives: Tuple[str, ...] = (),
        matched_intents: Tuple[str, ...] = (),
    ):
        obj = super().__new__(cls, objective_id, confidence, path, is_ambiguous)
        obj.secondary_objectives = tuple(secondary_objectives)
        obj.matched_intents = tuple(matched_intents)
        return obj

    def __repr__(self):
        return (
            f"RouteResult(objective_id={self.objective_id!r}, confidence={self.confidence!r}, "
            f"path={self.path!r}, is_ambiguous={self.is_ambiguous!r}, "
            f"secondary_objectives={self.secondary_objectives!r}, matched_intents={self.matched_intents!r})"
        )


class IntentRouter:
    """
    3-Path Intent Router that classifies queries or events into Level-2 Objective IDs.
    Delegates Path C (Event) routing directly to ObjectiveRegistry.
    Returns RouteResult (objective_id, confidence, path, is_ambiguous).
    """

    # ── B4.T2: Enterprise-Grade Conversational & Greeting Specification ──────
    # Covers: Salutations, Slang, Time-of-Day, Well-being/How-are-you, Identity/Capability,
    # Courtesies, Gratitude, and Parting pleasantries.
    _GREETING_EXACT = {
        # Direct Salutations & Slang
        "hi", "hello", "helo", "helllo", "hey", "heya", "howdy", "yo", "greetings", "salutations",
        "welcome", "ahoy", "hiya", "sup", "whats up", "what's up", "what's good", "whats good",
        "ay", "aye", "holla", "what's crackin", "whats crackin", "what's cooking", "whats cookin",
        "hii", "hiii", "heyy", "heyyy", "hai", "hlo", "ola",
        # Multilingual Field Greetings
        "hola", "buenos dias", "buenas tardes", "marhaba", "salam", "salam alaykum", "assalam alaikum",
        "bonjour", "salut", "guten tag", "hallo", "namaste", "ciao",
        # Time of Day & Shift Operations
        "good morning", "morning", "mornin", "mornin'", "good afternoon", "afternoon",
        "good evening", "evening", "good day", "top of the morning",
        "start of shift", "shift start", "shift change", "night shift hello", "on shift",
        # Well-being & Social Inquiries
        "how are you", "how are you doing", "how are you today", "how's it going", "hows it going",
        "how are things", "how is it going", "how is everything", "how's everything",
        "how have you been", "how do you do", "how r u", "how you doing", "how are u",
        "how's life", "how is life", "what's new", "whats new",
        "what is good", "what's happening", "whats happening", "what are you up to",
        "are you okay", "are you good", "hope all is well", "hope you are well",
        "hope your day is going well", "hope you're having a good day", "are you alive",
        "are you online", "are you still there", "are you working", "are you ready",
        # Identity, Role & Capabilities
        "who are you", "what is your name", "what are you", "what can you do", "what do you do",
        "how can you help", "how can you help me", "what can you help me with", "what are your capabilities",
        "what are your skills", "what features do you have", "what are you capable of",
        "help", "role", "identity", "introduce yourself", "tell me about yourself", "give me an intro",
        "who is jane", "who is agent jane", "what is agent jane", "who made you", "who created you",
        "are you an ai", "are you a bot", "are you human", "are you an agent", "is this an ai", "are you real",
        "nice to meet you", "glad to meet you", "pleased to meet you",
        # Courtesies & Gratitude
        "thanks", "thank you", "thx", "ty", "thanks a lot", "thank you so much", "thank you very much",
        "much appreciated", "appreciate it", "cheers", "good job", "great job", "well done",
        "nice work", "awesome work", "you're awesome", "you are great", "good bot", "great bot",
        "nice one", "danke", "gracias", "merci",
        "ok", "okay", "k", "got it", "cool", "nice", "great", "awesome", "perfect", "sure",
        "understood", "noted", "sounds good", "alright", "all right", "roger that", "copy that",
        "will do", "no problem", "you bet",
        # Parting & Farewells
        "bye", "goodbye", "see you", "see ya", "talk later", "catch you later", "see you later",
        "have a good day", "have a nice day", "have a great day", "have a good one",
        "good night", "take care", "signing off", "logging off"
    }

    _GREETING_PREFIXES = (
        "hi", "hello", "helo", "hey", "heya", "howdy", "hiya", "yo", "hola", "bonjour", "marhaba", "salam",
        "good morning", "good afternoon", "good evening", "good day", "morning", "afternoon", "evening",
        "greetings", "dear agent", "dear jane", "agent jane"
    )

    _OPERATIONAL_SIGNALS = {
        "fs-", "fsws-", "well", "wells", "pump", "motor", "drive", "vfd", "vsd",
        "frequency", "hz", "vibration", "temp", "temperature", "pressure", "pip", "pdp",
        "amps", "current", "voltage", "rate", "bpd", "water cut", "gas", "flow",
        "status", "trip", "tripped", "alarm", "fault", "anom", "anomaly", "decline", "dropping",
        "trend", "history", "log", "check", "inspect", "show", "tell me why", "diagnose",
        "sizing", "bep", "headroom", "fleet", "rank", "list", "all wells", "kwh", "power",
        "choke", "valve", "drawdown", "cavitation", "gas lock", "underload", "overload"
    }

    def __init__(self, registry: Optional[ObjectiveRegistry] = None):
        self.registry = registry or ObjectiveRegistry()
        self._llm_gateway = None   # lazy-init to avoid circular import at startup

    def _get_llm_gateway(self):
        if self._llm_gateway is None:
            try:
                from src.llm.gateway import LLMGateway
                self._llm_gateway = LLMGateway()
            except Exception as ex:
                logger.warning("IntentRouter: LLM gateway unavailable for fallback (%s)", ex)
        return self._llm_gateway

    def _llm_classify(
        self,
        user_query: str,
        conversation_context: Optional[Dict[str, Any]] = None,
    ) -> Optional[RouteResult]:
        """
        B4.T1 — Calibrated High-Precision LLM Classifier Fallback.
        Sends a descriptive operational domain catalog to Qwen2.5-3B to classify queries
        into Level-2 Objective IDs, extract target well, scope, and intent reasoning.
        Returns RouteResult or None if LLM call fails.
        """
        gw = self._get_llm_gateway()
        if gw is None:
            return None

        objectives = self.registry.list_all()

        objective_guide = (
            "- OP00_OPERATIONAL_CONTROL: Direct actuation or control command (Refusal Policy). Any command attempting to turn off/on, shut down, stop pump/well, start pump, reboot drive, ramp up/down, speed up/down, set frequency, adjust VSD speed, trip breaker, cut power, or kill a well.\n"
            "- OP01_CURRENT_STATUS: Instantaneous operational state, live operating conditions, current telemetry snapshot (vibration, motor temp, frequency, amps, intake/discharge pressure), running/stopped status, or hardware nameplate specs for a specific well.\n"
            "- OP02_PRODUCTION_DECLINE_RCA: Root cause analysis of production loss, flow rate drops, why production dropped, flowing below BEP/target, inflow performance, gas interference.\n"
            "- OP03_FAULT_DIAGNOSIS: Root cause analysis of active faults, trips, electrical anomalies (insulation, underload, overload, ground fault), motor overheating, abnormal pressure differentials, or high vibration root cause.\n"
            "- OP04_HEALTH_ASSESSMENT: Health index score, mechanical/electrical condition assessment, remaining useful life (RUL), degradation index, or risk horizon.\n"
            "- OP05_EARLY_WARNING: Detecting subtle drift, precursor anomaly warnings, or anomaly scores before equipment trips.\n"
            "- OP06_PROCEDURE_LOOKUP: Standard operating procedures (SOP), restart guides, commissioning checklists, backspin protocols, or engineering manuals.\n"
            "- OP07_GENERAL_INQUIRY: Small talk, greetings ('hi', 'hello'), identity questions ('who are you', 'what can you do'), general ESP engineering principles or acronym definitions.\n"
            "- OP08_FLEET_INVENTORY: Count, total, list, or inventory of assets across fleet (how many wells, total assets, running vs stopped).\n"
            "- OP09_FLEET_PRODUCTION_OPTIMIZATION: Ranking multiple wells by production rate (best/worst producers, production optimization, headroom gain).\n"
            "- OP10_FLEET_DESIGN_SIZING: Pump sizing, equipment selection, stage count comparison across fleet.\n"
            "- OP11_FLEET_MAINTENANCE_PRIORITY: Ranking wells by health index, degradation urgency, or maintenance priority.\n"
            "- OP12_FLEET_CASE_ANALYTICS: Historical incident clustering, recurring failure modes across wells.\n"
            "- OP13_FLEET_EXECUTIVE_REPORTING: Field-wide executive KPI summary, MTBF, failure rates, uptime dashboard across fleet.\n"
            "- OP14_OPERATIONAL_HISTORY: Historical telemetry trends, long-term logs, historical data over hours/days/weeks."
        )

        system_prompt = (
            "You are an expert ESP (Electric Submersible Pump) Operations AI Classifier.\n"
            "Classify the operator's query into exactly ONE primary objective ID and extract operational context.\n\n"
            f"OPERATIONAL INTENT CATALOG:\n{objective_guide}\n\n"
            "CLASSIFICATION RULES (evaluate top-down; first confident match wins; if two rules plausibly match, set BOTH as primary_objective + secondary_objectives rather than guessing):\n\n"
            "1. OP00_OPERATIONAL_CONTROL — Any request to change, command, or actuate equipment state (increase/decrease/adjust/set/change frequency or speed, start, stop, shut in, reset, trip, override, reboot, restart, 'ramp up', 'ramp down', 'kill', 'bump up/down'). Applies even without an explicit asset — actuation intent alone triggers this rule. When in doubt between OP00 and any diagnostic objective, choose OP00.\n"
            "2. OP01_CURRENT_STATUS — Asking what a specific, named asset's live/current reading, state, or value is right now (single snapshot, no comparison to history implied). Requires an asset reference (name, tag, or 'it'/'that well' resolved from prior turn context).\n"
            "3. OP02_PRODUCTION_DECLINE_RCA — Asking why liquid rate, flow, or production has dropped/declined/is lower than expected, for a specific asset, with an implied comparison over time (production used to be higher).\n"
            "4. OP03_FAULT_DIAGNOSIS — Asking why a specific asset tripped, faulted, alarmed, shut down unexpectedly, or is behaving abnormally right now (not a gradual decline — an event or fault state).\n"
            "5. OP04_HEALTH_ASSESSMENT — Asking for an overall health/condition assessment or score for a specific asset, without a specific complaint or triggering event (general 'how is this pump doing' without decline or fault language).\n"
            "6. OP05_EARLY_WARNING — Asking about anomalies, deviations from baseline, or emerging/early-stage issues for a specific asset, phrased proactively ('anything to watch for', 'early signs of trouble', 'flag any anomalies').\n"
            "7. OP06_PROCEDURE_LOOKUP — Asking for a standard operating procedure, checklist, troubleshooting steps, spec value, or reference to a written standard/API RP. Does not require an asset — procedures are asset-agnostic by nature.\n"
            "8. FLEET OBJECTIVES (OP08 through OP13) — Asking for a count, total, list, summary, ranking, or comparison ACROSS assets/wells (e.g. 'how many wells', 'total assets', 'which wells need attention', 'compare pump models across the field'). Trigger phrase pattern: plural/aggregate nouns ('wells', 'assets', 'the fleet', 'all pumps') with no single asset named. This rule takes precedence over Rule 10 — absence of a named asset means CHECK THIS RULE FIRST, not general inquiry.\n"
            "   - OP08_FLEET_INVENTORY: Count, total, list, or inventory of assets across fleet.\n"
            "   - OP09_FLEET_PRODUCTION_OPTIMIZATION: Ranking multiple wells by production rate or headroom gain.\n"
            "   - OP10_FLEET_DESIGN_SIZING: Pump sizing, BEP operating envelope comparison across fleet.\n"
            "   - OP11_FLEET_MAINTENANCE_PRIORITY: Ranking wells by health index, degradation urgency, or maintenance priority.\n"
            "   - OP12_FLEET_CASE_ANALYTICS: Incident clustering or recurring historical failure patterns across wells.\n"
            "   - OP13_FLEET_EXECUTIVE_REPORTING: Field-wide executive KPI summary or fleet uptime dashboard.\n"
            "9. OP14_OPERATIONAL_HISTORY — Asking about past events, downtime, run hours, or historical telemetry logs for a specific asset over a stated time window (retrospective record-keeping, not root-cause reasoning).\n"
            "10. OP07_GENERAL_INQUIRY — ONLY when the query is: a greeting/small talk, OR a conceptual/definitional question with no asset and no fleet-aggregate framing (e.g. 'what is drawdown', 'what does BEP mean'), OR genuinely unclassifiable after checking rules 1–9. This is the last-resort rule, not a default for 'no asset mentioned' — rule 8 already covers the no-asset-but-fleet-scoped case.\n\n"
            "TIE-BREAK: If a query matches both an aggregate pattern (rule 8) and a diagnostic pattern (rules 2–6) because it asks about a state across multiple named assets (e.g. 'why are FS-031 and FS-045 underperforming'), set primary_objective to the diagnostic rule and secondary_objectives to include the fleet objective.\n"
            "CONFIDENCE: If no rule matches with confidence >= 0.70, do not force a classification. Return 'UNCLASSIFIED' with your best-guess reasoning.\n\n"
            "Respond in JSON format with this exact schema:\n"
            "{\n"
            '  "primary_objective": "OP00_OPERATIONAL_CONTROL",\n'
            '  "confidence": 0.95,\n'
            '  "secondary_objectives": [],\n'
            '  "target_well": "FS-031",\n'
            '  "intent_reasoning": "Brief explanation"\n'
            "}"
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Query: {user_query}"},
        ]

        try:
            resp = gw.chat(messages=messages, max_tokens=150, temperature=0.0)
            content = (resp.content or "").strip()

            # Parse JSON
            json_text = content
            if "```json" in content:
                json_text = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                json_text = content.split("```")[1].split("```")[0].strip()

            matched_obj = None
            conf = 0.85
            sec_objs: List[str] = []
            reasoning = "llm_classified"

            try:
                data = json.loads(json_text)
                if isinstance(data, dict):
                    cand = str(data.get("primary_objective", "")).strip().upper()
                    if cand == "UNCLASSIFIED":
                        matched_obj = "CLARIFICATION"
                    else:
                        for o in objectives:
                            if o.objective_id == cand:
                                matched_obj = cand
                                break
                    if "confidence" in data:
                        try:
                            conf = max(0.50, min(0.98, float(data["confidence"])))
                        except (ValueError, TypeError):
                            pass
                    if "secondary_objectives" in data and isinstance(data["secondary_objectives"], list):
                        for s in data["secondary_objectives"]:
                            s_clean = str(s).strip().upper()
                            if any(o.objective_id == s_clean for o in objectives) and s_clean != matched_obj:
                                sec_objs.append(s_clean)
                    if "intent_reasoning" in data and data["intent_reasoning"]:
                        reasoning = str(data["intent_reasoning"])
            except Exception:
                pass

            # Fallback regex search if JSON parsing didn't find a valid objective_id
            if not matched_obj:
                content_upper = content.upper()
                if "UNCLASSIFIED" in content_upper:
                    matched_obj = "CLARIFICATION"
                else:
                    for obj in objectives:
                        if obj.objective_id in content_upper:
                            matched_obj = obj.objective_id
                            break

            q_low = user_query.lower().strip()
            is_vague = any(v in q_low for v in (
                "check it", "inspect it", "look at it", "something is wrong", "what about it", "fix it",
                "is everything okay", "everything okay", "look at things", "take a look", "check things"
            ))

            if not matched_obj and content:
                if is_vague or any(w in q_low for w in ("okay", "look at", "check", "wrong", "fine", "things", "what's up with")):
                    matched_obj = "OP01_CURRENT_STATUS"
                else:
                    matched_obj = "OP07_GENERAL_INQUIRY"

            if is_vague and matched_obj == "OP07_GENERAL_INQUIRY":
                matched_obj = "OP01_CURRENT_STATUS"

            # Low confidence (< 0.70) or UNCLASSIFIED marks query ambiguous to trigger HITL clarification
            is_ambiguous_result = is_vague or (conf < 0.70) or (matched_obj == "CLARIFICATION")
            if matched_obj == "CLARIFICATION":
                conf = min(conf, 0.60)

            if matched_obj:
                if is_vague:
                    conf = 0.60
                logger.info(
                    "IntentRouter Path LLM: '%s' → %s (conf=%.2f, ambiguous=%s, reason=%s)",
                    user_query[:40], matched_obj, conf, is_ambiguous_result, reasoning
                )
                return RouteResult(
                    matched_obj,
                    conf,
                    "Path_LLM_Fallback",
                    is_ambiguous_result,
                    tuple(sec_objs),
                    (reasoning,)
                )
        except Exception as ex:
            logger.warning("IntentRouter: LLM fallback call failed (%s)", ex)
        return None

    def route(
        self,
        user_query: str,
        event_code: Optional[str] = None,
        conversation_context: Optional[Dict[str, Any]] = None,
    ) -> RouteResult:
        """
        Classify intent using 3-Path strategy + optional LLM fallback.
        Returns RouteResult(objective_id, confidence, path, is_ambiguous).

        Backward-compatible: callers that unpack (obj_id, conf, path) = route(...) still work.

        Args:
            user_query:           The raw operator query string.
            event_code:           Optional SCADA/MQTT event code (Path C).
            conversation_context: Optional dict with keys:
                                    last_well      – most recent well_id in session
                                    last_objective – objective_id from the prior turn
                                    recent_turns   – list of recent turn dicts
                                  When None, behaviour is identical to pre-A2 (A2.T3).
        """
        # ── A2.T2 / B2: Follow-up resolution ─────────────────────────────────
        _FOLLOWUP_TOKENS = {
            "why", "is that bad", "what about it", "explain", "elaborate",
            "tell me more", "and?", "so?", "what does that mean", "how bad",
            "what now", "what next", "what should i do", "ok and",
        }
        if conversation_context:
            last_obj = conversation_context.get("last_objective")
            q_stripped = user_query.lower().strip().rstrip("?.,!")
            if last_obj and q_stripped in _FOLLOWUP_TOKENS:
                logger.info(
                    "IntentRouter Path A (Follow-up): '%s' → carry forward %s",
                    user_query[:40], last_obj,
                )
                return RouteResult(last_obj, 0.90, "Path_A_FollowUp", False, (), (q_stripped,))

        # Path C: Direct Event Mapping via ObjectiveRegistry (Single Authority)
        if event_code:
            target_id = self.registry.resolve_event_mapping(event_code)
            if target_id:
                logger.info("IntentRouter Path C (Event): Mapped event '%s' -> %s", event_code, target_id)
                return RouteResult(target_id, 1.0, "Path_C_Event", False, (), (event_code,))

        q_lower = user_query.lower().strip()

        # ── B4.T2: Enterprise-Grade Social Greeting & Hybrid Disambiguation ───────────
        # Elongated casual variants ("hiiiii", "heyyy", "heeeello", "hiiiii!") collapse
        # repeated letters and strip trailing punctuation before matching.
        q_clean = q_lower.rstrip("!?. ,")
        q_collapsed = re.sub(r"([a-z])\1+", r"\1", q_clean)

        is_exact_greeting = (
            q_clean in self._GREETING_EXACT
            or q_collapsed in self._GREETING_EXACT
        )

        is_prefixed_greeting = False
        if not is_exact_greeting:
            for p in self._GREETING_PREFIXES:
                if q_clean == p or q_clean.startswith(p + " ") or q_clean.startswith(p + ","):
                    rem = q_clean[len(p):].lstrip(" ,").rstrip("!?. ,")
                    rem_coll = re.sub(r"([a-z])\1+", r"\1", rem)
                    social_tokens = {"", "there", "jane", "agent", "agent jane", "assistant", "bot", "copilot", "everyone", "all", "friend", "buddy", "team", "partner", "folks", "colleagues", "boss"}
                    if rem in social_tokens or rem in self._GREETING_EXACT or rem_coll in self._GREETING_EXACT:
                        is_prefixed_greeting = True
                        break

        # Check for asset mention (direct or context)
        has_specific_asset = bool(re.search(r"\b(fs-\d+|fsws-\d+|well-\w+)\b", q_lower))
        has_context_asset = bool(conversation_context and conversation_context.get("last_well"))
        has_asset = has_specific_asset or has_context_asset

        # Check for operational keywords or asset tags (Hybrid polite wrapper check)
        has_operational_content = any(re.search(r"\b" + re.escape(w), q_lower) for w in self._OPERATIONAL_SIGNALS)

        # Pure greeting: either exact social match, or prefixed opener with NO operational intent/asset mention
        if is_exact_greeting or (is_prefixed_greeting and not has_operational_content and not has_asset):
            logger.info("IntentRouter Path A (Greeting): Social opener / small talk detected: '%s'", q_clean)
            return RouteResult("OP07_GENERAL_INQUIRY", 0.98, "Path_A_Greeting", False, (), (q_clean,))

        objectives = self.registry.list_all()

        # Detect fleet / multi-asset intent signals early
        is_fleet_query = any(w in q_lower for w in [
            "fleet", "all wells", "all assets", "which wells", "rank",
            "across the field", "entire field", "total field", "between fs-", "compare the installed"
        ])

        # Detect conceptual inquiry (learning, definitions, failure mechanisms, general questions)
        _CONCEPTUAL_PREFIXES = (
            "what is", "what are", "what causes", "what can cause", "what indicates",
            "what does", "how does", "how do", "how is", "how to", "explain", "describe",
            "tell me about", "overview of", "definition of", "principles of", "list the", "list all"
        )
        _CONCEPTUAL_INFIXES = (
            "symptoms of", "indicators of", "causes of", "faults that could occur",
            "failure modes of", "common faults", "common issues", "troubleshooting",
            "how to troubleshoot", "what indicates"
        )
        is_conceptual_inquiry = (
            any(q_lower.startswith(p) for p in _CONCEPTUAL_PREFIXES)
            or any(w in q_lower for w in _CONCEPTUAL_INFIXES)
        )

        has_explicit_sop_kw = any(w in q_lower for w in [
            "procedure", "sop", "standard", "manual", "checklist", "playbook",
            "tripping limits", "tripping limit", "thresholds", "backspin"
        ])

        LIVE_DIAGNOSTIC_OBJS = {
            "OP01_CURRENT_STATUS",
            "OP02_PRODUCTION_DECLINE_RCA",
            "OP03_FAULT_DIAGNOSIS",
            "OP04_HEALTH_ASSESSMENT",
            "OP05_EARLY_WARNING",
        }

        # Path A: Specificity-First Deterministic & Variant Keyword Matching
        rules: List = []
        for obj in objectives:
            is_safety = obj.objective_id in ("OP00_OPERATIONAL_CONTROL", "OBJ_OPERATIONAL_CONTROL")
            is_fleet_obj = (obj.scope == "fleet" or
                            any(obj.objective_id.startswith(p) for p in ("OP08","OP09","OP10","OP11","OP12","OP13")))
            is_live_diag = obj.objective_id in LIVE_DIAGNOSTIC_OBJS
            is_kb_obj = obj.objective_id == "OP06_PROCEDURE_LOOKUP"
            is_general_obj = obj.objective_id in ("OP07_GENERAL_INQUIRY", "OBJ_GENERAL_INQUIRY")

            if is_safety:
                base_prio = 100
            elif is_general_obj and (has_asset or is_fleet_query or has_operational_content):
                # Suppress OP07 general/greeting keywords if query explicitly mentions an asset,
                # fleet query, or operational telemetry/fault terms
                base_prio = 0
            elif is_fleet_query and is_fleet_obj:
                base_prio = 20
            elif not has_asset and is_conceptual_inquiry and is_live_diag:
                # Live telemetry diagnostics strictly require an asset.
                # When no asset is present and query is conceptual ("what indicates...", "what causes..."),
                # suppress live diagnostics so the query cleanly routes to OP06 (Procedures/KB) or OP07.
                base_prio = 0
            elif not has_asset and is_conceptual_inquiry and is_kb_obj:
                # Boost KB procedural / limits lookup for conceptual queries
                base_prio = 18
            elif is_kb_obj:
                base_prio = 16 if has_explicit_sop_kw else 12
            elif not is_fleet_query and not is_fleet_obj:
                base_prio = 15
            else:
                base_prio = 1

            for kw in obj.intent_classes:
                rules.append((kw, obj.objective_id, 0.95, "Path_A_Deterministic", base_prio))
            for var in obj.workflow_variants:
                for kw in var.intent_classes:
                    rules.append((kw, obj.objective_id, 0.96, f"Path_A_Variant_{var.variant_id}", base_prio + 2))

        rules.sort(key=lambda r: (r[4], len(r[0].split()), len(r[0])), reverse=True)

        # Asset-normalized query representation so "why did FS-031 stop" matches "why did it stop"
        q_norm_asset = re.sub(r"\b(fs-\d+|fsws-\d+|well-\w+)\b", "it", q_lower)

        matched_hits: List[tuple] = []
        for kw, obj_id, conf, path_lbl, prio in rules:
            if prio <= 0:
                continue
            kw_lower = kw.lower()
            pattern = r"\b" + re.escape(kw_lower) + r"\b"
            if re.search(pattern, q_lower) or re.search(pattern, q_norm_asset):
                matched_hits.append((kw, obj_id, conf, path_lbl, prio))

        if matched_hits:
            primary_kw, primary_obj, primary_conf, primary_path, _ = matched_hits[0]
            sec_objs = [h[1] for h in matched_hits if h[1] != primary_obj]
            unique_sec_objs = list(dict.fromkeys(sec_objs))
            matched_kws = list(dict.fromkeys([h[0] for h in matched_hits]))
            logger.info("IntentRouter %s: Primary '%s' -> %s, Secondaries=%s, Matched=%s",
                        primary_path, primary_kw, primary_obj, unique_sec_objs, matched_kws)
            return RouteResult(
                primary_obj,
                primary_conf,
                primary_path,
                False,
                tuple(unique_sec_objs),
                tuple(matched_kws)
            )

        # Path B: Semantic Heuristic / Keyword Overlap Fallback
        HARD_REFUSAL_IDS = {"OP00_OPERATIONAL_CONTROL", "OBJ_OPERATIONAL_CONTROL"}
        is_fleet_query = any(w in q_lower for w in [
            "fleet", "all wells", "all assets", "which wells", "rank", "across the field"
        ])
        has_specific_asset = bool(re.search(r"\b(fs-\d+|fsws-\d+|well-\w+)\b", q_lower))

        # Conversational / generic stop words to avoid false positive substring/token matching
        STOP_WORDS = {
            "the", "and", "why", "how", "for", "are", "can", "you", "give", "get",
            "got", "all", "any", "not", "but", "who", "his", "her", "its", "our",
            "out", "now", "see", "too", "use", "way", "yet", "low", "down", "bug",
            "this", "that", "there", "then", "with", "from", "have", "been", "was",
            "were", "what", "when", "where", "which", "will", "would", "could",
            "should", "about", "into", "over", "some", "take", "look", "things",
            "morning", "afternoon", "evening", "please", "check", "tell", "show",
            "well", "wells", "asset", "assets", "pump", "pumps", "okay", "good",
            "fsws", "well", "esp", "esps"
        }
        query_tokens = set(re.findall(r"\b[a-z]{3,}\b", q_lower)) - STOP_WORDS

        # Actuation signal detection - if actuation verb present, do not let Path B falsely claim high confidence
        _ACTUATION_SIGNALS = {
            "turn", "stop", "shut", "speed", "ramp", "trip", "breaker", "kill",
            "reboot", "set", "drive", "power", "vsd", "vfd", "choke", "restart",
            "bump", "nudge", "crank", "throttle", "dial", "boost", "push",
            "bring", "override", "adjust", "switch", "lower", "raise", "reduce"
        }
        has_actuation_signal = bool(query_tokens & _ACTUATION_SIGNALS)

        candidates: List[Tuple[float, str, set]] = []

        for obj in objectives:
            if obj.objective_id in HARD_REFUSAL_IDS or obj.objective_id == "OP07_GENERAL_INQUIRY":
                continue

            title_tokens = set(re.findall(r"\b[a-z]{3,}\b", obj.title.lower()))
            desc_tokens = set(re.findall(r"\b[a-z]{3,}\b", obj.description.lower()))

            kw_matches = query_tokens & title_tokens
            desc_matches = query_tokens & desc_tokens

            keyword_score = len(kw_matches) * 0.25 + len(desc_matches) * 0.12
            score = keyword_score

            # Only apply scope / asset tie-breaker if there is substantive keyword affinity (>= 0.30)
            if keyword_score >= 0.30:
                if is_fleet_query and obj.scope == "fleet":
                    score += 0.20
                elif has_specific_asset and obj.scope == "single":
                    score += 0.15

            if score > 0:
                candidates.append((score, obj.objective_id, kw_matches | desc_matches))

        candidates.sort(key=lambda c: c[0], reverse=True)

        if candidates:
            best_score, best_obj_id, best_matches = candidates[0]
            is_close_race = len(candidates) > 1 and (candidates[0][0] - candidates[1][0] < 0.15)
            semantic_confidence = min(0.85, 0.40 + best_score)
            if is_close_race:
                semantic_confidence = min(semantic_confidence, 0.65)
            # Require at least 2 distinct token matches before Path B is allowed to suppress LLM fallback.
            # A single keyword overlap (e.g. bare "fault") is insufficient to declare confident diagnostic intent
            # on conceptual questions ("what causes ESP faults").
            if len(best_matches) < 2:
                semantic_confidence = min(semantic_confidence, 0.65)
        else:
            best_score = 0.0
            best_obj_id = "OP07_GENERAL_INQUIRY"
            best_matches = set()
            semantic_confidence = 0.40

        # Actuation queries should never be handled by Path B semantic guessing
        if has_actuation_signal:
            semantic_confidence = min(semantic_confidence, 0.50)

        # ── B2.T1/T2: Ambiguity signal — compute before LLM hop ──────────────
        # Mark ambiguous when confidence is below threshold AND no specific asset was explicitly named.
        # An asset in conversation memory (last_well) should NOT suppress ambiguity for vague queries.
        # General inquiries (OP07) are non-operational and should never trigger asset ambiguity.
        is_ambiguous = (
            semantic_confidence < _AMBIGUITY_CONFIDENCE_THRESHOLD
            and not has_specific_asset
            and best_obj_id not in ("OP07_GENERAL_INQUIRY", "OP00_OPERATIONAL_CONTROL")
        )

        # ── B4.T3: Short-circuit — call LLM fallback when semantic is weak or actuation is present ──
        if semantic_confidence < _LLM_FALLBACK_THRESHOLD or has_actuation_signal:
            llm_result = self._llm_classify(user_query, conversation_context)
            if llm_result is not None:
                # LLM resolved intent but asset ambiguity is independent: if the
                # query had no well context, the operator still hasn't told us WHICH asset.
                resolved_obj = llm_result.objective_id
                resolved_def = self.registry.get(resolved_obj)
                requires_asset = (resolved_def is None or resolved_def.scope == "single")
                is_ambiguous = llm_result.is_ambiguous
                if resolved_obj == "CLARIFICATION":
                    is_ambiguous = True
                elif requires_asset and resolved_obj not in ("OP07_GENERAL_INQUIRY", "OP00_OPERATIONAL_CONTROL"):
                    has_known_well = bool(
                        (conversation_context and conversation_context.get("last_well"))
                        or has_specific_asset
                    )
                    if not has_known_well:
                        is_ambiguous = True
                return RouteResult(
                    llm_result.objective_id,
                    llm_result.confidence,
                    llm_result.path,
                    is_ambiguous,
                    llm_result.secondary_objectives,
                    llm_result.matched_intents
                )

        logger.info(
            "IntentRouter Path B (Semantic): Query '%s...' -> %s (conf=%.2f, ambiguous=%s)",
            user_query[:30], best_obj_id, semantic_confidence, is_ambiguous,
        )
        return RouteResult(best_obj_id, semantic_confidence, "Path_B_Semantic", is_ambiguous, (), tuple(best_matches))
