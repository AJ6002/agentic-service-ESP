import json
from pathlib import Path
import pytest
import yaml

from app.context.well_ids import is_canonical, list_canonical_wells, normalize_well_id
from app.gateway.signal_names import (
    is_known_signal,
    normalize_measurements_dict,
    to_canonical_signal_name,
    to_scada_signal_name,
    CANONICAL_SIGNALS,
)
from app.gateway.tool_gateway import execute_tool_call, dispatch_plan_calls
from app.contracts.plan import PlanArtifact, PlanCall


def test_well_id_canonical_14_registry():
    wells = list_canonical_wells()
    assert len(wells) == 14
    for w in wells:
        assert is_canonical(w) is True
        assert normalize_well_id(w) == w


def test_well_id_numeric_equivalence_normalization():
    # Unpadded canonicals
    assert normalize_well_id("FS-017") == "FS-17"
    assert normalize_well_id("fs-17") == "FS-17"
    assert normalize_well_id("FS-091") == "FS-91"
    assert normalize_well_id("fs-91") == "FS-91"

    # Padded canonicals
    assert normalize_well_id("FS-14") == "FS-014"
    assert normalize_well_id("FS-014") == "FS-014"
    assert normalize_well_id("FS-16") == "FS-016"
    assert normalize_well_id("FS-016") == "FS-016"
    assert normalize_well_id("FS-31") == "FS-031"
    assert normalize_well_id("FS-031") == "FS-031"

    # Exact suffix canonicals
    assert normalize_well_id("FSWS-001-A") == "FSWS-001-A"
    assert normalize_well_id("fsws-001-a") == "FSWS-001-A"

    # Non-existent wells must be rejected, NOT silently coerced
    assert normalize_well_id("FWS-04") is None
    assert normalize_well_id("UNKNOWN-99") is None
    assert normalize_well_id("") is None
    assert normalize_well_id(None) is None


def test_signal_name_normalization():
    assert to_canonical_signal_name("STD_INT_PRS_PSI") == "int_prs_psi"
    assert to_canonical_signal_name("STD_MOTOR_TEMP_C") == "motor_temp_c"
    assert to_canonical_signal_name("STD_VIBRATION_G") == "vibration_g"
    assert to_canonical_signal_name("int_prs_psi") == "int_prs_psi"

    assert to_scada_signal_name("int_prs_psi") == "STD_INT_PRS_PSI"
    assert to_scada_signal_name("motor_temp_c") == "STD_MOTOR_TEMP_C"

    raw = {
        "STD_INT_PRS_PSI": 420.5,
        "STD_DISCH_PRS_PSI": 1900.0,
        "STD_MOTOR_TEMP_C": 88.0,
        "amp_a": 36.0,
    }
    normalized = normalize_measurements_dict(raw)
    assert normalized == {
        "int_prs_psi": 420.5,
        "disch_prs_psi": 1900.0,
        "motor_temp_c": 88.0,
        "amp_a": 36.0,
    }


def test_spec_derived_config_tables():
    base_dir = Path(__file__).resolve().parent.parent
    freshness_path = base_dir / "config" / "qod_freshness.yaml"
    bounds_path = base_dir / "config" / "signal_bounds.yaml"

    with open(freshness_path, "r", encoding="utf-8") as f:
        freshness = yaml.safe_load(f)
    with open(bounds_path, "r", encoding="utf-8") as f:
        bounds = yaml.safe_load(f)

    assert "domains" in freshness
    for d in ["live_telemetry", "live_vfm", "events", "ml", "kpi", "cards", "historian"]:
        assert d in freshness["domains"]

    assert "signals" in bounds
    signals = bounds["signals"]
    assert len(signals) >= 20

    # Ensure every signal in signal_bounds is a known canonical signal
    for s_name, s_cfg in signals.items():
        assert is_known_signal(s_name), f"Signal {s_name} in bounds table is not in CANONICAL_SIGNALS"
        assert "unit" in s_cfg
        assert "min_plausible" in s_cfg
        assert "max_plausible" in s_cfg
        assert s_cfg["min_plausible"] <= s_cfg["max_plausible"]


@pytest.mark.anyio
async def test_tool_gateway_zero_fabricated_data_on_unreachable():
    """
    CRUCIAL ANTI-FABRICATION TEST (SLICE_2_PLAN Rule B):
    When an endpoint is unreachable or fails, the tool gateway MUST NOT
    return a hardcoded measurement dict. It must honestly return FAILED or TIMEOUT.
    """
    call = PlanCall(
        seq=1,
        kind="READ",
        tool="get_live_telemetry",
        args={"asset_id": "FS-17"},
    )
    # Point to a guaranteed unreachable port
    import os
    orig_184 = os.environ.get("SERVER184_BASE_URL")
    orig_3 = os.environ.get("SERVER3_BASE_URL")
    try:
        os.environ["SERVER184_BASE_URL"] = "http://127.0.0.1:59999"
        os.environ["SERVER3_BASE_URL"] = "http://127.0.0.1:59999"

        res = await execute_tool_call(call)
        assert res.status in ("FAILED", "TIMEOUT")
        # Assert no fake measurements are returned
        assert res.raw_response is None or "measurements" not in res.raw_response
        assert res.error is not None
    finally:
        if orig_184:
            os.environ["SERVER184_BASE_URL"] = orig_184
        else:
            os.environ.pop("SERVER184_BASE_URL", None)
        if orig_3:
            os.environ["SERVER3_BASE_URL"] = orig_3
        else:
            os.environ.pop("SERVER3_BASE_URL", None)


@pytest.mark.anyio
async def test_tool_gateway_rejects_missing_asset():
    call = PlanCall(
        seq=1,
        kind="READ",
        tool="get_live_telemetry",
        args={},  # No asset_id
    )
    res = await execute_tool_call(call)
    assert res.status == "FAILED"
    assert "requires asset_id" in res.error
