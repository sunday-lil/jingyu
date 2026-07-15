"""静屿 — 一键启动脚本（前后端一起起来）。

>>> 一句话用法：
    python start.py                # 后台启动（关掉终端服务也活着）
    python start.py fg             # 前台运行（关掉终端就停，调试用）
    python start.py --init-db      # 启动前重置数据库

--- 全部子命令：
    python start.py                # 后台启动（默认）
    python start.py start          # 同上
    python start.py stop           # 优雅停止
    python start.py restart        # 重启
    python start.py status         # 查看状态
    python start.py fg             # 前台运行（systemd / supervisor 用）

--- 架构说明（为什么不需要单独起前端）：
    本项目采用 **服务端渲染 (SSR)** —— FastAPI 同时承担三件事：
      1. 后端 API（/api/* 路由）
      2. 页面渲染（/、/login、/music 等，Jinja2 模板）
      3. 静态资源（/static/* 下的 CSS/JS/图片）
    所以 `start` 一下，前后端就一起起来了，没有 Vite/webpack 那种"双进程"。

--- 宝塔面板配置：
    项目类型  : Python
    启动命令  : cd /www/wwwroot/healing && python start.py
    停止命令  : cd /www/wwwroot/healing && python start.py stop
    端口      : 5000（与 .env 的 QI_PORT 一致）

环境变量（与 .env 一致）：
    QI_HOST, QI_PORT, QI_DEBUG, QI_SECRET_KEY, QI_DATABASE_URL,
    QI_LOG_DIR, QI_RUN_DIR
"""
from __future__ import annotations

import argparse
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

# 任何目录运行都能 import app.*
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

# Windows cmd/PowerShell 默认 GBK，emoji 会炸；强制 UTF-8 兜底
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

from app.config import settings  # noqa: E402

# 运行期目录（PID、日志）
RUN_DIR = Path(os.environ.get("QI_RUN_DIR", ROOT / "run"))
LOG_DIR = Path(os.environ.get("QI_LOG_DIR", ROOT / "logs"))
PID_FILE = RUN_DIR / "healing.pid"
LOG_FILE = LOG_DIR / "healing.log"


# ─────────────────────────────────────────────────────────────
# 工具
# ─────────────────────────────────────────────────────────────

def ensure_dirs() -> None:
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)


def read_pid() -> int | None:
    """读 PID 文件，返回进程号；不存在 / 失效返回 None。"""
    if not PID_FILE.exists():
        return None
    try:
        pid = int(PID_FILE.read_text().strip())
    except (ValueError, OSError):
        return None
    # 检查进程是否还活着
    if _pid_alive(pid):
        return pid
    # 僵尸 PID 文件，清理
    PID_FILE.unlink(missing_ok=True)
    return None


def _pid_alive(pid: int) -> bool:
    """跨平台检查进程是否还活着。"""
    if sys.platform == "win32":
        import ctypes
        kernel32 = ctypes.windll.kernel32
        PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
        STILL_ACTIVE = 259
        handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
        if handle == 0:
            return False
        try:
            exit_code = ctypes.c_ulong()
            ok = kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code))
            return bool(ok) and exit_code.value == STILL_ACTIVE
        finally:
            kernel32.CloseHandle(handle)
    else:
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            return False


def stop_process(graceful_timeout: float = 8.0) -> bool:
    """优雅停止。返回是否成功。

    - Linux/macOS：SIGTERM -> uvicorn 优雅退出 -> 超时 SIGKILL
    - Windows：DETACHED_PROCESS 启动的 python 不会响应温和信号，
              直接 taskkill /F（生产够用，强制清理连接）
    """
    pid = read_pid()
    if pid is None:
        print("[INFO] 未在运行")
        return True

    print(f"[STOP] 停止进程 {pid} ...")
    if sys.platform == "win32":
        result = subprocess.run(
            ["taskkill", "/F", "/PID", str(pid), "/T"],
            check=False, capture_output=True, text=True,
        )
        if "SUCCESS" in (result.stdout + result.stderr):
            PID_FILE.unlink(missing_ok=True)
            print("[OK] 已停止")
        else:
            print(f"   [WARN] taskkill 输出: {(result.stdout + result.stderr).strip()}")
        return True
    else:
        # Unix：SIGTERM -> 优雅退出
        try:
            os.kill(pid, signal.SIGTERM)
        except ProcessLookupError:
            PID_FILE.unlink(missing_ok=True)
            print("   进程已不存在")
            return True
        deadline = time.time() + graceful_timeout
        while time.time() < deadline:
            if not _pid_alive(pid):
                PID_FILE.unlink(missing_ok=True)
                print("[OK] 已停止")
                return True
            time.sleep(0.3)
        # 超时强杀
        print(f"   [TIMEOUT]  超过 {graceful_timeout}s 未退出，强杀")
        try:
            os.kill(pid, signal.SIGKILL)
        except OSError:
            pass
        PID_FILE.unlink(missing_ok=True)
        return True


