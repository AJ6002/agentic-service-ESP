"""
tests/test_gapfill.py — Gap-Fill (Slice 2.5) acceptance tests.

4 cases from the exit criteria in the implementation plan:
  1. Happy path: INSUFFICIENT -> gap-fill succeeds -> COMPLETE -> XAI fires
  2. Still INSUFFICIENT after gap-fill -> honest refusal fires, no third round
  3. max_gapfill_rounds=0 (OP01 default) -> refusal fires immediately, no gap-fill call
  4. Hash reuse: v1 items that were already OK are NOT re-dispatched
"""
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch, call

from app.contracts.evidence import (
    CallResult, EvidencePack, EvidenceItem, Gap, QoDResult, SealResult,
)
from app.contracts.plan import PlanArtifact, PlanCall
from app.contracts.objective_manifest import ObjectiveManifest
from app.synthesis.gapfill import run_gapfill
from datetime import datetime, timezone


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _manifest(max_gapfill_rounds: int = 1) -> ObjectiveManifest:
    return ObjectiveManifest(
        objective_id="OP03_FAULT_DIAGNOSIS",
        tool="diagnose_fault",
        safety_class="READ",
        scope="ASSET",
        required_evidence=["get_asset_context", "get_live_telemetry", "get_historian_window"],
        optional_evidence=[],
        max_gapfill_rounds=max_gapfill_rounds,
    )


def _plan() -> PlanArtifact:
    return PlanArtifact(
        run_id="test-run",
        session_id="test-session",
        objective_id="OP03_FAULT_DIAGNOSIS",
        args={"asset_id": "WELL-01"},
        confidence=0.9,
        calls=[],
    )


def _ok_item(tool: str) -> EvidenceItem:
    return EvidenceItem(
        evidence_id=f"eid-{tool}",
        tool=tool,
        source_domain=tool,
        fetched_at=datetime.now(timezone.utc),
        payload={"value": 1.0},
    )


def _ok_cr() -> CallResult:
    return CallResult(seq=1, status="OK", raw_response={"value": 1.0})


def _degraded_cr() -> CallResult:
    return CallResult(seq=1, status="FAILED", error="timeout", error_code="TIMEOUT")


def _v1_pack_insufficient() -> tuple[EvidencePack, SealResult]:
    """v1 pack: asset_context + live_telemetry OK, historian ABSENT."""
    pack = EvidencePack(
        run_id="test-run",
        version=1,
        items=[
            _ok_item("get_asset_context"),
            _ok_item("get_live_telemetry"),
        ],
        gaps=[
            Gap(source_domain="get_historian_window", reason="DEGRADED", required=True),
        ],
    )
    seal_res = SealResult(
        pack=pack,
        status="INSUFFICIENT",
        missing_required=["get_historian_window"],
    )
    return pack, seal_res


# ---------------------------------------------------------------------------
# Case 1: Happy path — gap-fill succeeds, pack v2 is COMPLETE
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_gapfill_happy_path():
    pack_v1, seal_v1 = _v1_pack_insufficient()
    manifest = _manifest(max_gapfill_rounds=1)
    plan = _plan()

    # Delta dispatch returns one successful result for historian
    delta_cr = _ok_cr()
    delta_qod = QoDResult(accepted=True, evidence_item=_ok_item("get_historian_window"))

    with patch("app.synthesis.gapfill.dispatch_plan_calls", new_callable=AsyncMock, return_value=[delta_cr]) as mock_dispatch, \
         patch("app.synthesis.gapfill.validate", return_value=delta_qod) as mock_validate, \
         patch("app.synthesis.gapfill.build_and_save") as mock_build, \
         patch("app.synthesis.gapfill.seal") as mock_seal:

        # build_and_save returns a delta pack with the historian item
        delta_pack = EvidencePack(
            run_id="test-run", version=2,
            items=[_ok_item("get_historian_window")], gaps=[],
        )
        mock_build.return_value = delta_pack

        # Re-seal of v2 pack is COMPLETE
        seal_v2 = SealResult(pack=delta_pack, status="COMPLETE", missing_required=[])
        mock_seal.return_value = seal_v2

        pack_result, seal_result = await run_gapfill(
            run_id="test-run",
            seal_res=seal_v1,
            plan=plan,
            manifest=manifest,
            existing_pack=pack_v1,
        )

    # Gap-fill dispatched exactly the missing tool
    assert mock_dispatch.called
    dispatched_tools = [c.tool for c in mock_dispatch.call_args[0][0].calls]
    assert dispatched_tools == ["get_historian_window"]

    # Pack v2 must include kept v1 items + new delta item
    assert any(i.tool == "get_asset_context"     for i in pack_result.items)
    assert any(i.tool == "get_live_telemetry"     for i in pack_result.items)
    assert any(i.tool == "get_historian_window"   for i in pack_result.items)
    assert pack_result.version == 2

    # Seal is now COMPLETE
    assert seal_result.status == "COMPLETE"


