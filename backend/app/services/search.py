"""
Search service — LIKE fuzzy query with optional FULLTEXT upgrade.

If a FULLTEXT INDEX exists on the content column, set USE_FULLTEXT=true
in env to switch to MATCH ... AGAINST for better performance.
"""

from __future__ import annotations

from sqlalchemy import select, func, desc, text, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Post


async def search_posts(
    db: AsyncSession,
    keyword: str,
    page: int = 1,
    page_size: int = 20,
    use_fulltext: bool = False,
) -> dict:
    offset = (page - 1) * page_size

    if use_fulltext:
        match_expr = text(
            "MATCH(content) AGAINST(:kw IN BOOLEAN MODE)"
        ).bindparams(kw=keyword)
        where_clause = match_expr
    else:
        where_clause = Post.content.like(f"%{keyword}%")

    count_q = select(func.count()).select_from(Post).where(where_clause)
    total = (await db.execute(count_q)).scalar()

    data_q = (
        select(Post)
        .where(where_clause)
        .order_by(desc(Post.created_at))
        .offset(offset)
        .limit(page_size)
    )
    rows = (await db.execute(data_q)).scalars().all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [r.to_dict() for r in rows],
    }


async def search_posts_for_rag(
    db: AsyncSession,
    keywords: list[str],
    limit: int = 15,
    full_query: str = "",
) -> list[dict]:
    """
    召回 + 相关性打分排序（方案 A）。

    打分规则：
      - 每命中一个不同关键词 +2
      - 关键词在内容中出现的总次数，每次 +0.3（封顶 +3）
      - 命中完整问题串（去空格后）额外 +5
      - 同分时按发布时间新的优先
    召回阶段多取候选（limit*4），打分后截断到 limit。
    """
    if not keywords:
        return []

    conditions = [Post.content.like(f"%{kw}%") for kw in keywords]
    candidate_q = (
        select(Post)
        .where(or_(*conditions))
        .order_by(desc(Post.created_at))
        .limit(limit * 4)
    )
    rows = (await db.execute(candidate_q)).scalars().all()

    cleaned_query = (full_query or "").replace(" ", "").strip()

    def score(post) -> float:
        content = post.content or ""
        s = 0.0
        for kw in keywords:
            if not kw:
                continue
            cnt = content.count(kw)
            if cnt > 0:
                s += 2.0                       # 命中该关键词
                s += min(cnt * 0.3, 3.0)       # 出现频次（封顶）
        if cleaned_query and len(cleaned_query) >= 3 and cleaned_query in content.replace(" ", ""):
            s += 5.0                            # 命中完整问题串
        return s

    def ts(post) -> float:
        try:
            return post.created_at.timestamp() if post.created_at else 0.0
        except Exception:
            return 0.0

    ranked = sorted(rows, key=lambda p: (score(p), ts(p)), reverse=True)
    return [r.to_dict() for r in ranked[:limit]]
