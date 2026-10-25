# 部署指南

> 三种部署方式：**宝塔面板**（最简单，私人项目首选）、**systemd**（VPS 标准）、**手动 nohup**（临时调试）。

> 🔒 **改了本文件涉及的部署配置（端口 / Nginx / systemd / HTTPS / 反代 / 前端构建），必须同步更新**：[README §1](../README.md) / [HANDOFF §1](HANDOFF.md) / [AGENTS.md](../AGENTS.md)。详见 [HANDOFF §12](HANDOFF.md) 文档自动同步铁律。

> **当前版本：v2.6.2（2026-10-25）**。版本变更历史见 [CHANGELOG.md](CHANGELOG.md)；本文只保留当前部署步骤。
>
> **部署三件事**：① 拉代码 ② 配置 `.env` ③ `python start.py`（默认生产模式；`static/dist/index.html` 不存在会自动 `npm install + npm run build`）。
>
> - 前端源码有改动 → 必须重新构建（`python start.py build` 或 `cd frontend && npm run build`），再重启。
> - 数据库迁移在启动时自动执行（`_migrate_legacy_columns()` + `Base.metadata.create_all`），不需要手动 ALTER。
> - AI 可选：`.env` 的 `QI_NVIDIA_API_KEY` 留空也能跑，3 个端点会优雅降级。
> - 后台入口是 `/admin/login`（`/admin` 会 302 到 `/admin/`）。

---

## 前端构建（v2.0 Vue 3 重构后必做，所有部署方式通用）

> 2026-07-19 v2.0 全站 Vue 3 重构后，前台从 Jinja2 SSR 迁移到 Vue 3 SPA。**部署前必须先构建前端**，否则访问 :5000 只看到「dist 未构建」提示页。

> 2026-07-19 v2.0.1 起 [start.py](../start.py) 新增 `build` 子命令：`python start.py build` 一键执行 `npm install && npm run build`（自动检测 Node 是否装好 + 自动 cd frontend + 输出到 ../static/dist/），推荐用此方式。

### 构建步骤

#### 方式 A：一键构建（推荐 ⭐）

```bash
# 一键执行 npm install + npm run build，输出到 static/dist/
python start.py build
```

[start.py](../start.py) 的 `build` 子命令内部做了 3 件事：
1. 检查 `frontend/node_modules/` 是否存在，不存在自动 `npm install`
2. 执行 `npm run build`（Vite 5 + Rollup）
3. 输出到 `../static/dist/`（即 [static/dist/](../static/dist/)）

#### 方式 B：手动两步

```bash
# 1. 确保已装 Node.js 18+（推荐 20 LTS）
node --version    # 应 >= v18

# 2. 进入前端目录
cd frontend

# 3. 安装依赖（首次：含 three.js 等大包，约 7 分钟，详见 [HANDOFF §6.14](HANDOFF.md)）
npm install

# 4. 构建（Vite 5 + Rollup，输出到 ../static/dist/）
npm run build
```

构建成功后会看到：
```
vite v5.x.x building for production...
✓ N modules transformed.
dist/index.html                  ← ../static/dist/index.html
dist/assets/index-xxxxxx.js      ← Vue 3 + 依赖 chunk
dist/assets/three-vendor-*.js    ← Three.js + addons 单独 chunk（v2.2 起 /garden FlowerField + / HeroScene + AmbientBackground 共享，gzip 719.84KB，含 OrbitControls / EffectComposer / UnrealBloomPass / RoomEnvironment，首屏不加载）
dist/assets/gsap-vendor-*.js     ← GSAP 单独 chunk
dist/assets/vue-vendor-*.js      ← Vue 3 + Vue Router + Pinia 单独 chunk（v2.0.1 加 manualChunks 分包）
dist/assets/HeroScene-*.js       ← 首页 Hero 区 3D 浮岛雾海 v2 组件（v2.1 加 7.5KB → v2.2 PBR 升级 13.54KB，仅 / 按需加载）
dist/assets/FlowerField-*.js     ← 3D 花田 v2 组件（v2.2 PBR 升级，9.94KB，仅 /garden 按需加载）
dist/assets/SceneControls-*.js   ← 3D 场景视图控制工具栏（v2.2 加，4.5KB，被 HeroScene / FlowerField 引用）
dist/assets/AudioVisualizer-*.js ← 音波可视化 v2 组件（4 模式 + 节拍检测，仅 /music/:yin 按需加载）
dist/assets/index-xxxxxx.css     ← Tailwind CSS
✓ built in Xs
```

> 💡 **Three.js chunk（v2.2 更新）**：[FlowerField.vue](../frontend/src/components/FlowerField.vue)（`/garden`）、[HeroScene.vue](../frontend/src/components/HeroScene.vue)（`/`）和 [AmbientBackground.vue](../frontend/src/components/AmbientBackground.vue)（全局，挂在 AppLayout）都用 `defineAsyncComponent` 异步导入 `three` + `three/addons/*`，所以 Three.js + addons 被打成单独的 `three-vendor-*.js` chunk，**首屏不加载**，仅在用户访问 `/` 或 `/garden` 时按需拉取。三处共享同一 chunk，不重复下载。v2.2 起 chunk 体积从 175KB 增长到 719.84KB，因为加入了 PBR 渲染管线所需的 addons：`OrbitControls`（交互）/ `EffectComposer` + `RenderPass` + `UnrealBloomPass` + `OutputPass`（后处理）/ `RoomEnvironment`（环境映射）。AmbientBackground 首屏 DOM 由 CSS 雾气光斑 + Canvas2D 光点兜底，Three.js 加载完前页面已有完整视觉效果（三层渐进增强）。

