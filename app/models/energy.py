"""EnergyRecord（能量变动记录）模型。"""

from __future__ import annotations

from datetime import datetime
from sqlalchemy import Integer, String, DateTime, ForeignKey, func, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class EnergyRecord(Base):
    """能量变动流水表。

    - ``amount``：正数为增加，负数为消费。
    - ``source``：来源枚举（listen_music / write_diary / checkin / streak_7 / exchange）。
    - ``note``：可选说明（如「听完《流水》」）。
    - ``music_id``：仅 listen_music 来源有值，用于「同一首歌 24h 内不重复发放」去重。
    """

    __tablename__ = "energy_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    source: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    note: Mapped[str | None] = mapped_column(String(200), nullable=True)
    music_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.current_timestamp(), nullable=False, index=True
    )

    # 关系
    user: Mapped["User"] = relationship("User", back_populates="energy_records")  # type: ignore[name-defined]

    __table_args__ = (
        Index("ix_energy_user_source_date", "user_id", "source", "created_at"),
        Index("ix_energy_user_music_date", "user_id", "music_id", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<EnergyRecord id={self.id} user_id={self.user_id} amount={self.amount} source={self.source}>"
