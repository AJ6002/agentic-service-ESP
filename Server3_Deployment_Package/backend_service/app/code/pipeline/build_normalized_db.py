# CCED ESP Normalized Database Builder & Feature Store
# ====================================================
# Builds cced_esp/data/normalized.db from cced_esp/data/unlabelled.db.
# Scales sensors to [0, 1] using WellCalibrationRegistry and pre-computes physics dynamics.

import os
import sys
import time
import sqlite3
import argparse
import re
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
CODE_DIR = os.path.join(WORKSPACE_ROOT, 'code')
for p in [CODE_DIR, WORKSPACE_ROOT]:
    if p not in sys.path:
        sys.path.insert(0, p)

from models.calibration_registry import WellCalibrationRegistry, STANDARD_SENSORS, clean_col_key

UNLABELLED_DB_PATH = os.path.join(WORKSPACE_ROOT, 'cced_esp', 'data', 'unlabelled.db')
NORMALIZED_DB_PATH = os.path.join(WORKSPACE_ROOT, 'cced_esp', 'data', 'normalized.db')

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS opg_normalized_telemetry (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    raw_id INTEGER,
    timestamp TEXT,
    Wells TEXT,
    Cluster TEXT,
    Source_File TEXT DEFAULT 'unlabelled.db',
    [Inp bar/psi] REAL,
    [Int temp °C] REAL,
    [Motor temp °C] REAL,
    [Disch pr. Bar/psi] REAL,
    [Vibration G's-Vx] REAL,
    [Leak Current Ct] REAL,
    [Volt] REAL,
    [VSD Amps/Load] REAL,
    [Frequency] REAL,
    [DHG Current] REAL,
    [WHP (PSI)] REAL,
    [FLP (PSI)] REAL,
    [AP (PSI)] REAL,
    [VFD STS] TEXT,
    VFD_STS_Binary INTEGER,
    Delta_P_PSI REAL,
    Torque_Proxy_A_Hz REAL,
    Power_kVA REAL,
    Thermal_Elevation_C REAL,
    norm_Inp_bar_psi REAL,
    norm_Int_temp_C REAL,
    norm_Motor_temp_C REAL,
    norm_Disch_pr_Bar_psi REAL,
    norm_Vibration_G_s_Vx REAL,
    norm_Leak_Current_Ct REAL,
    norm_Volt REAL,
    norm_VSD_Amps_Load REAL,
    norm_Frequency REAL,
    norm_DHG_Current REAL,
    norm_WHP_PSI REAL,
    norm_FLP_PSI REAL,
    norm_AP_PSI REAL,
    norm_Delta_P_PSI REAL,
    norm_Torque_Proxy_A_Hz REAL,
    norm_Power_kVA REAL,
    norm_Thermal_Elevation_C REAL
);
"""

CREATE_STATE_SQL = """
CREATE TABLE IF NOT EXISTS _build_state (
    well_id TEXT PRIMARY KEY,
    last_raw_id INTEGER,
    rows_processed INTEGER,
    updated_at TEXT
);
"""

CREATE_INDEX_SQL = """
CREATE INDEX IF NOT EXISTS idx_norm_well_time ON opg_normalized_telemetry (Wells, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_norm_raw_id ON opg_normalized_telemetry (raw_id);
"""

INSERT_ROW_SQL = """
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
);
"""


def get_sensor_bounds(sensor_name: str, st: Dict[str, Any]) -> Tuple[float, float]:
    p_min = float(st.get('min', 0.0))
    p_max = float(st.get('max', 1.0))
    p10 = float(st.get('p10', p_min))
    p90 = float(st.get('p90', p_max))

    # Guard against corrupted historical registry outliers (e.g. -9999 or 1e23)
    if p_min < -100.0 or p_max > 50000.0 or p_min >= p_max:
        if p90 > p10:
            p_min = max(0.0, p10 - 0.5 * (p90 - p10))
            p_max = p90 + 0.5 * (p90 - p10)
        else:
            p_min = 0.0
            p_max = max(1.0, float(st.get('median', 1.0)) * 2.0)
    return round(p_min, 2), round(p_max, 2)


def get_physics_bounds(sensor_bounds: Dict[str, Tuple[float, float]]) -> Dict[str, Tuple[float, float]]:
    inp_min, inp_max = sensor_bounds.get('Inp bar/psi', (100.0, 1000.0))
    disch_min, disch_max = sensor_bounds.get('Disch pr. Bar/psi', (800.0, 3500.0))
    amps_min, amps_max = sensor_bounds.get('VSD Amps/Load', (5.0, 50.0))
    volt_min, volt_max = sensor_bounds.get('Volt', (400.0, 1500.0))
    freq_min, freq_max = sensor_bounds.get('Frequency', (30.0, 65.0))
    freq_min = max(10.0, freq_min)
    mtemp_min, mtemp_max = sensor_bounds.get('Motor temp °C', (40.0, 130.0))
    itemp_min, itemp_max = sensor_bounds.get('Int temp °C', (30.0, 90.0))

    dp_min = max(0.0, disch_min - inp_max)
    dp_max = max(dp_min + 10.0, disch_max - inp_min)
    tq_min = round(amps_min / max(1.0, freq_max), 3)
    tq_max = round(max(tq_min + 0.1, amps_max / max(1.0, freq_min)), 3)
    p_min = round((volt_min * amps_min * 1.732) / 1000.0, 2)
    p_max = round(max(p_min + 1.0, (volt_max * amps_max * 1.732) / 1000.0), 2)
    te_min = max(0.0, mtemp_min - itemp_max)
    te_max = max(te_min + 5.0, mtemp_max - itemp_min)

    return {
        'Delta_P_PSI': (dp_min, dp_max),
        'Torque_Proxy_A_Hz': (tq_min, tq_max),
        'Power_kVA': (p_min, p_max),
        'Thermal_Elevation_C': (te_min, te_max)
    }


def normalize_val(val: float, p_min: float, p_max: float) -> float:
    if p_max <= p_min:
        return 0.0
    norm = (val - p_min) / (p_max - p_min)
    return round(float(max(0.0, min(1.0, norm))), 6)


def build_normalized_db(
    mode: str = 'incremental',
    well_filter: Optional[str] = None,
    limit: Optional[int] = None,
    chunk_size: int = 10000
):
    print('==============================================================================')
    print(' CCED ESP NORMALIZED DATABASE BUILDER')
    print(f' Mode: {mode} | Target: {NORMALIZED_DB_PATH}')
    if well_filter:
        print(f' Filtered to Well: {well_filter}')
    if limit:
        print(f' Limit per well: {limit} rows')
    print('==============================================================================')

    if not os.path.exists(UNLABELLED_DB_PATH):
        print(f'[ERROR] Source DB not found at: {UNLABELLED_DB_PATH}')
        return

    src_conn = sqlite3.connect(UNLABELLED_DB_PATH)
    src_conn.row_factory = sqlite3.Row
    tgt_conn = sqlite3.connect(NORMALIZED_DB_PATH)

    tgt_conn.execute('PRAGMA journal_mode=WAL;')
    tgt_conn.execute('PRAGMA synchronous=NORMAL;')
    tgt_conn.execute(CREATE_TABLE_SQL)
    tgt_conn.execute(CREATE_STATE_SQL)
    for idx_sql in CREATE_INDEX_SQL.strip().split(';'):
        if idx_sql.strip():
            tgt_conn.execute(idx_sql)
    tgt_conn.commit()

    if mode == 'full':
        if well_filter:
            print(f'Truncating data for well {well_filter}...')
            tgt_conn.execute('DELETE FROM opg_normalized_telemetry WHERE Wells = ?', (well_filter,))
            tgt_conn.execute('DELETE FROM _build_state WHERE well_id = ?', (well_filter,))
        else:
            print('Full rebuild: Truncating all normalized data...')
            tgt_conn.execute('DELETE FROM opg_normalized_telemetry')
            tgt_conn.execute('DELETE FROM _build_state')
        tgt_conn.commit()

    print('Loading Well Calibration Registry...')
    registry = WellCalibrationRegistry()

    wells_query = 'SELECT DISTINCT well_id FROM opg_well_telemetry ORDER BY well_id'
    if well_filter:
        wells = [well_filter]
    else:
        wells = [r[0] for r in src_conn.execute(wells_query).fetchall() if r[0]]

    print(f'Wells to process: {len(wells)}')

    total_inserted = 0
    t0 = time.time()

    for w_idx, well_id in enumerate(wells, 1):
        prof = registry.get_well_profile(well_id)
        sensors_prof = prof.get('sensors', {})
        cluster = prof.get('family', 'OTHER')
        if cluster == 'OTHER':
            m = re.match(r'^([A-Za-z]+)', str(well_id))
            cluster = m.group(1).upper() if m else 'OTHER'

        sensor_bounds = {s: get_sensor_bounds(s, sensors_prof.get(s, {})) for s in STANDARD_SENSORS}
        phys_bounds = get_physics_bounds(sensor_bounds)

        state_row = tgt_conn.execute('SELECT last_raw_id FROM _build_state WHERE well_id = ?', (well_id,)).fetchone()
        last_id = state_row[0] if (state_row and mode != 'full') else 0

        total_well_rows = 0

        while True:
            fetch_limit = min(chunk_size, limit - total_well_rows) if limit else chunk_size
            if fetch_limit <= 0:
                break

            q = '''
            SELECT id, timestamp, well_id,
                   intake_pressure_psi, intake_temperature_c, motor_temperature_c,
                   discharge_pressure_psi, vibration_g, leak_current_ct,
                   motor_voltage_v, motor_current_a, frequency_hz, dhg_current,
                   whp_psi, flp_psi, annulus_pressure_psi, vfd_status
            FROM opg_well_telemetry
            WHERE well_id = ? AND id > ?
            ORDER BY id ASC
            LIMIT ?
            '''
            rows = src_conn.execute(q, (well_id, last_id, fetch_limit)).fetchall()
            if not rows:
                break

            batch_values = []
            for r in rows:
                raw_id = r['id']
                ts = r['timestamp']

                inp = float(r['intake_pressure_psi']) if r['intake_pressure_psi'] is not None else float(sensors_prof.get('Inp bar/psi', {}).get('median', 230.0))
                int_t = float(r['intake_temperature_c']) if r['intake_temperature_c'] is not None else float(sensors_prof.get('Int temp °C', {}).get('median', 50.0))
                mot_t = float(r['motor_temperature_c']) if r['motor_temperature_c'] is not None else float(sensors_prof.get('Motor temp °C', {}).get('median', 70.0))
                disch = float(r['discharge_pressure_psi']) if r['discharge_pressure_psi'] is not None else float(sensors_prof.get('Disch pr. Bar/psi', {}).get('median', 1800.0))
                vib = float(r['vibration_g']) if r['vibration_g'] is not None else float(sensors_prof.get("Vibration G's-Vx", {}).get('median', 0.18))
                leak = float(r['leak_current_ct']) if r['leak_current_ct'] is not None else 0.0
                volt = float(r['motor_voltage_v']) if r['motor_voltage_v'] is not None else float(sensors_prof.get('Volt', {}).get('median', 1000.0))
                amps = float(r['motor_current_a']) if r['motor_current_a'] is not None else float(sensors_prof.get('VSD Amps/Load', {}).get('median', 20.0))
                freq = float(r['frequency_hz']) if r['frequency_hz'] is not None else float(sensors_prof.get('Frequency', {}).get('median', 50.0))
                dhg = float(r['dhg_current']) if r['dhg_current'] is not None else 0.0
                whp = float(r['whp_psi']) if r['whp_psi'] is not None else float(sensors_prof.get('WHP (PSI)', {}).get('median', 200.0))
                flp = float(r['flp_psi']) if r['flp_psi'] is not None else float(sensors_prof.get('FLP (PSI)', {}).get('median', 190.0))
                ap = float(r['annulus_pressure_psi']) if r['annulus_pressure_psi'] is not None else 0.0

                vfd_sts_raw = str(r['vfd_status']) if r['vfd_status'] is not None else '1'
                vfd_sts_bin = 1 if vfd_sts_raw in ('1', '1.0', 'True', 'true', 'RUN', 'RUNNING') else 0

                delta_p = round(disch - inp, 2)
                torque = round(amps / max(1.0, freq), 3)
                power = round((volt * amps * 1.732) / 1000.0, 2)
                thermal = round(mot_t - int_t, 2)

                n_inp = normalize_val(inp, sensor_bounds['Inp bar/psi'][0], sensor_bounds['Inp bar/psi'][1])
                n_int = normalize_val(int_t, sensor_bounds['Int temp °C'][0], sensor_bounds['Int temp °C'][1])
                n_mot = normalize_val(mot_t, sensor_bounds['Motor temp °C'][0], sensor_bounds['Motor temp °C'][1])
                n_disch = normalize_val(disch, sensor_bounds['Disch pr. Bar/psi'][0], sensor_bounds['Disch pr. Bar/psi'][1])
                n_vib = normalize_val(vib, sensor_bounds["Vibration G's-Vx"][0], sensor_bounds["Vibration G's-Vx"][1])
                n_leak = normalize_val(leak, sensor_bounds['Leak Current Ct'][0], sensor_bounds['Leak Current Ct'][1])
                n_volt = normalize_val(volt, sensor_bounds['Volt'][0], sensor_bounds['Volt'][1])
                n_amps = normalize_val(amps, sensor_bounds['VSD Amps/Load'][0], sensor_bounds['VSD Amps/Load'][1])
                n_freq = normalize_val(freq, sensor_bounds['Frequency'][0], sensor_bounds['Frequency'][1])
                n_dhg = normalize_val(dhg, sensor_bounds['DHG Current'][0], sensor_bounds['DHG Current'][1])
                n_whp = normalize_val(whp, sensor_bounds['WHP (PSI)'][0], sensor_bounds['WHP (PSI)'][1])
                n_flp = normalize_val(flp, sensor_bounds['FLP (PSI)'][0], sensor_bounds['FLP (PSI)'][1])
                n_ap = normalize_val(ap, sensor_bounds['AP (PSI)'][0], sensor_bounds['AP (PSI)'][1])

                n_dp = normalize_val(delta_p, phys_bounds['Delta_P_PSI'][0], phys_bounds['Delta_P_PSI'][1])
                n_tq = normalize_val(torque, phys_bounds['Torque_Proxy_A_Hz'][0], phys_bounds['Torque_Proxy_A_Hz'][1])
                n_pw = normalize_val(power, phys_bounds['Power_kVA'][0], phys_bounds['Power_kVA'][1])
                n_te = normalize_val(thermal, phys_bounds['Thermal_Elevation_C'][0], phys_bounds['Thermal_Elevation_C'][1])

                batch_values.append((
                    raw_id, ts, well_id, cluster, 'unlabelled.db',
                    inp, int_t, mot_t, disch, vib, leak, volt, amps, freq, dhg, whp, flp, ap,
                    vfd_sts_raw, vfd_sts_bin,
                    delta_p, torque, power, thermal,
                    n_inp, n_int, n_mot, n_disch, n_vib, n_leak, n_volt, n_amps, n_freq, n_dhg, n_whp, n_flp, n_ap,
                    n_dp, n_tq, n_pw, n_te
                ))

            tgt_conn.executemany(INSERT_ROW_SQL, batch_values)
            last_id = rows[-1]['id']
            total_well_rows += len(rows)
            total_inserted += len(rows)

            tgt_conn.execute('''
            INSERT OR REPLACE INTO _build_state (well_id, last_raw_id, rows_processed, updated_at)
            VALUES (?, ?, ?, ?)
            ''', (well_id, last_id, total_well_rows, datetime.now().isoformat()))
            tgt_conn.commit()

        print(f' [{w_idx:2d}/{len(wells)}] Well {well_id:<10}: {total_well_rows:>6} rows normalized (last_id={last_id})')

    elapsed = time.time() - t0
    print('------------------------------------------------------------------------------')
    print('Normalized DB build complete.')
    print(f'Total rows inserted: {total_inserted:,} in {elapsed:.2f}s')
    print('------------------------------------------------------------------------------')

    src_conn.close()
    tgt_conn.close()


def verify():
    if not os.path.exists(NORMALIZED_DB_PATH):
        print(f'[ERROR] normalized.db not found at {NORMALIZED_DB_PATH}')
        return

    conn = sqlite3.connect(NORMALIZED_DB_PATH)
    conn.row_factory = sqlite3.Row
    print('==============================================================================')
    print(' NORMALIZED DB VERIFICATION REPORT')
    print(f' Path: {NORMALIZED_DB_PATH}')
    print('==============================================================================')

    total = conn.execute('SELECT COUNT(*) FROM opg_normalized_telemetry').fetchone()[0]
    wells_count = conn.execute('SELECT COUNT(DISTINCT Wells) FROM opg_normalized_telemetry').fetchone()[0]
    print(f'Total rows: {total:,}')
    print(f'Distinct wells: {wells_count}')

    sample = conn.execute('SELECT * FROM opg_normalized_telemetry ORDER BY id DESC LIMIT 1').fetchone()
    if sample:
        print('\n--- Sample Latest Row ---')
        d = dict(sample)
        print(f'Well: {d.get("Wells")} | Cluster: {d.get("Cluster")} | Timestamp: {d.get("timestamp")}')
        print(f'Raw: Inp={d.get("Inp bar/psi")} psi | Disch={d.get("Disch pr. Bar/psi")} psi | Amps={d.get("VSD Amps/Load")} A | Freq={d.get("Frequency")} Hz')
        print(f'Physics: DeltaP={d.get("Delta_P_PSI")} psi | Torque={d.get("Torque_Proxy_A_Hz")} A/Hz | Power={d.get("Power_kVA")} kVA')
        print(f'Norm Sensors: Inp={d.get("norm_Inp_bar_psi")} | Disch={d.get("norm_Disch_pr_Bar_psi")} | Amps={d.get("norm_VSD_Amps_Load")} | Freq={d.get("norm_Frequency")}')
        print(f'Norm Physics: DeltaP={d.get("norm_Delta_P_PSI")} | Torque={d.get("norm_Torque_Proxy_A_Hz")} | Power={d.get("norm_Power_kVA")}')

    conn.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Build Normalized Feature Store DB')
    parser.add_argument('--mode', choices=['incremental', 'full'], default='incremental', help='Build mode')
    parser.add_argument('--well', type=str, default=None, help='Filter by specific well_id')
    parser.add_argument('--limit', type=int, default=None, help='Limit rows per well (for testing)')
    parser.add_argument('--chunk-size', type=int, default=10000, help='Batch size per transaction')
    parser.add_argument('--verify', action='store_true', help='Verify existing normalized.db')
    args = parser.parse_args()

    if args.verify:
        verify()
    else:
        build_normalized_db(mode=args.mode, well_filter=args.well, limit=args.limit, chunk_size=args.chunk_size)
