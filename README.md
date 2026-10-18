# 静屿 — 治愈系身心疗愈平台

> **潮声不止，心安自屿。**
> 非商业 · 纯治愈 · 强隐私边界 · 轻运营

[![GitHub](https://img.shields.io/badge/GitHub-sunday--lil%2Fjingyu-181717?logo=github)](https://github.com/sunday-lil/jingyu)
[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)](https://www.python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Status](https://img.shields.io/badge/status-v2.6.1-success)]()

**English** — Jingyu (静屿, "Quiet Isle") is a non-commercial healing web app: guqin five-tone music, a body-mind therapy recommender (Baduanjin / sachet / bracelet / food), drifting diary bottles, a private island corner, a Russell-circumplex mood calendar, and a garden that grows with your daily check-ins. Built with FastAPI + Vue 3 + Three.js. Self-host in two commands.

**每一种情绪，都值得温柔安放。** 静屿是一座只属于你的心灵港湾：古琴五音疗愈、身心调理、日记海岸、静屿角落、情绪日历，还有一座随你心情慢慢生长的花田。无广告、无内购、无算法推荐。

> ⚠️ **隐私说明（重要）**：日记自 v2.3 起为**明文存储**（`diaries.content`），后台 API 不返回正文，但数据库本身没有加密。旧版 README 的「端到端加密」描述已过时；如你需要强隐私，请先阅读 [ARCHITECTURE §7.3](docs/ARCHITECTURE.md)。

## 你可能需要它的 3 个瞬间

- 🌙 **深夜睡不着** —— 打开「琴音疗心」，听一曲《流水》，让古琴的余音把呼吸带慢
- 🍾 **有句话不想告诉任何人** —— 写进日记海岸，让它漂向远方；或者收进静屿角落，只留给自己
- 📅 **说不清这个月过得怎么样** —— 情绪日历把你每天随手一记的心情，画成一张看得懂的图

## 一览

| 首页 · 潮声不止，心安自屿 | 琴音疗心 · 古琴五音 |
|:---:|:---:|
| ![home](https://raw.githubusercontent.com/sunday-lil/jingyu/main/static/img/promo/jingyu_01_home.png) | ![music](https://raw.githubusercontent.com/sunday-lil/jingyu/main/static/img/promo/jingyu_02_music.png) |

| 日记海岸 · 漂流瓶 | 情绪日历 · 罗素情绪环 |
|:---:|:---:|
| ![diary](https://raw.githubusercontent.com/sunday-lil/jingyu/main/static/img/promo/jingyu_03_diary.png) | ![calendar](https://raw.githubusercontent.com/sunday-lil/jingyu/main/static/img/promo/jingyu_04_calendar.png) |

| 静屿角落 · 私密碎碎念 | 屿上花田 · 情绪养成 |
|:---:|:---:|
| ![corner](https://raw.githubusercontent.com/sunday-lil/jingyu/main/static/img/promo/jingyu_03_diary.png) | ![garden](https://raw.githubusercontent.com/sunday-lil/jingyu/main/static/img/promo/jingyu_06_garden.png) |

## 跑起来

```bash
git clone https://github.com/sunday-lil/jingyu.git
cd jingyu
pip install -r requirements.txt
python start.py    # 浏览器打开 http://127.0.0.1:5000
```

首次启动会自动安装前端依赖并构建（需 Python 3.11+ 与 Node.js 18+，首次约几分钟），之后秒开；数据库与种子数据全自动，无需任何配置。

---

# 以下为开发者参考，普通用户可跳过

> 🤖 **接手项目先读**：[AGENTS.md](AGENTS.md)（工作规则）→ [docs/HANDOFF.md](docs/HANDOFF.md)（交接）→ [docs/README.md](docs/README.md)（文档地图）。
> 📜 **版本更新历史**：[docs/CHANGELOG.md](docs/CHANGELOG.md)（v2.2.2 → v2.6.1）。

## 0. 一句话速览

**FastAPI（纯 API 后端）+ Vue 3 SPA + SQLite** 的中文治愈系 Web 应用。六大模块：琴音疗心（含身心调理）、日记海岸、静屿角落、情绪日历、落叶花坊、屿上花田，另有个人主页 / 通知中心 / 秘密后台。前端 Vue 3 `<script setup>` + Vite 5 + Vue Router 4 + Pinia + Tailwind CSS + GSAP + @vueuse/motion + Three.js + axios；后端约 3 000 行 Python。无商业元素、无广告、无内购。

**当前规模**：22 首曲目（16 首真实 + 6 首静音占位）、28 件商店物品、12 张表、16 条业务路由 + 404、17 个 Vue 视图。

**AI（可选）**：NVIDIA NIM API（OpenAI 兼容），当前模型 `z-ai/glm-5.3-flash`，3 个场景——漂流瓶鼓励语、情绪日历治愈语、音乐推荐。未配置 `QI_NVIDIA_API_KEY` 时这些端点返回 200 + `available:false` + 友好提示，业务不中断。AI 输出不写数据库。

---

## 1. 开发模式速查

> 日常使用只需上文「跑起来」的 4 行命令；以下命令用于本地开发、调试与服务器部署。完整部署见 [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)。

### 1.1 服务管理（[start.py](start.py)）

```bash
python start.py start      # 后台启动（默认 = 生产模式，FastAPI :5000 单进程）
python start.py --dev      # 开发模式：Vite :5000（HMR）+ FastAPI :5001 一起起
python start.py --prod     # 显式生产模式（默认即生产，兼容别名）
python start.py stop       # 停止（同时停 FastAPI + Vite）
python start.py restart    # 重启
python start.py status     # 查看 PID + 端口（FastAPI / Vite 两个进程状态）
python start.py fg         # 前台运行（systemd / 调试用；可加 --dev）
python start.py build      # 构建前端到 static/dist/（自动 npm install + npm run build）
python start.py --init-db  # 启动前重置数据库
```

PID 写入 `run/healing.pid`（FastAPI）+ `run/vite.pid`（Vite），日志写入 `logs/healing.log` + `logs/vite.log`。

### 1.2 备选：直接 uvicorn

```bash
python -m uvicorn app.main:app --reload --port 5000
```

启动入口是 [app/main.py](app/main.py)。`--reload` 适合本地改代码热重启，**不要**在生产用。

### 1.3 前端开发模式（Vue 3 + Vite 热更新）

前端源码在 [`frontend/`](frontend/)，开发时用 Vite dev server 跑 SPA，热更新。

```bash
python start.py --dev    # Vite :5000（用户入口）+ FastAPI :5001（API）
                         # frontend/node_modules 不存在时自动 npm install（首次约 7 分钟）
# 浏览器打开 http://127.0.0.1:5000
```

**手动分两个终端**（调试时方便看各自日志）：

```bash
# 终端 1：FastAPI（开发模式手动设置 QI_PORT=5001）
$env:QI_PORT="5001"; python start.py fg --dev   # Windows PowerShell
# 或：QI_PORT=5001 python start.py fg --dev      # Linux/macOS

# 终端 2：Vite dev server
cd frontend
npm install
npm run dev     # Vite :5000
```

**dev proxy**：[frontend/vite.config.js](frontend/vite.config.js) 把 `/api` / `/static` / `/admin` / `/docs` / `/openapi.json` 反代到 FastAPI `:5001`。Vite host 显式设为 `127.0.0.1`（默认 IPv6 `[::1]` 会导致 127.0.0.1 连不上，详见 [HANDOFF §6.12](docs/HANDOFF.md)）。

> 📌 **为什么 Vite 占 :5000 而不是 :5173**：FastAPI 反代 Vite 内部路径（如 `/@id/__x00__plugin-vue:export-helper` 含 null 转义 + 冒号）会被 httpx 破坏，浏览器报 `SyntaxError`。改成 Vite 直接占 :5000 后无转发问题。详见 [HANDOFF §6.16](docs/HANDOFF.md)。

**生产模式**：先 `python start.py build`（或 `cd frontend && npm run build`）输出到 `static/dist/`，再 `python start.py` 走 FastAPI :5000 单进程 SPA fallback。

---

## 2. 完整目录树

```
webwrold/
├── start.py                      # 一键启动（start/stop/restart/status/fg/build）
├── README.md                     # 本文件（产品 + 开发者速查）
├── AGENTS.md                     # AI/自动化开发者工作规则
├── app/
│   ├── main.py                   # FastAPI 入口 + 路由注册 + SPA fallback
│   ├── config.py                 # 配置（QI_* 环境变量 + 默认值）
│   ├── database.py               # SQLAlchemy 引擎 + Session + 轻量迁移
│   ├── deps.py                   # current_user / current_admin / db
│   ├── security.py               # 会话签名 + cookie
│   ├── seed.py                   # 曲目/商店/管理员种子 + 时长校准
│   ├── models/                   # 12 张表（user/diary/mood/music/energy/garden/therapy/...）
│   ├── schemas/                  # Pydantic v2 入参/出参
│   ├── routers/                  # auth/music/diary/mood/energy/garden/ai/therapy/profile/notification/admin
│   ├── services/                 # energy/diary/mood/flower/therapy/ai
│   └── utils/                    # constants.py / crypto.py
├── frontend/                     # Vue 3 SPA 源码
│   ├── package.json / vite.config.js / tailwind.config.js
│   └── src/
│       ├── main.js / App.vue / router/ / stores/ / api/
│       ├── data/islandGuide.js
│       ├── components/           # AppLayout + 4 个视觉组件 + SceneHint/SceneControls/EmojiIcon
│       ├── utils/                # visual.js / three-helpers.js
│       └── views/                # 17 个视图（home/auth/music/diary/mood/garden/profile/notification）
├── templates/admin/              # 后台 Jinja2 SSR（仅 /admin/*）
├── static/
│   ├── dist/                     # 前端构建产物（git 忽略）
│   ├── audio/tracks/             # 22 首曲目音频（一曲一文件）
│   ├── images/                   # 五音封面 SVG
│   ├── css/ + js/                # 后台 SSR 样式 / 脚本（前台不再使用）
│   └── uploads/                  # 用户头像上传
├── data/healing.db               # SQLite（git 忽略）
├── run/ + logs/                  # PID / 日志
└── docs/                         # 全部文档（见 docs/README.md）
```

---

## 3. 架构与关键设计

### 3.1 应用入口（[app/main.py](app/main.py)）

`FastAPI()` 实例 → 安全响应头中间件 → 挂载 `/static` → 注册 13 个 router（auth/music/diary/mood/energy/garden/pages/ai/therapy/notification/profile/admin/admin_pages）→ `lifespan` 初始化数据库 + 种子数据 → **SPA fallback**。

- **生产态**（`static/dist/index.html` 存在）：从 `static/dist/` 读取静态文件（`EXT_TO_MIME` 映射 MIME），未命中返回 `index.html` 让 Vue Router 接管。
- **开发态**（dist 未构建）：返回提示页，引导访问 Vite :5000。
- **排除路径**：`/api/`、`/static/`、`/admin`、`/docs`、`/openapi.json`；注意 `/admin` 无尾斜杠会被判 404，入口请用 `/admin/login`。

### 3.2 鉴权与会话

- **密码哈希**：`bcrypt` 直接使用（passlib 与 bcrypt 4.x 不兼容），密码超 72 字节自动截断。
- **会话**：`itsdangerous.URLSafeTimedSerializer` 签名 `qi_session`，HttpOnly + SameSite=Lax，30 天有效；不是 JWT，前端不存 token。
- **登录**：用 `nickname`（不是 username），登录/注册直接返回 user 对象。
- **日记隐私**：v2.3 起 `diaries.content` 为明文；`content_encrypted` / `encryption_salt` 仅兼容老库。后台 API 只返回统计、不返回正文，但数据库无加密。

### 3.3 数据表（12 张）

| 表 | 关键字段 | 说明 |
|---|---|---|
| `users` | id, nickname, password_hash, encryption_salt（遗留）, total_energy（露水）, leaves（落叶）, is_admin, avatar | 用户 |
| `diaries` | id, user_id, content（明文）, content_encrypted（遗留）, mood_type, is_public | 日记 / 漂流瓶 / 静屿角落（is_public=False） |
| `mood_checkins` | id, user_id, check_date, mood_emoji, note | 心情打卡（一天可多条） |
| `musics` | id, title, audio_url, cover_image, yin_type, category, duration, tags | 曲目 |
| `energy_records` | id, user_id, amount, source, note, music_id, created_at | 能量流水 |
| `shop_items` | id, name, item_type, cost, cost_currency, image, description, trigger | 商店物品（28 件） |
| `garden_items` | id, user_id, item_id, obtained_at | 用户持有（装扮/徽章） |
| `user_flowers` | id, user_id, flower_type, stage, watered_count, planted_at, ... | 花朵生命周期 |
| `encouragements` | id, from_user_id, to_user_id, diary_id, content | 匿名鼓励 |
| `notifications` | id, user_id, type, content, related_id, is_read, created_at | 站内通知 |
| `baduanjin_checkins` | id, user_id, check_date, move_key, created_at | 八段锦跟练打卡（每天一次） |
| `therapy_interests` | id, user_id, product_key, product_name, created_at | 好物预约/意向 |

### 3.4 能量与双资源（[app/services/energy_service.py](app/services/energy_service.py)）

- **露水** = `User.total_energy`：向内获得，用于浇花（1 露水/次）和兑换装扮。
- **落叶** = `User.leaves`：花朵枯萎后拾取（+2/朵），用于在落叶花坊兑换花种。

| 行为 | 收益 | 单日上限 |
|---|---|---|
| 听完一曲（进度 ≥ 90%，同曲 24h 去重） | +1 露水 | 20 |
| 写一篇日记 | +2 露水 | 10 |
| 心情打卡（每条） | +1 露水 | 5 |
| 给他人漂流瓶留言鼓励 | +1 露水 | 10 |
| 八段锦跟练打卡 | +1 露水 | 1 |
| 连续 7 天打卡 | +5 露水（绕过上限） | — |
| 解锁徽章 | +7~20 落叶（按 trigger） | — |
| 拾取枯萎花 | +2 落叶 | — |

> 所有资源增减都用 `db.query(User).update(...)` 显式 UPDATE，不要改对象属性。

### 3.5 前端架构（Vue 3 SPA）

- **入口**：[frontend/src/main.js](frontend/src/main.js)；根组件 [App.vue](frontend/src/App.vue) = `AppLayout` + `<router-view>` + transition。
- **路由**：[frontend/src/router/index.js](frontend/src/router/index.js) 16 条业务路由 + 404；`meta.requiresAuth` 守卫。
- **API 客户端**：[frontend/src/api/index.js](frontend/src/api/index.js) axios，`baseURL=/api` + `withCredentials=true` + 401 自动跳登录；**拦截器已解包 `response.data`**，视图里不要再取 `res.data`。
- **状态**：[frontend/src/stores/user.js](frontend/src/stores/user.js) 只缓存 user 对象到 localStorage，不存 token。
- **布局**：[AppLayout.vue](frontend/src/components/AppLayout.vue) 桌面顶部导航 / 平板紧凑 / 移动端 topbar + tabbar + 「更多」抽屉。
- **3D / 视觉**：4 个组件（FlowerField / AmbientBackground / HeroScene / AudioVisualizer）+ 共享 [three-helpers.js](frontend/src/utils/three-helpers.js) PBR 工具集 + [SceneHint](frontend/src/components/SceneHint.vue) / [SceneControls](frontend/src/components/SceneControls.vue)；能力检测与 `smartRAF` 在 [visual.js](frontend/src/utils/visual.js)。
- **跨浏览器 emoji**：[EmojiIcon.vue](frontend/src/components/EmojiIcon.vue) 使用 Iconify + twemoji 离线 SVG；前台新增 emoji 优先用它。
- **样式**：Tailwind + [main.css](frontend/src/assets/styles/main.css) 系统字体栈（零网络请求）；治愈系 token 在 [tailwind.config.js](frontend/tailwind.config.js)。

**后台 = Jinja2 SSR**：`/admin/*` 用 [templates/admin/](templates/admin/) + [static/css/07-admin.css](static/css/07-admin.css) + `static/js/pages/admin_*.js`，与前台 SPA 完全隔离。

### 3.6 五音定义（[app/utils/constants.py](app/utils/constants.py)）

```python
YIN_INFO = {
    "gong":  {"name": "宫", "element": "土", "organ": "脾胃", "tags": ["健脾", "助消化"]},
    "shang": {"name": "商", "element": "金", "organ": "肺大肠", "tags": ["润肺", "舒缓"]},
    "jue":   {"name": "角", "element": "木", "organ": "肝胆", "tags": ["疏肝", "解郁", "抗焦虑"]},
    "zhi":   {"name": "徵", "element": "火", "organ": "心小肠", "tags": ["养心", "安神"]},
    "yu":    {"name": "羽", "element": "水", "organ": "肾膀胱", "tags": ["宁心", "助眠"]},
}
```

心情 `MOOD_INFO` 共 7 种：ecstatic 🤩 / happy 😊 / calm 😌 / tired 😪 / anxious 😰 / angry 😠 / sad 😢。

### 3.7 AI 接入（NVIDIA NIM，可选）

3 个场景全部走 OpenAI 兼容的 `/chat/completions`，当前模型 `z-ai/glm-5.3-flash`。未配置 key 或调用失败时返回 200 + `available:false` + 治愈系提示，前端照常显示，不报错。

| 场景 | 前端入口 | 后端端点 | AI 输出去向 |
|---|---|---|---|
| 漂流瓶 AI 鼓励语 | `/diary/pick` | `POST /api/ai/encouragement` | 现场文案，不写库 |
| 情绪日历 AI 治愈语 | `/calendar` | `POST /api/ai/healing` | 现场文案，不写库 |
| 音乐 AI 心情推荐 | `/music` / 首页 | `POST /api/ai/recommend-music` | 推荐五音之一 + 理由，不写库 |

> AI 树洞对话、会话历史与「树洞倾心」徽章已在 v2.6.0 删除；不私密的碎碎念改存「静屿角落」。

**配置**（[.env.example](.env.example) 末尾，默认注释）：

```env
# AI 接入（可选，不配置时相关端点优雅降级）
# QI_NVIDIA_API_KEY=nvapi-xxxxx
# QI_AI_MODEL=z-ai/glm-5.3-flash
# QI_AI_BASE_URL=https://integrate.api.nvidia.com/v1
```

> `.env` 的 `QI_AI_MODEL` 会覆盖 [app/config.py](app/config.py) 默认值；换模型两处都要改。glm 是 reasoning 模型，`max_tokens` 需 900–1200，否则可能静默返回空 content。

### 3.8 其他模块速查

| 模块 | 路由 | 关键文件 |
|---|---|---|
| 身心调理 | `/music/therapy` | [therapy.py](app/routers/therapy.py) / [therapy_service.py](app/services/therapy_service.py)（含 B 站八段锦跟练视频） |
| 日记海岸 | `/diary`、`/diary/write`、`/diary/pick` | [diary.py](app/routers/diary.py) / [diary_service.py](app/services/diary_service.py) |
| 静屿角落 | `/corner` | [diary.py](app/routers/diary.py) `GET /api/diary/corner` / [CornerView.vue](frontend/src/views/diary/CornerView.vue) |
| 情绪日历 | `/calendar` | [mood.py](app/routers/mood.py) / [mood_service.py](app/services/mood_service.py) |
| 屿上花田 | `/garden` | [garden.py](app/routers/garden.py) / [flower_service.py](app/services/flower_service.py) |
| 落叶花坊 | `/shop` | [garden.py](app/routers/garden.py) / [energy.py](app/routers/energy.py) |
| 个人主页 | `/profile` | [profile.py](app/routers/profile.py) |
| 通知中心 | `/notifications` | [notification.py](app/routers/notification.py) |
| 秘密后台 | `/admin/login` | [admin.py](app/routers/admin.py) / [admin_pages.py](app/routers/admin_pages.py) |

---

## 4. 数据库与迁移

- **SQLite** 单文件 `data/healing.db`，启动时 `init_db()` 自动建表 + `_migrate_legacy_columns()` 补列 / 重建必要表。
- **不使用 Alembic**：加字段 → model 加列 + `_migrate_legacy_columns()` 加 `ALTER TABLE`；改列类型 / 删列需显式重建表。
- **种子幂等**：`seed_music` 按 title、`seed_shop_items` 按 name 补齐；`sync_durations_from_audio` 启动时按真实 MP3 校准 `musics.duration`。
- **好友/通知/花田** 等新表由 `Base.metadata.create_all` 自动建。

---

## 5. 常见改动

详细步骤见 [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md)；这里只给方向。

- **加前台页面**：`frontend/src/views/<module>/XxxView.vue` → [router/index.js](frontend/src/router/index.js) 加路由 → 需要导航时改 [AppLayout.vue](frontend/src/components/AppLayout.vue) / [islandGuide.js](frontend/src/data/islandGuide.js) → `npm run build`。
- **加 API**：`app/routers/<name>.py` 加路由 → schema → service → 更新文档。
- **加表**：`app/models/<name>.py` + `app/models/__init__.py` import → 重启自动建表。
- **加后台页面**：`templates/admin/*.html` + [admin_pages.py](app/routers/admin_pages.py) + `static/js/pages/admin_*.js`。
- **加 AI 场景**：schema → service → router（必须降级）→ Vue 视图集成；详见 [DEVELOPMENT §2.7](docs/DEVELOPMENT.md)。

---

## 6. 容易踩的坑（详情见 HANDOFF §6）

1. **能量累加必须用 `db.query(User).update(...)`**，不要 `user.total_energy += amount`。
2. **`expire_on_commit=False`**：commit 后要返回最新能量，必须重新 `db.query(User.total_energy).scalar()`。
3. **Pydantic Out schema 是超集**：`to_public_dict()` 的字段没在 `*Out` 声明会被静默过滤。
4. **GSAP 入场动画只做位移**，不设 `opacity:0` / `scale:0`；列表动画在 fetch 成功后 + `querySelector` 守卫。
5. **Vite host 写 `127.0.0.1`**；`base` 仅在 build 时设为 `/static/dist/`。
6. **SPA fallback 必须排除 `/api`、`/static`、`/admin`、`/docs`**。
7. **后台路径用 `/admin/login`**：`/admin` 无尾斜杠当前会 404。
8. **AI 模型会下架**：换模型同时改 `.env` 与 `config.py`；reasoning 模型给小 `max_tokens` 会静默空回复。

---

## 7. 验证清单（每次改动后）

```bash
# 1. 启动
python start.py restart
python start.py status                         # 应显示运行中

# 2. 冒烟
curl -I http://127.0.0.1:5000/                 # 200
curl -I http://127.0.0.1:5000/docs             # 200
curl -I http://127.0.0.1:5000/api/music        # 200（22 首）
curl -I http://127.0.0.1:5000/api/garden/shop  # 200（28 件）
curl -I http://127.0.0.1:5000/api/therapy/catalog # 200（八段锦 + 好物目录）
curl -I http://127.0.0.1:5000/api/auth/me      # 401（未登录）
curl -I http://127.0.0.1:5000/admin/login      # 200
curl -I http://127.0.0.1:5000/corner          # 200（SPA fallback）
curl -I http://127.0.0.1:5000/music/therapy   # 200（SPA fallback）

# 3. 前端改动必须重新构建
cd frontend && npm run build

# 4. 看日志
tail -n 50 logs/healing.log
```

**注册测试用户**：

```bash
curl -X POST http://127.0.0.1:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"nickname":"test","password":"hello123"}'
# 应返回 201 + {"id":..., "nickname":"test", ...}
```

更完整的端到端脚本见 [HANDOFF §8](docs/HANDOFF.md)。

---

## 8. 关键文件速查表

| 想找的东西 | 在哪个文件 |
|---|---|
| 服务管理 | [start.py](start.py) |
| 应用入口 | [app/main.py](app/main.py) |
| 配置 | [app/config.py](app/config.py) |
| DB 引擎 / 迁移 | [app/database.py](app/database.py) |
| 鉴权依赖 | [app/deps.py](app/deps.py) |
| 会话签名 | [app/security.py](app/security.py) |
| 能量规则 | [app/services/energy_service.py](app/services/energy_service.py) |
| 身心调理推荐 / 八段锦 / 好物 | [app/services/therapy_service.py](app/services/therapy_service.py) / [app/routers/therapy.py](app/routers/therapy.py) |
| 静屿角落页面 | [frontend/src/views/diary/CornerView.vue](frontend/src/views/diary/CornerView.vue) |
| 身心调理页面 | [frontend/src/views/music/TherapyView.vue](frontend/src/views/music/TherapyView.vue) |
| 花朵生命周期 | [app/services/flower_service.py](app/services/flower_service.py) |
| 5 音 / 心情 / 商店常量 | [app/utils/constants.py](app/utils/constants.py) |
| 种子数据 | [app/seed.py](app/seed.py) |
| AI 服务层 | [app/services/ai_service.py](app/services/ai_service.py) |
| AI API | [app/routers/ai.py](app/routers/ai.py) |
| 后台 API / 页面 | [app/routers/admin.py](app/routers/admin.py) / [app/routers/admin_pages.py](app/routers/admin_pages.py) |
| 前端入口 | [frontend/src/main.js](frontend/src/main.js) |
| 前端路由 | [frontend/src/router/index.js](frontend/src/router/index.js) |
| 前端 API 客户端 | [frontend/src/api/index.js](frontend/src/api/index.js) |
| 前端 user store | [frontend/src/stores/user.js](frontend/src/stores/user.js) |
| Vite / Tailwind | [frontend/vite.config.js](frontend/vite.config.js) / [frontend/tailwind.config.js](frontend/tailwind.config.js) |
| 指南共享文案 | [frontend/src/data/islandGuide.js](frontend/src/data/islandGuide.js) |
| 3D 组件 | [FlowerField](frontend/src/components/FlowerField.vue) / [HeroScene](frontend/src/components/HeroScene.vue) / [AmbientBackground](frontend/src/components/AmbientBackground.vue) / [AudioVisualizer](frontend/src/components/AudioVisualizer.vue) |
| API 文档 | http://127.0.0.1:5000/docs |
| 交接文档 | [docs/HANDOFF.md](docs/HANDOFF.md) |
| 文档地图 | [docs/README.md](docs/README.md) |

---

## 9. 文档与工作规则

> 🔒 **改代码 + 自测 + 改文档 + 推送 = 一次完成。** 详细规则见 [AGENTS.md](AGENTS.md)。

- 默认同步 6 份文档：README / HANDOFF / PROJECT_STATE / ARCHITECTURE / DEPLOYMENT / DEVELOPMENT；触及历史时再改 CHANGELOG。
- 自测标准：后端 `python start.py restart` + 受影响接口 + 日志无 ERROR；前端 `npm run build` + 浏览器验证 + console 无报错。
- 完成后用 `gh` 推送 `origin/main`，并校验远端 SHA 与本地一致。
- 文档与代码矛盾时：**以代码为准，立即修文档**。

---

## 10. License

MIT — 治愈系开源。
