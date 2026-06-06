from __future__ import annotations

import logging
from contextlib import asynccontextmanager

import redis.asyncio as aioredis
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import engine
from app.models import Base, User  # noqa: F401（确保模型注册到 metadata）
from app.routers import posts, chat, wechat, admin, upload

settings = get_settings()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.redis = aioredis.from_url(
        settings.redis_url, decode_responses=True
    )

    # 启动时确保 users 表存在（已存在则跳过；posts 表不会被重建）
    try:
        async with engine.begin() as conn:
            await conn.run_sync(
                lambda c: Base.metadata.create_all(c, tables=[User.__table__])
            )
        logger.info("users 表检查/创建完成")
    except Exception as e:
        logger.warning("users 表自动创建失败（如权限不足请手动建表）：%s", e)

    yield
    await app.state.redis.close()


app = FastAPI(title="校园墙查询", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(posts.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(wechat.router, prefix="/api/auth")
app.include_router(admin.router, prefix="/api")
app.include_router(upload.router, prefix="/api")


@app.get("/health")
async def health():
    return {"status": "ok"}
