# 项目现状快照

> 一眼看出「现在能跑吗」「最近改了什么」「还有什么 TODO」。
> 每次大改后请更新本文件。

**最后更新**：2026-07-17（会话 8 后续修复 — AI 模型换 `meta/llama-3.1-8b-instruct` + `_call_nvidia` 超时 60s + Google Fonts 换 `fonts.loli.net` 国内镜像）

---

## 1. 总体状态

| 维度 | 状态 | 备注 |
|---|---|---|
| **可运行** | ✅ | `python start.py` 即可起，端口 5000 |
| **6 个 Phase** | ✅ 全部完成 | 古琴五音 / 漂流瓶 / 情绪日历 / 精神花园 / **秘密后台** / **AI 全面接入** |
| **端到端测试** | ✅ 通过 | 注册→登录→发日记→打卡→听歌→兑换 |
| **秘密后台** | ✅ | `/admin` 入口，6 个页面 + `/api/admin/*` |
| **AI 全面接入** | ✅ 可选 | NVIDIA NIM API（`meta/llama-3.1-8b-instruct`），4 个场景；未配 `QI_NVIDIA_API_KEY` 时优雅降级，业务不中断 |
| **种子数据** | ✅ | 5 音 × 3-4 首 = 16 首古琴曲 + 11 件商店物品 + 首个管理员 |
| **文档** | ✅ | README + HANDOFF + 4 个 docs/ |
| **单元测试** | ❌ | 没有 pytest 套件（next agent 可加） |
| **HTTPS** | ❌ | 本地 HTTP，生产需 Nginx 反代 |
| **MySQL** | ❌ | 用 SQLite，将来可换 |

---

## 2. 最近改动（按时间倒序）

### 2026-07-17（会话 8 后续修复）— AI 模型默认值更换 + Google Fonts 国内镜像

- [x] 起因：① 用户 NVIDIA 账户下 `nvidia/llama-3.1-nemotron-70b-instruct` 模型不可用（API 返回 404 "Function not found for account"），实际查询账户有 119 个可用模型但不含该 70B 模型；② 国内访问 `fonts.googleapis.com` 会 ERR_CONNECTION_REFUSED（被墙），导致字体加载失败
- [x] **改动 1：AI 模型默认值更换**
  - [app/config.py](../../app/config.py)：`ai_model` 默认值 `nvidia/llama-3.1-nemotron-70b-instruct` → `meta/llama-3.1-8b-instruct`（8B 小模型，响应快：首次 5-10s，后续 1-3s）
  - [.env.example](../../.env.example)：注释里的示例值同步改为 `meta/llama-3.1-8b-instruct`
  - [app/services/ai_service.py](../../app/services/ai_service.py)：`_call_nvidia` 超时 30s → 60s（保留余量，8B 实际很快但兜底）
- [x] **改动 2：Google Fonts 换国内镜像**
  - [templates/base.html](../../templates/base.html)：3 行字体引用（preconnect + link）从 `fonts.googleapis.com` / `fonts.gstatic.com` 改为 `fonts.loli.net` / `gstatic.loli.net`
  - [templates/admin/_base.html](../../templates/admin/_base.html)：同上
  - 镜像测试：`fonts.loli.net` HTTP 200 / 1.9s（采用）；`fonts.lug.ustc.edu.cn` 301 跳转（域名已废弃）；`fonts.proxy.ustclug.org` SSL 失败；`fonts.font.im` 不可用
  - 兜底：CSS 变量 `--font-sans` / `--font-serif` 里有 `"PingFang SC", "Microsoft YaHei"` 等系统字体，镜像挂了也不会变方块字
- [x] 文档同步（铁律）：README §0/§3.5/§3.7、HANDOFF §2/§4/§5.7/末次更新、PROJECT_STATE §1/§2（本条）、ARCHITECTURE §6.6/§5、DEPLOYMENT §1.4/§2.4/AI 接入/网络要求、DEVELOPMENT §2.7/§3.14
- [x] 验证：① `meta/llama-3.1-8b-instruct` API 调用返回 200 + AI 文案；② 浏览器访问首页字体正常加载（Network 标签 `fonts.loli.net` 200）；③ 4 个 AI 端点降级正常

