"""
ESP Agent BFF Gateway Entrypoint for Uvicorn / ASGI servers.
Exposes FastAPI application instance `app` from `src.api.rest.gateway`.
"""

from src.api.rest.gateway import app

__all__ = ["app"]
