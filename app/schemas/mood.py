"""心情打卡相关 Pydantic。"""

from datetime import date
from typing import Optional
from pydantic import BaseModel, Field


class MoodCheckinIn(BaseModel):
    mood_emoji: str = Field(..., description="心情枚举字符串")
    note: Optional[str] = Field(None, max_length=200)
    check_date: Optional[date] = None  # 默认今天


class MoodCheckinOut(BaseModel):
    id: int
    check_date: str
    mood_emoji: str
    note: Optional[str] = None
    created_at: str
