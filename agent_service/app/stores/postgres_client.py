"""
PostgreSQL Client & Connection Pool Manager for ESP APM Database.
Connects to centralized esp_apm_db on Server 184 (Port 5433).
"""

import os
from contextlib import contextmanager
from typing import Generator
import psycopg2
from psycopg2.pool import ThreadedConnectionPool

_PG_POOL: ThreadedConnectionPool | None = None

def get_database_url() -> str:
    return os.getenv(
        "DATABASE_URL",
        "postgresql://esp_admin:EspApm2026!@192.168.1.184:5433/esp_apm_db"
    )

def get_postgres_pool() -> ThreadedConnectionPool:
    global _PG_POOL
    if _PG_POOL is None or _PG_POOL.closed:
        db_url = get_database_url()
        _PG_POOL = ThreadedConnectionPool(minconn=1, maxconn=20, dsn=db_url, connect_timeout=3)
    return _PG_POOL

@contextmanager
def get_db_cursor() -> Generator[psycopg2.extensions.cursor, None, None]:
    """Context manager for obtaining a pooled PostgreSQL connection and cursor."""
    pool = get_postgres_pool()
    conn = pool.getconn()
    try:
        with conn.cursor() as cur:
            yield cur
            conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        pool.putconn(conn)
