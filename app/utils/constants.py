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
    ENCOURAGE = "encourage"         # 给别人的漂流瓶留言鼓励


# 单日能量获取上限（防刷）
DAILY_ENERGY_LIMITS: Final[dict[str, int]] = {
    "listen_music": 20,    # 露水
    "write_diary": 10,     # 阳光
    "checkin": 5,          # 养分
    "encourage": 10,       # 留言鼓励
}


# ─────────────────────────────────────────────────────────────
# 物品类型
# ─────────────────────────────────────────────────────────────

class ItemType(str, Enum):
    """花园物品类型。"""
    FLOWER = "flower"      # 花种（用落叶兑换）
    COSTUME = "costume"    # 装扮（用露水兑换）
    BADGE = "badge"        # 徽章（自动触发）


# 默认兑换商店
# v2.3：花种用落叶（leaves）兑换，装饰物用露水（dew）兑换
# v2.4：花坊改名 + 花种种类增多 + 装扮扩充 + 每板块对应徽章
# v2.4.2：花种介绍统一为花语 / emoji 与名称对齐 / 装扮动物扩充 / 徽章奖励落叶
DEFAULT_SHOP_ITEMS: Final[list[dict]] = [
    # 花种（落叶兑换 —— 落叶归根能施肥种花；介绍统一为花语）
    {"name": "向日葵", "item_type": "flower", "cost": 3,  "cost_currency": "leaves", "image": "🌻", "description": "信念与爱慕，向阳而生"},
    {"name": "竹子",   "item_type": "flower", "cost": 5,  "cost_currency": "leaves", "image": "🎋", "description": "坚韧虚心，节节高升"},
    {"name": "雏菊",   "item_type": "flower", "cost": 5,  "cost_currency": "leaves", "image": "🌼", "description": "天真纯洁，深藏心底的爱"},
    {"name": "莲花",   "item_type": "flower", "cost": 8,  "cost_currency": "leaves", "image": "🪷", "description": "清白坚贞，出淤泥而不染"},
    {"name": "薰衣草", "item_type": "flower", "cost": 8,  "cost_currency": "leaves", "image": "🪻", "description": "等待爱情，安静与坚守"},
    {"name": "郁金香", "item_type": "flower", "cost": 10, "cost_currency": "leaves", "image": "🌷", "description": "完美的爱，体贴与高雅"},
    {"name": "樱花",   "item_type": "flower", "cost": 12, "cost_currency": "leaves", "image": "🌸", "description": "生命之美，纯洁与幸福"},
    {"name": "桃花",   "item_type": "flower", "cost": 12, "cost_currency": "leaves", "image": "🌺", "description": "爱情降临，美好生活的开始"},
    {"name": "青松",   "item_type": "flower", "cost": 18, "cost_currency": "leaves", "image": "🌲", "description": "坚定长寿，傲骨长青"},
    {"name": "小麦",   "item_type": "flower", "cost": 18, "cost_currency": "leaves", "image": "🌾", "description": "丰收富足，金色的希望"},
    {"name": "青叶",   "item_type": "flower", "cost": 20, "cost_currency": "leaves", "image": "🍃", "description": "生机新生，一叶知秋"},
    # 装扮（露水兑换 —— 点缀小岛；含动物伙伴）
    {"name": "竹编帽", "item_type": "costume", "cost": 8,  "cost_currency": "dew", "image": "👒", "description": "种花人遮阳的草帽"},
    {"name": "茶具",   "item_type": "costume", "cost": 12, "cost_currency": "dew", "image": "🍵", "description": "一套素雅茶具"},
    {"name": "小鸟",   "item_type": "costume", "cost": 15, "cost_currency": "dew", "image": "🐦", "description": "枝头喳喳的小鸟，为你唱清晨"},
    {"name": "折扇",   "item_type": "costume", "cost": 18, "cost_currency": "dew", "image": "🪭", "description": "清风徐来"},
    {"name": "小鸭",   "item_type": "costume", "cost": 18, "cost_currency": "dew", "image": "🦆", "description": "池边悠然踱步的小鸭"},
    {"name": "油纸伞", "item_type": "costume", "cost": 20, "cost_currency": "dew", "image": "☂️", "description": "烟雨江南的油纸伞"},
    {"name": "小狗",   "item_type": "costume", "cost": 20, "cost_currency": "dew", "image": "🐶", "description": "摇着尾巴守在岛边的小狗"},
    {"name": "斗篷",   "item_type": "costume", "cost": 22, "cost_currency": "dew", "image": "🧥", "description": "挡风御寒的厚斗篷"},
    {"name": "鱼竿",   "item_type": "costume", "cost": 25, "cost_currency": "dew", "image": "🎣", "description": "独钓寒江雪"},
    {"name": "橘猫",   "item_type": "costume", "cost": 28, "cost_currency": "dew", "image": "🐈", "description": "一只慵懒的橘猫陪你在岛上"},
    {"name": "乌篷船", "item_type": "costume", "cost": 30, "cost_currency": "dew", "image": "🛶", "description": "可在静屿海面悠然飘荡"},
    {"name": "火烈鸟", "item_type": "costume", "cost": 35, "cost_currency": "dew", "image": "🦩", "description": "通体绯红，与你同游"},
    # 徽章（自动触发，cost=0；解锁即赠 BADGE_LEAF_REWARD 片落叶）
    {"name": "琴音知音",   "item_type": "badge", "cost": 0, "cost_currency": "dew", "image": "🎼", "description": "听满 10 首曲子自动获得 · 赠 10 落叶", "trigger": "listen_10"},
    {"name": "日记达人",   "item_type": "badge", "cost": 0, "cost_currency": "dew", "image": "📖", "description": "写满 30 篇日记自动获得 · 赠 20 落叶", "trigger": "diary_30"},
    {"name": "七日静心",   "item_type": "badge", "cost": 0, "cost_currency": "dew", "image": "✨", "description": "连续 7 天打卡自动获得 · 赠 7 落叶", "trigger": "streak_7"},
    {"name": "拾瓶旅人",   "item_type": "badge", "cost": 0, "cost_currency": "dew", "image": "🏺", "description": "拾满 10 个漂流瓶自动获得 · 赠 10 落叶", "trigger": "pick_10"},
    {"name": "树洞倾心",   "item_type": "badge", "cost": 0, "cost_currency": "dew", "image": "🌳", "description": "与树洞对话满 20 次自动获得 · 赠 15 落叶", "trigger": "chat_20"},
    {"name": "花间客",     "item_type": "badge", "cost": 0, "cost_currency": "dew", "image": "🌷", "description": "种满 10 朵花自动获得 · 赠 10 落叶", "trigger": "flower_10"},
]


