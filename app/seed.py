"""启动时种子数据。

- 5 音各 2-3 首古琴曲目（真实曲名 + 占位音频）。
- 商店默认物品（与 constants.DEFAULT_SHOP_ITEMS 对齐）。
- 启动时如果表为空则插入；非空则跳过（保证可重复启动）。
- 首次启动时如果没有任何 is_admin 用户，按 settings 创建首个管理员。
"""

from __future__ import annotations

import logging
import secrets
import string
from pathlib import Path

from sqlalchemy.orm import Session

from app.config import settings
from app.models.music import Music
from app.models.garden import ShopItem
from app.models.user import User
from app.utils.constants import DEFAULT_SHOP_ITEMS, YinType
from app.utils.crypto import generate_salt, hash_password


logger = logging.getLogger(__name__)


# 真实古琴曲名（占位音频）
SEED_MUSIC: list[dict] = [
    # 宫音（土）
    {"title": "梅花三弄",  "yin_type": "gong",   "duration": 240, "tags": "健脾,古典"},
    {"title": "阳关三叠",  "yin_type": "gong",   "duration": 200, "tags": "助消化,送别"},
    {"title": "平沙落雁",  "yin_type": "gong",   "duration": 320, "tags": "健脾,秋意"},

    # 商音（金）
    {"title": "潇湘水云",  "yin_type": "shang",  "duration": 280, "tags": "润肺,山水"},
    {"title": "长门怨",    "yin_type": "shang",  "duration": 220, "tags": "舒缓,古意"},
    {"title": "佩兰",      "yin_type": "shang",  "duration": 180, "tags": "润肺,雅正"},

    # 角音（木）
    {"title": "流水",      "yin_type": "jue",    "duration": 420, "tags": "疏肝,解郁,抗焦虑"},
    {"title": "渔樵问答",  "yin_type": "jue",    "duration": 260, "tags": "疏肝,问答"},
    {"title": "鸥鹭忘机",  "yin_type": "jue",    "duration": 200, "tags": "解郁,自在"},

    # 徵音（火）
    {"title": "醉渔唱晚",  "yin_type": "zhi",    "duration": 240, "tags": "养心,渔歌"},
    {"title": "山居吟",    "yin_type": "zhi",    "duration": 200, "tags": "安神,山居"},
    {"title": "神人畅",    "yin_type": "zhi",    "duration": 180, "tags": "养心,古意"},

    # 羽音（水）
    {"title": "广陵散",    "yin_type": "yu",     "duration": 480, "tags": "宁心,助眠,古曲"},
    {"title": "大胡笳",    "yin_type": "yu",     "duration": 360, "tags": "助眠,胡笳"},
    {"title": "幽兰",      "yin_type": "yu",     "duration": 220, "tags": "宁心,兰香"},
    {"title": "普庵咒",    "yin_type": "yu",     "duration": 260, "tags": "助眠,梵音"},
]


def _ensure_placeholder_audio():
    """确保每个音有一个占位 mp3 文件。"""
    settings.audio_dir.mkdir(parents=True, exist_ok=True)
    for yin in YinType:
        path = settings.audio_dir / f"{yin.value}.mp3"
        if not path.exists():
            # 写一个最小的 MP3 文件头（ID3v2 + MPEG sync），浏览器可识别为音频但很短
            # 1 帧静音 MPEG-1 Layer III 32kbps 44.1kHz = 104 字节
            # 加上 ID3v1 尾部 128 字节
            silence_frame = bytes([
                0xFF, 0xFB, 0x10, 0x64,  # MPEG1 Layer3 32kbps 44.1kHz
                *([0x00] * 100),
            ])
            # 写一个 ID3v2 最小头 + 多个静音帧 + ID3v1
            id3v2_header = b"ID3\x03\x00\x00\x00\x00\x00\x00"
            id3v1_tag = b"TAG" + b"\x00" * 125
            data = id3v2_header + (silence_frame * 50) + id3v1_tag
            path.write_bytes(data)


def seed_music(db: Session) -> int:
    """插入曲目（仅当表为空时）。返回插入条数。"""
    if db.query(Music).count() > 0:
        return 0
    _ensure_placeholder_audio()

    rows: list[Music] = []
    for m in SEED_MUSIC:
        rows.append(Music(
            title=m["title"],
            audio_url=f"/static/audio/{m['yin_type']}.mp3",
            cover_image=f"/static/images/cover_{m['yin_type']}.svg",
            yin_type=m["yin_type"],
            duration=float(m["duration"]),
            tags=m["tags"],
        ))
    db.add_all(rows)
    db.commit()
    logger.info("已插入 %d 首古琴曲目", len(rows))
    return len(rows)


def seed_shop_items(db: Session) -> int:
    """插入商店物品（仅当表为空时）。返回插入条数。"""
    if db.query(ShopItem).count() > 0:
        return 0
    rows = [ShopItem(**item) for item in DEFAULT_SHOP_ITEMS]
    db.add_all(rows)
    db.commit()
    logger.info("已插入 %d 个商店物品", len(rows))
    return len(rows)


def run_seed(db: Session) -> None:
    """启动时执行：建表 → 种子数据 → 引导管理员。"""
    seed_music(db)
    seed_shop_items(db)
    ensure_first_admin(db)


def _generate_admin_password(length: int = 16) -> str:
    """生成易读的管理员初始密码（大小写+数字，去掉容易混淆的字符）。"""
    alphabet = "".join(c for c in (string.ascii_letters + string.digits) if c not in "0OIl1")
    return "".join(secrets.choice(alphabet) for _ in range(length))


def ensure_first_admin(db: Session) -> None:
    """如果系统里没有管理员，按 settings 创建第一个。

    - 已有管理员：什么都不做（保证可重复启动）
    - settings.admin_password 留空：随机生成 16 位密码，**写一行 WARN 到日志**
    - settings.admin_password 已设置：直接用固定密码
    - 写完密码后**不会**再次输出，避免泄露历史
    """
    exists = db.query(User).filter(User.is_admin == True).first()  # noqa: E712
    if exists is not None:
        return

    # 决定初始密码
    if settings.admin_password:
        password = settings.admin_password
        password_source = "fixed (.env)"
    else:
        password = _generate_admin_password()
        password_source = "random (auto-generated, see log)"

    # 决定昵称：如果 admin_username 已存在（普通用户占了），加后缀
    nickname = settings.admin_username
    suffix = 1
    while db.query(User).filter(User.nickname == nickname).first() is not None:
        suffix += 1
        nickname = f"{settings.admin_username}_{suffix}"

    user = User(
        nickname=nickname,
        password_hash=hash_password(password),
        encryption_salt=generate_salt(),
        total_energy=0,
        is_admin=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # 在日志里高亮提示（开机时显示一次，下次启动不会再生成）
    logger.warning("=" * 60)
    logger.warning("[ADMIN] 已创建首个管理员账户")
    logger.warning("[ADMIN]   nickname : %s", nickname)
    if password_source.startswith("random"):
        logger.warning("[ADMIN]   password : %s  (随机生成，请妥善保存)", password)
    else:
        logger.warning("[ADMIN]   password : (来自 .env，未显示)")
    logger.warning("[ADMIN]   入口     : http://%s:%d%s",
                   settings.host, settings.port, settings.admin_path_prefix)
    logger.warning("=" * 60)
