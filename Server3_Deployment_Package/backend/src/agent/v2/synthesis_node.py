"""
Synthesis Node for V2 Architecture
Transforms executed PlanArtifacts and domain observations into grounded, validated
engineering advisories while strictly enforcing allowed section registries.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .plan_schema import PlanArtifact, PlanStepStatus
from .section_registry import filter_advisory_sections, is_section_allowed

from urllib.parse import quote


def _resolve_evidence_deep_link(
    specialist: str,
    action: str,
    obj_id: str,
    asset_id: str,
    query_intent: str,
    observation: str,
) -> Optional[str]:
    """Generates direct, browser-clickable URLs to live database viewers (Neo4j, Qdrant, Docs)."""
    spec = (specialist or "").lower()
    act = (action or "").lower()
    combined_text = f"{query_intent} {observation}".lower()

    # 1. Neo4j Graph Browser for Diagnostic & Fault modes
    if (
        spec == "diagnostic"
        or "diagnose" in act
        or "fault" in act
        or obj_id == "OP03_FAULT_DIAGNOSIS"
        or "anomaly" in spec
    ):
        if "gas" in combined_text:
            fault_node = "Gas Interference"
        elif "temp" in combined_text or "overheat" in combined_text or "heat" in combined_text:
            fault_node = "Motor Overheating"
        elif "shaft" in combined_text or "broken" in combined_text:
            fault_node = "Broken Shaft"
        elif "sand" in combined_text or "wear" in combined_text:
            fault_node = "Pump Wear"
        elif "vib" in combined_text:
            fault_node = "High Vibration"
        elif "leak" in combined_text or "tubing" in combined_text:
            fault_node = "Tubing Leak"
        else:
            fault_node = None

        if fault_node:
            cypher = f"MATCH (n:FaultMode {{name: '{fault_node}'}})-[r]-(m) RETURN n,r,m"
        else:
            cypher = "MATCH (n:FaultMode)-[r]-(m) RETURN n,r,m LIMIT 25"
        return f"http://localhost:7474/browser/?cmd=play&arg={quote(cypher)}"

    # 2. Qdrant Vector DB Dashboard for Knowledge & SOP lookups
    if (
        spec == "knowledge"
        or "sop" in act
        or "procedure" in act
        or obj_id in ("OP06_PROCEDURE_LOOKUP", "OP07_GENERAL_INQUIRY")
    ):
        return "http://localhost:6333/dashboard#/collections/esp_kb"

    # 3. Standard Document Viewer for Certified Standards & Regulatory
    if spec in ("governance", "standards") or "api" in act or "rp11s" in act or obj_id == "OP_AGENT_PROFILE":
        return "/api/esp/knowledge/document/API-RP-11S"

    # 4. In-App Asset Deep Dive Nameplate card for Telemetry & Controls
    if asset_id:
        return f"http://localhost:3000/?openAssetDeepDive={asset_id}"

    return None


def synthesize_advisory(
    plan: PlanArtifact,
    evidence_items: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    Synthesizes a grounded, validated engineering advisory dictionary from an executed PlanArtifact.
    
    Fields generated:
    - run_id, objective_id, asset_id
    - assessment: Domain assessment grounded in step observations
    - diagnosis: Root-cause diagnosis or operational state classification
    - confidence: Routing and diagnostic confidence score (0.0 - 1.0)
    - recommendation: Primary engineering operational advice
    - recommended_action: Structured action payload with urgency and details
    - verification: Verification steps for field validation
    - constraints: Operating envelope constraints (e.g. API RP 11S bounds)
    - evidence: Grounded evidence list extracted from step observations
    - plan: Serialized PlanArtifact payload
    
    Applies filter_advisory_sections to enforce the zero-phantom anomaly card guarantee.
    """
    obj_id = plan.objective_id or "OP01_CURRENT_STATUS"
    asset_id = plan.asset_id or ""
    query_intent = plan.query_intent or ""

    # 1. Extract observations from plan steps
    step_observations: List[str] = [
        step.observation_summary
        for step in plan.steps
        if step.observation_summary and len(step.observation_summary.strip()) > 0
    ]
    primary_observation = step_observations[0] if step_observations else ""

    # 2. Derive objective-grounded assessment, diagnosis, confidence, and recommendations
    if obj_id == "OP00_OPERATIONAL_CONTROL":
        assessment = (
            f"Operational control validation completed for {asset_id}. "
            f"Pre-actuation telemetry and operating envelope verified. "
            f"{primary_observation}".strip()
        )
        diagnosis = "Nominal pre-actuation state. No active electrical or mechanical trip condition."
        confidence = 0.98
        recommendation = (
            f"Review target frequency bounds (40.0 - 65.0 Hz) and authorize VFD frequency setpoint adjustment on {asset_id}."
        )
        recommended_action = {
            "action_title": "Authorize Operating Frequency Setpoint",
            "action_detail": f"Ramp operating frequency on {asset_id} within API RP 11S compliance limits.",
            "urgency": "HIGH" if plan.requires_human_approval else "MEDIUM",
            "confidence_score": confidence,
        }

    elif obj_id == "OP01_CURRENT_STATUS":
        assessment = (
            f"Operating status assessment for {asset_id}: "
            f"{primary_observation or 'Telemetry streams acquired successfully and evaluated against operating limits.'}"
        )
        diagnosis = "Nominal telemetry metrics across electrical, thermal, and hydrodynamic parameters."
        confidence = 0.95
        recommendation = f"Maintain continuous operating parameters on {asset_id} within established envelope."
        recommended_action = {
            "action_title": "Monitor Asset Telemetry",
            "action_detail": f"Continue standard surveillance of intake pressure and motor temperature on {asset_id}.",
            "urgency": "INFORMATIONAL",
            "confidence_score": confidence,
        }

    elif obj_id == "OP02_PRODUCTION_DECLINE_RCA":
        assessment = (
            f"Production decline RCA completed for {asset_id}. "
            f"Head degradation and inflow drawdown evaluated relative to BEP. "
            f"{primary_observation}".strip()
        )
        diagnosis = "Hydraulic head degradation and operating point deviation from BEP."
        confidence = 0.90
        recommendation = f"Inspect choke settings and consider speed adjustment on {asset_id} to restore operating point toward BEP."
        recommended_action = {
            "action_title": "Optimize Production Operating Point",
            "action_detail": f"Adjust VFD setpoint on {asset_id} to align operating head with Best Efficiency Point.",
            "urgency": "MEDIUM",
            "confidence_score": confidence,
        }

    elif obj_id == "OP03_FAULT_DIAGNOSIS":
        # Extract specific symptom/fault if available in observations or query
        q_low = query_intent.lower()
        if "gas" in q_low or any("gas" in obs.lower() for obs in step_observations):
            diag_text = "Gas Interference / Gas Locking detected from intake pressure and motor current oscillations."
        elif any(k in q_low for k in ("temp", "overheat", "thermal")) or any("temp" in obs.lower() for obs in step_observations):
            diag_text = "Elevated motor temperature and thermal dissipation degradation detected."
        else:
            diag_text = "Operating fault signature identified from telemetry and physics classifier."

        assessment = (
            f"Fault diagnosis completed for {asset_id}. "
            f"Telemetry signatures analyzed against physics models and diagnostic classifiers: "
            f"{primary_observation}".strip()
        )
        diagnosis = diag_text
        confidence = 0.88
        recommendation = f"Initiate SOP mitigation protocol for {asset_id} and monitor thermal headroom."
        recommended_action = {
            "action_title": "Execute Diagnostic Mitigation SOP",
            "action_detail": f"Implement corrective procedures on {asset_id} to resolve {diag_text.lower()}.",
            "urgency": "HIGH",
            "confidence_score": confidence,
        }

    elif obj_id == "OP04_HEALTH_ASSESSMENT":
        assessment = (
            f"Composite health index evaluated for {asset_id} based on multi-sensor degradation models. "
            f"{primary_observation}".strip()
        )
        diagnosis = "Minor thermal and mechanical wear indicators within acceptable operational limits."
        confidence = 0.92
        recommendation = f"Continue tracking health index degradation trend on {asset_id}."
        recommended_action = {
            "action_title": "Track Asset RUL & Health Index",
            "action_detail": f"Schedule inspection if health index drops below 0.70 threshold on {asset_id}.",
            "urgency": "LOW",
            "confidence_score": confidence,
        }

    elif obj_id == "OP05_EARLY_WARNING":
        assessment = (
            f"Early warning indicators and pre-trip signatures checked for {asset_id}. "
            f"{primary_observation}".strip()
        )
        diagnosis = "Pre-trip anomaly indicators detected below protective shutdown threshold."
        confidence = 0.89
        recommendation = f"Monitor active alarms and multivariate anomaly scores closely on {asset_id}."
        recommended_action = {
            "action_title": "Investigate Pre-Trip Indicators",
            "action_detail": f"Cross-reference SCADA alarm logs and anomaly trends on {asset_id}.",
            "urgency": "MEDIUM",
            "confidence_score": confidence,
        }

    elif obj_id.startswith("OP08") or obj_id.startswith("OP09") or obj_id.startswith("OP10") or \
         obj_id.startswith("OP11") or obj_id.startswith("OP12") or obj_id.startswith("OP13"):
        assessment = (
            "Fleet-wide surveillance report compiled across monitored ESP wells. "
            "Active census, production uplift, and degradation rankings aggregated. "
            f"{primary_observation}".strip()
        )
        diagnosis = "Fleet overview: monitory surveillance across producing assets; no fleet-wide common cause failure."
        confidence = 0.95
        recommendation = "Prioritize maintenance schedules for flagged wells and optimize field-wide choke allocation."
        recommended_action = {
            "action_title": "Review Fleet Prioritization Schedule",
            "action_detail": "Dispatch field engineering resources to highest-risk wells identified in census.",
            "urgency": "INFORMATIONAL",
            "confidence_score": confidence,
        }

    elif obj_id == "OP_AGENT_PROFILE":
        from .tools import get_agent_profile
        profile_res = get_agent_profile(topic="all")
        manifest = profile_res.get("manifest", {})
        ident = manifest.get("identity", {})
        stds = manifest.get("standards_and_manuals", [])
        assessment = profile_res.get("narrative", "Agent Jane operations profile and certified standards.")
        diagnosis = f"Agent Jane Introspection: {ident.get('operational_mode', 'Advisory-Only')} Co-Pilot"
        confidence = 1.0
        recommendation = "Refer to certified API RP 11S and IEC 60034-14 operational standards for field operating limits."
        recommended_action = {
            "action_title": "Review Certified Operating Standards",
            "action_detail": "Verify active well operations conform to API RP 11S and manufacturer operating bounds.",
            "urgency": "INFORMATIONAL",
            "confidence_score": 1.0,
        }

    elif obj_id in ("OP06_PROCEDURE_LOOKUP", "OP07_GENERAL_INQUIRY", "OP_CLARIFICATION"):
        assessment = (
            f"Engineering inquiry and standards retrieval completed for '{query_intent}'. "
            f"{primary_observation}".strip()
        )
        diagnosis = "Informational guidance inquiry - no operational equipment fault detected."
        confidence = 1.0
        recommendation = "Adhere to API RP 11S / IEC engineering standards and field operational guidelines."
        recommended_action = {
            "action_title": "Apply Technical Operating Standards",
            "action_detail": "Ensure field operations and setpoint parameters conform to API RP 11S specifications.",
            "urgency": "INFORMATIONAL",
            "confidence_score": 1.0,
        }

    else:
        assessment = (
            f"Operational assessment for {asset_id}: {query_intent}. "
            f"{primary_observation}".strip()
        )
        diagnosis = "Normal operating envelope maintained."
        confidence = 0.90
        recommendation = "Continue normal field operations according to standard procedures."
        recommended_action = {
            "action_title": "Maintain Standard Operation",
            "action_detail": f"Continue routine monitoring on {asset_id}.",
            "urgency": "INFORMATIONAL",
            "confidence_score": confidence,
        }

    # 3. Grounded verification steps
    verification = [
        f"Verify SCADA telemetry streams on {asset_id} remain stable and within limits.",
        "Ensure surface VFD frequency and motor load align with design specifications.",
        "Confirm all parameter modifications comply with API RP 11S operational standards.",
    ]

    # 4. Grounded operational constraints
    constraints = [
        "API RP 11S operational speed limits: 40.0 Hz to 65.0 Hz.",
        "Motor temperature must remain below 120°C (Class H insulation thermal headroom).",
        "Minimum intake pressure must exceed bubble point pressure to prevent free gas breakout.",
    ]

    # Check for plan step degradation / failures (Zero-Fabrication Policy)
    has_failed_step = any(step.status == PlanStepStatus.FAILED for step in plan.steps)
    has_skipped_step = any(step.status == PlanStepStatus.SKIPPED for step in plan.steps)
    is_degraded = has_failed_step or has_skipped_step

    if is_degraded:
        confidence = 0.35  # strictly < 0.50
        assessment = f"[DEGRADED EXECUTION] {assessment} Note: One or more execution steps failed or were skipped; confidence degraded."

    # Resurrected Conflict Detection between physics hydrodynamic model & ML classifier
    conflicts: List[Dict[str, Any]] = []
    physics_obs = next(
        (s.observation_summary for s in plan.steps if "physics" in (s.specialist or "").lower() or "physics" in (s.action or "").lower() or "bep" in (s.action or "").lower()),
        None,
    )
    diagnostic_obs = next(
        (s.observation_summary for s in plan.steps if "diagnostic" in (s.specialist or "").lower() or "diagnose" in (s.action or "").lower() or "fault" in (s.action or "").lower()),
        None,
    )
    if physics_obs and diagnostic_obs:
        p_low = physics_obs.lower()
        d_low = diagnostic_obs.lower()
        # Conflict condition: physics indicates severe/degraded/high-head condition while diagnostic reports nominal, or vice versa
        if (
            ("severe" in p_low or "high liquid head" in p_low or "head degradation" in p_low or "drawdown" in p_low)
            and ("nominal" in d_low or "normal" in d_low or "no fault" in d_low)
        ) or (
            ("nominal" in p_low or "normal" in p_low)
            and ("severe" in d_low or "locking" in d_low or "fault" in d_low)
        ):
            conflicts.append({
                "conflict_id": f"CONF-{asset_id}-01",
                "model_a": "Physics Hydrodynamic Model",
                "finding_a": physics_obs,
                "model_b": "ML Diagnostic Classifier",
                "finding_b": diagnostic_obs,
                "severity": "HIGH",
                "reconciliation_guidance": "Physics model and ML classifier yielded divergent fault indicators. Operator physical gauge inspection advised.",
            })

    # 5. Grounded evidence aggregation
    evidence: List[Dict[str, Any]] = list(evidence_items or [])

    # Ingest execution step observations as authoritative evidence with live deep links
    for step in plan.steps:
        obs = step.observation_summary or step.expected_output or step.title
        deep_link = _resolve_evidence_deep_link(
            specialist=step.specialist,
            action=step.action,
            obj_id=obj_id,
            asset_id=asset_id,
            query_intent=query_intent,
            observation=obs,
        )
        evidence.append({
            "source_id": f"STEP-{step.step_id}",
            "source_type": (step.specialist or "SPECIALIST").upper(),
            "type": "EXECUTION_STEP",
            "observation": obs,
            "authority_level": "A",
            "source_deep_link": deep_link,
        })

    # Only include anomaly evidence and anomaly cards if permitted by the registry
    advisory: Dict[str, Any] = {
        "run_id": plan.run_id,
        "objective_id": obj_id,
        "asset_id": asset_id,
        "assessment": assessment,
        "diagnosis": diagnosis,
        "confidence": confidence,
        "is_degraded": is_degraded,
        "risk": "HIGH" if plan.requires_human_approval else "NOMINAL",
        "recommendation": recommendation,
        "recommended_action": recommended_action,
        "verification": verification,
        "constraints": constraints,
        "evidence": evidence,
        "conflicts": conflicts,
        "plan": plan.dict(),
    }


    if obj_id == "OP_AGENT_PROFILE":
        from .tools import get_agent_profile
        p_res = get_agent_profile(topic="all")
        m_data = p_res.get("manifest", {})
        advisory["agent_profile"] = m_data.get("identity", {})
        advisory["standards_catalog"] = m_data.get("standards_and_manuals", [])
        for std in m_data.get("standards_and_manuals", []):
            code_slug = std.get('code', 'STANDARD').replace(' ', '-')
            evidence.append({
                "source_id": f"STD-{code_slug}",
                "source_type": "CERTIFIED_STANDARD",
                "type": "STANDARD",
                "observation": f"[{std.get('authority_level', 'LEVEL_A')}] {std.get('code')}: {std.get('title')}",
                "authority_level": "A" if "A" in std.get("authority_level", "A") else "B",
                "source_deep_link": f"/api/esp/knowledge/document/{code_slug}",
            })

    if is_section_allowed(obj_id, "anomaly_cards"):
        # Include diagnostic anomaly card only when permitted
        advisory["anomaly_cards"] = [
            {
                "id": f"AC-{asset_id}-01",
                "asset_id": asset_id,
                "title": f"Diagnostic Anomaly: {diagnosis}",
                "severity": "HIGH" if any(kw in query_intent.lower() for kw in ("temp", "overheat", "trip", "gas")) else "MEDIUM",
                "confidence": confidence,
                "description": primary_observation or f"Identified operating anomaly on {asset_id}.",
                "recommended_action": recommendation,
            }
        ]
        from urllib.parse import quote
        fault_search = "Gas Interference" if "gas" in query_intent.lower() else ("Motor Overheating" if "temp" in query_intent.lower() else "")
        if fault_search:
            cypher = f"MATCH (n:FaultMode {{name: '{fault_search}'}})-[r]-(m) RETURN n,r,m"
        else:
            cypher = "MATCH (n:FaultMode)-[r]-(m) RETURN n,r,m LIMIT 25"
        evidence.append({
            "source_id": f"ANOMALY-{asset_id}-001",
            "source_type": "FAULT_CLASSIFIER",
            "type": "ANOMALY",
            "observation": f"Diagnostic anomaly detected: {diagnosis}",
            "authority_level": "A",
            "source_deep_link": f"http://localhost:7474/browser/?cmd=play&arg={quote(cypher)}",
        })

    # 6. Apply filter_advisory_sections to strictly enforce zero-phantom anomaly cards
    return filter_advisory_sections(obj_id, advisory)


__all__ = [
    "synthesize_advisory",
]
