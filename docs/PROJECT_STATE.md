# 项目现状快照

> 一眼看出「现在能跑吗」「最近改了什么」「还有什么 TODO」。
> 每次大改后请更新本文件。

> 🔒 **2026-07-28 v2.3.2 start.py 默认生产模式 + 自动构建简化**：`python start.py` 默认行为再次变更——**默认走生产模式**（FastAPI :5000 单进程，前后端不再一起起），需 `static/dist/` 已构建（不存在则自动 `npm install + npm run build`）。**自动构建仅检测 `static/dist/index.html` 存在性**（`dist 存在检测`），不再比较 `frontend/src/` 与 `static/dist/` 文件修改时间。**开发需显式 `python start.py --dev`**（Vite :5000 HMR + FastAPI :5001 API，前后端一起起的「应用模式」）。`--prod` 改为兼容别名（默认就是生产模式，加不加效果一样）。**服务器部署 2 步**：① 上传代码 ② `python start.py`（首次自动构建，之后秒启，FastAPI 单进程 :5000）。本次回滚 v2.2.2「默认应用模式」决策，理由：服务器端口代理已配好 :5000 不能动，应用模式会让 Vite 占 :5000 破坏代理。关键词 `默认生产模式` / `dist 存在检测` / `自动构建` / `--dev` / `应用模式` / `v2.3.2` 在 6 份文档中都要出现。

> 🔒 **2026-07-30 v2.3.3 Safari 兼容性修复（3D 上下文恢复 + emoji 跨浏览器一致）**：解决 Safari / iOS 用户反馈的两类问题。① **Safari 主页 3D 不渲染**：根因包括 `hasWebGL()` 检测 bug、iOS Safari 切后台→前台后 WebGL 上下文丢失无恢复逻辑、老 iOS 缺 `EXT_color_buffer_half_float` 扩展、Bloom + 高分辨率 PMREM 内存超限。修复：**`hasWebGL` 重写**（区分 WebGL1/2 + 检测扩展 + max texture size），新增 `getWebGLCaps()` / `isSafari()` / `isIOS()` 工具函数；[frontend/src/utils/three-helpers.js](../../frontend/src/utils/three-helpers.js) 添加 `webglcontextlost` / `webglcontextrestored` 事件监听，上下文丢失时保存场景状态、恢复时重建；[HeroScene.vue](../../frontend/src/components/HeroScene.vue) 实现 **iOS 降级**策略（**Bloom 降级**：iOS 关闭 UnrealBloomPass；**PMREM 降级**：iOS PMREM 分辨率 256→128、阴影 2048→1024、dpr 上限 2→1.5；老 iOS 缺扩展时关闭 PMREM + Bloom）。② **Safari emoji 显示不一致**：根因为跨平台 emoji 字体风格差异（Apple Color Emoji vs 系统 emoji）。修复：新建 [EmojiIcon.vue](../../frontend/src/components/EmojiIcon.vue) 组件，使用 **Iconify** + `@iconify-json/twemoji` 离线 **SVG emoji**，确保 **跨浏览器一致**；替换 [AppLayout.vue](../../frontend/src/components/AppLayout.vue)（品牌 / 导航 / 通知 / 资源）+ [ProfileView.vue](../../frontend/src/views/profile/ProfileView.vue)（头像 / 通知 / 资源 / 统计 / 快捷入口 / 花朵阶段）所有 emoji。构建 209 modules / 12.30s，HeroScene +0.71KB（降级逻辑）。关键词 `Safari 兼容` / `WebGL 上下文丢失` / `webglcontextlost` / `iOS 降级` / `EmojiIcon` / `Iconify` / `twemoji` / `SVG emoji` / `跨浏览器一致` / `hasWebGL 重写` / `getWebGLCaps` / `isSafari` / `isIOS` / `Bloom 降级` / `PMREM 降级` / `v2.3.3` 在 6 份文档中都要出现。

> 🔒 **2026-08-10 v2.4.0 UI/UX 大改 + 一天多条心情 + 头像/昵称编辑 + 花坊扩充**：18 项改动覆盖文案/功能/数据模型/AI/商店。① **首页文案**：'海上有座岛，岛上有人听' → '潮声不止，心安自屿'，删'静屿'副标题 + 删'今日打卡'板块；'漂流日记'入口统一显示'日记海岸'界面。② **一天多条心情**：移除 `mood_checkins` 表 `(user_id, check_date)` 唯一约束（SQLite 重建表方式：CREATE TABLE _new AS SELECT * → DROP → RENAME → CREATE INDEX），支持一天多次打卡（情绪是多变的）；[app/services/mood_service.py](../../app/services/mood_service.py) `upsert_checkin` → `add_checkin`（不再 UPSERT）+ 新增 `get_today_moods`；30 天心情趋势用 1-5 评分系统，多条取**平均分**（MOOD_SCORE：ecstatic=5/happy=4/calm=3/tired=2/anxious=2/angry=1/sad=1）。③ **头像/昵称修改**：[app/models/user.py](../../app/models/user.py) 新增 `User.avatar: str = "🙂"`（String(16)，默认 🙂）+ 新增 `PATCH /api/profile` 端点 + [app/schemas/profile.py](../../app/schemas/profile.py) `ProfileUpdateIn`（nickname 2-20 字符可选 / avatar 1-16 字符可选，昵称查重 409）+ 前端 [ProfileView.vue](../../frontend/src/views/profile/ProfileView.vue) 编辑弹窗（24 个可选 emoji）+ **头像同步树洞**（[AIChatView.vue](../../frontend/src/views/ai/AIChatView.vue) 用 `userStore.avatar`）。④ **花坊扩充**：'落叶画坊' → '花坊'（改名）；花种扩充至 12 种（向日葵/竹子/雏菊/莲花/薰衣草/郁金香/梅花/桃花/兰花/青松/桂花/银杏）+ 新装扮（油纸伞/蓑衣/乌篷船/鱼竿/橘猫/白鹤）+ '古琴初学者' → '琴音知音'（徽章改名）+ **每板块徽章**（琴音知音/日记达人/七日静心/拾瓶旅人/树洞倾心/花田主人）+ '竹编帽' 描述改'种花人遮阳的草帽'；`DEFAULT_SHOP_ITEMS` 扩充至 27 件。⑤ **AI 系统提示词 humanize**：心语树洞更接地气、像朋友聊天。⑥ **'我的'页面修复**：'收到鼓励'/'岛上物件'可点击跳转，删除重复'岛上物件'，新增**静屿使用指南**（详细介绍 7 个模块功能）。⑦ **花田 AI 显示基于实际种花情况**（没种花不显示）。⑧ **露水累加修复**：写日记和留言鼓励后正确发放露水。⑨ 情绪日历 emoji 显示/选择修复。数据库迁移 `_migrate_legacy_columns()`：`ALTER TABLE users ADD COLUMN avatar VARCHAR(16) DEFAULT '🙂' NOT NULL` + 移除 `mood_checkins` 唯一约束。关键词 `v2.4` / `潮声不止心安自屿` / `花坊` / `一天多条心情` / `mood_checkins 唯一约束移除` / `add_checkin` / `get_today_moods` / `平均分` / `humanize` / `琴音知音` / `每板块徽章` / `User.avatar` / `PATCH /api/profile` / `ProfileUpdateIn` / `头像同步树洞` / `静屿使用指南` / `露水累加修复` 在 6 份文档中都要出现。

> 🔒 **2026-08-10 v2.4.1 情绪日历改用罗素情绪环模型（Russell's Circumplex Model of Affect）四象限图表**：本次将情绪日历模块的「30 天趋势柱状图」板块替换为「罗素情绪环模型四象限图表」，让用户从「效价 × 唤醒度」二维视角理解自己的情绪分布，不再只看趋势分数。**文件**：[MoodCalendarView.vue](../../frontend/src/views/mood/MoodCalendarView.vue)。① **移除**：30 天趋势柱状图板块——`trendBars` computed / `scoreColor` 函数 / `.trend-section` 模板 / `.trend-bar` 样式全部删除（`30 天趋势柱状图移除`）。② **新增**：罗素情绪环模型四象限图表——横轴 **效价 Valence**（左消极 → 右积极），纵轴 **唤醒度 Arousal**（下低唤醒 → 上高唤醒），四象限 Q1(积极+高唤醒) / Q2(消极+高唤醒) / Q3(消极+低唤醒) / Q4(积极+低唤醒)（`四象限图表`）。③ **数据**：定义 `CIRCUMPLEX_EMOTIONS` 数组（`20 种情绪`），每种情绪带 `valence`(-1~+1) 和 `arousal`(-1~+1) 坐标——其中 `6 种已追踪情绪`（ecstatic / happy / calm / tired / anxious / angry / sad）映射到后端 [constants.py](../../app/utils/constants.py) `MOOD_INFO`，有真实打卡数据；`14 种参考情绪`（兴奋 / 激动 / 恐慌 / 恐惧 / 极度烦躁 / 低落 / 压抑 / 倦怠 / 空虚 / 闲适 / 舒心 / 恬淡平和 / 兴致高昂 / 狂喜）帮助用户理解情绪在环模型中的位置。④ **交互**（`点击交互`）：点击 emoji → 弹出详情卡片，显示「`本月出现次数` X 次」；已追踪情绪有边框高亮 + 次数角标（右上角小圆点）；未追踪情绪显示「该情绪暂未开放打卡记录」；`emotionPosition(emotion)` 将 valence/arousal 转为 left% / top% 百分比定位。⑤ **统计**：`moodCounts` computed 从 `checkins` 数据统计本月各心情出现次数；`totalCheckins` 显示本月总打卡数。⑥ **视觉**：治愈系配色（四象限淡色背景）+ GSAP 入场动画（emoji 逐个弹出 `back.out` 缓动）+ 移动端响应式。⑦ **保留**：`fetchTrend` 仍调用（为 `currentStreak` 连续打卡天数显示），但 `trend` 数据不再用于渲染。详见 [HANDOFF §4 Phase 10](../../HANDOFF.md)。关键词 `v2.4.1` / `Russell情绪环模型` / `Circumplex Model` / `四象限图表` / `效价Valence` / `唤醒度Arousal` / `CIRCUMPLEX_EMOTIONS` / `emotionPosition` / `moodCounts` / `20种情绪` / `6种已追踪` / `14种参考` / `点击交互` / `本月出现次数` 在 6 份文档中都要出现。

> 🔒 **2026-08-13 v2.4.2 整体架构优化与冗余清理（维护性清理版本）**：本次为维护性清理版本，**无功能变化 / 无数据库迁移 / 无新依赖**，7 项改动专注代码瘦身与一致性对齐。① **删除 15 个死模板 + 1 空目录**（`死模板清理`）：Vue 3 SPA 迁移前遗留的旧 Jinja2 SSR 模板——[templates/](../../templates/) 下 `base/_nav/_toast/index/login/register/music_list/diary_write/diary_detail/my_bottles/pick_bottle/mood_calendar/garden/shop/ai_chat.html` 全部删除 + `templates/partials/` 空目录删除；**仅保留** [templates/admin/](../../templates/admin/)（[admin_pages.py](../../app/routers/admin_pages.py) 仍使用 Jinja2 SSR）。② **删除 10 个死页面脚本**（`死页面脚本`）：[static/js/pages/](../../static/js/pages/) 下非 admin 脚本——`ai_chat/auth/diary/diary_detail/home/mood_calendar/music/my_bottles/pick/shop.js` 全部删除，仅被死模板引用，迁移后已无入口。③ **[app/main.py](../../app/main.py) 版本号 1.0.0 → 2.4.2**（`版本号对齐`）：与 git tag / README badge 对齐。④ **[app/main.py](../../app/main.py) `EXT_TO_MIME` 删除重复 `.webp` 条目**（`EXT_TO_MIME`）：字典中定义了两次，删除后者。⑤ **修复过时端口注释**（`过时注释`）：[app/routers/pages.py](../../app/routers/pages.py) / [frontend/vite.config.js](../../frontend/vite.config.js) / [static/js/app.js](../../static/js/app.js) 中 `:5173 → :5000`（Vite）/ `:5000 → :5001`（FastAPI 开发）。⑥ **新增 5 个五音封面 SVG**（`SVG封面`）：[static/img/cover_gong.svg](../../static/img/cover_gong.svg) / `cover_shang.svg` / `cover_jue.svg` / `cover_zhi.svg` / `cover_yu.svg`，颜色取自 [app/utils/constants.py](../../app/utils/constants.py) `YIN_INFO`，修复 [app/seed.py](../../app/seed.py) 引用的缺失资源。⑦ **[app/routers/admin_pages.py](../../app/routers/admin_pages.py) admin_users N+1 查询优化**（`N+1优化` / `GROUP BY`）：原 for 循环内 3 个 COUNT/用户 × 50 用户 = 151 次查询 → 1 次查用户 + 3 个 `GROUP BY` 聚合 + 字典拼接 = 4 次查询。**不动**：[static/css/](../../static/css/) 全部保留（admin/_base.html 加载 style.css）/ [static/js/app.js](../../static/js/app.js) 保留（仅改注释）/ [static/audio/](../../static/audio/) 保留（seed.py 生成占位 mp3）/ [templates/admin/](../../templates/admin/) 保留 / [config.py](../../config.py) / [app/database.py](../../app/database.py) / [requirements.txt](../../requirements.txt) 不动。关键词 `v2.4.2` / `死模板清理` / `死页面脚本` / `N+1优化` / `GROUP BY` / `SVG封面` / `EXT_TO_MIME` / `版本号对齐` / `过时注释` 在 6 份文档中都要出现。

> 🔒 **2026-08-14 v2.4.3 花语文案焕新 + emoji 名称对齐 + 徽章奖励落叶 + 树洞三层回复 + 情绪日历空 bug 修复**：本次为内容运营 + Bug 修复版本，**无新依赖**，专注文案打磨 / emoji 修正 / 资源死锁解除 / AI 回复质量提升。① **删除「古琴初学者」废弃徽章**（`废弃徽章删除`）：v2.4.0 改名「琴音知音」后旧徽章仍在 seed 残留，[app/seed.py](../../app/seed.py) 启动时清理 `DEPRECATED_BADGES = ["古琴初学者"]`。② **「花田主人」→「花间客」**（`花间客改名`）+ **「花坊」→「落叶花坊」**（`落叶花坊改名`）。③ **情绪日历空白 Bug 修复**（`情绪日历空白修复`）：[MoodCalendarView.vue](../../frontend/src/views/mood/MoodCalendarView.vue) `cell.moodKeys.length` 在空单元格上抛 `TypeError: Cannot read properties of undefined`，整页空白；修复为 `cell.moodKeys?.length > 0`。④ **落叶死锁解除**（`落叶死锁解除` / `BADGE_LEAF_REWARD`）：新增 [constants.py](../../app/utils/constants.py) `BADGE_LEAF_REWARD: Final[int] = 10`；[energy_service.py](../../app/services/energy_service.py) `check_achievements()` 每解锁一个徽章额外发放 10 落叶，返回 `{new_badges, new_leaves, leaves_balance}`；mood / diary / music / ai / energy 5 路由透传。⑤ **花田 AI 显示基于实际种花**（`花田 AI 显示修复`）：[GardenView.vue](../../frontend/src/views/garden/GardenView.vue) `<FlowerField v-if="flowers.length > 0" />`。⑥ **岛上物件 emoji 化**（`岛上物件 emoji`）+ **首页 emoji 🏝️ → 🌊**（`首页海浪 emoji`）+ **漂流瓶 emoji 🍶 → 🏺**（`漂流瓶 emoji`）。⑦ **树洞 AI 重写**（`树洞三层回复`）：[ai_service.py](../../app/services/ai_service.py) `SYSTEM_PROMPT_TREEHOLE` 重写为三层结构（接住情绪 / 安慰或新视角 / 具体可操作的小建议）。⑧ **花种 emoji 与名称对齐 + 花语化**（`花语化` / `emoji 对齐`）：12 种花种介绍全改为「花语：XX」；emoji 对齐（薰衣草 💜→🪻 / 桂花→小麦 🌾 / 银杏→青叶 🍃 / 兰花+梅花合并为樱花 🌸 / 白鹤→火烈鸟 🦩 / 蓑衣→斗篷 🧥）。⑨ **装扮动物扩充**（`动物扩充`）：新增小鸟 🐦 / 小鸭 🦆 / 小狗 🐶。⑩ **seed 改名迁移 + 去重**（`改名迁移` / `去重`）：`RENAME_MAP` 改名老库物品 + 合并同名重复。⑪ **版本号 2.4.2 → 2.4.3**（`版本号对齐`）。详见 [HANDOFF §4 Phase 11](../../HANDOFF.md)。关键词 `v2.4.3` / `花语化` / `emoji 对齐` / `BADGE_LEAF_REWARD` / `落叶死锁解除` / `树洞三层回复` / `情绪日历空白修复` / `花间客改名` / `落叶花坊改名` / `改名迁移` / `去重` / `岛上物件 emoji` / `首页海浪 emoji` / `漂流瓶 emoji` / `动物扩充` / `花田 AI 显示修复` 在 6 份文档中都要出现。

