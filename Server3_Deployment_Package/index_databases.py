"""
Database Indexer for Server 3 SQLite Databases
Creates performance compound indices on opg_well_telemetry tables
to eliminate 6+ second query locks and achieve sub-100ms response times.
"""

import glob
import os
import sqlite3
import sys

def index_databases():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"Scanning for SQLite databases in and around: {base_dir}")

    db_patterns = [
        os.path.join(base_dir, "**", "*.db"),
        os.path.join(base_dir, "..", "**", "*.db"),
        os.path.join("C:\\TAS_AI", "**", "*.db"),
        os.path.join("C:\\TAS_AI\\Server3_Deployment_Package", "**", "*.db"),
    ]

    found_dbs = set()
    for pat in db_patterns:
        for p in glob.glob(pat, recursive=True):
            found_dbs.add(os.path.abspath(p))

    if not found_dbs:
        print("No .db files found in default search paths.")
        return

    indexed_count = 0
    for db_path in sorted(found_dbs):
        try:
            conn = sqlite3.connect(db_path, timeout=10.0)
            cur = conn.cursor()
            tables = [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
            
            if 'opg_well_telemetry' in tables:
                print(f"[+] Indexing {db_path}...")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_telemetry_well_id_desc ON opg_well_telemetry(well_id, id DESC);")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_telemetry_asset_id_desc ON opg_well_telemetry(asset_id, id DESC);")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_telemetry_timestamp ON opg_well_telemetry(timestamp DESC);")
                conn.commit()
                indexed_count += 1
                print(f"    -> Successfully indexed {os.path.basename(db_path)}")
            conn.close()
        except Exception as ex:
            print(f"[!] Error on {db_path}: {ex}")

    print(f"\nCompleted! Indexed {indexed_count} database file(s).")

if __name__ == "__main__":
    index_databases()
