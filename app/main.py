"""FastAPI 应用主入口。

启动流程：
1. create_app() 创建实例 + 挂载中间件 + 注册路由
2. 启动事件：init_db() 建表 + run_seed() 种子数据
"""

from __future__ import annotations

import logging
import sys
from contextlib import asynccontextmanager

# 必须在任何 logger 之前执行：Windows cmd/PowerShell 默认 GBK，
# 子进程（uvicorn worker）会沿用此编码，导致 emoji/中文日志乱码。
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import SessionLocal, init_db
from app.routers import auth, music, diary, mood, energy, garden, pages, admin, admin_pages, ai
from app.seed import run_seed


# 日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
# 强制所有 handler 用 utf-8 写（关键：StreamHandler 默认用 sys.stdout.encoding，
# 但 uvicorn 自己的 handler 可能初始化更早，这里再绑一次兜底）
for _h in logging.getLogger().handlers:
    if hasattr(_h, "stream") and hasattr(_h.stream, "reconfigure"):
        try:
            _h.stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
logger = logging.getLogger("qi")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """启动 / 关闭事件。"""
    # 启动
    logger.info("[HEAL] 静屿 — 正在初始化 ...")
    init_db()
    db = SessionLocal()
    try:
        run_seed(db)
    finally:
        db.close()
    logger.info("[OK] 应用已就绪 -> http://%s:%d", settings.host, settings.port)
    yield
    # 关闭
    logger.info("[BYE] 静屿 — 已熄灭灯火")


def create_app() -> FastAPI:
    app = FastAPI(
        title="静屿 — 治愈系身心疗愈平台",
        description="古琴五音 · 漂流瓶日记 · 心情手帐 · 精神花园",
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url=None,
    )

    # 静态资源
    app.mount(
        "/static",
        StaticFiles(directory=str(settings.static_dir)),
        name="static",
    )

    # 路由
    app.include_router(auth.router)
    app.include_router(music.router)
    app.include_router(diary.router)
    app.include_router(mood.router)
    app.include_router(energy.router)
    app.include_router(garden.router)
    app.include_router(pages.router)
    # AI（NVIDIA NIM 接入：树洞对话 / 漂流瓶鼓励语 / 情绪日历治愈语 / 音乐推荐）
    app.include_router(ai.router)
    # 秘密后台：API + 页面
    app.include_router(admin.router)
    app.include_router(admin_pages.router)

    # ─────────────────────────────────────────────────────────────
    # Vue 3 SPA fallback
    # 前台已由 Vue 3 SPA 接管。
    # - 生产态（dist 已构建）：返回 static/dist/index.html + 静态资源
    # - 开发态（dist 未构建）：返回提示页（开发时用户访问 Vite :5000，
    #   FastAPI 在开发模式监听 :5001，由 start.py 自动切换）
    # 排除：/api/* /static/* /admin* /docs /openapi.json
    # ─────────────────────────────────────────────────────────────
    spa_index_path = settings.static_dir / "dist" / "index.html"
    spa_dist_dir = settings.static_dir / "dist"

    # 静态资源扩展名 → MIME 映射（生产态从 dist 读取时用）
    EXT_TO_MIME = {
        ".js": "application/javascript; charset=utf-8",
        ".mjs": "application/javascript; charset=utf-8",
        ".css": "text/css; charset=utf-8",
        ".html": "text/html; charset=utf-8",
        ".json": "application/json; charset=utf-8",
        ".svg": "image/svg+xml",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".ico": "image/x-icon",
        ".woff": "font/woff",
        ".woff2": "font/woff2",
        ".ttf": "font/ttf",
        ".map": "application/json; charset=utf-8",
    }

    @app.get("/{full_path:path}", include_in_schema=False)
    async def spa_fallback(request: Request, full_path: str):
        # 排除 API / 静态 / 后台 / 文档
        admin_prefix = settings.admin_path_prefix.lstrip("/")
        if (
            full_path.startswith("api/")
            or full_path.startswith("static/")
            or full_path.startswith(admin_prefix + "/")
            or full_path == admin_prefix
            or full_path.startswith("docs")
            or full_path == "openapi.json"
            or full_path.startswith("redoc")
        ):
            return JSONResponse({"error": "Not Found"}, status_code=404)

        # ─── 生产态：dist 已构建 ───
        if spa_index_path.exists():
            # 静态资源请求：尝试从 dist 读取对应文件
            if full_path:
                candidate = spa_dist_dir / full_path
                try:
                    if candidate.is_file() and ".." not in full_path:
                        ext = candidate.suffix.lower()
                        media_type = EXT_TO_MIME.get(ext, "application/octet-stream")
                        return Response(
                            candidate.read_bytes(),
                            media_type=media_type,
                        )
                except (ValueError, OSError):
                    pass  # 路径异常，fallback 到 index.html
            # SPA 路由：返回 index.html
            return HTMLResponse(spa_index_path.read_text(encoding="utf-8"))

        # ─── 开发态：dist 未构建，返回提示页 ───
        # 开发模式用户应访问 Vite dev server :5000（FastAPI 在 :5001）
        return HTMLResponse(
            "<!DOCTYPE html><html lang='zh-CN'><head><meta charset='UTF-8'>"
            "<title>静屿 · 前端未构建</title></head>"
            "<body style='font-family:PingFang SC,Microsoft YaHei,sans-serif;"
            "background:#F9F6F0;color:#4A4438;text-align:center;padding:80px 24px;'>"
            "<h1 style='font-weight:500;letter-spacing:0.1em;'>🌿 前端尚未构建</h1>"
            "<p style='color:#8B7B5E;margin-top:12px;line-height:1.8;'>"
            "开发模式：访问 Vite dev server（通常 <code>http://127.0.0.1:5000</code>）<br>"
            "或一键启动：<code>python start.py</code>（自动起 Vite + FastAPI）"
            "</p>"
            "<p style='color:#8B7B5E;margin-top:8px;font-size:13px;'>"
            "生产模式：先 <code>cd frontend && npm run build</code> 再访问本页</p>"
            "</body></html>",
            status_code=200,
        )

    # 全局异常
    @app.exception_handler(RequestValidationError)
    async def validation_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=422,
            content={"error": "参数有误", "details": exc.errors()},
        )

    @app.exception_handler(Exception)
    async def general_handler(request: Request, exc: Exception):
        logger.exception("未捕获异常: %s", exc)
        # 页面请求 → 友好错误页
        accept = request.headers.get("accept", "")
        if "text/html" in accept:
            return HTMLResponse(
                "<h1>海风停了一下，请稍后再试</h1><p>静屿正在深呼吸…</p>",
                status_code=500,
            )
        return JSONResponse(
            status_code=500,
            content={"error": "海风停了一下，请稍后再试"},
        )

    return app


app = create_app()
