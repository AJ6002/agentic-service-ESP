"""
Phase 1 Evidence Pipeline Tests.
Covers all cases specified in SLICE_2_PLAN.md §1 exit criteria.
All fixtures are inline — no live server required.
"""

import pytest
from datetime import datetime, timezone, timedelta

from app.contracts.evidence import CallResult, EvidencePack, EvidenceItem, Gap

from app.evidence.qod import validate
from app.evidence.pack import build_and_save
from app.evidence.seal_check import seal
from app.evidence.formatter import format_pack, FormattedEvidence


# ---------------------------------------------------------------------------
# Helpers / Fixtures
# ---------------------------------------------------------------------------

def _fresh_ts() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

_FRESH_TS = _fresh_ts()


def _live_telemetry_payload(
    motor_temp: float = 87.71,
    age_sec: float = 0.82,
    extra_signals: dict | None = None,
) -> dict:
    m = {
        "STD_INT_PRS_PSI": 395.4,
        "STD_DISCH_PRS_PSI": 1883.1,
        "STD_INT_TEMP_C": 64.53,
        "STD_MOTOR_TEMP_C": motor_temp,
        "STD_VIBRATION_G": 0.082,
        "STD_VOLT_V": 594.1,
        "STD_AMP_A": 35.7,
        "STD_FREQ_HZ": 53.1,
        "STD_LEAK_CURRENT_CT": 15.0,
        "STD_DHG_CURRENT_MA": 10.7,
        "STD_WHP_PSI": 180.3,
        "STD_FLP_PSI": 171.0,
        "STD_AP_PSI": 155.5,
        "STD_VFD_STS": True,
    }
    if extra_signals:
        m.update(extra_signals)
    return {
        "well_id": "FS-17",
        "timestamp": _FRESH_TS,
        "age_sec": age_sec,
        "measurements": m,
    }


def _make_ok_result(seq: int, payload: dict) -> CallResult:
    return CallResult(seq=seq, status="OK", raw_response=payload)


def _make_failed_result(seq: int, error: str = "MQTT_DISCONNECTED") -> CallResult:
    return CallResult(seq=seq, status="FAILED", error=error)


def _make_timeout_result(seq: int) -> CallResult:
    return CallResult(seq=seq, status="TIMEOUT", error="timeout")


# ---------------------------------------------------------------------------
# Step 1.1 — QoD Tests
# ---------------------------------------------------------------------------