### 构建产物去向

| 文件 | 路径 | 由谁服务 |
|---|---|---|
| `index.html` | [static/dist/index.html](../static/dist/) | FastAPI SPA fallback 兜底返回 |
| JS chunk | [static/dist/assets/index-*.js](../static/dist/) | FastAPI StaticFiles `/static/dist/*` |
| CSS chunk | [static/dist/assets/index-*.css](../static/dist/) | FastAPI StaticFiles `/static/dist/*` |

### 为什么必须先构建再启动

[app/main.py](../app/main.py) 末尾的 SPA fallback 通配路由会检查 `static/dist/index.html` 是否存在：
- **存在** → 返回 `index.html`，Vue Router 接管客户端路由（生产模式）
- **不存在** → 返回提示页引导访问 Vite dev server（开发模式，详见 [DEVELOPMENT 前端开发](DEVELOPMENT.md)）

### 重新构建时机

| 改动 | 是否需要 `npm run build` |
|---|---|
| 改 [`frontend/src/`](../frontend/src/) 下任何 `.vue` / `.js` / `.ts` / `.css` | ✅ 必须 |
| 改 [`frontend/tailwind.config.js`](../frontend/tailwind.config.js) | ✅ 必须 |
| 改 [`frontend/vite.config.js`](../frontend/vite.config.js) | ✅ 必须 |
| 改 [`app/`](../app/) 下 Python 代码 | ❌ 不需要（重启 `python start.py restart` 即可） |
| 改 [`templates/admin/`](../templates/admin/) 后台 SSR 模板 | ❌ 不需要（Jinja2 模板运行时渲染） |
| 改 [`.env`](../.env.example) | ❌ 不需要（重启即可） |

> 💡 **v2.3.3 Safari 兼容修复示例**：本次改了 [utils/visual.js](../frontend/src/utils/visual.js)（**`hasWebGL` 重写** + `getWebGLCaps` / `isSafari` / `isIOS`）+ [utils/three-helpers.js](../frontend/src/utils/three-helpers.js)（`webglcontextlost` / `webglcontextrestored` 监听）+ [HeroScene.vue](../frontend/src/components/HeroScene.vue)（**iOS 降级**：**Bloom 降级** + **PMREM 降级**）+ 新建 [EmojiIcon.vue](../frontend/src/components/EmojiIcon.vue)（**Iconify** + `twemoji` **SVG emoji**）+ 改 [AppLayout.vue](../frontend/src/components/AppLayout.vue) / [ProfileView.vue](../frontend/src/views/profile/ProfileView.vue)（替换 emoji）——全部命中表格首行（`.vue` / `.js`），**必须重新 `npm run build`** 才能让 Safari / iOS 用户拿到 **Safari 兼容**修复 + **跨浏览器一致** emoji。

### 部署流程（生产，v2.3.2 起默认生产模式 + 自动构建）

```bash
# 1. 拉代码
git pull

# 2. 构建前端（如果 frontend/src/ 有改动）
#    v2.3.2 起：也可跳过此步，python start.py 会 dist 存在检测，不存在则自动构建
cd frontend && npm install && npm run build && cd ..

# 3. 装/更新 Python 依赖（如果 requirements.txt 有改动）
pip install -r requirements.txt

# 4. 启动 / 重启后端（v2.3.2 起默认 = 生产模式，FastAPI :5000 单进程）
python start.py restart
```

> ⚠️ **顺序很重要**：先 `npm run build`，后 `python start.py`。否则 FastAPI 起来后还是返回旧 dist（v2.3.2 起 `dist 存在检测` 只看 `static/dist/index.html` 是否存在，不比较修改时间，旧 dist 不会自动触发重建）。

> 💡 **v2.3.2 服务器部署简化为 2 步**（首次或更新皆可）：① 上传代码（`git pull`）② `python start.py`（`dist 存在检测` → 不存在则 `自动构建` `npm install + npm run build`，需 Node.js 18+；已存在则秒启 FastAPI 单进程 :5000）。`--prod` 已改为兼容别名（默认就是生产模式）。

### 关于应用/开发模式（需要 `--dev` 显式开启，v2.3.2 起不再是默认行为）

> ⚠️ **v2.3.2 行为变更**：`python start.py`（无参数）默认走**生产模式**（FastAPI :5000 单进程，需 dist 已构建，不存在则自动构建）——回滚 v2.2.2「默认应用模式」。开发需显式 `python start.py --dev`（Vite :5000 HMR + FastAPI :5001 API，前后端一起起的「应用模式」）。`--prod` 改为兼容别名。理由：服务器端口代理已配好 :5000 不能动，应用模式会让 Vite 占 :5000 破坏代理。

