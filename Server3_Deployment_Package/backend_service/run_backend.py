"""
ESP APM Platform — Server 3 Backend Service Entry Point
======================================================
Loads environment configuration and runs the FastAPI application + ML Diagnostic Engine
and background MQTT telemetry subscriber on port 8090.
"""

import os
import sys
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent
APP_DIR = BASE_DIR / "app"
CONFIG_FILE = BASE_DIR.parent / "config" / "config.env"

# Add app and code/models to Python path
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

app_code = APP_DIR / "code"
if app_code.exists() and str(app_code) not in sys.path:
    sys.path.insert(0, str(app_code))

# Load config.env if present
if CONFIG_FILE.exists():
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                k = k.strip()
                v = v.strip().strip('"').strip("'")
                if k and k not in os.environ:
                    os.environ[k] = v

host = os.environ.get("BACKEND_HOST", "0.0.0.0")
port = int(os.environ.get("BACKEND_PORT", "8090"))

if __name__ == "__main__":
    import uvicorn
    print("=" * 80)
    print(" ESP APM PLATFORM — SERVER 3 BACKEND & ML DIAGNOSTIC SERVICE")
    print("=" * 80)
    print(f" Listening on      : http://{host}:{port}")
    print(f" Swagger UI Docs   : http://localhost:{port}/docs")
    print(f" Live WebSockets   : ws://localhost:{port}/ws/live")
    print(f" Server 1 MQTT Host: {os.environ.get('MQTT_BROKER_HOST', '192.168.1.155')}:{os.environ.get('MQTT_BROKER_PORT', '1883')}")
    print(f" Server 2 Agent URL: {os.environ.get('AGENT_GATEWAY_URL', 'http://192.168.1.160:8090')}")
    print("=" * 80)

    # Start uvicorn
    uvicorn.run(
        "src.api.rest.gateway:app",
        host=host,
        port=port,
        log_level="info",
        access_log=True
    )
