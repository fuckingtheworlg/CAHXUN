"""
WeChat login — exchange js_code for session (openid).
"""

from __future__ import annotations

import hashlib
import secrets

import httpx
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from app.config import get_settings

settings = get_settings()
router = APIRouter(tags=["auth"])


class LoginRequest(BaseModel):
    code: str


class LoginResponse(BaseModel):
    token: str
    openid: str


@router.post("/login", response_model=LoginResponse)
async def login(body: LoginRequest, request: Request):
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://api.weixin.qq.com/sns/jscode2session",
            params={
                "appid": settings.wechat_appid,
                "secret": settings.wechat_secret,
                "js_code": body.code,
                "grant_type": "authorization_code",
            },
        )
        data = resp.json()

    openid = data.get("openid")
    if not openid:
        raise HTTPException(status_code=401, detail="微信登录失败")

    # Generate a simple session token and store openid mapping in Redis
    token = hashlib.sha256(
        f"{openid}:{secrets.token_hex(16)}".encode()
    ).hexdigest()

    redis = request.app.state.redis
    await redis.set(f"session:{token}", openid, ex=86400 * 7)  # 7 days

    return LoginResponse(token=token, openid=openid)
