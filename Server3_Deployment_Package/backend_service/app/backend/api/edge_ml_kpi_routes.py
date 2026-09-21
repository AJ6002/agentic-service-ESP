"""
FastAPI Router for ML Results, Plots, Holistic KPI, and Granular Dashboard KPI Cards.
Mounted at /ml, /kpi, /cards, /plots
"""

from typing import Optional
from fastapi import APIRouter, Query, Path
from fastapi.responses import JSONResponse

from backend.services.edge_ml_kpi_service import ml_kpi_service

ml_router = APIRouter(tags=["ML API"])
kpi_router = APIRouter(tags=["KPI API"])
cards_router = APIRouter(tags=["Dashboard Cards & Widgets API"])
plots_router = APIRouter(tags=["Dashboard Plots API"])

# ── 1. ML Endpoints ──────────────────────────────────────────────────────────

@ml_router.get("/health")
def get_ml_health():
    """Health check for ML Diagnostic Service."""
    data = ml_kpi_service.get_health()
    return JSONResponse(status_code=200, content=data)


@ml_router.get("/anomaly/{well_id}")
def get_ml_anomaly(well_id: str = Path(..., description="Canonical well ID")):
    """Latest anomaly score for a well."""
    code, data = ml_kpi_service.get_anomaly(well_id)
    return JSONResponse(status_code=code, content=data)


@ml_router.get("/fault/{well_id}")
def get_ml_fault(well_id: str = Path(..., description="Canonical well ID")):
    """Latest fault classification with probability and top-k distribution."""
    code, data = ml_kpi_service.get_fault(well_id)
    return JSONResponse(status_code=code, content=data)


@ml_router.get("/health/{well_id}")
def get_ml_health_score(well_id: str = Path(..., description="Canonical well ID")):
    """Latest composite health index (0-100) and negative contributors."""
    code, data = ml_kpi_service.get_health_score(well_id)
    return JSONResponse(status_code=code, content=data)


@ml_router.get("/degradation/{well_id}")
def get_ml_degradation(well_id: str = Path(..., description="Canonical well ID")):
    """Degradation trajectory and projected days to threshold."""
    code, data = ml_kpi_service.get_degradation(well_id)
    return JSONResponse(status_code=code, content=data)


@ml_router.get("/explain/{well_id}")
def get_ml_explain(
    well_id: str = Path(..., description="Canonical well ID"),
    output: str = Query("fault", description="Target output to explain: anomaly, fault, or health")
):
    """SHAP-style feature contributions for the requested output."""
    code, data = ml_kpi_service.get_explain(well_id, output)
    return JSONResponse(status_code=code, content=data)


# ── 2. Plots Endpoints ───────────────────────────────────────────────────────

@plots_router.get("/{well_id}/{plot_id}")
def get_plot_data(
    well_id: str = Path(..., description="Canonical well ID"),
    plot_id: str = Path(..., description="Named plot ID: health_trajectory, anomaly_trend, pressure_corridor, motor_load_trend, production_decline")
):
    """Pre-computed plot series data for dashboard widget."""
    code, data = ml_kpi_service.get_plot(well_id, plot_id)
    return JSONResponse(status_code=code, content=data)


# ── 3. Holistic & Fleet KPI Endpoints ────────────────────────────────────────

@kpi_router.get("/fleet")
def get_kpi_fleet(
    cluster: Optional[str] = Query(None, description="Optional cluster filter"),
    status: Optional[str] = Query(None, description="Optional operating status filter: running, tripped")
):
    """KPI snapshot across all wells in scope."""
    code, data = ml_kpi_service.get_kpi_fleet(cluster, status)
    return JSONResponse(status_code=code, content=data)


@kpi_router.get("/{well_id}")
def get_kpi_snapshot(well_id: str = Path(..., description="Canonical well ID")):
    """Live holistic KPI snapshot for one well."""
    code, data = ml_kpi_service.get_kpi_snapshot(well_id)
    return JSONResponse(status_code=code, content=data)


# ── 4. Granular KPI Card Sub-Endpoints (/kpi/{well_id}/*) ───────────────────

