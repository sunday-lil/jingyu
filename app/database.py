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
        if "leaves" not in cols:
            conn.execute(text(
                "ALTER TABLE users ADD COLUMN leaves INTEGER DEFAULT 0 NOT NULL"
            ))
            logger.info("[MIGRATE] users.leaves 已添加（落叶资源，v2.3）")
        if "avatar" not in cols:
            conn.execute(text(
                "ALTER TABLE users ADD COLUMN avatar VARCHAR(16) DEFAULT '🙂' NOT NULL"
            ))
            logger.info("[MIGRATE] users.avatar 已添加（v2.4，用户头像 emoji）")

    # energy_records 表（2026-07-20 加 music_id，用于同歌 24h 去重）
    if insp.has_table("energy_records"):
        e_cols = {c["name"] for c in insp.get_columns("energy_records")}
        with engine.begin() as conn:
            if "music_id" not in e_cols:
                conn.execute(text(
                    "ALTER TABLE energy_records ADD COLUMN music_id INTEGER"
                ))
                logger.info("[MIGRATE] energy_records.music_id 已添加")

    # diaries 表（v2.3：改明文 + 发布选项）
    if insp.has_table("diaries"):
        d_cols = {c["name"] for c in insp.get_columns("diaries")}
        with engine.begin() as conn:
            if "content" not in d_cols:
                conn.execute(text(
                    "ALTER TABLE diaries ADD COLUMN content TEXT NOT NULL DEFAULT ''"
                ))
                logger.info("[MIGRATE] diaries.content 已添加（明文，v2.3）")
            if "send_to_ai_hole" not in d_cols:
                conn.execute(text(
                    "ALTER TABLE diaries ADD COLUMN send_to_ai_hole BOOLEAN DEFAULT 0 NOT NULL"
                ))
                logger.info("[MIGRATE] diaries.send_to_ai_hole 已添加（v2.3）")
            # content_encrypted 老库是 NOT NULL，放宽为 NULL 兼容新数据不写密文
            if "content_encrypted" in d_cols:
                # SQLite 不支持 ALTER COLUMN，只能靠新表；这里仅记录，新代码不再写该列
                pass

    # shop_items 表（v2.3：加 cost_currency 区分露水/落叶）
    if insp.has_table("shop_items"):
        s_cols = {c["name"] for c in insp.get_columns("shop_items")}
        with engine.begin() as conn:
            if "cost_currency" not in s_cols:
                conn.execute(text(
                    "ALTER TABLE shop_items ADD COLUMN cost_currency VARCHAR(20) DEFAULT 'dew' NOT NULL"
                ))
                logger.info("[MIGRATE] shop_items.cost_currency 已添加（v2.3）")

    # musics 表（v2.3：加 category 区分五音古曲 / 古琴弹西洋）
    if insp.has_table("musics"):
        m_cols = {c["name"] for c in insp.get_columns("musics")}
        with engine.begin() as conn:
            if "category" not in m_cols:
                conn.execute(text(
                    "ALTER TABLE musics ADD COLUMN category VARCHAR(20) DEFAULT 'classic' NOT NULL"
                ))
                logger.info("[MIGRATE] musics.category 已添加（v2.3）")

    # mood_checkins 表（v2.4：移除 user_id+check_date 唯一约束，支持一天多条心情记录）
    if insp.has_table("mood_checkins"):
        existing_uqs = {
            tuple(c["column_names"])
            for c in insp.get_unique_constraints("mood_checkins")
        }
        if ("user_id", "check_date") in existing_uqs:
            with engine.begin() as conn:
                # SQLite 重建表方式删除唯一约束
                conn.execute(text(
                    "CREATE TABLE mood_checkins_new AS SELECT * FROM mood_checkins"
                ))
                conn.execute(text("DROP TABLE mood_checkins"))
                conn.execute(text(
                    "ALTER TABLE mood_checkins_new RENAME TO mood_checkins"
                ))
                conn.execute(text(
                    "CREATE INDEX IF NOT EXISTS ix_mood_checkins_user_id "
                    "ON mood_checkins (user_id)"
                ))
                conn.execute(text(
                    "CREATE INDEX IF NOT EXISTS ix_mood_checkins_check_date "
                    "ON mood_checkins (check_date)"
                ))
            logger.info("[MIGRATE] mood_checkins 唯一约束已移除（v2.4，支持一天多条心情）")


def init_db() -> None:
    """建表 + 字段迁移。按依赖顺序 import 模型，确保 metadata 注册完整。"""
    from app import models  # noqa: F401  触发所有模型注册

    Base.metadata.create_all(bind=engine)
    _migrate_legacy_columns()
