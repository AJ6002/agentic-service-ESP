"""
KPI Domain Adapter backed directly by PostgreSQL (esp_apm_db).
Queries telemetry, assets, and ML assessments to calculate well and fleet operational KPIs.
Zero HTTP dependency on :8090.
"""

from __future__ import annotations

import asyncio
from typing import Any, Optional
import httpx

from app.stores.postgres_client import get_db_cursor
from .common import AdapterError, get_well_id_variants


async def fetch_kpi(well_id: str, client: Optional[httpx.AsyncClient] = None) -> dict[str, Any]:
    """Fetch aggregated KPI card bundle for a well."""
    def _query():
        variants = get_well_id_variants(well_id)
        with get_db_cursor() as cur:
            # 1. Telemetry metrics
            cur.execute("""
                SELECT flow_rate_bpd, water_cut_pct, motor_current_a, motor_voltage_v,
                       intake_pressure_psi, discharge_pressure_psi, motor_temperature_c,
                       vibration_g, frequency_hz, timestamp, operating_state
                FROM opg_well_telemetry
                WHERE well_id = ANY(%s) OR asset_id = ANY(%s)
                ORDER BY timestamp DESC
                LIMIT 1;
            """, (variants, variants))
            telem = cur.fetchone()
            if not telem:
                raise AdapterError(f"No KPI telemetry found for well {well_id}", status_code=404, code="NOT_FOUND")

            # 2. Asset limits
            cur.execute("""
                SELECT rated_amp_a, max_motor_temp_c, trip_intake_pressure_psi, bep_rate_bpd
                FROM asset_registry
                WHERE well_id = ANY(%s)
                LIMIT 1;
            """, (variants,))
            asset = cur.fetchone()
            rated_amps = float(asset[0]) if asset and asset[0] else 40.0
            bep_rate = float(asset[3]) if asset and asset[3] else 500.0

            # 3. ML assessment
            cur.execute("""
                SELECT overall_status, fault_name, anomaly_score, rul_hours
                FROM esp_unified_assessments
                WHERE well_id = ANY(%s) OR esp_id = ANY(%s)
                ORDER BY timestamp DESC
                LIMIT 1;
            """, (variants, variants))
            ml_row = cur.fetchone()

            liq_rate = float(telem[0]) if telem[0] is not None else 0.0
            wc = float(telem[1]) if telem[1] is not None else 0.0
            oil_rate = round(liq_rate * (1.0 - (wc / 100.0)), 2)
            cur_amps = float(telem[2]) if telem[2] is not None else 0.0
            motor_load_pct = round((cur_amps / rated_amps) * 100.0, 1) if rated_amps > 0 else 80.0

            overall_st = str(ml_row[0] or "HEALTHY") if ml_row else "HEALTHY"
            if "CRITICAL" in overall_st.upper():
                health_score = 42.0
            elif "WARN" in overall_st.upper():
                health_score = 68.0
            else:
                health_score = 92.0

            return {
                "well_id": well_id,
                "status": "OK",
                "gross_liquid_rate_bpd": liq_rate,
                "net_oil_rate_bopd": oil_rate,
                "water_cut_pct": wc,
                "motor_load_pct": motor_load_pct,
                "health_score": health_score,
                "intake_pressure_psi": float(telem[4]) if telem[4] is not None else 400.0,
                "discharge_pressure_psi": float(telem[5]) if telem[5] is not None else 1800.0,
                "motor_temp_c": float(telem[6]) if telem[6] is not None else 85.0,
                "vibration_g": float(telem[7]) if telem[7] is not None else 0.45,
                "frequency_hz": float(telem[8]) if telem[8] is not None else 50.0,
                "operating_state": str(telem[10] or "RUNNING"),
                "source": "POSTGRESQL",
            }

    try:
        return await asyncio.to_thread(_query)
    except AdapterError:
        raise
    except Exception as e:
        raise AdapterError(f"PostgreSQL fetch_kpi failed: {e}", status_code=500, code="DB_QUERY_FAILED")


