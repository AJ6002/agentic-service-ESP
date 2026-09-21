"""
Unified SCADA Chart Data Factory for ESP Operations Platform
Single Source of Truth for:
1. Frontend Dashboard Widgets (PumpPerformanceCurve, OperatingEnvelope, ForensicsTimeline)
2. Agent Jane Live Contextual Chart Narration & Inline Payloads
3. Tool Execution (explain_widget)

Zero Split-Brain Guarantee: The dashboard and the agent consume the exact same underlying logic.
"""

from typing import Dict, Any, Optional, List
import math
import logging

logger = logging.getLogger(__name__)


def build_hq_curve_data(asset_id: str, freq: Optional[float] = None) -> Dict[str, Any]:
    """
    Computes standard H-Q pump curve, power envelope, and real operating point from live telemetry.
    The single canonical source of truth for pump curve calculations.
    """
    from src.api.rest.esp_routes import (
        _normalize_well_id,
        _normalize_calibration_key,
        _get_registry,
        _get_raw_telemetry
    )

    clean_id = _normalize_well_id(asset_id)
    raw = _get_raw_telemetry(clean_id)
    calib_key = _normalize_calibration_key(clean_id)
    reg = _get_registry()
    wdata = reg.get("wells", {}).get(calib_key, reg.get("wells", {}).get("FS-31", {}))

    operating_freq = float(freq) if freq is not None else float(raw.get("Frequency", raw.get("frequency_hz", 50.0)))
    pip = float(raw.get("Inp bar/psi", raw.get("intake_pressure_psi", 650.0)))
    pdp = float(raw.get("Disch pr. Bar/psi", raw.get("pressure_psi", 2100.0)))

    # Check for live Digital Twin asset specifications and cubic curve coefficients
    collector_asset = None
    collector_vfm = None
    try:
        from src.pipeline.mqtt_collector import get_mqtt_collector
        col = get_mqtt_collector()
        collector_asset = col.get_well_asset(clean_id)
        collector_vfm = col.get_well_vfm(clean_id)
    except Exception:
        pass

    if collector_asset and "COEFF_D" in collector_asset:
        coeff_a = float(collector_asset.get("COEFF_A", -0.00005))
        coeff_b = float(collector_asset.get("COEFF_B", -0.005))
        coeff_c = float(collector_asset.get("COEFF_C", -0.5))
        coeff_d = float(collector_asset.get("COEFF_D", 1100.0))
        stages = int(collector_asset.get("STAGES", 150))
        pump_model = collector_asset.get("PUMP_TYPE", wdata.get("pump_model", "Centrilift XP-1650"))
        
        freq_mult = operating_freq / 50.0 if operating_freq > 10.0 else 1.0
        # Build 3rd-degree cubic flow curve across head span: Q(H) = A*H^3 + B*H^2 + C*H + D
        points = []
        for h_norm in [45, 42, 38, 35, 32, 28, 25, 22, 18, 15, 12, 10, 8, 5]:
            q_norm = (coeff_a * (h_norm**3)) + (coeff_b * (h_norm**2)) + (coeff_c * h_norm) + coeff_d
            if q_norm < 10.0:
                continue
            q_flow = round(q_norm * freq_mult, 1)
            h_total = round(h_norm * (freq_mult**2) * stages, 1)
            bhp = round((q_flow * h_total * 0.858) / (135740.0 * 0.65), 1)
            eff = round(72.0 * math.sin(max(0.1, min(1.0, (q_norm / max(1.0, coeff_d)))) * math.pi), 1)
            points.append({
                "flow_bpd": q_flow,
                "head_ft": max(0.0, h_total),
                "power_bhp": max(0.0, bhp),
                "efficiency_pct": max(0.0, eff)
            })
        points.sort(key=lambda p: p["flow_bpd"])
        rated_bep = round(coeff_d * 0.65 * freq_mult, 1)
        rated_head = round(22.0 * (freq_mult**2) * stages, 1)
    else:
        pump_model = wdata.get("pump_model", "Centrilift XP-1650")
        bep_rate = float(wdata.get("bep_rate", 1650))
        bep_head = float(wdata.get("bep_head", 5400))
        freq_ratio = operating_freq / 60.0 if operating_freq > 0 else 0.833
        rated_bep = bep_rate * freq_ratio
        rated_head = bep_head * (freq_ratio ** 2)
        coeff_a, coeff_b, coeff_c, coeff_d, stages = -0.00005, -0.005, -0.5, 1100.0, 150

        points = []
        for q_pct in range(20, 160, 10):
            flow = round(rated_bep * (q_pct / 100.0), 1)
            head = round(rated_head * (1.25 - 0.25 * ((q_pct / 100.0) ** 2)), 1)
            bhp = round(120.0 * ((q_pct / 100.0) * freq_ratio), 1)
            eff = round(72.0 * math.sin((q_pct / 140.0) * math.pi), 1)
            points.append({
                "flow_bpd": flow,
                "head_ft": max(0.0, head),
                "power_bhp": bhp,
                "efficiency_pct": max(0.0, eff)
            })

    # Real operating point from live telemetry or VFM
    if collector_vfm and "liquid_flow_rate_bpd" in collector_vfm:
        curr_flow = float(collector_vfm.get("liquid_flow_rate_bpd", 0.0))
        drv = collector_vfm.get("derived_parameters", {})
        curr_head = float(drv.get("DRV_TOTAL_HEAD_FT") or collector_vfm.get("total_head_ft", (pdp - pip) * 2.31))
        live_bhp = float(collector_vfm.get("hydraulic_power_bhp", 0.0))
        diff_psi = float(drv.get("DRV_DIFF_PRS_PSI", max(0.0, pdp - pip)))
    else:
        curr_flow = float(raw.get("Liquid Rate (BPD)", raw.get("flow_rate_bpd", round(rated_bep * 0.92, 1))))
        diff_psi = max(0.0, pdp - pip)
        curr_head = round(diff_psi * 2.31, 1)
        live_bhp = round((curr_flow * curr_head * 0.858) / (135740.0 * 0.65), 1)

    min_bep_bpd = round(rated_bep * 0.70, 1)
    max_bep_bpd = round(rated_bep * 1.20, 1)
    in_bep = min_bep_bpd <= curr_flow <= max_bep_bpd

    min_cont = round(rated_bep * 0.35, 1)
    max_runout = round(rated_bep * 1.35, 1)

    thrust = (
        "Downthrust (Left-Hand / Recirculation)" if curr_flow < min_bep_bpd
        else ("Upthrust (Right-Hand / Runout)" if curr_flow > max_bep_bpd else "Balanced (Nominal BEP)")
    )
    status_msg = (
        "IN RECOMMENDED BEP CORRIDOR" if in_bep
        else ("OPERATING LEFT OF BEP (Recirculation Risk)" if curr_flow < min_bep_bpd else "OPERATING RIGHT OF BEP (Upthrust Risk)")
    )

    summary = (
        f"Well {clean_id} ({pump_model}) is operating at {round(curr_flow, 1)} BPD with Total Dynamic Head of {curr_head} ft "
        f"(Intake: {round(pip, 1)} psi, Discharge: {round(pdp, 1)} psi) at {round(operating_freq, 1)} Hz. "
        f"Operating status: {status_msg}. Thrust regime: {thrust}."
    )

    return {
        "status": "SUCCESS",
        "asset_id": clean_id,
        "well_id": clean_id,
        "pump_model": pump_model,
        "frequency_hz": round(operating_freq, 2),
        "stages": stages,
        "coefficients": {
            "a": coeff_a,
            "b": coeff_b,
            "c": coeff_c,
            "d": coeff_d
        },
        "operating_point": {
            "flow_bpd": round(curr_flow, 1),
            "head_ft": curr_head,
            "head_psi": round(diff_psi, 1),
            "power_bhp": live_bhp,
            "in_bep_range": in_bep,
            "is_in_recommended_range": in_bep,
            "intake_pressure_psi": round(pip, 1),
            "discharge_pressure_psi": round(pdp, 1)
        },
        "bep_range": {
            "optimal_bpd": round(rated_bep, 1),
            "optimal_rate_bpd": round(rated_bep, 1),
            "optimal_head_ft": round(rated_head, 1),
            "min_flow_bpd": min_bep_bpd,
            "max_flow_bpd": max_bep_bpd
        },
        "minimum_continuous_flow_bpd": min_cont,
        "maximum_runout_flow_bpd": max_runout,
        "thrust_regime": thrust,
        "operating_status": status_msg,
        "summary_narration": summary,
        "curve": points,
        "curve_points": points
    }


