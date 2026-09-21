"""
13-Fault Diagnostic Classification Engine Component
===================================================
Physics-informed multi-criteria evaluation engine for diagnosing the 13 specific ESP failure modes:
1. Dry-Well Pump Off
2. Blocked Intake
3. Scale or Pump Wear
4. Sand Ingestion
5. Bearing Degradation
6. High Viscosity Cold Start
7. High Backpressure
8. Open Choke
9. Undervoltage
10. Phase Imbalance
11. Motor Overload
12. Power Loss
13. Sensor Drift
"""

from typing import Dict, List, Tuple, Optional, Any


FAULT_DEFINITIONS = {
    "Gas Interference": {
        "severity": "CRITICAL",
        "description": "High free gas volume at pump intake causing gas locking, severe head loss, underload cycling, and thermal elevation.",
        "action": "Increase casing gas venting, lower drive frequency, or adjust backpressure choke to stabilize intake pressure."
    },
    "Dry-Well Pump Off": {
        "severity": "CRITICAL",
        "description": "Fluid level in well has dropped below pump intake; pump running dry without fluid cooling.",
        "action": "Shut down or reduce frequency immediately to prevent motor burnout; allow well fluid recovery."
    },
    "Blocked Intake": {
        "severity": "CRITICAL",
        "description": "Debris, scale, or asphaltene plugging pump intake screen; fluid flow choked.",
        "action": "Backwash intake screen, adjust surface choke, or pull ESP for mechanical cleanout."
    },
    "Scale or Pump Wear": {
        "severity": "WARNING",
        "description": "Impeller stage erosion or mineral scale build-up causing hydraulic head degradation.",
        "action": "Schedule chemical scale descaling treatment or plan pump stage replacement."
    },
    "Sand Ingestion": {
        "severity": "CRITICAL",
        "description": "Solids/sand production causing impeller erosion, friction torque surges, and erratic vibration.",
        "action": "Flush well with clean fluid; install sand screens or downhole desander."
    },
    "Bearing Degradation": {
        "severity": "CRITICAL",
        "description": "Radial or thrust bearing mechanical wear causing high vibration and internal friction heating.",
        "action": "Plan ESP changeout before catastrophic mechanical shaft seizure occurs."
    },
    "High Viscosity Cold Start": {
        "severity": "WARNING",
        "description": "High crude oil viscosity/emulsion at cold start causing extreme motor starting torque and current.",
        "action": "Soft-ramp VFD frequency slowly; circulate hot oil or diluent to reduce crude viscosity."
    },
    "High Backpressure": {
        "severity": "WARNING",
        "description": "Flowline blockage, closed surface valves, or hydrate restriction elevating discharge pressure.",
        "action": "Check surface choke line, separator inlet, and manifold valves for restrictions."
    },
    "Open Choke": {
        "severity": "WARNING",
        "description": "Surface choke open too wide causing runout flow, high motor amperage, and low head.",
        "action": "Trim surface choke orifice to restore pump operating backpressure."
    },
    "Undervoltage": {
        "severity": "CRITICAL",
        "description": "Surface power supply/transformer voltage sag causing elevated motor current draw and heating.",
        "action": "Check surface transformer tap settings and power grid stability; balance bus voltage."
    },
    "Phase Imbalance": {
        "severity": "CRITICAL",
        "description": "Voltage or current unbalance across phases creating reverse magnetic fields, overheating, and vibration.",
        "action": "Perform downhole cable insulation Megger test and check surface VFD output phase balance."
    },
    "Motor Overload": {
        "severity": "CRITICAL",
        "description": "Motor operating continuously above rated nameplate amperage; imminent thermal trip.",
        "action": "Reduce VFD frequency by 3–5 Hz immediately to shed electrical load and cool motor."
    },
    "Power Loss": {
        "severity": "CRITICAL",
        "description": "Total power interruption or automated VFD trip; pump stopped.",
        "action": "Investigate surface breaker/VFD fault code before attempting restart."
    },
    "Sensor Drift": {
        "severity": "WATCHLIST",
        "description": "Sensor output flatlined, stuck, or drifted to non-physical range.",
        "action": "Recalibrate downhole gauge telemetry or replace surface pressure/temperature transmitter."
    },
    "Broken Shaft": {
        "severity": "CRITICAL",
        "description": "Mechanical shaft shear, coupling failure, or decoupled impeller; motor spinning at operating speed with zero hydraulic lift, underloaded current, and collapsed BPD flow rate.",
        "action": "Shut down VFD immediately to prevent motor free-spinning damage; schedule workover unit for ESP changeout."
    }
}


