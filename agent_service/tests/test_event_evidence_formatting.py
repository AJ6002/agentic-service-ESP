from datetime import datetime
from app.contracts.evidence import EvidenceItem, EvidencePack
from app.evidence.formatter import format_pack, FormattedEvidence
from app.synthesis.xai import format_evidence_for_prompt


def test_format_pack_empty_events_window():
    """Verify that event_count == 0 produces a FormattedEventRecord marked is_empty_window."""
    pack = EvidencePack(
        run_id="R-test-ev-0",
        version=1,
        items=[
            EvidenceItem(
                evidence_id="EV-test-ev-01",
                tool="get_events",
                source_domain="events",
                fetched_at=datetime.utcnow(),
                status="OK",
                payload={
                    "well_id": "FNW-01",
                    "start": "2026-09-18T14:00:00Z",
                    "end": "2026-09-18T16:00:00Z",
                    "event_count": 0,
                    "events": [],
                },
                unit_map={},
            )
        ],
    )
    formatted = format_pack(pack)
    assert len(formatted.events) == 1
    ev = formatted.events[0]
    assert ev.evidence_id == "EV-test-ev-01"
    assert ev.is_empty_window is True
    assert ev.window_start == "2026-09-18T14:00:00Z"
    assert ev.window_end == "2026-09-18T16:00:00Z"

    prompt_text = format_evidence_for_prompt(formatted)
    assert "--- OPERATIONAL EVENTS & TRIP RECORDS ---" in prompt_text
    assert "0 events recorded" in prompt_text
    assert "EV-test-ev-01" in prompt_text


def test_format_pack_active_trip_event():
    """Verify that active events are parsed into FormattedEventRecord with trip cause and alarms."""
    pack = EvidencePack(
        run_id="R-test-ev-1",
        version=1,
        items=[
            EvidenceItem(
                evidence_id="EV-test-ev-02",
                tool="get_trips",
                source_domain="events",
                fetched_at=datetime.utcnow(),
                status="OK",
                payload={
                    "event_count": 1,
                    "events": [
                        {
                            "event_id": "EV-20260913-100000-1010",
                            "timestamp": "2026-09-13T10:00:00Z",
                            "well_id": "FNW-01",
                            "operating_state": "tripped",
                            "scenario": "dry_well_pump_off",
                            "trip_cause": "UNDERLOAD_PUMP_OFF",
                            "alarms": ["LOW_INTAKE_PRESSURE", "UNDERLOAD"],
                            "event_type": "trip",
                        }
                    ],
                },
                unit_map={},
            )
        ],
    )
    formatted = format_pack(pack)
    assert len(formatted.events) == 1
    ev = formatted.events[0]
    assert ev.evidence_id == "EV-test-ev-02"
    assert ev.is_empty_window is False
    assert ev.event_id == "EV-20260913-100000-1010"
    assert ev.trip_cause == "UNDERLOAD_PUMP_OFF"
    assert "UNDERLOAD" in ev.alarms

    prompt_text = format_evidence_for_prompt(formatted)
    assert "EV-20260913-100000-1010" in prompt_text
    assert "UNDERLOAD_PUMP_OFF" in prompt_text
    assert "tripped" in prompt_text
