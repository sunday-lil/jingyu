"""FastAPI 公共依赖。

- ``get_db``：数据库 session（已在 database.py 暴露）
- ``get_current_user_optional``：未登录返回 None
- ``get_current_user``：未登录 302 跳转到 /login
- ``set_session_cookie``：写入 cookie 辅助

⚠️ 日记解密密钥不存数据库，仅在用户登录后通过请求级 state 传递：
``request.state.diary_key_func`` 是一个 lambda(password) -> Fernet 密钥生成器，
模板渲染时不会触及，只在 API 路由里调用。
"""

from __future__ import annotations

from typing import Optional

from fastapi import Depends, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.database import get_db as _get_db
from app.models.user import User
from app.security import make_session_token, parse_session_token
from app.config import settings


def get_db() -> Session:
    """FastAPI 依赖：DB session。"""
    yield from _get_db()


def _read_session_uid(request: Request) -> Optional[int]:
    """从 cookie 读取并校验 session token。"""
    token = request.cookies.get(settings.session_cookie_name)
    if not token:
        return None
    return parse_session_token(token)


def get_current_user_optional(
    request: Request,
    db: Session = Depends(get_db),
) -> Optional[User]:
    """未登录返回 None，不抛异常。"""
    uid = _read_session_uid(request)
    if uid is None:
        return None
    user = db.get(User, uid)
    if user is None:
        return None
    # 把用户挂在 request.state，方便后续读取
    request.state.user = user
    return user


def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
) -> User:
    """必须登录。API 路由用 HTTPException；页面路由请用 ``get_current_user_or_redirect``。"""
    user = get_current_user_optional(request, db)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="请先登录",
        )
    return user


def get_current_user_or_redirect(
    request: Request,
    db: Session = Depends(get_db),
) -> Optional[User]:
    """页面路由用：未登录返回 302 跳到 /login。"""
    user = get_current_user_optional(request, db)
    if user is None:
        return None
    return user


def set_session_cookie(response: Response, user_id: int) -> None:
    """写入签名后的 session cookie。"""
    token = make_session_token(user_id)
    response.set_cookie(
        key=settings.session_cookie_name,
        value=token,
        max_age=settings.session_max_age_seconds,
        httponly=True,
        samesite="lax",
        secure=False,  # 部署到 HTTPS 时改为 True
        path="/",
    )


def clear_session_cookie(response: Response) -> None:
    """清除 session cookie。"""
    response.delete_cookie(key=settings.session_cookie_name, path="/")


def get_current_admin(
    request: Request,
    db: Session = Depends(get_db),
) -> User:
    """必须登录且 is_admin=True。用于 /admin/* 路由。

    - 未登录 → 401（API 路由）或 302 → /admin/login（页面路由，请用 ``get_current_admin_or_redirect``）
    - 已登录但非 admin → 403
    """
    user = get_current_user_optional(request, db)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="请先以管理员身份登录",
        )
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问：需要管理员权限",
        )
    return user


def get_current_admin_or_redirect(
    request: Request,
    db: Session = Depends(get_db),
) -> Optional[User]:
    """页面路由用：未登录 → 跳 /admin/login；已登录但非 admin → 跳首页。"""
    user = get_current_user_optional(request, db)
    if user is None:
        return None
    if not user.is_admin:
        return None
    return user