class FaultClassificationEngine:
    """
    Diagnostic Classification Engine:
    Evaluates normalized features, raw values, and physical dynamics to classify the 13 specific well faults.
    """

    @staticmethod
    def diagnose(
        well_id: str,
        norm_data: Dict[str, float],
        raw_data: Dict[str, float],
        dynamics: Dict[str, float],
        profile: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Evaluates physical and statistical evidence for all 13 failure modes.
        """
        sensors_prof = profile.get("sensors", {})

        # ── Safe cast helper ────────────────────────────────────────────────
        def _f(key: str, default: float) -> float:
            v = raw_data.get(key, default)
            if v is None:
                return default
            try:
                import math
                fv = float(v)
                return default if math.isnan(fv) or math.isinf(fv) else fv
            except (TypeError, ValueError):
                return default

        # ── VFD STS: '[*]' = running (1), '' or '0' = stopped (0) ─────────
        def _vfd(key: str) -> float:
            v = str(raw_data.get(key, "1")).strip()
            if v in ("", "0", "nan", "None", "STOP", "FAULT"):
                return 0.0
            return 1.0  # '[*]', '1', 'RUN', or any non-zero string = running

        # Raw values (all safely cast to float)
        inp    = _f("Inp bar/psi",         100.0)
        disch  = _f("Disch pr. Bar/psi",  1000.0)
        amps   = _f("VSD Amps/Load",        50.0)
        volt   = _f("Volt",               400.0)
        freq   = _f("Frequency",            50.0)
        vib    = _f("Vibration G's-Vx",     0.1)
        leak   = _f("Leak Current Ct",       5.0)
        m_temp = _f("Motor temp \u00b0C",         70.0)
        i_temp = _f("Int temp \u00b0C",           50.0)
        whp    = _f("WHP (PSI)",            50.0)
        flp    = _f("FLP (PSI)",            50.0)
        ap     = _f("AP (PSI)",             10.0)
        vfd_sts = _vfd("VFD STS")

        # Dynamics
        delta_p  = dynamics.get("delta_p",          900.0)
        torque   = dynamics.get("torque_proxy",        1.0)
        dt_slope = dynamics.get("thermal_rate_hr",     0.0)
        try:
            delta_p  = float(delta_p)  if delta_p  is not None else 900.0
            torque   = float(torque)   if torque   is not None else 1.0
            dt_slope = float(dt_slope) if dt_slope is not None else 0.0
        except (TypeError, ValueError):
            delta_p, torque, dt_slope = 900.0, 1.0, 0.0


        # Baseline references
        amps_med = sensors_prof.get("VSD Amps/Load", {}).get("median", 50.0)
        disch_med = sensors_prof.get("Disch pr. Bar/psi", {}).get("median", 1500.0)
        inp_med = sensors_prof.get("Inp bar/psi", {}).get("median", 400.0)
        volt_med = sensors_prof.get("Volt", {}).get("median", 400.0)
        vib_med = sensors_prof.get("Vibration G's-Vx", {}).get("median", 0.1)
        whp_med = sensors_prof.get("WHP (PSI)", {}).get("median", 50.0)
        flp_med = sensors_prof.get("FLP (PSI)", {}).get("median", 45.0)
        m_temp_med = sensors_prof.get("Motor temp °C", {}).get("median", 70.0)
        head_med = max(200.0, disch_med - inp_med)

        scores = {}
        drivers = {}

        # ─────────────────────────────────────────────────────────────────────
        # ADAPTIVE RELATIVE THRESHOLDS
        # All rules compare sensor values as % deviation from each well's OWN
        # historical baseline median — so FS-28 (Inp~305 PSI, Amps~83 A) and
        # FNW-01 (Inp~80 PSI, Amps~25 A) both fire correctly without any
        # hardcoded absolute cut-off values.
        # ─────────────────────────────────────────────────────────────────────

        # Relative deviation helpers (safe, baseline-adaptive)
        _bv = lambda v, b: (v / max(b, 0.1))        # ratio: current / baseline
        _pct = lambda v, b: (_bv(v,b) - 1.0) * 100  # % change from baseline

        # Vibration: use baseline-relative spike  (FS-28 vib_med=2.12 G)
        vib_ratio = _bv(vib, max(vib_med, 0.01))

        # Amps deviation  (FS-28 amps_med=82.9 A)
        amps_ratio = _bv(amps, max(amps_med, 1.0))

        # Inp deviation   (FS-28 inp_med=304.7 PSI)
        inp_ratio  = _bv(inp,  max(inp_med,  1.0))

        # Disch deviation (FS-28 disch_med=2079.9 PSI)
        disch_ratio = _bv(disch, max(disch_med, 1.0))

        # Volt deviation  (FS-28 volt_med=356 V)
        volt_ratio  = _bv(volt, max(volt_med, 1.0))

        # Motor temp absolute (physics: overheating > 10°C above well's own median)
        m_temp_excess = m_temp - max(m_temp_med, 40.0)

        # ─────────────────────────────────────────────────────────────────────
        # 1. Power Loss — all electrical collapse to near-zero
        # ─────────────────────────────────────────────────────────────────────
        if volt < max(20.0, 0.08 * max(volt_med, 100.0)) and amps < max(2.0, 0.05 * max(amps_med, 10.0)) and freq < 5.0:
            scores["Power Loss"] = 0.98
            drivers["Power Loss"] = [("Volt", f"{volt:.0f} V (Power cut — {int((1-volt_ratio)*100)}% drop)"),
                                     ("VSD Amps/Load", f"{amps:.1f} A (Trip/outage)"),
                                     ("Frequency", f"{freq:.1f} Hz → Stopped")]
        else:
            scores["Power Loss"] = 0.0

        # ─────────────────────────────────────────────────────────────────────
        # 2. Dry-Well Pump Off
        #    Signature: Inp drops >15% below well's own baseline AND
        #               Amps drops >12% (gas pumping, no fluid load)
        #    Optional:  Motor temp rises >5°C above well's own baseline
        # ─────────────────────────────────────────────────────────────────────
        dry_score = 0.0
        dry_drivers = []
        if inp_ratio < 0.88 and amps_ratio < 0.90 and vfd_sts > 0.5:
            # Require physical confirmation: head degradation, discharge drop, or thermal rise
            if delta_p < 0.85 * head_med or disch_ratio < 0.88 or m_temp_excess > 5.0:
                drop_inp_pct = int((1.0 - inp_ratio) * 100)
                drop_amps_pct = int((1.0 - amps_ratio) * 100)
                dry_score = min(0.95, 0.50 * (0.88 - inp_ratio) / 0.20 + 0.40 * (0.90 - amps_ratio) / 0.15)
                dry_drivers.append(("Inp bar/psi", f"{inp:.1f} PSI (-{drop_inp_pct}% from well normal — fluid level falling)"))
                dry_drivers.append(("VSD Amps/Load", f"{amps:.1f} A (-{drop_amps_pct}% — reducing fluid torque load)"))
                if m_temp_excess > 3.0 or dt_slope > 1.0:
                    dry_score = min(0.97, dry_score + 0.15)
                    dry_drivers.append(("Motor temp °C", f"{m_temp:.1f}°C (+{m_temp_excess:.1f}°C above well normal — cooling reducing)"))
        scores["Dry-Well Pump Off"] = min(0.97, dry_score) if dry_score >= 0.30 else 0.0
        drivers["Dry-Well Pump Off"] = dry_drivers

        # ─────────────────────────────────────────────────────────────────────
        # 3. Blocked Intake
        #    Inp < 80% of baseline + Disch < 80% of baseline + low amps
        # ─────────────────────────────────────────────────────────────────────
        block_score = 0.0
        block_drivers = []
        if inp_ratio < 0.80 and vfd_sts > 0.5:
            block_score += 0.45
            block_drivers.append(("Inp bar/psi", f"{inp:.1f} (−{int((1-inp_ratio)*100)}% suction starved)"))
        if disch_ratio < 0.80 and delta_p < 0.75 * head_med:
            block_score += 0.40
            block_drivers.append(("Disch pr. Bar/psi", f"{disch:.1f} (−{int((1-disch_ratio)*100)}% no discharge)"))
        if amps_ratio < 0.75:
            block_score += 0.15
            block_drivers.append(("VSD Amps/Load", f"{amps:.1f} A (underloaded, no flow)"))
        scores["Blocked Intake"] = min(0.94, block_score) if block_score >= 0.45 else 0.0
        drivers["Blocked Intake"] = block_drivers

        # ─────────────────────────────────────────────────────────────────────
        # 4. Scale or Pump Wear
        #    Delta-P < 80% of well's own head at same frequency (constant-speed degradation)
        #    WHP > 0 means surface pressure is present (actual flow, not shut-in)
        # ─────────────────────────────────────────────────────────────────────
        wear_score = 0.0
        wear_drivers = []
        delta_p_ratio = delta_p / max(head_med, 1.0)
        if freq >= 42.0 and delta_p_ratio < 0.80 and inp_ratio > 0.70:
            # Progressive head loss at normal speed = wear
            wear_score = min(0.95, 0.60 + (0.80 - delta_p_ratio) * 1.5)
            wear_drivers.append(("ΔP (Disch-Inp)", f"{delta_p:.0f} PSI (-{int((1-delta_p_ratio)*100)}% head loss vs well norm)"))
            wear_drivers.append(("Frequency", f"{freq:.1f} Hz steady (impeller/stage degradation)"))
        scores["Scale or Pump Wear"] = wear_score
        drivers["Scale or Pump Wear"] = wear_drivers

        # ─────────────────────────────────────────────────────────────────────
        # 5. Sand Ingestion
        #    Vibration spike >30% above well's own vib median AND amps >8% above median
        # ─────────────────────────────────────────────────────────────────────
        sand_score = 0.0
        sand_drivers = []
        if vib_ratio > 1.30 and amps_ratio > 1.08:
            sand_score = min(0.96, 0.70 + (vib_ratio - 1.30) * 0.8)
            sand_drivers.append(("Vibration G's-Vx", f"{vib:.2f} G (+{int((vib_ratio-1)*100)}% abrasive turbulence)"))
            sand_drivers.append(("VSD Amps/Load", f"{amps:.1f} A (+{int((amps_ratio-1)*100)}% solids drag torque)"))
        scores["Sand Ingestion"] = sand_score
        drivers["Sand Ingestion"] = sand_drivers

        # ─────────────────────────────────────────────────────────────────────
        # 6. Bearing Degradation
        #    Vibration > 20% above well's own median (FS-28: 2.12 G → spike > 2.54 G)
        #    PLUS motor temp > 5°C above well's own median (bearing friction heat)
        #    NOTE: removed fixed 82°C cut — FS-28 never reaches 82°C
        # ─────────────────────────────────────────────────────────────────────
        bear_score = 0.0
        bear_drivers = []
        if vib_ratio > 1.20 and amps_ratio <= 1.20:
            # Vibration significantly above well's own baseline = primary bearing indicator
            # Motor temp confirmation is OPTIONAL — adds score but not required
            vib_score_part = min(0.70, 0.40 + (vib_ratio - 1.20) * 1.0)
            bear_score += vib_score_part
            bear_drivers.append(("Vibration G's-Vx", f"{vib:.2f} G (+{int((vib_ratio-1)*100)}% vs well baseline — bearing wear pattern)"))
            if m_temp_excess > 3.0:                  # Motor temp confirms friction heating
                bear_score += min(0.30, m_temp_excess * 0.03)
                bear_drivers.append(("Motor temp °C", f"{m_temp:.1f}°C (+{m_temp_excess:.1f}°C above well normal — bearing friction)"))
        scores["Bearing Degradation"] = min(0.97, bear_score) if bear_score >= 0.35 else 0.0
        drivers["Bearing Degradation"] = bear_drivers

        # ─────────────────────────────────────────────────────────────────────
        # 7. High Viscosity Cold Start
        #    Low frequency (<38 Hz) + amps >12% above baseline + cold fluid temp
        # ─────────────────────────────────────────────────────────────────────
        cold_score = 0.0
        cold_drivers = []
        if freq < 38.0 and amps_ratio > 1.12 and (i_temp < 35.0 or m_temp < 50.0):
            cold_score = 0.95
            cold_drivers.append(("VSD Amps/Load", f"{amps:.1f} A (+{int((amps_ratio-1)*100)}%) at {freq:.1f} Hz — high starting torque"))
            cold_drivers.append(("Int temp °C", f"{i_temp:.1f}°C (cold heavy crude/emulsion)"))
        scores["High Viscosity Cold Start"] = cold_score
        drivers["High Viscosity Cold Start"] = cold_drivers

        # ─────────────────────────────────────────────────────────────────────
        # 8. High Backpressure (surface choke/hydrate restriction)
        #    Discharge >15% above well's own baseline (surface resistance forcing pressure up)
        #    WHP or FLP elevated vs baseline
        # ─────────────────────────────────────────────────────────────────────
        back_score = 0.0
        back_drivers = []
        flp_ratio = _bv(flp, max(flp_med, 5.0))
        whp_ratio = _bv(whp, max(whp_med, 5.0))
        if disch_ratio > 1.15 and (flp_ratio > 1.20 or whp_ratio > 1.20):
            back_score = min(0.93, 0.70 + (disch_ratio - 1.15) * 1.0)
            back_drivers.append(("Disch pr. Bar/psi", f"{disch:.1f} (+{int((disch_ratio-1)*100)}% vs well normal — backpressure)"))
            if flp_ratio > 1.20:
                back_drivers.append(("FLP (PSI)", f"{flp:.1f} (+{int((flp_ratio-1)*100)}% flowline restriction)"))
        scores["High Backpressure"] = back_score
        drivers["High Backpressure"] = back_drivers

        # ─────────────────────────────────────────────────────────────────────
        # 9. Open Choke (runout flow — WHP low, amps elevated)
        #    Discharge <85% of baseline (less head needed) + amps >10% above baseline
        # ─────────────────────────────────────────────────────────────────────
        choke_score = 0.0
        choke_drivers = []
        if disch_ratio < 0.85 and amps_ratio > 1.10:
            choke_score = min(0.95, 0.60 + (1.0 - disch_ratio) * 0.8)
            choke_drivers.append(("Disch pr. Bar/psi", f"{disch:.1f} (-{int((1-disch_ratio)*100)}% — low backpressure runout)"))
            choke_drivers.append(("VSD Amps/Load", f"{amps:.1f} A (+{int((amps_ratio-1)*100)}% — pump runout overload)"))
        scores["Open Choke"] = choke_score
        drivers["Open Choke"] = choke_drivers

        # ─────────────────────────────────────────────────────────────────────
        # 10. Undervoltage (grid/transformer sag)
        #     Volt < 92% of well's own baseline median (FS-28 baseline=356 V → sag < 327 V)
        # ─────────────────────────────────────────────────────────────────────
        uv_score = 0.0
        uv_drivers = []
        if volt_ratio < 0.92 and volt > 50.0:
            uv_score += min(0.65, (0.92 - volt_ratio) * 8.0)
            uv_drivers.append(("Volt", f"{volt:.1f} V (-{int((1-volt_ratio)*100)}% from well nominal {volt_med:.0f} V)"))
            if amps_ratio > 1.08:
                uv_score += 0.30
                uv_drivers.append(("VSD Amps/Load", f"{amps:.1f} A (+{int((amps_ratio-1)*100)}% — compensating for voltage sag)"))
        scores["Undervoltage"] = min(0.95, uv_score) if uv_score >= 0.50 else 0.0
        drivers["Undervoltage"] = uv_drivers

        # ─────────────────────────────────────────────────────────────────────
        # 11. Phase Imbalance
        # ─────────────────────────────────────────────────────────────────────
        phase_score = 0.0
        phase_drivers = []
        i_imb = raw_data.get("I_Imb_pct", 0.0) if isinstance(raw_data, dict) else 0.0
        v_imb = raw_data.get("V_Imb_pct", 0.0) if isinstance(raw_data, dict) else 0.0
        if i_imb >= 3.0:
            phase_score += 0.70
            phase_drivers.append(("I-Imb", f"{i_imb:.2f}% (High current imbalance > 3%)"))
        if v_imb >= 2.0:
            phase_score += 0.30
            phase_drivers.append(("V-Imb", f"{v_imb:.2f}% (High voltage imbalance > 2%)"))
        if leak > 25.0:
            phase_score += 0.55
            phase_drivers.append(("Leak Current Ct", f"{leak:.1f} mA (Ground insulation breakdown)"))
        if m_temp_excess > 20.0 and amps_ratio < 1.15:
            phase_score += 0.40
            phase_drivers.append(("Motor temp °C", f"{m_temp:.1f}°C (+{m_temp_excess:.1f}°C — unbalanced phase heating)"))
        scores["Phase Imbalance"] = min(0.95, phase_score) if phase_score >= 0.50 else 0.0
        drivers["Phase Imbalance"] = phase_drivers

        # ─────────────────────────────────────────────────────────────────────
        # 12. Motor Overload
        #     Amps > 115% of well's own baseline (FS-28: 82.9 A → overload > 95.3 A)
        #     PLUS motor temp > 10°C above baseline
        # ─────────────────────────────────────────────────────────────────────
        ol_score = 0.0
        ol_drivers = []
        if amps_ratio > 1.15:
            ol_score += min(0.60, (amps_ratio - 1.15) * 4.0)
            ol_drivers.append(("VSD Amps/Load", f"{amps:.1f} A (+{int((amps_ratio-1)*100)}% — above rated nameplate)"))
            if m_temp_excess > 10.0:
                ol_score += min(0.35, m_temp_excess * 0.025)
                ol_drivers.append(("Motor temp °C", f"{m_temp:.1f}°C (+{m_temp_excess:.1f}°C — thermal overload risk)"))
        scores["Motor Overload"] = min(0.95, ol_score) if ol_score >= 0.45 else 0.0
        drivers["Motor Overload"] = ol_drivers

        # ─────────────────────────────────────────────────────────────────────
        # 13. Sensor Drift / Failure
        #     Non-physical values: negative pressures, motor temp < -10°C
        # ─────────────────────────────────────────────────────────────────────
        drift_score = 0.0
        drift_drivers = []
        if inp < 0.0 or disch < 0.0 or m_temp < -10.0 or volt < 0.0:
            drift_score = 0.95
            drift_drivers.append(("Sensor Integrity", "Non-physical (negative) measurement detected"))
        scores["Sensor Drift"] = drift_score
        drivers["Sensor Drift"] = drift_drivers

        # ─────────────────────────────────────────────────────────────────────
        # 14. Broken Shaft / Sheared Coupling
        #     Motor spinning at speed (freq OK) but amps < 55% of baseline AND
        #     delta_p < 40% of well's head baseline (no hydraulic lift)
        # ─────────────────────────────────────────────────────────────────────
        broken_shaft_score = 0.0
        broken_shaft_drivers = []
        if freq >= 35.0 and vfd_sts > 0.5:
            if delta_p < 0.40 * max(head_med, 10.0):
                broken_shaft_score += 0.50
                broken_shaft_drivers.append(("ΔP Head", f"{delta_p:.0f} PSI (-{int((1-delta_p/max(head_med,1))*100)}% no hydraulic lift)"))
            if amps_ratio < 0.55:
                broken_shaft_score += 0.45
                broken_shaft_drivers.append(("VSD Amps/Load", f"{amps:.1f} A (-{int((1-amps_ratio)*100)}% free-spinning no load)"))
        scores["Broken Shaft"] = min(0.98, broken_shaft_score) if broken_shaft_score >= 0.50 else 0.0
        drivers["Broken Shaft"] = broken_shaft_drivers

        # ─────────────────────────────────────────────────────────────────────
        # 15. Gas Interference / Gas Lock
        #     Signature: Casing / Annulus pressure rising + Inp dropping + Amps dropping + delta_p collapsing
        # ─────────────────────────────────────────────────────────────────────
        gas_score = 0.0
        gas_drivers = []
        casing_press = _f("AP (PSI)", ap)
        if (inp_ratio < 0.88 or delta_p < 0.70 * head_med) and vfd_sts > 0.5:
            ap_med = sensors_prof.get("AP (PSI)", {}).get("median", 10.0)
            if casing_press > max(15.0, 1.25 * ap_med):
                gas_score += 0.50
                gas_drivers.append(("AP (PSI)", f"{casing_press:.1f} PSI (Casing gas buildup above baseline)"))
            if amps_ratio < 0.90:
                gas_score += 0.40
                gas_drivers.append(("VSD Amps/Load", f"{amps:.1f} A (Underload gas interference)"))
        scores["Gas Interference"] = min(0.96, gas_score) if gas_score >= 0.45 else 0.0
        drivers["Gas Interference"] = gas_drivers

        # ── Out-of-Spec Parameter Setpoint Evaluation ─────────────────────────
        out_of_spec_items = []
        for s_name in [
            "Inp bar/psi", "Disch pr. Bar/psi", "VSD Amps/Load", "Volt", "Frequency",
            "Motor temp °C", "Int temp °C", "Vibration G's-Vx", "WHP (PSI)", "FLP (PSI)", "AP (PSI)"
        ]:
            if s_name in sensors_prof and s_name in raw_data:
                s_spec = sensors_prof[s_name]
                s_val = _f(s_name, s_spec.get("median", 0.0))
                n_min = float(s_spec.get("normal_min", s_spec.get("p10", 0.0)))
                n_max = float(s_spec.get("normal_max", s_spec.get("p90", 999999.0)))
                unit = s_spec.get("unit", "PSI" if "psi" in s_name.lower() else ("°C" if "°c" in s_name.lower() else ("A" if "amps" in s_name.lower() else "")))
                
                lower_benign_params = ("Vibration G's-Vx", "Motor temp °C", "Int temp °C", "Leak Current Ct")
                if s_val > n_max:
                    out_of_spec_items.append({
                        "param": s_name,
                        "direction": "Higher than max limit",
                        "value": round(s_val, 1),
                        "limit": round(n_max, 1),
                        "unit": unit,
                        "text": f"Higher than max limit in {s_name} ({s_val:.1f} > {n_max:.1f})"
                    })
                elif s_val < n_min and s_name not in lower_benign_params:
                    out_of_spec_items.append({
                        "param": s_name,
                        "direction": "Lower than min limit",
                        "value": round(s_val, 1),
                        "limit": round(n_min, 1),
                        "unit": unit,
                        "text": f"Lower than min limit in {s_name} ({s_val:.1f} < {n_min:.1f})"
                    })

        # -------------------------------------------------------------
        # Select Primary Fault & Compute Health Score
        # -------------------------------------------------------------
        best_fault = "Normal Operation"
        best_score = 0.0
        for f_name, f_score in scores.items():
            if f_score > best_score and f_score >= 0.30:
                best_score = f_score
                best_fault = f_name

        # Only critical out-of-spec parameters (pressure/current collapse) disqualify healthy status.
        critical_params = ("Inp bar/psi", "Disch pr. Bar/psi", "VSD Amps/Load")
        critical_violations = [item for item in out_of_spec_items if item["param"] in critical_params]
        is_healthy = (best_fault == "Normal Operation") and (len(critical_violations) == 0)

        if is_healthy:
            health_score = 98.0 - (vib * 10.0) - max(0.0, (m_temp - 75.0) * 0.5)
            health_score = max(75.0, min(100.0, health_score))
            alert_level = "🟢 NORMAL"
            confidence = 0.95
            est_trip = "N/A (Stable Operation)"
            primary_drivers = [("All Sensors", "Within normal calibrated boundaries")]
            canonical_verdict = "Healthy"
            model_output = "Healthy"
        else:
            health_score = max(5.0, (1.0 - best_score) * 80.0)
            if best_fault == "Normal Operation" and critical_violations:
                best_fault = "Out-of-Spec Parameter Deviation"
                best_score = 0.55
                confidence = 0.80
                alert_level = "🟡 WATCHLIST"
                est_trip = "24 to 48 Hours"
            else:
                severity = FAULT_DEFINITIONS.get(best_fault, {}).get("severity", "WARNING")
                alert_level = "🔴 CRITICAL" if severity == "CRITICAL" else "🟡 WATCHLIST"
                confidence = best_score
                if best_score > 0.85:
                    est_trip = "Immediate (< 2 Hours)"
                elif best_score > 0.65:
                    est_trip = "6 to 24 Hours"
                else:
                    est_trip = "24 to 48 Hours"

            primary_drivers = drivers.get(best_fault, [])

            if critical_violations:
                causes_text = " and ".join([item["text"] for item in critical_violations[:3]])
            elif primary_drivers:
                causes_text = " and ".join([f"{d_val} in {d_name}" for d_name, d_val in primary_drivers[:3]])
            elif out_of_spec_items:
                causes_text = " and ".join([item["text"] for item in out_of_spec_items[:3]])
            else:
                causes_text = "Operating parameter threshold breach"

            canonical_verdict = f"Anomaly is Detected, According to the ML Suggestions it Can be '{best_fault}', Due to {causes_text}"
            model_output = canonical_verdict

        fault_info = FAULT_DEFINITIONS.get(best_fault, {
            "description": "All electrical, thermal, mechanical, and hydraulic parameters within healthy baseline envelope.",
            "action": "Maintain current operating parameters; continue standard monitoring."
        })

        return {
            "primary_fault": best_fault,
            "confidence": f"{confidence * 100:.1f}%",
            "confidence_val": round(confidence, 4),
            "health_score": round(health_score, 1),
            "status": alert_level,
            "is_healthy": is_healthy,
            "canonical_verdict": canonical_verdict,
            "model_output": model_output,
            "est_time_to_trip": est_trip,
            "description": fault_info["description"],
            "action_advisory": fault_info["action"],
            "root_cause_drivers": primary_drivers,
            "out_of_spec_parameters": out_of_spec_items,
            "triggered_limits": [
                {
                    "tag": item["param"],
                    "value": f"{item['value']} {item.get('unit', '')}".strip(),
                    "type": "HIGH" if "Higher" in item["direction"] else "LOW",
                    "direction": item["direction"],
                    "limit": item["limit"]
                }
                for item in out_of_spec_items
            ],
            "all_scores": {k: f"{v*100:.1f}%" for k, v in scores.items() if v > 0.20},
            "scores": {k: round(v, 4) for k, v in scores.items()}
        }
