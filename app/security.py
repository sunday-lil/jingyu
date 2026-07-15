"""会话与安全工具。

- 使用 ``itsdangerous.URLSafeTimedSerializer`` 签名 user_id 写入 cookie。
- 不使用 JWT（无状态），使用有状态 session（更简单，签名防伪造）。
- 退出登录 = 删除 cookie。
"""

from __future__ import annotations

from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

from app.config import settings


_serializer = URLSafeTimedSerializer(settings.secret_key, salt="qi-session-v1")


def make_session_token(user_id: int) -> str:
    """生成签名后的 session token（写入 cookie 的值）。"""
    return _serializer.dumps({"uid": user_id})


def parse_session_token(token: str) -> int | None:
    """解析 session token。返回 user_id；签名错误或过期返回 None。"""
    try:
        data = _serializer.loads(token, max_age=settings.session_max_age_seconds)
        return int(data.get("uid"))
    except (BadSignature, SignatureExpired, ValueError, TypeError):
        return None
