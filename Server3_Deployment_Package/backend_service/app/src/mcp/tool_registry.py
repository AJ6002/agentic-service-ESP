"""
MCP Tool Registry — the governed service layer for the ESP agentic platform.

Single source of truth for every tool the agent (Option A) and external MCP/HTTP
clients (Option B) may call. Each `ToolSpec` binds:
  - a stable tool name
  - a JSON Schema for its arguments
  - governance metadata (read_only, allowed_objectives, domain)
  - a handler callable that invokes a REAL application service

Governance (allowed_objectives) can be overridden declaratively via
`src/api/mcp/mcp_registry.yaml`; the Python definitions here are the authoritative
default so the registry always works even if the YAML is missing.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)

# Sentinel meaning "callable under any objective".
ALL_OBJECTIVES = "*"


class ToolExecutionError(Exception):
    """Raised when a tool handler fails during execution."""


@dataclass
class ToolSpec:
    name: str
    description: str
    input_schema: Dict[str, Any]
    handler: Callable[[Dict[str, Any]], Dict[str, Any]]
    read_only: bool = True
    allowed_objectives: List[str] = field(default_factory=lambda: [ALL_OBJECTIVES])
    domain: str = "general"

    def is_allowed_for(self, objective_id: Optional[str]) -> bool:
        """RBAC check: is this tool callable under the given objective?"""
        if ALL_OBJECTIVES in self.allowed_objectives:
            return True
        if objective_id is None:
            return False
        return objective_id in self.allowed_objectives

    def to_manifest(self) -> Dict[str, Any]:
        """Serializable description (no handler) for tool discovery over HTTP/MCP."""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema,
            "read_only": self.read_only,
            "allowed_objectives": self.allowed_objectives,
            "domain": self.domain,
        }


class ToolRegistry:
    """In-memory catalogue of governed tools."""

    def __init__(self) -> None:
        self._tools: Dict[str, ToolSpec] = {}

    def register(self, spec: ToolSpec) -> None:
        if spec.name in self._tools:
            logger.warning("ToolRegistry: overwriting existing tool '%s'", spec.name)
        self._tools[spec.name] = spec

    def get(self, name: str) -> Optional[ToolSpec]:
        return self._tools.get(name)

    def names(self) -> List[str]:
        return sorted(self._tools.keys())

    def list(self, objective_id: Optional[str] = None) -> List[ToolSpec]:
        specs = [self._tools[n] for n in self.names()]
        if objective_id is None:
            return specs
        return [s for s in specs if s.is_allowed_for(objective_id)]


# ---------------------------------------------------------------------------
# Lazy service singletons (constructed on first use so importing the registry is cheap
# and never triggers DB / network connections at import time).
# ---------------------------------------------------------------------------
_SERVICES: Dict[str, Any] = {}


def _engineering():
    if "engineering" not in _SERVICES:
        from src.services.engineering_service import EngineeringService
        _SERVICES["engineering"] = EngineeringService()
    return _SERVICES["engineering"]


def _telemetry():
    if "telemetry" not in _SERVICES:
        from src.services.telemetry_service import TelemetryService
        _SERVICES["telemetry"] = TelemetryService()
    return _SERVICES["telemetry"]


def _twin():
    if "twin" not in _SERVICES:
        from src.services.twin_service import DigitalTwinService
        _SERVICES["twin"] = DigitalTwinService()
    return _SERVICES["twin"]


def _retrieval():
    if "retrieval" not in _SERVICES:
        from src.services.retrieval_service import RetrievalService
        _SERVICES["retrieval"] = RetrievalService()
    return _SERVICES["retrieval"]


def _asset_context():
    if "asset_context" not in _SERVICES:
        from src.services.asset_context_service import AssetContextService
        _SERVICES["asset_context"] = AssetContextService()
    return _SERVICES["asset_context"]


# ---------------------------------------------------------------------------
# Tool handlers — each maps a validated argument dict to a serializable result dict,
# wrapping a REAL application service call.
# ---------------------------------------------------------------------------
def _h_calculate_tdh(args: Dict[str, Any]) -> Dict[str, Any]:
    from shared.schemas.engineering import TDHRequest
    req = TDHRequest(
        pdp_psi=float(args["pdp_psi"]),
        pip_psi=float(args["pip_psi"]),
        fluid_sg=float(args.get("fluid_sg", 1.0)),
    )
    return _engineering().calculate_tdh(req).model_dump()


def _h_calculate_bep(args: Dict[str, Any]) -> Dict[str, Any]:
    from shared.schemas.engineering import BEPRequest
    req = BEPRequest(
        current_flow_bpd=float(args["current_flow_bpd"]),
        bep_target_bpd=float(args.get("bep_target_bpd", 1750.0)),
    )
    return _engineering().calculate_bep(req).model_dump()


def _h_calculate_drawdown(args: Dict[str, Any]) -> Dict[str, Any]:
    from shared.schemas.engineering import DrawdownRequest
    req = DrawdownRequest(
        static_reservoir_pressure_psi=float(args["static_reservoir_pressure_psi"]),
        flowing_bottomhole_pressure_psi=float(args["flowing_bottomhole_pressure_psi"]),
    )
    return _engineering().calculate_drawdown(req).model_dump()


def _h_get_latest_telemetry(args: Dict[str, Any]) -> Dict[str, Any]:
    return _telemetry().get_latest(str(args["asset_id"])).model_dump()


def _h_get_ml_assessment(args: Dict[str, Any]) -> Dict[str, Any]:
    from src.adapters.live_data_bridge import live_bridge
    result = live_bridge.get_ml_assessment(str(args["asset_id"]))
    if not result:
        return {"available": False, "asset_id": args["asset_id"],
                "note": "cced_esp ML assessment unavailable (backend offline or no data)."}
    return {"available": True, "asset_id": args["asset_id"], "assessment": result}


def _h_get_model_output(args: Dict[str, Any]) -> Dict[str, Any]:
    """Normalized ModelOutputPayload (LiveDataBridge -> ML mock API -> deterministic mock)."""
    from src.adapters.model_adapter import ModelAdapter
    out = ModelAdapter().get_model_output(str(args["asset_id"]), args.get("telemetry"))
    return out.model_dump()


def _h_get_asset_context(args: Dict[str, Any]) -> Dict[str, Any]:
    return _asset_context().get_context(str(args["asset_id"])).model_dump()


def _h_list_fleet_assets(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Fleet-wide asset inventory: real data (live cced_esp fleet -> local seed file).
    Prefers live cced_esp fleet data (26-asset canonical list with live health index);
    falls back to the standalone seed file (AssetContextService) if cced_esp is unreachable
    or returns an empty fleet (e.g. its MQTT ingestion is down but the backend is up).
    Never fabricates asset entries — an empty result is reported as empty, not padded.
    """
    from src.adapters.live_data_bridge import live_bridge
    source = "cced_esp_live"
    assets = live_bridge.get_fleet_assets()

    if not assets:
        # Fall back to the standalone seed file — independent of cced_esp's MQTT/DB availability.
        source = "standalone_seed_file"
        asset_ids = _asset_context().list_assets()
        assets = []
        for aid in asset_ids:
            try:
                ctx = _asset_context().get_context(aid)
                assets.append({
                    "asset_id": ctx.asset_id,
                    "well_id": ctx.well_id,
                    "asset_type": ctx.asset_type,
                    "status": ctx.status,
                    "pump_model": ctx.esp_configuration.pump_model if ctx.esp_configuration else None,
                })
            except Exception:
                continue

    # Aggregate counts by asset_type and by pump_model (the "types and counts" the user asked for).
    # NOTE: the two sources use different field names for the same concept — the live cced_esp
    # fleet uses "pump_family"/"operating_state", the standalone seed uses "asset_type"/"pump_model".
    # Check both so aggregation works regardless of which source answered.
    type_counts: Dict[str, int] = {}
    pump_model_counts: Dict[str, int] = {}
    for a in assets:
        atype = str(a.get("asset_type") or a.get("operating_state") or "UNKNOWN")
        type_counts[atype] = type_counts.get(atype, 0) + 1
        pmodel = a.get("pump_model") or a.get("pump_family")
        if pmodel:
            pump_model_counts[str(pmodel)] = pump_model_counts.get(str(pmodel), 0) + 1

    return {
        "source": source,
        "total_count": len(assets),
        "type_counts": type_counts,
        "pump_model_counts": pump_model_counts,
        "assets": assets,
    }


