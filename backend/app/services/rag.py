"""
Minimal RAG service:
  1. Extract keywords from user question via jieba
  2. Retrieve relevant posts from DB
  3. Pack context + question into a prompt
  4. Stream response from DeepSeek (OpenAI-compatible API)
"""

from __future__ import annotations

import json
from typing import AsyncGenerator

import httpx
import jieba
import jieba.analyse
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.services.search import search_posts_for_rag

settings = get_settings()

SYSTEM_PROMPT = (
    "你是校园墙智能助手。用户会向你提问关于校园生活的问题，"
    "下面提供了一些校园墙上的真实帖子作为参考资料。"
    "请根据这些帖子内容来回答用户的问题。"
    "如果提供的帖子中没有相关信息，请如实告知用户你未找到相关内容。"
    "回答要简洁、友好、有帮助。"
)


def extract_keywords(question: str, topk: int = 5) -> list[str]:
    keywords = jieba.analyse.extract_tags(question, topK=topk)
    if not keywords:
        keywords = [w for w in jieba.cut(question) if len(w) >= 2]
    return keywords[:topk]


def build_context(posts: list[dict]) -> str:
    if not posts:
        return "（暂无相关帖子）"
    parts = []
    for i, p in enumerate(posts, 1):
        time_str = p.get("created_at", "未知时间")
        parts.append(f"帖子{i}（{time_str}）：{p['content']}")
    return "\n\n".join(parts)


async def stream_chat(
    db: AsyncSession,
    question: str,
) -> AsyncGenerator[str, None]:
    keywords = extract_keywords(question)
    posts = await search_posts_for_rag(db, keywords, limit=15)
    context = build_context(posts)

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": f"以下是校园墙上的相关帖子：\n\n{context}\n\n我的问题是：{question}",
        },
    ]

    url = f"{settings.deepseek_base_url}/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.deepseek_api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": settings.deepseek_model,
        "messages": messages,
        "stream": True,
        "max_tokens": 1024,
        "temperature": 0.7,
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        async with client.stream("POST", url, json=payload, headers=headers) as resp:
            async for line in resp.aiter_lines():
                if not line.startswith("data: "):
                    continue
                data = line[6:]
                if data.strip() == "[DONE]":
                    break
                try:
                    chunk = json.loads(data)
                    delta = chunk["choices"][0].get("delta", {})
                    content = delta.get("content", "")
                    if content:
                        yield content
                except (json.JSONDecodeError, KeyError, IndexError):
                    continue
