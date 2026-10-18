"""AI 相关 Pydantic 模型（NVIDIA NIM API 接入）。

v2.6.0：AI 树洞对话移除，只保留 3 个场景。
"""

from typing import Optional
from pydantic import BaseModel, Field


class AIEncouragementIn(BaseModel):
    """漂流瓶 AI 鼓励语请求。"""
    diary_preview: Optional[str] = Field(None, max_length=200, description="日记前 120 字预览（可能为空）")
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
