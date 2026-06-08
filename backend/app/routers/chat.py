"""
AI Chat endpoint — SSE streaming response.
"""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException, Request, Header
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse

from app.database import get_db
from app.services.rag import stream_chat
from app.services.security import msg_sec_check
from app.services.rate_limiter import check_rate_limit, get_openid_from_token
from app.services.chat_logger import log_chat

router = APIRouter(tags=["chat"])


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    question: str
    history: list = []


@router.post("/chat")
async def chat(
    body: ChatRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    authorization: str = Header(default=""),
):
    redis = request.app.state.redis
    token = authorization.removeprefix("Bearer ").strip()
    openid = await get_openid_from_token(redis, token)

    if not openid:
        raise HTTPException(status_code=401, detail="请先登录")

    question = body.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="问题不能为空")
    if len(question) > 500:
        raise HTTPException(status_code=400, detail="问题过长，请控制在500字以内")

    allowed = await check_rate_limit(redis, openid)
    if not allowed:
        raise HTTPException(status_code=429, detail="提问太频繁，请稍后再试")

    is_safe = await msg_sec_check(redis, openid, question)
    if not is_safe:
        raise HTTPException(status_code=400, detail="输入内容包含违规信息，请修改后重试")

    await log_chat(redis, openid, question)

    history = body.history or []

    async def event_generator():
        async for evt in stream_chat(db, question, redis=redis, history=history):
            if evt["type"] == "sources":
                yield {"data": json.dumps({"sources": evt["data"]}, ensure_ascii=False)}
            else:
                yield {"data": json.dumps({"content": evt["data"]}, ensure_ascii=False)}
        yield {"data": "[DONE]"}

    return EventSourceResponse(event_generator())
