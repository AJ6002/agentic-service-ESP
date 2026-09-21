"""
ML Model Mock API Service (esp-ml-api :8082)
Grounded in dependency_detail.md & ESP_Agentic_ML_Team_Dependencies_and_API_PreRequisites.md

Implements the ML Team's v2.0.0 Dual-Tier Inference Engine contract:
  - POST /api/v1/esps/{asset_id}/predict
  - GET  /api/v1/esps/{asset_id}/history
  - GET  /api/v1/models/health
  - GET  /api/v1/esps/assets
"""

import time
import logging
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, Query, status
import uvicorn

from src.schemas.contracts import MLContractV2Payload, TriggeredLimitPayload

logger = logging.getLogger(__name__)

app = FastAPI(
    title="ESP ML Model Mock API Service",
    description="ML Team v2.0.0 Dual-Tier Inference Engine Service (:8082)",
    version="2.0.0",
)


# Default Sample Fixtures (§3 of dependency_detail.md)
_FIXTURES: Dict[str, MLContractV2Payload] = {
    "FS-010": MLContractV2Payload(
        asset_id="FS-010",
        well_id="OPG-W010",
        timestamp=int(time.time()),
        model_id="esp-hybrid-dual-tier",
        model_version="v2.0.0",
        feature_version="phys-v2.1",
        status="VALID",
        state="FAULT",
        fault_classification="Bearing Degradation",
        confidence_score=0.969,
        is_anomaly=True,
        anomaly_score=0.615,
        contributors=["R_MOTOR_TEMP", "R_VIBRATION_X", "thermal_gradient_c"],
        triggered_limits=[
            TriggeredLimitPayload(tag="R_MOTOR_TEMP", value=115.0, limit=100.0, type="HIGH"),
            TriggeredLimitPayload(tag="R_VIBRATION_X", value=0.48, limit=0.30, type="HIGH"),
        ],
        telemetry_received={
            "R_INTAKE_PRESS": 1650.0,
            "R_DISCH_PRESS": 2400.0,
            "R_MOTOR_TEMP": 115.0,
            "R_VIBRATION_X": 0.48,
            "R_DRV_CURR_AVG": 45.0,
        },
    ),
    "FS-031": MLContractV2Payload(
        asset_id="FS-031",
        well_id="Well-FS-031",
        timestamp=int(time.time()),
        model_id="esp-hybrid-dual-tier",
        model_version="v2.0.0",
        feature_version="phys-v2.1",
        status="VALID",
        state="FAULT",
        fault_classification="Intake Gas Interference",
        confidence_score=0.88,
        is_anomaly=True,
        anomaly_score=0.72,
        contributors=["intake_pressure", "drive_current", "liquid_rate"],
        triggered_limits=[
            TriggeredLimitPayload(tag="intake_pressure", value=236.5, limit=300.0, type="LOW"),
        ],
        telemetry_received={
            "liquid_rate": 735.7,
            "intake_pressure": 236.5,
            "discharge_pressure": 1883.7,
            "motor_temperature": 79.67,
        },
    ),
    "FS-OFFLINE": MLContractV2Payload(
        asset_id="FS-OFFLINE",
        well_id="Well-FS-OFFLINE",
        timestamp=int(time.time()),
        model_id="esp-hybrid-dual-tier",
        model_version="v2.0.0",
        feature_version="phys-v2.1",
        status="UNAVAILABLE",
        state="DEGRADED",
        fault_classification="UNAVAILABLE",
        confidence_score=None,
        is_anomaly=False,
        anomaly_score=0.0,
        reason="SENSOR_TELEMETRY_MISSING",
        last_valid_timestamp=int(time.time()) - 300,
    ),
}


@app.get("/health", tags=["system"])
@app.get("/api/v1/models/health", tags=["system"])
def health():
    """Model Health & Registry Endpoint (§2 of dependency_detail.md)."""
    return {
        "status": "UP",
        "service": "esp-ml-api",
        "model_id": "esp-hybrid-dual-tier",
        "model_version": "v2.0.0",
        "feature_version": "phys-v2.1",
        "loaded_models": ["XGBoost-Fault-Classifier-v2", "IsolationForest-Anomaly-v2"],
        "timestamp": int(time.time()),
    }


@app.get("/api/v1/esps/assets", tags=["metadata"])
def list_monitored_assets():
    """Asset Registry & Metadata Endpoint."""
    return {"assets": list(_FIXTURES.keys())}


@app.post("/api/v1/esps/{asset_id}/predict", tags=["inference"])
def predict_asset_state(asset_id: str, telemetry_override: Optional[Dict[str, float]] = None):
    """
    Live Real-Time Prediction API (§2 & §3 of dependency_detail.md).
    Returns contract v2.0.0 prediction payload.
    """
    if asset_id not in _FIXTURES:
        # Return generic valid prediction for unlisted asset
        return MLContractV2Payload(
            asset_id=asset_id,
            well_id=f"WELL-{asset_id}",
            timestamp=int(time.time()),
            fault_classification="Normal Operations",
            confidence_score=0.95,
            is_anomaly=False,
            anomaly_score=0.10,
        )

    fixture = _FIXTURES[asset_id]
    fixture.timestamp = int(time.time())
    if telemetry_override:
        fixture.telemetry_received.update(telemetry_override)
    return fixture


@app.get("/api/v1/esps/{asset_id}/history", tags=["history"])
def get_asset_model_history(asset_id: str, range_str: str = Query("6h", alias="range")):
    """
    Historical Model Query API (§2 of dependency_detail.md).
    Returns historical predictions for RCA trend queries.
    """
    if asset_id not in _FIXTURES:
        raise HTTPException(status_code=404, detail=f"No model history for asset '{asset_id}'.")

    base = _FIXTURES[asset_id]
    now = int(time.time())

    # Generate 6 historical prediction steps
    history = []
    for i in range(6, 0, -1):
        step_time = now - (i * 3600)
        history.append({
            "asset_id": asset_id,
            "timestamp": step_time,
            "model_version": base.model_version,
            "fault_classification": base.fault_classification,
            "confidence_score": round(max(0.5, base.confidence_score - (i * 0.03)), 3),
            "is_anomaly": base.is_anomaly,
            "anomaly_score": round(max(0.1, base.anomaly_score - (i * 0.05)), 3),
        })

    return {
        "asset_id": asset_id,
        "range": range_str,
        "history_count": len(history),
        "history": history,
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8082)
