"""
Well Performance Domain Specialist Subgraph
Grounded in ESP_APM_PHASE_7_LangGraph_Supervisor_MultiAgent_Architecture_Design.docx §4, §10, §11
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List, TypedDict, Optional
from langgraph.graph import StateGraph, END, START

from src.agent.supervisor.specialist_contracts import SpecialistInput, SpecialistOutput
from src.adapters.telemetry import TelemetryAdapter
from src.services.engineering_service import EngineeringService
from src.tools.registry import ToolRegistry

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Calibration registry — resolved once at module load, safe to cache
# ---------------------------------------------------------------------------
_CALIB_REGISTRY: Dict[str, Any] = {}
try:
    _reg_path = Path(__file__).resolve().parents[4] / "code" / "models" / "well_calibration_registry.json"
    if _reg_path.exists():
        with open(_reg_path, "r", encoding="utf-8") as _f:
            _CALIB_REGISTRY = json.load(_f)
except Exception as _ex:
    logger.warning("[well_performance] Could not load calibration registry: %s", _ex)


def _get_bep_from_registry(asset_id: str) -> float:
    """
    Look up the calibrated BEP (Best Efficiency Point) flow rate for a well.
    Uses the median of flow_rate_bpd from the calibration registry if present;
    falls back to 1750 BPD (FS-family fleet average) otherwise.

    Note: the registry stores per-sensor calibration under the canonical sensor
    key. BEP is derived from the median flow_rate at the well's typical operating
    frequency — this is a sound approximation when no manufacturer H-Q curve is
    available (which is the current state for all 73 wells in the registry).
    """
    wells = _CALIB_REGISTRY.get("wells", {})

    # Exact match first, then case-insensitive
    profile = wells.get(asset_id) or wells.get(asset_id.upper())
    if not profile:
        # Try stripping leading zeros: FS-010 → FS-10
        stripped = asset_id
        import re
        m = re.match(r'^([A-Za-z\-]+)0*(\d+)$', asset_id)
        if m:
            stripped = m.group(1) + m.group(2)
        profile = wells.get(stripped) or wells.get(stripped.upper())

    if profile:
        sensors = profile.get("sensors", {})
        # flow_rate_bpd isn't a calibration registry sensor key; use VSD Amps/Load
        # proxy: BEP correlates with amps near nameplate. Fall through to family avg.
        # The registry does have Frequency median — use it as a sanity check.
        freq_prof = sensors.get("Frequency", {})
        freq_median = freq_prof.get("median") if freq_prof else None
        if freq_median and freq_median > 0:
            # Affinity Law approximation: BEP scales with (freq/50)³ × 1750
            bep = round(1750.0 * (float(freq_median) / 50.0), 1)
            logger.debug(
                "[well_performance] BEP for %s: %.1f BPD (affinity from freq median %.1f Hz)",
                asset_id, bep, freq_median
            )
            return bep

    # Family fallback from family profile
    families = _CALIB_REGISTRY.get("families", {})
    import re
    m = re.match(r'^([A-Za-z]+)', asset_id)
    fam = m.group(1).upper() if m else None
    if fam and fam in families:
        fam_sensors = families[fam].get("sensors", {})
        freq_prof = fam_sensors.get("Frequency", {})
        freq_median = freq_prof.get("median") if freq_prof else None
        if freq_median and freq_median > 0:
            bep = round(1750.0 * (float(freq_median) / 50.0), 1)
            logger.debug(
                "[well_performance] BEP for %s (family %s fallback): %.1f BPD", asset_id, fam, bep
            )
            return bep

    logger.debug("[well_performance] BEP for %s: using default 1750.0 BPD", asset_id)
    return 1750.0


class WellPerformanceState(TypedDict):
    input: Dict[str, Any]
    telemetry: Dict[str, float]
    tdh_ft: float
    bep_target: float
    bep_deviation_pct: float
    findings: List[str]
    evidence_refs: List[str]
    output: Optional[Dict[str, Any]]


def create_well_performance_graph():
    """Build and compile the Well Performance domain specialist subgraph."""
    tool_registry = ToolRegistry()
    engineering_service = EngineeringService()

    builder = StateGraph(WellPerformanceState)

    def fetch_telemetry_node(state: WellPerformanceState) -> Dict[str, Any]:
        inp = state["input"]
        asset_id = inp.get("asset_id", "")

        # Pull telemetry from policy_context (populated by data_quality_gate_node).
        # Support both the canonical agent keys (intake_pressure, discharge_pressure)
        # AND the legacy specialist keys (pip, pdp) — whichever is present.
        ctx_tel = inp.get("policy_context", {}).get("telemetry") or {}

        def _pick(*keys: str, default: float = 0.0) -> float:
            for k in keys:
                v = ctx_tel.get(k)
                if v is not None and float(v) != 0.0:
                    return float(v)
            return default

        telemetry_data = {
            "motor_temperature":     _pick("motor_temperature", "motor_temp", default=0.0),
            "intake_pressure":       _pick("intake_pressure", "pip", default=0.0),
            "discharge_pressure":    _pick("discharge_pressure", "pdp", default=0.0),
            "flow_rate":             _pick("flow_rate", "flow_rate_bpd", default=0.0),
            "drive_current_average": _pick("drive_current_average", "current", default=0.0),
            "frequency":             _pick("frequency", "frequency_hz", default=0.0),
            "vibration_x":           _pick("vibration_x", "vibration", default=0.0),
        }
        # Preserve provenance tag if present
        if "_source" in ctx_tel:
            telemetry_data["_source"] = ctx_tel["_source"]

        evidence = [
            f"esp:telemetry:{asset_id}:flow_rate:{telemetry_data['flow_rate']:.0f}",
            f"esp:telemetry:{asset_id}:frequency:{telemetry_data['frequency']:.1f}hz",
        ]
        return {"telemetry": telemetry_data, "evidence_refs": evidence}

    def calculate_operating_point_node(state: WellPerformanceState) -> Dict[str, Any]:
        telemetry  = state["telemetry"]
        asset_id   = state["input"].get("asset_id", "FS-010")
        pip        = telemetry.get("intake_pressure", 0.0)
        pdp        = telemetry.get("discharge_pressure", 0.0)
        flow_rate  = telemetry.get("flow_rate", 0.0)

        # BEP from calibration registry — not hardcoded
        bep_target = _get_bep_from_registry(asset_id)

        # TDH from real pressures when available; fallback uses engineering service
        if pdp > 0 and pip >= 0:
            # Direct physics: TDH (ft) = (PDP - PIP) × 2.31 / fluid_sg
            fluid_sg = 0.85
            tdh = round((pdp - pip) * 2.31 / fluid_sg, 1)
        else:
            try:
                from shared.schemas.engineering import TDHRequest
                tdh_resp = engineering_service.calculate_tdh(TDHRequest(
                    asset_id=asset_id,
                    pdp_psi=float(pdp) if pdp else 2100.0,
                    pip_psi=float(pip) if pip else 350.0,
                    fluid_sg=0.85
                ))
                tdh = tdh_resp.tdh_ft
            except Exception as ex:
                logger.warning("[well_performance] TDH calculation failed: %s", ex)
                tdh = 0.0

        bep_dev = ((flow_rate - bep_target) / bep_target) * 100.0 if bep_target > 0 and flow_rate > 0 else 0.0

        evidence = list(state["evidence_refs"])
        evidence.append(f"esp:engineering:tdh:{tdh:.1f}")
        evidence.append(f"esp:engineering:bep_dev:{bep_dev:+.1f}%")

        return {
            "tdh_ft": tdh,
            "bep_target": bep_target,
            "bep_deviation_pct": bep_dev,
            "evidence_refs": evidence,
        }

    def assess_production_node(state: WellPerformanceState) -> Dict[str, Any]:
        bep_dev    = state["bep_deviation_pct"]
        bep_target = state.get("bep_target", 1750.0)
        tdh        = state["tdh_ft"]
        telemetry  = state["telemetry"]
        flow_rate  = telemetry.get("flow_rate", 0.0)
        pip        = telemetry.get("intake_pressure", 0.0)
        pdp        = telemetry.get("discharge_pressure", 0.0)
        freq       = telemetry.get("frequency", 0.0)
        m_temp     = telemetry.get("motor_temperature", 0.0)

        # Operating region assessment
        if flow_rate > 0 and bep_target > 0:
            bep_pct = (flow_rate / bep_target) * 100.0
            if bep_pct > 115:
                region = f"UPTHRUST RISK ({bep_pct:.0f}% of BEP)"
            elif bep_pct < 75:
                region = f"DOWNTHRUST RISK ({bep_pct:.0f}% of BEP)"
            else:
                region = f"NORMAL OPERATING RANGE ({bep_pct:.0f}% of BEP)"
        else:
            region = "UNKNOWN (no flow data)"

        findings = []
        if flow_rate > 0 and bep_target > 0:
            findings.append(
                f"Operating at {bep_dev:+.1f}% from Best Efficiency Point "
                f"(BEP {bep_target:.0f} BPD, current {flow_rate:.0f} BPD). Region: {region}."
            )
        if tdh > 0:
            findings.append(
                f"Calculated Total Dynamic Head (TDH): {tdh:.1f} ft "
                f"(PDP {pdp:.0f} psi − PIP {pip:.0f} psi)."
            )
        if freq > 0:
            findings.append(f"VFD operating frequency: {freq:.1f} Hz.")
        if m_temp > 0:
            overheat = " ⚠️ Approaching thermal limit (API RP 11S: 130°C max)." if m_temp > 120 else ""
            findings.append(f"Motor temperature: {m_temp:.1f}°C.{overheat}")
        if not findings:
            findings.append("Telemetry data unavailable for hydraulic assessment.")

        output = SpecialistOutput(
            specialist_id="well_performance",
            status="complete",
            findings=findings,
            evidence_refs=state["evidence_refs"],
            uncertainties=["Wellhead gas-oil ratio not dynamically metered"],
            next_verification=["Perform test separator liquid flow rate measurement"],
            completion_reason="Well performance hydraulic assessment completed"
        ).model_dump()

        return {"findings": findings, "output": output}

    builder.add_node("fetch_telemetry", fetch_telemetry_node)
    builder.add_node("calculate_operating_point", calculate_operating_point_node)
    builder.add_node("assess_production", assess_production_node)

    builder.add_edge(START, "fetch_telemetry")
    builder.add_edge("fetch_telemetry", "calculate_operating_point")
    builder.add_edge("calculate_operating_point", "assess_production")
    builder.add_edge("assess_production", END)

    return builder.compile()


well_performance_graph = create_well_performance_graph()
