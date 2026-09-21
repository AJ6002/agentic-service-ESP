import json
import os
from typing import List, Dict, Any, Optional
from src.schemas.canonical import TelemetryMetric


class RuleAdapter:
    """Universal Rule Adapter evaluating deterministic diagnostic rules against TelemetryMetric streams."""

    def __init__(self, rules_json_path: Optional[str] = None):
        self.rules_json_path = rules_json_path
        self.rules: List[Dict[str, Any]] = []
        if rules_json_path and os.path.exists(rules_json_path):
            with open(rules_json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.rules = data.get("rules", data if isinstance(data, list) else [])

    @classmethod
    def from_file(cls, rules_json_path: str) -> "RuleAdapter":
        return cls(rules_json_path=rules_json_path)

    def evaluate_rules(self, metrics: List[TelemetryMetric]) -> List[Dict[str, Any]]:
        """Evaluates all rules against current canonical telemetry metrics."""
        evaluations = []
        if not metrics or not self.rules:
            return evaluations

        # Build metric lookup map (canonical name and lowercase name)
        metric_map: Dict[str, TelemetryMetric] = {}
        for m in metrics:
            metric_map[m.parameter_name.lower()] = m

        for rule in self.rules:
            rule_id = rule.get("rule_id", "R_UNKNOWN")
            metric_name = rule.get("metric_name", "")
            operator = rule.get("operator", ">")
            threshold = float(rule.get("threshold", 0.0))
            severity = rule.get("severity", "warning")

            # Match against metric map
            matched_metric = None
            for key, m in metric_map.items():
                if metric_name.lower() in key or key in metric_name.lower():
                    matched_metric = m
                    break

            if not matched_metric:
                continue

            val = matched_metric.current_value
            violated = False
            if operator in (">", "gt") and val > threshold:
                violated = True
            elif operator in (">=", "gte") and val >= threshold:
                violated = True
            elif operator in ("<", "lt") and val < threshold:
                violated = True
            elif operator in ("<=", "lte") and val <= threshold:
                violated = True
            elif operator in ("==", "eq") and val == threshold:
                violated = True

            if violated:
                evaluations.append({
                    "rule_id": rule_id,
                    "metric_name": matched_metric.parameter_name,
                    "observed_value": val,
                    "threshold": threshold,
                    "operator": operator,
                    "severity": severity,
                    "status": "violated",
                    "description": rule.get("description", f"{matched_metric.parameter_name} ({val}) violated threshold {threshold}"),
                    "timestamp": matched_metric.timestamp,
                })

        return evaluations
