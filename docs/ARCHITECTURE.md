# 架构 — 静屿

> 本文件讲**为什么**这样设计，不是讲**做了什么**。想知道做了什么看 [README.md](../../README.md)。

> 🔒 **改了本文件涉及的代码，必须同步更新 [HANDOFF §12](../../HANDOFF.md) / [PROJECT_STATE §8](../PROJECT_STATE.md) / [DEVELOPMENT §1.8](DEVELOPMENT.md) 列出的对应文档。** 改代码不改文档 = 改了一半。

---

## 1. 总体架构

```
┌──────────────────────────────────────────────────────────────┐
│                       浏览器（前端）                          │
│                                                              │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐  │
│  │ HTML 模板渲染  │  │  CSS 模块化样式 │  │ 原生 JS 交互   │  │
│  │ (Jinja2 SSR)  │  │ (8 个 .css)   │  │ (一页一个 .js) │  │
│  └────────────────┘  └────────────────┘  └────────────────┘  │
│         ↑                  ↓                  ↓              │
│         │           显示页面骨架         fetch /api/...     │
│         │                                     ↓              │
└─────────┼─────────────────────────────────────┼──────────────┘
          │                                     │
          │         HTTP (Jinja2 HTML)          │  HTTP JSON
          │                                     ↓
┌─────────┼─────────────────────────────────────────────────────┐
│         │            FastAPI（uvicorn）                       │
│         │                                                     │
│  ┌──────┴──────┐  ┌──────────────┐  ┌──────────────────────┐ │
│  │  pages.py  │  │  routers/*   │  │  staticfiles mount   │ │
│  │ (返回HTML) │  │  (返回JSON)  │  │  /static/*           │ │
│  │            │  │  + admin     │  │                      │ │
│  │ admin_     │  │  + admin     │  │                      │ │
│  │  pages.py  │  │              │  │                      │ │
│  └──────┬─────┘  └──────┬───────┘  └──────────────────────┘ │
│         │               │                                   │
│         │       ┌───────┴────────┐                          │
│         │       │  services/*    │  ← 业务逻辑层             │
│         │       └────────┬───────┘                          │
│         │                ↓                                   │
│         │       ┌─────────────────┐                          │
│         │       │  models/*      │  ← ORM                   │
│         │       └────────┬────────┘                          │
│         │                ↓                                   │
│         │       ┌─────────────────┐                          │
│         │       │  SQLite        │                          │
│         │       │  data/healing.db│                          │
│         │       └─────────────────┘                          │
│         │                                                     │
│         └─ [admin] → admin_pages.py → templates/admin/*     │
│              → admin.py → /api/admin/* → services/models    │
└──────────────────────────────────────────────────────────────┘
```

**单一进程承担 3 个角色**：API + 页面 + 静态资源。这是有意为之的简化（见 [HANDOFF §2](../../HANDOFF.md)）。

