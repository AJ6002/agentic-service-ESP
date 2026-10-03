import socket
import psycopg2

hosts = ['192.168.1.184', '192.168.1.188', '192.168.1.155', '192.168.1.191', '127.0.0.1']
ports = [5432, 5433, 8080, 8090, 8091]

print("=== PORT SCAN ===")
for h in hosts:
    for p in ports:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.5)
        try:
            res = s.connect_ex((h, p))
            if res == 0:
                print(f"OPEN: {h}:{p}")
        except Exception as e:
            pass
        finally:
            s.close()

print("\n=== POSTGRES WELLS QUERY ===")
# Try connecting to any open postgres
for h in ['192.168.1.184', '192.168.1.188', '127.0.0.1']:
    for p in [5433, 5432]:
        url = f"postgresql://esp_admin:EspApm2026!@{h}:{p}/esp_apm_db"
        try:
            conn = psycopg2.connect(url, connect_timeout=2)
            cur = conn.cursor()
            cur.execute("SELECT DISTINCT well_id FROM opg_well_telemetry ORDER BY well_id;")
            wells_telem = [r[0] for r in cur.fetchall()]
            cur.execute("SELECT DISTINCT well_id FROM esp_unified_assessments ORDER BY well_id;")
            wells_assess = [r[0] for r in cur.fetchall()]
            print(f"SUCCESS on {h}:{p}!")
            print("opg_well_telemetry wells:", wells_telem)
            print("esp_unified_assessments wells:", wells_assess)
            cur.close()
            conn.close()
            break
        except Exception as e:
            pass
