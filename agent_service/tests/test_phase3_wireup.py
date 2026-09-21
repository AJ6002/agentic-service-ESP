import json
from datetime import datetime
import pytest
from unittest.mock import AsyncMock, patch
from httpx import ASGITransport, AsyncClient

from app.contracts.advisory import Advisory
from app.contracts.evidence import CallResult, EvidenceItem, EvidencePack, SealResult
from app.contracts.visualization import VisualizationSpec
from app.evidence.formatter import FormattedEvidence, FormattedValue
from app.main import app
from app.stores.run_store import get_run
from app.stores.session_store import delete_pending, delete_session
from app.synthesis.response_assembler import ResponseAssembler
from app.visualization.planner import plan_visualization


def test_cards_planner_full_pack_selects_expected_cards():
    """
    Step 3.1: For OP03_FAULT_DIAGNOSIS, allowed_visuals are:
    fault-classification, health-score, motor-temperature, vibration.
    If all signals exist in FormattedEvidence, all 4 cards must be selected.
    """
    pack = EvidencePack(
        run_id="R-test-1",
        version=1,
        sealed=True,
        items=[
            EvidenceItem(
                evidence_id="EV-test-1-01",
                tool="get_live_telemetry",
                source_domain="live",
                fetched_at=datetime.utcnow(),
                status="OK",
                payload={
                    "int_prs_psi": 850.0,
                    "motor_temp_c": 115.0,
                    "vibration_g": 2.4,
                    "health_score": 85.0,
                    "probability": 0.9,
                },
                unit_map={},
            )
        ],
    )
    formatted = FormattedEvidence(
        run_id=pack.run_id,
        pack_version=pack.version,
        values=[
            FormattedValue(evidence_id="EV-test-1-01", signal="int_prs_psi", value_str="850.0", unit="psi"),
            FormattedValue(evidence_id="EV-test-1-01", signal="motor_temp_c", value_str="115.0", unit="degC"),
            FormattedValue(evidence_id="EV-test-1-01", signal="vibration_g", value_str="2.4", unit="g RMS"),
            FormattedValue(evidence_id="EV-test-1-01", signal="health_score", value_str="85.0", unit="0-100"),
            FormattedValue(evidence_id="EV-test-1-01", signal="probability", value_str="0.9", unit="discrete"),
        ],
    )

    spec = plan_visualization("OP03_FAULT_DIAGNOSIS", pack, formatted)
    assert "fault-classification" in spec.card_ids
    assert "health-score" in spec.card_ids
    assert "motor-temperature" in spec.card_ids
    assert "vibration" in spec.card_ids
    assert len(spec.card_ids) == 4
    # Cited evidence IDs must contain the evidence IDs providing the signals
    assert "EV-test-1-01" in spec.evidence_ids


def test_cards_planner_missing_signal_omits_card():
    """
    Step 3.1: When vib_amp_x_mms is omitted from the pack,
    the vibration card must be dropped, while motor-temperature remains.
    """
    pack = EvidencePack(
        run_id="R-test-2",
        version=1,
        sealed=True,
        items=[
            EvidenceItem(
                evidence_id="EV-test-2-01",
                tool="get_live_telemetry",
                source_domain="live",
                fetched_at=datetime.utcnow(),
                status="OK",
                payload={
                    "int_prs_psi": 850.0,
                    "motor_temp_c": 115.0,
                },
                unit_map={},
            )
        ],
    )
    formatted = FormattedEvidence(
        run_id=pack.run_id,
        pack_version=pack.version,
        values=[
            FormattedValue(evidence_id="EV-test-2-01", signal="int_prs_psi", value_str="850.0", unit="psi"),
            FormattedValue(evidence_id="EV-test-2-01", signal="motor_temp_c", value_str="115.0", unit="degC"),
        ],
    )

    spec = plan_visualization("OP03_FAULT_DIAGNOSIS", pack, formatted)
    assert "motor-temperature" in spec.card_ids
    assert "vibration" not in spec.card_ids


