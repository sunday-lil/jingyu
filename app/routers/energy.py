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
    """兑换商店物品。"""
    gi = exchange_item(db, user, body.item_id)
    db.commit()
    return ExchangeOut(
        success=True,
        new_total_energy=user.total_energy or 0,
        garden_item=gi.to_dict(),
    )
