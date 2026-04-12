"""
Chat query logger — stores recent Q&A records in Redis for admin monitoring.
Uses a Redis list capped at 500 entries to avoid unbounded growth.
"""

from __future__ import annotations

import json
import time

from redis.asyncio import Redis

_LOG_KEY = "chat:logs"
_MAX_LOGS = 500


async def log_chat(redis: Redis, openid: str, question: str) -> None:
    entry = json.dumps(
        {"openid": openid, "question": question, "timestamp": time.time()},
        ensure_ascii=False,
    )
    pipe = redis.pipeline()
    pipe.lpush(_LOG_KEY, entry)
    pipe.ltrim(_LOG_KEY, 0, _MAX_LOGS - 1)
    await pipe.execute()


async def get_chat_logs(
    redis: Redis, offset: int = 0, limit: int = 20
) -> tuple[list[dict], int]:
    total = await redis.llen(_LOG_KEY)
    raw_items = await redis.lrange(_LOG_KEY, offset, offset + limit - 1)
    items = []
    for raw in raw_items:
        try:
            items.append(json.loads(raw))
        except json.JSONDecodeError:
            continue
    return items, total


async def get_today_chat_count(redis: Redis) -> int:
    """Count chat queries from today (scans recent entries)."""
    import datetime

    today_start = datetime.datetime.now().replace(
        hour=0, minute=0, second=0, microsecond=0
    ).timestamp()

    total = await redis.llen(_LOG_KEY)
    if total == 0:
        return 0

    count = 0
    batch_size = 50
    for start in range(0, min(total, _MAX_LOGS), batch_size):
        items = await redis.lrange(_LOG_KEY, start, start + batch_size - 1)
        for raw in items:
            try:
                entry = json.loads(raw)
                if entry.get("timestamp", 0) >= today_start:
                    count += 1
                else:
                    return count
            except json.JSONDecodeError:
                continue
    return count
