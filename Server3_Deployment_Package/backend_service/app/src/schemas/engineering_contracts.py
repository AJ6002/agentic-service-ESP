"""
Canonical Engineering Service Schemas & Data Contracts
Grounded in engineering_input_schema.json & ESP_APM_Engineering_Service_Architecture_Granular_Design.docx
"""

from typing import Dict, Any, List, Optional, Union
from enum import Enum
from pydantic import BaseModel, Field


class CalculationStatus(str, Enum):
    SUCCESS = "SUCCESS"
    BLOCKED = "BLOCKED"
    INVALID_INPUT = "INVALID_INPUT"
    REQUIRES_OEM_DATA = "REQUIRES_OEM_DATA"
    REQUIRES_CONFIGURATION = "REQUIRES_CONFIGURATION"
    ERROR = "ERROR"


class CalculationDomain(str, Enum):
    PHYSICS = "A"
    OEM = "B"
    ASSET = "C"
    FLUID_PVT = "D"
    LIMITS = "E"
    DIAGNOSTIC = "F"
    RELIABILITY = "G"


class RuntimeData(BaseModel):
    flow_rate_q_bpd: Optional[float] = Field(None, description="Measured liquid flow rate in BPD")
    intake_pressure_pip_psi: Optional[float] = Field(None, description="Pump intake pressure in psi")
    discharge_pressure_pdp_psi: Optional[float] = Field(None, description="Pump discharge pressure in psi")
    pressure_diff_psi: Optional[float] = Field(None, description="Differential pressure across pump in psi")
    operating_frequency_hz: float = Field(60.0, description="Operating electrical frequency in Hz")
    motor_measured_current_a: Optional[float] = Field(None, description="Measured motor current in Amperes")
    motor_temperature_c: Optional[float] = Field(None, description="Measured motor temperature in deg C")
    vibration_measured_g: Optional[float] = Field(None, description="Measured vibration in G RMS")
    timestamp: str = Field(..., description="Telemetry snapshot ISO timestamp")


class FluidData(BaseModel):
    water_cut_pct: Optional[float] = Field(None, description="Water cut percentage 0-100%")
    oil_gravity_api: Optional[float] = Field(None, description="Oil gravity in deg API")
    produced_water_sg: Optional[float] = Field(1.02, description="Produced water specific gravity")
    gas_sp_gr: Optional[float] = Field(0.7, description="Gas specific gravity relative to air")
    composite_sg: Optional[float] = Field(None, description="Calculated composite fluid specific gravity")
    viscosity_cp: Optional[float] = Field(None, description="Fluid viscosity in centipoise")


class ESPEquipmentData(BaseModel):
    pump_model_id: str = Field("D1450", description="OEM pump series identifier")
    stage_count: int = Field(120, description="Number of installed pump stages")
    motor_model_id: str = Field("M500", description="OEM motor series identifier")
    motor_nameplate_current_a: float = Field(65.0, description="Motor nameplate rated current in Amperes")
    motor_rating_hp: float = Field(150.0, description="Motor rated horsepower")
    bep_flow_rate_bpd: float = Field(1450.0, description="Best Efficiency Point flow rate at 60 Hz")
    setting_depth_ft: float = Field(6500.0, description="Pump setting depth in feet")


class CalculationRequest(BaseModel):
    calculation_id: str = Field(..., description="Authoritative calculation identifier (e.g. A1, A2, A4, A5, C2, F1, B1, E1)")
    asset_id: str = Field(..., description="Target ESP asset ID")
    runtime: RuntimeData = Field(..., description="Runtime telemetry snapshot")
    fluid: Optional[FluidData] = Field(default_factory=FluidData, description="Fluid / PVT parameters")
    equipment: Optional[ESPEquipmentData] = Field(default_factory=ESPEquipmentData, description="Installed equipment specification")
    overrides: Dict[str, Any] = Field(default_factory=dict, description="Optional parameter overrides")


class ProvenanceRecord(BaseModel):
    calculation_id: str
    formula_version: str = Field("1.0.0", description="Immutable formula version")
    registry_version: str = Field("1.0.0", description="Registry configuration version")
    execution_timestamp: str
    authority_reference: str = Field(..., description="Standard or OEM source authority basis")
    inputs_consumed: Dict[str, Any]


class CalculationResult(BaseModel):
    calculation_id: str
    calculation_name: str
    asset_id: str
    status: CalculationStatus
    value: Optional[float] = Field(None, description="Primary calculated numeric output")
    value_unit: Optional[str] = Field(None, description="Engineering unit of value")
    secondary_outputs: Dict[str, Any] = Field(default_factory=dict, description="Additional derived metrics")
    provenance: ProvenanceRecord
    validity_notes: List[str] = Field(default_factory=list)
    block_reason: Optional[str] = Field(None, description="Reason if status is BLOCKED or INVALID_INPUT")


class CalculationBatchRequest(BaseModel):
    asset_id: str
    calculation_ids: List[str] = Field(..., description="List of calculation IDs to execute in dependency order")
    runtime: RuntimeData
    fluid: Optional[FluidData] = Field(default_factory=FluidData)
    equipment: Optional[ESPEquipmentData] = Field(default_factory=ESPEquipmentData)


class CalculationBatchResponse(BaseModel):
    asset_id: str
    status: str = Field("COMPLETED", description="Overall batch execution status")
    results: Dict[str, CalculationResult]
    failed_count: int = 0
    blocked_count: int = 0
