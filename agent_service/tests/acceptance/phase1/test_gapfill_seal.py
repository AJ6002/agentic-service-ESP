"""
tests/acceptance/phase1/test_gapfill_seal.py
Formal Phase 1 (Gap-Fill) Acceptance Seal Suite.

Validates the complete Gap-Fill pipeline contracts:
  1. Single targeted refetch on transient DEGRADED required evidence.
  2. Strict replan cap enforcement (replan_count <= max_gapfill_rounds).
  3. Evidence pack version incrementation (v1 -> v2) and non-destructive delta merge.
  4. Honest refusal with INSUFFICIENT done status when gapfill fails to resolve missing data.
"""
from __future__ import annotations

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

from app.contracts.evidence import (
    CallResult, EvidencePack, EvidenceItem, Gap, QoDResult, SealResult,
)
from app.contracts.plan import PlanArtifact, PlanCall
from app.contracts.objective_manifest import ObjectiveManifest
from app.synthesis.gapfill import run_gapfill


def _make_manifest(max_gapfill_rounds: int = 1) -> ObjectiveManifest:
    return ObjectiveManifest(
        objective_id="OP03_FAULT_DIAGNOSIS",
        tool="diagnose_fault",
        safety_class="READ",
        scope="ASSET",
        required_evidence=["get_asset_context", "get_live_telemetry", "get_historian_window"],
        optional_evidence=["get_trips"],
        max_gapfill_rounds=max_gapfill_rounds,
    )


def _make_plan() -> PlanArtifact:
    return PlanArtifact(
        run_id="run-gapfill-seal-001",
        session_id="sess-gapfill-seal-001",
        objective_id="OP03_FAULT_DIAGNOSIS",
        args={"asset_id": "FS-17"},
        confidence=0.95,
        calls=[
            PlanCall(seq=1, kind="READ", tool="get_asset_context", args={"asset_id": "FS-17"}),
            PlanCall(seq=2, kind="READ", tool="get_live_telemetry", args={"asset_id": "FS-17"}),
            PlanCall(seq=3, kind="READ", tool="get_historian_window", args={"asset_id": "FS-17"}),
        ],
    )


def _make_evidence_item(tool: str) -> EvidenceItem:
    return EvidenceItem(
        evidence_id=f"EV-gapfill-{tool}",
        tool=tool,
        source_domain=tool,
        fetched_at=datetime.now(timezone.utc),
        payload={"status": "OK", "data": [10.0, 20.0, 30.0]},
    )


@pytest.mark.anyio
async def test_phase1_gapfill_single_refetch_success():
    """
    AC-P1-1: When a required source is DEGRADED in round 1, Gap-Fill executes
    exactly one targeted refetch, increments pack version to v2, and seals as COMPLETE.
    """
    plan = _make_plan()
    manifest = _make_manifest(max_gapfill_rounds=1)

    pack_v1 = EvidencePack(
        run_id=plan.run_id,
        version=1,
        items=[
            _make_evidence_item("get_asset_context"),
            _make_evidence_item("get_live_telemetry"),
        ],
        gaps=[
            Gap(source_domain="get_historian_window", reason="DEGRADED", required=True),
        ],
    )
    seal_v1 = SealResult(
        pack=pack_v1,
        status="INSUFFICIENT",
        missing_required=["get_historian_window"],
    )

    delta_cr = CallResult(seq=1, status="OK", raw_response={"telemetry": "restored"})
    delta_qod = QoDResult(accepted=True, evidence_item=_make_evidence_item("get_historian_window"))

    with patch("app.synthesis.gapfill.dispatch_plan_calls", new_callable=AsyncMock, return_value=[delta_cr]) as mock_dispatch, \
         patch("app.synthesis.gapfill.validate", return_value=delta_qod), \
         patch("app.synthesis.gapfill.build_and_save") as mock_build, \
         patch("app.synthesis.gapfill.seal") as mock_seal:

        delta_pack = EvidencePack(
            run_id=plan.run_id,
            version=2,
            items=[_make_evidence_item("get_historian_window")],
            gaps=[],
        )
        mock_build.return_value = delta_pack
        seal_v2 = SealResult(pack=delta_pack, status="COMPLETE", missing_required=[])
        mock_seal.return_value = seal_v2

        pack_result, seal_result = await run_gapfill(
            run_id=plan.run_id,
            seal_res=seal_v1,
            plan=plan,
            manifest=manifest,
            existing_pack=pack_v1,
        )

    # 1. Assert exactly 1 dispatch was made for the missing tool
    assert mock_dispatch.call_count == 1
    delta_plan = mock_dispatch.call_args[0][0]
    assert len(delta_plan.calls) == 1
    assert delta_plan.calls[0].tool == "get_historian_window"

    # 2. Assert pack version incremented to 2
    assert pack_result.version == 2

    # 3. Assert all 3 required tools are now present in the resulting pack
    tools_in_pack = {item.tool for item in pack_result.items}
    assert tools_in_pack == {"get_asset_context", "get_live_telemetry", "get_historian_window"}

    # 4. Assert seal status is COMPLETE
    assert seal_result.status == "COMPLETE"
    assert len(seal_result.missing_required) == 0


