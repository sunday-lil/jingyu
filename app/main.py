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
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import SessionLocal, init_db
from app.routers import auth, music, diary, mood, energy, garden, pages, admin, admin_pages
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
    # 秘密后台：API + 页面
    app.include_router(admin.router)
    app.include_router(admin_pages.router)

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
            from fastapi.responses import HTMLResponse
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
