"""
Agent View-Awareness and Bidirectional Control WebSocket (/ws/agent)
Decouples agent view-tracking and plan actions from high-frequency telemetry (/ws/live).
Caches active on-screen widgets, titles, and target assets in Redis with 120s TTL.
"""

import json
import logging
import time
from typing import Any, Dict, Optional, Set

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from src.agent.v2.plan_repository import PlanRepository
from src.agent.v2.plan_schema import PlanStepStatus
from src.services.chart_catalog import resolve_chart_from_title

logger = logging.getLogger("agent_ws")

router = APIRouter(tags=["agent_ws"])

_ACTIVE_AGENT_SOCKETS: Set[WebSocket] = set()
_IN_MEMORY_VIEW_CACHE: Dict[str, Dict[str, Any]] = {}


def get_redis_client():
    """Returns a Redis client instance or None if redis is unavailable."""
    try:
        import redis
        import os
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        client = redis.from_url(redis_url, decode_responses=True, socket_timeout=1.0)
        client.ping()
        return client
    except Exception:
        return None


def get_cached_view(session_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieves the currently cached view state for the given session.
    Checks Redis (esp:view:{session_id}) first, then in-memory fallback.
    """
    if not session_id:
        return None

    r = get_redis_client()
    if r:
        try:
            val = r.get(f"esp:view:{session_id}")
            if val:
                return json.loads(val)
        except Exception as exc:
            logger.debug("Redis view lookup error: %s", exc)

    return _IN_MEMORY_VIEW_CACHE.get(session_id)


def save_cached_view(session_id: str, view_data: Dict[str, Any], ttl: int = 120) -> None:
    """
    Caches the view state for the session in Redis (120s TTL) and in-memory.
    """
    if not session_id:
        return

    view_data["updated_at"] = time.time()
    _IN_MEMORY_VIEW_CACHE[session_id] = view_data

    r = get_redis_client()
    if r:
        try:
            r.set(f"esp:view:{session_id}", json.dumps(view_data), ex=ttl)
        except Exception as exc:
            logger.debug("Redis view save error: %s", exc)


@router.websocket("/ws/agent")
async def websocket_agent_endpoint(websocket: WebSocket):
    """
    Dedicated bidirectional WebSocket connection for Agent View Awareness and Plan Actions.
    Protocol:
    - VIEW_UPDATE: { "type": "VIEW_UPDATE", "session_id": str, "active_widget": str, "active_title": str, "target_asset": str, ... }
    - PLAN_ACTION: { "type": "PLAN_ACTION", "session_id": str, "run_id": str, "action": "APPROVE"|"REJECT", "comment": str }
    - HEARTBEAT:   { "type": "HEARTBEAT" }
    """
    await websocket.accept()
    _ACTIVE_AGENT_SOCKETS.add(websocket)
    logger.info("Agent WebSocket client connected. Active connections: %d", len(_ACTIVE_AGENT_SOCKETS))

    try:
        while True:
            raw_text = await websocket.receive_text()
            if not raw_text:
                continue

            try:
                msg = json.loads(raw_text)
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({"type": "ERROR", "message": "Invalid JSON format"}))
                continue

            msg_type = msg.get("type", "").upper()

            if msg_type in ("PING", "HEARTBEAT"):
                await websocket.send_text(json.dumps({"type": "PONG", "timestamp": time.time()}))

            elif msg_type == "VIEW_UPDATE":
                session_id = msg.get("session_id") or "default_session"
                active_widget = msg.get("active_widget")
                active_title = msg.get("active_title", "")
                target_asset = msg.get("target_asset", "")

                # Resolve chart spec from title if provided
                if active_title and not active_widget:
                    spec = resolve_chart_from_title(active_title)
                    if spec:
                        active_widget = spec["id"]

                view_data = {
                    "session_id": session_id,
                    "active_widget": active_widget,
                    "active_title": active_title,
                    "target_asset": target_asset,
                    "scroll_pct": msg.get("scroll_pct", 0.0),
                    "visible_range": msg.get("visible_range", "1h"),
                }
                save_cached_view(session_id, view_data, ttl=120)

                await websocket.send_text(json.dumps({
                    "type": "VIEW_ACK",
                    "session_id": session_id,
                    "active_widget": active_widget,
                    "target_asset": target_asset,
                    "status": "CACHED",
                }))

            elif msg_type == "PLAN_ACTION":
                run_id = msg.get("run_id")
                action = (msg.get("action") or "").strip().upper()
                comment = msg.get("comment")

                if not run_id or action not in ("APPROVE", "REJECT"):
                    await websocket.send_text(json.dumps({
                        "type": "ERROR",
                        "message": "PLAN_ACTION requires valid 'run_id' and 'action' ('APPROVE' or 'REJECT')",
                    }))
                    continue

                repo = PlanRepository()
                plan = repo.get_plan(run_id)
                if not plan:
                    await websocket.send_text(json.dumps({
                        "type": "ERROR",
                        "message": f"Plan '{run_id}' not found",
                    }))
                    continue

                if action == "APPROVE":
                    updated = repo.set_approval_status(run_id, is_approved=True)
                    await websocket.send_text(json.dumps({
                        "type": "PLAN_ACTION_ACK",
                        "run_id": run_id,
                        "action": "APPROVE",
                        "status": "APPROVED",
                        "plan": updated.dict() if updated else plan.dict(),
                    }))
                else:
                    updated = repo.update_step_status(
                        run_id,
                        step_id=1,
                        status=PlanStepStatus.SKIPPED,
                        observation=comment or "Plan rejected by operator via agent websocket",
                    )
                    await websocket.send_text(json.dumps({
                        "type": "PLAN_ACTION_ACK",
                        "run_id": run_id,
                        "action": "REJECT",
                        "status": "REJECTED",
                        "plan": updated.dict() if updated else plan.dict(),
                    }))

            else:
                await websocket.send_text(json.dumps({
                    "type": "UNKNOWN_EVENT",
                    "event": msg_type,
                }))

    except WebSocketDisconnect:
        logger.info("Agent WebSocket client disconnected normally.")
    except Exception as exc:
        logger.warning("Agent WebSocket error: %s", exc)
    finally:
        _ACTIVE_AGENT_SOCKETS.discard(websocket)
