"""能量规则服务。

规则（与 PRD 一致）：
- 听完一首曲子（进度 ≥ 90%）：+1 露水（listen_music）
- 写完一篇日记并成功投入：+2 阳光（write_diary）
- 完成当日心情手帐：+1 养分（checkin）
- 连续 7 天打卡：+5 阳光（streak_7）
- 兑换物品：-cost（exchange）

所有「+x」操作都有单日上限（防刷）：
- listen_music: 20
- write_diary: 10
- checkin: 5
"""

from __future__ import annotations

from datetime import datetime, date
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.energy import EnergyRecord
from app.models.garden import ShopItem, GardenItem
from app.utils.constants import (
    ENERGY_LABELS,
    DAILY_ENERGY_LIMITS,
    DEFAULT_SHOP_ITEMS,
)


# ─────────────────────────────────────────────────────────────
# 内部辅助
# ─────────────────────────────────────────────────────────────

def _today_start() -> datetime:
    """今天 00:00:00。"""
    today = date.today()
    return datetime(today.year, today.month, today.day)


def today_grant_total(db: Session, user_id: int, source: str) -> int:
    """今日某种来源的累计获得量（仅正数 amount）。"""
    start = _today_start()
    total = (
        db.query(func.coalesce(func.sum(EnergyRecord.amount), 0))
        .filter(
            EnergyRecord.user_id == user_id,
            EnergyRecord.source == source,
            EnergyRecord.created_at >= start,
            EnergyRecord.amount > 0,
        )
        .scalar()
    )
    return int(total or 0)


def can_grant_today(db: Session, user_id: int, source: str, amount: int) -> bool:
    """判断本次发放是否会被单日上限截断。"""
    limit = DAILY_ENERGY_LIMITS.get(source)
    if limit is None:
        return True
    current = today_grant_total(db, user_id, source)
    return (current + amount) <= limit


# ─────────────────────────────────────────────────────────────
# 发放能量
# ─────────────────────────────────────────────────────────────

def grant_energy(
    db: Session,
    user: User,
    amount: int,
    source: str,
    note: Optional[str] = None,
    *,
    bypass_limit: bool = False,
) -> Optional[EnergyRecord]:
    """给用户发放能量，写一条 EnergyRecord，更新 user.total_energy。

    - ``amount`` 必须为正数。
    - ``bypass_limit=True`` 时跳过单日上限（用于 streak_7 / daily_bonus 等一次性奖励）。
    - 返回 None 表示达到上限被截断。
    """
    if amount <= 0:
        return None

    if not bypass_limit and not can_grant_today(db, user.id, source, amount):
        return None

    record = EnergyRecord(
        user_id=user.id,
        amount=amount,
        source=source,
        note=note,
    )
    db.add(record)
    # 用显式 UPDATE 累加，避免在长调用链里对 user 对象的赋值
    # 不会同步到 DB（边界 case：用户对象可能从上一请求的 session 残留）。
    db.query(User).filter(User.id == user.id).update(
        {User.total_energy: User.total_energy + amount}
    )
    db.flush()
    return record


# ─────────────────────────────────────────────────────────────
# 兑换
# ─────────────────────────────────────────────────────────────

def exchange_item(db: Session, user: User, item_id: int) -> GardenItem:
    """用户用能量兑换一个商店物品。"""
    item = db.get(ShopItem, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="找不到这件物品")

    cost = item.cost or 0
    if cost > 0:
        if (user.total_energy or 0) < cost:
            raise HTTPException(status_code=400, detail=f"能量不足，还差 {cost - user.total_energy}")

        # 检查是否已持有
        existing = (
            db.query(GardenItem)
            .filter(GardenItem.user_id == user.id, GardenItem.item_id == item_id)
            .first()
        )
        if existing is not None:
            raise HTTPException(status_code=400, detail="这件你已经拥有啦")

        # 扣能量 + 写流水
        record = EnergyRecord(
            user_id=user.id,
            amount=-cost,
            source="exchange",
            note=f"兑换 {item.name}",
        )
        db.add(record)
        # 同上：显式 UPDATE 避免赋值跨 session 不同步
        db.query(User).filter(User.id == user.id).update(
            {User.total_energy: User.total_energy - cost}
        )

    # 写入持有
    garden_item = GardenItem(user_id=user.id, item_id=item_id)
    db.add(garden_item)
    db.flush()
    return garden_item


# ─────────────────────────────────────────────────────────────
# 成就检查
# ─────────────────────────────────────────────────────────────

def check_achievements(db: Session, user: User) -> list[GardenItem]:
    """检查并发放自动徽章：
    - listen_10：累计听完 10 首不同曲子
    - diary_30：累计写 30 篇日记
    - streak_7：连续 7 天打卡

    返回本次新获得的 GardenItem 列表。
    """
    from app.models.music import Music
    from app.models.diary import Diary
    from app.models.mood import MoodCheckin

    newly: list[GardenItem] = []

    # 已有物品 id 集合
    owned_ids = {
        gi.item_id
        for gi in db.query(GardenItem).filter(GardenItem.user_id == user.id).all()
    }

    # 1. listen_10：累计 10 条 listen_music 记录
    listen_count = (
        db.query(func.count(EnergyRecord.id))
        .filter(EnergyRecord.user_id == user.id, EnergyRecord.source == "listen_music")
        .scalar()
    )
    if listen_count >= 10:
        trigger_item = _find_trigger_item(db, "listen_10")
        if trigger_item and trigger_item.id not in owned_ids:
            gi = GardenItem(user_id=user.id, item_id=trigger_item.id)
            db.add(gi)
            newly.append(gi)
            owned_ids.add(trigger_item.id)

    # 2. diary_30：累计 30 篇日记
    diary_count = (
        db.query(func.count(Diary.id)).filter(Diary.user_id == user.id).scalar()
    )
    if diary_count >= 30:
        trigger_item = _find_trigger_item(db, "diary_30")
        if trigger_item and trigger_item.id not in owned_ids:
            gi = GardenItem(user_id=user.id, item_id=trigger_item.id)
            db.add(gi)
            newly.append(gi)
            owned_ids.add(trigger_item.id)

    # 3. streak_7：连续 7 天打卡
    from app.services.mood_service import get_current_streak
    streak = get_current_streak(db, user.id)
    if streak >= 7:
        trigger_item = _find_trigger_item(db, "streak_7")
        if trigger_item and trigger_item.id not in owned_ids:
            gi = GardenItem(user_id=user.id, item_id=trigger_item.id)
            db.add(gi)
            newly.append(gi)
            owned_ids.add(trigger_item.id)

    if newly:
        db.flush()
    return newly


def _find_trigger_item(db: Session, trigger: str) -> Optional[ShopItem]:
    return (
        db.query(ShopItem).filter(ShopItem.trigger == trigger).first()
    )