开发时不用每次改前端都 `npm run build`，直接跑 Vite dev server：
```bash
python start.py --dev           # 应用/开发模式（v2.3.2 起需显式 --dev）：
                                #   自动 npm install 当 node_modules 不存在
                                #   起 Vite :5000（HMR + 用户入口）+ FastAPI :5001（API）
```

或手动两终端（v2.0.1 端口策略）：
```bash
# 终端 1：Vite dev server（用户访问 :5000）
cd frontend && npm run dev     # http://127.0.0.1:5000/

# 终端 2：FastAPI（API 退到 :5001）
set QI_PORT=5001 && python start.py fg    # http://127.0.0.1:5001/
```

> ⚠️ **v2.0.1 端口策略调整**：应用/开发模式 Vite 占 :5000（用户入口 + HMR），FastAPI 退到 :5001（API）；不再是 v2.0 的 Vite :5173 + FastAPI :5000。理由：让 FastAPI 反代 Vite 内部路径 `/@id/__x00__plugin-vue:export-helper` 会因 null 字节转义 + 冒号失败（详见 [HANDOFF §6.16](HANDOFF.md)）。**用户始终访问 :5000**。

Vite dev server 提供 HMR 热更新 + 自动 proxy `/api`、`/static`、`/admin`、`/docs`、`/openapi.json` 到 FastAPI :5001，详见 [DEVELOPMENT 前端开发](DEVELOPMENT.md)。

---

## 方式 1：宝塔面板（推荐 ⭐）

宝塔自带 Python 项目管理器，省心。

### 1.1 准备工作

- 一台装了宝塔的 Linux 服务器（CentOS / Ubuntu / Debian）
- 宝塔后台：软件商店 → 安装 **「Python 项目管理器」**（一般自带 Python 3.8-3.12）
- 解析好的域名（可选，没域名直接用 IP）

### 1.2 上传代码

方式 A（推荐）：用宝塔「文件」直接上传 zip，解压到 `/www/wwwroot/healing/`

方式 B：用 git
```bash
cd /www/wwwroot/
git clone <your-repo-url> healing
```

### 1.3 创建项目

宝塔后台 → Python 项目 → 「添加项目」：

| 字段 | 填什么 |
|---|---|
| 项目类型 | Python |
| 项目路径 | `/www/wwwroot/healing` |
| 项目名称 | `healing` |
| Python 版本 | 3.11+ |
| 启动方式 | **自定义命令**（见下） |
| 启动命令 | `python start.py` |
| 停止命令 | `python start.py stop` |
| 端口 | 5000 |

**为什么用自定义命令**：
- 宝塔默认用 `gunicorn`，但本项目**没有** gunicorn 依赖
- 我们用自研的 [start.py](../start.py)，自带 PID / 日志 / 重启

### 1.4 配置 .env

SSH 到服务器：
```bash
cd /www/wwwroot/healing
cp .env.example .env
vi .env   # 改这几行：
```

```env
QI_SECRET_KEY=<用 python -c "import secrets; print(secrets.token_hex(32))" 生成>
QI_HOST=0.0.0.0
QI_PORT=5000
QI_DEBUG=false
# AI 接入（可选）：不配置也能跑，3 个 AI 端点会优雅降级返回治愈系提示
# QI_NVIDIA_API_KEY=nvapi-xxxxx
# QI_AI_MODEL=z-ai/glm-5.3-flash
# QI_AI_BASE_URL=https://integrate.api.nvidia.com/v1
# 详见下方「AI 接入（可选）」章节
```

### 1.5 安装依赖 + 构建前端

**5a. Python 依赖**（SSH 或宝塔「一键依赖」）：
```bash
cd /www/wwwroot/healing
python3 -m pip install -r requirements.txt
```

**5b. 前端构建**（v2.3.2 起默认生产模式，`dist 存在检测` + `自动构建`）：

**情况 A：默认生产模式部署**（推荐，FastAPI :5000 单进程）
```bash
# 服务器需先装 Node.js 18+（宝塔软件商店 → Node.js 版本管理器）
# 不需要手动 npm install / npm run build
# python start.py 首次启动时 dist 存在检测 → 不存在则自动 npm install + npm run build（约 7 分钟），之后秒启
# 端口代理 :5000 永远指向 FastAPI（单进程，API + SPA fallback + 静态资源）
# 也可提前手动构建（避免首次启动超时）：
cd /www/wwwroot/healing/frontend
npm install        # 首次约 7 分钟（含 three.js 大包）
npm run build      # 输出到 ../static/dist/
```

**情况 B：应用/开发模式部署**（需 `--dev` 显式开启，Vite :5000 + FastAPI :5001 一起起）
```bash
# 仅本地开发 / 真机调试用，不建议生产部署
# 服务器需先装 Node.js 18+（运行时需要，Vite dev server 常驻）
python start.py --dev    # 端口代理 :5000 指向 Vite dev server（用户入口），:5001 是 FastAPI（API 后端）
```