> 🔒 **2026-08-15 v2.4.4 情绪日历透明修复 + 旧版日记迁移 + mood_checkins 主键重建 + 头像图片上传 + 落叶花坊文案打磨**：本次为 Bug 修复 + 功能增强版本，专注修复用户反馈的可见性 / 数据完整性 / 表结构问题 + 新增头像上传功能。① **[BUG FIX] 情绪日历 emoji 透明**（`情绪日历透明修复`）：[MoodCalendarView.vue](../../frontend/src/views/mood/MoodCalendarView.vue) GSAP 动画设置了 `opacity:0` 导致心情选择按钮几乎不可见，已移除该属性。② **[BUG FIX] 旧版日记无内容**（`旧版日记迁移`）：旧版加密日记 `content` 字段为空（`content_encrypted` 是假占位符），数据库迁移自动填入提示文本「（这段日记来自旧版本，内容已无法读取）」。③ **[BUG FIX] mood_checkins 表缺失 PRIMARY KEY**（`mood_checkins 主键重建`）：v2.4 的迁移用了 `CREATE TABLE AS SELECT` 导致 `mood_checkins` 表丢失主键和自增，批量打卡时 `db.flush()` 报 `NULL identity key` 错误（500）。已重建表（`id INTEGER PRIMARY KEY AUTOINCREMENT` + FK + 索引），数据完整迁移。④ **[BUG FIX] avatar 字段长度**（`avatar 字段长度`）：[User.avatar](../../app/models/user.py) 原为 `String(16)`，无法存储图片上传后的 URL 路径。已改为 `String(255)`，[ProfileUpdateIn](../../app/schemas/profile.py) schema 同步调整为 `max_length=255`。⑤ **[FEATURE] 头像支持图片上传**（`头像图片上传`）：新增 `POST /api/profile/avatar` 端点，支持 JPG/PNG/WebP/GIF（≤2MB），存储到 `static/uploads/avatars/`。[ProfileView.vue](../../frontend/src/views/profile/ProfileView.vue) 增加上传按钮，[AIChatView.vue](../../frontend/src/views/ai/AIChatView.vue) 支持图片头像渲染。⑥ **[IMPROVEMENT] 落叶花坊花朵介绍**（`花朵介绍`）：移除「花语：」前缀，只保留完整花语。⑦ **[IMPROVEMENT] 徽章落叶奖励分级**（`徽章落叶分级`）：按徽章 trigger 分级设置落叶奖励（streak_7=7, listen_10=10, pick_10=10, flower_10=10, chat_20=15, diary_30=20, 默认=10）。⑧ **[IMPROVEMENT] 情绪日历使用指南更新**（`情绪日历指南`）：介绍改为罗素情绪环模型（Russell's Circumplex Model）四象限说明。⑨ **[IMPROVEMENT] 岛上物件 emoji**（`岛上物件 emoji`）：🎁 → 🧳（行李箱）。⑩ **[IMPROVEMENT] 通知 emoji 统一**（`通知 emoji 统一`）：漂流瓶回复通知的 emoji 统一为 💛（黄色爱心）。详见 [HANDOFF §4 Phase 12](../../HANDOFF.md)。关键词 `v2.4.4` / `情绪日历透明修复` / `旧版日记迁移` / `mood_checkins 主键重建` / `avatar 字段长度` / `头像图片上传` / `花朵介绍` / `徽章落叶分级` / `情绪日历指南` / `岛上物件 emoji` / `通知 emoji 统一` 在 6 份文档中都要出现。

**最后更新**：2026-08-15（v2.4.4 情绪日历透明修复 + 旧版日记迁移 + mood_checkins 主键重建 + 头像图片上传 + 落叶花坊文案打磨 — 10 项改动：① **[BUG FIX] 情绪日历 emoji 透明**（`情绪日历透明修复`，移除 GSAP `opacity:0`）；② **[BUG FIX] 旧版日记无内容**（`旧版日记迁移`，自动填提示文本）；③ **[BUG FIX] mood_checkins 表缺失 PRIMARY KEY**（`mood_checkins 主键重建`，重建表 `id INTEGER PRIMARY KEY AUTOINCREMENT` + FK + 索引）；④ **[BUG FIX] avatar 字段长度**（`avatar 字段长度`，`String(16)`→`String(255)` + `ProfileUpdateIn max_length=255`）；⑤ **[FEATURE] 头像支持图片上传**（`头像图片上传`，`POST /api/profile/avatar` + `static/uploads/avatars/`）；⑥ **[IMPROVEMENT] 落叶花坊花朵介绍**（`花朵介绍`，移除「花语：」前缀）；⑦ **[IMPROVEMENT] 徽章落叶奖励分级**（`徽章落叶分级`，按 trigger 分级 streak_7=7 / listen_10=10 / pick_10=10 / flower_10=10 / chat_20=15 / diary_30=20 / 默认=10）；⑧ **[IMPROVEMENT] 情绪日历使用指南更新**（`情绪日历指南`，改罗素情绪环模型四象限说明）；⑨ **[IMPROVEMENT] 岛上物件 emoji**（`岛上物件 emoji`，🎁→🧳）；⑩ **[IMPROVEMENT] 通知 emoji 统一**（`通知 emoji 统一`，漂流瓶回复通知统一 💛）。数据库迁移：mood_checkins 表重建 + User.avatar 字段长度扩展 + 旧版日记 content 填充。前一阶段 v2.4.3（2026-08-14 花语文案焕新 + emoji 名称对齐 + 徽章奖励落叶 + 树洞三层回复 + 情绪日历空 bug 修复 — 14 项改动）+ v2.4.2（2026-08-13 整体架构优化与冗余清理，维护性清理版本 — 7 项改动）+ v2.4.1（2026-08-10 情绪日历改用罗素情绪环模型四象限图表 — 7 项改动）+ v2.4.0（2026-08-10 文案焕新 + 一天多条心情 + 头像/昵称编辑 + 花坊扩充 — 18 项改动）+ v2.3.3（2026-07-30 Safari 兼容性修复 — 3D 上下文恢复 + emoji 跨浏览器一致）+ v2.3.2（2026-07-28 start.py 默认生产模式 + 自动构建简化）+ v2.3（2026-07-25 六大四字名模块重构 + 双资源系统 + 花朵生命周期 + 通知 + 个人主页 + 古琴弹西洋曲谱 — 10 项大改））

---

## 1. 总体状态

| 维度 | 状态 | 备注 |
|---|---|---|
| **可运行** | ✅ | 用户始终访问 `:5000`：生产模式（v2.3.2 起默认）FastAPI :5000 单进程（`python start.py`，dist 不存在则自动构建）；应用模式（`--dev`）Vite :5000 + FastAPI :5001（前后端一起起，本地开发用） |
| **v2.0 Vue 3 重构** | ✅ 完成 | 2026-07-19，前端独立 `frontend/`，13 个视图迁入 `frontend/src/views/`，详见 §2 |
| **v2.1 视觉增强** | ✅ 完成 | 2026-07-20，4 个视觉组件 + 三层渐进增强策略（CSS / Canvas2D / Three.js），全部支持降级，详见 §2 |
| **v2.2 视觉重构** | ✅ 完成 | 2026-07-20，解决 v2.1 "红白机观感" + "交互不明确"两大问题：three-helpers.js PBR 工具集 + SceneHint/SceneControls 交互组件 + 4 个视觉组件 v2 重写（PBR + Bloom + OrbitControls + raycaster），详见 §2 |
| **v2.2.1 start.py 自动构建** | ✅ 完成（已被 v2.2.2 调整） | 2026-07-20，`python start.py` 默认 dist 未构建时自动 `npm install + build` 走生产模式；新增 `--dev` 参数。**2026-07-25 v2.2.2 起默认行为变更**，详见下行 |
| **v2.2.2 start.py 默认应用模式** | ✅ 完成 | 2026-07-25，`python start.py` 默认行为回滚为**应用/开发模式**（Vite :5000 HMR + FastAPI :5001 API 一起起），自动检测 `frontend/node_modules` 不存在则 `npm install`；新增 `--prod` 参数显式生产模式；`--dev` 改为兼容别名；移除 v2.2.1 的 `_ensure_dist_or_dev()` 自动 build 逻辑，详见 §2 |
| **v2.2.3 移动端响应式 UI + 3D 几何降档** | ✅ 完成 | 2026-07-25，三档断点系统差异化布局（手机/平板/桌面）+ iOS Safari `dvh` + safe-area 适配 + fullscreen 路由模式 + 4 个 3D 组件移动端几何精度降档（详见 §2） |
| **v2.3 六大四字名模块 + 双资源 + 花朵生命周期 + 通知 + 个人主页 + 西方曲谱** | ✅ 完成 | 2026-07-25，10 项大改：六大四字名板块 + 双资源（露水/落叶）+ UserFlower + Notification + ProfileView + 古琴弹西洋曲谱子菜单 + 日记调整 + 情绪日历对齐 + 树洞改进 + 漂流瓶评论返回通知，详见 §2 |
| **v2.3.2 start.py 默认生产模式 + 自动构建简化** | ✅ 完成 | 2026-07-28，`python start.py` 默认回滚为**生产模式**（FastAPI :5000 单进程），**`dist 存在检测`** + **`自动构建`**（dist 不存在则 `npm install + npm run build`）；开发需显式 `--dev`（**应用模式**）；`--prod` 改为兼容别名；服务器部署 2 步。回滚 v2.2.2 默认应用模式（服务器端口代理 :5000 不能动），详见 §2 |
| **v2.3.3 Safari 兼容性修复** | ✅ 完成 | 2026-07-30，**Safari 兼容**两类问题修复：① 3D 不渲染（**`hasWebGL` 重写** + `getWebGLCaps` / `isSafari` / `isIOS` + `webglcontextlost` / `webglcontextrestored` 处理 **WebGL 上下文丢失** + **iOS 降级**：**Bloom 降级** + **PMREM 降级**）；② emoji 不一致（新建 **EmojiIcon** 组件，**Iconify** + `@iconify-json/twemoji` 离线 **SVG emoji**，**跨浏览器一致**），详见 §2 |
| **v2.4.0 UI/UX 大改 + 一天多条心情 + 头像/昵称编辑 + 花坊扩充** | ✅ 完成 | 2026-08-10，18 项改动：首页文案 '潮声不止，心安自屿' + 删今日打卡 + 漂流日记入口统一；**一天多条心情**（`mood_checkins` 唯一约束移除 + `add_checkin` + `get_today_moods` + 30 天趋势**平均分**）；**头像/昵称修改**（`User.avatar` + `PATCH /api/profile` + `ProfileUpdateIn` + **头像同步树洞**）；'落叶画坊' → '花坊' + 12 花种 + 6 新装扮 + '古琴初学者' → '琴音知音' + **每板块徽章**；AI 提示词 **humanize**；'我的'页面修复 + **静屿使用指南**；花田 AI 基于实际种花；**露水累加修复**，详见 §2 |
| **v2.4.1 情绪日历改用罗素情绪环模型四象限图表** | ✅ 完成 | 2026-08-10，7 项改动：**移除** 30 天趋势柱状图（`trendBars` / `scoreColor` / `.trend-section` / `.trend-bar`）；**新增** 罗素情绪环模型四象限图表（横轴**效价 Valence** + 纵轴**唤醒度 Arousal** + 四象限 Q1-Q4）；**数据** `CIRCUMPLEX_EMOTIONS` 数组（`20 种情绪`，6 种已追踪 + 14 种参考）；**点击交互** 弹详情卡片显示「`本月出现次数`」+ 边框高亮 + 次数角标 + `emotionPosition` 百分比定位；**统计** `moodCounts` + `totalCheckins`；**视觉** 治愈系配色 + GSAP `back.out` 入场动画 + 移动端响应式；**保留** `fetchTrend` 调用（为 `currentStreak` 连续打卡天数显示），详见 §2 |
| **v2.4.2 整体架构优化与冗余清理（维护性清理版本）** | ✅ 完成 | 2026-08-13，7 项改动：**死模板清理**（15 个 Jinja2 SSR 模板 + templates/partials/ 空目录，仅保留 templates/admin/）+ **死页面脚本**（10 个 static/js/pages/ 非 admin）+ **版本号对齐**（main.py 1.0.0 → 2.4.2）+ **EXT_TO_MIME 去重**（删除重复 .webp）+ **过时注释**（:5173→:5000 / :5000→:5001）+ **SVG封面**（5 个五音 cover_gong/shang/jue/zhi/yu.svg）+ **N+1优化**（admin_users 151 次→4 次 `GROUP BY` 聚合），无功能变化 / 无数据库迁移 / 无新依赖，详见 §2 |
| **v2.4.3 花语文案焕新 + emoji 名称对齐 + 徽章奖励落叶 + 树洞三层回复 + 情绪日历空 bug 修复** | ✅ 完成 | 2026-08-14，14 项改动：**废弃徽章删除**（清理「古琴初学者」残留）+ **花间客改名**（花田主人→花间客）+ **落叶花坊改名**（花坊→落叶花坊）+ **情绪日历空白修复**（`cell.moodKeys?.length` 可选链）+ **落叶死锁解除**（`BADGE_LEAF_REWARD=10`，每解锁徽章赠 10 落叶）+ **花田 AI 显示修复**（`v-if="flowers.length > 0"`）+ **岛上物件 emoji** + **首页海浪 emoji 🏝️→🌊** + **漂流瓶 emoji 🍶→🏺** + **树洞三层回复**（接住情绪 / 安慰或新视角 / 具体建议）+ **花语化**（12 种花种全改花语）+ **emoji 对齐**（薰衣草🪻 / 桂花→小麦🌾 / 银杏→青叶🍃 / 兰花+梅花→樱花🌸 / 白鹤→火烈鸟🦩 / 蓑衣→斗篷🧥）+ **动物扩充**（小鸟🐦/小鸭🦆/小狗🐶）+ **改名迁移/去重**（seed `RENAME_MAP`），无新依赖 / 不改后端模型结构，详见 §2 |
| **v2.4.4 情绪日历透明修复 + 旧版日记迁移 + mood_checkins 主键重建 + 头像图片上传 + 落叶花坊文案打磨** | ✅ 完成 | 2026-08-15，10 项改动：**情绪日历透明修复**（移除 GSAP `opacity:0`）+ **旧版日记迁移**（`content` 空字段自动填提示文本）+ **mood_checkins 主键重建**（`CREATE TABLE AS SELECT` 丢主键 → 重建 `id INTEGER PRIMARY KEY AUTOINCREMENT` + FK + 索引）+ **avatar 字段长度**（`String(16)`→`String(255)` + `ProfileUpdateIn max_length=255`）+ **头像图片上传**（`POST /api/profile/avatar` + `static/uploads/avatars/`，JPG/PNG/WebP/GIF ≤2MB）+ **花朵介绍**（移除「花语：」前缀）+ **徽章落叶分级**（按 trigger 分级 streak_7=7 / listen_10=10 / pick_10=10 / flower_10=10 / chat_20=15 / diary_30=20 / 默认=10）+ **情绪日历指南**（改罗素情绪环模型四象限说明）+ **岛上物件 emoji 🎁→🧳** + **通知 emoji 统一 💛**，数据库迁移：mood_checkins 表重建 + User.avatar 字段扩展 + 旧版日记 content 填充，详见 §2 |
| **6 个 Phase** | ✅ 全部完成 | 古琴五音 / 漂流瓶 / 情绪日历 / 精神花园 / **秘密后台** / **AI 全面接入** |
| **功能完整性** | ✅ 一个功能都不丢 | 古琴五音疗愈 / AI 选音 / 漂流瓶日记 / 拾瓶 / 情绪日历 / AI 树洞 / 精神花园 / 露水商店 / 鉴权 / 404 / 响应式 / GSAP 动效 / 治愈系配色 / **3D + 伪 3D 视觉增强** — 全部 ✅ |
| **端到端测试** | ✅ 通过 | 注册→登录→发日记→打卡→听歌→兑换 |
| **秘密后台** | ✅ | `/admin` 入口，6 个页面 + `/api/admin/*`（保留 Jinja2 SSR，与 Vue SPA 隔离） |
| **AI 全面接入** | ✅ 可选 | NVIDIA NIM API（`meta/llama-3.1-8b-instruct`），4 个场景；未配 `QI_NVIDIA_API_KEY` 时优雅降级，业务不中断 |
| **种子数据** | ✅ | 5 音 × 3-4 首 = 16 首古琴曲 + 11 件商店物品 + 首个管理员 |
| **文档** | ✅ | README + HANDOFF + 4 个 docs/，6 份文档同步（Iron Rule） |
| **单元测试** | ❌ | 没有 pytest 套件（next agent 可加） |
| **HTTPS** | ❌ | 本地 HTTP，生产需 Nginx 反代 |
| **MySQL** | ❌ | 用 SQLite，将来可换 |

