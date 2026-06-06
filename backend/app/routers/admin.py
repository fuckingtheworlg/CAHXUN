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
from app.models import Post, User
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
    deepseek_api_key: Optional[str] = None
    system_prompt: Optional[str] = None


class TestApiKeyRequest(BaseModel):
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    model: Optional[str] = None


class BanRequest(BaseModel):
    reason: Optional[str] = ""


class NoteRequest(BaseModel):
    note: Optional[str] = ""


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

    total_users = 0
    banned_users = 0
    try:
        total_users = (await db.execute(select(func.count()).select_from(User))).scalar() or 0
        banned_users = (
            await db.execute(
                select(func.count()).select_from(User).where(User.is_banned == True)  # noqa: E712
            )
        ).scalar() or 0
    except Exception:
        pass

    return {
        "total_posts": total_posts,
        "today_posts": today_posts,
        "today_chats": today_chats,
        "active_sessions": active_sessions,
        "total_users": total_users,
        "banned_users": banned_users,
        "rate_limit_per_minute": settings.rate_limit_per_minute,
    }


# --------------- System resources ---------------

@router.get("/admin/system", dependencies=[Depends(require_admin)])
async def admin_system_stats():
    """服务器 CPU / 内存 / 磁盘 / 负载 / 进程 / 运行时长。"""
    import psutil
    import time
    import platform

    # CPU
    cpu_percent = psutil.cpu_percent(interval=0.3)
    cpu_count = psutil.cpu_count(logical=True)
    cpu_freq = psutil.cpu_freq()
    cpu_freq_mhz = round(cpu_freq.current) if cpu_freq else 0

    # 内存
    mem = psutil.virtual_memory()
    swap = psutil.swap_memory()

    # 磁盘（根分区）
    disk = psutil.disk_usage("/")

    # 系统负载（仅 Linux）
    try:
        load1, load5, load15 = psutil.getloadavg()
    except Exception:
        load1 = load5 = load15 = 0

    # 网络（自启动累计）
    net = psutil.net_io_counters()

    # 进程数
    proc_count = len(psutil.pids())

    # 当前服务进程信息
    cur_proc = psutil.Process()
    proc_mem_mb = round(cur_proc.memory_info().rss / 1024 / 1024, 1)
    proc_cpu = cur_proc.cpu_percent(interval=0.1)

    # 系统启动时长
    boot_ts = psutil.boot_time()
    uptime_seconds = int(time.time() - boot_ts)

    return {
        "platform": f"{platform.system()} {platform.release()}",
        "cpu": {
            "percent": cpu_percent,
            "count": cpu_count,
            "freq_mhz": cpu_freq_mhz,
            "load_1": round(load1, 2),
            "load_5": round(load5, 2),
            "load_15": round(load15, 2),
        },
        "memory": {
            "total_mb": round(mem.total / 1024 / 1024),
            "used_mb": round(mem.used / 1024 / 1024),
            "available_mb": round(mem.available / 1024 / 1024),
            "percent": mem.percent,
            "swap_total_mb": round(swap.total / 1024 / 1024),
            "swap_used_mb": round(swap.used / 1024 / 1024),
            "swap_percent": swap.percent,
        },
        "disk": {
            "total_gb": round(disk.total / 1024 / 1024 / 1024, 1),
            "used_gb": round(disk.used / 1024 / 1024 / 1024, 1),
            "free_gb": round(disk.free / 1024 / 1024 / 1024, 1),
            "percent": disk.percent,
        },
        "network": {
            "bytes_sent_mb": round(net.bytes_sent / 1024 / 1024, 1),
            "bytes_recv_mb": round(net.bytes_recv / 1024 / 1024, 1),
        },
        "process": {
            "total": proc_count,
            "self_mem_mb": proc_mem_mb,
            "self_cpu_percent": proc_cpu,
        },
        "uptime_seconds": uptime_seconds,
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


# --------------- User management ---------------

@router.get("/admin/users", dependencies=[Depends(require_admin)])
async def admin_list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    q: str = Query(default=""),
    status: str = Query(default="", description="all|banned|active"),
    db: AsyncSession = Depends(get_db),
):
    base = select(User)
    count_base = select(func.count()).select_from(User)

    if q.strip():
        kw = f"%{q.strip()}%"
        cond = (User.openid.like(kw)) | (User.nickname.like(kw)) | (User.note.like(kw))
        base = base.where(cond)
        count_base = count_base.where(cond)

    if status == "banned":
        base = base.where(User.is_banned == True)  # noqa: E712
        count_base = count_base.where(User.is_banned == True)  # noqa: E712
    elif status == "active":
        base = base.where(User.is_banned == False)  # noqa: E712
        count_base = count_base.where(User.is_banned == False)  # noqa: E712

    total = (await db.execute(count_base)).scalar() or 0
    offset = (page - 1) * page_size
    rows = (
        await db.execute(
            base.order_by(desc(User.last_seen_at)).offset(offset).limit(page_size)
        )
    ).scalars().all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [r.to_dict() for r in rows],
    }