def start_background() -> int:
    """后台启动子进程（脱离父进程），返回子进程 PID。"""
    ensure_dirs()
    existing = read_pid()
    if existing is not None:
        print(f"[INFO] 已在运行（PID {existing}），先 stop 再 start")
        return existing

    print(f"[START] 后台启动 -> http://{settings.host}:{settings.port}")
    print(f"   日志文件 : {LOG_FILE}")
    print(f"   PID 文件 : {PID_FILE}")

    # 后台子进程：stdout/stderr 重定向到日志，stdin 关掉
    log_fp = open(LOG_FILE, "ab", buffering=0)
    # 强制子进程用 UTF-8 输出（解决 Windows GBK 终端 + emoji 乱码）
    child_env = os.environ.copy()
    child_env["PYTHONIOENCODING"] = "utf-8"
    child_env["PYTHONUTF8"] = "1"
    kwargs: dict = dict(
        # 用 __file__ 引用自己，不写死文件名（万一用户重命名也能跑）
        args=[sys.executable, str(Path(__file__).resolve()), "fg"],
        stdout=log_fp,
        stderr=subprocess.STDOUT,
        stdin=subprocess.DEVNULL,
        cwd=str(ROOT),
        env=child_env,
    )
    if sys.platform == "win32":
        # 脱离父进程 + 新进程组 + 不弹黑窗
        DETACHED_PROCESS = 0x00000008
        CREATE_NEW_PROCESS_GROUP = 0x00000200
        kwargs["creationflags"] = DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP
        kwargs["close_fds"] = True
    else:
        kwargs["start_new_session"] = True

    proc = subprocess.Popen(**kwargs)

    # 立即写 PID，detach 后子进程不会再写
    PID_FILE.write_text(str(proc.pid))

    # 等几秒看进程是否还在
    for _ in range(20):
        time.sleep(0.2)
        if not _pid_alive(proc.pid):
            print("[FAIL] 启动后立即退出，请查看日志：")
            print(f"   tail -n 50 {LOG_FILE}" if sys.platform != "win32"
                  else f"   type {LOG_FILE}")
            PID_FILE.unlink(missing_ok=True)
            return -1

    print(f"[OK] 启动成功（PID {proc.pid}）")
    print(f"   首页     http://{settings.host}:{settings.port}")
    print(f"   API 文档 http://{settings.host}:{settings.port}/docs")
    return proc.pid


def run_foreground() -> None:
    """前台运行（systemd / supervisor / 调试用）。"""
    ensure_dirs()
    # 用 lifespan 钩子做建表 + 种子
    import uvicorn
    print(f"[HEAL] 静屿 — 前台启动 -> http://{settings.host}:{settings.port}")
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=False,
        log_level=settings.debug and "debug" or "info",
        access_log=True,
    )


def show_status() -> None:
    pid = read_pid()
    if pid is None:
        print("状态：未运行")
        sys.exit(3)
    print(f"状态：运行中（PID {pid}）")
    print(f"地址：http://{settings.host}:{settings.port}")
    print(f"日志：{LOG_FILE}")
    sys.exit(0)


def maybe_reset_db() -> None:
    db_file = Path(settings.database_url.replace("sqlite:///", ""))
    if db_file.exists():
        print(f"[WARN]  删除旧数据库 {db_file.name} ...")
        db_file.unlink()
    print("[SEED] 初始化数据库 + 种子数据 ...")
    from app.database import init_db, SessionLocal
    from app.seed import run_seed
    init_db()
    db = SessionLocal()
    try:
        run_seed(db)
    finally:
        db.close()
    print("[OK] 种子完成\n")


# ─────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="start.py",
        description="静屿 — 治愈系身心疗愈平台 一键启动（前后端一起）",
    )
    p.add_argument(
        "action",
        nargs="?",
        default="start",
        choices=["start", "stop", "restart", "status", "fg", "foreground"],
        help="操作：start 后台启动（默认）/ stop / restart / status / fg 前台",
    )
    p.add_argument(
        "--init-db",
        action="store_true",
        help="启动前重置数据库（ 会清空所有用户数据）",
    )
    return p.parse_args()


def main() -> None:
    args = parse_args()

    if args.init_db and args.action in ("start", "fg", "foreground", "restart"):
        maybe_reset_db()

    action = "fg" if args.action in ("fg", "foreground") else args.action

    if action == "start":
        start_background()
    elif action == "stop":
        sys.exit(0 if stop_process() else 1)
    elif action == "restart":
        stop_process()
        time.sleep(0.5)
        start_background()
    elif action == "status":
        show_status()
    elif action == "fg":
        run_foreground()


if __name__ == "__main__":
    main()
