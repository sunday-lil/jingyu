"""心情打卡 API。"""

from __future__ import annotations

from datetime import date
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.schemas.mood import MoodCheckinIn, MoodCheckinOut
from app.services.mood_service import (
    upsert_checkin,
    get_month_checkins,
    get_recent_trend,
    get_current_streak,
)
from app.services.energy_service import grant_energy, check_achievements


router = APIRouter(prefix="/api/mood", tags=["mood"])


@router.post("/checkin", response_model=MoodCheckinOut)
def checkin(
    body: MoodCheckinIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """今日打卡或覆盖。"""
    record = upsert_checkin(
        db, user,
        mood_emoji=body.mood_emoji,
        note=body.note,
        check_date=body.check_date,
    )
    # 发 +1 养分（如果今天没发过）
    grant_energy(db, user, amount=1, source="checkin", note="今日手帐")
    # 7 日连胜额外 +5 阳光
    streak = get_current_streak(db, user.id)
    if streak == 7:
        grant_energy(
            db, user, amount=5, source="streak_7",
            note="连续 7 天打卡", bypass_limit=True
        )
    check_achievements(db, user)
    db.commit()

    return MoodCheckinOut(
        id=record.id,
        check_date=record.check_date.isoformat(),
        mood_emoji=record.mood_emoji,
        note=record.note,
        created_at=record.created_at.isoformat() if record.created_at else "",
    )


@router.get("/today")
def today_checkin(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """今日是否已打卡。"""
    from app.models.mood import MoodCheckin
    record = (
        db.query(MoodCheckin)
        .filter(MoodCheckin.user_id == user.id, MoodCheckin.check_date == date.today())
        .first()
    )
    if record is None:
        return {"checked_in": False}
    return {
        "checked_in": True,
        "mood_emoji": record.mood_emoji,
        "note": record.note,
        "check_date": record.check_date.isoformat(),
    }


@router.get("/calendar")
def calendar(
    year: int = Query(default=None),
    month: int = Query(default=None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """某月所有打卡。默认本月。"""
    today = date.today()
    y = year or today.year
    m = month or today.month
    records = get_month_checkins(db, user.id, y, m)
    return {
        "year": y, "month": m,
        "items": [
            {
                "check_date": r.check_date.isoformat(),
                "mood_emoji": r.mood_emoji,
                "note": r.note,
            }
            for r in records
        ],
    }


@router.get("/trend")
def trend(
    days: int = Query(default=30, ge=7, le=90),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """近 N 天每日心情趋势。"""
    items = get_recent_trend(db, user.id, days)
    streak = get_current_streak(db, user.id)
    return {"days": days, "items": items, "current_streak": streak}
