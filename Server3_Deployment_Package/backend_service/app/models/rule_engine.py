"""
Model 1: Deterministic Operating Envelope & Rule Engine.
Evaluates the 13 live telemetry parameters against Reference and Engineering limits,
computes normalized deviations, tracks persistence duration, and checks multivariate fault rules.
"""

import os
import yaml
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime, timezone
from ml.data.canonical_schema import (
    CanonicalESPTelemetry,
    ParameterEvaluation,
    ParameterStatus,
    RuleEvaluationResult,
    FaultClass
)

CONFIG_DIR = Path(__file__).resolve().parent.parent.parent / "config"
ENVELOPES_PATH = CONFIG_DIR / "envelopes.yaml"
RULES_PATH = CONFIG_DIR / "rules.yaml"


class ESPRuleEngine:
    def __init__(self, envelopes_path: Path = ENVELOPES_PATH, rules_path: Path = RULES_PATH):
        self.envelopes = self._load_yaml(envelopes_path).get("envelopes", {})
        self.rules = self._load_yaml(rules_path).get("rules", [])
        
        # Persistence tracking per well & rule: (well_key, rule_id) -> start_timestamp
        self.rule_start_times: Dict[str, float] = {}

    def _load_yaml(self, path: Path) -> Dict[str, Any]:
        if not path.exists():
            return {}
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    def evaluate_envelopes(self, telemetry: CanonicalESPTelemetry) -> List[ParameterEvaluation]:
        """Evaluates all 13 parameters against Reference and Engineering ranges."""
        results: List[ParameterEvaluation] = []

        for canonical_name, cfg in self.envelopes.items():
            val = getattr(telemetry, canonical_name, None)
            ref_min = float(cfg.get("reference_min", 0.0))
            ref_max = float(cfg.get("reference_max", 100.0))
            eng_min = float(cfg.get("engineering_min", ref_min * 0.8))
            eng_max = float(cfg.get("engineering_max", ref_max * 1.2))
            crit_low = float(cfg.get("critical_low", eng_min * 0.8))
            crit_high = float(cfg.get("critical_high", eng_max * 1.2))

            from ml.data.canonical_schema import SensorProvenance

            prov = getattr(telemetry, "provenance_map", {}).get(canonical_name, SensorProvenance.LIVE_MQTT)

            if val is None:
                eval_item = ParameterEvaluation(
                    parameter=cfg.get("name", canonical_name),
                    canonical_name=canonical_name,
                    unit=cfg.get("unit", ""),
                    value=None,
                    reference_min=ref_min,
                    reference_max=ref_max,
                    engineering_min=eng_min,
                    engineering_max=eng_max,
                    deviation=0.0,
                    deviation_percent=0.0,
                    status=ParameterStatus.NORMAL,
                    provenance=SensorProvenance.UNAVAILABLE,
                    provenance_note="Not received from MQTT / telemetry stream",
                    is_available=False,
                    message="Sensor measurement unavailable"
                )
                results.append(eval_item)
                continue

            val = float(val)

            # Calculate Deviation
            if val < ref_min:
                dev = ref_min - val
                dev_pct = (dev / (ref_max - ref_min)) * 100.0 if ref_max > ref_min else 0.0
            elif val > ref_max:
                dev = val - ref_max
                dev_pct = (dev / (ref_max - ref_min)) * 100.0 if ref_max > ref_min else 0.0
            else:
                dev = 0.0
                dev_pct = 0.0

            # Determine Status
            if val <= crit_low or val >= crit_high:
                status = ParameterStatus.CRITICAL
                msg = f"Critical safety limit breached! Value={val:.1f} {cfg.get('unit')}"
            elif val < eng_min or val > eng_max:
                status = ParameterStatus.WARNING
                msg = f"Outside operating limits! Value={val:.1f} {cfg.get('unit')} (Limits: {eng_min}-{eng_max})"
            elif val < ref_min or val > ref_max:
                status = ParameterStatus.WARNING
                msg = f"Deviating from reference envelope ({ref_min}-{ref_max} {cfg.get('unit')})"
            else:
                status = ParameterStatus.NORMAL
                msg = f"Within normal reference envelope ({ref_min}-{ref_max} {cfg.get('unit')})"

            if prov == SensorProvenance.LIVE_MQTT:
                prov_note = "Live sensor measurement from MQTT"
            elif prov == SensorProvenance.DATABASE:
                prov_note = "Historical record from site database"
            elif prov == SensorProvenance.DERIVED:
                prov_note = "Derived: I / I_rated × 100"
            elif prov == SensorProvenance.INFERRED:
                prov_note = "Inferred / Default (Not received from MQTT)"
            else:
                prov_note = "Sensor unavailable"

            eval_item = ParameterEvaluation(
                parameter=cfg.get("name", canonical_name),
                canonical_name=canonical_name,
                unit=cfg.get("unit", ""),
                value=val,
                reference_min=ref_min,
                reference_max=ref_max,
                engineering_min=eng_min,
                engineering_max=eng_max,
                deviation=dev,
                deviation_percent=dev_pct,
                status=status,
                provenance=prov,
                provenance_note=prov_note,
                is_available=prov != SensorProvenance.UNAVAILABLE,
                message=msg
            )
            results.append(eval_item)



        return results

    def evaluate_rules(
        self,
        telemetry: CanonicalESPTelemetry,
        feature_dict: Optional[Dict[str, float]] = None
    ) -> List[RuleEvaluationResult]:
        """Evaluates multivariate fault rules."""
        results: List[RuleEvaluationResult] = []
        
        # Build evaluation context combining telemetry and feature dictionary
        context = {k: getattr(telemetry, k, 0.0) for k in self.envelopes.keys()}
        context["differential_pressure_psi"] = max(0.0, telemetry.discharge_pressure_psi - telemetry.intake_pressure_psi)
        if feature_dict:
            context.update(feature_dict)

        for r in self.rules:
            rule_id = r.get("id")
            fault_str = r.get("fault", "HEALTHY")
            fault_enum = getattr(FaultClass, fault_str, FaultClass.UNKNOWN_UNSEEN)
            conditions = r.get("conditions", [])
            severity = r.get("severity", "WARNING")
            explanation = r.get("explanation", "")
            persist_req = float(r.get("persistence_seconds", 0))

            # Evaluate each condition safely in Python
            all_met = True
            for cond in conditions:
                try:
                    # Simple safe evaluation against context
                    passed = eval(cond, {"__builtins__": {}}, context)
                    if not passed:
                        all_met = False
                        break
                except Exception:
                    all_met = False
                    break

            # Check / update persistence
            well_rule_key = f"{telemetry.esp_id}_{rule_id}"
            now_ts = datetime.now(timezone.utc).timestamp()
            
            if all_met:
                if well_rule_key not in self.rule_start_times:
                    self.rule_start_times[well_rule_key] = now_ts
                
                elapsed = now_ts - self.rule_start_times[well_rule_key]
                is_active = elapsed >= persist_req or persist_req <= 0
            else:
                self.rule_start_times.pop(well_rule_key, None)
                elapsed = 0.0
                is_active = False

            if is_active:
                results.append(RuleEvaluationResult(
                    rule_id=rule_id,
                    fault=fault_enum,
                    triggered=True,
                    severity=severity,
                    condition_description=" AND ".join(conditions),
                    persistence_seconds=elapsed,
                    explanation=explanation
                ))

        return results
