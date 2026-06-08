"""
Minimal RAG service:
  1. Extract keywords from user question via jieba
  2. Retrieve relevant posts from DB
  3. Pack context + question into a prompt
  4. Stream response from DeepSeek (OpenAI-compatible API)
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import AsyncGenerator, Optional

import httpx
import jieba
import jieba.analyse
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.services.search import search_posts_for_rag

settings = get_settings()

_WEEKDAYS = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]


def _fmt_time(iso_str: str) -> str:
    """把 ISO 时间格式化成人类友好的中文日期。"""
    if not iso_str:
        return "时间未知"
    try:
        dt = datetime.fromisoformat(iso_str)
        return f"{dt.year}年{dt.month}月{dt.day}日 {_WEEKDAYS[dt.weekday()]} {dt.hour:02d}:{dt.minute:02d}"
    except (ValueError, TypeError):
        return iso_str

_SETTINGS_PREFIX = "admin:setting:"


async def _get_runtime_setting(redis, key: str, default: str) -> str:
    """从 Redis 读取后台动态覆盖的设置，没有则返回 .env 默认值。"""
    if redis is None:
        return default
    try:
        val = await redis.get(f"{_SETTINGS_PREFIX}{key}")
        if val is not None:
            return val
    except Exception:
        pass
    return default

DEFAULT_SYSTEM_PROMPT = (
    "你是一位友好、健谈的校园生活助手，了解中国大学校园的方方面面。"
    "下方会附带一些校园墙上的真实帖子作为补充资料，每条帖子都标注了发布时间和分类，仅供参考。"
    "\n\n回答原则："
    "\n1. 如果资料中有直接相关的内容，请优先结合资料回答，并自然地融入你的理解。"
    "\n2. 如果资料中没有相关内容，**禁止**说『文档中未提及』『数据库未提及』『参考资料里没有』之类的话，"
    "也不要让用户感觉你只是个查询工具。直接根据你自己的常识尽你所能地回答即可。"
    "\n3. 涉及具体校园事务（具体食堂菜品、某节课老师、某个学院联系方式等本校独有信息）时，"
    "如果资料里没有，可以友好地建议用户去问问周围同学或者去学校官网，但同时给出通用建议。"
    "\n4. 关于时间：只能依据每条帖子标注的『发布时间』来描述时间，禁止编造或臆测时间。"
    "若用户问『最近/最新/今天』，请对照下方给出的当前日期与帖子发布时间来判断，不要凭空说日期。"
    "\n5. 语气要轻松自然，像同学聊天一样，可以适当用一些口语化表达。"
    "\n6. 回答力求简洁、有信息量，避免冗长说教，避免过度免责声明。"
)

# 兼容老引用
SYSTEM_PROMPT = DEFAULT_SYSTEM_PROMPT


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
        time_str = _fmt_time(p.get("created_at", ""))
        category = p.get("category") or "未分类"
        parts.append(
            f"[帖子{i}] 发布时间：{time_str}｜分类：{category}\n内容：{p['content']}"
        )
    return "\n\n".join(parts)


def _sanitize_history(history, max_turns: int) -> list:
    """清洗前端传来的历史消息，只保留最近 max_turns 轮（user+assistant 算一轮）。"""
    if not history or max_turns <= 0:
        return []
    cleaned = []
    for m in history:
        if not isinstance(m, dict):
            continue
        role = m.get("role")
        content = (m.get("content") or "").strip()
        if role in ("user", "assistant") and content:
            cleaned.append({"role": role, "content": content[:1000]})
    # 保留最近 max_turns*2 条消息
    return cleaned[-(max_turns * 2):]


def _build_sources(posts: list[dict]) -> list[dict]:
    """提炼引用贴文的精简信息，供前端展示信息源卡片。"""
    sources = []
    for p in posts:
        content = (p.get("content") or "").strip()
        sources.append({
            "id": p.get("id"),
            "summary": content[:50] + ("…" if len(content) > 50 else ""),
            "category": p.get("category") or "",
            "created_at": p.get("created_at"),
        })
    return sources


async def stream_chat(
    db: AsyncSession,
    question: str,
    redis=None,
    history=None,
) -> AsyncGenerator[dict, None]:
    """以结构化事件流式输出：先 {"type":"sources"}，再多条 {"type":"content"}。"""
    keywords = extract_keywords(question)
    posts = await search_posts_for_rag(db, keywords, limit=15)
    context = build_context(posts)

    # 先把信息源推给前端
    yield {"type": "sources", "data": _build_sources(posts)}

    now_str = _fmt_time(datetime.now().isoformat())
    if posts:
        user_msg = (
            f"（当前日期：{now_str}）\n\n"
            f"【参考资料】校园墙上的相关帖子：\n\n{context}\n\n【我的问题】{question}"
        )
    else:
        user_msg = (
            f"（当前日期：{now_str}）\n\n"
            f"【我的问题】{question}\n\n（暂未找到相关校园贴文，请基于你的常识回答）"
        )

    system_prompt = await _get_runtime_setting(redis, "system_prompt", DEFAULT_SYSTEM_PROMPT)
    max_turns_str = await _get_runtime_setting(redis, "max_context_turns", "5")
    try:
        max_turns = int(max_turns_str)
    except (ValueError, TypeError):
        max_turns = 5

    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(_sanitize_history(history, max_turns))
    messages.append({"role": "user", "content": user_msg})

    api_key = await _get_runtime_setting(redis, "deepseek_api_key", settings.deepseek_api_key)
    base_url = await _get_runtime_setting(redis, "deepseek_base_url", settings.deepseek_base_url)
    model = await _get_runtime_setting(redis, "deepseek_model", settings.deepseek_model)

    url = f"{base_url}/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": messages,
        "stream": True,
        "max_tokens": 1024,
        "temperature": 1.0,
        "top_p": 0.95,
        "presence_penalty": 0.3,
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
                        yield {"type": "content", "data": content}
                except (json.JSONDecodeError, KeyError, IndexError):
                    continue
