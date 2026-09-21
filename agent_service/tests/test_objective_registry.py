from app.routing.objective_registry import load_objective_registry, get_objective, list_objectives

def test_load_objective_registry():
    registry = load_objective_registry(force_reload=True)
    assert len(registry) >= 6
    assert "OP07_GENERAL_INQUIRY" in registry
    assert "OP01_CURRENT_STATUS" in registry
    assert "OP03_FAULT_DIAGNOSIS" in registry
    assert "OP04_HEALTH_ASSESSMENT" in registry
    assert "OP05_EARLY_WARNING" in registry
    assert "OP14_OPERATIONAL_HISTORY" in registry

def test_get_objective_details():
    op03 = get_objective("OP03_FAULT_DIAGNOSIS")
    assert op03 is not None
    assert op03.tool == "diagnose_fault"
    assert op03.safety_class == "READ"
    assert op03.scope == "ASSET"
    assert "get_live_telemetry" in op03.required_evidence

    # OP04
    op04 = get_objective("OP04")
    assert op04 is not None
    assert op04.objective_id == "OP04_HEALTH_ASSESSMENT"
    assert op04.tool == "get_health_index"
    assert "get_historian_aggregates" in op04.required_evidence
    assert "get_health_index" in op04.required_evidence

    # OP05
    op05 = get_objective("OP05")
    assert op05 is not None
    assert op05.objective_id == "OP05_EARLY_WARNING"
    assert op05.tool == "get_anomaly"
    assert "get_historian_aggregates" in op05.required_evidence
    assert "get_anomaly" in op05.required_evidence

    # OP14
    op14 = get_objective("OP14")
    assert op14 is not None
    assert op14.objective_id == "OP14_OPERATIONAL_HISTORY"
    assert op14.tool == "get_historian_window"
    assert "get_historian_aggregates" in op14.required_evidence
    assert "get_events" in op14.required_evidence
