"""
Section Registry for V2 Architecture
Defines the canonical objective-to-allowed-sections mapping and advisory payload
filtering logic to guarantee zero-phantom anomaly cards for non-diagnostic queries.
"""

from typing import Any, Dict, List, Optional, Set

# Canonical objective-to-allowed-sections mapping
ALLOWED_SECTIONS_PER_OBJECTIVE: Dict[str, Set[str]] = {
    "OP00_OPERATIONAL_CONTROL": {
        "executive_summary",
        "recommendations",
        "constraints",
        "mitigation_steps",
        "evidence",
    },
    "OP01_CURRENT_STATUS": {
        "executive_summary",
        "operating_point",
        "telemetry_metrics",
        "early_warnings",
        "evidence",
    },
    "OP02_PRODUCTION_DECLINE_RCA": {
        "executive_summary",
        "inflow_analysis",
        "pump_curve",
        "recommendations",
        "evidence",
    },
    "OP03_FAULT_DIAGNOSIS": {
        "executive_summary",
        "anomaly_cards",
        "fault_details",
        "recommendations",
        "mitigation_steps",
        "evidence",
    },
    "OP04_HEALTH_ASSESSMENT": {
        "executive_summary",
        "health_index",
        "component_scores",
        "evidence",
    },
    "OP05_EARLY_WARNING": {
        "executive_summary",
        "early_warnings",
        "anomaly_cards",
        "evidence",
    },
    "OP06_PROCEDURE_LOOKUP": {
        "executive_summary",
        "reference_standards",
        "sop_steps",
        "citations",
        "evidence",
    },
    "OP07_GENERAL_INQUIRY": {
        "executive_summary",
        "reference_standards",
        "citations",
        "evidence",
    },  # STRICTLY NO anomaly_cards
    "OP08_FLEET_INVENTORY": {
        "executive_summary",
        "fleet_summary",
        "asset_table",
        "evidence",
    },  # STRICTLY NO single-well anomaly_cards
    "OP09_FLEET_PRODUCTION_OPTIMIZATION": {
        "executive_summary",
        "fleet_summary",
        "asset_table",
        "evidence",
    },
    "OP10_FLEET_DESIGN_SIZING": {
        "executive_summary",
        "fleet_summary",
        "asset_table",
        "evidence",
    },
    "OP11_FLEET_MAINTENANCE_PRIORITY": {
        "executive_summary",
        "fleet_summary",
        "asset_table",
        "evidence",
    },
    "OP12_FLEET_CASE_ANALYTICS": {
        "executive_summary",
        "fleet_summary",
        "asset_table",
        "evidence",
    },
    "OP13_FLEET_EXECUTIVE_REPORT": {
        "executive_summary",
        "fleet_summary",
        "asset_table",
        "evidence",
    },
    "OP14_OPERATIONAL_HISTORY": {
        "executive_summary",
        "operating_point",
        "telemetry_metrics",
        "evidence",
    },
    "OP_CLARIFICATION": {
        "executive_summary",
        "citations",
        "evidence",
    },
    "OP_AGENT_PROFILE": {
        "executive_summary",
        "agent_profile",
        "standards_catalog",
        "evidence",
    },  # STRICTLY NO anomaly_cards
    "OP_EXPLAIN_WIDGET": {
        "executive_summary",
        "operating_point",
        "telemetry_metrics",
        "reference_standards",
        "citations",
        "evidence",
    },  # STRICTLY NO anomaly_cards
    "OP_ML_RESULTS": {
        "executive_summary",
        "anomaly_cards",
        "fault_details",
        "health_index",
        "evidence",
    },
    "OP_RENDER_VISUAL": {
        "executive_summary",
        "operating_point",
        "telemetry_metrics",
        "reference_standards",
        "citations",
        "recommendations",
        "evidence",
    },
}

# Aliases for prefix matching (e.g., "OP00", "OP01", ..., "OP13")
_OBJECTIVE_PREFIX_ALIASES: Dict[str, str] = {
    "OP00": "OP00_OPERATIONAL_CONTROL",
    "OP01": "OP01_CURRENT_STATUS",
    "OP02": "OP02_PRODUCTION_DECLINE_RCA",
    "OP03": "OP03_FAULT_DIAGNOSIS",
    "OP04": "OP04_HEALTH_ASSESSMENT",
    "OP05": "OP05_EARLY_WARNING",
    "OP06": "OP06_PROCEDURE_LOOKUP",
    "OP07": "OP07_GENERAL_INQUIRY",
    "OP08": "OP08_FLEET_INVENTORY",
    "OP09": "OP09_FLEET_PRODUCTION_OPTIMIZATION",
    "OP10": "OP10_FLEET_DESIGN_SIZING",
    "OP11": "OP11_FLEET_MAINTENANCE_PRIORITY",
    "OP12": "OP12_FLEET_CASE_ANALYTICS",
    "OP13": "OP13_FLEET_EXECUTIVE_REPORT",
    "OP14": "OP14_OPERATIONAL_HISTORY",
}

