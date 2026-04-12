"""
Search service — LIKE fuzzy query with optional FULLTEXT upgrade.

If a FULLTEXT INDEX exists on the content column, set USE_FULLTEXT=true
in env to switch to MATCH ... AGAINST for better performance.
"""

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
) -> list[dict]:
    """Retrieve posts matching any of the given keywords, for RAG context."""
    if not keywords:
        return []

    conditions = [Post.content.like(f"%{kw}%") for kw in keywords]
    q = (
        select(Post)
        .where(or_(*conditions))
        .order_by(desc(Post.created_at))
        .limit(limit)
    )
    rows = (await db.execute(q)).scalars().all()
    return [r.to_dict() for r in rows]