> 💡 **v2.3.2 新行为**（回滚 v2.2.2）：`python start.py`（无参数）默认走**生产模式**（FastAPI :5000 单进程），**`dist 存在检测`**——`static/dist/index.html` 不存在则**`自动构建`** `npm install + npm run build`（需 Node.js 18+）；`--prod` 改为兼容别名（默认就是生产模式）。开发需显式 `python start.py --dev`（Vite :5000 + FastAPI :5001，前后端一起起的「应用模式」）。**端口代理 :5000 在生产模式指向 FastAPI，在应用模式指向 Vite**——服务器端口代理已配好 :5000 不能动，故默认生产模式。关键词 `默认生产模式` / `dist 存在检测` / `自动构建` / `--dev` / `应用模式` / `v2.3.2`。

### 1.6 启动

宝塔后台 → 项目 → 「启动」。

或 SSH：
```bash
cd /www/wwwroot/healing
python start.py          # v2.3.2 起默认 = 生产模式（FastAPI :5000 单进程，dist 不存在则自动构建）
```

应该看到（默认生产模式）：
```
[START] 后台启动（生产模式）
   FastAPI : http://0.0.0.0:5000（用户访问入口 + API）
   日志文件 : /www/wwwroot/healing/logs/healing.log
   PID 文件 : /www/wwwroot/healing/run/healing.pid
[OK] FastAPI 启动成功（PID 12345, :5000）
   访问     http://0.0.0.0:5000（FastAPI，服务 static/dist/ + SPA fallback）
   API      http://0.0.0.0:5000/docs
```

> 💡 **应用/开发模式启动**（本地开发用）：`python start.py --dev` → Vite :5000（用户入口，HMR）+ FastAPI :5001（API），前后端一起起。生产部署不需要。

### 1.7 反向代理（让外网能访问）

宝塔 → 网站 → 添加站点（PHP 静态就行）→ 站点的「设置」→「反向代理」：

| 字段 | 填什么 |
|---|---|
| 代理名称 | healing |
| 目标 URL | `http://127.0.0.1:5000` |
| 发送域名 | `$host` |

提交后，访问 `http://你的域名/` 就走 Nginx → Python 服务。

### 1.8 HTTPS（强烈推荐）

宝塔站点 → 「SSL」 → 选「Let's Encrypt」 → 申请 → 开启强制 HTTPS。

**完事。** 用户访问 `https://你的域名/` 就是你的应用。

### 1.9 日常维护

| 任务 | 命令 |
|---|---|
| 看服务状态 | SSH 跑 `python start.py status` |
| 看日志 | `tail -f logs/healing.log` |
| 重启服务 | `python start.py restart` |
| 备份数据库 | `cp data/healing.db backup/healing-$(date +%Y%m%d).db` |
| 更新代码（仅后端改动） | `git pull && python start.py restart` |
| 更新代码（含前端改动） | `git pull && cd frontend && npm install && npm run build && cd .. && python start.py restart` |

> 🔒 **改了部署相关配置（端口 / Nginx / systemd / HTTPS）必须同步更新**：[README §1](../README.md) / [HANDOFF §1](HANDOFF.md) / 本文件对应章节。改代码不改文档 = 改了一半（详见 [HANDOFF §12](HANDOFF.md)）。

---

## 方式 2：systemd（VPS 标准做法）

适合纯 Linux VPS，没有宝塔。

### 2.1 准备

```bash
# 1. 安装 Python 3.11+
sudo apt update && sudo apt install python3.11 python3.11-venv python3-pip
# 或 CentOS:
# sudo yum install python311 python311-pip

# 2. 创建用户（不推荐用 root 跑）
sudo useradd -m -s /bin/bash healing
```

### 2.2 部署代码

```bash
sudo -iu healing
mkdir -p /home/healing/app
cd /home/healing/app
git clone <your-repo> .
# 或 scp 上传
```

### 2.3 安装依赖 + 构建前端

**3a. Python 依赖**：
```bash
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**3b. 前端构建**（v2.3.2 起默认生产模式，`dist 存在检测` + `自动构建`）：

**情况 A：默认生产模式部署**（systemd 推荐，FastAPI 单进程）
```bash
# 服务器需先装 Node.js 18+（构建用，运行时不需要）
sudo apt install nodejs npm     # Ubuntu/Debian
# 或: curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash - && sudo apt install -y nodejs

