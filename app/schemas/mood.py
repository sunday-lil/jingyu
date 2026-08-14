"""心情打卡相关 Pydantic。"""

from datetime import date
from typing import Optional, List
from pydantic import BaseModel, Field


class MoodCheckinIn(BaseModel):
    mood_emoji: str = Field(..., description="心情枚举字符串")
    note: Optional[str] = Field(None, max_length=200)
    check_date: Optional[date] = None  # 默认今天


class MoodBatchIn(BaseModel):
    """批量打卡（一次选多个心情）。"""
    mood_emojis: List[str] = Field(..., description="心情枚举字符串列表")
    note: Optional[str] = Field(None, max_length=200)


class MoodCheckinOut(BaseModel):
    id: int
    check_date: str
    mood_emoji: str
    note: Optional[str] = None
    created_at: str
    # v2.4.2：附加资源变动信息（前端用于 toast + 更新余额）
    new_total_energy: Optional[int] = None
    new_leaves: Optional[int] = None
    leaves_balance: Optional[int] = None
    new_badges: Optional[List[dict]] = None
