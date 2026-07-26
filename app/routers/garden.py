"""屿上花田 + 落叶画坊（商店）API。

v2.3 调整：
- /api/garden/flowers：花朵生长周期（列表/浇水/拾叶）
- /api/garden/shop：商店列表（含 cost_currency 双货币）
- /api/garden/mine：我持有的装扮/徽章
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.models.garden import ShopItem, GardenItem
from app.services.flower_service import (
    list_my_flowers,
    water_flower,
    collect_wilted_leaves,
    get_flower_detail,
)


router = APIRouter(prefix="/api/garden", tags=["garden"])


@router.get("/shop")
def list_shop(db: Session = Depends(get_db)):
    """商店物品列表（含 cost_currency）。"""
    items = db.query(ShopItem).order_by(ShopItem.item_type, ShopItem.cost).all()
    return [item.to_dict() for item in items]


@router.get("/mine")
def my_garden(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """我持有的所有物品（装扮 + 徽章，不含花种——花种直接种到花田）。"""
    items = (
        db.query(GardenItem)
        .filter(GardenItem.user_id == user.id)
        .order_by(GardenItem.obtained_at.desc())
        .all()
    )
    return {
        "count": len(items),
        "items": [gi.to_dict() for gi in items],
    }


# ─────────────────────────────────────────────────────────────
# 花朵生长周期（屿上花田）
# ─────────────────────────────────────────────────────────────

@router.get("/flowers")
def list_flowers(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """我在屿上花田的所有花朵。"""
    flowers = list_my_flowers(db, user.id)
    return {
        "count": len(flowers),
        "items": [f.to_dict() for f in flowers],
    }


@router.get("/flowers/{flower_id}")
def flower_detail(
    flower_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """单朵花详情。"""
    f = get_flower_detail(db, user, flower_id)
    return f.to_dict()


@router.post("/flowers/{flower_id}/water")
def water(
    flower_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """用露水浇灌一朵花（消耗 1 露水）。"""
    f = water_flower(db, user, flower_id)
    db.commit()
    # 重新查最新的露水余额
    new_total = db.query(User.total_energy).filter(User.id == user.id).scalar()
    result = f.to_dict()
    result["new_total_energy"] = new_total or 0
    return result


@router.post("/flowers/{flower_id}/collect")
def collect_leaves(
    flower_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """拾取枯萎的花朵 → 转化为落叶。"""
    gained = collect_wilted_leaves(db, user, flower_id)
    db.commit()
    new_leaves = db.query(User.leaves).filter(User.id == user.id).scalar()
    return {
        "success": True,
        "gained_leaves": gained,
        "new_leaves": new_leaves or 0,
    }
