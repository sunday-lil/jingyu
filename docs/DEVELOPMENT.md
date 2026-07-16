# 开发约定 + 踩坑清单

> 改代码前**必读**。这里汇总了 9 个真实踩过的坑 + 7 条开发铁律。

---

## 1. 开发铁律

### 1.1 分层不许乱
```
routers/  →  services/  →  models/  →  database
   ↑          业务层         ORM
   └─ router 只调 service，不写业务
```
- router 里**不要**有 `if-else` 业务逻辑，全塞 service
- service**不要** import router
- model 只用 SQLAlchemy 基础类，**不要**写业务方法

### 1.2 中文文案要治愈
- 不用「提交」「确认」「删除」
- 用「寄出」「收好」「放下」「沉入海底」
- 改文案前先在 [PRD](../../README.md) 找调性
- toast 提示参考 [static/js/app.js](../../static/js/app.js)

### 1.3 配色字体
- 改颜色 → 改 [static/css/00-variables.css](../../static/css/00-variables.css) 的 `:root` 变量
- **不要**在子文件里写死颜色
- 主色调：`#F9F6F0` 米白 / `#E3F0EA` 淡青 / `#F0E3E8` 藕粉

### 1.4 不引外部前端框架
- ❌ React / Vue / Tailwind / Vite / webpack
- ✅ 原生 HTML + CSS + JS
- 加第三方库前先问：「不用它能写吗？」

### 1.5 隐私边界
- 日记密文**不**能在任何日志 / 错误信息里出现
- 错误处理**不**返回用户输入的原始内容
- 调试 API 时**不**用真用户数据

### 1.6 单日上限
- 所有「+x 能量」操作前先查当天累计
- 上限在 [app/utils/constants.py](../../app/utils/constants.py) `DAILY_LIMITS` 里
- 改上限要同步更新文档

### 1.7 改完跑验证
每次改完代码**必须**：
```bash
python start.py restart
sleep 1
python -c "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:5000/').status)"  # 200
```

### 1.8 改完代码**必须**同步更新文档（自动同步铁律）
> 🔒 **本节优先级最高。** 完整版见 [HANDOFF §12](../../HANDOFF.md) / [PROJECT_STATE §8](../PROJECT_STATE.md)。

**铁律**：**改代码 + 改文档 = 同一个 commit。** 不允许「代码先上，文档周末补」。

**自检 5 件事**（详见 [PROJECT_STATE §8.3](../PROJECT_STATE.md)）：
1. Pydantic Out schema 是否补了新字段（→ §3.10）
2. `_migrate_legacy_columns()` 是否补了老库列（→ §3.x / [HANDOFF §6.10](../../HANDOFF.md)）
3. `constants.py` / `energy_service.py` 是否同步
4. `.env.example` 是否同步新配置
5. README / HANDOFF 速查表是否更新

**反模式**（必须避免）：
- ❌ `feat(xxx): ...` 一小时后才发 `docs(readme): ...`
- ❌ 「改动太急，文档之后再补」
- ❌ 「这只是个 typo 不影响文档」

**正模式**：
- ✅ `feat(xxx): 新功能 + 同步 README / HANDOFF / PROJECT_STATE`

#### 1.8.1 改完自动 push（不延迟）
- `git commit` 完**立即** `git push origin main`
- 不允许「先 commit 一会儿一起推」/「明天推」/「攒一周推一次」
- 完整规则：[HANDOFF §12.6](../../HANDOFF.md)

#### 1.8.2 Commit 标题 / 脚本进度用 Conventional Commits
- 格式：`<type>(<scope>): <subject>`（subject ≤ 50 字符）
- type 9 个：`feat` / `fix` / `refactor` / `docs` / `style` / `test` / `chore` / `perf` / `revert`
- 项目 scope：`auth` / `diary` / `mood` / `music` / `energy` / `garden` / `admin` / `templates` / `static` / `docs` / `deps` / `scripts` …
- 脚本（`push-to-github.ps1`）的进度输出**也**用 `type(scope)` 标题
- 完整规则 + 示例：[HANDOFF §12.7](../../HANDOFF.md)

