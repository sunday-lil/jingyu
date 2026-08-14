"""AI API — NVIDIA NIM 接入。

端点：
- POST /api/ai/chat             树洞多轮对话（v2.3：文件历史 + 心情/日记上下文）
- POST /api/ai/encouragement    漂流瓶 AI 鼓励语
- POST /api/ai/healing          情绪日历打卡治愈语
- POST /api/ai/recommend-music  音乐 AI 心情推荐
- GET  /api/ai/conversations    树洞对话历史列表
- POST /api/ai/conversations     新建一段对话
- GET  /api/ai/conversations/{id}  加载某段对话
- DELETE /api/ai/conversations/{id} 删除某段对话（不保留）

所有端点都需要登录。AI 功能未启用（无 API key）或调用失败时，
返回 200 + available=false + 友好提示，前端优雅降级，不报错。
"""

from __future__ import annotations

import logging
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.models.diary import Diary
from app.models.mood import MoodCheckin
from app.schemas.ai import (
    AIChatIn, AIChatOut,
    AIEncouragementIn,
    AIHealingIn,
    AIMusicRecommendIn, AIMusicRecommendOut,
)
from app.services.ai_service import (
    AIServiceUnavailable,
    chat as ai_chat,
    generate_encouragement,
    generate_healing_message,
    recommend_music,
)
from app.services import chat_history_service


logger = logging.getLogger("qi.ai")

router = APIRouter(prefix="/api/ai", tags=["ai"])


# ─────────────────────────────────────────────────────────────
# 通用降级：AI 不可用时返回的占位回复
# ─────────────────────────────────────────────────────────────

_UNAVAILABLE_REPLY = "海风今天有点远，AI 暂时不在岛上。先把你想说的写在日记里，等风回来。"
_UNAVAILABLE_ENCOURAGEMENT = "这一刻，海替我抱了抱你。"
_UNAVAILABLE_HEALING = "今天的心，已经被这片海记下了。"
_UNAVAILABLE_MUSIC_REASON = "去听一听，让心慢下来。"


# ─────────────────────────────────────────────────────────────
# 辅助：拉取用户今日心情 + 今日日记片段（用于树洞上下文）
# ─────────────────────────────────────────────────────────────

def _get_today_mood_label(db: Session, user_id: int) -> str | None:
    """从情绪日历拉今日心情标签。"""
    from app.utils.constants import MOOD_INFO
    today = date.today()
    row = (
        db.query(MoodCheckin)
        .filter(MoodCheckin.user_id == user_id, MoodCheckin.check_date == today)
        .first()
    )
    if row is None:
        return None
    info = MOOD_INFO.get(row.mood_emoji)
    return info.get("label") if info else row.mood_emoji


def _get_today_diary_preview(db: Session, user_id: int) -> str | None:
    """拉今日最新一篇日记内容片段（前 80 字）。"""
    today_start = date.today().isoformat()
    row = (
        db.query(Diary)
        .filter(Diary.user_id == user_id)
        .order_by(Diary.created_at.desc())
        .first()
    )
    if row is None or not row.content:
        return None
    # 只取今日的
    created_str = row.created_at.date().isoformat() if row.created_at else None
    if created_str != today_start:
        return None
    return row.content[:80]


# ─────────────────────────────────────────────────────────────
# 端点
# ─────────────────────────────────────────────────────────────

