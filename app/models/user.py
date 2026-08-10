"""User 模型。"""

from __future__ import annotations

from datetime import datetime
from sqlalchemy import Integer, String, DateTime, Boolean, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    """用户表。

    - ``password_hash``：bcrypt 哈希后的密码
    - ``encryption_salt``：遗留字段（v2.3 前用于日记加密；v2.3 起日记改明文，保留字段仅为兼容老库）
    - ``total_energy``：露水能量（累计获得 - 消耗，用于浇灌已播种的花朵）
    - ``leaves``：落叶（用于在落叶画坊兑换花种；花朵枯萎后转化得到）
    - ``is_admin``：是否为后台管理员（默认 False）
    - ``avatar``：用户头像（emoji，默认 🙂；与树洞中显示的头像一致）
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nickname: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    encryption_salt: Mapped[str] = mapped_column(String(64), nullable=False)
    total_energy: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    leaves: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    avatar: Mapped[str] = mapped_column(String(16), default="🙂", nullable=False)
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
    user_flowers: Mapped[list["UserFlower"]] = relationship(  # type: ignore[name-defined]
        "UserFlower", back_populates="user", cascade="all, delete-orphan", lazy="select"
    )
    notifications: Mapped[list["Notification"]] = relationship(  # type: ignore[name-defined]
        "Notification", back_populates="user", cascade="all, delete-orphan", lazy="select"
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} nickname={self.nickname!r} admin={self.is_admin}>"

    def to_public_dict(self) -> dict:
        """对外可公开的字段（不含 password_hash / salt）。"""
        return {
            "id": self.id,
            "nickname": self.nickname,
            "avatar": self.avatar or "🙂",
            "total_energy": self.total_energy,
            "leaves": self.leaves,
            "is_admin": self.is_admin,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
