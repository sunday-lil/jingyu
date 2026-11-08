"""鉴权相关 Pydantic。"""

from pydantic import BaseModel, Field


class RegisterIn(BaseModel):
    nickname: str = Field(..., min_length=2, max_length=20, description="昵称")
    password: str = Field(..., min_length=6, max_length=64, description="密码")


class LoginIn(BaseModel):
    nickname: str = Field(..., min_length=2, max_length=20)
    password: str = Field(..., min_length=6, max_length=64)


class PasswordResetIn(BaseModel):
    nickname: str = Field(..., min_length=2, max_length=20)
    recovery_code: str = Field(..., min_length=6, max_length=20)
    new_password: str = Field(..., min_length=6, max_length=64)


class AuthOut(BaseModel):
    id: int
    nickname: str
    avatar: str = "🙂"
    total_energy: int
    leaves: int = 0
    is_admin: bool = False
    created_at: str
    # 只在新注册 / 老用户首次登录且尚未生成时返回一次；平时为 None
    recovery_code: str | None = None