def _h_simulate_frequency_change(args: Dict[str, Any]) -> Dict[str, Any]:
    from shared.schemas.twin import FrequencyWhatIfRequest
    req = FrequencyWhatIfRequest(
        asset_id=str(args["asset_id"]),
        current_frequency_hz=float(args.get("current_frequency_hz", 50.0)),
        target_frequency_hz=float(args["target_frequency_hz"]),
    )
    return _twin().simulate_frequency_change(req).model_dump()


def _h_optimize_vsd_speed(args: Dict[str, Any]) -> Dict[str, Any]:
    from shared.schemas.twin import OptimizationRequest
    req = OptimizationRequest(
        asset_id=str(args["asset_id"]),
        max_motor_temp_c=float(args.get("max_motor_temp_c", 130.0)),
        max_current_amps=float(args.get("max_current_amps", 65.0)),
        min_pip_psi=float(args.get("min_pip_psi", 300.0)),
    )
    return _twin().optimize_vsd_speed(req).model_dump()


def _h_search_knowledge(args: Dict[str, Any]) -> Dict[str, Any]:
    return _retrieval().hybrid_retrieve(
        query=str(args["query"]),
        top_k=int(args.get("top_k", 5)),
        authority_filter=args.get("authority_filter"),
    )


def _h_search_fault_taxonomy(args: Dict[str, Any]) -> Dict[str, Any]:
    matches = _retrieval().search_fault_taxonomy(str(args["fault_query"]))
    return {"fault_query": args["fault_query"], "matches": matches, "count": len(matches)}


