"""User 模型。"""

from __future__ import annotations

from datetime import datetime
from sqlalchemy import Integer, String, DateTime, Boolean, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    """用户表。

    - ``password_hash``：bcrypt 哈希后的密码
    - ``encryption_salt``：用于日记对称加密的盐（base64 字符串）
    - ``total_energy``：累计获得的能量（不扣除消费）
    - ``is_admin``：是否为后台管理员（默认 False）
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nickname: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    encryption_salt: Mapped[str] = mapped_column(String(64), nullable=False)
    total_energy: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.current_timestamp(), nullable=False
    )

    # 关系
    diaries: Mapped[list["Diary"]] = relationship(  # type: ignore[name-defined]
        "Diary", back_populates="user", cascade="all, delete-orphan", lazy="select"
    )
    mood_checkins: Mapped[list["MoodCheckin"]] = relationship(  # type: ignore[name-defined]
        "MoodCheckin", back_populates="user", cascade="all, delete-orphan", lazy="select"
    )
    energy_records: Mapped[list["EnergyRecord"]] = relationship(  # type: ignore[name-defined]
        "EnergyRecord", back_populates="user", cascade="all, delete-orphan", lazy="select"
    )
    garden_items: Mapped[list["GardenItem"]] = relationship(  # type: ignore[name-defined]
        "GardenItem", back_populates="user", cascade="all, delete-orphan", lazy="select"
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} nickname={self.nickname!r} admin={self.is_admin}>"

    def to_public_dict(self) -> dict:
        """对外可公开的字段（不含 password_hash / salt）。"""
        return {
            "id": self.id,
            "nickname": self.nickname,
            "total_energy": self.total_energy,
            "is_admin": self.is_admin,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
