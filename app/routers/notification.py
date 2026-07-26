"""站内通知 API。

v2.3 新增：漂流瓶评论返回发布者后的消息提醒机制。

端点：
- GET  /api/notifications          通知列表（最近 50 条）
- GET  /api/notifications/unread   未读数量
- POST /api/notifications/{id}/read  标记单条已读
- POST /api/notifications/read-all   全部标记已读
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.models.notification import Notification


router = APIRouter(prefix="/api/notifications", tags=["notification"])


@router.get("")
def list_notifications(
    limit: int = 50,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """我的通知列表（最近 limit 条，含已读未读）。"""
    rows = (
        db.query(Notification)
        .filter(Notification.user_id == user.id)
        .order_by(Notification.created_at.desc())
        .limit(limit)
        .all()
    )
    return {
        "count": len(rows),
        "items": [n.to_dict() for n in rows],
    }


@router.get("/unread")
def unread_count(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """未读通知数量。"""
    count = (
        db.query(func.count(Notification.id))
        .filter(Notification.user_id == user.id, Notification.is_read == False)  # noqa: E712
        .scalar()
    )
    return {"unread": int(count or 0)}


@router.post("/{notif_id}/read")
def mark_read(
    notif_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """标记单条通知为已读。"""
    n = db.get(Notification, notif_id)
    if n is None or n.user_id != user.id:
        return {"success": False, "error": "通知不存在"}
    if not n.is_read:
        n.is_read = True
        db.commit()
    return {"success": True}


@router.post("/read-all")
def mark_all_read(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """全部标记为已读。"""
    rows = (
        db.query(Notification)
        .filter(Notification.user_id == user.id, Notification.is_read == False)  # noqa: E712
        .all()
    )
    for n in rows:
        n.is_read = True
    db.commit()
    return {"success": True, "marked": len(rows)}
