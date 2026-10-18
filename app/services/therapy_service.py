"""身心调理推荐 + 八段锦打卡 + 好物预约。

设计原则：
- 只做「传统养生参考」，不做诊断、不承诺疗效。
- 推荐是规则映射（问题关键词 → 曲 / 八段锦 / 香囊 / 手串 / 食疗），
  不依赖 AI，结果稳定、可解释、可测试。
- 商品当前只做「橱窗 + 预约/外链」，不接支付与发货。
"""

from __future__ import annotations

import logging
from datetime import date
from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.music import Music
from app.models.therapy import BaduanjinCheckin, TherapyInterest
from app.models.user import User
from app.services.energy_service import grant_energy


logger = logging.getLogger("qi.therapy")


# ─────────────────────────────────────────────────────────────
# 八段锦 8 式
# ─────────────────────────────────────────────────────────────

BADUANJIN: dict[str, dict] = {
    "tuotian": {
        "name": "双手托天理三焦",
        "focus": "拉伸躯干、打开胸腔",
        "steps": [
            "自然站立，双脚与肩同宽，双手在腹前十指交叉。",
            "吸气，掌心向上托起，经胸前翻掌上举，抬头看手。",
            "呼气，双手分开沿体侧缓缓下落，回到腹前。",
        ],
    },
    "kaigong": {
        "name": "左右开弓似射雕",
        "focus": "打开肩背、舒展胸肺",
        "steps": [
            "马步站立，双手在胸前交叉。",
            "一手向外侧推出如拉弓，另一手在胸前如拉弦，头转向推手方向。",
            "左右交替，动作缓慢，配合呼吸。",
        ],
    },
    "danju": {
        "name": "调理脾胃须单举",
        "focus": "牵拉腹部、帮助消化",
        "steps": [
            "自然站立，一手掌心向上举过头顶，另一手掌心向下按。",
            "上下对拉，保持两秒，换另一侧。",
            "动作配合缓慢呼吸，不要憋气。",
        ],
    },
    "wanghou": {
        "name": "五劳七伤往后瞧",
        "focus": "放松颈肩、缓解久坐",
        "steps": [
            "自然站立，双手垂于体侧。",
            "头颈缓慢向后转，眼睛看向后方，身体保持不动。",
            "停留两秒后回正，左右交替。",
        ],
    },
    "yaotou": {
        "name": "摇头摆尾去心火",
        "focus": "活动腰胯、放松情绪",
        "steps": [
            "马步站立，双手扶膝。",
            "上身向一侧俯身，头与臀部向相反方向摆动。",
            "左右交替，动作柔和，不要用力过猛。",
        ],
    },
    "pansu": {
        "name": "两手攀足固肾腰",
        "focus": "拉伸腰背、放松后侧链",
        "steps": [
            "自然站立，双手上举后沿腰背向下。",
            "俯身，双手尽量攀握脚踝或小腿，膝盖可微屈。",
            "缓慢起身，双手回到腰后。",
        ],
    },
    "zanquan": {
        "name": "攒拳怒目增气力",
        "focus": "握拳发力、提振精神",
        "steps": [
            "马步站立，双手握拳收于腰侧。",
            "一拳缓慢向前打出，眼睛睁大看向拳面。",
            "收拳换另一侧，发力但不憋气。",
        ],
    },
    "dianzu": {
        "name": "背后七颠百病消",
        "focus": "放松全身、收势",
        "steps": [
            "自然站立，脚跟并拢，双手垂于体侧。",
            "脚跟缓慢抬起，再轻轻落下，身体放松。",
            "连续做 7 次，作为整套收势。",
        ],
    },
}


# ─────────────────────────────────────────────────────────────
# 香囊 / 手串 / 食疗（只做传统养生参考）
# ─────────────────────────────────────────────────────────────

