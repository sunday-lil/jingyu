"""花园相关模型：ShopItem（商店）、GardenItem（用户持有）。"""

from __future__ import annotations

from datetime import datetime
from sqlalchemy import Integer, String, DateTime, ForeignKey, func, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ShopItem(Base):
    """兑换商店物品表。"""

    __tablename__ = "shop_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    item_type: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    cost: Mapped[int] = mapped_column(Integer, nullable=False)
    image: Mapped[str] = mapped_column(String(50), default="🌿", nullable=False)
    description: Mapped[str | None] = mapped_column(String(200), nullable=True)
    trigger: Mapped[str | None] = mapped_column(String(50), nullable=True)  # 自动徽章触发器

    def __repr__(self) -> str:
        return f"<ShopItem id={self.id} name={self.name!r} cost={self.cost}>"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "item_type": self.item_type,
            "cost": self.cost,
            "image": self.image,
            "description": self.description,
            "trigger": self.trigger,
        }


class GardenItem(Base):
    """用户花园持有表。"""

    __tablename__ = "garden_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    item_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("shop_items.id", ondelete="CASCADE"), nullable=False
    )
    obtained_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.current_timestamp(), nullable=False
    )

    # 关系
    user: Mapped["User"] = relationship("User", back_populates="garden_items")  # type: ignore[name-defined]
    item: Mapped["ShopItem"] = relationship("ShopItem", lazy="joined")

    __table_args__ = (
        UniqueConstraint("user_id", "item_id", name="uq_user_item"),
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "item_id": self.item_id,
            "name": self.item.name if self.item else "?",
            "item_type": self.item.item_type if self.item else "?",
            "image": self.item.image if self.item else "🌿",
            "description": self.item.description if self.item else None,
            "obtained_at": self.obtained_at.isoformat() if self.obtained_at else None,
        }
