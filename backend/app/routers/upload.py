"""
图片上传接口 — 保存到本地文件系统，由 Nginx 静态托管。
"""

from __future__ import annotations

import os
import uuid
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request, Header, UploadFile, File

from app.config import get_settings
from app.services.rate_limiter import get_openid_from_token

settings = get_settings()
router = APIRouter(tags=["upload"])

UPLOAD_ROOT = Path(os.environ.get("UPLOAD_DIR", "/opt/chaxun/uploads"))
PUBLIC_BASE = os.environ.get("UPLOAD_PUBLIC_BASE", "https://api.ljdnet.top/uploads")

ALLOWED_EXT = {"jpg", "jpeg", "png", "webp", "gif"}
MAX_BYTES = 5 * 1024 * 1024  # 5MB


async def _resolve_openid(redis, authorization: str) -> str:
    if not authorization:
        return ""
    token = authorization.removeprefix("Bearer ").strip()
    return (await get_openid_from_token(redis, token)) or ""


@router.post("/upload/image")
async def upload_image(
    request: Request,
    file: UploadFile = File(...),
    authorization: str = Header(default=""),
):
    """上传单张图片，返回可访问的 URL。"""
    redis = request.app.state.redis
    openid = await _resolve_openid(redis, authorization)
    if not openid:
        raise HTTPException(status_code=401, detail="请先登录")

    # 扩展名校验
    orig_name = (file.filename or "").lower()
    ext = orig_name.rsplit(".", 1)[-1] if "." in orig_name else ""
    if ext not in ALLOWED_EXT:
        # 用 content-type 兜底
        ct = (file.content_type or "").lower()
        ct_map = {
            "image/jpeg": "jpg",
            "image/jpg": "jpg",
            "image/png": "png",
            "image/webp": "webp",
            "image/gif": "gif",
        }
        ext = ct_map.get(ct, "")
        if not ext:
            raise HTTPException(
                status_code=400,
                detail="只支持 jpg / png / webp / gif 格式",
            )

    # 读取并检查大小
    raw = await file.read()
    if len(raw) == 0:
        raise HTTPException(status_code=400, detail="文件为空")
    if len(raw) > MAX_BYTES:
        raise HTTPException(
            status_code=400,
            detail=f"图片过大，请控制在 {MAX_BYTES // 1024 // 1024}MB 以内",
        )

    # 按年月分目录
    now = datetime.now()
    rel_dir = f"posts/{now:%Y/%m}"
    abs_dir = UPLOAD_ROOT / rel_dir
    abs_dir.mkdir(parents=True, exist_ok=True)

    fname = f"{uuid.uuid4().hex}.{ext}"
    abs_path = abs_dir / fname

    try:
        with open(abs_path, "wb") as f:
            f.write(raw)
    except OSError as e:
        raise HTTPException(status_code=500, detail=f"保存失败: {e}")

    url = f"{PUBLIC_BASE.rstrip('/')}/{rel_dir}/{fname}"
    return {"url": url, "size": len(raw)}