def test_cards_planner_empty_pack_returns_empty_cards():
    """
    Rule C: If none qualify, return no visual rather than a degraded one.
    """
    pack = EvidencePack(
        run_id="R-test-3",
        version=1,
        items=[],
    )
    formatted = FormattedEvidence(run_id=pack.run_id, pack_version=pack.version, values=[])
    spec = plan_visualization("OP03_FAULT_DIAGNOSIS", pack, formatted)
    assert spec.card_ids == []
    assert spec.evidence_ids == []


@pytest.mark.anyio
async def test_response_assembler_emits_advisory_and_visual_frames():
    """
    Step 3.2: Verify assemble_stream yields AdvisoryFrame, VisualFrame, TextDeltaFrame, DoneFrame.
    """
    advisory = Advisory(
        objective_id="OP03_FAULT_DIAGNOSIS",
        assessment="Well is operating under high thermal load.",
        hypotheses=["Gas interference", "Cooling degradation"],
        recommendation="Reduce choke by 5%.",
        verification_steps=["Inspect intake pressure", "Monitor motor temperature"],
        confidence=0.88,
        cited_evidence_ids=["EV-101", "EV-102"],
    )
    viz = VisualizationSpec(
        widget_id="cards",
        card_ids=["motor-temperature", "health-score"],
        evidence_ids=["EV-101"],
    )

    stream = ResponseAssembler.assemble_stream(
        run_id="R-stream-1",
        route="WORKFLOW",
        text="Diagnosis complete.",
        advisory=advisory,
        visualization=viz,
    )

    lines = []
    async for item in stream:
        lines.append(json.loads(item))

    types = [line["type"] for line in lines]
    assert types == ["advisory", "visual", "text_delta", "done"]

    adv_frame = lines[0]
    assert adv_frame["advisory"]["assessment"] == advisory.assessment
    assert adv_frame["source_refs"] == ["EV-101", "EV-102"]

    viz_frame = lines[1]
    assert viz_frame["visualization"]["card_ids"] == ["motor-temperature", "health-score"]

    text_frame = lines[2]
    assert text_frame["delta"] == "Diagnosis complete."

    done_frame = lines[3]
    assert done_frame["status"] == "OK"


@pytest.mark.anyio
async def test_response_assembler_omits_visual_frame_when_card_ids_empty():
    """
    Rule C: If none qualify, no visual frame should be yielded.
    """
    advisory = Advisory(
        objective_id="OP03_FAULT_DIAGNOSIS",
        assessment="Assessment without cards.",
        hypotheses=[],
        recommendation="Check logs.",
        verification_steps=[],
        confidence=0.8,
        cited_evidence_ids=[],
    )
    viz = VisualizationSpec(
        widget_id="cards",
        card_ids=[],
        evidence_ids=[],
    )

    stream = ResponseAssembler.assemble_stream(
        run_id="R-stream-2",
        route="WORKFLOW",
        text="No cards available.",
        advisory=advisory,
        visualization=viz,
    )

    lines = [json.loads(item) async for item in stream]
    types = [line["type"] for line in lines]
    assert "visual" not in types
    assert types == ["advisory", "text_delta", "done"]


@pytest.mark.anyio
async def test_e2e_insufficient_evidence_clarify_flow():
    """
    Step 3.2: When clarify_on_insufficient=True and required evidence is missing,
    handle_query raises CLARIFY via raise_clarify(), pausing the run.
    """
    session_id = "test-phase3-insufficient-1"
    delete_pending(session_id)
    delete_session(session_id)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/query",
            json={
                "session_id": session_id,
                "message": "Diagnose well FS-9999",
                "clarify_on_insufficient": True,
            },
        )
        assert resp.status_code == 200
        lines = [json.loads(line) for line in resp.text.strip().splitlines() if line]

        # In test environment, Server 184 is unreachable -> required evidence missing -> CLARIFY
        assert len(lines) == 2
        assert lines[0]["type"] == "clarification"
        assert lines[0]["slot"] == "missing_evidence"
        assert "could not be completed" in lines[0]["question"]
        assert lines[1]["type"] == "done"
        assert lines[1]["status"] == "PAUSED"

        run_id = lines[0]["run_id"]
        run = get_run(run_id)
        assert run is not None
        assert run.status == "PAUSED"

    delete_pending(session_id)
    delete_session(session_id)