SACHETS: dict[str, dict] = {
    "anshen": {
        "key": "anshen", "type": "sachet", "name": "安神香囊",
        "ingredients": "薰衣草、合欢花、陈皮",
        "note": "放在枕边或书桌旁，气味变淡后更换。",
        "price": 39.0, "purchase_url": "", "available": False,
    },
    "shugan": {
        "key": "shugan", "type": "sachet", "name": "疏肝香囊",
        "ingredients": "玫瑰花、陈皮、佛手",
        "note": "适合白天随身或放在办公桌旁。",
        "price": 39.0, "purchase_url": "", "available": False,
    },
    "jianpi": {
        "key": "jianpi", "type": "sachet", "name": "健脾香囊",
        "ingredients": "陈皮、藿香、艾叶",
        "note": "气味较明显，建议先小范围试用。",
        "price": 42.0, "purchase_url": "", "available": False,
    },
    "qingxin": {
        "key": "qingxin", "type": "sachet", "name": "清心香囊",
        "ingredients": "薄荷、菊花、淡竹叶",
        "note": "气味清凉，午后使用更合适。",
        "price": 36.0, "purchase_url": "", "available": False,
    },
}

BRACELETS: dict[str, dict] = {
    "chenxiang": {
        "key": "chenxiang", "type": "bracelet", "name": "沉香手串",
        "material": "沉香木珠",
        "note": "木质手串，避免长时间浸水。",
        "price": 168.0, "purchase_url": "", "available": False,
    },
    "tanxiang": {
        "key": "tanxiang", "type": "bracelet", "name": "檀香手串",
        "material": "檀香木珠",
        "note": "气味温和，适合日常佩戴。",
        "price": 128.0, "purchase_url": "", "available": False,
    },
    "puti": {
        "key": "puti", "type": "bracelet", "name": "菩提子手串",
        "material": "菩提子",
        "note": "无香型，适合不喜欢香味的人。",
        "price": 98.0, "purchase_url": "", "available": False,
    },
}

FOODS: dict[str, dict] = {
    "lianzi": {
        "key": "lianzi", "type": "food", "name": "莲子",
        "nature": "平性，味甘涩",
        "serving": "可煮粥、煲汤，每次 10–15 克。",
        "allergens": "无已知常见过敏原；便秘者适量。",
        "price": 29.0, "purchase_url": "", "available": False,
    },
    "baihe": {
        "key": "baihe", "type": "food", "name": "百合",
        "nature": "微寒，味甘",
        "serving": "可煮粥、炒菜，每次 10–20 克。",
        "allergens": "百合科植物过敏者慎用；脾胃虚寒者适量。",
        "price": 32.0, "purchase_url": "", "available": False,
    },
    "shanyao": {
        "key": "shanyao", "type": "food", "name": "山药",
        "nature": "平性，味甘",
        "serving": "蒸食、煮粥或煲汤，每次 50–100 克。",
        "allergens": "含黏液蛋白，皮肤敏感者处理时建议戴手套。",
        "price": 26.0, "purchase_url": "", "available": False,
    },
    "hongzao": {
        "key": "hongzao", "type": "food", "name": "红枣",
        "nature": "温性，味甘",
        "serving": "可煮粥、泡水，每次 3–5 颗。",
        "allergens": "无已知常见过敏原；含糖量较高，控糖人群适量。",
        "price": 24.0, "purchase_url": "", "available": False,
    },
    "xiaomi": {
        "key": "xiaomi", "type": "food", "name": "小米",
        "nature": "凉性，味甘咸",
        "serving": "煮粥，每次 30–50 克。",
        "allergens": "无已知常见过敏原；胃寒者建议热食。",
        "price": 22.0, "purchase_url": "", "available": False,
    },
    "juhua": {
        "key": "juhua", "type": "food", "name": "菊花茶",
        "nature": "微寒，味甘苦",
        "serving": "每次 3–5 朵，温水冲泡。",
        "allergens": "菊科植物过敏者慎用；脾胃虚寒者适量。",
        "price": 28.0, "purchase_url": "", "available": False,
    },
}


# ─────────────────────────────────────────────────────────────
# 问题 → 推荐规则
# ─────────────────────────────────────────────────────────────

