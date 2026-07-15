"""业务常量：5 音定义、心情枚举、能量来源。"""

from __future__ import annotations

from enum import Enum
from typing import Final


# ─────────────────────────────────────────────────────────────
# 古琴五音
# ─────────────────────────────────────────────────────────────

class YinType(str, Enum):
    """五音枚举。"""
    GONG = "gong"     # 宫
    SHANG = "shang"   # 商
    JUE = "jue"       # 角
    ZHI = "zhi"       # 徵
    YU = "yu"         # 羽


YIN_INFO: Final[dict[str, dict]] = {
    "gong": {
        "name": "宫",
        "element": "土",
        "organ": "脾胃",
        "color": "#E8D5A8",
        "tags": ["健脾", "助消化"],
        "scene": "厚实沉稳的鼓声，傍晚的钟鸣",
        "description": "宫音入脾，五行属土。音律悠扬沉静，如大地承载万物，宜于消化不良、疲惫倦怠时聆听。",
    },
    "shang": {
        "name": "商",
        "element": "金",
        "organ": "肺大肠",
        "color": "#D4D9C8",
        "tags": ["润肺", "舒缓"],
        "scene": "秋日落叶，金属清越",
        "description": "商音入肺，五行属金。音色高洁清亮，如深秋之爽气，宜于胸闷气短、情绪低落时聆听。",
    },
    "jue": {
        "name": "角",
        "element": "木",
        "organ": "肝胆",
        "color": "#A8C5A0",
        "tags": ["疏肝", "解郁", "抗焦虑"],
        "scene": "春生草木，东风解冻",
        "description": "角音入肝，五行属木。音调舒展条达，如春日生发之机，宜于焦虑郁结、情绪压抑时聆听。",
    },
    "zhi": {
        "name": "徵",
        "element": "火",
        "organ": "心小肠",
        "color": "#E8B8A8",
        "tags": ["养心", "安神"],
        "scene": "夏日繁花，烛火跃动",
        "description": "徵音入心，五行属火。旋律热烈明快，如夏日之艳阳，宜于心烦易怒、夜间难眠时聆听。",
    },
    "yu": {
        "name": "羽",
        "element": "水",
        "organ": "肾膀胱",
        "color": "#A8B8C5",
        "tags": ["宁心", "助眠"],
        "scene": "冬雪初降，泉水叮咚",
        "description": "羽音入肾，五行属水。音色柔婉幽深，如寒夜之静水，宜于失眠多梦、惊恐不安时聆听。",
    },
}


# ─────────────────────────────────────────────────────────────
# 心情枚举
# ─────────────────────────────────────────────────────────────

class MoodEmoji(str, Enum):
    """心情图标。每种对应一个 emoji + 颜色。"""
    ECSTATIC = "ecstatic"   # 极度开心 🤩
    HAPPY = "happy"         # 开心 😊
    CALM = "calm"           # 平静 😌
    TIRED = "tired"         # 疲惫 😪
    ANXIOUS = "anxious"     # 焦虑 😰
    ANGRY = "angry"         # 生气 😠
    SAD = "sad"             # 悲伤 😢


MOOD_INFO: Final[dict[str, dict]] = {
    "ecstatic": {"emoji": "🤩", "label": "极度开心", "color": "#FFD56B"},
    "happy":    {"emoji": "😊", "label": "开心",     "color": "#F6B26B"},
    "calm":     {"emoji": "😌", "label": "平静",     "color": "#A8D5BA"},
    "tired":    {"emoji": "😪", "label": "疲惫",     "color": "#B8B5C5"},
    "anxious":  {"emoji": "😰", "label": "焦虑",     "color": "#9BB5D5"},
    "angry":    {"emoji": "😠", "label": "生气",     "color": "#E89A9A"},
    "sad":      {"emoji": "😢", "label": "悲伤",     "color": "#A5A8C5"},
}


# ─────────────────────────────────────────────────────────────
# 能量来源
# ─────────────────────────────────────────────────────────────

class EnergySource(str, Enum):
    """能量变动来源。"""
    LISTEN_MUSIC = "listen_music"   # 听完一首曲子
    WRITE_DIARY = "write_diary"     # 写日记
    CHECKIN = "checkin"             # 心情打卡
    STREAK_7 = "streak_7"           # 7 日连胜
    EXCHANGE = "exchange"           # 兑换物品
    DAILY_BONUS = "daily_bonus"     # 每日登录


# 单日能量获取上限（防刷）
DAILY_ENERGY_LIMITS: Final[dict[str, int]] = {
    "listen_music": 20,    # 露水
    "write_diary": 10,     # 阳光
    "checkin": 5,          # 养分
}


# ─────────────────────────────────────────────────────────────
# 物品类型
# ─────────────────────────────────────────────────────────────

class ItemType(str, Enum):
    """花园物品类型。"""
    FLOWER = "flower"      # 花种
    COSTUME = "costume"    # 装扮
    BADGE = "badge"        # 徽章


# 默认兑换商店
DEFAULT_SHOP_ITEMS: Final[list[dict]] = [
    # 花种
    {"name": "向日葵", "item_type": "flower", "cost": 5,  "image": "🌻", "description": "阳光之子"},
    {"name": "竹子",   "item_type": "flower", "cost": 10, "image": "🎋", "description": "虚心有节"},
    {"name": "莲花",   "item_type": "flower", "cost": 15, "image": "🪷", "description": "出淤泥而不染"},
    {"name": "梅花",   "item_type": "flower", "cost": 20, "image": "🌸", "description": "凌寒独自开"},
    {"name": "青松",   "item_type": "flower", "cost": 30, "image": "🌲", "description": "岁寒三友"},
    # 装扮
    {"name": "竹编帽", "item_type": "costume", "cost": 8,  "image": "👒", "description": "山间采药人的帽子"},
    {"name": "茶具",   "item_type": "costume", "cost": 12, "image": "🍵", "description": "一套素雅茶具"},
    {"name": "折扇",   "item_type": "costume", "cost": 18, "image": "🪭", "description": "清风徐来"},
    # 徽章
    {"name": "古琴初学者", "item_type": "badge", "cost": 0, "image": "🎼", "description": "听满 10 首曲子自动获得", "trigger": "listen_10"},
    {"name": "日记达人",   "item_type": "badge", "cost": 0, "image": "📖", "description": "写满 30 篇日记自动获得", "trigger": "diary_30"},
    {"name": "七日静心",   "item_type": "badge", "cost": 0, "image": "✨", "description": "连续 7 天打卡自动获得", "trigger": "streak_7"},
]


# 能量显示文案
ENERGY_LABELS: Final[dict[str, dict]] = {
    "listen_music": {"name": "露水", "icon": "💧"},
    "write_diary":  {"name": "阳光", "icon": "☀️"},
    "checkin":      {"name": "养分", "icon": "🌱"},
    "streak_7":     {"name": "阳光", "icon": "✨"},
    "exchange":     {"name": "消耗", "icon": "🍃"},
    "daily_bonus":  {"name": "晨露", "icon": "🌅"},
}
