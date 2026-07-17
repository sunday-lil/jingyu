"""应用配置。环境变量优先，缺失则用合理默认值。"""

from __future__ import annotations

import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """应用配置。从 .env 加载，无 .env 时使用默认值。"""

    # 安全
    secret_key: str = "dev-secret-key-please-change-in-production-12345"
    encryption_iterations: int = 200_000

    # 数据库
    database_url: str = f"sqlite:///{BASE_DIR / 'data' / 'healing.db'}"

    # 服务
    host: str = "127.0.0.1"
    port: int = 5000
    debug: bool = True

    # 会话
    session_cookie_name: str = "qi_session"
    session_max_age_seconds: int = 60 * 60 * 24 * 30  # 30 天

    # 后台管理员
    # 首次启动会扫描 users 表，若没有 is_admin=True 的用户，则按下面规则创建首个管理员：
    #   nickname = admin_username（默认 "admin"）
    #   password = admin_password（留空则随机生成一个，写入日志）
    admin_username: str = "admin"
    admin_password: str = ""  # 留空 → 随机生成
    admin_path_prefix: str = "/admin"  # 后台 URL 前缀，刻意不显眼

    # AI 接入（NVIDIA NIM API，OpenAI 兼容）
    # 留空 → AI 功能禁用，端点返回"AI 暂时不在"友好提示
    nvidia_api_key: str = ""
    ai_model: str = "nvidia/llama-3.1-nemotron-70b-instruct"
    ai_base_url: str = "https://integrate.api.nvidia.com/v1"

    # 路径
    base_dir: Path = BASE_DIR
    static_dir: Path = BASE_DIR / "static"
    templates_dir: Path = BASE_DIR / "templates"
    audio_dir: Path = BASE_DIR / "static" / "audio"
    data_dir: Path = BASE_DIR / "data"
    log_dir: Path = BASE_DIR / "logs"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()

# 启动时确保数据目录存在
settings.data_dir.mkdir(parents=True, exist_ok=True)
settings.audio_dir.mkdir(parents=True, exist_ok=True)
settings.log_dir.mkdir(parents=True, exist_ok=True)