# 提前手动构建（避免 systemd 首次启动超时）：
cd /home/healing/app/frontend
npm install        # 首次约 7 分钟（含 three.js 大包）
npm run build      # 输出到 ../static/dist/
# 之后用 python start.py fg 走生产模式（v2.3.2 起默认就是生产模式，端口代理 :5000 永远指向 FastAPI）
# 也可不提前构建，python start.py fg 会 dist 存在检测 → 不存在则自动构建（但 systemd TimeoutStartSec=90 可能不够）
```

**情况 B：应用/开发模式部署**（需 `--dev` 显式开启，不推荐 systemd 用，Vite + FastAPI 双进程不易管理）
```bash
# 仅本地开发 / 真机调试用，不建议生产部署
# 服务器需先装 Node.js 18+（运行时需要，Vite dev server 常驻）
python start.py fg --dev    # Vite :5000（用户入口）+ FastAPI :5001（API），前后端一起起
# 注意：systemd 管理双进程较复杂，建议用 §1 宝塔面板或 §3 nohup 方式跑应用模式
```

> 💡 **v2.3.2 新行为**（回滚 v2.2.2）：`python start.py fg`（systemd 调用）默认走**生产模式**（FastAPI 单进程 :5000），**`dist 存在检测`**——`static/dist/index.html` 不存在则**`自动构建`** `npm install + npm run build`；`--prod` 改为兼容别名。应用/开发模式需显式 `python start.py fg --dev`（Vite :5000 + FastAPI :5001，前后端一起起的「应用模式」）。但 systemd 默认 `TimeoutStartSec=90` 秒，**建议提前手动跑情况 A 的构建** 避免 systemd 因首次 `自动构建` 超时。**生产模式端口代理 :5000 永远指向 FastAPI**。关键词 `默认生产模式` / `dist 存在检测` / `自动构建` / `--dev` / `应用模式` / `v2.3.2`。

### 2.4 配置 .env

```bash
cp .env.example .env
vi .env
# 修改 QI_SECRET_KEY, QI_HOST=0.0.0.0, QI_DEBUG=false
# 可选：AI 接入（不配置也能跑，3 个端点会优雅降级）
#   QI_NVIDIA_API_KEY=nvapi-xxxxx
#   QI_AI_MODEL=z-ai/glm-5.3-flash
#   QI_AI_BASE_URL=https://integrate.api.nvidia.com/v1
#   详见下方「AI 接入（可选）」章节
```

### 2.5 写入 systemd unit

`/etc/systemd/system/healing.service`：

```ini
[Unit]
Description=Healing Platform (FastAPI)
After=network.target

[Service]
Type=simple
User=healing
Group=healing
WorkingDirectory=/home/healing/app
Environment="PATH=/home/healing/app/venv/bin"
Environment="QI_HOST=0.0.0.0"
Environment="QI_PORT=5000"
Environment="QI_DEBUG=false"
# 用 systemd 管，start.py 跑前台（fg 子命令）；v2.3.2 起默认就是生产模式（FastAPI :5000 单进程，需 dist 已构建）
# --prod 为兼容别名（加不加效果一样）；应用/开发模式需 --dev（不适合 systemd 双进程管理）
# dist 不存在时 fg 会自动构建（npm install + npm run build），但建议提前手动构建避免 systemd 超时
ExecStart=/home/healing/app/venv/bin/python start.py fg
Restart=always
RestartSec=5
StandardOutput=append:/home/healing/app/logs/healing.log
StandardError=append:/home/healing/app/logs/healing.log

[Install]
WantedBy=multi-user.target
```

启用：
```bash
sudo systemctl daemon-reload
sudo systemctl enable healing
sudo systemctl start healing
sudo systemctl status healing
```

**注意**：systemd 模式下 `start.py` 用 `fg`（前台运行），systemd 负责进程管理 + 自动重启 + 日志收集。

### 2.6 Nginx 反代

`/etc/nginx/sites-available/healing`：

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    # 客户端真实 IP
    real_ip_header X-Real-IP;
    set_real_ip_from 127.0.0.1;

    # 静态资源（FastAPI 也能服务，但 Nginx 缓存更专业）
    location /static/ {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        expires 7d;
        add_header Cache-Control "public, immutable";
        # ⚠️ 改动 CSS / JS 后（如 05-animations.css、app.js），由于 expires 7d + immutable，
        # 老用户浏览器会一直用旧缓存。建议发版后：
        #   1) 改 style.css / base.html 里的查询串版本号（如 ?v=20260715），或
        #   2) 临时 `sudo nginx -s reload` + 让用户硬刷新（Ctrl+Shift+R）一次。
    }

    # API + 页面
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

启用：
```bash
sudo ln -s /etc/nginx/sites-available/healing /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 2.7 HTTPS（Let's Encrypt）

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com
```

自动续期（certbot 自带）。

### 2.8 防火墙

```bash
# UFW (Ubuntu)
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow OpenSSH

# firewall-cmd (CentOS)
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```

**完事。**

### 2.9 日常维护

```bash
sudo systemctl status healing         # 状态
sudo systemctl restart healing        # 重启
sudo journalctl -u healing -f        # 日志（systemd 自带）
tail -f /home/healing/app/logs/healing.log   # 业务日志
```

> 🔒 **改了 systemd unit / Nginx 配置 / 端口** → 必须同步更新 [README §1](../README.md) / [HANDOFF §1](HANDOFF.md) / 本文件对应章节（详见 [HANDOFF §12](HANDOFF.md)）。

---

## 方式 3：手动 nohup（临时调试）

```bash
cd /path/to/healing
nohup python start.py > logs/manual.log 2>&1 &
echo $! > run/manual.pid
```

或用 start.py 的后台模式（自带 PID / 日志）：
```bash
python start.py start
```

**生产不要用**。进程没守护，挂了不会自动重启。

---

## 部署后验证清单

部署完成后**必须**跑一遍：

```bash
# 1. 服务在跑（v2.0.1 端口策略：生产模式 :5000 必须是 FastAPI）
curl -I http://127.0.0.1:5000/                        # 200
# 验证 :5000 是 FastAPI 而不是 Vite：
#   - 看响应头 Server: uvicorn（FastAPI）而非 Server: Vite
#   - 或 curl -s http://127.0.0.1:5000/ | grep -i "vite"  应无命中
#   - 若命中 Vite → 说明 dev 模式没切到 prod，检查 static/dist/ 是否已构建

