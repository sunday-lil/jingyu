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

**FastAPI + SQLite + Jinja2 + 原生 JS** 的中文治愈系 Web 应用。完整 4 阶段功能：古琴五音疗愈、漂流瓶日记、心情手帐、精神花园。约 2 000 行 Python + 1 500 行 CSS + 600 行 JS。无商业元素、无广告、无内购。

**强隐私承诺**：用户日记内容使用对称加密存储，密钥与用户密码派生。即便数据库泄露也无法直接读取明文（端到端加密）。

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
│   │   └── energy.py
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── pages.py              # SSR 页面路由（返回 HTML）
│   │   ├── auth.py               # /api/auth/*
│   │   ├── music.py              # /api/music/*
│   │   ├── diary.py              # /api/diary/*
│   │   ├── mood.py               # /api/mood/*
│   │   ├── energy.py             # /api/energy/*
│   │   └── garden.py             # /api/garden/*
│   ├── services/
│   │   ├── __init__.py
│   │   ├── energy_service.py     # 能量获取规则（听歌 90%+ / 日记 / 打卡 / 连胜）
│   │   ├── diary_service.py      # 漂流瓶随机拾取
│   │   └── mood_service.py       # 心情日历统计 + 趋势数据
│   └── utils/
│       ├── __init__.py
│       ├── constants.py          # 5 音定义 / 心情枚举 / 能量来源枚举
│       └── crypto.py             # bcrypt + Fernet + PBKDF2
│
├── templates/                    # Jinja2 SSR 模板
│   ├── base.html                 #   全局骨架（导航 + Toast + 页脚）
│   ├── _nav.html                 #   导航宏
│   ├── _toast.html               #   全局 Toast 提示
│   ├── index.html                #   首页（5 音入口 + 漂流瓶入口 + 今日手帐）
│   ├── login.html / register.html
│   ├── music_list.html           #   单音曲目列表 + 沉浸式播放器
│   ├── diary_write.html          #   漂流瓶写作页（含投瓶动效）
│   ├── my_bottles.html           #   我的瓶子时间线
│   ├── diary_detail.html         #   单个瓶子详情
│   ├── pick_bottle.html          #   拾取陌生人漂流瓶
│   ├── mood_checkin.html         #   今日心情手帐
│   ├── mood_calendar.html        #   情绪日历 + 30 天趋势图
│   ├── garden.html               #   精神花园（已种植物 + 装扮）
│   └── shop.html                 #   兑换商店（花种 / 装扮 / 徽章）
│
├── static/
│   ├── css/
│   │   ├── style.css             #   入口（@import 7 个模块）
│   │   ├── 00-variables.css      #   CSS 变量（治愈系配色 + 字体）
│   │   ├── 01-reset.css          #   重置 + body 渐变背景
│   │   ├── 02-layout.css         #   .container / .nav / .grid
│   │   ├── 03-components.css     #   .btn / .card / .toast / .form
│   │   ├── 04-pages.css          #   首页 / 列表页 / 详情页
│   │   ├── 05-animations.css     #   漂流瓶动效 / 心情弹跳 / 花朵生长
│   │   └── 06-music.css          #   沉浸式播放器
│   ├── js/
│   │   ├── app.js                #   window.QI 全局（fetch / toast / confirmThen）
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

`FastAPI()` 实例 → 挂载静态文件 → 注册 5 个 API router + 1 个 page router → 注册 `startup` 事件初始化数据库 + 种子数据。

所有页面通过 SSR（Jinja2）返回 HTML；交互通过 `fetch('/api/...')` 调用后端 API，JS 更新 DOM。

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

### 3.5 模板与前端

- **所有页面** 顶行 `{% extends "base.html" %}`，然后 `{% block content %}...{% endblock %}`。
- **导航**：统一用 `_nav.html` 的 `render_nav(current_user)` 宏。传 `current_user`（dict-like 或 ORM 对象）。
- **Toast**：基模板已经 `{% include "_toast.html" %}`，JS 里直接 `QI.toast('已收好', 'success')`。
- **动效**：漂流瓶投掷用 `static/css/05-animations.css` 的 `@keyframes bottle-throw`，触发后 1.8s 完成。

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
curl -I http://127.0.0.1:5000/mood                # 302

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