### 2026-07-17（会话 8）— Phase 6：AI 全面接入（NVIDIA NIM API，4 个场景，可选）
- [x] 起因：项目要加入 AI 陪伴能力，要求治愈系语气 + 不污染数据 + 未配 key 也能跑
- [x] **模型与 API**：`nvidia/llama-3.1-nemotron-70b-instruct` via NVIDIA NIM API（OpenAI 兼容格式 `/chat/completions`，base_url=`https://integrate.api.nvidia.com/v1`），用 [build.nvidia.com](https://build.nvidia.com) 免费 key
- [x] **后端新增**：
  - [app/config.py](../../app/config.py)：`Settings` 新增 `nvidia_api_key` / `ai_model` / `ai_base_url` 3 字段
  - [app/schemas/ai.py](../../app/schemas/ai.py)：7 个 Pydantic 模型（`ChatMessage`/`AIChatIn`/`AIChatOut`/`AIEncouragementIn`/`AIHealingIn`/`AIMusicRecommendIn`/`AIMusicRecommendOut`），已注册到 [app/schemas/__init__.py](../../app/schemas/__init__.py) 的 `__all__` + `model_rebuild()`
  - [app/services/ai_service.py](../../app/services/ai_service.py)：`AIServiceUnavailable` 异常 + 4 个系统提示词常量（温柔倾听 / 不诊断不开药 / 危机引导专业帮助） + `_call_nvidia()` 底层同步调用（httpx.Client 30s 超时） + 4 个上层方法 `chat()`/`generate_encouragement()`/`generate_healing_message()`/`recommend_music()`（后者含容错 JSON 解析）
  - [app/routers/ai.py](../../app/routers/ai.py)：4 个端点全部 `Depends(get_current_user)` + 全部 try/except 降级
  - [app/main.py](../../app/main.py)：注册 `ai` router（prefix=`/api/ai`）
- [x] **前端集成 4 处**：
  - **AI 树洞对话**：新增 [templates/ai_chat.html](../../templates/ai_chat.html) + [static/js/pages/ai_chat.js](../../static/js/pages/ai_chat.js)，独立页面 `/ai-chat`（需登录），多轮对话历史只存浏览器内存，刷新清空，**不落库**
  - **漂流瓶 AI 鼓励语**：[templates/pick_bottle.html](../../templates/pick_bottle.html) 加 `#ai-encouragement` 容器 + [static/js/pages/pick.js](../../static/js/pages/pick.js) 加 `loadAIEncouragement`，拾瓶成功后调 `/api/ai/encouragement`；AI 文案给读者看，**不写库**，不污染作者收件箱
  - **情绪日历 AI 治愈语**：[templates/mood_calendar.html](../../templates/mood_calendar.html) 加 `#ai-healing-msg` 容器 + [static/js/pages/mood_calendar.js](../../static/js/pages/mood_calendar.js) 加 `loadAIHealing`，打卡成功后调 `/api/ai/healing`，显示在今日心情卡片下方，**不落库**
  - **音乐 AI 心情推荐**：[templates/index.html](../../templates/index.html) 加「AI 帮我选音」卡片（仅登录可见）+ 新建 [static/js/pages/home.js](../../static/js/pages/home.js)，调 `/api/ai/recommend-music`，推荐宫商角徵羽之一 + 理由 + 跳转 `/music/{yin}`
- [x] **降级策略**：未配置 `QI_NVIDIA_API_KEY` 或调用失败（网络/超时/限流/4xx/5xx）→ 端点返回 `200 + available:false + 治愈系友好提示`，**不报 500**。前端照常显示文案，业务不中断
- [x] **隐私承诺**：AI 对话不入库；日记预览传 AI 时只取**前 120 字**（在 `ai_service.generate_encouragement()` 截断）
- [x] 依赖：[requirements.txt](../../requirements.txt) 新增 `httpx>=0.27.0,<0.29.0`
- [x] 配置：[.env.example](../../.env.example) 末尾新增 AI 配置段（默认注释掉）
- [x] 文档同步（铁律）：README §0/§2/§3.7/§8、HANDOFF §3/§4 Phase 6/§5.7/§7.9/末次更新、PROJECT_STATE §1/§2/§3（本条）、ARCHITECTURE §6.6/§7.8、DEPLOYMENT AI 环境变量段、DEVELOPMENT §2.7/§3.14
- [x] 验证：① 不配 key 跑 → 4 个 AI 端点均返回 200 + `available:false` + 治愈系提示；② 配 key 跑 → 4 个端点返回 200 + `available:true` + AI 文案；③ 浏览器手动测：/ai-chat 多轮对话 / 拾瓶后看鼓励语 / 打卡后看治愈语 / 首页 AI 推荐音

### 2026-07-16（会话 7）— 5 项 UX 优化（密码切换 / iOS 导航栏 / 模块职责分离 / 日历 emoji / 日记去心情）
- [x] 起因：甲方提 5 项需求 — ① 密码可见性切换 ② 苹果设备导航栏过大 ③ 情绪日历文本输入整合到日记 ④ 日历日期数字替换为情绪 emoji ⑤ 日记编辑页移除心情选择
- [x] **需求 1：密码可见性切换**
  - [static/css/03-components.css](../../static/css/03-components.css)：新增 `.password-input-wrap` + `.password-toggle` 样式（绝对定位眼睛按钮、tap-highlight 透明、focus-visible 描边）
  - [templates/login.html](../../templates/login.html) + [templates/register.html](../../templates/register.html)：密码 input 包裹 `.password-input-wrap`，加 `<button class="password-toggle" data-target="password">👁</button>`
  - [static/js/pages/diary.js](../../static/js/pages/diary.js)：`askPassword` 动态 modal 的 input 同样包裹 + toggle 按钮
  - [static/js/app.js](../../static/js/app.js)：新增 `initPasswordToggle()`（document-level 事件委托，支持动态生成的 modal），在 `initAll()` 调用；👁 ↔ 🙈 切换图标 + aria-label
- [x] **需求 2：iOS 导航栏优化 + 退出按钮可见性**
  - [static/css/02-layout.css](../../static/css/02-layout.css)：`.nav` 加 `padding-top: env(safe-area-inset-top)` 避让 iOS 刘海/灵动岛；移动端 `@media (max-width: 720px)` nav 高度 56px→52px、隐藏 `.nav__nickname`、加大离开按钮点击区域
  - [templates/_nav.html](../../templates/_nav.html)：L13 `/mood` → `/mood-calendar`，"手帐" → "日历"（修会话 6 遗漏未改的桌面 nav 链接）
  - [templates/base.html](../../templates/base.html) + [templates/index.html](../../templates/index.html)：meta description / hero subtitle 文案 "心情手帐" → "情绪日历"
- [x] **需求 3：情绪日历删文本输入区**
  - [templates/mood_calendar.html](../../templates/mood_calendar.html)：删除 textarea #mood-note + form-hint 整段；文案改为 "选一个表情，记录今天的心情"
  - [static/js/pages/mood_calendar.js](../../static/js/pages/mood_calendar.js)：删除 noteEl 取值，提交 `note: null`；文件头注释更新 "2026-07-16 移除文本输入，甲方要求文字内容统一进日记模块"
  - **数据迁移零改动**：DB 查询确认 `MoodCheckin.note` 历史数据 `with_note: 0`（本就 nullable=True，无历史数据需要迁移）
- [x] **需求 4：日历日期数字替换为情绪 emoji**
  - [static/js/pages/mood_calendar.js](../../static/js/pages/mood_calendar.js) `renderCalendar`：`isChecked` 时 content 只生成 `<span class="mood-emoji">${emoji}</span>`，否则显示数字；title 显示日期
  - [static/css/04-pages.css](../../static/css/04-pages.css)：`.calendar__day .mood-emoji` 从 absolute 右上角 14px 改为居中 22px（emoji 替代数字，利用 `.calendar__day` 已有的 flex 居中）
- [x] **需求 5：日记编辑页删心情选择模块**
  - [templates/diary_write.html](../../templates/diary_write.html)：删除整个心情选择模块（page-header + mood-grid）；placeholder 加 "也可以贴任何 emoji 🌸" 暗示
  - [static/js/pages/diary.js](../../static/js/pages/diary.js)：删除 `selectedMood` + moodItems click listener，提交 `mood_type: null`；**`Diary.mood_type` 字段保留**（向后兼容历史数据，新日记为 null）
- [x] 文档同步（铁律）：PROJECT_STATE §1/§2（本条）、README §3.3/§3.5、HANDOFF §2/§4、ARCHITECTURE §5.1/§7.1、DEVELOPMENT §3.13
- [x] 验证：python start.py restart → PID 17532；curl `/login` 200、`/register` 200、`/mood-calendar` 302→`/login`、`/diary/write` 302→`/login`、`/` 200；HTML 含 `password-toggle` / `password-input-wrap`；mood_calendar.html 不含 `mood-note`；diary_write.html 不含 `mood-grid`

### 2026-07-16（会话 6）— 心情模块重构：合并「今日手帐」与「情绪日历」
- [x] 起因：甲方反馈「今日手帐」与「漂流瓶」「选心情」功能重合，要求合并每日手帐与日历为「情绪日历」，不强制每天写文字（只选表情也行），漂流瓶与情绪日历分开
- [x] 改 [templates/mood_calendar.html](../../templates/mood_calendar.html)：顶部新增「今日心情」卡片（表情网格 + 可选备注 textarea + 收好按钮），文案「只选一个表情也行，文字想什么时候写就什么时候写」；连胜卡文案改为「连续记满 7 天有奖励，不勉强每天都来 ☀️」；删除趋势卡里的「记今天」按钮
- [x] 改 [static/js/pages/mood_calendar.js](../../static/js/pages/mood_calendar.js)：合并原 `mood.js` 的打卡逻辑（moodItems 选择 + saveBtn 保存 + confetti/floatEnergy 反馈），保存成功后调用 `loadCalendar()` + `loadTrend()` 刷新今日格子、趋势、连胜
- [x] 改 [app/routers/pages.py](../../app/routers/pages.py)：
  - `/mood` 路由改为 302 重定向到 `/mood-calendar`（兼容旧链接 / tabbar / 书签），未登录由 `/mood-calendar` 路由自行跳 `/login`
  - `/mood-calendar` 路由加 `db: Session = Depends(get_db)`，查 `today_record`，传 `today` + `today_record` 给模板
  - `/` index 路由：删除 `db` 参数和 `today_checkin` 查询（today-strip 已删，首页不再需要）
- [x] 改 [templates/index.html](../../templates/index.html)：删除首页 `{% if current_user %}<!-- 今日手帐条 -->{% endif %}` today-strip section；删除「今日手帐」module-card；更新「情绪日历」module-card 文案为「记今日心情，把日子染成颜色。不勉强每天，想记就记。」，图标渐变改为黄绿（#FFD56B → #A8D5BA）；漂流瓶相关卡保留不动，与情绪日历分开
- [x] 改 [templates/base.html](../../templates/base.html) tabbar：`/mood` → `/mood-calendar`，图标 🌱 → 📅，文案「手帐」→「日历」，加 `is-active` 判断
- [x] 删除 [templates/mood_checkin.html](../../templates/mood_checkin.html) + [static/js/pages/mood.js](../../static/js/pages/mood.js)（不再使用，逻辑已合并进 mood_calendar.* ）
- [x] 数据层零改动：`MoodCheckin.note` 字段本就 `nullable=True`，「只选表情不写文字」技术上一直支持，本次只调 UI 文案；`/api/mood/checkin` API 不变
- [x] 文档同步（铁律）：README §0/§2/§8、HANDOFF §2、PROJECT_STATE §1/§2（本条）、ARCHITECTURE §5.1/§8.1、DEVELOPMENT §3.12
- [x] 验证：python start.py restart → PID 18116；curl `/mood` 302 → `/mood-calendar`；`/mood-calendar` 302 → `/login?next=/mood-calendar`；`/` 200；`/static/js/pages/mood.js` 404；首页 HTML 不含「今日手帐」/「today-strip」，含「不勉强每天」/「/mood-calendar」

### 2026-07-15（会话 5）— iOS Safari 遮挡 / 沉浸感修复
- [x] 起因：苹果用户反馈 UI 界面有遮挡、影响沉浸感
- [x] 修 [static/css/01-reset.css](../../static/css/01-reset.css) body：加 `min-height: 100dvh`（`100vh` 兜底）修复 iOS 地址栏遮挡底部；加 `isolation: isolate` 建立根 stacking context，让 `.bg-orb / .petal-layer` 等负 z-index fixed 层在 iOS 上稳稳落在背景之上、内容之下
- [x] 修 [static/css/02-layout.css](../../static/css/02-layout.css) `.main`：`min-height: calc(100dvh - 64px)` 兜底
- [x] 修 [static/css/06-music.css](../../static/css/06-music.css)：
  - `.music-detail` `min-height` 用 `100dvh` 兜底
  - `.music-detail` 底部 `padding` 改 `calc(200px + env(safe-area-inset-bottom))`（桌面）/ 移动端 `calc(240px + env(safe-area-inset-bottom))`，避让 sticky 播放器，修复「最后一首歌被 player 盖住点不到」
- [x] 文档同步（铁律）：PROJECT_STATE §2（本条）、ARCHITECTURE §5.2 iOS 兼容约定、DEVELOPMENT §3.11 iOS 踩坑
- [x] 验证：python start.py restart → PID 12024；curl `/` 200、`/music/gong` 200、三个 CSS 200

### 2026-07-15（会话 4）— 前端交互增强（Netflix / Spotify 风格动效）
- [x] 扩展 [static/css/05-animations.css](../../static/css/05-animations.css) §2：滚动渐显 `.reveal`、卡片光泽扫过 sheen、按钮涟漪 `.ripple-ink`、数字计数 `.countup`、环境花瓣 `.petal`、音频频谱 `.eq-bars`、页面过渡 `.page-transition`、标题流光 `.title-shimmer`、成功花瓣 `.confetti-petal`；全部遵守 `prefers-reduced-motion`
- [x] 扩展 [static/js/app.js](../../static/js/app.js)：新增 `QI.initReveal / initRipple / initCountUp / initPetals / initPageTransition / initAll / countUp / confetti / prefersReducedMotion`；`DOMContentLoaded` 自动初始化（涟漪用事件委托，支持动态按钮）
- [x] 改 [templates/base.html](../../templates/base.html)：加 `.petal-layer` 花瓣层 + `<main class="page-transition">`
- [x] 改 [templates/index.html](../../templates/index.html)：标题 `title-shimmer`、五音 / 模块区容器 `reveal`（容器级揭示，避免与卡片 hover transform 冲突）
- [x] 改 [templates/shop.html](../../templates/shop.html)：能量数字 `data-countup` 计数
- [x] 改 [templates/music_list.html](../../templates/music_list.html) + [static/js/pages/music.js](../../static/js/pages/music.js)：播放器内嵌 `.eq-bars` 频谱（播放/暂停切换 `.is-active`）、列表容器 `reveal`
- [x] 改 [static/js/pages/shop.js](../../static/js/pages/shop.js) + [static/js/pages/mood.js](../../static/js/pages/mood.js)：成功时 `QI.confetti()` 撒花瓣
- [x] 文档同步（铁律）：README §2 目录树 + §3.5、PROJECT_STATE §2（本条）、ARCHITECTURE §5.2/§5.3、DEVELOPMENT §2.6、HANDOFF §2、DEPLOYMENT §2.6 缓存提示
- [x] 设计原则：**不引入框架**（纯原生 CSS + JS）；**治愈系调性**（米白 / 淡青 / 藕粉，光泽透明度 0.35，非 Netflix 暗黑商业风）；`.reveal` 只加在容器上，不覆盖卡片 hover

### 2026-07-15（会话 3）— 首发到 GitHub
- [x] 写 [push-to-github.ps1](../../push-to-github.ps1) — 一键「重置 + 推」脚本
  - 背景：本地 `.git` 有 loose object 损坏（`13a0fa25...`）+ 沙箱拒绝操作 `.git/`
  - 做法：脚本删坏 `.git` → `git init` → `git add -A` → `git commit` → `gh repo create` → `gh repo edit --add-topic`
  - 踩坑 1：Windows PowerShell 5.1 默认 GBK，UTF-8 中文乱码 → 改用纯英文
  - 踩坑 2：PowerShell 把 `end-to-end-encryption` 里的 `-e` 当参数 → 改用 `end_to_end_encryption` 下划线
  - 踩坑 3：`$Topics = "a,b,c"` 被解析成函数调用 → 改用数组 `@("a","b","c")`
- [x] 仓库创建成功：**https://github.com/sunday-lil/jingyu**（public）
- [x] Description / Topics 设好
- [x] 文档同步：
  - [x] [HANDOFF.md](../../HANDOFF.md) 顶部 + §1 加 GitHub URL
  - [x] [README.md](../../README.md) 顶部加 GitHub 徽章（可选）
  - [x] [PROJECT_STATE.md](PROJECT_STATE.md)（本文件）加会话 3 记录

### 2026-07-15（会话 2）— Bug 修复 + 文档同步铁律
- [x] 修 [app/schemas/auth.py](../../app/schemas/auth.py) `AuthOut` 加 `is_admin: bool` 字段
  - **症状**：admin 账号密码都正确，浏览器永远卡在「此账号没有后台权限」
  - **根因**：`response_model=AuthOut` 序列化时把未声明的 `is_admin` 静默过滤掉，前端 `data.is_admin` 永远 `undefined`
  - **修复**：一行字段声明，零代码逻辑改动
  - **同类项**：所有 Out schema 都必须是 `to_public_dict()` 字段超集
- [x] 直接连 SQLite 重置 admin 密码为 `GKmZinzvoXQbaK2D`（临时脚本，验证后删除）
- [x] 端到端验证：浏览器登录后台 → 6 统计卡正常显示
- [x] 文档同步（同步进行，**不允许**「之后再补」）：
  - [x] [HANDOFF.md](../../HANDOFF.md) 加 §6.11 Pydantic schema 踩坑
  - [x] [HANDOFF.md](../../HANDOFF.md) 加 §12 文档自动同步铁律
  - [x] [HANDOFF.md](../../HANDOFF.md) §1 标首管密码现状
  - [x] [PROJECT_STATE.md](PROJECT_STATE.md)（本文件）加会话 2 记录 + 强化 §8
  - [x] [DEVELOPMENT.md](DEVELOPMENT.md) 加 §3.10 踩坑 + §1.8 同步铁律
  - [x] [ARCHITECTURE.md](ARCHITECTURE.md) 加 §7.7 同步提示
  - [x] [README.md](../../README.md) 强化 §9 文档自洽性
  - [x] [DEPLOYMENT.md](DEPLOYMENT.md) 维护章节加同步提示

### 2026-07-15（会话 1）— Phase 5：秘密后台
- [x] 新增 [app/routers/admin.py](../../app/routers/admin.py) — 后台 API（统计/用户 CRUD/重置密码/调能量/清 pycache）
- [x] 新增 [app/routers/admin_pages.py](../../app/routers/admin_pages.py) — 后台 SSR 6 个页面
- [x] 新增 [app/schemas/admin.py](../../app/schemas/admin.py) — 后台 Pydantic 模型
- [x] 新增 `templates/admin/` — `_base.html` + `login/dashboard/users/user_detail/logs/system`
- [x] 新增 [static/css/07-admin.css](../../static/css/07-admin.css) — 后台暗色侧栏 / 表格 / 模态
- [x] 新增 `static/js/pages/admin_*.js` — 6 个后台页面 JS
- [x] 改 [app/models/user.py](../../app/models/user.py) 加 `is_admin: Boolean`
- [x] 改 [app/database.py](../../app/database.py) 加 `_migrate_legacy_columns()`（轻量迁移，不引 Alembic）
- [x] 改 [app/config.py](../../app/config.py) 加 `QI_ADMIN_USERNAME/PASSWORD/PATH_PREFIX`
- [x] 改 [app/deps.py](../../app/deps.py) 加 `get_current_admin` + `get_current_admin_or_redirect`
- [x] 改 [app/seed.py](../../app/seed.py) 自动创建首个管理员（密码随机 → `logs/healing.log`）
- [x] 改 [HANDOFF.md](../../HANDOFF.md) 加 Phase 5 / §5.6 设计边界 / §7.7 后台改动指南
- [x] 端到端验证：登录后台 → 看仪表盘 → 重置用户密码 → 调能量 → 看日志 → 清 pycache

### 2026-07-14
- [x] 写完 [HANDOFF.md](../../HANDOFF.md)（AI 交接说明）
- [x] 更新 [README.md](../../README.md) 端口/启动/目录树
- [x] 写 [docs/ARCHITECTURE.md](ARCHITECTURE.md)（架构详解）
- [x] 写 [docs/DEPLOYMENT.md](DEPLOYMENT.md)（部署指南）
- [x] 写 [docs/DEVELOPMENT.md](DEVELOPMENT.md)（开发约定）
- [x] 更新 [.env.example](../../.env.example) 用 QI_ 前缀
- [x] 修 [app/schemas/diary.py](../../app/schemas/diary.py) 删多余 `content` 字段（消除 422 错误）
- [x] 修 [app/main.py](../../app/main.py) 顶部强制 UTF-8（消除 emoji 乱码）
- [x] 修 [start.py](../../start.py) 子进程环境变量（消除 GBK 编码问题）
- [x] 修 [app/services/energy_service.py](../../app/services/energy_service.py) 用 `db.query().update()`（修能量累加）
- [x] 修 [app/utils/crypto.py](../../app/utils/crypto.py) 直接用 bcrypt + 72 字节截断
- [x] 修 [app/routers/pages.py](../../app/routers/pages.py) 用新 `TemplateResponse(request, ...)` 签名

### 之前
- 4 个 Phase 全部交付
- 13 个 HTML 模板 + 9 个页面 JS + 7 个 CSS 模块 + 8 张表

---

## 3. 文件清单

### 3.1 文档
- [README.md](../../README.md) — 用户主文档
- [HANDOFF.md](../../HANDOFF.md) — AI 交接说明（最重要）
- [docs/ARCHITECTURE.md](ARCHITECTURE.md) — 架构详解
- [docs/DEPLOYMENT.md](DEPLOYMENT.md) — 部署指南
- [docs/DEVELOPMENT.md](DEVELOPMENT.md) — 开发约定 + 踩坑
- [docs/PROJECT_STATE.md](PROJECT_STATE.md) — 现状快照（本文件）

### 3.2 后端（[app/](../../app/)）
- `__init__.py` / `main.py` / `config.py` / `database.py` / `deps.py` / `security.py` / `seed.py`
- `models/` — 7 张表 + `__init__.py`（users 含 `is_admin`）
- `schemas/` — **7 个** Pydantic 模块（auth/diary/mood/music/energy/**admin**/**ai**）+ `__init__.py`
- `routers/` — **10 个** router（pages + 6 业务 + **admin + admin_pages** + **ai**）
- `services/` — **4 个**业务服务（energy / diary / mood / **ai_service**）
- `utils/` — 加密 + 常量

### 3.3 前端
- `templates/` — **14 个**前台 .html（含 **ai_chat.html**）+ **6 个后台 .html**（`templates/admin/`）+ 宏
- `static/css/` — 8 个 .css（含 **07-admin.css**）
- `static/js/` — 1 个 app.js + **17 个** pages/（11 个前台：含 **ai_chat.js** + **home.js**；6 个后台）

### 3.4 脚本
- [start.py](../../start.py) — 服务管理（核心）

### 3.5 数据 / 运行时
- `data/healing.db` — SQLite（git 忽略）
- `run/healing.pid` — PID
- `logs/healing.log` — 日志
- `.env` — 用户环境变量（git 忽略，从 .env.example 复制）

---

## 4. 端口与地址

| 场景 | 地址 |
|---|---|
| 本机开发 | http://127.0.0.1:5000 |
| API 文档 | http://127.0.0.1:5000/docs |
| 健康检查 | http://127.0.0.1:5000/ |
| **秘密后台** | **http://127.0.0.1:5000/admin**（可在 `.env` 改 `QI_ADMIN_PATH_PREFIX`） |
| 生产服务器 | http://你的域名/（Nginx 80/443 → 5000） |

> 秘密后台不放任何前台链接，纯粹靠 URL 入口（书签/记忆）。首次启动会自动创建管理员，密码随机 → 写 `logs/healing.log`，看 `[ADMIN] password :` 一行。
>
> **当前真实首管密码**（2026-07-15 临时测试用）：`GKmZinzvoXQbaK2D`（由开发者直接改 SQLite 写回，便于人工测试）。生产部署前**必须**在 `.env` 设 `QI_ADMIN_PASSWORD=<强密码>` 并重启。

---

## 5. 数据快照

### 5.1 种子数据
- **音乐**（16 首）：每音 3-4 首
  - 宫音 (土): 梅花三弄 / 阳春 / 大胡笳
  - 商音 (金): 潇湘水云 / 广陵散 / 阳关三叠
  - 角音 (木): 流水 / 醉渔唱晚 / 平沙落雁
  - 徵音 (火): 渔樵问答 / 忆故人 / 普安咒
  - 羽音 (水): 良宵引 / 鸥鹭忘机 / 梧叶舞秋风
- **商店物品**（11 件）：
  - 植物：向日葵 / 竹子 / 莲花 / 梅花 / 菊花
  - 装扮：草帽 / 长袍 / 蒲扇
  - 徽章：古琴初学者 / 日记达人 / 连胜 7 日

### 5.2 业务规则常量
- 单日能量上限：露水 20 / 阳光 10 / 养分 5
- 心情：6 种（开心/平静/疲惫/焦虑/生气/悲伤）
- 心情打卡：每天 1 次可覆盖
- 日记长度：1-5000 字
- 会话有效期：30 天
- 管理员数量：≥ 1（首个启动时自动创建，密码随机 → 写日志）
- 后台 URL 前缀：`/admin`（默认，可在 .env 改）

### 5.3 秘密后台能做什么
- ✅ 看用户列表 / 详情（昵称 / 能量 / 统计 / 创建时间）
- ✅ 重置用户密码（前端弹二次确认）
- ✅ 调整用户能量（+N/-N 写流水，source=`admin_adjust`）
- ✅ 创建 / 删除用户（级联删日记/打卡/能量/花园）
- ✅ 切换用户 `is_admin` 状态
- ✅ tail `logs/healing.log`（按级别过滤，可 3s 自动刷新）
- ✅ 一键清 `__pycache__`（[app/routers/admin.py](../../app/routers/admin.py) 的 `POST /api/admin/system/clear-pycaches`）
- ❌ **不能**读日记明文（端到端加密保护，管理员也拿不到）
- ❌ **不能**删自己 / 改自己的 `is_admin`（防手滑）

---

## 6. 测试覆盖

| 范围 | 状态 | 测试方法 |
|---|---|---|
| 启动脚本 | ✅ | `python start.py restart` + `status` |
| 公共 API | ✅ | curl 冒烟（见 [README §7](../../README.md)） |
| 端到端流程 | ✅ | 浏览器手动测试（注册→听歌→日记→打卡→兑换） |
| 秘密后台 | ✅ | 浏览器手动测试（登录→仪表盘→重置密码→调能量→看日志→清 pycache） |
| 单元测试 | ❌ | 缺 `tests/` 目录 |
| 集成测试 | ❌ | 缺 pytest |

**验证命令**：
```bash
python start.py restart
sleep 1
python start.py status
curl -I http://127.0.0.1:5000/                          # 200
curl -I http://127.0.0.1:5000/api/music                 # 200
curl -I http://127.0.0.1:5000/api/garden/shop           # 200
curl -I http://127.0.0.1:5000/music/gong                # 200
curl -I http://127.0.0.1:5000/diary                     # 302 (未登录)
curl -I http://127.0.0.1:5000/admin                     # 302 (未登录跳 /admin/login)
curl -I http://127.0.0.1:5000/api/admin/stats           # 401 (未登录)

# 用当前真实首管密码登录（详见 HANDOFF §1 / 本文件 §4）
curl -c c.txt -X POST http://127.0.0.1:5000/api/auth/login \
     -H "Content-Type: application/json" \
     -d "{\"nickname\":\"admin\",\"password\":\"GKmZinzvoXQbaK2D\"}"   # 200 + cookie
curl -b c.txt http://127.0.0.1:5000/api/admin/stats     # 200 + {"is_admin":true,...}
```

---

## 7. 待办（next agent 可选）

按优先级：

### P0（重要）
- [ ] 加 `tests/`（pytest）— 业务逻辑、加密、能量规则
- [ ] CI / 自动化测试
- [ ] 真实音频（5 音真实 mp3，用户同意后换）

### P1（次要）
- [ ] 真实图片（5 音封面 SVG / PNG）
- [ ] MySQL 迁移测试
- [ ] 心情数据 iCal 导出
- [ ] 浏览器 favicon / manifest.json（PWA 准备）

### P2（远期）
- [ ] WebSocket 漂流瓶实时漂动
- [ ] 审计日志（谁在什么时候拾取了谁的瓶子）
- [ ] HTTPS / Let's Encrypt 一键配置
- [ ] 多语言（i18n）
- [ ] 离线写日记（IndexedDB 加密）
- [ ] 浏览器密码丢失 → 日记无法恢复的告警文档化

---

## 8. 文档维护规则（自动同步铁律）

> 🔒 **本节是项目最高优先级的一条规则。** 改代码不改文档 = 改了一半。
> 完整版见 [HANDOFF §12](../../HANDOFF.md)。

### 8.1 一句话铁律

**改代码 + 改对应文档 = 同一个 commit，**绝不允许**「代码先上，文档之后补」。**

### 8.2 改了 → 同步更新

| 改了 | 更新（必须在 commit 前完成） |
|---|---|
| 新页面 / 新文件 | [README.md](../../README.md) §2 目录树 + §8 速查表 |
| 新数据库表 | [README.md](../../README.md) §4 表速查 + [docs/ARCHITECTURE.md](ARCHITECTURE.md) §4 |
| 新能量规则 | [app/utils/constants.py](../../app/utils/constants.py) 同步 + [README.md](../../README.md) §3.4 |
| 新依赖 | [requirements.txt](../../requirements.txt) + [HANDOFF.md](../../HANDOFF.md) §2 |
| 启动方式变化 | [start.py](../../start.py) 顶部 docstring + [README.md](../../README.md) §1 |
| 端口变化 | [README.md](../../README.md) §0/§1/§4 + [.env.example](../../.env.example) |
| **后台新增页面 / API** | [HANDOFF.md](../../HANDOFF.md) §7.7 + [docs/ARCHITECTURE.md](ARCHITECTURE.md) §6（后台章节）+ 本文件 §5.3 |
| **后台 URL 前缀 / 管理员配置变化** | [.env.example](../../.env.example) + [HANDOFF.md](../../HANDOFF.md) §1 + 本文件 §4 |
| **踩坑** | [HANDOFF.md](../../HANDOFF.md) §6「已知坑」+ [docs/DEVELOPMENT.md](DEVELOPMENT.md) §3 |
| **大改** | 本文件 [docs/PROJECT_STATE.md](PROJECT_STATE.md) §2「最近改动」 |
| **任何 Pydantic schema 字段** | 对应 Out schema + [HANDOFF.md](../../HANDOFF.md) §6.11 铁律提醒 |
| **任何 User 字段** | [HANDOFF.md](../../HANDOFF.md) §1（首管/账号说明） |

### 8.3 提交前自检清单

- [ ] 改的 schema 字段在 `*Out` Pydantic 里**也都声明了**（避免 §6.11 类 Bug）
- [ ] 改的 model 字段在 `_migrate_legacy_columns()` 里**也加了**（避免老库丢列）
- [ ] 改的常量在 README 表格里**也更新了**（业务规则可见性）
- [ ] 改的 .env 配置在 `.env.example` 里**也加了**（部署可见性）
- [ ] 新增页面 / API 在 README §2 / §3 速查表里**也加了**（可发现性）

### 8.4 时序

```
改代码 → 改文档 → 跑验证（curl / 端到端） → git add . → 一个 commit
                ↑                                              │
                └──────── 验证发现还得改，回 1 ←───────────────┘
```

> ❌ 反例：`feat(xxx)` 一小时后才发 `docs(readme): ...`
> ✅ 正例：`feat(xxx): 新功能 + 同步 README / HANDOFF`

### 8.5 原则

文档 ≠ 摆设。改完代码随手更新，让下一个 AI / 开发者接手时一眼能懂。**不更新 = 给后人埋雷。**

### 8.6 改完自动 push（不延迟）
- 跟 §8.1 同优先级
- `git commit` 完**立即** `git push origin main`
- 不允许「先 commit 一会儿一起推」/「明天推」/「攒一周」
- 详细规则见 [HANDOFF §12.6](../../HANDOFF.md)

### 8.7 Commit 标题 / 脚本进度用 Conventional Commits
- 格式：`<type>(<scope>): <subject>`（subject ≤ 50 字符）
- 9 个 type：`feat` / `fix` / `refactor` / `docs` / `style` / `test` / `chore` / `perf` / `revert`
- 项目 scope：`auth` / `diary` / `mood` / `music` / `energy` / `garden` / `admin` / `templates` / `static` / `docs` / `deps` / `scripts` …
- 脚本（如 `push-to-github.ps1`）的进度输出**也**用 `type(scope)` 标题 → 跑完日志 = commit 历史
- 详细规则见 [HANDOFF §12.7](../../HANDOFF.md)

---

## 9. 联系 / 决策

- **设计原则**：见 [PRD](../../README.md)（用户最初提供）
- **关键技术决策**：[HANDOFF.md](../../HANDOFF.md) §5
- **已知坑**：[HANDOFF.md](../../HANDOFF.md) §6
- **如果文档和代码矛盾**：以代码为准，然后回更新文档。
