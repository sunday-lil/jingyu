"""加密工具。

- 密码哈希：passlib bcrypt
- 日记对称加密：Fernet（AES128-CBC + HMAC）
- 密钥派生：PBKDF2-HMAC-SHA256，从用户密码 + 盐派生 Fernet 密钥
- 盐生成：secrets.token_bytes(16)

⚠️ 安全边界：
- Fernet 密钥**不存数据库**，仅在用户登录后存于 request 上下文。
- 数据库泄露后，攻击者必须先拿到明文密码才能解密日记。
"""

from __future__ import annotations

import base64
import secrets
from typing import Optional

import bcrypt
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


from app.config import settings


# ─────────────────────────────────────────────────────────────
# 密码哈希
# ─────────────────────────────────────────────────────────────

def _truncate(password: str) -> bytes:
    """bcrypt 限制 72 字节；超过截断。"""
    return password.encode("utf-8")[:72]


def hash_password(password: str) -> str:
    """bcrypt 哈希密码。"""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(_truncate(password), salt).decode("ascii")


def verify_password(password: str, password_hash: str) -> bool:
    """校验密码。"""
    try:
        return bcrypt.checkpw(_truncate(password), password_hash.encode("ascii"))
    except Exception:
        return False


# ─────────────────────────────────────────────────────────────
# 盐生成
# ─────────────────────────────────────────────────────────────

def generate_salt() -> str:
    """生成 16 字节随机盐的 base64 字符串。"""
    return base64.b64encode(secrets.token_bytes(16)).decode("ascii")


# ─────────────────────────────────────────────────────────────
# 密钥派生
# ─────────────────────────────────────────────────────────────

def _derive_fernet_key(password: str, salt_b64: str) -> bytes:
    """从密码 + 盐派生 Fernet 密钥（44 字节 base64 字符串）。"""
    salt = base64.b64decode(salt_b64)
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=settings.encryption_iterations,
    )
    key = base64.urlsafe_b64encode(kdf.derive(password.encode("utf-8")))
    return key


# ─────────────────────────────────────────────────────────────
# 日记加解密
# ─────────────────────────────────────────────────────────────

def encrypt_diary(content: str, password: str, salt_b64: str) -> str:
    """用用户密码派生密钥，加密日记明文，返回密文（base64 字符串）。"""
    key = _derive_fernet_key(password, salt_b64)
    f = Fernet(key)
    return f.encrypt(content.encode("utf-8")).decode("ascii")


def decrypt_diary(token: str, password: str, salt_b64: str) -> Optional[str]:
    """解密日记密文。失败返回 None。"""
    try:
        key = _derive_fernet_key(password, salt_b64)
        f = Fernet(key)
        return f.decrypt(token.encode("ascii")).decode("utf-8")
    except (InvalidToken, ValueError, Exception):
        return None