@router.post("/chat", response_model=AIChatOut)
def chat(
    body: AIChatIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """树洞多轮对话。

    v2.3：
    - 基于 conversation_id 的文件历史存储。
    - 自动注入用户今日心情 + 今日日记作为上下文（让树洞针对性陪伴）。
    """
    # 获取或创建 conversation
    conv_id = chat_history_service.get_or_create_conversation(
        user.id, body.conversation_id
    )

    # 拉取今日上下文（若前端未显式传）
    today_mood = body.today_mood or _get_today_mood_label(db, user.id)
    today_diary = body.today_diary or _get_today_diary_preview(db, user.id)

    messages = [{"role": m.role, "content": m.content} for m in body.messages]
    try:
        reply = ai_chat(messages, today_mood=today_mood, today_diary=today_diary)
        # 写入历史：用户最后一条 + AI 回复
        last_user = next((m for m in reversed(messages) if m["role"] == "user"), None)
        if last_user:
            chat_history_service.append_message(user.id, conv_id, "user", last_user["content"])
        chat_history_service.append_message(user.id, conv_id, "assistant", reply)

        # v2.4.2：记一条 chat EnergyRecord（用于 chat_20 徽章计数）+ 检查成就
        from app.models.energy import EnergyRecord
        from app.services.energy_service import check_achievements
        db.add(EnergyRecord(
            user_id=user.id,
            amount=0,  # 对话本身不发露水，仅作为计数痕迹
            source="chat",
            note="树洞对话",
        ))
        achievement = check_achievements(db, user)
        db.commit()
        leaves_balance = achievement.get("leaves_balance", 0)
        new_leaves = achievement.get("new_leaves", 0)
        new_badges = achievement.get("new_badges", [])

        return AIChatOut(
            reply=reply,
            model=settings.ai_model,
            available=True,
            conversation_id=conv_id,
            new_leaves=new_leaves,
            leaves_balance=leaves_balance,
            new_badges=new_badges,
        )
    except AIServiceUnavailable as e:
        logger.info("AI chat 不可用: %s", e)
        return AIChatOut(
            reply=_UNAVAILABLE_REPLY,
            model="",
            available=False,
            conversation_id=conv_id,
        )


@router.get("/conversations")
def list_conversations(
    user: User = Depends(get_current_user),
):
    """树洞对话历史列表。"""
    items = chat_history_service.list_conversations(user.id)
    return {"count": len(items), "items": items}


@router.post("/conversations")
def new_conversation(
    user: User = Depends(get_current_user),
):
    """新建一段树洞对话。"""
    conv_id = chat_history_service.create_conversation(user.id)
    return {"conversation_id": conv_id}


@router.get("/conversations/{conversation_id}")
def get_conversation(
    conversation_id: str,
    user: User = Depends(get_current_user),
):
    """加载某段对话的所有消息。"""
    msgs = chat_history_service.load_messages(user.id, conversation_id)
    return {"conversation_id": conversation_id, "messages": msgs}


@router.delete("/conversations/{conversation_id}")
def delete_conversation(
    conversation_id: str,
    user: User = Depends(get_current_user),
):
    """删除一段对话（用户选择"不保留"时调用）。"""
    ok = chat_history_service.delete_conversation(user.id, conversation_id)
    return {"success": ok}


@router.post("/encouragement")
def encouragement(
    body: AIEncouragementIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """漂流瓶 AI 鼓励语（拾瓶时若无人写鼓励，前端调此端点）。"""
    try:
        text = generate_encouragement(
            diary_preview=body.diary_preview,
            mood_label=body.mood_label,
        )
        return {"text": text, "from_ai": True, "available": True, "model": settings.ai_model}
    except AIServiceUnavailable as e:
        logger.info("AI encouragement 不可用: %s", e)
        return {"text": _UNAVAILABLE_ENCOURAGEMENT, "from_ai": True, "available": False, "model": ""}


@router.post("/healing")
def healing(
    body: AIHealingIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """情绪日历打卡后的治愈语。"""
    label = body.mood_label or body.mood_emoji
    try:
        text = generate_healing_message(label)
        return {"text": text, "available": True, "model": settings.ai_model}
    except AIServiceUnavailable as e:
        logger.info("AI healing 不可用: %s", e)
        return {"text": _UNAVAILABLE_HEALING, "available": False, "model": ""}


@router.post("/recommend-music", response_model=AIMusicRecommendOut)
def recommend_music_endpoint(
    body: AIMusicRecommendIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """音乐 AI 心情推荐 — 根据用户描述推荐五音之一。"""
    try:
        result = recommend_music(body.user_state)
        return AIMusicRecommendOut(
            yin=result["yin"],
            reason=result["reason"],
            model=settings.ai_model,
            available=True,
        )
    except AIServiceUnavailable as e:
        logger.info("AI recommend-music 不可用: %s", e)
        # 降级：默认推荐「角」音（舒展生发，最通用）
        return AIMusicRecommendOut(
            yin="jue",
            reason=_UNAVAILABLE_MUSIC_REASON,
            model="",
            available=False,
        )
