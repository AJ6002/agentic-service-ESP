import pytest
from app.gateway.adapters.common import build_temporal_meta
from app.contracts.evidence import EvidenceItem, EvidencePack
from app.evidence.formatter import format_pack
from app.synthesis.xai import format_evidence_for_prompt

def test_build_temporal_meta_with_dict_records():
    records = [
        {"timestamp": "2026-09-18T19:45:14Z", "value": 1},
        {"timestamp": "2026-09-18T19:46:13Z", "value": 2},
        {"timestamp": "2026-09-18T19:45:30Z", "value": 3},
    ]
    meta = build_temporal_meta(
        query_start="2026-09-18T19:45:13Z",
        query_end="2026-09-18T19:46:13Z",
        records=records,
        ts_field="timestamp"
    )
    assert meta["query_window"]["start"] == "2026-09-18T19:45:13Z"
    assert meta["query_window"]["end"] == "2026-09-18T19:46:13Z"
    assert meta["query_window"]["span_seconds"] == 60.0
    assert meta["data_bounds"]["point_count"] == 3
    assert meta["data_bounds"]["earliest_ts"] == "2026-09-18T19:45:14Z"
    assert meta["data_bounds"]["latest_ts"] == "2026-09-18T19:46:13Z"
    assert "executed_at" in meta

def test_build_temporal_meta_with_list_records():
    columns = ["timestamp", "amp_a", "freq_hz"]
    rows = [
        ["2026-09-18T00:01:00Z", 35.0, 50.0],
        ["2026-09-18T00:05:00Z", 36.0, 50.0],
        ["2026-09-18T00:00:10Z", 34.0, 50.0],
    ]
    meta = build_temporal_meta(
        query_start="2026-09-18T00:00:00Z",
        query_end="2026-09-18T00:10:00Z",
        records=rows,
        columns=columns,
        ts_field="timestamp"
    )
    assert meta["query_window"]["span_seconds"] == 600.0
    assert meta["data_bounds"]["point_count"] == 3
    assert meta["data_bounds"]["earliest_ts"] == "2026-09-18T00:00:10Z"
    assert meta["data_bounds"]["latest_ts"] == "2026-09-18T00:05:00Z"

def test_formatter_and_xai_prompt_render_temporal_audit():
    from datetime import datetime, timezone
    pack = EvidencePack(
        run_id="R-test-temp",
        items=[
            EvidenceItem(
                evidence_id="EV-temp-01",
                tool="get_historian_window",
                source_domain="historian",
                fetched_at=datetime.now(timezone.utc),
                payload={
                    "well_id": "FS-17",
                    "temporal_meta": {
                        "executed_at": "2026-09-19T10:00:00Z",
                        "query_window": {
                            "start": "2026-09-18T19:45:00Z",
                            "end": "2026-09-18T19:46:00Z",
                            "span_seconds": 60.0
                        },
                        "data_bounds": {
                            "earliest_ts": "2026-09-18T19:45:05Z",
                            "latest_ts": "2026-09-18T19:45:55Z",
                            "point_count": 50
                        }
                    }
                }
            )
        ]
    )
    formatted = format_pack(pack)
    assert formatted.temporal.has_data()
    assert formatted.temporal.query_window_start == "2026-09-18T19:45:00Z"
    assert formatted.temporal.query_span_seconds == 60.0

    prompt_text = format_evidence_for_prompt(formatted)
    assert "--- TEMPORAL AUDIT & QUERY TIMESTAMPS ---" in prompt_text
    assert "2026-09-18T19:45:00Z to 2026-09-18T19:46:00Z (60.0s span)" in prompt_text
    assert "From 2026-09-18T19:45:05Z to 2026-09-18T19:45:55Z" in prompt_text
