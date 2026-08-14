"""能量 / 兑换 API。"""

from __future__ import annotations

from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.models.energy import EnergyRecord
from app.schemas.energy import EnergyRecordOut, ExchangeIn, ExchangeOut
from app.services.energy_service import exchange_item


router = APIRouter(prefix="/api/energy", tags=["energy"])


@router.get("/records", response_model=List[EnergyRecordOut])
def list_records(
    limit: int = 50,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """能量流水。"""
    records = (
        db.query(EnergyRecord)
        .filter(EnergyRecord.user_id == user.id)
        .order_by(EnergyRecord.created_at.desc())
        .limit(limit)
        .all()
    )
    return [
        EnergyRecordOut(
            id=r.id, amount=r.amount, source=r.source,
            note=r.note,
            created_at=r.created_at.isoformat() if r.created_at else "",
        )
        for r in records
    ]


@router.get("/summary")
def summary(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """当前能量 + 按来源分组累计。"""
    from sqlalchemy import func
    rows = (
        db.query(EnergyRecord.source, func.sum(EnergyRecord.amount))
        .filter(EnergyRecord.user_id == user.id)
        .group_by(EnergyRecord.source)
        .all()
    )
    by_source = {r[0]: int(r[1] or 0) for r in rows}
    return {
        "total_energy": user.total_energy or 0,
        "by_source": by_source,
    }


@router.post("/exchange", response_model=ExchangeOut)
def exchange(
    body: ExchangeIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """兑换商店物品。

    v2.3：花种用落叶兑换（直接种到屿上花田），装扮用露水兑换。
    v2.4.2：兑换花种后检查 flower_10 徽章（种满 10 朵花 → 花间客）。
    """
    from app.services.energy_service import check_achievements

    gi = exchange_item(db, user, body.item_id)
    # v2.4.2：兑换花种可能触发 flower_10 徽章
    achievement = check_achievements(db, user)
    db.commit()
    # expire_on_commit=False，user 字段仍是旧值，必须重新查 DB
    row = db.query(User.total_energy, User.leaves).filter(User.id == user.id).one()
    return ExchangeOut(
        success=True,
        new_total_energy=row[0] or 0,
        new_leaves=row[1] or 0,
        garden_item=gi.to_dict(),
        badge_new_leaves=achievement.get("new_leaves", 0),
        badge_leaves_balance=achievement.get("leaves_balance", 0),
        new_badges=achievement.get("new_badges", []),
    )