---

## 2. 最近改动（按时间倒序）

### 2026-08-10（v2.4.0）— UI/UX 大改 + 一天多条心情 + 头像/昵称编辑 + 花坊扩充

- [x] 起因：用户要求 18 项 UI/UX 和功能调整，覆盖文案、数据模型、AI、商店、个人主页
- [x] **改动 1：首页文案更新** — '海上有座岛，岛上有人听' → '潮声不止，心安自屿'，删除'静屿'副标题；[HomeView.vue](../../frontend/src/views/HomeView.vue) 文案更新
- [x] **改动 2：删除首页'今日打卡'板块** — [HomeView.vue](../../frontend/src/views/HomeView.vue) 移除今日打卡模块
- [x] **改动 3：'漂流日记'入口统一** — 不管从哪进入，直接显示'日记海岸'界面（含拾瓶/写日记模块）
- [x] **改动 4：情绪日历 emoji 显示/选择修复** — [MoodCalendarView.vue](../../frontend/src/views/mood/MoodCalendarView.vue) emoji 显示/选择修复
- [x] **改动 5：一天多条心情记录**（数据模型 + service 重构）：
  - 移除 `mood_checkins` 表 `(user_id, check_date)` 唯一约束（SQLite 重建表方式：CREATE TABLE _new AS SELECT * → DROP → RENAME → CREATE INDEX），支持一天多次打卡（情绪是多变的）
  - [app/services/mood_service.py](../../app/services/mood_service.py) 重构：`upsert_checkin` → `add_checkin`（不再 UPSERT，允许一天多条）+ 新增 `get_today_moods`（获取今日所有心情）
- [x] **改动 6：30 天心情趋势评分系统**（多条取平均分）：
  - 1-5 评分系统：极度开心=5 / 开心=4 / 平静=3 / 疲惫=2 / 焦虑=2 / 生气=1 / 悲伤=1
  - `get_recent_trend` 多条取**平均分**（MOOD_SCORE 映射：ecstatic=5/happy=4/calm=3/tired=2/anxious=2/angry=1/sad=1）
- [x] **改动 7：心语树洞 AI 系统提示词 humanize** — 更接地气、像朋友聊天
- [x] **改动 8：'落叶画坊' → '花坊'**（改名）— [HomeView.vue](../../frontend/src/views/HomeView.vue) 模块名更新
- [x] **改动 9：花种种类扩充** — 12 种植物：向日葵 / 竹子 / 雏菊 / 莲花 / 薰衣草 / 郁金香 / 梅花 / 桃花 / 兰花 / 青松 / 桂花 / 银杏
- [x] **改动 10：新装扮** — 油纸伞 / 蓑衣 / 乌篷船 / 鱼竿 / 橘猫 / 白鹤
- [x] **改动 11：'古琴初学者' → '琴音知音'**（徽章改名）
- [x] **改动 12：每板块对应徽章** — 琴音知音 / 日记达人 / 七日静心 / 拾瓶旅人 / 树洞倾心 / 花田主人
- [x] **改动 13：'竹编帽'介绍改为'种花人遮阳的草帽'**
- [x] **改动 14：花田 AI 显示基于实际种花情况** — [GardenView.vue](../../frontend/src/views/garden/GardenView.vue) 没种花不显示 AI
- [x] **改动 15：'我的'页面修复** — [ProfileView.vue](../../frontend/src/views/profile/ProfileView.vue) '收到鼓励'/'岛上物件'可点击跳转，删除重复'岛上物件'，新增**静屿使用指南**（详细介绍所有模块功能）
- [x] **改动 16：头像/昵称修改**（模型 + API + schema + 前端）：
  - 模型：[app/models/user.py](../../app/models/user.py) 新增 `User.avatar: str = "🙂"`（String(16)，默认 🙂，与树洞中显示的头像一致）
  - 数据库迁移：`_migrate_legacy_columns()` 加 `ALTER TABLE users ADD COLUMN avatar VARCHAR(16) DEFAULT '🙂' NOT NULL`
  - Schema：新增 [app/schemas/profile.py](../../app/schemas/profile.py) + `ProfileUpdateIn`（nickname 2-20 字符可选 / avatar 1-16 字符可选）
  - Router：`PATCH /api/profile` 更新头像/昵称（昵称查重 409，头像 1-16 字符）
  - 前端：[ProfileView.vue](../../frontend/src/views/profile/ProfileView.vue) 头像/昵称编辑弹窗（24 个可选 emoji）+ [stores/user.js](../../frontend/src/stores/user.js) 新增 `updateProfile` action（调用 PATCH /api/profile）
  - **头像同步树洞**：[AIChatView.vue](../../frontend/src/views/ai/AIChatView.vue) 使用 `userStore.avatar` 显示头像（与个人主页一致）
- [x] **改动 17：露水累加修复** — 写日记和留言鼓励后正确发放露水
- [x] **改动 18：常量扩充** — [app/utils/constants.py](../../app/utils/constants.py) `DEFAULT_SHOP_ITEMS` 扩充至 27 件（12 花种 + 9 装扮 + 6 徽章）；'古琴初学者' → '琴音知音'；'竹编帽' 描述改为'种花人遮阳的草帽'；新增装扮：油纸伞/蓑衣/乌篷船/鱼竿/橘猫/白鹤
- [x] **数据库迁移**（`_migrate_legacy_columns()`）：
  - `ALTER TABLE users ADD COLUMN avatar VARCHAR(16) DEFAULT '🙂' NOT NULL`（v2.4 用户头像）
  - 移除 `mood_checkins` 表 `(user_id, check_date)` 唯一约束（SQLite 重建表方式：CREATE TABLE _new AS SELECT * → DROP → RENAME → CREATE INDEX），支持一天多条心情记录
- [x] 文档同步（Iron Rule）：6 份文档同步更新 — README / HANDOFF / PROJECT_STATE / ARCHITECTURE / DEPLOYMENT / DEVELOPMENT

### 2026-08-10（v2.4.1）— 情绪日历改用罗素情绪环模型四象限图表

- [x] 起因：v2.4.0 的 30 天趋势柱状图只能反映「开心程度」随时间的变化，无法回答「我最近是处于高唤醒的焦虑还是低唤醒的平静」这类二维情绪分布问题。引入罗素情绪环模型（Russell's Circumplex Model of Affect，1980）让用户从「效价 × 唤醒度」二维视角理解情绪分布
- [x] **改动 1：移除 30 天趋势柱状图板块**（`30 天趋势柱状图移除`）：
  - [MoodCalendarView.vue](../../frontend/src/views/mood/MoodCalendarView.vue) 删除 `trendBars` computed（按天数聚合 1-5 评分）
  - 删除 `scoreColor` 函数（按评分映射颜色）
  - 删除 `.trend-section` 模板块（30 根柱子）
  - 删除 `.trend-bar` 样式（柱子渐变色 + 高度动画）
- [x] **改动 2：新增罗素情绪环模型四象限图表**（`四象限图表`，`Russell情绪环模型`，`Circumplex Model`）：
  - [MoodCalendarView.vue](../../frontend/src/views/mood/MoodCalendarView.vue) 新增 `.circumplex-section` 模板
  - 横轴 **效价 Valence**（`效价Valence`，左消极 → 右积极）
  - 纵轴 **唤醒度 Arousal**（`唤醒度Arousal`，下低唤醒 → 上高唤醒）
  - 四象限：Q1(积极+高唤醒，右上) / Q2(消极+高唤醒，左上) / Q3(消极+低唤醒，左下) / Q4(积极+低唤醒，右下)
  - 每个象限淡色背景（治愈系配色）+ 标签（如「积极 · 高唤醒」）
- [x] **改动 3：定义 `CIRCUMPLEX_EMOTIONS` 数组**（`CIRCUMPLEX_EMOTIONS`，`20 种情绪`）：
  - 每个元素 `{ key, label, emoji, valence, arousal, tracked }`
  - `valence` / `arousal` 取值范围 -1~+1（-1 极消极/低唤醒，+1 极积极/高唤醒）
  - **6 种已追踪情绪**（`6 种已追踪`，`tracked: true`）：ecstatic(🤩 valence=+0.9, arousal=+0.8) / happy(😊 +0.7, +0.4) / calm(😌 +0.4, -0.5) / tired(😪 -0.2, -0.8) / anxious(😰 -0.6, +0.7) / angry(😠 -0.8, +0.8) / sad(😢 -0.7, -0.4) —— 映射到后端 [constants.py](../../app/utils/constants.py) `MOOD_INFO`，有真实打卡数据
  - **14 种参考情绪**（`14 种参考`，`tracked: false`）：兴奋 / 激动 / 恐慌 / 恐惧 / 极度烦躁 / 低落 / 压抑 / 倦怠 / 空虚 / 闲适 / 舒心 / 恬淡平和 / 兴致高昂 / 狂喜 —— 补全象限位置，帮助用户理解情绪地图
- [x] **改动 4：点击交互**（`点击交互`）：
  - 点击 emoji → 弹出详情卡片
  - **已追踪情绪**：边框高亮（治愈系 accent 色）+ 右上角小圆点角标显示本月打卡次数；卡片内容「本月出现 X 次」（`本月出现次数` 由 `moodCounts[emotion.key]` 提供）
  - **未追踪情绪**（参考情绪）：无角标；卡片内容「该情绪暂未开放打卡记录」
  - `emotionPosition(emotion)` helper：将 `valence`/`arousal` 坐标转为 CSS `left%` / `top%` 百分比定位
    - `left% = (valence + 1) / 2 * 100`（-1 → 0%，+1 → 100%）
    - `top% = (1 - arousal) / 2 * 100`（+1 → 0% 顶部，-1 → 100% 底部，注意翻转）
- [x] **改动 5：统计 `moodCounts` + `totalCheckins`**：
  - `moodCounts` computed 从 `checkins`（本月打卡数据）按 `mood_emoji` 统计每种心情出现次数（`{ ecstatic: 3, happy: 5, ... }`）
  - `totalCheckins` computed 显示本月总打卡数（所有心情次数之和），显示在四象限图表上方
- [x] **改动 6：视觉设计**：
  - **治愈系配色**：四象限淡色背景（Q1 浅黄积极 / Q2 浅红警示 / Q3 浅蓝低落 / Q4 浅绿平静）+ emoji 圆形背景 + 边框
  - **GSAP 入场动画**：emoji 逐个弹出（`gsap.from('.emotion-dot', { scale: 0, opacity: 0, stagger: 0.05, ease: 'back.out(1.7)' })`，`back.out` 缓动让 emoji 有弹性出现感）
  - **移动端响应式**：图表 `aspect-ratio: 1` 自适应宽度，emoji 字号随屏幕宽度缩放（`clamp(20px, 4vw, 32px)`）；详情卡片移动端居中底部弹出
- [x] **改动 7：保留 `fetchTrend` 调用**：
  - `onMounted` 仍调 `fetchTrend()` 拉取 30 天趋势数据
  - `trend` 数据**不再用于渲染柱状图**——仅用于 `currentStreak`（连续打卡天数）显示在页面顶部连胜卡片
  - **渐进重构**而非「全部删除」，保留向后兼容性
- [x] **新增文件**：无（仅修改 [MoodCalendarView.vue](../../frontend/src/views/mood/MoodCalendarView.vue)）
- [x] **数据库迁移**：无（不改后端模型 / 不改 API / 不改 service）
- [x] 文档同步（Iron Rule）：6 份文档同步更新 — README / HANDOFF / PROJECT_STATE / ARCHITECTURE / DEPLOYMENT / DEVELOPMENT

### 2026-08-13（v2.4.2）— 整体架构优化与冗余清理（维护性清理版本）

- [x] 起因：v2.4.0/v2.4.1 功能迭代后积累冗余——Vue 3 SPA 迁移前遗留的旧 Jinja2 SSR 模板与死页面脚本仍在仓库、main.py 版本号（1.0.0）与 git tag / README badge（2.4.x）不一致、EXT_TO_MIME 字典中 .webp 重复定义、多处端口注释过时（:5173/:5000 残留）、seed.py 引用的五音封面 SVG 缺失、admin_users 接口存在 N+1 查询（151 次）
- [x] **改动 1：删除 15 个死模板 + 1 空目录**（`死模板清理`）：
  - [templates/](../../templates/) 下 Vue 3 SPA 迁移前遗留的旧 Jinja2 SSR 模板全部删除：`base.html` / `_nav.html` / `_toast.html` / `index.html` / `login.html` / `register.html` / `music_list.html` / `diary_write.html` / `diary_detail.html` / `my_bottles.html` / `pick_bottle.html` / `mood_calendar.html` / `garden.html` / `shop.html` / `ai_chat.html`
  - `templates/partials/` 空目录删除
  - **仅保留** [templates/admin/](../../templates/admin/)（[admin_pages.py](../../app/routers/admin_pages.py) 仍使用 Jinja2 SSR）
- [x] **改动 2：删除 10 个死页面脚本**（`死页面脚本`）：
  - [static/js/pages/](../../static/js/pages/) 下非 admin 脚本全部删除：`ai_chat.js` / `auth.js` / `diary.js` / `diary_detail.js` / `home.js` / `mood_calendar.js` / `music.js` / `my_bottles.js` / `pick.js` / `shop.js`
  - 仅被死模板引用，Vue 3 SPA 迁移后已无入口
- [x] **改动 3：[app/main.py](../../app/main.py) 版本号 1.0.0 → 2.4.2**（`版本号对齐`）：与 git tag / README badge 对齐
- [x] **改动 4：[app/main.py](../../app/main.py) `EXT_TO_MIME` 删除重复 `.webp` 条目**（`EXT_TO_MIME`）：字典中定义了两次，删除后者
- [x] **改动 5：修复过时端口注释**（`过时注释`）：
  - [app/routers/pages.py](../../app/routers/pages.py)：`:5173 → :5000`（Vite）
  - [frontend/vite.config.js](../../frontend/vite.config.js)：`:5000 → :5001`（FastAPI 开发）
  - [static/js/app.js](../../static/js/app.js)：端口注释更新
- [x] **改动 6：新增 5 个五音封面 SVG**（`SVG封面`）：
  - [static/img/cover_gong.svg](../../static/img/cover_gong.svg) / `cover_shang.svg` / `cover_jue.svg` / `cover_zhi.svg` / `cover_yu.svg`
  - 颜色取自 [app/utils/constants.py](../../app/utils/constants.py) `YIN_INFO`
  - 修复 [app/seed.py](../../app/seed.py) 引用的缺失资源
