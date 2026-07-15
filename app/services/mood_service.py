"""心情打卡服务。

- 每日一条 upsert：重复打卡覆盖。
- 不允许补录昨天（check_date != today 视为补录，拒收）。
- 月历视图：返回指定月份所有打卡。
- 30 天趋势：返回近 30 天每日心情代码（无打卡日为 None）。
- 连续打卡天数：今天往前数。
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Optional

from fastapi import HTTPException
from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.models.mood import MoodCheckin
from app.models.user import User
from app.utils.constants import MOOD_INFO


# ─────────────────────────────────────────────────────────────
# 写入
# ─────────────────────────────────────────────────────────────

def upsert_checkin(
    db: Session,
    user: User,
    mood_emoji: str,
    note: Optional[str] = None,
    check_date: Optional[date] = None,
) -> MoodCheckin:
    """打卡或覆盖今天的心情的。
    - check_date 默认今天。
    - 不允许补录昨天及更早。
    """
    if mood_emoji not in MOOD_INFO:
        raise HTTPException(status_code=400, detail="心情代码不认识")

    target = check_date or date.today()
    if target != date.today():
        raise HTTPException(status_code=400, detail="只能记录今天的心情哦")

    record = (
        db.query(MoodCheckin)
        .filter(MoodCheckin.user_id == user.id, MoodCheckin.check_date == target)
        .first()
    )
    if record is None:
        record = MoodCheckin(
            user_id=user.id,
            check_date=target,
            mood_emoji=mood_emoji,
            note=note,
        )
        db.add(record)
    else:
        record.mood_emoji = mood_emoji
        record.note = note
    db.flush()
    return record


# ─────────────────────────────────────────────────────────────
# 查询
# ─────────────────────────────────────────────────────────────

def get_month_checkins(
    db: Session, user_id: int, year: int, month: int
) -> list[MoodCheckin]:
    """返回某年某月所有打卡记录。"""
    start = date(year, month, 1)
    if month == 12:
        end = date(year + 1, 1, 1)
    else:
        end = date(year, month + 1, 1)
    return (
        db.query(MoodCheckin)
        .filter(
            MoodCheckin.user_id == user_id,
            MoodCheckin.check_date >= start,
            MoodCheckin.check_date < end,
        )
        .order_by(MoodCheckin.check_date.asc())
        .all()
    )


def get_recent_trend(db: Session, user_id: int, days: int = 30) -> list[dict]:
    """最近 N 天每日心情（无打卡返回 None）。"""
    today = date.today()
    start = today - timedelta(days=days - 1)

    records = (
        db.query(MoodCheckin)
        .filter(
            MoodCheckin.user_id == user_id,
            MoodCheckin.check_date >= start,
            MoodCheckin.check_date <= today,
        )
        .all()
    )
    by_date = {r.check_date: r for r in records}

    result: list[dict] = []
    for i in range(days):
        d = start + timedelta(days=i)
        r = by_date.get(d)
        info = MOOD_INFO.get(r.mood_emoji) if r else None
        result.append({
            "date": d.isoformat(),
            "mood_emoji": r.mood_emoji if r else None,
            "label": info["label"] if info else None,
            "color": info["color"] if info else None,
            "note": r.note if r else None,
        })
    return result


def get_current_streak(db: Session, user_id: int) -> int:
    """从今天往前数连续打卡天数。允许今天没打卡但昨天及之前连续。"""
    today = date.today()
    streak = 0
    # 从今天开始，往前找
    d = today
    while True:
        exists = (
            db.query(MoodCheckin)
            .filter(MoodCheckin.user_id == user_id, MoodCheckin.check_date == d)
            .first()
        )
        if exists is not None:
            streak += 1
            d = d - timedelta(days=1)
        else:
            # 如果是今天且没有，容许从昨天开始
            if d == today:
                d = d - timedelta(days=1)
                continue
            break
    return streak
