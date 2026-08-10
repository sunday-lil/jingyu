"""心情打卡 API。"""

from __future__ import annotations

from datetime import date
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.models.mood import MoodCheckin
from app.schemas.mood import MoodCheckinIn, MoodCheckinOut, MoodBatchIn
from app.services.mood_service import (
    add_checkin,
    get_month_checkins,
    get_recent_trend,
    get_current_streak,
    get_today_moods,
)
from app.services.energy_service import grant_energy, check_achievements
from app.utils.constants import MOOD_INFO


router = APIRouter(prefix="/api/mood", tags=["mood"])


@router.post("/checkin", response_model=MoodCheckinOut)
def checkin(
    body: MoodCheckinIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """添加一条心情记录（一天可以有多条）。"""
    record = add_checkin(
        db, user,
        mood_emoji=body.mood_emoji,
        note=body.note,
        check_date=body.check_date,
    )
    # 发 +1 养分（每次打卡都发，不再限制每日一次）
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


@router.post("/checkin/batch")
def batch_checkin(
    body: MoodBatchIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """批量添加多条心情记录（一次选择多个心情）。"""
    if not body.mood_emojis:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="至少选一个心情")

    records = []
    for mood_key in body.mood_emojis:
        record = add_checkin(
            db, user,
            mood_emoji=mood_key,
            note=body.note,
        )
        records.append(record)

    # 发 +1 养分（每次批量打卡只发一次）
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

    return {
        "count": len(records),
        "items": [
            {
                "id": r.id,
                "check_date": r.check_date.isoformat(),
                "mood_emoji": r.mood_emoji,
                "note": r.note,
                "created_at": r.created_at.isoformat() if r.created_at else "",
            }
            for r in records
        ],
    }


@router.get("/today")
def today_checkin(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """今日所有心情记录。"""
    records = get_today_moods(db, user.id)
    if not records:
        return {"checked_in": False, "moods": []}
    return {
        "checked_in": True,
        "moods": [
            {
                "id": r.id,
                "mood_emoji": r.mood_emoji,
                "note": r.note,
                "check_date": r.check_date.isoformat(),
                "created_at": r.created_at.isoformat() if r.created_at else "",
            }
            for r in records
        ],
    }


@router.get("/calendar")
def calendar(
    year: int = Query(default=None),
    month: int = Query(default=None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """某月所有打卡，按日期分组（支持一天多条）。"""
    today = date.today()
    y = year or today.year
    m = month or today.month
    records = get_month_checkins(db, user.id, y, m)
    # 按日期分组
    by_date: dict[str, list[dict]] = {}
    for r in records:
        d = r.check_date.isoformat()
        by_date.setdefault(d, []).append({
            "id": r.id,
            "mood_emoji": r.mood_emoji,
            "note": r.note,
            "created_at": r.created_at.isoformat() if r.created_at else "",
        })
    # 转为列表
    items = []
    for d, moods in sorted(by_date.items()):
        # 兼容旧格式：mood_emoji 取第一条，新增 moods 数组
        emojis = [m["mood_emoji"] for m in moods]
        items.append({
            "check_date": d,
            "mood_emoji": emojis[0],  # 兼容前端旧字段
            "mood_emojis": emojis,     # 新字段：所有心情
            "moods": moods,             # 完整记录
            "note": moods[0]["note"] if moods else None,
        })
    return {"year": y, "month": m, "items": items}


@router.get("/trend")
def trend(
    days: int = Query(default=30, ge=7, le=90),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """近 N 天每日心情趋势（多条取平均分）。"""
    items = get_recent_trend(db, user.id, days)
    streak = get_current_streak(db, user.id)
    return {"days": days, "items": items, "current_streak": streak}