---

## 2. 常见改动流程

### 2.1 加新页面
1. `templates/your_page.html` 继承 `base.html`
2. [app/routers/pages.py](../../app/routers/pages.py) 加路由（**新 API**：传 `request` 作第一参数）
3. `static/js/pages/your_page.js` 写逻辑
4. 模板底部 `<script defer src="/static/js/pages/your_page.js"></script>`
5. 同步更新 [README.md](../../README.md) §2 目录树

模板示例：
```html
{% extends "base.html" %}
{% block title %}你的页面 · 静屿{% endblock %}
{% block content %}
<div class="container">
    <h1>你的标题</h1>
    <p>...</p>
</div>
{% endblock %}

{% block scripts %}
<script defer src="/static/js/pages/your_page.js"></script>
{% endblock %}
```

### 2.2 加新 API
1. [app/schemas/<name>.py](../../app/schemas/) 写 Pydantic 模型
2. [app/schemas/__init__.py](../../app/schemas/__init__.py) 加 import + `model_rebuild()`
3. [app/routers/<name>.py](../../app/routers/) 加 `@router.post(...)`
4. 业务逻辑在 [app/services/<name>.py](../../app/services/)

Pydantic 模板：
```python
from typing import Optional
from pydantic import BaseModel, Field

class XxxIn(BaseModel):
    """入参：xxx 操作"""
    field_a: str = Field(..., min_length=1, max_length=100)
    field_b: Optional[int] = None

class XxxOut(BaseModel):
    """出参：xxx 操作结果"""
    id: int
    field_a: str
    created_at: str
```

### 2.3 加新表
1. [app/models/<name>.py](../../app/models/) 写 `class Xxx(Base): __tablename__ = "xxx"; ...`
2. [app/models/__init__.py](../../app/models/__init__.py) import 它
3. 重启 → `init_db()` 自动建表
4. 同步更新 [README.md](../../README.md) §4 + [docs/ARCHITECTURE.md](../ARCHITECTURE.md) §4

Model 模板：
```python
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.database import Base

class Xxx(Base):
    __tablename__ = "xxx"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
```

### 2.4 改能量规则
1. [app/services/energy_service.py](../../app/services/energy_service.py) 改 `grant_energy()` 逻辑
2. [app/utils/constants.py](../../app/utils/constants.py) 同步 `ENERGY_RULES` 字典
3. 更新 [README.md](../../README.md) §3.4 表格

### 2.5 改种子数据
1. [app/seed.py](../../app/seed.py) 改数据
2. `python start.py --init-db` 重置数据库

### 2.6 加新动效
1. 在 [static/css/05-animations.css](../../static/css/05-animations.css) 加 `@keyframes`
2. 触发元素加 `class="your-anim"`
3. JS 端用 `element.classList.add('your-anim')` + 监听 `animationend`

#### 2.6.1 复用现成交互增强（推荐先看，避免重复造轮子）
[static/js/app.js](../../static/js/app.js) 在 `DOMContentLoaded` 自动 `QI.initAll()`，已提供：

| 想要的效果 | 怎么用 |
|---|---|
| 滚动渐显 | 给**容器**加 `class="reveal"`（可叠加 `reveal--d1`…`reveal--d6` 错峰）|
| 数字从 0 计数 | 给元素加 `class="countup" data-countup="目标值"` |
| 按钮涟漪 | 自动生效，任何 `.btn` 都有，无需加东西 |
| 卡片光泽扫过 | 自动生效在 `.module-card / .shop-item / .song-item`（hover 触发）|
| 成功撒花瓣 | JS 里调 `QI.confetti(fromEl, { glyphs: ["🌸","🌿"] })` |
| 首页环境花瓣 | 自动生效（页面含 `.hero` 时）|

