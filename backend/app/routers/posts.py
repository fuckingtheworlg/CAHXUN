from __future__ import annotations

from fastapi import APIRouter, Depends, Query, HTTPException, Request
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Post
from app.services.search import search_posts
from app.services.view_counter import (
    record_view,
    get_views_for_posts,
    get_top_post_ids,
)

router = APIRouter(tags=["posts"])


def _attach_views(items: list, views: dict) -> list:
    for it in items:
        it["view_count"] = views.get(it["id"], 0)
    return items


@router.get("/posts")
async def list_posts(
    request: Request,
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
    items = [p.to_dict() for p in posts]

    redis = request.app.state.redis
    views = await get_views_for_posts(redis, [it["id"] for it in items])
    items = _attach_views(items, views)

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": items,
    }


@router.get("/posts/popular")
async def popular_posts(
    request: Request,
    limit: int = Query(10, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
):
    """按浏览量返回热门贴文 Top N。"""
    redis = request.app.state.redis
    top = await get_top_post_ids(redis, limit)

    if not top:
        return {"items": []}

    ids = [pid for pid, _ in top]
    view_map = {pid: cnt for pid, cnt in top}

    result = await db.execute(select(Post).where(Post.id.in_(ids)))
    posts = result.scalars().all()
    by_id = {p.id: p for p in posts}

    items = []
    for pid in ids:
        post = by_id.get(pid)
        if post is None:
            continue
        d = post.to_dict()
        d["view_count"] = view_map.get(pid, 0)
        items.append(d)

    return {"items": items}


@router.get("/posts/search")
async def search(
    request: Request,
    q: str = Query(..., min_length=1, max_length=100),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    if not q.strip():
        raise HTTPException(status_code=400, detail="搜索关键词不能为空")
    result = await search_posts(db, q.strip(), page, page_size)
    redis = request.app.state.redis
    views = await get_views_for_posts(redis, [it["id"] for it in result["items"]])
    result["items"] = _attach_views(result["items"], views)
    return result


@router.post("/posts/{post_id}/view")
async def record_post_view(
    post_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """记录一次浏览（前端点击贴文时调用）。"""
    redis = request.app.state.redis
    exists = (
        await db.execute(select(Post.id).where(Post.id == post_id))
    ).scalar_one_or_none()
    if not exists:
        raise HTTPException(status_code=404, detail="贴文不存在")

    count = await record_view(redis, post_id)
    return {"view_count": count}
