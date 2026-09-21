"""
Conversation Store — Level A Memory Tier
Plan.md Phase A1

Redis-backed per-session conversation history. Reuses the singleton
RedisConnectionManager from checkpoint.py — no second Redis client is opened.

Key scheme:  esp:conv:{session_id}
Value:       JSON list of turn dicts, newest last, trimmed to 20 stored.
TTL:         7 days (refreshed on every append).

Per-turn schema:
  { role, content, timestamp, well_id, intent_detected }

Methods:
  append(session_id, role, content, well_id=None, intent=None)
  get_history(session_id, limit=10)  -> last N turns
  get_last_well(session_id)           -> most recent non-null well_id
  clear(session_id)
"""

import os
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

from src.events.redis_connection import RedisConnectionManager

logger = logging.getLogger(__name__)

_CONV_TTL_SECONDS = 7 * 24 * 3600   # 7 days
_MAX_STORED_TURNS  = 20              # keep last 20; serve last 10
_KEY_PREFIX        = "esp:conv:"


class ConversationStore:
    """
    Session-scoped conversation history backed by the shared Redis singleton.
    Falls back to an in-process dict when Redis is unavailable (mirrors
    CheckpointManager's degradation behaviour per Plan.md A1).
    """

    def __init__(self, connection_mgr: Optional[RedisConnectionManager] = None):
        # Reuse existing singleton — do NOT open a new client.
        self.connection_mgr = connection_mgr or RedisConnectionManager()
        self._redis = self.connection_mgr
        # In-memory fallback: session_id -> list[turn]
        self._fallback: Dict[str, List[Dict[str, Any]]] = {}


    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def append(
        self,
        session_id: str,
        role: str,
        content: str,
        well_id: Optional[str] = None,
        intent: Optional[str] = None,
    ) -> None:
        """Push one turn, trim to last _MAX_STORED_TURNS, refresh TTL."""
        turn = {
            "role": role,
            "content": content,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "well_id": well_id,
            "intent_detected": intent,
        }
        turns = self._load(session_id)
        turns.append(turn)
        if len(turns) > _MAX_STORED_TURNS:
            turns = turns[-_MAX_STORED_TURNS:]
        self._save(session_id, turns)

    def get_history(self, session_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Return the most recent `limit` turns (sliding window)."""
        turns = self._load(session_id)
        return turns[-limit:] if len(turns) > limit else turns

    def push_asset(self, session_id: str, asset_id: str) -> None:
        """
        Record or bump an asset on the session's active multi-asset stack.
        Ensures the most recent explicit reference is at stack top.
        """
        if not asset_id or asset_id in ("UNKNOWN", "NONE", "FLEET"):
            return
        turns = self._load(session_id)
        if turns:
            last_turn = turns[-1]
            if last_turn.get("well_id") == asset_id:
                return
            if not last_turn.get("well_id"):
                last_turn["well_id"] = asset_id
                self._save(session_id, turns)
                return

        self.append(session_id, role="system", content=f"Grounding context: {asset_id}", well_id=asset_id)

    def get_active_asset_stack(self, session_id: str, max_staleness: int = 3) -> List[str]:
        """
        Return active, non-stale asset identifiers from recent turns.
        Implements:
        1. Multi-asset stack order (most recent first).
        2. Staleness eviction (wells not re-referenced within last `max_staleness` user turns are excluded).
        3. Topic-shift eviction: If a turn has a fleet intent, single-asset context before that turn is cut off.
        """
        turns = self._load(session_id)
        if not turns:
            return []

        fleet_objectives = {
            "OP08_FLEET_INVENTORY", "OP09_FLEET_PRODUCTION_OPTIMIZATION",
            "OP10_FLEET_DESIGN_SIZING", "OP11_FLEET_MAINTENANCE_PRIORITY",
            "OP12_FLEET_CASE_ANALYTICS", "OP13_FLEET_EXECUTIVE_REPORTING",
            "OP13_FLEET_EXECUTIVE_REPORT", "FLEET", "GLOBAL_FLEET"
        }

        active_stack: List[str] = []
        user_turn_count = 0

        for turn in reversed(turns):
            intent = (turn.get("intent_detected") or "").upper()
            if intent in fleet_objectives:
                break

            if turn.get("role") == "user":
                user_turn_count += 1
                if user_turn_count > max_staleness:
                    break

            wells_in_turn = []
            if turn.get("well_ids"):
                wells_in_turn = turn.get("well_ids")
            elif turn.get("well_id"):
                wells_in_turn = [turn.get("well_id")]

            for w in wells_in_turn:
                if w and w not in active_stack and w not in ("UNKNOWN", "NONE", "FLEET"):
                    active_stack.append(w)
                    if len(active_stack) >= 3:
                        break
            if len(active_stack) >= 3:
                break

        return active_stack

    def evict_asset_stack(self, session_id: str) -> None:
        """Explicitly evict the single-asset stack (e.g. upon fleet query or reset)."""
        turns = self._load(session_id)
        if turns:
            self.append(session_id, role="system", content="Context reset: fleet mode", well_id=None, intent="FLEET")

    def get_last_well(self, session_id: str, max_staleness: Optional[int] = None) -> Optional[str]:
        """Return the most recent non-null well_id seen in this session."""
        if max_staleness is not None:
            stack = self.get_active_asset_stack(session_id, max_staleness=max_staleness)
            return stack[0] if stack else None

        turns = self._load(session_id)
        for turn in reversed(turns):
            w = turn.get("well_id")
            if w and w not in ("UNKNOWN", "NONE", "FLEET"):
                return w
        return None

    def _get_sqlite_db_path(self) -> str:
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        data_dir = os.path.join(base_dir, "data")
        os.makedirs(data_dir, exist_ok=True)
        return os.path.join(data_dir, "conversations.db")

    def _init_sqlite_db(self) -> None:
        import sqlite3
        try:
            db_path = self._get_sqlite_db_path()
            with sqlite3.connect(db_path, timeout=5.0) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS conversation_sessions (
                        session_id TEXT PRIMARY KEY,
                        turns TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    );
                """)
                conn.commit()
        except Exception as exc:
            logger.debug("[ConversationStore] SQLite init failed: %s", exc)

    def _load_from_sqlite(self, session_id: str) -> List[Dict[str, Any]]:
        import sqlite3
        try:
            db_path = self._get_sqlite_db_path()
            if not os.path.exists(db_path):
                return []
            with sqlite3.connect(db_path, timeout=5.0) as conn:
                cursor = conn.cursor()
                row = cursor.execute(
                    "SELECT turns FROM conversation_sessions WHERE session_id = ?",
                    (session_id,)
                ).fetchone()
                if row and row[0]:
                    return json.loads(row[0])
        except Exception as exc:
            logger.debug("[ConversationStore] SQLite load failed for %s: %s", session_id, exc)
        return []

    def _save_to_sqlite(self, session_id: str, turns: List[Dict[str, Any]]) -> None:
        import sqlite3
        try:
            self._init_sqlite_db()
            db_path = self._get_sqlite_db_path()
            now_iso = datetime.now(timezone.utc).isoformat()
            with sqlite3.connect(db_path, timeout=5.0) as conn:
                conn.execute(
                    "INSERT OR REPLACE INTO conversation_sessions (session_id, turns, updated_at) VALUES (?, ?, ?)",
                    (session_id, json.dumps(turns), now_iso)
                )
                conn.commit()
        except Exception as exc:
            logger.debug("[ConversationStore] SQLite save failed for %s: %s", session_id, exc)

    def _delete_from_sqlite(self, session_id: str) -> None:
        import sqlite3
        try:
            db_path = self._get_sqlite_db_path()
            if os.path.exists(db_path):
                with sqlite3.connect(db_path, timeout=5.0) as conn:
                    conn.execute("DELETE FROM conversation_sessions WHERE session_id = ?", (session_id,))
                    conn.commit()
        except Exception as exc:
            logger.debug("[ConversationStore] SQLite delete failed for %s: %s", session_id, exc)

    def clear(self, session_id: str) -> None:
        """Delete the conversation for this session from Redis, SQLite, and in-memory fallback."""
        key = _KEY_PREFIX + session_id
        self._fallback.pop(session_id, None)
        self._delete_from_sqlite(session_id)
        try:
            self._redis.get_client().delete(key)
        except Exception as exc:
            logger.warning("[ConversationStore] Redis delete failed for %s: %s", session_id, exc)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _load(self, session_id: str) -> List[Dict[str, Any]]:
        # 1. Try Redis first
        key = _KEY_PREFIX + session_id
        try:
            raw = self._redis.get_client().get(key)
            if raw:
                turns = json.loads(raw)
                self._fallback[session_id] = turns
                return turns
        except Exception as exc:
            logger.debug("[ConversationStore] Redis load failed for %s: %s — checking local storage", session_id, exc)

        # 2. Check in-memory fallback
        if session_id in self._fallback:
            return list(self._fallback[session_id])

        # 3. Check persistent SQLite fallback on disk
        sqlite_turns = self._load_from_sqlite(session_id)
        if sqlite_turns:
            self._fallback[session_id] = sqlite_turns
            return sqlite_turns

        return []

    def _save(self, session_id: str, turns: List[Dict[str, Any]]) -> None:
        key = _KEY_PREFIX + session_id
        payload = json.dumps(turns)
        # Always keep in-memory fallback and SQLite disk fallback in sync
        self._fallback[session_id] = turns
        self._save_to_sqlite(session_id, turns)
        try:
            self._redis.get_client().set(key, payload, ex=_CONV_TTL_SECONDS)
        except Exception as exc:
            logger.debug("[ConversationStore] Redis save failed for %s: %s — stored in SQLite fallback", session_id, exc)
