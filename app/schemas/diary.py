"""日记 / 漂流瓶相关 Pydantic。

v2.3 调整：
- 移除密码保护，日记改明文存储（content 字段）。
- 新增发布选项：is_public（放入漂流瓶，公开可见可评论）/ send_to_ai_hole（不放入漂流瓶，仅自己可见 + 同步树洞）。
"""

from typing import Optional
from pydantic import BaseModel, Field


class DiaryCreateIn(BaseModel):
    """创建日记。v2.3 起改明文，移除密码加密。"""
    content: str = Field(..., min_length=1, description="日记明文内容")
    mood_type: Optional[str] = Field(None, max_length=20)
    is_public: bool = Field(False, description="是否放入漂流瓶（公开可见，允许评论）")
    send_to_ai_hole: bool = Field(False, description="不放入漂流瓶时，是否同步至树洞")


class DiaryOut(BaseModel):
    """日记详情（明文，仅本人查看自己的 / 拾取公开漂流瓶时返回）。"""
    id: int
    user_id: int
    content: str
    mood_type: Optional[str] = None
    is_public: bool
    send_to_ai_hole: bool = False
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
