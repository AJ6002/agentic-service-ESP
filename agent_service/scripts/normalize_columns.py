import os
import psycopg2

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://esp_admin:EspApm2026!@192.168.1.184:5433/esp_apm_db")

conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

cur.execute("""
    SELECT column_name FROM information_schema.columns 
    WHERE table_name = 'opg_normalized_telemetry' 
    ORDER BY ordinal_position;
""")
cols = [r[0] for r in cur.fetchall()]

rename_map = {
    'Wells': 'well_name',
    'Cluster': 'cluster',
    'Source_File': 'source_file',
    'Inp bar/psi': 'int_prs_psi',
    'Disch pr. Bar/psi': 'disch_prs_psi',
    'Leak Current Ct': 'leak_current_ct',
    'Volt': 'volt_v',
    'VSD Amps/Load': 'amp_a',
    'Frequency': 'freq_hz',
    'DHG Current': 'dhg_current_ma',
    'WHP (PSI)': 'whp_psi',
    'FLP (PSI)': 'flp_psi',
    'AP (PSI)': 'ap_psi',
    'VFD STS': 'vfd_sts',
}

for c in cols:
    if 'Int temp' in c and not c.startswith('norm_'):
        rename_map[c] = 'intake_temp_c'
    elif 'Motor temp' in c and not c.startswith('norm_'):
        rename_map[c] = 'motor_temp_c'
    elif 'Vibration' in c and not c.startswith('norm_'):
        rename_map[c] = 'vibration_g'

for old_col, new_col in rename_map.items():
    if old_col in cols:
        print(f"Renaming '{old_col}' -> '{new_col}'")
        cur.execute(f'ALTER TABLE opg_normalized_telemetry RENAME COLUMN "{old_col}" TO "{new_col}";')

conn.commit()
conn.close()
print("Column normalization complete!")
