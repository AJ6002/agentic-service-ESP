import os
import sys
import psycopg2

sys.stdout.reconfigure(encoding='utf-8')

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://esp_admin:EspApm2026!@192.168.1.184:5433/esp_apm_db")

try:
    conn = psycopg2.connect(DATABASE_URL, connect_timeout=5)
    cur = conn.cursor()

    print("=== 1. ALL TABLES AND COLUMNS IN esp_apm_db ===")
    cur.execute("""
        SELECT table_name, column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_schema = 'public'
        ORDER BY table_name, ordinal_position;
    """)
    rows = cur.fetchall()
    
    tables = {}
    for tbl, col, dtype, nullable in rows:
        tables.setdefault(tbl, []).append((col, dtype, nullable))
        
    for tbl, cols in tables.items():
        cur.execute(f"SELECT count(*) FROM public.{tbl}")
        cnt = cur.fetchone()[0]
        print(f"\nTABLE: public.{tbl} ({cnt} rows, {len(cols)} columns)")
        col_summary = ", ".join([f"{c[0]} ({c[1]})" for c in cols[:6]])
        if len(cols) > 6:
            col_summary += f", ... (+{len(cols)-6} more)"
        print(f"  Columns: {col_summary}")

    print("\n=== 2. EXTENSIONS INSTALLED ===")
    cur.execute("SELECT extname, extversion FROM pg_extension;")
    for ext, ver in cur.fetchall():
        print(f"  Extension: {ext} (v{ver})")

    conn.close()
except Exception as e:
    print(f"PostgreSQL connection error: {e}")
