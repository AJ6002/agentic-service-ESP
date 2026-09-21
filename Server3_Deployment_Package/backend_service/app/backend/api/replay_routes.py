"""
Replay API Routes for Historical Fault Replay.
"""

from fastapi import APIRouter, Query
from pydantic import BaseModel
from typing import Optional
from backend.services.replay_service import replay_service

replay_router = APIRouter(prefix="/api/esp/replay", tags=["ESP Replay"])


class ReplayControlRequest(BaseModel):
    action: str  # "start", "pause", "seek", "load"
    speed: Optional[float] = 1.0
    index: Optional[int] = 0
    well_id: Optional[str] = "ALL"
    fault_class: Optional[str] = "ALL"


@replay_router.post("/control")
async def control_replay(req: ReplayControlRequest):
    if req.action == "load":
        count = replay_service.load_replay_dataset(req.well_id, req.fault_class)
        return {"status": "success", "total_records": count}
    elif req.action == "start":
        await replay_service.start_replay(req.speed or 1.0)
        return {"status": "success", "is_playing": True, "speed": req.speed}
    elif req.action == "pause":
        replay_service.pause_replay()
        return {"status": "success", "is_playing": False}
    elif req.action == "seek":
        replay_service.seek(req.index or 0)
        return {"status": "success", "current_index": replay_service.current_index}
    return {"status": "error", "message": f"Unknown action {req.action}"}


@replay_router.get("/status")
async def get_replay_status():
    total = len(replay_service.replay_data) if replay_service.replay_data is not None else 0
    return {
        "status": "success",
        "is_playing": replay_service.is_playing,
        "current_index": replay_service.current_index,
        "total_records": total,
        "speed": replay_service.playback_speed
    }
