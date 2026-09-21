from datetime import datetime
import pytest

from app.contracts.api import UIContext
from app.contracts.context import SessionSnapshot
from app.contracts.hitl import PendingInterrupt
from app.context.resolver import resolve_asset, resolve_context, classify_resolution, match_alias
from app.stores.session_store import save_pending, delete_pending, save_session

def test_asset_priority_explicit_beats_ui():
    ui = UIContext(selected_asset="FNW-01")
    frame = resolve_context(
        session_id="s-priority-1",
        message="Check current readings for FS-091",
        ui_context=ui,
    )
    assert frame.asset.id == "FS-91"
    assert frame.asset.source == "EXPLICIT"

def test_ui_asset_used_when_no_explicit():
    ui = UIContext(selected_asset="FNW-01")
    frame = resolve_context(
        session_id="s-priority-2",
        message="What is the operating status?",
        ui_context=ui,
    )
    assert frame.asset.id == "FNW-01"
    assert frame.asset.source == "UI"

def test_unresolved_asset_does_not_block_router():
    frame = resolve_context(
        session_id="s-priority-3",
        message="Why did it trip?",
        ui_context=None,
    )
    assert frame.asset.id is None
    assert frame.asset.source == "UNRESOLVED"
    # Crucial rule: needs_clarify must be False so Router runs!
    assert frame.needs_clarify is False

def test_empty_message_sets_needs_clarify():
    frame = resolve_context(
        session_id="s-priority-4",
        message="   ",
    )
    assert frame.needs_clarify is True
    # clarify_reason is the shared InterruptType enum, not a free-text
    # reason code — "why" it's needed (empty message) lives in the
    # clarification question text, not in this field.
    assert frame.clarify_reason == "CLARIFY"

def test_pending_resolution_bind():
    sid = "s-pending-bind"
    pending = PendingInterrupt(
        run_id="R-bind-1",
        reason="CLARIFY",
        resume_at="PLAN_BUILD",
        slot="asset_id",
        options=["FS-17", "FNW-01"],
        raised_at=datetime.utcnow(),
    )
    save_pending(sid, pending)

    frame = resolve_context(session_id=sid, message="FS-17")
    assert frame.resolution == "BIND"
    assert frame.asset.id == "FS-17"
    assert frame.asset.source == "RESOLVED"

    delete_pending(sid)

def test_pending_resolution_supersede():
    sid = "s-pending-super"
    pending = PendingInterrupt(
        run_id="R-super-1",
        reason="CLARIFY",
        resume_at="PLAN_BUILD",
        slot="asset_id",
        options=["FS-017", "FNW-01"],
        raised_at=datetime.utcnow(),
    )
    save_pending(sid, pending)

    frame = resolve_context(session_id=sid, message="What does TDH mean?")
    assert frame.resolution == "SUPERSEDE"

    delete_pending(sid)

def test_pending_resolution_meta():
    sid = "s-pending-meta"
    pending = PendingInterrupt(
        run_id="R-meta-1",
        reason="CLARIFY",
        resume_at="PLAN_BUILD",
        slot="asset_id",
        options=["FS-017", "FNW-01"],
        raised_at=datetime.utcnow(),
    )
    save_pending(sid, pending)

    frame = resolve_context(session_id=sid, message="Why are you asking?")
    assert frame.resolution == "META"

    delete_pending(sid)


# ---------------------------------------------------------------------------
# Alias / nickname resolution (config/asset_aliases.yaml) — was a gap,
# now covered: layman terms must resolve deterministically, not just
# exact well IDs.
# ---------------------------------------------------------------------------

def test_alias_lookup_resolves_layman_term():
    hit = match_alias("what's wrong with the flowstation right now?")
    assert hit == "FS-17"

def test_alias_lookup_no_match_returns_none():
    assert match_alias("what is a best efficiency point?") is None

def test_resolve_context_uses_alias_for_layman_term():
    frame = resolve_context(
        session_id="s-alias-1",
        message="why did the flowstation trip?",
    )
    assert frame.asset.id == "FS-17"
    assert frame.asset.source == "EXPLICIT"
    assert frame.asset.match_method == "ALIAS"
    assert frame.asset.confidence == 0.8

def test_alias_beats_ui_but_not_exact_id():
    # Exact well-id mention still wins over an alias match elsewhere in
    # the same message (EXACT_ID is checked before ALIAS).
    frame = resolve_context(
        session_id="s-alias-2",
        message="FS-091 status, not the flowstation",
    )
    assert frame.asset.id == "FS-91"
    assert frame.asset.match_method == "EXACT_ID"


# ---------------------------------------------------------------------------
# Pronoun -> session resolution — was dead code (parameters accepted but
# never used); now wired up and covered.
# ---------------------------------------------------------------------------

def test_pronoun_resolves_against_session_last_asset():
    sid = "s-pronoun-1"
    save_session(sid, SessionSnapshot(last_objective="OP03_FAULT_DIAGNOSIS", last_asset_id="FS-17", turn_count=1))

    frame = resolve_context(session_id=sid, message="why did it trip?")
    assert frame.asset.id == "FS-17"
    assert frame.asset.source == "SESSION"
    assert frame.asset.match_method == "PRONOUN"

def test_pronoun_with_no_session_asset_stays_unresolved():
    frame = resolve_context(session_id="s-pronoun-2", message="why did it trip?")
    assert frame.asset.id is None
    assert frame.asset.source == "UNRESOLVED"
    # Still must not block the Router (§5.1) even via this path.
    assert frame.needs_clarify is False

