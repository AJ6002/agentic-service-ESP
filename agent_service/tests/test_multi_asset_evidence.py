"""
Tests for Sprint 4 — Multi-Asset Evidence Representation.
Validates:
1. EvidenceItem.asset_id optional field (single-well vs fleet)
2. QoD validation & sealing for multi-well payloads without rejecting on missing asset_id
3. FormattedEvidence.by_well_and_signal() with unpadded/padded ID variant resolution
4. FormattedEvidence.all_by_signal() and events_by_well()
5. End-to-end integration with fleet tools (fetch_fleet_kpi, fetch_fleet_health, fetch_fleet_events)
"""

import pytest
from datetime import datetime, timezone

from app.contracts.evidence import EvidenceItem, EvidencePack, CallResult
from app.evidence.qod import validate
from app.evidence.seal_check import seal
from app.evidence.formatter import format_pack, FormattedValue, FormattedEventRecord
from app.gateway.adapters.kpi import fetch_fleet_kpi, fetch_fleet_health
from app.gateway.adapters.events import fetch_fleet_events


def test_evidence_item_asset_id_optional():
    """Single-asset items carry asset_id; fleet items have asset_id=None."""
    item_single = EvidenceItem(
        evidence_id="EV-TEST-0001",
        tool="get_kpi",
        source_domain="kpi",
        asset_id="FS-17",
        fetched_at=datetime.now(timezone.utc),
        payload={"well_id": "FS-17", "gross_liquid_rate_bpd": 850.0},
    )
    assert item_single.asset_id == "FS-17"
    assert item_single.payload["well_id"] == "FS-17"

    item_fleet = EvidenceItem(
        evidence_id="EV-TEST-0002",
        tool="get_fleet_kpi",
        source_domain="kpi",
        fetched_at=datetime.now(timezone.utc),
        payload={"total_production_bpd": 9200.0, "running_wells": 12},
    )
    assert item_fleet.asset_id is None
    assert "well_id" not in item_fleet.payload


def test_qod_validates_multi_well_payloads():
    """QoD validates both single-asset and fleet tool responses without error."""
    # 1. Single asset call
    res_single = CallResult(
        seq=1,
        status="OK",
        raw_response={"well_id": "FS-17", "health_score": 88.5, "band": "GOOD"},
    )
    qod_single = validate(res_single, run_id="run-1", tool="get_current_status")
    assert qod_single.accepted is True
    assert qod_single.evidence_item is not None
    assert qod_single.evidence_item.asset_id == "FS-17"

    # 2. Fleet KPI call
    res_fleet = CallResult(
        seq=2,
        status="OK",
        raw_response={
            "total_production_bpd": 11500.0,
            "fleet_health_score": 78.4,
            "total_wells": 13,
            "running_wells": 12,
            "down_wells": 1,
        },
    )
    qod_fleet = validate(res_fleet, run_id="run-1", tool="get_fleet_kpi")
    assert qod_fleet.accepted is True
    assert qod_fleet.evidence_item is not None
    assert qod_fleet.evidence_item.asset_id is None
    assert qod_fleet.evidence_item.payload["total_production_bpd"] == 11500.0


def test_formatter_by_signal_and_by_well_and_signal():
    """FormattedEvidence supports both global by_signal and per-well by_well_and_signal with ID resolution."""
    pack = EvidencePack(run_id="run-multi-1", version=1)

    # Add single-well item (FS-17)
    pack.items.append(
        EvidenceItem(
            evidence_id="EV-0001",
            tool="get_current_status",
            source_domain="kpi",
            asset_id="FS-17",
            fetched_at=datetime.now(timezone.utc),
            payload={
                "well_id": "FS-17",
                "health_score": 42.0,
                "band": "CRITICAL",
                "measurements": {"freq_hz": 45.0, "motor_temp_c": 112.5},
            },
        )
    )

    # Add multi-well fleet health item
    pack.items.append(
        EvidenceItem(
            evidence_id="EV-0002",
            tool="get_fleet_health",
            source_domain="ml",
            asset_id=None,
            fetched_at=datetime.now(timezone.utc),
            payload={
                "fleet_health_score": 75.0,
                "count": 3,
                "wells": [
                    {"well_id": "FS-17", "health_score": 42.0, "band": "CRITICAL"},
                    {"well_id": "FNW-01", "health_score": 68.0, "band": "DEGRADED"},
                    {"well_id": "FS-21", "health_score": 95.0, "band": "OPTIMAL"},
                ],
            },
        )
    )

    fmt = format_pack(pack)

    # Global signal lookup
    fleet_health = fmt.by_signal("fleet_health_score")
    assert fleet_health is not None
    assert fleet_health.raw == 75.0
    assert "75.0" in fleet_health.value_str

    # Per-well lookup: unpadded exact match
    fs17_score = fmt.by_well_and_signal("FS-17", "health_score")
    assert fs17_score is not None
    assert fs17_score.raw == 42.0
    assert fs17_score.well_id == "FS-17"

    # Per-well lookup: padded variant match (query FS-017 matches FS-17)
    fs017_score = fmt.by_well_and_signal("FS-017", "health_score")
    assert fs017_score is not None
    assert fs017_score.raw == 42.0

    # Per-well lookup: other wells in multi-well array
    fnw_score = fmt.by_well_and_signal("FNW-01", "health_score")
    assert fnw_score is not None
    assert fnw_score.raw == 68.0

    fs21_band = fmt.by_well_and_signal("FS-21", "health_band")
    assert fs21_band is not None
    assert fs21_band.raw == "OPTIMAL"

    # All by signal
    all_health = fmt.all_by_signal("health_score")
    # From EV-0001 (1) + EV-0002 (3) = 4 entries
    assert len(all_health) == 4


