"""
Tests for Sprint 6 — Fleet Visual Cards.
Validates:
1. Card registry declarations for fleet-health-table, fleet-opportunity-view, fleet-production-summary
2. PostgreSQL generators in cards adapter (fetch_card for each fleet card)
3. Visualization planner qualification for OP08, OP09, OP13 fleet objectives
"""

import pytest
import yaml
from pathlib import Path

from app.gateway.adapters.cards import fetch_card, fetch_cards_catalog
from app.visualization.planner import plan_visualization, _load_cards_registry
from app.contracts.evidence import EvidenceItem, EvidencePack
from app.evidence.seal_check import seal


def test_cards_registry_declarations():
    """Verify fleet visual cards are declared with required_signals: [] in cards_registry.yaml."""
    cfg_path = Path(__file__).resolve().parent.parent / "config" / "cards_registry.yaml"
    with open(cfg_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)["cards"]

    assert "fleet-health-table" in data
    assert data["fleet-health-table"]["required_signals"] == []
    assert data["fleet-health-table"]["component_id"] == "FleetHealthTable"

    assert "fleet-opportunity-view" in data
    assert data["fleet-opportunity-view"]["required_signals"] == []
    assert data["fleet-opportunity-view"]["component_id"] == "FleetOpportunityView"

    assert "fleet-production-summary" in data
    assert data["fleet-production-summary"]["required_signals"] == []
    assert data["fleet-production-summary"]["component_id"] == "FleetProductionSummary"


@pytest.mark.anyio
async def test_fetch_card_fleet_health_table():
    """Real PostgreSQL test: fetch fleet-health-table card and verify structure."""
    res = await fetch_card("GLOBAL", "fleet-health-table")
    assert res["status"] == "OK"
    assert res["card_id"] == "fleet_health_table"
    payload = res["payload"]

    assert payload["totalWells"] > 0
    assert len(payload["wells"]) == payload["totalWells"]
    assert payload["healthyCount"] + payload["degradedCount"] + payload["criticalCount"] == payload["totalWells"]

    # Check well fields
    first_well = payload["wells"][0]
    assert "wellId" in first_well
    assert "healthScore" in first_well
    assert first_well["healthBand"] in ("HEALTHY", "DEGRADED", "CRITICAL")
    assert "operatingState" in first_well
    assert "topSignal" in first_well
    assert "grossRateBpd" in first_well


@pytest.mark.anyio
async def test_fetch_card_fleet_opportunity_view():
    """Real PostgreSQL test: fetch fleet-opportunity-view card and verify ranking."""
    res = await fetch_card("GLOBAL", "fleet-opportunity-view")
    assert res["status"] == "OK"
    assert res["card_id"] == "fleet_opportunity_view"
    payload = res["payload"]

    assert "rankedWells" in payload
    assert payload["candidateCount"] == len(payload["rankedWells"])
    assert payload["totalOpportunityBpd"] >= 0.0

    if payload["candidateCount"] > 0:
        top_cand = payload["rankedWells"][0]
        assert top_cand["rank"] == 1
        assert "wellId" in top_cand
        assert top_cand["opportunityType"] in ("TRIP_RECOVERY", "LIFT_OPTIMIZATION")
        assert top_cand["deferredProductionBpd"] > 0.0
        assert len(top_cand["recommendedAction"]) > 10


@pytest.mark.anyio
async def test_fetch_card_fleet_production_summary():
    """Real PostgreSQL test: fetch fleet-production-summary card and verify aggregates."""
    res = await fetch_card("GLOBAL", "fleet-production-summary")
    assert res["status"] == "OK"
    assert res["card_id"] == "fleet_production_summary"
    payload = res["payload"]

    assert payload["totalGrossLiquidBpd"] > 0.0
    assert payload["totalNetOilBopd"] > 0.0
    assert 0.0 <= payload["averageWaterCutPct"] <= 100.0
    assert payload["activeWells"] >= 0
    assert payload["downWells"] >= 0
    assert 0.0 <= payload["fleetAvailabilityPct"] <= 100.0


def test_visualization_planner_fleet_objectives():
    """Verify visualization planner selects new fleet cards for OP08, OP09, OP13."""
    # Force reload of registry
    _load_cards_registry(force_reload=True)

    # Sealed dummy pack with fleet tools
    pack = EvidencePack(
        run_id="run-vis-fleet",
        version=1,
        items=[
            EvidenceItem(
                evidence_id="EV-1",
                tool="get_fleet_kpi",
                source_domain="kpi",
                fetched_at="2026-10-05T12:00:00Z",
                payload={"total_production_bpd": 12000.0},
            ),
            EvidenceItem(
                evidence_id="EV-2",
                tool="get_fleet_health",
                source_domain="ml",
                fetched_at="2026-10-05T12:00:00Z",
                payload={"fleet_health_score": 85.0},
            ),
            EvidenceItem(
                evidence_id="EV-3",
                tool="get_fleet_events",
                source_domain="events",
                fetched_at="2026-10-05T12:00:00Z",
                payload={"events": []},
            ),
        ],
    )
    seal_res = seal(pack, required_tools=["get_fleet_kpi", "get_fleet_health", "get_fleet_events"])
    assert seal_res.status == "COMPLETE"

    # OP08
    spec_op08 = plan_visualization("OP08_FLEET_INVENTORY", pack)
    assert "fleet-health-table" in spec_op08.card_ids

    # OP09
    spec_op09 = plan_visualization("OP09_FLEET_PRODUCTION_OPTIMIZATION", pack)
    assert "fleet-opportunity-view" in spec_op09.card_ids
    assert "fleet-production-summary" in spec_op09.card_ids

    # OP13
    spec_op13 = plan_visualization("OP13_FLEET_EXECUTIVE_REPORT", pack)
    assert "fleet-production-summary" in spec_op13.card_ids
    assert "fleet-health-table" in spec_op13.card_ids
