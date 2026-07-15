"""秘密后台 Pydantic schemas。

⚠️ 注意：不要在 schema 里给管理员看 diary 明文（端到端加密保护），
也尽量少暴露 password_hash（只回传首尾 6 位用于辨认）。
"""

from pydantic import BaseModel, Field


# ─────────────────────────────────────────────────────────────
# 仪表盘
# ─────────────────────────────────────────────────────────────

class DashboardStats(BaseModel):
    """首页仪表盘的关键数字。"""
    total_users: int
    total_admins: int
    total_diaries: int
    total_public_diaries: int
    total_mood_checkins: int
    total_energy_records: int
    total_garden_items: int


class RecentActivity(BaseModel):
    """最近活动（时间倒序）。"""
    diaries: list[dict]    # [{id, user_id, nickname, is_public, created_at, mood_type}]
    mood_checkins: list[dict]
    new_users: list[dict]


# ─────────────────────────────────────────────────────────────
# 用户管理
# ─────────────────────────────────────────────────────────────

class UserListItem(BaseModel):
    """用户列表项（不含敏感字段）。"""
    id: int
    nickname: str
    total_energy: int
    is_admin: bool
    created_at: str
    diary_count: int
    public_diary_count: int
    mood_count: int
    last_diary_at: str | None = None
    last_mood_at: str | None = None


class UserListOut(BaseModel):
    """用户列表分页响应。"""
    items: list[UserListItem]
    total: int
    page: int
    page_size: int


class UserDetailOut(BaseModel):
    """用户详情。"""
    id: int
    nickname: str
    total_energy: int
    is_admin: bool
    created_at: str
    # 只显示加密盐的摘要，便于管理员判断『密钥是否仍可用』
    encryption_salt_preview: str
    password_hash_preview: str   # 首 4 + "..." + 尾 4，仅供辨识
    # 统计
    diary_count: int
    public_diary_count: int
    mood_count: int
    energy_total_in: int
    energy_total_out: int
    garden_item_count: int
    # 最近活动
    recent_diaries: list[dict]      # [{id, created_at, is_public, mood_type}]
    recent_moods: list[dict]        # [{id, check_date, mood_emoji, note}]
    recent_energy: list[dict]       # [{id, created_at, amount, source, note}]


# ─────────────────────────────────────────────────────────────
# 操作入参
# ─────────────────────────────────────────────────────────────

class ResetPasswordIn(BaseModel):
    """管理员重置某用户的密码。"""
    new_password: str = Field(..., min_length=6, max_length=64, description="新密码")


class CreateUserIn(BaseModel):
    """管理员代建用户。"""
    nickname: str = Field(..., min_length=2, max_length=20)
    password: str = Field(..., min_length=6, max_length=64)
    is_admin: bool = False


class AdjustEnergyIn(BaseModel):
    """管理员调整用户能量（+/-，写流水）。"""
    delta: int = Field(..., description="正数加，负数减")
    note: str = Field("", max_length=200, description="原因说明（写入流水）")


# ─────────────────────────────────────────────────────────────
# 系统维护
# ─────────────────────────────────────────────────────────────

class PyCacheCleanResult(BaseModel):
    """清 pycache 后的统计。"""
    dirs_removed: int
    files_removed: int
    bytes_freed: int
    duration_ms: int
    scanned_paths: list[str]


class SystemInfo(BaseModel):
    """系统信息（仪表盘用）。"""
    python_version: str
    platform: str
    db_path: str
    db_size_bytes: int
    log_path: str
    log_size_bytes: int
    pycache_dirs: int
    pycache_size_bytes: int
    base_dir: str
