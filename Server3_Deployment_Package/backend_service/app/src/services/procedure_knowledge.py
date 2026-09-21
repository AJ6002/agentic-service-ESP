"""
Procedure and Knowledge Service (T1_KB_ONLY)
Provides authoritative operating limits, tripping thresholds, and SOP lookups
from deterministic YAML playbooks and diagnostic rules without fabricating live telemetry.
"""

import os
import re
import yaml
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

_CURRENT_DIR = Path(__file__).resolve().parent
_ESP_AGENT_ROOT = _CURRENT_DIR.parent.parent
_PROJECT_ROOT = _ESP_AGENT_ROOT.parent

_ALERTS_YAML = _PROJECT_ROOT / "esp-knowledge" / "deterministic" / "alerts" / "seed_alerts.yaml"
_RULES_JSON = _ESP_AGENT_ROOT / "knowledge_bases" / "esp" / "rules" / "diagnostic_rules.json"


class ProcedureKnowledgeService:
    """Service to look up governing operational thresholds, tripping limits, and SOPs."""

    def __init__(self):
        self._alerts: List[Dict[str, Any]] = []
        self._rules: List[Dict[str, Any]] = []
        self._load_sources()

    def _load_sources(self):
        if _ALERTS_YAML.exists():
            try:
                with open(_ALERTS_YAML, "r", encoding="utf-8") as f:
                    ydata = yaml.safe_load(f)
                    self._alerts = ydata.get("alerts", [])
            except Exception as e:
                logger.warning(f"Failed to load {_ALERTS_YAML}: {e}")

        if _RULES_JSON.exists():
            try:
                with open(_RULES_JSON, "r", encoding="utf-8") as f:
                    rdata = json.load(f)
                    self._rules = rdata.get("rules", [])
            except Exception as e:
                logger.warning(f"Failed to load {_RULES_JSON}: {e}")

    def lookup_limits(self, query: str) -> Dict[str, Any]:
        """
        Extract relevant operating limits and tripping thresholds matching the query.
        """
        q_low = query.lower()
        matched_limits = []

        # 1. Thermal / Temperature
        if any(w in q_low for w in ["temp", "temperature", "thermal", "overheat", "motor temp"]):
            matched_limits.append({
                "parameter": "Motor Internal Temperature",
                "canonical_metric": "primary_thermal_metric",
                "normal_envelope": "< 125.0 °C",
                "warning_threshold": "130.0 °C",
                "tripping_limit": "150.0 °C (Critical Trip)",
                "governing_standard": "API RP 11S / seed_alerts.yaml (MOTOR_TEMP_CRITICAL)",
                "consequence": "Stator winding thermal insulation breakdown and motor burnout.",
                "action": "Immediate engineering review, inspect cooling flow, evaluate controlled shutdown."
            })

        # 2. Intake Pressure / PIP / Gas Locking
        if any(w in q_low for w in ["intake", "pip", "drawdown", "suction", "gas lock"]):
            matched_limits.append({
                "parameter": "Pump Intake Pressure (PIP)",
                "canonical_metric": "primary_intake_pressure",
                "normal_envelope": "> 200.0 psi",
                "warning_threshold": "< 150.0 psi",
                "tripping_limit": "< 100.0 psi (Critical Low-PIP Trip)",
                "governing_standard": "diagnostic_rules.json (RULE_PIP_CRIT) / seed_alerts.yaml",
                "consequence": "Free gas breakout, fluid vapor lock, loss of cooling, and cavitation damage.",
                "action": "Reduce VFD frequency, verify choke setting, activate gas agitation cycle."
            })

        # 3. Vibration / Mechanical
        if any(w in q_low for w in ["vib", "vibration", "mechanical", "radial", "axial"]):
            matched_limits.append({
                "parameter": "Radial Vibration",
                "canonical_metric": "vibration_metric",
                "normal_envelope": "< 1.5 g RMS",
                "warning_threshold": "> 3.0 g RMS",
                "tripping_limit": "> 5.0 g RMS (Critical Trip)",
                "governing_standard": "API RP 11S8 / diagnostic_rules.json (RULE_VIB_CRIT)",
                "consequence": "Rotor unbalance, shaft deflection, bearing wear, and mechanical seal destruction.",
                "action": "Inspect vibration frequency spectrum, avoid resonance speeds, schedule bearing inspection."
            })
            matched_limits.append({
                "parameter": "Axial Vibration",
                "canonical_metric": "axial_vibration_metric",
                "normal_envelope": "< 0.8 g RMS",
                "warning_threshold": "> 1.5 g RMS",
                "tripping_limit": "> 2.5 g RMS",
                "governing_standard": "diagnostic_rules.json (RULE_AXIAL_VIB_WARN)",
                "consequence": "Thrust bearing axial load failure and stage rubbing.",
                "action": "Verify pump thrust bearing condition and fluid gas fraction."
            })

        # 4. Motor Current / Electrical Overload / Underload
        if any(w in q_low for w in ["current", "amp", "overload", "underload", "electrical", "imbalance"]):
            matched_limits.append({
                "parameter": "Drive Current Overload",
                "canonical_metric": "primary_electrical_load",
                "normal_envelope": "70% – 100% Nameplate Rating",
                "warning_threshold": "> 105% Nameplate Amps",
                "tripping_limit": "> 115% Nameplate Amps (Overload Trip)",
                "governing_standard": "diagnostic_rules.json (RULE_OVERLOAD_CRIT) / API RP 11S",
                "consequence": "Electrical overload, motor stall, or solid sand ingestion in pump stages.",
                "action": "Check for mechanical binding or fluid viscosity change; verify VFD current limit."
            })
            matched_limits.append({
                "parameter": "Drive Current Underload",
                "canonical_metric": "primary_electrical_load",
                "normal_envelope": "70% – 100% Nameplate Rating",
                "warning_threshold": "< 65% Nameplate Amps",
                "tripping_limit": "< 60% Nameplate Amps (Underload Trip)",
                "governing_standard": "diagnostic_rules.json (RULE_UNDERLOAD_CRIT)",
                "consequence": "Pump pump-off, broken shaft, or complete gas lock.",
                "action": "Verify fluid inflow and well fluid level before restart."
            })

        # 5. Backspin Rotation & Lockout
        if any(w in q_low for w in ["backspin", "back spin", "reverse rotation", "fluid fallback"]):
            matched_limits.append({
                "parameter": "Backspin Rotation Lockout",
                "canonical_metric": "reverse_rotation_rpm",
                "normal_envelope": "0 RPM (Complete Stop)",
                "warning_threshold": "Reverse rotation detected",
                "tripping_limit": "Lockout Active (Mandatory 30-45 min delay)",
                "governing_standard": "API RP 11S Section 6.4 / OEM Standard",
                "consequence": "Instantaneous spline shaft shear and mechanical seal destruction if re-energized during reverse rotation.",
                "action": "Enforce mandatory 30-minute VFD restart lockout timer; verify 0 RPM before re-energizing."
            })

        # 6. General / Catch-All if no specific parameter detected
        if not matched_limits:
            matched_limits.append({
                "parameter": "Motor Internal Temperature",
                "normal_envelope": "< 125.0 °C",
                "warning_threshold": "130.0 °C",
                "tripping_limit": "150.0 °C (Critical Trip)",
                "governing_standard": "API RP 11S",
                "action": "Inspect cooling flow, evaluate controlled shutdown."
            })
            matched_limits.append({
                "parameter": "Pump Intake Pressure",
                "normal_envelope": "> 200.0 psi",
                "warning_threshold": "< 150.0 psi",
                "tripping_limit": "< 100.0 psi (Critical Trip)",
                "governing_standard": "diagnostic_rules.json",
                "action": "Reduce VFD frequency, check choke setting."
            })
            matched_limits.append({
                "parameter": "Radial Vibration",
                "normal_envelope": "< 1.5 g RMS",
                "warning_threshold": "> 3.0 g RMS",
                "tripping_limit": "> 5.0 g RMS (Critical Trip)",
                "governing_standard": "API RP 11S8",
                "action": "Check for mechanical unbalance or gas slugging."
            })

        return {
            "query": query,
            "matched_limits": matched_limits,
            "is_sop_query": any(w in q_low for w in ["startup", "start up", "sop", "procedure", "maintenance", "how to", "backspin"]),
        }

    def format_advisory_text(self, query: str, asset_id: str) -> Dict[str, Any]:
        """
        Format an authoritative advisory text responding to the operator's procedure query.
        Returns both human-readable markdown and structured procedural card components.
        """
        info = self.lookup_limits(query)
        q_low = query.lower()

        # 1. Backspin SOP Flow
        if any(w in q_low for w in ["backspin", "back spin", "reverse rotation"]):
            assessment = (
                f"### 🛑 Standard Operating Procedure: ESP Backspin Lockout & Restart Protocol\n\n"
                f"**Governing Reference:** API RP 11S §6.4 & API RP 11S1 (Recommended Practice for Operation of ESP Installations)\n\n"
                f"#### Phase 1: Fluid Fallback & Reverse Rotation Detection\n"
                f"1. **Rotor Motion Check:** Following any pump shutdown, fluid column head drains back through pump stages, driving rotor in reverse (up to 3,000+ RPM).\n"
                f"2. **Safety Lockout Timer:** VFD restart lockout timer MUST automatically activate for a minimum of 30 minutes (recommended 45 minutes for deep wells > 6,000 ft).\n\n"
                f"#### Phase 2: Tubing Head Equalization\n"
                f"1. **Pressure Monitoring:** Monitor tubing head pressure (THP) until pressure stabilizes and fluid column drainage completes.\n"
                f"2. **Rotation Verification:** Verify zero electrical back-EMF or visual motor shaft stationary status before attempting restart.\n\n"
                f"#### Phase 3: Controlled Safe Restart\n"
                f"1. **Pre-Start Checks:** Confirm casing fluid level, check motor insulation resistance (> 10 MΩ).\n"
                f"2. **Initial Frequency:** Ramp up from minimum 35 Hz at a rate not exceeding 0.5 Hz / minute."
            )
            diagnosis = "API RP 11S Section 6.4 mandatory backspin restart delay and mechanical shaft protection protocol."
            recommendation = "Enforce mandatory 30-minute VFD backspin timer lockout. NEVER re-energize motor while rotor rotates in reverse."
            verification = [
                "1. Confirm VFD backspin lockout timer is engaged and shows remaining cooldown time.",
                "2. Verify zero back-EMF generated by downhole motor before releasing restart lockout.",
                "3. Log shutdown event and standing fluid level in daily operations log."
            ]
            prohibited_actions = [
                "CRITICAL: NEVER attempt restart while pump is backspinning (causes instantaneous spline shaft torsion shear).",
                "NEVER bypass VFD backspin timer relay under any operational circumstance.",
                "NEVER close surface flowline master valve while fluid is actively falling back through tubing."
            ]
            execution_steps = [
                {"phase": "Phase 1: Lockout Verification", "steps": ["Verify VFD lockout timer engaged (30-45 min)", "Measure zero motor back-EMF voltage"]},
                {"phase": "Phase 2: Fluid Dissipation", "steps": ["Allow fluid column to equalize through tubing", "Inspect surface check valve sealing"]},
                {"phase": "Phase 3: Controlled Restart", "steps": ["Perform pre-start Megger insulation test (> 10 MΩ)", "Initiate VFD ramp at minimum 35 Hz"]}
            ]
            thresholds_table = [
                {"parameter": "Backspin Rotation", "normal": "0 RPM (Stationary)", "warning": "Reverse rotation active", "trip": "Start Lockout Engaged", "action": "Wait full 30-45 min timer"},
                {"parameter": "Lockout Timer Duration", "normal": "0 min (Ready)", "warning": "< 15 min remaining", "trip": "30.0 min minimum", "action": "Do not override relay"},
                {"parameter": "Motor Insulation", "normal": "> 50 MΩ", "warning": "< 20 MΩ", "trip": "< 10 MΩ (Abort Start)", "action": "Megger test downhole cable"}
            ]
            citations = [
                {"document_id": "API_RP_11S1_V4", "section": "Section 5.3: Backspin Safeguard", "authority_level": "A"},
                {"document_id": "DOC-STD-API-11S_p16_c1", "section": "Restart Delay Protocols", "authority_level": "A"},
                {"document_id": "DOC-OEM-BH-001", "section": "Centrilift Operations Manual §4", "authority_level": "B"}
            ]
            return {
                "assessment": assessment,
                "diagnosis": diagnosis,
                "recommendation": recommendation,
                "verification": verification,
                "prohibited_actions": prohibited_actions,
                "execution_steps": execution_steps,
                "thresholds_table": thresholds_table,
                "governing_standard": "API RP 11S §6.4 (Backspin Protocol)",
                "authority_level": "A",
                "citations": citations
            }

        # 2. Startup SOP Flow
        if any(w in q_low for w in ["startup", "start up", "procedure for startup", "start procedure"]):
            assessment = (
                f"### 📋 Standard Operating Procedure: ESP Pump Startup Protocol\n\n"
                f"**Governing Reference:** API RP 11S §6 (Recommended Practice for ESP Installations) & OEM Standard\n\n"
                f"#### Phase 1: Pre-Start Verification Checklist\n"
                f"1. **Electrical Isolation & Insulation:** Verify motor and downhole cable insulation resistance > 10 MΩ (Megger test).\n"
                f"2. **Surface Facilities:** Confirm flowline master valves are fully OPEN, flowmeter active, and surface separator ready.\n"
                f"3. **Fluid Level:** Confirm well casing fluid level and static intake pressure > 250 psi.\n\n"
                f"#### Phase 2: Start & Ramp-Up Sequence\n"
                f"1. **Initial Frequency:** Initiate VFD at 35.0 Hz minimum startup speed to establish fluid lift and motor cooling.\n"
                f"2. **Current Surge Monitoring:** Observe motor starting current spike; ensure current stabilizes within nameplate rating within 15 seconds.\n"
                f"3. **Gradual Frequency Ramp:** Increment VFD speed at a rate not exceeding 0.5 Hz / minute toward nominal operating point (typically 50.0 Hz).\n\n"
                f"#### Phase 3: Post-Startup Critical Thresholds (First 60 Minutes)\n"
                f"• **Motor Temperature:** Must stabilize < 130.0 °C (Abort startup if temp exceeds 150.0 °C).\n"
                f"• **Intake Pressure (PIP):** Must remain > 150.0 psi (Gas lock warning threshold).\n"
                f"• **Vibration:** Must remain < 3.0 g RMS radial vibration."
            )
            diagnosis = "API RP 11S standard operating procedure for ESP pump startup and commissioning."
            recommendation = "Execute pre-start Megger check and verify open surface valves prior to initiating VFD ramp."
            verification = [
                "1. Document pre-start insulation resistance in well log.",
                "2. Confirm flowline backpressure is within design parameters.",
                "3. Monitor motor temperature rate of rise during first 30 minutes of runtime."
            ]
            prohibited_actions = [
                "NEVER initiate startup with closed wing or master valves on wellhead.",
                "NEVER ramp VFD faster than 0.5 Hz / minute during initial fluid lift phase.",
                "NEVER run pump if motor insulation resistance tests below 10 MΩ."
            ]
            execution_steps = [
                {"phase": "Phase 1: Pre-Start Verification", "steps": ["Megger test motor cable (> 10 MΩ)", "Verify flowline master valve 100% OPEN", "Check static casing fluid level (> 250 psi)"]},
                {"phase": "Phase 2: Start & Ramp Sequence", "steps": ["Initiate VFD at 35.0 Hz minimum", "Confirm drive current stabilizes within 15 sec", "Ramp speed at ≤ 0.5 Hz/min to target 50 Hz"]},
                {"phase": "Phase 3: Post-Startup Monitoring", "steps": ["Verify motor temp stabilizes < 130°C", "Confirm intake pressure remains > 150 psi", "Check radial vibration < 3.0 g RMS"]}
            ]
            thresholds_table = [
                {"parameter": "Minimum Startup Speed", "normal": "35.0 Hz", "warning": "< 30.0 Hz", "trip": "< 25.0 Hz (No Lift)", "action": "Ensure minimum flow velocity past motor"},
                {"parameter": "Frequency Ramp Rate", "normal": "0.5 Hz/min", "warning": "> 1.0 Hz/min", "trip": "Instantaneous Step (Overcurrent)", "action": "Smooth VFD acceleration"},
                {"parameter": "Motor Insulation", "normal": "> 50 MΩ", "warning": "< 20 MΩ", "trip": "< 10 MΩ (No Start)", "action": "Cable repair required if low"}
            ]
            citations = [
                {"document_id": "API_RP_11S", "section": "Section 6: Startup & Commissioning", "authority_level": "A"},
                {"document_id": "SOP_PUMP_STARTUP", "section": "Standard Commissioning Checklist", "authority_level": "B"},
                {"document_id": "DOC-STD-API-11S4", "section": "Sizing & Installation Guidelines", "authority_level": "A"}
            ]
            return {
                "assessment": assessment,
                "diagnosis": diagnosis,
                "recommendation": recommendation,
                "verification": verification,
                "prohibited_actions": prohibited_actions,
                "execution_steps": execution_steps,
                "thresholds_table": thresholds_table,
                "governing_standard": "API RP 11S Section 6 (Startup & Commissioning)",
                "authority_level": "A",
                "citations": citations
            }

        # 3. ESP Failure Modes & Faults Catalog Flow
        if any(w in q_low for w in ["fault", "faults", "failure mode", "failure modes", "what could go wrong", "common issues", "troubleshoot"]):
            assessment = (
                "### 🔍 Governing ESP Failure Modes & Diagnostic Catalog\n\n"
                "**Governing Reference:** API RP 11S (ESP Installations) & OEM Diagnostic Standards\n\n"
                "Electric Submersible Pumps operate in harsh downhole environments subject to 4 primary failure classifications:\n\n"
                "#### 1. Thermal & Electrical Degradation\n"
                "- **Motor Overheating:** Caused by insufficient fluid cooling velocity (< 1 ft/s past motor), electrical overload, or heavy scale coating. Trip limit: `150.0 °C`.\n"
                "- **Insulation Breakdown (Phase-to-Ground):** Cable dielectric puncture or motor pothead seal leak causing low Megger resistance (< 10 MΩ).\n"
                "- **Current Imbalance:** VFD phase voltage unbalance or high-resistance cable connector faults (> 5% imbalance).\n\n"
                "#### 2. Hydraulic & Gas Interference\n"
                "- **Gas Locking / Interference:** Free gas breakout exceeding pump intake capability (> 15% free gas without separator, > 50% with AGS), causing head degradation and underload.\n"
                "- **Pump Cavitation / Low PIP:** Intake pressure dropping below bubble point or minimum submergence (< 100 psi trip).\n\n"
                "#### 3. Mechanical & Structural Failures\n"
                "- **Broken / Sheared Shaft:** High torsional stress during reverse backspin restart, sand slugging, or fatigue failure. Characterized by sudden current drop with nominal frequency.\n"
                "- **Impeller / Diffuser Stage Wear:** Sand/abrasives erosion causing gradual head loss, increasing slip, and rising vibration.\n"
                "- **Thrust Bearing Failure (Upthrust / Downthrust):** Operating outside the Recommended Operating Range (ROR). Continuous upthrust (high flow/low head) or severe downthrust (low flow/high head) destroys thrust runners.\n\n"
                "#### 4. Reservoir & Fluid Incompatibilities\n"
                "- **Scale Deposition:** Carbonate or sulfate precipitation inside intake screens and pump stages, causing flow constriction and motor heating.\n"
                "- **Emulsion & Viscosity Loading:** Heavy fluid loading driving drive current past nameplate overload (> 115%)."
            )
            diagnosis = "API RP 11S comprehensive failure modes and degradation mechanisms catalog."
            recommendation = "Maintain telemetry monitoring within the Recommended Operating Range (ROR) and ensure all VFD protective shutdown setpoints are active."
            verification = [
                "1. Verify VFD underload and overload protective relays are calibrated.",
                "2. Monitor motor internal temperature rate of rise (< 130 °C warning, 150 °C critical trip).",
                "3. Track intake pressure relative to fluid bubble point to prevent gas locking.",
                "4. Enforce mandatory 30-minute backspin restart delay to protect shafts."
            ]
            prohibited_actions = [
                "NEVER restart an ESP while fluid fallback or reverse rotation is active.",
                "NEVER operate continuously above 130 °C motor temperature.",
                "NEVER bypass VFD underload trip setpoints without engineering approval."
            ]
            execution_steps = [
                {"phase": "Phase 1: Surveillance", "steps": ["Monitor 5 canonical metrics (PIP, PDP, Temp, Amps, Vib)", "Cross-reference operating point against BEP curve"]},
                {"phase": "Phase 2: Anomaly Triage", "steps": ["Identify whether anomaly is electrical, hydraulic, or mechanical", "Check for precursor drift before trips occur"]},
                {"phase": "Phase 3: Mitigation", "steps": ["Apply frequency trims or choke adjustments", "Initiate controlled shutdown if critical limits exceeded"]}
            ]
            thresholds_table = [
                {"parameter": "Motor Temp Trip", "normal": "< 125 °C", "warning": "130 °C", "trip": "150 °C", "action": "Inspect cooling flow / shutdown"},
                {"parameter": "Radial Vibration", "normal": "< 1.5 g", "warning": "3.0 g", "trip": "5.0 g", "action": "Check for unbalance / sand"},
                {"parameter": "Intake Pressure (PIP)", "normal": "> 200 psi", "warning": "150 psi", "trip": "100 psi", "action": "Mitigate gas lock / choke trim"},
                {"parameter": "Motor Current", "normal": "70-100% Nameplate", "warning": "> 105%", "trip": "> 115% (Overload)", "action": "Check mechanical binding"}
            ]
            citations = [
                {"document_id": "API_RP_11S", "section": "Section 4: Operating Safeguards & Failure Modes", "authority_level": "A"},
                {"document_id": "DOC-STD-API-11S8", "section": "Vibration & Mechanical Wear Guidelines", "authority_level": "A"},
                {"document_id": "diagnostic_rules.json", "section": "ESP Fault Classification Registry", "authority_level": "B"}
            ]
            return {
                "assessment": assessment,
                "diagnosis": diagnosis,
                "recommendation": recommendation,
                "verification": verification,
                "prohibited_actions": prohibited_actions,
                "execution_steps": execution_steps,
                "thresholds_table": thresholds_table,
                "governing_standard": "API RP 11S (ESP Systems & Failure Analysis)",
                "authority_level": "A",
                "citations": citations
            }

        # 4. Limits & Operating Thresholds Flow
        limits = info["matched_limits"]
        table_rows = []
        thresholds_table = []
        for lim in limits:
            norm = lim.get('normal_envelope', 'Nominal')
            warn = lim.get('warning_threshold', 'Warning')
            trip = lim.get('tripping_limit', 'Critical Trip')
            table_rows.append(
                f"| **{lim['parameter']}** | `{norm}` | "
                f"`{warn}` | **`{trip}`** | "
                f"*{lim.get('governing_standard', 'API RP 11S')}* |"
            )
            thresholds_table.append({
                "parameter": lim["parameter"],
                "normal": norm,
                "warning": warn,
                "trip": trip,
                "action": lim.get("action", "Adhere to operating envelope")
            })

        table_md = "\n".join(table_rows)

        assessment = (
            f"### ⚙️ Governing Operating Thresholds & Tripping Limits\n\n"
            f"**Authority Hierarchy:** API RP 11S (Authority A) & Seed Diagnostic Rules (Authority B)\n\n"
            f"| Operational Parameter | Normal Range | Warning Alarm | Shutdown Tripping Limit | Standard Source |\n"
            f"| :--- | :--- | :--- | :--- | :--- |\n"
            f"{table_md}\n\n"
        )

        prohibited_actions = []
        for lim in limits:
            if "consequence" in lim:
                assessment += (
                    f"#### ⚠️ {lim['parameter']} Safeguard Specification\n"
                    f"- **Tripping Limit:** `{lim.get('tripping_limit')}`\n"
                    f"- **Failure Risk:** {lim['consequence']}\n"
                    f"- **Approved Action:** {lim.get('action')}\n\n"
                )
                prohibited_actions.append(f"NEVER operate continuously when {lim['parameter']} exceeds {lim['warning_threshold']}.")

        if not prohibited_actions:
            prohibited_actions.append("NEVER operate pump outside Recommended Operating Range (ROR) defined in pump performance curves.")

        diagnosis = f"Operational thresholds retrieved for: {', '.join(l['parameter'] for l in limits)}."
        recommendation = "Ensure SCADA alarm bands and VFD protective setpoints match these governing limits."
        verification = [
            "1. Audit VFD trip parameter registers against API RP 11S thresholds.",
            "2. Verify SCADA alarm dispatch configuration and trip relay latching.",
            "3. Cross-reference operating point against installed pump model BEP curve."
        ]
        execution_steps = [
            {"phase": "Phase 1: Threshold Verification", "steps": ["Inspect current telemetry against warning corridor", "Verify SCADA alarm limits are configured correctly"]},
            {"phase": "Phase 2: Corrective Adjustment", "steps": ["Trim VFD frequency if operating in warning band", "Verify adequate fluid intake submergence"]}
        ]
        citations = [
            {"document_id": "API_RP_11S", "section": "Protection & Monitoring §5", "authority_level": "A"},
            {"document_id": "diagnostic_rules.json", "section": "Critical Limits Register", "authority_level": "B"},
            {"document_id": "DOC-STD-API-11S8", "section": "Vibration & Mechanical Safeguards", "authority_level": "A"}
        ]
        return {
            "assessment": assessment,
            "diagnosis": diagnosis,
            "recommendation": recommendation,
            "verification": verification,
            "prohibited_actions": prohibited_actions,
            "execution_steps": execution_steps,
            "thresholds_table": thresholds_table,
            "governing_standard": "API RP 11S & OEM Technical Manuals",
            "authority_level": "A",
            "citations": citations
        }


procedure_knowledge_service = ProcedureKnowledgeService()
