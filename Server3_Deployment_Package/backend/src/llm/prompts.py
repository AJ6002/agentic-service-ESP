"""
Layered Prompt Architecture — Phase 10: LLM Layer Architecture
Grounded in ESP APM LLM Architecture Design §3

Avoids monolithic prompts. Composes layered prompts dynamically:
  SYSTEM_PROMPT (Role, safety, evidence requirements, no fabrication)
        +
  ESP_DOMAIN_RULES (Physical hydraulic boundaries, pump curves, gas slugging)
        +
  OBJECTIVE_PROMPTS (Task-specific goal: RCA, fault diagnosis, RUL, maintenance)
        +
  COMPACT_CONTEXT (JSON context block built by CompactContextBuilder)
        +
  OUTPUT_SCHEMA_INSTRUCTIONS (Pydantic JSON format rules)
"""

import json
from typing import Any, Dict, Optional


# ---------------------------------------------------------------------------
# 1. System Prompt Layer
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = """You are Agent Jane, an expert AI Industrial Equipment Supervisor specializing in Electrical Submersible Pump (ESP) Artificial Lift systems.

CORE DIRECTIVES:
1. Ground every claim strictly in provided telemetry, engineering calculations, and evidence IDs.
2. NEVER fabricate telemetry values, sensor readings, or physics equations.
3. If data is missing or uncertain, state the uncertainty explicitly in the 'uncertainties' list.
4. All recommendations are ADVISORY-ONLY. You do not possess direct actuation authority over SCADA equipment.
5. Provide actionable, evidence-backed findings that can be verified by a field operator.
6. Your response MUST be a single, valid JSON object conforming strictly to the required schema.
"""


# ---------------------------------------------------------------------------
# 2. ESP Domain Rules Layer
# ---------------------------------------------------------------------------
ESP_DOMAIN_RULES = """ESP DOMAIN DIAGNOSTIC RULES:
- Intake Gas Interference: Cyclical PIP acoustic spikes, motor amp dips, GOR > 500 scf/bbl, pump operating left of BEP.
- Mechanical Pump Wear: Linear head decline (-15%+), stable motor current, non-recovering TDH reduction.
- Electrical Motor Overheating: Motor temperature > 130°C, winding insulation breakdown risk, drive current spiking.
- Scale / Plugging: Discharge pressure drop, rising motor load, differential pressure reduction across pump stages.
- Dry-Well Pump-off: PIP drops below minimum submergence limit (< 200 psi), flow rate drops sharply to 0 BPD.
"""


# ---------------------------------------------------------------------------
# 3. Objective Prompts Layer
# ---------------------------------------------------------------------------
OBJECTIVE_PROMPTS: Dict[str, str] = {
    "OP00_OPERATIONAL_CONTROL": """OBJECTIVE: Operational Safeguard & Direct Control Refusal Policy.
Task Requirements:
1. Explain clearly in "assessment" that direct remote actuation commands (start/stop/change frequency) cannot be executed autonomously because Agent Jane is locked in Advisory-Only mode under Safety Policy.
2. Return an empty list [] for "hypotheses" as this is a command refusal, not a diagnostic investigation.
3. In "recommendation", instruct the operator to contact the authorized Control Room Operator (CRO) or execute via approved SCADA interface.
4. Set "verification" to "Confirm authorization with lead operations supervisor before manual SCADA adjustments."
""",
    "OP01_CURRENT_STATUS": """OBJECTIVE: Current Operational Status & Operating Point Baseline.
Task Requirements:
1. Summarize current running telemetry (PIP, PDP, Motor Temp, Freq, Current) and compare against BEP and operating limits.
2. If metrics are stable within limits, note system health is nominal.
3. Identify any baseline deviations in hypotheses.
4. Recommend routine surveillance interval.
""",
    "OP02_PRODUCTION_DECLINE_RCA": """OBJECTIVE: Root Cause Analysis for ESP Production Decline.
Task Requirements:
1. Analyze liquid flow rate decline against baseline TDH and BEP curves.
2. Differentiate between Intake Gas Interference (slugging) vs Mechanical Pump Wear or Inflow Restriction.
3. Reference specific frozen evidence IDs (e.g. EV-001, EV-007) in hypotheses.
4. Recommend actionable operator verification checklist.
""",
    "OP03_FAULT_DIAGNOSIS": """OBJECTIVE: Comprehensive Multi-Hypothesis ESP Fault Classification.
Task Requirements:
1. Compare physics-based model outputs against telemetry indicators.
2. Assign confidence scores (0.0 to 1.0) to top failure mode hypotheses.
3. Provide causal reasoning grounded in sensor evidence tags.
""",
    "OP04_HEALTH_ASSESSMENT": """OBJECTIVE: Health Index, Degradation & Remaining Useful Life (RUL).
Task Requirements:
1. Evaluate equipment degradation trajectory and 24h/72h/7d failure risk horizons.
2. Report Health Index (0-100) and identify primary degrading components.
3. Recommend preventive workover window or operating envelope adjustments.
""",
    "OP05_EARLY_WARNING": """OBJECTIVE: Early Warning Anomaly & Thermal/Submergence Proximity Alert.
Task Requirements:
1. Detect subtle multi-variate signal drift before hardware alarm trips.
2. Assess proximity to motor thermal limit (130°C) or minimum submergence (PIP < 200 psi).
3. Recommend proactive choke or frequency trim to prevent downtime.
""",
    "OP06_PROCEDURE_LOOKUP": """OBJECTIVE: Standard Operating Procedure (SOP) & OEM Manual Reference.
Task Requirements:
1. Provide verified troubleshooting steps and guidelines from OEM specifications.
2. List step-by-step mitigation procedures.
""",
    "OP07_GENERAL_INQUIRY": """OBJECTIVE: General Conversational Inquiry (greeting, identity, or capability question).
Task Requirements:
1. Respond conversationally and briefly introduce yourself as Agent Jane and your role.
2. This is NOT a diagnostic request — do not fabricate fault hypotheses or evidence.
3. Leave "hypotheses" as an empty list [] since there is no diagnostic question to evaluate.
4. Set "recommendation" to a brief, friendly prompt inviting the user to ask a diagnostic or operational question.
""",
    "OP08_FLEET_INVENTORY": """OBJECTIVE: Fleet Inventory & Multi-Asset Discovery.
Task Requirements:
1. Summarize active vs stopped pumps and compare installed models across requested wells.
2. Format findings as a multi-well asset comparison.
""",
    "OP09_FLEET_PRODUCTION_OPTIMIZATION": """OBJECTIVE: Fleet-Wide Production Optimization & Power Balancing.
Task Requirements:
1. Identify high-potential optimization candidates across the field.
2. Balance frequency adjustments against substation electrical capacity.
""",
    "OP10_FLEET_DESIGN_SIZING": """OBJECTIVE: Fleet Operating Envelopes & Hydraulic Design Sizing.
Task Requirements:
1. Evaluate whether pumps across the field operate inside OEM recommended head-capacity envelopes.
""",
    "OP11_FLEET_MAINTENANCE_PRIORITY": """OBJECTIVE: Fleet Risk Ranking & Workover Prioritization.
Task Requirements:
1. Rank top highest-risk wells across the fleet based on RUL, thermal stress, and failure probability.
""",
    "OP12_FLEET_CASE_ANALYTICS": """OBJECTIVE: Historical Case Analytics & Incident Clustering.
Task Requirements:
1. Match current symptoms against historical workover records and known field failure cases.
""",
    "OP13_FLEET_EXECUTIVE_REPORTING": """OBJECTIVE: Executive Performance Summary & Daily/Weekly KPI Briefing.
Task Requirements:
1. Summarize total field uptime, production delivery, and critical risk items for management review.
""",
}

