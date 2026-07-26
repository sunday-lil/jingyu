"""花园相关模型：ShopItem（商店）、GardenItem（用户持有）。"""

from __future__ import annotations

from datetime import datetime
from sqlalchemy import Integer, String, DateTime, ForeignKey, func, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ShopItem(Base):
    """兑换商店物品表。

    v2.3 调整：
    - ``cost_currency``：兑换货币（dew 露水 / leaves 落叶）。花种用落叶兑换，装饰物用露水。
    """

    __tablename__ = "shop_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    item_type: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    cost: Mapped[int] = mapped_column(Integer, nullable=False)
    cost_currency: Mapped[str] = mapped_column(String(20), default="dew", nullable=False)
    image: Mapped[str] = mapped_column(String(50), default="🌿", nullable=False)
    description: Mapped[str | None] = mapped_column(String(200), nullable=True)
    trigger: Mapped[str | None] = mapped_column(String(50), nullable=True)  # 自动徽章触发器

    def __repr__(self) -> str:
        return f"<ShopItem id={self.id} name={self.name!r} cost={self.cost} {self.cost_currency}>"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "item_type": self.item_type,
            "cost": self.cost,
            "cost_currency": self.cost_currency,
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


# ─────────────────────────────────────────────────────────────
# 花朵生长周期（v2.3 新增）
# ─────────────────────────────────────────────────────────────

# 成长阶段
STAGE_SEED = "seed"        # 种子（刚种下）
STAGE_SPROUT = "sprout"    # 发芽
STAGE_BUD = "bud"          # 花苞
STAGE_BLOOM = "bloom"      # 盛开
STAGE_WILTED = "wilted"    # 枯萎

STAGE_ORDER = [STAGE_SEED, STAGE_SPROUT, STAGE_BUD, STAGE_BLOOM, STAGE_WILTED]

# 每阶段升级所需浇水次数（露水浇灌）
WATER_TO_NEXT_STAGE = {
    STAGE_SEED: 2,      # 种子 → 发芽：浇 2 次
    STAGE_SPROUT: 3,    # 发芽 → 花苞：浇 3 次
    STAGE_BUD: 2,       # 花苞 → 盛开：浇 2 次
    STAGE_BLOOM: 0,     # 盛开（已最终态，不升级）
    STAGE_WILTED: 0,    # 枯萎（终态）
}

# 盛开后超过此天数未浇水 → 枯萎
WILT_DAYS_AFTER_BLOOM = 7


class UserFlower(Base):
    """用户在屿上花田种下的花朵（生长周期）。

    - ``flower_type``：花种 key（对应 ShopItem 里 item_type=flower 的种子）。
    - ``stage``：当前阶段（seed/sprout/bud/bloom/wilted）。
    - ``watered_count``：当前阶段累计浇水次数（达到阈值升级，升级后归零）。
    - ``last_watered_at``：最后一次浇水时间。
    - ``bloom_at``：进入盛开的时间（用于计算枯萎）。
    - ``wilted_at``：枯萎时间（用于"拾取落叶"后删除）。
    """

    __tablename__ = "user_flowers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    flower_type: Mapped[str] = mapped_column(String(50), nullable=False)
    stage: Mapped[str] = mapped_column(String(20), default=STAGE_SEED, nullable=False)
    watered_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    planted_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.current_timestamp(), nullable=False
    )
    last_watered_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    bloom_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    wilted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # 关系
    user: Mapped["User"] = relationship("User", back_populates="user_flowers")  # type: ignore[name-defined]

    def __repr__(self) -> str:
        return f"<UserFlower id={self.id} user_id={self.user_id} type={self.flower_type!r} stage={self.stage}>"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "flower_type": self.flower_type,
            "stage": self.stage,
            "watered_count": self.watered_count,
            "water_needed": WATER_TO_NEXT_STAGE.get(self.stage, 0),
            "planted_at": self.planted_at.isoformat() if self.planted_at else None,
            "last_watered_at": self.last_watered_at.isoformat() if self.last_watered_at else None,
            "bloom_at": self.bloom_at.isoformat() if self.bloom_at else None,
            "wilted_at": self.wilted_at.isoformat() if self.wilted_at else None,
        }