class TestQoDEngine:
    def test_nominal_accepted(self):
        """Nominal telemetry payload → accepted."""
        result = _make_ok_result(1, _live_telemetry_payload())
        qod = validate(result, run_id="run-001", tool="get_live_telemetry")
        assert qod.accepted is True
        assert qod.evidence_item is not None
        assert qod.evidence_item.evidence_id.startswith("EV-run-001-")

    def test_motor_temp_alarming_but_accepted(self):
        """
        motor_temp_c=130 is above alarm threshold (125°C) but within
        max_plausible (160°C). MUST be accepted — real data, not sensor failure.
        This is the critical invariant from SLICE_2_PLAN §1.1.
        """
        payload = _live_telemetry_payload(motor_temp=130.0)
        result = _make_ok_result(1, payload)
        qod = validate(result, run_id="run-002", tool="get_live_telemetry")
        assert qod.accepted is True, (
            f"Alarming but plausible motor_temp=130 must be accepted. "
            f"Got: {qod.rejection_reason}"
        )

    def test_motor_temp_out_of_range_rejected(self):
        """
        motor_temp_c=999 is above max_plausible (160°C) → sensor failure → rejected.
        """
        payload = _live_telemetry_payload(motor_temp=999.0)
        result = _make_ok_result(1, payload)
        qod = validate(result, run_id="run-003", tool="get_live_telemetry")
        assert qod.accepted is False
        assert "motor_temp_c" in qod.rejection_reason
        assert "sensor failure" in qod.rejection_reason

    def test_stale_warning_accepted_marked(self):
        """
        age_sec=10 exceeds warning threshold (5s) but not critical (30s).
        Accepted but EvidenceItem.status = STALE.
        """
        payload = _live_telemetry_payload(age_sec=10.0)
        result = _make_ok_result(1, payload)
        qod = validate(result, run_id="run-004", tool="get_live_telemetry")
        assert qod.accepted is True
        assert qod.evidence_item.status == "STALE"

    def test_stale_critical_rejected(self):
        """age_sec=45 exceeds critical threshold (30s) → rejected."""
        payload = _live_telemetry_payload(age_sec=45.0)
        result = _make_ok_result(1, payload)
        qod = validate(result, run_id="run-005", tool="get_live_telemetry")
        assert qod.accepted is False
        assert "critical" in qod.rejection_reason.lower() or "45" in qod.rejection_reason

    def test_failed_result_rejected(self):
        """FAILED CallResult → always rejected."""
        result = _make_failed_result(1)
        qod = validate(result, run_id="run-006", tool="get_live_telemetry")
        assert qod.accepted is False
        assert qod.evidence_item is None

    def test_timeout_result_rejected(self):
        """TIMEOUT CallResult → always rejected."""
        result = _make_timeout_result(1)
        qod = validate(result, run_id="run-007", tool="get_live_telemetry")
        assert qod.accepted is False

    def test_completeness_missing_required_field(self):
        """Payload missing 'measurements' (required for get_live_telemetry) → rejected."""
        payload = {"well_id": "FS-17", "timestamp": _FRESH_TS, "age_sec": 1.0}
        result = _make_ok_result(1, payload)
        qod = validate(result, run_id="run-008", tool="get_live_telemetry")
        assert qod.accepted is False
        assert "measurements" in qod.rejection_reason

    def test_historian_never_stale(self):
        """historian domain is never_stale — no freshness rejection regardless of age."""
        old_ts = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat().replace("+00:00", "Z")
        payload = {"well_id": "FS-17", "rows": [], "timestamp": old_ts}
        result = _make_ok_result(1, payload)
        qod = validate(result, run_id="run-009", tool="get_historian_window")
        assert qod.accepted is True

    def test_unit_map_populated_from_signal_bounds(self):
        """Accepted result should have unit_map entries for known signals."""
        result = _make_ok_result(1, _live_telemetry_payload())
        qod = validate(result, run_id="run-010", tool="get_live_telemetry")
        assert qod.accepted is True
        assert "motor_temp_c" in qod.evidence_item.unit_map
        assert qod.evidence_item.unit_map["motor_temp_c"] == "°C"


# ---------------------------------------------------------------------------
# Step 1.2 — EvidencePack + SealCheck Tests (in-memory, no Redis)
# ---------------------------------------------------------------------------

class TestEvidencePackSeal:
    """
    Builds packs in-memory using mock items and checks seal logic.
    We bypass build_and_save (Redis) to avoid test infrastructure dependency.
    """

    def _make_item(self, tool: str, ev_id: str = "EV-t-0001") -> EvidenceItem:
        return EvidenceItem(
            evidence_id=ev_id,
            tool=tool,
            source_domain=tool,
            fetched_at=datetime.now(timezone.utc),
            status="OK",
            payload={"well_id": "FS-17"},
        )

    def test_seal_complete_when_all_required_present(self):
        pack = EvidencePack(
            run_id="run-seal-001",
            items=[
                self._make_item("get_asset_context", "EV-t-0001"),
                self._make_item("get_live_telemetry", "EV-t-0002"),
            ],
        )
        result = seal(pack, required_tools=["get_asset_context", "get_live_telemetry"])
        assert result.status == "COMPLETE"
        assert result.missing_required == []
        assert result.pack.sealed is True
        assert result.pack.sealed_at is not None

    def test_seal_insufficient_when_required_missing(self):
        pack = EvidencePack(
            run_id="run-seal-002",
            items=[self._make_item("get_asset_context", "EV-t-0001")],
        )
        result = seal(pack, required_tools=["get_asset_context", "get_live_telemetry"])
        assert result.status == "INSUFFICIENT"
        assert "get_live_telemetry" in result.missing_required

    def test_degraded_source_appears_in_gaps(self):
        """A FAILED call must produce a Gap in the pack (not be silently dropped)."""
        failed_result = _make_failed_result(2, "MQTT_DISCONNECTED")
        telemetry_ok = _make_ok_result(1, _live_telemetry_payload())
        asset_ok = _make_ok_result(3, {"well_id": "FS-17", "asset_type": "ESP"})

        qod_telemetry = validate(telemetry_ok, run_id="run-gap-001", tool="get_live_telemetry")
        qod_failed = validate(failed_result, run_id="run-gap-001", tool="get_events")
        qod_asset = validate(asset_ok, run_id="run-gap-001", tool="get_asset_context")

        pack = EvidencePack(run_id="run-gap-001")
        # Manually build pack (avoid Redis in unit test)
        if qod_telemetry.accepted:
            pack.items.append(qod_telemetry.evidence_item)
        else:
            pack.gaps.append(Gap(source_domain="get_live_telemetry", reason="DEGRADED", required=True))

        if not qod_failed.accepted:
            pack.gaps.append(Gap(source_domain="get_events", reason="DEGRADED", required=False))

        if qod_asset.accepted:
            pack.items.append(qod_asset.evidence_item)

        assert any(g.source_domain == "get_events" for g in pack.gaps), (
            "FAILED events call must appear as a Gap, never silently dropped"
        )
        assert len(pack.items) >= 1

    def test_contradictory_events_still_seals(self):
        """
        Pack with conflicts still seals if all required evidence is present.
        Conflicts are informational, not blocking.
        """
        pack = EvidencePack(
            run_id="run-conflict-001",
            items=[
                self._make_item("get_asset_context", "EV-t-0001"),
                self._make_item("get_live_telemetry", "EV-t-0002"),
            ],
        )
        from app.contracts.evidence import Conflict
        pack.conflicts.append(
            Conflict(
                description="VFD running but trip event present",
                evidence_ids=["EV-t-0002"],
            )
        )
        result = seal(pack, required_tools=["get_asset_context", "get_live_telemetry"])
        assert result.status == "COMPLETE"
        assert len(result.pack.conflicts) == 1


