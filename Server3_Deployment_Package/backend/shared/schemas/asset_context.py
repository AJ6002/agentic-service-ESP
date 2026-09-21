"""
Canonical Asset Context Contract
Grounded in ESP_APM_Asset_Context_Service_Verification_Architecture.docx §6
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class AssetHierarchy(BaseModel):
    customer: Optional[str] = Field(default=None, description="Customer tenant name, e.g. CCED")
    block: Optional[str] = Field(default=None, description="Block identifier, e.g. BLOCK 3")
    station: Optional[str] = Field(default=None, description="Station or field unit name, e.g. FARHA")
    cluster: Optional[str] = Field(default=None, description="Well cluster or pad ID")


class WellContext(BaseModel):
    well_name: Optional[str] = Field(default=None, description="Official well designation")
    latitude: Optional[float] = Field(default=None)
    longitude: Optional[float] = Field(default=None)
    casing_size_in: Optional[float] = Field(default=None)
    tubing_size_in: Optional[float] = Field(default=None)
    perforation_depth_m: Optional[float] = Field(default=None)


class ESPConfiguration(BaseModel):
    pump_model: Optional[str] = Field(default=None, description="OEM pump model name")
    pump_stages: Optional[int] = Field(default=None)
    be_point_bpd: Optional[float] = Field(default=None, description="Best Efficiency Point BPD")
    pump_setting_depth_m: Optional[float] = Field(default=None, description="Pump setting depth in meters")
    motor_hp: Optional[float] = Field(default=None)
    motor_volts: Optional[float] = Field(default=None)
    motor_amps: Optional[float] = Field(default=None)
    cable_type: Optional[str] = Field(default=None)
    vsd_model: Optional[str] = Field(default=None)


class SourceProvenance(BaseModel):
    source_system: str = Field(default="ADVAIT", description="Originating registry system")
    record_version: str = Field(default="v2.1", description="Asset record schema version")
    last_synced_at: str = Field(default="", description="ISO timestamp of last sync")
    authoritative_level: str = Field(default="A", description="Level A Installed Asset Context")


class SignalCatalogItem(BaseModel):
    tag: str = Field(description="Raw SCADA tag name")
    semantic_name: str = Field(description="Canonical metric name")
    unit: str = Field(description="Engineering unit")
    description: Optional[str] = Field(default=None)
    operating_range_min: Optional[float] = Field(default=None)
    operating_range_max: Optional[float] = Field(default=None)
    is_safety_limit: bool = Field(default=False, description="Flag indicating if range is an approved safety limit")


class CanonicalAssetContextPayload(BaseModel):
    asset_id: str = Field(description="Unique canonical asset identifier, e.g. FS-031")
    well_id: str = Field(description="Parent well identifier, e.g. FS-031")
    asset_type: str = Field(default="ESP", description="Equipment classification")
    status: str = Field(default="ACTIVE", description="ACTIVE, SHUT_IN, TRIPPED, UNKNOWN")
    
    hierarchy: Optional[AssetHierarchy] = Field(default=None)
    well_context: Optional[WellContext] = Field(default=None)
    esp_configuration: Optional[ESPConfiguration] = Field(default=None)
    
    tag_mapping: Dict[str, str] = Field(default_factory=dict, description="Raw SCADA tag -> semantic name mapping")
    signal_catalog: List[SignalCatalogItem] = Field(default_factory=list, description="Full signal catalog with units and operating ranges")
    operating_envelope: Dict[str, Any] = Field(default_factory=dict, description="Approved safety operating limits")
    
    source_provenance: SourceProvenance = Field(default_factory=SourceProvenance)
    missing_fields: List[str] = Field(default_factory=list, description="Explicit list of missing or unsupplied context attributes")