@pytest.mark.anyio
async def test_e2e_complete_evidence_yields_advisory_and_visual_frames():
    """
    End-to-end test with mocked tool gateway and XAI synthesizer producing complete
    evidence and advisory, verifying full NDJSON delivery through /query.
    """
    session_id = "test-phase3-full-stream-1"
    delete_pending(session_id)
    delete_session(session_id)

    mock_advisory = Advisory(
        objective_id="OP03_FAULT_DIAGNOSIS",
        assessment="Motor temperature is elevated above normal operating threshold.",
        hypotheses=["Excessive load on pump stage 3"],
        recommendation="Throttle back frequency by 2 Hz.",
        verification_steps=["Monitor motor_temp_c for 30 minutes"],
        confidence=0.92,
        cited_evidence_ids=["EV-mock-1", "EV-mock-2"],
    )

    async def mock_dispatch(plan):
        res = []
        for call in plan.calls:
            if call.tool == "get_live_telemetry":
                res.append(CallResult(
                    seq=call.seq,
                    status="OK",
                    raw_response={
                        "well_id": "FS-17",
                        "timestamp": 1789659000.0,
                        "age_sec": 4.0,
                        "measurements": {
                            "int_prs_psi": 850.0,
                            "motor_temp_c": 125.0,
                            "vibration_g": 2.1,
                            "active_power_kw": 92.0,
                            "freq_hz": 50.0,
                            "amp_a": 42.0,
                        },
                    },
                ))
            elif call.tool == "get_asset_context":
                res.append(CallResult(
                    seq=call.seq,
                    status="OK",
                    raw_response={
                        "well_id": "FS-17",
                        "nameplate": {"max_temp_c": 135.0, "rated_power_kw": 100.0},
                    },
                ))
            elif call.tool == "get_historian_window":
                res.append(CallResult(
                    seq=call.seq,
                    status="OK",
                    raw_response={
                        "well_id": "FS-17",
                        "row_count": 5,
                        "data": [{"timestamp": 1789658000.0, "int_prs_psi": 852.0}],
                    },
                ))
            elif call.tool == "get_ml_results":
                res.append(CallResult(
                    seq=call.seq,
                    status="OK",
                    raw_response={"well_id": "FS-17", "score": 0.85, "health_score": 78.0},
                ))
            elif call.tool == "diagnose_fault":
                res.append(CallResult(
                    seq=call.seq,
                    status="OK",
                    raw_response={"well_id": "FS-17", "fault_class": "OVERHEAT", "confidence": 0.9, "probability": 0.9},
                ))
            elif call.tool == "search_knowledge":
                res.append(CallResult(
                    seq=call.seq,
                    status="OK",
                    raw_response={"hits": [], "total_found": 0},
                ))
            else:
                res.append(CallResult(seq=call.seq, status="OK", raw_response={"well_id": "FS-17"}))
        return res

    transport = ASGITransport(app=app)
    with patch("app.workflow.runner.dispatch_plan_calls", side_effect=mock_dispatch), \
         patch("app.workflow.runner.synthesize_advisory", AsyncMock(return_value=(mock_advisory, None))):
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post(
                "/query",
                json={
                    "session_id": session_id,
                    "message": "why did FS-017 trip?",
                },
            )
            assert resp.status_code == 200
            lines = [json.loads(line) for line in resp.text.strip().splitlines() if line]

            types = [l["type"] for l in lines]
            assert "advisory" in types
            assert "visual" in types
            assert "text_delta" in types
            assert "done" in types

            # Check advisory frame
            adv_frame = next(l for l in lines if l["type"] == "advisory")
            assert "elevated above normal" in adv_frame["advisory"]["assessment"]

            # Check visual frame has selected cards
            viz_frame = next(l for l in lines if l["type"] == "visual")
            card_ids = viz_frame["visualization"]["card_ids"]
            assert "fault-classification" in card_ids
            assert "motor-temperature" in card_ids
            assert "vibration" in card_ids

            # Check done status
            done_frame = next(l for l in lines if l["type"] == "done")
            assert done_frame["status"] == "OK"

    delete_pending(session_id)
    delete_session(session_id)


