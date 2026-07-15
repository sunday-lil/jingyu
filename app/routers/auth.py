"""鉴权 API：注册 / 登录 / 注销 / 当前用户。"""

from __future__ import annotations

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
from app.schemas.auth import RegisterIn, LoginIn, AuthOut
from app.utils.crypto import hash_password, verify_password, generate_salt


router = APIRouter(prefix="/api/auth", tags=["auth"])


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
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="注册失败，请重试")
    db.refresh(user)

    set_session_cookie(response, user.id)
    return user.to_public_dict()


@router.post("/login", response_model=AuthOut)
def login(body: LoginIn, response: Response, db: Session = Depends(get_db)):
    """登录。"""
    user = db.query(User).filter(User.nickname == body.nickname).first()
    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="昵称或密码不对")
    set_session_cookie(response, user.id)
    return user.to_public_dict()


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
