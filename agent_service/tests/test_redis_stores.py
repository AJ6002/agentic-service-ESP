from datetime import datetime
import pytest

from app.contracts.context import SessionSnapshot
from app.contracts.hitl import PendingInterrupt, RunState
from app.stores.session_store import (
    save_session,
    get_session,
    save_pending,
    get_pending,
    delete_pending,
    get_pending_ttl,
)
from app.stores.run_store import (
    save_run,
    get_run,
    get_run_ttl,
    save_pack,
    get_pack,
)

def test_session_store_crud_and_ttl():
    session_id = "test-session-001"
    snapshot = SessionSnapshot(
        last_objective="OP03_FAULT_DIAGNOSIS",
        last_analysis_id="R999",
        turn_count=2,
    )
    save_session(session_id, snapshot, ttl_sec=60)
    retrieved = get_session(session_id)
    assert retrieved is not None
    assert retrieved.last_objective == "OP03_FAULT_DIAGNOSIS"
    assert retrieved.turn_count == 2

def test_pending_store_crud_and_delete():
    session_id = "test-session-002"
    pending = PendingInterrupt(
        run_id="R888",
        reason="CLARIFY",
        resume_at="PLAN_BUILD",
        slot="asset_id",
        options=["FS-017", "FNW-01"],
        raised_at=datetime.utcnow(),
    )
    save_pending(session_id, pending, ttl_sec=300)
    retrieved = get_pending(session_id)
    assert retrieved is not None
    assert retrieved.run_id == "R888"
    assert retrieved.slot == "asset_id"
    assert get_pending_ttl(session_id) > 0

    delete_pending(session_id)
    assert get_pending(session_id) is None

def test_run_store_crud_and_pack_versioning():
    run_id = "R777"
    run = RunState(
        run_id=run_id,
        session_id="test-session-003",
        status="RUNNING",
        objective_id="OP01_CURRENT_STATUS",
        args={"asset_id": "FS-091"},
        turn_count=1,
    )
    save_run(run, ttl_sec=120)
    retrieved = get_run(run_id)
    assert retrieved is not None
    assert retrieved.run_id == run_id
    assert retrieved.status == "RUNNING"
    assert get_run_ttl(run_id) > 0

    pack_v1 = {"items": [{"id": 1, "val": "data_v1"}]}
    save_pack(run_id, version=1, pack_data=pack_v1)
    pack_v2 = {"items": [{"id": 2, "val": "data_v2"}]}
    save_pack(run_id, version=2, pack_data=pack_v2)

    assert get_pack(run_id, version="latest") == pack_v2
    assert get_pack(run_id, version="1") == pack_v1
