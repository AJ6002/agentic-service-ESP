# CCED ESP Normalized Database — Async Live Writer
# ===================================================
# Receives unlabelled_batch dicts from mqtt_collector._batch_writer_loop()
# and writes pre-computed normalized rows to cced_esp/data/normalized.db.
# The WellCalibrationRegistry is loaded ONCE at startup and kept in RAM.
# Normalization of a 200-record batch takes <0.5ms regardless of batch size.

import os
import sys
import re
import logging
import aiosqlite
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger("opg.normalized_db")

# ── Import calibration registry from code/models ─────────────────────────────
_WORKSPACE_ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
_CODE_DIR = os.path.join(_WORKSPACE_ROOT, "code")
for p in [_CODE_DIR, _WORKSPACE_ROOT]:
    if p not in sys.path:
        sys.path.append(p)

try:
    from models.calibration_registry import WellCalibrationRegistry, STANDARD_SENSORS
    _REGISTRY_AVAILABLE = True
except ImportError as e:
    logger.warning(f"[normalized_db] Could not import WellCalibrationRegistry: {e} — live normalization disabled")
    _REGISTRY_AVAILABLE = False
    WellCalibrationRegistry = None
    STANDARD_SENSORS = []

INSERT_NORM_SQL = """
INSERT INTO opg_normalized_telemetry (
    raw_id, timestamp, Wells, Cluster, Source_File,
    [Inp bar/psi], [Int temp °C], [Motor temp °C], [Disch pr. Bar/psi],
    [Vibration G's-Vx], [Leak Current Ct], [Volt], [VSD Amps/Load],
    [Frequency], [DHG Current], [WHP (PSI)], [FLP (PSI)], [AP (PSI)],
    [VFD STS], VFD_STS_Binary,
    Delta_P_PSI, Torque_Proxy_A_Hz, Power_kVA, Thermal_Elevation_C,
    norm_Inp_bar_psi, norm_Int_temp_C, norm_Motor_temp_C, norm_Disch_pr_Bar_psi,
    norm_Vibration_G_s_Vx, norm_Leak_Current_Ct, norm_Volt, norm_VSD_Amps_Load,
    norm_Frequency, norm_DHG_Current, norm_WHP_PSI, norm_FLP_PSI, norm_AP_PSI,
    norm_Delta_P_PSI, norm_Torque_Proxy_A_Hz, norm_Power_kVA, norm_Thermal_Elevation_C
) VALUES (
    ?, ?, ?, ?, ?,
    ?, ?, ?, ?,
    ?, ?, ?, ?,
    ?, ?, ?, ?, ?,
    ?, ?,
    ?, ?, ?, ?,
    ?, ?, ?, ?,
    ?, ?, ?, ?,
    ?, ?, ?, ?, ?,
    ?, ?, ?, ?
)
"""


def _norm(val: float, p_min: float, p_max: float) -> float:
    if p_max <= p_min:
        return 0.0
    return round(float(max(0.0, min(1.0, (val - p_min) / (p_max - p_min)))), 6)


def _get_sensor_bounds(sensor_name: str, st: Dict[str, Any]) -> Tuple[float, float]:
    p_min = float(st.get("min", 0.0))
    p_max = float(st.get("max", 1.0))
    p10 = float(st.get("p10", p_min))
    p90 = float(st.get("p90", p_max))
    if p_min < -100.0 or p_max > 50000.0 or p_min >= p_max:
        if p90 > p10:
            p_min = max(0.0, p10 - 0.5 * (p90 - p10))
            p_max = p90 + 0.5 * (p90 - p10)
        else:
            p_min = 0.0
            p_max = max(1.0, float(st.get("median", 1.0)) * 2.0)
    return round(p_min, 2), round(p_max, 2)


def _physics_bounds(sb: Dict[str, Tuple[float, float]]) -> Dict[str, Tuple[float, float]]:
    inp_min, inp_max = sb.get("Inp bar/psi", (100.0, 1000.0))
    disch_min, disch_max = sb.get("Disch pr. Bar/psi", (800.0, 3500.0))
    amps_min, amps_max = sb.get("VSD Amps/Load", (5.0, 50.0))
    volt_min, volt_max = sb.get("Volt", (400.0, 1500.0))
    freq_min, freq_max = sb.get("Frequency", (30.0, 65.0))
    freq_min = max(10.0, freq_min)
    mtemp_min, mtemp_max = sb.get("Motor temp \u00b0C", (40.0, 130.0))
    itemp_min, itemp_max = sb.get("Int temp \u00b0C", (30.0, 90.0))
    dp_min = max(0.0, disch_min - inp_max)
    dp_max = max(dp_min + 10.0, disch_max - inp_min)
    tq_min = round(amps_min / max(1.0, freq_max), 3)
    tq_max = round(max(tq_min + 0.1, amps_max / max(1.0, freq_min)), 3)
    p_min = round((volt_min * amps_min * 1.732) / 1000.0, 2)
    p_max = round(max(p_min + 1.0, (volt_max * amps_max * 1.732) / 1000.0), 2)
    te_min = max(0.0, mtemp_min - itemp_max)
    te_max = max(te_min + 5.0, mtemp_max - itemp_min)
    return {
        "Delta_P_PSI": (dp_min, dp_max),
        "Torque_Proxy_A_Hz": (tq_min, tq_max),
        "Power_kVA": (p_min, p_max),
        "Thermal_Elevation_C": (te_min, te_max)
    }


