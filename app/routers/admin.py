"""秘密后台 API：所有端点都要求 ``is_admin=True``。

涵盖：
- /api/admin/me                          当前管理员信息
- /api/admin/stats                       仪表盘统计
- /api/admin/users                       用户列表（分页 + 搜索）
- /api/admin/users/{id}                  用户详情
- /api/admin/users/{id}/reset-password   重置用户密码
- /api/admin/users/{id}/adjust-energy    调整用户能量
- /api/admin/users/{id}/toggle-admin     切换用户管理员身份
- /api/admin/users/{id}/delete           删除用户
- /api/admin/users                       POST 代建用户
- /api/admin/system/info                 系统状态
- /api/admin/system/clear-pycaches       一键清 pycache
- /api/admin/logs                        tail 日志

⚠️ 端到端加密边界：管理员**永远**拿不到 diary 明文（content_encrypted 也不回传）。
"""

from __future__ import annotations

import logging
import os
import platform
import shutil
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func as sa_func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.deps import get_current_admin
from app.models.diary import Diary
from app.models.encouragement import Encouragement
from app.models.energy import EnergyRecord
from app.models.garden import GardenItem, ShopItem
from app.models.mood import MoodCheckin
from app.models.music import Music
from app.models.user import User
from app.schemas.admin import (
    AdjustEnergyIn, CreateUserIn, DashboardStats, PyCacheCleanResult,
    ResetPasswordIn, SystemInfo, UserDetailOut, UserListItem, UserListOut,
)
from app.utils.crypto import generate_salt, hash_password


router = APIRouter(prefix="/api/admin", tags=["admin"])
logger = logging.getLogger("qi.admin")


# ─────────────────────────────────────────────────────────────
# 当前管理员
# ─────────────────────────────────────────────────────────────

@router.get("/me")
def admin_me(admin: User = Depends(get_current_admin)):
    """当前管理员基本信息。"""
    return admin.to_public_dict()


# ─────────────────────────────────────────────────────────────
# 仪表盘
# ─────────────────────────────────────────────────────────────

