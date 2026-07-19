"""页面路由：Vue 3 SPA 重构后的兼容层。

前台所有页面已由 Vue 3 SPA（frontend/）接管：
- 开发：访问 http://127.0.0.1:5173（Vite dev server，proxy /api 到 FastAPI :5000）
- 生产：访问 http://127.0.0.1:5000，FastAPI 挂载 static/dist 并 SPA fallback

本模块只保留旧 SSR 链接到新 SPA 路由的 302 重定向（兼容历史书签）。
新前端路由：/ /login /register /music /music/:yin /diary /diary/write
            /diary/pick /calendar /ai-chat /garden /shop
"""

from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import RedirectResponse


router = APIRouter(tags=["pages"])


# 旧 SSR 链接 → 新 SPA 路由
@router.get("/mood", include_in_schema=False)
def mood_legacy_redirect():
    """旧 /mood → 新 /calendar。"""
    return RedirectResponse("/calendar", status_code=302)


@router.get("/mood-calendar", include_in_schema=False)
def mood_calendar_legacy_redirect():
    """旧 /mood-calendar → 新 /calendar。"""
    return RedirectResponse("/calendar", status_code=302)


@router.get("/my-bottles", include_in_schema=False)
def my_bottles_legacy_redirect():
    """旧 /my-bottles → 新 /diary。"""
    return RedirectResponse("/diary", status_code=302)


@router.get("/pick", include_in_schema=False)
def pick_legacy_redirect():
    """旧 /pick → 新 /diary/pick。"""
    return RedirectResponse("/diary/pick", status_code=302)