**铁律**：
- `.reveal` **只加在容器上**，不要加在 `.yin-card / .module-card / .song-item / .card` 等带 `:hover { transform }` 的卡片上 —— `.reveal.is-visible` 的 transform 会覆盖 hover transform（同特异性 0,2,0，后定义胜出）。详见 [ARCHITECTURE §5.3](../ARCHITECTURE.md)。
- 所有动效已内置 `prefers-reduced-motion` 降级，新增 `@keyframes` 时**必须**也加一段 `@media (prefers-reduced-motion: reduce)` 关闭它（无障碍）。
- 涟漪用事件委托，**动态插入**的 `.btn` 也自动生效，无需手动 `initRipple()`。

---

## 3. 9 个真实踩过的坑

### 3.1 Pydantic 前向引用

**症状**：
```
pydantic.errors.PydanticUserError: `TypeAdapter[typing.Annotated[list[EnergyRecordOut], FieldInfo(...)]] is not fully defined`
```

**根因**：
Pydantic v2 用类型注解，前向引用不会自动 `model_rebuild()`。

**修复**：
1. **不要**在 schema 文件顶部加 `from __future__ import annotations`
2. 在 [app/schemas/__init__.py](../../app/schemas/__init__.py) 显式 `BaseModel.model_rebuild()`

---

### 3.2 bcrypt 4.x 与 passlib 不兼容

**症状**：
```
AttributeError: module 'bcrypt' has no attribute '__about__'
```

**根因**：
passlib 1.7 用 `bcrypt.__about__.__version__` 检查版本，bcrypt 4.x 移除了这个属性。

**修复**：
[app/utils/crypto.py](../../app/utils/crypto.py) **不**用 passlib：
```python
import bcrypt  # 直接用

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode()[:72], salt).decode("ascii")
```

---

### 3.3 bcrypt 72 字节限制

**症状**：
```
ValueError: password cannot be longer than 72 bytes
```

**根因**：
bcrypt 算法只支持最多 72 字节密码。

**修复**：
[app/utils/crypto.py](../../app/utils/crypto.py) 有 `_truncate()` 函数，**所有** hash/verify 之前必须调用。

---

### 3.4 Jinja2 TemplateResponse 新签名

**症状**：
```
TypeError: cannot use 'tuple' as a dict key (unhashable type: 'dict')
```

**根因**：
Starlette 升级后 `TemplateResponse` 第一个参数必须是 `Request` 对象，旧 API 传 dict 会触发 Jinja2 缓存键冲突。

**修复（强制）**：
```python
# ✅ 正确
return templates.TemplateResponse(
    request,                  # ← Request 对象
    "template.html",
    {"current_user": user, ...},
)

# ❌ 错误（已废弃）
return templates.TemplateResponse(
    "template.html",
    {"request": request, ...},
)
```

`grep -r "TemplateResponse("` 项目里所有页面应该都是新 API。

---

### 3.5 Windows GBK 终端 emoji 乱码

**症状**：
```
UnicodeEncodeError: 'gbk' codec can't encode character '\U0001f33f' in position 0: illegal multibyte sequence
```

**根因**：
Windows cmd/PowerShell 默认 GBK，emoji 无法编码。

**修复（3 处协同）**：
1. [app/main.py](../../app/main.py) 顶部（任何 import 之前）：
```python
import sys
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass
```

2. [app/main.py](../../app/main.py) logging 初始化后强制所有 handler 用 utf-8

3. [start.py](../../start.py) 启动 fg 子进程时：
```python
child_env["PYTHONIOENCODING"] = "utf-8"
child_env["PYTHONUTF8"] = "1"
```

4. **logger 输出不要用 emoji**（用户消息也容易出），统一用 ASCII 标记 `[OK]` `[FAIL]` `[WARN]`

---

### 3.6 日记 schema 多余 `content` 字段

**症状**：
```
POST /api/diary 422 Unprocessable Content
```

**根因**：
[app/schemas/diary.py](../../app/schemas/diary.py) 错误地要求 `content: str`（明文）字段。

**设计**：
客户端加密后只发密文，**服务端永不接触明文**（端到端加密）。

**修复**：
```python
class DiaryCreateIn(BaseModel):
    mood_type: Optional[str] = Field(None, max_length=20)
    is_public: bool = False
    content_encrypted: str = Field(..., min_length=1)  # 只有这个
    # ❌ 千万不要加 content: str
```