@router.get("/stats", response_model=DashboardStats)
def dashboard_stats(db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    """仪表盘关键数字。"""
    return {
        "total_users": db.query(User).count(),
        "total_admins": db.query(User).filter(User.is_admin == True).count(),  # noqa: E712
        "total_diaries": db.query(Diary).count(),
        "total_public_diaries": db.query(Diary).filter(Diary.is_public == True).count(),  # noqa: E712
        "total_mood_checkins": db.query(MoodCheckin).count(),
        "total_energy_records": db.query(EnergyRecord).count(),
        "total_garden_items": db.query(GardenItem).count(),
    }


@router.get("/activity")
def recent_activity(
    limit: int = Query(8, ge=1, le=50),
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """最近活动：日记 / 心情 / 新增用户。"""
    diaries = (
        db.query(Diary, User.nickname)
        .join(User, User.id == Diary.user_id)
        .order_by(Diary.created_at.desc())
        .limit(limit).all()
    )
    moods = (
        db.query(MoodCheckin, User.nickname)
        .join(User, User.id == MoodCheckin.user_id)
        .order_by(MoodCheckin.created_at.desc())
        .limit(limit).all()
    )
    new_users = (
        db.query(User)
        .order_by(User.created_at.desc())
        .limit(limit).all()
    )
    return {
        "diaries": [
            {
                "id": d.id, "user_id": d.user_id, "nickname": nick,
                "is_public": d.is_public, "mood_type": d.mood_type,
                "created_at": d.created_at.isoformat() if d.created_at else None,
            }
            for d, nick in diaries
        ],
        "mood_checkins": [
            {
                "id": m.id, "user_id": m.user_id, "nickname": nick,
                "check_date": m.check_date.isoformat() if m.check_date else None,
                "mood_emoji": m.mood_emoji, "note": m.note,
                "created_at": m.created_at.isoformat() if m.created_at else None,
            }
            for m, nick in moods
        ],
        "new_users": [u.to_public_dict() for u in new_users],
    }


# ─────────────────────────────────────────────────────────────
# 用户管理
# ─────────────────────────────────────────────────────────────

def _user_list_item(db: Session, u: User) -> dict:
    """组装列表项（含聚合统计）。"""
    diary_count = db.query(sa_func.count(Diary.id)).filter(Diary.user_id == u.id).scalar() or 0
    public_count = db.query(sa_func.count(Diary.id)).filter(
        Diary.user_id == u.id, Diary.is_public == True  # noqa: E712
    ).scalar() or 0
    mood_count = db.query(sa_func.count(MoodCheckin.id)).filter(MoodCheckin.user_id == u.id).scalar() or 0
    last_diary = db.query(Diary.created_at).filter(Diary.user_id == u.id).order_by(
        Diary.created_at.desc()
    ).first()
    last_mood = db.query(MoodCheckin.check_date).filter(MoodCheckin.user_id == u.id).order_by(
        MoodCheckin.check_date.desc()
    ).first()
    return {
        "id": u.id,
        "nickname": u.nickname,
        "total_energy": u.total_energy,
        "is_admin": u.is_admin,
        "created_at": u.created_at.isoformat() if u.created_at else None,
        "diary_count": diary_count,
        "public_diary_count": public_count,
        "mood_count": mood_count,
        "last_diary_at": last_diary[0].isoformat() if last_diary and last_diary[0] else None,
        "last_mood_at": last_mood[0].isoformat() if last_mood and last_mood[0] else None,
    }


@router.get("/users", response_model=UserListOut)
def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    q: str = Query("", description="按昵称模糊搜索"),
    admin_only: bool = Query(False),
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """分页列出用户。"""
    base = db.query(User)
    if q:
        base = base.filter(User.nickname.contains(q))
    if admin_only:
        base = base.filter(User.is_admin == True)  # noqa: E712
    total = base.count()
    users = base.order_by(User.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return {
        "items": [_user_list_item(db, u) for u in users],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/users/{user_id}")
def get_user_detail(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """用户详情。"""
    u = db.get(User, user_id)
    if u is None:
        raise HTTPException(status_code=404, detail="用户不存在")

    diary_count = db.query(sa_func.count(Diary.id)).filter(Diary.user_id == u.id).scalar() or 0
    public_count = db.query(sa_func.count(Diary.id)).filter(
        Diary.user_id == u.id, Diary.is_public == True  # noqa: E712
    ).scalar() or 0
    mood_count = db.query(sa_func.count(MoodCheckin.id)).filter(MoodCheckin.user_id == u.id).scalar() or 0
    energy_in = db.query(sa_func.coalesce(sa_func.sum(EnergyRecord.amount), 0)).filter(
        EnergyRecord.user_id == u.id, EnergyRecord.amount > 0
    ).scalar() or 0
    energy_out = db.query(sa_func.coalesce(sa_func.sum(EnergyRecord.amount), 0)).filter(
        EnergyRecord.user_id == u.id, EnergyRecord.amount < 0
    ).scalar() or 0
    garden_count = db.query(sa_func.count(GardenItem.id)).filter(GardenItem.user_id == u.id).scalar() or 0

    recent_diaries = (
        db.query(Diary)
        .filter(Diary.user_id == u.id)
        .order_by(Diary.created_at.desc())
        .limit(8).all()
    )
    recent_moods = (
        db.query(MoodCheckin)
        .filter(MoodCheckin.user_id == u.id)
        .order_by(MoodCheckin.check_date.desc())
        .limit(8).all()
    )
    recent_energy = (
        db.query(EnergyRecord)
        .filter(EnergyRecord.user_id == u.id)
        .order_by(EnergyRecord.created_at.desc())
        .limit(8).all()
    )

    ph = u.password_hash or ""
    ph_preview = f"{ph[:4]}...{ph[-4:]}" if len(ph) > 12 else "(空)"

    return {
        "id": u.id,
        "nickname": u.nickname,
        "total_energy": u.total_energy,
        "is_admin": u.is_admin,
        "created_at": u.created_at.isoformat() if u.created_at else None,
        "encryption_salt_preview": (u.encryption_salt[:8] + "..." + u.encryption_salt[-4:]) if u.encryption_salt else "",
        "password_hash_preview": ph_preview,
        "diary_count": diary_count,
        "public_diary_count": public_count,
        "mood_count": mood_count,
        "energy_total_in": energy_in,
        "energy_total_out": abs(energy_out),
        "garden_item_count": garden_count,
        "recent_diaries": [
            {
                "id": d.id, "created_at": d.created_at.isoformat() if d.created_at else None,
                "is_public": d.is_public, "mood_type": d.mood_type,
            }
            for d in recent_diaries
        ],
        "recent_moods": [
            {
                "id": m.id, "check_date": m.check_date.isoformat() if m.check_date else None,
                "mood_emoji": m.mood_emoji, "note": m.note,
            }
            for m in recent_moods
        ],
        "recent_energy": [
            {
                "id": e.id, "created_at": e.created_at.isoformat() if e.created_at else None,
                "amount": e.amount, "source": e.source, "note": e.note,
            }
            for e in recent_energy
        ],
    }


@router.post("/users", status_code=status.HTTP_201_CREATED)
def create_user(
    body: CreateUserIn,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """管理员代建用户。"""
    if db.query(User).filter(User.nickname == body.nickname).first():
        raise HTTPException(status_code=400, detail="昵称已存在")
    u = User(
        nickname=body.nickname,
        password_hash=hash_password(body.password),
        encryption_salt=generate_salt(),
        total_energy=0,
        is_admin=body.is_admin,
    )
    db.add(u)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="创建失败")
    db.refresh(u)
    logger.info("[ADMIN] %s 代建用户 %s (id=%d, admin=%s)",
                admin.nickname, u.nickname, u.id, u.is_admin)
    return u.to_public_dict()


@router.post("/users/{user_id}/reset-password")
def reset_user_password(
    user_id: int,
    body: ResetPasswordIn,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """重置用户密码。

    ⚠️ 端到端加密警告：用户用新密码登录后，PBKDF2 派生的 Fernet 密钥会变化，
    旧日记将无法在本机解密（除非用户记得旧密码）。
    加密盐 encryption_salt 不会被重置，所以同一密码的密钥可复用。
    """
    u = db.get(User, user_id)
    if u is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    u.password_hash = hash_password(body.new_password)
    db.add(u)
    db.commit()
    logger.warning("[ADMIN] %s 重置了用户 %s (id=%d) 的密码",
                   admin.nickname, u.nickname, u.id)
    return {
        "ok": True,
        "user_id": u.id,
        "nickname": u.nickname,
        "warning": "新密码已生效。旧密码派生的日记加密密钥会失效，"
                   "用户用新密码登录后看不到旧日记。",
    }


@router.post("/users/{user_id}/adjust-energy")
def adjust_user_energy(
    user_id: int,
    body: AdjustEnergyIn,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """调整用户能量（+ delta）。写流水。"""
    u = db.get(User, user_id)
    if u is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    if body.delta == 0:
        raise HTTPException(status_code=400, detail="delta 不能为 0")
    # 显式 UPDATE（见 HANDOFF §6.7）
    db.query(User).filter(User.id == u.id).update(
        {User.total_energy: User.total_energy + body.delta},
        synchronize_session=False,
    )
    note = body.note or f"管理员 {admin.nickname} {'授予' if body.delta > 0 else '扣除'}"
    rec = EnergyRecord(user_id=u.id, amount=body.delta, source="admin_adjust", note=note)
    db.add(rec)
    db.commit()
    # 重新读 total_energy
    db.refresh(u)
    logger.info("[ADMIN] %s 调整用户 %s (id=%d) 能量 %+d → %d",
                admin.nickname, u.nickname, u.id, body.delta, u.total_energy)
    return {
        "ok": True,
        "user_id": u.id,
        "new_total_energy": u.total_energy,
        "delta": body.delta,
    }


@router.post("/users/{user_id}/toggle-admin")
def toggle_user_admin(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """切换用户的 is_admin 标志。"""
    u = db.get(User, user_id)
    if u is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    if u.id == admin.id:
        raise HTTPException(status_code=400, detail="不能修改自己的管理员身份")
    u.is_admin = not u.is_admin
    db.add(u)
    db.commit()
    db.refresh(u)
    logger.info("[ADMIN] %s 切换用户 %s (id=%d) 的管理员身份 → %s",
                admin.nickname, u.nickname, u.id, u.is_admin)
    return {"ok": True, "user_id": u.id, "is_admin": u.is_admin}


@router.delete("/users/{user_id}", status_code=status.HTTP_200_OK)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """硬删除用户（级联删除其所有日记/打卡/能量/花园记录）。

    ⚠️ 端到端加密：删除的是数据库行，密文一并消失。
    """
    u = db.get(User, user_id)
    if u is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    if u.id == admin.id:
        raise HTTPException(status_code=400, detail="不能删除自己")
    nickname = u.nickname
    db.delete(u)
    db.commit()
    logger.warning("[ADMIN] %s 删除了用户 %s (id=%d)", admin.nickname, nickname, user_id)
    return {"ok": True, "deleted_user_id": user_id, "deleted_nickname": nickname}


# ─────────────────────────────────────────────────────────────
# 系统维护
# ─────────────────────────────────────────────────────────────

def _scan_pycaches(root: Path) -> tuple[int, int, list[str]]:
    """递归扫描 __pycache__ 目录和散落的 .pyc 文件。返回 (目录数, 文件数, 路径列表)。"""
    dirs = 0
    files = 0
    paths: list[str] = []
    if not root.exists():
        return 0, 0, []
    for dirpath, dirnames, filenames in os.walk(root):
        # 跳过虚拟环境内部（一般不清理 venv）
        # 但默认清理，避免磁盘膨胀
        for dn in list(dirnames):
            full = Path(dirpath) / dn
            if dn == "__pycache__":
                # 统计文件
                try:
                    for _p, _dns, _fns in os.walk(full):
                        files += len(_fns)
                    paths.append(str(full))
                    dirs += 1
                except OSError:
                    pass
        for fn in filenames:
            if fn.endswith((".pyc", ".pyo")):
                paths.append(str(Path(dirpath) / fn))
                files += 1
    return dirs, files, paths


def _path_size(path: Path) -> int:
    """文件 → 文件大小；目录 → 递归求和。"""
    if path.is_file():
        try:
            return path.stat().st_size
        except OSError:
            return 0
    if path.is_dir():
        total = 0
        for _p, _dns, _fns in os.walk(path):
            for fn in _fns:
                try:
                    total += (Path(_p) / fn).stat().st_size
                except OSError:
                    pass
        return total
    return 0


@router.get("/system/info", response_model=SystemInfo)
def system_info(admin: User = Depends(get_current_admin)):
    """系统状态：DB / 日志 / pycache 大小等。"""
    db_path = Path(settings.database_url.replace("sqlite:///", ""))
    log_path = settings.log_dir / "healing.log"
    pyc_dirs, pyc_files, _ = _scan_pycaches(settings.base_dir)
    # 算 pycache 总体积
    pyc_bytes = 0
    for _p, _dns, _fns in os.walk(settings.base_dir):
        for fn in _fns:
            if fn.endswith((".pyc", ".pyo")):
                try:
                    pyc_bytes += (Path(_p) / fn).stat().st_size
                except OSError:
                    pass
    return {
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "db_path": str(db_path),
        "db_size_bytes": _path_size(db_path) if db_path.exists() else 0,
        "log_path": str(log_path),
        "log_size_bytes": _path_size(log_path) if log_path.exists() else 0,
        "pycache_dirs": pyc_dirs,
        "pycache_size_bytes": pyc_bytes,
        "base_dir": str(settings.base_dir),
    }


@router.post("/system/clear-pycaches", response_model=PyCacheCleanResult)
def clear_pycaches(
    include_venv: bool = Query(False, description="是否也清理 venv/ 下的缓存"),
    admin: User = Depends(get_current_admin),
):
    """一键清理所有 __pycache__ 目录和散落的 .pyc/.pyo 文件。

    默认**不**清理 venv 内部（避免误删正在用的包）。
    """
    started = time.time()
    root = settings.base_dir
    # 第一步：扫描
    dirs_removed = 0
    files_removed = 0
    bytes_freed = 0
    scanned_paths: list[str] = []

    for dirpath, dirnames, filenames in os.walk(root):
        # 跳过 venv
        if not include_venv and ("venv" in dirpath or ".venv" in dirpath or "node_modules" in dirpath):
            dirnames[:] = []
            continue
        # 删 __pycache__
        for dn in list(dirnames):
            if dn == "__pycache__":
                full = Path(dirpath) / dn
                size = _path_size(full)
                try:
                    shutil.rmtree(full, ignore_errors=True)
                    dirs_removed += 1
                    bytes_freed += size
                    scanned_paths.append(str(full))
                except Exception as e:
                    logger.warning("[ADMIN] 删除 %s 失败: %s", full, e)
                dirnames.remove(dn)
        # 删散落的 .pyc / .pyo
        for fn in filenames:
            if fn.endswith((".pyc", ".pyo")):
                full = Path(dirpath) / fn
                try:
                    size = full.stat().st_size
                    full.unlink(missing_ok=True)
                    files_removed += 1
                    bytes_freed += size
                except Exception as e:
                    logger.warning("[ADMIN] 删除 %s 失败: %s", full, e)

    duration_ms = int((time.time() - started) * 1000)
    logger.warning("[ADMIN] %s 清 pycache: %d 目录 + %d 文件 = %d 字节 (%d ms)",
                   admin.nickname, dirs_removed, files_removed, bytes_freed, duration_ms)
    return {
        "dirs_removed": dirs_removed,
        "files_removed": files_removed,
        "bytes_freed": bytes_freed,
        "duration_ms": duration_ms,
        "scanned_paths": scanned_paths[:200],  # 最多返 200 条防爆
    }


# ─────────────────────────────────────────────────────────────
# 日志查看
# ─────────────────────────────────────────────────────────────

@router.get("/logs")
def tail_logs(
    lines: int = Query(200, ge=10, le=2000),
    level: str = Query("all", description="all | INFO | WARNING | ERROR | DEBUG"),
    db: Session = Depends(None),
    admin: User = Depends(get_current_admin),
):
    """tail 最近 N 行日志。"""
    log_path = settings.log_dir / "healing.log"
    if not log_path.exists():
        return {"exists": False, "path": str(log_path), "lines": []}
    try:
        # 简易 tail：读整个文件，截最后 N 行
        # 文件大于 5MB 时只读后 2MB
        max_bytes = 2 * 1024 * 1024
        size = log_path.stat().st_size
        with open(log_path, "rb") as f:
            if size > max_bytes:
                f.seek(size - max_bytes)
                # 跳过第一行（可能残缺）
                f.readline()
            data = f.read().decode("utf-8", errors="replace")
        all_lines = data.splitlines()[-lines:]
        # 按 level 过滤
        if level and level.upper() != "ALL":
            lvl = level.upper()
            all_lines = [ln for ln in all_lines if f"[{lvl}]" in ln]
        return {
            "exists": True,
            "path": str(log_path),
            "size_bytes": size,
            "total_lines": len(all_lines),
            "lines": all_lines,
        }
    except Exception as e:
        logger.exception("[ADMIN] 读日志失败: %s", e)
        raise HTTPException(status_code=500, detail=f"读日志失败: {e}")
