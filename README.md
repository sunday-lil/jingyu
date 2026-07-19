# 静屿 — 治愈系身心疗愈平台

> **非商业 · 纯治愈 · 强隐私 · 轻运营**

[![GitHub](https://img.shields.io/badge/GitHub-sunday--lil%2Fjingyu-181717?logo=github)](https://github.com/sunday-lil/jingyu)
[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)](https://www.python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Status](https://img.shields.io/badge/status-v1%20shipped-success)]()

一个旨在缓解现代人焦虑情绪、关注心理健康的 Web 应用。通过「古琴五音疗愈」与「私密情绪记录」相结合，提供一个安全、安静、无压力的精神角落。

> 🤖 **AI 接手请先看 [HANDOFF.md](file:///c:/Users/Administrator/Desktop/webwrold/HANDOFF.md)**，那是元信息 + 关键决策 + 踩坑清单的汇总。

---

## 0. 一句话速览

**FastAPI（纯 API 后端）+ Vue 3 SPA + SQLite** 的中文治愈系 Web 应用。完整 4 阶段功能：古琴五音疗愈、漂流瓶日记、情绪日历、精神花园。前端 Vue 3 `<script setup>` + Vite 5 + Vue Router 4 + Pinia + Tailwind CSS + GSAP + @vueuse/motion + Three.js + axios，后端约 2 000 行 Python。无商业元素、无广告、无内购。

> 📌 **2026-07-19 全站 Vue 3 重构**：前端从「Jinja2 SSR + 原生 HTML/CSS/JS」迁移到「Vue 3 SPA + Vite 工程化」。FastAPI 后端简化为纯 API + SPA fallback，所有页面逻辑迁入 `frontend/src/views/` 13 个 .vue 视图。详见 [HANDOFF.md](file:///c:/Users/Administrator/Desktop/webwrold/HANDOFF.md) 元信息。

**强隐私承诺**：用户日记内容使用对称加密存储，密钥与用户密码派生。即便数据库泄露也无法直接读取明文（端到端加密）。

**AI 全面接入**（2026-07-17 加入，**可选**功能）：基于 NVIDIA NIM API（OpenAI 兼容格式，模型 `meta/llama-3.1-8b-instruct`）的 4 个治愈场景——AI 树洞对话、漂流瓶 AI 鼓励语、情绪日历 AI 治愈语、首页音乐 AI 心情推荐。**不配置 API key 时所有功能照常可用**（优雅降级，仅少 AI 文案），保持「渐进增强」原则。AI 文案不入库，对话历史只在浏览器内存（刷新即清空）。

---

## 1. 跑起来

### 1.1 推荐：`start.py` 一键起

```bash
# 安装依赖
pip install -r requirements.txt

# 启动（后台运行，端口默认 5000）
python start.py

# 浏览器打开 http://127.0.0.1:5000
```

**服务管理：**
```bash
python start.py start     # 后台启动（默认）
python start.py stop      # 停止
python start.py restart   # 重启
python start.py status    # 查 PID
python start.py fg        # 前台（systemd / 调试用）
python start.py --init-db # 启动前重置数据库
```

PID 写入 `run/healing.pid`，日志写入 `logs/healing.log`。

### 1.2 备选：直接 uvicorn

```bash
python -m uvicorn app.main:app --reload --port 5000
```

启动入口是 [app/main.py](file:///c:/Users/Administrator/Desktop/webwrold/app/main.py)。`--reload` 模式适合本地改代码热重启，**不要**在生产用。

### 1.3 前端开发模式（Vue 3 + Vite 热更新）

2026-07-19 全站 Vue 3 重构后，前端代码独立到 [`frontend/`](file:///c:/Users/Administrator/Desktop/webwrold/frontend/) 目录，开发时用 Vite dev server 跑 SPA，热更新：

```bash
cd frontend
npm install     # 首次：装 vue / vue-router / pinia / axios / gsap / three / @vueuse/motion / tailwindcss / vite 等（含 three.js 大包，约 7 分钟）
npm run dev     # 启动 Vite dev server，访问 http://127.0.0.1:5173/
```

**dev proxy**：[frontend/vite.config.js](file:///c:/Users/Administrator/Desktop/webwrold/frontend/vite.config.js) 把 `/api` / `/static` / `/admin` 反代到 FastAPI `:5000`，所以 Vite 跑 :5173、FastAPI 跑 :5000 同时开着，前端调 API 走代理无跨域。**注意** Vite host 显式设为 `127.0.0.1`（默认监听 IPv6 `[::1]` 会导致 127.0.0.1 连不上，详见 [HANDOFF.md](file:///c:/Users/Administrator/Desktop/webwrold/HANDOFF.md) 踩坑清单）。

**生产模式**：见 §1.1，`cd frontend && npm run build` 输出到 `static/dist/`，再 `python start.py` 走 FastAPI SPA fallback（详见 [docs/ARCHITECTURE.md](file:///c:/Users/Administrator/Desktop/webwrold/docs/ARCHITECTURE.md)「开发/生产模式切换」节）。

---

## 2. 完整目录树

```
webwrold/
├── start.py                      # 一键启动脚本（start/stop/restart/status/fg）
├── README.md                     # 本文件
├── HANDOFF.md                    # AI 交接说明（必读）
│
├── app/
│   ├── __init__.py
│   ├── main.py                   # FastAPI 入口 + 路由注册 + 启动事件
│   ├── config.py                 # 配置（环境变量 QI_* + 默认值）
│   ├── database.py               # SQLAlchemy 引擎 + Session + init_db
│   ├── deps.py                   # 公共依赖（current_user、db）
│   ├── security.py               # 会话签名 + cookie 读写
│   ├── seed.py                   # 启动时种子（5 音曲目 + 商店物品）
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py               # User
│   │   ├── diary.py              # Diary（加密存储）
│   │   ├── mood.py               # MoodCheckin
│   │   ├── music.py              # Music
│   │   ├── energy.py             # EnergyRecord
│   │   ├── garden.py             # GardenItem / ShopItem
│   │   └── encouragement.py      # Encouragement（陌生人鼓励语）
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── diary.py
│   │   ├── mood.py
│   │   ├── music.py
│   │   ├── energy.py
│   │   └── ai.py                 # AI 4 场景入参/出参（2026-07-17 加）
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── pages.py              # SPA 兼容重定向（4 个 302：/mood→/calendar、/mood-calendar→/calendar、/my-bottles→/diary、/pick→/diary/pick）
│   │   ├── auth.py               # /api/auth/*
│   │   ├── music.py              # /api/music/*
│   │   ├── diary.py              # /api/diary/*
│   │   ├── mood.py               # /api/mood/*
│   │   ├── energy.py             # /api/energy/*
│   │   ├── garden.py             # /api/garden/*
│   │   └── ai.py                 # /api/ai/* 4 个 AI 端点（2026-07-17 加）
│   ├── services/
│   │   ├── __init__.py
│   │   ├── energy_service.py     # 能量获取规则（听歌 90%+ / 日记 / 打卡 / 连胜）
│   │   ├── diary_service.py      # 漂流瓶随机拾取
│   │   ├── mood_service.py       # 心情日历统计 + 趋势数据
│   │   └── ai_service.py         # NVIDIA NIM API 调用 + 降级处理（2026-07-17 加）
│   └── utils/
│       ├── __init__.py
│       ├── constants.py          # 5 音定义 / 心情枚举 / 能量来源枚举
│       └── crypto.py             # bcrypt + Fernet + PBKDF2
│
├── templates/                    # Jinja2 SSR 模板
│   ├── base.html                 #   全局骨架（导航 + Toast + 页脚）
│   ├── _nav.html                 #   导航宏
│   ├── _toast.html               #   全局 Toast 提示
│   ├── index.html                #   首页（5 音入口 + 漂流瓶入口 + 情绪日历入口 + AI 推荐音卡片）
│   ├── login.html / register.html
│   ├── music_list.html           #   单音曲目列表 + 沉浸式播放器
│   ├── diary_write.html          #   漂流瓶写作页（含投瓶动效）
│   ├── my_bottles.html           #   我的瓶子时间线
│   ├── diary_detail.html         #   单个瓶子详情
│   ├── pick_bottle.html          #   拾取陌生人漂流瓶（含 #ai-encouragement 容器）
│   ├── mood_calendar.html        #   情绪日历（今日打卡 + 月历 + 30 天趋势 + #ai-healing-msg 容器）
│   ├── garden.html               #   精神花园（已种植物 + 装扮）
│   ├── shop.html                 #   兑换商店（花种 / 装扮 / 徽章）
│   └── ai_chat.html              #   AI 树洞对话页（2026-07-17 加，需登录，多轮对话仅存浏览器）
│
├── frontend/                     # Vue 3 SPA 源码（2026-07-19 全站重构加）
│   ├── package.json              #   依赖：vue ^3.4 / vue-router ^4.4 / pinia ^2.2 / axios ^1.7 / gsap ^3.12 / @vueuse/motion ^2.2 / three ^0.168；devDeps：vite ^5.4 / @vitejs/plugin-vue ^5.1 / tailwindcss ^3.4 / postcss / autoprefixer
│   ├── vite.config.js            #   dev proxy /api、/static、/admin → :5000；build outDir ../static/dist；base 仅 build 时为 /static/dist/；host 127.0.0.1，strictPort
│   ├── tailwind.config.js        #   治愈系色彩 token（mist/ink/五音色/accent）+ 动画（breathe/float/fade-up）
│   ├── postcss.config.js
│   ├── index.html                #   HTML 壳
│   └── src/
│       ├── main.js               #   入口（createApp + Pinia + Router + MotionPlugin）
│       ├── App.vue               #   根组件（AppLayout + router-view + transition）
│       ├── assets/
│       │   └── styles/main.css   #   Tailwind 指令 + 全局 CSS 变量 + 通用组件类（.btn/.card/.form-input）+ 系统字体（PingFang SC/Microsoft YaHei，零网络请求）
│       ├── router/
│       │   └── index.js          #   路由：/ /login /register /music /music/:yin /diary /diary/write /diary/pick /calendar /ai-chat /garden /shop /404；requiresAuth 守卫
│       ├── api/
│       │   └── index.js          #   axios 实例，baseURL=/api，withCredentials=true，401 自动跳登录
│       ├── stores/
│       │   └── user.js           #   Pinia user store（cookie session 模式，不存 token，只缓存 user 对象到 localStorage）
│       ├── components/
│       │   └── AppLayout.vue     #   桌面顶部导航 + 移动端底部 tabbar（768px 断点）
│       └── views/                #   13 个视图（一个功能一个 .vue）
│           ├── HomeView.vue              # 首页：Hero + 五音入口 + 模块卡 + GSAP 入场
│           ├── auth/
│           │   ├── LoginView.vue
│           │   └── RegisterView.vue
│           ├── music/
│           │   ├── MusicListView.vue     # 含 AI 帮我选音
│           │   └── MusicDetailView.vue   # 含底部播放器 + 听完 90% 调 /api/music/listen-complete
│           ├── diary/
│           │   ├── DiaryListView.vue     # 时间线 + Web Crypto 解密
│           │   ├── DiaryWriteView.vue    # 心情 emoji + 加密
│           │   └── PickBottleView.vue    # 拾瓶 + AI 鼓励语
│           ├── mood/
│           │   └── MoodCalendarView.vue  # 日历网格 + 30 天趋势 + AI 治愈语
│           ├── ai/
│           │   └── AIChatView.vue        # 多轮对话，历史只在内存
│           ├── garden/
│           │   ├── GardenView.vue        # 能量/来源/物品/流水
│           │   └── ShopView.vue          # 按 item_type 分组 + 兑换
│           └── NotFoundView.vue
│
├── static/
│   ├── css/
│   │   ├── style.css             #   入口（@import 7 个模块）
│   │   ├── 00-variables.css      #   CSS 变量（治愈系配色 + 字体）
│   │   ├── 01-reset.css          #   重置 + body 渐变背景
│   │   ├── 02-layout.css         #   .container / .nav / .grid
│   │   ├── 03-components.css     #   .btn / .card / .toast / .form
│   │   ├── 04-pages.css          #   首页 / 列表页 / 详情页
│   │   ├── 05-animations.css     #   漂流瓶动效 / 心情弹跳 / 花朵生长 / 滚动渐显 / 涟漪 / 花瓣 / 频谱
│   │   └── 06-music.css          #   沉浸式播放器
│   ├── js/
│   │   ├── app.js                #   window.QI 全局（fetch / toast / confirmThen / reveal / ripple / countUp / confetti）
│   │   └── pages/                #   每个页面一个
│   ├── audio/                    #   占位音频（5 个 mp3，每音一个）
│   └── images/                   #   占位封面（5 音各 1 张 SVG）
│
├── data/
│   └── healing.db                # SQLite 数据库（git 忽略）
├── run/
│   └── healing.pid               # 后台进程 PID
├── logs/
│   └── healing.log               # 后台进程日志
│
├── docs/                         # 详细文档
│   ├── ARCHITECTURE.md
│   ├── DEPLOYMENT.md
│   ├── DEVELOPMENT.md
│   └── PROJECT_STATE.md
│
├── .env.example
├── requirements.txt
└── README.md
```

---

## 3. 架构与关键设计

### 3.1 应用入口（[app/main.py](file:///c:/Users/Administrator/Desktop/webwrold/app/main.py)）

`FastAPI()` 实例 → 挂载静态文件 → 注册 API router（auth/music/diary/mood/energy/garden/ai + admin）+ 1 个 SPA 兼容重定向 router（[pages.py](file:///c:/Users/Administrator/Desktop/webwrold/app/routers/pages.py)）→ 注册 `startup` 事件初始化数据库 + 种子数据 → **SPA fallback**。

**前后端分离 + SPA fallback**（2026-07-19 全站 Vue 3 重构后）：
- **前端**：Vue 3 SPA 工程化在 [`frontend/`](file:///c:/Users/Administrator/Desktop/webwrold/frontend/)，`npm run build` 输出到 `static/dist/`，含 `index.html` + JS/CSS chunk
- **后端**：FastAPI 只提供 `/api/*` JSON 接口 + SPA fallback；前台不再用 Jinja2 渲染（仅 `/admin/*` 后台仍保留 SSR）
- **SPA fallback**：所有未匹配的 GET 请求（排除 `/api/`、`/static/`、`/admin`、`/docs`）返回 `static/dist/index.html`；若 `dist` 未构建返回提示页引导访问 Vite dev server
- **路由兼容层**：[app/routers/pages.py](file:///c:/Users/Administrator/Desktop/webwrold/app/routers/pages.py) 简化为 4 个 302 重定向（`/mood`→`/calendar`、`/mood-calendar`→`/calendar`、`/my-bottles`→`/diary`、`/pick`→`/diary/pick`），兼容旧书签
- **认证机制（不变）**：cookie session（不是 JWT token），登录用 nickname（不是 username），登录/注册直接返回 user 对象（不是 `{access_token, user}`），前端 userStore 只缓存 user 对象到 localStorage，不存 token
- **配置修复**：[app/config.py](file:///c:/Users/Administrator/Desktop/webwrold/app/config.py) 加 `env_prefix="qi_"`，让 `.env` 里 `QI_*` 变量正确加载
- **AI 调整**：[app/services/ai_service.py](file:///c:/Users/Administrator/Desktop/webwrold/app/services/ai_service.py) 超时 30s→60s；模型链 `nvidia/llama-3.1-nemotron-70b-instruct` → `meta/llama-3.3-70b-instruct` → `meta/llama-3.1-8b-instruct`
- **删除的旧页面**：showcase 动效页（`templates/showcase.html`、`static/js/pages/showcase.js`、`static/css/08-showcase.css`）已删

> 改代码 + 改文档 = 同一个 commit（详见 [HANDOFF §12](file:///c:/Users/Administrator/Desktop/webwrold/HANDOFF.md) 文档自动同步铁律）。本次 Vue 3 重构同步更新 6 份文档（README / HANDOFF / PROJECT_STATE / ARCHITECTURE / DEPLOYMENT / DEVELOPMENT），互链保持一致。

### 3.2 数据访问层（`app/models/`）

使用 **SQLAlchemy 2.0 ORM**。每个模型一个文件，`app/models/__init__.py` 统一 import。

| 模型 | 文件 | 关键字段 |
|---|---|---|
| `User` | models/user.py | id, nickname, password_hash, encryption_salt, total_energy, created_at |
| `Diary` | models/diary.py | id, user_id, content_encrypted, mood_type, is_public, created_at |
| `MoodCheckin` | models/mood.py | id, user_id, check_date, mood_emoji, note |
| `Music` | models/music.py | id, title, audio_url, cover_image, yin_type, duration, tags |
| `EnergyRecord` | models/energy.py | id, user_id, amount, source, created_at |
| `ShopItem` | models/garden.py | id, name, item_type, cost, image |
| `GardenItem` | models/garden.py | id, user_id, item_id, obtained_at |
| `Encouragement` | models/encouragement.py | id, from_user_id, to_user_id, diary_id, content |

**新增模型**：在 `app/models/<name>.py` 写一个 `class Xxx(Base): ...`，然后在 `app/models/__init__.py` 里 import 它，重启即可（`init_db` 会自动建表）。

### 3.3 鉴权与会话

- **密码哈希**：`bcrypt`（直接使用，passlib 与新版 bcrypt 4.x 不兼容），注册时 `hash_password(pw)`，登录时 `verify_password(pw, hash)`。密码超 72 字节自动截断。
- **密码输入可见性切换**：登录 / 注册 / 日记解锁 modal 的密码框统一用 `.password-input-wrap` + `.password-toggle` 👁 按钮，点击切换明文/掩码；`app.js initPasswordToggle()` 用 document-level 事件委托，动态生成的 modal 也生效（2026-07-16 会话 7 加）。
- **会话**：用 `itsdangerous.URLSafeTimedSerializer` 签名 session_id，存在 cookie 里，HttpOnly + SameSite=Lax。
- **日记加密**：用户注册时生成随机 `encryption_salt` 存入 User 表。每次写日记时用 `PBKDF2HMAC(pw + salt)` 派生 Fernet 密钥，**密钥不存数据库**，只存在用户登录后的 session 上下文里。退出登录即丢失。
- **隐私边界**：管理员视图只能看到 `Diary.content_encrypted`（密文），没有任何方式读取明文。

### 3.4 能量规则（[app/services/energy_service.py](file:///c:/Users/Administrator/Desktop/webwrold/app/services/energy_service.py)）

| 行为 | 增量 | 来源 code |
|---|---|---|
| 听完一首曲子（进度 ≥ 90%） | +1 露水 | `listen_music` |
| 写完一篇日记并投入 | +2 阳光 | `write_diary` |
| 当日心情打卡 | +1 养分 | `checkin` |
| 连续 7 天打卡 | +5 阳光 | `streak_7` |
| 兑换商店物品 | -cost | `exchange` |

每次能量变动都写一条 `EnergyRecord`，用户主页能看历史。所有「+x」单日上限：露水 20、阳光 10、养分 5（防刷）。

### 3.5 前端架构（Vue 3 SPA，2026-07-19 重构）

**前台 = Vue 3 SPA**（[`frontend/`](file:///c:/Users/Administrator/Desktop/webwrold/frontend/)）：

- **技术栈**：Vue 3 `<script setup>` + Vite 5 + Vue Router 4 + Pinia + Tailwind CSS + GSAP + @vueuse/motion + Three.js + axios
- **入口**：[frontend/src/main.js](file:///c:/Users/Administrator/Desktop/webwrold/frontend/src/main.js) `createApp(App).use(pinia).use(router).use(MotionPlugin).mount('#app')`
- **根组件**：[frontend/src/App.vue](file:///c:/Users/Administrator/Desktop/webwrold/frontend/src/App.vue) = `AppLayout`（导航/tabbar）+ `<router-view>` + `<transition>`
- **路由**：[frontend/src/router/index.js](file:///c:/Users/Administrator/Desktop/webwrold/frontend/src/router/index.js) 13 条路由（`/` / `/login` / `/register` / `/music` / `/music/:yin` / `/diary` / `/diary/write` / `/diary/pick` / `/calendar` / `/ai-chat` / `/garden` / `/shop` / `/:pathMatch(.*)*` 404），`meta.requiresAuth` 守卫
- **API 客户端**：[frontend/src/api/index.js](file:///c:/Users/Administrator/Desktop/webwrold/frontend/src/api/index.js) axios 实例，`baseURL=/api` + `withCredentials=true` + 401 自动跳 `/login`
- **状态管理**：[frontend/src/stores/user.js](file:///c:/Users/Administrator/Desktop/webwrold/frontend/src/stores/user.js) Pinia user store；cookie session 模式，**不存 token**，只缓存 user 对象到 localStorage
- **布局**：[frontend/src/components/AppLayout.vue](file:///c:/Users/Administrator/Desktop/webwrold/frontend/src/components/AppLayout.vue) 桌面顶部导航 + 移动端底部 tabbar（768px 断点）
- **样式**：Tailwind CSS + [frontend/src/assets/styles/main.css](file:///c:/Users/Administrator/Desktop/webwrold/frontend/src/assets/styles/main.css) 全局 CSS 变量 + 通用组件类（`.btn` / `.card` / `.form-input`）+ 系统字体（`PingFang SC` / `Microsoft YaHei`，**零网络请求**，不再依赖 Google Fonts 国内镜像）
- **治愈系配色**（[frontend/tailwind.config.js](file:///c:/Users/Administrator/Desktop/webwrold/frontend/tailwind.config.js)）：米白 `#F9F6F0` + 茶褐 `#8B7B5E` + 雾粉 / 雾蓝 / 青绿点缀；动画 token `breathe` / `float` / `fade-up`
- **动效**：GSAP 入场 stagger 浮入 + 呼吸动效；`prefers-reduced-motion` 自动降级
- **日记加密**：浏览器 Web Crypto API（PBKDF2 + Fernet 等价 AES-128-CBC），前端加密后只发密文给服务端
- **响应式**：桌面顶部导航 + 移动端底部 tabbar，768px 断点切换

**后台 = Jinja2 SSR**（保留）：`/admin/*` 仍用 [templates/admin/](file:///c:/Users/Administrator/Desktop/webwrold/templates/admin/) + [static/css/07-admin.css](file:///c:/Users/Administrator/Desktop/webwrold/static/css/07-admin.css) + `static/js/pages/admin_*.js`，与前台 Vue SPA 完全隔离。

**旧 Jinja2 前台模板**（`templates/base.html` / `_nav.html` / `index.html` 等）仍保留在仓库，但 Vue 3 重构后**不再被路由引用**，仅作历史参考。新功能一律加在 `frontend/src/views/`。

> 想知道前端架构为什么这么分，看 [docs/ARCHITECTURE.md](file:///c:/Users/Administrator/Desktop/webwrold/docs/ARCHITECTURE.md)「前端架构」节；想本地起前端热更新，看 §1.3；想构建生产包，看 [docs/DEPLOYMENT.md](file:///c:/Users/Administrator/Desktop/webwrold/docs/DEPLOYMENT.md)「前端构建」。

### 3.6 5 音定义（[app/utils/constants.py](file:///c:/Users/Administrator/Desktop/webwrold/app/utils/constants.py)）

```python
YIN_TYPES = {
    "gong":  {"name": "宫", "element": "土", "organ": "脾胃", "tags": ["健脾", "助消化"]},
    "shang": {"name": "商", "element": "金", "organ": "肺大肠", "tags": ["润肺", "舒缓"]},
    "jue":   {"name": "角", "element": "木", "organ": "肝胆", "tags": ["疏肝", "解郁", "抗焦虑"]},
    "zhi":   {"name": "徵", "element": "火", "organ": "心小肠", "tags": ["养心", "安神"]},
    "yu":    {"name": "羽", "element": "水", "organ": "肾膀胱", "tags": ["宁心", "助眠"]},
}
```

### 3.7 AI 接入（NVIDIA NIM API，可选，2026-07-17 加入）

4 个治愈场景，全部走 NVIDIA NIM API（OpenAI 兼容格式 `/chat/completions`，模型 `meta/llama-3.1-8b-instruct`）。**未配置 API key 时端点返回 200 + `available:false` + 治愈系友好提示**，前端照常显示文案不报错——AI 是「渐进增强」，不是核心功能。

| 场景 | 前端入口 | 后端端点 | AI 文案去向 |
|---|---|---|---|
| AI 树洞对话 | `/ai-chat`（独立页面，需登录） | `POST /api/ai/chat` | 仅浏览器内存，刷新即清空，**不落库** |
| 漂流瓶 AI 鼓励语 | `/pick` 拾瓶后 `#ai-encouragement` | `POST /api/ai/encouragement` | 给读者看的现场文案，**不写库**，不污染作者收件箱 |
| 情绪日历 AI 治愈语 | `/mood-calendar` 打卡后 `#ai-healing-msg` | `POST /api/ai/healing` | 显示在今日心情卡片下方，**不落库** |
| 音乐 AI 心情推荐 | 首页 `/` 「AI 帮我选音」卡片（仅登录可见） | `POST /api/ai/recommend-music` | 推荐宫商角徵羽之一 + 理由 + 跳转 `/music/{yin}` 链接 |

**4 个 AI 场景的隐私承诺**：
- AI 树洞对话历史只在浏览器内存，刷新清空，**不落库**
- 漂流瓶 AI 鼓励语是给读者看的，不写入数据库，不污染作者收件箱
- 情绪日历 AI 治愈语也不落库
- 用户日记内容传给 AI 时只取**前 120 字**预览（在 `ai_service.generate_encouragement()` 里截断）

**相关文件**：
- 配置：[app/config.py](file:///c:/Users/Administrator/Desktop/webwrold/app/config.py) `Settings` 类的 `nvidia_api_key` / `ai_model` / `ai_base_url`
- Schema：[app/schemas/ai.py](file:///c:/Users/Administrator/Desktop/webwrold/app/schemas/ai.py) 7 个 Pydantic 模型
- Service：[app/services/ai_service.py](file:///c:/Users/Administrator/Desktop/webwrold/app/services/ai_service.py) — `AIServiceUnavailable` 异常 + 4 个系统提示词常量 + `_call_nvidia()` 底层调用 + 4 个上层方法
- Router：[app/routers/ai.py](file:///c:/Users/Administrator/Desktop/webwrold/app/routers/ai.py) 4 个端点（全部 `Depends(get_current_user)` + 全部有降级处理）
- 依赖：[requirements.txt](file:///c:/Users/Administrator/Desktop/webwrold/requirements.txt) 新增 `httpx>=0.27.0,<0.29.0`

**.env 配置示例**（在 [.env.example](file:///c:/Users/Administrator/Desktop/webwrold/.env.example) 末尾，默认注释掉）：
```env
# AI 接入（可选，不配置时所有功能正常，AI 端点会优雅降级）
# QI_NVIDIA_API_KEY=nvapi-xxxxx
# QI_AI_MODEL=meta/llama-3.1-8b-instruct
# QI_AI_BASE_URL=https://integrate.api.nvidia.com/v1
```

> 模型默认用 `meta/llama-3.1-8b-instruct`（8B 小模型，响应快：首次 5-10s，后续 1-3s）。原默认 `nvidia/llama-3.1-nemotron-70b-instruct` 在用户 NVIDIA 账户下 API 返回 404（"Function not found for account"，账户实际有 119 个可用模型但不含该 70B 模型），故换 8B 兼顾速度与质量。NVIDIA 提供**免费 API key**，注册 [build.nvidia.com](https://build.nvidia.com) 即可获取，符合本项目「非商业纯治愈」调性。

---

## 4. 数据库表速查

| 表 | 关键字段 | 说明 |
|---|---|---|
| `users` | id, nickname, password_hash, encryption_salt, total_energy | 用户（encryption_salt 用于日记加密） |
| `diaries` | id, user_id, content_encrypted, mood_type, is_public, created_at | 漂流瓶（密文） |
| `mood_checkins` | id, user_id, check_date, mood_emoji, note | 心情打卡 |
| `musics` | id, title, audio_url, cover_image, yin_type, duration, tags | 古琴曲目 |
| `energy_records` | id, user_id, amount, source, created_at | 能量流水 |
| `shop_items` | id, name, item_type, cost, image | 商店物品 |
| `garden_items` | id, user_id, item_id, obtained_at | 用户持有 |
| `encouragements` | id, from_user_id, to_user_id, diary_id, content | 陌生人鼓励语 |

---

## 5. 常见改动 — 「我要加 X」速查

### 我要加一个新页面
1. 写 `templates/your_page.html`：`{% extends "base.html" %}` + `{% block content %}`。
2. 在 [app/routers/pages.py](file:///c:/Users/Administrator/Desktop/webwrold/app/routers/pages.py) 加 `@router.get("/your-path")` + `return TemplateResponse("your_page.html", {...})`。
3. 页面专属 JS：写 `static/js/pages/your_page.js`，模板底部 `<script defer src="/static/js/pages/your_page.js"></script>`。

### 我要加一个 API
1. 在对应的 `app/routers/<name>.py` 加 `@router.post("/api/...")`。
2. 入参用 Pydantic model（在 `app/schemas/<name>.py` 定义）。
3. 鉴权用 `Depends(get_current_user)`。

### 我要加一张表
1. 在 `app/models/<name>.py` 写 `class Xxx(Base): __tablename__ = "xxx"; ...`。
2. 在 `app/models/__init__.py` import 它。
3. 重启应用，`init_db` 自动建表。

---

## 6. 容易踩的坑（必读）

1. **日记加密密钥**：密钥在 `get_current_user` 时派生，存在 request 上下文里。**不要**把密钥写进 session cookie（泄露风险）。
2. **能量单日上限**：所有 +x 操作都要检查当日累计，防刷。
3. **陌生人拾取**：返回的 `Diary` 内容**临时解密**后立即返回，绝不落库。拾取记录只记 `from_user_id`（登录用户），不记 `to_user_id`（因为日记所有者要看到「收到 1 个陌生人的拥抱」是匿名的）。
4. **心情打卡覆盖**：当天重复打卡 → UPDATE 旧记录，不要 INSERT 新行。
5. **静态文件路径**：所有 `url_for('static', ...)` 都用 `/static/...` 路径，FastAPI 自动挂载。
6. **不要引入 SQLAlchemy 之外的重 ORM**：项目刻意保持轻量。
7. **能量累加一定要用 `query.update()`**：不要直接 `user.total_energy += amount` 这种对象属性赋值。FastAPI 一次请求一个 session，但 `User` 对象可能在依赖链里被多次 `db.get()` 加载，对跨 session 的对象赋值不会写回 DB（`EnergyRecord` 能写成功但 `User.total_energy` 一直是 0）。**一律走 `db.query(User).filter(User.id == uid).update({User.total_energy: User.total_energy ± amount})` 显式 UPDATE。**

---

## 7. 验证清单（修改后必跑）

```bash
# 1. 启动
python start.py restart
# 等 2 秒
python start.py status
# 应输出：状态：运行中（PID xxxx）

# 2. 端到端冒烟（无需登录）
curl -I http://127.0.0.1:5000/                    # 200
curl -I http://127.0.0.1:5000/api/music           # 200 (16 首古琴曲)
curl -I http://127.0.0.1:5000/api/garden/shop     # 200 (11 件商品)
curl -I http://127.0.0.1:5000/static/css/style.css   # 200
curl -I http://127.0.0.1:5000/static/audio/gong.mp3  # 200
curl -I http://127.0.0.1:5000/docs                # 200 (FastAPI 自动)

# 3. 需要登录的页面（未登录时 302 → /login）
curl -I http://127.0.0.1:5000/diary               # 302
curl -I http://127.0.0.1:5000/mood-calendar       # 302
curl -I http://127.0.0.1:5000/mood                # 302（旧链接兼容，重定向到 /mood-calendar）

# 4. 公开音乐页
curl -I http://127.0.0.1:5000/music/gong          # 200

# 5. 注册一个测试用户
curl -X POST http://127.0.0.1:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"nickname":"test","password":"hello123"}'
# 应返回 201 + {"id":..., "nickname":"test"}

# 6. 看日志
type logs\healing.log              # Windows
# 或
tail -n 50 logs/healing.log        # Linux/macOS
```

---

## 8. 关键文件速查表

| 想找的东西 | 在哪个文件 |
|---|---|
| 服务管理 | [start.py](file:///c:/Users/Administrator/Desktop/webwrold/start.py) |
| 应用入口 | [app/main.py](file:///c:/Users/Administrator/Desktop/webwrold/app/main.py) |
| 配置 | [app/config.py](file:///c:/Users/Administrator/Desktop/webwrold/app/config.py) |
| DB 引擎 | [app/database.py](file:///c:/Users/Administrator/Desktop/webwrold/app/database.py) |
| 用户依赖 / 鉴权 | [app/deps.py](file:///c:/Users/Administrator/Desktop/webwrold/app/deps.py) |
| 会话签名 | [app/security.py](file:///c:/Users/Administrator/Desktop/webwrold/app/security.py) |
| 加密工具 | [app/utils/crypto.py](file:///c:/Users/Administrator/Desktop/webwrold/app/utils/crypto.py) |
| 能量规则 | [app/services/energy_service.py](file:///c:/Users/Administrator/Desktop/webwrold/app/services/energy_service.py) |
| 5 音 / 心情 / 能量枚举 | [app/utils/constants.py](file:///c:/Users/Administrator/Desktop/webwrold/app/utils/constants.py) |
| 种子数据 | [app/seed.py](file:///c:/Users/Administrator/Desktop/webwrold/app/seed.py) |
| 基础模板 | [templates/base.html](file:///c:/Users/Administrator/Desktop/webwrold/templates/base.html) |
| 导航宏 | [templates/_nav.html](file:///c:/Users/Administrator/Desktop/webwrold/templates/_nav.html) |
| CSS 变量 | [static/css/00-variables.css](file:///c:/Users/Administrator/Desktop/webwrold/static/css/00-variables.css) |
| 全局 JS | [static/js/app.js](file:///c:/Users/Administrator/Desktop/webwrold/static/js/app.js) |
| AI 服务层 | [app/services/ai_service.py](file:///c:/Users/Administrator/Desktop/webwrold/app/services/ai_service.py) |
| AI API 端点 | [app/routers/ai.py](file:///c:/Users/Administrator/Desktop/webwrold/app/routers/ai.py) |
| AI Schema | [app/schemas/ai.py](file:///c:/Users/Administrator/Desktop/webwrold/app/schemas/ai.py) |
| AI 树洞对话页 | [templates/ai_chat.html](file:///c:/Users/Administrator/Desktop/webwrold/templates/ai_chat.html) |
| **前端 Vue SPA 入口** | [frontend/src/main.js](file:///c:/Users/Administrator/Desktop/webwrold/frontend/src/main.js) |
| **前端路由表** | [frontend/src/router/index.js](file:///c:/Users/Administrator/Desktop/webwrold/frontend/src/router/index.js) |
| **前端 API 客户端** | [frontend/src/api/index.js](file:///c:/Users/Administrator/Desktop/webwrold/frontend/src/api/index.js) |
| **前端 user store** | [frontend/src/stores/user.js](file:///c:/Users/Administrator/Desktop/webwrold/frontend/src/stores/user.js) |
| **前端 Vite 配置** | [frontend/vite.config.js](file:///c:/Users/Administrator/Desktop/webwrold/frontend/vite.config.js) |
| **前端 Tailwind 配置** | [frontend/tailwind.config.js](file:///c:/Users/Administrator/Desktop/webwrold/frontend/tailwind.config.js) |
| API 文档（自动） | http://127.0.0.1:5000/docs |
| **AI 交接** | [HANDOFF.md](file:///c:/Users/Administrator/Desktop/webwrold/HANDOFF.md) |
| 详细文档 | [docs/](file:///c:/Users/Administrator/Desktop/webwrold/docs/) |

---

## 9. 文档自洽性（自动同步铁律）

> 🔒 **本节是项目最高优先级的一条规则。** 改代码不改文档 = 改了一半。
> 完整版见 [HANDOFF §12](file:///c:/Users/Administrator/Desktop/webwrold/HANDOFF.md) / [docs/PROJECT_STATE.md §8](file:///c:/Users/Administrator/Desktop/webwrold/docs/PROJECT_STATE.md) / [docs/DEVELOPMENT.md §1.8](file:///c:/Users/Administrator/Desktop/webwrold/docs/DEVELOPMENT.md)。

### 9.1 一句话铁律

**改代码 + 改文档 = 同一个 commit。** 不允许「代码先上，文档之后补」。

### 9.2 同步表（简化版，完整版见 [PROJECT_STATE §8.2](file:///c:/Users/Administrator/Desktop/webwrold/docs/PROJECT_STATE.md)）

| 改了 | 同步更新 |
|---|---|
| 新增页面 / 新文件 | §2 目录树 + §8 速查表 |
| 新增模型 | §4 表速查 + [docs/ARCHITECTURE.md](file:///c:/Users/Administrator/Desktop/webwrold/docs/ARCHITECTURE.md) §4 |
| 新增能量规则 | §3.4 同步 |
| **Pydantic schema 字段** | 对应 `*Out` schema + [HANDOFF §6.11](file:///c:/Users/Administrator/Desktop/webwrold/HANDOFF.md) |
| 端口/启动方式变动 | §1 + [.env.example](file:///c:/Users/Administrator/Desktop/webwrold/.env.example) + [docs/DEPLOYMENT.md](file:///c:/Users/Administrator/Desktop/webwrold/docs/DEPLOYMENT.md) |
| 新增后台功能 | [HANDOFF §5.6](file:///c:/Users/Administrator/Desktop/webwrold/HANDOFF.md) + [docs/ARCHITECTURE.md §6.5](file:///c:/Users/Administrator/Desktop/webwrold/docs/ARCHITECTURE.md) + [docs/PROJECT_STATE.md §5.3](file:///c:/Users/Administrator/Desktop/webwrold/docs/PROJECT_STATE.md) |
| **前端 Vue 视图 / 路由 / store 改动** | §2 目录树 frontend/ 子树 + §3.5 前端架构 + [docs/ARCHITECTURE.md](file:///c:/Users/Administrator/Desktop/webwrold/docs/ARCHITECTURE.md)「前端架构」 + [docs/DEVELOPMENT.md](file:///c:/Users/Administrator/Desktop/webwrold/docs/DEVELOPMENT.md)「前端开发」 |
| **Vite / Tailwind / 依赖改动** | §1.3 + [frontend/package.json](file:///c:/Users/Administrator/Desktop/webwrold/frontend/package.json) + [HANDOFF §2](file:///c:/Users/Administrator/Desktop/webwrold/HANDOFF.md) + [docs/DEPLOYMENT.md](file:///c:/Users/Administrator/Desktop/webwrold/docs/DEPLOYMENT.md)「前端构建」 |
| **6 份文档同步**（Iron Rule） | 本次 Vue 3 重构涉及 README / HANDOFF / PROJECT_STATE / ARCHITECTURE / DEPLOYMENT / DEVELOPMENT 6 份文档，必须同一 commit 一起更新 |

### 9.3 提交前自检 5 件事

- [ ] 改的 Pydantic 字段在 `*Out` schema 里**也都声明了**（→ 防止静默过滤 Bug）
- [ ] 改的 model 字段在 `_migrate_legacy_columns()` 里**也加了**（→ 防止老库丢列）
- [ ] 改的常量在 §3.4 表格里**也更新了**（→ 业务规则可见性）
- [ ] 改的 .env 配置在 [.env.example](file:///c:/Users/Administrator/Desktop/webwrold/.env.example) 里**也加了**（→ 部署可见性）
- [ ] 新增页面 / API 在 §2 / §3 / §8 速查表里**也加了**（→ 可发现性）

如果发现这份文档和实际代码矛盾：**以代码为准，然后更新这份文档**。

---

## 10. License

MIT — 治愈系开源。
