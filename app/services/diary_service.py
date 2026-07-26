"""日记 / 漂流瓶服务。

v2.3 调整：
- 移除密码加密，日记改明文存储（content 字段）。
- 拾取漂流瓶直接返回明文 content（不再需要前端解密）。
- 鼓励语留言后创建 Notification，通知漂流瓶所有者。
"""

from __future__ import annotations

import random
from datetime import datetime, date
from typing import Optional

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.diary import Diary
from app.models.encouragement import Encouragement
from app.models.notification import Notification


# ─────────────────────────────────────────────────────────────
# 创建
# ─────────────────────────────────────────────────────────────

def create_diary(
    db: Session,
    user: User,
    content: str,
    mood_type: Optional[str] = None,
    is_public: bool = False,
    send_to_ai_hole: bool = False,
) -> Diary:
    """写入一条日记（明文）。

    - is_public=True：放入漂流瓶，公开可见，允许评论。
    - is_public=False & send_to_ai_hole=True：仅自己可见，同步至树洞。
    - is_public=False & send_to_ai_hole=False：仅自己可见。
    """
    diary = Diary(
        user_id=user.id,
        content=content,
        content_encrypted="",  # 老库 NOT NULL 兼容占位，新代码不使用
        mood_type=mood_type,
        is_public=is_public,
        send_to_ai_hole=send_to_ai_hole,
    )
    db.add(diary)
    db.flush()
    return diary


# ─────────────────────────────────────────────────────────────
# 我的瓶子
# ─────────────────────────────────────────────────────────────

def list_my_diaries(
    db: Session,
    user_id: int,
    *,
    page: int = 1,
    per_page: int = 20,
) -> tuple[list[Diary], int]:
    """我的日记列表（时间倒序）。"""
    q = db.query(Diary).filter(Diary.user_id == user_id)
    total = q.count()
    diaries = (
        q.order_by(Diary.created_at.desc())
        .limit(per_page)
        .offset((page - 1) * per_page)
        .all()
    )
    return diaries, total


def get_diary_detail(db: Session, user: User, diary_id: int) -> Diary:
    diary = db.get(Diary, diary_id)
    if diary is None or diary.user_id != user.id:
        raise HTTPException(status_code=404, detail="漂流瓶已被海浪卷走")
    return diary


# ─────────────────────────────────────────────────────────────
# 陌生人拾取
# ─────────────────────────────────────────────────────────────

def pick_random_bottle(
    db: Session,
    current_user: User,
) -> Optional[dict]:
    """随机拾取一条公开漂流瓶（明文返回）。

    - 不取自己的。
    - v2.3 起漂流瓶明文存储，直接返回 content。
    """
    candidates = (
        db.query(Diary)
        .filter(Diary.is_public == True, Diary.user_id != current_user.id)  # noqa: E712
        .order_by(Diary.created_at.desc())
        .limit(50)
        .all()
    )
    if not candidates:
        return None
    chosen = random.choice(candidates)
    enc_count = (
        db.query(func.count(Encouragement.id))
        .filter(Encouragement.diary_id == chosen.id)
        .scalar()
    )
    return {
        "id": chosen.id,
        "mood_type": chosen.mood_type,
        "content": chosen.content,
        "created_at": chosen.created_at.isoformat() if chosen.created_at else None,
        "encouragement_count": int(enc_count or 0),
    }


# ─────────────────────────────────────────────────────────────
# 鼓励语（评论）
# ─────────────────────────────────────────────────────────────

def leave_encouragement(
    db: Session,
    from_user: User,
    diary_id: int,
    content: str,
) -> Encouragement:
    """给一条漂流瓶留一条匿名鼓励，并通知漂流瓶所有者。"""
    diary = db.get(Diary, diary_id)
    if diary is None:
        raise HTTPException(status_code=404, detail="漂流瓶不存在")
    if diary.user_id == from_user.id:
        raise HTTPException(status_code=400, detail="不能给自己鼓励哦")
    enc = Encouragement(
        from_user_id=from_user.id,
        to_user_id=diary.user_id,
        diary_id=diary_id,
        content=content[:200],
    )
    db.add(enc)
    db.flush()
    # 创建站内通知（v2.3 新增：评论返回发布者 + 消息提醒）
    notif = Notification(
        user_id=diary.user_id,
        type="encouragement",
        content=f"你的漂流瓶收到了一条匿名鼓励：「{content[:30]}{'…' if len(content) > 30 else ''}」",
        related_id=diary_id,
    )
    db.add(notif)
    db.flush()
    return enc


def list_diary_encouragements(
    db: Session, diary_id: int
) -> list[Encouragement]:
    """某条漂流瓶收到的所有鼓励（按时间正序）。"""
    return (
        db.query(Encouragement)
        .filter(Encouragement.diary_id == diary_id)
        .order_by(Encouragement.created_at.asc())
        .all()
    )
