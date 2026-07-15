"""秘密后台页面路由：6 个 SSR 页面。

URL 风格：全部挂在 ``/admin`` 下（可在 .env 用 QI_ADMIN_PATH_PREFIX 改前缀）。
刻意不放任何链接到这些页面，靠 URL 入口（书签/记忆）。
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.deps import get_current_admin_or_redirect
from app.models.user import User
from app.models.diary import Diary
from app.models.mood import MoodCheckin
from app.models.energy import EnergyRecord
from app.models.garden import GardenItem
from sqlalchemy import func as sa_func


router = APIRouter(prefix=settings.admin_path_prefix, tags=["admin-pages"])
# 模板根目录是 templates/，admin 页面位于 templates/admin/ 下，继承 admin/_base.html
admin_templates = Jinja2Templates(directory=str(settings.templates_dir))


# ─────────────────────────────────────────────────────────────
# 登录
# ─────────────────────────────────────────────────────────────

@router.get("/login", response_class=HTMLResponse)
def admin_login_page(
    request: Request,
    user: Optional[User] = Depends(get_current_admin_or_redirect),
):
    """登录页（独立设计）。已登录且 is_admin 则直接跳后台首页。"""
    if user is not None:
        return RedirectResponse(f"{settings.admin_path_prefix}/", status_code=302)
    return admin_templates.TemplateResponse(
        request,
        "admin/login.html",
        {
            "current_user": None,
            "admin_path_prefix": settings.admin_path_prefix,
        },
    )


# ─────────────────────────────────────────────────────────────
# 仪表盘
# ─────────────────────────────────────────────────────────────

@router.get("/", response_class=HTMLResponse)
def admin_dashboard(
    request: Request,
    user: Optional[User] = Depends(get_current_admin_or_redirect),
    db: Session = Depends(get_db),
):
    if user is None:
        return RedirectResponse(f"{settings.admin_path_prefix}/login", status_code=302)
    stats = {
        "total_users": db.query(User).count(),
        "total_admins": db.query(User).filter(User.is_admin == True).count(),  # noqa: E712
        "total_diaries": db.query(Diary).count(),
        "total_public_diaries": db.query(Diary).filter(Diary.is_public == True).count(),  # noqa: E712
        "total_mood_checkins": db.query(MoodCheckin).count(),
        "total_energy_records": db.query(EnergyRecord).count(),
        "total_garden_items": db.query(GardenItem).count(),
    }
    return admin_templates.TemplateResponse(
        request,
        "admin/dashboard.html",
        {
            "current_user": user,
            "admin_path_prefix": settings.admin_path_prefix,
            "stats": stats,
        },
    )


# ─────────────────────────────────────────────────────────────
# 用户列表
# ─────────────────────────────────────────────────────────────

@router.get("/users", response_class=HTMLResponse)
def admin_users(
    request: Request,
    user: Optional[User] = Depends(get_current_admin_or_redirect),
    db: Session = Depends(get_db),
):
    if user is None:
        return RedirectResponse(f"{settings.admin_path_prefix}/login", status_code=302)
    users = db.query(User).order_by(User.id.desc()).limit(50).all()
    items = []
    for u in users:
        diary_count = db.query(sa_func.count(Diary.id)).filter(Diary.user_id == u.id).scalar() or 0
        public_count = db.query(sa_func.count(Diary.id)).filter(
            Diary.user_id == u.id, Diary.is_public == True  # noqa: E712
        ).scalar() or 0
        mood_count = db.query(sa_func.count(MoodCheckin.id)).filter(MoodCheckin.user_id == u.id).scalar() or 0
        items.append({
            "id": u.id,
            "nickname": u.nickname,
            "total_energy": u.total_energy,
            "is_admin": u.is_admin,
            "created_at": u.created_at,
            "diary_count": diary_count,
            "public_diary_count": public_count,
            "mood_count": mood_count,
        })
    return admin_templates.TemplateResponse(
        request,
        "admin/users.html",
        {
            "current_user": user,
            "admin_path_prefix": settings.admin_path_prefix,
            "items": items,
            "total": len(items),
        },
    )


# ─────────────────────────────────────────────────────────────
# 用户详情
# ─────────────────────────────────────────────────────────────

@router.get("/users/{user_id}", response_class=HTMLResponse)
def admin_user_detail(
    user_id: int,
    request: Request,
    user: Optional[User] = Depends(get_current_admin_or_redirect),
    db: Session = Depends(get_db),
):
    if user is None:
        return RedirectResponse(f"{settings.admin_path_prefix}/login", status_code=302)
    target = db.get(User, user_id)
    if target is None:
        return RedirectResponse(f"{settings.admin_path_prefix}/users", status_code=302)

    diary_count = db.query(sa_func.count(Diary.id)).filter(Diary.user_id == target.id).scalar() or 0
    public_count = db.query(sa_func.count(Diary.id)).filter(
        Diary.user_id == target.id, Diary.is_public == True  # noqa: E712
    ).scalar() or 0
    mood_count = db.query(sa_func.count(MoodCheckin.id)).filter(MoodCheckin.user_id == target.id).scalar() or 0
    energy_in = db.query(sa_func.coalesce(sa_func.sum(EnergyRecord.amount), 0)).filter(
        EnergyRecord.user_id == target.id, EnergyRecord.amount > 0
    ).scalar() or 0
    energy_out = db.query(sa_func.coalesce(sa_func.sum(EnergyRecord.amount), 0)).filter(
        EnergyRecord.user_id == target.id, EnergyRecord.amount < 0
    ).scalar() or 0
    garden_count = db.query(sa_func.count(GardenItem.id)).filter(GardenItem.user_id == target.id).scalar() or 0

    recent_diaries = (
        db.query(Diary)
        .filter(Diary.user_id == target.id)
        .order_by(Diary.created_at.desc())
        .limit(10).all()
    )
    recent_moods = (
        db.query(MoodCheckin)
        .filter(MoodCheckin.user_id == target.id)
        .order_by(MoodCheckin.check_date.desc())
        .limit(10).all()
    )
    recent_energy = (
        db.query(EnergyRecord)
        .filter(EnergyRecord.user_id == target.id)
        .order_by(EnergyRecord.created_at.desc())
        .limit(10).all()
    )

    ph = target.password_hash or ""
    ph_preview = f"{ph[:4]}...{ph[-4:]}" if len(ph) > 12 else "(空)"

    return admin_templates.TemplateResponse(
        request,
        "admin/user_detail.html",
        {
            "current_user": user,
            "admin_path_prefix": settings.admin_path_prefix,
            "target": target,
            "stats": {
                "diary_count": diary_count,
                "public_diary_count": public_count,
                "mood_count": mood_count,
                "energy_in": energy_in,
                "energy_out": abs(energy_out),
                "garden_count": garden_count,
            },
            "ph_preview": ph_preview,
            "recent_diaries": [
                {
                    "id": d.id, "created_at": d.created_at,
                    "is_public": d.is_public, "mood_type": d.mood_type,
                }
                for d in recent_diaries
            ],
            "recent_moods": [
                {
                    "id": m.id, "check_date": m.check_date,
                    "mood_emoji": m.mood_emoji, "note": m.note,
                }
                for m in recent_moods
            ],
            "recent_energy": [
                {
                    "id": e.id, "created_at": e.created_at,
                    "amount": e.amount, "source": e.source, "note": e.note,
                }
                for e in recent_energy
            ],
        },
    )


# ─────────────────────────────────────────────────────────────
# 日志
# ─────────────────────────────────────────────────────────────

@router.get("/logs", response_class=HTMLResponse)
def admin_logs(
    request: Request,
    user: Optional[User] = Depends(get_current_admin_or_redirect),
):
    if user is None:
        return RedirectResponse(f"{settings.admin_path_prefix}/login", status_code=302)
    return admin_templates.TemplateResponse(
        request,
        "admin/logs.html",
        {
            "current_user": user,
            "admin_path_prefix": settings.admin_path_prefix,
            "log_path": str(settings.log_dir / "healing.log"),
        },
    )


# ─────────────────────────────────────────────────────────────
# 系统
# ─────────────────────────────────────────────────────────────

@router.get("/system", response_class=HTMLResponse)
def admin_system(
    request: Request,
    user: Optional[User] = Depends(get_current_admin_or_redirect),
):
    if user is None:
        return RedirectResponse(f"{settings.admin_path_prefix}/login", status_code=302)
    return admin_templates.TemplateResponse(
        request,
        "admin/system.html",
        {
            "current_user": user,
            "admin_path_prefix": settings.admin_path_prefix,
        },
    )
