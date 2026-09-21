import os
import json
import pandas as pd
from typing import List, Optional, Dict, Any
from src.schemas.canonical import TelemetryMetric
from src.schemas.mapping import MappingConfig, FieldMapping


class TelemetryAdapter:
    """Universal Telemetry Adapter converting raw telemetry streams into canonical TelemetryMetric objects."""

    def __init__(self, mapping_config: MappingConfig, telemetry_csv_path: Optional[str] = None):
        self.mapping_config = mapping_config
        self.telemetry_csv_path = telemetry_csv_path
        self._mappings = {m.source_field: m for m in mapping_config.get_mappings_list()}
        self._canonical_mappings = {m.canonical_field: m for m in mapping_config.get_mappings_list()}

    @classmethod
    def from_config_file(cls, mapping_config_path: str, telemetry_csv_path: Optional[str] = None) -> "TelemetryAdapter":
        # utf-8-sig transparently strips a UTF-8 BOM if present and reads plain utf-8 too.
        with open(mapping_config_path, "r", encoding="utf-8-sig") as f:
            data = json.load(f)
        config = MappingConfig(**data)
        return cls(mapping_config=config, telemetry_csv_path=telemetry_csv_path)

    def fetch_from_api(self, asset_id: str, api_url: str = "http://localhost:8081") -> List[TelemetryMetric]:
        """
        Fetch latest canonical telemetry record from ESP Telemetry Mock API (:8081).
        Grounded in ESP_APM_Telemetry_Service_Consumption_Architecture.docx §3, §5.
        """
        import urllib.request
        import urllib.error
        url = f"{api_url.rstrip('/')}/api/v1/assets/{asset_id}/telemetry/current"
        try:
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=1.5) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    metrics = []
                    ts = data.get("timestamp", "")
                    for sig, val_obj in data.get("measurements", {}).items():
                        val = val_obj.get("value", 0.0) if isinstance(val_obj, dict) else float(val_obj)
                        unit = val_obj.get("unit", "") if isinstance(val_obj, dict) else ""
                        metrics.append(TelemetryMetric(
                            parameter_name=sig,
                            current_value=val,
                            unit=unit,
                            sensor_tag=f"raw_{sig}",
                            metric_type=self._determine_metric_type(sig, sig),
                            timestamp=ts
                        ))
                    return metrics
        except Exception:
            pass

        # Fall back to CSV load if API unavailable
        return self.load_latest_telemetry(asset_id)

    def load_latest_telemetry(self, asset_id: str, csv_path: Optional[str] = None) -> List[TelemetryMetric]:
        """Loads the most recent telemetry record for the specified asset_id and maps to canonical TelemetryMetric."""
        target_path = csv_path or self.telemetry_csv_path
        if not target_path or not os.path.exists(target_path):
            raise FileNotFoundError(f"Telemetry data file not found at path: {target_path}")

        df = pd.read_csv(target_path)
        if df.empty:
            return []

        # Filter by asset_id if column exists
        if "asset_id" in df.columns:
            asset_df = df[df["asset_id"] == asset_id]
            if asset_df.empty:
                return []
            latest_row = asset_df.iloc[-1].to_dict()
        else:
            latest_row = df.iloc[-1].to_dict()

        return self._convert_row_to_canonical(latest_row)

    def _determine_metric_type(self, canonical_name: str, source_name: str) -> str:
        name_lower = (canonical_name + " " + source_name).lower()
        if "thermal" in name_lower or "temp" in name_lower:
            return "thermal"
        elif "pressure" in name_lower or "pip" in name_lower or "pdp" in name_lower:
            return "pressure"
        elif "vibration" in name_lower or "vib" in name_lower:
            return "vibration"
        elif "electrical" in name_lower or "current" in name_lower or "imbalance" in name_lower:
            return "electrical"
        elif "flow" in name_lower or "efficiency" in name_lower:
            return "hydraulic"
        return "general"

    def _convert_row_to_canonical(self, row: Dict[str, Any]) -> List[TelemetryMetric]:
        metrics: List[TelemetryMetric] = []
        timestamp = str(row.get("timestamp", "now"))

        # Process mapped fields
        for src_field, val in row.items():
            if src_field in ("timestamp", "asset_id"):
                continue

            mapping: Optional[FieldMapping] = self._mappings.get(src_field) or self._canonical_mappings.get(src_field)
            if mapping:
                canonical_name = mapping.canonical_field
                unit = mapping.unit or ""
                valid_range = mapping.valid_range
            else:
                # If unmapped, fallback to raw field name
                canonical_name = src_field
                unit = ""
                valid_range = None

            try:
                numeric_val = float(val)
            except (ValueError, TypeError):
                continue

            status = "normal"
            if valid_range and len(valid_range) == 2:
                min_val, max_val = valid_range
                if numeric_val < min_val or numeric_val > max_val:
                    status = "warning"

            metric_type = self._determine_metric_type(canonical_name, src_field)

            metrics.append(
                TelemetryMetric(
                    parameter_name=canonical_name,
                    metric_type=metric_type,
                    current_value=numeric_val,
                    unit=unit,
                    status=status,
                    timestamp=timestamp,
                )
            )

        return metrics