@kpi_router.get("/{well_id}/gross-liquid-rate")
@kpi_router.get("/{well_id}/liquid-rate")
def get_kpi_liquid_rate(well_id: str = Path(...)):
    code, data = ml_kpi_service.get_card_data(well_id, "gross-liquid-rate")
    return JSONResponse(status_code=code, content=data)


@kpi_router.get("/{well_id}/net-oil-rate")
@kpi_router.get("/{well_id}/oil-rate")
def get_kpi_oil_rate(well_id: str = Path(...)):
    code, data = ml_kpi_service.get_card_data(well_id, "net-oil-rate")
    return JSONResponse(status_code=code, content=data)


@kpi_router.get("/{well_id}/water-cut")
@kpi_router.get("/{well_id}/produced-water")
def get_kpi_water_cut(well_id: str = Path(...)):
    code, data = ml_kpi_service.get_card_data(well_id, "water-cut")
    return JSONResponse(status_code=code, content=data)


@kpi_router.get("/{well_id}/associated-gas")
@kpi_router.get("/{well_id}/gas-rate")
def get_kpi_gas_rate(well_id: str = Path(...)):
    code, data = ml_kpi_service.get_card_data(well_id, "associated-gas")
    return JSONResponse(status_code=code, content=data)


@kpi_router.get("/{well_id}/production-deferment")
@kpi_router.get("/{well_id}/deferment")
def get_kpi_deferment(well_id: str = Path(...)):
    code, data = ml_kpi_service.get_card_data(well_id, "production-deferment")
    return JSONResponse(status_code=code, content=data)


@kpi_router.get("/{well_id}/energy-balance")
def get_kpi_energy_balance(well_id: str = Path(...)):
    code, data = ml_kpi_service.get_card_data(well_id, "energy-balance")
    return JSONResponse(status_code=code, content=data)


@kpi_router.get("/{well_id}/motor-load")
def get_kpi_motor_load(well_id: str = Path(...)):
    code, data = ml_kpi_service.get_card_data(well_id, "motor-load")
    return JSONResponse(status_code=code, content=data)


@kpi_router.get("/{well_id}/motor-temperature")
def get_kpi_motor_temp(well_id: str = Path(...)):
    code, data = ml_kpi_service.get_card_data(well_id, "motor-temperature")
    return JSONResponse(status_code=code, content=data)


@kpi_router.get("/{well_id}/vibration")
def get_kpi_vibration(well_id: str = Path(...)):
    code, data = ml_kpi_service.get_card_data(well_id, "vibration")
    return JSONResponse(status_code=code, content=data)


@kpi_router.get("/{well_id}/intake-pressure")
def get_kpi_intake_pressure(well_id: str = Path(...)):
    code, data = ml_kpi_service.get_card_data(well_id, "intake-pressure")
    return JSONResponse(status_code=code, content=data)


@kpi_router.get("/{well_id}/discharge-pressure")
def get_kpi_discharge_pressure(well_id: str = Path(...)):
    code, data = ml_kpi_service.get_card_data(well_id, "discharge-pressure")
    return JSONResponse(status_code=code, content=data)


@kpi_router.get("/{well_id}/vsd-advisor")
def get_kpi_vsd_advisor(well_id: str = Path(...)):
    code, data = ml_kpi_service.get_card_data(well_id, "vsd-advisor")
    return JSONResponse(status_code=code, content=data)


# ── 5. Dashboard Cards & Component Catalog (/cards/*) ───────────────────────

@cards_router.get("/catalog")
def get_cards_catalog():
    """Complete catalog of all dashboard widgets, component IDs, visual descriptions, and Agent usage guides."""
    code, data = ml_kpi_service.get_catalog()
    return JSONResponse(status_code=code, content=data)


@cards_router.get("/{well_id}/{card_id}")
def get_individual_card(
    well_id: str = Path(..., description="Canonical well ID"),
    card_id: str = Path(..., description="Card ID or Component ID from catalog (e.g. gross-liquid-rate, net-oil-rate, health-score)")
):
    """
    Returns data payload for a specific KPI Card, enriched with component-ID metadata,
    plot style, thresholds, operational representation, and Agent reasoning guidance.
    """
    code, data = ml_kpi_service.get_card_data(well_id, card_id)
    return JSONResponse(status_code=code, content=data)