---

### 3.7 能量累加失效

**症状**：
`EnergyRecord` 写入成功（amount=1），但 `users.total_energy` 一直是 0。

**根因**：
FastAPI 一次请求一个 session，`user` 对象在依赖链里被多次 `db.get()` 加载，对跨 session 的对象属性赋值**不会**写回 DB。

**正确写法**：
```python
# ✅ 显式 UPDATE
db.query(User).filter(User.id == user.id).update(
    {User.total_energy: User.total_energy + amount},
    synchronize_session=False,
)
record = EnergyRecord(user_id=user.id, amount=amount, source=source)
db.add(record)
db.commit()
```

**错误写法**：
```python
# ❌ 不可靠
user.total_energy = (user.total_energy or 0) + amount
db.add(user)
```

详见 [app/services/energy_service.py](../../app/services/energy_service.py)。

---

### 3.8 文件名跟 `app/` 包同名

**症状**：
各种奇怪 import 错误，或 `start.py` 报 `can't open file 'start.py'`

**根因**：
Python 优先把 `app.py` 解释为 `app` 包的成员。

**修复**：
根目录**不要**有 `app.py` / `app2.py` 等与 `app/` 同名的 `.py` 文件。

---

### 3.9 start.py 用字面量引用自己

**症状**：
改名后 `start.py` 子进程找不到自己。

**修复**：
[start.py](../../start.py) 启动子进程时**永远**用 `Path(__file__).resolve()`：
```python
args=[sys.executable, str(Path(__file__).resolve()), "fg"]
```
**不要**写 `args=[sys.executable, "start.py", "fg"]` 这种字面量。

---

### 3.10 Pydantic Out schema 缺字段 = 响应被静默过滤

**症状**：
- 接口 200 OK
- 前端 JS 拿到的 `data.is_admin` 永远是 `undefined`
- 业务逻辑 `if (!data.is_admin)` 永远走「无权限」分支
- 排查时**不抛错**，纯静默失败，最坑

**典型场景**（2026-07-15 真实踩坑）：
1. [app/models/user.py](../../app/models/user.py) 加了 `is_admin` 字段
2. `User.to_public_dict()` 也加了
3. ❌ **漏了**：[app/schemas/auth.py](../../app/schemas/auth.py) `AuthOut` **没声明** `is_admin`
4. [app/routers/auth.py](../../app/routers/auth.py) 用 `response_model=AuthOut` → FastAPI 序列化时**只保留 schema 声明的字段**
5. 前端 `data.is_admin` 永远 `undefined` → JS 卡在「此账号没有后台权限」

**修复**（[app/schemas/auth.py](../../app/schemas/auth.py)）：
```python
class AuthOut(BaseModel):
    id: int
    nickname: str
    total_energy: int
    is_admin: bool = False   # ← 显式声明
    created_at: str
```

**铁律**：
- Pydantic Out schema **必须**是 `to_public_dict()` 字段的**超集**
- 每次 `to_public_dict()` 加字段 → 同步给所有对应 Out schema 加字段
- 改完**立即**用浏览器 DevTools → Network 看 Response body，确认字段没被吃掉

**如何在团队里防**：
- 加一个 `tests/test_schemas.py`：断言 `Out(...)` 字段 ⊇ `to_public_dict()` 字段（项目里还没有 pytest，next agent 可加）

---

### 3.11 iOS Safari 视口遮挡 / 负 z-index 层绘制错乱

**症状**（2026-07-15 苹果用户反馈）：
- 页面底部内容被地址栏挡住，滚动时地址栏收起会跳变，破坏沉浸感
- 音乐页最后一首歌被 sticky 播放器盖住，点不到
- 首页飘落花瓣 `.petal-layer` 偶尔盖在内容之上（或被 body 背景盖住看不见）

