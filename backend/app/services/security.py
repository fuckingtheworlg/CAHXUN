"""
WeChat content security — msgSecCheck API.
"""

import httpx
from redis.asyncio import Redis

from app.utils.wechat_token import get_access_token


async def msg_sec_check(redis: Redis, openid: str, content: str) -> bool:
    """
    Returns True if the content passes WeChat security check.
    Returns False if rejected (or on API error, fail-open can be toggled).
    """
    token = await get_access_token(redis)
    if not token:
        return True  # fail-open when token unavailable

    url = f"https://api.weixin.qq.com/wxa/msg_sec_check?access_token={token}"
    payload = {
        "version": 2,
        "openid": openid,
        "scene": 2,  # 2 = comment scene
        "content": content,
    }

    async with httpx.AsyncClient() as client:
        resp = await client.post(url, json=payload)
        data = resp.json()

    # errcode 0 means success; result.suggest == "pass" means safe
    if data.get("errcode", -1) != 0:
        return True  # fail-open on API error
    result = data.get("result", {})
    return result.get("suggest") == "pass"
