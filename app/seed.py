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
from app.models.garden import ShopItem, GardenItem
from app.models.user import User
from app.utils.constants import DEFAULT_SHOP_ITEMS, YinType
from app.utils.crypto import generate_salt, hash_password


logger = logging.getLogger(__name__)


# 真实古琴曲名（占位音频）
SEED_MUSIC: list[dict] = [
    # 宫音（土）
    {"title": "梅花三弄",  "yin_type": "gong",   "category": "classic", "duration": 240, "tags": "健脾,古典"},
    {"title": "阳关三叠",  "yin_type": "gong",   "category": "classic", "duration": 200, "tags": "助消化,送别"},
    {"title": "平沙落雁",  "yin_type": "gong",   "category": "classic", "duration": 320, "tags": "健脾,秋意"},

    # 商音（金）
    {"title": "潇湘水云",  "yin_type": "shang",  "category": "classic", "duration": 280, "tags": "润肺,山水"},
    {"title": "长门怨",    "yin_type": "shang",  "category": "classic", "duration": 220, "tags": "舒缓,古意"},
    {"title": "佩兰",      "yin_type": "shang",  "category": "classic", "duration": 180, "tags": "润肺,雅正"},

    # 角音（木）
    {"title": "流水",      "yin_type": "jue",    "category": "classic", "duration": 420, "tags": "疏肝,解郁,抗焦虑"},
    {"title": "渔樵问答",  "yin_type": "jue",    "category": "classic", "duration": 260, "tags": "疏肝,问答"},
    {"title": "鸥鹭忘机",  "yin_type": "jue",    "category": "classic", "duration": 200, "tags": "解郁,自在"},

    # 徵音（火）
    {"title": "醉渔唱晚",  "yin_type": "zhi",    "category": "classic", "duration": 240, "tags": "养心,渔歌"},
    {"title": "山居吟",    "yin_type": "zhi",    "category": "classic", "duration": 200, "tags": "安神,山居"},
    {"title": "神人畅",    "yin_type": "zhi",    "category": "classic", "duration": 180, "tags": "养心,古意"},

    # 羽音（水）
    {"title": "广陵散",    "yin_type": "yu",     "category": "classic", "duration": 480, "tags": "宁心,助眠,古曲"},
    {"title": "大胡笳",    "yin_type": "yu",     "category": "classic", "duration": 360, "tags": "助眠,胡笳"},
    {"title": "幽兰",      "yin_type": "yu",     "category": "classic", "duration": 220, "tags": "宁心,兰香"},
    {"title": "普庵咒",    "yin_type": "yu",     "category": "classic", "duration": 260, "tags": "助眠,梵音"},

    # ── 古琴弹西洋曲谱（v2.3 新增子板块） ──
    # 用古琴演绎西洋经典旋律，yin_type 取最贴近的五音归类
    {"title": "绿袖子",      "yin_type": "yu",   "category": "western", "duration": 220, "tags": "西洋,民谣,古琴改编"},
    {"title": "卡农",        "yin_type": "gong", "category": "western", "duration": 260, "tags": "西洋,古典,古琴改编"},
    {"title": "致爱丽丝",    "yin_type": "jue",  "category": "western", "duration": 180, "tags": "西洋,钢琴改编,古琴"},
    {"title": "月光奏鸣曲",  "yin_type": "yu",   "category": "western", "duration": 300, "tags": "西洋,贝多芬,古琴改编"},
    {"title": "天鹅湖",      "yin_type": "shang","category": "western", "duration": 280, "tags": "西洋,芭蕾,古琴改编"},
    {"title": "昨日重现",    "yin_type": "zhi",  "category": "western", "duration": 240, "tags": "西洋,怀旧,古琴改编"},
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
    """插入曲目（按 title 幂等：缺失的补齐，已有的跳过）。返回新增条数。

    v2.3 改为按 title 幂等：老库已有 classic 曲目时，新加入的 western
    曲目也能补种进去。
    """
    _ensure_placeholder_audio()

    existing_titles = {t for (t,) in db.query(Music.title).all()}
    new_rows: list[Music] = []
    for m in SEED_MUSIC:
        if m["title"] in existing_titles:
            continue
        new_rows.append(Music(
            title=m["title"],
            audio_url=f"/static/audio/{m['yin_type']}.mp3",
            cover_image=f"/static/images/cover_{m['yin_type']}.svg",
            yin_type=m["yin_type"],
            category=m.get("category", "classic"),
            duration=float(m["duration"]),
            tags=m["tags"],
        ))
    if not new_rows:
        return 0
    db.add_all(new_rows)
    db.commit()
    logger.info("已插入 %d 首古琴曲目", len(new_rows))
    return len(new_rows)


def seed_shop_items(db: Session) -> int:
    """插入商店物品（按 name 幂等：缺失的补齐，已有的跳过）。返回新增条数。

    v2.4.2：新增「改名迁移」+「字段同步」——
      - 把老库里已被改名的物品（旧名→新名）的 name 改过来，并同步 user_flowers.flower_type。
      - 删除已被废弃的徽章（如「古琴初学者」）及其已发放的 GardenItem。
      - 已存在的物品同步 image / description / cost / cost_currency 字段（保持与 constants 一致）。
    v2.4：改为按 name 幂等，老库已有物品时新物品也能补种进去。
    v2.3：若老库 shop_items 已存在但缺少 cost_currency（DEFAULT NULL），
    按物品类型回填：flower → leaves，其他 → dew。
    """
    from sqlalchemy import text

    # 老库回填 cost_currency（migration 已加列，但老行默认 'dew'）
    # 花种应为 leaves
    db.execute(text(
        "UPDATE shop_items SET cost_currency='leaves' "
        "WHERE item_type='flower' AND cost_currency='dew'"
    ))
    db.commit()

    # ── v2.4.2 改名迁移表（旧名 → 新名）──
    # 因 emoji 不匹配或命名调整而改名的花种 / 装扮 / 徽章
    RENAME_MAP = {
        # 花种（emoji 与名称对齐）
        "桂花":   "小麦",   # 🌾 对应小麦而非桂花
        "银杏":   "青叶",   # 🍃 对应青叶而非银杏
        "兰花":   "樱花",   # 🌸 对应樱花；与原「梅花」合并
        "梅花":   "樱花",   # 🌸 对应樱花；删一留一
        # 装扮（emoji 与名称对齐）
        "白鹤":   "火烈鸟", # 🦩 对应火烈鸟
        "蓑衣":   "斗篷",   # 🧥 对应斗篷
        # 徽章（命名调整）
        "花田主人": "花间客", # 太直白 → 花间客
    }
    for old_name, new_name in RENAME_MAP.items():
        # 1. 改 shop_items.name（若新名已存在则直接删旧名行）
        existing_new = db.query(ShopItem).filter(ShopItem.name == new_name).first()
        old_rows = db.query(ShopItem).filter(ShopItem.name == old_name).all()
        if old_rows:
            if existing_new:
                # 新名已存在（来自 DEFAULT_SHOP_ITEMS 补种）：删旧名行 + 迁移 garden_items.item_id
                for r in old_rows:
                    db.query(GardenItem).filter(GardenItem.item_id == r.id).update(
                        {GardenItem.item_id: existing_new.id}
                    )
                    db.delete(r)
            else:
                # 新名不存在：直接改名
                for r in old_rows:
                    r.name = new_name
        # 2. 迁移 user_flowers.flower_type（仅对花种改名）
        if any(old_name == k for k in ("桂花", "银杏", "兰花", "梅花")):
            db.execute(text(
                "UPDATE user_flowers SET flower_type=:new WHERE flower_type=:old"
            ), {"new": new_name, "old": old_name})
    db.commit()

    # ── v2.4.2 去重：合并同名物品（如兰花+梅花都改名为樱花时会重复）──
    from sqlalchemy import func as _func
    dup_names = (
        db.query(ShopItem.name, _func.count(ShopItem.id))
        .group_by(ShopItem.name)
        .having(_func.count(ShopItem.id) > 1)
        .all()
    )
    for dup_name, _cnt in dup_names:
        rows = db.query(ShopItem).filter(ShopItem.name == dup_name).order_by(ShopItem.id.asc()).all()
        if len(rows) <= 1:
            continue
        keeper = rows[0]  # 保留 id 最小的
        for r in rows[1:]:
            # 把 garden_items.item_id 迁移到 keeper
            db.query(GardenItem).filter(GardenItem.item_id == r.id).update(
                {GardenItem.item_id: keeper.id}
            )
            db.delete(r)
        logger.info("去重：%s 保留 id=%d，删除 %d 个重复行", dup_name, keeper.id, len(rows) - 1)
    db.commit()

    # ── v2.4.2 删除废弃徽章 ──
    # 「古琴初学者」废弃（保留「琴音知音」）；删 shop_items 行 + 已发放的 GardenItem
    DEPRECATED_BADGES = ["古琴初学者"]
    for badge_name in DEPRECATED_BADGES:
        rows = db.query(ShopItem).filter(ShopItem.name == badge_name).all()
        for r in rows:
            db.query(GardenItem).filter(GardenItem.item_id == r.id).delete()
            db.delete(r)
    db.commit()

    # ── v2.4.2 已存在物品字段同步（image/description/cost/cost_currency）──
    existing_items = {it.name: it for it in db.query(ShopItem).all()}
    for item in DEFAULT_SHOP_ITEMS:
        row = existing_items.get(item["name"])
        if row is None:
            continue
        row.image = item.get("image", row.image)
        row.description = item.get("description", row.description)
        row.cost = item.get("cost", row.cost)
        row.cost_currency = item.get("cost_currency", row.cost_currency)
        if "trigger" in item:
            row.trigger = item["trigger"]
    db.commit()

    # 按 name 幂等：补种缺失的物品
    existing_names = {n for (n,) in db.query(ShopItem.name).all()}
    new_rows: list[ShopItem] = []
    for item in DEFAULT_SHOP_ITEMS:
        if item["name"] in existing_names:
            continue
        new_rows.append(ShopItem(**item))
    if not new_rows:
        return 0
    db.add_all(new_rows)
    db.commit()
    logger.info("已插入 %d 个商店物品", len(new_rows))
    return len(new_rows)


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
