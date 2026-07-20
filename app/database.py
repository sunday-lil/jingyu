"""数据库引擎与 Session 工厂。

使用 SQLAlchemy 2.0 同步 ORM。
"""

from __future__ import annotations

import logging
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session

from app.config import settings


logger = logging.getLogger(__name__)


# SQLite 需要 check_same_thread=False 以便在请求中复用连接
connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(
    settings.database_url,
    connect_args=connect_args,
    echo=False,
    future=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    future=True,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """所有 ORM 模型的基类。"""
    pass


def get_db() -> Session:
    """FastAPI 依赖：每次请求一个 Session，结束自动关闭。"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _migrate_legacy_columns() -> None:
    """轻量级字段迁移：给老库补上新加的列。

    项目刻意不引入 Alembic（见 HANDOFF §2），所以把『列是否存在』的检查写在这里。
    新加列时：
    1. 在 models/<file>.py 增加 ``Mapped[...]`` 字段
    2. 在本函数加一段 ``if "<col>" not in cols: ALTER TABLE ...``
    3. 重启 → 自动迁移
    """
    insp = inspect(engine)
    if not insp.has_table("users"):
        return  # 首次启动还没建表，create_all 会处理

    # users 表
    cols = {c["name"] for c in insp.get_columns("users")}
    with engine.begin() as conn:
        if "is_admin" not in cols:
            conn.execute(text(
                "ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT 0 NOT NULL"
            ))
            logger.info("[MIGRATE] users.is_admin 已添加")

    # energy_records 表（2026-07-20 加 music_id，用于同歌 24h 去重）
    if insp.has_table("energy_records"):
        e_cols = {c["name"] for c in insp.get_columns("energy_records")}
        with engine.begin() as conn:
            if "music_id" not in e_cols:
                conn.execute(text(
                    "ALTER TABLE energy_records ADD COLUMN music_id INTEGER"
                ))
                logger.info("[MIGRATE] energy_records.music_id 已添加")


def init_db() -> None:
    """建表 + 字段迁移。按依赖顺序 import 模型，确保 metadata 注册完整。"""
    from app import models  # noqa: F401  触发所有模型注册

    Base.metadata.create_all(bind=engine)
    _migrate_legacy_columns()
