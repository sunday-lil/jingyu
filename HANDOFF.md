# HANDOFF — 静屿项目交接说明

> 写给接手这个项目的下一个 AI（Cursor / Copilot / Devin / 任何 Agent）。
> 读这一份文件 ≈ 读完整套文档。它是项目元信息 + 关键决策 + 踩坑清单的汇总。

---

## 0. 你正在接手什么

**项目名**：静屿（代号，可改）
**类型**：治愈系身心疗愈 Web 应用
**性质**：非商业 / 纯治愈 / 强隐私 / 轻运营
**代码体量**：约 2 500 行 Python + 1 800 行 CSS + 900 行 JS
**当前阶段**：4 个 Phase 全部实现 + 秘密后台 + 端到端通过

---

## 1. 30 秒跑起来

```bash
cd c:\Users\Administrator\Desktop\webwrold
pip install -r requirements.txt
python start.py
# 浏览器自动打开 http://127.0.0.1:5000
```

服务管理：
```bash
python start.py start     # 后台启动（默认）
python start.py stop      # 停止
python start.py restart   # 重启
python start.py status    # 查 PID
python start.py fg        # 前台（systemd / 调试）
python start.py --init-db # 启动前重置数据库
```

**秘密后台**：`http://127.0.0.1:5000/admin`（默认入口）
- 首次启动会自动创建管理员 `admin`，密码**随机生成并写入 `logs/healing.log`**（看 `[ADMIN] password :` 一行）
- 强烈建议在 `.env` 里设置 `QI_ADMIN_USERNAME` + `QI_ADMIN_PASSWORD` 固定一个强密码
- 不在任何前台页面放链接，纯粹靠 URL 入口
- **当前数据库内的真实首管密码**（2026-07-15 测试用）：`GKmZinzvoXQbaK2D`
  > 这是会话中通过直接改 SQLite 写回的固定密码，便于人工测试；生产环境请改 `.env` → `QI_ADMIN_PASSWORD=` 强密码。

**GitHub**：`https://github.com/sunday-lil/jingyu`（public, MIT 友好，私有项目只发了一次）

---

## 2. 技术栈（已定，不要再讨论）

| 层 | 选型 | 备注 |
|---|---|---|
| 后端 | **FastAPI 0.115+** | 路由 + Pydantic + lifespan |
| ORM | **SQLAlchemy 2.0** | `Base` + `Session`，不用 Alembic |
| DB | **SQLite** | 单文件 `data/healing.db`，将来可换 MySQL |
| 模板 | **Jinja2** | SSR，所有页面 `{% extends "base.html" %}` |
| 静态 | **FastAPI StaticFiles** | `/static/*` 一条命令挂载 |
| 前端 | **原生 HTML/CSS/JS** | 无框架、无打包器 |
| 密码哈希 | **bcrypt 4.x**（直接用，不用 passlib） | passlib 与 4.x 不兼容 |
| 日记加密 | **Fernet (AES-128-CBC + HMAC)** | 客户端 PBKDF2 派生密钥 |
| 会话 | **itsdangerous URLSafeTimedSerializer** | 签名 cookie，HttpOnly + SameSite=Lax |
| 启动 | **uvicorn** | `app.main:app` |

**不要做的事**：
- ❌ 引入 React / Vue / Tailwind / Vite —— 项目刻意保持轻量
- ❌ 引入 Alembic —— 改完模型重启即可，`init_db()` 自动建表
- ❌ 把 `passlib` 拉回来 —— 用 `app/utils/crypto.py` 里直接调 bcrypt 的版本

---

## 3. 项目结构