- [x] **改动 7：[app/routers/admin_pages.py](../../app/routers/admin_pages.py) admin_users N+1 查询优化**（`N+1优化` / `GROUP BY`）：
  - 原 for 循环内 3 个 COUNT/用户 × 50 用户 = 151 次查询
  - 优化为 1 次查用户 + 3 个 `GROUP BY` 聚合 + 字典拼接 = 4 次查询
- [x] **不动**：[static/css/](../../static/css/) 全部保留（admin/_base.html 加载 style.css）/ [static/js/app.js](../../static/js/app.js) 保留（仅改注释）/ [static/audio/](../../static/audio/) 保留（seed.py 生成占位 mp3）/ [templates/admin/](../../templates/admin/) 保留 / [config.py](../../config.py) / [app/database.py](../../app/database.py) / [requirements.txt](../../requirements.txt) 不动
- [x] **数据库迁移**：无（不改后端模型 / 不改 API / 不改 service）
- [x] 文档同步（Iron Rule）：6 份文档同步更新 — README / HANDOFF / PROJECT_STATE / ARCHITECTURE / DEPLOYMENT / DEVELOPMENT

### 2026-08-14（v2.4.3）— 花语文案焕新 + emoji 名称对齐 + 徽章奖励落叶 + 树洞三层回复 + 情绪日历空 bug 修复

- [x] 起因：用户反馈一系列内容运营 + Bug 修复点——① v2.4.0 改名「琴音知音」后旧徽章「古琴初学者」仍在 seed 残留；② 徽章名「花田主人」太直白；③ 情绪日历页面完全空白（bug）；④ 「没花没落叶、没落叶种不了花」死锁；⑤ 花田 AI 在没种花时显示无关花朵；⑥ 缺少 emoji 标识岛上物件 section；⑦ 首页沙滩 emoji 不贴合海意；⑧ 树洞只会重复消极情绪不做有用共鸣；⑨ 花种 emoji 和名称对不上（薰衣草配紫色爱心、桂花配麦子、白鹤配火烈鸟、蓑衣配斗篷、兰花+梅花都是樱花）；⑩ 花种介绍太直白（花中皇后）；⑪ 缺少动物装扮；⑫ 漂流瓶 emoji 🍶 不够正式；⑬ 板块名「花坊」不够点题
- [x] **改动 1：删除「古琴初学者」废弃徽章**（`废弃徽章删除`）：[app/seed.py](../../app/seed.py) 启动时清理 `DEPRECATED_BADGES = ["古琴初学者"]`，含 GardenItem 引用一并删除
- [x] **改动 2：「花田主人」→「花间客」**（`花间客改名`）：[constants.py](../../app/utils/constants.py) 徽章名 + seed `RENAME_MAP` 迁移表 + [ProfileView.vue](../../frontend/src/views/profile/ProfileView.vue) 使用指南同步
- [x] **改动 3：「花坊」→「落叶花坊」**（`落叶花坊改名`）：[HomeView.vue](../../frontend/src/views/HomeView.vue) 模块名 + [GardenView.vue](../../frontend/src/views/garden/GardenView.vue) 入口 + ProfileView 使用指南同步
- [x] **改动 4：情绪日历空白 Bug 修复**（`情绪日历空白修复`）：[MoodCalendarView.vue](../../frontend/src/views/mood/MoodCalendarView.vue) 月历空单元格 `cell.moodKeys.length` 抛 `TypeError: Cannot read properties of undefined`，整页渲染中断显示空白；修复为 `cell.moodKeys?.length > 0`（含 moodInfos 同步加可选链 `cell.moodInfos?.length`）
- [x] **改动 5：落叶死锁解除**（`落叶死锁解除` / `BADGE_LEAF_REWARD`）：
  - [constants.py](../../app/utils/constants.py) 新增 `BADGE_LEAF_REWARD: Final[int] = 10`
  - [energy_service.py](../../app/services/energy_service.py) `check_achievements()` 每解锁一个徽章额外发放 10 落叶，返回 `{new_badges, new_leaves, leaves_balance}`（用 `db.query(User).filter(...).update({User.leaves: User.leaves + reward})` + `db.flush()`，取 DB 最新落叶余额返回避免 `expire_on_commit=False` 旧值问题）
  - mood / diary / music / ai / energy 5 路由透传返回字段
  - 前端 [MoodCalendarView](../../frontend/src/views/mood/MoodCalendarView.vue) / [DiaryWriteView](../../frontend/src/views/diary/DiaryWriteView.vue) / [PickBottleView](../../frontend/src/views/diary/PickBottleView.vue) / [AIChatView](../../frontend/src/views/ai/AIChatView.vue) 接 toast「解锁徽章「X」· 赠 10 落叶」+ 更新 `userStore.leaves` 余额
- [x] **改动 6：花田 AI 显示基于实际种花**（`花田 AI 显示修复`）：[GardenView.vue](../../frontend/src/views/garden/GardenView.vue) `<FlowerField v-if="flowers.length > 0" />`，未种花时不渲染 3D 花田（避免空花田显示 AI 生成无关花朵）
- [x] **改动 7：岛上物件 emoji 化**（`岛上物件 emoji`）：[GardenView.vue](../../frontend/src/views/garden/GardenView.vue) 「🏝️ 岛上物件」section 头部加 emoji
- [x] **改动 8：首页 emoji 🏝️ → 🌊**（`首页海浪 emoji`）：[HomeView.vue](../../frontend/src/views/HomeView.vue) hero-icon 由沙滩 🏝️ 改为海浪 🌊，更贴合「静屿」海意；[EmojiIcon.vue](../../frontend/src/components/EmojiIcon.vue) twemoji 映射 `🏝️ desert-island` 移除，新增 `🌊 wave`
- [x] **改动 9：树洞 AI 重写**（`树洞三层回复`）：[ai_service.py](../../app/services/ai_service.py) `SYSTEM_PROMPT_TREEHOLE` 重写为三层结构——① 接住情绪（1 句，准确点出感受，不复述原话）② 安慰或新视角（1-2 句，温暖肯定 / 温柔宽慰 / 换个角度）③ 具体可操作的小建议或问题（1-2 句，小 / 具体 / 现在就能做），解决旧版「只重复消极情绪、做无用情感共鸣」问题
- [x] **改动 10：花种 emoji 与名称对齐 + 花语化**（`花语化` / `emoji 对齐`）：
  - 12 种花种介绍全部改为「花语：XX」格式——向日葵「信念与爱慕」/ 竹子「坚韧虚心」/ 雏菊「天真纯洁」/ 莲花「清白坚贞」/ 薰衣草「等待爱情」/ 郁金香「完美的爱」/ 樱花「生命之美」/ 桃花「爱情降临」/ 青松「坚定长寿」/ 小麦「丰收富足」/ 青叶「生机新生」
  - emoji 与名称对齐——薰衣草 💜→🪻（紫花浪漫）/ 桂花→小麦 🌾 / 银杏→青叶 🍃 / 兰花+梅花合并为樱花 🌸（删一留一，seed 去重）/ 白鹤→火烈鸟 🦩 / 蓑衣→斗篷 🧥
- [x] **改动 11：装扮动物扩充**（`动物扩充`）：[constants.py](../../app/utils/constants.py) 新增 3 件动物装扮——小鸟 🐦 / 小鸭 🦆 / 小狗 🐶
- [x] **改动 12：漂流瓶 emoji 🍶 → 🏺**（`漂流瓶 emoji`）：[HomeView.vue](../../frontend/src/views/HomeView.vue) 漂流日记 icon + [DiaryWriteView](../../frontend/src/views/diary/DiaryWriteView.vue) 发布选项 + [EmojiIcon.vue](../../frontend/src/components/EmojiIcon.vue) twemoji 映射 `🍶 sake` 移除，新增 `🏺 amphora`；拾瓶旅人徽章 🏺 与板块入口一致
- [x] **改动 13：seed 改名迁移 + 去重**（`改名迁移` / `去重`）：[app/seed.py](../../app/seed.py) 启动时按 `RENAME_MAP` 改名老库物品（桂花→小麦 / 银杏→青叶 / 兰花+梅花→樱花 / 白鹤→火烈鸟 / 蓑衣→斗篷 / 花田主人→花间客）+ 合并同名重复（如兰花+梅花都改名为樱花时保留 id 最小的，GardenItem 引用迁移到 keeper）
- [x] **改动 14：版本号 2.4.2 → 2.4.3**（`版本号对齐`）：[app/main.py](../../app/main.py) `version="2.4.3"` + README badge v2.4.3 + 6 份文档同步
- [x] **Smoke test 结果**（2026-08-14 实测）：
  - `python start.py restart` ✅
  - `curl /api/shop/items` 200（27 件，含新动物 + 花语介绍）✅
  - 情绪日历页面非空（可选链修复后正常渲染）✅
  - 树洞回复含建议（三层结构生效）✅
  - 花田未种花不显示 3D（v-if 守卫生效）✅
- [x] **数据库迁移**：无（不改后端模型结构，仅 seed 启动时改名 / 去重 / 删废弃行）
- [x] 文档同步（Iron Rule）：6 份文档同步更新 — README / HANDOFF / PROJECT_STATE / ARCHITECTURE / DEPLOYMENT / DEVELOPMENT

### 2026-08-15（v2.4.4）— 情绪日历透明修复 + 旧版日记迁移 + mood_checkins 主键重建 + 头像图片上传 + 落叶花坊文案打磨

- [x] 起因：用户反馈一系列可见性 / 数据完整性 / 表结构问题——① 情绪日历心情选择按钮几乎不可见（GSAP `opacity:0`）；② 旧版加密日记 `content` 字段为空（`content_encrypted` 是假占位符）；③ 批量打卡 500（`mood_checkins` 表丢失主键，`db.flush()` 报 `NULL identity key`）；④ `User.avatar` 字段太短存不下图片 URL（`String(16)`）；⑤ 缺少头像图片上传能力；⑥ 花坊介绍「花语：」前缀冗余；⑦ 徽章奖励落叶统一值不够分级；⑧ 情绪日历使用指南不够专业；⑨ 岛上物件 emoji 不够贴合；⑩ 通知 emoji 风格不一致
- [x] **改动 1：[BUG FIX] 情绪日历 emoji 透明**（`情绪日历透明修复`）：[MoodCalendarView.vue](../../frontend/src/views/mood/MoodCalendarView.vue) GSAP 动画设置了 `opacity:0` 导致心情选择按钮几乎不可见，已移除该属性
- [x] **改动 2：[BUG FIX] 旧版日记无内容**（`旧版日记迁移`）：旧版加密日记 `content` 字段为空（`content_encrypted` 是假占位符），数据库迁移自动填入提示文本「（这段日记来自旧版本，内容已无法读取）」
- [x] **改动 3：[BUG FIX] mood_checkins 表缺失 PRIMARY KEY**（`mood_checkins 主键重建`）：v2.4 的迁移用了 `CREATE TABLE AS SELECT` 导致 `mood_checkins` 表丢失主键和自增，批量打卡时 `db.flush()` 报 `NULL identity key` 错误（500）。已重建表（`id INTEGER PRIMARY KEY AUTOINCREMENT` + FK + 索引），数据完整迁移
- [x] **改动 4：[BUG FIX] avatar 字段长度**（`avatar 字段长度`）：[User.avatar](../../app/models/user.py) 原为 `String(16)`，无法存储图片上传后的 URL 路径（如 `/static/uploads/avatars/1_1234567890.jpg`）。已改为 `String(255)`，[ProfileUpdateIn](../../app/schemas/profile.py) schema 同步调整为 `max_length=255`
- [x] **改动 5：[FEATURE] 头像支持图片上传**（`头像图片上传`）：新增 `POST /api/profile/avatar` 端点，支持 JPG/PNG/WebP/GIF（≤2MB），存储到 `static/uploads/avatars/`（目录不存在自动创建）；[ProfileView.vue](../../frontend/src/views/profile/ProfileView.vue) 增加上传按钮（支持拍摄/相册选择），[AIChatView.vue](../../frontend/src/views/ai/AIChatView.vue) 支持图片头像渲染
- [x] **改动 6：[IMPROVEMENT] 落叶花坊花朵介绍**（`花朵介绍`）：移除「花语：」前缀，只保留完整花语
- [x] **改动 7：[IMPROVEMENT] 徽章落叶奖励分级**（`徽章落叶分级`）：按徽章 trigger 分级设置落叶奖励（streak_7=7, listen_10=10, pick_10=10, flower_10=10, chat_20=15, diary_30=20, 默认=10），替代原来统一的固定值
- [x] **改动 8：[IMPROVEMENT] 情绪日历使用指南更新**（`情绪日历指南`）：介绍改为罗素情绪环模型（Russell's Circumplex Model）四象限说明
- [x] **改动 9：[IMPROVEMENT] 岛上物件 emoji**（`岛上物件 emoji`）：🎁 → 🧳（行李箱）
- [x] **改动 10：[IMPROVEMENT] 通知 emoji 统一**（`通知 emoji 统一`）：漂流瓶回复通知的 emoji 统一为 💛（黄色爱心）
- [x] **Smoke test 结果**（2026-08-15 实测）：
  - `python start.py restart` ✅
  - 情绪日历心情按钮可见（移除 `opacity:0` 后正常显示）✅
  - 旧版日记显示提示文本（迁移填充生效）✅
  - 批量打卡不再 500（主键重建生效）✅
  - 头像上传 200（`POST /api/profile/avatar` 端点正常）✅
- [x] **数据库迁移**：
  - `mood_checkins` 表重建（`id INTEGER PRIMARY KEY AUTOINCREMENT` + FK + 索引，数据完整迁移）
  - `User.avatar` 字段长度 `String(16)` → `String(255)`（`_migrate_legacy_columns()` 自动 ALTER）
  - 旧版加密日记 `content` 字段为空时自动填入提示文本
- [x] 文档同步（Iron Rule）：6 份文档同步更新 — README / HANDOFF / PROJECT_STATE / ARCHITECTURE / DEPLOYMENT / DEVELOPMENT

### 2026-07-30（v2.3.3）— Safari 兼容性修复（3D 上下文恢复 + emoji 跨浏览器一致）

- [x] 起因：Safari / iOS 用户反馈两类问题——① 主页 3D 浮岛场景不渲染（直接降级 SVG 或黑屏）；② 导航 / 个人主页 emoji 显示风格与 Chrome 不一致（Apple Color Emoji vs 系统 emoji）
- [x] **改动 1：Safari 主页 3D 不渲染修复**（3 个根因逐一解决）：
  - **`hasWebGL` 重写**：[utils/visual.js](../../frontend/src/utils/visual.js) 原 `hasWebGL()` 仅尝试 WebGL2，老 Safari 只支持 WebGL1 被误判无 WebGL → 降级 SVG。重写为区分 WebGL1/2（先试 WebGL2 失败再试 WebGL1）+ 检测扩展 + max texture size
  - 新增 `getWebGLCaps()` / `isSafari()` / `isIOS()` 工具函数（`getWebGLCaps` 检测 `EXT_color_buffer_half_float` 等关键扩展）
  - [three-helpers.js](../../frontend/src/utils/three-helpers.js) 添加 `webglcontextlost` / `webglcontextrestored` 事件监听，处理 **WebGL 上下文丢失**（iOS Safari 切后台→前台时触发）：`webglcontextlost` 时 `event.preventDefault()` + 保存场景状态；`webglcontextrestored` 时重建 renderer + 恢复场景状态 + 重启 rAF
  - [HeroScene.vue](../../frontend/src/components/HeroScene.vue) **iOS 降级**策略降低内存压力：**Bloom 降级**（iOS 关闭 `UnrealBloomPass`）+ **PMREM 降级**（iOS PMREM 256→128、阴影 2048→1024、dpr 上限 2→1.5；老 iOS 缺 `EXT_color_buffer_half_float` 扩展时完全关闭 PMREM + Bloom）
- [x] **改动 2：Safari emoji 显示不一致修复**：
  - 新建 [EmojiIcon.vue](../../frontend/src/components/EmojiIcon.vue) 组件，使用 **Iconify** + `@iconify-json/twemoji` 离线 **SVG emoji**（twemoji 风格统一扁平彩色），确保 **跨浏览器一致**
  - 替换 [AppLayout.vue](../../frontend/src/components/AppLayout.vue)（品牌 / 导航 / 通知 / 资源）+ [ProfileView.vue](../../frontend/src/views/profile/ProfileView.vue)（头像 / 通知 / 资源 / 统计 / 快捷入口 / 花朵阶段）所有 emoji
