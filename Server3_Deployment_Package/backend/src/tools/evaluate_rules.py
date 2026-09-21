from typing import List, Dict, Any
from src.adapters.rules import RuleAdapter
from src.schemas.canonical import TelemetryMetric


def evaluate_rules_tool(rule_adapter: RuleAdapter, metrics: List[TelemetryMetric]) -> List[Dict[str, Any]]:
    """Tool function to evaluate deterministic diagnostic rules against canonical telemetry metrics."""
    return rule_adapter.evaluate_rules(metrics=metrics)