async def fetch_fleet_kpi(client: Optional[httpx.AsyncClient] = None) -> dict[str, Any]:
    """Fetch field-level fleet KPI summary aggregated directly from PostgreSQL."""
    def _query():
        with get_db_cursor() as cur:
            cur.execute("""
                WITH latest_telem AS (
                    SELECT DISTINCT ON (well_id) well_id, flow_rate_bpd, operating_state
                    FROM opg_well_telemetry
                    ORDER BY well_id, timestamp DESC
                ),
                latest_ml AS (
                    SELECT DISTINCT ON (well_id) well_id, overall_status
                    FROM esp_unified_assessments
                    ORDER BY well_id, timestamp DESC
                )
                SELECT 
                    COUNT(t.well_id) AS total_wells,
                    COUNT(t.well_id) FILTER (WHERE LOWER(t.operating_state) = 'running') AS running_wells,
                    COUNT(t.well_id) FILTER (WHERE LOWER(t.operating_state) != 'running') AS down_wells,
                    COALESCE(SUM(t.flow_rate_bpd), 0.0) AS total_production_bpd,
                    COALESCE(AVG(
                        CASE 
                            WHEN UPPER(m.overall_status) LIKE '%CRITICAL%' OR UPPER(m.overall_status) LIKE '%ALARM%' THEN 42.0
                            WHEN UPPER(m.overall_status) LIKE '%WARN%' OR UPPER(m.overall_status) LIKE '%DEGRADED%' THEN 68.0
                            ELSE 92.0
                        END
                    ), 90.0) AS avg_health_score
                FROM latest_telem t
                LEFT JOIN latest_ml m ON m.well_id = t.well_id;
            """)
            row = cur.fetchone()
            total_wells = int(row[0]) if row and row[0] is not None else 0
            running_wells = int(row[1]) if row and row[1] is not None else 0
            down_wells = int(row[2]) if row and row[2] is not None else 0
            total_prod = round(float(row[3]), 2) if row and row[3] is not None else 0.0
            avg_health = round(float(row[4]), 1) if row and row[4] is not None else 90.0

            return {
                "status": "OK",
                "total_wells": total_wells,
                "running_wells": running_wells,
                "down_wells": down_wells,
                "fleet_health_estimate": avg_health,
                "fleet_health_score": avg_health,  # backward compatibility
                "method": "bucketed_status",
                "total_production_bpd": total_prod,
                "source": "POSTGRESQL",
            }

    try:
        return await asyncio.to_thread(_query)
    except Exception as e:
        raise AdapterError(f"PostgreSQL fetch_fleet_kpi failed: {e}", status_code=500, code="DB_QUERY_FAILED")


async def fetch_fleet_health(client: Optional[httpx.AsyncClient] = None) -> dict[str, Any]:
    """Fetch per-well health ranking across the fleet."""
    def _query():
        with get_db_cursor() as cur:
            cur.execute("""
                WITH latest_ml AS (
                    SELECT DISTINCT ON (well_id) well_id, overall_status, anomaly_score, timestamp
                    FROM esp_unified_assessments
                    ORDER BY well_id, timestamp DESC
                )
                SELECT 
                    well_id,
                    CASE 
                        WHEN UPPER(overall_status) LIKE '%CRITICAL%' OR UPPER(overall_status) LIKE '%ALARM%' THEN 42.0
                        WHEN UPPER(overall_status) LIKE '%WARN%' OR UPPER(overall_status) LIKE '%DEGRADED%' THEN 68.0
                        ELSE 92.0
                    END AS health_score,
                    CASE 
                        WHEN UPPER(overall_status) LIKE '%CRITICAL%' OR UPPER(overall_status) LIKE '%ALARM%' THEN 'CRITICAL'
                        WHEN UPPER(overall_status) LIKE '%WARN%' OR UPPER(overall_status) LIKE '%DEGRADED%' THEN 'DEGRADED'
                        ELSE 'HEALTHY'
                    END AS band
                FROM latest_ml
                ORDER BY health_score ASC, well_id ASC;
            """)
            rows = cur.fetchall()
            wells = []
            for r in rows:
                wells.append({
                    "well_id": str(r[0]),
                    "health_score": float(r[1]),
                    "band": str(r[2]),
                })

            worst = wells[0]["well_id"] if wells else None
            best = wells[-1]["well_id"] if wells else None

            return {
                "status": "OK",
                "wells": wells,
                "count": len(wells),
                "worst": worst,
                "best": best,
                "source": "POSTGRESQL",
            }

    try:
        return await asyncio.to_thread(_query)
    except Exception as e:
        raise AdapterError(f"PostgreSQL fetch_fleet_health failed: {e}", status_code=500, code="DB_QUERY_FAILED")

