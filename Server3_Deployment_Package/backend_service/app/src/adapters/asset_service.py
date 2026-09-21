import os
import json
import logging
from typing import List, Dict, Any, Optional
from src.schemas.contracts import AssetContextPayload

logger = logging.getLogger(__name__)

SEEDS_JSON_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "..", "data", "advait", "asset_context_initial_seed_v2_rich.json"
)

class AssetService:
    """
    Asset Service:
    - Provides normalized asset context for ESP installations.
    - Connects to Advait REST API on ADVAIT_API_URL (default: http://localhost:8090/api/v1).
    - Maintains local rich JSON projection cache fallback.
    """

    def __init__(self, api_url: Optional[str] = None):
        self.api_url = api_url or os.getenv("ADVAIT_API_URL", None)
        self._local_assets = None

    def get_asset(self, asset_id: str) -> AssetContextPayload:
        """
        Fetch normalized AssetContextPayload for an asset.
        """
        if self.api_url and asset_id and asset_id not in ("UNKNOWN", "NONE", "FLEET"):
            try:
                return self._query_advait_api(asset_id)
            except Exception as e:
                logger.warning(f"Advait API call failed for '{asset_id}' ({e}). Using local projection cache.")

        return self.get_cached_asset_projection(asset_id)

    # Public alias: several call-sites (pipeline runners, BFF routes) request the
    # asset context under the name `get_asset_context`. Provide it so a wrong-method
    # name never silently falls through a bare `except` and feeds the LLM generic
    # default specs instead of the real registry record.
    def get_asset_context(self, asset_id: str) -> AssetContextPayload:
        """Alias for get_asset(). Returns the normalized AssetContextPayload."""
        return self.get_asset(asset_id)

    def get_cached_asset_projection(self, asset_id: str) -> AssetContextPayload:
        """
        Local rich JSON projection cache for offline development and testing.
        """
        if self._local_assets is None:
            self._load_local_rich_json()

        raw_asset = self._local_assets.get(asset_id)
        if raw_asset:
            return self._parse_advait_dict(raw_asset)

        # Fallback for synthetic/unknown test asset IDs
        return AssetContextPayload(
            asset_id=asset_id,
            well_id=f"WELL-{asset_id.split('-')[-1]}" if "-" in asset_id else "WELL-001",
            asset_type="ESP",
            status="ACTIVE",
            source_system="ADVAIT_CACHE_FALLBACK",
            installation_depth_ft=8500.0,
            pump_model="Weatherford DN1750",
            motor_rating_hp=250.0,
            nameplate_current_amps=65.0,
            be_point_bpd=1750.0
        )

    def _query_advait_api(self, asset_id: str) -> AssetContextPayload:
        import httpx
        # Try context endpoint first with fast 0.2s timeout
        url = f"{self.api_url}/assets/{asset_id}/context"
        try:
            resp = httpx.get(url, timeout=0.2)
            if resp.status_code == 200:
                return self._parse_advait_dict(resp.json())
        except Exception:
            pass

        # Fallback to direct asset endpoint
        resp = httpx.get(f"{self.api_url}/assets/{asset_id}", timeout=0.2)
        resp.raise_for_status()
        return self._parse_advait_dict(resp.json())

    def _load_local_rich_json(self):
        self._local_assets = {}
        candidate_paths = [
            os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "advait", "asset_context_initial_seed_v2_rich.json")),
            os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "data", "advait", "asset_context_initial_seed_v2_rich.json")),
            os.path.abspath(os.path.join("data", "advait", "asset_context_initial_seed_v2_rich.json")),
            os.path.abspath(os.path.join("..", "data", "advait", "asset_context_initial_seed_v2_rich.json")),
            os.path.abspath(SEEDS_JSON_PATH)
        ]
        target_path = None
        for p in candidate_paths:
            if os.path.exists(p):
                target_path = p
                break
        if target_path:
            with open(target_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                for item in data.get("assets", []):
                    self._local_assets[item["asset_id"]] = item

    def _parse_advait_dict(self, d: Dict[str, Any]) -> AssetContextPayload:
        esp = d.get("esp_configuration", {})
        pump = esp.get("pump", {}) or {}
        motor = esp.get("motor", {}) or {}
        well = d.get("well_context", {}) or {}

        # Extract numerical specs with sensible defaults
        depth_m = well.get("pump_setting_depth_m")
        depth_ft = (depth_m * 3.28084) if depth_m else 8500.0

        bep_bpd = pump.get("bep_flow_bpd") or 1750.0
        pump_model = pump.get("model") or "Weatherford DN1750"
        motor_hp = motor.get("rated_power_hp") or 250.0
        motor_amps = motor.get("rated_current_a") or 65.0

        return AssetContextPayload(
            asset_id=d.get("asset_id", "UNKNOWN"),
            well_id=d.get("well_id", d.get("asset_id", "UNKNOWN")),
            asset_type=d.get("asset_type", "ESP"),
            status=d.get("asset_status") or "ACTIVE",
            source_system="ADVAIT_REGISTRY",
            installation_depth_ft=round(depth_ft, 1),
            pump_model=pump_model,
            motor_rating_hp=motor_hp,
            nameplate_current_amps=motor_amps,
            be_point_bpd=bep_bpd,
            hierarchy=d.get("hierarchy"),
            well_context=d.get("well_context"),
            esp_configuration=esp,
            tag_mapping=d.get("tag_mapping"),
            operating_envelope=d.get("operating_envelope"),
            source_provenance=d.get("source_provenance")
        )
