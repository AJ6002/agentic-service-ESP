"""
FastAPI Router for Historian API
Mounted at /historian
"""

from typing import Optional
from fastapi import APIRouter, Query, Response, status
from fastapi.responses import JSONResponse

from backend.services.edge_historian_service import historian_service

router = APIRouter(tags=["Historian API"])


@router.get("/health")
def get_historian_health():
    """Health check for Historian service."""
    return historian_service.get_health()


@router.get("/window")
def get_historian_window(
    well_id: str = Query(..., description="Canonical well ID"),
    start: str = Query(..., description="Start ISO-8601 timestamp inclusive"),
    end: str = Query(..., description="End ISO-8601 timestamp inclusive"),
    signals: Optional[str] = Query(None, description="Comma-separated canonical signal names"),
    limit: int = Query(10000, description="Max row count (default 10000, max 50000)")
):
    """Raw rows for a bounded time window."""
    code, data = historian_service.get_window(well_id, start, end, signals, limit)
    return JSONResponse(status_code=code, content=data)


@router.get("/latest")
def get_historian_latest(
    well_id: str = Query(..., description="Canonical well ID"),
    signals: Optional[str] = Query(None, description="Comma-separated signal names")
):
    """Most recent reading per signal for one well."""
    code, data = historian_service.get_latest(well_id, signals)
    return JSONResponse(status_code=code, content=data)


@router.get("/aggregates")
def get_historian_aggregates(
    well_id: str = Query(..., description="Canonical well ID"),
    start: str = Query(..., description="Start ISO-8601 timestamp inclusive"),
    end: str = Query(..., description="End ISO-8601 timestamp inclusive"),
    signals: str = Query(..., description="Comma-separated signal names"),
    bucket: str = Query("5m", description="Bucket window: 1m, 5m, 15m, 1h, 1d"),
    agg: str = Query("avg", description="Aggregation function: avg, min, max, all")
):
    """Downsampled time window backed by DuckDB/SQLite GROUP BY."""
    code, data = historian_service.get_aggregates(well_id, start, end, signals, bucket, agg)
    return JSONResponse(status_code=code, content=data)


@router.get("/coverage")
def get_historian_coverage(
    well_id: str = Query(..., description="Canonical well ID")
):
    """Time ranges and telemetry coverage available for a well."""
    code, data = historian_service.get_coverage(well_id)
    return JSONResponse(status_code=code, content=data)
