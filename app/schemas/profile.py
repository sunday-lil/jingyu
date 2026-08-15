"""个人主页相关 Pydantic。"""

from typing import Optional

from pydantic import BaseModel, Field


class ProfileUpdateIn(BaseModel):
    """更新个人资料（头像 / 昵称）。

    avatar 支持 emoji（1-16 字符）或上传图片后的 URL 路径（最长 255 字符）。
    """
    nickname: Optional[str] = Field(None, min_length=2, max_length=20, description="新昵称")
    avatar: Optional[str] = Field(None, min_length=1, max_length=255, description="新头像 emoji 或图片 URL")
