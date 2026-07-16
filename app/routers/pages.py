"""页面路由：所有 SSR HTML 页面。

每个页面都返回 TemplateResponse。current_user 通过 ``request.state.user`` 传递，
未登录时为 None；模板自行判断显示登录/注册按钮还是用户菜单。
"""

from __future__ import annotations

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.deps import get_current_user_optional
from app.models.user import User
from app.models.music import Music
from app.models.diary import Diary
from app.models.mood import MoodCheckin
from app.models.garden import GardenItem, ShopItem
from app.models.energy import EnergyRecord
from app.utils.constants import YIN_INFO, MOOD_INFO


router = APIRouter(tags=["pages"])
templates = Jinja2Templates(directory=str(settings.templates_dir))


# ─────────────────────────────────────────────────────────────
# 首页
# ─────────────────────────────────────────────────────────────

@router.get("/", response_class=HTMLResponse)
def index(
    request: Request,
    user: Optional[User] = Depends(get_current_user_optional),
):
    # 今日手帐条已移除（甲方 2026-07-15 要求合并进情绪日历），首页不再查 today_checkin
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "current_user": user,
            "yin_info": YIN_INFO,
            "mood_info": MOOD_INFO,
        },
    )


# ─────────────────────────────────────────────────────────────
# 鉴权页
# ─────────────────────────────────────────────────────────────

@router.get("/login", response_class=HTMLResponse)
def login_page(
    request: Request,
    user: Optional[User] = Depends(get_current_user_optional),
):
    if user is not None:
        return RedirectResponse("/", status_code=302)
    return templates.TemplateResponse(
        request,
        "login.html",
        {"current_user": None},
    )


@router.get("/register", response_class=HTMLResponse)
def register_page(
    request: Request,
    user: Optional[User] = Depends(get_current_user_optional),
):
    if user is not None:
        return RedirectResponse("/", status_code=302)
    return templates.TemplateResponse(
        request,
        "register.html",
        {"current_user": None},
    )


# ─────────────────────────────────────────────────────────────
# 古琴五音
# ─────────────────────────────────────────────────────────────

