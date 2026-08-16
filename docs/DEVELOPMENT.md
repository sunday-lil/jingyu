# 开发约定 + 踩坑清单

> 改代码前**必读**。这里汇总了 9 个真实踩过的坑 + 7 条开发铁律。

> 🔒 **2026-07-19 v2.0.1 端口策略调整 + Three.js 花田**：开发模式从 Vite :5173 + FastAPI :5000 改为 **Vite :5000 + FastAPI :5001**（用户始终访问 :5000）；新增 [FlowerField.vue](../../frontend/src/components/FlowerField.vue) 3D 花田组件作为 `defineAsyncComponent` 异步加载示例。关键词 `5001` / `FlowerField` / `Vite :5000` 在 6 份文档（README / HANDOFF / PROJECT_STATE / ARCHITECTURE / DEPLOYMENT / DEVELOPMENT）中都要出现。详见 [§1.9.1 启动开发模式](#191-启动开发模式vite-dev-server-5000--fastapi-50012026-07-19-v201-改) / [§1.9.5 加新视图](#195-加新视图vue-3-spa-模式替代旧-21-jinja2-模式) / [§1.9.7 调试技巧](#197-调试技巧)。

> 🔒 **2026-07-20 v2.1 视觉增强**：新增 4 个视觉组件（[AmbientBackground.vue](../../frontend/src/components/AmbientBackground.vue) / [HeroScene.vue](../../frontend/src/components/HeroScene.vue) / [AudioVisualizer.vue](../../frontend/src/components/AudioVisualizer.vue) + [utils/visual.js](../../frontend/src/utils/visual.js)），三层渐进增强策略（CSS 永远启用 → Canvas2D 中量级 → Three.js 按需）。**新建视觉组件必须遵守 4 大铁律**（详见 [§1.9.8 视觉组件开发指南](#198-视觉组件开发指南v21-加2026-07-20)）：① `createMediaElementSource` 一次性守卫；② Three.js 对象用 `shallowRef` 而非 `ref`；③ rAF 必须走 `smartRAF` 而非 `requestAnimationFrame`；④ `onBeforeUnmount` 必须完整释放。关键词 `三层渐进增强` / `AmbientBackground` / `HeroScene` / `AudioVisualizer` / `visual.js` / `shallowRef` / `smartRAF` 在 6 份文档中都要出现。

> 🔒 **2026-07-25 v2.2.2 start.py 默认应用模式**：`python start.py` 默认行为变更——**默认走应用/开发模式**（Vite :5000 HMR + FastAPI :5001 API 一起起），自动检测 `frontend/node_modules` 不存在则 `npm install`。生产模式需显式 `python start.py --prod`（FastAPI :5000 单进程，需 dist 已构建）。`--dev` 改为兼容别名（等同默认行为）。关键词 `--prod` / `默认应用模式` / `自动 npm install` / `前后端一起起` 在 6 份文档中都要出现。

> 🔒 **2026-07-25 v2.3 六大四字名模块 + 双资源系统 + 花朵生命周期 + 通知 + 个人主页 + 古琴弹西洋曲谱**：13 项大改全部完成。**开发新功能必须遵守 pre-commit 5 项 checklist**（详见 [§1.8](#18-改完代码必须同步更新文档自动同步铁律) / [HANDOFF §12.4](../../HANDOFF.md)）：① Pydantic Out schema 同步 ② `_migrate_legacy_columns()` 加列 ③ `constants.py` 业务常量同步 ④ `.env.example` 配置同步 ⑤ README+HANDOFF 速查表同步。新增模型 `UserFlower` / `Notification` + service `flower_service` + routers `notifications.py` / `profile.py` + 前端视图 `HealingView` / `WesternMusicListView` / `ProfileView`；双资源系统 `User.dew` + `User.leaves` 替代单一 `total_energy`；情绪日历 emoji 字符统一；树洞文件式聊天历史 `data/chats/{user_id}/{session_id}.json`；五音疗愈盘独立为顶级模块（`/healing`）；古琴弹西洋曲谱子菜单（`musics.is_western_score` + `/music/western`）。关键词 `双资源` / `露水` / `落叶` / `UserFlower` / `Notification` / `ProfileView` / `古琴弹西洋曲谱` / `visibility` / `树洞` / `漂流瓶社交` / `五音疗愈盘` / `pre-commit 5 项` 在 6 份文档中都要出现。

> 🔒 **2026-07-28 v2.3.2 start.py 默认生产模式 + 自动构建简化**：`python start.py` 默认行为**再次变更**（回滚 v2.2.2「默认应用模式」）——**默认走生产模式**（FastAPI :5000 单进程，前后端不再一起起），需 `static/dist/` 已构建（不存在则自动 `npm install + npm run build`）。**`dist 存在检测`**——仅检测 `static/dist/index.html` 存在性；**`自动构建`**：dist 不存在时自动 `npm install + npm run build`（需 Node.js 18+）。**开发需显式 `python start.py --dev`**（Vite :5000 HMR + FastAPI :5001 API，前后端一起起的「应用模式」）。`--prod` 改为兼容别名（默认就是生产模式）。详见 [§1.9.1](#191-启动开发模式vite-dev-server-5000--fastapi-5001v232-起需显式---dev) / [§1.9.2](#192-开发模式-vs-生产模式v232-起默认生产模式)。关键词 `默认生产模式` / `dist 存在检测` / `自动构建` / `--dev` / `应用模式` / `v2.3.2` 在 6 份文档中都要出现。

> 🔒 **2026-07-30 v2.3.3 Safari 兼容性修复（3D 上下文恢复 + emoji 跨浏览器一致）**：**Safari 兼容**两类问题修复。① 3D 不渲染：[utils/visual.js](../../frontend/src/utils/visual.js) **`hasWebGL` 重写**（区分 WebGL1/2 + 检测扩展 + max texture size）+ 新增 `getWebGLCaps()` / `isSafari()` / `isIOS()`；[utils/three-helpers.js](../../frontend/src/utils/three-helpers.js) 添加 `webglcontextlost` / `webglcontextrestored` 事件监听处理 **WebGL 上下文丢失**（iOS Safari 切后台→前台触发）；[HeroScene.vue](../../frontend/src/components/HeroScene.vue) **iOS 降级**（**Bloom 降级**：iOS 关闭 UnrealBloomPass；**PMREM 降级**：iOS PMREM 256→128、阴影 2048→1024、dpr 2→1.5）。② emoji 不一致：新建 [EmojiIcon.vue](../../frontend/src/components/EmojiIcon.vue) 组件用 **Iconify** + `@iconify-json/twemoji` 离线 **SVG emoji**，确保 **跨浏览器一致**，替换 AppLayout.vue + ProfileView.vue 所有 emoji。**新建 3D 组件必须复制 HeroScene 的 `webglcontextlost` / `webglcontextrestored` 监听 + iOS 降级逻辑**（详见 [§1.9.8](#198-视觉组件开发指南v21-加2026-07-20) / [HANDOFF §6.24](../../HANDOFF.md)）；**新增 emoji 必须用 `<EmojiIcon name="..." />` 而非裸 emoji 字符**（详见 [§1.9.9](#199-emoji-组件用法emojiiconvuev233-加2026-07-30)）。关键词 `Safari 兼容` / `WebGL 上下文丢失` / `webglcontextlost` / `iOS 降级` / `EmojiIcon` / `Iconify` / `twemoji` / `SVG emoji` / `跨浏览器一致` / `hasWebGL 重写` / `getWebGLCaps` / `isSafari` / `isIOS` / `Bloom 降级` / `PMREM 降级` / `v2.3.3` 在 6 份文档中都要出现。

> 🔒 **2026-08-10 v2.4.0 开发规则（头像/昵称编辑 + 一天多条心情 + 花坊改名 + 静屿使用指南）**：开发 v2.4.0 新功能必须遵守 5 条规则（在 v2.3 pre-commit 5 项 checklist 之上）：① **新增模型字段必须同步 `_migrate_legacy_columns()`**——如 **User.avatar**（`String(16)` 默认 `🙂`），老库重启时 `ALTER TABLE users ADD COLUMN avatar VARCHAR(16) DEFAULT '🙂' NOT NULL` 自动加列；② **SQLite 移除唯一约束的迁移方式**（SQLite 不支持 DROP CONSTRAINT，必须重建表）：CREATE TABLE _new AS SELECT * FROM old → DROP TABLE old → RENAME TABLE _new TO old → CREATE INDEX，本次 **mood_checkins 唯一约束移除**（`(user_id, check_date)` 唯一约束）走此流程，支持**一天多条心情**记录；③ **service 函数重命名时必须同步 [app/services/__init__.py](../../app/services/__init__.py) + [app/schemas/__init__.py](../../app/schemas/__init__.py) 的 import**——如 `upsert_checkin` → `add_checkin`（不再 UPSERT，允许一天多条）+ 新增 `get_today_moods`（获取今日所有心情）+ `get_recent_trend` 多条取**平均分**（MOOD_SCORE 映射：ecstatic=5/happy=4/calm=3/tired=2/anxious=2/angry=1/sad=1）；④ **新增 Pydantic schema 文件必须在 [app/schemas/__init__.py](../../app/schemas/__init__.py) 中 `model_rebuild()`**——如新增 [app/schemas/profile.py](../../app/schemas/profile.py) + `ProfileUpdateIn`（nickname 2-20 字符可选 / avatar 1-16 字符可选），配合新增 router **PATCH /api/profile**（昵称查重 409，**头像同步树洞**显示）；⑤ **emoji 必须用 `<EmojiIcon name="..." />` 组件**（v2.3.3 铁律延续，详见 [§1.9.9](#199-emoji-组件用法emojiiconvuev233-加2026-07-30)）——[ProfileView.vue](../../frontend/src/views/profile/ProfileView.vue) 头像编辑弹窗 24 个可选 emoji + [AIChatView.vue](../../frontend/src/views/ai/AIChatView.vue) 用 `userStore.avatar` 显示头像 + [HomeView.vue](../../frontend/src/views/HomeView.vue) 文案改为「**潮声不止心安自屿**」+ 删今日打卡 + 模块名「**花坊**」+ [MoodCalendarView.vue](../../frontend/src/views/mood/MoodCalendarView.vue) emoji 显示修复 + 多条打卡 + [GardenView.vue](../../frontend/src/views/garden/GardenView.vue) AI 基于实际种花 + stores/user.js 新增 `updateProfile` action。其他 v2.4.0 改动：心语树洞 AI 系统提示词 **humanize**（更接地气）+ 「落叶画坊」→「花坊」+ 花种扩充至 12 种 + 新装扮（油纸伞/蓑衣/乌篷船/鱼竿/橘猫/白鹤）+ 「古琴初学者」→「**琴音知音**」+ **每板块徽章**（琴音知音/日记达人/七日静心/拾瓶旅人/树洞倾心/花田主人）+ 「竹编帽」描述更新 + **静屿使用指南**（详细介绍所有模块）+ **露水累加修复**（写日记和留言鼓励后正确发放）+ [DEFAULT_SHOP_ITEMS](../../app/utils/constants.py) 扩充至 27 件。pre-commit 5 项 checklist（Pydantic Out / `_migrate_legacy_columns` / `constants.py` / `.env.example` / README+HANDOFF 速查表）仍然适用。关键词 `v2.4` / `潮声不止心安自屿` / `花坊` / `一天多条心情` / `mood_checkins 唯一约束移除` / `add_checkin` / `get_today_moods` / `平均分` / `humanize` / `琴音知音` / `每板块徽章` / `User.avatar` / `PATCH /api/profile` / `ProfileUpdateIn` / `头像同步树洞` / `静屿使用指南` / `露水累加修复` 在 6 份文档中都要出现。

> 🔒 **2026-08-10 v2.4.1 开发规则（情绪日历罗素情绪环模型四象限图表）**：开发情绪环模型图表时必须遵守 4 条规则（在 v2.4.0 规则之上）：① **valence/arousal 坐标系约定**——`CIRCUMPLEX_EMOTIONS` 数组 20 种情绪，每种情绪带 `valence`(-1~+1，消极→积极) 和 `arousal`(-1~+1，低唤醒→高唤醒) 坐标，7 种已追踪情绪（ecstatic/happy/calm/tired/anxious/angry/sad）映射后端 [MOOD_INFO](../../app/utils/constants.py)（`tracked: true`），13 种参考情绪 `tracked: false`；② **emotionPosition 百分比转换公式**——`left% = (valence + 1) / 2 * 100`，`top% = (1 - (arousal + 1) / 2) * 100`（top 反转，上=高唤醒），用百分比绝对定位 emoji 到四象限图表；③ **moodCounts 从 checkins 统计**——`moodCounts` computed 从 `checkins` 数据统计本月各心情出现次数，已追踪情绪有边框高亮 + 次数角标，`totalCheckins` 显示本月总打卡数；点击 emoji 弹详情卡片（已追踪显示「本月出现 X 次」/ 未追踪显示「该情绪暂未开放打卡记录」）；④ **保留 fetchTrend 供 currentStreak 使用**——`fetchTrend` 仍调用（为 `currentStreak` 连续打卡天数显示），但 `trend` 数据不再用于渲染（原 `trendBars` computed / `scoreColor` 函数 / `.trend-section` 模板 / `.trend-bar` 样式全部删除）。纯前端变更（[MoodCalendarView.vue](../../frontend/src/views/mood/MoodCalendarView.vue)），无后端改动 / 无数据库迁移 / 无新依赖。关键词 `v2.4.1` / `Russell情绪环模型` / `Circumplex Model` / `四象限图表` / `效价Valence` / `唤醒度Arousal` / `CIRCUMPLEX_EMOTIONS` / `emotionPosition` / `moodCounts` / `20种情绪` / `点击交互` / `本月出现次数` 在 6 份文档中都要出现。

> 🔒 **2026-08-13 v2.4.2 开发规则（整体架构优化与冗余清理，维护性清理版本）**：本次为维护性清理版本，**无功能变化 / 无数据库迁移 / 无新依赖**，7 项改动专注代码瘦身与一致性对齐。开发维护性清理时遵守以下要点：① **死代码清理原则**——Vue 3 SPA 迁移前的旧 Jinja2 SSR 模板（[templates/](../../templates/) 下 15 个 `.html` + `templates/partials/` 空目录，`死模板清理`）+ 死页面脚本（[static/js/pages/](../../static/js/pages/) 下 10 个非 admin `.js`，`死页面脚本`）仅被彼此引用，迁移后已无入口，可安全删除；**仅保留** [templates/admin/](../../templates/admin/)（[admin_pages.py](../../app/routers/admin_pages.py) 仍使用 Jinja2 SSR）。② **版本号必须三处对齐**（`版本号对齐`）——[app/main.py](../../app/main.py) 版本号 1.0.0 → 2.4.2（与 git tag / README badge 对齐），改版本号时检查 `main.py` / `README.md` badge / git tag 三处一致。③ **EXT_TO_MIME 字典去重**（`EXT_TO_MIME`）——[app/main.py](../../app/main.py) `EXT_TO_MIME` 中 `.webp` 重复定义，删除后者。④ **过时注释修复**（`过时注释`）——[app/routers/pages.py](../../app/routers/pages.py) / [frontend/vite.config.js](../../frontend/vite.config.js) / [static/js/app.js](../../static/js/app.js) 中端口注释 `:5173 → :5000`（Vite）/ `:5000 → :5001`（FastAPI 开发），与 [§1.9.1](#191-启动开发模式vite-dev-server-5000--fastapi-50012026-07-19-v201-改) 端口策略一致。⑤ **五音封面 SVG 资源补全**（`SVG封面`）——[static/img/cover_gong.svg](../../static/img/cover_gong.svg) / `cover_shang.svg` / `cover_jue.svg` / `cover_zhi.svg` / `cover_yu.svg`，颜色取自 [app/utils/constants.py](../../app/utils/constants.py) `YIN_INFO`，修复 [app/seed.py](../../app/seed.py) 引用的缺失资源。⑥ **N+1 查询优化模式**（`N+1优化` / `GROUP BY`）——[app/routers/admin_pages.py](../../app/routers/admin_pages.py) `admin_users` 原 for 循环内 3 个 COUNT/用户 × 50 用户 = 151 次查询，优化为 1 次查用户 + 3 个 `GROUP BY` 聚合 + 字典拼接 = 4 次查询；**开发新管理端列表接口时优先用 `GROUP BY` 聚合 + 字典拼接，避免 for 循环内 COUNT**。⑦ **不动**：[static/css/](../../static/css/) / [static/js/app.js](../../static/js/app.js) / [static/audio/](../../static/audio/) / [templates/admin/](../../templates/admin/) / [config.py](../../config.py) / [app/database.py](../../app/database.py) / [requirements.txt](../../requirements.txt)。关键词 `v2.4.2` / `死模板清理` / `死页面脚本` / `N+1优化` / `GROUP BY` / `SVG封面` / `EXT_TO_MIME` / `版本号对齐` / `过时注释` 在 6 份文档中都要出现。

> 🔒 **2026-08-14 v2.4.3 开发规则（花语文案焕新 + emoji 名称对齐 + 徽章奖励落叶 + 树洞三层回复 + 情绪日历空 bug 修复）**：本次为内容运营 + Bug 修复版本，**无新依赖 / 不改后端模型结构**，开发时遵守以下要点（在 v2.4.2 规则之上）：① **花种文案统一为花语**（`花语化`）——[constants.py](../../app/utils/constants.py) `DEFAULT_SHOP_ITEMS` 中花种 `description` 全改为「花语：……」格式，不再用「花中皇后」等直白标语；② **emoji 必须与名称对齐**（`emoji对齐`）——改 emoji 时同步检查名称是否匹配，不匹配则改名而非改 emoji：薰衣草用 🪻（非 💜）/ 🌾 对应「小麦」非「桂花」/ 🍃 对应「青叶」非「银杏」/ 🌸 对应「樱花」非「兰花」「梅花」（重复时删一留一并合并 GardenItem 引用）/ 🦩 对应「火烈鸟」非「白鹤」/ 🧥 对应「斗篷」非「蓑衣」；③ **改名迁移走 seed `RENAME_MAP`**（`改名迁移`）——在 [app/seed.py](../../app/seed.py) 维护 `RENAME_MAP = {旧名: 新名}` 字典，启动时按 name 查 ShopItem 批量 UPDATE，**改完名必须处理重复**（多条旧名指向同一新名时合并 GardenItem 引用 + 删除多余 ShopItem），避免 UNIQUE 冲突；④ **废弃物品删除**——`DEPRECATED_BADGES` 列表 + 先删 GardenItem 引用再删 ShopItem，否则外键残留；⑤ **徽章奖励落叶模式**（`BADGE_LEAF_REWARD`）——[energy_service.py](../../app/services/energy_service.py) `check_achievements` 返回 dict `{new_badges, new_leaves, leaves_balance}`，**用 `db.query(User).filter(...).update({User.leaves: User.leaves + reward})` 累加落叶**（禁止内存对象赋值，参考 project_memory 铁律），`leaves_balance` 用 `db.query(User.leaves).filter(...).scalar()` 取 DB 最新值（`expire_on_commit=False` 场景下 user.leaves 可能是旧值）；⑥ **router 透传落叶/徽章**——各 router（mood/diary/music/ai）在完成主业务后调用 `check_achievements(db, user)` 并把 `leaves_balance` / `new_badges` / `new_leaves` 放进响应体，前端 `userStore.updateResources({ leaves })` 同步余额 + `showToast` 提示徽章解锁；⑦ **Pydantic Out schema 同步**——`check_achievements` 返回的新字段若进 `response_model`，对应 Out schema 必须声明该字段（否则 FastAPI 静默过滤，前端拿到 undefined），本次 Mood/Diary/Music/AI 的 Out 已补 `new_badges` / `new_leaves` / `leaves_balance`（可为 None）；⑧ **Vue 模板空值用可选链**（`情绪日历空bug`）——`v-for` 渲染的数组元素属性访问加 `?.`，如 `cell.moodKeys?.length > 0` / `cell.moodInfos?.length`，避免空单元格抛 TypeError 导致整页空白；⑨ **3D 组件条件渲染**（`花田AI`）——`<FlowerField v-if="flowers.length > 0">`，没数据不渲染 Three.js 场景，省性能 + 避免显示无关 AI 生成内容；⑩ **AI 系统提示词三层结构**（`树洞三层回复`）——[ai_service.py](../../app/services/ai_service.py) `SYSTEM_PROMPT_TREEHOLE` 重写为「① 接住情绪（1 句，用自己的话点出）→ ② 安慰或新视角（1-2 句）→ ③ 具体可操作小建议或问题（1-2 句）」，禁止只复述用户原话或只说「嗯嗯确实」。关键词 `v2.4.3` / `花语化` / `emoji对齐` / `BADGE_LEAF_REWARD` / `落叶死锁解除` / `树洞三层回复` / `情绪日历空bug` / `花田AI` / `改名迁移` / `落叶花坊` / `花间客` 在 6 份文档中都要出现。

> 🔧 **2026-08-15 v2.4.3 补丁（首页滚动提示可点击）**：[HomeView.vue](../../frontend/src/views/HomeView.vue) Hero 底部滚动提示由 `pointer-events:none` 的 `<div>` 改为 `<button>` + `scrollToModules()`（`scrollIntoView({behavior:'smooth'})`）；**启示：视觉性引导元素若可被用户点击，应做成真实可交互元素并给 cursor:pointer + hover 反馈，不要用 pointer-events:none 假装不可点**。纯前端修复，需重新 `npm run build`。

> 🔒 **2026-08-15 v2.4.4 开发规则（情绪日历透明修复 + 旧版日记迁移 + mood_checkins 主键重建 + 头像图片上传 + 落叶花坊文案打磨）**：本次为 Bug 修复 + 功能增强版本，开发时遵守以下要点（在 v2.4.3 规则之上）：① **GSAP 动画不要设 `opacity:0` 作为入场初始态**（`情绪日历透明修复`）——[MoodCalendarView.vue](../../frontend/src/views/mood/MoodCalendarView.vue) GSAP 动画设置了 `opacity:0` 导致心情选择按钮几乎不可见，**启示：GSAP `from()` 动画初始态 `opacity:0` 在动画失败 / 元素 unmount 时会永久残留，导致元素不可见；用 `fromTo()` 显式声明起止态或 `clearProps` 清理**；② **旧版数据迁移自动填充占位文本**（`旧版日记迁移`）——旧版加密日记 `content` 字段为空（`content_encrypted` 是假占位符），`_migrate_legacy_columns()` 启动时检测 `content` 为空且 `content_encrypted` 非空的行自动填入提示文本「（这段日记来自旧版本，内容已无法读取）」；③ **SQLite 重建表必须显式定义 schema + `INSERT INTO ... SELECT *` 迁移数据**（`mood_checkins 主键重建`）——v2.4 用 `CREATE TABLE AS SELECT` 重建 `mood_checkins` 表丢失主键和自增，批量打卡 `db.flush()` 报 `NULL identity key`（500）；**正确流程：`CREATE TABLE _new (id INTEGER PRIMARY KEY AUTOINCREMENT, ...)` 显式定义 → `INSERT INTO _new SELECT * FROM old` → `DROP TABLE old` → `RENAME TABLE _new TO old` → `CREATE INDEX`**；④ **字段长度变更必须 model + schema 同步**（`avatar 字段长度`）——[User.avatar](../../app/models/user.py) `String(16)` → `String(255)`（存图片 URL 路径如 `/static/uploads/avatars/1_1234567890.jpg`），[ProfileUpdateIn](../../app/schemas/profile.py) `max_length=255` 同步，**`_migrate_legacy_columns()` 加 `ALTER TABLE users MODIFY COLUMN avatar VARCHAR(255)`**（SQLite 实际是重建表方式 ALTER）；⑤ **头像图片上传端点**（`头像图片上传`）——新增 `POST /api/profile/avatar` 端点，支持 JPG/PNG/WebP/GIF（≤2MB），存储到 `static/uploads/avatars/`（目录不存在 `os.makedirs(exist_ok=True)` 自动创建）；**前端用 `<input type="file" accept="image/*" capture>` 支持拍摄 / 相册选择**，FormData 上传，成功后更新 `userStore.avatar` 为返回的 URL 路径；前端渲染按是否以 `/static/uploads/` 开头判断是图片 URL 还是 emoji 字符；⑥ **落叶花坊花朵介绍移除「花语：」前缀**（`花朵介绍`）——[constants.py](../../app/utils/constants.py) `DEFAULT_SHOP_ITEMS` 花种 `description` 不再带「花语：」前缀，只保留完整花语；⑦ **徽章落叶奖励分级**（`徽章落叶分级`）——`BADGE_LEAF_REWARD` 由 `Final[int] = 10` 改为按 trigger 分级的字典 / 函数（streak_7=7, listen_10=10, pick_10=10, flower_10=10, chat_20=15, diary_30=20, 默认=10），[energy_service.py](../../app/services/energy_service.py) `check_achievements` 按徽章 trigger 查对应奖励值；⑧ **情绪日历使用指南改为罗素情绪环模型**（`情绪日历指南`）——介绍文案改为四象限说明；⑨ **岛上物件 emoji 🎁→🧳**（`岛上物件 emoji`）；⑩ **通知 emoji 统一 💛**（`通知 emoji 统一`）——漂流瓶回复通知的 emoji 统一为 💛。关键词 `v2.4.4` / `情绪日历透明修复` / `旧版日记迁移` / `mood_checkins 主键重建` / `avatar 字段长度` / `头像图片上传` / `花朵介绍` / `徽章落叶分级` / `情绪日历指南` / `岛上物件 emoji` / `通知 emoji 统一` 在 6 份文档中都要出现。

---

> 🔒 **2026-08-16 v2.4.5 开发规则（情绪日历 30 天趋势柱状图恢复 + 罗素情绪环显示修复 + 头像相册选择 + 通知空状态 emoji 统一）**：本次为 Bug 修复版本，开发时遵守以下要点（在 v2.4.4 规则之上）：① **GSAP 入场动画禁用 `opacity:0` / `scale:0` 初始态**（`罗素情绪环显示修复`）——[MoodCalendarView.vue](../../frontend/src/views/mood/MoodCalendarView.vue) 全部入场动画只保留位移动画（`y`）；v2.4.4 修「透明 bug」时只移除了心情按钮一处的 `opacity:0`，环模型区域的 `opacity:0` / `scale:0` 漏修导致动画中断（切后台 / 路由切换）时元素**永久卡在不可见状态**——**启示：同类 bug 修复必须全局搜索所有同类模式（`gsap.from` 带 opacity/scale），不能只修用户报告的那一处**；② **替换式重构保留旧视图并存**（`30天趋势柱状图恢复`）——v2.4.1 把 30 天趋势柱状图整体删除换成罗素情绪环，用户习惯打卡后看柱状趋势；本次恢复柱状图与环模型**并存**（柱高 = 当日平均分 1-5，柱色心情渐变，柱顶 emoji，未记录 3px 占位柱）——**启示：删除用户已习惯的视图前先确认，或直接并存**；③ **`capture` 属性只在「仅相机」场景使用**（`头像相册选择`）——`<input type="file" accept="image/*" capture="environment">` 在移动端**强制调起相机**跳过相册；通用图片上传**不要加 `capture`**，只留 `accept="image/*"` 即可弹出「拍照 / 从相册选择」选择框；④ **emoji 统一决策要覆盖所有状态**（`通知空状态emoji`）——v2.4.4「通知 emoji 统一 💛」只改了通知列表项，空状态 🌙 漏改——**启示：统一 emoji / 文案时全局搜索该 emoji 出现的所有位置（列表项 / 空状态 / 图标 / 标题）**。关键词 `v2.4.5` / `30天趋势柱状图恢复` / `罗素情绪环显示修复` / `头像相册选择` / `通知空状态emoji` 在 6 份文档中都要出现。

---

> 🔊 **2026-08-16 v2.4.6 开发规则（五音音频真实化）**：本次为历史遗留清理版本，开发时遵守以下要点（在 v2.4.5 规则之上）：① **音频是生成产物，不是手放资产**（`五音音频合成`）——`static/audio/*.wav` 的源是 [scripts/generate_audio.py](../../scripts/generate_audio.py)（Karplus-Strong 拨弦物理建模，五声调式），改音频先改脚本再重新生成（固定随机种子保证可复现），**不要手动替换/编辑 WAV 文件**；② **占位兜底只写合法容器**（`audio_url切wav`）——[seed.py](../../app/seed.py) `_ensure_placeholder_audio()` 现写最小合法 RIFF 静音 WAV（44 字节头 + 1 秒 8kHz 静音）而非假 MP3 帧——**启示：占位文件也必须是「能被播放器正常打开的合法文件」，假头骗 mime 检测只会造成「看似有文件实则播不出」的隐性 bug**；③ **音频格式切换要带数据迁移**——`audio_url` 存 DB 里，静态文件改名必须同步 `UPDATE`（[database.py](../../app/database.py) musics 表幂等迁移），否则老库仍指向已删除的 `.mp3` → 404；④ **沙箱环境下网络下载不可用时，本地合成是合法 fallback**——Karplus-Strong 纯标准库实现（random/struct/wave），零依赖零版权，比「下载失败就搁置」好。关键词 `v2.4.6` / `五音音频合成` / `Karplus-Strong` / `audio_url切wav` 在 6 份文档中都要出现。

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

### 1.4 前端框架选型（2026-07-19 v2.0 重构后）

> **2026-07-19 v2.0 全站 Vue 3 重构后**：本节规则已更新。前台 13 个页面已迁移到 Vue 3 SPA，**不再**使用原生 HTML/CSS/JS。后台 `/admin/*` 仍保留 Jinja2 SSR（有意为之的独立隔离）。

**前台 Vue 3 SPA**（[`frontend/src/`](../../frontend/src/)）：
- ✅ Vue 3 `<script setup>` + Vite 5 + Vue Router 4 + Pinia + Tailwind CSS 3.4 + GSAP + @vueuse/motion + Three.js + axios
- ❌ 不要再引入 React / Angular / Svelte（已选定 Vue 3，不再讨论）
- ❌ 不要在 Vue SPA 之外另起前端框架（后台 Jinja2 SSR 是有意为之的独立隔离）

**后台 Jinja2 SSR**（[`templates/admin/`](../../templates/admin/)）：
- ✅ 原生 HTML + CSS + JS（继承 `admin/_base.html`）
- ❌ 不引 React / Vue / Tailwind / Vite / webpack
- 加第三方库前先问：「不用它能写吗？」

> 详见 [§1.9 前端开发模式](#19-前端开发模式vue-3-spa2026-07-19-v20-加) / [HANDOFF §5.8](../../HANDOFF.md) 前端选型决策。

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

> 🔒 **2026-07-19 v2.0 Vue 3 重构后特殊规则（6 份文档同步）**：
> 改 Vue 3 前端代码（[`frontend/src/`](../../frontend/src/)）+ 后端 SPA fallback（[app/main.py](../../app/main.py)）= **同一 commit 同步更新 6 份文档**（README / HANDOFF / PROJECT_STATE / ARCHITECTURE / DEPLOYMENT / DEVELOPMENT）。关键词 `Vue 3` / `Vite` / `SPA fallback` / `frontend/` 在 6 份文档中都要出现。**改代码不改文档 = 改了一半。**
> 同步点速查：[README §9](../../README.md) / [HANDOFF §12](../../HANDOFF.md) / [PROJECT_STATE §8](../PROJECT_STATE.md) / [ARCHITECTURE §7.7](../ARCHITECTURE.md) / [DEPLOYMENT 顶部](../DEPLOYMENT.md) / 本节。
> 完整规则 + 5 项 pre-commit checklist：[HANDOFF §12](../../HANDOFF.md) / [PROJECT_STATE §8.1](../PROJECT_STATE.md) v2.0 特殊说明。

#### 1.8.1 改完自动 push（不延迟）
- `git commit` 完**立即** `git push origin main`
- 不允许「先 commit 一会儿一起推」/「明天推」/「攒一周推一次」
- 完整规则：[HANDOFF §12.6](../../HANDOFF.md)

#### 1.8.2 Commit 标题 / 脚本进度用 Conventional Commits
- 格式：`<type>(<scope>): <subject>`（subject ≤ 50 字符）
- type 9 个：`feat` / `fix` / `refactor` / `docs` / `style` / `test` / `chore` / `perf` / `revert`
- 项目 scope：`auth` / `diary` / `mood` / `music` / `energy` / `garden` / `admin` / `templates` / `static` / `docs` / `deps` / `scripts` …
- v2.0 起新增 scope：`frontend` / `vue` / `vite` / `tailwind` / `gsap`（[`frontend/`](../../frontend/) 相关改动用）
- 脚本（`push-to-github.ps1`）的进度输出**也**用 `type(scope)` 标题
- 完整规则 + 示例：[HANDOFF §12.7](../../HANDOFF.md)

---

## 1.9 前端开发模式（Vue 3 SPA，2026-07-19 v2.0 加，v2.0.1 端口策略调整，v2.3.2 默认生产模式）

> 2026-07-19 v2.0 全站 Vue 3 重构后，前台 13 个页面迁移到 Vue 3 SPA。本节讲**怎么开发前端**，不是讲铁律。架构看 [ARCHITECTURE §1.1](../ARCHITECTURE.md)，部署看 [DEPLOYMENT 前端构建](../DEPLOYMENT.md)。

> 2026-07-19 v2.0.1 端口策略调整：开发模式 Vite 占 :5000（用户入口）+ FastAPI 退到 :5001（API），**用户始终访问 :5000**。理由见 [HANDOFF §6.16](../../HANDOFF.md)（FastAPI 反代 Vite 内部路径含 null 字节转义 + 冒号失败）。

> 🔒 **2026-07-25 v2.2.2 start.py 默认应用模式**（⚠️ **已被 v2.3.2 回滚，保留仅为历史记录**）：`python start.py`（无参数）默认行为变更——**默认走应用/开发模式**（Vite :5000 HMR + FastAPI :5001 API 一起起），自动检测 `frontend/node_modules` 不存在则 `npm install`（约 7 分钟，仅首次）。**v2.2.1 的「dist 未构建 → 自动 build 后走生产模式」逻辑已移除**（应用模式用 Vite dev server 不需要构建产物）。生产模式需显式 `python start.py --prod`（FastAPI :5000 单进程，需 `static/dist/` 已构建，未构建报错退出）。`--dev` 改为兼容别名（等同默认行为，向后兼容）。关键词 `--prod` / `默认应用模式` / `自动 npm install` / `前后端一起起` 在 6 份文档中都要出现。

> 🔒 **2026-07-28 v2.3.2 start.py 默认生产模式 + 自动构建简化**（⭐ **当前最新行为，回滚 v2.2.2**）：`python start.py`（无参数）默认行为**再次变更**——**默认走生产模式**（FastAPI :5000 单进程，前后端不再一起起），需 `static/dist/` 已构建（不存在则自动 `npm install + npm run build`）。**`dist 存在检测`**——仅检测 `static/dist/index.html` 存在性；**`自动构建`**：dist 不存在时自动 `npm install + npm run build`（需 Node.js 18+）。**开发需显式 `python start.py --dev`**（Vite :5000 HMR + FastAPI :5001 API，前后端一起起的「应用模式」）。`--prod` 改为兼容别名（默认就是生产模式，加不加效果一样）。理由：服务器端口代理已配好 :5000 不能动，应用模式会让 Vite 占 :5000 破坏代理。关键词 `默认生产模式` / `dist 存在检测` / `自动构建` / `--dev` / `应用模式` / `v2.3.2` 在 6 份文档中都要出现。

### 1.9.1 启动开发模式（Vite dev server :5000 + FastAPI :5001，v2.3.2 起需显式 `--dev`）

#### 方式 A：一键启动（推荐 ⭐）

```bash
cd c:\Users\Administrator\Desktop\webwrold
python start.py --dev    # 应用/开发模式（Vite :5000 + FastAPI :5001，前后端一起起）
                         # v2.3.2 起：默认行为改为生产模式，开发必须显式加 --dev
                         # 自动检测 frontend/node_modules 不存在 → npm install（约 7 分钟，仅首次）
```

[start.py](../../start.py) 在 dev 模式会：
1. 检测 `frontend/node_modules` 不存在 → 自动 `npm install`（仅首次，约 7 分钟）
2. 后台启动 Vite dev server（监听 :5000）
3. 设置环境变量 `QI_PORT=5001` 启动 FastAPI（监听 :5001）
4. `python start.py status` 同时显示两个进程状态

#### 方式 B：手动两终端

```bash
# 终端 1：启动 Vite dev server（占 :5000，用户入口）
cd c:\Users\Administrator\Desktop\webwrold\frontend
npm install                    # 首次：含 three.js 大包，约 7 分钟
npm run dev                    # http://127.0.0.1:5000

# 终端 2：启动 FastAPI（退到 :5001，API 后端）
cd c:\Users\Administrator\Desktop\webwrold
set QI_PORT=5001
python start.py fg             # http://127.0.0.1:5001（fg 前台，关终端即停；或用 python start.py 后台双进程）
```

浏览器访问 **http://127.0.0.1:5000/**（即 Vite，不是 :5001）。
- Vite 提供 HMR 热更新（改 `.vue` / `.js` / `.css` 浏览器自动刷新，**保留组件状态**）
- 所有 `/api/*`、`/static/*`、`/admin/*`、`/docs`、`/openapi.json` 请求自动 proxy 到 FastAPI :5001
- 改前端代码 → 浏览器秒级热更新；改后端代码 → 重启 `python start.py restart`（注意是 :5001 的进程）

> ⚠️ Vite host 显式设 `127.0.0.1`（不写 `localhost`）避免 IPv6 `[::1]` 问题，详见 [HANDOFF §6.12](../../HANDOFF.md) / [§3.15](#315-vite-ipv6-localhost-连不上)。
>
> ⚠️ Vite `strictPort: true` 防止 :5000 被占用时自动跳到 :5001（会和 FastAPI 撞）。若启动报 `Port 5000 is in use` → 先 `python start.py stop` 关掉 FastAPI，或检查是否有别的 Vite 实例残留。
>
> ⚠️ **dev 模式 :5000 是 Vite，不是 FastAPI**：若用 `curl http://127.0.0.1:5000/api/...` 测试 API，会经 Vite proxy 转发到 :5001 的 FastAPI。直接打 FastAPI 用 :5001（如 `curl http://127.0.0.1:5001/docs` 看 Swagger）。
>
> ⚠️ **v2.3.2 行为变更**（回滚 v2.2.2）：`python start.py`（无参数）默认走**生产模式**（FastAPI :5000 单进程，需 dist 已构建，不存在则**`自动构建`** `npm install + npm run build`，**`dist 存在检测`** 仅看 `static/dist/index.html` 是否存在）。开发需显式 `python start.py --dev`（Vite :5000 + FastAPI :5001，前后端一起起的「应用模式」）。`--prod` 改为兼容别名（默认就是生产模式）。

### 1.9.2 开发模式 vs 生产模式（v2.3.2 起默认生产模式）

| 维度 | 生产模式（默认，v2.3.2 起） | 应用模式（--dev） |
|---|---|---|
| 启动命令 | `python start.py`（默认）或 `python start.py --prod`（兼容别名） | `python start.py --dev` |
| 浏览器访问 | `http://127.0.0.1:5000/`（FastAPI） | `http://127.0.0.1:5000/`（Vite） |
| 谁服务 :5000 | FastAPI（服务 `static/dist/index.html` + SPA fallback） | Vite dev server（HMR + 源码） |
| FastAPI 监听 | :5000（从 .env 读 QI_PORT） | :5001（由 start.py 设 QI_PORT=5001） |
| Vite 是否运行 | ❌ 否（dist 已构建，不需要 Vite） | ✅ 是 |
| dist 不存在时 | **`自动构建`** `npm install + npm run build`（**`dist 存在检测`**） | 自动 `npm install`（不构建 dist，应用模式用 Vite dev server） |
| 改 .vue 后 | 必须重新 `python start.py build` 或 `npm run build` | 浏览器自动热更新 |
| 适用场景 | 部署上线 / 真机测试 / 服务器（端口代理 :5000 指向 FastAPI） | 日常开发（本地，端口代理 :5000 指向 Vite） |

### 1.9.3 dev proxy 配置（[frontend/vite.config.js](../../frontend/vite.config.js)）

Vite dev server 把以下路径 proxy 到 FastAPI :5001，**无跨域**：

| 前端请求路径 | proxy 到 | 用途 |
|---|---|---|
| `/api/*` | `http://127.0.0.1:5001/api/*` | 所有 JSON API（axios `baseURL=/api`） |
| `/static/*` | `http://127.0.0.1:5001/static/*` | 静态资源（音频、图片、旧 CSS/JS） |
| `/admin/*` | `http://127.0.0.1:5001/admin/*` | 秘密后台 SSR（Jinja2） |
| `/docs` | `http://127.0.0.1:5001/docs` | FastAPI Swagger UI（开发调试用） |
| `/openapi.json` | `http://127.0.0.1:5001/openapi.json` | FastAPI OpenAPI schema（Swagger 依赖） |

> axios 实例（[frontend/src/api/index.js](../../frontend/src/api/index.js)）配置 `baseURL='/api'` + `withCredentials=true`，cookie 自动带，401 自动跳 `/login`。

> **dev proxy 不要改**：5 项配置（`/api` / `/static` / `/admin` / `/docs` / `/openapi.json` + host=127.0.0.1）是项目最稳定的部分之一。改了必然破东西。

### 1.9.4 文件结构（[`frontend/src/`](../../frontend/src/)）

```
frontend/
├── package.json              ← 依赖 + 脚本（npm install / dev / build）
├── vite.config.js            ← Vite 配置（dev proxy + build outDir + base）
├── tailwind.config.js        ← Tailwind 色彩 token + 动画
├── postcss.config.js
├── index.html                ← Vite 入口 HTML（<div id="app">）
└── src/
    ├── main.js               ← Vue 入口（createApp + Pinia + Router + MotionPlugin）
    ├── App.vue               ← 根组件（AppLayout + router-view + transition）
    ├── router/
    │   └── index.js          ← 13 条路由 + requiresAuth 守卫 + 404 catch-all
    ├── stores/
    │   └── user.js           ← Pinia user store（cookie session 模式，不存 token）
    ├── api/
    │   └── index.js          ← axios 实例（baseURL=/api，withCredentials，401 拦截）
    ├── components/
    │   ├── AppLayout.vue     ← 桌面顶部导航 + 移动端底部 tabbar（768px 断点）
    │   ├── FlowerField.vue   ← 3D 花田场景 v2（立体花瓣 BufferGeometry + MeshPhysicalMaterial + Bloom + OrbitControls + raycaster；v2.0.1 加，v2.2 PBR 升级）
    │   ├── AmbientBackground.vue  ← 全局氛围背景 v2（CSS 雾气 + Canvas2D 柔光 sprite + Three.js 双层粒子 + 鼠标排斥 + 滚动视差 + 轻量 Bloom；v2.1 加，v2.2 升级）
    │   ├── HeroScene.vue     ← 首页 Hero 区 3D 浮岛雾海 v2（LatheGeometry 浮岛 + 递归樱花树 + PBR 水面 shader + Bloom + OrbitControls + raycaster；v2.1 加，v2.2 PBR 升级）
    │   ├── AudioVisualizer.vue  ← 音波可视化 v2（4 模式：wave/mirror/radial/particles + 节拍检测 + 频响颜色 + 点击切换；v2.1 加，v2.2 升级）
    │   ├── SceneHint.vue     ← 3D 场景交互指引横幅（拖拽旋转 · 滚轮缩放 · 点击交互，3 秒淡出；v2.2 加）
    │   └── SceneControls.vue  ← 3D 场景视图控制工具栏（重置视角 / 自动旋转开关；v2.2 加）
    ├── utils/
    │   ├── visual.js         ← 视觉能力检测（hasWebGL / prefersReducedMotion / smartRAF；v2.1 加）
    │   └── three-helpers.js  ← Three.js PBR 工具集（createRenderer / createEnvironment / createPostProcessing / createOrbitControls / disposeObject3D 等 9 函数；v2.2 加）
    ├── views/                ← 【一个视图一个 .vue 文件】
    │   ├── HomeView.vue
    │   ├── NotFoundView.vue
    │   ├── auth/
    │   │   ├── LoginView.vue
    │   │   └── RegisterView.vue
    │   ├── music/
    │   │   ├── MusicListView.vue
    │   │   ├── MusicDetailView.vue
    │   │   └── WesternMusicListView.vue   ← v2.3 加：古琴弹西洋曲谱子菜单 /music/western
    │   ├── diary/
    │   │   ├── DiaryListView.vue
    │   │   ├── DiaryWriteView.vue        ← v2.3 加：visibility（仅自己/漂流瓶/朋友）+ category 下拉
    │   │   └── PickBottleView.vue
    │   ├── mood/
    │   │   └── MoodCalendarView.vue     ← v2.3 修复：mood_emoji 统一为 emoji 字符
    │   ├── ai/
    │   │   └── AIChatView.vue            ← v2.3 改：SVG 灯笼图标 + textarea + 文件式聊天历史
    │   ├── garden/
    │   │   ├── GardenView.vue            ← v2.3 加：花田生长网格（种花/浇水按钮）
    │   │   └── ShopView.vue              ← v2.3 加：双资源条（dew/leaves）显示
    │   ├── healing/                       ← v2.3 加：五音疗愈盘独立顶级模块
    │   │   └── HealingView.vue           ←   /healing 路由，原 /music 重定向到此
    │   └── profile/                       ← v2.3 加：个人主页
    │       └── ProfileView.vue           ←   /profile 路由，requiresAuth 守卫
    └── assets/
        └── styles/
            └── main.css      ← Tailwind 入口 + 系统字体栈（无 Google Fonts）
```

**约定**：
- **一个视图一个 `.vue` 文件**：视图文件名 = 路由名 + `View.vue`（如 `/diary/write` → `DiaryWriteView.vue`）
- 视图按模块分目录：`auth/` / `music/` / `diary/` / `mood/` / `ai/` / `garden/`
- 复用组件放 `components/`（如 `AppLayout.vue`）；视图不放 `components/`
- 路由表 `router/index.js` 用 `meta.requiresAuth: true` 标记需登录的视图，router 守卫统一处理 401 跳转

### 1.9.5 加新视图（Vue 3 SPA 模式，替代旧 §2.1 Jinja2 模式）

> **2026-07-19 v2.0 后**：加新前台页面走 Vue 3 SPA 模式（本节），**不再**走 §2.1 Jinja2 模式。§2.1 仅适用于 `/admin/*` 后台 SSR 页面。

1. 在 `frontend/src/views/<module>/` 加 `XxxView.vue`（一个视图一个文件）
2. 在 [frontend/src/router/index.js](../../frontend/src/router/index.js) 加路由：
   ```js
   {
     path: '/xxx',
     name: 'xxx',
     component: () => import('@/views/<module>/XxxView.vue'),
     meta: { requiresAuth: true }   // 或 false
   }
   ```
3. 视图里用 axios 调 API：
   ```vue
   <script setup>
   import { ref, onMounted } from 'vue'
   import api from '@/api'
   import { useUserStore } from '@/stores/user'

   const userStore = useUserStore()
   const data = ref(null)

   onMounted(async () => {
     const res = await api.get('/xxx')   // baseURL=/api 自动拼
     data.value = res.data
   })
   </script>

   <template>
     <div>{{ data }}</div>
   </template>
   ```
4. 同步更新 [README.md](../../README.md) §2 目录树 + [PROJECT_STATE.md](../PROJECT_STATE.md) §3.3 前端文件列表（Iron Rule）

> **后台页面**仍走 §2.1 Jinja2 模式（继承 `admin/_base.html`），不要混用。

#### 1.9.5.1 异步加载重组件（defineAsyncComponent 示例，2026-07-19 v2.0.1 加）

> **场景**：某个视图依赖体积大的库（如 Three.js ~600KB / pdf.js / monaco-editor），不想让它进首屏包。用 `defineAsyncComponent` 按需加载，**首屏只加载主 chunk，重组件单独成 chunk 在访问时才拉**。

**真实案例**：[GardenView.vue](../../frontend/src/views/garden/GardenView.vue) 顶部嵌入了 3D 花田场景 [FlowerField.vue](../../frontend/src/components/FlowerField.vue)，后者动态 `import('three')` 加载 Three.js。通过 `defineAsyncComponent` 把 FlowerField.vue 整体异步化，访问 `/garden` 时才拉 Three.js chunk。

```vue
<!-- GardenView.vue -->
<script setup>
import { defineAsyncComponent } from 'vue'

// 异步加载花田组件（首屏不拉 three.js，访问 /garden 时才按需加载）
const FlowerField = defineAsyncComponent(() =>
  import('@/components/FlowerField.vue')
)
</script>

<template>
  <!-- 用法和普通组件一样 -->
  <FlowerField :flower-count="60" height="380px" />
</template>
```

**配套：vite.config.js 的 manualChunks**（[frontend/vite.config.js](../../frontend/vite.config.js)）：
```js
build: {
  rollupOptions: {
    output: {
      manualChunks: {
        'vue-vendor': ['vue', 'vue-router', 'pinia'],
        'gsap-vendor': ['gsap'],
        'three-vendor': ['three'],   // Three.js 单独 chunk
      },
    },
  },
}
```

**加载占位**：异步组件加载中默认啥也不显示，建议在组件内部用 `isLoading` ref + `<div v-if="isLoading">` 显示占位（FlowerField.vue 显示「🌿 花田正在生长…」）。

**何时用 / 何时不用**：
- ✅ 用：3D / 大图表 / 编辑器 / PDF 渲染等重组件，只在特定路由用
- ❌ 不用：通用组件（按钮 / 卡片 / 表单 / Toast），这些就该进首屏包

### 1.9.6 常用 npm 脚本

| 命令 | 用途 |
|---|---|
| `npm install` | 装依赖（首次约 7 分钟，含 three.js 大包） |
| `npm run dev` | 启动 Vite dev server **:5000**（HMR + proxy → FastAPI :5001） |
| `npm run build` | 构建生产产物到 `../static/dist/`（v2.0.1 起也可用 `python start.py build` 一键） |
| `npm run preview` | 本地预览 build 产物（不常用，生产走 FastAPI SPA fallback） |

> **start.py 子命令对照**（v2.3.2 起，回滚 v2.2.2）：`python start.py`（**默认生产模式**：FastAPI :5000 单进程，**`dist 存在检测`** → 不存在则**`自动构建`** `npm install + npm run build`）/ `python start.py --prod`（兼容别名，默认就是生产模式，加不加效果一样）/ `python start.py --dev`（**应用模式**：Vite :5000 HMR + FastAPI :5001 API，前后端一起起，本地开发用，自动 `npm install` 当 `frontend/node_modules` 不存在）/ `python start.py build`（仅构建前端到 `static/dist/`，不启动服务）/ `python start.py fg`（前台运行，systemd 用，默认生产模式，加 `--dev` 切应用模式）/ `python start.py status`（查 FastAPI / Vite 进程状态）/ `python start.py stop`（停进程）/ `python start.py restart`（重启，默认生产模式）。

### 1.9.7 调试技巧

- **Vue DevTools**：浏览器装 [Vue.js devtools](https://devtools.vuejs.org/) 扩展，看组件树 / Pinia state / Router
- **Vite 启动慢 / HMR 不生效**：检查 [frontend/vite.config.js](../../frontend/vite.config.js) 的 `host: '127.0.0.1'`（不要写 `localhost`，IPv6 `[::1]` 会连不上，详见 [HANDOFF §6.12](../../HANDOFF.md)）
- **API 401 不跳登录**：检查 [frontend/src/api/index.js](../../frontend/src/api/index.js) 的 axios 拦截器
- **404 不显示**：检查 `router/index.js` 末尾的 `/:pathMatch(.*)*` catch-all 路由
- **dist 未构建提示页**：访问 :5000 看到「dist 未构建」→ `python start.py build` 或 `cd frontend && npm run build`（v2.3.2 起默认生产模式 `python start.py` 也会自动构建）
- **dev 模式 :5000 是 Vite，不是 FastAPI**（v2.0.1 加）：应用模式（`--dev`）访问 :5000 是 Vite dev server（HMR + 源码），API 请求经 Vite proxy 转发到 :5001 的 FastAPI。要看 FastAPI Swagger 文档直接访问 :5001（`http://127.0.0.1:5001/docs`）。**生产模式（默认）:5000 才是 FastAPI**。详见 [§1.9.1](#191-启动开发模式vite-dev-server-5000--fastapi-5001v232-起需显式---dev)。
- **端口 5000 被占用**：`python start.py stop` 停掉旧进程；或检查是否同时跑了 Vite 和 FastAPI（应用模式 Vite 占 :5000，如果 FastAPI 没改成 :5001 就会撞）。Vite `strictPort: true` 会直接报错不自动跳端口。
- **3D 花田不显示**：访问 `/garden` 看到「🌿 花田正在生长…」一直转 → 打开 DevTools Console 看是不是 `Failed to fetch dynamically imported module`（three-vendor chunk 没加载到，检查 `static/dist/assets/three-vendor-*.js` 是否存在 → 不存在重新 `npm run build`）
- **Safari 主页 3D 不渲染**（v2.3.3 加）：iOS Safari 切后台→前台后 3D 黑屏 → 检查 `webglcontextlost` / `webglcontextrestored` 监听是否挂载（详见 [§1.9.8 Safari / iOS 兼容](#safari--ios-兼容v233-加) / [HANDOFF §6.24](../../HANDOFF.md)）；Safari 直接降级 SVG → 检查 `hasWebGL()` 是否误判（v2.3.3 **hasWebGL 重写** 已修复，区分 WebGL1/2）
- **Safari emoji 与 Chrome 不一致**（v2.3.3 加）：检查是否用了裸 emoji 字符 → 改用 `<EmojiIcon name="..." />`（详见 [§1.9.9](#19-emoji-组件用法emojiiconvuev233-加2026-07-30)）
- **proxy 没生效**：检查 [vite.config.js](../../frontend/vite.config.js) 的 `server.proxy` 是否包含 `/api`、`/static`、`/admin`、`/docs`、`/openapi.json`（v2.0.1 起多了 `/docs` 和 `/openapi.json`，方便开发时直接在 :5000 访问 Swagger）

### 1.9.8 视觉组件开发指南（v2.1 加，2026-07-20；v2.2 PBR 升级，2026-07-20）

> 适用范围：所有用 Three.js / Canvas2D / Web Audio API 的视觉组件。当前已有 7 个：[FlowerField.vue](../../frontend/src/components/FlowerField.vue) / [AmbientBackground.vue](../../frontend/src/components/AmbientBackground.vue) / [HeroScene.vue](../../frontend/src/components/HeroScene.vue) / [AudioVisualizer.vue](../../frontend/src/components/AudioVisualizer.vue) / [SceneHint.vue](../../frontend/src/components/SceneHint.vue) / [SceneControls.vue](../../frontend/src/components/SceneControls.vue) + [utils/three-helpers.js](../../frontend/src/utils/three-helpers.js) PBR 工具集。

#### v2.2 新增 3 大铁律（在 v2.1 4 大铁律之上）

**⑤ PBR 渲染管线必须用 `three-helpers.js` 工具函数**（v2.2 加）
```js
// ❌ 不要自己 new THREE.WebGLRenderer / new THREE.PMREMGenerator / new EffectComposer
// ✅ 用 three-helpers.js 集中导出的函数
import { createRenderer, createEnvironment, createPostProcessing, createOrbitControls } from '@/utils/three-helpers'

const renderer = createRenderer(canvas)              // ACESFilmic + SRGB + PCFSoft + dpr≤2
const envMap = createEnvironment(renderer)           // RoomEnvironment + PMREM
scene.environment = envMap
const composer = createPostProcessing(renderer, scene, camera)  // EffectComposer + UnrealBloomPass
const controls = createOrbitControls(camera, canvas) // 阻尼 + 极角约束 + 禁用 pan + 自动旋转
```
理由：v2.1 各组件自己写 `new THREE.WebGLRenderer({ canvas, antialias: true })` + `renderer.toneMapping = ...`，4 个组件 4 套配置不一致；v2.2 抽到 [utils/three-helpers.js](../../frontend/src/utils/three-helpers.js) 统一管理，新组件直接调函数即可。

**⑥ 3D 场景必须有 `SceneHint.vue` 交互指引 + `SceneControls.vue` 视图控制**（v2.2 加）
```vue
<template>
  <div class="scene-root">
    <div ref="mount" class="scene-canvas" />
    <SceneHint />                       <!-- ← 顶部交互指引横幅，3 秒淡出 -->
    <SceneControls                      <!-- ← 视图控制工具栏 -->
      @reset-view="resetView"
      @toggle-auto-rotate="toggleAutoRotate"
    />
  </div>
</template>
```
理由：v2.1 的 3D 场景用户不知道可以拖拽 / 缩放 / 点击，以为是静态背景；v2.2 强制要求所有 3D 场景挂 `SceneHint` + `SceneControls`，让用户**第一眼就知道怎么交互**。

**⑦ 3D 场景必须支持 `OrbitControls` 拖拽旋转 + 滚轮缩放 + `raycaster` 点击拾取**（v2.2 加）
```js
import { createOrbitControls } from '@/utils/three-helpers'
const controls = createOrbitControls(camera, canvas)  // 阻尼 + 极角约束 + 禁用 pan + 自动旋转

// raycaster 点击拾取
const raycaster = new THREE.Raycaster()
const onMouseClick = (e) => {
  const rect = canvas.getBoundingClientRect()
  const mouse = new THREE.Vector2(
    ((e.clientX - rect.left) / rect.width) * 2 - 1,
    -((e.clientY - rect.top) / rect.height) * 2 + 1
  )
  raycaster.setFromCamera(mouse, camera)
  const hits = raycaster.intersectObjects(clickableObjects.value)
  if (hits.length > 0) handleClick(hits[0].object)
}
```
理由：v2.1 的 3D 场景只能看不能交互；v2.2 要求所有 3D 场景统一 `OrbitControls` + `raycaster`，让 3D 场景「可交互」而非「只能看」。

#### 4 大铁律（缺任何一个都会在长时间使用或多视图切换后出问题）

**① `createMediaElementSource` 一次性守卫**（仅 AudioVisualizer 类组件）
```js
// AudioVisualizer.vue
let sourceNode = null
const connect = (audioEl) => {
  if (sourceNode) return                    // ← 已连接则直接返回
  sourceNode = audioCtx.createMediaElementSource(audioEl)
  sourceNode.connect(analyser)
  analyser.connect(audioCtx.destination)
}
defineExpose({ connect })
```
父组件用 ref 标记是否已连接，首次播放时调 `connect(audioEl)`，后续切歌不重连：
```js
// MusicDetailView.vue
const visualizerConnected = ref(false)
const playIndex = (idx) => {
  // ...
  if (!visualizerConnected.value && visualizerRef.value) {
    visualizerRef.value.connect(audioEl)
    visualizerConnected.value = true
  }
  audioEl.load(); audioEl.play()
}
```

**② Three.js 对象用 `shallowRef` 而非 `ref`**
```js
import { shallowRef } from 'vue'
const three = shallowRef(null)              // ← 而不是 ref(null)
three.value = { scene, camera, renderer, clock, rafId }
// 访问字段用 three.value?.scene，不要解构
```
理由：`ref` 对 object 会递归代理每一层属性，Three.js 的 Scene/Object3D 内部有大量私有字段 + 数组 + Map，递归代理既慢又可能干扰 Three.js 自己的内部逻辑。

**③ rAF 必须走 `smartRAF` 而非 `requestAnimationFrame`**
```js
import { smartRAF } from '@/utils/visual'
const loop = () => {
  three.value?.renderer.render(three.value.scene, three.value.camera)
  three.value.rafId = smartRAF(loop)        // ← 而不是 requestAnimationFrame(loop)
}
```
理由：`requestAnimationFrame` 在标签页隐藏时浏览器虽降为 1 fps 但仍执行渲染循环，GPU 不释放；`smartRAF` 在 `document.hidden` 时主动 `cancelAnimationFrame`，可见时自动恢复。

**④ `onBeforeUnmount` 必须完整释放**
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
理由：Vue 卸载组件时 Three.js 的 renderer / geometry / material / event listener / ResizeObserver 不会被 GC 自动回收，5 次切走后浏览器报 `Too many active WebGL contexts` 黑屏。

#### 三层渐进增强实现模板

```vue
<script setup>
import { ref, shallowRef, onMounted, onBeforeUnmount } from 'vue'
import { hasWebGL, prefersReducedMotion, isMobile, isLowPower, shouldUseThreeJS, shouldUseCanvas, smartRAF } from '@/utils/visual'

const canvas2d = ref(null)                  // Layer 2: Canvas2D
const three = shallowRef(null)              // Layer 3: Three.js

onMounted(async () => {
  // Layer 2: Canvas2D（reduced-motion 关闭）
  if (shouldUseCanvas()) initCanvas2D()
  // Layer 3: Three.js（WebGL + 非 reduced-motion + 非低性能）
  if (shouldUseThreeJS()) {
    try {
      const THREE = await import('three')   // 异步加载，不进首屏包
      initThree(THREE)
    } catch (e) {
      console.warn('[Visual] Three.js init failed, falling back to Canvas2D/CSS', e)
    }
  }
})

onBeforeUnmount(() => { /* 见铁律 ④ */ })
</script>

<template>
  <div class="visual-root">
    <!-- Layer 1: CSS 永远启用 -->
    <div class="css-layer" />
    <!-- Layer 2: Canvas2D -->
    <canvas v-if="shouldUseCanvas()" ref="canvas2d" />
    <!-- Layer 3: Three.js -->
    <div v-if="shouldUseThreeJS()" ref="threeMount" />
    <!-- 降级静态层（无 WebGL / reduced-motion） -->
    <svg v-if="!shouldUseThreeJS()" class="fallback-svg" viewBox="0 0 800 480">
      <!-- 静态插画 -->
    </svg>
  </div>
</template>
```

#### 视觉组件开发流程

1. **判断需要哪层**：纯装饰背景 → CSS + Canvas2D 即可；要景深 / 光影 / 实例化 → Three.js；要音频可视化 → Web Audio API + Canvas2D
2. **复制模板**：从 [AmbientBackground.vue](../../frontend/src/components/AmbientBackground.vue)（三层全有）或 [HeroScene.vue](../../frontend/src/components/HeroScene.vue)（Three.js + SVG 降级）开始改
3. **配色一致性**：用治愈系 5 色（藕粉 `#E8B8C5` / 淡黄 `#E8D5A8` / 青绿 `#A8C5A0` / 雾蓝 `#A8B8C5` / 纯白 `#FAF6F2`）+ 米白 `#F9F6F0` 背景，与 [tailwind.config.js](../../frontend/tailwind.config.js) token 一致
4. **性能保护**：移动端粒子数减半 + `dpr` ≤ 1.5 + 几何精度降档（Lathe/Cylinder/Icosahedron 段数与细分降低、花瓣网格 5×8→4×6、地面圆 64→32、AudioVisualizer 柱数减半）；`defineAsyncComponent` 异步加载 Three.js
5. **降级路径**：每个 Three.js 组件必须有 CSS / SVG 静态降级；reduced-motion 用户不能看到闪烁 / 摇晃内容
6. **验证清单**：
   - 桌面 Chrome 默认 motion：3D / Canvas2D 正常渲染
   - DevTools → Rendering → `prefers-reduced-motion: reduce`：降级为静态
   - 移动端 Safari：粒子数减半、dpr ≤ 1.5、几何精度降档（顶点数大幅减少）
   - 切走标签页 30s 后回切：GPU 占用应归零（smartRAF 生效）
   - 在该组件所在视图和其他 Three.js 视图间来回切 5 次：无 `Too many active WebGL contexts` 警告
   - DevTools 模拟 iPhone 16（390×844）：topbar + 底部 tabbar + 「更多」抽屉 + 各视图差异化布局生效
7. **文档同步**：新增视觉组件 = **同一 commit 同步更新 6 份文档**（详见 [HANDOFF §12](../../HANDOFF.md)）

#### 视觉能力检测 API（[utils/visual.js](../../frontend/src/utils/visual.js)）

| 函数 | 返回 | 说明 |
|---|---|---|
| `hasWebGL()` | boolean | 当前浏览器是否支持 WebGL（v2.3.3 **hasWebGL 重写**：区分 WebGL1/2 + 检测扩展 + max texture size，先试 WebGL2 失败再试 WebGL1，避免老 Safari 误判） |
| `getWebGLCaps()` | object \| null | **v2.3.3 加**：返回 WebGL 能力对象（`isWebGL2` / `maxTextureSize` / `hasHalfFloatExt` 等）；`hasHalfFloatExt` 检测 `EXT_color_buffer_half_float` 扩展，老 iOS 缺该扩展时需关闭 PMREM + Bloom |
| `isSafari()` | boolean | **v2.3.3 加**：UA 是否含 Safari 且不含 Chrome/Edge（区分 Safari 与 Chrome 的 Safari UA 伪装） |
| `isIOS()` | boolean | **v2.3.3 加**：UA 是否含 iPhone/iPad/iPod（iPadOS 13+ 用 `navigator.platform` 含 Mac + `navigator.maxTouchPoints > 1` 兜底） |
| `prefersReducedMotion()` | boolean | 用户是否设置 `prefers-reduced-motion: reduce` |
| `isMobile()` | boolean | 视口宽度 < 768px 或 UA 含 Mobile |
| `isLowPower()` | boolean | `navigator.hardwareConcurrency` ≤ 4 或 `deviceMemory` ≤ 4 |
| `shouldUseThreeJS()` | boolean | `hasWebGL && !prefersReducedMotion && !isLowPower` |
| `shouldUseCanvas()` | boolean | `!prefersReducedMotion` |
| `smartRAF(callback)` | number | `requestAnimationFrame` 包装，`document.hidden` 时 `cancelAnimationFrame`，可见时自动恢复 |

所有函数**单次缓存**结果（同一会话内重复调用直接返回缓存值），不会重复检测拖累性能。

#### Safari / iOS 兼容（v2.3.3 加）

> 🔒 **Safari 兼容 3 大坑**（详见 [HANDOFF §6.24](../../HANDOFF.md)）：① **WebGL 上下文丢失**（iOS Safari 切后台→前台触发 `webglcontextlost`）；② **`hasWebGL` 误判**（老 Safari 仅 WebGL1 被判无 WebGL）；③ **emoji 字体不一致**（Apple Color Emoji vs 系统 emoji）。

**新建 3D 组件必须复制 [HeroScene.vue](../../frontend/src/components/HeroScene.vue) 的 Safari 兼容逻辑**：

1. **`webglcontextlost` / `webglcontextrestored` 事件监听**（在 [utils/three-helpers.js](../../frontend/src/utils/three-helpers.js) 的 `createRenderer` 中已统一挂载）：
   - `webglcontextlost`：`event.preventDefault()` + 保存场景状态（相机位置 / OrbitControls 状态 / 自动旋转开关）
   - `webglcontextrestored`：重建 renderer + 恢复场景状态 + 重启 rAF
   - 组件侧需在回调里恢复自身场景（HeroScene 的 `onContextRestored` 为模板）
2. **iOS 降级**（`isIOS()` 检测）降低内存压力，避免老 iOS 缺 `EXT_color_buffer_half_float` 扩展时崩溃：
   - **Bloom 降级**：iOS 关闭 `UnrealBloomPass`（`if (!isIOS()) composer = createPostProcessing(...)`）
   - **PMREM 降级**：iOS PMREM 分辨率 256→128、阴影贴图 2048→1024、`renderer.setPixelRatio(Math.min(dpr, 1.5))`（桌面 dpr 上限 2）
   - 老 iOS 缺 `EXT_color_buffer_half_float` 扩展时（`getWebGLCaps().hasHalfFloatExt === false`）完全关闭 PMREM + Bloom
3. **验证清单**（在原 §1.9.8 验证清单基础上追加）：
   - iOS Safari 真机访问首页：3D 浮岛正常渲染（不降级 SVG）
   - iOS Safari 切到其他 App 再切回：3D 场景恢复（不黑屏）
   - 老 iOS（缺 `EXT_color_buffer_half_float`）：PMREM + Bloom 关闭，3D 仍可渲染（无扩展崩溃）
   - Safari / Chrome 对照：emoji 风格一致（twemoji SVG）

详见 [ARCHITECTURE §1.1.6](../ARCHITECTURE.md) Safari 兼容决策 + 降级验证矩阵 + [HANDOFF §6.24](../../HANDOFF.md) 3 大坑。

### 1.9.9 emoji 组件用法（EmojiIcon.vue，v2.3.3 加，2026-07-30）

> 🔒 **铁律**：**新增 emoji 必须用 `<EmojiIcon name="..." />` 而非裸 emoji 字符**。裸 emoji 在 Safari（Apple Color Emoji 彩色写实）与 Chrome（系统 emoji 扁平）风格不一致，破坏 **跨浏览器一致** 的视觉调性。

**是什么**：[EmojiIcon.vue](../../frontend/src/components/EmojiIcon.vue) 是基于 **Iconify** + `@iconify-json/twemoji` 的离线 **SVG emoji** 组件。twemoji 风格统一扁平彩色，不依赖系统 emoji 字体，确保 Safari / Chrome / Firefox / Edge 渲染完全一致。

**为什么用 SVG emoji 而非系统 emoji**：Safari 用 Apple Color Emoji（彩色写实风格），Chrome 用系统 emoji（扁平风格），同一 emoji 在不同浏览器视觉差异明显（如 🌳 树 / 🏝️ 岛屿 / 🔔 铃铛）。**跨浏览器一致** 是治愈系视觉调性的硬要求，故用 Iconify 离线 SVG 统一。

**用法**：

```vue
<script setup>
import EmojiIcon from '@/components/EmojiIcon.vue'
</script>

<template>
  <!-- name = twemoji 图标名（kebab-case），见 @iconify-json/twemoji -->
  <EmojiIcon name="desert-island" />        <!-- 🏝️ 岛屿 -->
  <EmojiIcon name="bell" />                 <!-- 🔔 铃铛 -->
  <EmojiIcon name="deciduous-tree" />       <!-- 🌳 树 -->
  <EmojiIcon name="herb" />                 <!-- 🌿 草本 -->
  <EmojiIcon name="champagne-bottle" />     <!-- 🍶 拾瓶 -->
  <EmojiIcon name="sparkles" />             <!-- ✨ -->
</template>
```

**支持的 props**：

| prop | 类型 | 默认 | 说明 |
|---|---|---|---|
| `name` | string | **必填** | twemoji 图标名（kebab-case），查 [Iconify twemoji](https://icon-sets.iconify.design/twemoji/) |
| `size` | string \| number | `'1em'` | SVG 尺寸，默认跟随父元素 `font-size`（`1em`） |
| `class` | string | — | 透传给 SVG 的 CSS class（Tailwind class 也可） |

**已替换的位置**（v2.3.3）：
- [AppLayout.vue](../../frontend/src/components/AppLayout.vue)：品牌图标 / 导航项 / 通知铃铛 / 资源条
- [ProfileView.vue](../../frontend/src/views/profile/ProfileView.vue)：头像 / 通知 / 资源 / 统计卡 / 快捷入口 / 花朵阶段

**查 twemoji 图标名**：访问 https://icon-sets.iconify.design/twemoji/ 搜索 emoji，复制 `name`（如 🏝️ → `desert-island`）。`@iconify-json/twemoji` 已在 [frontend/package.json](../../frontend/package.json) 依赖中，构建时打包进 bundle（离线，不联网）。

> ⚠️ **不要**用裸 emoji 字符（如 `🏝️`）写进 `.vue` 模板——Safari 与 Chrome 渲染不一致。**所有前台 emoji 必须走 `<EmojiIcon>`**。后台 `/admin/*` SSR 模板不受此约束（独立隔离，不强求跨浏览器一致）。

---

## 2. 常见改动流程

### 2.1 加新页面（Jinja2 SSR 模式，v2.0 后仅用于 `/admin/*` 后台）

> **2026-07-19 v2.0 Vue 3 重构后**：加新**前台**页面走 [§1.9.5 Vue 3 SPA 模式](#195-加新视图vue-3-spa-模式替代旧-21-jinja2-模式)。本节仅适用于 `/admin/*` 后台 SSR 页面（继承 `admin/_base.html`）。

1. `templates/admin/your_page.html` 继承 `admin/_base.html`
2. [app/routers/admin_pages.py](../../app/routers/admin_pages.py) 加路由（**新 API**：传 `request` 作第一参数）
3. `static/js/pages/admin_your_page.js` 写逻辑
4. 模板底部 `<script defer src="/static/js/pages/admin_your_page.js"></script>`
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

### 2.7 加一个 AI 场景（2026-07-17 起）

> 现有 4 个场景在 [app/services/ai_service.py](../../app/services/ai_service.py) / [app/routers/ai.py](../../app/routers/ai.py) / [app/schemas/ai.py](../../app/schemas/ai.py)。再加一个走同样套路。完整决策见 [HANDOFF §7.9](../../HANDOFF.md)。

**4 步走**：

#### 第 1 步：Schema
在 [app/schemas/ai.py](../../app/schemas/ai.py) 加 `AI<X>In` + `AI<X>Out` 两个 Pydantic 模型：

```python
class AIXxxIn(BaseModel):
    """入参：xxx 场景"""
    user_text: str = Field(..., min_length=1, max_length=500)

class AIXxxOut(BaseModel):
    """出参：xxx 场景"""
    available: bool
    message: str
```

在 [app/schemas/__init__.py](../../app/schemas/__init__.py) 的 `__all__` 加 import；末尾 `model_rebuild()` 区段确保新模型也被 rebuild（防 §3.1 Pydantic 前向引用坑）。

#### 第 2 步：Service
在 [app/services/ai_service.py](../../app/services/ai_service.py) 加：

```python
# 1. 系统提示词常量（温柔语气、不诊断不开药、危机引导专业帮助）
SYSTEM_PROMPT_XXX = """你是一个温柔的倾听者..."""

# 2. 上层方法
def generate_xxx(self, user_text: str) -> str:
    return self._call_nvidia(
        system_prompt=SYSTEM_PROMPT_XXX,
        user_content=user_text,
        max_tokens=300,
        temperature=0.7,
    )
```

**禁止**在 router 里直接调 `_call_nvidia()`——业务规则集中在 service。

#### 第 3 步：Router
在 [app/routers/ai.py](../../app/routers/ai.py) 加：

```python
@router.post("/xxx", response_model=AIXxxOut)
def xxx(body: AIXxxIn, user: User = Depends(get_current_user)):
    try:
        msg = ai_service.generate_xxx(body.user_text)
        return {"available": True, "message": msg}
    except AIServiceUnavailable:
        # 降级：不报 500，返回治愈系友好提示
        return {"available": False, "message": "AI 在休息一下，待会儿再来轻声陪伴你"}
```

**铁律**：
- 端点**必须** `Depends(get_current_user)` 鉴权
- 端点**必须** try/except `AIServiceUnavailable` 降级，**不报 500**

#### 第 4 步：前端集成（3 选 1）

| 方式 | 模板 | JS |
|---|---|---|
| **独立新页面**（如 AI 树洞对话） | `templates/xxx.html` + 在 [app/routers/pages.py](../../app/routers/pages.py) 加 SSR 路由 | `static/js/pages/xxx.js` |
| **已有页面加容器**（如漂流瓶鼓励语 / 情绪日历治愈语） | 在 `templates/xxx.html` 加 `<div id="ai-xxx">` | 在 `static/js/pages/xxx.js` 加 `loadAIXxx()` 函数 |
| **首页加卡片**（如音乐推荐） | 在 `templates/index.html` 加卡片（用 `{% if current_user %}` 控制仅登录可见） | `static/js/pages/home.js` 或新建 JS |

JS 调用示例：

```javascript
async function loadAIXxx() {
  const data = await QI.fetchJSON('/api/ai/xxx', {
    method: 'POST',
    body: JSON.stringify({ user_text: '...' }),
  });
  // 拿到 available:true/false 都正常显示文案，不报错
  document.querySelector('#ai-xxx').textContent = data.message;
}
```

#### 第 5 步：测试降级（必做）
**先不配 `QI_NVIDIA_API_KEY`**，确认端点返回 `available:false` + 友好提示；**再配 key** 跑一遍，确认 `available:true` + AI 文案。详见 [§3.14](#314-ai-端点降级测试方法)。

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

### 3.13 模块职责分离 + 密码可见性切换 + iOS 导航栏避让

**场景**（2026-07-16 会话 7 甲方 5 项需求）：
1. 登录/注册/日记解锁 modal 密码框要带"睁眼/闭眼"切换
2. 苹果用户反馈导航栏占据过大屏幕空间
3. 情绪日历的文本输入要整合到日记模块，日历只记表情
4. 日历日期数字要被当日心情 emoji 替代显示
5. 日记编辑页不再选心情，心情选择与日记编写完全分离

**决策 1：密码切换用事件委托，复用三处**
- 不在 login.html / register.html / diary.js 三处各写一份 toggle 逻辑
- 统一 `.password-input-wrap`（包裹 input + 按钮）+ `.password-toggle`（👁 按钮）的 DOM 结构
- `app.js initPasswordToggle()` 在 document 上监听 click，`e.target.closest(".password-toggle")` 命中即切换 `input.type` + 按钮图标（👁 ↔ 🙈）+ aria-label
- 用 `this._pwdToggleBound = true` 防重复绑定（与 `initRipple` 同模式）
- **关键**：diary.js 的 `askPassword` modal 是动态生成的，事件委托天然支持，不需要 modal 生成后再 attach listener

**决策 2：iOS 导航栏避让**
- `.nav` 加 `padding-top: env(safe-area-inset-top)`（iOS 自动注入刘海/灵动岛高度）
- 移动端 `@media (max-width: 720px)`：nav 高度 56px→52px、隐藏 `.nav__nickname`、加大「离开」按钮点击区域
- **铁律**：会话 5 已确立 `env(safe-area-inset-bottom)` 避让底部 home indicator；本次补 `env(safe-area-inset-top)` 避让顶部刘海，两个方向都要顾

**决策 3：模块职责分离 = 删 UI，不删字段**
- 情绪日历删 textarea `#mood-note`，提交 `note: null`
- 日记编辑页删 mood-grid，提交 `mood_type: null`
- **`MoodCheckin.note` 和 `Diary.mood_type` 字段都保留**（nullable=True），向后兼容历史数据
- **数据迁移零改动**：DB 查询确认 `MoodCheckin.note` 历史数据 `with_note: 0`；`Diary.mood_type` 历史数据保留显示（「我的瓶子」时间线仍显示历史日记的心情表情）
- **铁律**：删 UI 功能 ≠ 删 DB 字段。先查历史数据是否需要迁移，能不删字段就不删（保留向后兼容，新数据写 null）

**决策 4：日历 emoji 替代数字**
- `renderCalendar` 里 `isChecked` 时 content 只生成 `<span class="mood-emoji">${emoji}</span>`，否则显示数字
- CSS `.calendar__day .mood-emoji` 从 absolute 右上角 14px 改为居中 22px
- 利用 `.calendar__day` 已有的 `display: flex; align-items: center; justify-content: center`，emoji span 直接居中放大，不需要新写定位
- title 属性显示日期字符串，鼠标 hover 可看完整日期

**决策 5：日记正文自由贴 emoji**
- 删心情选择模块后，textarea placeholder 加 "也可以贴任何 emoji 🌸" 暗示
- 不做 emoji picker（甲方要求"自由粘贴或插入任意 emoji"，picker 反而限制选择范围）
- 用户可用系统输入法自带的 emoji 面板（Win+. / Mac Ctrl+Cmd+Space）

**验证矩阵**（curl.exe）：
```
curl /login            → 200，HTML 含 password-toggle / password-input-wrap
curl /register         → 200，HTML 含 password-toggle / password-input-wrap
curl /mood-calendar    → 302 Location: /login?next=/mood-calendar（未登录）
curl /diary/write      → 302 Location: /login?next=/diary/write（未登录）
curl /                 → 200，HTML 不含"心情手帐"，含"情绪日历"
```

**铁律汇总**：
- 密码切换/按钮涟漪/事件委托类增强，统一用 document-level 委托 + `_xxxBound = true` 防重复绑定，动态生成的 modal 天然支持
- iOS safe-area 两个方向都要顾：底部 `env(safe-area-inset-bottom)` + 顶部 `env(safe-area-inset-top)`
- 删 UI 功能 ≠ 删 DB 字段：先查历史数据，nullable 字段保留向后兼容，新数据写 null
- 日历 emoji 替代数字：复用已有 flex 居中，不新写定位
- 「自由贴 emoji」需求不做 picker，让用户用系统输入法

### 3.14 AI 端点降级测试方法（2026-07-17 加）

**场景**：4 个 AI 端点（`/api/ai/chat` / `/api/ai/encouragement` / `/api/ai/healing` / `/api/ai/recommend-music`）必须保证「未配 key 或调用失败时返回 200 + `available:false` + 治愈系友好提示」，**不报 500**。这是 AI 接入「渐进增强」的核心保证。

**测试 1：未配 key 降级**（默认状态）
```bash
# 1. 确保 .env 没有 QI_NVIDIA_API_KEY（或留空）
# 2. 重启
python start.py restart
# 3. 登录拿 cookie
curl -c c.txt -X POST http://127.0.0.1:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"nickname":"test","password":"hello123"}'
# 4. 调 4 个 AI 端点，应该都返回 200 + available:false
curl -b c.txt -X POST http://127.0.0.1:5000/api/ai/healing \
  -H "Content-Type: application/json" \
  -d '{"mood_emoji":"calm"}'
# 期望: {"available":false,"message":"AI 在休息一下..."}
```

**测试 2：配 key 正常返回**
```bash
# 1. 在 .env 加入 3 个变量（参考 DEPLOYMENT「AI 接入」段）
# 2. 重启
python start.py restart
# 3. 调端点，应该返回 200 + available:true + AI 文案
curl -b c.txt -X POST http://127.0.0.1:5000/api/ai/healing \
  -H "Content-Type: application/json" \
  -d '{"mood_emoji":"calm"}'
# 期望: {"available":true,"message":"<AI 生成的治愈语>"}
```

**测试 3：调用失败降级**（模拟网络/限流/4xx/5xx）
```bash
# 方法 A：临时把 QI_AI_BASE_URL 改成无效地址（如 https://invalid.example.com/v1）→ 重启 → 调端点
# 方法 B：临时把 QI_NVIDIA_API_KEY 改成无效 key（如 nvapi-invalid）→ 重启 → 调端点
# 期望: 200 + available:false + 治愈系提示（不报 500）
```

**测试 4：前端浏览器手动测**
```
# 1. 浏览器访问 /ai-chat（需登录）→ 输入对话 → 看到回复（配 key）或治愈系提示（不配 key）
# 2. /pick 拾瓶后看 #ai-encouragement 容器有内容
# 3. /mood-calendar 打卡后看 #ai-healing-msg 容器有内容
# 4. / 首页「AI 帮我选音」卡片（仅登录可见）→ 描述状态 → 看推荐 + 跳转链接
```

**铁律**：
- AI 端点**永不**返回 5xx——失败时统一返回 200 + `available:false` + 治愈系提示
- 前端拿 `available:true/false` 都正常显示文案，**不报错**
- 改完 AI 代码必须跑测试 1（不配 key 降级）+ 测试 2（配 key 正常）—— 两个状态都要测
- 失败原因走 `logger.warning`，**不**暴露给前端（避免泄露内部信息）
- `_call_nvidia()` 超时 60s（模型默认 `meta/llama-3.1-8b-instruct`，8B 实际 1-10s，60s 纯兜底；原默认 `nvidia/llama-3.1-nemotron-70b-instruct` 在用户 NVIDIA 账户下 404 不可用）；超时也走降级返回 `available:false`，不报 500

---

### 3.15 v2.3 双资源系统迁移（露水 + 落叶替代单一 total_energy，2026-07-25 加）

**场景**（v2.3 重构核心改动）：
- 原单一 `users.total_energy` 拆为 `users.dew`（露水，向内获得）+ `users.leaves`（落叶，向外获得）
- `EnergyRecord` 加 `resource_type` 列（`"dew"` / `"leaves"`）
- `ShopItem` 加 `cost_resource` 列决定兑换时扣哪种资源
- `total_energy` 字段保留作兼容总能量（= dew + leaves），**不删**

**铁律**（v2.3 加，违反任何一条都会导致资源显示不一致）：

1. **grant_energy 必须显式传 resource_type**（[app/services/energy_service.py](../../app/services/energy_service.py)）：
```python
# ✅ 正确：显式指定 resource_type
grant_energy(db, user, amount=1, source="listen_music", resource_type="dew")
grant_energy(db, user, amount=2, source="write_diary", resource_type="leaves")

# ❌ 错误：漏掉 resource_type（默认 "dew"，但写日记应该是 leaves）
grant_energy(db, user, amount=2, source="write_diary")
```

2. **能量累加用 `db.query(User).filter(...).update(...)` 而非对象属性赋值**（沿用 §3.7 铁律，v2.3 强调双资源都要这样）：
```python
# ✅ 正确：按 resource_type 选列，显式 UPDATE
column = User.dew if resource_type == "dew" else User.leaves
db.query(User).filter(User.id == user.id).update(
    {column: column + amount}, synchronize_session=False,
)

# ❌ 错误：对象属性赋值不会写回 DB（FastAPI 一请求一 session）
user.dew += amount
db.add(user)
```

3. **兑换商店物品按 `ShopItem.cost_resource` 扣对应资源**（[app/services/energy_service.py](../../app/services/energy_service.py) `exchange_item`）：
```python
# ✅ 正确：按 item.cost_resource 决定扣 dew 还是 leaves
column = User.dew if item.cost_resource == "dew" else User.leaves
db.query(User).filter(User.id == user.id).update(
    {column: column - item.cost}, synchronize_session=False,
)

# ❌ 错误：硬编码扣 dew（落叶物品会扣错资源）
db.query(User).filter(User.id == user.id).update(
    {User.dew: User.dew - item.cost}, synchronize_session=False,
)
```

4. **Pydantic Out schema 必须同步 dew + leaves 字段**（pre-commit 第 1 项，沿用 §3.10 铁律）：
```python
# app/schemas/energy.py / auth.py
class EnergySummaryOut(BaseModel):
    dew: int          # ← v2.3 加
    leaves: int       # ← v2.3 加
    total_energy: int # ← 兼容字段，= dew + leaves
    resource_type: Optional[str] = None  # EnergyRecordOut 用
```
漏掉 dew / leaves → 前端 `data.dew` 永远 `undefined` → 双资源条不显示（沿用 §3.10 静默过滤坑）。

5. **`_migrate_legacy_columns()` 必须加 4 个新列**（pre-commit 第 2 项，详见 [ARCHITECTURE §1.1.7.10](../ARCHITECTURE.md)）：
   - `users.dew INTEGER DEFAULT 0` + `users.leaves INTEGER DEFAULT 0`
   - `energy_records.resource_type VARCHAR DEFAULT 'dew'`
   - `shop_items.cost_resource VARCHAR DEFAULT 'dew'`
   老库重启后自动加列，**不需要**手动 ALTER TABLE。

**验证矩阵**（v2.3 双资源系统）：
```bash
# 1. 老库迁移成功
sqlite3 data/healing.db
sqlite> .schema users | grep -E "dew|leaves"           # 应看到两列
sqlite> .schema energy_records | grep resource_type    # 应看到 resource_type
sqlite> .schema shop_items | grep cost_resource        # 应看到 cost_resource

# 2. 听歌后露水 +1，落叶不变
curl -b c.txt -X POST http://127.0.0.1:5000/api/music/listen-complete \
  -H "Content-Type: application/json" -d '{"music_id":1,"progress":0.95}'
curl -b c.txt http://127.0.0.1:5000/api/profile/me | python -m json.tool
# 期望: {"dew": 1, "leaves": 0, "total_energy": 1, ...}

# 3. 写日记后落叶 +2，露水不变
curl -b c.txt -X POST http://127.0.0.1:5000/api/diary \
  -H "Content-Type: application/json" -d '{"content_encrypted":"...","visibility":"public"}'
curl -b c.txt http://127.0.0.1:5000/api/profile/me | python -m json.tool
# 期望: {"dew": 1, "leaves": 2, "total_energy": 3, ...}

# 4. 兑换露水物品后 dew 减少，leaves 不变；兑换落叶物品反之
```

**铁律汇总**：
- 双资源系统下，所有 `grant_energy` / `exchange_item` 调用必须显式传 `resource_type` / 检查 `item.cost_resource`
- Pydantic Out schema 必须同步 dew + leaves + resource_type 三个字段（沿用 §3.10）
- `_migrate_legacy_columns()` 必须加 4 个新列（pre-commit 第 2 项）
- 前端双资源条（GardenView / ShopView / ProfileView）必须同时显示 dew + leaves，不能只显示一个

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