```
webwrold/
├── start.py                  ← 服务管理脚本（start/stop/restart/status/fg）
├── README.md                 ← 用户主文档
├── HANDOFF.md                ← 【当前文件】AI 交接说明
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
│   ├── models/               ← 一张表一个文件
│   │   ├── user.py           ← 含 is_admin 字段
│   │   ├── diary.py
│   │   ├── mood.py
│   │   ├── music.py
│   │   ├── energy.py
│   │   ├── garden.py
│   │   ├── encouragement.py
│   │   └── __init__.py       ← 统一 import（init_db 依赖这里）
│   │
│   ├── schemas/              ← Pydantic v2 入参/出参
│   │   ├── auth.py / diary.py / mood.py / music.py / energy.py
│   │   ├── admin.py          ← 后台统计/用户/系统 Pydantic
│   │
│   ├── routers/              ← 一个领域一个文件
│   │   ├── pages.py          ← SSR 页面（/、/login、/music/*、/diary 等）
│   │   ├── auth.py / music.py / diary.py / mood.py / energy.py / garden.py
│   │   ├── admin.py          ← 后台 API（/api/admin/*）
│   │   ├── admin_pages.py    ← 后台 SSR 页面（/admin/*）
│   │
│   ├── services/             ← 业务逻辑层（routers 不直接调 model）
│   │   ├── energy_service.py ← 能量获取 + 单日上限
│   │   ├── diary_service.py  ← 漂流瓶随机抽取
│   │   └── mood_service.py   ← 日历 + 30 天趋势
│   │
│   └── utils/
│       ├── constants.py      ← YIN_TYPES / MOOD_INFO / ENERGY_RULES
│       └── crypto.py         ← bcrypt + Fernet + PBKDF2
│
├── templates/                ← Jinja2（13 个前台页面 + 7 个后台页面 + 宏）
│   ├── base.html / _nav.html / _toast.html
│   ├── index.html / login.html / register.html
│   ├── music_list.html
│   ├── diary_write.html / my_bottles.html / diary_detail.html / pick_bottle.html
│   ├── mood_checkin.html / mood_calendar.html
│   ├── garden.html / shop.html
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
│   ├── css/
│   │   ├── style.css         ← 入口（@import 8 个模块）
│   │   ├── 00-variables.css  ← 治愈系配色 + 字体（先 import 它）
│   │   ├── 01-reset.css
│   │   ├── 02-layout.css
│   │   ├── 03-components.css
│   │   ├── 04-pages.css
│   │   ├── 05-animations.css ← 漂流瓶动效 / 心情弹跳 / 花朵生长
│   │   ├── 06-music.css
│   │   └── 07-admin.css      ← 后台专属（暗色侧栏 + 表格 + 模态）
│   ├── js/
│   │   ├── app.js            ← window.QI 全局（fetch / toast / confirmThen）
│   │   └── pages/            ← 一页一个 JS
│   │       ├── auth.js / music.js / diary.js / diary_detail.js
│   │       ├── my_bottles.js / pick.js
│   │       ├── mood.js / mood_calendar.js
│   │       ├── shop.js
│   │       ├── admin_login.js / admin_dashboard.js
│   │       ├── admin_users.js / admin_user_detail.js
│   │       ├── admin_logs.js / admin_system.js
│   ├── audio/                ← 5 个占位 mp3（每音一个）
│   └── images/               ← 占位封面（按需添加）
│
├── data/healing.db           ← SQLite（git 忽略）
├── run/healing.pid           ← 后台进程 PID
└── logs/healing.log          ← 后台进程日志（含首管密码）
```

---

## 4. 4 个 Phase 都实现了什么

### Phase 1 — 基础架构
- 用户注册 / 登录（账号密码，无邮箱）
- bcrypt 密码哈希（72 字节截断）
- 签名 cookie 会话
- 8 张表自动建表 + 种子

### Phase 2 — 古琴五音疗愈馆
- 5 音（宫商角徵羽）对应 5 脏腑，16 首古琴曲种子
- 列表 + 沉浸式播放器（播放/暂停/上下首/进度/音量/全屏）
- 听完 ≥ 90% 自动调 `/api/energy/grant` +1 露水

### Phase 3 — 漂流瓶日记
- 客户端加密：用户密码 + salt → PBKDF2 → Fernet 密钥 → AES-128-CBC
- 服务端**永不接触明文**（已实现端到端加密）
- 写日记动效：纸团 → 投瓶 → 水花 → 沉没（1.8s CSS 动画）
- 「我的瓶子」时间线：日期 + 心情表情 + 前 20 字预览
- 「拾取陌生人漂流瓶」：随机抽 `is_public=True` 的日记，给前 20 字 + 一条匿名鼓励

### Phase 4 — 心情手帐 + 精神花园
- 6 种心情表情（开心/平静/疲惫/焦虑/生气/悲伤）
- 月份日历 + 30 天趋势折线图
- 每天限 1 次，可覆盖
- 能量获取：听歌 +1 露水 / 日记 +2 阳光 / 打卡 +1 养分 / 7 连胜 +5 阳光
- 商店兑换虚拟花 / 装扮 / 徽章（**严禁**用"购买""充值"等商业词）

