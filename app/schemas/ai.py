"""AI 相关 Pydantic 模型（NVIDIA NIM API 接入）。"""

from typing import List, Optional
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """单条对话消息（OpenAI 兼容格式）。"""
    role: str = Field(..., description="user / assistant / system")
    content: str = Field(..., max_length=4000)


class AIChatIn(BaseModel):
    """树洞对话请求。前端传最近几轮 messages。"""
    messages: List[ChatMessage] = Field(..., min_length=1, max_length=20)
    scene: Optional[str] = Field(None, description="场景标识：treehole / companion 等，预留")


class AIChatOut(BaseModel):
    reply: str
    model: str
    available: bool = True


class AIEncouragementIn(BaseModel):
    """漂流瓶 AI 鼓励语请求。"""
    diary_preview: Optional[str] = Field(None, max_length=200, description="日记前 20 字预览（可能为空）")
    mood_label: Optional[str] = Field(None, max_length=20, description="作者心情标签中文")


class AIHealingIn(BaseModel):
    """情绪日历 AI 治愈语请求。"""
    mood_emoji: str = Field(..., max_length=20, description="心情枚举字符串，如 happy/sad")
    mood_label: Optional[str] = Field(None, max_length=20)


class AIMusicRecommendIn(BaseModel):
    """音乐 AI 心情推荐请求。"""
    user_state: Optional[str] = Field(None, max_length=200, description="用户自由描述当前状态")


class AIMusicRecommendOut(BaseModel):
    yin: str = Field(..., description="推荐的音：gong/shang/jue/zhi/yu")
    reason: str = Field(..., description="推荐理由（治愈系语气）")
    model: str
    available: bool = True
