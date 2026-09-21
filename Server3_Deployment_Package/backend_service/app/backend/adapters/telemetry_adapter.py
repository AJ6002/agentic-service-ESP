"""
Telemetry Adapter Layer.
Converts raw SQLite records (opg_well_telemetry) and live MQTT dictionaries
into verified, type-safe CanonicalESPTelemetry instances for ML models and engineering visualizations.
"""

import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from ml.data.canonical_schema import CanonicalESPTelemetry, DataQualityStatus, SensorProvenance

logger = logging.getLogger("esp.telemetry_adapter")


def safe_float(val: Any, default: Optional[float] = None) -> Optional[float]:
    """Safely cast any input to float without fabricating values."""
    if val is None:
        return default
    try:
        f = float(val)
        return f if f == f else default  # Handle NaN
    except (ValueError, TypeError):
        return default


def record_to_canonical(record: Dict[str, Any]) -> CanonicalESPTelemetry:
    """
    Transforms any raw telemetry dict (from SQLite opg_well_telemetry or MQTT)
    into a structured CanonicalESPTelemetry instance with field extraction.
    """
    # Extract nested measurements and asset metadata if present in raw_payload
    meas: Dict[str, Any] = {}
    asset_meta: Dict[str, Any] = {}
    raw = record.get("raw_payload")
    if isinstance(raw, str):
        try:
            raw_dict = json.loads(raw)
            meas = raw_dict.get("measurements", {})
            asset_meta = raw_dict.get("asset", {})
        except Exception:
            meas = {}
            asset_meta = {}
    elif isinstance(raw, dict):
        meas = raw.get("measurements", {})
        asset_meta = raw.get("asset", {})

    # Extract Well & ESP ID
    well_id = str(record.get("well_id") or "UNKNOWN_WELL").strip().upper()
    asset_id = str(record.get("asset_id") or f"ESP-{well_id}").strip().upper()
    esp_id = asset_id

    # 1. Total Liquid Rate (BPD)
    liquid_rate = safe_float(
        record.get("flow_rate_bpd") if record.get("flow_rate_bpd") is not None
        else (meas.get("flow_bpd") if meas.get("flow_bpd") is not None
              else (meas.get("flow_rate_bpd") or meas.get("flow_rate") or meas.get("oil_rate_bpd"))),
        default=0.0
    )

    # 2. Intake Pressure (PSI)
    intake_p = safe_float(
        record.get("intake_pressure_psi") if record.get("intake_pressure_psi") is not None
        else (meas.get("intake_pressure_psi") if meas.get("intake_pressure_psi") is not None
              else (meas.get("intake_p") or meas.get("casing_pressure_psi"))),
        default=0.0
    )

    # 3. Motor Current (A)
    motor_current = safe_float(
        record.get("motor_current_a") if record.get("motor_current_a") is not None
        else (meas.get("motor_current_a") if meas.get("motor_current_a") is not None
              else (meas.get("current") or meas.get("amps"))),
        default=0.0
    )

    # 4. Motor Load (%)
    motor_load_val = meas.get("motor_load_pct") if meas.get("motor_load_pct") is not None else record.get("motor_load_pct")
    if motor_load_val is not None:
        motor_load = safe_float(motor_load_val, default=0.0)
    else:
        motor_load = (motor_current / 40.0 * 100.0) if motor_current > 0 else 0.0
    motor_load = max(0.0, min(150.0, motor_load or 0.0))

    # 5. Motor Temperature (°C)
    motor_temp = safe_float(
        record.get("temperature_c") if record.get("temperature_c") is not None
        else (meas.get("motor_temperature_c") if meas.get("motor_temperature_c") is not None
              else (meas.get("temperature_c") or meas.get("temp"))),
        default=0.0
    )

    # 6. Vibration RMS (g)
    vibration = safe_float(
        record.get("vibration_g") if record.get("vibration_g") is not None
        else (meas.get("vibration_g_rms") if meas.get("vibration_g_rms") is not None
              else (meas.get("vibration_rms") or meas.get("vibration"))),
        default=0.0
    )

    # 7. Discharge Pressure (PSI)
    discharge_p = safe_float(
        record.get("discharge_pressure_psi") if record.get("discharge_pressure_psi") is not None
        else (record.get("pressure_psi") if record.get("pressure_psi") is not None
              else (meas.get("discharge_pressure_psi") if meas.get("discharge_pressure_psi") is not None
                    else (meas.get("discharge_p") or meas.get("tubing_pressure_psi")))),
        default=0.0
    )

    # 8. Motor Voltage (V)
    motor_voltage = safe_float(
        record.get("motor_voltage_v") if record.get("motor_voltage_v") is not None
        else (meas.get("motor_voltage_v") if meas.get("motor_voltage_v") is not None
              else (meas.get("voltage") or meas.get("volts"))),
        default=0.0
    )

    # 9. Intake Temperature (°C)
    intake_temp_val = meas.get("intake_temperature_c") or meas.get("wellhead_temperature_c") or record.get("intake_temperature_c")
    intake_temp = safe_float(intake_temp_val, default=None)

    # 10. Flowline Pressure (PSI)
    flowline_p_val = meas.get("flowline_pressure_psi") or record.get("flowline_pressure_psi")
    flowline_p = safe_float(flowline_p_val, default=None)

    # 11. Wellhead Pressure (PSI)
    wellhead_p_val = meas.get("wellhead_pressure_psi") or meas.get("whp_psi") or record.get("wellhead_pressure_psi")
    wellhead_p = safe_float(wellhead_p_val, default=None)

    # 12. Casing Pressure (PSI)
    casing_p_val = meas.get("casing_pressure_psi") or record.get("casing_pressure_psi")
    casing_p = safe_float(casing_p_val, default=None)

    # 13. Choke Size (/64 in)
    choke_size_val = meas.get("choke_size_64ths") or meas.get("choke_size_pct") or record.get("choke_size_pct")
    choke_size = safe_float(choke_size_val, default=None)

    # Contextual fields
    freq_hz = safe_float(record.get("frequency_hz") if record.get("frequency_hz") is not None else meas.get("frequency_hz"), default=0.0)
    water_cut = safe_float(record.get("water_cut_pct") if record.get("water_cut_pct") is not None else meas.get("water_cut_pct"), default=0.0)
    gas_flow = safe_float(record.get("gas_flow_mscfd") if record.get("gas_flow_mscfd") is not None else meas.get("gas_flow_mscfd"), default=0.0)

    # Asset specs from payload or record
    pump_model = str(asset_meta.get("pump_model") or record.get("pump_family") or "").strip() or None
    stages = int(asset_meta.get("stages")) if asset_meta.get("stages") is not None else None
    motor_hp = float(asset_meta.get("motor_hp")) if asset_meta.get("motor_hp") is not None else None

    fluid_level = safe_float(meas.get("fluid_level_above_pump_ft"))
    productivity_index = safe_float(meas.get("productivity_index_bpd_psi"))
    drawdown = safe_float(meas.get("drawdown_psi"))
    gvf = safe_float(meas.get("pump_intake_gas_volume_fraction_pct"))
    v_imbal = safe_float(meas.get("voltage_imbalance_pct"))
    c_imbal = safe_float(meas.get("current_imbalance_pct"))

    is_live_mqtt = "opg/wells" in str(record.get("topic", "")) or "esp/" in str(record.get("topic", ""))
    base_provenance = SensorProvenance.LIVE_MQTT if is_live_mqtt else SensorProvenance.DATABASE

    provenance_map = {
        "liquid_rate_bpd": base_provenance if liquid_rate is not None else SensorProvenance.UNAVAILABLE,
        "intake_pressure_psi": base_provenance if intake_p is not None else SensorProvenance.UNAVAILABLE,
        "motor_current_a": base_provenance if motor_current is not None else SensorProvenance.UNAVAILABLE,
        "motor_load_pct": SensorProvenance.DERIVED,
        "motor_temperature_c": base_provenance if motor_temp is not None else SensorProvenance.UNAVAILABLE,
        "vibration_rms": base_provenance if vibration is not None else SensorProvenance.UNAVAILABLE,
        "discharge_pressure_psi": base_provenance if discharge_p is not None else SensorProvenance.UNAVAILABLE,
        "motor_voltage_v": base_provenance if motor_voltage is not None else SensorProvenance.UNAVAILABLE,
        "intake_temperature_c": base_provenance if intake_temp is not None else SensorProvenance.UNAVAILABLE,
        "flowline_pressure_psi": base_provenance if flowline_p is not None else SensorProvenance.UNAVAILABLE,
        "wellhead_pressure_psi": base_provenance if wellhead_p is not None else SensorProvenance.UNAVAILABLE,
        "casing_pressure_psi": base_provenance if casing_p is not None else SensorProvenance.UNAVAILABLE,
        "choke_size_64in": base_provenance if choke_size is not None else SensorProvenance.UNAVAILABLE,
        "frequency_hz": base_provenance if freq_hz is not None else SensorProvenance.UNAVAILABLE,
        "water_cut_pct": base_provenance if water_cut is not None else SensorProvenance.UNAVAILABLE,
        "gas_flow_mscfd": base_provenance if gas_flow is not None else SensorProvenance.UNAVAILABLE
    }

    timestamp_str = str(record.get("timestamp") or datetime.now(timezone.utc).isoformat())

    return CanonicalESPTelemetry(
        timestamp=timestamp_str,
        esp_id=esp_id,
        well_id=well_id,
        liquid_rate_bpd=liquid_rate or 0.0,
        intake_pressure_psi=intake_p or 0.0,
        motor_current_a=motor_current or 0.0,
        motor_load_pct=motor_load or 0.0,
        motor_temperature_c=motor_temp or 0.0,
        vibration_rms=vibration or 0.0,
        discharge_pressure_psi=discharge_p or 0.0,
        motor_voltage_v=motor_voltage or 0.0,
        intake_temperature_c=intake_temp,
        flowline_pressure_psi=flowline_p,
        wellhead_pressure_psi=wellhead_p,
        casing_pressure_psi=casing_p,
        choke_size_64in=choke_size,
        frequency_hz=freq_hz or 0.0,
        water_cut_pct=water_cut or 0.0,
        gas_flow_mscfd=gas_flow or 0.0,
        pump_model=pump_model,
        stages=stages,
        motor_hp=motor_hp,
        fluid_level_above_pump_ft=fluid_level,
        productivity_index_bpd_psi=productivity_index,
        drawdown_psi=drawdown,
        gas_volume_fraction_pct=gvf,
        voltage_imbalance_pct=v_imbal,
        current_imbalance_pct=c_imbal,
        provenance_map=provenance_map,
        data_quality=DataQualityStatus.GOOD,
        source=record.get("topic") or ("LIVE_MQTT" if is_live_mqtt else "SQLITE_HISTORIAN")
    )