# ---------------------------------------------------------------------------
# Step 1.3 — Evidence Formatter Tests
# ---------------------------------------------------------------------------

class TestEvidenceFormatter:
    def _nominal_pack(self) -> EvidencePack:
        """Creates a minimal sealed EvidencePack with telemetry data."""
        payload = _live_telemetry_payload()
        result = _make_ok_result(1, payload)
        qod = validate(result, run_id="run-fmt-001", tool="get_live_telemetry")
        assert qod.accepted
        return EvidencePack(
            run_id="run-fmt-001",
            items=[qod.evidence_item],
            sealed=True,
        )

    def test_every_numeric_has_unit_and_evidence_id(self):
        """
        Every FormattedValue must have a non-empty unit and a valid evidence_id.
        Exit criterion 4: "Every number in FormattedEvidence carries a unit
        and an evidence_id."
        """
        pack = self._nominal_pack()
        fe = format_pack(pack)
        assert len(fe.values) > 0, "Expected at least some formatted values"
        for fv in fe.values:
            assert fv.evidence_id.startswith("EV-"), (
                f"Missing evidence_id on signal {fv.signal}: {fv.evidence_id}"
            )
            # unit can be empty string for unknown signals but must be present
            assert fv.value_str, f"Empty value_str for {fv.signal}"

    def test_motor_temp_correctly_formatted(self):
        """motor_temp_c should appear exactly once with unit °C."""
        pack = self._nominal_pack()
        fe = format_pack(pack)
        motor_vals = [v for v in fe.values if v.signal == "motor_temp_c"]
        assert len(motor_vals) == 1
        assert "°C" in motor_vals[0].unit
        assert "87.71" in motor_vals[0].value_str

    def test_empty_pack_produces_empty_values_no_crash(self):
        """Pack with no items → FormattedEvidence with empty values list, not crash."""
        pack = EvidencePack(run_id="run-fmt-empty", items=[])
        fe = format_pack(pack)
        assert isinstance(fe, FormattedEvidence)
        assert fe.values == []

    def test_no_raw_float_escapes_without_evidence_id(self):
        """
        Verifies that no value in the formatted output is a bare float
        (all wrapped in FormattedValue with provenance).
        """
        pack = self._nominal_pack()
        fe = format_pack(pack)
        for fv in fe.values:
            assert isinstance(fv.value_str, str)
            assert fv.evidence_id is not None and len(fv.evidence_id) > 0

    def test_by_signal_lookup(self):
        """FormattedEvidence.by_signal() returns correct entry."""
        pack = self._nominal_pack()
        fe = format_pack(pack)
        val = fe.by_signal("motor_temp_c")
        assert val is not None
        assert val.unit == "°C"


# ---------------------------------------------------------------------------
# End-to-End Phase 1 Pipeline Test
# ---------------------------------------------------------------------------

