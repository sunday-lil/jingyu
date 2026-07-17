"""Pydantic schemas。"""

from app.schemas.auth import RegisterIn, LoginIn, AuthOut
from app.schemas.diary import DiaryCreateIn, DiaryOut, EncouragementIn, EncouragementOut, DiaryPublicOut
from app.schemas.mood import MoodCheckinIn, MoodCheckinOut
from app.schemas.music import MusicOut, ListenCompleteIn
from app.schemas.energy import EnergyRecordOut, ExchangeIn, ExchangeOut
from app.schemas.admin import (
    DashboardStats, RecentActivity,
    UserListItem, UserListOut, UserDetailOut,
    ResetPasswordIn, CreateUserIn, AdjustEnergyIn,
    PyCacheCleanResult, SystemInfo,
)
from app.schemas.ai import (
    ChatMessage, AIChatIn, AIChatOut,
    AIEncouragementIn,
    AIHealingIn,
    AIMusicRecommendIn, AIMusicRecommendOut,
)

# Pydantic 2 + PEP 563 注解延迟求值时，部分 Optional/List 类型
# 在 FastAPI 0.139 响应模型包装时未完全重建。显式 rebuild 一次解决。
for _m in (
    RegisterIn, LoginIn, AuthOut,
    DiaryCreateIn, DiaryOut, EncouragementIn, EncouragementOut, DiaryPublicOut,
    MoodCheckinIn, MoodCheckinOut,
    MusicOut, ListenCompleteIn,
    EnergyRecordOut, ExchangeIn, ExchangeOut,
    DashboardStats, RecentActivity,
    UserListItem, UserListOut, UserDetailOut,
    ResetPasswordIn, CreateUserIn, AdjustEnergyIn,
    PyCacheCleanResult, SystemInfo,
    ChatMessage, AIChatIn, AIChatOut,
    AIEncouragementIn,
    AIHealingIn,
    AIMusicRecommendIn, AIMusicRecommendOut,
):
    try:
        _m.model_rebuild()
    except Exception:
        pass

__all__ = [
    "RegisterIn", "LoginIn", "AuthOut",
    "DiaryCreateIn", "DiaryOut", "DiaryPublicOut", "EncouragementIn", "EncouragementOut",
    "MoodCheckinIn", "MoodCheckinOut",
    "MusicOut", "ListenCompleteIn",
    "EnergyRecordOut", "ExchangeIn", "ExchangeOut",
    "DashboardStats", "RecentActivity",
    "UserListItem", "UserListOut", "UserDetailOut",
    "ResetPasswordIn", "CreateUserIn", "AdjustEnergyIn",
    "PyCacheCleanResult", "SystemInfo",
    "ChatMessage", "AIChatIn", "AIChatOut",
    "AIEncouragementIn",
    "AIHealingIn",
    "AIMusicRecommendIn", "AIMusicRecommendOut",
]
