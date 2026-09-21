"""
Calculation Registry Loader & Configuration Resolver
Grounded in engineering_calculation_registry.yaml & ESP_APM_Engineering_Service_Architecture_Granular_Design.docx §8
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from src.schemas.engineering_contracts import CalculationStatus, CalculationDomain


class CalculationDefinition(BaseModel):
    id: str
    name: str
    domain: CalculationDomain
    formula_expression: str
    required_inputs: List[str]
    optional_inputs: List[str] = Field(default_factory=list)
    output_name: str
    output_unit: str
    reference_authority: str
    status: CalculationStatus
    failure_condition: str


# Immutable Authoritative Registry Catalogue (engineering_calculation_registry.yaml lines 15-406)
_REGISTRY_CATALOGUE: Dict[str, CalculationDefinition] = {
    "A1": CalculationDefinition(
        id="A1",
        name="Pressure to Head Conversion",
        domain=CalculationDomain.PHYSICS,
        formula_expression="Head (ft) = 2.31 * delta_p (psi) / SG",
        required_inputs=["pressure_diff_psi", "composite_sg"],
        optional_inputs=["intake_pressure_pip_psi", "discharge_pressure_pdp_psi"],
        output_name="total_dynamic_head_ft",
        output_unit="ft",
        reference_authority="API RP 11S2 / Fundamental Hydraulics",
        status=CalculationStatus.SUCCESS,
        failure_condition="FAIL_CLOSED if SG <= 0 or delta_p <= 0"
    ),
    "A2": CalculationDefinition(
        id="A2",
        name="Hydraulic Power Calculation",
        domain=CalculationDomain.PHYSICS,
        formula_expression="P_hyd (hp) = (Q_bpd * H_ft * SG) / 3960",
        required_inputs=["flow_rate_q_bpd", "total_dynamic_head_ft", "composite_sg"],
        optional_inputs=[],
        output_name="hydraulic_power_hp",
        output_unit="hp",
        reference_authority="API RP 11S2 §4.2",
        status=CalculationStatus.SUCCESS,
        failure_condition="FAIL_CLOSED if Q < 0 or H < 0 or SG <= 0"
    ),
    "A4": CalculationDefinition(
        id="A4",
        name="Frequency / Speed Correction (Affinity Laws)",
        domain=CalculationDomain.PHYSICS,
        formula_expression="Q_adj = Q * (f/60), H_adj = H * (f/60)^2, P_adj = P * (f/60)^3",
        required_inputs=["operating_frequency_hz"],
        optional_inputs=["flow_rate_q_bpd", "total_dynamic_head_ft"],
        output_name="adjusted_frequency_metrics",
        output_unit="multi",
        reference_authority="Centrifugal Pump Affinity Laws / ISO 13709",
        status=CalculationStatus.SUCCESS,
        failure_condition="FAIL_CLOSED if operating_frequency_hz <= 0"
    ),
    "A5": CalculationDefinition(
        id="A5",
        name="Best Efficiency Point Percentage (%BEP)",
        domain=CalculationDomain.PHYSICS,
        formula_expression="%BEP = (Q_operating / Q_BEP_at_freq) * 100",
        required_inputs=["flow_rate_q_bpd", "bep_flow_rate_bpd", "operating_frequency_hz"],
        optional_inputs=[],
        output_name="bep_operating_percentage",
        output_unit="%",
        reference_authority="OEM Performance Specs / API RP 11S2",
        status=CalculationStatus.SUCCESS,
        failure_condition="FAIL_CLOSED if bep_flow_rate_bpd <= 0"
    ),
    "C2": CalculationDefinition(
        id="C2",
        name="Motor Load Percentage",
        domain=CalculationDomain.ASSET,
        formula_expression="%Load = (I_measured / I_nameplate) * 100",
        required_inputs=["motor_measured_current_a", "motor_nameplate_current_a"],
        optional_inputs=["operating_frequency_hz"],
        output_name="motor_load_percentage",
        output_unit="%",
        reference_authority="IEEE Std 1018 / Motor Nameplate",
        status=CalculationStatus.SUCCESS,
        failure_condition="FAIL_CLOSED if nameplate_current <= 0 or measured_current < 0"
    ),
    "F1": CalculationDefinition(
        id="F1",
        name="Current Trend Slope",
        domain=CalculationDomain.DIAGNOSTIC,
        formula_expression="Slope = delta_I / delta_t (Amps / hour)",
        required_inputs=["motor_measured_current_a"],
        optional_inputs=["historical_buffer"],
        output_name="current_trend_amps_per_hr",
        output_unit="A/hr",
        reference_authority="Diagnostic Statistical Filtering",
        status=CalculationStatus.SUCCESS,
        failure_condition="FAIL_CLOSED if telemetry buffer insufficient"
    ),
    "B1": CalculationDefinition(
        id="B1",
        name="OEM Pump Performance Curve Lookup",
        domain=CalculationDomain.OEM,
        formula_expression="Interpolated H, Efficiency, BHP from OEM H-Q curve at frequency f",
        required_inputs=["flow_rate_q_bpd", "operating_frequency_hz", "pump_model_id", "stage_count"],
        optional_inputs=[],
        output_name="oem_curve_point",
        output_unit="multi",
        reference_authority="OEM Master Datasheet (Baker Hughes / Schlumberger / REDA)",
        status=CalculationStatus.REQUIRES_OEM_DATA,
        failure_condition="FAIL_CLOSED if matching OEM curve dataset missing"
    ),
    "E1": CalculationDefinition(
        id="E1",
        name="Recommended Operating Range (ROR) Check",
        domain=CalculationDomain.LIMITS,
        formula_expression="Verify Q_operating within [Q_min_ror, Q_max_ror]",
        required_inputs=["flow_rate_q_bpd", "bep_flow_rate_bpd"],
        optional_inputs=["operating_frequency_hz"],
        output_name="ror_status",
        output_unit="status",
        reference_authority="Client Operating Limits / API RP 11S2",
        status=CalculationStatus.SUCCESS,
        failure_condition="FAIL_CLOSED if ROR bounds undefined"
    )
}


class CalculationRegistryLoader:
    """Provides access to immutable calculation definitions"""

    @staticmethod
    def get_definition(calc_id: str) -> Optional[CalculationDefinition]:
        return _REGISTRY_CATALOGUE.get(calc_id.upper())

    @staticmethod
    def list_all() -> Dict[str, CalculationDefinition]:
        return _REGISTRY_CATALOGUE
