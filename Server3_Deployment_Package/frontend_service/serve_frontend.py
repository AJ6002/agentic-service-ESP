"""
ESP APM Platform — Server 3 Frontend Static & Reverse-Proxy Server
===================================================================
Serves the pre-compiled React Dashboard SPA on port 3000, and transparently 
reverse-proxies API requests (/api/*) and live WebSockets (/ws/*) to the 
Backend Service on port 8090 (or Server 2 Agent Gateway on port 8090).
"""

import os
import sys
import time
from pathlib import Path
import asyncio
from fastapi import FastAPI, Request, Response, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware
import httpx
import websockets

BASE_DIR = Path(__file__).resolve().parent
DIST_DIR = BASE_DIR / "dist"
CONFIG_FILE = BASE_DIR.parent / "config" / "config.env"

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

FRONTEND_HOST = os.environ.get("FRONTEND_HOST", "0.0.0.0")
FRONTEND_PORT = int(os.environ.get("FRONTEND_PORT", "3000"))
BACKEND_PORT = int(os.environ.get("BACKEND_PORT", "8090"))
BACKEND_HTTP_BASE = f"http://127.0.0.1:{BACKEND_PORT}"
BACKEND_WS_BASE = f"ws://127.0.0.1:{BACKEND_PORT}"
AGENT_GATEWAY_URL = os.environ.get("AGENT_GATEWAY_URL", "http://192.168.1.191:8090").rstrip("/")

app = FastAPI(title="ESP Frontend Production Server", docs_url=None, redoc_url=None)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global async HTTP client for reverse proxy with extended 120s timeout
_http_client: httpx.AsyncClient = None

@app.on_event("startup")
async def startup_event():
    global _http_client
    _http_client = httpx.AsyncClient(timeout=120.0)

@app.on_event("shutdown")
async def shutdown_event():
    global _http_client
    if _http_client:
        await _http_client.aclose()

# 1. Reverse Proxy for /api/* (Bifurcated: Agent -> Server 2, Core/SCADA -> Local Backend)
@app.api_route("/api/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"])
async def reverse_proxy_api(request: Request, path: str):
    start_time = time.time()
    is_agent = path.startswith("agent/") or path.startswith("ui/agent/")

    # Normalize path mappings
    if path.startswith("agent/agent/"):
        target_path = "ui/agent/" + path[len("agent/agent/"):]
    elif path.startswith("agent/"):
        target_path = "ui/" + path[len("agent/"):]
    else:
        target_path = path

    base_url = AGENT_GATEWAY_URL if is_agent else BACKEND_HTTP_BASE
    url = f"{base_url}/api/{target_path}"
    headers = dict(request.headers)
    headers.pop("host", None)

    body = await request.body()
    try:
        req = _http_client.build_request(
            method=request.method,
            url=url,
            headers=headers,
            params=request.query_params,
            content=body
        )
        resp = await _http_client.send(req, stream=True)
        proc_time_ms = round((time.time() - start_time) * 1000, 2)
        resp_headers = dict(resp.headers)
        resp_headers["X-Process-Time"] = f"{proc_time_ms}ms"
        resp_headers["X-Proxied-By"] = "ESP-Frontend-Service"

        # Stream SSE / NDJSON real-time without buffering
        content_type = resp.headers.get("content-type", "")
        if "text/event-stream" in content_type or "application/x-ndjson" in content_type:
            return StreamingResponse(
                resp.aiter_bytes(),
                status_code=resp.status_code,
                headers=resp_headers,
                background=resp.aclose
            )

        # Standard buffered response for small REST payloads
        response_content = await resp.aread()
        await resp.aclose()
        return Response(
            content=response_content,
            status_code=resp.status_code,
            headers=resp_headers
        )
    except Exception as e:
        return Response(
            content=f'{{"error": "Target unreachable at {base_url}", "detail": "{str(e)}"}}',
            status_code=502,
            media_type="application/json"
        )

# 2. Transparent WebSocket Reverse Proxy for /ws/*
@app.websocket("/ws/{path:path}")
async def reverse_proxy_ws(client_ws: WebSocket, path: str):
    await client_ws.accept()
    backend_ws_url = f"{BACKEND_WS_BASE}/ws/{path}"
    if client_ws.query_params:
        backend_ws_url += f"?{client_ws.query_params}"

    try:
        async with websockets.connect(backend_ws_url) as backend_ws:
            async def client_to_backend():
                try:
                    while True:
                        msg = await client_ws.receive_text()
                        await backend_ws.send(msg)
                except (WebSocketDisconnect, websockets.exceptions.ConnectionClosed):
                    pass

            async def backend_to_client():
                try:
                    while True:
                        msg = await backend_ws.recv()
                        await client_ws.send_text(msg)
                except (WebSocketDisconnect, websockets.exceptions.ConnectionClosed):
                    pass

            # Run both bidirectional loops concurrently
            await asyncio.gather(client_to_backend(), backend_to_client())
    except Exception:
        pass
    finally:
        try:
            await client_ws.close()
        except Exception:
            pass

# 3. Mount static assets
if (DIST_DIR / "assets").exists():
    app.mount("/assets", StaticFiles(directory=str(DIST_DIR / "assets")), name="assets")

# 4. Serve index.html or static files (SPA fallback)
@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    target_file = DIST_DIR / full_path
    if full_path and target_file.is_file():
        return FileResponse(target_file)
    index_file = DIST_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return Response("<h1>React dist not found. Please build frontend first.</h1>", status_code=404, media_type="text/html")

if __name__ == "__main__":
    import uvicorn
    print("=" * 80)
    print(" ESP APM PLATFORM — SERVER 3 FRONTEND DASHBOARD SERVICE")
    print("=" * 80)
    print(f" Dashboard URL      : http://{FRONTEND_HOST}:{FRONTEND_PORT}")
    print(f" Reverse Proxying To: {BACKEND_HTTP_BASE} and {BACKEND_WS_BASE}")
    print(f" Agent Gateway URL  : {AGENT_GATEWAY_URL}")
    print("=" * 80)
    uvicorn.run(app, host=FRONTEND_HOST, port=FRONTEND_PORT, log_level="info")
