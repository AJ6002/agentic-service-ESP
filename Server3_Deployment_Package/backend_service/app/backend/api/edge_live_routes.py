"""
FastAPI Router for Live Data API (MQTT Facade)
Mounted at /live
"""

from typing import Optional
from fastapi import APIRouter, Query, Path
from fastapi.responses import JSONResponse

from backend.services.edge_live_service import live_service

router = APIRouter(tags=["Live Data API"])


@router.get("/health")
def get_live_health():
    """Health check for Live MQTT Facade."""
    code, data = live_service.get_health()
    return JSONResponse(status_code=code, content=data)


@router.get("/telemetry/{well_id}")
def get_live_telemetry(
    well_id: str = Path(..., description="Canonical well ID")
):
    """Most recent telemetry packet for a well."""
    code, data = live_service.get_telemetry(well_id)
    return JSONResponse(status_code=code, content=data)


@router.get("/telemetry/{well_id}/recent")
def get_live_recent(
    well_id: str = Path(..., description="Canonical well ID"),
    seconds: int = Query(30, ge=1, le=60, description="Recent window span in seconds (max 60)")
):
    """Ring buffer of last N seconds of telemetry."""
    code, data = live_service.get_recent(well_id, seconds)
    return JSONResponse(status_code=code, content=data)


@router.get("/vfm/{well_id}")
def get_live_vfm(
    well_id: str = Path(..., description="Canonical well ID")
):
    """Most recent Virtual Flow Metering (VFM) packet."""
    code, data = live_service.get_vfm(well_id)
    return JSONResponse(status_code=code, content=data)


@router.get("/asset/{well_id}")
def get_live_asset(
    well_id: str = Path(..., description="Canonical well ID")
):
    """Retained nameplate specifications and pump curve coefficients."""
    code, data = live_service.get_asset(well_id)
    return JSONResponse(status_code=code, content=data)


@router.get("/status")
def get_live_status():
    """Simulator liveness status."""
    code, data = live_service.get_status()
    return JSONResponse(status_code=code, content=data)


@router.get("/wells")
def get_live_wells():
    """List of all wells currently publishing."""
    code, data = live_service.get_wells()
    return JSONResponse(status_code=code, content=data)
