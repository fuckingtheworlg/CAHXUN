from __future__ import annotations

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Post
from app.services.search import search_posts

router = APIRouter(tags=["posts"])


@router.get("/posts")
async def list_posts(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    offset = (page - 1) * page_size

    count_result = await db.execute(select(func.count()).select_from(Post))
    total = count_result.scalar()

    result = await db.execute(
        select(Post).order_by(desc(Post.created_at)).offset(offset).limit(page_size)
    )
    posts = result.scalars().all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [p.to_dict() for p in posts],
    }


@router.get("/posts/search")
async def search(
    q: str = Query(..., min_length=1, max_length=100),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    if not q.strip():
        raise HTTPException(status_code=400, detail="搜索关键词不能为空")
    return await search_posts(db, q.strip(), page, page_size)