### Phase 5 — 秘密后台（运维 / 治理）
> 设计原则：**「管理用户」而不「窥视用户」** —— 日记是端到端加密的，管理员**永远**拿不到明文。

- **入口**：`http://127.0.0.1:5000/admin`（可在 .env 改 `QI_ADMIN_PATH_PREFIX` 换更隐蔽的路径）
- **不在前台放任何链接**（书签/记忆入口）
- **首次启动**自动创建第一个管理员（密码随机 → 写 `logs/healing.log`）
- **6 个页面**：
  1. **登录** —— 单独设计；非 admin 登录会拒绝
  2. **概览** —— 6 统计卡（用户/管理员/日记/打卡/能量流水/花园物件）+ 最近 8 条活动
  3. **用户列表** —— 昵称搜索 / 仅管理员筛选 / 分页 / 重置密码 / 代建用户
  4. **用户详情** —— 完整档案 + 统计 + **能量调整**（+N/-N 写流水）+ 重置密码 / 切换 admin / 删除
  5. **日志查看** —— tail logs/healing.log，按级别过滤，可 3s 自动刷新
  6. **系统维护** —— Python 平台 / DB 日志大小 / **一键清 pycache**
- **API 端点**全部 `/api/admin/*`，统一 `Depends(get_current_admin)` 校验
- **不能删除自己**、**不能修改自己的 is_admin 状态**（防手滑）
- **管理员可调能量**：通过 `/api/admin/users/{id}/adjust-energy`，**写流水**（source=`admin_adjust`），前端弹窗带二次确认

⚠️ **端到端加密边界**：管理员能看到 diary 的 ID / 时间 / `is_public` / `mood_type`，但**永远**拿不到 `content_encrypted` 的明文。
重置用户密码时，**`encryption_salt` 不会被改**（同一密码的密钥可复用），但用户**重置后用新密码登录**，PBKDF2 派生的 Fernet 密钥会变化，**旧日记在本机无法解密**（除非用户记得旧密码）。

---

## 5. 关键设计决策（带原因）

### 5.1 为什么客户端加密日记（端到端）
- **隐私承诺**：PRD 第 6 节明确要求"数据库泄露也无法直接读取明文"
- **实现**：每个用户注册时生成随机 16 字节 `encryption_salt` 存 `users` 表
- **密钥派生**：客户端用 PBKDF2-HMAC-SHA256(密码 + salt, 200 000 轮) → Fernet 密钥
- **密钥生命周期**：只在用户登录后的浏览器内存里，**绝不**写 cookie / localStorage / 服务端
- **退出登录 = 密钥丢失** = 旧日记无法在本机解密（但用户重新登录即可恢复）

### 5.2 为什么用 SSR 而非 SPA
- 项目是「纯治愈」，SEO 友好 + 首屏快 + JS 少
- 11 个页面每个交互都很轻，原生 fetch + DOM 操作够用
- 不需要路由状态管理（每个页面独立 JS）