**秘密后台**（[app/routers/admin.py](../../app/routers/admin.py) + [app/routers/admin_pages.py](../../app/routers/admin_pages.py)）挂在 `QI_ADMIN_PATH_PREFIX`（默认 `/admin`）下，**完全独立于前台**：不共享 base.html，不共享 nav，不放任何前台链接（见 [§6.5](#65-秘密后台架构)）。

---

## 2. 分层约定

```
routers/  →  services/  →  models/  →  database
   (HTTP)     (业务)        (ORM)       (SQL)
```

**严格单向依赖**：
- `routers/` 可以 import `services/` 和 `models/`
- `services/` 只能 import `models/`，**不** import `routers/`
- `models/` 只能 import SQLAlchemy 基础类，**不** import 上层
- `utils/` 是无状态的纯函数 / 常量，谁都能 import

**为什么这么分**：
- router 只做「接参 + 调 service + 返响应」，业务规则集中在 service
- 换 ORM / DB 时只改 `models/`
- 加新功能时只改 `services/`，不动 router

---

## 3. 鉴权流（端到端）

```
浏览器                          FastAPI
  │                                │
  │ POST /api/auth/login           │
  │ {nickname, password}           │
  ├───────────────────────────────→│
  │                                │ 1. bcrypt.verify(password, user.password_hash)
  │                                │ 2. 用 user.encryption_salt + password 派生 Fernet 密钥
  │                                │ 3. 存密钥到 request.state.diary_key (内存)
  │                                │ 4. 签 qi_session cookie
  │ ←─ 200 + Set-Cookie            │
  │                                │
  │ GET /api/diary                 │
  │ Cookie: qi_session=...         │
  ├───────────────────────────────→│
  │                                │ 1. 验签 cookie → user
  │                                │ 2. 重建 diary_key（user.encryption_salt + password）
  │                                │    ⚠️ 但 password 哪来？→ 存 request.state
  │                                │ 3. 查 diaries 表 → 解密 → 返回
  │ ←─ 200 [{id, content, ...}]    │
```

**关键点**：
1. 密码只在登录那一刻被服务端拿到，之后只通过 cookie 间接传递用户身份
2. 浏览器端还要**自己**用同一密码 + salt 派生 Fernet 密钥，**前端**做写日记的加密
3. 服务端的 `request.state.diary_key` 只能用于**读**已存在的密文（写日记是客户端加密的）

**详细字段定义**：看 [app/utils/crypto.py](../../app/utils/crypto.py) 和 [app/deps.py](../../app/deps.py)。

---

## 4. 数据库架构

### 4.1 实体关系

```
                 ┌──────────┐
                 │  users   │
                 └────┬─────┘
                      │ 1:N
        ┌─────────────┼──────────────┬───────────────┐
        ↓             ↓              ↓               ↓
  ┌──────────┐  ┌──────────┐  ┌──────────────┐  ┌──────────┐
  │ diaries  │  │ mood_    │  │ energy_      │  │ garden_  │
  │          │  │ checkins │  │ records      │  │ items    │
  └──────────┘  └──────────┘  └──────────────┘  └──────────┘
       ↑
       │ N:M
       │
  ┌──────────────────┐         ┌──────────────┐
  │ encouragements   │ ──────→ │ diaries      │
  │ (匿名鼓励)        │         │ (被鼓励的)    │
  └──────────────────┘         └──────────────┘
```

### 4.2 关键表字段

| 表 | 关键字段 | 业务含义 |
|---|---|---|
| `users.encryption_salt` | bytes (16) | 客户端加密日记的盐，**注册时**生成，**永不**改 |
| `users.total_energy` | int | 当前总能量（用 `db.query().update()` 更新，**不要**对象属性赋值） |
| `users.is_admin` | bool | 是否后台管理员（**默认 False**；首管由 `app/seed.py` 自动创建） |
| `diaries.content_encrypted` | str | Fernet 密文，前端传上来直接存 |
| `diaries.is_public` | bool | 是否可被陌生人拾取 |
| `mood_checkins.check_date` | date | 当天日期（unique + user_id） |
| `energy_records.source` | enum | `listen_music` / `write_diary` / `checkin` / `streak_7` / `exchange` / **`admin_adjust`** |
| `garden_items.item_id` | int | FK → `shop_items.id` |
| `encouragements.from_user_id` | int | 拾取者，**不**记录被鼓励者的 ID（保护匿名） |

### 4.3 单日能量上限

在 [app/utils/constants.py](../../app/utils/constants.py) 里硬编码：
```python
DAILY_LIMITS = {
    "listen_music": 20,   # 露水
    "write_diary": 10,    # 阳光
    "checkin": 5,         # 养分
}
```

`energy_service.grant_energy()` 每次 grant 前查当天累计，超限返 False。

---

## 5. 前端架构

### 5.1 模板继承

```
base.html                    ← 全局前台骨架（head + nav + Toast + main block）
  ├── index.html             ← 首页
  ├── login.html
  ├── register.html
  ├── music_list.html
  ├── diary_write.html
  ├── my_bottles.html
  ├── diary_detail.html
  ├── pick_bottle.html
  ├── mood_checkin.html
  ├── mood_calendar.html
  ├── garden.html
  └── shop.html

admin/_base.html             ← 后台骨架（暗色侧栏 + 金边 logo，独立 base）
  ├── login.html             ← 单独登录页（与前台登录页分离）
  ├── dashboard.html         ← 6 统计卡 + 最近 8 条活动
  ├── users.html             ← 用户列表（搜索/分页/重置密码/代建）
  ├── user_detail.html       ← 用户详情（统计/能量调整/最近活动）
  ├── logs.html              ← tail logs/healing.log
  └── system.html            ← 系统信息 + 一键清 pycache
```

每个前台页面 3 步：
1. `{% extends "base.html" %}` 继承骨架
2. `{% block content %}` 写主内容
3. 底部 `<script defer src="/static/js/pages/xxx.js"></script>` 加载专属 JS

每个后台页面 3 步：
1. `{% extends "admin/_base.html" %}` 继承后台骨架
2. `{% block content %}` 写主内容
3. 底部 `<script defer src="/static/js/pages/admin_xxx.js"></script>` 加载专属 JS

### 5.2 CSS 模块化

```
style.css                 ← 前台入口
  @import 00-variables.css  ← 颜色 / 字体 / 间距 变量
  @import 01-reset.css      ← 重置 + body 渐变背景
  @import 02-layout.css     ← 容器 / 导航 / 网格
  @import 03-components.css ← 按钮 / 卡片 / Toast / 表单
  @import 04-pages.css      ← 页面专属样式
  @import 05-animations.css ← 动效（漂流瓶 / 心情弹跳 / 花朵生长）
  @import 06-music.css      ← 沉浸式播放器
  @import 07-admin.css      ← 【后台专属】暗色侧栏 / 表格 / 模态
```

**为什么分 8 个**：
- 每个文件 < 300 行
- 改颜色只动 `00-variables.css`，全局生效
- 改动效只动 `05-animations.css`
- 浏览器只缓存变化的文件
- **07-admin.css 独立** —— 后台样式变了不影响前台；不加载 `style.css` 不会拖累后台首屏

### 5.3 JS 模式

`window.QI` 全局（[static/js/app.js](../../static/js/app.js)）暴露：
- `QI.toast(msg, type)` — 治愈系 Toast
- `QI.confirmThen(msg, fn)` — 二次确认（柔和版）
- `QI.fetch(url, opts)` — fetch 包装，自动带 cookie

页面 JS（[static/js/pages/](../../static/js/pages/)）只做：
1. 监听 DOM 事件
2. 调 `QI.fetch('/api/...')`
3. 更新 DOM

**不**引入任何框架（React/Vue/Tailwind），**不**打包，**不**用 npm。

---

## 6. 部署架构（生产）

```
[ 用户浏览器 ]
       │ HTTPS
       ↓
[ Nginx（80/443）]
       │ 反向代理
       ↓
[ uvicorn (127.0.0.1:5000) ]   ← python start.py
       │
       ↓
[ SQLite (data/healing.db) ]    ← 单文件，可备份可迁移
```

**为什么需要 Nginx**：
- HTTPS 终止（uvicorn 也能加，但 Nginx 更专业）
- 静态资源缓存（Gzip + Cache-Control）
- 限流 / 防 CC 攻击
- 多 worker 负载均衡（将来）

详细配置看 [docs/DEPLOYMENT.md](DEPLOYMENT.md)。

---

## 6.5 秘密后台架构

> 设计原则：**「管理用户」而不「窥视用户」** —— 日记是端到端加密的，管理员**永远**拿不到明文。

### 6.5.1 模块组成

| 层 | 文件 | 说明 |
|---|---|---|
| API | [app/routers/admin.py](../../app/routers/admin.py) | 全部 `/api/admin/*` JSON 端点 |
| 页面 | [app/routers/admin_pages.py](../../app/routers/admin_pages.py) | 全部 `/admin/*` SSR 页面 |
| Schema | [app/schemas/admin.py](../../app/schemas/admin.py) | Pydantic 入参/出参 |
| 鉴权 | [app/deps.py](../../app/deps.py) `get_current_admin` / `get_current_admin_or_redirect` | 未登录 → 401 / 302；非 admin → 403 |
| 配置 | [app/config.py](../../app/config.py) | `QI_ADMIN_USERNAME/PASSWORD/PATH_PREFIX` |
| 种子 | [app/seed.py](../../app/seed.py) | 首次启动自动创建首管，密码随机 → `logs/healing.log` |
| 模板 | `templates/admin/` | 7 个 .html（_base + 6 页面） |
| 样式 | [static/css/07-admin.css](../../static/css/07-admin.css) | 暗色侧栏 + 表格 + 模态（与前台完全隔离） |
| 脚本 | `static/js/pages/admin_*.js` | 6 个页面 JS |

### 6.5.2 6 个页面

| URL | 页面 | 功能 |
|---|---|---|
| `/admin/login` | 登录 | 单独设计；非 admin 登录会拒绝 |
| `/admin/` | 概览 | 6 统计卡（用户/管理员/日记/打卡/能量流水/花园）+ 最近 8 条活动 |
| `/admin/users` | 用户列表 | 昵称搜索 / 仅管理员筛选 / 分页 / 重置密码 / 代建用户 |
| `/admin/users/{id}` | 用户详情 | 完整档案 + 统计 + 能量调整 + 重置密码 / 切换 admin / 删除 |
| `/admin/logs` | 日志查看 | tail logs/healing.log，按级别过滤，可 3s 自动刷新 |
| `/admin/system` | 系统维护 | Python 平台 / DB 日志大小 / 一键清 pycache |

### 6.5.3 「秘密」怎么实现

- **URL 前缀可改**：`.env` 设 `QI_ADMIN_PATH_PREFIX=/your-secret-path`（默认 `/admin`）
- **不在前台 nav / footer / 任何角落放链接**（连「联系管理员」也不放）
- **robots meta `noindex,nofollow`**（[templates/admin/_base.html](../../templates/admin/_base.html)）
- 用户必须知道 URL + 管理员账号才能进
- 与前台**完全独立**：
  - 不共享 base.html（后台有独立 `admin/_base.html`）
  - 不共享 nav / Toast
  - 不共享 CSS 入口（[static/css/07-admin.css](../../static/css/07-admin.css) 独立）
  - JS 也独立（`admin_*.js`）

### 6.5.4 「管理」与「窥视」的分界

| 能做 | 不能做 |
|---|---|
| 看昵称 / 能量 / 创建时间 / 日记数量（不读内容） | 读 `content_encrypted` 的明文（端到端保护） |
| 重置用户密码 | 导出全库 |
| 删除账号 | 删自己 / 改自己的 `is_admin`（防手滑） |
| 调整能量（写流水，source=`admin_adjust`） | 绕过 cookie 鉴权（API 全部 `Depends(get_current_admin)`） |
| 看运行日志 | — |
| 一键清 `__pycache__` | — |

### 6.5.5 能量调整的审计可追溯

```python
# app/routers/admin.py
@router.post("/users/{user_id}/adjust-energy")
def adjust_energy(user_id: int, body: AdjustEnergyIn, ...):
    # 1. 调用户能量（用 query().update()，不要 user.total_energy += ...）
    db.query(User).filter(User.id == user_id).update(
        {User.total_energy: User.total_energy + body.amount},
        synchronize_session=False,
    )
    # 2. 写流水（必须！审计可追溯）
    record = EnergyRecord(
        user_id=user_id,
        amount=body.amount,
        source="admin_adjust",       # ← 唯一标识这是管理员调的
        note=body.note or f"admin {admin.id} adjusted",
    )
    db.add(record)
    db.commit()
```

前端弹窗带二次确认，避免误操作。

### 6.5.6 重置密码的边界

- 重置时**改** `password_hash`（新密码）
- 重置时**不改** `encryption_salt`（同一用户的 salt 永远不变）
- 用户用新密码登录后，PBKDF2 派生的 Fernet 密钥会变化
- 旧日记在本机**无法解密**（除非用户记得旧密码）
- 这是端到端加密的固有代价，**不能**绕过

### 6.5.7 一键清 pycache

```python
# app/routers/admin.py
@router.post("/system/clear-pycaches")
def clear_pycaches(...):
    cleared = 0
    for root, dirs, files in os.walk(project_root):
        for d in dirs:
            if d == "__pycache__":
                shutil.rmtree(Path(root) / d, ignore_errors=True)
                cleared += 1
    return {"cleared_dirs": cleared, "cleared_files": ...}
```

只清 `__pycache__`，**不**碰 `data/` / `logs/` / 用户文件。

---

## 7. 安全模型

### 7.1 密码
- bcrypt(rounds=12) + 72 字节截断
- 注册时存 `password_hash`，登录时 verify

### 7.2 会话
- `itsdangerous.URLSafeTimedSerializer` 签名
- HttpOnly + SameSite=Lax
- 30 天有效

### 7.3 日记（端到端）
- 注册时生成 16 字节随机 `encryption_salt`，存 `users` 表
- 客户端 PBKDF2(password + salt, 200 000 轮) 派生 Fernet 密钥
- 写日记：浏览器加密 → 只发密文给服务端
- 读日记：浏览器解密（用户登录后浏览器内存里有密钥）

**安全边界**：
- 服务端**永不**接触明文日记
- 数据库泄露 → 攻击者拿到 `content_encrypted` 也读不了（不知道密码）
- 管理员也无法读取用户明文

### 7.4 CSRF
- 状态修改用 POST/PUT/DELETE（GET 只读）
- SameSite=Lax Cookie 默认防跨站
- 没用 CSRF token（项目无第三方嵌入场景）

### 7.5 SQL 注入
- 一律走 SQLAlchemy ORM，参数化查询
- 不拼接原始 SQL

### 7.6 管理员鉴权
- 普通登录 → `Depends(get_current_user)` → 拿到任意 `User`
- 后台 API → `Depends(get_current_admin)` → 二次校验 `is_admin == True`
- 失败：
  - 未登录 → 401（API）/ 302 → `/admin/login`（页面）
  - 已登录但非 admin → 403（API）/ 跳回首页（页面）
- 防止普通用户通过猜 URL 进入后台
- 重启服务 → `seed.py` 检查 `is_admin` 数量，= 0 时**自动**新建一个（密码随机 → 写日志）

### 7.7 Pydantic schema 字段完整性（防 §6.11 静默过滤）
**铁律**：`User.to_public_dict()` 与所有出参 schema（`AuthOut` / `*Out`）的字段**必须**一致 — schema 是 `to_public_dict()` 字段的**超集**。

**为什么**：
FastAPI 用 `response_model=*Out` 序列化时，**只保留 schema 显式声明的字段**，未声明的被静默丢弃（不报错）。前端拿到的是「少了字段」的 JSON，业务逻辑 `data.xxx` 永远 `undefined`。

**防**：
- 改 `to_public_dict()` 字段 → **同一 commit** 改所有对应 `*Out` schema
- 改完**立即**在浏览器 DevTools Network 标签看 Response body
- 详见 [HANDOFF §6.11](../../HANDOFF.md) / [DEVELOPMENT §3.10](DEVELOPMENT.md)

---

## 8. 性能

### 8.1 首屏 < 3s
- 11 个 HTML 页面共享 base.html，浏览器缓存 CSS/JS
- 静态资源 gzip（生产 Nginx 开）
- 古琴音频用 `preload="metadata"`，不预加载整个文件

### 8.2 数据库
- SQLite 单文件，< 1000 用户完全无压力
- 写日记 / 能量 / 打卡 都是简单 INSERT，索引足够
- 30 天心情趋势查 `mood_checkins` 表，按 `user_id + check_date` 索引

### 8.3 加密
- PBKDF2 200 000 轮 ≈ 200ms/次（用户登录时一次性）
- Fernet AES-128-CBC ≈ 0.1ms/1KB（写日记时无感）

---

## 9. 可扩展性

### 9.1 换 MySQL
只改 `.env`：
```env
QI_DATABASE_URL=mysql+pymysql://user:pw@localhost:3306/healing?charset=utf8mb4
```
业务层不动。

### 9.2 加新模块（如「冥想引导」）
1. `app/models/meditation.py` + `app/models/__init__.py` 加 import
2. `app/schemas/meditation.py` + `app/schemas/__init__.py` 重建
3. `app/routers/meditation.py` + `app/routers/__init__.py` 注册
4. `app/services/meditation_service.py` 业务逻辑
5. `templates/meditation.html` + `static/js/pages/meditation.js`
6. `app/seed.py` 加种子数据
7. 重启 → `init_db()` 自动建表

### 9.3 加一个后台页面 / API
1. 后台 API：[app/routers/admin.py](../../app/routers/admin.py) 加 `@router.get/post/...`，Pydantic in [app/schemas/admin.py](../../app/schemas/admin.py)
2. 后台页面：[app/routers/admin_pages.py](../../app/routers/admin_pages.py) 加 `@router.get(...)` + `admin_templates.TemplateResponse(request, "admin/your.html", {...})`
3. 鉴权统一 `Depends(get_current_admin)`（API）/ `get_current_admin_or_redirect`（页面）
4. 模板放 `templates/admin/your.html`，继承 `admin/_base.html`
5. 表格 / 模态样式直接用 [static/css/07-admin.css](../../static/css/07-admin.css) 的 `.admin-*` 类
6. JS 放 `static/js/pages/admin_xxx.js`，模板底部 `<script defer src="/static/js/pages/admin_xxx.js"></script>`

### 9.4 加一个新字段到旧库（轻量迁移，不引 Alembic）
1. [app/models/xxx.py](../../app/models/) 加 `Mapped[...] = mapped_column(...)`
2. [app/database.py](../../app/database.py) 的 `_migrate_legacy_columns()` 加一段：
   ```python
   cols = {c["name"] for c in insp.get_columns("xxx")}
   if "new_field" not in cols:
       conn.execute(text("ALTER TABLE xxx ADD COLUMN new_field ... DEFAULT ..."))
   ```
3. 重启即可（已存在的老库自动加列）

⚠️ 这套方案只支持**加列 / 加默认值**。改列类型 / 删列 / 加索引还是建议上 Alembic（但项目刻意不引）。

### 9.5 真实音频
1. 把 mp3 放到 `static/audio/<yin>/<曲名>.mp3`
2. 改 `app/seed.py` 里的 `audio_url` 字段
3. `python start.py --init-db` 重置种子

### 9.6 PWA / 离线
- `static/manifest.json` + service worker
- 离线写日记：用浏览器 `crypto.subtle` 加密到 IndexedDB，联网时同步

---

## 10. 不做的事（明确边界）

- ❌ 不做账户系统（密码 / 邮箱 / 实名）
- ❌ 不做支付 / 内购 / 充值 / 商业化
- ❌ 不做关注 / 粉丝 / 社交关系链
- ❌ 不做评论 / 点赞（破坏「安静」氛围）
- ❌ 不做推送通知（避免打扰）
- ❌ 不做用户数据导出（保护隐私）
- ❌ **不做公开的**「管理员入口」链接（秘密后台只在 .env 配 URL，靠记忆进入）

**关于秘密后台的边界**：
- ✅ 允许：重置用户密码 / 调整能量（写流水）/ 删账号 / 看日志 / 清 pycache
- ❌ 禁止：读日记明文（端到端加密保护，管理员也拿不到）

这些边界是项目精神的一部分，不要突破。