def test_explicit_mention_beats_session_pronoun():
    sid = "s-pronoun-3"
    save_session(sid, SessionSnapshot(last_objective="OP03_FAULT_DIAGNOSIS", last_asset_id="FNW-01", turn_count=1))

    frame = resolve_context(session_id=sid, message="why did FS-091 trip?")
    assert frame.asset.id == "FS-91"
    assert frame.asset.source == "EXPLICIT"


# ---------------------------------------------------------------------------
# Slot-match shape check — was a bug: any well-id mention anywhere in the
# reply text was treated as a direct BIND answer, even when the message
# was actually a fresh, unrelated question that happened to name a
# DIFFERENT asset. That silently ran the wrong diagnosis instead of
# answering what was actually asked.
# ---------------------------------------------------------------------------

def test_short_asset_reply_still_binds():
    sid = "s-shape-1"
    pending = PendingInterrupt(
        run_id="R-shape-1",
        reason="CLARIFY",
        resume_at="PLAN_BUILD",
        slot="asset_id",
        options=["FS-17", "FS-91"],
        raised_at=datetime.utcnow(),
    )
    save_pending(sid, pending)

    # A real, short answer to "which well?" must still BIND.
    resolution, bound = classify_resolution("FS-17", pending)
    assert resolution == "BIND"
    assert bound == "FS-17"

    resolution2, bound2 = classify_resolution("it's FS-17", pending)
    assert resolution2 == "BIND"
    assert bound2 == "FS-17"

    delete_pending(sid)

def test_unrelated_question_mentioning_different_asset_supersedes_not_binds():
    sid = "s-shape-2"
    pending = PendingInterrupt(
        run_id="R-shape-2",
        reason="CLARIFY",
        resume_at="PLAN_BUILD",
        slot="asset_id",
        options=["FS-17", "FS-91"],
        raised_at=datetime.utcnow(),
    )
    save_pending(sid, pending)

    # This is a NEW question ("what's the pressure at FS-091?"), not an
    # answer to "which well tripped?" — even though it names an asset
    # that happens to be one of the offered options. Must SUPERSEDE, not
    # silently BIND onto the wrong objective.
    resolution, bound = classify_resolution("what's the pressure at FS-091?", pending)
    assert resolution == "SUPERSEDE"
    assert bound is None

    delete_pending(sid)

def test_unrelated_question_with_no_asset_mention_supersedes():
    sid = "s-shape-3"
    pending = PendingInterrupt(
        run_id="R-shape-3",
        reason="CLARIFY",
        resume_at="PLAN_BUILD",
        slot="asset_id",
        options=["FS-17", "FS-91"],
        raised_at=datetime.utcnow(),
    )
    save_pending(sid, pending)

    resolution, bound = classify_resolution("what does gas lock mean?", pending)
    assert resolution == "SUPERSEDE"
    assert bound is None

    delete_pending(sid)

def test_long_message_with_asset_id_does_not_auto_bind():
    sid = "s-shape-4"
    pending = PendingInterrupt(
        run_id="R-shape-4",
        reason="CLARIFY",
        resume_at="PLAN_BUILD",
        slot="asset_id",
        options=["FS-17", "FS-91"],
        raised_at=datetime.utcnow(),
    )
    save_pending(sid, pending)

    # Long, sentence-shaped message naming an asset but with no question
    # marker — still should not silently bind past the word-count guard.
    resolution, bound = classify_resolution(
        "actually can you check the historian trend for FS-091 over the last week instead",
        pending,
    )
    assert resolution == "SUPERSEDE"

    delete_pending(sid)


# ---------------------------------------------------------------------------
# Time-window parsing (Slice 2) — deterministic, no network/LLM
# ---------------------------------------------------------------------------
from datetime import datetime, timezone
from app.context.resolver import parse_time_window


_FIXED_NOW = datetime(2026, 9, 16, 12, 0, 0, tzinfo=timezone.utc)


def test_parse_time_window_last_n_minutes():
    tb = parse_time_window("what was the status of FS-17 in the last 30 mins?", now=_FIXED_NOW)
    assert tb is not None
    assert tb.source == "EXPLICIT"
    assert tb.window_end == _FIXED_NOW
    assert (tb.window_end - tb.window_start).total_seconds() == 30 * 60
    assert tb.label == "last 30 mins"


def test_parse_time_window_past_hours():
    tb = parse_time_window("show trips for FS-17 over the past 2 hours", now=_FIXED_NOW)
    assert tb is not None
    assert (tb.window_end - tb.window_start).total_seconds() == 2 * 3600


def test_parse_time_window_single_unit_implicit_one():
    tb = parse_time_window("events in the last hour", now=_FIXED_NOW)
    assert tb is not None
    assert (tb.window_end - tb.window_start).total_seconds() == 3600
    assert tb.label == "last hour"


def test_parse_time_window_days():
    tb = parse_time_window("historian for FS-17 last 7 days", now=_FIXED_NOW)
    assert tb is not None
    assert (tb.window_end - tb.window_start).total_seconds() == 7 * 86400


def test_parse_time_window_none_when_no_phrase():
    assert parse_time_window("why did FS-17 trip?", now=_FIXED_NOW) is None


def test_resolve_context_message_time_beats_ui():
    """A time phrase in the message wins over a UI time selection."""
    ui = UIContext(selected_asset="FS-17", selected_time_range="last_7d")
    frame = resolve_context(
        session_id="s-time-1",
        message="status of FS-17 in the last 30 mins",
        ui_context=ui,
    )
    assert frame.time.source == "EXPLICIT"
    assert frame.time.window_start is not None
    assert frame.time.window_end is not None
    assert (frame.time.window_end - frame.time.window_start).total_seconds() == 30 * 60