PROBLEM_RULES: list[dict] = [
    {
        "key": "sleep", "label": "睡眠",
        "keywords": ["睡不着", "失眠", "多梦", "易醒", "熬夜", "睡不好", "入睡"],
        "yin": "yu", "moves": ["dianzu", "pansu"],
        "sachet": "anshen", "bracelet": "chenxiang", "food": "lianzi",
        "music_reason": "羽音沉静下行，适合把浮起来的心慢慢放回身体里。",
    },
    {
        "key": "anxiety", "label": "焦虑",
        "keywords": ["焦虑", "紧张", "心慌", "担心", "压力", "不安", "害怕"],
        "yin": "jue", "moves": ["kaigong", "tuotian"],
        "sachet": "shugan", "bracelet": "tanxiang", "food": "baihe",
        "music_reason": "角音舒展生发，适合把憋闷的情绪轻轻打开。",
    },
    {
        "key": "fatigue", "label": "疲惫",
        "keywords": ["累", "疲惫", "没力气", "乏力", "困", "提不起劲", "倦"],
        "yin": "gong", "moves": ["tuotian", "danju"],
        "sachet": "jianpi", "bracelet": "puti", "food": "shanyao",
        "music_reason": "宫音温厚安定，像一顿热饭，先把人托住。",
    },
    {
        "key": "digestion", "label": "脾胃",
        "keywords": ["胃", "消化", "腹胀", "没胃口", "吃不下", "脾胃", "反酸"],
        "yin": "gong", "moves": ["danju", "yaotou"],
        "sachet": "jianpi", "bracelet": "chenxiang", "food": "xiaomi",
        "music_reason": "宫音入脾，节奏平稳，适合饭后安静地听一会儿。",
    },
    {
        "key": "low_mood", "label": "低落",
        "keywords": ["难过", "低落", "想哭", "没意思", "沮丧", "悲伤", "失落"],
        "yin": "zhi", "moves": ["kaigong", "zanquan"],
        "sachet": "shugan", "bracelet": "chenxiang", "food": "hongzao",
        "music_reason": "徵音温暖明亮，像一束不刺眼的光，陪你坐一会儿。",
    },
    {
        "key": "irritability", "label": "烦躁",
        "keywords": ["烦", "生气", "暴躁", "上火", "易怒", "静不下来", "急躁"],
        "yin": "shang", "moves": ["wanghou", "yaotou"],
        "sachet": "qingxin", "bracelet": "tanxiang", "food": "juhua",
        "music_reason": "商音清肃收敛，适合把往外冲的劲儿慢慢收回来。",
    },
]

DEFAULT_CATEGORY = {
    "key": "general", "label": "日常放松",
    "yin": "jue", "moves": ["tuotian", "dianzu"],
    "sachet": "shugan", "bracelet": "puti", "food": "xiaomi",
    "music_reason": "先从一段舒展的角音开始，配合两次缓慢呼吸。",
}

DISCLAIMER = (
    "以上为传统养生与生活方式参考，不构成医疗诊断或治疗建议。"
    "如有持续不适、慢性病、孕期、儿童或正在服药，请先咨询医生。"
    "香囊/手串为日常用品，不替代药物；食疗请留意过敏原与适量原则。"
)


# ─────────────────────────────────────────────────────────────
# 推荐
# ─────────────────────────────────────────────────────────────

def _match_category(problem: str, tags: Optional[list[str]] = None) -> dict:
    text = (problem or "").strip().lower()
    joined_tags = " ".join(tags or [])
    haystack = f"{text} {joined_tags}"
    for rule in PROBLEM_RULES:
        if rule["key"] in (tags or []):
            return rule
        if any(k.lower() in haystack for k in rule["keywords"]):
            return rule
    return DEFAULT_CATEGORY


def _music_for(db: Session, yin: str) -> Optional[dict]:
    m = (
        db.query(Music)
        .filter(Music.yin_type == yin, Music.category == "classic")
        .order_by(Music.id.asc())
        .first()
    )
    if m is None:
        return None
    return {
        "id": m.id,
        "title": m.title,
        "yin_type": m.yin_type,
        "audio_url": m.audio_url,
        "cover_image": m.cover_image,
        "duration": m.duration,
    }