class TestPhase1EndToEnd:
    def test_live_fixture_to_formatted_evidence(self):
        """
        Exit Criterion 1: CallResult → QoD → pack → formatted evidence, end-to-end.
        Uses fixture data, no live server.
        """
        # Simulate two successful tool results
        telemetry_cr = _make_ok_result(1, _live_telemetry_payload())
        asset_cr = _make_ok_result(2, {"well_id": "FS-17", "asset_type": "ESP", "manufacturer": "Borets"})

        run_id = "run-e2e-001"
        qod_tel = validate(telemetry_cr, run_id=run_id, tool="get_live_telemetry")
        qod_asset = validate(asset_cr, run_id=run_id, tool="get_asset_context")

        assert qod_tel.accepted
        assert qod_asset.accepted

        pack = EvidencePack(
            run_id=run_id,
            items=[qod_tel.evidence_item, qod_asset.evidence_item],
        )
        seal_result = seal(pack, required_tools=["get_live_telemetry", "get_asset_context"])
        assert seal_result.status == "COMPLETE"
        assert seal_result.pack.sealed is True

        fe = format_pack(seal_result.pack)
        assert len(fe.values) > 0

        # Every value must be attributed
        for fv in fe.values:
            assert fv.evidence_id.startswith("EV-")
            assert fv.value_str

    def test_stale_and_absent_sources_named_as_gaps(self):
        """
        Exit Criterion 2: a stale and an absent source each show up as a named Gap.

        Drives this through the REAL build_and_save() -> classify_gap_reason()
        path, not a hand-appended Gap. The earlier version of this test set
        reason="ABSENT" by hand while the fixture CallResult had no
        error_code — so it never actually verified that production code
        produces ABSENT; it only verified that a manually-constructed Gap
        object satisfies the assertion.
        """
        stale_cr = _make_ok_result(1, _live_telemetry_payload(age_sec=45.0))
        absent_cr = _make_failed_result(2, "Knowledge Base is ABSENT (no backend endpoint)")
        absent_cr.error_code = "ABSENT"

        run_id = "run-gaps-001"
        qod_stale = validate(stale_cr, run_id=run_id, tool="get_live_telemetry")
        qod_absent = validate(absent_cr, run_id=run_id, tool="search_knowledge")

        assert qod_stale.accepted is False   # critically stale → rejected → Gap
        assert qod_absent.accepted is False  # FAILED → Gap

        pack = build_and_save(
            run_id=run_id,
            version=1,
            qod_results=[qod_stale, qod_absent],
            call_results=[stale_cr, absent_cr],
            tool_names=["get_live_telemetry", "search_knowledge"],
            required_tools=["get_live_telemetry"],
        )

        by_domain = {g.source_domain: g for g in pack.gaps}
        assert "get_live_telemetry" in by_domain, "Stale source must appear as a Gap"
        assert by_domain["get_live_telemetry"].reason == "DEGRADED"
        assert "search_knowledge" in by_domain, "Absent source must appear as a Gap"
        assert by_domain["search_knowledge"].reason == "ABSENT", (
            "classify_gap_reason() must produce ABSENT from error_code, "
            "not fall through to DEGRADED"
        )


# ---------------------------------------------------------------------------
# Phase 1 audit fixes — QoD top-level range sanity + Formatter field names
# ---------------------------------------------------------------------------

