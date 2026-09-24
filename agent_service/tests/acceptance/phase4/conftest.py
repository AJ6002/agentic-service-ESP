import json
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.contracts.context import SessionSnapshot
from app.contracts.evidence import EvidenceItem, EvidencePack
from app.contracts.advisory import Advisory
from app.contracts.visualization import VisualizationSpec
from app.stores.redis_client import get_redis_client
from app.stores.session_store import save_session, delete_session, delete_pending
from app.stores.run_store import save_pack, save_run_artifacts, _run_key

@pytest.fixture
def seed_prior_analysis():
    """Seeds a sealed diagnostic analysis into Redis for Turn 2 follow-up testing."""
    def _seed(session_id: str = "sess-fup-1", run_id: str = "run-diag-101", well_id: str = "FS-17"):
        # 1. Create items
        item1 = EvidenceItem(
            evidence_id="EV-001",
            tool="get_asset_context",
            source_domain="context",
            fetched_at=datetime.now(timezone.utc),
            payload={"asset": {"well_id": well_id, "pump_type": "B400", "rated_amp_a": 48.0}},
            status="OK",
        )
        item2 = EvidenceItem(
            evidence_id="EV-002",
            tool="get_live_telemetry",
            source_domain="telemetry",
            fetched_at=datetime.now(timezone.utc),
            payload={"measurements": {"STD_FREQ_HZ": 50.0, "STD_AMP_A": 35.5, "STD_MOTOR_TEMP_C": 88.4, "STD_INT_PRS_PSI": 412.0, "STD_DISCH_PRS_PSI": 1890.0, "STD_VFD_STS": True}},
            status="OK",
        )
        pack = EvidencePack(
            run_id=run_id,
            version=1,
            sealed=True,
            sealed_at=datetime.now(timezone.utc),
            items=[item1, item2],
            gaps=[],
            conflicts=[],
        )
        save_pack(run_id, 1, pack.model_dump(mode="json"))

        adv = {
            "objective_id": "OP03_FAULT_DIAGNOSIS",
            "assessment": "Gas interference detected causing pump-off with intake pressure at 412.0 psi.",
            "recommendation": "Vent annular gas and reduce VFD frequency to 48.0 Hz.",
            "hypotheses": ["Severe gas locking at pump intake", "Intermittent gas slugging"],
            "cited_evidence_ids": ["EV-001", "EV-002"],
        }
        viz = {
            "widget_id": "cards",
            "card_ids": ["pressure-corridor", "evidence-cards"],
            "evidence_ids": ["EV-001", "EV-002"],
        }
        save_run_artifacts(run_id, adv, viz)

        session = SessionSnapshot(
            session_id=session_id,
            turn_count=1,
            last_asset_id=well_id,
            last_objective="OP03_FAULT_DIAGNOSIS",
            last_analysis_id=run_id,
        )
        save_session(session_id, session)
        return session_id, run_id, pack, adv, viz

    return _seed
