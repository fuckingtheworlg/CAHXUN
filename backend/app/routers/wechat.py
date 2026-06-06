"""
WeChat login — exchange js_code for session (openid)，并 upsert User 记录。
"""

from __future__ import annotations

import hashlib
import secrets
from datetime import datetime

import httpx
from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.models import User

settings = get_settings()
router = APIRouter(tags=["auth"])


class LoginRequest(BaseModel):
    code: str


class LoginResponse(BaseModel):
    token: str
    openid: str


@router.post("/login", response_model=LoginResponse)
async def login(
    body: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
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

    # upsert User
    now = datetime.now()
    try:
        user = (
            await db.execute(select(User).where(User.openid == openid))
        ).scalar_one_or_none()

        if user is None:
            user = User(
                openid=openid,
                created_at=now,
                last_login_at=now,
                last_seen_at=now,
                login_count=1,
                is_banned=False,
            )
            db.add(user)
        else:
            if user.is_banned:
                reason = user.ban_reason or "违规行为"
                raise HTTPException(status_code=403, detail=f"账号已被封禁：{reason}")
            user.last_login_at = now
            user.last_seen_at = now
            user.login_count = (user.login_count or 0) + 1
        await db.commit()
    except HTTPException:
        raise
    except Exception:
        await db.rollback()
        # 不影响登录，仅记录用户表失败

    # Generate a simple session token and store openid mapping in Redis
    token = hashlib.sha256(
        f"{openid}:{secrets.token_hex(16)}".encode()
    ).hexdigest()

    redis = request.app.state.redis
    await redis.set(f"session:{token}", openid, ex=86400 * 7)  # 7 days

    return LoginResponse(token=token, openid=openid)
