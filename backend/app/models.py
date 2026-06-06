"""
SQLAlchemy ORM model for the campus wall posts table.

The table name and column names are designed as a generic adapter —
update __tablename__ and Column mappings to match the real schema.
"""

from __future__ import annotations

import json
from datetime import datetime

from sqlalchemy import Column, Integer, Text, DateTime, String, Boolean
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class User(Base):
    """小程序用户表，按 openid 唯一。"""

    __tablename__ = "users"

    openid = Column(String(64), primary_key=True)
    nickname = Column(String(64), nullable=True)
    avatar_url = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    last_login_at = Column(DateTime, default=datetime.now)
    last_seen_at = Column(DateTime, default=datetime.now)
    login_count = Column(Integer, default=1)
    is_banned = Column(Boolean, default=False)
    ban_reason = Column(String(255), nullable=True)
    note = Column(String(255), nullable=True)

    def to_dict(self) -> dict:
        def _iso(dt):
            return dt.isoformat() if dt else None

        return {
            "openid": self.openid,
            "openid_short": (self.openid[:4] + "***" + self.openid[-4:])
            if self.openid and len(self.openid) > 8
            else self.openid,
            "nickname": self.nickname,
            "avatar_url": self.avatar_url,
            "created_at": _iso(self.created_at),
            "last_login_at": _iso(self.last_login_at),
            "last_seen_at": _iso(self.last_seen_at),
            "login_count": self.login_count or 0,
            "is_banned": bool(self.is_banned),
            "ban_reason": self.ban_reason,
            "note": self.note,
        }


class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    content = Column(Text, nullable=False)
    images = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    category = Column(String(64), nullable=True)

    def to_dict(self) -> dict:
        image_list = []
        if self.images:
            raw = self.images.strip()
            if raw.startswith("["):
                try:
                    image_list = json.loads(raw)
                except json.JSONDecodeError:
                    image_list = [u.strip() for u in raw.split(",") if u.strip()]
            else:
                image_list = [u.strip() for u in raw.split(",") if u.strip()]

        return {
            "id": self.id,
            "content": self.content,
            "images": image_list,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "category": self.category,
        }
