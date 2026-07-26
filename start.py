"""静屿 — 一键启动脚本（前后端一起起来）。

>>> 一句话用法：
    python start.py                # 后台启动：默认生产模式（自动构建前端 + FastAPI :5000）
    python start.py --dev          # 应用/开发模式（Vite :5000 HMR + FastAPI :5001，本地开发用）
    python start.py fg             # 前台运行（systemd / 调试用，关掉终端就停）
    python start.py --init-db      # 启动前重置数据库

--- 全部子命令：
    python start.py                # 后台启动（默认 = 生产模式）：自动构建前端（如果 static/dist/ 不存在）+ FastAPI :5000
    python start.py start          # 同上
    python start.py --prod         # 显式生产模式（默认就是生产模式，加不加效果一样）
    python start.py --dev          # 应用/开发模式：Vite :5000（HMR）+ FastAPI :5001，本地开发用
    python start.py stop           # 优雅停止（同时停 FastAPI + Vite）
    python start.py restart        # 重启
    python start.py status         # 查看状态
    python start.py fg             # 前台运行（systemd / 调试用，关掉终端就停；fg 默认仍是生产模式，可加 --dev 切应用模式）
    python start.py build          # 仅构建前端到 static/dist/（不启动服务）

--- 架构说明（v2.0 Vue 3 重构 + v2.0.1 端口策略 + v2.2.2 默认应用模式）：
    前端由 Vue 3 SPA 接管，FastAPI 改为纯 API 后端 + SPA fallback：
      1. 后端 API（/api/* 路由）
      2. SPA fallback：dist 已构建 → 返回 static/dist/index.html
                      dist 未构建 → 开发态返回提示页引导访问 Vite :5000
      3. 静态资源（/static/* 下的 CSS/JS/图片 + /static/dist/* 前端构建产物）

    start.py 默认应用/开发模式（前后端一起起）：
      - 应用模式（默认）：Vite 占 :5000（HMR）+ FastAPI 退 :5001（API）
        启动前自动检测 frontend/node_modules，不存在则自动 npm install（约 7 分钟，仅首次）
        Vite proxy 把 /api、/static、/admin、/docs、/openapi.json 转发到 :5001
        **用户始终访问 :5000**（Vite dev server，HMR 热更新）
      - 生产模式（--prod）：只起 FastAPI :5000（从 .env 读 QI_PORT），需 static/dist/ 已构建
        dist 未构建 → 报错退出（提示先跑 `python start.py build` 或不要加 --prod 走默认应用模式）

--- 服务器开机启动 + 端口转发（生产场景，端口代理已配好 :5000 不能动）：
    前提：服务器装 Node.js 18+（v2.3.1 起 --prod 模式会自动构建，需要 Node.js）
          或本地构建好 dist 后把 static/dist/ 一起上传（则服务器不需要 Node.js）

    方式 A（宝塔面板，默认应用模式）：
      项目类型  : Python
      启动命令  : cd /www/wwwroot/healing && python start.py
      停止命令  : cd /www/wwwroot/healing && python start.py stop
      端口      : 5000（Vite dev server，用户入口）+ 5001（FastAPI，API 后端）
      反向代理  : 宝塔站点 → 反向代理 → 目标 URL http://127.0.0.1:5000
      首次启动  : 自动 npm install（约 7 分钟），之后秒启
    方式 B（systemd，生产模式推荐 ⭐ v2.3.1）：
      ExecStart=/home/healing/app/venv/bin/python start.py fg --prod  # fg 前台运行 + 显式生产模式
      Environment=QI_PORT=5000
      Nginx 反代 80/443 → 127.0.0.1:5000
      更新流程  : git pull 或 FileZilla 上传新代码 → python start.py --prod restart
                  （v2.3.1 起：自动检测 frontend/src/ 新于 static/dist/ 时自动 npm install + build）

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
NODE_MODULES_DIR = FRONTEND_DIR / "node_modules"


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


def _check_node_available() -> tuple[bool, str]:
    """检测 node + npm 是否可用。返回 (是否可用, 版本信息字符串)。"""
    npm_cmd = "npm.cmd" if sys.platform == "win32" else "npm"
    try:
        r1 = subprocess.run(["node", "--version"], capture_output=True, text=True, timeout=5)
        r2 = subprocess.run([npm_cmd, "--version"], capture_output=True, text=True, timeout=5)
        if r1.returncode == 0 and r2.returncode == 0:
            return True, f"node {r1.stdout.strip()} / npm {r2.stdout.strip()}"
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        pass
    return False, ""


def _ensure_node_modules() -> bool:
    """应用/开发模式启动前的依赖检查。

    检测 frontend/node_modules 是否存在：
      - 存在 → 直接返回 True
      - 不存在 → 检测 Node.js → 自动 npm install（约 7 分钟，仅首次）
      - Node.js 不可用 → 报错退出
    """
    if NODE_MODULES_DIR.exists():
        return True

    print("[INFO] 检测到前端依赖未安装（frontend/node_modules 不存在）")
    node_ok, node_ver = _check_node_available()
    if not node_ok:
        print("[FAIL] 前端依赖未安装且 Node.js 不可用，无法自动 npm install")
        print("       解决方案（任选其一）：")
        print("         A. 装 Node.js 18+，再跑 python start.py（自动 npm install）")
        print("         B. 本地构建好 dist 后，用 python start.py --prod 走生产模式（不需要 Node.js）")
        sys.exit(1)

    print(f"[INFO] 检测到 {node_ver}，自动安装前端依赖（首次约 7 分钟）...")
    npm_cmd = "npm.cmd" if sys.platform == "win32" else "npm"
    result = subprocess.run(
        [npm_cmd, "install", "--no-audit", "--no-fund", "--loglevel=error"],
        cwd=str(FRONTEND_DIR),
    )
    if result.returncode != 0:
        print("[FAIL] npm install 失败")
        print("       请手动执行：cd frontend && npm install")
        sys.exit(1)

    print("[OK] 前端依赖安装完成")
    return True


def _ensure_dist_for_prod() -> None:
    """生产模式启动前的 dist 检查 + 自动构建。

    逻辑很简单：static/dist/index.html 存在 → 直接启动；不存在 → 自动构建。

    服务器部署流程：
      1. FileZilla 上传代码（static/dist/ 不上传，被 .gitignore 排除）
      2. python start.py → 检测到 dist 不存在 → 自动 npm install + npm run build
      3. 构建完启动 FastAPI :5000

    想强制重建？删除 static/dist/ 目录再启动，或跑 `python start.py build`。
    """
    if is_dist_built():
        return  # dist 已存在，直接启动

    print("[INFO] static/dist/ 不存在，自动构建前端...")

    node_ok, node_ver = _check_node_available()
    if not node_ok:
        print("[FAIL] 需要构建前端但 Node.js 不可用")
        print("       解决方案（任选其一）：")
        print("         A. 在服务器上装 Node.js 18+，再跑 python start.py")
        print("         B. 在本地构建好 dist 后，把 static/dist/ 整个目录上传到服务器")
        sys.exit(1)

    print(f"[INFO] 检测到 {node_ver}，开始构建前端...")
    if not build_frontend():
        print("[FAIL] 前端构建失败，请手动执行：cd frontend && npm install && npm run build")
        sys.exit(1)

    print("[OK] 前端构建完成，继续启动服务")


def start_vite_background() -> int | None:
    """后台启动 Vite dev server（应用/开发模式用）。

    返回 Vite 进程 PID，失败返回 None。
    """
    if not NODE_MODULES_DIR.exists():
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
    if not NODE_MODULES_DIR.exists():
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


def start_background(force_prod: bool = False) -> int:
    """后台启动子进程（脱离父进程），返回子进程 PID。

    默认 = 应用/开发模式（前后端一起起）：
      - 自动检测 frontend/node_modules，不存在则 npm install（约 7 分钟，仅首次）
      - Vite 监听 :5000（用户入口，HMR）+ FastAPI 改听 :5001（API，由 start.py 设 QI_PORT=5001）
      - Vite proxy 把 /api、/static、/admin、/docs、/openapi.json 转发到 :5001

    生产模式（force_prod=True）：
      - 要求 static/dist/ 已构建（未构建报错退出）
      - FastAPI 监听 :5000（从 .env 读 QI_PORT），Vite 不运行
    """
    ensure_dirs()
    existing = read_pid()
    if existing is not None:
        print(f"[INFO] FastAPI 已在运行（PID {existing}），先 stop 再 start")
        return existing

    if force_prod:
        _ensure_dist_for_prod()
        is_prod = True
    else:
        _ensure_node_modules()
        is_prod = False

    mode_label = "生产" if is_prod else "应用"

    # 应用模式：FastAPI 改听 :5001，让 Vite 占 :5000
    # 生产模式：FastAPI 听 :5000（默认，从 .env 读 QI_PORT）
    if not is_prod:
        fastapi_port = 5001
    else:
        fastapi_port = settings.port

    print(f"[START] 后台启动（{mode_label}模式）")
    print(f"   FastAPI : http://{settings.host}:{fastapi_port}")
    if not is_prod:
        print(f"   Vite    : http://{settings.host}:5000（用户访问入口，HMR 热更新）")
    print(f"   日志文件 : {LOG_FILE}")
    print(f"   PID 文件 : {PID_FILE}")

    # 后台子进程：stdout/stderr 重定向到日志，stdin 关掉
    log_fp = open(LOG_FILE, "ab", buffering=0)
    # 强制子进程用 UTF-8 输出（解决 Windows GBK 终端 + emoji 乱码）
    child_env = os.environ.copy()
    child_env["PYTHONIOENCODING"] = "utf-8"
    child_env["PYTHONUTF8"] = "1"
    # 应用模式覆盖 QI_PORT 让 FastAPI 听 :5001
    if not is_prod:
        child_env["QI_PORT"] = str(fastapi_port)
    kwargs: dict = dict(
        # 用 __file__ 引用自己，不写死文件名（万一用户重命名也能跑）
        args=[sys.executable, str(Path(__file__).resolve()), "fg"] + (["--prod"] if force_prod else []),
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

    # 应用模式：再起 Vite（占 :5000）
    if not is_prod:
        vite_pid = start_vite_background()
        if vite_pid is not None:
            print(f"   访问     http://{settings.host}:5000（Vite dev，HMR 热更新）")
            print(f"   API      http://{settings.host}:{fastapi_port}/docs")
        else:
            print(f"   [WARN] Vite 未启动，访问 :5000 会失败")
    else:
        print(f"   访问     http://{settings.host}:{settings.port}")

    return proc.pid


def run_foreground(force_prod: bool = False) -> None:
    """前台运行（systemd / supervisor / 调试用）。

    默认 = 应用/开发模式：
      - 自动检测 frontend/node_modules，不存在则 npm install
      - FastAPI 退到 :5001（由 start.py 设 QI_PORT=5001），需单独起 Vite
      - 注意：fg 模式不会自动起 Vite，应用模式请单独执行 `cd frontend && npm run dev`
              或用 `python start.py`（后台模式自动起 Vite）

    生产模式（force_prod=True）：
      - 要求 static/dist/ 已构建
      - FastAPI 听 :5000（systemd 推荐场景）
    """
    ensure_dirs()
    # 用 lifespan 钩子做建表 + 种子
    import uvicorn
    if force_prod:
        _ensure_dist_for_prod()
        is_prod = True
    else:
        _ensure_node_modules()
        is_prod = False
    mode_label = "生产" if is_prod else "应用"
    print(f"[HEAL] 静屿 — 前台启动（{mode_label}模式）-> http://{settings.host}:{settings.port}")
    if not is_prod:
        print(f"   [提示] 应用模式（fg）：请单独执行 `cd frontend && npm run dev` 启动 Vite :5000")
        print(f"   [提示] 或用 `python start.py`（后台模式）自动同时起 Vite + FastAPI")
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
    # 状态判断：默认应用模式（FastAPI 在 :5001）；--prod 模式 FastAPI 在 :5000
    # 通过查 vite_pid 是否存在判断当前是否应用模式
    fastapi_port = settings.port if dist_built and vite_pid is None else 5001
    print("状态：")
    if pid is not None:
        print(f"  FastAPI : 运行中（PID {pid}）-> http://{settings.host}:{fastapi_port}")
    else:
        print(f"  FastAPI : 未运行")
    if vite_pid is not None:
        print(f"  Vite    : 运行中（PID {vite_pid}）-> http://{settings.host}:5000")
    elif not dist_built or fastapi_port == 5001:
        print(f"  Vite    : 未运行（应用模式建议启动）")
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
        description="静屿 — 治愈系身心疗愈平台 一键启动（默认 = 生产模式，自动构建 + FastAPI :5000）",
    )
    p.add_argument(
        "action",
        nargs="?",
        default="start",
        choices=["start", "stop", "restart", "status", "fg", "foreground", "build"],
        help="操作：start 后台启动（默认 = 生产模式，自动构建 + FastAPI :5000）/ stop / restart / status / fg 前台 / build 构建前端",
    )
    mode_group = p.add_mutually_exclusive_group()
    mode_group.add_argument(
        "--prod",
        action="store_true",
        help="显式生产模式（默认就是生产模式，加不加效果一样）",
    )
    mode_group.add_argument(
        "--dev",
        action="store_true",
        help="应用/开发模式：Vite :5000（HMR）+ FastAPI :5001，本地开发用",
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

    # v2.3.1 起默认 = 生产模式（force_prod=True）
    # --dev 才走应用模式（Vite + FastAPI 双进程，本地开发用）
    force_prod = not args.dev

    if action == "start":
        start_background(force_prod=force_prod)
    elif action == "stop":
        sys.exit(0 if stop_process() else 1)
    elif action == "restart":
        stop_process()
        time.sleep(0.5)
        start_background(force_prod=force_prod)
    elif action == "status":
        show_status()
    elif action == "build":
        sys.exit(0 if build_frontend() else 1)
    elif action == "fg":
        run_foreground(force_prod=force_prod)


if __name__ == "__main__":
    main()
