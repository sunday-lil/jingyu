"""精神花园 + 商店 API。"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.models.garden import ShopItem, GardenItem


router = APIRouter(prefix="/api/garden", tags=["garden"])


@router.get("/shop")
def list_shop(db: Session = Depends(get_db)):
    """商店物品列表。"""
    items = db.query(ShopItem).order_by(ShopItem.item_type, ShopItem.cost).all()
    return [item.to_dict() for item in items]


@router.get("/mine")
def my_garden(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """我持有的所有物品。"""
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