# ---------------------------------------------------------------------------
# Self-Verify Checklist Tests (User Demanded Verification)
# ---------------------------------------------------------------------------

def test_op01_full_pack_all_four_cards_selected_with_kpi():
    """
    Checklist 1:
    OP01 full pack with get_current_status (returning kpis dict) + get_live_telemetry.
    All 4 allowed cards (health-score, intake-pressure, gross-liquid-rate, production-deferment)
    must appear in card_ids.
    """
    kpi_payload = {
        "well_id": "FS-17",
        "kpis": {
            "liquid_rate_bpd": 399.1,
            "oil_rate_bopd": 399.1,
            "water_cut_pct": 0.0,
            "gas_rate_mscfd": 119.7,
            "health_score": 88.0,
        },
    }
    telemetry_payload = {
        "well_id": "FS-17",
        "measurements": {
            "int_prs_psi": 520.0,
            "volt_v": 480.0,
            "amp_a": 45.0,
        },
    }
    pack = EvidencePack(
        run_id="R-op01-kpi",
        version=1,
        sealed=True,
        items=[
            EvidenceItem(
                evidence_id="EV-kpi-1",
                tool="get_current_status",
                source_domain="kpi",
                fetched_at=datetime.utcnow(),
                status="OK",
                payload=kpi_payload,
                unit_map={"liquid_rate_bpd": "BPD", "health_score": "index"},
            ),
            EvidenceItem(
                evidence_id="EV-telem-1",
                tool="get_live_telemetry",
                source_domain="live_telemetry",
                fetched_at=datetime.utcnow(),
                status="OK",
                payload=telemetry_payload,
                unit_map={"int_prs_psi": "PSI"},
            ),
        ],
    )
    from app.evidence.formatter import format_pack
    formatted = format_pack(pack)
    signals = {fv.signal for fv in formatted.values}
    assert "liquid_rate_bpd" in signals
    assert "int_prs_psi" in signals
    assert "health_score" in signals

    spec = plan_visualization("OP01_CURRENT_STATUS", pack, formatted)
    assert spec.card_ids == [
        "health-score",
        "intake-pressure",
        "gross-liquid-rate",
        "production-deferment",
    ]
    assert "EV-kpi-1" in spec.evidence_ids
    assert "EV-telem-1" in spec.evidence_ids


def test_missing_signal_motor_temp_dropped_not_crash():
    """
    Checklist 2:
    Strip motor_temp_c from an OP03 pack, confirm motor-temperature vanishes from
    card_ids, nothing else breaks.
    """
    pack = EvidencePack(
        run_id="R-op03-strip",
        version=1,
        sealed=True,
        items=[
            EvidenceItem(
                evidence_id="EV-strip-1",
                tool="get_live_telemetry",
                source_domain="live_telemetry",
                fetched_at=datetime.utcnow(),
                status="OK",
                payload={
                    "well_id": "FS-17",
                    "measurements": {
                        "int_prs_psi": 850.0,
                        # motor_temp_c stripped
                        "vibration_g": 2.4,
                    },
                },
                unit_map={},
            ),
            EvidenceItem(
                evidence_id="EV-strip-2",
                tool="diagnose_fault",
                source_domain="ml",
                fetched_at=datetime.utcnow(),
                status="OK",
                payload={"well_id": "FS-17", "probability": 0.85, "health_score": 75.0},
                unit_map={},
            ),
        ],
    )
    from app.evidence.formatter import format_pack
    formatted = format_pack(pack)
    spec = plan_visualization("OP03_FAULT_DIAGNOSIS", pack, formatted)
    assert "motor-temperature" not in spec.card_ids
    assert "fault-classification" in spec.card_ids
    assert "health-score" in spec.card_ids
    assert "vibration" in spec.card_ids


