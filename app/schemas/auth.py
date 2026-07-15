"""鉴权相关 Pydantic。"""

from pydantic import BaseModel, Field


class RegisterIn(BaseModel):
    nickname: str = Field(..., min_length=2, max_length=20, description="昵称")
    password: str = Field(..., min_length=6, max_length=64, description="密码")


class LoginIn(BaseModel):
    nickname: str = Field(..., min_length=2, max_length=20)
    password: str = Field(..., min_length=6, max_length=64)


class AuthOut(BaseModel):
    id: int
    nickname: str
    total_energy: int
    is_admin: bool = False
    created_at: str
