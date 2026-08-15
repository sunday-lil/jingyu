"""个人主页 API。

v2.3 新增。v2.4 增加头像 / 昵称修改。

端点：
- GET   /api/profile           我自己的主页（公开统计 + 资源 + 成就）
- PATCH /api/profile           更新我的头像 / 昵称
- GET   /api/profile/stats     我的统计数据（日记数 / 打卡天数 / 听曲数 / 花朵数）
- GET   /api/profile/{user_id} 他人主页（仅展示公开信息）
"""

from __future__ import annotations

import time
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.models.diary import Diary
from app.models.mood import MoodCheckin
from app.models.energy import EnergyRecord
from app.models.garden import GardenItem, UserFlower
from app.models.encouragement import Encouragement
from app.schemas.profile import ProfileUpdateIn


router = APIRouter(prefix="/api/profile", tags=["profile"])


def _build_profile(db: Session, user: User, is_self: bool) -> dict:
    """构建主页数据。"""
    # 统计
    diary_count = (
        db.query(func.count(Diary.id)).filter(Diary.user_id == user.id).scalar() or 0
    )
    public_diary_count = (
        db.query(func.count(Diary.id))
        .filter(Diary.user_id == user.id, Diary.is_public == True)  # noqa: E712
        .scalar() or 0
    )
    checkin_count = (
        db.query(func.count(MoodCheckin.id))
        .filter(MoodCheckin.user_id == user.id).scalar() or 0
    )
    listen_count = (
        db.query(func.count(EnergyRecord.id))
        .filter(
            EnergyRecord.user_id == user.id,
            EnergyRecord.source == "listen_music",
        ).scalar() or 0
    )
    flower_count = (
        db.query(func.count(UserFlower.id))
        .filter(UserFlower.user_id == user.id).scalar() or 0
    )
    garden_item_count = (
        db.query(func.count(GardenItem.id))
        .filter(GardenItem.user_id == user.id).scalar() or 0
    )
    received_encouragement_count = (
        db.query(func.count(Encouragement.id))
        .filter(Encouragement.to_user_id == user.id).scalar() or 0
    )

    # 连续打卡天数
    from app.services.mood_service import get_current_streak
    streak = get_current_streak(db, user.id)

    data = {
        "id": user.id,
        "nickname": user.nickname,
        "avatar": user.avatar or "🙂",
        "is_admin": user.is_admin,
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "is_self": is_self,
        # 资源
        "total_energy": user.total_energy or 0,
        "leaves": user.leaves or 0,
        # 统计
        "stats": {
            "diary_count": diary_count,
            "public_diary_count": public_diary_count,
            "checkin_count": checkin_count,
            "listen_count": listen_count,
            "flower_count": flower_count,
            "garden_item_count": garden_item_count,
            "received_encouragement_count": received_encouragement_count,
            "streak": streak,
        },
    }
    return data


@router.get("")
def my_profile(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """我自己的主页。"""
    return _build_profile(db, user, is_self=True)


@router.patch("")
def update_my_profile(
    body: ProfileUpdateIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """更新我的头像 / 昵称。

    - 昵称改了要查重，不能跟别人重名。
    - 头像支持 emoji 或上传图片后的 URL 路径（最长 255 字符）。
    """
    changed = False
    if body.nickname is not None and body.nickname != user.nickname:
        existing = db.query(User).filter(User.nickname == body.nickname).first()
        if existing is not None:
            raise HTTPException(status_code=409, detail="这个名字已经有人用了，换一个吧")
        user.nickname = body.nickname
        changed = True
    if body.avatar is not None and body.avatar != user.avatar:
        user.avatar = body.avatar
        changed = True

    if changed:
        db.query(User).filter(User.id == user.id).update({
            "nickname": user.nickname,
            "avatar": user.avatar,
        })
        db.commit()
        db.refresh(user)

    return _build_profile(db, user, is_self=True)


# 允许的图片类型 → 扩展名
_AVATAR_EXT = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
}
_AVATAR_MAX = 2 * 1024 * 1024  # 2MB


@router.post("/avatar")
def upload_avatar(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """上传头像图片（支持拍摄 / 相册选择）。

    - 只接受 JPG / PNG / WebP / GIF，不超过 2MB。
    - 存储到 static/uploads/avatars/，avatar 字段存 URL 路径。
    """
    if file.content_type not in _AVATAR_EXT:
        raise HTTPException(status_code=400, detail="只支持 JPG/PNG/WebP/GIF 图片")
    data = file.file.read()
    if len(data) > _AVATAR_MAX:
        raise HTTPException(status_code=400, detail="图片不能超过 2MB")
    ext = _AVATAR_EXT[file.content_type]
    filename = f"{user.id}_{int(time.time())}{ext}"
    upload_dir = settings.static_dir / "uploads" / "avatars"
    upload_dir.mkdir(parents=True, exist_ok=True)
    (upload_dir / filename).write_bytes(data)
    avatar_url = f"/static/uploads/avatars/{filename}"
    db.query(User).filter(User.id == user.id).update({"avatar": avatar_url})
    db.commit()
    return {"avatar": avatar_url}


@router.get("/stats")
def my_stats(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """我的统计快照（轻量）。"""
    diary_count = (
        db.query(func.count(Diary.id)).filter(Diary.user_id == user.id).scalar() or 0
    )
    checkin_count = (
        db.query(func.count(MoodCheckin.id))
        .filter(MoodCheckin.user_id == user.id).scalar() or 0
    )
    listen_count = (
        db.query(func.count(EnergyRecord.id))
        .filter(
            EnergyRecord.user_id == user.id,
            EnergyRecord.source == "listen_music",
        ).scalar() or 0
    )
    flower_count = (
        db.query(func.count(UserFlower.id))
        .filter(UserFlower.user_id == user.id).scalar() or 0
    )
    from app.services.mood_service import get_current_streak
    streak = get_current_streak(db, user.id)
    return {
        "diary_count": diary_count,
        "checkin_count": checkin_count,
        "listen_count": listen_count,
        "flower_count": flower_count,
        "streak": streak,
        "total_energy": user.total_energy or 0,
        "leaves": user.leaves or 0,
    }


@router.get("/{user_id}")
def user_profile(
    user_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """查看他人主页（仅展示公开信息）。"""
    target = db.get(User, user_id)
    if target is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    is_self = (target.id == user.id)
    return _build_profile(db, target, is_self=is_self)