def test_empty_pack_returns_empty_card_ids_no_exception():
    """
    Checklist 3:
    Objective with an empty pack produces an empty list, not an exception.
    """
    pack = EvidencePack(run_id="R-empty", version=1, items=[])
    from app.evidence.formatter import format_pack
    formatted = format_pack(pack)
    spec = plan_visualization("OP01_CURRENT_STATUS", pack, formatted)
    assert spec.card_ids == []
    assert spec.evidence_ids == []

    spec03 = plan_visualization("OP03_FAULT_DIAGNOSIS", pack, formatted)
    assert spec03.card_ids == []
    assert spec03.evidence_ids == []


def test_fault_classification_resolves_against_real_ml_fault_response():
    """
    Checklist 4:
    fault-classification (required_signals: [probability]) resolves against
    a real /ml/fault (diagnose_fault) response with top-level probability.
    """
    pack = EvidencePack(
        run_id="R-ml-fault",
        version=1,
        sealed=True,
        items=[
            EvidenceItem(
                evidence_id="EV-fault-1",
                tool="diagnose_fault",
                source_domain="ml",
                fetched_at=datetime.utcnow(),
                status="OK",
                payload={
                    "well_id": "FS-17",
                    "fault_class": "GAS_INTERFERENCE",
                    "probability": 0.94,
                    "confidence": 0.94,
                },
                unit_map={"probability": "discrete"},
            )
        ],
    )
    from app.evidence.formatter import format_pack
    formatted = format_pack(pack)
    prob_values = [fv for fv in formatted.values if fv.signal == "probability"]
    assert len(prob_values) == 1
    assert prob_values[0].raw == 0.94

    spec = plan_visualization("OP03_FAULT_DIAGNOSIS", pack, formatted)
    assert "fault-classification" in spec.card_ids
    assert "EV-fault-1" in spec.evidence_ids


def test_cards_with_empty_required_signals_require_pack_items():
    """
    Checklist 5:
    fleet-health / system-ingestion (empty required_signals) — confirm they only
    appear when pack.items is non-empty, not unconditionally.
    """
    from app.contracts.objective_manifest import ObjectiveManifest
    from app.routing.objective_registry import _OBJECTIVES
    from app.evidence.formatter import format_pack

    mock_manifest = ObjectiveManifest(
        objective_id="OP_TEST_FLEET",
        tool="get_fleet_status",
        safety_class="READ",
        scope="FLEET",
        allowed_visuals=["fleet-health", "system-ingestion"],
    )
    _OBJECTIVES["OP_TEST_FLEET"] = mock_manifest

    # When pack.items is empty -> neither card appears
    empty_pack = EvidencePack(run_id="R-fleet-empty", version=1, items=[])
    spec_empty = plan_visualization("OP_TEST_FLEET", empty_pack, format_pack(empty_pack))
    assert spec_empty.card_ids == []

    # When pack.items is non-empty -> both qualify
    non_empty_pack = EvidencePack(
        run_id="R-fleet-full",
        version=1,
        sealed=True,
        items=[
            EvidenceItem(
                evidence_id="EV-fleet-1",
                tool="get_fleet_summary",
                source_domain="fleet",
                fetched_at=datetime.utcnow(),
                status="OK",
                payload={"well_count": 42},
                unit_map={},
            )
        ],
    )
    spec_full = plan_visualization("OP_TEST_FLEET", non_empty_pack, format_pack(non_empty_pack))
    assert spec_full.card_ids == ["fleet-health", "system-ingestion"]