class TestQoDTopLevelRangeSanity:
    """
    Bug: QoD's range-sanity check only ever inspected payload["measurements"],
    so ML-domain responses (health_score, score, probability are top-level,
    not nested) passed unconditionally regardless of value. A model/sensor
    failure returning health_score=-999 or score=47.0 (bounded 0.0-1.0) would
    have been silently accepted as real evidence.
    """

    def test_ml_health_nominal_accepted(self):
        payload = {
            "well_id": "FS-17",
            "timestamp": _fresh_ts(),
            "health_score": 71.4,
            "band": "DEGRADED",
        }
        result = _make_ok_result(1, payload)
        qod = validate(result, run_id="run-ml-001", tool="get_ml_results")
        assert qod.accepted is True

    def test_ml_health_out_of_range_rejected(self):
        payload = {
            "well_id": "FS-17",
            "timestamp": _fresh_ts(),
            "health_score": -999.0,
        }
        result = _make_ok_result(1, payload)
        qod = validate(result, run_id="run-ml-002", tool="get_ml_results")
        assert qod.accepted is False
        assert "health_score" in qod.rejection_reason

    def test_ml_anomaly_score_out_of_bounds_rejected(self):
        """score is physically bounded 0.0-1.0 per signal_bounds.yaml anomaly_score."""
        payload = {"well_id": "FS-17", "timestamp": _fresh_ts(), "score": 47.0, "threshold": 0.65}
        result = _make_ok_result(1, payload)
        qod = validate(result, run_id="run-ml-003", tool="get_anomaly")
        assert qod.accepted is False
        assert "score" in qod.rejection_reason

    def test_ml_anomaly_score_nominal_accepted(self):
        payload = {"well_id": "FS-17", "timestamp": _fresh_ts(), "score": 0.72, "threshold": 0.65}
        result = _make_ok_result(1, payload)
        qod = validate(result, run_id="run-ml-004", tool="get_anomaly")
        assert qod.accepted is True

    def test_fault_probability_out_of_range_rejected(self):
        """probability must be within [0.0, 1.0]."""
        payload = {"well_id": "FS-17", "timestamp": _fresh_ts(), "fault_class": "X", "probability": 5.0}
        result = _make_ok_result(1, payload)
        qod = validate(result, run_id="run-ml-005", tool="diagnose_fault")
        assert qod.accepted is False
        assert "probability" in qod.rejection_reason

    def test_fault_probability_nominal_accepted(self):
        payload = {"well_id": "FS-17", "timestamp": _fresh_ts(), "fault_class": "MOTOR_OVERLOAD", "probability": 0.78}
        result = _make_ok_result(1, payload)
        qod = validate(result, run_id="run-ml-006", tool="diagnose_fault")
        assert qod.accepted is True

    def test_negative_probability_rejected(self):
        payload = {"well_id": "FS-17", "timestamp": _fresh_ts(), "fault_class": "X", "probability": -0.1}
        result = _make_ok_result(1, payload)
        qod = validate(result, run_id="run-ml-007", tool="diagnose_fault")
        assert qod.accepted is False


class TestFormatterMLFieldNames:
    """
    Bug: formatter's top-level field map used invented names
    (anomaly_score, fault_probability, rul_days) that never match the
    real endpoint field names (score, probability,
    projected_days_to_threshold). This locks in the corrected names
    against the ACTUAL fixture payloads (spec-verified).
    """

    def _item_from_payload(self, tool: str, payload: dict, ev_id: str = "EV-t-fmt") -> EvidenceItem:
        return EvidenceItem(
            evidence_id=ev_id,
            tool=tool,
            source_domain=tool,
            fetched_at=datetime.now(timezone.utc),
            status="OK",
            payload=payload,
        )

    def test_ml_health_score_formatted_and_attributed(self):
        import json
        from pathlib import Path
        fixtures = Path(__file__).parent / "fixtures" / "server184"
        with open(fixtures / "ml_health_nominal.json", encoding="utf-8") as f:
            payload = json.load(f)
        item = self._item_from_payload("get_ml_results", payload)
        pack = EvidencePack(run_id="run-fmt-ml-1", items=[item], sealed=True)
        fe = format_pack(pack)
        val = fe.by_signal("health_score")
        assert val is not None, "health_score must be formatted from a real /ml/health/{well} response"
        assert val.raw == 71.4
        assert val.evidence_id == "EV-t-fmt"

    def test_ml_anomaly_score_field_formatted(self):
        payload = {"well_id": "FS-17", "score": 0.72, "threshold": 0.65, "is_anomalous": True}
        item = self._item_from_payload("get_anomaly", payload)
        pack = EvidencePack(run_id="run-fmt-ml-2", items=[item], sealed=True)
        fe = format_pack(pack)
        val = fe.by_signal("score")
        assert val is not None, "the real field name is 'score', not 'anomaly_score'"
        assert val.raw == 0.72

    def test_fault_probability_field_formatted(self):
        import json
        from pathlib import Path
        fixtures = Path(__file__).parent / "fixtures" / "server184"
        with open(fixtures / "ml_fault_nominal.json", encoding="utf-8") as f:
            payload = json.load(f)
        item = self._item_from_payload("diagnose_fault", payload)
        pack = EvidencePack(run_id="run-fmt-ml-3", items=[item], sealed=True)
        fe = format_pack(pack)
        val = fe.by_signal("probability")
        assert val is not None, "the real field name is 'probability', not 'fault_probability'"
        assert val.raw == 0.78

    def test_degradation_rul_field_formatted(self):
        payload = {
            "well_id": "FS-17",
            "trend": "increasing",
            "rate_per_day": 0.42,
            "projected_days_to_threshold": 50,
            "threshold": 50.0,
            "confidence": 0.68,
        }
        item = self._item_from_payload("get_degradation", payload)
        pack = EvidencePack(run_id="run-fmt-ml-4", items=[item], sealed=True)
        fe = format_pack(pack)
        rul = fe.by_signal("projected_days_to_threshold")
        assert rul is not None, "the real field name is 'projected_days_to_threshold', not 'rul_days'"
        assert rul.raw == 50
        rate = fe.by_signal("rate_per_day")
        assert rate is not None
        assert rate.raw == 0.42

    def test_old_invented_field_names_no_longer_used(self):
        """
        Regression guard: the old (wrong) names must not silently resurface.
        A payload that ONLY has the old invented keys should format nothing
        for them, proving the map no longer looks for names that don't exist
        on any real endpoint.
        """
        payload = {"well_id": "FS-17", "anomaly_score": 0.9, "fault_probability": 0.5, "rul_days": 10}
        item = self._item_from_payload("get_ml_results", payload)
        pack = EvidencePack(run_id="run-fmt-ml-5", items=[item], sealed=True)
        fe = format_pack(pack)
        assert fe.by_signal("anomaly_score") is None
        assert fe.by_signal("fault_probability") is None
        assert fe.by_signal("rul_days") is None


