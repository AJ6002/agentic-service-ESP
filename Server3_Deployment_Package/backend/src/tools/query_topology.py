from typing import Dict, Any, List
from src.adapters.graph import GraphAdapter


def query_topology_tool(graph_adapter: GraphAdapter, asset_id: str, query_type: str = "trace", target: str = "") -> Dict[str, Any]:
    """Tool function to query topology and cause-effect relationships from the knowledge graph."""
    if query_type == "components":
        components = graph_adapter.get_components(asset_id)
        return {"components": [c.model_dump() for c in components]}
    elif query_type == "failure_modes":
        modes = graph_adapter.get_failure_modes(target or asset_id)
        return {"failure_modes": modes}
    else:
        traces = graph_adapter.trace_cause_effect(target or asset_id)
        return {"cause_effect_traces": traces}