def _move(key: str) -> dict:
    data = BADUANJIN[key]
    return {
        "key": key,
        "name": data["name"],
        "focus": data["focus"],
        "steps": data["steps"],
        "video_url": f"https://search.bilibili.com/all?keyword=八段锦%20{data['name']}",
    }


def _product(data: dict) -> dict:
    return {
        "key": data["key"],
        "type": data["type"],
        "name": data["name"],
        "price": data["price"],
        "purchase_url": data["purchase_url"],
        "available": data["available"],
        "note": data.get("note") or data.get("serving") or "",
        "allergens": data.get("allergens"),
        "ingredients": data.get("ingredients"),
        "material": data.get("material"),
        "nature": data.get("nature"),
    }


def recommend(db: Session, problem: str, tags: Optional[list[str]] = None) -> dict:
    category = _match_category(problem, tags)
    music = _music_for(db, category["yin"])
    return {
        "category": {
            "key": category["key"],
            "label": category["label"],
        },
        "music": {
            "yin_type": category["yin"],
            "reason": category["music_reason"],
            "track": music,
        },
        "baduanjin": [_move(k) for k in category["moves"]],
        "sachet": _product(SACHETS[category["sachet"]]),
        "bracelet": _product(BRACELETS[category["bracelet"]]),
        "food": _product(FOODS[category["food"]]),
        "disclaimer": DISCLAIMER,
    }


# ─────────────────────────────────────────────────────────────
# 八段锦打卡
# ─────────────────────────────────────────────────────────────

def checkin_baduanjin(db: Session, user: User, move_key: str = "general") -> dict:
    today = date.today()
    existing = (
        db.query(BaduanjinCheckin)
        .filter(
            BaduanjinCheckin.user_id == user.id,
            BaduanjinCheckin.check_date == today,
        )
        .first()
    )
    if existing is not None:
        raise HTTPException(status_code=400, detail="今天已经跟练过啦，明天再来活动一下")

    record = BaduanjinCheckin(user_id=user.id, check_date=today, move_key=move_key or "general")
    db.add(record)
    db.flush()

    grant_energy(
        db, user, amount=1, source="baduanjin",
        note="八段锦跟练打卡",
    )
    db.commit()
    new_total = db.query(User.total_energy).filter(User.id == user.id).scalar()
    return {
        "success": True,
        "checkin": record.to_dict(),
        "new_total_energy": new_total or 0,
        "granted_energy": 1,
    }


def baduanjin_status(db: Session, user: User) -> dict:
    today = date.today()
    existing = (
        db.query(BaduanjinCheckin)
        .filter(
            BaduanjinCheckin.user_id == user.id,
            BaduanjinCheckin.check_date == today,
        )
        .first()
    )
    return {
        "checked_in": existing is not None,
        "checkin": existing.to_dict() if existing else None,
    }


# ─────────────────────────────────────────────────────────────
# 好物预约 / 意向
# ─────────────────────────────────────────────────────────────

def _all_products() -> dict[str, dict]:
    items = {}
    for group in (SACHETS, BRACELETS, FOODS):
        for key, data in group.items():
            items[key] = data
    return items


def record_interest(db: Session, user: User, product_key: str) -> dict:
    product = _all_products().get(product_key)
    if product is None:
        raise HTTPException(status_code=404, detail="找不到这件好物")

    existing = (
        db.query(TherapyInterest)
        .filter(
            TherapyInterest.user_id == user.id,
            TherapyInterest.product_key == product_key,
        )
        .first()
    )
    if existing is not None:
        return {"success": True, "already": True, "interest": existing.to_dict()}

    row = TherapyInterest(
        user_id=user.id,
        product_key=product_key,
        product_name=product["name"],
    )
    db.add(row)
    db.commit()
    return {"success": True, "already": False, "interest": row.to_dict()}