**根因 3 连**：
1. **`100vh` 含地址栏**：iOS Safari 的 `100vh` = 最大视口高度（地址栏隐藏时），地址栏显示时实际可视 < 100vh，底部内容被吃掉
2. **sticky player 遮挡列表**：`.player { position: sticky; bottom: ... }` 浮在底部，但 `.music-detail` 的 `padding-bottom` 不够，最后一项滚不到 player 上方
3. **负 z-index fixed 层绘制顺序不稳**：body 不是 stacking context 时，`.bg-orb / .petal-layer`（`position: fixed; z-index: -1`）在 iOS Safari 上的绘制顺序不可预测，可能盖内容或被背景吃掉

**修复**（[static/css/01-reset.css](../../static/css/01-reset.css) + [02-layout.css](../../static/css/02-layout.css) + [06-music.css](../../static/css/06-music.css)）：
```css
/* 1. body：dvh 兜底 + 建立 stacking context */
body {
  min-height: 100vh;
  min-height: 100dvh;     /* iOS 动态视口，覆盖上一行 */
  isolation: isolate;     /* 根 stacking context，负 z-index 层归位 */
}
/* 2. .main / .music-detail 同样 dvh 兜底 */
/* 3. sticky player 所在容器底部留足避让空间 */
.music-detail {
  padding-bottom: calc(200px + env(safe-area-inset-bottom));        /* 桌面 */
}
@media (max-width: 720px) {
  .music-detail { padding-bottom: calc(240px + env(safe-area-inset-bottom)); } /* 移动含 tabbar offset */
}
```

**铁律**：
- 任何 `min-height: 100vh` 都紧跟一行 `100dvh` 兜底（iOS 15.4+ 支持，老浏览器自动忽略第二行）
- 任何 `position: sticky/fixed` 的底部元素，其所在容器底部 `padding` ≥ 元素高度 + bottom offset + safe-area
- 全局负 z-index 的 `position: fixed` 装饰层，靠 body `isolation: isolate` 兜底，不要在每层上单独 hack z-index

---

### 3.12 页面合并 / 路由兼容重定向（以情绪日历合并今日手帐为例）

**场景**（2026-07-16 甲方反馈）：
- 「今日手帐」（每日选表情 + 写一句备注）与「漂流瓶」「选心情」功能重合
- 要求合并「每日手帐」+「日历」为「情绪日历」，不强制每天写文字（只选表情也行）
- 漂流瓶与情绪日历分开

**合并决策**：
1. **目标页选定**：把「今日打卡」UI 并入 `mood_calendar.html` 顶部，下方保留月历 + 趋势 + 连胜
2. **旧路由保留为 302 重定向**：`/mood` → `/mood-calendar`，兼容 tabbar / 书签 / 历史入口（不要直接删路由，老用户书签会 404）
3. **数据层零改动优先**：先查 `MoodCheckin.note` 是否本就 `nullable=True`——是的，那「只选表情不写文字」技术上一直支持，本次只调 UI 文案 + 文案提示，不动 model / schema / API
4. **JS 合并而非新写**：把 `mood.js` 的打卡逻辑（moodItems 选择 + saveBtn 保存 + confetti 反馈）整体并入 `mood_calendar.js`，保存成功后调用目标页已有的 `loadCalendar()` + `loadTrend()` 同步刷新今日格子、趋势、连胜
5. **删除孤立文件**：合并完确认无其他引用后，删除 `mood_checkin.html` + `mood.js`（用 `grep -r "mood_checkin.html\|js/pages/mood\.js"` 全仓搜，只有自身和文档引用）

**代码片段**（[app/routers/pages.py](../../app/routers/pages.py) 路由兼容层）：
```python
@router.get("/mood", response_class=HTMLResponse)
def mood_checkin_redirect():
    """今日手帐已合并进情绪日历（甲方 2026-07-16 要求「每日手帐与日历合一」）。

    旧链接 /mood（含 tabbar、书签、历史入口）302 重定向到 /mood-calendar，
    未登录由 /mood-calendar 路由自行跳 /login。
    """
    return RedirectResponse("/mood-calendar", status_code=302)
```