DEFAULT_OBJECTIVE_PROMPT = """OBJECTIVE: ESP Operational Performance Diagnostic.
Task Requirements:
1. Evaluate available telemetry and engineering metrics.
2. Formulate evidence-grounded hypotheses for any operational anomalies.
3. Recommend safe operator verification steps under Advisory-Only lock.
"""


# ---------------------------------------------------------------------------
# 4. Output Schema Prompt Layer
# ---------------------------------------------------------------------------
OUTPUT_SCHEMA_INSTRUCTION = """OUTPUT REQUIREMENT:
You MUST respond with a single, strictly formatted JSON object matching this schema:
{
  "assessment": "<executive summary sentence>",
  "hypotheses": [
    {
      "cause": "<primary hypothesis cause name>",
      "confidence": <float between 0.0 and 1.0>,
      "reasoning": "<one sentence justifying this hypothesis from the evidence>",
      "supporting_evidence": ["<EV-ID1>", "<EV-ID2>"],
      "contradicting_evidence": []
    }
  ],
  "uncertainties": ["<any missing data or unverified assumptions>"],
  "recommendation": "<actionable recommendation>",
  "verification": "<operator verification checklist>"
}

Do NOT wrap the response in markdown blocks if raw JSON is requested. Do NOT include conversational prose before or after the JSON.
"""


# ---------------------------------------------------------------------------
# Prompt Composer
# ---------------------------------------------------------------------------
class LayeredPromptBuilder:
    """
    Composes system prompt, domain rules, objective prompts, and compact context
    into a structured message list ready for the LLM Gateway.
    """

    @staticmethod
    def build_chat_messages(
        compact_context: Dict[str, Any],
        user_query: Optional[str] = None,
        custom_system_prompt: Optional[str] = None,
    ) -> list[Dict[str, str]]:
        """
        Build Open-AI style message array:
        [
          {"role": "system", "content": SYSTEM_PROMPT + DOMAIN_RULES},
          {"role": "user", "content": OBJECTIVE_PROMPT + COMPACT_CONTEXT + USER_QUERY + SCHEMA_INSTRUCTION}
        ]
        """
        # System prompt layer
        system_content = (custom_system_prompt or SYSTEM_PROMPT) + "\n\n" + ESP_DOMAIN_RULES

        # Objective layer
        obj_id = compact_context.get("objective", "")
        obj_prompt = OBJECTIVE_PROMPTS.get(obj_id, DEFAULT_OBJECTIVE_PROMPT)

        # Context layer (compact JSON string)
        context_json = json.dumps(compact_context, indent=2)

        # User payload layer
        user_parts = [
            obj_prompt,
            "--- COMPACT OPERATIONAL CONTEXT ---",
            context_json,
            "----------------------------------",
        ]

        if user_query:
            user_parts.append(f"OPERATOR QUERY: {user_query}")

        user_parts.append("\n" + OUTPUT_SCHEMA_INSTRUCTION)
        user_content = "\n\n".join(user_parts)

        return [
            {"role": "system", "content": system_content},
            {"role": "user", "content": user_content},
        ]
