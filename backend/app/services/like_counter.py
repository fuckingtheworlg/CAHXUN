"""
Post like service — Redis-based like counter with per-user dedup.

Storage:
  - Sorted set "post:likes" — score = like count, member = post_id (用于排序/查询)
  - Set "post:likers:{post_id}" — openids that liked this post (用于去重 & 取消)
"""

from __future__ import annotations

from typing import List

from redis.asyncio import Redis

_LIKE_COUNT_KEY = "post:likes"


def _likers_key(post_id: int) -> str:
    return f"post:likers:{post_id}"


async def like_post(redis: Redis, post_id: int, openid: str) -> dict:
    """点赞。返回 {liked: bool, count: int}。已点过则返回当前状态不重复加分。"""
    if redis is None:
        return {"liked": False, "count": 0}

    likers = _likers_key(post_id)
    already = await redis.sismember(likers, openid)
    if already:
        score = await redis.zscore(_LIKE_COUNT_KEY, str(post_id))
        return {"liked": True, "count": int(score or 0)}

    pipe = redis.pipeline()
    pipe.sadd(likers, openid)
    pipe.zincrby(_LIKE_COUNT_KEY, 1, str(post_id))
    results = await pipe.execute()
    new_count = int(results[1])
    return {"liked": True, "count": new_count}


async def unlike_post(redis: Redis, post_id: int, openid: str) -> dict:
    """取消点赞。返回 {liked: bool, count: int}。"""
    if redis is None:
        return {"liked": False, "count": 0}

    likers = _likers_key(post_id)
    was_liked = await redis.sismember(likers, openid)
    if not was_liked:
        score = await redis.zscore(_LIKE_COUNT_KEY, str(post_id))
        return {"liked": False, "count": int(score or 0)}

    pipe = redis.pipeline()
    pipe.srem(likers, openid)
    pipe.zincrby(_LIKE_COUNT_KEY, -1, str(post_id))
    results = await pipe.execute()
    new_count = int(results[1])
    if new_count <= 0:
        await redis.zrem(_LIKE_COUNT_KEY, str(post_id))
        new_count = 0
    return {"liked": False, "count": new_count}


async def get_like_info(redis: Redis, post_id: int, openid: str = "") -> dict:
    """查询单条贴文的点赞数与当前用户是否点赞。"""
    if redis is None:
        return {"liked": False, "count": 0}
    pipe = redis.pipeline()
    pipe.zscore(_LIKE_COUNT_KEY, str(post_id))
    if openid:
        pipe.sismember(_likers_key(post_id), openid)
    results = await pipe.execute()
    score = results[0]
    liked = bool(results[1]) if openid else False
    return {"liked": liked, "count": int(score or 0)}


async def get_likes_for_posts(redis: Redis, post_ids: List[int]) -> dict:
    """批量取多个 post 的点赞量。返回 {post_id: count}。"""
    if redis is None or not post_ids:
        return {}
    pipe = redis.pipeline()
    for pid in post_ids:
        pipe.zscore(_LIKE_COUNT_KEY, str(pid))
    scores = await pipe.execute()
    return {
        pid: int(s) if s else 0
        for pid, s in zip(post_ids, scores)
    }