# 1b. 前端 dist 已构建（v2.0 Vue 3 重构后必查）
curl http://127.0.0.1:5000/ | grep -E "Vue|<div id=\"app\">"   # 命中 = dist 已构建并返回 Vue 3 SPA
curl -I http://127.0.0.1:5000/static/dist/index.html           # 200
# 若返回「dist 未构建」提示页 → 回 [前端构建](#前端构建v20-vue-3-重构后必做所有部署方式通用) 跑 python start.py build

# 1c. 3D 花田 chunk 存在（v2.0.1 FlowerField.vue 加）
curl -I http://127.0.0.1:5000/static/dist/assets/three-vendor-*.js   # 200（Three.js chunk）
# 浏览器访问 /garden 应能看到 3D 花田场景

# 2. 静态资源
curl -I http://127.0.0.1:5000/static/dist/index.html     # 200（前端构建产物）
curl -I http://127.0.0.1:5000/static/audio/tracks/流水.mp3   # 200（已接入真实音频）

# 3. 公开 API
curl http://127.0.0.1:5000/api/music | head           # 22 首（16 classic + 6 western）
curl http://127.0.0.1:5000/api/music?category=western | head   # v2.3 加：仅 6 首西方改编
curl http://127.0.0.1:5000/api/garden/shop | head     # 28 件商品（含 cost_currency 字段）
curl http://127.0.0.1:5000/api/therapy/catalog | head # v2.6.1：八段锦 + 好物目录

# 3b. v2.3 新路由（无需登录也能拿 200 / 302）
curl -I http://127.0.0.1:5000/music                  # 200（琴音疗心顶级路由）
curl -I http://127.0.0.1:5000/music/western          # 200（西洋曲谱子菜单）
curl -I http://127.0.0.1:5000/profile                # 302（未登录跳 /login，requiresAuth 生效）
curl -I http://127.0.0.1:5000/notifications          # 302（未登录跳 /login，requiresAuth 生效）
curl -I http://127.0.0.1:5000/api/notifications      # 401 或 200（需登录后访问）
curl -I http://127.0.0.1:5000/api/admin/stats        # 401（未登录拒绝，符合预期）
curl -I http://127.0.0.1:5000/admin/login            # 200（后台登录页）
curl -I http://127.0.0.1:5000/corner                 # 200（静屿角落 SPA）
curl -I http://127.0.0.1:5000/music/therapy          # 200（身心调理 SPA）

# 4. 注册一个测试账号
curl -X POST http://127.0.0.1:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"nickname":"smoketest","password":"test123456"}'
# 应返回 201

# 5. （可选）用浏览器访问
# http://yourdomain.com
# 注册 → 听歌 → 写日记 → 打卡 → 兑换
# 访问 /garden 确认 3D 花田场景加载正常
# v2.3 加：访问 /music 看琴音疗心板块（五音 + 西洋曲谱六宫格 + AI 选音）
# v2.3 加：访问 /music/western 看西洋曲谱独立列表
# v2.3 加：登录后访问 /profile 看个人主页 + 双资源条（露水/落叶）
# v2.3 加：登录后访问 /notifications 看通知列表；顶部 🔔 铃铛显示未读数（60s 轮询）
# v2.3 加：访问 /garden 看花田生长网格（浇水 / 拾取按钮）
```

### v2.3 数据库自动迁移验证

部署后第一次启动时，`init_db()` → `_migrate_legacy_columns()` 会自动给老库加列，无需手动 ALTER TABLE。验证：

```bash
sqlite3 data/healing.db
sqlite> .schema users | grep leaves                  # 应看到 leaves INTEGER DEFAULT 0 NOT NULL
sqlite> .schema diaries | grep -E "content|is_public"
sqlite> .schema shop_items | grep cost_currency      # 应看到 cost_currency VARCHAR(20) DEFAULT 'dew'
sqlite> .schema musics | grep category               # 应看到 category VARCHAR(20) DEFAULT 'classic'
sqlite> .tables                                       # 应看到 user_flowers + notifications 新表
sqlite> SELECT COUNT(*) FROM musics WHERE category='western';  # 应为 6（西方改编 seed）
sqlite> .quit
```

**迁移失败排查**：
- 若新列不存在 → 检查 `logs/healing.log` 是否有 `_migrate_legacy_columns` 报错
- 若新表 `user_flowers` / `notifications` 不存在 → `init_db()` 没跑通，检查 `app/models/__init__.py` 是否 import 了 `UserFlower` / `Notification`
- 修复后重启 `python start.py restart` 即可重跑迁移（已存在的列会跳过，不重复加）

**全部通过 = 部署完成。**

---

## AI 接入（可选，2026-07-17 加）

> **本节是可选功能**。不配置 AI 也能跑，3 个 AI 端点会优雅降级返回治愈系友好提示，业务不中断。详见 [ARCHITECTURE §6.6](ARCHITECTURE.md) / [HANDOFF §5.7](HANDOFF.md)。

### 是什么

静屿 3 个场景接入 NVIDIA NIM API（OpenAI 兼容格式），当前模型 `z-ai/glm-5.3-flash`（reasoning 模型；旧的 `meta/llama-3.1-8b-instruct` 已于 2026-08-26 下架，详见 [HANDOFF §5.7](HANDOFF.md)）：

| 场景 | 端点 | 入口 |
|---|---|---|
| 漂流瓶 AI 鼓励语 | `POST /api/ai/encouragement` | `/diary/pick` 拾瓶后 |
| 情绪日历 AI 治愈语 | `POST /api/ai/healing` | `/calendar` 打卡后 |
| 音乐 AI 心情推荐 | `POST /api/ai/recommend-music` | `/music` 或首页「AI 帮我选音」 |

### 配置 3 个环境变量

获取 NVIDIA 免费 API key：访问 [build.nvidia.com](https://build.nvidia.com) → 注册 → 在模型目录选择 `z-ai/glm-5.3-flash` 生成 key（格式 `nvapi-xxxxx`）。

在 `.env` 加入（或取消注释 [.env.example](../.env.example) 末尾的对应行）：

```env
# NVIDIA NIM API（OpenAI 兼容格式）
QI_NVIDIA_API_KEY=nvapi-你的真实key
QI_AI_MODEL=z-ai/glm-5.3-flash
QI_AI_BASE_URL=https://integrate.api.nvidia.com/v1
```

**3 个变量说明**：

| 变量 | 必填？ | 默认值 | 说明 |
|---|---|---|---|
| `QI_NVIDIA_API_KEY` | 否 | 空 | NVIDIA NIM API 的 key，`nvapi-` 开头；**留空时 3 个 AI 端点自动降级**返回 `available:false` + 治愈系提示 |
| `QI_AI_MODEL` | 否 | `z-ai/glm-5.3-flash` | 模型名，OpenAI 兼容格式。换其他 NVIDIA NIM 模型只改这里 |
| `QI_AI_BASE_URL` | 否 | `https://integrate.api.nvidia.com/v1` | API base URL，换其他厂商（DeepSeek / 智谱 / 自部署 vLLM）只改这里 |