def test_formatter_events_by_well():
    """FormattedEvidence.events_by_well correctly filters fleet event streams."""
    pack = EvidencePack(run_id="run-multi-2", version=1)

    pack.items.append(
        EvidenceItem(
            evidence_id="EV-0003",
            tool="get_fleet_events",
            source_domain="events",
            asset_id=None,
            fetched_at=datetime.now(timezone.utc),
            payload={
                "events": [
                    {"well_id": "FS-16", "event_id": "EVT-1", "event_type": "TRIP", "trip_cause": "OVERLOAD"},
                    {"well_id": "FS-17", "event_id": "EVT-2", "event_type": "ALARM", "trip_cause": None},
                    {"well_id": "FS-16", "event_id": "EVT-3", "event_type": "STARTUP", "trip_cause": None},
                ],
                "event_count": 3,
            },
        )
    )

    fmt = format_pack(pack)

    # Filter for FS-16
    fs16_events = fmt.events_by_well("FS-16")
    assert len(fs16_events) == 2
    assert fs16_events[0].event_id == "EVT-1"
    assert fs16_events[1].event_id == "EVT-3"

    # Filter for FS-16 using padded variant FS-016
    fs016_events = fmt.events_by_well("FS-016")
    assert len(fs016_events) == 2

    # Filter for FS-17
    fs17_events = fmt.events_by_well("FS-17")
    assert len(fs17_events) == 1
    assert fs17_events[0].event_id == "EVT-2"


@pytest.mark.anyio
async def test_end_to_end_fleet_pack_and_formatting():
    """Real database integration: fetch fleet endpoints, validate via QoD, seal into pack, format and query."""
    # 1. Fetch real fleet data from PostgreSQL adapters
    kpi_raw = await fetch_fleet_kpi()
    health_raw = await fetch_fleet_health()
    events_raw = await fetch_fleet_events()

    # 2. QoD validation
    res_kpi = CallResult(seq=1, status="OK", raw_response=kpi_raw)
    res_health = CallResult(seq=2, status="OK", raw_response=health_raw)
    res_events = CallResult(seq=3, status="OK", raw_response=events_raw)

    qod_kpi = validate(res_kpi, run_id="live-run-1", tool="get_fleet_kpi")
    qod_health = validate(res_health, run_id="live-run-1", tool="get_fleet_health")
    qod_events = validate(res_events, run_id="live-run-1", tool="get_fleet_events")

    assert qod_kpi.accepted is True
    assert qod_health.accepted is True
    assert qod_events.accepted is True

    # 3. Seal into EvidencePack
    items = [qod_kpi.evidence_item, qod_health.evidence_item, qod_events.evidence_item]
    pack = EvidencePack(run_id="live-run-1", version=1, items=items)
    seal_res = seal(pack, required_tools=["get_fleet_kpi", "get_fleet_health", "get_fleet_events"])

    assert seal_res.status == "COMPLETE"
    assert seal_res.pack.sealed is True

    # 4. Format pack
    fmt = format_pack(seal_res.pack)

    # Check top-level fleet aggregates
    tot_prod = fmt.by_signal("total_production_bpd")
    assert tot_prod is not None
    assert tot_prod.raw > 0

    fleet_h = fmt.by_signal("fleet_health_score")
    assert fleet_h is not None
    assert 0.0 <= fleet_h.raw <= 100.0

    # Check per-well retrieval for a well in the fleet
    assert len(health_raw.get("wells", [])) > 0
    first_well = health_raw["wells"][0]["well_id"]
    well_h = fmt.by_well_and_signal(first_well, "health_score")
    assert well_h is not None
    assert well_h.raw == health_raw["wells"][0]["health_score"]
