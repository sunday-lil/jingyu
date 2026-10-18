"""身心调理相关模型：八段锦打卡、好物预约意向。"""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class BaduanjinCheckin(Base):
    """八段锦跟练打卡（每日最多一次）。"""

    __tablename__ = "baduanjin_checkins"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    check_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    move_key: Mapped[str] = mapped_column(String(50), default="general", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.current_timestamp(), nullable=False
    )

    __table_args__ = (
        UniqueConstraint("user_id", "check_date", name="uq_baduanjin_user_date"),
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "check_date": self.check_date.isoformat() if self.check_date else None,
            "move_key": self.move_key,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class TherapyInterest(Base):
    """好物橱窗的预约/意向记录（不涉及支付）。"""

    __tablename__ = "therapy_interests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    product_key: Mapped[str] = mapped_column(String(50), nullable=False)
    product_name: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.current_timestamp(), nullable=False
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "product_key": self.product_key,
            "product_name": self.product_name,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
