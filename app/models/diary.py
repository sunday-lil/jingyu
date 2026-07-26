"""Diary（漂流瓶日记）模型。"""

from __future__ import annotations

from datetime import datetime
from sqlalchemy import Integer, String, Text, DateTime, Boolean, ForeignKey, func, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Diary(Base):
    """漂流瓶日记表。

    v2.3 调整：
    - ``content``：明文日记内容（v2.3 起替代 content_encrypted，移除密码保护）。
    - ``content_encrypted``：遗留字段（v2.3 前的 Fernet 密文），保留只为兼容老库，新数据不再写入。
    - ``mood_type``：关联心情枚举字符串（也可为空）。
    - ``is_public``：是否放入漂流瓶（公开可见，允许所有人查看和评论）。
    - ``send_to_ai_hole``：不放入漂流瓶时，是否同步至树洞（仅自己可见 + AI 对话）。
    """

    __tablename__ = "diaries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    content: Mapped[str] = mapped_column(Text, nullable=False, default="")
    content_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    mood_type: Mapped[str | None] = mapped_column(String(20), nullable=True)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    send_to_ai_hole: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
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
