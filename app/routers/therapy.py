"""身心调理 API：推荐 / 八段锦打卡 / 好物橱窗。

端点：
- POST /api/therapy/recommend          问题 → 曲 / 八段锦 / 香囊 / 手串 / 食疗
- GET  /api/therapy/catalog            好物与招式目录
- POST /api/therapy/baduanjin/checkin  八段锦跟练打卡（+1 露水/日）
- GET  /api/therapy/baduanjin/status   今日打卡状态
- POST /api/therapy/interest           好物预约/意向
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.schemas.therapy import (
    BaduanjinCheckinIn,
    TherapyInterestIn,
    TherapyRecommendIn,
)
from app.services.therapy_service import (
    BADUANJIN,
    BRACELETS,
    DISCLAIMER,
    FOODS,
    SACHETS,
    baduanjin_status,
    checkin_baduanjin,
    recommend,
    record_interest,
)


router = APIRouter(prefix="/api/therapy", tags=["therapy"])


def _catalog_products() -> list[dict]:
    items: list[dict] = []
    for group in (SACHETS, BRACELETS, FOODS):
        for data in group.values():
            items.append({
                "key": data["key"],
                "type": data["type"],
                "name": data["name"],
                "price": data["price"],
                "purchase_url": data["purchase_url"],
                "available": data["available"],
                "note": data.get("note") or data.get("serving") or "",
                "allergens": data.get("allergens"),
                "ingredients": data.get("ingredients"),
                "material": data.get("material"),
                "nature": data.get("nature"),
            })
    return items


@router.post("/recommend")
def therapy_recommend(
    body: TherapyRecommendIn,
    db: Session = Depends(get_db),
):
    """根据用户描述返回身心调理建议（不需要登录）。"""
    return recommend(db, body.problem, body.tags)


@router.get("/catalog")
def therapy_catalog():
    """返回八段锦 8 式与好物橱窗目录。"""
    return {
        "baduanjin": [
            {
                "key": key,
                "name": data["name"],
                "focus": data["focus"],
                "steps": data["steps"],
                "video_url": f"https://search.bilibili.com/all?keyword=八段锦%20{data['name']}",
            }
            for key, data in BADUANJIN.items()
        ],
        "products": _catalog_products(),
        "disclaimer": DISCLAIMER,
    }


@router.post("/baduanjin/checkin")
def baduanjin_checkin(
    body: BaduanjinCheckinIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """八段锦跟练打卡：每天一次，+1 露水。"""
    return checkin_baduanjin(db, user, body.move_key)


@router.get("/baduanjin/status")
def baduanjin_today(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """今日是否已跟练打卡。"""
    return baduanjin_status(db, user)


@router.post("/interest")
def therapy_interest(
    body: TherapyInterestIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """好物预约/意向登记；当前不涉及支付。"""
    return record_interest(db, user, body.product_key)