### 重启 + 验证

```bash
# 重启
python start.py restart    # 或 sudo systemctl restart healing

# 验证 1：不配 key 时降级正常（默认状态）
# 应返回 200 + {available:false, text:"治愈系友好提示"}
curl -b c.txt -X POST http://127.0.0.1:5000/api/ai/healing \
  -H "Content-Type: application/json" \
  -d '{"mood_emoji":"calm"}'
# 注意：c.txt 是登录后的 cookie 文件，参考「部署后验证清单」注册流程

# 验证 2：配 key 后 AI 正常返回
# 编辑 .env 加入 3 个变量 → 重启 → 再调一次
# 应返回 200 + {available:true, text:"<AI 生成的治愈语>"}
```

### 网络要求

- 出站访问 `https://integrate.api.nvidia.com`（443）— 服务器防火墙需放行
- 超时 / 重试：[app/services/ai_service.py](../app/services/ai_service.py) `_call_nvidia()` 单次超时 60 秒，瞬时错误（超时 / 断连 / 429 / 5xx）线性退避重试 3 次；4xx 快速失败
- 调用失败（网络/超时/限流/4xx/5xx）→ 端点返回 200 + `available:false` + 治愈系提示，**不报 500**
- **前端字体**：Vue 3 SPA 使用 [frontend/src/assets/styles/main.css](../frontend/src/assets/styles/main.css) 的系统字体栈（零网络请求）；后台 `/admin/*` 仍用 `fonts.loli.net` 镜像 + 系统字体兜底，完全离线也不影响功能

### 成本

- NVIDIA 提供**免费** API key，符合本项目「非商业纯治愈」调性
- 限流策略由 NVIDIA 控制，本项目不主动限流；命中限流时自动降级，用户无感知

### 隐私承诺

| 场景 | 发给 NVIDIA 的内容 | 入库？ |
|---|---|---|
| 漂流瓶 AI 鼓励语 | 作者日记**前 120 字**预览 | ❌ 文案不入库，明文不留存 |
| 情绪日历 AI 治愈语 | 心情 emoji + 可选 note | ❌ 不入库 |
| 音乐 AI 心情推荐 | 用户描述的状态文本 | ❌ 不入库 |

**API key 不入仓**：`.env` 已在 `.gitignore` 里，[.env.example](../.env.example) 只放注释掉的占位。

**完全离线方案**：不配 `QI_NVIDIA_API_KEY` → 3 个端点自动降级 → 业务正常跑（仅少 AI 文案）。适合内网部署 / 不允许数据出站的环境。

---

## 备份与恢复

### 备份

```bash
# 数据库（最重要）
cp data/healing.db backup/healing-$(date +%Y%m%d-%H%M).db

# 用户上传（如果有，将来加）
tar czf backup/static-$(date +%Y%m%d).tar.gz static/

# 加密盐（已含在数据库里，不用单独备份）
```

**强烈建议**：每天 cron 备份一次：

