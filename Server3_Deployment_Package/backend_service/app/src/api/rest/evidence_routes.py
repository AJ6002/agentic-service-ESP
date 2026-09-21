"""
FastAPI REST API Routes for Phase 8 Evidence Pack & Agent Context
Grounded in ESP_APM_PHASE_8_Evidence_Pack_Agent_Context_Implementation_Design.docx §22
"""

from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query, Body

from src.schemas.evidence import EvidencePack, EvidenceItem
from src.schemas.context_view import ContextView
from src.services.evidence.context_builder import ContextBuilder
from src.adapters.evidence_repository import EvidenceRepository

router = APIRouter(prefix="/api/v1", tags=["evidence"])
context_builder = ContextBuilder()
evidence_repo = EvidenceRepository()


@router.post("/evidence/pack", response_model=Dict[str, Any])
def build_and_freeze_evidence_pack(
    request_id: str = Query(..., description="Session request ID"),
    asset_id: str = Query(..., description="Target asset identifier"),
    objective_id: str = Query("OP02_PRODUCTION_DECLINE_RCA", description="Operational objective ID"),
    payload: Dict[str, Any] = Body(default={}, description="Optional evidence inputs: telemetry, calculations, models")
):
    """
    POST /api/v1/evidence/pack
    Build, validate, rank, and freeze EvidencePack.
    """
    try:
        pack = context_builder.build_evidence_pack(
            request_id=request_id,
            asset_id=asset_id,
            objective_id=objective_id,
            asset_context=payload.get("asset_context"),
            telemetry_data=payload.get("telemetry"),
            model_outputs=payload.get("models"),
            calculations=payload.get("calculations"),
            knowledge_results=payload.get("knowledge")
        )
        pack_id = evidence_repo.save_evidence_pack(pack)
        return {
            "status": "FROZEN",
            "pack_id": pack_id,
            "checksum": pack.checksum,
            "items_count": len(pack.items),
            "conflicts_count": len(pack.conflicts),
            "evidence_pack": pack.model_dump()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/evidence/{pack_id}", response_model=Dict[str, Any])
def get_frozen_evidence_pack(pack_id: str):
    """
    GET /api/v1/evidence/{pack_id}
    Retrieve frozen EvidencePack by ID.
    """
    pack = evidence_repo.get_evidence_pack(pack_id)
    if not pack:
        raise HTTPException(status_code=404, detail=f"EvidencePack '{pack_id}' not found.")
    return pack.model_dump()


@router.get("/evidence/{pack_id}/conflicts", response_model=Dict[str, Any])
def get_evidence_pack_conflicts(pack_id: str):
    """
    GET /api/v1/evidence/{pack_id}/conflicts
    Fetch surfaced conflicts for an EvidencePack.
    """
    pack = evidence_repo.get_evidence_pack(pack_id)
    if not pack:
        raise HTTPException(status_code=404, detail=f"EvidencePack '{pack_id}' not found.")
    return {
        "pack_id": pack_id,
        "conflicts_count": len(pack.conflicts),
        "conflicts": [c.model_dump() for c in pack.conflicts]
    }


@router.post("/context/build", response_model=Dict[str, Any])
def build_context_view(
    run_id: str = Query(..., description="Agent run ID"),
    pack_id: str = Query(..., description="Associated frozen EvidencePack ID")
):
    """
    POST /api/v1/context/build
    Assemble bounded ContextView from a frozen EvidencePack.
    """
    pack = evidence_repo.get_evidence_pack(pack_id)
    if not pack:
        raise HTTPException(status_code=404, detail=f"EvidencePack '{pack_id}' not found.")
    
    view = context_builder.build_context_view(pack, run_id=run_id)
    return view.model_dump()