# Populate aliases into dictionary for direct O(1) lookup
for prefix, canonical in _OBJECTIVE_PREFIX_ALIASES.items():
    if prefix not in ALLOWED_SECTIONS_PER_OBJECTIVE and canonical in ALLOWED_SECTIONS_PER_OBJECTIVE:
        ALLOWED_SECTIONS_PER_OBJECTIVE[prefix] = ALLOWED_SECTIONS_PER_OBJECTIVE[canonical]

DEFAULT_ALLOWED_SECTIONS: Set[str] = {
    "executive_summary",
    "recommendations",
    "evidence",
}

# All known domain sections across all objectives
ALL_KNOWN_SECTIONS: Set[str] = {
    "executive_summary",
    "recommendations",
    "constraints",
    "mitigation_steps",
    "evidence",
    "operating_point",
    "telemetry_metrics",
    "early_warnings",
    "inflow_analysis",
    "pump_curve",
    "anomaly_cards",
    "fault_details",
    "health_index",
    "component_scores",
    "reference_standards",
    "sop_steps",
    "citations",
    "fleet_summary",
    "asset_table",
    "agent_profile",
    "standards_catalog",
}

# Envelope keys that form the standard advisory contract and must not be treated as stripped sections
CORE_ADVISORY_KEYS: Set[str] = {
    "run_id",
    "objective_id",
    "asset_id",
    "assessment",
    "diagnosis",
    "confidence",
    "risk",
    "recommendation",
    "recommended_action",
    "verification",
    "constraints",
    "evidence",
    "plan",
    "sections",
}


def _resolve_allowed_sections(objective_id: str) -> Set[str]:
    """Resolves the set of allowed sections for an objective string."""
    norm_obj = (objective_id or "").strip().upper()
    if norm_obj in ALLOWED_SECTIONS_PER_OBJECTIVE:
        return ALLOWED_SECTIONS_PER_OBJECTIVE[norm_obj]

    # Prefix match attempt
    for prefix, canonical in _OBJECTIVE_PREFIX_ALIASES.items():
        if norm_obj.startswith(prefix):
            return ALLOWED_SECTIONS_PER_OBJECTIVE[canonical]

    # Direct substring match attempt
    for key, sec_set in ALLOWED_SECTIONS_PER_OBJECTIVE.items():
        if norm_obj.startswith(key) or key.startswith(norm_obj):
            return sec_set

    return DEFAULT_ALLOWED_SECTIONS


def is_section_allowed(objective_id: str, section_name: str) -> bool:
    """
    Checks if a given section name is permitted for the specified objective.
    """
    allowed = _resolve_allowed_sections(objective_id)
    return section_name in allowed


def _is_anomaly_evidence(item: Any) -> bool:
    """
    Determines if an evidence item represents an anomaly card or anomaly finding.
    """
    if not isinstance(item, dict):
        return False
    item_type = str(item.get("type", "")).strip().lower()
    source_type = str(item.get("source_type", "")).strip().lower()
    source_id = str(item.get("source_id", "")).strip().lower()

    if item_type in ("anomaly", "anomaly_card", "anomaly_cards", "anomaly_detection", "fault_signature"):
        return True
    if "anomaly" in item_type or "anomaly" in source_type:
        return True
    if source_id.startswith("anomaly") or "anomaly" in source_id:
        return True
    return False


def filter_advisory_sections(objective_id: str, advisory: Dict[str, Any]) -> Dict[str, Any]:
    """
    Filters and cleanses an advisory dictionary according to allowed sections for objective_id.
    
    Guarantees:
    - If 'anomaly_cards' is NOT in allowed sections, any orphan/synthetic anomaly cards are removed.
    - Anomaly-type evidence items are filtered out of the 'evidence' list.
    - Suppressed sections are cleanly stripped before payload reaches the UI.
    """
    filtered = dict(advisory)
    anomaly_allowed = is_section_allowed(objective_id, "anomaly_cards")

    # 1. Enforce zero-phantom anomaly cards
    if not anomaly_allowed:
        filtered.pop("anomaly_cards", None)

        # Filter out anomaly-type evidence items
        if "evidence" in filtered and isinstance(filtered["evidence"], list):
            filtered["evidence"] = [
                item for item in filtered["evidence"]
                if not _is_anomaly_evidence(item)
            ]

    # 2. Filter nested 'sections' mapping or collection if present
    if "sections" in filtered:
        if isinstance(filtered["sections"], dict):
            filtered["sections"] = {
                sec: val for sec, val in filtered["sections"].items()
                if is_section_allowed(objective_id, sec)
            }
        elif isinstance(filtered["sections"], list):
            filtered["sections"] = [
                s for s in filtered["sections"]
                if is_section_allowed(
                    objective_id,
                    s.get("id") or s.get("name") or s.get("section_name", "")
                )
            ]

    # 3. Strip any known top-level domain section keys not allowed for this objective
    for sec_name in ALL_KNOWN_SECTIONS:
        if sec_name in CORE_ADVISORY_KEYS:
            continue
        if sec_name in filtered and not is_section_allowed(objective_id, sec_name):
            filtered.pop(sec_name, None)

    return filtered


__all__ = [
    "ALLOWED_SECTIONS_PER_OBJECTIVE",
    "DEFAULT_ALLOWED_SECTIONS",
    "ALL_KNOWN_SECTIONS",
    "is_section_allowed",
    "filter_advisory_sections",
]