- [x] **Smoke test 结果**（2026-07-30 实测）：
  - `npm run build` ✅ 通过：209 modules / 12.30s，HeroScene +0.71KB（降级逻辑）
  - Safari 主页 3D 浮岛场景正常渲染（不再降级 SVG）✅
  - iOS Safari 切后台→前台后 3D 场景恢复（不再黑屏）✅
  - Safari / Chrome emoji 风格一致（twemoji SVG）✅
- [x] 文档同步（Iron Rule）：6 份文档同步更新 — README / HANDOFF / PROJECT_STATE / ARCHITECTURE / DEPLOYMENT / DEVELOPMENT

### 2026-07-28（v2.3.2）— start.py 默认生产模式 + 自动构建简化

- [x] 起因：v2.2.2 默认应用模式让 Vite 占 :5000，但服务器端口代理已配好 :5000 不能动，应用模式会破坏代理。回滚为默认生产模式
- [x] **改动 1：[start.py](../../start.py) 默认行为变更** — 回滚 v2.2.2，默认走生产模式：
  - 默认（无参数）：FastAPI :5000 单进程（生产模式），Vite 不运行
  - **`dist 存在检测`**：仅检测 `static/dist/index.html` 存在性，不再比较 `frontend/src/` 与 `static/dist/` 文件修改时间
  - **`自动构建`**：dist 不存在时自动 `npm install + npm run build`（需 Node.js 18+）
  - `--dev` 改为显式应用模式（Vite :5000 HMR + FastAPI :5001 API，前后端一起起的「应用模式」）
  - `--prod` 改为兼容别名（默认就是生产模式，加不加效果一样）
- [x] **改动 2：服务器部署简化** — 从 3 步简化为 2 步：① 上传代码 ② `python start.py`（首次自动构建，之后秒启，FastAPI 单进程 :5000）
- [x] 文档同步（Iron Rule）：6 份文档同步更新 — README / HANDOFF / PROJECT_STATE / ARCHITECTURE / DEPLOYMENT / DEVELOPMENT

### 2026-07-25（v2.3）— 六大四字名板块重构 + 双资源系统 + 花朵生命周期 + 通知 + 个人主页 + 古琴弹西洋曲谱

- [x] 起因：用户要求按治愈系调性对模块重命名 + 双资源经济 + 花朵生命周期 + 通知 + 个人主页 + 西方曲谱子菜单 + 日记调整 + 情绪日历对齐修复 + 树洞改进 + 漂流瓶评论返回通知（共 10 项大改）
- [x] **改动 1：主界面六大四字名板块**（替换原底部「五音疗愈」板块）+ 顶部品牌图标更新：
  - 六大板块 + 2 个辅助入口（共 8 项 navItems）：琴音疗心（`/music` 🎵）/ 漂流日记（`/diary` 📖）/ 拾瓶（`/diary/pick` 🍶，无漂流瓶 emoji 故保留原香槟瓶）/ 情绪日历（`/calendar` 🌙）/ 心语树洞（`/ai-chat` 🌳）/ 落叶画坊（`/shop` 🍂）/ 屿上花田（`/garden` 🌸）/ 我的（`/profile` 👤）
  - [AppLayout.vue](../../frontend/src/components/AppLayout.vue) 顶部品牌图标由 🌿 草本更新为 🏝️ 岛屿 emoji；桌面/平板/移动三档导航同步四字短标签
  - 移动端 tabbar 4 项固定（静屿 / 漂流日记 / 情绪日历 / 我的）+ 中央「更多」抽屉（琴音疗心 / 拾瓶 / 心语树洞 / 落叶画坊 / 屿上花田）
- [x] **改动 2：双资源系统（露水 + 落叶）** + 数据库迁移 + seed 更新：
  - 模型：[app/models/user.py](../../app/models/user.py) 保留 `total_energy`（露水）+ 新增 `leaves: int = 0`（落叶）；[app/models/garden.py](../../app/models/garden.py) `ShopItem` 加 `cost_currency: str = "dew"`（dew 露水 / leaves 落叶）
  - 迁移：[app/database.py](../../app/database.py) `_migrate_legacy_columns()` 加 `ALTER TABLE users ADD COLUMN leaves INTEGER DEFAULT 0 NOT NULL` + `ALTER TABLE shop_items ADD COLUMN cost_currency VARCHAR(20) DEFAULT 'dew' NOT NULL`
  - 常量：[app/utils/constants.py](../../app/utils/constants.py) `DEFAULT_SHOP_ITEMS` 11 件物品全部带 `cost_currency`：5 件花种 = `leaves`，3 件装扮 = `dew`，3 件徽章 = `dew`（自动触发）
  - seed：[app/seed.py](../../app/seed.py) `seed_shop_items()` 对老库回填 `UPDATE shop_items SET cost_currency='leaves' WHERE item_type='flower' AND cost_currency='dew'`
  - **资源哲学**：露水（不可兑换）= 听歌 / 写日记 / 打卡获得，用于浇灌已播种花朵；落叶 = 花朵枯萎后拾取获得，用于在落叶画坊兑换花种（寓意「落叶归根能施肥种花」）
  - 前端：[GardenView.vue](../../frontend/src/views/garden/GardenView.vue) / [ShopView.vue](../../frontend/src/views/garden/ShopView.vue) / [ProfileView.vue](../../frontend/src/views/profile/ProfileView.vue) 双资源条同步显示
- [x] **改动 3：花朵生命周期**（新模型 + service + API + 前端）：
  - 模型：[app/models/garden.py](../../app/models/garden.py) 新增 `UserFlower`（id / user_id / flower_type / stage / watered_count / planted_at / last_watered_at / bloom_at / wilted_at）+ 5 阶段常量 `STAGE_SEED/STAGE_SPROUT/STAGE_BUD/STAGE_BLOOM/STAGE_WILTED` + `WATER_TO_NEXT_STAGE` 浇水阈值 + `WILT_DAYS_AFTER_BLOOM = 7`
  - Service：[app/services/flower_service.py](../../app/services/flower_service.py) — `list_my_flowers` / `water_flower` / `collect_wilted_leaves` / `get_flower_detail`；阶段 `seed → sprout → bud → bloom → wilted`，每浇 1 次消耗 1 露水，达阈值升级；盛开 7 天未浇水 lazy 标记枯萎；拾取枯花 → +2 落叶 → 删除该花
  - API：[app/routers/garden.py](../../app/routers/garden.py) 新增 `GET /api/garden/flowers` / `GET /api/garden/flowers/{id}` / `POST /api/garden/flowers/{id}/water` / `POST /api/garden/flowers/{id}/collect`
  - 前端：[GardenView.vue](../../frontend/src/views/garden/GardenView.vue) `STAGE_INFO` 映射（emoji/label/progress/desc）+ 浇水按钮（消耗 1 露水）+ 拾取按钮（枯花 → 落叶）+ 移动端单列网格
- [x] **改动 4：通知系统**（新模型 + router + 前端轮询）：
  - 模型：[app/models/notification.py](../../app/models/notification.py) 新增（id / user_id / type / content / related_id / is_read / created_at）；类型：`encouragement`（漂流瓶评论返回）/ `system`（预留）
  - Router：[app/routers/notification.py](../../app/routers/notification.py)（**单数形式**）— `GET /api/notifications` / `GET /api/notifications/unread` / `POST /api/notifications/{id}/read` / `POST /api/notifications/read-all`
  - 触发点：漂流瓶被评论 → 写 `Notification(type='encouragement', user_id=作者, related_id=diary_id)`，作者下次进入应用看到未读提醒
  - 前端：[AppLayout.vue](../../frontend/src/components/AppLayout.vue) 顶部 + 移动端 topbar 加 🔔 铃铛 + 红点未读数；`onMounted` 起 60s 轮询 `/api/notifications/unread`；点击跳 `/notifications` 页（非下拉）
  - 页面：[NotificationsView.vue](../../frontend/src/views/notification/NotificationsView.vue) 列表 + 未读高亮 + 单条已读 + 全部已读
- [x] **改动 5：个人主页**（新 router + 前端视图）：
  - Router：[app/routers/profile.py](../../app/routers/profile.py) — `GET /api/profile`（自己）/ `GET /api/profile/stats`（轻量统计）/ `GET /api/profile/{user_id}`（他人，仅公开信息）
  - 统计字段：`diary_count` / `public_diary_count` / `checkin_count` / `listen_count` / `flower_count` / `garden_item_count` / `received_encouragement_count` / `streak`（连续打卡）
  - 前端：[frontend/src/views/profile/ProfileView.vue](../../frontend/src/views/profile/ProfileView.vue) — 卡片式布局：🏝️ 头像 + 昵称 + 在岛天数 + 双资源条（露水/落叶）+ 6 统计卡（日记/打卡/听曲/花朵/收到鼓励/岛上物件）+ 快捷入口
  - 路由：`/profile` + `/notifications` 加入 `requiresAuth: true` 守卫
- [x] **改动 6：古琴弹西洋曲谱子菜单**（数据库迁移 + seed 幂等 + API 参数 + 前端路由）：
  - 模型：[app/models/music.py](../../app/models/music.py) 加 `category: str = "classic"`（classic 五音古曲 / western 古琴弹西洋）
  - 迁移：`_migrate_legacy_columns()` 加 `ALTER TABLE musics ADD COLUMN category VARCHAR(20) DEFAULT 'classic' NOT NULL`
  - 常量：[app/utils/constants.py](../../app/utils/constants.py) 新增 `class MusicCategory(str, Enum)`：`CLASSIC = "classic"` / `WESTERN = "western"`
  - seed：[app/seed.py](../../app/seed.py) `SEED_MUSIC` 加 6 首西方改编——绿袖子（yu）/ 卡农（gong）/ 致爱丽丝（jue）/ 月光奏鸣曲（yu）/ 天鹅湖（shang）/ 昨日重现（zhi）；**`seed_music()` 改为按 title 幂等**（不再「表空才插」），老库重启即自动补齐 western 曲目
  - API：[app/routers/music.py](../../app/routers/music.py) `GET /api/music?category=western` 加 query 参数过滤
  - 前端：[MusicListView.vue](../../frontend/src/views/music/MusicListView.vue) 底部加「古琴弹西洋」入口卡片；新视图 [MusicWesternView.vue](../../frontend/src/views/music/MusicWesternView.vue) 按五音分组展示 + 内置播放器 + AudioVisualizer
  - 路由：[frontend/src/router/index.js](../../frontend/src/router/index.js) 加 `/music/western`（**必须放在 `/music/:yin` 前面**避免动态段捕获）+ `/profile` + `/notifications`
- [x] **改动 7：日记调整**（明文化 + 发布选项 + 前端）：
  - 模型：[app/models/diary.py](../../app/models/diary.py) `content: Text` 明文（v2.3 起替代 `content_encrypted`，移除密码保护）；新增 `send_to_ai_hole: bool = False`；保留 `is_public` + `mood_type`
  - 迁移：`_migrate_legacy_columns()` 加 `ALTER TABLE diaries ADD COLUMN content TEXT NOT NULL DEFAULT ''` + `ADD COLUMN send_to_ai_hole BOOLEAN DEFAULT 0 NOT NULL`
  - `User.encryption_salt` 保留仅为兼容老库（v2.3 起不再使用）
  - 发布选项（前端 radio）：放入漂流瓶（`is_public=True`，公开可见 + 允许评论）/ 不放入漂流瓶（`is_public=False`，仅自己可见 + 可选 `send_to_ai_hole=True` 同步至心语树洞）
  - 前端：[DiaryWriteView.vue](../../frontend/src/views/diary/DiaryWriteView.vue) 移除 emoji 选择器 + 移除密码 UI + 加发布选项 radio + 加 SVG 海浪动画（日记海岸主题）
- [x] **改动 8：情绪日历对齐修复**（前后端字段一致 + emoji 完整显示）：
  - 修复：前端 `MoodCalendarView.vue` 原用 `mood_type` + `date`，后端 `MoodCheckin` 用 `mood_emoji` + `check_date`；统一改为后端字段名（前端兼容旧字段）
  - [app/utils/constants.py](../../app/utils/constants.py) `MOOD_INFO` 7 种心情：ecstatic 🤩 / happy 😊 / calm 😌 / tired 😪 / anxious 😰 / angry 😠 / sad 😢
  - 前端 `MOOD_INFO` 同步 7 种 + 日历加心情图例（legend）解决「emoji 显示不全」问题
- [x] **改动 9：树洞改进**（统一图标 + 文本输入 + 文件式聊天历史 + 留存提示）：
  - 统一图标：AIChatView + AppLayout 导航 + tabbar 全部用 🌳 树形 emoji（替代原 🌿）
  - 文本输入：[AIChatView.vue](../../frontend/src/views/ai/AIChatView.vue) 加 `<textarea>` 多行输入框（原仅单行 input）
  - 文件式聊天历史：[app/services/chat_history_service.py](../../app/services/chat_history_service.py) 新增——存于 `data/chat_history/<user_id>/<conversation_id>.json`；`create_conversation` / `load_messages` / `append_message` / `list_conversations` / `delete_conversation` / `get_or_create_conversation`；单对话上限 100 条；每次 AI 调用前加载历史
  - 留存提示：每次聊天结束时树洞询问用户是否保留记录；选「不保留」则 `delete_conversation` 删文件
  - 上下文增强：树洞根据用户当日 `MoodCheckin.mood_emoji` + 当日 `Diary.content`（若 `send_to_ai_hole=True`）提供针对性聊天和安慰
- [x] **改动 10：漂流瓶评论返回 + 通知集成**：
  - 读者在拾瓶后留鼓励语 → 写 `Encouragement` + 同步写 `Notification(type='encouragement', user_id=作者, related_id=diary_id)`
  - 作者顶部 🔔 红点 + 60s 轮询 `/api/notifications/unread` → 点击跳 `/notifications` → 单条已读 → 跳回原日记
- [x] **数据库迁移**（`_migrate_legacy_columns()` 一次性自动加列 + `init_db()` 建新表）：
  - `users` 加 `leaves INTEGER DEFAULT 0 NOT NULL`
  - `diaries` 加 `content TEXT NOT NULL DEFAULT ''` + `send_to_ai_hole BOOLEAN DEFAULT 0 NOT NULL`
  - `shop_items` 加 `cost_currency VARCHAR(20) DEFAULT 'dew' NOT NULL`
  - `musics` 加 `category VARCHAR(20) DEFAULT 'classic' NOT NULL`
  - 新表 `user_flowers` / `notifications` 由 `init_db()` 自动建表（Base.metadata.create_all）
- [x] 文档同步（Iron Rule）：6 份文档同步更新 — README / HANDOFF / PROJECT_STATE / ARCHITECTURE / DEPLOYMENT / DEVELOPMENT
- [x] **Smoke test 结果**（2026-07-25 实测）：
  - `python -m py_compile` 9 个新/改文件 ✅ 通过
  - `python -c "import app.main"` ✅ IMPORT OK，69 routes total，55 in OpenAPI
  - `npm run build` ✅ 通过：206 modules，MusicWesternView 6.61KB / ProfileView 9.59KB / NotificationsView 4.18KB / three-vendor 719.84KB
  - `GET /api/music?category=western` ✅ 返回 6 首西方改编曲目（绿袖子/卡农/致爱丽丝/月光奏鸣曲/天鹅湖/昨日重现）
  - `GET /api/notifications` / `/api/notifications/unread` / `/api/profile` / `/api/profile/stats` / `/api/garden/flowers` ✅ 全部 200/401（守卫生效）
  - `GET /` ✅ SPA fallback 返回 dist/index.html（含 `viewport-fit=cover` meta + `<div id="app">` 挂载点）
  - `_migrate_legacy_columns()` ✅ 跑通（老库自动加 5 个新列 + 2 张新表）
  - seed_music 幂等 ✅（重启后自动补齐 6 首西方曲目，已有曲目不重复插入）

### 2026-07-25（v2.2.3）— 移动端响应式 UI + 3D 几何降档

