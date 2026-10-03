"""
ML Diagnostics Domain Adapter backed directly by PostgreSQL (esp_apm_db).
Queries esp_unified_assessments table for multi-model health scoring, fault classifications,
anomaly metrics, RUL forecasts, and SHAP explainability.
Zero HTTP dependency on :8090.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any, Optional
import httpx

from app.stores.postgres_client import get_db_cursor
from .common import AdapterError, get_well_id_variants, build_temporal_meta


async def fetch_ml_fault(well_id: str, client: Optional[httpx.AsyncClient] = None) -> dict[str, Any]:
    """Fetch latest fault diagnostic classification from esp_unified_assessments."""
    def _query():
        variants = get_well_id_variants(well_id)
        with get_db_cursor() as cur:
            cur.execute("""
                SELECT timestamp, overall_status, fault_status, fault_name, fault_probability,
                       confidence_level, primary_risk_fault, max_risk_probability, top_reasons,
                       operator_action, technical_explanation, parameter_evaluations
                FROM esp_unified_assessments
                WHERE well_id = ANY(%s) OR esp_id = ANY(%s)
                ORDER BY timestamp DESC
                LIMIT 1;
            """, (variants, variants))
            row = cur.fetchone()
            if not row:
                raise AdapterError(f"No ML assessment found for well {well_id}", status_code=404, code="NOT_FOUND")

            ts = row[0].isoformat() if hasattr(row[0], "isoformat") else str(row[0])
            fault_nm = row[3] or "Healthy Operation"
            fault_cls = fault_nm.upper().replace(" ", "_")

            return {
                "well_id": well_id,
                "timestamp": ts,
                "overall_status": str(row[1] or "HEALTHY"),
                "fault_status": str(row[2] or "NORMAL"),
                "fault_name": fault_nm,
                "fault_class": fault_cls,
                "probability": float(row[4]) if row[4] is not None else 0.95,
                "confidence": str(row[5] or "HIGH"),
                "primary_risk": str(row[6] or fault_nm),
                "top_drivers": row[8] or [],
                "action": str(row[9] or "Maintain routine surveillance."),
                "explanation": str(row[10] or "Operating conditions are steady."),
                "source": "POSTGRESQL",
            }

    try:
        return await asyncio.to_thread(_query)
    except AdapterError:
        raise
    except Exception as e:
        raise AdapterError(f"PostgreSQL fetch_ml_fault failed: {e}", status_code=500, code="DB_QUERY_FAILED")


async def fetch_ml_health(well_id: str, client: Optional[httpx.AsyncClient] = None) -> dict[str, Any]:
    """Fetch composite health index & RUL prediction from esp_unified_assessments."""
    def _query():
        variants = get_well_id_variants(well_id)
        with get_db_cursor() as cur:
            cur.execute("""
                SELECT timestamp, overall_status, rule_status, rul_status, rul_hours,
                       rul_lower_hours, rul_upper_hours, anomaly_score, data_quality
                FROM esp_unified_assessments
                WHERE well_id = ANY(%s) OR esp_id = ANY(%s)
                ORDER BY timestamp DESC
                LIMIT 1;
            """, (variants, variants))
            row = cur.fetchone()
            if not row:
                raise AdapterError(f"No ML health assessment found for well {well_id}", status_code=404, code="NOT_FOUND")

            ts = row[0].isoformat() if hasattr(row[0], "isoformat") else str(row[0])
            st = str(row[1] or "HEALTHY").upper()

            # Map status string to health score
            if "CRITICAL" in st or "ALARM" in st:
                h_score = 42.0
                band = "CRITICAL"
            elif "WARN" in st or "DEGRADED" in st:
                h_score = 68.0
                band = "DEGRADED"
            else:
                h_score = 92.0
                band = "HEALTHY"

            rul_hrs = float(row[4]) if row[4] is not None else 4320.0

            return {
                "well_id": well_id,
                "timestamp": ts,
                "health_score": h_score,
                "health_band": band,
                "rul_hours": rul_hrs,
                "rul_days": round(rul_hrs / 24.0, 1),
                "rul_status": str(row[3] or "NOMINAL"),
                "anomaly_score": float(row[7]) if row[7] is not None else 0.0,
                "data_quality": str(row[8] or "EXCELLENT"),
                "source": "POSTGRESQL",
            }

    try:
        return await asyncio.to_thread(_query)
    except AdapterError:
        raise
    except Exception as e:
        raise AdapterError(f"PostgreSQL fetch_ml_health failed: {e}", status_code=500, code="DB_QUERY_FAILED")


async def fetch_ml_anomaly(well_id: str, client: Optional[httpx.AsyncClient] = None) -> dict[str, Any]:
    """Fetch ML anomaly detection score from esp_unified_assessments."""
    def _query():
        variants = get_well_id_variants(well_id)
        with get_db_cursor() as cur:
            cur.execute("""
                SELECT timestamp, anomaly_score, anomaly_status, top_reasons
                FROM esp_unified_assessments
                WHERE well_id = ANY(%s) OR esp_id = ANY(%s)
                ORDER BY timestamp DESC
                LIMIT 1;
            """, (variants, variants))
            row = cur.fetchone()
            if not row:
                raise AdapterError(f"No anomaly assessment found for well {well_id}", status_code=404, code="NOT_FOUND")

            ts = row[0].isoformat() if hasattr(row[0], "isoformat") else str(row[0])
            score = float(row[1]) if row[1] is not None else 0.0
            return {
                "well_id": well_id,
                "timestamp": ts,
                "anomaly_score": score,
                "is_anomalous": score >= 0.85,
                "anomaly_status": str(row[2] or "NORMAL"),
                "top_reasons": row[3] or [],
                "source": "POSTGRESQL",
            }

    try:
        return await asyncio.to_thread(_query)
    except AdapterError:
        raise
    except Exception as e:
        raise AdapterError(f"PostgreSQL fetch_ml_anomaly failed: {e}", status_code=500, code="DB_QUERY_FAILED")


async def fetch_ml_explain(well_id: str, output: str = "fault", client: Optional[httpx.AsyncClient] = None) -> dict[str, Any]:
    """Fetch SHAP explainability drivers from esp_unified_assessments."""
    def _query():
        variants = get_well_id_variants(well_id)
        with get_db_cursor() as cur:
            cur.execute("""
                SELECT timestamp, fault_name, shap_contributions, top_reasons, technical_explanation
                FROM esp_unified_assessments
                WHERE well_id = ANY(%s) OR esp_id = ANY(%s)
                ORDER BY timestamp DESC
                LIMIT 1;
            """, (variants, variants))
            row = cur.fetchone()
            if not row:
                raise AdapterError(f"No explainability record found for well {well_id}", status_code=404, code="NOT_FOUND")

            ts = row[0].isoformat() if hasattr(row[0], "isoformat") else str(row[0])
            return {
                "well_id": well_id,
                "timestamp": ts,
                "output_type": output,
                "fault_name": row[1] or "Healthy Operation",
                "shap_values": row[2] or {},
                "top_drivers": row[3] or [],
                "explanation": str(row[4] or "Operating conditions are nominal."),
                "source": "POSTGRESQL",
            }

    try:
        return await asyncio.to_thread(_query)
    except AdapterError:
        raise
    except Exception as e:
        raise AdapterError(f"PostgreSQL fetch_ml_explain failed: {e}", status_code=500, code="DB_QUERY_FAILED")


async def query_mlresults(
    well_id: Optional[str] = None,
    limit: Optional[int] = 50,
    anomalous_only: Optional[bool] = False,
    client: Optional[httpx.AsyncClient] = None,
) -> dict[str, Any]:
    """Batch query esp_unified_assessments."""
    def _query():
        with get_db_cursor() as cur:
            if well_id:
                variants = get_well_id_variants(well_id)
                if anomalous_only:
                    cur.execute("""
                        SELECT timestamp, well_id, overall_status, fault_name, fault_probability, anomaly_score
                        FROM esp_unified_assessments
                        WHERE (well_id = ANY(%s) OR esp_id = ANY(%s)) AND anomaly_score >= 0.85
                        ORDER BY timestamp DESC
                        LIMIT %s;
                    """, (variants, variants, limit or 50))
                else:
                    cur.execute("""
                        SELECT timestamp, well_id, overall_status, fault_name, fault_probability, anomaly_score
                        FROM esp_unified_assessments
                        WHERE well_id = ANY(%s) OR esp_id = ANY(%s)
                        ORDER BY timestamp DESC
                        LIMIT %s;
                    """, (variants, variants, limit or 50))
            else:
                cur.execute("""
                    SELECT timestamp, well_id, overall_status, fault_name, fault_probability, anomaly_score
                    FROM esp_unified_assessments
                    ORDER BY timestamp DESC
                    LIMIT %s;
                """, (limit or 50,))

            rows = cur.fetchall()
            results = []
            for r in rows:
                ts = r[0].isoformat() if hasattr(r[0], "isoformat") else str(r[0])
                results.append({
                    "timestamp": ts,
                    "well_id": r[1],
                    "overall_status": r[2],
                    "fault_name": r[3],
                    "fault_probability": float(r[4]) if r[4] is not None else None,
                    "anomaly_score": float(r[5]) if r[5] is not None else None,
                })
            return {"results": results, "count": len(results), "source": "POSTGRESQL"}

    try:
        return await asyncio.to_thread(_query)
    except Exception as e:
        raise AdapterError(f"PostgreSQL query_mlresults failed: {e}", status_code=500, code="DB_QUERY_FAILED")


async def check_ml_health(client: Optional[httpx.AsyncClient] = None) -> dict[str, Any]:
    """Check ML assessment table liveness."""
    def _query():
        with get_db_cursor() as cur:
            cur.execute("SELECT 1 FROM esp_unified_assessments LIMIT 1;")
            return {"status": "HEALTHY", "source": "POSTGRESQL"}
    try:
        return await asyncio.to_thread(_query)
    except Exception as e:
        return {"status": "DEGRADED", "error": str(e), "source": "POSTGRESQL"}