def test_energy_balance_requires_volt_and_amp_no_double_counting():
    """
    Checklist 6:
    energy-balance needs volt_v + amp_a from get_live_telemetry.
    Verify:
    - Only volt_v: card dropped.
    - Only amp_a: card dropped.
    - Both volt_v and amp_a: card selected exactly once without double counting.
    """
    from app.contracts.objective_manifest import ObjectiveManifest
    from app.routing.objective_registry import _OBJECTIVES
    from app.evidence.formatter import format_pack

    mock_manifest = ObjectiveManifest(
        objective_id="OP_TEST_ENERGY",
        tool="get_live_telemetry",
        safety_class="READ",
        scope="ASSET",
        allowed_visuals=["energy-balance"],
    )
    _OBJECTIVES["OP_TEST_ENERGY"] = mock_manifest

    # 1. Only volt_v
    pack_v = EvidencePack(
        run_id="R-energy-v",
        version=1,
        items=[
            EvidenceItem(
                evidence_id="EV-v-1",
                tool="get_live_telemetry",
                source_domain="live_telemetry",
                fetched_at=datetime.utcnow(),
                status="OK",
                payload={"measurements": {"volt_v": 480.0}},
                unit_map={},
            )
        ],
    )
    assert plan_visualization("OP_TEST_ENERGY", pack_v, format_pack(pack_v)).card_ids == []

    # 2. Only amp_a
    pack_a = EvidencePack(
        run_id="R-energy-a",
        version=1,
        items=[
            EvidenceItem(
                evidence_id="EV-a-1",
                tool="get_live_telemetry",
                source_domain="live_telemetry",
                fetched_at=datetime.utcnow(),
                status="OK",
                payload={"measurements": {"amp_a": 42.0}},
                unit_map={},
            )
        ],
    )
    assert plan_visualization("OP_TEST_ENERGY", pack_a, format_pack(pack_a)).card_ids == []

    # 3. Both volt_v and amp_a + kpis present in another item
    pack_both = EvidencePack(
        run_id="R-energy-both",
        version=1,
        sealed=True,
        items=[
            EvidenceItem(
                evidence_id="EV-both-1",
                tool="get_live_telemetry",
                source_domain="live_telemetry",
                fetched_at=datetime.utcnow(),
                status="OK",
                payload={"measurements": {"volt_v": 480.0, "amp_a": 42.0}},
                unit_map={},
            ),
            EvidenceItem(
                evidence_id="EV-both-2",
                tool="get_current_status",
                source_domain="kpi",
                fetched_at=datetime.utcnow(),
                status="OK",
                payload={"kpis": {"liquid_rate_bpd": 399.1}},
                unit_map={},
            ),
        ],
    )
    spec_both = plan_visualization("OP_TEST_ENERGY", pack_both, format_pack(pack_both))
    assert spec_both.card_ids == ["energy-balance"]
    assert spec_both.card_ids.count("energy-balance") == 1


def test_qod_validates_and_extracts_kpis():
    """
    Verify validate() applies range sanity to kpis and populates unit_map.
    """
    from app.contracts.evidence import CallResult
    from app.evidence.qod import validate

    # Valid KPI response
    cr = CallResult(
        seq=1,
        status="OK",
        raw_response={
            "well_id": "FS-17",
            "kpis": {
                "liquid_rate_bpd": 450.0,
                "oil_rate_bopd": 380.0,
                "water_cut_pct": 15.0,
                "gas_rate_mscfd": 120.0,
                "health_score": 88.0,
            },
        },
    )
    res = validate(cr, run_id="R-qod-kpi", tool="get_current_status")
    assert res.accepted is True
    assert res.evidence_item is not None
    assert res.evidence_item.unit_map.get("liquid_rate_bpd") == "BPD"
    assert res.evidence_item.unit_map.get("oil_rate_bopd") == "BOPD"
    assert res.evidence_item.unit_map.get("water_cut_pct") == "%"
    assert res.evidence_item.unit_map.get("health_score") == "index"

    # Out of range KPI response
    cr_bad = CallResult(
        seq=2,
        status="OK",
        raw_response={
            "well_id": "FS-17",
            "kpis": {
                "liquid_rate_bpd": 99999.0,  # Max plausible is 5000.0
            },
        },
    )
    res_bad = validate(cr_bad, run_id="R-qod-kpi-bad", tool="get_current_status")
    assert res_bad.accepted is False
    assert "Range:" in res_bad.rejection_reason and "above max_plausible" in res_bad.rejection_reason


