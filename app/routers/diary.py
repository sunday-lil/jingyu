"""漂流瓶日记 API。

v2.3 调整：
- 移除密码加密，日记改明文存储。
- 新增发布选项：is_public（放入漂流瓶）/ send_to_ai_hole（同步树洞）。
- 拾取漂流瓶直接返回明文 content。
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.schemas.diary import (
    DiaryCreateIn,
    EncouragementIn,
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
    """写一篇日记。

    - is_public=True：放入漂流瓶，公开可见，允许评论。
    - send_to_ai_hole=True：同步至树洞（仅自己可见 + AI 对话依据）。
    """
    diary = create_diary(
        db, user,
        content=body.content,
        mood_type=body.mood_type,
        is_public=body.is_public,
        send_to_ai_hole=body.send_to_ai_hole,
    )

    # 写日记发 +2 露水
    grant_energy(db, user, amount=2, source="write_diary", note="写日记")
    check_achievements(db, user)
    db.commit()
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
    """我的日记列表（明文）。"""
    diaries, total = list_my_diaries(db, user.id, page=page, per_page=per_page)
    return {
        "total": total,
        "page": page,
        "per_page": per_page,
        "items": [
            {
                "id": d.id,
                "content": d.content,
                "mood_type": d.mood_type,
                "is_public": d.is_public,
                "send_to_ai_hole": d.send_to_ai_hole,
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
    """单个日记详情（明文 + 收到的鼓励）。"""
    diary = get_diary_detail(db, user, diary_id)
    encs = list_diary_encouragements(db, diary.id)
    return {
        "id": diary.id,
        "content": diary.content,
        "mood_type": diary.mood_type,
        "is_public": diary.is_public,
        "send_to_ai_hole": diary.send_to_ai_hole,
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
    """随机拾取一条公开漂流瓶（明文）。"""
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
    """删除自己的日记。"""
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
    """给一条漂流瓶留匿名鼓励语（评论返回发布者 + 消息提醒）。"""
    enc = leave_encouragement(db, user, diary_id, body.content)
    # 留言鼓励发 +1 露水
    grant_energy(db, user, amount=1, source="encourage", note="留言鼓励")
    db.commit()
    new_total = db.query(User.total_energy).filter(User.id == user.id).scalar()
    return {
        "id": enc.id,
        "content": enc.content,
        "created_at": enc.created_at.isoformat(),
        "granted_energy": 1,
        "new_total_energy": new_total,
    }

