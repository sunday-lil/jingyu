"""个人主页相关 Pydantic。"""

from typing import Optional

from pydantic import BaseModel, Field


class ProfileUpdateIn(BaseModel):
    """更新个人资料（头像 / 昵称）。"""
    nickname: Optional[str] = Field(None, min_length=2, max_length=20, description="新昵称")
    avatar: Optional[str] = Field(None, min_length=1, max_length=16, description="新头像 emoji")