@pytest.mark.anyio
async def test_phase1_gapfill_replan_cap_enforced():
    """
    AC-P1-2: When refetch also fails, Gap-Fill does not loop infinitely.
    Replan cap is enforced, and result is returned as INSUFFICIENT.
    """
    plan = _make_plan()
    manifest = _make_manifest(max_gapfill_rounds=1)

    pack_v1 = EvidencePack(
        run_id=plan.run_id,
        version=1,
        items=[_make_evidence_item("get_asset_context")],
        gaps=[
            Gap(source_domain="get_live_telemetry", reason="DEGRADED", required=True),
        ],
    )
    seal_v1 = SealResult(
        pack=pack_v1,
        status="INSUFFICIENT",
        missing_required=["get_live_telemetry"],
    )

    failed_cr = CallResult(seq=1, status="FAILED", error="Gateway 503", error_code="GATEWAY_503")
    failed_qod = QoDResult(accepted=False, rejection_reason="GATEWAY_503")

    with patch("app.synthesis.gapfill.dispatch_plan_calls", new_callable=AsyncMock, return_value=[failed_cr]) as mock_dispatch, \
         patch("app.synthesis.gapfill.validate", return_value=failed_qod), \
         patch("app.synthesis.gapfill.build_and_save") as mock_build, \
         patch("app.synthesis.gapfill.seal") as mock_seal:

        still_failed_pack = EvidencePack(
            run_id=plan.run_id,
            version=2,
            items=[],
            gaps=[Gap(source_domain="get_live_telemetry", reason="DEGRADED", required=True)],
        )
        mock_build.return_value = still_failed_pack
        seal_v2 = SealResult(
            pack=still_failed_pack,
            status="INSUFFICIENT",
            missing_required=["get_live_telemetry"],
        )
        mock_seal.return_value = seal_v2

        pack_result, seal_result = await run_gapfill(
            run_id=plan.run_id,
            seal_res=seal_v1,
            plan=plan,
            manifest=manifest,
            existing_pack=pack_v1,
        )

    # Exactly one refetch attempt occurred
    assert mock_dispatch.call_count == 1
    # Remains INSUFFICIENT with clear missing requirement
    assert seal_result.status == "INSUFFICIENT"
    assert "get_live_telemetry" in seal_result.missing_required


@pytest.mark.anyio
async def test_phase1_gapfill_pack_versioning_and_isolation():
    """
    AC-P1-3: Evidence pack merging maintains item integrity without duplicate entries.
    """
    plan = _make_plan()
    manifest = _make_manifest(max_gapfill_rounds=1)

    existing_item_1 = _make_evidence_item("get_asset_context")
    existing_item_2 = _make_evidence_item("get_live_telemetry")

    pack_v1 = EvidencePack(
        run_id=plan.run_id,
        version=1,
        items=[existing_item_1, existing_item_2],
        gaps=[Gap(source_domain="get_historian_window", reason="DEGRADED", required=True)],
    )
    seal_v1 = SealResult(pack=pack_v1, status="INSUFFICIENT", missing_required=["get_historian_window"])

    new_item = _make_evidence_item("get_historian_window")
    delta_qod = QoDResult(accepted=True, evidence_item=new_item)

    with patch("app.synthesis.gapfill.dispatch_plan_calls", new_callable=AsyncMock, return_value=[_make_evidence_item("get_historian_window")]), \
         patch("app.synthesis.gapfill.validate", return_value=delta_qod), \
         patch("app.synthesis.gapfill.build_and_save", return_value=EvidencePack(run_id=plan.run_id, version=2, items=[new_item], gaps=[])), \
         patch("app.synthesis.gapfill.seal", return_value=SealResult(pack=pack_v1, status="COMPLETE", missing_required=[])):

        pack_result, _ = await run_gapfill(
            run_id=plan.run_id,
            seal_res=seal_v1,
            plan=plan,
            manifest=manifest,
            existing_pack=pack_v1,
        )

    assert pack_result.version == 2
    assert len(pack_result.items) == 3
    # Check that item IDs are unique
    item_ids = [item.evidence_id for item in pack_result.items]
    assert len(item_ids) == len(set(item_ids))
