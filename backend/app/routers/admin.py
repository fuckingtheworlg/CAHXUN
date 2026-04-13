"""
Admin API routes — JWT-authenticated management endpoints.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional, List

import jwt
from fastapi import APIRouter, Depends, HTTPException, Request, Query
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from sqlalchemy import select, func, desc, delete as sa_delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.models import Post
from app.services.search import search_posts
from app.services.chat_logger import get_chat_logs, get_today_chat_count

settings = get_settings()
router = APIRouter(tags=["admin"])

_JWT_ALGORITHM = "HS256"
_JWT_EXPIRY_HOURS = 24
_SETTINGS_PREFIX = "admin:setting:"


# --------------- Request / Response models ---------------

class AdminLoginRequest(BaseModel):
    username: str
    password: str


class AdminLoginResponse(BaseModel):
    token: str
    expires_at: str


class PostCreateRequest(BaseModel):
    content: str
    images: str = ""
    category: str = ""


class PostUpdateRequest(BaseModel):
    content: Optional[str] = None
    images: Optional[str] = None
    category: Optional[str] = None


class BatchDeleteRequest(BaseModel):
    ids: List[int]


class SettingsUpdateRequest(BaseModel):
    rate_limit_per_minute: Optional[int] = None
    deepseek_model: Optional[str] = None
    deepseek_base_url: Optional[str] = None


# --------------- Auth helpers ---------------

def create_admin_token() -> tuple:
    exp = datetime.utcnow() + timedelta(hours=_JWT_EXPIRY_HOURS)
    payload = {"sub": "admin", "exp": exp}
    token = jwt.encode(payload, settings.admin_jwt_secret, algorithm=_JWT_ALGORITHM)
    return token, exp


def verify_admin_token(token: str) -> bool:
    try:
        jwt.decode(token, settings.admin_jwt_secret, algorithms=[_JWT_ALGORITHM])
        return True
    except jwt.PyJWTError:
        return False


async def require_admin(request: Request) -> None:
    auth = request.headers.get("Authorization", "")
    token = auth.removeprefix("Bearer ").strip()
    if not token or not verify_admin_token(token):
        raise HTTPException(status_code=401, detail="管理员认证失败")


# --------------- Login ---------------

@router.post("/admin/login", response_model=AdminLoginResponse)
async def admin_login(body: AdminLoginRequest):
    if body.username != settings.admin_username or body.password != settings.admin_password:
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    token, exp = create_admin_token()
    return AdminLoginResponse(token=token, expires_at=exp.isoformat())


# --------------- Dashboard stats ---------------

@router.get("/admin/stats", dependencies=[Depends(require_admin)])
async def admin_stats(request: Request, db: AsyncSession = Depends(get_db)):
    redis = request.app.state.redis

    total_posts = (await db.execute(select(func.count()).select_from(Post))).scalar()

    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    today_posts = (
        await db.execute(
            select(func.count())
            .select_from(Post)
            .where(Post.created_at >= today_start)
        )
    ).scalar()

    today_chats = await get_today_chat_count(redis)

    session_keys = []
    cursor = "0"
    while True:
        cursor, keys = await redis.scan(cursor=cursor, match="session:*", count=100)
        session_keys.extend(keys)
        if cursor == 0 or cursor == "0":
            break
    active_sessions = len(session_keys)

    return {
        "total_posts": total_posts,
        "today_posts": today_posts,
        "today_chats": today_chats,
        "active_sessions": active_sessions,
        "rate_limit_per_minute": settings.rate_limit_per_minute,
    }


# --------------- Post CRUD ---------------

@router.post("/admin/posts", dependencies=[Depends(require_admin)])
async def admin_create_post(body: PostCreateRequest, db: AsyncSession = Depends(get_db)):
    post = Post(
        content=body.content,
        images=body.images if body.images else None,
        created_at=datetime.now(),
        category=body.category if body.category else None,
    )
    db.add(post)
    await db.commit()
    await db.refresh(post)
    return post.to_dict()


@router.post("/admin/posts/batch-delete", dependencies=[Depends(require_admin)])
async def admin_batch_delete_posts(body: BatchDeleteRequest, db: AsyncSession = Depends(get_db)):
    if not body.ids:
        raise HTTPException(status_code=400, detail="请选择要删除的贴文")
    result = await db.execute(sa_delete(Post).where(Post.id.in_(body.ids)))
    await db.commit()
    return {"message": f"成功删除 {result.rowcount} 条贴文", "deleted": result.rowcount}


@router.get("/admin/posts", dependencies=[Depends(require_admin)])
async def admin_list_posts(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    q: str = Query(default=""),
    db: AsyncSession = Depends(get_db),
):
    if q.strip():
        return await search_posts(db, q.strip(), page, page_size)

    offset = (page - 1) * page_size
    total = (await db.execute(select(func.count()).select_from(Post))).scalar()
    rows = (
        await db.execute(
            select(Post).order_by(desc(Post.created_at)).offset(offset).limit(page_size)
        )
    ).scalars().all()
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [r.to_dict() for r in rows],
    }


@router.get("/admin/posts/{post_id}", dependencies=[Depends(require_admin)])
async def admin_get_post(post_id: int, db: AsyncSession = Depends(get_db)):
    post = (await db.execute(select(Post).where(Post.id == post_id))).scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="贴文不存在")
    return post.to_dict()


@router.put("/admin/posts/{post_id}", dependencies=[Depends(require_admin)])
async def admin_update_post(post_id: int, body: PostUpdateRequest, db: AsyncSession = Depends(get_db)):
    post = (await db.execute(select(Post).where(Post.id == post_id))).scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="贴文不存在")
    if body.content is not None:
        post.content = body.content
    if body.images is not None:
        post.images = body.images if body.images else None
    if body.category is not None:
        post.category = body.category if body.category else None
    await db.commit()
    await db.refresh(post)
    return post.to_dict()


@router.delete("/admin/posts/{post_id}", dependencies=[Depends(require_admin)])
async def admin_delete_post(post_id: int, db: AsyncSession = Depends(get_db)):
    post = (await db.execute(select(Post).where(Post.id == post_id))).scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="贴文不存在")
    await db.delete(post)
    await db.commit()
    return {"message": "删除成功"}


# --------------- Chat logs ---------------

@router.get("/admin/chat-logs", dependencies=[Depends(require_admin)])
async def admin_chat_logs(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    redis = request.app.state.redis
    offset = (page - 1) * page_size
    items, total = await get_chat_logs(redis, offset, page_size)

    for item in items:
        ts = item.get("timestamp")
        if ts:
            item["time"] = datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
        openid = item.get("openid", "")
        if len(openid) > 8:
            item["openid_short"] = openid[:4] + "***" + openid[-4:]
        else:
            item["openid_short"] = openid

    return {"total": total, "page": page, "page_size": page_size, "items": items}


@router.delete("/admin/chat-logs", dependencies=[Depends(require_admin)])
async def admin_clear_chat_logs(request: Request):
    redis = request.app.state.redis
    await redis.delete("chat:logs")
    return {"message": "问答日志已清空"}


# --------------- System settings ---------------

@router.get("/admin/settings", dependencies=[Depends(require_admin)])
async def admin_get_settings(request: Request):
    redis = request.app.state.redis

    overrides = {}
    for key in ["rate_limit_per_minute", "deepseek_model", "deepseek_base_url"]:
        val = await redis.get(f"{_SETTINGS_PREFIX}{key}")
        if val is not None:
            overrides[key] = val

    return {
        "rate_limit_per_minute": int(overrides.get("rate_limit_per_minute", settings.rate_limit_per_minute)),
        "deepseek_model": overrides.get("deepseek_model", settings.deepseek_model),
        "deepseek_base_url": overrides.get("deepseek_base_url", settings.deepseek_base_url),
        "db_host": settings.db_host,
        "db_name": settings.db_name,
        "db_table_name": settings.db_table_name,
        "wechat_appid": settings.wechat_appid,
        "api_key_configured": bool(settings.deepseek_api_key),
        "wechat_secret_configured": bool(settings.wechat_secret),
    }


@router.put("/admin/settings", dependencies=[Depends(require_admin)])
async def admin_update_settings(body: SettingsUpdateRequest, request: Request):
    redis = request.app.state.redis
    updated = {}
    data = body.model_dump(exclude_none=True)
    for field, value in data.items():
        await redis.set(f"{_SETTINGS_PREFIX}{field}", str(value))
        updated[field] = value
    if not updated:
        raise HTTPException(status_code=400, detail="没有需要更新的设置项")
    return {"message": "设置已更新", "updated": updated}


# --------------- CSV Import ---------------

@router.get("/admin/import/template", dependencies=[Depends(require_admin)])
async def download_csv_template():
    from fastapi.responses import StreamingResponse
    import io

    buf = io.StringIO()
    buf.write("content,images,created_at,category\n")
    buf.write('"这是一条示例贴文内容","https://example.com/a.jpg,https://example.com/b.jpg","2025-01-15 10:30:00","失物招领"\n')
    buf.write('"第二条示例，图片和分类可以留空","","",""\n')
    buf.seek(0)

    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=import_template.csv"},
    )


@router.post("/admin/import/csv", dependencies=[Depends(require_admin)])
async def import_csv(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    import csv
    import io

    content_type = request.headers.get("content-type", "")
    if "multipart/form-data" not in content_type:
        raise HTTPException(status_code=400, detail="请使用 multipart/form-data 上传文件")

    form = await request.form()
    file = form.get("file")
    if file is None:
        raise HTTPException(status_code=400, detail="未找到上传文件")

    raw_bytes = await file.read()
    try:
        text = raw_bytes.decode("utf-8-sig")
    except UnicodeDecodeError:
        try:
            text = raw_bytes.decode("gbk")
        except UnicodeDecodeError:
            raise HTTPException(status_code=400, detail="文件编码不支持，请使用 UTF-8 编码")

    reader = csv.DictReader(io.StringIO(text))

    if "content" not in (reader.fieldnames or []):
        raise HTTPException(
            status_code=400,
            detail=f"CSV 缺少必需列 'content'，当前列: {reader.fieldnames}",
        )

    success_count = 0
    fail_count = 0
    errors = []

    for i, row in enumerate(reader, start=2):
        content_val = (row.get("content") or "").strip()
        if not content_val:
            fail_count += 1
            errors.append(f"第{i}行: content 为空，已跳过")
            continue

        images_val = (row.get("images") or "").strip()
        category_val = (row.get("category") or "").strip() or None
        created_at_val = None

        raw_time = (row.get("created_at") or "").strip()
        if raw_time:
            for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%Y/%m/%d %H:%M:%S", "%Y/%m/%d"):
                try:
                    created_at_val = datetime.strptime(raw_time, fmt)
                    break
                except ValueError:
                    continue
            if created_at_val is None:
                fail_count += 1
                errors.append(f"第{i}行: created_at 格式无法识别 '{raw_time}'，已跳过")
                continue
        else:
            created_at_val = datetime.now()

        post = Post(
            content=content_val,
            images=images_val if images_val else None,
            created_at=created_at_val,
            category=category_val,
        )
        db.add(post)
        success_count += 1

    if success_count > 0:
        try:
            await db.commit()
        except Exception as e:
            await db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"数据库写入失败: {str(e)}。请确认数据库用户拥有 INSERT 权限。",
            )

    return {
        "success": success_count,
        "failed": fail_count,
        "errors": errors[:20],
        "message": f"导入完成：成功 {success_count} 条，失败 {fail_count} 条",
    }


# --------------- Serve admin SPA ---------------

@router.get("/admin", response_class=HTMLResponse, include_in_schema=False)
async def admin_page():
    import pathlib

    html_path = pathlib.Path(__file__).resolve().parent.parent / "static" / "admin" / "index.html"
    if not html_path.exists():
        raise HTTPException(status_code=404, detail="Admin page not found")
    return HTMLResponse(html_path.read_text(encoding="utf-8"))