### 5.3 为什么 `energy_service.py` 用 `db.query().update()` 而不是 `user.total_energy +=`
- FastAPI 一次请求一个 session，但 `User` 对象在依赖链里可能被多次 `db.get()` 加载
- 跨 session 的对象属性赋值**不会写回 DB**（这是历史踩坑，见 [HANDOFF §6.7](#67-能量累加一定要用-queryupdate)）
- 一律走显式 `UPDATE` SQL

### 5.4 为什么心情打卡用 UPSERT 而非新插一行
- 「每天限 1 次但可覆盖」业务规则要求：当天重复 → UPDATE 旧记录
- 看 `app/services/mood_service.py` 的 `checkin_today()` 函数

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
  - **不能做**：读 diary 明文（端到端加密保护）、导出全库（隐私）
- **为什么用 SQLAlchemy 显式 `.update()` 而不是 `user.total_energy = ...`**：见 [§6.7](#67-能量累加一定要用-queryupdate)
- **为什么自动迁移字段而不上 Alembic**：见 [§6.10](#610-加新字段用-lightweight-migrate-不引-alembic)

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

**修复**：[app/utils/crypto.py](file:///c:/Users/Administrator/Desktop/webwrold/app/utils/crypto.py) **不**用 passlib，直接 `import bcrypt` + `bcrypt.hashpw()` + `bcrypt.checkpw()`

### 6.3 bcrypt 72 字节限制
**症状**：`ValueError: password cannot be longer than 72 bytes`

**修复**：[app/utils/crypto.py:42-44](file:///c:/Users/Administrator/Desktop/webwrold/app/utils/crypto.py#L42) 有 `_truncate(password)`，**必须**在所有 hash/verify 之前调用

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
项目里 [app/routers/pages.py](file:///c:/Users/Administrator/Desktop/webwrold/app/routers/pages.py) 所有页面都用了新 API。

### 6.5 Windows 终端 GBK 编码
**症状**：`UnicodeEncodeError: 'gbk' codec can't encode character '\U0001f33f'`

**根因**：Windows cmd/PowerShell 默认 GBK，emoji 写入 stdout 失败

**修复（3 处协同）**：
1. [app/main.py:11-19](file:///c:/Users/Administrator/Desktop/webwrold/app/main.py#L11) 文件最顶部 `sys.stdout.reconfigure(encoding="utf-8", errors="replace")`
2. [app/main.py:38-45](file:///c:/Users/Administrator/Desktop/webwrold/app/main.py#L38) 强制所有 logging handler 的 stream 也 reconfigure
3. [start.py:175-178](file:///c:/Users/Administrator/Desktop/webwrold/start.py#L175) 启动 fg 子进程时设 `PYTHONIOENCODING=utf-8` + `PYTHONUTF8=1`

**附加**：所有 logger 输出**不要**用 emoji，统一用 ASCII 标记（`[OK] [FAIL] [WARN] ...`）

### 6.6 日记 Pydantic schema 不要 `content` 字段
**症状**：`POST /api/diary` 422 Unprocessable Content

**根因**：[app/schemas/diary.py](file:///c:/Users/Administrator/Desktop/webwrold/app/schemas/diary.py) `DiaryCreateIn` **不能**有 `content: str`（明文）字段

**设计**：客户端加密后只发 `content_encrypted`，后端**不接触明文**（端到端加密）
- ✅ `content_encrypted: str`（必填）
- ✅ `mood_type: Optional[str]`
- ✅ `is_public: bool`
- ❌ `content: str`（明文，绝对不要）

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

详见 [app/services/energy_service.py](file:///c:/Users/Administrator/Desktop/webwrold/app/services/energy_service.py)。

### 6.8 文件名不能跟 `app/` 同名
**症状**：各种奇怪 import 错误，或 `start.py` 报 `can't open file 'start.py'`

**根因**：Python 优先把 `app.py` 解释为包 `app` 的成员而非脚本

**修复**：根目录**不要**有 `app.py` / `app2.py` 等与 `app/` 同名的 `.py` 文件

### 6.9 不要在子进程里用 `import start` 引用自己
`start.py` 的 `subprocess.Popen` 用 `Path(__file__).resolve()` 而不是字面量 `"start.py"`，**永远**用 `__file__` 引用自身，万一文件改名也跑得起来。

### 6.10 加新字段用 lightweight migrate，不引 Alembic
**症状**：给 User 加了 `is_admin` 字段，老库 `data/healing.db` 重启后还是没这一列。

**原因**：`Base.metadata.create_all()` 只创建**不存在的表**，**不**会 ALTER 已存在的表。

**修复（[app/database.py:50-68](file:///c:/Users/Administrator/Desktop/webwrold/app/database.py#L50)）**：
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

**根因**：[app/routers/auth.py](../../app/routers/auth.py) 用 `response_model=AuthOut`，FastAPI 序列化时**只保留 schema 里声明的字段**。`User.to_public_dict()` 返回的 `is_admin` 虽然存在，但 `AuthOut` schema 不声明它，就被静默丢了。

**修复（[app/schemas/auth.py:16-21](../../app/schemas/auth.py)）**：
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

---

## 7. 改动指南

### 7.1 加一个新页面
1. `templates/your_page.html`：`{% extends "base.html" %}` + `{% block content %}...{% endblock %}`
2. [app/routers/pages.py](file:///c:/Users/Administrator/Desktop/webwrold/app/routers/pages.py) 加 `@router.get("/your-path")` + `return templates.TemplateResponse(request, "your_page.html", {...})`
3. `static/js/pages/your_page.js`：写页面逻辑
4. 模板底部 `<script defer src="/static/js/pages/your_page.js"></script>`
5. 更新 [README.md](file:///c:/Users/Administrator/Desktop/webwrold/README.md) §2 目录树

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
4. 更新 [README.md](file:///c:/Users/Administrator/Desktop/webwrold/README.md) §4 表速查

### 7.4 改能量规则
1. [app/services/energy_service.py](file:///c:/Users/Administrator/Desktop/webwrold/app/services/energy_service.py) 改 `ENERGY_RULES`
2. [app/utils/constants.py](file:///c:/Users/Administrator/Desktop/webwrold/app/utils/constants.py) 同步枚举
3. [README.md](file:///c:/Users/Administrator/Desktop/webwrold/README.md) §3.4 同步表格
4. **单日上限**也要在常量里更新

### 7.5 改配色 / 字体
1. 改 [static/css/00-variables.css](file:///c:/Users/Administrator/Desktop/webwrold/static/css/00-variables.css) 的 `:root { --xxx: ... }`
2. 全局自动生效
3. 项目主色调：`#F9F6F0` 米白 / `#E3F0EA` 淡青 / `#F0E3E8` 藕粉

### 7.6 部署到服务器
详见 [docs/DEPLOYMENT.md](file:///c:/Users/Administrator/Desktop/webwrold/docs/DEPLOYMENT.md)。

### 7.7 加一个后台页面 / API
1. 后台 API：[app/routers/admin.py](file:///c:/Users/Administrator/Desktop/webwrold/app/routers/admin.py) 加 `@router.get/post/...`，入参用 Pydantic in [app/schemas/admin.py](file:///c:/Users/Administrator/Desktop/webwrold/app/schemas/admin.py)
2. 后台页面：[app/routers/admin_pages.py](file:///c:/Users/Administrator/Desktop/webwrold/app/routers/admin_pages.py) 加 `@router.get(...)` + `admin_templates.TemplateResponse(request, "admin/your.html", {...})`
3. 鉴权统一用 `Depends(get_current_admin)`（API）或 `Depends(get_current_admin_or_redirect)`（页面）
4. 模板放 `templates/admin/your.html`，继承 `admin/_base.html`
5. 表格 / 模态样式直接用 [static/css/07-admin.css](file:///c:/Users/Administrator/Desktop/webwrold/static/css/07-admin.css) 里的 `.admin-*` 类
6. JS 放 `static/js/pages/admin_xxx.js`，模板底部 `<script defer src="/static/js/pages/admin_xxx.js"></script>`

### 7.8 改后台入口路径
- `.env` 改 `QI_ADMIN_PATH_PREFIX=/your-secret-path`
- 重启服务即可
- ⚠️ 改完**不会**自动迁移用户的书签，需要更新 [README.md](file:///c:/Users/Administrator/Desktop/webwrold/README.md) / [HANDOFF.md §1](file:///c:/Users/Administrator/Desktop/webwrold/HANDOFF.md) 等文档

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

# 2. 听歌 + 能量
r = s.post("http://127.0.0.1:5000/api/energy/grant",
           json={"source": "listen_music", "amount": 1})
assert r.json()["new_total_energy"] == 1

# 3. 写日记（密文）
r = s.post("http://127.0.0.1:5000/api/diary",
           json={"content_encrypted": "gAAAAA-test", "is_public": False})
assert r.status_code == 201

# 4. 心情打卡
r = s.post("http://127.0.0.1:5000/api/mood/checkin",
           json={"mood_emoji": "calm", "note": "测试"})
assert r.status_code in (200, 201)
```

---

## 9. 待优化（next agent 可选做）

按优先级：

1. **测试覆盖**（最高）— 加 `tests/`，pytest 覆盖 services + routers
2. **音频** — 5 个占位 mp3 换成真实古琴曲（用户同意再换）
3. **真实图片** — `static/images/` 现在没东西，5 音封面用 SVG
4. **MySQL 迁移** — 改 `QI_DATABASE_URL` 即可，业务层不用动
5. **WebSocket 漂流瓶实时漂动** — 现在是随机抽取，可加推送
6. **审计日志** — 谁在什么时候拾取了谁的瓶子（现在不记）
7. **HTTPS** — 服务器部署时用 Nginx 反向代理
8. **PWA / 离线** — 离线写日记（IndexedDB 加密）
9. **多语言** — 现在文案全是中文，i18n 抽出来
10. **iCal 导出心情日历**

---

## 10. 文档目录

| 文件 | 给谁看 |
|---|---|
| [README.md](file:///c:/Users/Administrator/Desktop/webwrold/README.md) | 用户 + 开发者（对外） |
| [HANDOFF.md](file:///c:/Users/Administrator/Desktop/webwrold/HANDOFF.md) | **接手的 AI**（最重要） |
| [docs/ARCHITECTURE.md](file:///c:/Users/Administrator/Desktop/webwrold/docs/ARCHITECTURE.md) | 想深入了解架构的开发者 |
| [docs/DEPLOYMENT.md](file:///c:/Users/Administrator/Desktop/webwrold/docs/DEPLOYMENT.md) | 部署到服务器的人 |
| [docs/DEVELOPMENT.md](file:///c:/Users/Administrator/Desktop/webwrold/docs/DEVELOPMENT.md) | 改代码的开发者 |
| [docs/PROJECT_STATE.md](file:///c:/Users/Administrator/Desktop/webwrold/docs/PROJECT_STATE.md) | 想知道「现在能跑吗/最近改了什么」的人 |

---

## 11. 联系人 / 决策记录

- **设计原则**：见项目 PRD（用户最初提供）
- **本会话决策**：
  - 端口 5000（不是 8000，方便和 Flask 项目区分）
  - 不用 Alembic（项目轻量，改 model 重启就好）
  - 客户端加密日记（端到端，符合 PRD 隐私要求）
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

### 12.2 触发条件：什么时候必须改文档

| 改动类型 | 必须更新的文档 | 章节 |
|---|---|---|
| 加 / 删 / 改 SQLAlchemy 模型字段 | README + PROJECT_STATE + ARCHITECTURE | README §4 / PROJECT_STATE §2 / ARCHITECTURE §4 |
| 加 / 删 / 改 Pydantic schema 字段 | README + HANDOFF | README §3.3 / HANDOFF §6.11 |
| 加 / 删 / 改 API 端点 | README + HANDOFF | README §3.2 / HANDOFF §7.2 |
| 加 / 删 / 改 SSR 页面 | README + PROJECT_STATE | README §2 / PROJECT_STATE §3.3 |
| 加 / 删 / 改能量规则 / 单日上限 | README + HANDOFF + ARCHITECTURE | README §3.4 / HANDOFF §5.3 / ARCHITECTURE §4.3 |
| 加 / 删 / 改业务常量 | README + PROJECT_STATE | README §3.6 / PROJECT_STATE §5.2 |
| 加 / 改 / 删依赖 | requirements.txt + HANDOFF | requirements.txt / HANDOFF §2 |
| 加 / 改 / 删 .env 配置项 | .env.example + HANDOFF + PROJECT_STATE | .env.example / HANDOFF §1 / PROJECT_STATE §4 |
| 改端口 / 启动命令 | README + DEPLOYMENT + HANDOFF | README §1 / DEPLOYMENT 全文 / HANDOFF §1 |
| 改 CSS 变量 / 配色 | PROJECT_STATE | PROJECT_STATE §5 |
| 改后台入口路径 / 新后台 API | HANDOFF + ARCHITECTURE + PROJECT_STATE | HANDOFF §5.6 / ARCHITECTURE §6.5 / PROJECT_STATE §5.3 |
| 修 Bug（任何） | HANDOFF + DEVELOPMENT | HANDOFF §6 / DEVELOPMENT §3 |
| 引入新的「踩坑」 | HANDOFF + DEVELOPMENT | HANDOFF §6 / DEVELOPMENT §3 |

### 12.3 同步时序

```
改代码 → 改对应文档 → 跑验证（curl 冒烟 / 端到端） → git add . → 一次 commit
                                          ↑                            │
                                          └────── 验证发现还得改 ←──────┘
                                                                         │
                                          验证通过 ←─── 文档跟着改好 ←──┘
```

> ❌ 反例：commit `feat(xxx): ...` 一小时后才想起来 README 没改 → 单独再发一个 `docs(readme): ...` commit
> ✅ 正例：feat commit **里面** README 同步改好 → diff 里能一眼看到「代码 + 文档」是同一件事

### 12.4 文档 ≠ 摆设 — 验收清单

每次提交前过一遍：
- [ ] 改了 schema → `to_public_dict()` 与 `*Out` schema 字段一致（参考 §6.11）
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

---

> 写于 2026-07-14 — 项目状态：完整可运行，所有 4 Phase 已交付
>
> 末次更新 2026-07-15（会话 2）：补 §6.11 Pydantic schema 字段缺失踩坑、§12 文档自动同步铁律、首管密码现状说明。
>
> 末次更新 2026-07-15（会话 3）：首发到 GitHub — `https://github.com/sunday-lil/jingyu`（public）。
