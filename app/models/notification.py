"""Notification（站内通知）模型。

v2.3 新增：漂流瓶评论返回发布者后的消息提醒机制。
当前通知类型：
- ``encouragement``：你的漂流瓶收到了一条匿名鼓励语
- ``system``：系统通知（预留）
"""

from __future__ import annotations

from datetime import datetime
from sqlalchemy import Integer, String, DateTime, Boolean, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Notification(Base):
    """站内通知表。

    - ``user_id``：通知接收者（漂流瓶所有者）
    - ``type``：通知类型（encouragement / system）
    - ``content``：通知正文
    - ``related_id``：相关对象 id（如 diary_id，用于点击跳转）
    - ``is_read``：是否已读
    """

    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    type: Mapped[str] = mapped_column(String(30), nullable=False)
    content: Mapped[str] = mapped_column(String(200), nullable=False)
    related_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.current_timestamp(), nullable=False, index=True
    )

    # 关系
    user: Mapped["User"] = relationship("User", back_populates="notifications")  # type: ignore[name-defined]

    def __repr__(self) -> str:
        return f"<Notification id={self.id} user_id={self.user_id} type={self.type} read={self.is_read}>"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "type": self.type,
            "content": self.content,
            "related_id": self.related_id,
            "is_read": self.is_read,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
