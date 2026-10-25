# HANDOFF — 静屿项目交接说明

> 写给接手这个项目的下一个 AI（Cursor / Copilot / Devin / 任何 Agent）。
> 本文 = 项目元信息 + 关键决策 + 踩坑清单；完整文档地图见 [README.md](README.md)。

> **当前版本：v2.6.2（2026-10-25）**。全部版本变更历史见 [CHANGELOG.md](CHANGELOG.md)；本文只保留交接所需的当前信息。

---

## 0. 你正在接手什么

**项目名**：静屿（代号，可改）
**类型**：治愈系身心疗愈 Web 应用
**性质**：非商业 / 纯治愈 / 隐私边界清晰 / 轻运营
**代码体量**：约 2 500 行 Python（FastAPI 纯 API 后端 + SPA fallback）+ Vue 3 SPA 工程化前端（`frontend/`，约 3 000 行 `.vue`/`.js`）
**当前阶段**：v2.6.2（2026-10-25）——移除 AI 树洞、新增静屿角落、身心调理推荐、八段锦跟练打卡 + B 站跟练视频、好物橱窗；本轮完成全量 bug 修复与性能优化（听曲露水、资料保存、私密日记留言、输入边界、N+1、启动 IO）。更早的版本细节统一见 [CHANGELOG.md](CHANGELOG.md)，本文不再重复。当前状态与已知问题见 [PROJECT_STATE.md](PROJECT_STATE.md)。

---

## 1. 30 秒跑起来

```bash
cd <项目根目录>
pip install -r requirements.txt
python start.py
# 浏览器打开 http://127.0.0.1:5000
# v2.3.2 起：默认 = 生产模式（FastAPI :5000 单进程），dist 不存在则自动 npm install + npm run build
```

服务管理：
```bash
python start.py start     # 后台启动（v2.3.2 起默认 = 生产模式，FastAPI :5000 单进程，dist 不存在则自动构建）
python start.py --prod    # 后台启动（兼容别名，默认就是生产模式，加不加效果一样）
python start.py --dev     # 应用/开发模式（Vite :5000 HMR + FastAPI :5001，前后端一起起，本地开发用）
python start.py stop      # 停止（同时停 FastAPI + Vite）
python start.py restart   # 重启（默认生产模式）
python start.py status    # 查 PID + 端口（显示 FastAPI / Vite 进程状态）
python start.py fg        # 前台运行 FastAPI（systemd / 调试；fg 默认生产模式，可加 --dev 切应用模式）
python start.py build     # 构建前端到 static/dist/（自动 npm install + npm run build）
python start.py --init-db # 启动前重置数据库
```

