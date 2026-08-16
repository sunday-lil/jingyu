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
            # v2.4.4：旧版加密日记 content 为空（content_encrypted 是假占位符），
            # 填入提示文本让用户知道内容已无法读取（幂等：content 填充后不再触发）
            conn.execute(text(
                "UPDATE diaries SET content = '（这段日记来自旧版本，内容已无法读取）' "
                "WHERE (content IS NULL OR content = '') "
                "AND content_encrypted IS NOT NULL AND content_encrypted != ''"
            ))

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
            # v2.4.6：音频占位 mp3 换成 Karplus-Strong 合成的真实 wav
            # （幂等：audio_url 已是 .wav 的行不受影响）
            result = conn.execute(text(
                "UPDATE musics SET audio_url = REPLACE(audio_url, '.mp3', '.wav') "
                "WHERE audio_url LIKE '%.mp3'"
            ))
            if result.rowcount:
                logger.info(
                    "[MIGRATE] musics.audio_url 已切换 .mp3 → .wav（%d 行，v2.4.6 真实音频）",
                    result.rowcount,
                )

    # mood_checkins 表
    # v2.4：移除 user_id+check_date 唯一约束（支持一天多条心情）
    # v2.4.4：修复 v2.4 迁移用 CREATE TABLE AS SELECT 导致丢失 PRIMARY KEY 的问题
    #         （SQLite 不会自动加 INTEGER PRIMARY KEY，导致 db.flush() 报 NULL identity key）
    if insp.has_table("mood_checkins"):
        pk = insp.get_pk_constraint("mood_checkins")
        pk_cols = pk.get("constrained_columns") if pk else None
        existing_uqs = {
            tuple(c["column_names"])
            for c in insp.get_unique_constraints("mood_checkins")
        }
        need_rebuild = (
            not pk_cols                      # 没有主键（v2.4 迁移遗留 bug）
            or ("user_id", "check_date") in existing_uqs  # 还有旧唯一约束
        )
        if need_rebuild:
            with engine.begin() as conn:
                # 1. 备份旧表
                conn.execute(text("DROP TABLE IF EXISTS mood_checkins_broken"))
                conn.execute(text("ALTER TABLE mood_checkins RENAME TO mood_checkins_broken"))
                # 2. 删除跟随旧表的索引（CREATE TABLE 时不带主键，但旧迁移可能手动建过索引）
                conn.execute(text("DROP INDEX IF EXISTS ix_mood_checkins_user_id"))
                conn.execute(text("DROP INDEX IF EXISTS ix_mood_checkins_check_date"))
            # 3. 用 ORM 模型创建正确的新表（id INTEGER PRIMARY KEY AUTOINCREMENT + FK + 索引）
            from app.models.mood import MoodCheckin
            MoodCheckin.__table__.create(engine, checkfirst=True)
            # 4. 复制数据（不复制旧 id，让新表自增）
            with engine.begin() as conn:
                conn.execute(text(
                    "INSERT INTO mood_checkins (user_id, check_date, mood_emoji, note, created_at) "
                    "SELECT user_id, check_date, mood_emoji, note, created_at "
                    "FROM mood_checkins_broken"
                ))
                conn.execute(text("DROP TABLE mood_checkins_broken"))
            logger.info("[MIGRATE] mood_checkins 表已重建（修复缺失主键 / 旧唯一约束，v2.4.4）")


def init_db() -> None:
    """建表 + 字段迁移。按依赖顺序 import 模型，确保 metadata 注册完整。"""
    from app import models  # noqa: F401  触发所有模型注册

    Base.metadata.create_all(bind=engine)
    _migrate_legacy_columns()
