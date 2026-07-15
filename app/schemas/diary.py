"""日记 / 漂流瓶相关 Pydantic。"""

from typing import Optional
from pydantic import BaseModel, Field


class DiaryCreateIn(BaseModel):
    """客户端加密后只传密文；后端永远不接触明文（端到端加密）。"""
    mood_type: Optional[str] = Field(None, max_length=20)
    is_public: bool = False
    content_encrypted: str = Field(..., min_length=1, description="客户端加密后的密文")


class DiaryOut(BaseModel):
    id: int
    user_id: int
    content: str  # 解密后的明文（仅本人查看时返回）
    mood_type: Optional[str] = None
    is_public: bool
    created_at: str
    encouragement_count: int = 0


class DiaryPublicOut(BaseModel):
    """陌生人视角的漂流瓶：脱敏后只给前 20 字。"""
    id: int
    mood_type: Optional[str] = None
    preview: str
    created_at: str


class EncouragementIn(BaseModel):
    content: str = Field(..., min_length=1, max_length=200)


class EncouragementOut(BaseModel):
    id: int
    content: str
    created_at: str
    diary_id: int
