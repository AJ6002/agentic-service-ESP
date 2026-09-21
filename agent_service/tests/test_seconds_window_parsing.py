from datetime import datetime, timezone
import pytest
from app.context.resolver import parse_time_window, parse_query_limit
from app.gateway.tool_gateway import _default_window

def test_parse_time_window_seconds():
    now = datetime(2026, 9, 19, 12, 0, 0, tzinfo=timezone.utc)
    
    # 1. "last 30 seconds"
    tb = parse_time_window("show vibration for FS-17 in the last 30 seconds", now=now)
    assert tb is not None
    assert (tb.window_end - tb.window_start).total_seconds() == 30
    assert tb.label == "last 30 seconds"

    # 2. "past 60 secs"
    tb2 = parse_time_window("motor temp in the past 60 secs", now=now)
    assert tb2 is not None
    assert (tb2.window_end - tb2.window_start).total_seconds() == 60
    assert tb2.label == "last 60 secs"

    # 3. Single unit "last second"
    tb3 = parse_time_window("check spike in the last second", now=now)
    assert tb3 is not None
    assert (tb3.window_end - tb3.window_start).total_seconds() == 1

def test_limit_not_confused_with_seconds():
    msg = "show 10 rows of vibration in the last 30 seconds"
    limit = parse_query_limit(msg)
    assert limit == 10

    tb = parse_time_window(msg)
    assert tb is not None
    assert (tb.window_end - tb.window_start).total_seconds() == 30

def test_default_window_is_two_hours():
    start_iso, end_iso = _default_window()
    t_start = datetime.fromisoformat(start_iso.replace("Z", "+00:00"))
    t_end = datetime.fromisoformat(end_iso.replace("Z", "+00:00"))
    diff_sec = (t_end - t_start).total_seconds()
    # 7200 seconds = 2 hours
    assert diff_sec == 7200