@router.get("/admin/users/{openid}", dependencies=[Depends(require_admin)])
async def admin_get_user(openid: str, request: Request, db: AsyncSession = Depends(get_db)):
    user = (
        await db.execute(select(User).where(User.openid == openid))
    ).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    redis = request.app.state.redis

    # 当前会话数（同一用户可能多端登录）
    session_count = 0
    cursor = "0"
    while True:
        cursor, keys = await redis.scan(cursor=cursor, match="session:*", count=200)
        for k in keys:
            if (await redis.get(k)) == openid:
                session_count += 1
        if cursor == 0 or cursor == "0":
            break

    # 当前限流计数（一分钟内问答次数）
    rl_count = 0
    try:
        rl_count = await redis.zcard(f"ratelimit:{openid}")
    except Exception:
        pass

    data = user.to_dict()
    data["active_sessions"] = session_count
    data["recent_chat_count"] = rl_count
    return data


@router.post("/admin/users/{openid}/ban", dependencies=[Depends(require_admin)])
async def admin_ban_user(
    openid: str,
    body: BanRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    user = (
        await db.execute(select(User).where(User.openid == openid))
    ).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    user.is_banned = True
    user.ban_reason = (body.reason or "").strip() or "违规行为"
    await db.commit()

    # 同时强制下线该用户所有 session
    redis = request.app.state.redis
    cursor = "0"
    killed = 0
    while True:
        cursor, keys = await redis.scan(cursor=cursor, match="session:*", count=200)
        for k in keys:
            if (await redis.get(k)) == openid:
                await redis.delete(k)
                killed += 1
        if cursor == 0 or cursor == "0":
            break

    return {"message": f"已封禁，并踢下线 {killed} 个会话", "user": user.to_dict()}


@router.post("/admin/users/{openid}/unban", dependencies=[Depends(require_admin)])
async def admin_unban_user(openid: str, db: AsyncSession = Depends(get_db)):
    user = (
        await db.execute(select(User).where(User.openid == openid))
    ).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    user.is_banned = False
    user.ban_reason = None
    await db.commit()
    return {"message": "已解封", "user": user.to_dict()}


@router.put("/admin/users/{openid}/note", dependencies=[Depends(require_admin)])
async def admin_update_user_note(
    openid: str, body: NoteRequest, db: AsyncSession = Depends(get_db)
):
    user = (
        await db.execute(select(User).where(User.openid == openid))
    ).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    user.note = (body.note or "").strip() or None
    await db.commit()
    return {"message": "备注已更新", "user": user.to_dict()}


@router.delete("/admin/users/{openid}/sessions", dependencies=[Depends(require_admin)])
async def admin_kick_user(openid: str, request: Request):
    """强制该用户所有端下线（不改用户表，仅清除 session）。"""
    redis = request.app.state.redis
    cursor = "0"
    killed = 0
    while True:
        cursor, keys = await redis.scan(cursor=cursor, match="session:*", count=200)
        for k in keys:
            if (await redis.get(k)) == openid:
                await redis.delete(k)
                killed += 1
        if cursor == 0 or cursor == "0":
            break
    return {"message": f"已强制下线 {killed} 个会话"}


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

def _mask_api_key(key: str) -> str:
    """脱敏 API Key，前 4 位 + 末 4 位。"""
    if not key:
        return ""
    if len(key) <= 12:
        return "***"
    return f"{key[:4]}{'*' * 8}{key[-4:]}"


@router.get("/admin/settings", dependencies=[Depends(require_admin)])
async def admin_get_settings(request: Request):
    redis = request.app.state.redis

    overrides = {}
    for key in [
        "rate_limit_per_minute",
        "deepseek_model",
        "deepseek_base_url",
        "deepseek_api_key",
        "system_prompt",
    ]:
        val = await redis.get(f"{_SETTINGS_PREFIX}{key}")
        if val is not None:
            overrides[key] = val

    effective_api_key = overrides.get("deepseek_api_key", settings.deepseek_api_key)

    from app.services.rag import DEFAULT_SYSTEM_PROMPT
    effective_prompt = overrides.get("system_prompt", DEFAULT_SYSTEM_PROMPT)

    return {
        "rate_limit_per_minute": int(overrides.get("rate_limit_per_minute", settings.rate_limit_per_minute)),
        "deepseek_model": overrides.get("deepseek_model", settings.deepseek_model),
        "deepseek_base_url": overrides.get("deepseek_base_url", settings.deepseek_base_url),
        "deepseek_api_key_mask": _mask_api_key(effective_api_key),
        "deepseek_api_key_source": "override" if "deepseek_api_key" in overrides else "env",
        "system_prompt": effective_prompt,
        "system_prompt_source": "override" if "system_prompt" in overrides else "default",
        "db_host": settings.db_host,
        "db_name": settings.db_name,
        "db_table_name": settings.db_table_name,
        "wechat_appid": settings.wechat_appid,
        "api_key_configured": bool(effective_api_key),
        "wechat_secret_configured": bool(settings.wechat_secret),
    }


@router.put("/admin/settings", dependencies=[Depends(require_admin)])
async def admin_update_settings(body: SettingsUpdateRequest, request: Request):
    redis = request.app.state.redis
    updated = {}
    data = body.model_dump(exclude_none=True)
    for field, value in data.items():
        if field == "deepseek_api_key":
            value = value.strip()
            if not value:
                raise HTTPException(status_code=400, detail="API Key 不能为空")
        elif field == "system_prompt":
            value = (value or "").strip()
            if len(value) < 5:
                raise HTTPException(status_code=400, detail="系统提示词过短，至少 5 个字符")
            if len(value) > 4000:
                raise HTTPException(status_code=400, detail="系统提示词过长，请控制在 4000 字符以内")
        await redis.set(f"{_SETTINGS_PREFIX}{field}", str(value))
        updated[field] = "***" if field == "deepseek_api_key" else (
            (value[:50] + "...") if field == "system_prompt" and len(str(value)) > 50 else value
        )
    if not updated:
        raise HTTPException(status_code=400, detail="没有需要更新的设置项")
    return {"message": "设置已更新", "updated": updated}


@router.delete("/admin/settings/deepseek_api_key", dependencies=[Depends(require_admin)])
async def admin_reset_api_key(request: Request):
    """删除 API Key 覆盖，恢复使用 .env 中的默认 Key。"""
    redis = request.app.state.redis
    await redis.delete(f"{_SETTINGS_PREFIX}deepseek_api_key")
    return {"message": "已恢复使用 .env 中的默认 API Key"}


@router.delete("/admin/settings/system_prompt", dependencies=[Depends(require_admin)])
async def admin_reset_system_prompt(request: Request):
    """删除系统提示词覆盖，恢复使用代码内置的默认提示词。"""
    redis = request.app.state.redis
    await redis.delete(f"{_SETTINGS_PREFIX}system_prompt")
    return {"message": "已恢复默认系统提示词"}


@router.post("/admin/settings/test-api-key", dependencies=[Depends(require_admin)])
async def admin_test_api_key(body: TestApiKeyRequest, request: Request):
    """实测 DeepSeek API Key 是否可用。"""
    import httpx

    redis = request.app.state.redis

    async def _read(key: str, fallback: str) -> str:
        val = await redis.get(f"{_SETTINGS_PREFIX}{key}")
        return val if val is not None else fallback

    api_key = (body.api_key or "").strip() or await _read("deepseek_api_key", settings.deepseek_api_key)
    base_url = (body.base_url or "").strip() or await _read("deepseek_base_url", settings.deepseek_base_url)
    model = (body.model or "").strip() or await _read("deepseek_model", settings.deepseek_model)

    if not api_key:
        raise HTTPException(status_code=400, detail="未配置 API Key")

    url = f"{base_url}/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": "ping"}],
        "max_tokens": 5,
        "stream": False,
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(url, json=payload, headers=headers)
        if resp.status_code == 200:
            return {"ok": True, "message": "API Key 可用", "model": model}
        try:
            err = resp.json().get("error", {}).get("message") or resp.text
        except Exception:
            err = resp.text
        return {"ok": False, "status": resp.status_code, "message": f"调用失败：{err}"}
    except httpx.HTTPError as e:
        return {"ok": False, "message": f"网络错误：{e}"}


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
