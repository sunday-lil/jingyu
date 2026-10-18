"""日记 / 漂流瓶相关 Pydantic。

v2.3：日记改明文。
v2.6.0：移除 AI 树洞同步，is_public=False 统一进入「静屿角落」。
"""

from typing import Optional
from pydantic import BaseModel, Field


class DiaryCreateIn(BaseModel):
    """创建日记。v2.3 起明文；v2.6.0 用 is_public 区分漂流瓶 / 静屿角落。"""
    content: str = Field(..., min_length=1, description="日记明文内容")
    mood_type: Optional[str] = Field(None, max_length=20)
    is_public: bool = Field(False, description="True=放入漂流瓶（公开）；False=留在静屿角落（仅自己可见）")


class DiaryOut(BaseModel):
    """日记详情（明文，仅本人查看自己的 / 拾取公开漂流瓶时返回）。"""
    id: int
    user_id: int
    content: str
    mood_type: Optional[str] = None
    is_public: bool
    created_at: str
    encouragement_count: int = 0


class DiaryPublicOut(BaseModel):
    """陌生人视角的漂流瓶：完整明文（v2.3 起漂流瓶公开可见）。"""
    id: int
    mood_type: Optional[str] = None
    content: str
    created_at: str
    encouragement_count: int = 0


class EncouragementIn(BaseModel):
    content: str = Field(..., min_length=1, max_length=200)


class EncouragementOut(BaseModel):
    id: int
    content: str
    created_at: str
    diary_id: int
