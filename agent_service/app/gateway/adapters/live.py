"""
Live Telemetry & Asset Domain Adapter backed directly by PostgreSQL (esp_apm_db).
Queries opg_well_telemetry and asset_registry.
Zero HTTP dependency on :8090.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any, Optional
import httpx

from app.stores.postgres_client import get_db_cursor
from .common import AdapterError, get_well_id_variants


async def fetch_live_telemetry(well_id: str, client: Optional[httpx.AsyncClient] = None) -> dict[str, Any]:
    """Fetch latest telemetry packet from opg_well_telemetry."""
    def _query():
        variants = get_well_id_variants(well_id)
        with get_db_cursor() as cur:
            cur.execute("""
                SELECT well_id, asset_id, timestamp, intake_pressure_psi, discharge_pressure_psi,
                       motor_temperature_c, intake_temperature_c, flow_rate_bpd, frequency_hz,
                       motor_current_a, motor_voltage_v, vibration_g, whp_psi, flp_psi,
                       annulus_pressure_psi, water_cut_pct, gas_flow_mscfd, choke_size_pct,
                       operating_state, trip_cause, status, scenario, alarms, alerts
                FROM opg_well_telemetry
                WHERE well_id = ANY(%s) OR asset_id = ANY(%s)
                ORDER BY timestamp DESC
                LIMIT 1;
            """, (variants, variants))
            row = cur.fetchone()
            if not row:
                raise AdapterError(f"No telemetry data found for well {well_id}", status_code=404, code="NOT_FOUND")

            ts = row[2].isoformat() if hasattr(row[2], "isoformat") else str(row[2])
            meas = {
                "intake_pressure_psi": float(row[3]) if row[3] is not None else None,
                "discharge_pressure_psi": float(row[4]) if row[4] is not None else None,
                "motor_temperature_c": float(row[5]) if row[5] is not None else None,
                "intake_temperature_c": float(row[6]) if row[6] is not None else None,
                "flow_rate_bpd": float(row[7]) if row[7] is not None else None,
                "frequency_hz": float(row[8]) if row[8] is not None else None,
                "motor_current_a": float(row[9]) if row[9] is not None else None,
                "motor_voltage_v": float(row[10]) if row[10] is not None else None,
                "vibration_g": float(row[11]) if row[11] is not None else None,
                "whp_psi": float(row[12]) if row[12] is not None else None,
                "flp_psi": float(row[13]) if row[13] is not None else None,
                "annulus_pressure_psi": float(row[14]) if row[14] is not None else None,
                "water_cut_pct": float(row[15]) if row[15] is not None else None,
                "gas_flow_mscfd": float(row[16]) if row[16] is not None else None,
                "choke_size_pct": float(row[17]) if row[17] is not None else None,
            }
            return {
                "well_id": row[0] or well_id,
                "asset_id": row[1] or row[0] or well_id,
                "timestamp": ts,
                "measurements": meas,
                **meas,
                "operating_state": str(row[18] or "RUNNING"),
                "trip_cause": str(row[19] or ""),
                "status": str(row[20] or "NORMAL"),
                "scenario": str(row[21] or ""),
                "alarms": [a.strip() for a in str(row[22] or "").split(",") if a.strip()],
                "alerts": [a.strip() for a in str(row[23] or "").split(",") if a.strip()],
                "source": "POSTGRESQL",
            }

    try:
        return await asyncio.to_thread(_query)
    except AdapterError:
        raise
    except Exception as e:
        raise AdapterError(f"PostgreSQL fetch_live_telemetry failed: {e}", status_code=500, code="DB_QUERY_FAILED")


async def fetch_live_asset(well_id: str, client: Optional[httpx.AsyncClient] = None) -> dict[str, Any]:
    """Fetch well configuration and engineering limits from asset_registry."""
    def _query():
        variants = get_well_id_variants(well_id)
        with get_db_cursor() as cur:
            cur.execute("""
                SELECT well_id, cluster, pump_type, pump_stages, pump_depth_ft, bep_rate_bpd,
                       motor_kw, rated_amp_a, voltage_rating_v, frequency_nominal_hz,
                       casing_id_in, tubing_od_in, is_active, water_cut_baseline_pct,
                       pump_model_id, motor_hp, vsd_model, min_intake_warning_psi,
                       trip_intake_pressure_psi, max_motor_temp_c, max_vibration_g,
                       station_id, field_id
                FROM asset_registry
                WHERE well_id = ANY(%s)
                LIMIT 1;
            """, (variants,))
            row = cur.fetchone()
            if not row:
                raise AdapterError(f"Asset registry entry not found for well {well_id}", status_code=404, code="NOT_FOUND")

            return {
                "well_id": row[0] or well_id,
                "cluster": row[1] or "DEFAULT",
                "pump_type": row[2] or "CENTRIFUGAL_ESP",
                "pump_stages": int(row[3]) if row[3] is not None else 100,
                "pump_depth_ft": float(row[4]) if row[4] is not None else 5000.0,
                "bep_rate_bpd": float(row[5]) if row[5] is not None else 500.0,
                "motor_kw": float(row[6]) if row[6] is not None else 50.0,
                "rated_amp_a": float(row[7]) if row[7] is not None else 40.0,
                "voltage_rating_v": float(row[8]) if row[8] is not None else 1000.0,
                "frequency_nominal_hz": float(row[9]) if row[9] is not None else 50.0,
                "casing_id_in": float(row[10]) if row[10] is not None else 7.0,
                "tubing_od_in": float(row[11]) if row[11] is not None else 3.5,
                "is_active": bool(row[12]),
                "water_cut_baseline_pct": float(row[13]) if row[13] is not None else 0.0,
                "pump_model_id": row[14] or "PUMP-DEFAULT",
                "motor_hp": float(row[15]) if row[15] is not None else 65.0,
                "vsd_model": row[16] or "VSD-DEFAULT",
                "min_intake_warning_psi": float(row[17]) if row[17] is not None else 150.0,
                "trip_intake_pressure_psi": float(row[18]) if row[18] is not None else 80.0,
                "max_motor_temp_c": float(row[19]) if row[19] is not None else 130.0,
                "max_vibration_g": float(row[20]) if row[20] is not None else 3.0,
                "station_id": row[21] or "STATION-01",
                "field_id": row[22] or "FIELD-01",
                "source": "POSTGRESQL",
            }

    try:
        return await asyncio.to_thread(_query)
    except AdapterError:
        raise
    except Exception as e:
        raise AdapterError(f"PostgreSQL fetch_live_asset failed: {e}", status_code=500, code="DB_QUERY_FAILED")


async def fetch_live_vfm(well_id: str, client: Optional[httpx.AsyncClient] = None) -> dict[str, Any]:
    """Fetch Virtual Flow Meter production estimates from opg_well_telemetry."""
    def _query():
        variants = get_well_id_variants(well_id)
        with get_db_cursor() as cur:
            cur.execute("""
                SELECT well_id, timestamp, flow_rate_bpd, water_cut_pct, gas_flow_mscfd, choke_size_pct
                FROM opg_well_telemetry
                WHERE well_id = ANY(%s) OR asset_id = ANY(%s)
                ORDER BY timestamp DESC
                LIMIT 1;
            """, (variants, variants))
            row = cur.fetchone()
            if not row:
                raise AdapterError(f"No VFM data found for well {well_id}", status_code=404, code="NOT_FOUND")

            liq_rate = float(row[2]) if row[2] is not None else 0.0
            wc = float(row[3]) if row[3] is not None else 0.0
            oil_rate = liq_rate * (1.0 - (wc / 100.0))
            water_rate = liq_rate * (wc / 100.0)

            ts = row[1].isoformat() if hasattr(row[1], "isoformat") else str(row[1])
            return {
                "well_id": row[0] or well_id,
                "timestamp": ts,
                "liquid_rate_bpd": liq_rate,
                "oil_rate_bopd": round(oil_rate, 2),
                "water_rate_bwpd": round(water_rate, 2),
                "water_cut_pct": wc,
                "gas_rate_mscfd": float(row[4]) if row[4] is not None else 0.0,
                "choke_opening_pct": float(row[5]) if row[5] is not None else 100.0,
                "confidence": 0.95,
                "source": "POSTGRESQL",
            }

    try:
        return await asyncio.to_thread(_query)
    except AdapterError:
        raise
    except Exception as e:
        raise AdapterError(f"PostgreSQL fetch_live_vfm failed: {e}", status_code=500, code="DB_QUERY_FAILED")


async def fetch_live_wells(client: Optional[httpx.AsyncClient] = None) -> dict[str, Any]:
    """Fetch active well inventory from live telemetry."""
    def _query():
        with get_db_cursor() as cur:
            cur.execute("""
                WITH latest_state AS (
                    SELECT DISTINCT ON (well_id) well_id, operating_state
                    FROM opg_well_telemetry
                    ORDER BY well_id, timestamp DESC
                )
                SELECT l.well_id, COALESCE(a.cluster, 'Field-1'), (LOWER(l.operating_state) = 'running') AS is_running
                FROM latest_state l
                LEFT JOIN asset_registry a ON a.well_id = l.well_id
                ORDER BY l.well_id;
            """)
            rows = cur.fetchall()
            wells = [r[0] for r in rows]
            active = [r[0] for r in rows if r[2]]
            return {
                "total_wells": len(wells),
                "wells": wells,
                "active_wells": active,
                "running_count": len(active),
                "down_count": len(wells) - len(active),
                "source": "POSTGRESQL",
            }
    try:
        return await asyncio.to_thread(_query)
    except Exception as e:
        raise AdapterError(f"PostgreSQL fetch_live_wells failed: {e}", status_code=500, code="DB_QUERY_FAILED")


async def check_live_health(client: Optional[httpx.AsyncClient] = None) -> dict[str, Any]:
    """Check telemetry table liveness."""
    def _query():
        with get_db_cursor() as cur:
            cur.execute("SELECT 1 FROM opg_well_telemetry LIMIT 1;")
            return {"status": "HEALTHY", "source": "POSTGRESQL"}
    try:
        return await asyncio.to_thread(_query)
    except Exception as e:
        return {"status": "DEGRADED", "error": str(e), "source": "POSTGRESQL"}