- [x] 起因：用户要求「不同设备不同 UI 布局，考虑手机屏幕小不能展示所有功能，iPhone 16 默认浏览器 Safari 导航和搜索栏在底部，UI 要自适应」
- [x] **改动 1：三档断点系统差异化布局**（[frontend/src/components/AppLayout.vue](../../frontend/src/components/AppLayout.vue) + [frontend/src/assets/styles/main.css](../../frontend/src/assets/styles/main.css)）：
  - 桌面（≥1025px）：顶部完整导航（7 项 + 能量条 + 离开按钮）
  - 平板（769-1024px）：顶部紧凑导航（图标 + 短标签纵向排列）
  - 移动端（≤768px）：顶部精简 topbar（品牌 + 能量 + 登录）+ 底部 tabbar（4 个固定核心 + 中央「更多」按钮 → 抽屉展开 3 项次要入口）
- [x] **改动 2：iOS Safari 底部地址栏 + iPhone 刘海/Home Indicator 适配**：
  - `100dvh` + `100vh` 兜底（应对 iOS 16+ Safari 底部地址栏出现/消失时视口跳变）
  - `env(safe-area-inset-top)` 避让刘海/灵动岛（topbar 顶部 padding）
  - `env(safe-area-inset-bottom)` 避让 Home Indicator（tabbar 底部 padding）
  - `.safe-top` / `.safe-bottom` 工具类 + 三档断点工具类（`.mobile-only` / `.tablet-only` / `.desktop-only` 等）
- [x] **改动 3：fullscreen 路由模式** — `route.meta.fullscreen = true` 时隐藏 topbar + tabbar，main 占满 `100dvh`（AIChatView 等全屏场景用，避免 tabbar 遮挡聊天输入框）
- [x] **改动 4：核心视图移动端差异化布局**（13 个视图全部覆盖）：
  - HomeView：五音卡片改横向滚动 + scroll-snap；模块入口改单列大卡片；hero 用 `min(380px, 60svh)` 适配小屏
  - MusicDetailView：播放器底部 offset `calc(72px + env(safe-area-inset-bottom))` 避让 tabbar；toast 抬高到 tabbar 之上
  - DiaryListView：时间轴线左移到 21px；diary-item 紧凑 padding；toast 避让 tabbar
  - GardenView：花田花朵数 60→36（移动端）；3D 场景高度 380px→280px
  - MoodCalendarView：日历网格移动端单列大单元格
  - ShopView：物品网格移动端 2 列
  - LoginView / RegisterView：移动端减小内边距 + 字号
  - AIChatView：fullscreen 模式 + 输入框避让 Home Indicator
- [x] **改动 5：4 个 3D 组件移动端几何精度降档**（在原有「粒子减半 + dpr≤1.5 + Bloom 降强度」基础上进一步降顶点数）：
  - [HeroScene.vue](../../frontend/src/components/HeroScene.vue)：浮岛 LatheGeometry 段数 24→16、岛顶 CylinderGeometry 段数 24→16、樱花树递归深度 4→3（指数级降顶点）、花团 IcosahedronGeometry detail 2→1（顶点数 1/4）、树枝圆柱段数 6→5
  - [FlowerField.vue](../../frontend/src/components/FlowerField.vue)：花瓣 BufferGeometry 网格 5×8→4×6（顶点数 ↓约 50%）、花蕊 IcosahedronGeometry detail 2→1、地面 CircleGeometry 段数 64→32、花茎 CylinderGeometry 段数 6→5
  - [AudioVisualizer.vue](../../frontend/src/components/AudioVisualizer.vue)：镜像柱状模式柱数 48→32、径向频谱模式柱数 64→32（减少 Canvas2D 绘制次数）
  - [AmbientBackground.vue](../../frontend/src/components/AmbientBackground.vue)：已优化（dpr 1.25 / Canvas2D 粒子 24 / Three.js 粒子 50 / 近景粒子 20 / Bloom 0.12）保留
- [x] 文档同步（Iron Rule）：6 份文档同步更新 — README §3.5/§8、HANDOFF §5.10、PROJECT_STATE §1（本条 + 总体状态表）、ARCHITECTURE §1.1.6/§7.7、DEPLOYMENT 顶部 Iron Rule、DEVELOPMENT §1.9.4
- [x] 验证：① `npm run build` 通过，无编译错误；② 浏览器 DevTools 模拟 iPhone 16（390×844）→ 顶部 topbar + 底部 tabbar + 「更多」抽屉 + 各视图差异化布局生效；③ DevTools 模拟 iPad（834×1194）→ 平板紧凑导航；④ DevTools 切到桌面 → 完整顶部导航；⑤ Performance 面板录 3D 场景，移动端帧率稳定 50-60fps（几何降档前 35-45fps）

### 2026-07-25（v2.2.2）— start.py 默认应用模式（前后端一起起 + 自动 npm install）

- [x] 起因：用户要求「`python start.py` 启动时是应用模式不是生产模式，前后端一起启动，且检测到没有编译的时候自动编译」。v2.2.1 默认走生产模式（dist 未构建时自动 `npm install + npm run build` 后走 FastAPI 单进程）不符合用户对「应用模式 = 前后端一起跑 + HMR 热更新」的预期
- [x] **改动 1：[start.py](../../start.py) 默认行为变更** — 回滚 v2.2.1，默认走应用/开发模式：
  - 默认（无参数）：Vite 占 :5000（HMR）+ FastAPI 改听 :5001（API），前后端一起起
  - 自动检测 `frontend/node_modules` 不存在 → 自动 `npm install`（约 7 分钟，仅首次），**不再** `npm run build`（应用模式用 Vite dev server 不需要构建产物）
  - Node.js 不可用 → 报错退出（提示装 Node.js 18+ 或用 `--prod` 走生产模式）
- [x] **改动 2：新增 `--prod` 参数** — `python start.py --prod` 显式生产模式：
  - FastAPI 监听 :5000（从 .env 读 QI_PORT），Vite 不运行
  - 需 `static/dist/` 已构建（未构建报错退出，提示先 `python start.py build` 或不加 `--prod` 走默认应用模式）
- [x] **改动 3：`--dev` 改为兼容别名** — 等同默认行为（应用/开发模式），保留向后兼容（v2.2.1 时 `--dev` 是强制开发模式的开关）
- [x] **改动 4：`fg` 子命令默认也是应用模式** — `python start.py fg` 前台运行 FastAPI（默认应用模式，可加 `--prod` 切生产）。fg 模式不自动起 Vite，应用模式需单独 `cd frontend && npm run dev` 或用 `python start.py`（后台模式自动起 Vite）
- [x] **改动 5：新增 2 个辅助函数 + 移除 1 个**：
  - `_ensure_node_modules()` — 应用模式启动前的依赖检查（node_modules 不存在 → npm install）
  - `_ensure_dist_for_prod()` — 生产模式启动前的 dist 检查（dist 未构建 → 报错退出）
  - 移除 v2.2.1 的 `_ensure_dist_or_dev(force_dev)`（不再有「dist 未构建 → 自动 npm run build 走生产模式」逻辑）
- [x] **改动 6：`start_background()` 和 `run_foreground()` 接受 `force_prod` 参数**（替代 v2.2.1 的 `force_dev`）；后台子进程通过 `args + ["--prod"]` 把模式传递给 fg 子进程
- [x] **服务器部署 3 步不变**：① 上传代码 ② 装 Python + Node.js 18+ ③ `python start.py`（首次自动 npm install，之后秒启，默认应用模式 Vite :5000 + FastAPI :5001）
- [x] **生产部署可选**：`python start.py build && python start.py --prod`（构建 dist + 单进程生产模式，端口代理 :5000 永远指向 FastAPI，不需要 Node.js 运行时）
- [x] **6 份文档同步**：README §1.1/§1.3/§3.1、HANDOFF §1/§5.9/§6.16/末次更新、PROJECT_STATE §1/§2（本条）、ARCHITECTURE §1/§1.2 顶部提示、DEPLOYMENT 顶部提示/§1.5/§2.3、DEVELOPMENT 顶部提示/§1.9/§1.9.1/§1.9.2 全部更新

### 2026-07-20（v2.2.1）— start.py 自动构建（服务器部署重大简化，已被 v2.2.2 调整）

- [x] 起因：用户服务器部署场景「端口代理已配好 :5000 不能动，服务端只跑 `python start.py`」，但 v2.2 行为是 dist 未构建 → 走开发模式（Vite 占 :5000），会破坏端口代理
- [x] **改动 1：[start.py](../../start.py) 默认行为变更** — dist 未构建时不再走开发模式，而是：
  - Node.js 可用 → 自动 `npm install + npm run build` 后走生产模式（:5000 永远是 FastAPI）
  - Node.js 不可用 → 报错退出（不让 Vite 占 :5000 破坏端口代理）
- [x] **改动 2：新增 `--dev` 参数** — `python start.py --dev` 显式走开发模式（Vite :5000 + FastAPI :5001），本地开发用
- [x] **改动 3：新增 2 个辅助函数**：
  - `_check_node_available()` — 检测 node + npm 版本，返回 (是否可用, 版本信息)
  - `_ensure_dist_or_dev(force_dev)` — 决策启动模式：dist 已构建→prod / 未构建+force_dev→dev / 未构建+非 force_dev+Node 可用→自动构建后 prod / 未构建+非 force_dev+Node 不可用→sys.exit(1)
- [x] **改动 4：`start_background()` 和 `run_foreground()` 都接受 `force_dev` 参数**
- [x] **服务器部署简化为 3 步**：① 上传代码 ② 装 Python 依赖 + Node.js 18+ ③ `python start.py`（首次自动构建约 7 分钟，之后秒启）
- [x] **6 份文档同步**：DEVELOPMENT §1.9.1 / §1.9.2 / §1.9.6 更新（开发模式现在需 `--dev`）；DEPLOYMENT §1.5 / §2.3 更新（前端构建可选，start.py 自动）；README / HANDOFF / PROJECT_STATE / ARCHITECTURE 顶部加 v2.2.1 提示

### 2026-07-20（v2.2）— 视觉重构：PBR 管线 + 交互指引 + raycaster 拾取

- [x] 起因：用户反馈 v2.1 视觉效果"红白机观感"（MeshLambertMaterial + 平面 2D ShapeGeometry + 方形 PointsMaterial + 无阴影/Bloom/色调映射）+ "交互不明确"（仅被动鼠标跟随，无指引无反馈）；要求彻底重构达现代设计水准
- [x] **改动 1：新增 [utils/three-helpers.js](../../frontend/src/utils/three-helpers.js) PBR 工具集** — 统一现代渲染管线工厂函数：`createRenderer`（ACES + sRGB + PCFSoftShadowMap）、`createEnvironment`（RoomEnvironment + PMREMGenerator）、`createPostProcessing`（EffectComposer + RenderPass + UnrealBloomPass + OutputPass）、`createOrbitControls`（统一约束：禁用 pan + 极角限制 + 阻尼）、`createSoftSpriteTexture`（程序化柔光圆点 sprite，替代方形 PointsMaterial）、`createKeyLight` / `createFillLight`（带阴影主光 + 半球补光）、`disposeObject3D` / `disposeRenderer`（递归释放 geometry/material/texture/renderer/composer/pmrem/envMap）。所有 addon 走 `three/addons/` 子路径，便于 tree-shaking
- [x] **改动 2：新增交互组件**
  - [frontend/src/components/SceneHint.vue](../../frontend/src/components/SceneHint.vue)：可复用交互指引横幅。Props: `text` / `gesture` ('drag-rotate' / 'scroll-zoom' / 'click' / 'drag-rotate-zoom' / 'touch') / `autoHide` (5s) / `showDelay` (800ms) / `visible` (v-model)。毛玻璃胶囊 + SVG 手势图标 + 脉冲动画，用户首次交互（pointerdown/wheel/touchstart）后自动消失
  - [frontend/src/components/SceneControls.vue](../../frontend/src/components/SceneControls.vue)：可复用视图控制工具栏。Props: `modelValue` (v-model autoRotate) / `enableFullscreen` / `position`。Emits: `update:modelValue` / `reset` / `fullscreen`。三个按钮（自动旋转开关 / 重置视角 / 全屏）
- [x] **改动 3：[HeroScene.vue](../../frontend/src/components/HeroScene.vue) v2 重写** — PBR 现代化管线
  - `LatheGeometry` 程序化有机浮岛轮廓（10 段 + 噪声扰动 + 顶部轻微鼓起），替代 v1 ConeGeometry 倒锥
  - 递归樱花树（4 层分枝 + IcosahedronGeometry 花团），Bloom 高亮
  - PBR 水面：`MeshStandardMaterial` + `onBeforeCompile` 注入 4 层正弦波 vertex shader 位移（柔和起伏），metalness 0.35 + roughness 0.12 让水面有反射
  - `OrbitControls` 拖拽旋转 + 滚轮缩放 + 自动旋转 + `SceneHint` 交互提示 + `SceneControls` 控制工具栏
  - `raycaster` 点击主岛 → 相机平滑飞入 + 信息卡浮现（3 岛名：静屿 / 远屿 / 花屿 + 诗句）
  - `UnrealBloomPass`（strength 0.55，移动端 0.4）+ `OutputPass` + ACES 色调映射
  - 柔光 sprite 纹理替代方形点（80 个飘浮光点）
  - 体积：13.54KB（gzip 5.71KB）
- [x] **改动 4：[FlowerField.vue](../../frontend/src/components/FlowerField.vue) v2 重写** — 3D 立体花瓣 + 点击花语
  - 自定义 `BufferGeometry` 立体花瓣（4×6 顶点网格 + Z 轴凸起 + 顶部收窄），替代 v1 平面 `ShapeGeometry`
  - `MeshPhysicalMaterial`（sheen 0.7 + clearcoat 0.2 + envMap 反射 0.9），替代 v1 MeshLambertMaterial
  - `InstancedMesh` 300 花瓣 + 60 花蕊 + 60 花茎（3 draw call）
  - `PCFSoftShadowMap` 软阴影 + `UnrealBloomPass` 花蕊高光
  - `OrbitControls` + `SceneHint` + `SceneControls`
  - `raycaster` 拾取 InstancedMesh → 花朵爆裂脉冲动画（1.5s sin 放大）+ 花语 tooltip（5 种花语：温柔的陪伴 / 阳光的心意 / 宁静的生长 / 深沉的思念 / 纯粹的可能）
  - 体积：9.94KB（gzip 4.51KB）
- [x] **改动 5：[AudioVisualizer.vue](../../frontend/src/components/AudioVisualizer.vue) v2 重写** — 多模式 + 节拍检测
  - 4 种可视化模式，点击 canvas 循环切换：
    - `wave` 流动波形（v1 默认，5 色曲线）
    - `mirror` 镜像柱状（48 根上下对称频谱柱，渐变色）
    - `radial` 径向频谱（64 根 360° + 中心呼吸圆）
    - `particles` 粒子流（120 个粒子带光晕 + 拖尾 + 频谱驱动跳动）
  - 节拍检测：bass 能量突增（>1.35× 上次 + >0.35 阈值）→ 触发 10 个粒子爆裂（所有模式通用）
  - 频响主色：低频强 → 暖色（gong/zhi），高频强 → 冷色（yu/shang），混合时用 accent 色
  - 模式切换 toast（顶部居中毛玻璃胶囊 1.4s）+ 持续 hint 提示（8s 淡出）
  - 高度 120px → 160px
  - 保留：`createMediaElementSource` 一次性 `if (!sourceNode)` 守卫、`smartRAF` 30fps（移动端 24fps）、reduced-motion 静态 5 色横条降级
- [x] **改动 6：[AmbientBackground.vue](../../frontend/src/components/AmbientBackground.vue) v2 重写** — 柔光 sprite + 鼠标交互 + 视差
  - Canvas2D 层：预生成 32×32 柔光圆点 sprite 纹理（径向渐变），`source-atop` 合成模式叠加颜色；鼠标 120px 半径内柔和排斥（带阻尼回归）
  - Three.js 层：`createSoftSpriteTexture` 128×128 柔光 sprite + `AdditiveBlending` 加法混合；双层粒子（远景 90 个 + 近景 35 个，移动端减半）
  - 鼠标跟随：相机轻微旋转（仅旋转，不位移，避免视觉抖动）
  - 滚动视差：远景 `scrollY * 0.0008`，近景 `scrollY * 0.002`（近景物镜移动快，景深感强）
  - 轻量 `UnrealBloomPass`（strength 0.3，移动端 0.18）+ `OutputPass`
  - 完整释放：`disposeRenderer(renderer, composer)` + `disposeObject3D(points)` + sprite 纹理 dispose
  - 保留：3 层渐进增强（CSS 永远启用 → Canvas2D reduced-motion 关闭 → Three.js 按需）+ `smartRAF` + `prefers-reduced-motion` 降级
