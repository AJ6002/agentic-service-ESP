"""
ESP Platform Database Auto-Flush & Space Reclamation Utility
============================================================
Checks the sizes of ESP SQLite databases (unlabelled.db, labelled.db, normalized.db, mlresults.db).
When any database exceeds the 1.5 GB threshold (~360,000 rows at ~4.2 KB/row):
1. Safely retains the most recent 300,000 telemetry rows (approx 1.2 GB).
2. Deletes older historical records.
3. Runs SQLite VACUUM to immediately reclaim and free physical storage space back to the operating system.

Usage:
  python prune_databases.py [--max-mb 1500] [--retain 300000] [--force]
"""

import os
import sys
import sqlite3
import argparse
from pathlib import Path

try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# Identify workspace data directory
SCRIPT_DIR = Path(__file__).resolve().parent
CANDIDATE_DATA_DIRS = [
    Path(r"c:\Users\admin.DESKTOP-17T37DJ\Desktop\New folder (6)\data"),
    SCRIPT_DIR / "data",
    SCRIPT_DIR.parent / "data",
    Path("data").resolve(),
    Path("../data").resolve(),
] + [p / "data" for p in SCRIPT_DIR.parents]

DATA_DIR = next((d for d in CANDIDATE_DATA_DIRS if (d / "unlabelled.db").exists() and (d / "unlabelled.db").stat().st_size > 1000000), None)
if DATA_DIR is None:
    DATA_DIR = next((d for d in CANDIDATE_DATA_DIRS if d.exists()), SCRIPT_DIR.parent / "data")

TARGET_DATABASES = [
    ("unlabelled.db", "opg_well_telemetry"),
    ("labelled.db", "opg_well_telemetry"),
    ("normalized.db", "opg_normalized_telemetry"),
    ("mlresults.db", "ml_results")
]

def prune_database(db_file: Path, table_name: str, max_bytes: int, retain_rows: int, force: bool = False):
    if not db_file.exists():
        print(f"[-] Database not found: {db_file}")
        return

    size_bytes = db_file.stat().st_size
    size_mb = size_bytes / (1024 * 1024)
    print(f"\n[*] Checking {db_file.name}: {size_mb:.2f} MB ({size_bytes:,} bytes)")

    if not force and size_bytes < max_bytes:
        print(f"    [OK] Under size threshold ({max_bytes / (1024*1024):.0f} MB). No pruning necessary.")
        return

    print(f"    [!] Size exceeds limit ({max_bytes / (1024*1024):.0f} MB). Connecting for maintenance...")
    try:
        with sqlite3.connect(str(db_file), timeout=60.0) as conn:
            cur = conn.cursor()
            
            # Check table existence
            tables = [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()]
            if table_name not in tables:
                if tables:
                    table_name = tables[0]
                else:
                    print(f"    [-] No tables found in {db_file.name}.")
                    return

            total_rows = cur.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
            max_id = cur.execute(f"SELECT MAX(id) FROM {table_name}").fetchone()[0] or 0
            print(f"    [i] Current rows in '{table_name}': {total_rows:,} (Max ID: {max_id:,})")

            if total_rows <= retain_rows and not force:
                print(f"    [OK] Row count ({total_rows:,}) is within retention window ({retain_rows:,}).")
                return

            cutoff_row = cur.execute(f"""
                SELECT id FROM {table_name} 
                ORDER BY id DESC 
                LIMIT 1 OFFSET {retain_rows}
            """).fetchone()

            if cutoff_row and cutoff_row[0]:
                cutoff_id = cutoff_row[0]
                print(f"    [x] Deleting rows with ID <= {cutoff_id:,} (Retaining latest {retain_rows:,} rows)...")
                cur.execute(f"DELETE FROM {table_name} WHERE id <= ?", (cutoff_id,))
                deleted_count = cur.rowcount
                conn.commit()
                print(f"    [+] Deleted {deleted_count:,} older rows.")

            print(f"    [x] Executing VACUUM to reclaim disk space back to operating system...")
            cur.execute("VACUUM;")
            
            new_size_bytes = db_file.stat().st_size
            new_size_mb = new_size_bytes / (1024 * 1024)
            freed_mb = size_mb - new_size_mb
            print(f"    [SUCCESS] New Size: {new_size_mb:.2f} MB. Freed: {freed_mb:.2f} MB!")

    except Exception as ex:
        print(f"    [ERROR] Maintenance failed for {db_file.name}: {ex}")

def main():
    parser = argparse.ArgumentParser(description="ESP Platform SQLite Maintenance & Auto-Flush Utility")
    parser.add_argument("--max-mb", type=int, default=1500, help="Maximum DB size in MB before flushing (Default: 1500 MB = 1.5 GB)")
    parser.add_argument("--retain", type=int, default=300000, help="Number of latest rows to retain (Default: 300,000 rows ~ 1.2 GB)")
    parser.add_argument("--force", action="store_true", help="Force prune even if under size limit")
    parser.add_argument("--data-dir", type=str, default=None, help="Custom data directory path")
    args = parser.parse_args()

    data_dir = Path(args.data_dir) if args.data_dir else DATA_DIR
    print("=" * 65)
    print("ESP PLATFORM DATABASE STORAGE RECLAMATION UTILITY")
    print(f"Data Directory: {data_dir}")
    print(f"Threshold     : {args.max_mb} MB (1.5 GB)")
    print(f"Retention     : Latest {args.retain:,} rows")
    print("=" * 65)

    max_bytes = args.max_mb * 1024 * 1024
    for db_name, tbl_name in TARGET_DATABASES:
        db_path = data_dir / db_name
        prune_database(db_path, tbl_name, max_bytes, args.retain, force=args.force)

    print("\n[OK] All database maintenance operations completed.")

if __name__ == "__main__":
    main()
