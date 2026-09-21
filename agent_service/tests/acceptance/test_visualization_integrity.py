import json
import pathlib
import pytest
from datetime import datetime
from app.contracts.evidence import EvidenceItem, EvidencePack
from app.evidence.formatter import format_pack
from app.visualization.planner import plan_visualization

FIXTURES_DIR = pathlib.Path(__file__).parent / "fixtures"


def test_ac_5_1_card_selection_requires_sealed_pack():
    """
    AC-5.1: VisualizationSpec.card_ids must be empty when pack.sealed == false.
    Prevents Bug D (vibration card emitted on failed run).
    """
    data = json.loads((FIXTURES_DIR / "partial_pack.json").read_text(encoding="utf-8"))
    pack = EvidencePack.model_validate(data)
    assert pack.sealed is False

    spec = plan_visualization("OP03_FAULT_DIAGNOSIS", pack, format_pack(pack))
    assert spec.card_ids == [], "Unsealed pack must yield zero card_ids"
    assert spec.evidence_ids == []


def test_ac_5_2_missing_signals_drop_dependent_card():
    """
    AC-5.2: Selected cards must have their required data in the pack.
    """
    # Sealed pack with only motor_temp_c, missing vibration_g
    pack = EvidencePack(
        run_id="R-viz-sealed",
        version=1,
        sealed=True,
        items=[
            EvidenceItem(
                evidence_id="EV-1",
                tool="get_live_telemetry",
                source_domain="live",
                fetched_at=datetime.utcnow(),
                status="OK",
                payload={"measurements": {"motor_temp_c": 115.0}},
                unit_map={},
            )
        ],
    )
    spec = plan_visualization("OP03_FAULT_DIAGNOSIS", pack, format_pack(pack))
    assert "motor-temperature" in spec.card_ids
    assert "vibration" not in spec.card_ids, "Vibration card must be dropped when vibration_g is absent"


def test_ac_5_3_zero_qualifying_cards_is_not_an_error():
    """
    AC-5.3: A run with zero qualifying cards emits empty card_ids list, not an ErrorFrame.
    """
    pack = EvidencePack(
        run_id="R-viz-empty-signals",
        version=1,
        sealed=True,
        items=[
            EvidenceItem(
                evidence_id="EV-unknown",
                tool="get_live_telemetry",
                source_domain="live",
                fetched_at=datetime.utcnow(),
                status="OK",
                payload={"measurements": {"unrelated_signal": 123.4}},
                unit_map={},
            )
        ],
    )
    spec = plan_visualization("OP03_FAULT_DIAGNOSIS", pack, format_pack(pack))
    assert spec.card_ids == []
    assert spec.widget_id == "cards"