> 📌 **端口策略**（用户始终访问 :5000，由 `start.py` 自动切换）：
> - **生产模式**（默认，v2.3.2 起）：FastAPI 监听 :5000（从 `.env` 读 `QI_PORT`），Vite 不运行，需 `static/dist/` 已构建；**`dist 存在检测`**——`static/dist/index.html` 不存在则自动 `npm install + npm run build`（`自动构建`，需 Node.js 18+）；**服务器部署 2 步**：① 上传代码 ② `python start.py`（首次自动构建，之后秒启）
> - **应用模式**（`--dev`）：Vite 监听 :5000（用户入口，HMR 热更新）+ FastAPI 改听 :5001（API 后端，由 `start.py` 设置 `QI_PORT=5001`）；Vite proxy 把 `/api`、`/static`、`/admin`、`/docs`、`/openapi.json` 转发到 :5001；自动检测 `frontend/node_modules` 不存在则 `npm install`（约 7 分钟，仅首次）
> - 详见 [HANDOFF §5.9](#59-为什么开发模式让-vite-占5000-fastapi-改50012026-07-19-加) 决策 + [§6.16](#616-fastapi-代理转发-vite-内部路径含特殊字符失败2026-07-19-加) 踩坑

**秘密后台**：`http://127.0.0.1:5000/admin/login`（默认入口；`/admin` 会 302 到 `/admin/`）
- 首次启动会自动创建管理员 `admin`，密码**随机生成并写入 `logs/healing.log`**（看 `[ADMIN] password :` 一行）
- 强烈建议在 `.env` 里设置 `QI_ADMIN_USERNAME` + `QI_ADMIN_PASSWORD` 固定一个强密码
- 不在任何前台页面放链接，纯粹靠 URL 入口
- 本机测试如需固定密码，在 `.env` 设 `QI_ADMIN_PASSWORD` 后重启；**不要把任何真实密码写进文档或提交到仓库**。

**GitHub**：`https://github.com/sunday-lil/jingyu`（public, MIT 友好，私有项目只发了一次）

**前端开发模式**（2026-07-19 Vue 3 重构后；v2.3.2 起 `python start.py` 默认走生产模式，开发需显式 `--dev`）：

**推荐：`python start.py --dev` 一键起**（应用模式：自动 npm install + 启动 Vite :5000 + FastAPI :5001）
```bash
python start.py --dev   # 应用/开发模式：自动起 Vite :5000（用户入口）+ FastAPI :5001（API）
                        # frontend/node_modules 不存在时自动 npm install（约 7 分钟，仅首次）
# 浏览器打开 http://127.0.0.1:5000（Vite dev server，HMR 热更新）
```

> ⚠️ **v2.3.2 行为变更**：`python start.py`（无参数）默认走**生产模式**（FastAPI :5000 单进程，需 dist 已构建，不存在则自动 `npm install + npm run build`）。开发需显式 `python start.py --dev`（Vite :5000 + FastAPI :5001，前后端一起起的「应用模式」）。`--prod` 改为兼容别名（默认就是生产模式）。

**备选：手动分两个终端**（调试时方便看各自日志）
```bash
# 终端 1：FastAPI（应用模式手动设置 QI_PORT=5001）
$env:QI_PORT="5001"; python start.py fg --dev   # Windows PowerShell
# 或：QI_PORT=5001 python start.py fg --dev      # Linux/macOS

# 终端 2：Vite dev server
cd frontend
npm install         # 首次：含 three.js 大包，约 7 分钟
npm run dev         # Vite dev server :5000
```
- dev proxy `/api` / `/static` / `/admin` / `/docs` / `/openapi.json` → FastAPI `:5001`（[frontend/vite.config.js](../frontend/vite.config.js)）
- 生产（默认，部署用）：`python start.py` → dist 不存在则自动构建 → FastAPI :5000 单进程 SPA fallback（详见 [docs/DEPLOYMENT.md](DEPLOYMENT.md)「前端构建」）

---

## 2. 技术栈（已定，不要再讨论）

| 层 | 选型 | 备注 |
|---|---|---|
| 后端 | **FastAPI 0.115+** | 纯 API + SPA fallback（2026-07-19 重构后不再渲染前台页面，仅 `/admin/*` 后台保留 SSR） |
| ORM | **SQLAlchemy 2.0** | `Base` + `Session`，不用 Alembic |
| DB | **SQLite** | 单文件 `data/healing.db`，将来可换 MySQL |
| 模板 | **Jinja2**（仅后台 `/admin/*`） | 2026-07-19 Vue 3 重构后，前台不再用 Jinja2，仅后台 SSR 保留 |
| 静态 | **FastAPI StaticFiles** | `/static/*` 一条命令挂载；Vue 构建产物在 `/static/dist/` |
| 前端 | **Vue 3 `<script setup>` + Vite 5** | 2026-07-19 全站重构，从原生 HTML/CSS/JS 迁移到 Vue 3 SPA |
| 前端路由 | **Vue Router 4** | 16 条业务路由 + 404 catch-all，`requiresAuth` 守卫 |
| 前端状态 | **Pinia** | user store（cookie session 模式，不存 token） |
| 前端样式 | **Tailwind CSS 3.4** | 治愈系色彩 token + 动画（breathe/float/fade-up） |
| 前端动效 | **GSAP 3.12 + @vueuse/motion 2.2** | 入场 stagger + 呼吸动效，`prefers-reduced-motion` 降级 |
| 前端 3D | **Three.js 0.168** | 4 个治愈系 3D / Canvas 组件群（v2.2 PBR 升级版，v2.3.3 Safari 兼容增强）：① [FlowerField.vue](../frontend/src/components/FlowerField.vue) 3D 花田 v2（自定义 `BufferGeometry` 立体花瓣 + `MeshPhysicalMaterial` + `UnrealBloomPass` + `OrbitControls` + `raycaster` 点击花语）；② [AmbientBackground.vue](../frontend/src/components/AmbientBackground.vue) 全局氛围背景 v2（Canvas2D 柔光 sprite + 鼠标排斥 + Three.js 双层粒子 + 滚动视差 + 轻量 Bloom）；③ [HeroScene.vue](../frontend/src/components/HeroScene.vue) 首页浮岛雾海 v2（`LatheGeometry` 浮岛 + 递归樱花树 + PBR 水面 shader + `UnrealBloomPass` + `OrbitControls` + `raycaster` 飞入；v2.3.3 **iOS 降级**：**Bloom 降级** + **PMREM 降级** + `webglcontextlost` 上下文恢复）；④ [AudioVisualizer.vue](../frontend/src/components/AudioVisualizer.vue) 音波可视化 v2（4 模式 wave/mirror/radial/particles + 节拍检测 + 频响颜色 + 点击切换）。配套 [utils/visual.js](../frontend/src/utils/visual.js) 能力检测（v2.3.3 **hasWebGL 重写** + `getWebGLCaps` / `isSafari` / `isIOS`）+ [utils/three-helpers.js](../frontend/src/utils/three-helpers.js) PBR 工具集（v2.2 加，9 个共享函数；v2.3.3 加 `webglcontextlost` / `webglcontextrestored` 事件监听处理 **WebGL 上下文丢失**）+ [SceneHint.vue](../frontend/src/components/SceneHint.vue) 交互指引横幅 + [SceneControls.vue](../frontend/src/components/SceneControls.vue) 视图控制工具栏。全部支持 SVG / CSS 静态降级 + `prefers-reduced-motion` + `OrbitControls` 拖拽旋转 / 滚轮缩放 + `raycaster` 点击拾取 |
| 前端 emoji | **Iconify + @iconify-json/twemoji**（v2.3.3 加） | [EmojiIcon.vue](../frontend/src/components/EmojiIcon.vue) 离线 **SVG emoji** 组件，解决 Safari Apple Color Emoji 与系统 emoji 字体风格差异，确保 **跨浏览器一致**；已替换 AppLayout.vue + ProfileView.vue 所有 emoji |
| 前端 HTTP | **axios 1.7** | `baseURL=/api`，`withCredentials=true`，401 自动跳登录 |
| 密码哈希 | **bcrypt 4.x**（直接用，不用 passlib） | passlib 与 4.x 不兼容 |
| 日记存储 | **明文 `diaries.content`**（v2.3 起） | **不是**端到端加密；`content_encrypted` 仅为老库兼容字段，新数据不再写入。后台 API 只返回统计、不返回正文，但数据库层面无加密保护 |
| 会话 | **itsdangerous URLSafeTimedSerializer** | 签名 cookie，HttpOnly + SameSite=Lax |
| 启动 | **uvicorn** | `app.main:app` |

**前端字体依赖**（2026-07-19 重构后）：Vue 3 SPA 用 [frontend/src/assets/styles/main.css](../frontend/src/assets/styles/main.css) 的系统字体栈 `"PingFang SC", "Microsoft YaHei"`，**零网络请求**，不再依赖任何 Google Fonts 镜像。后台 `/admin/*` SSR 仍走旧 [templates/admin/_base.html](../templates/admin/_base.html) 的 `fonts.loli.net` 镜像 + 系统字体兜底。

**不要做的事**：
- ❌ 引入 React / Angular / Svelte —— Vue 3 已选定，不要再讨论
- ❌ 引入 Alembic —— 改完模型重启即可，`init_db()` 自动建表
- ❌ 把 `passlib` 拉回来 —— 用 `app/utils/crypto.py` 里直接调 bcrypt 的版本
- ❌ 在 Vue SPA 之外另起前端框架 —— 后台 `/admin/*` 保留 Jinja2 SSR 是有意为之（独立隔离）

---

## 3. 项目结构

```
webwrold/
├── start.py                  ← 服务管理脚本（start/stop/restart/status/fg/build；默认生产模式 FastAPI :5000，--dev 走双进程开发模式）
├── README.md                 ← 产品首页 + 开发者速查
├── AGENTS.md                 ← AI/自动化开发者的硬性工作规则
├── .env.example              ← 环境变量模板
├── requirements.txt
│
├── app/
│   ├── main.py               ← FastAPI 入口（lifespan + 路由注册 + 静态挂载）
│   ├── config.py             ← Pydantic Settings（从 .env 读，QI_* 前缀）
│   ├── database.py           ← SQLAlchemy engine + Session + init_db() + 字段迁移
│   ├── deps.py               ← get_db / get_current_user / get_current_admin
│   ├── security.py           ← session 签名 + cookie 读写
│   ├── seed.py               ← 5 音曲目 + 商店物品 + 首个管理员 种子
│   │
│   ├── models/               ← 一张表一个文件（12 张表）
│   │   ├── user.py           ← 含 is_admin / avatar / leaves
│   │   ├── diary.py          ← 明文 content + 遗留 content_encrypted
│   │   ├── mood.py / music.py / energy.py
│   │   ├── garden.py         ← ShopItem / GardenItem / UserFlower
│   │   ├── encouragement.py / notification.py
│   │   ├── therapy.py        ← BaduanjinCheckin / TherapyInterest
│   │   └── __init__.py       ← 统一 import（init_db 依赖这里）
│   │
│   ├── schemas/              ← Pydantic v2 入参/出参
│   │   ├── auth.py / diary.py / mood.py / music.py / energy.py
│   │   ├── admin.py          ← 后台统计/用户/系统 Pydantic
│   │   └── ai.py             ← AI 3 场景 Pydantic（AIEncouragementIn / AIHealingIn / AIMusicRecommendIn/Out）
│   │
│   ├── routers/              ← 一个领域一个文件
│   │   ├── pages.py          ← 4 个旧书签 302 兼容重定向（不做 SSR 页面）
│   │   ├── auth.py / music.py / diary.py / mood.py / energy.py / garden.py
│   │   ├── therapy.py        ← 身心调理 / 八段锦打卡 / 好物预约
│   │   ├── notification.py   ← 站内通知（单数文件名）
│   │   ├── profile.py        ← 个人主页 / 头像上传
│   │   ├── admin.py          ← 后台 API（/api/admin/*）
│   │   ├── admin_pages.py    ← 后台 SSR 页面（/admin/*）
│   │   └── ai.py             ← /api/ai/* 3 个 AI 端点（全部需登录 + 全部有降级）
│   │
│   ├── services/             ← 业务逻辑层（routers 不直接调 model）
│   │   ├── energy_service.py ← 能量获取 + 单日上限 + 兑换 + 徽章
│   │   ├── diary_service.py  ← 漂流瓶随机抽取 + 鼓励语 + 通知
│   │   ├── flower_service.py ← 花朵生命周期（浇水 / 枯萎 / 拾叶）
│   │   ├── therapy_service.py ← 问题→曲/八段锦/香囊/手串/食疗 + 打卡 + 预约
│   │   ├── mood_service.py   ← 日历 + 趋势 + 连胜
│   │   └── ai_service.py     ← NVIDIA NIM API 调用 + 降级处理
│   │
│   └── utils/
│       ├── constants.py      ← YIN_INFO / MOOD_INFO / 商店 / 徽章 / 上限
│       └── crypto.py         ← bcrypt 哈希 + 遗留 Fernet 工具（当前日记不再加密）
│
├── templates/                ← Jinja2（v2.4.2 死模板清理后仅剩后台，前台已全部 Vue 3 SPA）
│   └── admin/                ← 秘密后台模板（继承 admin/_base.html）
│       ├── _base.html        ← 暗色侧栏 + 金边 logo
│       ├── login.html        ← 单独登录页
│       ├── dashboard.html    ← 概览（6 统计卡 + 最近活动）
│       ├── users.html        ← 用户列表（搜索/分页/重置密码/代建）
│       ├── user_detail.html  ← 用户详情（统计/能量调整/最近活动）
│       ├── logs.html         ← tail 日志（级别过滤/自动刷新）
│       └── system.html       ← 系统信息 + 一键清 pycache
│
├── static/
│   ├── dist/                 ← 前端构建产物（npm run build 输出，git 忽略；SPA fallback 服务于此）
│   ├── css/                  ← style.css 入口 + 7 个模块（00-variables ~ 07-admin）
│   ├── js/
│   │   ├── app.js            ← 后台用全局（fetch / toast 等）
│   │   └── pages/            ← 后台页面脚本（admin_*；前台脚本已随 SSR 模板在 v2.4.2 删除）
│   ├── audio/tracks/         ← 曲目音频槽位（22 个一曲一文件，同名覆盖接真实音频；见 docs/曲目清单.md）
│   ├── images/               ← 五音封面（5 张 SVG）
│   ├── img/promo/            ← README 宣传截图（GitHub raw 直链用）
│   └── uploads/              ← 用户头像上传目录
│
├── frontend/                 ← Vue 3 SPA 源码（2026-07-19 v2.0 重构加，详见 §5.8）
│   ├── package.json          ← 依赖：vue/vue-router/pinia/axios/gsap/@vueuse/motion/three；devDeps：vite/@vitejs/plugin-vue/tailwindcss
│   ├── vite.config.js        ← dev :5000 + proxy /api /static /admin /docs /openapi.json → :5001；build outDir ../static/dist；manualChunks（three-vendor / gsap-vendor / vue-vendor 三 chunk）
│   ├── tailwind.config.js    ← 治愈系色彩 token（mist/ink/五音色/accent）+ 动画（breathe/float/fade-up）
│   ├── index.html
│   └── src/
│       ├── main.js / App.vue
│       ├── router/index.js   ← 16 条业务路由 + 404 + requiresAuth 守卫
│       ├── stores/user.js    ← Pinia user store（cookie session 模式，不存 token）
│       ├── api/index.js      ← axios 实例（baseURL=/api，withCredentials=true，401 自动跳登录；拦截器已解包 response.data）
│       ├── assets/styles/main.css
│       ├── data/islandGuide.js ← 首页指南 / 模块奖励 / 个人主页指南共享文案
│       ├── components/
│       │   ├── AppLayout.vue        ← 桌面顶部导航 + 移动端底部 tabbar（768px 断点）+ 挂载 AmbientBackground
│       │   ├── FlowerField.vue      ← Three.js 3D 花田（60 朵花 × 5 瓣；PBR + Bloom + OrbitControls + raycaster；异步加载）
│       │   ├── AmbientBackground.vue ← 全局氛围背景（CSS 雾气 + Canvas2D 光点 + Three.js 粒子层三层渐进增强）
│       │   ├── HeroScene.vue        ← 首页 3D 浮岛雾海（LatheGeometry + 樱花树 + PBR 水面 + SVG 降级）
│       │   ├── AudioVisualizer.vue  ← 4 模式音波可视化 + 节拍检测（挂在 MusicDetailView）
│       │   ├── SceneHint.vue        ← 3D 交互指引横幅
│       │   ├── SceneControls.vue    ← 3D 视图控制工具栏
│       │   └── EmojiIcon.vue        ← 离线 twemoji SVG emoji（跨浏览器一致）
│       ├── utils/
│       │   ├── visual.js      ← 视觉能力检测 + smartRAF
│       │   └── three-helpers.js ← Three.js PBR 工具集（9 个共享函数）
│       └── views/             ← 17 个视图（Home / auth / music / diary / mood / garden / profile / notification / NotFound）
│
├── docs/                      ← 全部项目文档（根目录仅留 README / AGENTS）
│   ├── README.md              ← 【文档地图】各文档职责与阅读顺序
│   ├── HANDOFF.md             ← 【当前文件】AI 交接说明
│   ├── PROJECT_STATE.md       ← 当前状态快照
│   ├── CHANGELOG.md           ← 全部版本变更记录
│   ├── ARCHITECTURE.md / DEPLOYMENT.md / DEVELOPMENT.md
│   ├── 曲目清单.md            ← 真实音频下载指引（22 首）
│   └── HOME_REDESIGN_PROPOSAL.md ← 首页重构设计稿（第一期已落地）
│
├── data/healing.db           ← SQLite（git 忽略）
├── run/healing.pid           ← 后台进程 PID
└── logs/healing.log          ← 后台进程日志（首管密码仅首次生成时出现）
```

---

## 4. 实现阶段（摘要）

> 逐版本细节（v2.2.2 → v2.6.2）统一见 [CHANGELOG.md](CHANGELOG.md)。这里只列对交接有影响的主线。

| 阶段 | 主要内容 | 代码落点 |
|---|---|---|
| v2.0（2026-07-19） | 全站从 Jinja2 SSR 迁移到 Vue 3 SPA + Vite；FastAPI 变成纯 API + SPA fallback | [frontend/](../frontend/) / [app/main.py](../app/main.py) |
| v2.1 / v2.2（07-20） | 三层渐进增强视觉；PBR 渲染 + Bloom + OrbitControls + raycaster + SceneHint/SceneControls | `frontend/src/components/*Scene*` / [three-helpers.js](../frontend/src/utils/three-helpers.js) |
| v2.2.3（07-25） | 三档响应式 + iOS `100dvh`/safe-area + fullscreen 路由 + 3D 几何降档 | [AppLayout.vue](../frontend/src/components/AppLayout.vue) / `main.css` |
| v2.3（07-25） | 六模块四字名 + 露水/落叶双资源 + 花朵生命周期 + 通知 + 个人主页 + 西洋曲谱 | [energy_service.py](../app/services/energy_service.py) / [flower_service.py](../app/services/flower_service.py) / [notification.py](../app/routers/notification.py) / [profile.py](../app/routers/profile.py) |
| v2.4（08-10 → 08-16） | 一天多条心情 + 头像/昵称/图片上传 + 花坊扩充 + 罗素情绪环 + 徽章赠落叶 | [mood_service.py](../app/services/mood_service.py) / [profile.py](../app/routers/profile.py) / [constants.py](../app/utils/constants.py) |
| v2.5.0（09-12） | 首页理念卡 + 模块奖励行 + 岛上指南手风琴 + `islandGuide.js` 数据共享 | [HomeView.vue](../frontend/src/views/HomeView.vue) / [islandGuide.js](../frontend/src/data/islandGuide.js) |
| v2.5.1（09-12） | GSAP 列表动画改到 fetch 成功后 + querySelector 守卫 | [DiaryListView.vue](../frontend/src/views/diary/DiaryListView.vue) / [ShopView.vue](../frontend/src/views/garden/ShopView.vue) |
| v2.5.2（09-12） | 16 首真实音频入库 + 启动时按 MP3 实际时长自动校准 `musics.duration` | [seed.py](../app/seed.py) |
| v2.5.3（09-13） | 日记海岸改名 + 西洋曲谱并入六宫格 + 打卡可删除 + AI 模型切 `z-ai/glm-5.3-flash` | [music.py](../app/routers/music.py) / [mood.py](../app/routers/mood.py) / [ai_service.py](../app/services/ai_service.py) |
| v2.6.0（10-18） | 删除 AI 树洞 + 静屿角落 + 身心调理推荐 + 八段锦打卡 + 好物橱窗 | [therapy_service.py](../app/services/therapy_service.py) / [therapy.py](../app/routers/therapy.py) / [CornerView.vue](../frontend/src/views/diary/CornerView.vue) |
| v2.6.1（10-18） | 八段锦结果卡嵌入 B 站跟练视频 + CSP `frame-src` | [TherapyView.vue](../frontend/src/views/music/TherapyView.vue) / [app/main.py](../app/main.py) |
| v2.6.2（10-25） | 全量 bug 修复：听曲露水 422、资料保存 session、`/admin` 404、私密日记留言、输入边界、N+1/启动 IO 优化 | [deps.py](../app/deps.py) / [diary.py](../app/routers/diary.py) / [MusicDetailView.vue](../frontend/src/views/music/MusicDetailView.vue) |

**当前代码规模**：Python 约 3k 行；Vue/JS 约 3k 行；12 张表；约 70 个 API 端点（含后台 13 个）。

---

## 5. 关键设计决策（带原因）

### 5.1 为什么 v2.3 起日记改为明文（以及隐私边界）
- **历史原因**：v2.0–v2.2 曾做客户端加密（PBKDF2 + Fernet），但密钥完全依赖用户密码，密码丢失 = 日记永久不可读，且前端加密链路复杂、与「拾瓶后直接读」的产品体验冲突。
- **v2.3 决策**：日记改为明文 `diaries.content`，取消密码保护；`content_encrypted` 与 `User.encryption_salt` 仅保留兼容老库，新数据不再写入。
- **当前隐私边界**：
  - 公开漂流瓶：`is_public=True` 的正文可被其他登录用户拾取阅读；
  - 私密日记：仅作者本人可读（API 按 `user_id` 过滤）；
  - 后台 API 只返回日记数量 / 最近时间，不返回正文；但**数据库层面没有加密**，拥有 DB 文件的人可以读明文。文档与产品文案不得再声称「端到端加密」。
- **升级方向**（未实施）：若要恢复强隐私，应做服务端不可见的端到端加密，并单独处理「忘记密码 = 日记不可恢复」的产品提示。

### 5.2 为什么最终选择 SPA（v2.0 重构）
- **早期选择 SSR 的理由**：页面少、交互轻、SEO 友好、首屏快；后台至今仍保留 Jinja2 SSR，正是这个理由的延续。
- **后来改 SPA 的原因**：功能膨胀到 6 大模块 + 通知 + 个人主页后，一页一个 JS、状态散落、路由靠 302，新增页面要改 HTML + JS + pages.py + 文档四处；Vue 3 SPA 用组件化 + Pinia + Vue Router 一次性解决。
- **结论**：前台 Vue 3 SPA，后台 `/admin/*` 继续 Jinja2 SSR；两套前端刻意隔离，详见 [ARCHITECTURE §1.1](ARCHITECTURE.md)。

### 5.3 为什么 `energy_service.py` 用 `db.query().update()` 而不是 `user.total_energy +=`
- FastAPI 一次请求一个 session，但 `User` 对象在依赖链里可能被多次 `db.get()` 加载
- 跨 session 的对象属性赋值**不会写回 DB**（这是历史踩坑，见 [HANDOFF §6.7](#67-能量累加一定要用-queryupdate)）
- 一律走显式 `UPDATE` SQL

### 5.4 为什么心情打卡改为一天多条（`add_checkin`）
- v2.4 起移除 `mood_checkins` 的 `(user_id, check_date)` 唯一约束，一天可以记录多次心情（情绪是流动的）。
- `mood_service.add_checkin()` 每次 INSERT 新行；`get_today_moods()` 返回今日全部记录；趋势 / 罗素环按多条取平均或统计次数。
- 旧 `upsert_checkin` / 「每天覆盖」逻辑已废弃，不要按旧文档实现。

### 5.5 启动脚本用 `start.py` 而不是 `python -m uvicorn`
- 用户场景是「宝塔面板一键部署」，需要后台进程 + PID 文件 + 日志
- `start.py` 跨平台（Windows `taskkill` / Unix `SIGTERM`）
- 默认后台启动（关掉终端服务不死）

### 5.6 秘密后台的设计边界
> 原 ARCHITECTURE.md 写「不做后台管理界面」，但**用户必须能找回密码 / 查日志 / 清缓存**。所以加了"秘密后台"。

- **「秘密」怎么实现**：
  - URL 前缀可在 `.env` 改（默认 `/admin`，可改成 `/sanctuary` / `/quiet-house` 等）
  - **不在前台 nav / footer / 任何角落放链接**（连「联系管理员」也不放）
  - robots meta `noindex,nofollow`
  - 用户必须知道 URL + 管理员账号才能进
- **「管理」与「窥视」的分界**：
  - 能做：看昵称 / 能量 / 创建时间 / 日记数量（不读内容） / 重置密码 / 删账号 / 调能量 / 看日志
  - API 层不做：读日记正文、导出全库
  - ⚠️ 注意：日记当前是明文存储，后台 API 虽不返回正文，但**数据库本身没有加密**——不要把「后台看不到」误写成「端到端加密」。
- **为什么用 SQLAlchemy 显式 `.update()` 而不是 `user.total_energy = ...`**：见 [§6.7](#67-能量累加一定要用-queryupdate)
- **为什么自动迁移字段而不上 Alembic**：见 [§6.10](#610-加新字段用-lightweight-migrate-不引-alembic)

### 5.7 为什么 AI 接入用 NVIDIA NIM API + 渐进增强降级（2026-07-17 加）
- **选 NVIDIA NIM**：[build.nvidia.com](https://build.nvidia.com) 提供**免费** API key，OpenAI 兼容格式接入成本几乎为零，符合本项目「非商业纯治愈」调性
- **模型当前为 `z-ai/glm-5.3-flash`**（2026-09-13 切换）：原 `meta/llama-3.1-8b-instruct` 已于 2026-08-26 从 NVIDIA NIM 下架（410 Gone）。`.env` 的 `QI_AI_MODEL` **会覆盖** `config.py` 默认值，换模型必须两处同步改。glm 是 reasoning 模型，`max_tokens` 需给足 900–1200，否则思考内容会吃光配额并静默返回 `content=None`。
- **OpenAI 兼容**：将来想换其他厂商（DeepSeek / 智谱 / 自部署 vLLM）只改 `QI_AI_BASE_URL` + `QI_AI_MODEL`，不动业务代码
- **降级而非报错**：AI 是「锦上添花」不是核心功能，**未配置 key 或调用失败时返回 200 + `available:false` + 治愈系友好提示**（**不报 500**）。前端拿到 `available:false` 仍正常显示文案。这保证：① 没拿到 key 的部署方也能跑；② NVIDIA 限流时业务不中断；③ 用户感知不到「故障」，只感知「AI 在休息」
- **AI 树洞已移除**：v2.6.0 删除对话端点、`chat_history_service`、树洞徽章与聊天历史；不公开的碎碎念改存「静屿角落」。
- **日记预览只取前 120 字**：漂流瓶 AI 鼓励语调用时，把作者日记**截断到前 120 字**再发给 AI，避免长文本消耗 token + 减少隐私暴露面
- **温柔语气系统提示词**：3 个场景的 system_prompt 统一约定「不诊断不开药、危机情况引导求助专业资源、温柔倾听」，与项目治愈系调性一致

详见 [app/services/ai_service.py](../app/services/ai_service.py) 顶部的 4 个系统提示词常量。

### 5.8 为什么前端选 Vue 3 + Vite + Pinia + Tailwind + GSAP（2026-07-19 加）
- **为什么换掉「原生 HTML/CSS/JS + Jinja2 SSR」**：项目迭代到 4 Phase + 后台 + AI 后，前端逻辑膨胀（每个页面一套 HTML + JS，最终 17 个视图），状态管理散落在各 `static/js/pages/*.js`，路由靠后端 302 + 浏览器刷新，新增页面要改 4 处（HTML + JS + pages.py + 速查表）。Vue 3 SPA 一次解决：组件化复用、Pinia 集中状态、Vue Router 客户端路由、Vite HMR 热更新
- **为什么选 Vue 3 而不是 React**：① Vue 3 `<script setup>` 语法对单人项目最简洁；② Tailwind + Vue 单文件组件天然契合治愈系「样式与模板同视图」的写法；③ Pinia 是 Vue 官方推荐 store，比 Redux 心智负担低；④ 国内 Vue 生态成熟，文档中文友好
- **为什么选 Vite 5**：① dev server 启动 < 1s（vs webpack 10s+）；② HMR 真正热更新（改 .vue 即刻生效，不刷新页面）；③ build 用 Rollup，产物体积小；④ 配置极简（`vite.config.js` 不到 30 行）
- **为什么选 Pinia 而不是 Vuex**：Pinia 是 Vue 3 官方推荐，TypeScript 友好，API 更简洁（无 mutations），tree-shaking 友好
- **为什么选 Tailwind CSS**：① 治愈系配色用 `tailwind.config.js` token 化（mist/ink/五音色/accent），改色改一处全局生效；② 不用写自定义 CSS 类，组件样式内联在 `<template>` 里，与 Vue SFC 同视图；③ purge 后 CSS 体积 < 20KB
- **为什么选 GSAP**：① Netflix/Spotify 级动效（stagger / scrub / timeline）原生 CSS 做不到；② Vue 3 `<script setup>` 里 `gsap.from()` 配合 `onMounted` 自然；③ 自动检测 `prefers-reduced-motion` 降级；④ `@vueuse/motion` 补充轻量入场动效
- **为什么保留 Jinja2 后台 SSR**：① 后台是「管理工具」不需要 SPA 体验；② 后台样式完全独立（`07-admin.css` 暗色侧栏），与前台治愈系调性冲突；③ Vue 3 重构范围聚焦前台用户体验，后台保留 SSR 减少改动面
- **cookie session 不变**：Vue 3 重构只动前端，后端鉴权机制（cookie session + nickname 登录 + 直接返回 user 对象）保持不变，前端 userStore 只缓存 user 对象到 localStorage，**不存 token**——这是与「JWT + localStorage」模式的关键差异，避免 XSS 拿 token 的风险
- **SPA fallback 而非双服务器**：生产模式只跑 FastAPI :5000，Vue 构建产物放 `static/dist/`，FastAPI 兜底返回 `index.html`。不引入 Nginx 双服务器或 Node.js 生产环境，保持「单进程三角色（API + 静态 + SPA fallback）」简化

详见 [frontend/](../frontend/) + [docs/ARCHITECTURE.md](ARCHITECTURE.md)「前端架构」节。

### 5.9 为什么开发模式让 Vite 占 :5000，FastAPI 改 :5001（2026-07-19 加）
- **背景**：v2.0 Vue 3 重构初版用「FastAPI :5000 + Vite :5173 + FastAPI 反代 Vite」方案，但实际跑起来浏览器报 `SyntaxError: Unexpected token '.'`，定位到是 Vite 内部路径 `/@id/__x00__plugin-vue:export-helper` 含 null 字符转义（`__x00__`）+ 冒号（`plugin-vue:export-helper`），httpx 转发时这些特殊字符被破坏，返回的 JS 文件首行变成 `<` 开头的 HTML 错误页，浏览器当 JS 解析就报错。详见 [§6.16](#616-fastapi-代理转发-vite-内部路径含特殊字符失败2026-07-19-加) 踩坑
- **决策**：开发模式让 **Vite 直接占 :5000**（用户访问入口），**FastAPI 改听 :5001**（API 后端，由 [start.py](../start.py) 设置 `QI_PORT=5001`），Vite proxy 把 `/api`、`/static`、`/admin`、`/docs`、`/openapi.json` 转发到 :5001
- **为什么不让 Vite 仍占 :5173 + FastAPI :5000**：① 用户要记两个端口（:5173 看前端 / :5000 看 API），心智负担大；② Vite proxy 转发到 FastAPI 的方向是稳定的（FastAPI 是普通 HTTP JSON，无特殊字符），但反过来 FastAPI 转发到 Vite 就会踩坑
- **生产模式不变**：dist 已构建时 FastAPI 监听 :5000（从 `.env` 读 `QI_PORT`），Vite 不运行，FastAPI 提供 SPA fallback + API + 静态资源
- **用户体验**：用户始终访问 `http://127.0.0.1:5000`，无需关心是应用还是生产模式，[start.py](../start.py) 自动切换
- **start.py 当前行为（v2.3.2 起）**：默认生产模式（FastAPI :5000，dist 不存在则自动构建）；`--dev` 才起 Vite :5000 + FastAPI :5001；`--prod` 是兼容别名。`stop` 同时停两个进程，`status` 显示两个进程，`build` 只构建前端。
- **vite.config.js 改动**：① dev server port 5173 → 5000；② proxy target :5000 → :5001；③ 移除 `hmr.clientPort`（Vite 直接占 :5000 后 HMR 走本地不需要）；④ 新增 `/docs` 和 `/openapi.json` 代理
- **main.py 改动**：① SPA fallback 移除回退代理到 Vite 的逻辑（开发态不再转发，返回提示页引导用户访问 Vite :5000）；② 新增 `EXT_TO_MIME` 映射（`.js` / `.css` / `.woff2` 等正确设置 `Content-Type`），生产态从 dist 读取静态资源时不再被 Starlette 默认当成 `application/octet-stream` 让浏览器拒绝执行

详见 [start.py](../start.py) + [frontend/vite.config.js](../frontend/vite.config.js) + [app/main.py](../app/main.py)。

### 5.10 为什么视觉增强走「三层渐进增强 + 能力检测 + 异步加载」策略（2026-07-20 加）
- **背景**：v2.0.1 完成 FlowerField.vue 3D 花田后，用户要求进一步提升整体视觉美感，加入 3D / 伪 3D 背景元素和动态视觉效果，但**不能**影响页面加载性能或用户体验，且**必须**为 3D 渲染能力有限的浏览器实现备用机制
- **决策**：用「CSS 永远启用 → Canvas2D 中量级 → Three.js 按需」三层渐进增强策略，每层独立可降级，配合 [utils/visual.js](../frontend/src/utils/visual.js) 能力检测
- **三层分级**：
  - **Layer 1 — CSS（永远启用）**：AmbientBackground 的 3 个 radial-gradient 雾气光斑 + 24s `mistDrift` 动画；AudioVisualizer 降级时的 5 色横条 CSS 动画；HomeView 五音卡片的 `perspective + rotateX/Y + translateZ` 3D 倾斜。零 JS 开销
  - **Layer 2 — Canvas2D（reduced-motion 关闭）**：AmbientBackground 飘浮光点（移动端 24 / 桌面 60）；AudioVisualizer 5 条流动曲线。轻量 CPU 渲染
  - **Layer 3 — Three.js（WebGL + 非 reduced-motion + 非低性能）**：FlowerField 花田（已有）；AmbientBackground 远景粒子层（80 个 sprite）；HeroScene 浮岛雾海（128×128 海面 + 3 浮岛 + 雾 + 80 光点）。GPU 渲染
- **能力检测**：[utils/visual.js](../frontend/src/utils/visual.js) 单次缓存 `hasWebGL()` / `prefersReducedMotion()` / `isMobile()` / `isLowPower()` 结果；`shouldUseThreeJS()` = `hasWebGL && !prefersReducedMotion && !isLowPower`；`shouldUseCanvas()` = `!prefersReducedMotion`
- **降级路径**：
  - HeroScene 不支持 WebGL / reduced-motion / initScene 异常 → 渲染 SVG 静态插画（800×480 viewBox，天空渐变 + 太阳光晕 + 3 个岛 + 3 层波浪 + 5 漂浮点）
  - AudioVisualizer 无 Web Audio API / reduced-motion → 5 色静态横条 CSS 动画（`barBreath` 3.6s）
  - AmbientBackground 无 WebGL / 低性能 → 只显示 CSS 雾气光斑 + Canvas2D 光点（无 Three.js 粒子层）
- **性能保护**：
  - 所有 Three.js 组件用 `defineAsyncComponent(() => import(...))` 异步加载，**不进首屏包**（vite.config.js `manualChunks` 把 `three` + addons 单独打成 `three-vendor` chunk，gzip 约 720KB，仅访问 `/`（HeroScene）或 `/garden`（FlowerField）时按需拉取）
  - Three.js 对象用 `shallowRef` 持有，避免 Vue 深度代理拖累性能
  - `smartRAF(callback)` 在 `document.hidden` 时暂停 rAF、可见时自动恢复，避免标签页隐藏时浪费 GPU
  - 移动端降粒子数（Three.js 80→40，Canvas2D 60→24）、降分辨率（HeroScene 海面 128×128 → 64×64）、降帧率（AudioVisualizer 30fps → 24fps）、降几何精度（v2.2.3 加：HeroScene Lathe/Cylinder 段数 24→16、樱花树递归深度 4→3、花团 Icosahedron detail 2→1；FlowerField 花瓣网格 5×8→4×6、花蕊 Icosahedron detail 2→1、地面圆 64→32、茎圆柱段 6→5；AudioVisualizer 镜像柱 48→32、径向柱 64→32）
  - 所有 Three.js 组件 `onBeforeUnmount` 释放 geometry / material / renderer / 事件监听 / ResizeObserver，避免切走后 WebGL 上下文泄漏
- **Web Audio API 一次性约束**：`createMediaElementSource(audioEl)` 对同一 `<audio>` 元素**只能调用一次**，AudioVisualizer 用 `if (!sourceNode)` 守卫；MusicDetailView 用 `visualizerConnected` ref 标记是否已连接，首次 `playIndex` 时调 `visualizerRef.value.connect(audioEl)`，后续切歌不重连
- **配色一致性**：4 个视觉组件全部用治愈系 5 色（藕粉 `#E8B8C5` / 淡黄 `#E8D5A8` / 青绿 `#A8C5A0` / 雾蓝 `#A8B8C5` / 纯白 `#FAF6F2`）+ 米白 `#F9F6F0` 背景，与 [tailwind.config.js](../frontend/tailwind.config.js) token 一致；AudioVisualizer 5 条曲线对应宫商角徵羽 5 音色
- **为什么不用全屏 shader / 后处理**：① 治愈系调性要「柔和不刺眼」，shader bloom / DOF 过度装饰反而破坏氛围；② 后处理增加 GPU 开销，移动端掉帧；③ 现有 Fog + InstancedMesh + Canvas2D 已足够，性能与视觉平衡

详见 [frontend/src/components/AmbientBackground.vue](../frontend/src/components/AmbientBackground.vue) + [HeroScene.vue](../frontend/src/components/HeroScene.vue) + [AudioVisualizer.vue](../frontend/src/components/AudioVisualizer.vue) + [utils/visual.js](../frontend/src/utils/visual.js)。

### 5.11 为什么 v2.2 走「PBR 渲染管线 + 共享工具集 + 交互指引组件」策略（2026-07-20 加）

- **背景**：v2.1 视觉增强上线后用户反馈两个核心问题：① **交互体验缺失**——用户不知道 3D 场景可以拖拽 / 缩放 / 点击，以为是静态背景；② **视觉粗糙过时**——`PointsMaterial` 方形粒子 + `MeshBasicMaterial` 平面着色 + 无环境映射，整体观感类似 80/90 年代红白机低品质视觉，缺乏现代感与高级感
- **决策**：① 4 个视觉组件全部升级到 PBR（Physically Based Rendering）渲染管线；② 抽出 [utils/three-helpers.js](../frontend/src/utils/three-helpers.js) 集中 9 个共享 PBR 工具函数，避免每个组件重复造轮子；③ 新增 [SceneHint.vue](../frontend/src/components/SceneHint.vue) 交互指引横幅 + [SceneControls.vue](../frontend/src/components/SceneControls.vue) 视图控制工具栏，让用户**第一眼就知道怎么交互**
- **PBR 渲染管线 5 件套**：
  - `ACESFilmicToneMapping`：电影级色调映射，高光不爆，暗部有细节（替代 `LinearToneMapping` 的灰白平淡）
  - `SRGBColorSpace` output：正确伽马校正，颜色不过饱和不发灰
  - `PCFSoftShadowMap`：软阴影，告别锯齿硬边
  - `RoomEnvironment` + `PMREMGenerator`：程序化生成室内环境映射（无外部 HDR 依赖），让 `MeshStandardMaterial` / `MeshPhysicalMaterial` 的反射有真实感
  - `UnrealBloomPass` 后处理：辉光效果让发光物体（花瓣 / 樱花 / 光点）有「柔光」高级感
- **几何升级**：
  - HeroScene 浮岛：`ConeGeometry` 倒锥 → `LatheGeometry` 旋转曲面（3 段贝塞尔曲线轮廓，更自然的岛形）
  - HeroScene 树：`CylinderGeometry` 单柱 → 递归分枝（深 3 级 + 8 个花球 `InstancedMesh`，像真樱花树）
  - HeroScene 水面：`MeshBasicMaterial` 平面 → `MeshStandardMaterial` + `onBeforeCompile` 注入顶点位移 shader（波纹动画 + 反射环境）
  - FlowerField 花瓣：`PlaneGeometry` 4 顶点 → 自定义 `BufferGeometry` 12 顶点立体花瓣（ curvature + 法线）
  - FlowerField 材质：`MeshBasicMaterial` → `MeshPhysicalMaterial`（带 `transmission` 透射 + `sheen` 织物感，花瓣有玉润感）
  - AmbientBackground 粒子：`PointsMaterial` 方形 → `createSoftSpriteTexture` 程序化生成 Canvas2D 径向渐变柔光 sprite + `AdditiveBlending` 加法混合
- **交互升级**：
  - 所有 3D 场景统一 `OrbitControls`（阻尼 + 极角约束 + 禁用 pan + 自动旋转），用户可拖拽旋转 + 滚轮缩放
  - `raycaster` 点击拾取：HeroScene 点击浮岛相机飞入；FlowerField 点击花朵显示花语 toast
  - `SceneHint.vue` 顶部横幅显示「拖拽旋转 · 滚轮缩放 · 点击交互」图标 + 文案，3 秒后自动淡出（`pointer-events: none` 不阻挡交互）
  - `SceneControls.vue` 玻璃拟态工具栏，提供「重置视角」+「自动旋转开关」两个按钮
- **共享工具集**（[utils/three-helpers.js](../frontend/src/utils/three-helpers.js)，9 个函数）：
  - `createRenderer(canvas, alpha)` — ACESFilmic + SRGB + PCFSoft + dpr 上限 2
  - `createEnvironment(renderer)` — RoomEnvironment + PMREM 程序化环境映射
  - `createPostProcessing(renderer, scene, camera)` — EffectComposer + RenderPass + UnrealBloomPass + OutputPass
  - `createOrbitControls(camera, domElement, options)` — 阻尼 + 极角约束 + 禁用 pan + 自动旋转
  - `createKeyLight(scene)` / `createFillLight(scene)` — 主光 + 补光预设
  - `createSoftSpriteTexture(size)` — 程序化 Canvas2D 径向渐变柔光 sprite
  - `disposeObject3D(obj)` / `disposeRenderer(renderer, composer)` — 完整释放 geometry / material / texture / renderer / composer
- **AudioVisualizer 4 模式 + 节拍检测**：v2.1 单一波形 → v2.2 4 种可视化模式（`wave` 流动波形 / `mirror` 镜像柱状 / `radial` 径向频谱 / `particles` 粒子流），点击画布切换 + toast 提示；节拍检测（bass > 1.35× 平均 + > 0.35 阈值）触发粒子爆裂；频响颜色（低频暖色 → 高频冷色）
- **AmbientBackground v2 升级**：Canvas2D 预生成 32×32 柔光 sprite + `source-atop` 合成模式叠加颜色；鼠标 120px 半径内柔和排斥（0.985 阻尼回归）；Three.js 双层粒子（远景 90 + 近景 35）+ `AdditiveBlending`；鼠标跟随相机轻微旋转（仅旋转不位移）+ 滚动视差（远景 `scrollY*0.0008`、近景 `scrollY*0.002`）；轻量 `UnrealBloomPass`（strength 0.3，移动端 0.18）
- **降级路径保留**：v2.1 的三层渐进增强 + SVG / CSS 静态降级 + `prefers-reduced-motion` 自动降级 + 移动端粒子数减半 + dpr ≤ 1.5 全部保留；v2.2 的 PBR 管线在不支持 WebGL 的浏览器自动降级为 v2.1 的 SVG 静态插画
- **构建产物体积**：HeroScene 7.5KB → 13.54KB、FlowerField 单独 chunk 9.94KB、SceneControls 4.5KB、SceneHint 进 HomeView/GardenView 主包；three-vendor 175KB → 719.84KB（含 addons：OrbitControls / EffectComposer / UnrealBloomPass / RoomEnvironment）。首屏不加载，仅访问 `/` 或 `/garden` 时按需拉取

详见 [utils/three-helpers.js](../frontend/src/utils/three-helpers.js) + [SceneHint.vue](../frontend/src/components/SceneHint.vue) + [SceneControls.vue](../frontend/src/components/SceneControls.vue) + 4 个 v2 视觉组件。

---

## 6. 已知坑（必读！）

### 6.1 Pydantic 字段顺序问题
**症状**：`TypeAdapter[typing.Annotated[list[EnergyRecordOut], FieldInfo(...)]] is not fully defined`

**原因**：Pydantic v2 用类型注解，**前向引用**在某些场景下不会自动 `model_rebuild()`

**修复**：
1. `from __future__ import annotations` **不要**加在 schema 文件顶部
2. 任何 Pydantic v2 模型**必须**在 `app/schemas/__init__.py` 用 `BaseModel.model_rebuild()` 强制重建

### 6.2 bcrypt 4.x 与 passlib 不兼容
**症状**：`AttributeError: module 'bcrypt' has no attribute '__about__'`

**原因**：passlib 1.7 用的 `bcrypt.__about__.__version__` 在 bcrypt 4.x 被移除

**修复**：[app/utils/crypto.py](../app/utils/crypto.py) **不**用 passlib，直接 `import bcrypt` + `bcrypt.hashpw()` + `bcrypt.checkpw()`

### 6.3 bcrypt 72 字节限制
**症状**：`ValueError: password cannot be longer than 72 bytes`

**修复**：[app/utils/crypto.py:42-44](../app/utils/crypto.py#L42) 有 `_truncate(password)`，**必须**在所有 hash/verify 之前调用

### 6.4 Jinja2 `TemplateResponse` 新签名
**症状**：`TypeError: cannot use 'tuple' as a dict key (unhashable type: 'dict')`

**原因**：Starlette 升级后 `TemplateResponse` 第一个参数是 `Request`，不是模板名字符串

**修复（强制）**：
```python
# 正确（新 API）
return templates.TemplateResponse(
    request,                  # ← Request 对象作第一个参数
    "template.html",
    {"current_user": user, ...},
)

# 错误（旧 API，已废弃）
return templates.TemplateResponse(
    "template.html",
    {"request": request, ...},  # ← 不要再这样写
)
```
项目里 [app/routers/pages.py](../app/routers/pages.py) 所有页面都用了新 API。

### 6.5 Windows 终端 GBK 编码
**症状**：`UnicodeEncodeError: 'gbk' codec can't encode character '\U0001f33f'`

**根因**：Windows cmd/PowerShell 默认 GBK，emoji 写入 stdout 失败

**修复（3 处协同）**：
1. [app/main.py:11-19](../app/main.py#L11) 文件最顶部 `sys.stdout.reconfigure(encoding="utf-8", errors="replace")`
2. [app/main.py:38-45](../app/main.py#L38) 强制所有 logging handler 的 stream 也 reconfigure
3. [start.py:175-178](../start.py#L175) 启动 fg 子进程时设 `PYTHONIOENCODING=utf-8` + `PYTHONUTF8=1`

**附加**：所有 logger 输出**不要**用 emoji，统一用 ASCII 标记（`[OK] [FAIL] [WARN] ...`）

### 6.6 日记 schema 的字段方向（v2.3 已反转）
**现状**：[app/schemas/diary.py](../app/schemas/diary.py) `DiaryCreateIn` 的必填字段是 **`content: str`（明文）**，可选 `mood_type` / `is_public`；`content_encrypted` 与 `send_to_ai_hole` 仅为老库兼容/遗留，不应再作为入参。
- ✅ `content: str`（明文，1 字以上）
- ✅ `is_public`（True=漂流瓶；False=静屿角落）
- ❌ 不要再按 v2.3 之前的文档传 `content_encrypted`（会 422 或写入空内容）

**历史坑**：v2.3 之前 `DiaryCreateIn` 只有 `content_encrypted`，明文 `content` 是禁止字段；如果你看到旧文档 / 旧 commit 说「不要 content」，那是历史版本，已不适用。

### 6.7 能量累加一定要用 `query.update()`
**症状**：`EnergyRecord` 写入成功（amount=1），但 `users.total_energy` 一直是 0

**根因**：FastAPI 一次请求一个 session，`user` 对象在依赖链里被多次 `db.get()` 加载，跨 session 的对象属性赋值不会写回 DB

**正确写法**：
```python
# ✅ 显式 UPDATE
db.query(User).filter(User.id == user.id).update(
    {User.total_energy: User.total_energy + amount},
    synchronize_session=False,
)
# 别忘了写流水
record = EnergyRecord(user_id=user.id, amount=amount, source=source)
db.add(record)
db.commit()
```

**错误写法（不要）**：
```python
# ❌ 对象属性赋值不可靠
user.total_energy = (user.total_energy or 0) + amount
db.add(user)
```

详见 [app/services/energy_service.py](../app/services/energy_service.py)。

### 6.8 文件名不能跟 `app/` 同名
**症状**：各种奇怪 import 错误，或 `start.py` 报 `can't open file 'start.py'`

**根因**：Python 优先把 `app.py` 解释为包 `app` 的成员而非脚本

**修复**：根目录**不要**有 `app.py` / `app2.py` 等与 `app/` 同名的 `.py` 文件

### 6.9 不要在子进程里用 `import start` 引用自己
`start.py` 的 `subprocess.Popen` 用 `Path(__file__).resolve()` 而不是字面量 `"start.py"`，**永远**用 `__file__` 引用自身，万一文件改名也跑得起来。

### 6.10 加新字段用 lightweight migrate，不引 Alembic
**症状**：给 User 加了 `is_admin` 字段，老库 `data/healing.db` 重启后还是没这一列。

**原因**：`Base.metadata.create_all()` 只创建**不存在的表**，**不**会 ALTER 已存在的表。

**修复（[app/database.py:50-68](../app/database.py#L50)）**：
- 启动时 `init_db()` 调 `_migrate_legacy_columns()`
- 用 `inspect(engine).get_columns("users")` 拿已有列
- 缺什么 `ALTER TABLE` 加什么
- 例：
  ```python
  cols = {c["name"] for c in insp.get_columns("users")}
  if "is_admin" not in cols:
      conn.execute(text("ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT 0 NOT NULL"))
  ```
- **新加字段时**记得到这里加一段。

⚠️ 这个方案只支持**加列 / 加默认值**。改列类型 / 删列还是建议上 Alembic（但项目刻意不引）。

### 6.11 Pydantic 出参 schema 没声明字段 = 响应里被静默过滤
**症状**：登录接口 200 OK，但前端 `data.is_admin` 永远是 `undefined` → JS 写 `if (!data.is_admin)` 永远走「无权限」分支 → 账号密码都对的 admin 也登不进后台。

**根因**：[app/routers/auth.py](../app/routers/auth.py) 用 `response_model=AuthOut`，FastAPI 序列化时**只保留 schema 里声明的字段**。`User.to_public_dict()` 返回的 `is_admin` 虽然存在，但 `AuthOut` schema 不声明它，就被静默丢了。

**修复（[app/schemas/auth.py:16-21](../app/schemas/auth.py)）**：
```python
class AuthOut(BaseModel):
    id: int
    nickname: str
    total_energy: int
    is_admin: bool = False   # ← 必须显式声明
    created_at: str
```

**铁律**：Pydantic 出参 schema 必须是 `to_public_dict()` 字段的**超集**。每加一个 `to_public_dict()` 字段，**必须**同时在对应 Out schema 声明。

**如何自查**：浏览器 DevTools → Network → 调一次接口 → 看 Response body 里少了哪些字段 → 补 schema。

### 6.12 Vite 默认监听 IPv6 `[::1]` 导致 127.0.0.1 连不上（2026-07-19 加）
**症状**：`npm run dev` 启动后，浏览器访问 `http://127.0.0.1:5173/` 报 `ERR_CONNECTION_REFUSED`，但 `http://localhost:5173/` 能访问。

**根因**：Vite 5 默认 `host: 'localhost'`，Node.js 把 `localhost` 解析为 IPv6 `[::1]` 而非 IPv4 `127.0.0.1`。Windows / 部分浏览器访问 `127.0.0.1` 时只查 IPv4，连不上 IPv6 监听端口。

**修复**：[frontend/vite.config.js](../frontend/vite.config.js) 显式设 `server.host: '127.0.0.1'`：
```javascript
server: {
  host: '127.0.0.1',     // ← 显式 IPv4，不写 'localhost'（会被解析为 [::1]）
  port: 5173,
  strictPort: true,      // 端口被占直接报错，不自动 +1
  proxy: { ... }
}
```

**铁律**：Vite dev server 的 `host` 永远写 `'127.0.0.1'`，不写 `'localhost'`。

### 6.13 Vite `base` 在 dev 模式也会应用（2026-07-19 加）
**症状**：dev 模式下浏览器访问 `http://127.0.0.1:5173/` 返回空白页，Console 报 `Failed to load module script: Expected a JavaScript module script but the server responded with a MIME type of "text/html"`，资源 404。

**根因**：[frontend/vite.config.js](../frontend/vite.config.js) 为了让 build 产物在 `/static/dist/` 子路径下正确加载，设了 `base: '/static/dist/'`。但 Vite **dev 模式也读 `base`**，导致 dev 模式下 index.html 引用 `/static/dist/src/main.js`，而 Vite dev server 实际服务在 `/src/main.js`，404 后 fallback 返回 index.html，浏览器把 HTML 当 JS 解析报错。

**修复**：用 `command === 'build'` 条件设置 `base`：
```javascript
export default defineConfig(({ command }) => ({
  base: command === 'build' ? '/static/dist/' : '/',   // ← dev 用 '/'，build 用 '/static/dist/'
  // ...其他配置
}));
```

**铁律**：Vite `base` 是 dev 和 build 都会应用的配置，dev 期路径不匹配时一定要用 `command` 条件判断。

### 6.14 npm install 拉 three.js 等大包耗时极长（2026-07-19 加）
**症状**：`cd frontend && npm install` 跑了 7 分钟还没完，以为卡死。

**根因**：[frontend/package.json](../frontend/package.json) 依赖里 `three ^0.168`（约 30MB，含大量 .js 文件）+ `gsap ^3.12` + `@vueuse/motion ^2.2`，首次安装时 npm 要下载 + 解压 + 写入 node_modules，磁盘 IO 是瓶颈。

**修复**：① 用 `npm install --no-audit --no-fund` 跳过审计 + 资助检查，省 30s；② 用 `npm install --prefer-offline` 优先用本地缓存；③ 接受首次 5-7 分钟的耗时，后续 `npm install` 增量更新只需 10s。

**铁律**：首次安装大依赖（three / gsap / @vueuse/motion）耗时正常，**不要**中途 Ctrl+C，跑完一次后续就快了。CI/CD 里建议 `npm ci`（用 lockfile，更快更稳定）。

### 6.15 FastAPI SPA fallback 必须排除 /api/、/static/、/admin、/docs 路径（2026-07-19 加）
**症状**：Vue 3 重构后，浏览器访问 `/api/music` 返回 `index.html`（HTML），前端 axios 拿到 HTML 解析 JSON 报错；访问 `/admin` 返回 Vue SPA 而非后台 SSR 页面。

**根因**：[app/main.py](../app/main.py) 的 SPA fallback 用通配路由 `@app.get("/{path:path}")` 兜底所有 GET 请求，但**没有排除**已注册的路径。FastAPI 路由匹配是「先注册先匹配」，但通配路由如果顺序不对会拦截掉其他路由。

**修复**：在 [app/main.py](../app/main.py) 末尾注册 SPA fallback 时显式排除 4 类路径：
```python
@app.get("/{path:path}")
async def spa_fallback(path: str):
    # 排除 API / 静态 / 后台 / 文档
    if (path.startswith("api/")
        or path.startswith("static/")
        or path.startswith("admin")
        or path.startswith("docs")
        or path.startswith("redoc")
        or path.startswith("openapi")):
        raise HTTPException(404)
    # dist 未构建时返回提示页
    dist_index = STATIC_DIR / "dist" / "index.html"
    if not dist_index.exists():
        return HTMLResponse("<h1>前端未构建</h1><p>请先 cd frontend && npm run build，或访问 Vite dev server :5173</p>")
    return FileResponse(dist_index)
```

**铁律**：SPA fallback 通配路由**必须**排除：① `/api/*`（JSON API）；② `/static/*`（静态资源）；③ `/admin*`（后台 SSR）；④ `/docs`、`/redoc`、`/openapi`（FastAPI 自动文档）。否则会让 API 返回 HTML、后台被 SPA 接管。

### 6.16 FastAPI 代理转发 Vite 内部路径含特殊字符失败（2026-07-19 加）
**症状**：v2.0 Vue 3 重构初版用「FastAPI :5000 + Vite :5173 + FastAPI 反代 Vite」方案，浏览器访问 `http://127.0.0.1:5000/` 报 `SyntaxError: Unexpected token '.'`（或 `Unexpected token '<'`），控制台 Network 标签看到 Vite 内部模块请求（如 `/@id/__x00__plugin-vue:export-helper`）返回 200 但内容是 HTML 错误页（首行 `<`），浏览器把 HTML 当 JS 解析就炸了。

**根因**：Vite 5 dev server 的内部模块路径含特殊字符：
- `/@id/__x00__plugin-vue:export-helper` — `__x00__` 是 null 字符 `\x00` 的转义形式（Vite 用它表示 `@rollup/plugin-vue` 注入的 export-helper 模块），`:export-helper` 含冒号
- httpx / aiohttp / requests 转发时这些特殊字符会被 URL 编码或破坏（null 字符在某些 HTTP 客户端实现里会截断请求路径，冒号在 URL path 段需要编码）
- 转发后的路径 Vite dev server 自己也认不出，fallback 返回 index.html（HTML），浏览器拿到 HTML 当 JS 解析就报 `SyntaxError`

**为什么 FastAPI 反代 Vite 不可行**：
- Vite dev server 不是普通 HTTP 服务，它服务的是「源码模块图」，路径含大量内部约定（`/@id/`、`/@fs/`、`?import`、`?t=timestamp` 等），这些都是 Vite 自己解析的，HTTP 客户端转发时会破坏
- 反过来 Vite proxy 转发到 FastAPI 是稳定的（FastAPI 是普通 HTTP JSON API，路径不含特殊字符）

**修复**：让 **Vite 直接占 :5000**（用户访问入口），**FastAPI 改听 :5001**（API 后端）：
- [start.py](../start.py) 应用模式（默认，v2.2.2 起）自动设置 `QI_PORT=5001` 启动 FastAPI + 启动 Vite :5000；自动检测 `frontend/node_modules` 不存在则 `npm install`
- [frontend/vite.config.js](../frontend/vite.config.js) dev server port 5173 → 5000，proxy target :5000 → :5001，移除 `hmr.clientPort`（HMR 走本地），新增 `/docs` 和 `/openapi.json` 代理
- [app/main.py](../app/main.py) SPA fallback 移除回退代理到 Vite 的逻辑，开发态（dist 未构建）返回提示页引导用户访问 Vite :5000

**铁律**：永远**不要**让后端 HTTP 框架（FastAPI / Flask / Express）反向代理 Vite dev server 的内部模块路径。要么让 Vite 直接占用户访问端口，要么用 Nginx 这种能透传任意字符的反向代理（生产环境也不需要 Vite，所以只影响开发模式）。详见 [§5.9](#59-为什么开发模式让-vite-占5000-fastapi-改50012026-07-19-加) 决策。

### 6.17 `Depends(None)` 导致 `/openapi.json` 500（2026-07-20 加）
**症状**：访问 `http://127.0.0.1:5000/openapi.json` 返回 500，`/docs` Swagger UI 页面能加载但 API 列表空白。FastAPI 日志报 `pydantic.errors.PydanticUserError: TypeAdapter[typing.Annotated[ForwardRef('Optional[_SessionBind]'), Query(None)]]` is not fully defined。

**根因**：[app/routers/admin.py](../app/routers/admin.py) 的 `tail_logs` 路由签名写错：
```python
def tail_logs(
    lines: int = Query(200, ...),
    level: str = Query("all", ...),
    db: Session = Depends(None),   # ← bug：Depends(None) 不是有效依赖
    admin: User = Depends(get_current_admin),
):
```
- `Depends(None)` 让 FastAPI 把 `None` 当成依赖工厂，返回 `None`，但 `db: Session` 的类型注解在 `from __future__ import annotations` 下变成 ForwardRef `"Session"`
- FastAPI 生成 OpenAPI schema 时，把 `db` 当成有默认值 `None` 的查询参数（`Query(None)`），尝试为 `Session` 类型构建 JSON schema
- Pydantic 解析 `Session` 时遇到 SQLAlchemy 内部泛型 `_SessionBind`（ForwardRef 未定义），抛 `PydanticUserError`
- 函数体根本没用 `db`，这个参数是多余且错误的

**修复**：直接删掉 `db: Session = Depends(None)` 参数（函数体没用 `db`）。`Depends(None)` 是错误写法，`Depends` 的参数必须是可调用对象（如 `get_db`）。

**铁律**：路由签名里的每个参数要么是请求输入（`Query` / `Body` / `Path`），要么是依赖（`Depends(callable)`）。**绝不**写 `Depends(None)`、`Depends(0)`、`Depends("")` 这种空值依赖——要么用真实依赖工厂，要么删掉参数。

### 6.18 `expire_on_commit=False` 导致 `new_total_energy` 返回旧值（2026-07-20 加）
**症状**：用户听完一首歌（进度 ≥ 90%），前端调用 `POST /api/music/listen-complete`，返回 `{"granted": true, "amount": 1, "new_total_energy": 0}`——能量发放了（`granted: true`）但总能量没变（`new_total_energy: 0`，应该是 1）。写日记（`+2`）、兑换（`-cost`）也有同样问题。

**根因**：[app/database.py](../app/database.py) `SessionLocal` 配置了 `expire_on_commit=False`（line 32）：
```python
SessionLocal = sessionmaker(
    bind=engine, autocommit=False, autoflush=False, future=True,
    expire_on_commit=False,  # ← commit 后不 expire 内存对象
)
```
- [app/services/energy_service.py](../app/services/energy_service.py) 的 `grant_energy` 用 `db.query(User).filter(...).update({...})` 在 DB 层 UPDATE（符合 §6.7 铁律），但这个 UPDATE **不会同步到 session 里已加载的 `user` 对象的 `total_energy` 属性**（SQLAlchemy 的 `query.update()` 默认 `synchronize_session='auto'`，但在 `autoflush=False` + 对象已加载的边界 case 下同步可能失效）
- `db.commit()` 后，因为 `expire_on_commit=False`，`user.total_energy` 仍是旧的内存值（0），不会触发重新查询
- 路由层 `return {"new_total_energy": user.total_energy}` 返回旧值

**修复**：所有"commit 后需要返回最新 total_energy"的路由，**必须用 `db.query(User.total_energy).filter(User.id == user.id).scalar()` 重新查 DB**，不能依赖 `user.total_energy` 内存值。已修复 3 处：
- [app/routers/music.py](../app/routers/music.py) `listen_complete`
- [app/routers/energy.py](../app/routers/energy.py) `exchange`
- [app/routers/diary.py](../app/routers/diary.py) `create_diary` 路由

**铁律**：`expire_on_commit=False` 下，**commit 后读 ORM 对象属性 = 读旧值**。凡是"修改了某字段 → commit → 返回该字段新值"的场景，必须用 `db.query(Model.field).filter(...).scalar()` 或 `db.refresh(obj)` 重新获取。不要相信内存对象。

### 6.19 同歌 24h 重复发放能量（已修复，保留作规则示例）
**历史症状**：同一首歌 24h 内重复调 `/api/music/listen-complete`，会重复 +1 露水；docstring 写了去重但代码没实现。

**当前实现**（已修复）：`EnergyRecord` 有 `music_id`，`listen_complete` 在发放前查 24h 内同 `user_id + music_id + source=listen_music` 的记录，存在则返回 `{"granted": False, "reason": "这首 24 小时内已经听过了"}`；`grant_energy` 接收 `music_id` 并写入流水。

**铁律**：docstring 写的规则必须有对应查询/分支实现；规则要查 DB 去重时必须有索引覆盖（`user_id + 业务键 + created_at`）。

### 6.20 `exchange_item` 已持有检查位置错误导致重复兑换 500（2026-07-20 加）
**症状**：用户兑换一个 `cost=0` 的徽章（如"古琴初学者"），第二次兑换同一徽章返回 **HTTP 500**，错误：`sqlalchemy.exc.IntegrityError: UNIQUE constraint failed: garden_items.user_id, garden_items.item_id`。

**根因**：[app/services/energy_service.py](../app/services/energy_service.py) `exchange_item` 原代码：
```python
def exchange_item(db, user, item_id):
    item = db.get(ShopItem, item_id)
    if item is None: raise HTTPException(404, ...)
    cost = item.cost or 0
    if cost > 0:
        # 扣能量 + 写流水
        ...
        # ❌ "检查已持有"在这 if 块里！cost=0 的徽章跳过检查
        existing = db.query(GardenItem).filter(...).first()
        if existing is not None:
            raise HTTPException(400, "这件你已经拥有啦")
    # 写入持有 → UNIQUE constraint 触发 500
    garden_item = GardenItem(user_id=user.id, item_id=item_id)
    db.add(garden_item)
```

"检查已持有"被嵌在 `if cost > 0:` 内部，**cost=0 的徽章完全跳过检查**，直接 INSERT，触发数据库唯一约束 → 500（应该返回 400 友好提示）。

**修复**：把"检查已持有"**提到 `if cost > 0:` 之前**，对所有物品（不论 cost 多少）都先检查：
```python
def exchange_item(db, user, item_id):
    item = db.get(ShopItem, item_id)
    if item is None: raise HTTPException(404, ...)
    # ✅ 对所有物品都检查
    existing = db.query(GardenItem).filter(
        GardenItem.user_id == user.id, GardenItem.item_id == item_id
    ).first()
    if existing is not None:
        raise HTTPException(400, "这件你已经拥有啦")
    cost = item.cost or 0
    if cost > 0:
        # 扣能量 + 写流水（不再含"检查已持有"）
        ...
    # 写入持有
    garden_item = GardenItem(user_id=user.id, item_id=item_id)
    db.add(garden_item)
```

**铁律**：**业务校验必须独立于价格分支**。"是否已持有"是物品层面的状态校验，跟"是否需要扣能量"是两个正交维度。**绝不能**把通用业务校验（持有/权限/存在性）埋进特定价格分支里。任何数据库 `UNIQUE` 约束都应该被业务层提前拦截，返回友好 4xx，而不是让 5xx 漏出去。

### 6.21 FlowerField.vue 重新赋值 `three.value` 丢失 `_THREE`/`_dummy` 导致花田不渲染（2026-07-20 加）
**症状**：访问 `/garden`，3D 花田区域只显示 CSS 渐变背景（`#F9F6F0 → #E4E9DC`），看不到任何花朵。Console 无报错，canvas 元素存在且尺寸正常（896×380），WebGL2 上下文可用，`isContextLost()=false`，但 readPixels 显示整个 canvas 都是背景色。

**根因**：[frontend/src/components/FlowerField.vue](../frontend/src/components/FlowerField.vue) `initScene()` 流程：
```js
const initScene = async () => {
  const THREE = await import('three')
  three.value._THREE = THREE                    // ① 在旧对象上设 _THREE
  three.value._dummy = new THREE.Object3D()     // ② 在旧对象上设 _dummy
  // ... 创建场景、相机、渲染器、InstancedMesh ...
  three.value = {                               // ③ 重新赋值整个对象！
    scene, renderer, camera, clock,
    flowers, petalGeometry, petalMaterial,
    flowerData, centers, dust,
    // ❌ 没把 _THREE 和 _dummy 带过来！
  }
}

const animate = () => {
  const t = three.value
  if (!t || !t.renderer || !t._THREE) return    // ← _THREE=undefined，第一帧就 return！
  // ... 永远执行不到 ...
}
```

`initScene` 开头给旧 `three.value` 对象设了 `_THREE` / `_dummy`，但末尾用 `three.value = {...}` 整体替换了对象，**新对象里没有这俩字段**。`animate()` 第一行 `if (!t._THREE) return` 直接退出，**渲染循环从未启动**，canvas 内部一直是透明的（`alpha: true`），用户看到的是 `.flower-field` 容器的 CSS 渐变背景。

**修复**：把 `_THREE: THREE` 和 `_dummy: new THREE.Object3D()` 加到新 `three.value` 对象里；并清理 `initScene` 开头那两行误导性赋值（在即将被覆盖的旧对象上设值毫无意义）。

**铁律**：用 `shallowRef` / `ref` 存复杂状态时，**整体替换 `.value` 一定要清点旧对象上的所有字段**（包括动态添加的、运行时才设的）。更安全的做法是用 `Object.assign(three.value, { ...newFields })` 增量更新而不是整体替换。另一个铁律：**渲染验证不能只看 DOM 元素存在性**（canvas 存在 ≠ 渲染了内容），必须用 `gl.readPixels()` 检查实际像素，否则像这种"canvas 在但没渲染"的 bug 会被漏掉。

### 6.22 GSAP `target not found` 警告：v-for 异步数据 + `onMounted` 立即动画（2026-07-20 加）
**症状**：访问 `/garden`，Console 报多条警告：
```
GSAP target .source-bar not found. https://gsap.com
GSAP target .garden-item not found.
GSAP target .record-row not found.
```

**根因**：[frontend/src/views/garden/GardenView.vue](../frontend/src/views/garden/GardenView.vue) `onMounted` 里**没 await** 异步的 `fetchAll()`，立即在 `nextTick` 里调 `gsap.from('.source-bar', ...)`：
```js
onMounted(() => {
  fetchAll()                                    // ❌ 没 await，立即返回 Promise
  nextTick(() => {
    gsap.from('.source-bar', {...})             // ← 数据还没从 API 回来，v-for 没渲染
    gsap.from('.garden-item', {...})            // ← 同上
    gsap.from('.record-row', {...})             // ← 同上
  })
})
```

`.source-bar`、`.garden-item`、`.record-row` 都在 v-for 里，依赖 `myItems` / `energySummary.by_source` / `energyRecords` 这些 ref，初始值为空数组/空对象。`fetchAll()` 是异步的（`Promise.all([...api.get...])`），`onMounted` 同步执行完后立即 `nextTick` 调 GSAP 时，数据**还没从后端回来**，v-for 没渲染任何元素，GSAP 找不到目标就警告。

**修复**：把入场动画从 `onMounted` 移到 `fetchAll` 完成后 + `await nextTick()` 后执行；每个选择器先 `document.querySelector` 检查存在再调 `gsap.from`（用户可能没有能量记录/物品/来源，对应元素不渲染，GSAP 警告也避免）：
```js
const fetchAll = async () => {
  try {
    const [mine, summary, records] = await Promise.all([...])
    myItems.value = mine?.items || []
    // ...
    await nextTick()                            // 等数据驱动的 DOM 更新完
    playEnterAnimations()                       // 再放动画
  } catch (e) { ... }
}

const playEnterAnimations = () => {
  gsap.from('.garden-header', {...})            // 静态元素，永远存在
  gsap.from('.energy-card', {...})
  if (document.querySelector('.source-bar')) {  // 动态元素，先检查存在
    gsap.from('.source-bar', {...})
  }
  if (document.querySelector('.garden-item')) {
    gsap.from('.garden-item', {...})
  }
  if (document.querySelector('.record-row')) {
    gsap.from('.record-row', {...})
  }
}
```

**铁律**：**`onMounted` 里有 async 数据加载 + GSAP 入场动画时，动画必须在数据加载完成 + `nextTick` 之后执行**，不能依赖 `onMounted` 自己的 `nextTick`（那是 DOM 挂载完的 nextTick，不是数据加载完的 nextTick）。**v-for 渲染的元素必须先 `document.querySelector` 检查存在再调 `gsap.from`**，否则数据为空时 GSAP 必报 "target not found" 警告。该模式已在 v2.5.1 全站补齐（GardenView / NotificationsView / ShopView / DiaryListView / AIChatView），新加列表动画时照此写法。

### 6.23 视觉组件集成 4 大坑（2026-07-20 加）

#### 6.23.1 `createMediaElementSource` 一次性约束（AudioVisualizer）

**症状**：[MusicDetailView](../frontend/src/views/music/MusicDetailView.vue) 切到第二首歌时，Console 报 `InvalidStateError: HTMLMediaElement already connected previously to a different MediaElementSourceNode`，音波可视化卡住不更新。

**根因**：Web Audio API 规范规定 `audioCtx.createMediaElementSource(audioEl)` 对同一 `<audio>` 元素**只能调用一次**。但 [AudioVisualizer.vue](../frontend/src/components/AudioVisualizer.vue) 的 `connect(audioEl)` 在每次切歌时被调用 → 第二次抛 InvalidStateError。

**修复**：① AudioVisualizer 内部 `connect()` 用 `if (!sourceNode)` 守卫，已连接则直接返回；② MusicDetailView 用 `visualizerConnected` ref 标记，**首次 `playIndex` 时调 `visualizerRef.value.connect(audioEl)`，后续切歌不重连**：
```js
const playIndex = (idx) => {
  // ...
  if (!visualizerConnected.value && visualizerRef.value) {
    visualizerRef.value.connect(audio)              // 只在首次播放时连接
    visualizerConnected.value = true
  }
  audio.load()
  audio.play().then(...)
}
```

#### 6.23.2 `shallowRef` 持有 Three.js 对象，别用 `ref`

**症状**：[AmbientBackground](../frontend/src/components/AmbientBackground.vue) / [HeroScene](../frontend/src/components/HeroScene.vue) 用 `ref({ scene, camera, renderer, ... })` 时，初次渲染卡顿 200ms+，Console 有大量 Vue 警告 `Avoid adding reactive properties to a Vue instance`。

**根因**：Vue 3 `ref` 对 object 会递归代理每一层属性（深度响应式）。Three.js 的 `Scene` / `Object3D` / `Geometry` / `Material` 内部有大量私有字段 + 数组 + Map，递归代理既慢又可能干扰 Three.js 自己的内部逻辑。

**修复**：所有 Three.js 对象**必须**用 `shallowRef`（只代理 `.value`，不递归内部）：
```js
import { shallowRef } from 'vue'
const three = shallowRef(null)              // ← 而不是 ref(null)
three.value = { scene, camera, renderer, clock, rafId }
```
所有访问 Three.js 字段的地方用 `three.value?.scene` / `three.value?.renderer.dispose()`，**不要**解构。

#### 6.23.3 `smartRAF` 必须用，否则标签页隐藏时浪费 GPU

**症状**：开 `/`（HeroScene）+ `/garden`（FlowerField）切换后切走标签页，笔记本风扇狂转，任务管理器看 GPU 占用 30%。

**根因**：Three.js 的 `requestAnimationFrame` 在标签页隐藏时浏览器虽然会降到 1 fps，但**仍在执行**渲染循环（GPU 资源不释放）。

**修复**：所有视觉组件的 rAF 必须走 [utils/visual.js](../frontend/src/utils/visual.js) 的 `smartRAF(callback)`，它在 `document.hidden` 时主动 `cancelAnimationFrame`，可见时自动恢复：
```js
import { smartRAF } from '@/utils/visual'
const loop = () => {
  three.value?.renderer.render(three.value.scene, three.value.camera)
  three.value.rafId = smartRAF(loop)        // ← 用 smartRAF 而不是 requestAnimationFrame
}
```

#### 6.23.4 `onBeforeUnmount` 必须释放 geometry / material / renderer / 监听 / ResizeObserver

**症状**：在 `/`（HeroScene）和 `/garden`（FlowerField）之间来回切 5 次，浏览器 Console 报 `WARNING: Too many active WebGL contexts. Oldest context will be lost.`，3D 场景黑屏。

**根因**：每次切走视图时 Vue 卸载组件，但 Three.js 的 `renderer` / `geometry` / `material` / `event listener` / `ResizeObserver` 不会被 GC 自动回收。5 次切走 = 5 个 WebGL context 累积，浏览器强制丢弃最老的 → 黑屏。

**修复**：所有 Three.js 组件**必须**在 `onBeforeUnmount` 释放：
```js
import { onBeforeUnmount } from 'vue'
onBeforeUnmount(() => {
  if (three.value?.rafId) cancelAnimationFrame(three.value.rafId)
  three.value?.geometry?.dispose()
  three.value?.material?.dispose()
  three.value?.renderer?.dispose()
  window.removeEventListener('resize', three.value.onResize)
  three.value?.resizeObserver?.disconnect()
  three.value = null                        // 释放引用，让 GC 回收
})
```

**铁律**：视觉组件的 4 大坑（`createMediaElementSource` 一次性 / `shallowRef` 而非 `ref` / `smartRAF` 替代 `requestAnimationFrame` / `onBeforeUnmount` 完整释放）**必须同时满足**，缺任何一个都会在长时间使用或多视图切换后出问题。新建视觉组件时直接复制 [AmbientBackground.vue](../frontend/src/components/AmbientBackground.vue) 的结构作为模板。

### 6.24 Safari / iOS WebGL 上下文丢失 + emoji 字体不一致（2026-07-30 v2.3.3 加）

#### 6.24.1 iOS Safari 切后台→前台后 3D 场景黑屏（WebGL 上下文丢失）

**症状**：iOS Safari 用户访问首页（HeroScene 3D 浮岛）后切到其他 App，再切回 Safari 时 3D 场景黑屏，Console 无报错但 WebGL context 已失效。

**根因**：iOS Safari 为节省内存，在页面切到后台时会主动释放 WebGL 上下文（触发 `webglcontextlost` 事件）。v2.3.3 之前 [three-helpers.js](../frontend/src/utils/three-helpers.js) 没有监听该事件，上下文丢失后 Three.js 的 renderer / geometry / material 全部失效，切回前台时无恢复逻辑 → 黑屏。

**修复**（v2.3.3）：[three-helpers.js](../frontend/src/utils/three-helpers.js) 添加 `webglcontextlost` / `webglcontextrestored` 事件监听：
- `webglcontextlost`：`event.preventDefault()` + 保存当前场景状态（相机位置 / OrbitControls 状态 / 自动旋转开关）
- `webglcontextrestored`：重建 renderer + 重新编译 material + 恢复场景状态 + 重启 rAF 循环

同时 [HeroScene.vue](../frontend/src/components/HeroScene.vue) 实现 **iOS 降级**策略降低内存压力：
- **Bloom 降级**：iOS 关闭 `UnrealBloomPass`（后处理内存大户）
- **PMREM 降级**：iOS PMREM 分辨率 256→128、阴影贴图 2048→1024、dpr 上限 2→1.5
- 老 iOS 缺 `EXT_color_buffer_half_float` 扩展时，完全关闭 PMREM + Bloom（[utils/visual.js](../frontend/src/utils/visual.js) `getWebGLCaps()` 检测）

#### 6.24.2 `hasWebGL()` 检测 bug 导致 Safari 误判无 WebGL

**症状**：部分 Safari 用户报告首页 3D 场景直接降级为 SVG 静态插画，但 Safari 明明支持 WebGL。

**根因**：v2.3.3 之前 [utils/visual.js](../frontend/src/utils/visual.js) 的 `hasWebGL()` 实现有 bug——仅尝试创建 WebGL2 context，若失败就返回 false。但部分老 Safari 只支持 WebGL1（无 WebGL2），被误判为「无 WebGL」→ 直接降级 SVG。

**修复**（v2.3.3）：**hasWebGL 重写**——区分 WebGL1 / WebGL2，先试 WebGL2 失败再试 WebGL1；同时检测关键扩展（`EXT_color_buffer_half_float` 等）+ max texture size；新增 `getWebGLCaps()` 返回完整能力对象、`isSafari()` / `isIOS()` 判断浏览器/平台。

#### 6.24.3 Safari emoji 显示不一致（Apple Color Emoji vs 系统 emoji）

**症状**：Safari 用户反馈导航/个人主页的 emoji 风格与 Chrome 不一致——Safari 用 Apple Color Emoji（彩色写实风格），Chrome 用系统 emoji（扁平风格），视觉不统一。

**根因**：跨平台 emoji 字体差异——浏览器各自调用系统 emoji 字体渲染，不同平台风格差异大（Apple Color Emoji vs Noto Color Emoji vs Segoe UI Emoji），无法通过 CSS 统一。

**修复**（v2.3.3）：新建 [EmojiIcon.vue](../frontend/src/components/EmojiIcon.vue) 组件，使用 **Iconify** + `@iconify-json/twemoji` 离线 **SVG emoji**（twemoji 风格统一扁平彩色），确保 **跨浏览器一致**。已替换 [AppLayout.vue](../frontend/src/components/AppLayout.vue)（品牌 / 导航 / 通知 / 资源）+ [ProfileView.vue](../frontend/src/views/profile/ProfileView.vue)（头像 / 通知 / 资源 / 统计 / 快捷入口 / 花朵阶段）所有 emoji。

**铁律**：Safari / iOS 兼容 3 大坑（`webglcontextlost` 上下文恢复 / `hasWebGL` 须区分 WebGL1+2 + 检测扩展 / emoji 须用 SVG 统一而非系统字体）**必须同时满足**。新建 3D 组件时直接复制 [HeroScene.vue](../frontend/src/components/HeroScene.vue) 的 `webglcontextlost` / `webglcontextrestored` 监听 + iOS 降级逻辑作为模板。

### 6.25 两个 `get_db` 导致鉴权 user 与端点不在同一 session（2026-10-25 v2.6.2 加）

**症状**：`PATCH /api/profile` 改昵称/头像一直 500，日志为 `InvalidRequestError: Instance '<User ...>' is not persistent within this Session`；数据库偶发被改了一半。

**根因**：[app/deps.py](../app/deps.py) 定义了 `def get_db(): yield from _get_db()` 包装，而所有 routers 直接 `from app.database import get_db`。FastAPI 按「依赖 callable」缓存，两个函数不是同一个，于是 `get_current_user` 用一个 session、端点 `db` 用另一个 session；`user` 是 detach 的，`db.commit()/refresh(user)` 自然失败。

**修复**（v2.6.2）：`deps.py` 直接 `from app.database import get_db`，删掉包装函数；所有 router 继续用同一个 `get_db`。**铁律**：全项目只允许一个 `get_db` 定义，不要在 deps 里再包一层；需要新依赖时传 `Depends(get_db)`。

### 6.26 听曲进度单位 0–1 vs 0–100（2026-10-25 v2.6.2 加）

**症状**：听满 90% 后露水从未到账，前端静默失败；`POST /api/music/listen-complete` 实际返回 422。

**根因**：[MusicDetailView.vue](../frontend/src/views/music/MusicDetailView.vue) / [MusicWesternView.vue](../frontend/src/views/music/MusicWesternView.vue) 的 `progress` 是 0–1，但上报时 `Math.round(progress.value * 100)` 传了 90/100；后端 `ListenCompleteIn.progress` 要求 0–1。

**修复**（v2.6.2）：统一传 `Math.min(1, progress.value)`；失败时把 `listenReported` 复位，允许下一次 `timeupdate` 重试。新增同类上报时先看 schema 的 `ge/le`，不要凭感觉传百分比。

---

## 7. 改动指南

### 7.1 加一个新页面（前台 Vue 3 SPA）
1. 在 `frontend/src/views/<module>/` 新建 `XxxView.vue`。
2. 在 [frontend/src/router/index.js](../frontend/src/router/index.js) 加路由（懒加载 `() => import(...)`，按需加 `meta.requiresAuth`）。
3. 视图里用 `@/api` 的 axios 实例调接口；注意拦截器已解包 `response.data`，不要再写 `res.data`。
4. 需要导航入口时改 [AppLayout.vue](../frontend/src/components/AppLayout.vue) 与 [islandGuide.js](../frontend/src/data/islandGuide.js)。
5. 前端改动必须 `npm run build`；后台 `/admin/*` 页面仍走 Jinja2 SSR（见 §7.7）。

### 7.2 加一个 API 端点
1. `app/routers/<name>.py` 加 `@router.post("/api/...")`
2. 入参用 Pydantic model（在 `app/schemas/<name>.py` 定义）
3. 鉴权用 `Depends(get_current_user)`
4. 业务逻辑写在 `app/services/<name>.py`（**不**在 router 里堆 if-else）
5. 出参 Pydantic model 加在 `app/schemas/<name>.py`

### 7.3 加一张数据库表
1. `app/models/<name>.py` 写 `class Xxx(Base): __tablename__ = "xxx"; ...`
2. `app/models/__init__.py` import 它
3. 重启 → `init_db()` 自动建表
4. 更新 [README.md](../README.md) §4 表速查

### 7.4 改能量规则
1. [app/services/energy_service.py](../app/services/energy_service.py) 改发放 / 兑换 / 徽章逻辑
2. [app/utils/constants.py](../app/utils/constants.py) 同步 `DAILY_ENERGY_LIMITS` / `DEFAULT_SHOP_ITEMS` / `BADGE_LEAF_REWARDS`
3. [README.md](../README.md) §3.4 同步表格
4. **单日上限**也要在常量里更新

### 7.5 改配色 / 字体
1. 前台颜色 token 在 [frontend/tailwind.config.js](../frontend/tailwind.config.js)；全局 CSS 变量 / 通用类在 [frontend/src/assets/styles/main.css](../frontend/src/assets/styles/main.css)。
2. 后台 `/admin/*` 仍用 [static/css/07-admin.css](../static/css/07-admin.css)，与前台隔离。
3. 项目主色调：`#F9F6F0` 米白 / `#E3F0EA` 淡青 / `#F0E3E8` 藕粉。

### 7.6 部署到服务器
详见 [docs/DEPLOYMENT.md](DEPLOYMENT.md)。

### 7.7 加一个后台页面 / API
1. 后台 API：[app/routers/admin.py](../app/routers/admin.py) 加 `@router.get/post/...`，入参用 Pydantic in [app/schemas/admin.py](../app/schemas/admin.py)
2. 后台页面：[app/routers/admin_pages.py](../app/routers/admin_pages.py) 加 `@router.get(...)` + `admin_templates.TemplateResponse(request, "admin/your.html", {...})`
3. 鉴权统一用 `Depends(get_current_admin)`（API）或 `Depends(get_current_admin_or_redirect)`（页面）
4. 模板放 `templates/admin/your.html`，继承 `admin/_base.html`
5. 表格 / 模态样式直接用 [static/css/07-admin.css](../static/css/07-admin.css) 里的 `.admin-*` 类
6. JS 放 `static/js/pages/admin_xxx.js`，模板底部 `<script defer src="/static/js/pages/admin_xxx.js"></script>`

### 7.8 改后台入口路径
- `.env` 改 `QI_ADMIN_PATH_PREFIX=/your-secret-path`
- 重启服务即可
- ⚠️ 改完**不会**自动迁移用户的书签，需要更新 [README.md](../README.md) / [HANDOFF.md §1](HANDOFF.md) 等文档

### 7.9 加一个 AI 场景（2026-07-17 起约定）
> 现有 3 个场景在 [app/services/ai_service.py](../app/services/ai_service.py) / [app/routers/ai.py](../app/routers/ai.py) / [app/schemas/ai.py](../app/schemas/ai.py)。再加一个走同样套路：

1. **Schema**：在 [app/schemas/ai.py](../app/schemas/ai.py) 加 `AI<X>In` + `AI<X>Out` 两个 Pydantic 模型；在 [app/schemas/__init__.py](../app/schemas/__init__.py) 的 `__all__` 里加 import + 在末尾 `model_rebuild()` 区段确保新模型也被 rebuild
2. **Service**：在 [app/services/ai_service.py](../app/services/ai_service.py) 加 ① 系统提示词常量（温柔语气、不诊断不开药、危机引导专业帮助） ② 上层方法 `generate_xxx()`，调 `_call_nvidia()`；**禁止**在 router 里直接调 `_call_nvidia()`
3. **Router**：在 [app/routers/ai.py](../app/routers/ai.py) 加 `@router.post("/xxx")`，**必须**：
   - `Depends(get_current_user)` 鉴权
   - `try: ... except AIServiceUnavailable: return {"available": False, "message": "治愈系友好提示"}` 降级，**不报 500**
4. **前端集成（Vue 3 SPA）**：
   - 独立页面：新建 `frontend/src/views/xxx/XxxView.vue` + 在 [router/index.js](../frontend/src/router/index.js) 加路由
   - 已有页面加容器：直接在对应 `.vue` 里加区块，用 `@/api` 调端点
   - 首页卡片：改 [HomeView.vue](../frontend/src/views/HomeView.vue)（仅登录可见用 `userStore.isLoggedIn`）
5. **测试降级**：先**不配** `QI_NVIDIA_API_KEY` 跑一遍，确认返回 `available:false` + 友好提示；再配 key 跑一遍，确认 `available:true` + AI 文案

**铁律**：
- AI 输出**不写入数据库**；树洞对话已移除，不再有聊天历史
- 系统提示词**必须**包含「不诊断不开药、危机情况引导求助专业资源」语义（治愈系调性 + 责任边界）
- 端点**必须**有 try/except 降级（「渐进增强」原则，没 key 也能跑）
- 改完同步更新 README §3.7、[DEVELOPMENT.md §2.7](DEVELOPMENT.md) 与 [CHANGELOG.md](CHANGELOG.md)

---

## 8. 验证清单

### 8.1 本机冒烟
```bash
python start.py restart
# 等 2 秒
curl -I http://127.0.0.1:5000/                       # 200
curl -I http://127.0.0.1:5000/api/music               # 200
curl -I http://127.0.0.1:5000/api/garden/shop         # 200
curl -I http://127.0.0.1:5000/docs                    # 200
curl -I http://127.0.0.1:5000/music/gong              # 200
curl -I http://127.0.0.1:5000/diary                   # 302 (未登录跳 login)
```

### 8.2 端到端测试
写一个 `tests/e2e.py`（项目里没现成的，可以自己加）：
```python
import requests
s = requests.Session()

# 1. 注册
r = s.post("http://127.0.0.1:5000/api/auth/register",
           json={"nickname": "test", "password": "hello123"})
assert r.status_code == 201, r.text

# 2. 听歌 + 能量（v2.0 后统一走 POST /api/music/listen-complete）
musics = s.get("http://127.0.0.1:5000/api/music").json()
music_id = musics[0]["id"] if musics else 1
r = s.post("http://127.0.0.1:5000/api/music/listen-complete",
           json={"music_id": music_id, "progress": 1.0})
assert r.status_code == 200, r.text
assert r.json()["new_total_energy"] == 1  # 见 §6.18：必须重新查 DB 才能拿到新值

# 3. 写日记（明文，v2.3 起）
r = s.post("http://127.0.0.1:5000/api/diary",
           json={"content": "今天有点累", "is_public": False})
assert r.status_code == 201

# 4. 心情打卡
r = s.post("http://127.0.0.1:5000/api/mood/checkin",
           json={"mood_emoji": "calm", "note": "测试"})
assert r.status_code in (200, 201)

# 5. 花园（可选）
r = s.get("http://127.0.0.1:5000/api/garden/shop")
assert r.status_code == 200
r = s.get("http://127.0.0.1:5000/api/garden/mine")
assert r.status_code == 200
```

---

## 9. 待优化（next agent 可选做）

按优先级：

1. **测试覆盖**（最高）— 加 `tests/`，pytest 覆盖 services + routers
2. **音频** — 16 首真实音频已入库；剩余 6 首西洋曲是 5338 字节静音占位，需补真实音频
3. **真实图片** — `static/images/` 目前只有 5 张五音 SVG 封面，可补曲目封面
4. **MySQL 迁移** — 改 `QI_DATABASE_URL` 即可，业务层不用动
5. **WebSocket 漂流瓶实时漂动** — 现在是随机抽取，可加推送
6. **审计日志** — 谁在什么时候拾取了谁的瓶子（现在不记）
7. **HTTPS** — 服务器部署时用 Nginx 反向代理
8. **PWA / 离线** — 离线写日记（IndexedDB；注意当前日记已是明文存储，需先决定加密方案）
9. **多语言** — 现在文案全是中文，i18n 抽出来
10. **iCal 导出心情日历**

---

## 10. 文档目录

| 文件 | 给谁看 |
|---|---|
| [README.md](../README.md) | 产品首页 + 开发者速查 |
| [AGENTS.md](../AGENTS.md) | AI/自动化开发者的工作规则（自测 + 文档 + gh 推送） |
| [docs/README.md](README.md) | 文档地图与职责边界 |
| [HANDOFF.md](HANDOFF.md) | **接手的 AI**（最重要） |
| [PROJECT_STATE.md](PROJECT_STATE.md) | 当前状态 / 已知问题 / TODO |
| [ARCHITECTURE.md](ARCHITECTURE.md) | 想深入了解架构的开发者 |
| [DEVELOPMENT.md](DEVELOPMENT.md) | 改代码的开发者 |
| [DEPLOYMENT.md](DEPLOYMENT.md) | 部署到服务器的人 |
| [CHANGELOG.md](CHANGELOG.md) | 全部版本变更历史 |
| [曲目清单.md](曲目清单.md) | 真实音频放置指引 |
| [HOME_REDESIGN_PROPOSAL.md](HOME_REDESIGN_PROPOSAL.md) | 首页重构设计提案 |

---

## 11. 联系人 / 决策记录

- **设计原则**：见项目 PRD（用户最初提供）
- **本会话决策**：
  - 端口 5000（不是 8000，方便和 Flask 项目区分）
  - 不用 Alembic（项目轻量，改 model 重启就好）
  - 日记 v2.3 起改为明文存储；早期「客户端加密」决策已回退，不要再按端到端加密实现
  - 启动脚本自研 `start.py`（不用 supervisor，更轻量）
  - ASCII-only 日志（兼容 Windows GBK）

**如果发现文档和代码矛盾：**
**以代码为准**，然后回来更新这份文档（HANDOFF.md + README.md + 对应 docs/）。

---

## 12. 文档自动同步铁律（必读！）

> ⚠️ **本节是本项目最高优先级的一条规则，地位高于 §6 任何具体技术决策。**

### 12.1 铁律全文

**改任何一行代码之前，先问自己：「这会不会影响文档？」如果会 — 改完代码、跑通测试、提交之前，文档**必须**已经更新完毕。**

> 改代码不改文档 = 改了一半。下一任接手的人会被你的旧文档带进沟里。

> 🔒 **自测铁律（2026-10-18 立）**：任何代码改动在 commit 前**必须自测通过**——后端 `python start.py restart` 无报错 + 受影响接口返回符合预期 + `logs/healing.log` 无 ERROR；前端必须 `cd frontend && npm run build` 通过并在浏览器验证受影响页面功能与 console；修 Bug 必须复验原复现步骤。**未自测 = 未完成，不得 commit。** 按改动范围执行的最小自测表见根目录 [AGENTS.md](../AGENTS.md)。

> 🔒 **2026-07-19 全站 Vue 3 重构特别约定**：本次重构涉及 **6 份文档同步**（README / HANDOFF / PROJECT_STATE / ARCHITECTURE / DEPLOYMENT / DEVELOPMENT），必须**同一个 commit** 一起更新。互链保持一致，关键词 `Vue 3` / `Vite` / `SPA fallback` / `frontend/` 在 6 份文档中都要出现。

### 12.2 触发条件：什么时候必须改文档

| 改动类型 | 必须更新的文档 | 章节 |
|---|---|---|
| 加 / 删 / 改 SQLAlchemy 模型字段 | README + PROJECT_STATE + ARCHITECTURE | README §3.3 / PROJECT_STATE §2 / ARCHITECTURE §4.2 |
| 加 / 删 / 改 Pydantic schema 字段 | README + HANDOFF | README §3.2 / HANDOFF §6.11 |
| 加 / 删 / 改 API 端点 | README + HANDOFF | README §3.8 / HANDOFF §7.2 |
| 加 / 删 / 改后台 SSR 页面 | README + PROJECT_STATE + ARCHITECTURE | README §3.5 / PROJECT_STATE §2 / ARCHITECTURE §5 |
| **加 / 删 / 改 Vue 视图 / 路由 / store** | README + HANDOFF + ARCHITECTURE + DEVELOPMENT | README §2 + §3.5 / HANDOFF §2 + §5.8 / ARCHITECTURE §1.1 / DEVELOPMENT §1.9 |
| **加 / 删 / 改 Vite / Tailwind / 前端依赖** | README + HANDOFF + DEPLOYMENT | README §1.3 + §3.5 / HANDOFF §2 / DEPLOYMENT「前端构建」 |
| 加 / 删 / 改能量规则 / 单日上限 | README + HANDOFF + ARCHITECTURE | README §3.4 / HANDOFF §5.3 / ARCHITECTURE §4.3 |
| 加 / 删 / 改业务常量 | README + PROJECT_STATE | README §3.6 / PROJECT_STATE §3 |
| 加 / 改 / 删依赖 | requirements.txt + HANDOFF + frontend/package.json | requirements.txt / HANDOFF §2 / frontend/package.json |
| 加 / 改 / 删 .env 配置项 | .env.example + HANDOFF + DEPLOYMENT | .env.example / HANDOFF §1 / DEPLOYMENT「AI 接入」 |
| 改端口 / 启动命令 | README + DEPLOYMENT + HANDOFF | README §1 / DEPLOYMENT 全文 / HANDOFF §1 |
| 改 CSS 变量 / 配色 | README + frontend/tailwind.config.js | README §3.5 / tailwind.config.js token |
| 改后台入口路径 / 新后台 API | HANDOFF + ARCHITECTURE + PROJECT_STATE | HANDOFF §5.6 / ARCHITECTURE §6.5 / PROJECT_STATE §2 |
| 修 Bug（任何） | HANDOFF + DEVELOPMENT | HANDOFF §6 / DEVELOPMENT §3 |
| 引入新的「踩坑」 | HANDOFF + DEVELOPMENT | HANDOFF §6 / DEVELOPMENT §3 |

### 12.3 同步时序

```
改代码 → 改对应文档 → 跑验证（curl 冒烟 / 端到端） → git add . → git commit → git push
                                          ↑                            │            │
                                          └────── 验证发现还得改 ←──────┘            │
                                                                                    ↓
                                          验证通过 ←─── 文档跟着改好 ←──── 远端接收 ←┘
```

> ❌ 反例 A：commit `feat(xxx): ...` 一小时后才想起来 README 没改 → 单独再发一个 `docs(readme): ...` commit
> ❌ 反例 B：本地 commit 完不 push，留到明天 / 下周 / 「攒一波一起推」→ 仓库永远落后本地
> ✅ 正例：feat commit **里面** README 同步改好 → 紧接着 `git push origin main` → 远端 / 本地**完全一致**

### 12.4 文档 ≠ 摆设 — 验收清单

每次提交前过一遍：
- [ ] 改了 schema → `to_public_dict()` 与 `*Out` schema 字段一致（参考 §6.11）
- [ ] 改了 model 字段长度 / 类型 → schema 的 `max_length` / 类型也同步（→ 如 v2.4.4 `avatar 字段长度 String(255) / ProfileUpdateIn max_length=255`）
- [ ] 改了 model → `_migrate_legacy_columns()` 也加了（参考 §6.10）
- [ ] 改了 energy → `constants.py` + `energy_service.py` 同步
- [ ] 改了 config → `.env.example` 同步
- [ ] 改了后台 → `[ADMIN] password` 怎么获取这一段还是有效的
- [ ] 改了 §5.6 / §10 边界 → 至少另一个文档里引用了它的地方也更新了

### 12.5 文档不能「之后再补」

> 「代码先提交，文档我周末补」 = **永远不会补**。

如果某次改动太急没时间更新文档：
1. commit message 里**必须**明确写 `WIP: docs pending`
2. **当天**至少把对应的「改了」表里那一行填上
3. 下一条 commit 之前必须把文档补完

### 12.6 自动推送铁律（commit 完必须立即 push，使用 gh）

> 🔒 跟 §12.1 同一优先级。**任务完成的定义包含「远端已同步」，本地 commit 不算完成。**

**认证前置**：推送前先跑 `gh auth status`；token 失效时执行 `gh auth refresh -h github.com`（或 `gh auth login`），并用 `gh auth setup-git` 让 git 复用 gh 凭据。认证修不好就如实报告并停止，不得声称完成。

**铁律**：`git commit` 完之后**立刻** `git push origin main`，**不允许**：
- ❌ 「先 commit 完，一会儿一起推」→ 仓库永远落后本地
- ❌ 「明天再推」→ 第二天忘了 → 本地数据丢失 / 换电脑没同步
- ❌ 「攒一周的 commit 一起推」→ 出错时回滚困难
- ❌ 「push 前再 review 一下」→ 没问题立即推，「review 完忘了」也算违反

**正确做法**：
```bash
gh auth status                 # 认证前置：必须通过
gh auth setup-git              # 让 git 复用 gh 凭据（首次/换机时）
git add -A
git commit -m "fix(auth): add is_admin field to AuthOut schema"
git push origin main           # ← 必须紧跟 commit
git status --short             # 应为空
git ls-remote origin refs/heads/main   # 与 git rev-parse HEAD 一致
# 或 gh api repos/sunday-lil/jingyu/commits/main --jq .sha
```

**push 失败的应急**：
- 网络问题：retry 一次；再失败 → 截图报错，留 `WIP: push pending` 标记
- 远端冲突：`git pull --rebase` → 解决 → `git push`（**不要** `git push --force`，除非你 100% 确定）
- 权限问题：`gh auth status` 确认账号；token 失效 → `gh auth refresh -h github.com` / `gh auth login` → `gh auth setup-git` → 重试

**特殊场景**（可以延迟 push）：
- 多文件多模块大改（> 5 个文件）：允许攒一个原子 commit 一起推
- 写到一半想先备份：可以 `git stash` + 暂存，但 stash 完**也必须**当天处理掉

### 12.7 Commit 标题 / 脚本标题规范（Conventional Commits）

> 无论代码 commit 还是脚本（如 `push-to-github.ps1`）里的进度输出，**统一**用 Conventional Commits 风格。

#### 12.7.1 Commit message 格式

```
<type>(<scope>): <subject>           ← 第一行，subject ≤ 50 字符

<body>                               ← 可选，72 字符 / 行，列改动点
- bullet 1
- bullet 2

<footer>                             ← 可选
BREAKING CHANGE: ...
Refs: HANDOFF §6.11
```

#### 12.7.2 Type 清单（必用）

| type | 含义 | 例子 |
|---|---|---|
| `feat` | 新功能 | `feat(admin): add user detail page` |
| `fix` | 修 Bug | `fix(auth): add is_admin field to AuthOut` |
| `refactor` | 重构（无功能变化） | `refactor(energy): extract constants` |
| `docs` | 仅文档 | `docs(readme): add GitHub badges` |
| `style` | 格式（空格/引号/CSS 微调） | `style(admin): rename card icons` |
| `test` | 测试 | `test(schemas): add Out field check` |
| `chore` | 杂事（依赖 / 配置） | `chore: bump FastAPI to 0.116` |
| `perf` | 性能 | `perf(music): lazy-load tracks` |
| `revert` | 回滚 | `revert: feat(admin): add user detail` |

#### 12.7.3 Scope 清单（项目模块名）

```
auth, diary, mood, music, energy, garden, admin, templates, static,
docs, deps, config, start, deploy, healing (通用), scripts
```

无明确 scope → 省略括号（`chore: bump version` 而不是 `chore(): ...`）

#### 12.7.4 标题规则

- ✅ 用动词原形开头：`add` / `fix` / `remove` / `bump` / `refactor`
- ✅ 全部小写（专有名词除外：`FastAPI` / `Jinja2` / `SQLite`）
- ✅ 句尾**不加**句号
- ✅ 50 字符以内，超了就换 scope 或简化
- ❌ 不要：`feat: 修改了一些东西` / `fix: 修复 bug` / `update code`

#### 12.7.5 完整 commit 示例

```bash
# 修 Bug
git commit -m "fix(auth): add is_admin field to AuthOut schema

Pydantic response_model silently filters out undeclared fields,
so frontend always gets data.is_admin === undefined and the
'no admin permission' branch always triggers.

Refs: HANDOFF §6.11, DEVELOPMENT §3.10"

# 新功能
git commit -m "feat(admin): add user detail page with energy audit

- show diary/mood/energy/garden counts
- show recent 10 entries of each
- allow admin to adjust energy (logged in EnergyRecord.source='admin_adjust')
- allow admin to reset user password (bcrypt rehash)

Refs: HANDOFF §5.6, ARCHITECTURE §6.5"

# 仅文档
git commit -m "docs(github): add repo URL + fix topics loop

- HANDOFF.md: GitHub URL in top note + §1
- PROJECT_STATE.md: add session 3 changelog
- README.md: add 4 badges
- push-to-github.ps1: topics now loops (--add-topic accepts 1 arg)"

# 杂事
git commit -m "chore(deps): bump bcrypt to 4.2"
```

#### 12.7.6 脚本/工具里的进度标题

`push-to-github.ps1` 这种工具脚本里，**每一步的输出标题也要遵守 type(scope) 风格**：

```powershell
Write-Host "[1/6] chore(git): removing broken .git ..." -ForegroundColor Yellow
Write-Host "[2/6] chore(git): git init -b main ..."       -ForegroundColor Yellow
Write-Host "[3/6] feat(git): staging files ..."          -ForegroundColor Yellow
Write-Host "[4/6] feat(git): committing ..."              -ForegroundColor Yellow
Write-Host "[5/6] feat(github): creating repo + push ..." -ForegroundColor Yellow
Write-Host "[6/6] feat(github): setting topics ..."       -ForegroundColor Yellow
```

> 这样跑完脚本，看到日志就能**复述出**「这次提交是 chore(git) + feat(github)」，自动同步到 commit 历史。

---

> 最后更新：2026-10-18（文档结构整理：去重版本块、按代码修正事实、历史细节归入 [CHANGELOG.md](CHANGELOG.md)）。
> 代码版本：v2.6.2（2026-10-25）。