```bash
# /etc/cron.daily/healing-backup
0 3 * * * healing cd /home/healing/app && cp data/healing.db /home/healing/backup/healing-$(date +\%Y\%m\%d).db
```

### 恢复

```bash
# 1. 停服务
python start.py stop

# 2. 覆盖数据库
cp backup/healing-20260714.db data/healing.db

# 3. 启动
python start.py
```

**注意**：用户密码和日记加密盐都在 DB 里，备份 = 备份了所有用户的所有数据。**加密文件妥善保管**。

---

## 监控（可选）

### 简单方案：宝塔自带监控

宝塔后台 → 监控 → 启用 CPU / 内存 / 磁盘告警。

### 进阶：uptime 检查

注册一个免费服务如 [UptimeRobot](https://uptimerobot.com/)，监控 `http://yourdomain.com/`，挂了发邮件 / 微信。

---

## 扩容（用户增长后）

### 阶段 1（0-1000 用户）：单服务器

当前架构完全够用。

### 阶段 2（1000-10 000 用户）：加 worker

```bash
# /etc/systemd/system/healing.service
ExecStart=/home/healing/app/venv/bin/python -m uvicorn app.main:app \
  --host 0.0.0.0 --port 5000 --workers 4
```

SQLite 换 MySQL：
```env
QI_DATABASE_URL=mysql+pymysql://user:pw@localhost:3306/healing?charset=utf8mb4
```

### 阶段 3（10 000+ 用户）：分离

- 应用服务器 × N（gunicorn + uvicorn workers）
- MySQL 主从
- Redis 缓存 + session
- 对象存储（音频文件）

**当前不需要做**。等真到了再处理。

---

## 故障排查

### 服务起不来

```bash
# 1. 看日志
tail -50 logs/healing.log

# 常见错误:
# - ModuleNotFoundError → pip install -r requirements.txt
# - PermissionError → chown -R healing:healing /home/healing/app
# - Address already in use → 别的进程占着 5000 端口，lsof -i :5000 查
```

### 502 Bad Gateway

```bash
# 1. uvicorn 没起
sudo systemctl status healing
# 2. Nginx 配置错
sudo nginx -t
# 3. 端口不通
curl -I http://127.0.0.1:5000/   # 应该 200
```

### 数据库锁死（SQLite）

```bash
# 1. 找长事务
lsof data/healing.db
# 2. 重启服务（最暴力也最有效）
python start.py restart
# 3. 长期方案：换 MySQL
```

### 静态资源 404

```bash
# 检查前端构建产物与曲目音频
ls -la static/dist/ static/dist/assets/ static/audio/tracks/
# 重启服务（init 阶段会确保目录存在）
python start.py restart
```

- `static/dist/index.html` 不存在 → `python start.py build`
- 曲目 404 → 检查文件名是否与 `musics.title` 一致（`static/audio/tracks/{曲名}.mp3`）
- 后台 CSS/JS 404 → 确认 `templates/admin/` 与 `static/css/07-admin.css`、`static/js/pages/admin_*.js` 存在

---

## 安全清单

部署前确认：

- [ ] `.env` 里 `QI_SECRET_KEY` 已改为随机长字符串
- [ ] `.env` 里 `QI_DEBUG=false`
- [ ] `.env` 文件**不**在 git 仓库里（.gitignore 已配）
- [ ] 数据库文件**不**暴露到公网（Nginx 不代理 `/data/` 路径）
- [ ] 服务器 SSH 用密钥登录，禁密码
- [ ] 服务器防火墙只开 80 / 443 / SSH
- [ ] HTTPS 已配置（Let's Encrypt）
- [ ] 数据库定期备份到异地
- [ ] 宝塔面板改默认端口 + 强密码

**完事。** 静屿已正式上线。🌿

---

## 附：start.py 命令速查（自 README 迁入）

| 命令 | 行为 |
|---|---|
| `python start.py` | 后台启动，默认生产模式（FastAPI :5000 单进程；`static/dist/` 不存在时自动 `npm install + npm run build`，需 Node.js 18+） |
| `python start.py start` | 同上 |
| `python start.py --prod` | 显式生产模式（与默认行为一致，加不加效果一样） |
| `python start.py --dev` | 应用/开发模式：Vite :5000（HMR 热更新，用户入口）+ FastAPI :5001（API）；Vite proxy 把 `/api` / `/static` / `/admin` / `/docs` / `/openapi.json` 转发到 :5001；`frontend/node_modules` 不存在时自动 `npm install`（约 7 分钟，仅首次） |
| `python start.py stop` | 优雅停止（同时停 FastAPI + Vite） |
| `python start.py restart` | 重启（默认生产模式） |
| `python start.py status` | 查看状态（FastAPI / Vite 两个进程的 PID + 端口） |
| `python start.py fg` | 前台运行（systemd / 调试用，关终端即停；默认生产模式，可加 `--dev` 切应用模式） |
| `python start.py build` | 仅构建前端到 `static/dist/`（不启动服务；自动 `npm install + npm run build`） |
| `python start.py --init-db` | 启动前重置数据库 |

PID 文件：`run/healing.pid`（FastAPI）+ `run/vite.pid`（Vite）；日志：`logs/healing.log` + `logs/vite.log`。
