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
    BADGE_LEAF_REWARDS,
    BADGE_LEAF_REWARD_DEFAULT,
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
    music_id: Optional[int] = None,
) -> Optional[EnergyRecord]:
    """给用户发放能量，写一条 EnergyRecord，更新 user.total_energy。

    - ``amount`` 必须为正数。
    - ``bypass_limit=True`` 时跳过单日上限（用于 streak_7 / daily_bonus 等一次性奖励）。
    - ``music_id`` 仅 listen_music 来源用，写入 EnergyRecord.music_id 供 24h 去重查询。
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
        music_id=music_id,
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
    """用户兑换一个商店物品。

    v2.3 调整：双货币系统。
    - 花种（item_type=flower）：用 ``leaves``（落叶）兑换。
    - 装扮（item_type=costume）：用 ``total_energy``（露水）兑换。
    - 徽章（item_type=badge）：cost=0，自动触发，不在这里走。
    """
    item = db.get(ShopItem, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="找不到这件物品")

    # 花种特殊处理：兑换后直接种到屿上花田（不进 garden_items）
    if item.item_type == "flower":
        return _exchange_flower_seed(db, user, item)

    # 检查是否已持有（对所有物品都检查，包括 cost=0 的徽章）
    existing = (
        db.query(GardenItem)
        .filter(GardenItem.user_id == user.id, GardenItem.item_id == item_id)
        .first()
    )
    if existing is not None:
        raise HTTPException(status_code=400, detail="这件你已经拥有啦")

    cost = item.cost or 0
    currency = item.cost_currency or "dew"

    if cost > 0:
        if currency == "leaves":
            # 落叶兑换（理论上 costume 不会走这里，留作扩展）
            if (user.leaves or 0) < cost:
                raise HTTPException(status_code=400, detail=f"落叶不足，还差 {cost - user.leaves}")
            db.query(User).filter(User.id == user.id).update(
                {User.leaves: User.leaves - cost}
            )
        else:
            # 露水兑换
            if (user.total_energy or 0) < cost:
                raise HTTPException(status_code=400, detail=f"露水不足，还差 {cost - user.total_energy}")
            record = EnergyRecord(
                user_id=user.id,
                amount=-cost,
                source="exchange",
                note=f"兑换 {item.name}",
            )
            db.add(record)
            db.query(User).filter(User.id == user.id).update(
                {User.total_energy: User.total_energy - cost}
            )

    # 写入持有
    garden_item = GardenItem(user_id=user.id, item_id=item_id)
    db.add(garden_item)
    db.flush()
    return garden_item


def _exchange_flower_seed(db: Session, user: User, item: ShopItem) -> GardenItem:
    """兑换花种：扣落叶 → 直接种到 user_flowers 表（stage=seed）。

    返回一个伪 GardenItem 包装（to_dict 包含 flower 信息），前端按需展示。
    """
    from app.models.garden import UserFlower, STAGE_SEED

    cost = item.cost or 0
    if cost > 0:
        if (user.leaves or 0) < cost:
            raise HTTPException(status_code=400, detail=f"落叶不足，还差 {cost - user.leaves}")
        db.query(User).filter(User.id == user.id).update(
            {User.leaves: User.leaves - cost}
        )

    # 种下：flower_type 用 item.name（中文花名）作为 key
    flower = UserFlower(
        user_id=user.id,
        flower_type=item.name,
        stage=STAGE_SEED,
        watered_count=0,
    )
    db.add(flower)
    db.flush()

    # 返回一个包装对象，前端用 is_flower_seed 字段区分
    class _FlowerSeedResult:
        def to_dict(self) -> dict:
            return {
                "id": flower.id,
                "is_flower_seed": True,
                "flower_type": item.name,
                "image": item.image,
                "stage": STAGE_SEED,
                "planted_at": flower.planted_at.isoformat() if flower.planted_at else None,
            }
    return _FlowerSeedResult()


# ─────────────────────────────────────────────────────────────
# 成就检查
# ─────────────────────────────────────────────────────────────

def check_achievements(db: Session, user: User) -> dict:
    """检查并发放自动徽章：
    - listen_10：累计听完 10 首不同曲子 → 琴音知音
    - diary_30：累计写 30 篇日记 → 日记达人
    - streak_7：连续 7 天打卡 → 七日静心
    - pick_10：拾满 10 个漂流瓶 → 拾瓶旅人
    - chat_20：与树洞对话满 20 次 → 树洞倾心
    - flower_10：种满 10 朵花 → 花间客

    v2.4.2：每解锁一个徽章额外发放 BADGE_LEAF_REWARD 片落叶，
    打破「没花没落叶」的死锁，让用户能种下第一朵花。

    返回 dict：
      {
        "new_badges": [{name, image, description}, ...],  # 本次新解锁徽章
        "new_leaves": int,    # 本次奖励的落叶总数
        "leaves_balance": int # 当前落叶余额（DB 最新值）
      }
    """
    from app.models.music import Music
    from app.models.diary import Diary
    from app.models.mood import MoodCheckin
    from app.models.garden import UserFlower

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

    # 4. pick_10：拾满 10 个漂流瓶
    pick_count = (
        db.query(func.count(EnergyRecord.id))
        .filter(EnergyRecord.user_id == user.id, EnergyRecord.source == "encourage")
        .scalar()
    )
    if pick_count >= 10:
        trigger_item = _find_trigger_item(db, "pick_10")
        if trigger_item and trigger_item.id not in owned_ids:
            gi = GardenItem(user_id=user.id, item_id=trigger_item.id)
            db.add(gi)
            newly.append(gi)
            owned_ids.add(trigger_item.id)

    # 5. chat_20：与树洞对话满 20 次
    chat_count = (
        db.query(func.count(EnergyRecord.id))
        .filter(EnergyRecord.user_id == user.id, EnergyRecord.source == "chat")
        .scalar()
    )
    if chat_count >= 20:
        trigger_item = _find_trigger_item(db, "chat_20")
        if trigger_item and trigger_item.id not in owned_ids:
            gi = GardenItem(user_id=user.id, item_id=trigger_item.id)
            db.add(gi)
            newly.append(gi)
            owned_ids.add(trigger_item.id)

    # 6. flower_10：种满 10 朵花
    flower_count = (
        db.query(func.count(UserFlower.id))
        .filter(UserFlower.user_id == user.id)
        .scalar()
    )
    if flower_count >= 10:
        trigger_item = _find_trigger_item(db, "flower_10")
        if trigger_item and trigger_item.id not in owned_ids:
            gi = GardenItem(user_id=user.id, item_id=trigger_item.id)
            db.add(gi)
            newly.append(gi)
            owned_ids.add(trigger_item.id)

    if newly:
        db.flush()

    # ── v2.4.4：解锁徽章奖励落叶（按 trigger 分级）──
    new_leaves_total = 0
    new_badges_info: list[dict] = []
    if newly:
        for gi in newly:
            item = db.get(ShopItem, gi.item_id)
            if item:
                reward = BADGE_LEAF_REWARDS.get(item.trigger, BADGE_LEAF_REWARD_DEFAULT)
                new_leaves_total += reward
                new_badges_info.append({
                    "name": item.name,
                    "image": item.image,
                    "description": item.description,
                })
        if new_leaves_total > 0:
            db.query(User).filter(User.id == user.id).update(
                {User.leaves: User.leaves + new_leaves_total}
            )
            db.flush()

    # 取 DB 最新落叶余额（expire_on_commit=False 场景下 user.leaves 可能是旧值）
    leaves_balance = db.query(User.leaves).filter(User.id == user.id).scalar()

    return {
        "new_badges": new_badges_info,
        "new_leaves": new_leaves_total,
        "leaves_balance": int(leaves_balance or 0),
    }


def _find_trigger_item(db: Session, trigger: str) -> Optional[ShopItem]:
    return (
        db.query(ShopItem).filter(ShopItem.trigger == trigger).first()
    )