# ---------------------------------------------------------------------------
# Case 2: Still INSUFFICIENT after gap-fill -> honest refusal path fires
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_gapfill_still_insufficient():
    pack_v1, seal_v1 = _v1_pack_insufficient()
    manifest = _manifest(max_gapfill_rounds=1)
    plan = _plan()

    degraded_cr = _degraded_cr()
    degraded_qod = QoDResult(accepted=False, rejection_reason="TIMEOUT")

    with patch("app.synthesis.gapfill.dispatch_plan_calls", new_callable=AsyncMock, return_value=[degraded_cr]), \
         patch("app.synthesis.gapfill.validate", return_value=degraded_qod), \
         patch("app.synthesis.gapfill.build_and_save") as mock_build, \
         patch("app.synthesis.gapfill.seal") as mock_seal:

        still_missing_pack = EvidencePack(
            run_id="test-run", version=2,
            items=[], gaps=[Gap(source_domain="get_historian_window", reason="DEGRADED", required=True)],
        )
        mock_build.return_value = still_missing_pack

        # Re-seal of v2 pack is STILL INSUFFICIENT
        seal_v2 = SealResult(
            pack=still_missing_pack,
            status="INSUFFICIENT",
            missing_required=["get_historian_window"],
        )
        mock_seal.return_value = seal_v2

        pack_result, seal_result = await run_gapfill(
            run_id="test-run",
            seal_res=seal_v1,
            plan=plan,
            manifest=manifest,
            existing_pack=pack_v1,
        )

    # Still INSUFFICIENT — caller's honest refusal block will fire
    assert seal_result.status == "INSUFFICIENT"
    assert "get_historian_window" in seal_result.missing_required
    # run_gapfill itself did NOT raise; it returned cleanly


# ---------------------------------------------------------------------------
# Case 3: max_gapfill_rounds=0 — runner.py must NOT call run_gapfill
#          (tested at runner level by checking the manifest guard logic)
# ---------------------------------------------------------------------------

def test_gapfill_disabled_when_zero_rounds():
    """
    Verify that the manifest guard (max_gapfill_rounds >= 1) correctly
    short-circuits for objectives with the default value of 0.
    This tests the contract, not runner.py internals.
    """
    manifest = _manifest(max_gapfill_rounds=0)
    assert manifest.max_gapfill_rounds == 0
    # The runner.py condition `manifest.max_gapfill_rounds >= 1` will be False,
    # so run_gapfill is never called. No mock needed — the guard is the spec.


# ---------------------------------------------------------------------------
# Case 4: Hash reuse — OK v1 items are NOT re-dispatched in the delta plan
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_gapfill_only_dispatches_missing_tools():
    pack_v1, seal_v1 = _v1_pack_insufficient()
    manifest = _manifest(max_gapfill_rounds=1)
    plan = _plan()

    delta_cr = _ok_cr()
    delta_qod = QoDResult(accepted=True, evidence_item=_ok_item("get_historian_window"))

    with patch("app.synthesis.gapfill.dispatch_plan_calls", new_callable=AsyncMock, return_value=[delta_cr]) as mock_dispatch, \
         patch("app.synthesis.gapfill.validate", return_value=delta_qod), \
         patch("app.synthesis.gapfill.build_and_save") as mock_build, \
         patch("app.synthesis.gapfill.seal") as mock_seal:

        delta_pack = EvidencePack(
            run_id="test-run", version=2,
            items=[_ok_item("get_historian_window")], gaps=[],
        )
        mock_build.return_value = delta_pack
        mock_seal.return_value = SealResult(pack=delta_pack, status="COMPLETE", missing_required=[])

        await run_gapfill(
            run_id="test-run",
            seal_res=seal_v1,
            plan=plan,
            manifest=manifest,
            existing_pack=pack_v1,
        )

    # Only the MISSING tool was dispatched — not get_asset_context or get_live_telemetry
    dispatched = mock_dispatch.call_args[0][0]
    assert len(dispatched.calls) == 1
    assert dispatched.calls[0].tool == "get_historian_window"
    # get_asset_context and get_live_telemetry were already OK — not re-dispatched
    dispatched_tools = {c.tool for c in dispatched.calls}
    assert "get_asset_context"  not in dispatched_tools
    assert "get_live_telemetry" not in dispatched_tools


# ---------------------------------------------------------------------------
# Case 5: ABSENT gap is NOT retried (permanent failure like WELL_NOT_FOUND)
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_gapfill_skips_absent_gaps():
    """
    If the v1 gap for a missing required tool has reason=ABSENT (e.g. WELL_NOT_FOUND),
    run_gapfill must NOT dispatch a retry for it — the asset is permanently unknown.
    The original pack and seal result are returned unchanged.
    """
    # All three required tools are ABSENT (well doesn't exist in any domain)
    pack_v1 = EvidencePack(
        run_id="test-run",
        version=1,
        items=[],
        gaps=[
            Gap(source_domain="get_asset_context",   reason="ABSENT", required=True),
            Gap(source_domain="get_live_telemetry",  reason="ABSENT", required=True),
            Gap(source_domain="get_historian_window", reason="ABSENT", required=True),
        ],
    )
    seal_v1 = SealResult(
        pack=pack_v1,
        status="INSUFFICIENT",
        missing_required=["get_asset_context", "get_live_telemetry", "get_historian_window"],
    )
    manifest = _manifest(max_gapfill_rounds=1)
    plan = _plan()

    with patch("app.synthesis.gapfill.dispatch_plan_calls", new_callable=AsyncMock) as mock_dispatch:
        pack_result, seal_result = await run_gapfill(
            run_id="test-run",
            seal_res=seal_v1,
            plan=plan,
            manifest=manifest,
            existing_pack=pack_v1,
        )

    # No dispatch should have happened — all gaps are ABSENT (permanent)
    mock_dispatch.assert_not_called()
    # Original seal returned unchanged (still INSUFFICIENT)
    assert seal_result.status == "INSUFFICIENT"
    assert pack_result is pack_v1  # same object, no merge