class NormalizedDatabase:
    """
    Async writer for cced_esp/data/normalized.db.
    Loaded once by mqtt_collector at startup; registry stays warm in RAM.
    insert_batch() is called in lockstep with unlabelled_db.insert_telemetry_batch().
    """

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._registry: Optional[Any] = None
        # Per-well cached bounds: {well_id: {sensor_bounds, phys_bounds, sensors_prof, cluster}}
        self._well_cache: Dict[str, Dict[str, Any]] = {}

    def _load_registry(self):
        if not _REGISTRY_AVAILABLE:
            return
        if self._registry is None:
            try:
                self._registry = WellCalibrationRegistry()
                logger.info("[normalized_db] WellCalibrationRegistry loaded into RAM.")
            except Exception as e:
                logger.error(f"[normalized_db] Failed to load registry: {e}")

    def _get_well_bounds(self, well_id: str) -> Dict[str, Any]:
        if well_id in self._well_cache:
            return self._well_cache[well_id]
        if self._registry is None:
            return {}
        prof = self._registry.get_well_profile(well_id)
        sensors_prof = prof.get("sensors", {})
        cluster = prof.get("family", "OTHER")
        if cluster == "OTHER":
            m = re.match(r"^([A-Za-z]+)", str(well_id))
            cluster = m.group(1).upper() if m else "OTHER"
        sb = {s: _get_sensor_bounds(s, sensors_prof.get(s, {})) for s in STANDARD_SENSORS}
        pb = _physics_bounds(sb)
        entry = {"sensors_prof": sensors_prof, "sensor_bounds": sb, "phys_bounds": pb, "cluster": cluster}
        self._well_cache[well_id] = entry
        return entry

    def _normalize_record(self, r: Dict[str, Any], raw_id: Optional[int] = None) -> Optional[tuple]:
        """Convert one unlabelled dict to a 41-value tuple ready for INSERT_NORM_SQL."""
        well_id = str(r.get("well_id") or "").upper()
        if not well_id:
            return None
        wb = self._get_well_bounds(well_id)
        if not wb:
            return None

        sb = wb["sensor_bounds"]
        pb = wb["phys_bounds"]
        sp = wb["sensors_prof"]
        cluster = wb["cluster"]

        def _f(v, fallback=0.0):
            try:
                return float(v) if v is not None else fallback
            except (TypeError, ValueError):
                return fallback

        def _med(sensor):
            return float(sp.get(sensor, {}).get("median", 0.0))

        inp   = _f(r.get("intake_pressure_psi"),   _med("Inp bar/psi"))
        int_t = _f(r.get("intake_temperature_c"),  _med("Int temp \u00b0C"))
        mot_t = _f(r.get("motor_temperature_c"),   _med("Motor temp \u00b0C"))
        disch = _f(r.get("discharge_pressure_psi"),_med("Disch pr. Bar/psi"))
        vib   = _f(r.get("vibration_g"),           _med("Vibration G's-Vx"))
        leak  = _f(r.get("leak_current_ct"),        0.0)
        volt  = _f(r.get("motor_voltage_v"),        _med("Volt"))
        amps  = _f(r.get("motor_current_a"),        _med("VSD Amps/Load"))
        freq  = _f(r.get("frequency_hz"),           _med("Frequency"))
        dhg   = _f(r.get("dhg_current"),            0.0)
        whp   = _f(r.get("whp_psi"),                _med("WHP (PSI)"))
        flp   = _f(r.get("flp_psi"),                _med("FLP (PSI)"))
        ap    = _f(r.get("annulus_pressure_psi"),   0.0)

        vfd_raw = str(r.get("vfd_status") if r.get("vfd_status") is not None else "1")
        vfd_bin = 1 if vfd_raw in ("1", "1.0", "True", "true", "RUN", "RUNNING") else 0

        delta_p = round(disch - inp, 2)
        torque  = round(amps / max(1.0, freq), 3)
        power   = round((volt * amps * 1.732) / 1000.0, 2)
        thermal = round(mot_t - int_t, 2)

        # Sensor normalization (registry bounds)
        n_inp  = _norm(inp,   sb.get("Inp bar/psi",          (100.0, 1000.0))[0], sb.get("Inp bar/psi",          (100.0, 1000.0))[1])
        n_int  = _norm(int_t, sb.get("Int temp \u00b0C",     (30.0, 90.0))[0],    sb.get("Int temp \u00b0C",     (30.0, 90.0))[1])
        n_mot  = _norm(mot_t, sb.get("Motor temp \u00b0C",   (40.0, 130.0))[0],   sb.get("Motor temp \u00b0C",   (40.0, 130.0))[1])
        n_dis  = _norm(disch, sb.get("Disch pr. Bar/psi",    (800.0, 3500.0))[0], sb.get("Disch pr. Bar/psi",    (800.0, 3500.0))[1])
        n_vib  = _norm(vib,   sb.get("Vibration G's-Vx",     (0.0, 2.0))[0],      sb.get("Vibration G's-Vx",     (0.0, 2.0))[1])
        n_leak = _norm(leak,  sb.get("Leak Current Ct",       (0.0, 50.0))[0],     sb.get("Leak Current Ct",       (0.0, 50.0))[1])
        n_volt = _norm(volt,  sb.get("Volt",                  (400.0, 1500.0))[0], sb.get("Volt",                  (400.0, 1500.0))[1])
        n_amps = _norm(amps,  sb.get("VSD Amps/Load",         (5.0, 50.0))[0],     sb.get("VSD Amps/Load",         (5.0, 50.0))[1])
        n_freq = _norm(freq,  sb.get("Frequency",             (30.0, 65.0))[0],    sb.get("Frequency",             (30.0, 65.0))[1])
        n_dhg  = _norm(dhg,   sb.get("DHG Current",           (0.0, 30.0))[0],     sb.get("DHG Current",           (0.0, 30.0))[1])
        n_whp  = _norm(whp,   sb.get("WHP (PSI)",             (50.0, 500.0))[0],   sb.get("WHP (PSI)",             (50.0, 500.0))[1])
        n_flp  = _norm(flp,   sb.get("FLP (PSI)",             (50.0, 500.0))[0],   sb.get("FLP (PSI)",             (50.0, 500.0))[1])
        n_ap   = _norm(ap,    sb.get("AP (PSI)",              (0.0, 300.0))[0],     sb.get("AP (PSI)",              (0.0, 300.0))[1])

        # Physics normalization (registry-derived envelope bounds)
        n_dp  = _norm(delta_p, pb["Delta_P_PSI"][0],        pb["Delta_P_PSI"][1])
        n_tq  = _norm(torque,  pb["Torque_Proxy_A_Hz"][0],  pb["Torque_Proxy_A_Hz"][1])
        n_pw  = _norm(power,   pb["Power_kVA"][0],           pb["Power_kVA"][1])
        n_te  = _norm(thermal, pb["Thermal_Elevation_C"][0], pb["Thermal_Elevation_C"][1])

        ts = r.get("timestamp") or datetime.utcnow().isoformat()

        return (
            raw_id, ts, well_id, cluster, "live_mqtt",
            inp, int_t, mot_t, disch, vib, leak, volt, amps, freq, dhg, whp, flp, ap,
            vfd_raw, vfd_bin,
            delta_p, torque, power, thermal,
            n_inp, n_int, n_mot, n_dis, n_vib, n_leak, n_volt, n_amps, n_freq, n_dhg, n_whp, n_flp, n_ap,
            n_dp, n_tq, n_pw, n_te
        )

    async def insert_batch(self, records: List[Dict[str, Any]]) -> int:
        """
        Normalize and insert a batch of unlabelled records into normalized.db.
        Called in lockstep with unlabelled_db.insert_telemetry_batch().
        Errors are logged and swallowed — never allowed to crash the MQTT loop.
        """
        if not _REGISTRY_AVAILABLE or not records:
            return 0
        if self._registry is None:
            self._load_registry()
            if self._registry is None:
                return 0

        batch: List[tuple] = []
        for r in records:
            try:
                row = self._normalize_record(r)
                if row is not None:
                    batch.append(row)
            except Exception as e:
                logger.debug(f"[normalized_db] Skipped record for {r.get('well_id')}: {e}")

        if not batch:
            return 0

        try:
            async with aiosqlite.connect(self.db_path, timeout=10.0) as db:
                await db.execute("PRAGMA busy_timeout = 10000;")
                await db.executemany(INSERT_NORM_SQL, batch)
                await db.commit()
            return len(batch)
        except Exception as e:
            logger.error(f"[normalized_db] insert_batch failed: {e}")
            return 0


# Singleton imported by mqtt_collector
from backend.config import NORMALIZED_DB_PATH
normalized_db = NormalizedDatabase(NORMALIZED_DB_PATH)