def build_operating_envelope_data(asset_id: str) -> Dict[str, Any]:
    """
    Computes statistical P10/P50/P90 boundary monitoring and live channel evaluations.
    """
    from src.api.rest.esp_routes import get_well_envelope, _normalize_well_id
    clean_id = _normalize_well_id(asset_id)
    envelope = get_well_envelope(clean_id)

    # Add summary narration for Agent Jane
    out_of_spec = [e["parameter"] for e in envelope.get("evaluations", []) if e.get("status") == "OUT_OF_SPEC"]
    if out_of_spec:
        summary = f"Well {clean_id} operating envelope has {len(out_of_spec)} channel(s) breaching P10-P90 corridors: {', '.join(out_of_spec)}."
    else:
        summary = f"Well {clean_id} operating envelope is fully nominal across all 13 channels within P10-P90 statistical boundaries."

    envelope["summary_narration"] = summary
    return envelope


def build_forensics_timeline_data(asset_id: str, time_card: str = "1h", source: str = "historian") -> Dict[str, Any]:
    """
    Computes dynamic divergence tipping timeline and culprit tracks for incident forensics.
    """
    from src.api.rest.esp_routes import get_forensics_timeline, _normalize_well_id
    clean_id = _normalize_well_id(asset_id)
    timeline = get_forensics_timeline(clean_id, time_card=time_card, source=source)

    verdict = timeline.get("verdict", "Nominal dynamic stability")
    culprits = timeline.get("culprits", [])
    culprit_names = [c.get("name", "Sensor") for c in culprits[:3]]
    trip_msg = "Trip event detected" if timeline.get("trip_detected") else "No trip observed in time window"

    summary = (
        f"Forensics timeline for {clean_id} ({time_card} window): {verdict}. {trip_msg}. "
        f"Leading divergence culprits: {', '.join(culprit_names) if culprit_names else 'None'}."
    )
    timeline["summary_narration"] = summary
    return timeline


