"""Diary（漂流瓶日记）模型。"""

from __future__ import annotations

from datetime import datetime
from sqlalchemy import Integer, String, Text, DateTime, Boolean, ForeignKey, func, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Diary(Base):
    """漂流瓶日记表。

    - ``content_encrypted``：Fernet 密文（base64 字符串）。**明文绝不落库**。
    - ``mood_type``：关联心情枚举字符串（也可为空）。
    - ``is_public``：是否允许被陌生人拾取。
    """

    __tablename__ = "diaries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    content_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    mood_type: Mapped[str | None] = mapped_column(String(20), nullable=True)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.current_timestamp(), nullable=False, index=True
    )

    # 关系
    user: Mapped["User"] = relationship("User", back_populates="diaries")  # type: ignore[name-defined]
    encouragements: Mapped[list["Encouragement"]] = relationship(  # type: ignore[name-defined]
        "Encouragement", back_populates="diary", cascade="all, delete-orphan", lazy="select"
    )

    __table_args__ = (
        Index("ix_diaries_public_created", "is_public", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<Diary id={self.id} user_id={self.user_id} created_at={self.created_at}>"
