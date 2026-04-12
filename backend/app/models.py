"""
SQLAlchemy ORM model for the campus wall posts table.

The table name and column names are designed as a generic adapter —
update __tablename__ and Column mappings to match the real schema.
"""

import json
from datetime import datetime

from sqlalchemy import Column, Integer, Text, DateTime, String
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


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
