"""屿上花田 — 花朵生长周期服务。

v2.3 新增。

生长阶段：
- seed（种子）→ sprout（发芽）→ bud（花苞）→ bloom（盛开）→ wilted（枯萎）

浇灌规则：
- 用露水（total_energy）浇灌已种下的花朵。
- 每阶段累计浇水达阈值 → 升级到下一阶段，watered_count 归零。
- 升级到 bloom 时记录 bloom_at。
- 盛开后超过 WILT_DAYS_AFTER_BLOOM 天未浇水 → 自动枯萎（lazy 检查）。

枯萎与落叶：
- 枯萎花朵可"拾取"→ 转化为若干落叶（leaves）→ 从 user_flowers 删除。
- 寓意：花落归土，化作春泥更护花。
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.garden import (
    UserFlower,
    STAGE_SEED,
    STAGE_SPROUT,
    STAGE_BUD,
    STAGE_BLOOM,
    STAGE_WILTED,
    STAGE_ORDER,
    WATER_TO_NEXT_STAGE,
    WILT_DAYS_AFTER_BLOOM,
)

# 拾取枯萎花获得的落叶数
LEAVES_FROM_WILTED_FLOWER = 2


def _check_wilt(flower: UserFlower) -> bool:
    """检查盛开花朵是否该枯萎（lazy）。

    盛开超过 WILT_DAYS_AFTER_BLOOM 天且未再浇水 → 标记枯萎。
    返回是否触发了枯萎。
    """
    if flower.stage != STAGE_BLOOM or flower.bloom_at is None:
        return False
    # 若有最后一次浇水时间，从浇水算起；否则从盛开算起
    base_time = flower.last_watered_at or flower.bloom_at
    if datetime.now() - base_time > timedelta(days=WILT_DAYS_AFTER_BLOOM):
        flower.stage = STAGE_WILTED
        flower.wilted_at = datetime.now()
        return True
    return False


def list_my_flowers(db: Session, user_id: int) -> list[UserFlower]:
    """列出我在屿上花田的所有花朵（含枯萎待拾取的）。"""
    flowers = (
        db.query(UserFlower)
        .filter(UserFlower.user_id == user_id)
        .order_by(UserFlower.planted_at.desc())
        .all()
    )
    # lazy 检查枯萎
    changed = False
    for f in flowers:
        if _check_wilt(f):
            changed = True
    if changed:
        db.flush()
    return flowers


def water_flower(db: Session, user: User, flower_id: int) -> UserFlower:
    """用露水浇灌一朵花。

    - 每次浇灌消耗 1 露水（total_energy -1）。
    - 累计浇水达阈值 → 升级。
    - 升级到 bloom 时记录 bloom_at。
    - 若花已枯萎，不能浇。
    """
    flower = db.get(UserFlower, flower_id)
    if flower is None or flower.user_id != user.id:
        raise HTTPException(status_code=404, detail="这朵花不在你的岛上")

    # lazy 检查枯萎
    _check_wilt(flower)

    if flower.stage == STAGE_WILTED:
        raise HTTPException(status_code=400, detail="花已枯萎，无法再浇水。可以拾取它化作落叶")

    if flower.stage == STAGE_BLOOM:
        # 盛开后再浇水：刷新 last_watered_at，延长枯萎时间
        flower.last_watered_at = datetime.now()
        db.flush()
        return flower

    # 检查露水
    if (user.total_energy or 0) < 1:
        raise HTTPException(status_code=400, detail="露水不足，先去听一曲古琴或写篇日记吧")

    # 扣 1 露水
    db.query(User).filter(User.id == user.id).update(
        {User.total_energy: User.total_energy - 1}
    )

    # 累计浇水
    flower.watered_count = (flower.watered_count or 0) + 1
    flower.last_watered_at = datetime.now()

    needed = WATER_TO_NEXT_STAGE.get(flower.stage, 0)
    if needed > 0 and flower.watered_count >= needed:
        # 升级
        idx = STAGE_ORDER.index(flower.stage)
        if idx + 1 < len(STAGE_ORDER):
            new_stage = STAGE_ORDER[idx + 1]
            flower.stage = new_stage
            flower.watered_count = 0
            if new_stage == STAGE_BLOOM:
                flower.bloom_at = datetime.now()

    db.flush()
    return flower


def collect_wilted_leaves(db: Session, user: User, flower_id: int) -> int:
    """拾取枯萎的花朵 → 转化为落叶 → 删除该花。

    返回获得的落叶数。
    """
    flower = db.get(UserFlower, flower_id)
    if flower is None or flower.user_id != user.id:
        raise HTTPException(status_code=404, detail="这朵花不在你的岛上")

    # lazy 检查
    _check_wilt(flower)

    if flower.stage != STAGE_WILTED:
        raise HTTPException(status_code=400, detail="这朵花还没枯萎，不能拾取")

    # 增加落叶
    db.query(User).filter(User.id == user.id).update(
        {User.leaves: User.leaves + LEAVES_FROM_WILTED_FLOWER}
    )

    # 删除枯花
    db.delete(flower)
    db.flush()
    return LEAVES_FROM_WILTED_FLOWER


def get_flower_detail(db: Session, user: User, flower_id: int) -> UserFlower:
    flower = db.get(UserFlower, flower_id)
    if flower is None or flower.user_id != user.id:
        raise HTTPException(status_code=404, detail="这朵花不在你的岛上")
    _check_wilt(flower)
    db.flush()
    return flower
