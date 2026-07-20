"""漂流瓶日记 API。

⚠️ 隐私关键点：
- 创建日记：客户端**先在浏览器用 PBKDF2 派生密钥 + Fernet 加密**，后端只收密文。
- 我的瓶子列表：后端**只返回密文**；前端用用户密码派生密钥解密。
- 拾取陌生人：后端返回**密文 + 对方 salt**，前端派生密钥解密。
- 后端**永远不接触明文**。
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.models.encouragement import Encouragement
from app.schemas.diary import (
    DiaryCreateIn,
    EncouragementIn,
    DiaryPublicOut,
)
from app.services.diary_service import (
    create_diary,
    list_my_diaries,
    get_diary_detail,
    pick_random_bottle,
    leave_encouragement,
    list_diary_encouragements,
)
from app.services.energy_service import grant_energy, check_achievements


router = APIRouter(prefix="/api/diary", tags=["diary"])


@router.post("", status_code=201)
def create_my_diary(
    body: DiaryCreateIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """投入一个漂流瓶。客户端负责加密。"""
    diary = create_diary(
        db, user,
        content_encrypted=body.content_encrypted,
        mood_type=body.mood_type,
        is_public=body.is_public,
    )

    # 发 +2 阳光
    grant_energy(db, user, amount=2, source="write_diary", note="写日记")
    # 检查成就
    check_achievements(db, user)
    db.commit()
    # expire_on_commit=False，user.total_energy 仍是旧值，必须重新查 DB
    new_total = db.query(User.total_energy).filter(User.id == user.id).scalar()

    return {
        "id": diary.id,
        "created_at": diary.created_at.isoformat() if diary.created_at else None,
        "granted_energy": 2,
        "new_total_energy": new_total,
    }


@router.get("/mine")
def list_mine(
    page: int = 1,
    per_page: int = 20,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """我的瓶子列表（密文）。前端用密码派生密钥解密后展示。"""
    diaries, total = list_my_diaries(db, user.id, page=page, per_page=per_page)
    return {
        "total": total,
        "page": page,
        "per_page": per_page,
        "items": [
            {
                "id": d.id,
                "content_encrypted": d.content_encrypted,
                "salt": user.encryption_salt,
                "mood_type": d.mood_type,
                "is_public": d.is_public,
                "created_at": d.created_at.isoformat() if d.created_at else None,
                "encouragement_count": len(list_diary_encouragements(db, d.id)),
            }
            for d in diaries
        ],
    }


@router.get("/{diary_id}")
def get_diary(
    diary_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """单个瓶子详情（密文 + 收到的鼓励）。"""
    diary = get_diary_detail(db, user, diary_id)
    encs = list_diary_encouragements(db, diary.id)
    return {
        "id": diary.id,
        "content_encrypted": diary.content_encrypted,
        "salt": user.encryption_salt,
        "mood_type": diary.mood_type,
        "is_public": diary.is_public,
        "created_at": diary.created_at.isoformat() if diary.created_at else None,
        "encouragements": [
            {"id": e.id, "content": e.content, "created_at": e.created_at.isoformat()}
            for e in encs
        ],
    }


@router.get("/pick/random")
def pick_random(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """随机拾取一条公开漂流瓶。返回密文 + 对方 salt。"""
    result = pick_random_bottle(db, user)
    if result is None:
        raise HTTPException(status_code=404, detail="海面上暂时没有瓶子")
    return result


@router.delete("/{diary_id}", status_code=204)
def delete_diary(
    diary_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """删除自己的漂流瓶。"""
    diary = get_diary_detail(db, user, diary_id)
    db.delete(diary)
    db.commit()
    return None


@router.post("/{diary_id}/encourage", status_code=201)
def encourage(
    diary_id: int,
    body: EncouragementIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """给一条漂流瓶留匿名鼓励语。"""
    enc = leave_encouragement(db, user, diary_id, body.content)
    db.commit()
    return {
        "id": enc.id,
        "content": enc.content,
        "created_at": enc.created_at.isoformat(),
    }
