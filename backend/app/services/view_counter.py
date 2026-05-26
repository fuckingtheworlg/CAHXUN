"""
Post view counter — track view counts in Redis (no DB migration needed).

Storage:
  - Sorted set "post:views" — score = view count, member = post_id
  - Used by GET /posts/popular to fetch top N posts.
"""

from __future__ import annotations

from typing import List, Tuple

from redis.asyncio import Redis

_VIEW_KEY = "post:views"


async def record_view(redis: Redis, post_id: int) -> int:
    """记录一次浏览，返回当前浏览量。"""
    if redis is None:
        return 0
    return int(await redis.zincrby(_VIEW_KEY, 1, str(post_id)))


async def get_view_count(redis: Redis, post_id: int) -> int:
    if redis is None:
        return 0
    score = await redis.zscore(_VIEW_KEY, str(post_id))
    return int(score) if score else 0


async def get_views_for_posts(redis: Redis, post_ids: List[int]) -> dict:
    """批量取多个 post 的浏览量。"""
    if redis is None or not post_ids:
        return {}
    pipe = redis.pipeline()
    for pid in post_ids:
        pipe.zscore(_VIEW_KEY, str(pid))
    scores = await pipe.execute()
    return {
        pid: int(s) if s else 0
        for pid, s in zip(post_ids, scores)
    }


async def get_top_post_ids(redis: Redis, limit: int = 10) -> List[Tuple[int, int]]:
    """返回 [(post_id, view_count), ...]，按浏览量降序。"""
    if redis is None:
        return []
    rows = await redis.zrevrange(_VIEW_KEY, 0, limit - 1, withscores=True)
    return [(int(pid), int(score)) for pid, score in rows]
