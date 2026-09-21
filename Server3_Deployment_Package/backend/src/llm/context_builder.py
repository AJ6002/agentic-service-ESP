"""
Compact Context Builder — Phase 10: LLM Layer Architecture
Grounded in ESP APM LLM Architecture Design §2

Critical for small (4B) models: transforms raw telemetry arrays and large evidence
dumps into a compact, high-density JSON context window.

A 4B parameter model cannot reason over 10,000 raw telemetry points.
This builder compresses inputs to a single structured JSON object under ~800 tokens.

Output format:
{
  "asset_id": "FS-031",
  "objective": "production_decline_analysis",
  "telemetry_summary": {
    "flow": {"current": 735.7, "trend": "declining", "qod": "good"},
    "intake_pressure": {"current": 236.5, "trend": "stable"},
    ...
  },
  "engineering": {"pump_delta_p": 1647.2, "frequency_hz": 46.06},
  "ml_scores": {"degradation_probability": 0.72},
  "frozen_evidence_ids": ["EV-001", "EV-007"],
  "specialist_findings": ["Finding A", "Finding B"],
  "safety_constraints": ["ADVISORY-ONLY — no direct actuator commands"],
  "conflicts_summary": ["ML fault confidence disagrees with physics model at p=0.15"]
}
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Max evidence items to include in compact context (prevents token overflow)
MAX_EVIDENCE_REFS = 8
MAX_SPECIALIST_FINDINGS = 6
MAX_CONFLICT_SUMMARY = 4


class CompactContextBuilder:
    """
    Transforms raw AgentState context into a compact, Qwen3 4B-safe JSON payload.
    
    LangGraph Supervisor
          ↓
    CompactContextBuilder.build(state)
          ↓
    compact_context: Dict (< 800 tokens when serialised)
          ↓
    LLM Adapter → Prompt Builder → Qwen3 4B
    """

    def build(
        self,
        asset_id: str,
        objective_id: str,
        asset_context: Optional[Dict[str, Any]] = None,
        telemetry: Optional[Dict[str, Any]] = None,
        engineering: Optional[Dict[str, Any]] = None,
        model_outputs: Optional[Dict[str, Any]] = None,
        vfd_diagnostic: Optional[Dict[str, Any]] = None,
        specialist_results: Optional[List[Dict[str, Any]]] = None,
        evidence_refs: Optional[List[str]] = None,
        safety_constraints: Optional[List[str]] = None,
        conflicts: Optional[List[Any]] = None,
        conversation_history: Optional[List[Dict[str, Any]]] = None,
        episodic_memory: Optional[Dict[str, Any]] = None,
        telemetry_status: Optional[Dict[str, Any]] = None,
        knowledge: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Build a compact context dict from all available supervisor state components.
        """
        compact: Dict[str, Any] = {
            "asset_id": asset_id,
            "objective": objective_id,
        }

        # --- Asset Hardware & Installation Context ---
        if asset_context:
            compact["asset_nameplate"] = {
                "pump_model": asset_context.get("pump_model") or "Not specified",
                "motor_rating_hp": asset_context.get("motor_rating_hp") or "Not specified",
                "nameplate_current_amps": asset_context.get("nameplate_current_amps") or "Not specified",
                "installation_depth_ft": asset_context.get("installation_depth_ft") or "Not specified",
                "be_point_bpd": asset_context.get("be_point_bpd") or "Not specified",
                "status": asset_context.get("status", "ACTIVE"),
            }

        # --- Telemetry Summary ---
        if telemetry:
            compact["telemetry_summary"] = self._compress_telemetry(telemetry)

        # --- Telemetry data-source honesty flag (X1) ---
        # When the telemetry handoff verdict is not LIVE (FALLBACK/DEGRADED/MOCK), the
        # numbers in telemetry_summary are synthetic placeholders, not measured readings.
        # Tell the model explicitly so it never reports them as real values — the
        # live_fault_diagnosis (VFD engine) remains the trustworthy signal in that case.
        if telemetry_status:
            status_val = str(telemetry_status.get("status", "")).upper()
            if status_val and status_val != "LIVE":
                compact["telemetry_data_source"] = {
                    "status": status_val,
                    "warning": (
                        "Telemetry values above are synthetic/unavailable "
                        f"({status_val}) — do NOT present them as measured readings. "
                        "Base the assessment on live_fault_diagnosis and state that live "
                        "telemetry was unavailable."
                    ),
                }

        # --- Engineering Snapshot ---
        if engineering:
            compact["engineering"] = self._compress_engineering(engineering)

        # --- ML/Model Scores (legacy health-index path) ---
        if model_outputs:
            compact["ml_scores"] = self._compress_model_outputs(model_outputs)

        # --- ESP_APM_models Live VFD Diagnosis (sole source of truth for live fault
        # classification — see collect_from_vfd_diagnostic() in evidence/collector.py).
        # BUG FIX (2026-09-02): This was previously never threaded into the compact
        # context at all, even though the evidence pack (and evidence_refs list, after
        # the earlier cap-priority fix) correctly carried EVID-VFD-* items. The LLM
        # prompt only ever saw bare evidence ID strings with no attached fault content,
        # so a well showing a live CRITICAL fault (e.g. High Backpressure, health 5.6)
        # still produced a "nominal, confidence 1.0" advisory — the model never actually
        # saw the diagnosis text, only an opaque ID. This is the fix for that.
        if vfd_diagnostic:
            compact["live_fault_diagnosis"] = self._compress_vfd_diagnostic(vfd_diagnostic)

        # --- Specialist Findings ---
        if specialist_results:
            findings = []
            for res in specialist_results:
                for f in res.get("findings", [])[:2]:  # max 2 per specialist
                    findings.append(f)
            compact["specialist_findings"] = findings[:MAX_SPECIALIST_FINDINGS]

        # --- Evidence References ---
        if evidence_refs:
            compact["frozen_evidence_ids"] = evidence_refs[:MAX_EVIDENCE_REFS]

        # --- Safety Constraints ---
        if safety_constraints:
            compact["safety_constraints"] = safety_constraints[:3]

        # --- Conflict Summaries ---
        if conflicts:
            compact["conflicts_summary"] = self._compress_conflicts(conflicts)

        # --- Conversation History (A3.T3) ---
        # Compact: role + first 120 chars of content only — never re-dump evidence.
        # Bounded to last 10 turns. Empty list and None both skip this key.
        if conversation_history:
            compact["conversation_history"] = [
                {
                    "role": t.get("role", "user"),
                    "content": str(t.get("content", ""))[:120],
                }
                for t in conversation_history[-10:]
            ]

        # --- Episodic Well Memory (C1.T2) ---
        # High-signal summary of prior diagnoses and recommendations for this asset across sessions.
        if episodic_memory:
            compact["episodic_well_memory"] = {
                "last_assessed": episodic_memory.get("last_updated", "Unknown"),
                "prior_objective": episodic_memory.get("last_objective", "N/A"),
                "prior_diagnosis": episodic_memory.get("last_diagnosis", "Nominal"),
                "prior_recommendation": episodic_memory.get("last_recommendation", "Continue monitoring"),
            }

        # --- Knowledge Base Context (OP06 / Diagnostic Guidance) ---
        if knowledge:
            compact["governing_knowledge_limits"] = [
                {
                    "param": k.get("parameter", "Unknown"),
                    "envelope": k.get("normal_envelope", "Nominal"),
                    "warning": k.get("warning_threshold", "N/A"),
                    "trip": k.get("tripping_limit", "N/A"),
                    "standard": k.get("governing_standard", "API RP 11S")
                }
                for k in knowledge[:4]
            ]

        logger.debug(
            f"CompactContextBuilder: built compact context for {asset_id}/{objective_id} "
            f"with keys: {list(compact.keys())}"
        )
        return compact

    def build_from_agent_state(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convenience builder that extracts fields directly from a LangGraph AgentState dict.
        """
        ctx = state.get("context", {})
        return self.build(
            asset_id=state.get("request", {}).get("asset_id", "UNKNOWN"),
            objective_id=state.get("run", {}).get("objective_id", "UNKNOWN"),
            asset_context=ctx.get("asset"),
            telemetry=ctx.get("telemetry"),
            engineering=ctx.get("engineering"),
            model_outputs=ctx.get("models"),
            vfd_diagnostic=ctx.get("vfd_diagnostic"),
            specialist_results=state.get("specialist_results", []),
            evidence_refs=state.get("evidence_refs", []),
            safety_constraints=state.get("safety_state", {}).get("blocked_actions", []),
            conflicts=[c.model_dump() if hasattr(c, "model_dump") else c
                       for c in state.get("conflicts", [])],
            conversation_history=ctx.get("history") or None,
            episodic_memory=ctx.get("episodic_memory") or None,
            telemetry_status=ctx.get("provenance", {}).get("telemetry") or None,
            knowledge=ctx.get("knowledge") or None,
        )


    # ------------------------------------------------------------------
    # Internal compression helpers
    # ------------------------------------------------------------------

    def _compress_telemetry(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        """
        Reduce raw telemetry dict to key signal summaries with trend direction.
        Input: flat dict of signal_name -> value (may include lists/arrays).
        Output: compact dict of signal_name -> {current, trend, qod}
        """
        SIGNAL_MAP = {
            "flow_rate": "flow",
            "liquid_rate": "flow",
            "intake_pressure": "intake_pressure",
            "pip": "intake_pressure",
            "discharge_pressure": "discharge_pressure",
            "pdp": "discharge_pressure",
            "motor_temperature": "motor_temp",
            "motor_temp": "motor_temp",
            "current": "drive_current",
            "drive_current": "drive_current",
            "frequency": "frequency_hz",
            "vibration": "vibration",
            "gor": "gor",
            "wc": "water_cut",
        }

        summary: Dict[str, Any] = {}
        for raw_key, val in raw.items():
            canonical = SIGNAL_MAP.get(raw_key.lower(), raw_key.lower())
            if isinstance(val, dict):
                # Pass through pre-computed statistical summaries
                summary[canonical] = {
                    k: (round(v, 4) if isinstance(v, float) else v)
                    for k, v in val.items()
                }
            elif isinstance(val, (int, float)):
                summary[canonical] = {"current": round(float(val), 2), "trend": "unknown"}
            elif isinstance(val, list) and len(val) >= 2:
                # Derive simple trend from first and last values
                first, last = float(val[0]), float(val[-1])
                if last < first * 0.95:
                    trend = "declining"
                elif last > first * 1.05:
                    trend = "rising"
                else:
                    trend = "stable"
                summary[canonical] = {"current": round(last, 2), "trend": trend}

        return summary

    def _compress_engineering(self, eng: Dict[str, Any]) -> Dict[str, Any]:
        """Keep key engineering KPIs and equipment specifications relevant to diagnosis."""
        keep_numeric = [
            "tdh_ft", "pump_delta_p", "bep_flow_rate", "bep_deviation_pct",
            "frequency_hz", "frequency", "efficiency_pct", "motor_hp",
            "nameplate_amps", "bep_bpd", "be_point_bpd", "installation_depth_ft",
            "motor_rating_hp", "nameplate_current_amps"
        ]
        keep_string = ["pump_model", "asset_id", "status", "asset_type"]

        res: Dict[str, Any] = {}
        for k, v in eng.items():
            if k in keep_numeric and isinstance(v, (int, float)):
                res[k] = round(float(v), 2)
            elif k in keep_string and isinstance(v, str):
                res[k] = v
            elif isinstance(v, (int, float, str)):
                res[k] = round(float(v), 2) if isinstance(v, float) else v
        return res

    def _compress_model_outputs(self, models: Dict[str, Any]) -> Dict[str, Any]:
        """Compress ML model outputs to key probability scores."""
        keep = ["degradation_probability", "anomaly_score", "risk_24h",
                "confidence", "predicted_fault_class", "health_index"]
        result = {}
        for k, v in models.items():
            if k in keep:
                result[k] = round(float(v), 3) if isinstance(v, (int, float)) else v
        return result

    def _compress_vfd_diagnostic(self, vfd: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compress ESP_APM_models.WellDiagnosticEngine's live diagnosis into a compact
        dict the LLM can actually read and cite. This is the highest-value single piece
        of evidence in the context — a live, physics-informed fault classification —
        so it is kept as its own top-level compact_context key ("live_fault_diagnosis"),
        never buried inside a generic list the model might skim past.
        """
        diag = vfd.get("diagnostic") or {}
        ml_anom = vfd.get("ml_anomaly") or {}
        root_causes = diag.get("root_cause_drivers") or []
        root_cause_str = "; ".join(
            f"{d[0]}: {d[1]}" for d in root_causes if isinstance(d, (list, tuple)) and len(d) == 2
        )
        result = {
            "primary_fault": diag.get("primary_fault", "Normal Operation"),
            "confidence": diag.get("confidence", "N/A"),
            "health_score": diag.get("health_score"),
            "status": diag.get("status", "").replace("🟢", "").replace("🟡", "").replace("🔴", "").strip(),
            "est_time_to_trip": diag.get("est_time_to_trip", "N/A"),
        }
        if diag.get("description"):
            result["description"] = diag["description"][:200]
        if diag.get("action_advisory"):
            result["recommended_action"] = diag["action_advisory"][:200]
        if root_cause_str:
            result["root_cause_drivers"] = root_cause_str[:200]
        if ml_anom.get("is_anomaly"):
            result["anomaly_flag"] = f"Independently confirmed anomalous (p={ml_anom.get('anomaly_probability', 0):.2f})"
        return result

    def _compress_conflicts(self, conflicts: List[Any]) -> List[str]:
        """Summarise conflicts as brief strings for the model."""
        summaries = []
        for c in conflicts[:MAX_CONFLICT_SUMMARY]:
            if isinstance(c, dict):
                ctype = c.get("conflict_type", "CONFLICT")
                auth = c.get("authority_comparison", "")
                summaries.append(f"{ctype}: {auth}"[:120])
            elif hasattr(c, "conflict_type"):
                summaries.append(f"{c.conflict_type}: {c.authority_comparison}"[:120])
            else:
                summaries.append(str(c)[:80])
        return summaries