- [x] **改动 7：[vite.config.js](../../frontend/vite.config.js) `manualChunks` 函数形式** — 让 `three/addons/*`（EffectComposer / OrbitControls / RoomEnvironment 等）跨 HeroScene / FlowerField / AmbientBackground 共享同一 `three-vendor` chunk，避免每个组件重复打包 addon 代码
- [x] **设计原则**：
  - **交互指引优先**：所有 3D 场景首次进入显示 `SceneHint` 提示如何操作（拖拽 / 滚轮 / 点击），首次交互后自动消失，避免用户"不知道能做什么"
  - **视图控制统一**：所有 3D 场景都有 `SceneControls` 工具栏（自动旋转开关 + 重置视角），用户能主动控制相机
  - **点击反馈**：HeroScene 点击岛屿飞入 + 信息卡；FlowerField 点击花朵爆裂 + 花语；AudioVisualizer 点击 canvas 切换模式 + toast
  - **PBR 一致性**：4 个组件统一用 `three-helpers.js` 工厂函数，渲染管线一致（ACES + sRGB + Bloom + 软阴影），视觉语言统一
  - **完整释放**：`onBeforeUnmount` 用 `disposeRenderer` + `disposeObject3D` 统一释放，避免 WebGL context 累积
- [x] **降级保留**：
  - HeroScene 不支持 WebGL / reduced-motion / initScene 异常 → SVG 静态插画（不变）
  - AudioVisualizer 无 Web Audio API / reduced-motion → 5 色静态横条 CSS 动画（不变）
  - AmbientBackground 无 WebGL / 低性能 → CSS 雾气光斑 + Canvas2D 光点（不变）
  - 移动端：dpr ≤ 1.5 / 粒子数减半 / Bloom 强度降低 / 阴影 mapSize 1024 / 几何精度降档（v2.2.3 加：Lathe/Cylinder/Icosahedron 段数与细分降低、樱花树递归深度 4→3、花瓣网格 5×8→4×6、地面圆 64→32、AudioVisualizer 柱数 48/64→32）
- [x] 文档同步（Iron Rule）：6 份文档同步更新 — README §2/§3.5/§8、HANDOFF §2/§5.11/末次更新、PROJECT_STATE §1/§2（本条）/§3.3、ARCHITECTURE §1.1.6/§7.7、DEPLOYMENT 前端构建/顶部 Iron Rule、DEVELOPMENT §1.9.4/§1.9.8/顶部 Iron Rule
- [x] 验证：① `npm run build` 通过，200 模块编译无错；② `three-vendor` 719.84KB（gzip 184.01KB）独立 chunk，所有 Three.js 组件共享；③ HeroScene 13.54KB / FlowerField 9.94KB / SceneControls 4.5KB（共享，被 HeroScene + FlowerField 引用）/ MusicDetailView 13.11KB / index 102.02KB；④ SceneControls 从 7.5KB 降到 4.5KB（AmbientBackground 不再依赖它，tree-shaking 优化）；⑤ 浏览器访问 `/` 看到 PBR 浮岛雾海 + 樱花树 + Bloom 高光 + 拖拽旋转 + 滚轮缩放 + 点击岛屿飞入 + 信息卡；⑥ `/garden` 看到 3D 立体花瓣 + 阴影 + Bloom + 点击花朵爆裂 + 花语 tooltip；⑦ `/music/gong` 听歌看到 4 模式音波可视化（点击切换）+ 节拍粒子爆裂；⑧ 全局背景看到柔光粒子 + 鼠标排斥 + 滚动视差；⑨ DevTools 模拟 reduced-motion → 3D 降级为 SVG / CSS 静态

### 2026-07-20（v2.1）— 视觉增强：三层渐进增强 + 4 个视觉组件

- [x] 起因：用户要求在 v2.0.1 FlowerField 基础上进一步提升整体视觉美感，加入 3D / 伪 3D 背景元素和动态视觉效果，**但不能影响页面加载性能或用户体验，且必须为 3D 渲染能力有限的浏览器实现备用机制**
- [x] **改动 1：三层渐进增强视觉策略** — 「CSS 永远启用 → Canvas2D 中量级 → Three.js 按需」三层独立可降级，配套 [utils/visual.js](../../frontend/src/utils/visual.js) 能力检测（`hasWebGL` / `prefersReducedMotion` / `isMobile` / `isLowPower` / `shouldUseThreeJS` / `shouldUseCanvas` / `smartRAF`）
- [x] **改动 2：新增 4 个视觉文件**
  - [frontend/src/utils/visual.js](../../frontend/src/utils/visual.js)：视觉能力检测工具（hasWebGL / prefersReducedMotion / isMobile / isLowPower / shouldUseThreeJS / shouldUseCanvas / smartRAF）
  - [frontend/src/components/AmbientBackground.vue](../../frontend/src/components/AmbientBackground.vue)：全局氛围背景（CSS 雾气光斑 24s `mistDrift` 动画 + Canvas2D 飘浮光点（移动端 24 / 桌面 60）+ Three.js 远景粒子层 80 个 sprite），三层渐进增强，挂在 [AppLayout.vue](../../frontend/src/components/AppLayout.vue) 根；无 WebGL / 低性能 → 仅 CSS + Canvas2D；reduced-motion → 仅 CSS
  - [frontend/src/components/HeroScene.vue](../../frontend/src/components/HeroScene.vue)：首页 Hero 区 3D 浮岛雾海（PlaneGeometry 128×128 波动海面 + 3 浮岛 + FogExp2 雾 + 80 飘浮光点 + 鼠标视差），SVG 静态插画降级（800×480 viewBox：天空渐变 + 太阳 + 3 岛 + 3 层波浪 + 5 漂浮点）；嵌入 [HomeView.vue](../../frontend/src/views/HomeView.vue) 顶部
  - [frontend/src/components/AudioVisualizer.vue](../../frontend/src/components/AudioVisualizer.vue)：5 色音波可视化（Web Audio API `AnalyserNode` + Canvas2D 5 条流动曲线，对应宫商角徵羽 5 音色 + 治愈系 5 色），CSS 5 色横条降级（reduced-motion / 无 Web Audio 时）；挂在 [MusicDetailView.vue](../../frontend/src/views/music/MusicDetailView.vue) 详情头之后
- [x] **改动 3：HomeView 重写** — 集成 HeroScene 3D 背景 + 五音卡片 CSS 3D 倾斜（`perspective: 1000px` + `rotateX/Y` + `translateZ`，鼠标跟随 + `prefers-reduced-motion` 自动降级为静态卡片）
- [x] **改动 4：MusicDetailView 集成 AudioVisualizer** — `<AudioVisualizer ref="visualizerRef" :yin-key :is-playing :progress />`，首次 `playIndex` 时调 `visualizerRef.value.connect(audioEl)`，用 `visualizerConnected` ref 守卫 `createMediaElementSource` 一次性约束
- [x] **性能保护**：
  - 所有 Three.js 组件用 `defineAsyncComponent(() => import(...))` 异步加载，**不进首屏包**
  - [vite.config.js](../../frontend/vite.config.js) `manualChunks` 把 `three` 单独打成 `three-vendor` chunk（gzip 175KB），仅访问 `/`（HeroScene）或 `/garden`（FlowerField）时按需拉取
  - Three.js 对象用 `shallowRef` 持有（避免 Vue 深度代理拖累性能）
  - `smartRAF(callback)` 在 `document.hidden` 时暂停 rAF、可见时自动恢复
  - 移动端降级：粒子数减半 + `dpr` ≤ 1.5
  - 所有 Three.js 组件 `onBeforeUnmount` 释放 geometry / material / renderer / 事件监听 / ResizeObserver
- [x] **配色一致性**：4 个视觉组件全部用治愈系 5 色（藕粉 `#E8B8C5` / 淡黄 `#E8D5A8` / 青绿 `#A8C5A0` / 雾蓝 `#A8B8C5` / 纯白 `#FAF6F2`）+ 米白 `#F9F6F0` 背景，与 [tailwind.config.js](../../frontend/tailwind.config.js) token 一致；AudioVisualizer 5 条曲线对应宫商角徵羽 5 音色
- [x] **踩坑 4 条**（详见 [HANDOFF §6.23](../../HANDOFF.md)）：
  1. `createMediaElementSource` 一次性约束 → AudioVisualizer `if (!sourceNode)` 守卫 + MusicDetailView `visualizerConnected` ref 标记
  2. Three.js 对象用 `ref` 会深度代理拖累性能 → 改用 `shallowRef`
  3. `requestAnimationFrame` 在标签页隐藏时仍执行 → 改用 `smartRAF`
  4. `onBeforeUnmount` 不释放 WebGL context → 5 次切走后浏览器报 `Too many active WebGL contexts` → 必须完整释放
- [x] 文档同步（Iron Rule）：6 份文档同步更新 — README §2/§3.5/§8、HANDOFF §2/§3/§5.10/§6.23/末次更新、PROJECT_STATE §1/§2（本条）/§3.3、ARCHITECTURE §1.1.6/§7.7、DEPLOYMENT 前端构建/顶部 Iron Rule、DEVELOPMENT §1.9.8/顶部 Iron Rule
- [x] 验证：① `npm run build` 通过，183 模块编译无错，`three-vendor` 175KB gzip 独立 chunk，HeroScene 7.56KB，MusicDetailView 8.64KB；② 浏览器访问 `/` 看到 3D 浮岛雾海 + 五音卡片 3D 倾斜；③ 访问 `/garden` 看到 3D 花田（已有）；④ 访问 `/music/gong` 听歌时看到 5 色音波可视化随音量起伏；⑤ 全局氛围背景在所有页面可见（雾气光斑 + 飘浮光点）；⑥ DevTools 切到 reduced-motion 模拟 → 3D 场景降级为 SVG / CSS 静态；⑦ 切走标签页 → GPU 占用归零（smartRAF 生效）

### 2026-07-19（v2.0.1）— 端口策略调整 + Three.js 3D 花田场景

- [x] 起因：① v2.0 Vue 3 重构初版用「FastAPI :5000 + Vite :5173 + FastAPI 反代 Vite」方案，但 Vite 内部路径 `/@id/__x00__plugin-vue:export-helper` 含 null 字符转义 + 冒号，httpx 转发破坏后浏览器报 `SyntaxError: Unexpected token '.'`；② 想给精神花园页加一个治愈系 3D 视觉锚点，提升沉浸感
- [x] **改动 1：端口策略调整**
  - **开发模式**（dist 未构建）：Vite 监听 **:5000**（用户访问入口，HMR 热更新）+ FastAPI 改听 **:5001**（API 后端，由 [start.py](../../start.py) 设置 `QI_PORT=5001`）
  - **生产模式**（dist 已构建）：FastAPI 监听 **:5000**（默认，从 `.env` 读 `QI_PORT`），Vite 不运行
  - Vite proxy 把 `/api`、`/static`、`/admin`、`/docs`、`/openapi.json` 转发到 :5001（[frontend/vite.config.js](../../frontend/vite.config.js)）
  - **用户始终访问 :5000**，由 [start.py](../../start.py) 自动检测 `static/dist/index.html` 是否存在来切换端口策略
- [x] **改动 2：start.py 增强**（[start.py](../../start.py)）
  - `start` 子命令：自动检测 dist，未构建时设置 `QI_PORT=5001` 启动 FastAPI + 启动 Vite :5000
  - `stop` 子命令：同时停 FastAPI 和 Vite
  - `status` 子命令：显示两个进程状态 + 端口
  - `build` 子命令（**新增**）：构建前端到 `static/dist/`（自动 `npm install` + `npm run build`）
  - `fg` 子命令：前台运行 FastAPI（生产模式用，不自动起 Vite）
- [x] **改动 3：vite.config.js**（[frontend/vite.config.js](../../frontend/vite.config.js)）
  - dev server port: 5173 → **5000**
  - proxy target: :5000 → **:5001**
  - 移除 `hmr.clientPort`（Vite 直接占 :5000 后 HMR 走本地不需要）
  - 新增 `/docs` 和 `/openapi.json` 代理
- [x] **改动 4：main.py**（[app/main.py](../../app/main.py)）
  - SPA fallback 移除回退代理到 Vite 的逻辑（开发态不再转发，避免内部路径含特殊字符被 httpx 破坏）
  - 开发态（dist 未构建）返回提示页，引导用户访问 Vite :5000
  - 生产态（dist 已构建）从 dist 读取静态资源 + 返回 index.html
  - 新增 `EXT_TO_MIME` 映射，正确设置 `.js` / `.css` / `.woff2` 等 `Content-Type`（避免被 Starlette 默认当成 `application/octet-stream` 让浏览器拒绝执行）
- [x] **改动 5：Three.js 3D 花田场景**
  - 新增 [frontend/src/components/FlowerField.vue](../../frontend/src/components/FlowerField.vue)：
    - Three.js `InstancedMesh` 渲染 **60 朵花 × 5 瓣 = 300 个实例**（性能与视觉的平衡点）
    - **5 种治愈色**：藕粉 `#E8B8C5` / 淡黄 `#E8D5A8` / 青绿 `#A8C5A0` / 雾蓝 `#A8B8C5` / 纯白 `#FAF6F2`
    - **绽放动效**：从地面错峰升起 + 缓动缩放（ease-in-out）
    - **风摆动**：每朵花错相位摆动（sin 函数）
    - **摄影机**：自动呼吸摆动 + 鼠标跟随
    - **雾效 + 渐变背景**：远处花朵融入雾里（与背景同色 `#F9F6F0`）
    - **飘浮光点**：80 个 `Points`，缓缓上升
    - 用 `defineAsyncComponent` 异步加载（按需加载 Three.js，减小首屏包），加载时显示 "🌿 花田正在生长…" 提示
  - 改 [frontend/src/views/garden/GardenView.vue](../../frontend/src/views/garden/GardenView.vue)：
    - 顶部嵌入 FlowerField 组件（380px 高）
    - 底部覆盖提示文案 "移动鼠标，看花田随风摆动"
    - 圆角 + 阴影包裹
- [x] **踩坑 1 条**（详见 [HANDOFF §6.16](../../HANDOFF.md)）：
  - FastAPI 代理转发 Vite 内部路径含特殊字符失败 → Vite 直接占 :5000，FastAPI 改 :5001
- [x] 文档同步（Iron Rule）：6 份文档同步更新 — README §1.1/§1.3/§2/§3.1/§3.5/§8、HANDOFF §1/§2/§3/§5.9/§6.16/末次更新、PROJECT_STATE §1/§2（本条）/§3.3/§4、ARCHITECTURE §1 架构图/§1.1/§1.2、DEPLOYMENT 前端构建/部署后验证、DEVELOPMENT §1.9.1/§1.9.2/§1.9.5/§1.9.7
- [x] 验证：① `python start.py`（dist 未构建）→ 自动起 Vite :5000 + FastAPI :5001，浏览器访问 :5000 看到 Vue SPA + HMR 正常，调 API 走 proxy 到 :5001 正常；② `python start.py build` → 输出 `static/dist/`；③ `python start.py`（dist 已构建）→ FastAPI :5000 走 SPA fallback，访问 :5000 看到 Vue SPA + 静态资源 `Content-Type` 正确（`.js` → `application/javascript`）；④ `/garden` 页面顶部显示 3D 花田，鼠标移动摄影机跟随，花朵风摆动 + 飘浮光点动效正常

### 2026-07-19（v2.0）— 全站 Vue 3 重构（前端独立工程化 + 后端 SPA fallback）