**验证矩阵**（curl.exe，PowerShell 下 `curl` 是 `Invoke-WebRequest` 别名）：
```
curl /mood                → 302 Location: /mood-calendar       （旧链接兼容）
curl /mood-calendar       → 302 Location: /login?next=/mood-calendar  （未登录）
curl /                    → 200                                  （首页）
curl /static/js/pages/mood.js → 404                              （已删除）
curl / > tmp.html && grep "今日手帐\|today-strip" tmp.html  → 无命中
curl / > tmp.html && grep "不勉强每天\|/mood-calendar" tmp.html → 命中
```

**铁律**：
- 路由合并 = 旧路由 302 重定向 + 新路由承载功能 + 删除孤立模板/JS + 文档目录树同步
- 「不强制写文字」类需求先查 schema 是否 nullable，能不改数据层就不改数据层
- 合并 JS 时复用目标页已有的刷新函数（`loadCalendar()` / `loadTrend()`），不要在两个地方各写一份渲染逻辑
- tabbar 链接更新时顺手加 `is-active` 判断，否则当前页 tab 不高亮

---

## 4. 性能 & 安全 checklist

### 4.1 改完代码后跑

```bash
python start.py restart
sleep 1
python start.py status
# 看日志
cat logs/healing.log | tail -20
# 公共 API 冒烟
curl -I http://127.0.0.1:5000/
curl -I http://127.0.0.1:5000/api/music
curl -I http://127.0.0.1:5000/api/garden/shop
```

### 4.2 安全 review

每个 PR / 改动问自己：
- [ ] 用户输入验证了吗？长度？类型？
- [ ] 鉴权依赖对吗？`get_current_user` vs `get_current_user_optional`？
- [ ] 数据库查询有 N+1 问题吗？
- [ ] 错误响应泄露了内部信息吗？
- [ ] 日记密文出现在日志里了吗？（绝对不能）

---

## 5. 调试技巧

### 5.1 看完整错误

```bash
cat logs/healing.log | tail -100
```

或前台跑：
```bash
python start.py fg
```

### 5.2 手动调 API

```python
import requests
s = requests.Session()

# 登录
r = s.post("http://127.0.0.1:5000/api/auth/login",
           json={"nickname": "test", "password": "hello123"})
print(r.status_code, r.json())

# 调任意接口
r = s.get("http://127.0.0.1:5000/api/diary")
print(r.status_code, r.json())
```

### 5.3 数据库直接看

```bash
sqlite3 data/healing.db
sqlite> .tables
sqlite> .schema users
sqlite> SELECT * FROM users LIMIT 5;
sqlite> .quit
```

### 5.4 浏览器 DevTools

- Network 标签：看 API 请求 / 响应
- Application → Cookies：看 `qi_session`
- Console：看 JS 错误

---

## 6. Git 规范

（如果用 git）

```bash
# 提交格式
git commit -m "<type>(<scope>): <subject>"
# 例: feat(diary): add bottle throw animation
# 例: fix(energy): use query.update for total_energy
# 例: docs(readme): update start.py section

# type: feat / fix / docs / refactor / test / chore
```

分支策略（单人项目可以简单点）：
- `main` — 稳定
- `dev` — 开发
- `feat/xxx` — 新功能
- `fix/xxx` — 修 bug

---

## 7. 资源

- FastAPI 文档：https://fastapi.tiangolo.com/zh/
- SQLAlchemy 2.0：https://docs.sqlalchemy.org/en/20/
- Pydantic v2：https://docs.pydantic.dev/latest/
- Jinja2：https://jinja.palletsprojects.com/
- 密码哈希：bcrypt 算法 / OWASP 密码存储备忘单
- 对称加密：Fernet (cryptography) / PBKDF2

---

## 8. 联系

- 项目 PRD：[README.md](../../README.md)
- 关键设计决策：[HANDOFF.md](../../HANDOFF.md) §5
- 架构详解：[docs/ARCHITECTURE.md](../ARCHITECTURE.md)
- 部署指南：[docs/DEPLOYMENT.md](../DEPLOYMENT.md)
- 现状快照：[docs/PROJECT_STATE.md](../PROJECT_STATE.md)
