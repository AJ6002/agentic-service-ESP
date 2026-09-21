"""
FastAPI Router for Events API
Mounted at /events
"""

from typing import Optional
from fastapi import APIRouter, Query, Path
from fastapi.responses import JSONResponse

from backend.services.edge_events_service import events_service

router = APIRouter(tags=["Events API"])


@router.get("/health")
def get_events_health():
    """Health check for Events API."""
    data = events_service.get_health()
    return JSONResponse(status_code=200, content=data)


@router.get("/timeline")
def get_events_timeline(
    well_id: str = Query(..., description="Canonical well ID"),
    start: str = Query(..., description="Start ISO-8601 timestamp"),
    end: str = Query(..., description="End ISO-8601 timestamp"),
    types: Optional[str] = Query(None, description="Comma-separated event types: trip, alarm, state_change, scenario_change"),
    limit: int = Query(1000, ge=1, le=10000, description="Max event count")
):
    """Events for a well over a bounded window."""
    code, data = events_service.get_timeline(well_id, start, end, types, limit)
    return JSONResponse(status_code=code, content=data)


@router.get("/trips")
def get_events_trips(
    well_id: Optional[str] = Query(None, description="Optional well ID filter"),
    start: Optional[str] = Query(None, description="Optional start timestamp"),
    end: Optional[str] = Query(None, description="Optional end timestamp"),
    limit: int = Query(1000, ge=1, le=10000, description="Max event count")
):
    """Filtered trips across the fleet or one well."""
    code, data = events_service.get_trips(well_id, start, end, limit)
    return JSONResponse(status_code=code, content=data)


@router.get("/latest/{well_id}")
def get_events_latest(
    well_id: str = Path(..., description="Canonical well ID")
):
    """Most recent event for a well."""
    code, data = events_service.get_latest(well_id)
    return JSONResponse(status_code=code, content=data)


@router.get("/summary")
def get_events_summary(
    start: Optional[str] = Query(None, description="Start timestamp"),
    end: Optional[str] = Query(None, description="End timestamp"),
    well_id: Optional[str] = Query(None, description="Optional well ID filter")
):
    """Counts per well per event type over a window."""
    code, data = events_service.get_summary(start, end, well_id)
    return JSONResponse(status_code=code, content=data)


@router.get("/catalog")
def get_events_catalog():
    """Reference data: canonical trip causes and alarm tags."""
    code, data = events_service.get_catalog()
    return JSONResponse(status_code=code, content=data)
