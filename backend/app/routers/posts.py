from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, Query, HTTPException, Request, Header
from pydantic import BaseModel
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
from app.services.like_counter import (
    like_post as do_like,
    unlike_post as do_unlike,
    get_like_info,
    get_likes_for_posts,
)
from app.services.rate_limiter import get_openid_from_token, check_rate_limit
from app.services.security import msg_sec_check

router = APIRouter(tags=["posts"])


def _attach_stats(items: list, views: dict, likes: dict) -> list:
    for it in items:
        it["view_count"] = views.get(it["id"], 0)
        it["like_count"] = likes.get(it["id"], 0)
    return items


async def _resolve_openid(redis, authorization: str) -> str:
    if not authorization:
        return ""
    token = authorization.removeprefix("Bearer ").strip()
    openid = await get_openid_from_token(redis, token)
    return openid or ""


class PostCreateRequest(BaseModel):
    content: str
    category: str = ""
    images: str = ""


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
    ids = [it["id"] for it in items]
    views = await get_views_for_posts(redis, ids)
    likes = await get_likes_for_posts(redis, ids)
    items = _attach_stats(items, views, likes)

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

    like_map = await get_likes_for_posts(redis, ids)
    items = []
    for pid in ids:
        post = by_id.get(pid)
        if post is None:
            continue
        d = post.to_dict()
        d["view_count"] = view_map.get(pid, 0)
        d["like_count"] = like_map.get(pid, 0)
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
    ids = [it["id"] for it in result["items"]]
    views = await get_views_for_posts(redis, ids)
    likes = await get_likes_for_posts(redis, ids)
    result["items"] = _attach_stats(result["items"], views, likes)
    return result


@router.get("/posts/{post_id}")
async def get_post_detail(
    post_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    authorization: str = Header(default=""),
):
    """获取单条贴文详情（含点赞数、是否已点赞、浏览量）。"""
    post = (
        await db.execute(select(Post).where(Post.id == post_id))
    ).scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="贴文不存在")

    redis = request.app.state.redis
    openid = await _resolve_openid(redis, authorization)

    data = post.to_dict()
    like_info = await get_like_info(redis, post_id, openid)
    views = await get_views_for_posts(redis, [post_id])
    data["like_count"] = like_info["count"]
    data["liked"] = like_info["liked"]
    data["view_count"] = views.get(post_id, 0)
    return data


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


@router.post("/posts")
async def create_post(
    body: PostCreateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    authorization: str = Header(default=""),
):
    """用户发帖（需登录、内容安全检测、限流）。"""
    redis = request.app.state.redis
    openid = await _resolve_openid(redis, authorization)
    if not openid:
        raise HTTPException(status_code=401, detail="请先登录")

    content = (body.content or "").strip()
    if len(content) < 2:
        raise HTTPException(status_code=400, detail="内容太短啦，至少 2 个字")
    if len(content) > 500:
        raise HTTPException(status_code=400, detail="内容太长了，请控制在 500 字以内")

    if not await check_rate_limit(redis, f"post:{openid}"):
        raise HTTPException(status_code=429, detail="发帖太频繁，请稍后再试")

    if not await msg_sec_check(redis, openid, content):
        raise HTTPException(status_code=400, detail="内容包含违规信息，请修改后重试")

    category = (body.category or "").strip()
    if category and not await msg_sec_check(redis, openid, category):
        raise HTTPException(status_code=400, detail="分类含违规内容")

    post = Post(
        content=content,
        images=(body.images or "").strip() or None,
        category=category or None,
        created_at=datetime.now(),
    )
    db.add(post)
    try:
        await db.commit()
        await db.refresh(post)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"发帖失败: {e}")

    return post.to_dict()


@router.post("/posts/{post_id}/like")
async def like_post_route(
    post_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    authorization: str = Header(default=""),
):
    """点赞（需登录）。已点赞过则等同查询，幂等。"""
    redis = request.app.state.redis
    openid = await _resolve_openid(redis, authorization)
    if not openid:
        raise HTTPException(status_code=401, detail="请先登录后再点赞")

    exists = (
        await db.execute(select(Post.id).where(Post.id == post_id))
    ).scalar_one_or_none()
    if not exists:
        raise HTTPException(status_code=404, detail="贴文不存在")

    return await do_like(redis, post_id, openid)


@router.delete("/posts/{post_id}/like")
async def unlike_post_route(
    post_id: int,
    request: Request,
    authorization: str = Header(default=""),
):
    """取消点赞（需登录）。"""
    redis = request.app.state.redis
    openid = await _resolve_openid(redis, authorization)
    if not openid:
        raise HTTPException(status_code=401, detail="请先登录")
    return await do_unlike(redis, post_id, openid)
