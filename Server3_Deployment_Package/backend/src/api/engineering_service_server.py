"""
Standalone ESP Engineering REST API Service (esp-engineering-service :8083)
Grounded in ESP_APM_Engineering_Service_Architecture_Granular_Design.docx §5, §46
"""

import time
import logging
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, status
import uvicorn

from src.schemas.engineering_contracts import (
    CalculationRequest, CalculationResult, CalculationBatchRequest, CalculationBatchResponse
)
from src.services.engineering.engine import EngineeringCalculationEngine
from src.services.engineering.calculation_registry import CalculationRegistryLoader

logger = logging.getLogger(__name__)

app = FastAPI(
    title="ESP Engineering Service",
    description="Deterministic Calculation Authority for ESP Agentic APM Platform (:8083)",
    version="1.0.0"
)

engine = EngineeringCalculationEngine()


@app.get("/health", status_code=status.HTTP_200_OK)
@app.get("/api/v1/engineering/health", status_code=status.HTTP_200_OK)
def get_service_health():
    """System health check & registry status endpoint"""
    return {
        "status": "HEALTHY",
        "service": "esp-engineering-service",
        "port": 8083,
        "version": "1.0.0",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }


@app.get("/api/v1/engineering/registry", response_model=Dict[str, Any])
def get_calculation_registry():
    """GET /api/v1/engineering/registry - Exposes authoritative calculation catalogue"""
    defs = CalculationRegistryLoader.list_all()
    return {
        "total_calculations": len(defs),
        "catalogue": {cid: cdef.model_dump() for cid, cdef in defs.items()}
    }


@app.post("/api/v1/engineering/calculate", response_model=CalculationResult)
def execute_single_calculation(req: CalculationRequest):
    """
    POST /api/v1/engineering/calculate
    Executes a single deterministic calculation (e.g. A1, A2, A4, A5, C2, F1, B1, E1).
    Fails closed if required parameters are missing.
    """
    try:
        return engine.execute(req)
    except Exception as e:
        logger.error(f"Error executing calculation {req.calculation_id} for asset {req.asset_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/engineering/batch", response_model=CalculationBatchResponse)
def execute_batch_calculations(batch_req: CalculationBatchRequest):
    """
    POST /api/v1/engineering/batch
    Executes a sequence of dependent calculations with dynamic output cascading.
    """
    try:
        return engine.execute_batch(batch_req)
    except Exception as e:
        logger.error(f"Error executing calculation batch for asset {batch_req.asset_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8083)