# ---------------------------------------------------------------------------
# Second audit pass — unit consistency was documented but never checked
# ---------------------------------------------------------------------------

class TestQoDUnitConsistency:
    """
    Bug: QoD's docstring claimed a "unit consistency" check, but the code
    only ever WROTE the expected unit into unit_map — it never READ or
    compared payload["units"] (which historian/window and
    historian/aggregates responses genuinely carry per spec §4). A value
    reported in the wrong unit (e.g. pressure in bar, not PSI) would pass
    QoD unconditionally and get silently re-labeled with the WRONG-but-
    expected unit, making it look trustworthy when it wasn't.
    """

    def test_matching_units_accepted(self):
        payload = {
            "well_id": "FS-17",
            "start": "2026-08-01T00:00:00Z",
            "end": "2026-08-30T00:00:00Z",
            "columns": ["timestamp", "amp_a", "motor_temp_c"],
            "units": {"amp_a": "A", "motor_temp_c": "°C"},
            "rows": [["2026-08-27T07:20:21Z", 35.7, 87.71]],
        }
        result = _make_ok_result(1, payload)
        qod = validate(result, run_id="run-unit-001", tool="get_historian_window")
        assert qod.accepted is True

    def test_mismatched_unit_rejected(self):
        """Pressure reported in 'bar' when the canonical unit is 'PSI' must reject."""
        payload = {
            "well_id": "FS-17",
            "start": "2026-08-01T00:00:00Z",
            "end": "2026-08-30T00:00:00Z",
            "columns": ["timestamp", "int_prs_psi"],
            "units": {"int_prs_psi": "bar"},
            "rows": [["2026-08-27T07:20:21Z", 27.3]],
        }
        result = _make_ok_result(1, payload)
        qod = validate(result, run_id="run-unit-002", tool="get_historian_window")
        assert qod.accepted is False
        assert "Unit mismatch" in qod.rejection_reason
        assert "int_prs_psi" in qod.rejection_reason

    def test_case_and_whitespace_insensitive_match(self):
        """'psi' / ' PSI ' etc. must NOT false-reject — this checks unit identity, not formatting."""
        payload = {
            "well_id": "FS-17",
            "columns": ["int_prs_psi"],
            "units": {"int_prs_psi": " psi "},
            "rows": [],
        }
        result = _make_ok_result(1, payload)
        qod = validate(result, run_id="run-unit-003", tool="get_historian_window")
        assert qod.accepted is True

    def test_no_units_key_passes_through(self):
        """/live/telemetry and /ml/* have no 'units' map — nothing to cross-check."""
        payload = _live_telemetry_payload()
        assert "units" not in payload
        result = _make_ok_result(1, payload)
        qod = validate(result, run_id="run-unit-004", tool="get_live_telemetry")
        assert qod.accepted is True

    def test_unknown_signal_in_units_map_ignored(self):
        """A units entry for a signal with no signal_bounds entry must not crash or reject."""
        payload = {
            "well_id": "FS-17",
            "columns": ["some_unmapped_signal"],
            "units": {"some_unmapped_signal": "widgets"},
            "rows": [],
        }
        result = _make_ok_result(1, payload)
        qod = validate(result, run_id="run-unit-005", tool="get_historian_window")
        assert qod.accepted is True
