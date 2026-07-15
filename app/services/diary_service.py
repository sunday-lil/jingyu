"""日记 / 漂流瓶服务。

- 创建漂流瓶：接收客户端加密后的密文（不接触明文）。
- 我的瓶子列表：本人可看密文，由前端用密码派生密钥解密（前端加密 / 解密，后端只管存密文）。
- 拾取陌生人漂流瓶：随机选一条 is_public=True 的日记，**服务端用该用户密码的派生密钥解密后**返回明文（仅当时可见，不缓存，不入库明文）。
- 鼓励语：匿名留言，对方在「我的瓶子」详情页可见「收到 N 个陌生人的拥抱」。
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
from app.utils.crypto import decrypt_diary


# ─────────────────────────────────────────────────────────────
# 创建
# ─────────────────────────────────────────────────────────────

def create_diary(
    db: Session,
    user: User,
    content_encrypted: str,
    mood_type: Optional[str] = None,
    is_public: bool = False,
) -> Diary:
    """写入一条漂流瓶。客户端负责加密，本服务只存密文。"""
    diary = Diary(
        user_id=user.id,
        content_encrypted=content_encrypted,
        mood_type=mood_type,
        is_public=is_public,
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
    """我的漂流瓶列表（时间倒序）。"""
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
    *,
    current_password: Optional[str] = None,
) -> Optional[dict]:
    """随机拾取一条公开漂流瓶。

    - 不取自己的。
    - 解密需要**当前用户密码**（用于派生密钥），所以需要登录用户在请求中带明文密码。
      出于安全考虑，这里采用**前端方案**：前端拿到密文后，在浏览器用 PBKDF2 派生密钥再解密。
      因此本服务只返回密文 + 元数据，**不返回明文**。

    返回 dict: {id, mood_type, content_encrypted, salt, created_at, encouragement_count}
    """
    candidates = (
        db.query(Diary)
        .filter(Diary.is_public == True, Diary.user_id != current_user.id)  # noqa: E712
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
    # 返回日记所有者的 encryption_salt（让前端派生密钥解密）
    owner = db.get(User, chosen.user_id)
    return {
        "id": chosen.id,
        "mood_type": chosen.mood_type,
        "content_encrypted": chosen.content_encrypted,
        "salt": owner.encryption_salt if owner else None,
        "created_at": chosen.created_at.isoformat() if chosen.created_at else None,
        "encouragement_count": int(enc_count or 0),
    }


# ─────────────────────────────────────────────────────────────
# 鼓励语
# ─────────────────────────────────────────────────────────────

def leave_encouragement(
    db: Session,
    from_user: User,
    diary_id: int,
    content: str,
) -> Encouragement:
    """给一条漂流瓶留一条匿名鼓励。"""
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
