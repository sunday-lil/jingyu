"""心情打卡服务。

- 支持一天多条心情记录（v2.4）：情绪是多变的，一天可以记录多次。
- 不允许补录昨天（check_date != today 视为补录，拒收）。
- 月历视图：返回指定月份所有打卡（按日期分组）。
- 30 天趋势：返回近 30 天每日心情代码（多条取平均分）。
- 连续打卡天数：今天往前数。
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.mood import MoodCheckin
from app.models.user import User
from app.utils.constants import MOOD_INFO


# ─────────────────────────────────────────────────────────────
# 写入
# ─────────────────────────────────────────────────────────────

def add_checkin(
    db: Session,
    user: User,
    mood_emoji: str,
    note: Optional[str] = None,
    check_date: Optional[date] = None,
) -> MoodCheckin:
    """添加一条心情记录（一天可以有多条）。

    - check_date 默认今天。
    - 不允许补录昨天及更早。
    """
    if mood_emoji not in MOOD_INFO:
        raise HTTPException(status_code=400, detail="心情代码不认识")

    target = check_date or date.today()
    if target != date.today():
        raise HTTPException(status_code=400, detail="只能记录今天的心情哦")

    record = MoodCheckin(
        user_id=user.id,
        check_date=target,
        mood_emoji=mood_emoji,
        note=note,
    )
    db.add(record)
    db.flush()
    return record


def get_today_moods(db: Session, user_id: int) -> list[MoodCheckin]:
    """获取今日所有心情记录。"""
    return (
        db.query(MoodCheckin)
        .filter(
            MoodCheckin.user_id == user_id,
            MoodCheckin.check_date == date.today(),
        )
        .order_by(MoodCheckin.created_at.asc())
        .all()
    )


# ─────────────────────────────────────────────────────────────
# 查询
# ─────────────────────────────────────────────────────────────

def get_month_checkins(
    db: Session, user_id: int, year: int, month: int
) -> list[MoodCheckin]:
    """返回某年某月所有打卡记录（含一天多条）。"""
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
        .order_by(MoodCheckin.check_date.asc(), MoodCheckin.created_at.asc())
        .all()
    )


def get_recent_trend(db: Session, user_id: int, days: int = 30) -> list[dict]:
    """最近 N 天每日心情（多条取平均分，无打卡返回 None）。

    趋势柱子的高度衡量方式：
    - 每种心情有一个 1~5 的分数（极度开心=5, 开心=4, 平静=3, 疲惫/焦虑=2, 生气/悲伤=1）
    - 如果一天只有一条记录，柱子高度 = 该心情分数 / 5
    - 如果一天有多条记录，柱子高度 = 所有心情分数的平均值 / 5
      例如：一天记录了「生气(1)」和「开心(4)」，平均分 = (1+4)/2 = 2.5，柱子中等偏低
    - 柱子越高代表那天整体心情越好，越低代表越低落
    """
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
    # 按日期分组
    by_date: dict[date, list[MoodCheckin]] = {}
    for r in records:
        by_date.setdefault(r.check_date, []).append(r)

    # 心情分数映射（与前端 MOOD_INFO 的 score 对齐）
    MOOD_SCORE = {
        "ecstatic": 5, "happy": 4, "calm": 3,
        "tired": 2, "anxious": 2, "angry": 1, "sad": 1,
    }

    result: list[dict] = []
    for i in range(days):
        d = start + timedelta(days=i)
        day_records = by_date.get(d)
        if not day_records:
            result.append({
                "date": d.isoformat(),
                "mood_emoji": None,
                "label": None,
                "color": None,
                "note": None,
            })
        else:
            # 取平均分
            scores = [MOOD_SCORE.get(r.mood_emoji, 3) for r in day_records]
            avg_score = sum(scores) / len(scores)
            # 主心情：取分数最接近平均分的那条（用于显示 emoji 和 label）
            # 如果只有一条，直接用那条
            if len(day_records) == 1:
                main_record = day_records[0]
                info = MOOD_INFO.get(main_record.mood_emoji)
            else:
                # 多条：选最接近平均分的心情
                main_record = min(
                    day_records,
                    key=lambda r: abs(MOOD_SCORE.get(r.mood_emoji, 3) - avg_score),
                )
                info = MOOD_INFO.get(main_record.mood_emoji)
                # 标注多条
            result.append({
                "date": d.isoformat(),
                "mood_emoji": main_record.mood_emoji,
                "label": info["label"] if info else None,
                "color": info["color"] if info else None,
                "note": main_record.note if main_record.note else None,
                "mood_count": len(day_records),
                "avg_score": round(avg_score, 2),
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
