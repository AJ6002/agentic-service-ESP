import os
import redis
from dotenv import load_dotenv

load_dotenv()

_redis_pool = None

def get_redis_client() -> redis.Redis:
    global _redis_pool
    if _redis_pool is None:
        redis_url = os.getenv("REDIS_URL", "redis://127.0.0.1:6381/0")
        _redis_pool = redis.ConnectionPool.from_url(
            redis_url,
            decode_responses=True,
            protocol=2,
        )
    return redis.Redis(connection_pool=_redis_pool)