# 解锁徽章奖励的落叶数（v2.4.4：按徽章次数要求分级，打破"没花没落叶"死锁）
BADGE_LEAF_REWARDS: Final[dict[str, int]] = {
    "streak_7": 7,    # 连续 7 天打卡
    "listen_10": 10,  # 听满 10 首曲子
    "pick_10": 10,    # 拾满 10 个漂流瓶
    "flower_10": 10,  # 种满 10 朵花
    "chat_20": 15,    # 与树洞对话满 20 次
    "diary_30": 20,   # 写满 30 篇日记
}
# 默认奖励（未匹配 trigger 时的兜底）
BADGE_LEAF_REWARD_DEFAULT: Final[int] = 10



# ─────────────────────────────────────────────────────────────
# 古琴曲谱分类（v2.3 新增：古琴弹西洋曲谱子板块）
# ─────────────────────────────────────────────────────────────

class MusicCategory(str, Enum):
    """古琴曲目分类。"""
    CLASSIC = "classic"    # 五音传统古曲（宫商角徵羽）
    WESTERN = "western"    # 古琴弹西洋曲谱


MUSIC_CATEGORY_INFO: Final[dict[str, dict]] = {
    "classic": {"name": "五音古曲", "desc": "宫商角徵羽 · 入五脏 · 调情志"},
    "western": {"name": "古琴弹西洋", "desc": "用古琴演绎西洋旋律 · 中西合璧"},
}


# 能量显示文案
ENERGY_LABELS: Final[dict[str, dict]] = {
    "listen_music": {"name": "露水", "icon": "💧"},
    "write_diary":  {"name": "阳光", "icon": "☀️"},
    "checkin":      {"name": "养分", "icon": "🌱"},
    "streak_7":     {"name": "阳光", "icon": "✨"},
    "exchange":     {"name": "消耗", "icon": "🍃"},
    "daily_bonus":  {"name": "晨露", "icon": "🌅"},
    "encourage":    {"name": "善意", "icon": "💛"},
}
