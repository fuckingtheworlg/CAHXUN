"""
Redis sliding-window rate limiter.
"""

from __future__ import annotations

import time
from typing import Optional

from redis.asyncio import Redis

from app.config import get_settings

settings = get_settings()


async def check_rate_limit(redis: Redis, openid: str) -> bool:
    """
    Returns True if the request is allowed, False if rate-limited.
    Uses a sorted-set sliding window keyed by openid.
    """
    key = f"ratelimit:{openid}"
    now = time.time()
    window = 60.0  # 1-minute window
    max_requests = settings.rate_limit_per_minute

    pipe = redis.pipeline()
    pipe.zremrangebyscore(key, 0, now - window)
    pipe.zadd(key, {f"{now}": now})
    pipe.zcard(key)
    pipe.expire(key, int(window) + 1)
    results = await pipe.execute()

    current_count = results[2]
    return current_count <= max_requests


async def get_openid_from_token(redis: Redis, token: str) -> Optional[str]:
    """Resolve session token to openid."""
    if not token:
        return None
    return await redis.get(f"session:{token}")
