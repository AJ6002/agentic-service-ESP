"""
Read-only script to inspect PostgreSQL tables, schemas, and columns in esp_apm_db.
DO NOT WRITE ANYTHING TO DATABASE.
"""
import json
import psycopg2
import sys

sys.stdout.reconfigure(encoding='utf-8')

DATABASE_URL = "postgresql://esp_admin:EspApm2026!@192.168.1.184:5433/esp_apm_db"

def main():
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    cur.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        ORDER BY table_name;
    """)
    tables = [r[0] for r in cur.fetchall()]

    print(f"Total Public Tables Found: {len(tables)}\n")
    
    summary = {}
    for t in tables:
        cur.execute(f'SELECT count(*) FROM "{t}"')
        cnt = cur.fetchone()[0]
        
        cur.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = %s
            ORDER BY ordinal_position;
        """, (t,))
        cols = [{'column': r[0], 'type': r[1], 'nullable': r[2]} for r in cur.fetchall()]
        summary[t] = {
            'rows': cnt,
            'col_count': len(cols),
            'cols': cols
        }
        print(f"Table: {t:<30} | Rows: {cnt:<8} | Cols: {len(cols)}")

    print("\n" + "="*80)
    print("DETAILED SCHEMA BREAKDOWN")
    print("="*80)
    for t, info in summary.items():
        print(f"\nTABLE: {t} (Rows: {info['rows']}, Columns: {info['col_count']})")
        col_names = [c['column'] + f" ({c['type']})" for c in info['cols']]
        print("  Columns: " + ", ".join(col_names))

if __name__ == "__main__":
    main()