- [x] 起因：项目迭代到 4 Phase + 后台 + AI 后，原生 HTML/CSS/JS + Jinja2 SSR 模式前端逻辑膨胀，状态散落、路由靠后端 302、新增页面要改 4 处。决定全站迁 Vue 3 SPA 工程化
- [x] **技术栈变更**：
  - 旧：FastAPI + Jinja2 SSR + 原生 HTML/CSS/JS
  - 新：FastAPI（纯 API 后端）+ Vue 3 SPA（`<script setup>`）+ Vite 5 + Vue Router 4 + Pinia + Tailwind CSS + GSAP + @vueuse/motion + Three.js + axios
- [x] **新增 `frontend/` 目录**（Vue 3 SPA 源码）：
  - [frontend/package.json](../../frontend/package.json)：依赖 vue ^3.4 / vue-router ^4.4 / pinia ^2.2 / axios ^1.7 / gsap ^3.12 / @vueuse/motion ^2.2 / three ^0.168；devDeps vite ^5.4 / @vitejs/plugin-vue ^5.1 / tailwindcss ^3.4 / postcss / autoprefixer
  - [frontend/vite.config.js](../../frontend/vite.config.js)：dev proxy `/api`、`/static`、`/admin` → :5000；build outDir `../static/dist`；base 仅 build 时为 `/static/dist/`（用 `command === 'build'` 条件判断）；host `127.0.0.1`，strictPort
  - [frontend/tailwind.config.js](../../frontend/tailwind.config.js)：治愈系色彩 token（mist/ink/五音色/accent）+ 动画（breathe/float/fade-up）
  - [frontend/src/main.js](../../frontend/src/main.js)：入口（createApp + Pinia + Router + MotionPlugin）
  - [frontend/src/App.vue](../../frontend/src/App.vue)：根组件（AppLayout + router-view + transition）
  - [frontend/src/router/index.js](../../frontend/src/router/index.js)：13 条路由 + requiresAuth 守卫
  - [frontend/src/api/index.js](../../frontend/src/api/index.js)：axios 实例，baseURL=/api，withCredentials=true，401 自动跳登录
  - [frontend/src/stores/user.js](../../frontend/src/stores/user.js)：Pinia user store（cookie session 模式，**不存 token**，只缓存 user 对象到 localStorage）
  - [frontend/src/components/AppLayout.vue](../../frontend/src/components/AppLayout.vue)：桌面顶部导航 + 移动端底部 tabbar（768px 断点）
  - [frontend/src/views/](../../frontend/src/views/)：13 个视图（HomeView / auth/LoginView+RegisterView / music/MusicListView+MusicDetailView / diary/DiaryListView+DiaryWriteView+PickBottleView / mood/MoodCalendarView / ai/AIChatView / garden/GardenView+ShopView / NotFoundView）
- [x] **后端变更**：
  - [app/main.py](../../app/main.py)：加 SPA fallback — 所有未匹配的 GET 请求（排除 `/api/`、`/static/`、`/admin`、`/docs`）返回 `static/dist/index.html`；若 dist 未构建返回提示页引导访问 Vite dev server
  - [app/routers/pages.py](../../app/routers/pages.py)：简化为 4 个 302 重定向（`/mood`→`/calendar`、`/mood-calendar`→`/calendar`、`/my-bottles`→`/diary`、`/pick`→`/diary/pick`），兼容旧书签
  - [app/config.py](../../app/config.py)：修复 env_prefix bug（加 `env_prefix="qi_"` 让 .env 里 QI_* 变量正确加载）
  - [app/services/ai_service.py](../../app/services/ai_service.py)：超时 30s→60s
  - AI 模型链：`nvidia/llama-3.1-nemotron-70b-instruct` → `meta/llama-3.3-70b-instruct` → `meta/llama-3.1-8b-instruct`
  - 删除 showcase 动效页（`templates/showcase.html`、`static/js/pages/showcase.js`、`static/css/08-showcase.css`）
- [x] **认证机制（不变）**：
  - cookie session（不是 JWT token）
  - 登录用 nickname（不是 username）
  - 登录/注册直接返回 user 对象（不是 `{access_token, user}`）
  - 前端 userStore 只缓存 user 对象到 localStorage，不存 token
- [x] **功能完整性（一个功能都不丢）**：
  - ✅ 古琴五音疗愈（5 音列表 + 单音曲目 + 沉浸式播放器 + 听完 90% +1 露水）
  - ✅ AI 帮我选音（输入描述 → POST /api/ai/recommend-music → 跳转）
  - ✅ 漂流瓶日记（写日记 + Web Crypto 加密 + 时间线 + 解密查看）
  - ✅ 拾漂流瓶（拾陌生人瓶子 + 解密 + 写鼓励语 + AI 鼓励语降级）
  - ✅ 情绪日历（emoji 打卡 + 月历网格 + 30 天趋势 + AI 治愈语）
  - ✅ AI 树洞（多轮对话 + 历史只在内存 + available=false 降级）
  - ✅ 精神花园（能量卡 + 来源分布 + 物品分组 + 能量流水）
  - ✅ 露水商店（按 item_type 分组 + 兑换 + 已持有/能量不足状态）
  - ✅ 鉴权（登录 + 注册 + 密码切换显示 + 401 自动跳登录）
  - ✅ 404 页面
  - ✅ 响应式（桌面顶部导航 + 移动端底部 tabbar）
  - ✅ GSAP 入场动效（stagger 浮入 + 呼吸动效）
  - ✅ 治愈系配色（米白 #F9F6F0 + 茶褐 #8B7B5E + 雾粉/雾蓝/青绿点缀）
- [x] **开发/生产模式**：
  - 开发：`cd frontend && npm install && npm run dev` → http://127.0.0.1:5173/（Vite dev server，proxy /api 到 FastAPI :5000）
  - 生产：`cd frontend && npm run build` → 输出到 `static/dist/` → `python start.py` → http://127.0.0.1:5000（FastAPI 提供 SPA fallback）
- [x] **踩坑 4 条**（详见 [HANDOFF §6.12-6.15](../../HANDOFF.md)）：
  1. Vite 默认监听 IPv6 `[::1]` 导致 127.0.0.1 连不上 → 显式设 `host: '127.0.0.1'`
  2. Vite `base` 在 dev 模式也会应用 → 用 `command === 'build'` 条件设置
  3. `npm install` 拉 three.js 等大包耗时 7 分钟 → 接受首次耗时，后续增量快
  4. FastAPI SPA fallback 必须排除 `/api/`、`/static/`、`/admin`、`/docs` 路径
- [x] 文档同步（Iron Rule）：6 份文档同步更新 — README §0/§1.3/§2/§3/§8/§9、HANDOFF §0/§1/§2/§5.8/§6.12-6.15/§12、PROJECT_STATE §1/§2（本条）/§3/§8、ARCHITECTURE 架构图+前端架构+开发/生产模式+§7.7、DEPLOYMENT 前端构建+部署步骤+顶部 Iron Rule、DEVELOPMENT 前端开发+dev proxy+文件结构+§1.8
- [x] 验证：① `npm run dev` 启动 :5173 + `python start.py` 启动 :5000，前端调 API 走 proxy 正常；② `npm run build` 输出 `static/dist/`，`python start.py` 起后访问 :5000 走 SPA fallback 正常；③ 13 个视图全部加载，路由跳转、requiresAuth 守卫、401 自动跳登录、Web Crypto 加密、GSAP 动效、Tailwind 治愈系配色、响应式断点 — 全部通过

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
- `__init__.py` / `main.py`（v2.0 加 SPA fallback）/ `config.py`（v2.0 修复 env_prefix bug）/ `database.py` / `deps.py` / `security.py` / `seed.py`
- `models/` — 7 张表 + `__init__.py`（users 含 `is_admin`）
- `schemas/` — **7 个** Pydantic 模块（auth/diary/mood/music/energy/**admin**/**ai**）+ `__init__.py`
- `routers/` — **10 个** router（**pages（v2.0 简化为 4 个 302 重定向）** + 6 业务 + **admin + admin_pages** + **ai**）
- `services/` — **4 个**业务服务（energy / diary / mood / **ai_service**（v2.0 超时 30s→60s））
- `utils/` — 加密 + 常量

### 3.3 前端

**v2.0 Vue 3 SPA**（[frontend/](../../frontend/)，2026-07-19 加）：
- `package.json` — 依赖 vue ^3.4 / vue-router ^4.4 / pinia ^2.2 / axios ^1.7 / gsap ^3.12 / @vueuse/motion ^2.2 / three ^0.168；devDeps vite ^5.4 / @vitejs/plugin-vue ^5.1 / tailwindcss ^3.4 / postcss / autoprefixer
- `vite.config.js` / `tailwind.config.js` / `postcss.config.js` / `index.html`
- `src/main.js` — 入口（createApp + Pinia + Router + MotionPlugin）
- `src/App.vue` — 根组件（AppLayout + router-view + transition）
- `src/router/index.js` — 13 条路由 + requiresAuth 守卫
- `src/api/index.js` — axios 实例（baseURL=/api，withCredentials=true，401 自动跳登录）
- `src/stores/user.js` — Pinia user store（cookie session 模式，不存 token）
- `src/components/AppLayout.vue` — 桌面顶部导航 + 移动端底部 tabbar（768px 断点）
- `src/components/FlowerField.vue` — **Three.js 3D 花田场景**（v2.0.1 加）：60 朵花 × 5 瓣 = 300 `InstancedMesh`；5 种治愈色（藕粉 / 淡黄 / 青绿 / 雾蓝 / 纯白）；绽放动效 + 风摆动 + 雾效 + 80 个飘浮光点；摄影机自动呼吸 + 鼠标跟随；`defineAsyncComponent` 异步加载；嵌入 `GardenView.vue` 顶部 380px 高
- `src/components/AmbientBackground.vue` — **全局氛围背景**（v2.1 加）：三层渐进增强 — CSS 雾气光斑（3 个 radial-gradient + 24s `mistDrift` 动画，永远启用）+ Canvas2D 飘浮光点（移动端 24 / 桌面 60，reduced-motion 关闭）+ Three.js 远景粒子层（80 个 sprite，WebGL + 非低性能时启用）；挂在 `AppLayout.vue` 根；`shallowRef` + `smartRAF` + `onBeforeUnmount` 完整释放
- `src/components/HeroScene.vue` — **首页 Hero 区 3D 浮岛雾海**（v2.1 加）：PlaneGeometry 128×128 波动海面 + 3 浮岛 + FogExp2 雾 + 80 飘浮光点 + 鼠标视差；SVG 静态插画降级（800×480 viewBox：天空渐变 + 太阳光晕 + 3 岛 + 3 层波浪 + 5 漂浮点）；嵌入 `HomeView.vue` 顶部；`defineAsyncComponent` 异步加载
- `src/components/AudioVisualizer.vue` — **5 色音波可视化**（v2.1 加）：Web Audio API `AnalyserNode` + Canvas2D 5 条流动曲线（对应宫商角徵羽 5 音色 + 治愈系 5 色）；CSS 5 色横条降级（reduced-motion / 无 Web Audio 时）；`defineExpose({ connect })` 暴露给父组件连接 `<audio>` 元素；挂在 `MusicDetailView.vue` 详情头之后
- `src/utils/visual.js` — **视觉能力检测**（v2.1 加）：`hasWebGL()` / `prefersReducedMotion()` / `isMobile()` / `isLowPower()` / `shouldUseThreeJS()` / `shouldUseCanvas()` / `smartRAF(callback)`（标签页隐藏自动暂停 rAF，可见时自动恢复）；单次缓存检测结果
- `src/views/` — **13 个视图**（HomeView / auth/LoginView+RegisterView / music/MusicListView+MusicDetailView / diary/DiaryListView+DiaryWriteView+PickBottleView / mood/MoodCalendarView / ai/AIChatView / garden/GardenView+ShopView / NotFoundView）
- `src/assets/styles/main.css` — Tailwind 指令 + 全局 CSS 变量 + 通用组件类 + 系统字体

**旧 Jinja2 SSR 模板**（[templates/](../../templates/)，v2.0 后仅后台 `/admin/*` 仍使用）：
- `templates/` — **14 个**前台 .html（v2.0 后保留作历史参考，不再被路由引用）+ **6 个后台 .html**（`templates/admin/`，**仍活跃**）+ 宏
- `static/css/` — 8 个 .css（含 **07-admin.css**，**仍活跃**；其他前台 CSS v2.0 后保留作历史参考）
- `static/js/` — 1 个 app.js + **17 个** pages/（11 个前台：v2.0 后保留作历史参考；6 个后台：**仍活跃**）
- `static/dist/` — **v2.0 新增**，Vue 3 build 产物（`index.html` + JS/CSS chunk），由 `npm run build` 生成，FastAPI SPA fallback 兜底服务

### 3.4 脚本
- [start.py](../../start.py) — 服务管理（核心）

### 3.5 数据 / 运行时
- `data/healing.db` — SQLite（git 忽略）
- `run/healing.pid` — PID
- `logs/healing.log` — 日志
- `.env` — 用户环境变量（git 忽略，从 .env.example 复制）

---

## 4. 端口与地址

> 📌 **用户始终访问 :5000**，开发 / 生产模式由 [start.py](../../start.py) 自动检测 `static/dist/index.html` 是否存在来切换。

| 场景 | 地址 |
|---|---|
| **开发模式**（dist 未构建）— 用户访问入口 | http://127.0.0.1:5000/（**Vite dev server**，HMR 热更新） |
| **开发模式** — FastAPI API 后端 | http://127.0.0.1:5001/（由 `start.py` 设置 `QI_PORT=5001`，Vite proxy 转发 `/api`、`/static`、`/admin`、`/docs`、`/openapi.json`） |
| **生产模式**（dist 已构建）— FastAPI | http://127.0.0.1:5000/（从 `.env` 读 `QI_PORT`，提供 SPA + API + 静态资源；Vite 不运行） |
| API 文档 | http://127.0.0.1:5000/docs（生产）或 http://127.0.0.1:5001/docs（开发，经 Vite proxy） |
| 健康检查 | http://127.0.0.1:5000/ |
| **秘密后台** | **http://127.0.0.1:5000/admin**（可在 `.env` 改 `QI_ADMIN_PATH_PREFIX`） |
| 生产服务器 | http://你的域名/（Nginx 80/443 → 5000） |

> 💡 **为什么开发模式 Vite 占 :5000**：v2.0 重构初版用「FastAPI :5000 反代 Vite :5173」方案，但 Vite 内部路径 `/@id/__x00__plugin-vue:export-helper` 含 null 字符 + 冒号被 httpx 转发破坏，浏览器报 `SyntaxError`。改成 Vite 直接占 :5000 后所有内部路径走本地，无转发问题。详见 [HANDOFF §5.9](../../HANDOFF.md) 决策 + [§6.16](../../HANDOFF.md) 踩坑。
>
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

> 🔒 **2026-07-19 v2.0 Vue 3 重构特别约定**：本次涉及 **6 份文档同步**（README / HANDOFF / PROJECT_STATE / ARCHITECTURE / DEPLOYMENT / DEVELOPMENT），关键词 `Vue 3` / `Vite` / `SPA fallback` / `frontend/` 在 6 份文档中都要出现。

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
| **Vue 视图 / 路由 / store 改动**（v2.0 加） | [README.md](../../README.md) §2 frontend/ 子树 + §3.5 + [ARCHITECTURE.md](ARCHITECTURE.md)「前端架构」 + [DEVELOPMENT.md](DEVELOPMENT.md)「前端开发」 |
| **Vite / Tailwind / 前端依赖改动**（v2.0 加） | [README.md](../../README.md) §1.3 + [frontend/package.json](../../frontend/package.json) + [HANDOFF.md](../../HANDOFF.md) §2 + [DEPLOYMENT.md](DEPLOYMENT.md)「前端构建」 |
| **6 份文档同步**（Iron Rule，v2.0 强调） | README / HANDOFF / PROJECT_STATE / ARCHITECTURE / DEPLOYMENT / DEVELOPMENT 必须同一 commit 一起更新 |

### 8.3 提交前自检清单

- [ ] 改的 schema 字段在 `*Out` Pydantic 里**也都声明了**（避免 §6.11 类 Bug）
- [ ] 改的 model 字段长度 / 类型在 schema 的 `max_length` / 类型里**也同步了**（→ 如 v2.4.4 `avatar 字段长度 String(255) / ProfileUpdateIn max_length=255`）
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