def _h_get_pump_curve(args: Dict[str, Any]) -> Dict[str, Any]:
    curve = _retrieval().get_pump_curve(str(args["pump_model"]))
    return {"pump_model": args["pump_model"], "found": curve is not None, "curve": curve}


def _h_search_glossary(args: Dict[str, Any]) -> Dict[str, Any]:
    term = _retrieval().search_glossary(str(args["term"]))
    return {"term": args["term"], "found": term is not None, "definition": term}


# ---------------------------------------------------------------------------
# Default registry construction
# ---------------------------------------------------------------------------
_SIMULATION_OBJECTIVES = ["OP02_PRODUCTION_DECLINE_RCA", "OP03_FAULT_DIAGNOSIS", "OP04_HEALTH_ASSESSMENT"]


def _default_specs() -> List[ToolSpec]:
    return [
        # ---- Engineering (deterministic physics) ----
        ToolSpec(
            name="calculate_tdh",
            description="Calculate Total Dynamic Head (TDH) in feet: (PDP - PIP) * 2.31 / SG.",
            input_schema={
                "type": "object",
                "properties": {
                    "pdp_psi": {"type": "number", "description": "Pump discharge pressure (psi)"},
                    "pip_psi": {"type": "number", "description": "Pump intake pressure (psi)"},
                    "fluid_sg": {"type": "number", "description": "Fluid specific gravity", "default": 1.0},
                },
                "required": ["pdp_psi", "pip_psi"],
            },
            handler=_h_calculate_tdh, read_only=True, domain="engineering",
        ),
        ToolSpec(
            name="calculate_bep",
            description="Calculate Best Efficiency Point (BEP) flow deviation and operating region.",
            input_schema={
                "type": "object",
                "properties": {
                    "current_flow_bpd": {"type": "number", "description": "Current liquid flow rate (BPD)"},
                    "bep_target_bpd": {"type": "number", "description": "Pump design BEP flow (BPD)", "default": 1750.0},
                },
                "required": ["current_flow_bpd"],
            },
            handler=_h_calculate_bep, read_only=True, domain="engineering",
        ),
        ToolSpec(
            name="calculate_drawdown",
            description="Calculate reservoir drawdown differential (static - flowing bottomhole pressure).",
            input_schema={
                "type": "object",
                "properties": {
                    "static_reservoir_pressure_psi": {"type": "number"},
                    "flowing_bottomhole_pressure_psi": {"type": "number"},
                },
                "required": ["static_reservoir_pressure_psi", "flowing_bottomhole_pressure_psi"],
            },
            handler=_h_calculate_drawdown, read_only=True, domain="engineering",
        ),
        # ---- Telemetry ----
        ToolSpec(
            name="get_latest_telemetry",
            description="Fetch the latest telemetry snapshot (live from cced_esp when available, else fallback).",
            input_schema={
                "type": "object",
                "properties": {"asset_id": {"type": "string", "description": "Target ESP asset ID"}},
                "required": ["asset_id"],
            },
            handler=_h_get_latest_telemetry, read_only=True, domain="telemetry",
        ),
        # ---- ML assessment ----
        ToolSpec(
            name="get_ml_assessment",
            description="Fetch live ML health/fault assessment for an asset from the cced_esp unified pipeline.",
            input_schema={
                "type": "object",
                "properties": {"asset_id": {"type": "string", "description": "Target ESP asset ID"}},
                "required": ["asset_id"],
            },
            handler=_h_get_ml_assessment, read_only=True, domain="ml",
        ),
        ToolSpec(
            name="get_model_output",
            description="Fetch the normalized ML model output payload (rules, anomaly, failure, fault, health).",
            input_schema={
                "type": "object",
                "properties": {
                    "asset_id": {"type": "string", "description": "Target ESP asset ID"},
                    "telemetry": {"type": "object", "description": "Optional telemetry dict for mock inference"},
                },
                "required": ["asset_id"],
            },
            handler=_h_get_model_output, read_only=True, domain="ml",
        ),
        # ---- Asset context ----
        ToolSpec(
            name="get_asset_context",
            description="Fetch canonical asset context (hierarchy, ESP config, tag mapping, provenance).",
            input_schema={
                "type": "object",
                "properties": {"asset_id": {"type": "string", "description": "Target ESP asset ID"}},
                "required": ["asset_id"],
            },
            handler=_h_get_asset_context, read_only=True, domain="asset",
        ),
        # ---- Fleet inventory (cross-asset, scope=fleet) ----
        ToolSpec(
            name="list_fleet_assets",
            description="List all fleet assets with type/pump-model counts (real data: live cced_esp "
                        "fleet, falling back to the standalone seed file). No single asset_id required.",
            input_schema={
                "type": "object",
                "properties": {},
                "required": [],
            },
            handler=_h_list_fleet_assets, read_only=True, domain="fleet",
        ),
        # ---- Digital twin (scoped) ----
        ToolSpec(
            name="simulate_frequency_change",
            description="Simulate flow/motor-temp/power under a VSD frequency change (Affinity Laws).",
            input_schema={
                "type": "object",
                "properties": {
                    "asset_id": {"type": "string"},
                    "current_frequency_hz": {"type": "number", "default": 50.0},
                    "target_frequency_hz": {"type": "number"},
                },
                "required": ["asset_id", "target_frequency_hz"],
            },
            handler=_h_simulate_frequency_change, read_only=True, domain="twin",
            allowed_objectives=list(_SIMULATION_OBJECTIVES),
        ),
        ToolSpec(
            name="optimize_vsd_speed",
            description="Constrained optimization for max production within the operating envelope.",
            input_schema={
                "type": "object",
                "properties": {
                    "asset_id": {"type": "string"},
                    "max_motor_temp_c": {"type": "number", "default": 130.0},
                    "max_current_amps": {"type": "number", "default": 65.0},
                    "min_pip_psi": {"type": "number", "default": 300.0},
                },
                "required": ["asset_id"],
            },
            handler=_h_optimize_vsd_speed, read_only=True, domain="twin",
            allowed_objectives=["OP02_PRODUCTION_DECLINE_RCA"],
        ),
        # ---- Knowledge retrieval ----
        ToolSpec(
            name="search_knowledge",
            description="Hybrid KB retrieval (glossary + fault taxonomy + BM25 + pgvector) with authority sort.",
            input_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "top_k": {"type": "integer", "default": 5},
                    "authority_filter": {"type": "string", "description": "Max authority level A-F", "default": None},
                },
                "required": ["query"],
            },
            handler=_h_search_knowledge, read_only=True, domain="knowledge",
        ),
        ToolSpec(
            name="search_fault_taxonomy",
            description="Look up fault patterns by symptom, category, or fault ID.",
            input_schema={
                "type": "object",
                "properties": {"fault_query": {"type": "string"}},
                "required": ["fault_query"],
            },
            handler=_h_search_fault_taxonomy, read_only=True, domain="knowledge",
        ),
        ToolSpec(
            name="get_pump_curve",
            description="Exact pump curve lookup by OEM model name (authoritative curve data).",
            input_schema={
                "type": "object",
                "properties": {"pump_model": {"type": "string"}},
                "required": ["pump_model"],
            },
            handler=_h_get_pump_curve, read_only=True, domain="knowledge",
        ),
        ToolSpec(
            name="search_glossary",
            description="Exact lookup of an ESP engineering/business glossary term.",
            input_schema={
                "type": "object",
                "properties": {"term": {"type": "string"}},
                "required": ["term"],
            },
            handler=_h_search_glossary, read_only=True, domain="knowledge",
        ),
    ]


