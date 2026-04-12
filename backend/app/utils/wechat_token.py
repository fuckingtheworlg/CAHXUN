"""
WeChat access_token manager — cached in Redis with TTL.
"""

import httpx
from redis.asyncio import Redis

from app.config import get_settings

settings = get_settings()

_TOKEN_KEY = "wechat:access_token"
_TOKEN_TTL = 7000  # official validity 7200s, refresh a bit early


async def get_access_token(redis: Redis) -> str:
    cached = await redis.get(_TOKEN_KEY)
    if cached:
        return cached

    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://api.weixin.qq.com/cgi-bin/token",
            params={
                "grant_type": "client_credential",
                "appid": settings.wechat_appid,
                "secret": settings.wechat_secret,
            },
        )
        data = resp.json()

    token = data.get("access_token", "")
    if token:
        await redis.set(_TOKEN_KEY, token, ex=_TOKEN_TTL)
    return token
