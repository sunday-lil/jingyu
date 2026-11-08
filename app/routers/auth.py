"""鉴权 API：注册 / 登录 / 注销 / 当前用户。"""

from __future__ import annotations

import secrets

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import (
    get_current_user_optional,
    set_session_cookie,
    clear_session_cookie,
)
from app.models.user import User
from app.schemas.auth import RegisterIn, LoginIn, PasswordResetIn, AuthOut
from app.utils.crypto import hash_password, verify_password, generate_salt


router = APIRouter(prefix="/api/auth", tags=["auth"])


def _new_recovery_code() -> str:
    """生成 8 位大写恢复码（去掉易混字符）。"""
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    return "".join(secrets.choice(alphabet) for _ in range(8))


def _set_recovery_code(user: User) -> str:
    code = _new_recovery_code()
    user.recovery_code_hash = hash_password(code)
    return code


@router.post("/register", response_model=AuthOut, status_code=status.HTTP_201_CREATED)
def register(body: RegisterIn, response: Response, db: Session = Depends(get_db)):
    """注册：新用户。

    - nickname 唯一
    - 密码 bcrypt 哈希
    - 生成 encryption_salt（用于日记加密），存入数据库
    - 写 session cookie
    """
    if db.query(User).filter(User.nickname == body.nickname).first():
        raise HTTPException(status_code=400, detail="这个昵称已经有人用了")

    user = User(
        nickname=body.nickname,
        password_hash=hash_password(body.password),
        encryption_salt=generate_salt(),
        total_energy=0,
    )
    recovery_code = _set_recovery_code(user)
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="注册失败，请重试")
    db.refresh(user)

    set_session_cookie(response, user.id)
    data = user.to_public_dict()
    data["recovery_code"] = recovery_code
    return data


@router.post("/login", response_model=AuthOut)
def login(body: LoginIn, response: Response, db: Session = Depends(get_db)):
    """登录。"""
    user = db.query(User).filter(User.nickname == body.nickname).first()
    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="昵称或密码不对")
    set_session_cookie(response, user.id)
    data = user.to_public_dict()
    # 老用户第一次登录且还没有恢复码时，补发一次并提示保存
    if not user.recovery_code_hash:
        data["recovery_code"] = _set_recovery_code(user)
        db.commit()
    return data


@router.post("/reset-password")
def reset_password(body: PasswordResetIn, db: Session = Depends(get_db)):
    """用恢复码重置密码。

    恢复码在注册时 / 老用户首次登录时显示一次；忘记密码且没有恢复码时，
    由管理员在后台用户详情中重置。
    """
    user = db.query(User).filter(User.nickname == body.nickname).first()
    code = body.recovery_code.strip().upper().replace("-", "").replace(" ", "")
    if (
        user is None
        or not user.recovery_code_hash
        or not verify_password(code, user.recovery_code_hash)
    ):
        raise HTTPException(
            status_code=400,
            detail="昵称或恢复码不对；如果还没有恢复码，请联系岛主重置密码",
        )
    user.password_hash = hash_password(body.new_password)
    # 用过的恢复码作废；下次登录会补发一枚新的
    user.recovery_code_hash = None
    db.commit()
    return {"success": True}


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(response: Response):
    """注销：清 cookie。"""
    clear_session_cookie(response)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/me", response_model=AuthOut)
def me(user: User = Depends(get_current_user_optional)):
    """当前用户信息（未登录 401）。"""
    if user is None:
        raise HTTPException(status_code=401, detail="未登录")
    return user.to_public_dict()