def _apply_yaml_overrides(specs: List[ToolSpec]) -> None:
    """Optionally override allowed_objectives from mcp_registry.yaml (declarative governance)."""
    yaml_path = os.path.join(os.path.dirname(__file__), "..", "api", "mcp", "mcp_registry.yaml")
    yaml_path = os.path.abspath(yaml_path)
    if not os.path.exists(yaml_path):
        return
    try:
        import yaml
        with open(yaml_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
    except Exception as exc:  # pragma: no cover - defensive
        logger.debug("ToolRegistry: could not load YAML overrides: %s", exc)
        return

    overrides: Dict[str, List[str]] = {}
    for server in (data.get("mcp_servers") or {}).values():
        for tool_name, tool_cfg in (server.get("tools") or {}).items():
            if isinstance(tool_cfg, dict) and "allowed_objectives" in tool_cfg:
                overrides[tool_cfg.get("tool_name", tool_name)] = tool_cfg["allowed_objectives"]

    by_name = {s.name: s for s in specs}
    for name, allowed in overrides.items():
        if name in by_name and isinstance(allowed, list) and allowed:
            by_name[name].allowed_objectives = allowed
            logger.debug("ToolRegistry: applied YAML allowed_objectives override for '%s'", name)


def build_default_registry() -> ToolRegistry:
    registry = ToolRegistry()
    specs = _default_specs()
    _apply_yaml_overrides(specs)
    for spec in specs:
        registry.register(spec)
    return registry


# Global singleton shared by client, REST facade, and MCP server.
_GLOBAL_REGISTRY: Optional[ToolRegistry] = None


def get_global_registry() -> ToolRegistry:
    global _GLOBAL_REGISTRY
    if _GLOBAL_REGISTRY is None:
        _GLOBAL_REGISTRY = build_default_registry()
    return _GLOBAL_REGISTRY