def build_subsystem_equalizer_data(
    asset_id: str,
    time_bracket: str = "1h",
    source: str = "historian"
) -> Dict[str, Any]:
    """
    Computes 4-subsystem deviations (% delta vs P50 calibration baseline),
    wellbore depth profile (hydrostatic pressure gradient),
    and 3-tier cosine differential diagnosis.
    Single source of truth for Visual 2 for dashboard & Agent Jane.
    """
    from src.api.rest.esp_routes import get_well_forensics, _normalize_well_id
    clean_id = _normalize_well_id(asset_id)
    forensics = get_well_forensics(clean_id, source=source, time_bracket=time_bracket)

    subsystems = forensics.get("subsystems", [])
    dp = forensics.get("depth_profile", {})
    diag = forensics.get("differential_diagnosis", {})
    top_match = diag.get("top_match", {})
    top_fault = top_match.get("fault", "Nominal Operation")
    sim = top_match.get("similarity", 1.0)
    geom_source = dp.get("geometry_source", "GENERIC_DEFAULT")
    psd_ft = dp.get("psd_ft", 4850)
    perfs_ft = dp.get("perfs_ft", 5200)

    dev_map = {s.get("domain", "").lower(): s.get("deviation", 0.0) for s in subsystems}
    dev_hyd = dev_map.get("hydraulic", 0.0)
    dev_elec = dev_map.get("electrical", 0.0)
    dev_therm = dev_map.get("thermal", 0.0)
    dev_mech = dev_map.get("mechanical", 0.0)

    summary = (
        f"Subsystem Health Equalizer for {clean_id}: Top match {top_fault} (Cosine Similarity: {sim:.2f}). "
        f"Deviations: Hydraulic {dev_hyd:+.1f}%, Electrical {dev_elec:+.1f}%, "
        f"Thermal {dev_therm:+.1f}%, Mechanical {dev_mech:+.1f}%. "
        f"Depth profile source: {geom_source} ({psd_ft} ft PSD, {perfs_ft} ft Perfs)."
    )

    forensics["summary_narration"] = summary
    return forensics