@pytest.mark.anyio
async def test_e2e_turn2_resume_partial_evidence_flow():
    """
    Turn-2 E2E resumption:
    Turn 1 pauses with INSUFFICIENT evidence clarification.
    Turn 2 user responds "Proceed with partial evidence".
    Verify:
    - asset_id is preserved as "FS-17" (not clobbered by prompt string)
    - allow_partial is passed to runner
    - full NDJSON stream completes with status "OK"
    """
    session_id = "test-phase3-turn2-resume"
    delete_pending(session_id)
    delete_session(session_id)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Turn 1: request diagnosis with clarify_on_insufficient=True
        resp1 = await client.post(
            "/query",
            json={
                "session_id": session_id,
                "message": "Diagnose well FS-9999",
                "clarify_on_insufficient": True,
            },
        )
        assert resp1.status_code == 200
        lines1 = [json.loads(l) for l in resp1.text.strip().splitlines() if l]
        assert lines1[0]["type"] == "clarification"
        assert lines1[1]["type"] == "done"
        assert lines1[1]["status"] == "PAUSED"
        paused_run_id = lines1[0]["run_id"]

        # Turn 2: resume with "Proceed with partial evidence"
        resp2 = await client.post(
            "/query",
            json={
                "session_id": session_id,
                "message": "Proceed with partial evidence",
            },
        )
        assert resp2.status_code == 200
        lines2 = [json.loads(l) for l in resp2.text.strip().splitlines() if l]
        types2 = [l["type"] for l in lines2]

        # Resumed execution must not pause again; it should emit text_delta and done OK
        assert "text_delta" in types2
        assert "done" in types2
        done_frame = next(l for l in lines2 if l["type"] == "done")
        assert done_frame["status"] == "OK"

        # Verify run state and asset_id
        resumed_run = get_run(paused_run_id)
        assert resumed_run is not None
        assert resumed_run.status == "DONE"
        assert resumed_run.args.get("asset_id") == "FS-9999"
        assert resumed_run.args.get("allow_partial") is True

    delete_pending(session_id)
    delete_session(session_id)

def test_cards_planner_unsealed_pack_returns_empty_cards():
    """
    Bug D: When pack.sealed is False (unsealed/insufficient),
    plan_visualization MUST return an empty list of card_ids even if signals are present.
    """
    pack = EvidencePack(
        run_id="R-unsealed-1",
        version=1,
        sealed=False,
        items=[
            EvidenceItem(
                evidence_id="EV-unsealed-1",
                tool="get_live_telemetry",
                source_domain="live",
                fetched_at=datetime.utcnow(),
                status="OK",
                payload={"int_prs_psi": 850.0, "motor_temp_c": 115.0, "vibration_g": 2.4},
                unit_map={},
            )
        ],
    )
    formatted = FormattedEvidence(
        run_id=pack.run_id,
        pack_version=pack.version,
        values=[
            FormattedValue(evidence_id="EV-unsealed-1", signal="int_prs_psi", value_str="850.0", unit="psi"),
            FormattedValue(evidence_id="EV-unsealed-1", signal="vibration_g", value_str="2.4", unit="g RMS"),
        ],
    )
    spec = plan_visualization("OP03_FAULT_DIAGNOSIS", pack, formatted)
    assert spec.card_ids == []
    assert spec.evidence_ids == []


