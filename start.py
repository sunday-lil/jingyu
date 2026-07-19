"""静屿 — 一键启动脚本（前后端一起起来）。

>>> 一句话用法：
    python start.py                # 后台启动：dist 已构建走生产，未构建自动起 Vite
    python start.py fg             # 前台运行（关掉终端就停，调试用）
    python start.py --init-db      # 启动前重置数据库

--- 全部子命令：
    python start.py                # 后台启动（默认，自动检测 dist）
    python start.py start          # 同上
    python start.py stop           # 优雅停止（同时停 FastAPI + Vite）
    python start.py restart        # 重启
    python start.py status         # 查看状态
    python start.py fg             # 前台运行（systemd / supervisor 用）
    python start.py build          # 构建前端到 static/dist/

--- 架构说明（v2.0 Vue 3 重构后）：
    前端由 Vue 3 SPA 接管，FastAPI 改为纯 API 后端 + SPA fallback：
      1. 后端 API（/api/* 路由）
      2. SPA fallback：dist 已构建 → 返回 static/dist/index.html
                      dist 未构建 → 转发到 Vite dev server :5173
      3. 静态资源（/static/* 下的 CSS/JS/图片 + /static/dist/* 前端构建产物）

    start.py 自动检测：
      - dist 已构建（生产模式）：只起 FastAPI :5000
      - dist 未构建（开发模式）：同时起 FastAPI :5000 + Vite :5173，用户访问 :5000 即可

--- 宝塔面板配置（生产）：
    项目类型  : Python
    启动命令  : cd /www/wwwroot/healing && python start.py
    停止命令  : cd /www/wwwroot/healing && python start.py stop
    端口      : 5000（与 .env 的 QI_PORT 一致）
    前端构建  : cd frontend && npm install && npm run build（部署时一次性）

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
PID_FILE = RUN_DIR / "healing.pid"           # FastAPI PID
VITE_PID_FILE = RUN_DIR / "vite.pid"         # Vite dev server PID
LOG_FILE = LOG_DIR / "healing.log"
VITE_LOG_FILE = LOG_DIR / "vite.log"
FRONTEND_DIR = ROOT / "frontend"
DIST_INDEX = ROOT / "static" / "dist" / "index.html"


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
    """优雅停止 FastAPI + Vite dev server。返回是否成功。

    - Linux/macOS：SIGTERM -> uvicorn 优雅退出 -> 超时 SIGKILL
    - Windows：DETACHED_PROCESS 启动的 python 不会响应温和信号，
              直接 taskkill /F（生产够用，强制清理连接）
    """
    # 先停 Vite（如果存在）
    vite_pid = read_vite_pid()
    if vite_pid is not None:
        print(f"[STOP] 停止 Vite 进程 {vite_pid} ...")
        _kill_pid(vite_pid, graceful_timeout)
        VITE_PID_FILE.unlink(missing_ok=True)

    # 再停 FastAPI
    pid = read_pid()
    if pid is None and vite_pid is None:
        print("[INFO] 未在运行")
        return True
    if pid is None:
        print("[OK] Vite 已停止，FastAPI 未在运行")
        return True

    print(f"[STOP] 停止 FastAPI 进程 {pid} ...")
    _kill_pid(pid, graceful_timeout)
    PID_FILE.unlink(missing_ok=True)
    print("[OK] 已全部停止")
    return True


def _kill_pid(pid: int, graceful_timeout: float = 8.0) -> None:
    """杀掉指定 PID（跨平台）。"""
    if sys.platform == "win32":
        result = subprocess.run(
            ["taskkill", "/F", "/PID", str(pid), "/T"],
            check=False, capture_output=True, text=True,
        )
        if "SUCCESS" not in (result.stdout + result.stderr):
            print(f"   [WARN] taskkill 输出: {(result.stdout + result.stderr).strip()}")
    else:
        try:
            os.kill(pid, signal.SIGTERM)
        except ProcessLookupError:
            return
        deadline = time.time() + graceful_timeout
        while time.time() < deadline:
            if not _pid_alive(pid):
                return
            time.sleep(0.3)
        try:
            os.kill(pid, signal.SIGKILL)
        except OSError:
            pass


def read_vite_pid() -> int | None:
    """读 Vite PID 文件。"""
    if not VITE_PID_FILE.exists():
        return None
    try:
        pid = int(VITE_PID_FILE.read_text().strip())
    except (ValueError, OSError):
        return None
    if _pid_alive(pid):
        return pid
    VITE_PID_FILE.unlink(missing_ok=True)
    return None


def is_dist_built() -> bool:
    """检测前端是否已构建（static/dist/index.html 存在）。"""
    return DIST_INDEX.exists()


def start_vite_background() -> int | None:
    """后台启动 Vite dev server（仅开发模式用）。

    返回 Vite 进程 PID，失败返回 None。
    """
    if not (FRONTEND_DIR / "node_modules").exists():
        print("[WARN] frontend/node_modules 不存在，跳过 Vite 启动")
        print("       请先执行：cd frontend && npm install")
        return None

    print(f"[START] 后台启动 Vite dev server -> http://127.0.0.1:5000")
    print(f"   日志文件 : {VITE_LOG_FILE}")

    log_fp = open(VITE_LOG_FILE, "ab", buffering=0)
    child_env = os.environ.copy()
    child_env["PYTHONIOENCODING"] = "utf-8"
    child_env["PYTHONUTF8"] = "1"

    # 用 npx vite（避免 npm run dev 多一层 shell）
    npm_cmd = "npm.cmd" if sys.platform == "win32" else "npm"
    kwargs: dict = dict(
        args=[npm_cmd, "run", "dev"],
        stdout=log_fp,
        stderr=subprocess.STDOUT,
        stdin=subprocess.DEVNULL,
        cwd=str(FRONTEND_DIR),
        env=child_env,
    )
    if sys.platform == "win32":
        DETACHED_PROCESS = 0x00000008
        CREATE_NEW_PROCESS_GROUP = 0x00000200
        kwargs["creationflags"] = DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP
        kwargs["close_fds"] = True
    else:
        kwargs["start_new_session"] = True

    proc = subprocess.Popen(**kwargs)
    VITE_PID_FILE.write_text(str(proc.pid))

    # 等几秒看进程是否还在
    for _ in range(15):
        time.sleep(0.3)
        if not _pid_alive(proc.pid):
            print("[FAIL] Vite 启动后立即退出，请查看日志：")
            print(f"   tail -n 50 {VITE_LOG_FILE}" if sys.platform != "win32"
                  else f"   type {VITE_LOG_FILE}")
            VITE_PID_FILE.unlink(missing_ok=True)
            return None

    print(f"[OK] Vite 启动成功（PID {proc.pid}）")
    return proc.pid


def build_frontend() -> bool:
    """构建前端到 static/dist/。返回是否成功。"""
    if not (FRONTEND_DIR / "node_modules").exists():
        print("[INFO] frontend/node_modules 不存在，先执行 npm install ...")
        npm_cmd = "npm.cmd" if sys.platform == "win32" else "npm"
        result = subprocess.run(
            [npm_cmd, "install", "--no-audit", "--no-fund", "--loglevel=error"],
            cwd=str(FRONTEND_DIR),
        )
        if result.returncode != 0:
            print("[FAIL] npm install 失败")
            return False

    print("[BUILD] 构建前端到 static/dist/ ...")
    npm_cmd = "npm.cmd" if sys.platform == "win32" else "npm"
    result = subprocess.run([npm_cmd, "run", "build"], cwd=str(FRONTEND_DIR))
    if result.returncode != 0:
        print("[FAIL] npm run build 失败")
        return False
    if not DIST_INDEX.exists():
        print(f"[FAIL] 构建完成但 {DIST_INDEX} 不存在")
        return False
    print(f"[OK] 前端构建完成 → {DIST_INDEX}")
    return True


def start_background() -> int:
    """后台启动子进程（脱离父进程），返回子进程 PID。

    自动检测 dist 是否构建：
    - 已构建（生产模式）：FastAPI 监听 :5000，提供 SPA + API
    - 未构建（开发模式）：Vite 监听 :5000（用户入口），FastAPI 改听 :5001（API）
      Vite proxy 把 /api、/static、/admin 转发到 :5001
    """
    ensure_dirs()
    existing = read_pid()
    if existing is not None:
        print(f"[INFO] FastAPI 已在运行（PID {existing}），先 stop 再 start")
        return existing

    dist_built = is_dist_built()
    mode_label = "生产" if dist_built else "开发"

    # 开发模式：FastAPI 改听 :5001，让 Vite 占 :5000
    # 生产模式：FastAPI 听 :5000（默认，从 .env 读 QI_PORT）
    if not dist_built:
        fastapi_port = 5001
    else:
        fastapi_port = settings.port

    print(f"[START] 后台启动（{mode_label}模式）")
    print(f"   FastAPI : http://{settings.host}:{fastapi_port}")
    if not dist_built:
        print(f"   Vite    : http://{settings.host}:5000（用户访问入口）")
    print(f"   日志文件 : {LOG_FILE}")
    print(f"   PID 文件 : {PID_FILE}")

    # 后台子进程：stdout/stderr 重定向到日志，stdin 关掉
    log_fp = open(LOG_FILE, "ab", buffering=0)
    # 强制子进程用 UTF-8 输出（解决 Windows GBK 终端 + emoji 乱码）
    child_env = os.environ.copy()
    child_env["PYTHONIOENCODING"] = "utf-8"
    child_env["PYTHONUTF8"] = "1"
    # 开发模式覆盖 QI_PORT 让 FastAPI 听 :5001
    if not dist_built:
        child_env["QI_PORT"] = str(fastapi_port)
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
            print("[FAIL] FastAPI 启动后立即退出，请查看日志：")
            print(f"   tail -n 50 {LOG_FILE}" if sys.platform != "win32"
                  else f"   type {LOG_FILE}")
            PID_FILE.unlink(missing_ok=True)
            return -1

    print(f"[OK] FastAPI 启动成功（PID {proc.pid}, :{fastapi_port}）")

    # 开发模式：再起 Vite（占 :5000）
    if not dist_built:
        vite_pid = start_vite_background()
        if vite_pid is not None:
            print(f"   访问     http://{settings.host}:5000（Vite dev，HMR 热更新）")
            print(f"   API      http://{settings.host}:{fastapi_port}/docs")
        else:
            print(f"   [WARN] Vite 未启动，访问 :5000 会失败")
    else:
        print(f"   访问     http://{settings.host}:{settings.port}")

    return proc.pid


def run_foreground() -> None:
    """前台运行（systemd / supervisor / 调试用）。

    注意：fg 模式不会自动起 Vite，需要用户在另一个终端执行 `cd frontend && npm run dev`。
    或者用 `python start.py start`（后台模式，自动起 Vite）。
    """
    ensure_dirs()
    # 用 lifespan 钩子做建表 + 种子
    import uvicorn
    dist_built = is_dist_built()
    mode_label = "生产" if dist_built else "开发"
    print(f"[HEAL] 静屿 — 前台启动（{mode_label}模式）-> http://{settings.host}:{settings.port}")
    if not dist_built:
        print(f"   [提示] 开发模式：请单独执行 `cd frontend && npm run dev` 启动 Vite")
        print(f"   [提示] 或用 `python start.py start`（后台模式自动起 Vite）")
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
    vite_pid = read_vite_pid()
    if pid is None and vite_pid is None:
        print("状态：未运行")
        sys.exit(3)
    dist_built = is_dist_built()
    fastapi_port = settings.port if dist_built else 5001
    print("状态：")
    if pid is not None:
        print(f"  FastAPI : 运行中（PID {pid}）-> http://{settings.host}:{fastapi_port}")
    else:
        print(f"  FastAPI : 未运行")
    if vite_pid is not None:
        print(f"  Vite    : 运行中（PID {vite_pid}）-> http://{settings.host}:5000")
    elif not dist_built:
        print(f"  Vite    : 未运行（开发模式建议启动）")
    else:
        print(f"  Vite    : 未启动（生产模式，dist 已构建）")
    print(f"  日志    : {LOG_FILE} | {VITE_LOG_FILE}")
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
        choices=["start", "stop", "restart", "status", "fg", "foreground", "build"],
        help="操作：start 后台启动（默认，自动检测 dist）/ stop / restart / status / fg 前台 / build 构建前端",
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
    elif action == "build":
        sys.exit(0 if build_frontend() else 1)
    elif action == "fg":
        run_foreground()


if __name__ == "__main__":
    main()
