"""
Full regression run for ESP Agent Service.
Runs all tests, captures env info, writes REPORT_REGRESSION_<date>.txt
"""
import subprocess, sys, os, json, platform, datetime, socket, shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, f"REPORT_REGRESSION_{datetime.datetime.now():%Y%m%d_%H%M}.txt")

# Ensure virtualenv Scripts and bin are in PATH so subprocesses pick up correct pytest & pip
venv_scripts = os.path.join(ROOT, ".venv", "Scripts")
if os.path.isdir(venv_scripts):
    os.environ["PATH"] = venv_scripts + os.pathsep + os.environ.get("PATH", "")
os.environ["PYTHONPATH"] = ROOT

PHASES = [
    "tests/",
]

def run(cmd, timeout=600):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout, cwd=ROOT)
        return r.stdout + r.stderr, r.returncode
    except subprocess.TimeoutExpired:
        return f"TIMEOUT after {timeout}s", -1

def probe(name, host, port):
    try:
        with socket.create_connection((host, int(port)), timeout=3):
            return f"{name} ({host}:{port}) = UP"
    except Exception as e:
        return f"{name} ({host}:{port}) = DOWN ({e})"

def check_pytest_timeout():
    out, rc = run(f'"{sys.executable}" -m pytest --help')
    return "--timeout" in out

def main():
    has_timeout = check_pytest_timeout()
    timeout_flag = "--timeout=120" if has_timeout else ""

    with open(OUT, "w", encoding="utf-8") as f:
        w = f.write

        w("=" * 85 + "\n")
        w("ESP AGENT SERVICE — FULL REGRESSION REPORT\n")
        w(f"Generated: {datetime.datetime.now():%Y-%m-%d %H:%M:%S}\n")
        w("=" * 85 + "\n\n")

        # 1. Environment
        w("1. ENVIRONMENT\n" + "-" * 85 + "\n")
        w(f"Python:  {sys.version.split()[0]}\n")
        w(f"OS:      {platform.platform()}\n")
        w(f"Host:    {platform.node()}\n")
        pip_freeze, _ = run(f'"{sys.executable}" -m pip freeze')
        w("Key packages:\n")
        for line in pip_freeze.splitlines():
            if any(p in line.lower() for p in ["fastapi", "pydantic", "redis", "httpx", "pytest", "duckdb", "qdrant", "neo4j", "openai"]):
                w(f"  {line}\n")
        w("\n")

        # 2. Service probes
        w("2. SERVICE PROBES\n" + "-" * 85 + "\n")
        w(probe("Redis",          "127.0.0.1", 6381) + "\n")
        w(probe("Agent",          "127.0.0.1", 8091) + "\n")
        w(probe("Server 184",     "192.168.1.184", 8090) + "\n")
        w(probe("KB Service",     "192.168.1.184", 8085) + "\n")
        w(probe("llama-server",   "127.0.0.1", 8080) + "\n")
        w("\n")

        # 3. Test collection
        w("3. TEST COLLECTION\n" + "-" * 85 + "\n")
        collect, _ = run(f'"{sys.executable}" -m pytest --collect-only -q tests/')
        lines = [l for l in collect.splitlines() if "::" in l or "test" in l.lower()]
        w(f"Total collected: {len([l for l in collect.splitlines() if '::' in l])}\n\n")
        w(collect[:5000] + "\n\n" if len(collect) > 5000 else collect + "\n\n")

        # 4. Per-phase runs
        w("4. PER-PHASE RESULTS\n" + "-" * 85 + "\n")
        totals = {"passed": 0, "failed": 0, "skipped": 0, "error": 0}
        failures_block = []

        for phase in PHASES:
            full = os.path.join(ROOT, phase)
            if not os.path.exists(full):
                w(f"\n--- {phase}  (MISSING — skipped)\n")
                continue
            w(f"\n--- {phase}\n")
            pytest_cmd = f'"{sys.executable}" -m pytest "{phase}" -v --tb=short {timeout_flag}'.strip()
            out, rc = run(pytest_cmd, timeout=1800)
            # Extract summary line
            for line in out.splitlines():
                if " passed" in line or " failed" in line or " error" in line:
                    w(f"    {line.strip()}\n")
            w(f"    exit code: {rc}\n")
            # Capture failures separately
            if "FAILED" in out or "ERROR" in out:
                failures_block.append((phase, out))
            totals["failed"] += out.count("FAILED ")
            totals["passed"] += out.count(" PASSED ")
            totals["skipped"] += out.count(" SKIPPED ")

        w("\n")

        # 5. Full failure tracebacks
        w("5. FAILURE DETAIL (full tracebacks)\n" + "-" * 85 + "\n")
        if not failures_block:
            w("No failures.\n")
        else:
            for phase, out in failures_block:
                w(f"\n### Failures in {phase}\n")
                w(out)
                w("\n")

        # 6. Summary
        w("\n6. SUMMARY\n" + "-" * 85 + "\n")
        w(f"Passed:  {totals['passed']}\n")
        w(f"Failed:  {totals['failed']}\n")
        w(f"Skipped: {totals['skipped']}\n")
        w(f"Overall: {'GREEN' if totals['failed'] == 0 else 'RED'}\n")

        w("\n" + "=" * 85 + "\n")
        w("END OF REPORT\n")
        w("=" * 85 + "\n")

    print(f"Report written to: {OUT}")

if __name__ == "__main__":
    main()
