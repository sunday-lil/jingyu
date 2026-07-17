"""AI API — NVIDIA NIM 接入。

端点：
- POST /api/ai/chat             树洞多轮对话
- POST /api/ai/encouragement    漂流瓶 AI 鼓励语
- POST /api/ai/healing          情绪日历打卡治愈语
- POST /api/ai/recommend-music  音乐 AI 心情推荐

所有端点都需要登录。AI 功能未启用（无 API key）或调用失败时，
返回 200 + available=false + 友好提示，前端优雅降级，不报错。
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.deps import get_current_user
from app.models.user import User
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
# 端点
# ─────────────────────────────────────────────────────────────

@router.post("/chat", response_model=AIChatOut)
def chat(
    body: AIChatIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """树洞多轮对话。前端传最近几轮 messages。"""
    messages = [{"role": m.role, "content": m.content} for m in body.messages]
    try:
        reply = ai_chat(messages)
        return AIChatOut(reply=reply, model=settings.ai_model, available=True)
    except AIServiceUnavailable as e:
        logger.info("AI chat 不可用: %s", e)
        return AIChatOut(reply=_UNAVAILABLE_REPLY, model="", available=False)


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
