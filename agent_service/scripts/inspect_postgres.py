import psycopg2
import os

db_url = 'postgresql://esp_admin:EspApm2026!@192.168.1.184:5433/esp_apm_db'
conn = psycopg2.connect(db_url)
cur = conn.cursor()

cur.execute("""
    SELECT table_name, count(column_name) as cols
    FROM information_schema.columns
    WHERE table_schema = 'public'
    GROUP BY table_name
    ORDER BY table_name;
""")
rows = cur.fetchall()

print(f"=== POSTGRESQL POOL INSPECTION: {len(rows)} TABLES FOUND ===")
print(f"{'#':<3} {'Table Name':<32} {'Columns':<10} {'Rows':<8} {'Indexes'}")
print("-" * 75)

for i, (tbl, col_cnt) in enumerate(rows, 1):
    cur.execute(f'SELECT count(*) FROM "{tbl}"')
    row_cnt = cur.fetchone()[0]
    
    cur.execute(f"SELECT indexname FROM pg_indexes WHERE schemaname = 'public' AND tablename = '{tbl}'")
    idxs = [r[0] for r in cur.fetchall()]
    idx_str = ", ".join(idxs) if idxs else "None"
    
    print(f"{i:<3} {tbl:<32} {col_cnt:<10} {row_cnt:<8} {idx_str}")

conn.close()
