"""身心调理 Pydantic 模型。"""

from typing import Optional

from pydantic import BaseModel, Field


class TherapyRecommendIn(BaseModel):
    problem: str = Field(..., min_length=1, max_length=500, description="用户描述的身体/情绪状态")
    tags: Optional[list[str]] = Field(None, max_length=8, description="可选的快捷标签")


class BaduanjinCheckinIn(BaseModel):
    move_key: str = Field("general", max_length=50, description="跟练的招式 key")


class TherapyInterestIn(BaseModel):
    product_key: str = Field(..., min_length=1, max_length=50)