@router.get("/music/{yin_type}", response_class=HTMLResponse)
def music_list(
    yin_type: str,
    request: Request,
    user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    if yin_type not in YIN_INFO:
        return RedirectResponse("/", status_code=302)
    musics = (
        db.query(Music)
        .filter(Music.yin_type == yin_type)
        .order_by(Music.id.asc())
        .all()
    )
    return templates.TemplateResponse(
        request,
        "music_list.html",
        {
            "current_user": user,
            "yin_type": yin_type,
            "yin_info": YIN_INFO[yin_type],
            "musics": [
                {
                    "id": m.id, "title": m.title, "audio_url": m.audio_url,
                    "cover_image": m.cover_image, "yin_type": m.yin_type,
                    "duration": m.duration, "tags": m.tag_list(),
                }
                for m in musics
            ],
        },
    )


# ─────────────────────────────────────────────────────────────
# 漂流瓶
# ─────────────────────────────────────────────────────────────

@router.get("/diary", response_class=HTMLResponse)
def diary_write(
    request: Request,
    user: Optional[User] = Depends(get_current_user_optional),
):
    if user is None:
        return RedirectResponse("/login?next=/diary", status_code=302)
    return templates.TemplateResponse(
        request,
        "diary_write.html",
        {
            "current_user": user,
            "mood_info": MOOD_INFO,
            "encryption_salt": user.encryption_salt,
        },
    )


@router.get("/my-bottles", response_class=HTMLResponse)
def my_bottles(
    request: Request,
    user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    if user is None:
        return RedirectResponse("/login?next=/my-bottles", status_code=302)
    diaries = (
        db.query(Diary)
        .filter(Diary.user_id == user.id)
        .order_by(Diary.created_at.desc())
        .all()
    )
    return templates.TemplateResponse(
        request,
        "my_bottles.html",
        {
            "current_user": user,
            "diaries": [
                {
                    "id": d.id,
                    "content_encrypted": d.content_encrypted,
                    "mood_type": d.mood_type,
                    "is_public": d.is_public,
                    "created_at": d.created_at,
                }
                for d in diaries
            ],
            "mood_info": MOOD_INFO,
            "encryption_salt": user.encryption_salt,
        },
    )


@router.get("/my-bottles/{diary_id}", response_class=HTMLResponse)
def diary_detail(
    diary_id: int,
    request: Request,
    user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    if user is None:
        return RedirectResponse("/login", status_code=302)
    diary = db.get(Diary, diary_id)
    if diary is None or diary.user_id != user.id:
        return RedirectResponse("/my-bottles", status_code=302)
    from app.models.encouragement import Encouragement
    encs = (
        db.query(Encouragement)
        .filter(Encouragement.diary_id == diary.id)
        .order_by(Encouragement.created_at.asc())
        .all()
    )
    return templates.TemplateResponse(
        request,
        "diary_detail.html",
        {
            "current_user": user,
            "diary": {
                "id": diary.id,
                "content_encrypted": diary.content_encrypted,
                "mood_type": diary.mood_type,
                "is_public": diary.is_public,
                "created_at": diary.created_at,
            },
            "encouragements": [
                {"id": e.id, "content": e.content, "created_at": e.created_at}
                for e in encs
            ],
            "mood_info": MOOD_INFO,
            "encryption_salt": user.encryption_salt,
        },
    )


@router.get("/pick", response_class=HTMLResponse)
def pick_page(
    request: Request,
    user: Optional[User] = Depends(get_current_user_optional),
):
    if user is None:
        return RedirectResponse("/login?next=/pick", status_code=302)
    return templates.TemplateResponse(
        request,
        "pick_bottle.html",
        {
            "current_user": user,
            "mood_info": MOOD_INFO,
        },
    )


# ─────────────────────────────────────────────────────────────
# 心情手帐
# ─────────────────────────────────────────────────────────────

@router.get("/mood", response_class=HTMLResponse)
def mood_checkin_redirect():
    """今日手帐已合并进情绪日历（甲方 2026-07-15 要求「每日手帐与日历合一」）。

    旧链接 /mood（含 tabbar、书签、历史入口）302 重定向到 /mood-calendar，
    未登录由 /mood-calendar 路由自行跳 /login。
    """
    return RedirectResponse("/mood-calendar", status_code=302)


@router.get("/mood-calendar", response_class=HTMLResponse)
def mood_calendar(
    request: Request,
    user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    if user is None:
        return RedirectResponse("/login?next=/mood-calendar", status_code=302)
    today = date.today()
    today_record = (
        db.query(MoodCheckin)
        .filter(MoodCheckin.user_id == user.id, MoodCheckin.check_date == today)
        .first()
    )
    return templates.TemplateResponse(
        request,
        "mood_calendar.html",
        {
            "current_user": user,
            "mood_info": MOOD_INFO,
            "today": today,
            "today_record": today_record,
        },
    )


# ─────────────────────────────────────────────────────────────
# 精神花园 + 商店
# ─────────────────────────────────────────────────────────────

@router.get("/garden", response_class=HTMLResponse)
def garden(
    request: Request,
    user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    if user is None:
        return RedirectResponse("/login?next=/garden", status_code=302)
    items = (
        db.query(GardenItem)
        .filter(GardenItem.user_id == user.id)
        .order_by(GardenItem.obtained_at.desc())
        .all()
    )
    return templates.TemplateResponse(
        request,
        "garden.html",
        {
            "current_user": user,
            "items": [gi.to_dict() for gi in items],
        },
    )


@router.get("/shop", response_class=HTMLResponse)
def shop(
    request: Request,
    user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    items = db.query(ShopItem).order_by(ShopItem.item_type, ShopItem.cost).all()
    # 按 item_type 分组（避免模板里用 set 副作用）
    by_type: dict[str, list[dict]] = {}
    for it in items:
        by_type.setdefault(it.item_type, []).append(it.to_dict())
    return templates.TemplateResponse(
        request,
        "shop.html",
        {
            "current_user": user,
            "items": [i.to_dict() for i in items],
            "items_by_type": by_type,
        },
    )
