"""MoodCheckin（心情打卡）模型。"""

from __future__ import annotations

from datetime import datetime, date
from sqlalchemy import Integer, String, Date, DateTime, Text, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class MoodCheckin(Base):
    """每日心情打卡表。

    - ``check_date``：日期字符串（YYYY-MM-DD），与 user_id 联合唯一。
    - ``mood_emoji``：心情枚举字符串。
    - ``note``：一句话备注（可选，<= 200 字）。
    """

    __tablename__ = "mood_checkins"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    check_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    mood_emoji: Mapped[str] = mapped_column(String(20), nullable=False)
    note: Mapped[str | None] = mapped_column(String(200), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.current_timestamp(), nullable=False
    )

    # 关系
    user: Mapped["User"] = relationship("User", back_populates="mood_checkins")  # type: ignore[name-defined]

    __table_args__ = (
        UniqueConstraint("user_id", "check_date", name="uq_user_checkin_date"),
    )

    def __repr__(self) -> str:
        return f"<MoodCheckin id={self.id} user_id={self.user_id} date={self.check_date} mood={self.mood_emoji}>"
