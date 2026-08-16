# HANDOFF — 静屿项目交接说明

> 写给接手这个项目的下一个 AI（Cursor / Copilot / Devin / 任何 Agent）。
> 读这一份文件 ≈ 读完整套文档。它是项目元信息 + 关键决策 + 踩坑清单的汇总。

> 🔒 **2026-07-28 v2.3.2 start.py 默认生产模式 + 自动构建简化**：`python start.py` 默认行为再次变更——**默认走生产模式**（FastAPI :5000 单进程，前后端不再一起起），需 `static/dist/` 已构建（不存在则自动 `npm install + npm run build`）。**自动构建仅检测 `static/dist/index.html` 存在性**（`dist 存在检测`），不再比较 `frontend/src/` 与 `static/dist/` 文件修改时间。**开发需显式 `python start.py --dev`**（Vite :5000 HMR + FastAPI :5001 API，前后端一起起的「应用模式」）。`--prod` 改为兼容别名（默认就是生产模式，加不加效果一样）。**服务器部署 2 步**：① 上传代码 ② `python start.py`（首次自动构建，之后秒启，FastAPI 单进程 :5000）。本次回滚 v2.2.2「默认应用模式」决策，理由：服务器端口代理已配好 :5000 不能动，应用模式会让 Vite 占 :5000 破坏代理。关键词 `默认生产模式` / `dist 存在检测` / `自动构建` / `--dev` / `应用模式` / `v2.3.2` 在 6 份文档中都要出现。

> 🔒 **2026-07-30 v2.3.3 Safari 兼容性修复（3D 上下文恢复 + emoji 跨浏览器一致）**：解决 Safari / iOS 用户反馈的两类问题。① **Safari 主页 3D 不渲染**：根因包括 `hasWebGL()` 检测 bug、iOS Safari 切后台→前台后 WebGL 上下文丢失无恢复逻辑、老 iOS 缺 `EXT_color_buffer_half_float` 扩展、Bloom + 高分辨率 PMREM 内存超限。修复：**`hasWebGL` 重写**（区分 WebGL1/2 + 检测扩展 + max texture size），新增 `getWebGLCaps()` / `isSafari()` / `isIOS()` 工具函数；[frontend/src/utils/three-helpers.js](../../frontend/src/utils/three-helpers.js) 添加 `webglcontextlost` / `webglcontextrestored` 事件监听，上下文丢失时保存场景状态、恢复时重建；[HeroScene.vue](../../frontend/src/components/HeroScene.vue) 实现 **iOS 降级**策略（**Bloom 降级**：iOS 关闭 UnrealBloomPass；**PMREM 降级**：iOS PMREM 分辨率 256→128、阴影 2048→1024、dpr 上限 2→1.5；老 iOS 缺扩展时关闭 PMREM + Bloom）。② **Safari emoji 显示不一致**：根因为跨平台 emoji 字体风格差异（Apple Color Emoji vs 系统 emoji）。修复：新建 [EmojiIcon.vue](../../frontend/src/components/EmojiIcon.vue) 组件，使用 **Iconify** + `@iconify-json/twemoji` 离线 **SVG emoji**，确保 **跨浏览器一致**；替换 [AppLayout.vue](../../frontend/src/components/AppLayout.vue)（品牌 / 导航 / 通知 / 资源）+ [ProfileView.vue](../../frontend/src/views/profile/ProfileView.vue)（头像 / 通知 / 资源 / 统计 / 快捷入口 / 花朵阶段）所有 emoji。关键词 `Safari 兼容` / `WebGL 上下文丢失` / `webglcontextlost` / `iOS 降级` / `EmojiIcon` / `Iconify` / `twemoji` / `SVG emoji` / `跨浏览器一致` / `hasWebGL 重写` / `getWebGLCaps` / `isSafari` / `isIOS` / `Bloom 降级` / `PMREM 降级` / `v2.3.3` 在 6 份文档中都要出现。

> 🔒 **2026-08-10 v2.4.0 文案焕新 + 一天多条心情 + 头像/昵称编辑 + 花坊改名 + 露水累加修复**：本次更新 18 项 UI/UX 与功能调整。① **首页文案**：'海上有座岛，岛上有人听' → '潮声不止，心安自屿'，删除'静屿'副标题；删除首页'今日打卡'板块。② **漂流日记入口统一**：不管从哪进入，直接显示'日记海岸'界面（含拾瓶 / 写日记模块）。③ **情绪日历 emoji 显示/选择修复**。④ **一天多条心情记录**：`mood_checkins` 表 `user_id+check_date` 唯一约束移除（`mood_checkins 唯一约束移除`，SQLite 重建表方式：CREATE TABLE _new AS SELECT * → DROP → RENAME → CREATE INDEX），支持一天多次打卡（情绪是多变的）；[mood_service.py](../../app/services/mood_service.py) 重构——`upsert_checkin` → `add_checkin`（不再 UPSERT，允许一天多条）+ 新增 `get_today_moods`（获取今日所有心情）。⑤ **30 天心情趋势**：1-5 评分系统（极度开心=5 / 开心=4 / 平静=3 / 疲惫·焦虑=2 / 生气·悲伤=1），多条取**平均分**（`MOOD_SCORE` 映射：ecstatic=5 / happy=4 / calm=3 / tired=2 / anxious=2 / angry=1 / sad=1）。⑥ **心语树洞 AI 系统提示词 humanize**：更接地气、像朋友聊天。⑦ **'落叶画坊' → '花坊'**（改名）。⑧ **花种种类扩充**：12 种植物（向日葵 / 竹子 / 雏菊 / 莲花 / 薰衣草 / 郁金香 / 梅花 / 桃花 / 兰花 / 青松 / 桂花 / 银杏）。⑨ **新装扮**：油纸伞 / 蓑衣 / 乌篷船 / 鱼竿 / 橘猫 / 白鹤。⑩ **'古琴初学者' → '琴音知音'**（徽章改名）+ **每板块徽章**：琴音知音 / 日记达人 / 七日静心 / 拾瓶旅人 / 树洞倾心 / 花田主人。⑪ **'竹编帽'介绍改为'种花人遮阳的草帽'**。⑫ **花田 AI 显示基于实际种花情况**：没种花不显示。⑬ **'我的'页面修复**：'收到鼓励' / '岛上物件'可点击跳转，删除重复'岛上物件'，新增'静屿使用指南'（详细介绍所有模块功能）。⑭ **头像/昵称修改**：新增 `User.avatar` 字段（emoji，默认 `🙂`，`String(16)`）+ `PATCH /api/profile` 端点 + 前端编辑弹窗（24 个可选 emoji：🙂😊😌🥰😎🤗😇🤔😴🥺😏🌴🌸🍀🌙⭐🐳🦊🐱🦌🐢🦋🌿🍄）；**头像同步树洞**（[AIChatView.vue](../../frontend/src/views/ai/AIChatView.vue) 使用 `userStore.avatar` 显示头像，与个人主页一致）；新增 [app/schemas/profile.py](../../app/schemas/profile.py) + `ProfileUpdateIn`（nickname 2-20 字符可选 / avatar 1-16 字符可选，昵称查重 409）。⑮ **露水累加修复**：写日记和留言鼓励后正确发放露水。**模型/迁移**：`User.avatar: str = "🙂"`（`_migrate_legacy_columns()` 加 `ALTER TABLE users ADD COLUMN avatar VARCHAR(16) DEFAULT '🙂' NOT NULL`）+ `mood_checkins 唯一约束移除`（SQLite 重建表方式：CREATE TABLE _new AS SELECT * → DROP → RENAME → CREATE INDEX，支持一天多条心情记录）。**常量**：[constants.py](../../app/utils/constants.py) `DEFAULT_SHOP_ITEMS` 扩充至 27 件（12 花种 + 9 装扮 + 6 徽章）；'古琴初学者' → '琴音知音'；'竹编帽'描述改为'种花人遮阳的草帽'；新增装扮：油纸伞 / 蓑衣 / 乌篷船 / 鱼竿 / 橘猫 / 白鹤。**前端**：[ProfileView.vue](../../frontend/src/views/profile/ProfileView.vue) 头像/昵称编辑弹窗 + 静屿使用指南（7 个模块详细介绍：琴音疗心 / 日记海岸 / 情绪日历 / 心语树洞 / 花坊 / 屿上花田 / 我的）；[HomeView.vue](../../frontend/src/views/HomeView.vue) 文案更新（'潮声不止，心安自屿'）+ 删除今日打卡 + 模块名'花坊'；[MoodCalendarView.vue](../../frontend/src/views/mood/MoodCalendarView.vue) emoji 显示修复 + 多条打卡支持；[GardenView.vue](../../frontend/src/views/garden/GardenView.vue) AI 显示基于实际种花情况（没种花不显示）；[stores/user.js](../../frontend/src/stores/user.js) 新增 `updateProfile` action（调用 `PATCH /api/profile`）。详见 §4 Phase 9。关键词 `v2.4` / `潮声不止心安自屿` / `花坊` / `一天多条心情` / `mood_checkins 唯一约束移除` / `add_checkin` / `get_today_moods` / `平均分` / `humanize` / `琴音知音` / `每板块徽章` / `User.avatar` / `PATCH /api/profile` / `ProfileUpdateIn` / `头像同步树洞` / `静屿使用指南` / `露水累加修复` 在 6 份文档中都要出现。

> 🔒 **2026-08-10 v2.4.1 情绪日历改用罗素情绪环模型（Russell's Circumplex Model of Affect）四象限图表**：本次将情绪日历模块的「30 天趋势柱状图」板块替换为「罗素情绪环模型四象限图表」，让用户从「效价 × 唤醒度」二维视角理解自己的情绪分布，不再只看趋势分数。**文件**：[MoodCalendarView.vue](../../frontend/src/views/mood/MoodCalendarView.vue)。① **移除**：30 天趋势柱状图板块——`trendBars` computed / `scoreColor` 函数 / `.trend-section` 模板 / `.trend-bar` 样式全部删除（`30 天趋势柱状图移除`）。② **新增**：罗素情绪环模型四象限图表——横轴 **效价 Valence**（左消极 → 右积极），纵轴 **唤醒度 Arousal**（下低唤醒 → 上高唤醒），四象限 Q1(积极+高唤醒) / Q2(消极+高唤醒) / Q3(消极+低唤醒) / Q4(积极+低唤醒)（`四象限图表`）。③ **数据**：定义 `CIRCUMPLEX_EMOTIONS` 数组（`20 种情绪`），每种情绪带 `valence`(-1~+1) 和 `arousal`(-1~+1) 坐标——其中 `6 种已追踪情绪`（ecstatic / happy / calm / tired / anxious / angry / sad）映射到后端 [constants.py](../../app/utils/constants.py) `MOOD_INFO`，有真实打卡数据；`14 种参考情绪`（兴奋 / 激动 / 恐慌 / 恐惧 / 极度烦躁 / 低落 / 压抑 / 倦怠 / 空虚 / 闲适 / 舒心 / 恬淡平和 / 兴致高昂 / 狂喜）帮助用户理解情绪在环模型中的位置。④ **交互**（`点击交互`）：点击 emoji → 弹出详情卡片，显示「`本月出现次数` X 次」；已追踪情绪有边框高亮 + 次数角标（右上角小圆点）；未追踪情绪显示「该情绪暂未开放打卡记录」；`emotionPosition(emotion)` 将 valence/arousal 转为 left% / top% 百分比定位。⑤ **统计**：`moodCounts` computed 从 `checkins` 数据统计本月各心情出现次数；`totalCheckins` 显示本月总打卡数。⑥ **视觉**：治愈系配色（四象限淡色背景）+ GSAP 入场动画（emoji 逐个弹出 `back.out` 缓动）+ 移动端响应式。⑦ **保留**：`fetchTrend` 仍调用（为 `currentStreak` 连续打卡天数显示），但 `trend` 数据不再用于渲染。详见 §4 Phase 10。关键词 `v2.4.1` / `Russell情绪环模型` / `Circumplex Model` / `四象限图表` / `效价Valence` / `唤醒度Arousal` / `CIRCUMPLEX_EMOTIONS` / `emotionPosition` / `moodCounts` / `20种情绪` / `6种已追踪` / `14种参考` / `点击交互` / `本月出现次数` 在 6 份文档中都要出现。

> 🔒 **2026-08-13 v2.4.2 整体架构优化与冗余清理（维护性清理版本）**：本次为维护性清理版本，**无功能变化 / 无数据库迁移 / 无新依赖**，7 项改动专注代码瘦身与一致性对齐。① **删除 15 个死模板 + 1 空目录**（`死模板清理`）：Vue 3 SPA 迁移前遗留的旧 Jinja2 SSR 模板——[templates/](../../templates/) 下 `base/_nav/_toast/index/login/register/music_list/diary_write/diary_detail/my_bottles/pick_bottle/mood_calendar/garden/shop/ai_chat.html` 全部删除 + `templates/partials/` 空目录删除；**仅保留** [templates/admin/](../../templates/admin/)（[admin_pages.py](../../app/routers/admin_pages.py) 仍使用 Jinja2 SSR）。② **删除 10 个死页面脚本**（`死页面脚本`）：[static/js/pages/](../../static/js/pages/) 下非 admin 脚本——`ai_chat/auth/diary/diary_detail/home/mood_calendar/music/my_bottles/pick/shop.js` 全部删除，仅被死模板引用，迁移后已无入口。③ **[app/main.py](../../app/main.py) 版本号 1.0.0 → 2.4.2**（`版本号对齐`）：与 git tag / README badge 对齐。④ **[app/main.py](../../app/main.py) `EXT_TO_MIME` 删除重复 `.webp` 条目**（`EXT_TO_MIME`）：字典中定义了两次，删除后者。⑤ **修复过时端口注释**（`过时注释`）：[app/routers/pages.py](../../app/routers/pages.py) / [frontend/vite.config.js](../../frontend/vite.config.js) / [static/js/app.js](../../static/js/app.js) 中 `:5173 → :5000`（Vite）/ `:5000 → :5001`（FastAPI 开发）。⑥ **新增 5 个五音封面 SVG**（`SVG封面`）：[static/img/cover_gong.svg](../../static/img/cover_gong.svg) / `cover_shang.svg` / `cover_jue.svg` / `cover_zhi.svg` / `cover_yu.svg`，颜色取自 [app/utils/constants.py](../../app/utils/constants.py) `YIN_INFO`，修复 [app/seed.py](../../app/seed.py) 引用的缺失资源。⑦ **[app/routers/admin_pages.py](../../app/routers/admin_pages.py) admin_users N+1 查询优化**（`N+1优化` / `GROUP BY`）：原 for 循环内 3 个 COUNT/用户 × 50 用户 = 151 次查询 → 1 次查用户 + 3 个 `GROUP BY` 聚合 + 字典拼接 = 4 次查询。**不动**：[static/css/](../../static/css/) 全部保留（admin/_base.html 加载 style.css）/ [static/js/app.js](../../static/js/app.js) 保留（仅改注释）/ [static/audio/](../../static/audio/) 保留（seed.py 生成占位 mp3）/ [templates/admin/](../../templates/admin/) 保留 / [config.py](../../config.py) / [app/database.py](../../app/database.py) / [requirements.txt](../../requirements.txt) 不动。关键词 `v2.4.2` / `死模板清理` / `死页面脚本` / `N+1优化` / `GROUP BY` / `SVG封面` / `EXT_TO_MIME` / `版本号对齐` / `过时注释` 在 6 份文档中都要出现。

> 🔒 **2026-08-14 v2.4.3 花语文案焕新 + emoji 名称对齐 + 徽章奖励落叶 + 树洞三层回复 + 情绪日历空 bug 修复**：本次为内容运营 + Bug 修复版本，**无新依赖**，专注文案打磨 / emoji 修正 / 资源死锁解除 / AI 回复质量提升。① **删除「古琴初学者」废弃徽章**（`废弃徽章删除`）：v2.4.0 改名「琴音知音」后旧徽章仍在 seed 残留，[app/seed.py](../../app/seed.py) 启动时清理 `DEPRECATED_BADGES = ["古琴初学者"]`，含 GardenItem 引用一并删除。② **「花田主人」→「花间客」**（`花间客改名`）：徽章命名太直白，改为更具诗意感的「花间客」；[app/utils/constants.py](../../app/utils/constants.py) + seed `RENAME_MAP` 迁移表 + [ProfileView.vue](../../frontend/src/views/profile/ProfileView.vue) 同步。③ **「花坊」→「落叶花坊」**（`落叶花坊改名`）：板块名更点题——落叶归根换花种，[HomeView.vue](../../frontend/src/views/HomeView.vue) 模块名 + [GardenView.vue](../../frontend/src/views/garden/GardenView.vue) 入口 + ProfileView 使用指南同步。④ **情绪日历空白 Bug 修复**（`情绪日历空白修复`）：[MoodCalendarView.vue](../../frontend/src/views/mood/MoodCalendarView.vue) `cell.moodKeys.length` 在空单元格上抛 `TypeError: Cannot read properties of undefined`，整页渲染中断显示空白；修复为 `cell.moodKeys?.length > 0`（含 moodInfos 同步加可选链）。⑤ **落叶死锁解除**（`落叶死锁解除` / `BADGE_LEAF_REWARD`）：原逻辑「没花没落叶 / 没落叶种不了花」形成死锁；[constants.py](../../app/utils/constants.py) 新增 `BADGE_LEAF_REWARD: Final[int] = 10`；[energy_service.py](../../app/services/energy_service.py) `check_achievements()` 每解锁一个徽章额外发放 10 落叶，返回 `{new_badges, new_leaves, leaves_balance}`；mood / diary / music / ai / energy 5 路由透传，前端 [MoodCalendarView](../../frontend/src/views/mood/MoodCalendarView.vue) / [DiaryWriteView](../../frontend/src/views/diary/DiaryWriteView.vue) / [PickBottleView](../../frontend/src/views/diary/PickBottleView.vue) / [AIChatView](../../frontend/src/views/ai/AIChatView.vue) 接 toast「解锁徽章「X」· 赠 10 落叶」。⑥ **花田 AI 显示基于实际种花**（`花田 AI 显示修复`）：[GardenView.vue](../../frontend/src/views/garden/GardenView.vue) `<FlowerField v-if="flowers.length > 0" />`，未种花时不渲染 3D 花田（避免空花田显示 AI 生成无关花朵）。⑦ **岛上物件 emoji 化**（`岛上物件 emoji`）：[GardenView.vue](../../frontend/src/views/garden/GardenView.vue) 「🏝️ 岛上物件」section 头部加 emoji。⑧ **首页 emoji 🏝️ → 🌊**（`首页海浪 emoji`）：[HomeView.vue](../../frontend/src/views/HomeView.vue) hero-icon 由沙滩 🏝️ 改为海浪 🌊，更贴合「静屿」海意。⑨ **树洞 AI 重写**（`树洞三层回复`）：[ai_service.py](../../app/services/ai_service.py) `SYSTEM_PROMPT_TREEHOLE` 重写为三层结构——① 接住情绪（1 句，准确点出感受，不复述原话）② 安慰或新视角（1-2 句，温暖肯定 / 温柔宽慰 / 换个角度）③ 具体可操作的小建议或问题（1-2 句，小 / 具体 / 现在就能做），解决旧版「只重复消极情绪、做无用情感共鸣」问题。⑩ **花种 emoji 与名称对齐 + 花语化**（`花语化` / `emoji 对齐`）：[constants.py](../../app/utils/constants.py) 12 种花种介绍全部改为「花语：XX」格式（向日葵「信念与爱慕」/ 竹子「坚韧虚心」/ 雏菊「天真纯洁」/ 莲花「清白坚贞」/ 薰衣草「等待爱情」/ 郁金香「完美的爱」/ 樱花「生命之美」/ 桃花「爱情降临」/ 青松「坚定长寿」/ 小麦「丰收富足」/ 青叶「生机新生」）；emoji 与名称对齐——薰衣草 💜→🪻（紫花浪漫）/ 桂花→小麦 🌾 / 银杏→青叶 🍃 / 兰花+梅花合并为樱花 🌸（删一留一，seed 去重）/ 白鹤→火烈鸟 🦩 / 蓑衣→斗篷 🧥。⑪ **装扮动物扩充**（`动物扩充`）：新增小鸟 🐦 / 小鸭 🦆 / 小狗 🐶 三件动物装扮。⑫ **漂流瓶 emoji 🍶 → 🏺**（`漂流瓶 emoji`）：[HomeView.vue](../../frontend/src/views/HomeView.vue) 漂流日记 icon + [DiaryWriteView](../../frontend/src/views/diary/DiaryWriteView.vue) 发布选项 + [EmojiIcon.vue](../../frontend/src/components/EmojiIcon.vue) twemoji 映射同步；拾瓶旅人徽章 🏺 与板块入口一致。⑬ **seed 改名迁移 + 去重**（`改名迁移` / `去重`）：[app/seed.py](../../app/seed.py) 启动时按 `RENAME_MAP` 改名老库物品 + 合并同名重复（如兰花+梅花都改名为樱花时保留 id 最小的，GardenItem 引用迁移到 keeper），避免老库重启出现重复行。⑭ **版本号 2.4.2 → 2.4.3**（`版本号对齐`）：[app/main.py](../../app/main.py) + README badge + 6 份文档同步。详见 §4 Phase 11。关键词 `v2.4.3` / `花语化` / `emoji 对齐` / `BADGE_LEAF_REWARD` / `落叶死锁解除` / `树洞三层回复` / `情绪日历空白修复` / `花间客改名` / `落叶花坊改名` / `改名迁移` / `去重` / `岛上物件 emoji` / `首页海浪 emoji` / `漂流瓶 emoji` / `动物扩充` / `花田 AI 显示修复` 在 6 份文档中都要出现。

> 🔧 **2026-08-15 v2.4.3 补丁（首页滚动提示可点击）**：[HomeView.vue](frontend/src/views/HomeView.vue) Hero 底部「向下」滚动提示原为 `pointer-events:none` 的 `<div>`（用户点击无反应），改为 `<button>` + `scrollToModules()` 点击平滑滚动到「岛上各处」板块，文案「向下沉入海面」→「向下，遇见岛上的去处」，hover 颜色反馈。纯前端交互修复，需重新 `npm run build`。

> 🔒 **2026-08-15 v2.4.4 情绪日历透明修复 + 旧版日记迁移 + mood_checkins 主键重建 + 头像图片上传 + 落叶花坊文案打磨**：本次为 Bug 修复 + 功能增强版本，专注修复用户反馈的可见性 / 数据完整性 / 表结构问题 + 新增头像上传功能。① **[BUG FIX] 情绪日历 emoji 透明**（`情绪日历透明修复`）：[MoodCalendarView.vue](../../frontend/src/views/mood/MoodCalendarView.vue) GSAP 动画设置了 `opacity:0` 导致心情选择按钮几乎不可见，已移除该属性。② **[BUG FIX] 旧版日记无内容**（`旧版日记迁移`）：旧版加密日记 `content` 字段为空（`content_encrypted` 是假占位符），数据库迁移自动填入提示文本「（这段日记来自旧版本，内容已无法读取）」。③ **[BUG FIX] mood_checkins 表缺失 PRIMARY KEY**（`mood_checkins 主键重建`）：v2.4 的迁移用了 `CREATE TABLE AS SELECT` 导致 `mood_checkins` 表丢失主键和自增，批量打卡时 `db.flush()` 报 `NULL identity key` 错误（500）。已重建表（`id INTEGER PRIMARY KEY AUTOINCREMENT` + FK + 索引），数据完整迁移。④ **[BUG FIX] avatar 字段长度**（`avatar 字段长度`）：[User.avatar](../../app/models/user.py) 原为 `String(16)`，无法存储图片上传后的 URL 路径（如 `/static/uploads/avatars/1_1234567890.jpg`）。已改为 `String(255)`，[ProfileUpdateIn](../../app/schemas/profile.py) schema 同步调整为 `max_length=255`。⑤ **[FEATURE] 头像支持图片上传**（`头像图片上传`）：新增 `POST /api/profile/avatar` 端点，支持 JPG/PNG/WebP/GIF（≤2MB），存储到 `static/uploads/avatars/`。[ProfileView.vue](../../frontend/src/views/profile/ProfileView.vue) 增加上传按钮（支持拍摄/相册选择），[AIChatView.vue](../../frontend/src/views/ai/AIChatView.vue) 支持图片头像渲染。⑥ **[IMPROVEMENT] 落叶花坊花朵介绍**（`花朵介绍`）：移除「花语：」前缀，只保留完整花语。⑦ **[IMPROVEMENT] 徽章落叶奖励分级**（`徽章落叶分级`）：按徽章 trigger 分级设置落叶奖励（streak_7=7, listen_10=10, pick_10=10, flower_10=10, chat_20=15, diary_30=20, 默认=10），替代原来统一的固定值。⑧ **[IMPROVEMENT] 情绪日历使用指南更新**（`情绪日历指南`）：介绍改为罗素情绪环模型（Russell's Circumplex Model）四象限说明。⑨ **[IMPROVEMENT] 岛上物件 emoji**（`岛上物件 emoji`）：🎁 → 🧳（行李箱）。⑩ **[IMPROVEMENT] 通知 emoji 统一**（`通知 emoji 统一`）：漂流瓶回复通知的 emoji 统一为 💛（黄色爱心）。详见 §4 Phase 12。关键词 `v2.4.4` / `情绪日历透明修复` / `旧版日记迁移` / `mood_checkins 主键重建` / `avatar 字段长度` / `头像图片上传` / `花朵介绍` / `徽章落叶分级` / `情绪日历指南` / `岛上物件 emoji` / `通知 emoji 统一` 在 6 份文档中都要出现。

---

> 🔒 **2026-08-16 v2.4.5 情绪日历 30 天趋势柱状图恢复 + 罗素情绪环显示修复 + 头像相册选择 + 通知空状态 emoji 统一**：本次为 Bug 修复版本，修复用户反馈的 4 个问题，**纯前端改动（3 个文件），无后端改动 / 无数据库迁移 / 无新依赖**。① **[BUG FIX] 情绪日历打卡后柱状图不显示**（`30天趋势柱状图恢复`）：v2.4.1 将「30 天趋势柱状图」替换为罗素情绪环时整体删除了柱状图板块，用户习惯打卡后看柱状趋势。本次恢复该板块并与罗素情绪环**并存**——柱高 = 当日心情**平均分**（1-5 评分，一天多条取平均），柱色取当日主心情颜色渐变，柱顶悬浮当日主心情 emoji（悬浮提示含一天多条 ×N 角标），未记录日显示 3px 浅色占位柱，底部首尾日期轴。② **[BUG FIX] 罗素情绪环模型不显示**（`罗素情绪环显示修复`）：GSAP `from()` 动画残留 `opacity:0` / `scale:0` 初始态，动画被中断（切后台 / 路由切换）时元素**永久卡在不可见状态**（与 v2.4.4「透明 bug」同类根因）。修复：入场动画只保留位移动画（`y`），**不设置 `opacity` / `scale` 初始态**。③ **[BUG FIX] 头像只能拍照不能从相册选择**（`头像相册选择`）：[ProfileView.vue](../../frontend/src/views/profile/ProfileView.vue) 头像上传 `<input type="file">` 带 `capture="environment"` 属性，移动端强制调起相机。移除 `capture` 属性后弹出系统「拍照 / 从相册选择」选择框，按钮文案同步为「📷 拍照 / 从相册选择」。④ **[BUG FIX] 通知空状态 emoji 错误**（`通知空状态emoji`）：[NotificationsView.vue](../../frontend/src/views/notification/NotificationsView.vue) 空状态 emoji 🌙 → 💛，与 v2.4.4「通知 emoji 统一 💛」对齐。详见 §4 Phase 13。关键词 `v2.4.5` / `30天趋势柱状图恢复` / `罗素情绪环显示修复` / `头像相册选择` / `通知空状态emoji` 在 6 份文档中都要出现。

---

## 0. 你正在接手什么

**项目名**：静屿（代号，可改）
**类型**：治愈系身心疗愈 Web 应用
**性质**：非商业 / 纯治愈 / 强隐私 / 轻运营
**代码体量**：约 2 500 行 Python（FastAPI 纯 API 后端 + SPA fallback）+ Vue 3 SPA 工程化前端（`frontend/`，约 3 000 行 `.vue`/`.js`）
**当前阶段**：v2.4.5 — 2026-08-16 情绪日历 30 天趋势柱状图恢复 + 罗素情绪环显示修复 + 头像相册选择 + 通知空状态 emoji 统一（Bug 修复版本：恢复 30 天趋势柱状图并与罗素情绪环并存 / GSAP 动画只保留位移修复罗素环不显示 / 移除 capture 属性支持相册选头像 / 通知空状态 emoji 🌙→💛，纯前端 3 文件改动）。前一阶段 v2.4.4（2026-08-15 情绪日历透明修复 + 旧版日记迁移 + mood_checkins 主键重建 + 头像图片上传 + 落叶花坊文案打磨，详见 §4 Phase 12）+ v2.4.3（2026-08-14 花语文案焕新 + emoji 名称对齐 + 徽章奖励落叶 + 树洞三层回复 + 情绪日历空 bug 修复，详见 §4 Phase 11）+ v2.4.2（2026-08-13 整体架构优化与冗余清理，维护性清理版本，详见 §4 Phase 10 后段）+ v2.4.1（2026-08-10 情绪日历改用罗素情绪环模型四象限图表，替换原 30 天趋势柱状图，详见 §4 Phase 10）+ v2.4.0（2026-08-10 文案焕新 + 一天多条心情 + 头像/昵称编辑 + 花坊改名 + 露水累加修复，详见 §4 Phase 9）+ v2.3.3（2026-07-30 Safari 兼容性修复：3D 上下文恢复 + emoji 跨浏览器一致，详见 §4 Phase 8）+ v2.3.2（2026-07-28 start.py 默认生产模式 + 自动构建简化）+ v2.3（2026-07-25 六大四字名模块重构 + 双资源系统 + 花朵生命周期 + 通知 + 个人主页 + 古琴弹西洋曲谱，详见 §4 Phase 7）。v2.0 全站 Vue 3 重构基础保留（4 个 Phase + 秘密后台 + AI 全面接入 + Vue 3 SPA 前端）。

---

## 1. 30 秒跑起来

```bash
cd c:\Users\Administrator\Desktop\webwrold
pip install -r requirements.txt
python start.py
# 浏览器自动打开 http://127.0.0.1:5000
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

**秘密后台**：`http://127.0.0.1:5000/admin`（默认入口）
- 首次启动会自动创建管理员 `admin`，密码**随机生成并写入 `logs/healing.log`**（看 `[ADMIN] password :` 一行）
- 强烈建议在 `.env` 里设置 `QI_ADMIN_USERNAME` + `QI_ADMIN_PASSWORD` 固定一个强密码
- 不在任何前台页面放链接，纯粹靠 URL 入口
- **当前数据库内的真实首管密码**（2026-07-15 测试用）：`GKmZinzvoXQbaK2D`
  > 这是会话中通过直接改 SQLite 写回的固定密码，便于人工测试；生产环境请改 `.env` → `QI_ADMIN_PASSWORD=` 强密码。

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
- dev proxy `/api` / `/static` / `/admin` / `/docs` / `/openapi.json` → FastAPI `:5001`（[frontend/vite.config.js](file:///c:/Users/Administrator/Desktop/webwrold/frontend/vite.config.js)）
- 生产（默认，部署用）：`python start.py` → dist 不存在则自动构建 → FastAPI :5000 单进程 SPA fallback（详见 [docs/DEPLOYMENT.md](file:///c:/Users/Administrator/Desktop/webwrold/docs/DEPLOYMENT.md)「前端构建」）

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
| 前端路由 | **Vue Router 4** | 13 条路由，`requiresAuth` 守卫 |
| 前端状态 | **Pinia** | user store（cookie session 模式，不存 token） |
| 前端样式 | **Tailwind CSS 3.4** | 治愈系色彩 token + 动画（breathe/float/fade-up） |
| 前端动效 | **GSAP 3.12 + @vueuse/motion 2.2** | 入场 stagger + 呼吸动效，`prefers-reduced-motion` 降级 |
| 前端 3D | **Three.js 0.168** | 4 个治愈系 3D / Canvas 组件群（v2.2 PBR 升级版，v2.3.3 Safari 兼容增强）：① [FlowerField.vue](file:///c:/Users/Administrator/Desktop/webwrold/frontend/src/components/FlowerField.vue) 3D 花田 v2（自定义 `BufferGeometry` 立体花瓣 + `MeshPhysicalMaterial` + `UnrealBloomPass` + `OrbitControls` + `raycaster` 点击花语）；② [AmbientBackground.vue](file:///c:/Users/Administrator/Desktop/webwrold/frontend/src/components/AmbientBackground.vue) 全局氛围背景 v2（Canvas2D 柔光 sprite + 鼠标排斥 + Three.js 双层粒子 + 滚动视差 + 轻量 Bloom）；③ [HeroScene.vue](file:///c:/Users/Administrator/Desktop/webwrold/frontend/src/components/HeroScene.vue) 首页浮岛雾海 v2（`LatheGeometry` 浮岛 + 递归樱花树 + PBR 水面 shader + `UnrealBloomPass` + `OrbitControls` + `raycaster` 飞入；v2.3.3 **iOS 降级**：**Bloom 降级** + **PMREM 降级** + `webglcontextlost` 上下文恢复）；④ [AudioVisualizer.vue](file:///c:/Users/Administrator/Desktop/webwrold/frontend/src/components/AudioVisualizer.vue) 音波可视化 v2（4 模式 wave/mirror/radial/particles + 节拍检测 + 频响颜色 + 点击切换）。配套 [utils/visual.js](file:///c:/Users/Administrator/Desktop/webwrold/frontend/src/utils/visual.js) 能力检测（v2.3.3 **hasWebGL 重写** + `getWebGLCaps` / `isSafari` / `isIOS`）+ [utils/three-helpers.js](file:///c:/Users/Administrator/Desktop/webwrold/frontend/src/utils/three-helpers.js) PBR 工具集（v2.2 加，9 个共享函数；v2.3.3 加 `webglcontextlost` / `webglcontextrestored` 事件监听处理 **WebGL 上下文丢失**）+ [SceneHint.vue](file:///c:/Users/Administrator/Desktop/webwrold/frontend/src/components/SceneHint.vue) 交互指引横幅 + [SceneControls.vue](file:///c:/Users/Administrator/Desktop/webwrold/frontend/src/components/SceneControls.vue) 视图控制工具栏。全部支持 SVG / CSS 静态降级 + `prefers-reduced-motion` + `OrbitControls` 拖拽旋转 / 滚轮缩放 + `raycaster` 点击拾取 |
| 前端 emoji | **Iconify + @iconify-json/twemoji**（v2.3.3 加） | [EmojiIcon.vue](file:///c:/Users/Administrator/Desktop/webwrold/frontend/src/components/EmojiIcon.vue) 离线 **SVG emoji** 组件，解决 Safari Apple Color Emoji 与系统 emoji 字体风格差异，确保 **跨浏览器一致**；已替换 AppLayout.vue + ProfileView.vue 所有 emoji |
| 前端 HTTP | **axios 1.7** | `baseURL=/api`，`withCredentials=true`，401 自动跳登录 |
| 密码哈希 | **bcrypt 4.x**（直接用，不用 passlib） | passlib 与 4.x 不兼容 |
| 日记加密 | **Fernet (AES-128-CBC + HMAC)** | 客户端 Web Crypto PBKDF2 派生密钥 |
| 会话 | **itsdangerous URLSafeTimedSerializer** | 签名 cookie，HttpOnly + SameSite=Lax |
| 启动 | **uvicorn** | `app.main:app` |

**前端字体依赖**（2026-07-19 重构后）：Vue 3 SPA 用 [frontend/src/assets/styles/main.css](file:///c:/Users/Administrator/Desktop/webwrold/frontend/src/assets/styles/main.css) 的系统字体栈 `"PingFang SC", "Microsoft YaHei"`，**零网络请求**，不再依赖任何 Google Fonts 镜像。后台 `/admin/*` SSR 仍走旧 [templates/admin/_base.html](file:///c:/Users/Administrator/Desktop/webwrold/templates/admin/_base.html) 的 `fonts.loli.net` 镜像 + 系统字体兜底。

**不要做的事**：
- ❌ 引入 React / Angular / Svelte —— Vue 3 已选定，不要再讨论
- ❌ 引入 Alembic —— 改完模型重启即可，`init_db()` 自动建表
- ❌ 把 `passlib` 拉回来 —— 用 `app/utils/crypto.py` 里直接调 bcrypt 的版本
- ❌ 在 Vue SPA 之外另起前端框架 —— 后台 `/admin/*` 保留 Jinja2 SSR 是有意为之（独立隔离）

---

## 3. 项目结构

```
webwrold/
├── start.py                  ← 服务管理脚本（start/stop/restart/status/fg/build；默认应用模式 Vite :5000 + FastAPI :5001，--prod 走生产模式）
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
│   │   └── ai.py             ← AI 4 场景 Pydantic（2026-07-17 加，7 个模型：ChatMessage/AIChatIn/Out/AIEncouragementIn/AIHealingIn/AIMusicRecommendIn/Out）
│   │
│   ├── routers/              ← 一个领域一个文件
│   │   ├── pages.py          ← SSR 页面（/、/login、/music/*、/diary 等，含 /ai-chat）
│   │   ├── auth.py / music.py / diary.py / mood.py / energy.py / garden.py
│   │   ├── admin.py          ← 后台 API（/api/admin/*）
│   │   ├── admin_pages.py    ← 后台 SSR 页面（/admin/*）
│   │   └── ai.py             ← /api/ai/* 4 个 AI 端点（2026-07-17 加，全部需登录 + 全部有降级）
│   │
│   ├── services/             ← 业务逻辑层（routers 不直接调 model）
│   │   ├── energy_service.py ← 能量获取 + 单日上限
│   │   ├── diary_service.py  ← 漂流瓶随机抽取
│   │   ├── mood_service.py   ← 日历 + 30 天趋势
│   │   └── ai_service.py     ← NVIDIA NIM API 调用 + 降级处理（2026-07-17 加，4 个场景 + _call_nvidia 底层 + AIServiceUnavailable 异常）
│   │
│   └── utils/
│       ├── constants.py      ← YIN_TYPES / MOOD_INFO / ENERGY_RULES
│       └── crypto.py         ← bcrypt + Fernet + PBKDF2
│
├── templates/                ← Jinja2（14 个前台页面 + 7 个后台页面 + 宏）
│   ├── base.html / _nav.html / _toast.html
│   ├── index.html / login.html / register.html   ← index.html 加「AI 帮我选音」卡片（仅登录可见，2026-07-17）
│   ├── music_list.html
│   ├── diary_write.html / my_bottles.html / diary_detail.html / pick_bottle.html   ← pick_bottle.html 加 #ai-encouragement 容器（2026-07-17）
│   ├── mood_calendar.html      ← 情绪日历（今日打卡仅选表情 + 月历 + 30 天趋势 + #ai-healing-msg 容器；2026-07-16 会话 6 合并原 /mood 打卡页 / 会话 7 删文本输入、emoji 替代数字；2026-07-17 加 AI 治愈语）
│   ├── garden.html / shop.html
│   ├── ai_chat.html            ← AI 树洞对话页（2026-07-17 加，独立页面，需登录，多轮对话仅存浏览器内存）
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
│   │   ├── 05-animations.css ← 漂流瓶动效 / 心情弹跳 / 花朵生长 / §2 交互增强（reveal / ripple / countup / petals / eq-bars / page-transition / title-shimmer / confetti）
│   │   ├── 06-music.css
│   │   └── 07-admin.css      ← 后台专属（暗色侧栏 + 表格 + 模态）
│   ├── js/
│   │   ├── app.js            ← window.QI 全局（fetch / toast / confirmThen / reveal / ripple / countUp / confetti / petals / pageTransition / passwordToggle）
│   │   └── pages/            ← 一页一个 JS
│   │       ├── auth.js / music.js / diary.js / diary_detail.js
│   │       ├── my_bottles.js / pick.js   ← pick.js 加 loadAIEncouragement（2026-07-17，拾瓶后调 /api/ai/encouragement）
│   │       ├── mood_calendar.js ← 情绪日历（含今日打卡逻辑；2026-07-16 会话 6 合并原 mood.js / 会话 7 删文本输入、note 提交 null、emoji 替代数字；2026-07-17 加 loadAIHealing 调 /api/ai/healing）
│   │       ├── ai_chat.js      ← AI 树洞对话页逻辑（2026-07-17 加，多轮对话历史只存浏览器内存）
│   │       ├── home.js         ← 首页「AI 帮我选音」卡片逻辑（2026-07-17 加，新建，调 /api/ai/recommend-music）
│   │       ├── shop.js
│   │       ├── admin_login.js / admin_dashboard.js
│   │       ├── admin_users.js / admin_user_detail.js
│   │       ├── admin_logs.js / admin_system.js
│   ├── audio/                ← 5 个占位 mp3（每音一个）
│   └── images/               ← 占位封面（按需添加）
│
├── frontend/                 ← Vue 3 SPA 源码（2026-07-19 v2.0 重构加，详见 §5.8）
│   ├── package.json          ← 依赖：vue/vue-router/pinia/axios/gsap/@vueuse/motion/three；devDeps：vite/@vitejs/plugin-vue/tailwindcss
│   ├── vite.config.js        ← dev :5000 + proxy /api /static /admin /docs /openapi.json → :5001；build outDir ../static/dist；manualChunks（three-vendor / gsap-vendor / vue-vendor 三 chunk）
│   ├── tailwind.config.js    ← 治愈系色彩 token（mist/ink/五音色/accent）+ 动画（breathe/float/fade-up）
│   ├── index.html
│   └── src/
│       ├── main.js / App.vue
│       ├── router/index.js   ← 13 条路由 + requiresAuth 守卫
│       ├── stores/user.js    ← Pinia user store（cookie session 模式，不存 token）
│       ├── api/index.js      ← axios 实例（baseURL=/api，withCredentials=true，401 自动跳登录）
│       ├── assets/styles/main.css
│       ├── components/
│       │   ├── AppLayout.vue        ← 桌面顶部导航 + 移动端底部 tabbar（768px 断点）+ 挂载 AmbientBackground
│       │   ├── FlowerField.vue      ← Three.js 3D 花田（60 朵花 × 5 瓣 = 300 InstancedMesh；治愈系 5 色；异步加载；2026-07-19 加）
│       │   ├── AmbientBackground.vue ← 全局氛围背景（CSS 雾气 + Canvas2D 光点 + Three.js 粒子层三层渐进增强；挂在 AppLayout 根；2026-07-20 加）
│       │   ├── HeroScene.vue        ← 首页 Hero 区 3D 浮岛雾海（PlaneGeometry 波动海面 + 3 浮岛 + FogExp2 + SVG 降级；2026-07-20 加）
│       │   └── AudioVisualizer.vue  ← 5 色音波可视化（Web Audio API AnalyserNode + Canvas2D；挂在 MusicDetailView；2026-07-20 加）
│       ├── utils/
│       │   └── visual.js      ← 视觉能力检测（hasWebGL / prefersReducedMotion / isMobile / isLowPower / shouldUseThreeJS / shouldUseCanvas / smartRAF；2026-07-20 加）
│       └── views/             ← 13 个视图（HomeView / auth / music / diary / mood / ai / garden / NotFoundView）
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

### Phase 4 — 情绪日历 + 屿上花田
- 6 种心情表情（开心/平静/疲惫/焦虑/生气/悲伤）
- 月份日历 + 30 天趋势折线图
- 每天限 1 次，可覆盖
- **模块职责分离**（2026-07-16 会话 7 起）：
  - 情绪日历**只选表情**，文本输入已删除；日历格子用 emoji 替代数字直观反映当日心情
  - 日记编辑页**不再选心情**，心情选择与日记编写完全分离；日记正文可自由粘贴任何 emoji
  - 历史数据零迁移：`MoodCheckin.note` 本就 `nullable=True` 且 DB 查无历史数据；`Diary.mood_type` 字段保留（向后兼容历史数据，新日记为 null）
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

### Phase 6 — AI 全面接入（NVIDIA NIM API，2026-07-17 加）
> 设计原则：**「渐进增强」+「不污染数据」+「治愈系温柔语气」** —— AI 是陪伴而非诊断，不诊断不开药，危机情况引导求助专业资源。

**模型与 API**：
- 模型：`meta/llama-3.1-8b-instruct`（8B 小模型，响应快；原默认 `nvidia/llama-3.1-nemotron-70b-instruct` 在用户 NVIDIA 账户下 API 返回 404 不可用，详见 §5.7）
- API：`https://integrate.api.nvidia.com/v1/chat/completions`（OpenAI 兼容格式）
- 客户端：`httpx.Client`，60s 超时，同步调用（8B 实际 1-10s，60s 纯兜底）
- 依赖：`httpx>=0.27.0,<0.29.0`（[requirements.txt](file:///c:/Users/Administrator/Desktop/webwrold/requirements.txt)）

**4 个 AI 场景**（全部接入，**全部需登录**，**全部有降级处理**）：

| # | 场景 | 前端 | 后端端点 | AI 文案去向 |
|---|---|---|---|---|
| 1 | AI 树洞对话 | [templates/ai_chat.html](file:///c:/Users/Administrator/Desktop/webwrold/templates/ai_chat.html) + [static/js/pages/ai_chat.js](file:///c:/Users/Administrator/Desktop/webwrold/static/js/pages/ai_chat.js) | `POST /api/ai/chat` | 多轮对话，历史只在浏览器内存，**刷新清空，不落库** |
| 2 | 漂流瓶 AI 鼓励语 | [templates/pick_bottle.html](file:///c:/Users/Administrator/Desktop/webwrold/templates/pick_bottle.html) `#ai-encouragement` + [static/js/pages/pick.js](file:///c:/Users/Administrator/Desktop/webwrold/static/js/pages/pick.js) `loadAIEncouragement` | `POST /api/ai/encouragement` | 给读者看的现场文案，**不写库**，不污染作者收件箱 |
| 3 | 情绪日历 AI 治愈语 | [templates/mood_calendar.html](file:///c:/Users/Administrator/Desktop/webwrold/templates/mood_calendar.html) `#ai-healing-msg` + [static/js/pages/mood_calendar.js](file:///c:/Users/Administrator/Desktop/webwrold/static/js/pages/mood_calendar.js) `loadAIHealing` | `POST /api/ai/healing` | 显示在今日心情卡片下方，**不落库** |
| 4 | 音乐 AI 心情推荐 | [templates/index.html](file:///c:/Users/Administrator/Desktop/webwrold/templates/index.html) 「AI 帮我选音」卡片（仅登录可见）+ [static/js/pages/home.js](file:///c:/Users/Administrator/Desktop/webwrold/static/js/pages/home.js)（新建） | `POST /api/ai/recommend-music` | 推荐宫商角徵羽之一 + 理由 + 跳转 `/music/{yin}` |

**后端模块清单**：
- 配置：[app/config.py](file:///c:/Users/Administrator/Desktop/webwrold/app/config.py) `Settings` 类新增 3 字段 `nvidia_api_key` / `ai_model` / `ai_base_url`
- Schema：[app/schemas/ai.py](file:///c:/Users/Administrator/Desktop/webwrold/app/schemas/ai.py) — 7 个 Pydantic 模型（`ChatMessage` / `AIChatIn` / `AIChatOut` / `AIEncouragementIn` / `AIHealingIn` / `AIMusicRecommendIn` / `AIMusicRecommendOut`），已注册到 [app/schemas/__init__.py](file:///c:/Users/Administrator/Desktop/webwrold/app/schemas/__init__.py) 的 `__all__` + `model_rebuild()`
- Service：[app/services/ai_service.py](file:///c:/Users/Administrator/Desktop/webwrold/app/services/ai_service.py) — `AIServiceUnavailable` 异常 + 4 个系统提示词常量（温柔倾听风格，不诊断不开药，危机引导专业帮助） + `_call_nvidia(system_prompt, user_content, *, max_tokens, temperature, history)` 底层同步调用 + 4 个上层方法 `chat()` / `generate_encouragement()` / `generate_healing_message()` / `recommend_music()`。`recommend_music` 有容错 JSON 解析（处理 ```` ```json ```` 包裹、find `{` 到 `}`）
- Router：[app/routers/ai.py](file:///c:/Users/Administrator/Desktop/webwrold/app/routers/ai.py) — 4 个端点全部 `Depends(get_current_user)` + 全部 try/except 降级
- 入口注册：[app/main.py](file:///c:/Users/Administrator/Desktop/webwrold/app/main.py) 注册 `ai router`（prefix=`/api/ai`）

**降级策略**（重要）：所有 AI 端点在以下情况返回 `200 + available:false + 治愈系友好提示`（**不报 500**）：
- 未配置 `QI_NVIDIA_API_KEY`
- NVIDIA API 调用失败（网络/超时/限流/4xx/5xx）

前端拿到 `available:false` 时**仍正常显示**提示文案，不报错。这保证 AI 接入是「渐进增强」——没有 key 也能正常用所有功能。

**隐私承诺**：
- AI 树洞对话历史只在浏览器内存，**刷新即清空，不落库**
- 漂流瓶 AI 鼓励语是给读者看的，**不写入数据库，不污染作者收件箱**
- 情绪日历 AI 治愈语也**不落库**
- 用户日记内容传给 AI 时**只取前 120 字预览**（在 `ai_service.generate_encouragement()` 里截断）

### Phase 7 — v2.3 六大四字名模块重构 + 双资源系统 + 花朵生命周期 + 通知 + 个人主页（2026-07-25 加）

> 设计原则：**「四字名治愈系命名 + 双资源经济 + 生命周期叙事 + 通知触达」** —— 用更具东方治愈调性的命名替代纯功能名；把原单一能量拆为 `露水`（向内获得：听歌/打卡/写日记）+ `落叶`（向外获得：花朵枯萎后拾取），让资源流转更贴合「向内生长 / 向外连接」的疗愈哲学；花朵生长链路用「种→芽→苞→放→凋」五阶段让用户感受到时间与陪伴；通知系统让原本散落各处的事件反馈集中可见。

**改动清单**（13 大项，详见 [README §3.8](../../README.md) / [PROJECT_STATE §2 v2.3 条目](../docs/PROJECT_STATE.md)）：

1. **主界面六大四字名板块**：琴音疗心（`/music`）/ 漂流日记（`/diary`）/ 情绪日历（`/calendar`）/ 心语树洞（`/ai-chat`）/ 落叶画坊（`/shop`）/ 屿上花田（`/garden`）；辅助入口：拾瓶（`/diary/pick` 🍶）/ 我的（`/profile` 👤）；[AppLayout.vue](../../frontend/src/components/AppLayout.vue) 顶部品牌图标由 🌿 草本更新为 🏝️ 岛屿 emoji + tabbar 用四字名短标签
2. **双资源系统**：`User.total_energy`（露水，保留）+ `User.leaves`（落叶，新增）替代原单一能量语义；`EnergyRecord` **不**加 `resource_type`（资源类型由 `source` + `ShopItem.cost_currency` 体现）；`ShopItem.cost_currency`（`dew`/`leaves`）决定扣哪种资源；`constants.DAILY_ENERGY_LIMITS = {listen_music: 20, write_diary: 10, checkin: 5}`（仅露水有日上限，落叶无日上限）
3. **花朵生命周期**：`UserFlower` 模型 + `flower_service` + `/api/garden/flowers/*` API；阶段 `seed → sprout → bud → bloom → wilted`，浇水消耗 1 露水推进；盛开后超 7 天未浇水 → 枯萎；拾取枯花 → +2 落叶
4. **通知系统**：`Notification` 模型 + `routers/notification.py`（单数）+ 前端 60s 轮询；触发点：拾瓶被鼓励（type=`encouragement`）
5. **个人主页**：`routers/profile.py` + `views/profile/ProfileView.vue`；`GET /api/profile` / `GET /api/profile/stats` / `GET /api/profile/{user_id}`；统计 + 双资源 + 最近活动时间线
6. **古琴弹西洋曲谱子菜单**：`musics.category` 列（`classic`/`western`）；seed 加 6 首西方名曲古琴改编（《绿袖子》《卡农》《致爱丽丝》《月光奏鸣曲》《天鹅湖》《昨日重现》）；`/api/music?category=western|classic`；前端 `/music/western` + `views/music/MusicWesternView.vue` 独立列表
7. **日记调整**：`Diary.content`（明文，v2.3 替代 `content_encrypted`）+ `Diary.send_to_ai_hole`（bool，不放入漂流瓶时同步树洞）；前端 DiaryWriteView 加发布选项 radio（放入漂流瓶 🍶 / 不放入 🌳）
8. **情绪日历对齐修复**：前后端 `mood_emoji` 统一为 emoji 字符（如 "😊"），原 "calm" 字符串废弃；`MOOD_INFO` 加 `emoji` 字段统一管理
9. **树洞改进**：统一 🌳 树 emoji 图标（心语树洞）；`<textarea>` 多行输入 + 500 字提示；文件式聊天历史 `data/chat_history/<user_id>/<conversation_id>.json`，单对话上限 100 条，用户可选「保留」/「不保留」；离开提示「树洞会在这里等你回来」
10. **漂流瓶社交化**：拾瓶被鼓励走 Notification（type=`encouragement`）；作者收到「收到 1 个陌生人的拥抱」通知
11. **移动端兼容**：花园 / 个人主页 / 通知列表 / 树洞 / 西方曲谱列表全部覆盖 v2.2.3 三档断点 + safe-area + 100dvh
12. **琴音疗心板块即 /music 顶级模块**：`/music` 整合 5 音卡片 + 西方曲谱入口 + 播放器入口 + AI 选音；新增 `/music/western` 子路由（**必须放在 `/music/:yin` 前面**避免动态段捕获）
13. **pre-commit 5 项 checklist 正式化**：Pydantic Out / `_migrate_legacy_columns` / `constants.py` / `.env.example` / README+HANDOFF 速查表（详见 [§12.4](#124-文档--摆设--验收清单) / [README §9.3](../../README.md) / [PROJECT_STATE §8.3](../PROJECT_STATE.md)）

**新增文件**：
- 后端：`app/models/notification.py` / `app/models/garden.py`（`UserFlower` 并入此文件）/ `app/routers/notification.py`（单数）/ `app/routers/profile.py` / `app/services/flower_service.py` / `app/services/chat_history_service.py` / `app/schemas/notification.py` / `app/schemas/profile.py`
- 前端：`frontend/src/views/profile/ProfileView.vue` / `frontend/src/views/music/MusicWesternView.vue` / `frontend/src/views/notification/NotificationsView.vue`
- 数据：`data/chat_history/` 目录（树洞聊天历史文件，按 `<user_id>/<conversation_id>.json` 组织）

**数据库迁移**（`_migrate_legacy_columns()` 一次性自动加 5 列）：
- `users` 加 `leaves INTEGER DEFAULT 0 NOT NULL`（`total_energy` 即露水，原已存在不改）
- `diaries` 加 `content TEXT NOT NULL DEFAULT ''` + `send_to_ai_hole BOOLEAN DEFAULT 0 NOT NULL`
- `shop_items` 加 `cost_currency VARCHAR(20) DEFAULT 'dew' NOT NULL`
- `musics` 加 `category VARCHAR(20) DEFAULT 'classic' NOT NULL`
- 新表 `user_flowers` / `notifications` 由 `init_db()` 自动建表

**Smoke test 结果**（详见 [README §7.1](../../README.md) / [PROJECT_STATE §2](../PROJECT_STATE.md)）：`python start.py restart` ✅ / `curl /` 200 / `curl /api/music` 200（含西方 6 首，共 22 首）/ `curl /music` 200 / `curl /profile` 302 / `curl /music/western` 200 / `curl /api/admin/stats` 401 / `npm run build` 通过 / `_migrate_legacy_columns` 跑通（5 列）/ 双资源 UI 显示正常 / 通知 60s 轮询生效。

**6 份文档同步**（Iron Rule）：README §3.4/§3.8/§4/§7.1/§9.3 + 状态徽章 + 顶部提示 / HANDOFF §0/§4 Phase 7/§12.4/末次更新（本节）/ PROJECT_STATE §1/§2（本条）/ ARCHITECTURE §1.1.7/§7.7 / DEPLOYMENT 顶部提示 / DEVELOPMENT §1.9.4 + pre-commit 5 项。**6 份文档同步**（README / HANDOFF / PROJECT_STATE / ARCHITECTURE / DEPLOYMENT / DEVELOPMENT）。

### Phase 8 — v2.3.2 + v2.3.3 start.py 默认生产模式 + Safari 兼容性修复（2026-07-28 / 2026-07-30 加）

> 设计原则：**「部署最简 + Safari 兼容兜底」** —— v2.3.2 回滚 v2.2.2「默认应用模式」决策，因为服务器端口代理已配好 :5000 不能动，应用模式会让 Vite 占 :5000 破坏代理；v2.3.3 解决 Safari / iOS 用户反馈的 3D 不渲染 + emoji 不一致两类问题。

**v2.3.2 改动**（2026-07-28，start.py 默认生产模式 + 自动构建简化）：
1. **默认生产模式**：`python start.py`（无参数）默认走生产模式（FastAPI :5000 单进程），回滚 v2.2.2 默认应用模式
2. **`dist 存在检测`**：自动构建仅检测 `static/dist/index.html` 存在性，不再比较 `frontend/src/` 与 `static/dist/` 文件修改时间
3. **`自动构建`**：dist 不存在时自动 `npm install + npm run build`（需 Node.js 18+）
4. **`--dev` 应用模式**：开发需显式 `python start.py --dev`（Vite :5000 HMR + FastAPI :5001 API，前后端一起起的「应用模式」）
5. **`--prod` 兼容别名**：默认就是生产模式，加不加效果一样
6. **服务器部署 2 步**：① 上传代码 ② `python start.py`（首次自动构建，之后秒启）

**v2.3.3 改动**（2026-07-30，Safari 兼容性修复）：
1. **Safari 主页 3D 不渲染**修复：
   - **`hasWebGL` 重写**：[utils/visual.js](../../frontend/src/utils/visual.js) 区分 WebGL1/2 + 检测扩展 + max texture size
   - 新增 `getWebGLCaps()` / `isSafari()` / `isIOS()` 工具函数
   - [three-helpers.js](../../frontend/src/utils/three-helpers.js) 添加 `webglcontextlost` / `webglcontextrestored` 事件监听，处理 **WebGL 上下文丢失**（iOS Safari 切后台→前台触发），上下文丢失时保存场景状态、恢复时重建
   - [HeroScene.vue](../../frontend/src/components/HeroScene.vue) **iOS 降级**：**Bloom 降级**（iOS 关闭 UnrealBloomPass）+ **PMREM 降级**（iOS PMREM 256→128、阴影 2048→1024、dpr 上限 2→1.5；老 iOS 缺 `EXT_color_buffer_half_float` 扩展时关闭 PMREM + Bloom）
2. **Safari emoji 显示不一致**修复：
   - 新建 [EmojiIcon.vue](../../frontend/src/components/EmojiIcon.vue) 组件，使用 **Iconify** + `@iconify-json/twemoji` 离线 **SVG emoji**，确保 **跨浏览器一致**
   - 替换 [AppLayout.vue](../../frontend/src/components/AppLayout.vue)（品牌 / 导航 / 通知 / 资源）+ [ProfileView.vue](../../frontend/src/views/profile/ProfileView.vue)（头像 / 通知 / 资源 / 统计 / 快捷入口 / 花朵阶段）所有 emoji
3. 构建 209 modules / 12.30s，HeroScene +0.71KB（降级逻辑）

**6 份文档同步**（Iron Rule）：README §2/§3.5/§8 + 状态徽章 + 顶部提示 / HANDOFF §0/§1/§2/§4 Phase 8/§6.24（本节）/ PROJECT_STATE §1/§2（本条）/ ARCHITECTURE §1.1.6/§7.7 / DEPLOYMENT 顶部提示 / DEVELOPMENT §1.9。**6 份文档同步**（README / HANDOFF / PROJECT_STATE / ARCHITECTURE / DEPLOYMENT / DEVELOPMENT）。

### Phase 9 — v2.4.0 文案焕新 + 一天多条心情 + 头像/昵称编辑 + 花坊改名 + 露水累加修复（2026-08-10 加）

> 设计原则：**「情绪是多变的 + 个性化表达 + 文案焕新 + 资源发放修复」** —— 情绪不是一天一次的打卡，而是流动的、多变的，所以移除唯一约束支持一天多条心情记录；用户应该能自定义头像和昵称，让治愈空间更有归属感（头像同步到树洞，让 AI 对话也有身份感）；首页文案从「海上有座岛，岛上有人听」焕新为「潮声不止，心安自屿」，更贴合「潮声 + 心安 + 岛屿」的治愈意象；'落叶画坊'改名'花坊'更简洁；露水累加修复确保资源发放准确。

**改动清单**（18 项，详见 [README 顶部 v2.4.0 提示块](../../README.md)）：

1. **首页文案焕新**：'海上有座岛，岛上有人听' → '潮声不止，心安自屿'（`潮声不止心安自屿`），删除'静屿'副标题；[HomeView.vue](../../frontend/src/views/HomeView.vue) 文案更新
2. **删除首页'今日打卡'板块**：[HomeView.vue](../../frontend/src/views/HomeView.vue) 移除今日打卡模块
3. **'漂流日记'入口统一**：不管从哪进入，直接显示'日记海岸'界面（含拾瓶 / 写日记模块）
4. **情绪日历 emoji 显示/选择修复**：[MoodCalendarView.vue](../../frontend/src/views/mood/MoodCalendarView.vue) emoji 显示修复
5. **一天多条心情记录**：`mood_checkins` 表 `user_id+check_date` 唯一约束移除（`mood_checkins 唯一约束移除`），支持一天多次打卡（情绪是多变的，`一天多条心情`）；[mood_service.py](../../app/services/mood_service.py) 重构——`upsert_checkin` → `add_checkin`（不再 UPSERT，允许一天多条）+ 新增 `get_today_moods`（获取今日所有心情）
6. **30 天心情趋势评分系统**：1-5 评分（极度开心=5 / 开心=4 / 平静=3 / 疲惫=2 / 焦虑=2 / 生气=1 / 悲伤=1），多条取**平均分**（`MOOD_SCORE` 映射：ecstatic=5 / happy=4 / calm=3 / tired=2 / anxious=2 / angry=1 / sad=1）；`get_recent_trend` 重构支持多条取平均
7. **心语树洞 AI 系统提示词 humanize**：[ai_service.py](../../app/services/ai_service.py) 系统提示词更接地气、像朋友聊天（`humanize`）
8. **'落叶画坊' → '花坊'**（改名）：[HomeView.vue](../../frontend/src/views/HomeView.vue) 模块名更新；[constants.py](../../app/utils/constants.py) / seed 同步
9. **花种种类扩充**：[constants.py](../../app/utils/constants.py) `DEFAULT_SHOP_ITEMS` 花种扩充至 12 种（向日葵 / 竹子 / 雏菊 / 莲花 / 薰衣草 / 郁金香 / 梅花 / 桃花 / 兰花 / 青松 / 桂花 / 银杏）
10. **新装扮**：[constants.py](../../app/utils/constants.py) 新增 6 件装扮（油纸伞 / 蓑衣 / 乌篷船 / 鱼竿 / 橘猫 / 白鹤）
11. **'古琴初学者' → '琴音知音'**（徽章改名）：[constants.py](../../app/utils/constants.py) 徽章名更新
12. **每板块徽章**：6 个板块各对应一个徽章——琴音知音 / 日记达人 / 七日静心 / 拾瓶旅人 / 树洞倾心 / 花田主人（`每板块徽章`）
13. **'竹编帽'介绍改为'种花人遮阳的草帽'**：[constants.py](../../app/utils/constants.py) 描述更新
14. **花田 AI 显示基于实际种花情况**：[GardenView.vue](../../frontend/src/views/garden/GardenView.vue) 没种花不显示 AI 内容
15. **'我的'页面修复**：[ProfileView.vue](../../frontend/src/views/profile/ProfileView.vue) '收到鼓励' / '岛上物件'可点击跳转，删除重复'岛上物件'，新增'静屿使用指南'（详细介绍所有 7 个模块功能：琴音疗心 / 日记海岸 / 情绪日历 / 心语树洞 / 花坊 / 屿上花田 / 我的）
16. **头像/昵称修改**：新增 `User.avatar` 字段（emoji，默认 `🙂`，`String(16)`，与树洞中显示的头像一致）+ `PATCH /api/profile` 端点（更新头像/昵称，昵称查重 409，头像 1-16 字符）+ 前端编辑弹窗（24 个可选 emoji：🙂😊😌🥰😎🤗😇🤔😴🥺😏🌴🌸🍀🌙⭐🐳🦊🐱🦌🐢🦋🌿🍄）；新增 [app/schemas/profile.py](../../app/schemas/profile.py) + `ProfileUpdateIn`（nickname 2-20 字符可选 / avatar 1-16 字符可选）；**头像同步树洞**（[AIChatView.vue](../../frontend/src/views/ai/AIChatView.vue) 使用 `userStore.avatar` 显示头像，与个人主页一致）；[stores/user.js](../../frontend/src/stores/user.js) 新增 `updateProfile` action（调用 `PATCH /api/profile`）
17. **露水累加修复**：写日记和留言鼓励后正确发放露水（`露水累加修复`）
18. **情绪日历多条打卡支持**：[MoodCalendarView.vue](../../frontend/src/views/mood/MoodCalendarView.vue) 支持一天多条心情记录显示

**新增文件**：
- 后端：[app/schemas/profile.py](../../app/schemas/profile.py)（`ProfileUpdateIn`：nickname 2-20 字符可选 / avatar 1-16 字符可选）

**数据库迁移**（`_migrate_legacy_columns()`）：
- `users` 加 `avatar VARCHAR(16) DEFAULT '🙂' NOT NULL`（v2.4 用户头像，`User.avatar: str = "🙂"`，与树洞中显示的头像一致）
- `mood_checkins` 表 `(user_id, check_date)` 唯一约束移除（`mood_checkins 唯一约束移除`，SQLite 重建表方式：CREATE TABLE _new AS SELECT * → DROP old → RENAME _new to old → CREATE INDEX，支持一天多条心情记录）

**Service 重构**（[mood_service.py](../../app/services/mood_service.py)）：
- `upsert_checkin` → `add_checkin`（不再 UPSERT，允许一天多条心情记录）
- 新增 `get_today_moods`（获取今日所有心情）
- `get_recent_trend` 重构：多条取**平均分**（`MOOD_SCORE` 映射：ecstatic=5 / happy=4 / calm=3 / tired=2 / anxious=2 / angry=1 / sad=1）

**常量更新**（[constants.py](../../app/utils/constants.py)）：
- `DEFAULT_SHOP_ITEMS` 扩充至 27 件（12 花种 + 9 装扮 + 6 徽章）
- '古琴初学者' → '琴音知音'（徽章改名）
- '竹编帽'描述改为'种花人遮阳的草帽'
- 新增装扮：油纸伞 / 蓑衣 / 乌篷船 / 鱼竿 / 橘猫 / 白鹤
- 花种扩充至 12 种：向日葵 / 竹子 / 雏菊 / 莲花 / 薰衣草 / 郁金香 / 梅花 / 桃花 / 兰花 / 青松 / 桂花 / 银杏
- 每板块徽章：琴音知音 / 日记达人 / 七日静心 / 拾瓶旅人 / 树洞倾心 / 花田主人

**Router**：
- `PATCH /api/profile`（更新头像/昵称，昵称查重 409，头像 1-16 字符）

**前端**：
- [ProfileView.vue](../../frontend/src/views/profile/ProfileView.vue)：头像/昵称编辑弹窗（24 个可选 emoji）+ 静屿使用指南（7 个模块详细介绍：琴音疗心 / 日记海岸 / 情绪日历 / 心语树洞 / 花坊 / 屿上花田 / 我的）+ '收到鼓励'/'岛上物件'可点击跳转 + 删除重复'岛上物件'
- [AIChatView.vue](../../frontend/src/views/ai/AIChatView.vue)：使用 `userStore.avatar` 显示头像（与个人主页一致，头像同步树洞）
- [HomeView.vue](../../frontend/src/views/HomeView.vue)：文案更新（'潮声不止，心安自屿'）+ 删除今日打卡 + 模块名'花坊'
- [MoodCalendarView.vue](../../frontend/src/views/mood/MoodCalendarView.vue)：emoji 显示修复 + 多条打卡支持
- [GardenView.vue](../../frontend/src/views/garden/GardenView.vue)：AI 显示基于实际种花情况（没种花不显示）
- [stores/user.js](../../frontend/src/stores/user.js)：新增 `updateProfile` action（调用 `PATCH /api/profile`）

**6 份文档同步**（Iron Rule）：README 状态徽章 + 顶部 v2.4.0 提示块 + §3.4/§3.8.1 落叶画坊→花坊 / HANDOFF §0 当前阶段 + 顶部 v2.4.0 提示块 + §4 Phase 9（本节）/ PROJECT_STATE §1/§2 / ARCHITECTURE / DEPLOYMENT / DEVELOPMENT。**6 份文档同步**（README / HANDOFF / PROJECT_STATE / ARCHITECTURE / DEPLOYMENT / DEVELOPMENT）。

### Phase 10 — v2.4.1 情绪日历改用罗素情绪环模型（Russell's Circumplex Model of Affect）四象限图表（2026-08-10 加）

> 设计原则：**「情绪不是一条上升下降的趋势线，而是效价 × 唤醒度的二维分布」** —— 30 天趋势柱状图只能反映「开心程度」随时间的变化，无法回答「我最近是处于高唤醒的焦虑还是低唤醒的平静」这类问题。引入罗素情绪环模型（Russell's Circumplex Model of Affect，1980）让用户从二维视角理解情绪：横轴**效价 Valence**（积极↔消极），纵轴**唤醒度 Arousal**（高唤醒↔低唤醒），四象限分别对应 Q1(积极+高唤醒) / Q2(消极+高唤醒) / Q3(消极+低唤醒) / Q4(积极+低唤醒)。6 种已追踪情绪（ecstatic / happy / calm / tired / anxious / angry / sad）按 valence/arousal 坐标落点 + 真实打卡次数角标；14 种参考情绪（兴奋 / 激动 / 恐慌 / 恐惧 / 极度烦躁 / 低落 / 压抑 / 倦怠 / 空虚 / 闲适 / 舒心 / 恬淡平和 / 兴致高昂 / 狂喜）补全象限位置，帮助用户理解情绪地图。

**改动清单**（7 项，详见 [README 顶部 v2.4.1 提示块](../../README.md)）：

1. **移除 30 天趋势柱状图板块**（`30 天趋势柱状图移除`）：删除 [MoodCalendarView.vue](../../frontend/src/views/mood/MoodCalendarView.vue) 中的 `trendBars` computed（按天数聚合 1-5 评分）+ `scoreColor` 函数（按评分映射颜色）+ `.trend-section` 模板块（30 根柱子）+ `.trend-bar` 样式（柱子渐变色 + 高度动画）
2. **新增罗素情绪环模型四象限图表**（`四象限图表`）：[MoodCalendarView.vue](../../frontend/src/views/mood/MoodCalendarView.vue) 新增 `.circumplex-section` 模板——横轴 **效价 Valence**（左消极 → 右积极）+ 纵轴 **唤醒度 Arousal**（下低唤醒 → 上高唤醒），中央十字坐标轴把区域分为 Q1(积极+高唤醒，右上) / Q2(消极+高唤醒，左上) / Q3(消极+低唤醒，左下) / Q4(积极+低唤醒，右下) 四个象限，每个象限淡色背景（治愈系配色）+ 标签（如「积极 · 高唤醒」）
3. **数据定义 `CIRCUMPLEX_EMOTIONS`**（`20 种情绪`）：在 [MoodCalendarView.vue](../../frontend/src/views/mood/MoodCalendarView.vue) script 中定义数组，每个元素 `{ key, label, emoji, valence, arousal, tracked }`——`valence`/`arousal` 取值范围 -1~+1（-1 极消极/低唤醒，+1 极积极/高唤醒）。其中：
   - **6 种已追踪情绪**（`6 种已追踪`，`tracked: true`）：ecstatic(🤩 valence=+0.9, arousal=+0.8) / happy(😊 +0.7, +0.4) / calm(😌 +0.4, -0.5) / tired(😪 -0.2, -0.8) / anxious(😰 -0.6, +0.7) / angry(😠 -0.8, +0.8) / sad(😢 -0.7, -0.4) —— 映射到后端 [constants.py](../../app/utils/constants.py) `MOOD_INFO` 7 种心情（实际 7 种 tracked，任务描述中称「6 种已追踪」沿用了文档约定，对应 ecstatic/happy/calm/tired/anxious/angry/sad），有真实打卡数据
   - **14 种参考情绪**（`14 种参考`，`tracked: false`）：兴奋 / 激动 / 恐慌 / 恐惧 / 极度烦躁 / 低落 / 压抑 / 倦怠 / 空虚 / 闲适 / 舒心 / 恬淡平和 / 兴致高昂 / 狂喜 —— 各自占据象限内的位置，帮助用户理解情绪在环模型中的相对位置
4. **点击交互**（`点击交互`）：点击 emoji → 弹出详情卡片：
   - **已追踪情绪**：边框高亮（治愈系 accent 色）+ 右上角小圆点角标显示本月打卡次数；卡片内容「本月出现 X 次」（`本月出现次数` 由 `moodCounts[emotion.key]` 提供）
   - **未追踪情绪**（参考情绪）：无角标；卡片内容「该情绪暂未开放打卡记录」
   - `emotionPosition(emotion)` computed/helper：将 `valence`/`arousal` 坐标转为 CSS `left%` / `top%` 百分比定位 —— `left% = (valence + 1) / 2 * 100`（-1 → 0%，+1 → 100%），`top% = (1 - arousal) / 2 * 100`（+1 → 0% 顶部，-1 → 100% 底部，注意翻转）
5. **统计 `moodCounts` + `totalCheckins`**：`moodCounts` computed 从 `checkins`（本月打卡数据）按 `mood_emoji` 统计每种心情出现次数（`{ ecstatic: 3, happy: 5, ... }`）；`totalCheckins` computed 显示本月总打卡数（所有心情次数之和），显示在四象限图表上方
6. **视觉设计**：
   - **治愈系配色**：四象限淡色背景（Q1 浅黄积极 / Q2 浅红警示 / Q3 浅蓝低落 / Q4 浅绿平静）+ emoji 圆形背景 + 边框
   - **GSAP 入场动画**：emoji 逐个弹出（`gsap.from('.emotion-dot', { scale: 0, opacity: 0, stagger: 0.05, ease: 'back.out(1.7)' })`，`back.out` 缓动让 emoji 有弹性出现感）
   - **移动端响应式**：图表 `aspect-ratio: 1` 自适应宽度，emoji 字号随屏幕宽度缩放（`clamp(20px, 4vw, 32px)`）；详情卡片移动端居中底部弹出
7. **保留 `fetchTrend` 调用**：`onMounted` 仍调 `fetchTrend()` 拉取 30 天趋势数据，但 `trend` 数据**不再用于渲染柱状图**——仅用于 `currentStreak`（连续打卡天数）显示在页面顶部连胜卡片。这是**渐进重构**而非「全部删除」，保留向后兼容性

**新增文件**：无（仅修改 [MoodCalendarView.vue](../../frontend/src/views/mood/MoodCalendarView.vue)）

**数据库迁移**：无（不改后端模型 / 不改 API / 不改 service）

**前端**：
- [MoodCalendarView.vue](../../frontend/src/views/mood/MoodCalendarView.vue)：
  - **移除**：`trendBars` computed / `scoreColor` 函数 / `.trend-section` 模板 / `.trend-bar` 样式
  - **新增**：`CIRCUMPLEX_EMOTIONS` 数组（20 种情绪，6+14 分类）/ `emotionPosition(emotion)` helper / `moodCounts` computed / `totalCheckins` computed / `.circumplex-section` 模板（四象限 + emoji 定位）/ 详情卡片交互 / GSAP 入场动画
  - **保留**：`fetchTrend` 调用（为 `currentStreak` 连续打卡天数显示）/ `checkins` 数据加载 / 月历网格 / 今日打卡模块

**6 份文档同步**（Iron Rule）：README 状态徽章 v2.4.0→v2.4.1 + 顶部 v2.4.1 提示块 / HANDOFF §0 当前阶段 v2.4.0→v2.4.1 + 顶部 v2.4.1 提示块 + §4 Phase 10（本节）/ PROJECT_STATE §1（新增 v2.4.1 行）+ §2（新增 2026-08-10 v2.4.1 节）+ 顶部 v2.4.1 提示块 + 「最后更新」v2.4.1 / ARCHITECTURE / DEPLOYMENT / DEVELOPMENT。**6 份文档同步**（README / HANDOFF / PROJECT_STATE / ARCHITECTURE / DEPLOYMENT / DEVELOPMENT）。

### Phase 11 — v2.4.3 花语文案焕新 + emoji 名称对齐 + 徽章奖励落叶 + 树洞三层回复 + 情绪日历空 bug 修复（2026-08-14 加）

> 设计原则：**「文案要有点诗意 / emoji 要对得上名字 / 资源要能跑起来 / AI 要真的有用」** —— 用户反馈一系列内容运营和体验问题：徽章名「花田主人」太直白、「古琴初学者」旧徽章还在残留；情绪日历页面完全空白（bug）；「没花没落叶、没落叶种不了花」死锁；花田 AI 在没种花时显示无关花朵；首页沙滩 emoji 不贴合海意；树洞只会重复消极情绪不做有用共鸣；花种 emoji 和名称对不上（薰衣草配紫色爱心、桂花配麦子、白鹤配火烈鸟、蓑衣配斗篷）；花种介绍太直白（花中皇后）；缺少动物装扮；漂流瓶 emoji 不够正式。本次逐一修复，无新依赖，专注打磨内容质量。

**改动清单**（14 项，详见 [README 顶部 v2.4.3 提示块](../../README.md)）：

1. **删除「古琴初学者」废弃徽章**（`废弃徽章删除`）：v2.4.0 改名「琴音知音」后旧徽章仍在 seed 残留——[app/seed.py](../../app/seed.py) 启动时清理 `DEPRECATED_BADGES = ["古琴初学者"]`，含 GardenItem 引用一并删除
2. **「花田主人」→「花间客」**（`花间客改名`）：徽章命名太直白 → 改为更具诗意感的「花间客」；[constants.py](../../app/utils/constants.py) 徽章名 + seed `RENAME_MAP` 迁移表 + [ProfileView.vue](../../frontend/src/views/profile/ProfileView.vue) 使用指南同步
3. **「花坊」→「落叶花坊」**（`落叶花坊改名`）：板块名更点题——落叶归根换花种；[HomeView.vue](../../frontend/src/views/HomeView.vue) 模块名 + [GardenView.vue](../../frontend/src/views/garden/GardenView.vue) 入口 + ProfileView 使用指南同步
4. **情绪日历空白 Bug 修复**（`情绪日历空白修复`）：[MoodCalendarView.vue](../../frontend/src/views/mood/MoodCalendarView.vue) 月历空单元格 `cell.moodKeys.length` 抛 `TypeError: Cannot read properties of undefined`，整页渲染中断显示空白；修复为 `cell.moodKeys?.length > 0`（含 moodInfos 同步加可选链 `cell.moodInfos?.length`）
5. **落叶死锁解除**（`落叶死锁解除` / `BADGE_LEAF_REWARD`）：原逻辑「没花没落叶 / 没落叶种不了花」形成死锁——[constants.py](../../app/utils/constants.py) 新增 `BADGE_LEAF_REWARD: Final[int] = 10`；[energy_service.py](../../app/services/energy_service.py) `check_achievements()` 每解锁一个徽章额外发放 10 落叶，返回 `{new_badges, new_leaves, leaves_balance}`；mood / diary / music / ai / energy 5 路由透传返回字段；前端 [MoodCalendarView](../../frontend/src/views/mood/MoodCalendarView.vue) / [DiaryWriteView](../../frontend/src/views/diary/DiaryWriteView.vue) / [PickBottleView](../../frontend/src/views/diary/PickBottleView.vue) / [AIChatView](../../frontend/src/views/ai/AIChatView.vue) 接 toast「解锁徽章「X」· 赠 10 落叶」+ 更新 `userStore.leaves` 余额
6. **花田 AI 显示基于实际种花**（`花田 AI 显示修复`）：[GardenView.vue](../../frontend/src/views/garden/GardenView.vue) `<FlowerField v-if="flowers.length > 0" />`，未种花时不渲染 3D 花田（避免空花田显示 AI 生成无关花朵）；保留 v2.4.0 已加的 AI 显示判断
7. **岛上物件 emoji 化**（`岛上物件 emoji`）：[GardenView.vue](../../frontend/src/views/garden/GardenView.vue) 「🏝️ 岛上物件」section 头部加 emoji
8. **首页 emoji 🏝️ → 🌊**（`首页海浪 emoji`）：[HomeView.vue](../../frontend/src/views/HomeView.vue) hero-icon 由沙滩 🏝️ 改为海浪 🌊，更贴合「静屿」海意；[EmojiIcon.vue](../../frontend/src/components/EmojiIcon.vue) twemoji 映射 `🏝️ desert-island` 移除，新增 `🌊 wave`
9. **树洞 AI 重写**（`树洞三层回复`）：[ai_service.py](../../app/services/ai_service.py) `SYSTEM_PROMPT_TREEHOLE` 重写为三层结构——① 接住情绪（1 句，准确点出感受，不复述原话）② 安慰或新视角（1-2 句，温暖肯定 / 温柔宽慰 / 换个角度）③ 具体可操作的小建议或问题（1-2 句，小 / 具体 / 现在就能做），解决旧版「只重复消极情绪、做无用情感共鸣」问题
10. **花种 emoji 与名称对齐 + 花语化**（`花语化` / `emoji 对齐`）：[constants.py](../../app/utils/constants.py) 12 种花种介绍全部改为「花语：XX」格式——向日葵「信念与爱慕」/ 竹子「坚韧虚心」/ 雏菊「天真纯洁」/ 莲花「清白坚贞」/ 薰衣草「等待爱情」/ 郁金香「完美的爱」/ 樱花「生命之美」/ 桃花「爱情降临」/ 青松「坚定长寿」/ 小麦「丰收富足」/ 青叶「生机新生」；emoji 与名称对齐——薰衣草 💜→🪻（紫花浪漫）/ 桂花→小麦 🌾 / 银杏→青叶 🍃 / 兰花+梅花合并为樱花 🌸（删一留一，seed 去重）/ 白鹤→火烈鸟 🦩 / 蓑衣→斗篷 🧥
11. **装扮动物扩充**（`动物扩充`）：[constants.py](../../app/utils/constants.py) 新增 3 件动物装扮——小鸟 🐦 / 小鸭 🦆 / 小狗 🐶
12. **漂流瓶 emoji 🍶 → 🏺**（`漂流瓶 emoji`）：[HomeView.vue](../../frontend/src/views/HomeView.vue) 漂流日记 icon + [DiaryWriteView](../../frontend/src/views/diary/DiaryWriteView.vue) 发布选项 + [EmojiIcon.vue](../../frontend/src/components/EmojiIcon.vue) twemoji 映射 `🍶 sake` 移除，新增 `🏺 amphora`；拾瓶旅人徽章 🏺 与板块入口一致
13. **seed 改名迁移 + 去重**（`改名迁移` / `去重`）：[app/seed.py](../../app/seed.py) 启动时按 `RENAME_MAP` 改名老库物品（桂花→小麦 / 银杏→青叶 / 兰花+梅花→樱花 / 白鹤→火烈鸟 / 蓑衣→斗篷 / 花田主人→花间客）+ 合并同名重复（如兰花+梅花都改名为樱花时保留 id 最小的，GardenItem 引用迁移到 keeper）
14. **版本号 2.4.2 → 2.4.3**（`版本号对齐`）：[app/main.py](../../app/main.py) `version="2.4.3"` + README badge v2.4.3 + 6 份文档同步

**新增文件**：无（仅修改现有文件）

**数据库迁移**：无（不改后端模型结构，仅 seed 启动时改名 / 去重 / 删废弃行）

**常量更新**（[constants.py](../../app/utils/constants.py)）：
- `DEFAULT_SHOP_ITEMS` 27 件（12 花种 + 9 装扮 + 6 徽章，总数不变但内容大改）
- 花种介绍全部改为花语格式
- 花种 emoji 与名称对齐（薰衣草 🪻 / 桂花→小麦 🌾 / 银杏→青叶 🍃 / 兰花+梅花→樱花 🌸）
- 装扮 emoji 与名称对齐（白鹤→火烈鸟 🦩 / 蓑衣→斗篷 🧥）
- 装扮动物扩充：小鸟 🐦 / 小鸭 🦆 / 小狗 🐶
- 徽章名「花田主人」→「花间客」
- 徽章描述加「· 赠 10 落叶」
- 新增 `BADGE_LEAF_REWARD: Final[int] = 10`

**Service 重构**（[energy_service.py](../../app/services/energy_service.py)）：
- `check_achievements()` 返回值由 `list` 改为 `dict`：`{new_badges, new_leaves, leaves_balance}`
- 每解锁一个徽章额外发放 `BADGE_LEAF_REWARD` 落叶（用 `db.query(User).filter(...).update({User.leaves: User.leaves + reward})` + `db.flush()`）
- 取 DB 最新落叶余额返回（`expire_on_commit=False` 场景下 `user.leaves` 可能是旧值）

**Router 透传**（5 个）：
- [mood.py](../../app/routers/mood.py) 心情打卡后 `check_achievements` + 透传 new_badges / new_leaves / leaves_balance
- [diary.py](../../app/routers/diary.py) 写日记 / 拾瓶 / 留言后透传
- [music.py](../../app/routers/music.py) 听完曲子后透传
- [ai.py](../../app/routers/ai.py) 树洞对话后透传
- [energy.py](../../app/routers/energy.py) 兑换物品后透传

**前端**：
- [HomeView.vue](../../frontend/src/views/HomeView.vue)：hero-icon 🏝️→🌊 + 漂流日记 icon 🍶→🏺 + 模块名「花坊」→「落叶花坊」
- [GardenView.vue](../../frontend/src/views/garden/GardenView.vue)：`<FlowerField v-if="flowers.length > 0" />` + 「🏝️ 岛上物件」section emoji
- [MoodCalendarView.vue](../../frontend/src/views/mood/MoodCalendarView.vue)：可选链修复 + 徽章 / 落叶 toast
- [DiaryWriteView.vue](../../frontend/src/views/diary/DiaryWriteView.vue)：🍶→🏺 + 徽章 / 落叶 toast
- [PickBottleView.vue](../../frontend/src/views/diary/PickBottleView.vue)：徽章 / 落叶 toast
- [AIChatView.vue](../../frontend/src/views/ai/AIChatView.vue)：徽章 / 落叶 toast
- [ProfileView.vue](../../frontend/src/views/profile/ProfileView.vue)：「花田主人」→「花间客」+ 「花坊」→「落叶花坊」使用指南同步
- [EmojiIcon.vue](../../frontend/src/components/EmojiIcon.vue)：EMOJI_MAP 🏝️→🌊 / 🍶→🏺

**Smoke test 结果**：`python start.py restart` ✅ / `curl /api/shop/items` 200（27 件，含新动物 + 花语介绍）✅ / 情绪日历页面非空 ✅ / 树洞回复含建议 ✅ / 花田未种花不显示 3D ✅

**6 份文档同步**（Iron Rule）：README 状态徽章 v2.4.2→v2.4.3 + 顶部 v2.4.3 提示块 + §3.8.1 花坊→落叶花坊 / HANDOFF §0 当前阶段 v2.4.2→v2.4.3 + 顶部 v2.4.3 提示块 + §4 Phase 11（本节）/ PROJECT_STATE §1（新增 v2.4.3 行）+ §2（新增 2026-08-14 v2.4.3 节）+ 顶部 v2.4.3 提示块 + 「最后更新」v2.4.3 / ARCHITECTURE / DEPLOYMENT / DEVELOPMENT。**6 份文档同步**（README / HANDOFF / PROJECT_STATE / ARCHITECTURE / DEPLOYMENT / DEVELOPMENT）。

### Phase 12 — v2.4.4 情绪日历透明修复 + 旧版日记迁移 + mood_checkins 主键重建 + 头像图片上传 + 落叶花坊文案打磨（2026-08-15 加）

> 设计原则：**「看得见 / 读得到 / 主键在 / 头像能上图」** —— 用户反馈一系列可见性 / 数据完整性 / 表结构问题：情绪日历心情选择按钮几乎不可见；旧版加密日记 `content` 字段为空；批量打卡 500（`mood_checkins` 表丢失主键）；`User.avatar` 字段太短存不下图片 URL；缺少头像图片上传能力；花坊介绍「花语：」前缀冗余；徽章奖励落叶统一值不够分级；情绪日历使用指南不够专业；岛上物件 emoji 不够贴合；通知 emoji 风格不一致。本次逐一修复 + 新增头像上传功能。

**改动清单**（10 项，详见 [README 顶部 v2.4.4 提示块](../../README.md)）：

1. **[BUG FIX] 情绪日历 emoji 透明**（`情绪日历透明修复`）：[MoodCalendarView.vue](../../frontend/src/views/mood/MoodCalendarView.vue) GSAP 动画设置了 `opacity:0` 导致心情选择按钮几乎不可见，已移除该属性
2. **[BUG FIX] 旧版日记无内容**（`旧版日记迁移`）：旧版加密日记 `content` 字段为空（`content_encrypted` 是假占位符），数据库迁移自动填入提示文本「（这段日记来自旧版本，内容已无法读取）」
3. **[BUG FIX] mood_checkins 表缺失 PRIMARY KEY**（`mood_checkins 主键重建`）：v2.4 的迁移用了 `CREATE TABLE AS SELECT` 导致 `mood_checkins` 表丢失主键和自增，批量打卡时 `db.flush()` 报 `NULL identity key` 错误（500）。已重建表（`id INTEGER PRIMARY KEY AUTOINCREMENT` + FK + 索引），数据完整迁移
4. **[BUG FIX] avatar 字段长度**（`avatar 字段长度`）：[User.avatar](../../app/models/user.py) 原为 `String(16)`，无法存储图片上传后的 URL 路径（如 `/static/uploads/avatars/1_1234567890.jpg`）。已改为 `String(255)`，[ProfileUpdateIn](../../app/schemas/profile.py) schema 同步调整为 `max_length=255`
5. **[FEATURE] 头像支持图片上传**（`头像图片上传`）：新增 `POST /api/profile/avatar` 端点，支持 JPG/PNG/WebP/GIF（≤2MB），存储到 `static/uploads/avatars/`（目录不存在自动创建）；[ProfileView.vue](../../frontend/src/views/profile/ProfileView.vue) 增加上传按钮（支持拍摄/相册选择），[AIChatView.vue](../../frontend/src/views/ai/AIChatView.vue) 支持图片头像渲染
6. **[IMPROVEMENT] 落叶花坊花朵介绍**（`花朵介绍`）：移除「花语：」前缀，只保留完整花语
7. **[IMPROVEMENT] 徽章落叶奖励分级**（`徽章落叶分级`）：按徽章 trigger 分级设置落叶奖励（streak_7=7, listen_10=10, pick_10=10, flower_10=10, chat_20=15, diary_30=20, 默认=10），替代原来统一的固定值
8. **[IMPROVEMENT] 情绪日历使用指南更新**（`情绪日历指南`）：介绍改为罗素情绪环模型（Russell's Circumplex Model）四象限说明
9. **[IMPROVEMENT] 岛上物件 emoji**（`岛上物件 emoji`）：🎁 → 🧳（行李箱）
10. **[IMPROVEMENT] 通知 emoji 统一**（`通知 emoji 统一`）：漂流瓶回复通知的 emoji 统一为 💛（黄色爱心）

**新增文件**：`static/uploads/avatars/` 目录（上传端点自动创建）+ `POST /api/profile/avatar` 路由

**数据库迁移**：
- `mood_checkins` 表重建（`id INTEGER PRIMARY KEY AUTOINCREMENT` + FK + 索引，数据完整迁移）
- `User.avatar` 字段长度 `String(16)` → `String(255)`（`_migrate_legacy_columns()` 自动 ALTER）
- 旧版加密日记 `content` 字段为空时自动填入提示文本

**Smoke test 结果**：`python start.py restart` ✅ / 情绪日历心情按钮可见 ✅ / 旧版日记显示提示文本 ✅ / 批量打卡不再 500 ✅ / 头像上传 200 ✅

**6 份文档同步**（Iron Rule）：README 状态徽章 v2.4.3→v2.4.4 + 顶部 v2.4.4 提示块 / HANDOFF §0 当前阶段 v2.4.3→v2.4.4 + 顶部 v2.4.4 提示块 + §4 Phase 12（本节）/ PROJECT_STATE §1（新增 v2.4.4 行）+ §2（新增 2026-08-15 v2.4.4 节）+ 顶部 v2.4.4 提示块 + 「最后更新」v2.4.4 / ARCHITECTURE / DEPLOYMENT / DEVELOPMENT。**6 份文档同步**（README / HANDOFF / PROJECT_STATE / ARCHITECTURE / DEPLOYMENT / DEVELOPMENT）。

### Phase 13 — v2.4.5 情绪日历 30 天趋势柱状图恢复 + 罗素情绪环显示修复 + 头像相册选择 + 通知空状态 emoji 统一（2026-08-16 加）

> 设计原则：**「柱状图回归 · 环模型常显 · 相册能选 · 空态对齐」** —— 用户反馈 4 个问题：① 情绪日历打卡后下方不显示柱状图（v2.4.1 把柱状图换成了罗素情绪环，但用户习惯看柱状趋势）；② 罗素情绪环模型不显示（GSAP 动画初始态残留）；③ 头像只能拍照不能从相册选择（`capture` 属性强制调起相机）；④ 「我的」>「通知」空状态显示黄色月亮 🌙 而非黄色爱心 💛。本次逐一修复，纯前端 3 文件改动，无后端 / 无迁移 / 无新依赖。

**改动清单**（4 项，详见 [README 顶部 v2.4.5 提示块](../../README.md)）：

1. **[BUG FIX] 情绪日历打卡后柱状图不显示**（`30天趋势柱状图恢复`）：[MoodCalendarView.vue](../../frontend/src/views/mood/MoodCalendarView.vue) 恢复「近 30 天心情趋势」柱状图板块（`.trend-section` 模板 + 样式 + `trend` computed 数据流），与罗素情绪环四象限图表**并存**——柱高 = 当日心情平均分（1-5 评分，一天多条取平均），柱色取当日主心情颜色渐变（`linear-gradient`），柱顶悬浮当日主心情 emoji，悬浮 title 显示「日期 ·心情名 ×N」（一天多条），未记录日显示 3px 浅色占位柱，底部首尾日期轴（起始日 → 今天）
2. **[BUG FIX] 罗素情绪环模型不显示**（`罗素情绪环显示修复`）：GSAP `from()` 动画残留 `opacity:0` / `scale:0` 初始态，动画被中断（切后台 / 路由切换）时元素**永久卡在不可见状态**（与 v2.4.4「透明 bug」同类根因——v2.4.4 只修了心情选择按钮那一处，环模型区域的动画初始态漏修）。修复：入场动画（`.mood-header` / `.mood-picker__btn` / `.calendar-nav` / `.calendar-cell` / `.circumplex-section` / `.circumplex-emotion`）**只保留位移动画（`y`），不设置 `opacity` / `scale` 初始态**
3. **[BUG FIX] 头像只能拍照不能从相册选择**（`头像相册选择`）：[ProfileView.vue](../../frontend/src/views/profile/ProfileView.vue) 头像上传 `<input type="file">` 带 `capture="environment"` 属性，移动端浏览器会**强制调起相机**跳过相册。移除 `capture` 属性后（保留 `accept="image/*"`），点击弹出系统「拍照 / 从相册选择」选择框；按钮文案同步为「📷 拍照 / 从相册选择」
4. **[BUG FIX] 通知空状态 emoji 错误**（`通知空状态emoji`）：[NotificationsView.vue](../../frontend/src/views/notification/NotificationsView.vue) 空状态 emoji 🌙 → 💛，与 v2.4.4「通知 emoji 统一 💛」决策对齐（v2.4.4 只统一了通知列表项，空状态漏改）

**改动文件**：仅 3 个前端文件——`frontend/src/views/mood/MoodCalendarView.vue` / `frontend/src/views/profile/ProfileView.vue` / `frontend/src/views/notification/NotificationsView.vue` + [app/main.py](../../app/main.py) 版本号 2.4.4 → 2.4.5（`版本号对齐`）

**无数据库迁移 / 无新依赖 / 无后端逻辑改动**

**Smoke test 结果**（2026-08-16 实测，dist 重构建后浏览器端到端验证）：打卡后 30 天趋势柱状图显示 ✅ / 罗素情绪环四象限正常渲染 ✅ / 头像上传弹「拍照 / 从相册选择」选择框 ✅ / 通知空状态显示 💛 ✅

**6 份文档同步**（Iron Rule）：README 状态徽章 v2.4.4→v2.4.5 + 顶部 v2.4.5 提示块 / HANDOFF §0 当前阶段 v2.4.4→v2.4.5 + 顶部 v2.4.5 提示块 + §4 Phase 13（本节）/ PROJECT_STATE §1（新增 v2.4.5 行）+ §2（新增 2026-08-16 v2.4.5 节）+ 顶部 v2.4.5 提示块 + 「最后更新」v2.4.5 / ARCHITECTURE / DEPLOYMENT / DEVELOPMENT。**6 份文档同步**（README / HANDOFF / PROJECT_STATE / ARCHITECTURE / DEPLOYMENT / DEVELOPMENT）。

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

### 5.7 为什么 AI 接入用 NVIDIA NIM API + 渐进增强降级（2026-07-17 加）
- **选 NVIDIA NIM**：[build.nvidia.com](https://build.nvidia.com) 提供**免费** API key，OpenAI 兼容格式接入成本几乎为零，符合本项目「非商业纯治愈」调性
- **模型默认 `meta/llama-3.1-8b-instruct`**（2026-07-17 会话 8 后续修复）：原默认 `nvidia/llama-3.1-nemotron-70b-instruct`（Llama 3.1 系列 NVIDIA 微调的 70B 指令模型）在用户 NVIDIA 账户下 API 返回 404（"Function not found for account"），实际查询账户有 119 个可用模型但不含该 70B 模型；改用 8B 小模型兼顾速度与质量：首次 5-10s、后续 1-3s。`_call_nvidia` 超时也相应从 30s 调到 60s 保留余量（8B 实际很快但兜底）
- **OpenAI 兼容**：将来想换其他厂商（DeepSeek / 智谱 / 自部署 vLLM）只改 `QI_AI_BASE_URL` + `QI_AI_MODEL`，不动业务代码
- **降级而非报错**：AI 是「锦上添花」不是核心功能，**未配置 key 或调用失败时返回 200 + `available:false` + 治愈系友好提示**（**不报 500**）。前端拿到 `available:false` 仍正常显示文案。这保证：① 没拿到 key 的部署方也能跑；② NVIDIA 限流时业务不中断；③ 用户感知不到「故障」，只感知「AI 在休息」
- **对话历史不入库**：AI 树洞对话历史只存浏览器内存（刷新清空），符合「日记端到端加密」的隐私承诺——服务端不留对话痕迹
- **日记预览只取前 120 字**：漂流瓶 AI 鼓励语调用时，把作者日记**截断到前 120 字**再发给 AI，避免长文本消耗 token + 减少隐私暴露面
- **温柔语气系统提示词**：4 个场景的 system_prompt 统一约定「不诊断不开药、危机情况引导求助专业资源、温柔倾听」，与项目治愈系调性一致

详见 [app/services/ai_service.py](file:///c:/Users/Administrator/Desktop/webwrold/app/services/ai_service.py) 顶部的 4 个系统提示词常量。

### 5.8 为什么前端选 Vue 3 + Vite + Pinia + Tailwind + GSAP（2026-07-19 加）
- **为什么换掉「原生 HTML/CSS/JS + Jinja2 SSR」**：项目迭代到 4 Phase + 后台 + AI 后，前端逻辑膨胀（13 个页面 × 一页一个 JS），状态管理散落在各 `static/js/pages/*.js`，路由靠后端 302 + 浏览器刷新，新增页面要改 4 处（HTML + JS + pages.py + 速查表）。Vue 3 SPA 一次解决：组件化复用、Pinia 集中状态、Vue Router 客户端路由、Vite HMR 热更新
- **为什么选 Vue 3 而不是 React**：① Vue 3 `<script setup>` 语法对单人项目最简洁；② Tailwind + Vue 单文件组件天然契合治愈系「样式与模板同视图」的写法；③ Pinia 是 Vue 官方推荐 store，比 Redux 心智负担低；④ 国内 Vue 生态成熟，文档中文友好
- **为什么选 Vite 5**：① dev server 启动 < 1s（vs webpack 10s+）；② HMR 真正热更新（改 .vue 即刻生效，不刷新页面）；③ build 用 Rollup，产物体积小；④ 配置极简（`vite.config.js` 不到 30 行）
- **为什么选 Pinia 而不是 Vuex**：Pinia 是 Vue 3 官方推荐，TypeScript 友好，API 更简洁（无 mutations），tree-shaking 友好
- **为什么选 Tailwind CSS**：① 治愈系配色用 `tailwind.config.js` token 化（mist/ink/五音色/accent），改色改一处全局生效；② 不用写自定义 CSS 类，组件样式内联在 `<template>` 里，与 Vue SFC 同视图；③ purge 后 CSS 体积 < 20KB
- **为什么选 GSAP**：① Netflix/Spotify 级动效（stagger / scrub / timeline）原生 CSS 做不到；② Vue 3 `<script setup>` 里 `gsap.from()` 配合 `onMounted` 自然；③ 自动检测 `prefers-reduced-motion` 降级；④ `@vueuse/motion` 补充轻量入场动效
- **为什么保留 Jinja2 后台 SSR**：① 后台是「管理工具」不需要 SPA 体验；② 后台样式完全独立（`07-admin.css` 暗色侧栏），与前台治愈系调性冲突；③ Vue 3 重构范围聚焦前台用户体验，后台保留 SSR 减少改动面
- **cookie session 不变**：Vue 3 重构只动前端，后端鉴权机制（cookie session + nickname 登录 + 直接返回 user 对象）保持不变，前端 userStore 只缓存 user 对象到 localStorage，**不存 token**——这是与「JWT + localStorage」模式的关键差异，避免 XSS 拿 token 的风险
- **SPA fallback 而非双服务器**：生产模式只跑 FastAPI :5000，Vue 构建产物放 `static/dist/`，FastAPI 兜底返回 `index.html`。不引入 Nginx 双服务器或 Node.js 生产环境，保持「单进程三角色（API + 静态 + SPA fallback）」简化

详见 [frontend/](file:///c:/Users/Administrator/Desktop/webwrold/frontend/) + [docs/ARCHITECTURE.md](file:///c:/Users/Administrator/Desktop/webwrold/docs/ARCHITECTURE.md)「前端架构」节。

### 5.9 为什么开发模式让 Vite 占 :5000，FastAPI 改 :5001（2026-07-19 加）
- **背景**：v2.0 Vue 3 重构初版用「FastAPI :5000 + Vite :5173 + FastAPI 反代 Vite」方案，但实际跑起来浏览器报 `SyntaxError: Unexpected token '.'`，定位到是 Vite 内部路径 `/@id/__x00__plugin-vue:export-helper` 含 null 字符转义（`__x00__`）+ 冒号（`plugin-vue:export-helper`），httpx 转发时这些特殊字符被破坏，返回的 JS 文件首行变成 `<` 开头的 HTML 错误页，浏览器当 JS 解析就报错。详见 [§6.16](#616-fastapi-代理转发-vite-内部路径含特殊字符失败2026-07-19-加) 踩坑
- **决策**：开发模式让 **Vite 直接占 :5000**（用户访问入口），**FastAPI 改听 :5001**（API 后端，由 [start.py](file:///c:/Users/Administrator/Desktop/webwrold/start.py) 设置 `QI_PORT=5001`），Vite proxy 把 `/api`、`/static`、`/admin`、`/docs`、`/openapi.json` 转发到 :5001
- **为什么不让 Vite 仍占 :5173 + FastAPI :5000**：① 用户要记两个端口（:5173 看前端 / :5000 看 API），心智负担大；② Vite proxy 转发到 FastAPI 的方向是稳定的（FastAPI 是普通 HTTP JSON，无特殊字符），但反过来 FastAPI 转发到 Vite 就会踩坑
- **生产模式不变**：dist 已构建时 FastAPI 监听 :5000（从 `.env` 读 `QI_PORT`），Vite 不运行，FastAPI 提供 SPA fallback + API + 静态资源
- **用户体验**：用户始终访问 `http://127.0.0.1:5000`，无需关心是应用还是生产模式，[start.py](file:///c:/Users/Administrator/Desktop/webwrold/start.py) 自动切换
- **start.py 改动**：① `start` 子命令自动检测 dist，未构建时设置 `QI_PORT=5001` 启动 FastAPI + 启动 Vite :5000；② `stop` 同时停 FastAPI 和 Vite；③ `status` 显示两个进程状态 + 端口；④ 新增 `build` 子命令一键构建前端到 `static/dist/`（自动 `npm install` + `npm run build`）；⑤ `fg` 子命令只前台运行 FastAPI（生产模式用，不自动起 Vite）
- **2026-07-25 v2.2.2 行为变更**：默认走应用/开发模式（Vite :5000 + FastAPI :5001，自动 `npm install` 当 `frontend/node_modules` 不存在），不再因 dist 已构建就走生产模式。生产模式需显式 `python start.py --prod`（需 dist 已构建）。详见末次更新行 v2.2.2 段。
- **vite.config.js 改动**：① dev server port 5173 → 5000；② proxy target :5000 → :5001；③ 移除 `hmr.clientPort`（Vite 直接占 :5000 后 HMR 走本地不需要）；④ 新增 `/docs` 和 `/openapi.json` 代理
- **main.py 改动**：① SPA fallback 移除回退代理到 Vite 的逻辑（开发态不再转发，返回提示页引导用户访问 Vite :5000）；② 新增 `EXT_TO_MIME` 映射（`.js` / `.css` / `.woff2` 等正确设置 `Content-Type`），生产态从 dist 读取静态资源时不再被 Starlette 默认当成 `application/octet-stream` 让浏览器拒绝执行

详见 [start.py](file:///c:/Users/Administrator/Desktop/webwrold/start.py) + [frontend/vite.config.js](file:///c:/Users/Administrator/Desktop/webwrold/frontend/vite.config.js) + [app/main.py](file:///c:/Users/Administrator/Desktop/webwrold/app/main.py)。

### 5.10 为什么视觉增强走「三层渐进增强 + 能力检测 + 异步加载」策略（2026-07-20 加）
- **背景**：v2.0.1 完成 FlowerField.vue 3D 花田后，用户要求进一步提升整体视觉美感，加入 3D / 伪 3D 背景元素和动态视觉效果，但**不能**影响页面加载性能或用户体验，且**必须**为 3D 渲染能力有限的浏览器实现备用机制
- **决策**：用「CSS 永远启用 → Canvas2D 中量级 → Three.js 按需」三层渐进增强策略，每层独立可降级，配合 [utils/visual.js](file:///c:/Users/Administrator/Desktop/webwrold/frontend/src/utils/visual.js) 能力检测
- **三层分级**：
  - **Layer 1 — CSS（永远启用）**：AmbientBackground 的 3 个 radial-gradient 雾气光斑 + 24s `mistDrift` 动画；AudioVisualizer 降级时的 5 色横条 CSS 动画；HomeView 五音卡片的 `perspective + rotateX/Y + translateZ` 3D 倾斜。零 JS 开销
  - **Layer 2 — Canvas2D（reduced-motion 关闭）**：AmbientBackground 飘浮光点（移动端 24 / 桌面 60）；AudioVisualizer 5 条流动曲线。轻量 CPU 渲染
  - **Layer 3 — Three.js（WebGL + 非 reduced-motion + 非低性能）**：FlowerField 花田（已有）；AmbientBackground 远景粒子层（80 个 sprite）；HeroScene 浮岛雾海（128×128 海面 + 3 浮岛 + 雾 + 80 光点）。GPU 渲染
- **能力检测**：[utils/visual.js](file:///c:/Users/Administrator/Desktop/webwrold/frontend/src/utils/visual.js) 单次缓存 `hasWebGL()` / `prefersReducedMotion()` / `isMobile()` / `isLowPower()` 结果；`shouldUseThreeJS()` = `hasWebGL && !prefersReducedMotion && !isLowPower`；`shouldUseCanvas()` = `!prefersReducedMotion`
- **降级路径**：
  - HeroScene 不支持 WebGL / reduced-motion / initScene 异常 → 渲染 SVG 静态插画（800×480 viewBox，天空渐变 + 太阳光晕 + 3 个岛 + 3 层波浪 + 5 漂浮点）
  - AudioVisualizer 无 Web Audio API / reduced-motion → 5 色静态横条 CSS 动画（`barBreath` 3.6s）
  - AmbientBackground 无 WebGL / 低性能 → 只显示 CSS 雾气光斑 + Canvas2D 光点（无 Three.js 粒子层）
- **性能保护**：
  - 所有 Three.js 组件用 `defineAsyncComponent(() => import(...))` 异步加载，**不进首屏包**（vite.config.js `manualChunks` 把 `three` 单独打成 `three-vendor` chunk，gzip 后 175KB，仅访问 `/`（HeroScene）或 `/garden`（FlowerField）时按需拉取）
  - Three.js 对象用 `shallowRef` 持有，避免 Vue 深度代理拖累性能
  - `smartRAF(callback)` 在 `document.hidden` 时暂停 rAF、可见时自动恢复，避免标签页隐藏时浪费 GPU
  - 移动端降粒子数（Three.js 80→40，Canvas2D 60→24）、降分辨率（HeroScene 海面 128×128 → 64×64）、降帧率（AudioVisualizer 30fps → 24fps）、降几何精度（v2.2.3 加：HeroScene Lathe/Cylinder 段数 24→16、樱花树递归深度 4→3、花团 Icosahedron detail 2→1；FlowerField 花瓣网格 5×8→4×6、花蕊 Icosahedron detail 2→1、地面圆 64→32、茎圆柱段 6→5；AudioVisualizer 镜像柱 48→32、径向柱 64→32）
  - 所有 Three.js 组件 `onBeforeUnmount` 释放 geometry / material / renderer / 事件监听 / ResizeObserver，避免切走后 WebGL 上下文泄漏
- **Web Audio API 一次性约束**：`createMediaElementSource(audioEl)` 对同一 `<audio>` 元素**只能调用一次**，AudioVisualizer 用 `if (!sourceNode)` 守卫；MusicDetailView 用 `visualizerConnected` ref 标记是否已连接，首次 `playIndex` 时调 `visualizerRef.value.connect(audioEl)`，后续切歌不重连
- **配色一致性**：4 个视觉组件全部用治愈系 5 色（藕粉 `#E8B8C5` / 淡黄 `#E8D5A8` / 青绿 `#A8C5A0` / 雾蓝 `#A8B8C5` / 纯白 `#FAF6F2`）+ 米白 `#F9F6F0` 背景，与 [tailwind.config.js](file:///c:/Users/Administrator/Desktop/webwrold/frontend/tailwind.config.js) token 一致；AudioVisualizer 5 条曲线对应宫商角徵羽 5 音色
- **为什么不用全屏 shader / 后处理**：① 治愈系调性要「柔和不刺眼」，shader bloom / DOF 过度装饰反而破坏氛围；② 后处理增加 GPU 开销，移动端掉帧；③ 现有 Fog + InstancedMesh + Canvas2D 已足够，性能与视觉平衡

详见 [frontend/src/components/AmbientBackground.vue](file:///c:/Users/Administrator/Desktop/webwrold/frontend/src/components/AmbientBackground.vue) + [HeroScene.vue](file:///c:/Users/Administrator/Desktop/webwrold/frontend/src/components/HeroScene.vue) + [AudioVisualizer.vue](file:///c:/Users/Administrator/Desktop/webwrold/frontend/src/components/AudioVisualizer.vue) + [utils/visual.js](file:///c:/Users/Administrator/Desktop/webwrold/frontend/src/utils/visual.js)。

### 5.11 为什么 v2.2 走「PBR 渲染管线 + 共享工具集 + 交互指引组件」策略（2026-07-20 加）

- **背景**：v2.1 视觉增强上线后用户反馈两个核心问题：① **交互体验缺失**——用户不知道 3D 场景可以拖拽 / 缩放 / 点击，以为是静态背景；② **视觉粗糙过时**——`PointsMaterial` 方形粒子 + `MeshBasicMaterial` 平面着色 + 无环境映射，整体观感类似 80/90 年代红白机低品质视觉，缺乏现代感与高级感
- **决策**：① 4 个视觉组件全部升级到 PBR（Physically Based Rendering）渲染管线；② 抽出 [utils/three-helpers.js](file:///c:/Users/Administrator/Desktop/webwrold/frontend/src/utils/three-helpers.js) 集中 9 个共享 PBR 工具函数，避免每个组件重复造轮子；③ 新增 [SceneHint.vue](file:///c:/Users/Administrator/Desktop/webwrold/frontend/src/components/SceneHint.vue) 交互指引横幅 + [SceneControls.vue](file:///c:/Users/Administrator/Desktop/webwrold/frontend/src/components/SceneControls.vue) 视图控制工具栏，让用户**第一眼就知道怎么交互**
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
- **共享工具集**（[utils/three-helpers.js](file:///c:/Users/Administrator/Desktop/webwrold/frontend/src/utils/three-helpers.js)，9 个函数）：
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

详见 [utils/three-helpers.js](file:///c:/Users/Administrator/Desktop/webwrold/frontend/src/utils/three-helpers.js) + [SceneHint.vue](file:///c:/Users/Administrator/Desktop/webwrold/frontend/src/components/SceneHint.vue) + [SceneControls.vue](file:///c:/Users/Administrator/Desktop/webwrold/frontend/src/components/SceneControls.vue) + 4 个 v2 视觉组件。

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

### 6.12 Vite 默认监听 IPv6 `[::1]` 导致 127.0.0.1 连不上（2026-07-19 加）
**症状**：`npm run dev` 启动后，浏览器访问 `http://127.0.0.1:5173/` 报 `ERR_CONNECTION_REFUSED`，但 `http://localhost:5173/` 能访问。

**根因**：Vite 5 默认 `host: 'localhost'`，Node.js 把 `localhost` 解析为 IPv6 `[::1]` 而非 IPv4 `127.0.0.1`。Windows / 部分浏览器访问 `127.0.0.1` 时只查 IPv4，连不上 IPv6 监听端口。

**修复**：[frontend/vite.config.js](file:///c:/Users/Administrator/Desktop/webwrold/frontend/vite.config.js) 显式设 `server.host: '127.0.0.1'`：
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

**根因**：[frontend/vite.config.js](file:///c:/Users/Administrator/Desktop/webwrold/frontend/vite.config.js) 为了让 build 产物在 `/static/dist/` 子路径下正确加载，设了 `base: '/static/dist/'`。但 Vite **dev 模式也读 `base`**，导致 dev 模式下 index.html 引用 `/static/dist/src/main.js`，而 Vite dev server 实际服务在 `/src/main.js`，404 后 fallback 返回 index.html，浏览器把 HTML 当 JS 解析报错。

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

**根因**：[frontend/package.json](file:///c:/Users/Administrator/Desktop/webwrold/frontend/package.json) 依赖里 `three ^0.168`（约 30MB，含大量 .js 文件）+ `gsap ^3.12` + `@vueuse/motion ^2.2`，首次安装时 npm 要下载 + 解压 + 写入 node_modules，磁盘 IO 是瓶颈。

**修复**：① 用 `npm install --no-audit --no-fund` 跳过审计 + 资助检查，省 30s；② 用 `npm install --prefer-offline` 优先用本地缓存；③ 接受首次 5-7 分钟的耗时，后续 `npm install` 增量更新只需 10s。

**铁律**：首次安装大依赖（three / gsap / @vueuse/motion）耗时正常，**不要**中途 Ctrl+C，跑完一次后续就快了。CI/CD 里建议 `npm ci`（用 lockfile，更快更稳定）。

### 6.15 FastAPI SPA fallback 必须排除 /api/、/static/、/admin、/docs 路径（2026-07-19 加）
**症状**：Vue 3 重构后，浏览器访问 `/api/music` 返回 `index.html`（HTML），前端 axios 拿到 HTML 解析 JSON 报错；访问 `/admin` 返回 Vue SPA 而非后台 SSR 页面。

**根因**：[app/main.py](file:///c:/Users/Administrator/Desktop/webwrold/app/main.py) 的 SPA fallback 用通配路由 `@app.get("/{path:path}")` 兜底所有 GET 请求，但**没有排除**已注册的路径。FastAPI 路由匹配是「先注册先匹配」，但通配路由如果顺序不对会拦截掉其他路由。

**修复**：在 [app/main.py](file:///c:/Users/Administrator/Desktop/webwrold/app/main.py) 末尾注册 SPA fallback 时显式排除 4 类路径：
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
- [start.py](file:///c:/Users/Administrator/Desktop/webwrold/start.py) 应用模式（默认，v2.2.2 起）自动设置 `QI_PORT=5001` 启动 FastAPI + 启动 Vite :5000；自动检测 `frontend/node_modules` 不存在则 `npm install`
- [frontend/vite.config.js](file:///c:/Users/Administrator/Desktop/webwrold/frontend/vite.config.js) dev server port 5173 → 5000，proxy target :5000 → :5001，移除 `hmr.clientPort`（HMR 走本地），新增 `/docs` 和 `/openapi.json` 代理
- [app/main.py](file:///c:/Users/Administrator/Desktop/webwrold/app/main.py) SPA fallback 移除回退代理到 Vite 的逻辑，开发态（dist 未构建）返回提示页引导用户访问 Vite :5000

**铁律**：永远**不要**让后端 HTTP 框架（FastAPI / Flask / Express）反向代理 Vite dev server 的内部模块路径。要么让 Vite 直接占用户访问端口，要么用 Nginx 这种能透传任意字符的反向代理（生产环境也不需要 Vite，所以只影响开发模式）。详见 [§5.9](#59-为什么开发模式让-vite-占5000-fastapi-改50012026-07-19-加) 决策。

### 6.17 `Depends(None)` 导致 `/openapi.json` 500（2026-07-20 加）
**症状**：访问 `http://127.0.0.1:5000/openapi.json` 返回 500，`/docs` Swagger UI 页面能加载但 API 列表空白。FastAPI 日志报 `pydantic.errors.PydanticUserError: TypeAdapter[typing.Annotated[ForwardRef('Optional[_SessionBind]'), Query(None)]]` is not fully defined。

**根因**：[app/routers/admin.py](file:///c:/Users/Administrator/Desktop/webwrold/app/routers/admin.py) 的 `tail_logs` 路由签名写错：
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

**根因**：[app/database.py](file:///c:/Users/Administrator/Desktop/webwrold/app/database.py) `SessionLocal` 配置了 `expire_on_commit=False`（line 32）：
```python
SessionLocal = sessionmaker(
    bind=engine, autocommit=False, autoflush=False, future=True,
    expire_on_commit=False,  # ← commit 后不 expire 内存对象
)
```
- [app/services/energy_service.py](file:///c:/Users/Administrator/Desktop/webwrold/app/services/energy_service.py) 的 `grant_energy` 用 `db.query(User).filter(...).update({...})` 在 DB 层 UPDATE（符合 §6.7 铁律），但这个 UPDATE **不会同步到 session 里已加载的 `user` 对象的 `total_energy` 属性**（SQLAlchemy 的 `query.update()` 默认 `synchronize_session='auto'`，但在 `autoflush=False` + 对象已加载的边界 case 下同步可能失效）
- `db.commit()` 后，因为 `expire_on_commit=False`，`user.total_energy` 仍是旧的内存值（0），不会触发重新查询
- 路由层 `return {"new_total_energy": user.total_energy}` 返回旧值

**修复**：所有"commit 后需要返回最新 total_energy"的路由，**必须用 `db.query(User.total_energy).filter(User.id == user.id).scalar()` 重新查 DB**，不能依赖 `user.total_energy` 内存值。已修复 3 处：
- [app/routers/music.py](file:///c:/Users/Administrator/Desktop/webwrold/app/routers/music.py) `listen_complete`
- [app/routers/energy.py](file:///c:/Users/Administrator/Desktop/webwrold/app/routers/energy.py) `exchange`
- [app/routers/diary.py](file:///c:/Users/Administrator/Desktop/webwrold/app/routers/diary.py) `create_diary` 路由

**铁律**：`expire_on_commit=False` 下，**commit 后读 ORM 对象属性 = 读旧值**。凡是"修改了某字段 → commit → 返回该字段新值"的场景，必须用 `db.query(Model.field).filter(...).scalar()` 或 `db.refresh(obj)` 重新获取。不要相信内存对象。

### 6.19 同歌 24h 重复发放能量（代码缺失，2026-07-20 加）
**症状**：用户听完一首歌（进度 ≥ 90%）调 `/api/music/listen-complete` 得到 +1 露水；24h 内重复调同一首，**又**得到 +1 露水。docstring 明确写"同一首歌 24h 内重复调用不重复发放"，但**代码完全没实现去重逻辑**。

**根因**：[app/routers/music.py](file:///c:/Users/Administrator/Desktop/webwrold/app/routers/music.py) `listen_complete` 只检查进度和单日上限，**没有任何"同一首歌 24h 内是否已发放过"的查询**。EnergyRecord 表里也没存 `music_id`，无法做这个去重。

**修复**：
1. [app/models/energy.py](file:///c:/Users/Administrator/Desktop/webwrold/app/models/energy.py) `EnergyRecord` 加 `music_id: Mapped[int | None]`（可空，仅 listen_music 来源有值）+ 复合索引 `ix_energy_user_music_date (user_id, music_id, created_at)`
2. [app/database.py](file:///c:/Users/Administrator/Desktop/webwrold/app/database.py) `_migrate_legacy_columns()` 加 `ALTER TABLE energy_records ADD COLUMN music_id INTEGER`（轻量迁移，符合 §6.10）
3. [app/services/energy_service.py](file:///c:/Users/Administrator/Desktop/webwrold/app/services/energy_service.py) `grant_energy` 加 `music_id: Optional[int] = None` 参数，写入 `EnergyRecord.music_id`
4. [app/routers/music.py](file:///c:/Users/Administrator/Desktop/webwrold/app/routers/music.py) `listen_complete` 在 `grant_energy` 调用**前**查 24h 内同 user_id + music_id + source=listen_music 的记录，存在则直接 `return {"granted": False, "reason": "这首 24 小时内已经听过了"}`；并把 `body.music_id` 传给 `grant_energy`

**铁律**：docstring 写的规则 ≠ 代码实现的规则。**每条写在文档里的业务规则，必须有对应的查询/分支代码实现**。规则要查 DB 去重时，**必须**有索引覆盖（避免全表扫描），并优先用复合索引（`user_id + 业务键 + created_at`）。

### 6.20 `exchange_item` 已持有检查位置错误导致重复兑换 500（2026-07-20 加）
**症状**：用户兑换一个 `cost=0` 的徽章（如"古琴初学者"），第二次兑换同一徽章返回 **HTTP 500**，错误：`sqlalchemy.exc.IntegrityError: UNIQUE constraint failed: garden_items.user_id, garden_items.item_id`。

**根因**：[app/services/energy_service.py](file:///c:/Users/Administrator/Desktop/webwrold/app/services/energy_service.py) `exchange_item` 原代码：
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

**根因**：[frontend/src/components/FlowerField.vue](file:///c:/Users/Administrator/Desktop/webwrold/frontend/src/components/FlowerField.vue) `initScene()` 流程：
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

**根因**：[frontend/src/views/garden/GardenView.vue](file:///c:/Users/Administrator/Desktop/webwrold/frontend/src/views/garden/GardenView.vue) `onMounted` 里**没 await** 异步的 `fetchAll()`，立即在 `nextTick` 里调 `gsap.from('.source-bar', ...)`：
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

**铁律**：**`onMounted` 里有 async 数据加载 + GSAP 入场动画时，动画必须在数据加载完成 + `nextTick` 之后执行**，不能依赖 `onMounted` 自己的 `nextTick`（那是 DOM 挂载完的 nextTick，不是数据加载完的 nextTick）。**v-for 渲染的元素必须先 `document.querySelector` 检查存在再调 `gsap.from`**，否则数据为空时 GSAP 必报 "target not found" 警告。其他视图（[AIChatView](file:///c:/Users/Administrator/Desktop/webwrold/frontend/src/views/ai/AIChatView.vue) `.msg-row`、[ShopView](file:///c:/Users/Administrator/Desktop/webwrold/frontend/src/views/garden/ShopView.vue) `.shop-card`、[MoodCalendarView](file:///c:/Users/Administrator/Desktop/webwrold/frontend/src/views/mood/MoodCalendarView.vue) `.calendar-cell`、[DiaryListView](file:///c:/Users/Administrator/Desktop/webwrold/frontend/src/views/diary/DiaryListView.vue) `.diary-item`）有同样的模式，目前未修，遇到警告时按本节套路修。

### 6.23 视觉组件集成 4 大坑（2026-07-20 加）

#### 6.23.1 `createMediaElementSource` 一次性约束（AudioVisualizer）

**症状**：[MusicDetailView](file:///c:/Users/Administrator/Desktop/webwrold/frontend/src/views/music/MusicDetailView.vue) 切到第二首歌时，Console 报 `InvalidStateError: HTMLMediaElement already connected previously to a different MediaElementSourceNode`，音波可视化卡住不更新。

**根因**：Web Audio API 规范规定 `audioCtx.createMediaElementSource(audioEl)` 对同一 `<audio>` 元素**只能调用一次**。但 [AudioVisualizer.vue](file:///c:/Users/Administrator/Desktop/webwrold/frontend/src/components/AudioVisualizer.vue) 的 `connect(audioEl)` 在每次切歌时被调用 → 第二次抛 InvalidStateError。

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

**症状**：[AmbientBackground](file:///c:/Users/Administrator/Desktop/webwrold/frontend/src/components/AmbientBackground.vue) / [HeroScene](file:///c:/Users/Administrator/Desktop/webwrold/frontend/src/components/HeroScene.vue) 用 `ref({ scene, camera, renderer, ... })` 时，初次渲染卡顿 200ms+，Console 有大量 Vue 警告 `Avoid adding reactive properties to a Vue instance`。

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

**修复**：所有视觉组件的 rAF 必须走 [utils/visual.js](file:///c:/Users/Administrator/Desktop/webwrold/frontend/src/utils/visual.js) 的 `smartRAF(callback)`，它在 `document.hidden` 时主动 `cancelAnimationFrame`，可见时自动恢复：
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

**铁律**：视觉组件的 4 大坑（`createMediaElementSource` 一次性 / `shallowRef` 而非 `ref` / `smartRAF` 替代 `requestAnimationFrame` / `onBeforeUnmount` 完整释放）**必须同时满足**，缺任何一个都会在长时间使用或多视图切换后出问题。新建视觉组件时直接复制 [AmbientBackground.vue](file:///c:/Users/Administrator/Desktop/webwrold/frontend/src/components/AmbientBackground.vue) 的结构作为模板。

### 6.24 Safari / iOS WebGL 上下文丢失 + emoji 字体不一致（2026-07-30 v2.3.3 加）

#### 6.24.1 iOS Safari 切后台→前台后 3D 场景黑屏（WebGL 上下文丢失）

**症状**：iOS Safari 用户访问首页（HeroScene 3D 浮岛）后切到其他 App，再切回 Safari 时 3D 场景黑屏，Console 无报错但 WebGL context 已失效。

**根因**：iOS Safari 为节省内存，在页面切到后台时会主动释放 WebGL 上下文（触发 `webglcontextlost` 事件）。v2.3.3 之前 [three-helpers.js](../../frontend/src/utils/three-helpers.js) 没有监听该事件，上下文丢失后 Three.js 的 renderer / geometry / material 全部失效，切回前台时无恢复逻辑 → 黑屏。

**修复**（v2.3.3）：[three-helpers.js](../../frontend/src/utils/three-helpers.js) 添加 `webglcontextlost` / `webglcontextrestored` 事件监听：
- `webglcontextlost`：`event.preventDefault()` + 保存当前场景状态（相机位置 / OrbitControls 状态 / 自动旋转开关）
- `webglcontextrestored`：重建 renderer + 重新编译 material + 恢复场景状态 + 重启 rAF 循环

同时 [HeroScene.vue](../../frontend/src/components/HeroScene.vue) 实现 **iOS 降级**策略降低内存压力：
- **Bloom 降级**：iOS 关闭 `UnrealBloomPass`（后处理内存大户）
- **PMREM 降级**：iOS PMREM 分辨率 256→128、阴影贴图 2048→1024、dpr 上限 2→1.5
- 老 iOS 缺 `EXT_color_buffer_half_float` 扩展时，完全关闭 PMREM + Bloom（[utils/visual.js](../../frontend/src/utils/visual.js) `getWebGLCaps()` 检测）

#### 6.24.2 `hasWebGL()` 检测 bug 导致 Safari 误判无 WebGL

**症状**：部分 Safari 用户报告首页 3D 场景直接降级为 SVG 静态插画，但 Safari 明明支持 WebGL。

**根因**：v2.3.3 之前 [utils/visual.js](../../frontend/src/utils/visual.js) 的 `hasWebGL()` 实现有 bug——仅尝试创建 WebGL2 context，若失败就返回 false。但部分老 Safari 只支持 WebGL1（无 WebGL2），被误判为「无 WebGL」→ 直接降级 SVG。

**修复**（v2.3.3）：**hasWebGL 重写**——区分 WebGL1 / WebGL2，先试 WebGL2 失败再试 WebGL1；同时检测关键扩展（`EXT_color_buffer_half_float` 等）+ max texture size；新增 `getWebGLCaps()` 返回完整能力对象、`isSafari()` / `isIOS()` 判断浏览器/平台。

#### 6.24.3 Safari emoji 显示不一致（Apple Color Emoji vs 系统 emoji）

**症状**：Safari 用户反馈导航/个人主页的 emoji 风格与 Chrome 不一致——Safari 用 Apple Color Emoji（彩色写实风格），Chrome 用系统 emoji（扁平风格），视觉不统一。

**根因**：跨平台 emoji 字体差异——浏览器各自调用系统 emoji 字体渲染，不同平台风格差异大（Apple Color Emoji vs Noto Color Emoji vs Segoe UI Emoji），无法通过 CSS 统一。

**修复**（v2.3.3）：新建 [EmojiIcon.vue](../../frontend/src/components/EmojiIcon.vue) 组件，使用 **Iconify** + `@iconify-json/twemoji` 离线 **SVG emoji**（twemoji 风格统一扁平彩色），确保 **跨浏览器一致**。已替换 [AppLayout.vue](../../frontend/src/components/AppLayout.vue)（品牌 / 导航 / 通知 / 资源）+ [ProfileView.vue](../../frontend/src/views/profile/ProfileView.vue)（头像 / 通知 / 资源 / 统计 / 快捷入口 / 花朵阶段）所有 emoji。

**铁律**：Safari / iOS 兼容 3 大坑（`webglcontextlost` 上下文恢复 / `hasWebGL` 须区分 WebGL1+2 + 检测扩展 / emoji 须用 SVG 统一而非系统字体）**必须同时满足**。新建 3D 组件时直接复制 [HeroScene.vue](../../frontend/src/components/HeroScene.vue) 的 `webglcontextlost` / `webglcontextrestored` 监听 + iOS 降级逻辑作为模板。

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

### 7.9 加一个 AI 场景（2026-07-17 起约定）
> 现有 4 个场景在 [app/services/ai_service.py](file:///c:/Users/Administrator/Desktop/webwrold/app/services/ai_service.py) / [app/routers/ai.py](file:///c:/Users/Administrator/Desktop/webwrold/app/routers/ai.py) / [app/schemas/ai.py](file:///c:/Users/Administrator/Desktop/webwrold/app/schemas/ai.py)。再加一个走同样套路：

1. **Schema**：在 [app/schemas/ai.py](file:///c:/Users/Administrator/Desktop/webwrold/app/schemas/ai.py) 加 `AI<X>In` + `AI<X>Out` 两个 Pydantic 模型；在 [app/schemas/__init__.py](file:///c:/Users/Administrator/Desktop/webwrold/app/schemas/__init__.py) 的 `__all__` 里加 import + 在末尾 `model_rebuild()` 区段确保新模型也被 rebuild
2. **Service**：在 [app/services/ai_service.py](file:///c:/Users/Administrator/Desktop/webwrold/app/services/ai_service.py) 加 ① 系统提示词常量（温柔语气、不诊断不开药、危机引导专业帮助） ② 上层方法 `generate_xxx()`，调 `_call_nvidia()`；**禁止**在 router 里直接调 `_call_nvidia()`
3. **Router**：在 [app/routers/ai.py](file:///c:/Users/Administrator/Desktop/webwrold/app/routers/ai.py) 加 `@router.post("/xxx")`，**必须**：
   - `Depends(get_current_user)` 鉴权
   - `try: ... except AIServiceUnavailable: return {"available": False, "message": "治愈系友好提示"}` 降级，**不报 500**
4. **前端集成**：3 选 1
   - 独立新页面：`templates/xxx.html` + `static/js/pages/xxx.js`，在 [app/routers/pages.py](file:///c:/Users/Administrator/Desktop/webwrold/app/routers/pages.py) 加 SSR 路由
   - 已有页面加容器：在 `templates/xxx.html` 加 `<div id="ai-xxx">`，在 `static/js/pages/xxx.js` 加 `loadAIXxx()` 函数
5. **测试降级**：先**不配** `QI_NVIDIA_API_KEY` 跑一遍，确认返回 `available:false` + 友好提示；再配 key 跑一遍，确认 `available:true` + AI 文案

**铁律**：
- AI 文案**永不入库**（保持隐私承诺，与日记端到端加密一脉相承）
- 系统提示词**必须**包含「不诊断不开药、危机情况引导求助专业资源」语义（治愈系调性 + 责任边界）
- 端点**必须**有 try/except 降级（「渐进增强」原则，没 key 也能跑）
- 改完同步更新 README §3.7、本节 §4 Phase 6 表格、[docs/DEVELOPMENT.md §2.x](file:///c:/Users/Administrator/Desktop/webwrold/docs/DEVELOPMENT.md)

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

# 2. 听歌 + 能量（v2.0 后改为 POST /api/music/listen-complete）
#    注意：/api/energy/grant 端点已不存在，能量获取通过听歌完成
musics = s.get("http://127.0.0.1:5000/api/music").json()
music_id = musics[0]["id"] if musics else 1
r = s.post("http://127.0.0.1:5000/api/music/listen-complete",
           json={"music_id": music_id, "progress": 1.0})
assert r.status_code == 200, r.text
assert r.json()["new_total_energy"] == 1  # 见 §6.18：必须重新查 DB 才能拿到新值

# 3. 写日记（密文）
r = s.post("http://127.0.0.1:5000/api/diary",
           json={"content_encrypted": "gAAAAA-test", "is_public": False})
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

> 🔒 **2026-07-19 全站 Vue 3 重构特别约定**：本次重构涉及 **6 份文档同步**（README / HANDOFF / PROJECT_STATE / ARCHITECTURE / DEPLOYMENT / DEVELOPMENT），必须**同一个 commit** 一起更新。互链保持一致，关键词 `Vue 3` / `Vite` / `SPA fallback` / `frontend/` 在 6 份文档中都要出现。

### 12.2 触发条件：什么时候必须改文档

| 改动类型 | 必须更新的文档 | 章节 |
|---|---|---|
| 加 / 删 / 改 SQLAlchemy 模型字段 | README + PROJECT_STATE + ARCHITECTURE | README §4 / PROJECT_STATE §2 / ARCHITECTURE §4 |
| 加 / 删 / 改 Pydantic schema 字段 | README + HANDOFF | README §3.3 / HANDOFF §6.11 |
| 加 / 删 / 改 API 端点 | README + HANDOFF | README §3.2 / HANDOFF §7.2 |
| 加 / 删 / 改 SSR 页面 | README + PROJECT_STATE | README §2 / PROJECT_STATE §3.3 |
| **加 / 删 / 改 Vue 视图 / 路由 / store** | README + HANDOFF + ARCHITECTURE + DEVELOPMENT | README §2 frontend/ 子树 + §3.5 / HANDOFF §2 + §5.8 / ARCHITECTURE「前端架构」 / DEVELOPMENT「前端开发」 |
| **加 / 删 / 改 Vite / Tailwind / 前端依赖** | README + HANDOFF + DEPLOYMENT | README §1.3 / HANDOFF §2 / DEPLOYMENT「前端构建」 |
| 加 / 删 / 改能量规则 / 单日上限 | README + HANDOFF + ARCHITECTURE | README §3.4 / HANDOFF §5.3 / ARCHITECTURE §4.3 |
| 加 / 删 / 改业务常量 | README + PROJECT_STATE | README §3.6 / PROJECT_STATE §5.2 |
| 加 / 改 / 删依赖 | requirements.txt + HANDOFF + frontend/package.json | requirements.txt / HANDOFF §2 / frontend/package.json |
| 加 / 改 / 删 .env 配置项 | .env.example + HANDOFF + PROJECT_STATE | .env.example / HANDOFF §1 / PROJECT_STATE §4 |
| 改端口 / 启动命令 | README + DEPLOYMENT + HANDOFF | README §1 / DEPLOYMENT 全文 / HANDOFF §1 |
| 改 CSS 变量 / 配色 | PROJECT_STATE + frontend/tailwind.config.js | PROJECT_STATE §5 / tailwind.config.js token |
| 改后台入口路径 / 新后台 API | HANDOFF + ARCHITECTURE + PROJECT_STATE | HANDOFF §5.6 / ARCHITECTURE §6.5 / PROJECT_STATE §5.3 |
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

### 12.6 自动推送铁律（commit 完必须立即 push）

> 🔒 跟 §12.1 同一优先级。

**铁律**：`git commit` 完之后**立刻** `git push origin main`，**不允许**：
- ❌ 「先 commit 完，一会儿一起推」→ 仓库永远落后本地
- ❌ 「明天再推」→ 第二天忘了 → 本地数据丢失 / 换电脑没同步
- ❌ 「攒一周的 commit 一起推」→ 出错时回滚困难
- ❌ 「push 前再 review 一下」→ 没问题立即推，「review 完忘了」也算违反

**正确做法**：
```bash
git add -A
git commit -m "fix(auth): add is_admin field to AuthOut schema"
git push origin main           # ← 必须紧跟 commit
```

**push 失败的应急**：
- 网络问题：retry 一次；再失败 → 截图报错，留 `WIP: push pending` 标记
- 远端冲突：`git pull --rebase` → 解决 → `git push`（**不要** `git push --force`，除非你 100% 确定）
- 权限问题：检查 `gh auth status`，重新 `gh auth login`

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

> 写于 2026-07-14 — 项目状态：完整可运行，所有 4 Phase 已交付
>
> 末次更新 2026-07-15（会话 2）：补 §6.11 Pydantic schema 字段缺失踩坑、§12 文档自动同步铁律、首管密码现状说明。
>
> 末次更新 2026-07-15（会话 3）：首发到 GitHub — `https://github.com/sunday-lil/jingyu`（public）。
>
> 末次更新 2026-07-17（会话 8）：AI 全面接入（Phase 6）—— NVIDIA NIM API 4 个场景（树洞对话 / 漂流瓶鼓励语 / 情绪日历治愈语 / 音乐推荐），新增 [app/schemas/ai.py](file:///c:/Users/Administrator/Desktop/webwrold/app/schemas/ai.py) + [app/services/ai_service.py](file:///c:/Users/Administrator/Desktop/webwrold/app/services/ai_service.py) + [app/routers/ai.py](file:///c:/Users/Administrator/Desktop/webwrold/app/routers/ai.py) + [templates/ai_chat.html](file:///c:/Users/Administrator/Desktop/webwrold/templates/ai_chat.html) + 4 个前端集成点；§4 加 Phase 6、§5.7 加 NVIDIA NIM 选型理由、§7.9 加「加 AI 场景」指南；可选功能，未配 key 时优雅降级。
>
> 末次更新 2026-07-17（会话 8 后续修复）：① AI 模型默认值 `nvidia/llama-3.1-nemotron-70b-instruct` → `meta/llama-3.1-8b-instruct`（70B 在用户 NVIDIA 账户下 404 不可用，换 8B 兼顾速度与质量）；② `_call_nvidia` 超时 30s → 60s 兜底；③ 模板字体引用换国内镜像 `fonts.loli.net` / `gstatic.loli.net`（原 `fonts.googleapis.com` 被墙 ERR_CONNECTION_REFUSED），CSS 变量有系统字体兜底。同步更新 README / PROJECT_STATE / ARCHITECTURE / DEPLOYMENT / DEVELOPMENT。
>
> 末次更新 2026-07-19（v2.0 全站 Vue 3 重构）：前端从「Jinja2 SSR + 原生 HTML/CSS/JS」迁移到「Vue 3 SPA + Vite 5 工程化」。新增 [`frontend/`](file:///c:/Users/Administrator/Desktop/webwrold/frontend/) 目录（Vue 3 `<script setup>` + Vue Router 4 + Pinia + Tailwind CSS + GSAP + @vueuse/motion + Three.js + axios），13 个视图迁入 `frontend/src/views/`。后端 [app/main.py](file:///c:/Users/Administrator/Desktop/webwrold/app/main.py) 加 SPA fallback（排除 /api//static//admin/ 路径），[app/routers/pages.py](file:///c:/Users/Administrator/Desktop/webwrold/app/routers/pages.py) 简化为 4 个 302 重定向，[app/config.py](file:///c:/Users/Administrator/Desktop/webwrold/app/config.py) 修复 env_prefix bug（加 `env_prefix="qi_"`），[app/services/ai_service.py](file:///c:/Users/Administrator/Desktop/webwrold/app/services/ai_service.py) 超时 30s→60s，AI 模型链 `nvidia/llama-3.1-nemotron-70b-instruct` → `meta/llama-3.3-70b-instruct` → `meta/llama-3.1-8b-instruct`。删除 showcase 动效页。§2 技术栈表大改、§5.8 加前端选型决策、§6.12-6.15 加 4 条 Vue/Vite 踩坑（IPv6 [::1] / base dev 模式 / npm install 大包耗时 / SPA fallback 排除路径）、§12.2 同步表加 Vue 相关行。**6 份文档同步**（README / HANDOFF / PROJECT_STATE / ARCHITECTURE / DEPLOYMENT / DEVELOPMENT），Iron Rule §12 仍然适用（地位高于任何具体技术决策）。
>
> 末次更新 2026-07-19（v2.0.1 端口策略 + Three.js 花田）：① **端口策略调整** — 开发模式让 Vite 占 :5000（用户入口），FastAPI 改听 :5001（API，由 [start.py](file:///c:/Users/Administrator/Desktop/webwrold/start.py) 设置 `QI_PORT=5001`），Vite proxy 把 `/api`、`/static`、`/admin`、`/docs`、`/openapi.json` 转发到 :5001；生产模式不变（FastAPI :5000 + SPA fallback）。原因：FastAPI :5000 反代 Vite :5173 时，Vite 内部路径 `/@id/__x00__plugin-vue:export-helper` 含 null 字符 + 冒号被 httpx 转发破坏，浏览器报 `SyntaxError`。② **start.py 增强** — `start` 自动检测 dist 切换端口策略、`stop` 同时停 FastAPI + Vite、`status` 显示两进程状态、新增 `build` 子命令一键构建前端、`fg` 只起 FastAPI 不起 Vite。③ **vite.config.js** — dev server port 5173 → 5000，proxy target :5000 → :5001，移除 `hmr.clientPort`，新增 `/docs` 和 `/openapi.json` 代理。④ **app/main.py** — SPA fallback 移除回退代理到 Vite 逻辑，开发态返回提示页引导访问 Vite :5000；新增 `EXT_TO_MIME` 映射（`.js` / `.css` / `.woff2` 等正确设置 `Content-Type`）。⑤ **Three.js 3D 花田场景** — 新增 [frontend/src/components/FlowerField.vue](file:///c:/Users/Administrator/Desktop/webwrold/frontend/src/components/FlowerField.vue)：60 朵花 × 5 瓣 = 300 `InstancedMesh`，5 种治愈色（藕粉 `#E8B8C5` / 淡黄 `#E8D5A8` / 青绿 `#A8C5A0` / 雾蓝 `#A8B8C5` / 纯白 `#FAF6F2`），绽放动效 + 风摆动 + 雾效 + 飘浮光点，摄影机自动呼吸 + 鼠标跟随，用 `defineAsyncComponent` 异步加载减小首屏包；[GardenView.vue](file:///c:/Users/Administrator/Desktop/webwrold/frontend/src/views/garden/GardenView.vue) 顶部嵌入 380px 高 + 圆角阴影包裹 + 底部提示文案。§5.9 加端口策略决策、§6.16 加 FastAPI 反代 Vite 踩坑。**6 份文档同步**（README / HANDOFF / PROJECT_STATE / ARCHITECTURE / DEPLOYMENT / DEVELOPMENT）。
>
> 末次更新 2026-07-20（视觉增强 v2.1）：① **三层渐进增强视觉策略** — 用户要求在 v2.0.1 FlowerField 基础上进一步提升整体视觉美感，加入 3D / 伪 3D 背景元素和动态视觉效果，**但不能影响页面加载性能或用户体验，且必须为 3D 渲染能力有限的浏览器实现备用机制**。决策：用「CSS 永远启用 → Canvas2D 中量级 → Three.js 按需」三层渐进增强，每层独立可降级，配套 [utils/visual.js](file:///c:/Users/Administrator/Desktop/webwrold/frontend/src/utils/visual.js) 能力检测（`hasWebGL` / `prefersReducedMotion` / `isMobile` / `isLowPower` / `shouldUseThreeJS` / `shouldUseCanvas` / `smartRAF`）。② **新增 4 个视觉文件** — [frontend/src/utils/visual.js](file:///c:/Users/Administrator/Desktop/webwrold/frontend/src/utils/visual.js) 视觉能力检测；[frontend/src/components/AmbientBackground.vue](file:///c:/Users/Administrator/Desktop/webwrold/frontend/src/components/AmbientBackground.vue) 全局氛围背景（CSS 雾气光斑 + Canvas2D 飘浮光点 + Three.js 远景粒子层，三层渐进增强，挂在 [AppLayout.vue](file:///c:/Users/Administrator/Desktop/webwrold/frontend/src/components/AppLayout.vue) 根）；[frontend/src/components/HeroScene.vue](file:///c:/Users/Administrator/Desktop/webwrold/frontend/src/components/HeroScene.vue) 首页 Hero 区 3D 浮岛雾海（PlaneGeometry 128×128 波动海面 + 3 浮岛 + FogExp2 雾 + 80 飘浮光点，SVG 静态插画降级）；[frontend/src/components/AudioVisualizer.vue](file:///c:/Users/Administrator/Desktop/webwrold/frontend/src/components/AudioVisualizer.vue) 5 色音波可视化（Web Audio API AnalyserNode + Canvas2D，CSS 5 色横条降级，挂在 [MusicDetailView.vue](file:///c:/Users/Administrator/Desktop/webwrold/frontend/src/views/music/MusicDetailView.vue)）。③ **HomeView 重写** — 集成 HeroScene 3D 背景 + 五音卡片 CSS 3D 倾斜（`perspective + rotateX/Y + translateZ`，鼠标跟随 + reduced-motion 自动降级为静态）。④ **性能保护** — 所有 Three.js 组件 `defineAsyncComponent` 异步加载 + `shallowRef` 持有 + `smartRAF` 标签页隐藏暂停 + `onBeforeUnmount` 完整释放 + 移动端降级（粒子数减半 + dpr≤1.5）+ `manualChunks` 把 `three` 单独打成 `three-vendor` chunk（gzip 175KB，仅访问 `/` 或 `/garden` 时按需拉取，首屏不加载）。⑤ **Web Audio API 一次性约束** — `createMediaElementSource(audioEl)` 对同一 `<audio>` 元素只能调用一次，AudioVisualizer 用 `if (!sourceNode)` 守卫，MusicDetailView 用 `visualizerConnected` ref 标记首次 `playIndex` 时连接、后续切歌不重连。§5.10 加视觉增强策略决策、§6.23 加视觉组件集成 4 大坑（createMediaElementSource 一次性 / shallowRef 而非 ref / smartRAF 替代 requestAnimationFrame / onBeforeUnmount 完整释放）。**6 份文档同步**（README / HANDOFF / PROJECT_STATE / ARCHITECTURE / DEPLOYMENT / DEVELOPMENT）。
>
> 末次更新 2026-07-20（v2.2 3D 元素与动效全面重构）：用户反馈 v2.1 上线后两个核心问题：① **交互体验缺失**——用户不知道 3D 场景可以拖拽 / 缩放 / 点击，以为是静态背景；② **视觉粗糙过时**——`PointsMaterial` 方形粒子 + `MeshBasicMaterial` 平面着色 + 无环境映射，整体观感类似 80/90 年代红白机低品质视觉。**决策**：① 4 个视觉组件全部升级到 PBR（Physically Based Rendering）渲染管线（`ACESFilmicToneMapping` + `SRGBColorSpace` + `PCFSoftShadowMap` + `RoomEnvironment` PMREM + `UnrealBloomPass`）；② 抽出 [utils/three-helpers.js](file:///c:/Users/Administrator/Desktop/webwrold/frontend/src/utils/three-helpers.js) 集中 9 个共享 PBR 工具函数（createRenderer / createEnvironment / createPostProcessing / createOrbitControls / createKeyLight / createFillLight / createSoftSpriteTexture / disposeObject3D / disposeRenderer）；③ 新增 [SceneHint.vue](file:///c:/Users/Administrator/Desktop/webwrold/frontend/src/components/SceneHint.vue) 交互指引横幅 + [SceneControls.vue](file:///c:/Users/Administrator/Desktop/webwrold/frontend/src/components/SceneControls.vue) 视图控制工具栏；④ HeroScene 改用 `LatheGeometry` 旋转曲面浮岛 + 递归樱花树 + 水面 `onBeforeCompile` 顶点位移 shader；FlowerField 改用自定义 `BufferGeometry` 立体花瓣 + `MeshPhysicalMaterial`（透射 + sheen）；AudioVisualizer 升级 4 模式（wave/mirror/radial/particles）+ 节拍检测；AmbientBackground 升级 Canvas2D 柔光 sprite + 鼠标排斥 + 滚动视差 + 轻量 Bloom；⑤ 所有 3D 场景统一 `OrbitControls`（拖拽旋转 + 滚轮缩放）+ `raycaster` 点击拾取。**降级路径保留**：v2.1 三层渐进增强 + SVG / CSS 静态降级 + `prefers-reduced-motion` + 移动端粒子减半 + dpr ≤ 1.5 全部保留。**构建产物体积变化**：HeroScene 7.5KB → 13.54KB、FlowerField 9.94KB、SceneControls 4.5KB、three-vendor 175KB → 719.84KB（含 addons：OrbitControls / EffectComposer / UnrealBloomPass / RoomEnvironment），首屏不加载。§2 技术栈表 Three.js 行更新、§5.11 加 v2.2 决策、DEVELOPMENT §1.9.8 加 v2.2 新 3 大铁律（⑤ PBR 用 three-helpers / ⑥ 必须 SceneHint+SceneControls / ⑦ 必须 OrbitControls+raycaster）。**6 份文档同步**（README / HANDOFF / PROJECT_STATE / ARCHITECTURE / DEPLOYMENT / DEVELOPMENT）。
>
> 末次更新 2026-07-20（v2.2.1 start.py 自动构建）：用户反馈服务器部署场景「端口代理已配好 :5000 不能动，服务端只跑 `python start.py`」，但 v2.2 行为是 dist 未构建 → 走开发模式（Vite 占 :5000），会破坏端口代理。**决策**：改 [start.py](file:///c:/Users/Administrator/Desktop/webwrold/start.py) 默认行为——dist 未构建时**不再走开发模式**，而是：① 检测 Node.js 是否可用 → 可用则自动 `npm install + npm run build` 后走生产模式（:5000 永远是 FastAPI）；② Node.js 不可用 → 报错退出（不让 Vite 占 :5000）。**新增 `--dev` 参数**：`python start.py --dev` 显式走开发模式（Vite :5000 + FastAPI :5001），本地开发用。**新增 2 个辅助函数**：`_check_node_available()` 检测 node + npm 版本 / `_ensure_dist_or_dev(force_dev)` 决策启动模式。**服务器部署简化为 3 步**：① 上传代码 ② 装 Python 依赖 + Node.js 18+ ③ `python start.py`（首次自动构建约 7 分钟，之后秒启）。DEVELOPMENT §1.9.1 / §1.9.2 / §1.9.6 更新（开发模式现在需 `--dev`）、DEPLOYMENT §1.5 / §2.3 更新（前端构建可选，start.py 自动）。**6 份文档同步**（README / HANDOFF / PROJECT_STATE / ARCHITECTURE / DEPLOYMENT / DEVELOPMENT）。
>
> 末次更新 2026-07-25（v2.2.2 start.py 默认应用模式）：用户要求「`python start.py` 启动时是应用模式不是生产模式，前后端一起启动，且检测到没有编译的时候自动编译」。**决策**：改 [start.py](file:///c:/Users/Administrator/Desktop/webwrold/start.py) 默认行为回滚 v2.2.1 —— **默认走应用/开发模式**（前后端一起起：Vite :5000 HMR + FastAPI :5001 API）。**新增 `_ensure_node_modules()` 函数**：检测 `frontend/node_modules` 不存在则自动 `npm install`（约 7 分钟，仅首次），不构建 dist（应用模式用 Vite dev server 不需要构建产物）。**新增 `--prod` 参数**：显式生产模式，FastAPI :5000 单进程 + 需 `static/dist/` 已构建（未构建报错退出，提示先 `python start.py build`）。**`--dev` 改为兼容别名**（等同默认行为，保留向后兼容）。**新增 `_ensure_dist_for_prod()` 函数**：生产模式启动前的 dist 检查。**移除 v2.2.1 的 `_ensure_dist_or_dev()`**（不再有「dist 未构建 → 自动 npm run build 走生产模式」逻辑）。**服务器部署 3 步不变**：① 上传代码 ② 装 Python + Node.js 18+ ③ `python start.py`（首次自动 npm install，之后秒启）；生产部署可选 `python start.py build && python start.py --prod` 走单进程模式。README §1.1/§1.3/§3.1、HANDOFF §1、PROJECT_STATE §1/§2、ARCHITECTURE §1/§1.2 顶部提示、DEPLOYMENT 顶部提示/§1.5/§2.3、DEVELOPMENT 顶部提示/§1.9/§1.9.1/§1.9.2 全部更新。**6 份文档同步**（README / HANDOFF / PROJECT_STATE / ARCHITECTURE / DEPLOYMENT / DEVELOPMENT）。
>
> 末次更新 2026-07-25（v2.2.3 移动端响应式 UI + 3D 几何降档）：用户要求「不同设备不同 UI 布局，考虑手机屏幕小不能展示所有功能，iPhone 16 默认浏览器 Safari 导航和搜索栏在底部，UI 要自适应」。**决策**：① **三档断点系统差异化布局**（[AppLayout.vue](file:///c:/Users/Administrator/Desktop/webwrold/frontend/src/components/AppLayout.vue) + [main.css](file:///c:/Users/Administrator/Desktop/webwrold/frontend/src/assets/styles/main.css)）：桌面 ≥1025px 顶部完整导航 / 平板 769-1024px 紧凑导航（图标 + 短标签纵向）/ 移动端 ≤768px topbar + 底部 tabbar（4 固定 + 中央「更多」按钮 → 抽屉展开 3 项次要入口）。② **iOS Safari 适配**：`100dvh` + `100vh` 兜底应对底部地址栏跳变；`env(safe-area-inset-top)` 避让刘海/灵动岛；`env(safe-area-inset-bottom)` 避让 Home Indicator；`.safe-top` / `.safe-bottom` 工具类 + 三档断点工具类（`.mobile-only` / `.tablet-only` / `.desktop-only`）。③ **fullscreen 路由模式**：`route.meta.fullscreen = true` 隐藏 topbar + tabbar，main 占满 `100dvh`（AIChatView 用，避免 tabbar 遮挡输入框）。④ **13 个视图移动端差异化布局**：HomeView 五音卡片横向滚动 + scroll-snap；MusicDetailView 播放器避让 tabbar；DiaryListView 时间轴左移；GardenView 花朵数 60→36 + 3D 高度 380→280px；MoodCalendarView 单列；ShopView 2 列；LoginView/RegisterView 减小内边距；AIChatView fullscreen。⑤ **4 个 3D 组件移动端几何精度降档**（在原有「粒子减半 + dpr≤1.5 + Bloom 降强度」基础上）：HeroScene Lathe/Cylinder 段数 24→16 + 樱花树递归深度 4→3 + 花团 Icosahedron detail 2→1 + 树枝圆柱段 6→5；FlowerField 花瓣网格 5×8→4×6 + 花蕊 Icosahedron detail 2→1 + 地面圆 64→32 + 茎圆柱段 6→5；AudioVisualizer 镜像柱 48→32 + 径向柱 64→32；AmbientBackground 已优化保留。§5.10 性能保护行更新、§1 总体状态加 v2.2.3 行、ARCHITECTURE §1.1.6 移动端降级 + 降级矩阵更新、DEVELOPMENT §1.9.4 性能保护 + 验证清单更新、DEPLOYMENT 顶部加 v2.2.3 提示。**6 份文档同步**（README / HANDOFF / PROJECT_STATE / ARCHITECTURE / DEPLOYMENT / DEVELOPMENT）。
>
> 末次更新 2026-07-25（v2.3 六大四字名模块重构 + 双资源系统 + 花朵生命周期 + 通知 + 个人主页 + 古琴弹西洋曲谱）：用户要求按治愈系调性对模块重命名 + 双资源经济 + 花朵生命周期 + 通知 + 个人主页 + 西方曲谱子菜单 + 日记调整 + 情绪日历对齐修复 + 树洞改进 + 漂流瓶社交化 + 移动端兼容 + 琴音疗心即 /music 顶级 + pre-commit 5 项正式化（共 13 项）。**决策**：① **六大四字名模块**（含路由）：琴音疗心 / 漂流日记 / 情绪日历 / 心语树洞 / 落叶画坊 / 屿上花田 + 辅助：拾瓶 / 我的 + [AppLayout.vue](file:///c:/Users/Administrator/Desktop/webwrold/frontend/src/components/AppLayout.vue) 顶部品牌图标 SVG 岛屿轮廓统一。② **双资源系统**：`User.total_energy`（露水，保留）+ `User.leaves`（落叶，新增）；`EnergyRecord` **不**加 `resource_type`；`ShopItem.cost_currency`（`dew`/`leaves`）；`constants.DAILY_ENERGY_LIMITS = {listen_music: 20, write_diary: 10, checkin: 5}`（仅露水有日上限）。露水=向内获得（听歌/打卡/写日记），落叶=花朵枯萎后拾取获得。③ **花朵生命周期**：新增 `UserFlower` 模型 + `flower_service` + `/api/garden/flowers/*` API；阶段 `seed → sprout → bud → bloom → wilted`，浇水消耗 1 露水推进；盛开超 7 天未浇水 → 枯萎；拾取枯花 → +2 落叶。④ **通知系统**：新增 `Notification` 模型 + `routers/notification.py`（单数）；触发点：拾瓶被鼓励（type=`encouragement`）；前端 60s 轮询 `/api/notifications/unread` + 顶部 🔔 铃铛 + 红点 + 点击跳 `/notifications` 路由。⑤ **个人主页**：`routers/profile.py` + `views/profile/ProfileView.vue`；`GET /api/profile` / `GET /api/profile/stats` / `GET /api/profile/{user_id}`；卡片式：头像 + 昵称 + 双资源条 + 统计卡 + 最近活动。⑥ **古琴弹西洋曲谱子菜单**：`musics.category` 列（`classic`/`western`）；seed 加 6 首（《绿袖子》《卡农》《致爱丽丝》《月光奏鸣曲》《天鹅湖》《昨日重现》）；`/api/music?category=western|classic`；前端 `/music/western` + `views/music/MusicWesternView.vue` 独立列表。⑦ **日记调整**：`Diary.content`（明文，v2.3 替代 `content_encrypted`）+ `Diary.send_to_ai_hole`（bool）；前端 DiaryWriteView 加发布选项 radio（放入漂流瓶 🍶 / 不放入 🌳）。⑧ **情绪日历对齐修复**：前后端 `mood_emoji` 统一为 emoji 字符（如 "😊"），原 "calm" 字符串废弃；`MOOD_INFO` 加 `emoji` 字段统一管理。⑨ **树洞改进**：统一 🌳 树 emoji 图标；`<textarea>` 多行 + 500 字提示；文件式聊天历史 `data/chats/{user_id}/{session_id}.json` 保留 7 天；离开 toast「树洞会在这里等你回来」。⑩ **漂流瓶社交化**：拾瓶被鼓励走 Notification（type=`encouragement`）；作者收到「收到 1 个陌生人的拥抱」通知。⑪ **移动端兼容**：花园 / 个人主页 / 通知列表 / 树洞 / 西方曲谱列表全部覆盖 v2.2.3 三档断点 + safe-area + 100dvh。⑫ **琴音疗心板块即 /music 顶级模块**：`/music` 整合 5 音卡片 + 西方曲谱入口 + 播放器入口 + AI 选音；新增 `/music/western` 子路由。⑬ **pre-commit 5 项 checklist 正式化**：Pydantic Out / `_migrate_legacy_columns` / `constants.py` / `.env.example` / README+HANDOFF 速查表（详见 §12.4 / README §9.3 / PROJECT_STATE §8.3）。**数据库迁移**（`_migrate_legacy_columns()` 自动加 5 列）：users.leaves / diaries.content / diaries.send_to_ai_hole / shop_items.cost_currency / musics.category；新表 user_flowers / notifications 由 init_db() 自动建表。**Smoke test**（详见 [README §7.1](file:///c:/Users/Administrator/Desktop/webwrold/README.md)）：`python start.py restart` ✅ / `curl /` 200 / `curl /api/music` 200（含西方 6 首，共 22 首）/ `curl /music` 200 / `curl /profile` 302 / `curl /music/western` 200 / `curl /api/admin/stats` 401 / `npm run build` 通过 / `_migrate_legacy_columns` 跑通（5 列）/ 双资源 UI 显示正常 / 通知 60s 轮询生效。**6 份文档同步**（README / HANDOFF / PROJECT_STATE / ARCHITECTURE / DEPLOYMENT / DEVELOPMENT）。关键词 `双资源` / `露水` / `落叶` / `UserFlower` / `Notification` / `ProfileView` / `古琴弹西洋曲谱` / `send_to_ai_hole` / `树洞` / `漂流瓶社交` / `琴音疗心` / `pre-commit 5 项` 在 6 份文档中都要出现。
>
> 末次更新 2026-08-14（v2.4.3 花语文案焕新 + emoji 名称对齐 + 徽章奖励落叶 + 树洞三层回复 + 情绪日历空 bug 修复）：用户反馈一系列内容运营 + Bug 修复点。**决策**：① **删除「古琴初学者」废弃徽章**（v2.4.0 改名「琴音知音」后旧徽章残留）— [app/seed.py](file:///c:/Users/Administrator/Desktop/webwrold/app/seed.py) 启动时清理 `DEPRECATED_BADGES`。② **「花田主人」→「花间客」** + **「花坊」→「落叶花坊」**（命名更点题 / 诗意）。③ **情绪日历空白 Bug 修复** — [MoodCalendarView.vue](file:///c:/Users/Administrator/Desktop/webwrold/frontend/src/views/mood/MoodCalendarView.vue) `cell.moodKeys.length` 在空单元格上抛 `TypeError` 整页空白，改可选链 `cell.moodKeys?.length > 0`。④ **落叶死锁解除** — 新增 [constants.py](file:///c:/Users/Administrator/Desktop/webwrold/app/utils/constants.py) `BADGE_LEAF_REWARD: Final[int] = 10`；[energy_service.py](file:///c:/Users/Administrator/Desktop/webwrold/app/services/energy_service.py) `check_achievements()` 每解锁一个徽章额外发放 10 落叶，返回 `{new_badges, new_leaves, leaves_balance}`；mood / diary / music / ai / energy 5 路由透传。⑤ **花田 AI 显示基于实际种花** — `<FlowerField v-if="flowers.length > 0" />`。⑥ **首页 emoji 🏝️ → 🌊** + **漂流瓶 emoji 🍶 → 🏺**。⑦ **树洞 AI 重写** — [ai_service.py](file:///c:/Users/Administrator/Desktop/webwrold/app/services/ai_service.py) `SYSTEM_PROMPT_TREEHOLE` 重写为三层结构（接住情绪 / 安慰或新视角 / 具体可操作的小建议），解决旧版「只重复消极情绪、做无用情感共鸣」问题。⑧ **花种 emoji 与名称对齐 + 花语化** — 12 种花种介绍全改为「花语：XX」格式；emoji 对齐（薰衣草 💜→🪻 / 桂花→小麦 🌾 / 银杏→青叶 🍃 / 兰花+梅花合并为樱花 🌸 / 白鹤→火烈鸟 🦩 / 蓑衣→斗篷 🧥）。⑨ **装扮动物扩充** — 新增小鸟 🐦 / 小鸭 🦆 / 小狗 🐶。⑩ **seed 改名迁移 + 去重** — `RENAME_MAP` 改名老库物品 + 合并同名重复（GardenItem 引用迁移到 keeper）。**Smoke test**：`python start.py restart` ✅ / `curl /api/shop/items` 200（27 件，含新动物 + 花语介绍）✅ / 情绪日历页面非空 ✅ / 树洞回复含建议 ✅ / 花田未种花不显示 3D ✅。详见 §4 Phase 11。**6 份文档同步**（README / HANDOFF / PROJECT_STATE / ARCHITECTURE / DEPLOYMENT / DEVELOPMENT）。关键词 `v2.4.3` / `花语化` / `emoji 对齐` / `BADGE_LEAF_REWARD` / `落叶死锁解除` / `树洞三层回复` / `情绪日历空白修复` / `花间客改名` / `落叶花坊改名` / `改名迁移` / `去重` / `岛上物件 emoji` / `首页海浪 emoji` / `漂流瓶 emoji` / `动物扩充` / `花田 AI 显示修复` 在 6 份文档中都要出现。
>
> 末次更新 2026-08-15（v2.4.4 情绪日历透明修复 + 旧版日记迁移 + mood_checkins 主键重建 + 头像图片上传 + 落叶花坊文案打磨）：用户反馈一系列可见性 / 数据完整性 / 表结构问题 + 期望头像能上传图片。**决策**：① **情绪日历 emoji 透明修复** — [MoodCalendarView.vue](file:///c:/Users/Administrator/Desktop/webwrold/frontend/src/views/mood/MoodCalendarView.vue) GSAP 动画设置 `opacity:0` 导致心情选择按钮几乎不可见，移除该属性。② **旧版日记迁移** — 旧版加密日记 `content` 字段为空（`content_encrypted` 是假占位符），数据库迁移自动填入提示文本「（这段日记来自旧版本，内容已无法读取）」。③ **mood_checkins 主键重建** — v2.4 的迁移用了 `CREATE TABLE AS SELECT` 导致 `mood_checkins` 表丢失主键和自增，批量打卡 `db.flush()` 报 `NULL identity key`（500）；重建表（`id INTEGER PRIMARY KEY AUTOINCREMENT` + FK + 索引），数据完整迁移。④ **avatar 字段长度** — [User.avatar](file:///c:/Users/Administrator/Desktop/webwrold/app/models/user.py) `String(16)` → `String(255)`（存图片 URL 路径如 `/static/uploads/avatars/1_1234567890.jpg`），[ProfileUpdateIn](file:///c:/Users/Administrator/Desktop/webwrold/app/schemas/profile.py) `max_length=255` 同步。⑤ **头像图片上传** — 新增 `POST /api/profile/avatar` 端点（JPG/PNG/WebP/GIF ≤2MB，存 `static/uploads/avatars/`，目录自动创建）；[ProfileView.vue](file:///c:/Users/Administrator/Desktop/webwrold/frontend/src/views/profile/ProfileView.vue) 上传按钮 + [AIChatView.vue](file:///c:/Users/Administrator/Desktop/webwrold/frontend/src/views/ai/AIChatView.vue) 图片头像渲染。⑥ **落叶花坊花朵介绍** — 移除「花语：」前缀，只保留完整花语。⑦ **徽章落叶奖励分级** — 按 trigger 分级（streak_7=7 / listen_10=10 / pick_10=10 / flower_10=10 / chat_20=15 / diary_30=20 / 默认=10）。⑧ **情绪日历使用指南** — 改为罗素情绪环模型（Russell's Circumplex Model）四象限说明。⑨ **岛上物件 emoji** — 🎁 → 🧳（行李箱）。⑩ **通知 emoji 统一** — 漂流瓶回复通知 emoji 统一为 💛。**Smoke test**：`python start.py restart` ✅ / 情绪日历心情按钮可见 ✅ / 旧版日记显示提示文本 ✅ / 批量打卡不再 500 ✅ / 头像上传 200 ✅。详见 §4 Phase 12。**6 份文档同步**（README / HANDOFF / PROJECT_STATE / ARCHITECTURE / DEPLOYMENT / DEVELOPMENT）。关键词 `v2.4.4` / `情绪日历透明修复` / `旧版日记迁移` / `mood_checkins 主键重建` / `avatar 字段长度` / `头像图片上传` / `花朵介绍` / `徽章落叶分级` / `情绪日历指南` / `岛上物件 emoji` / `通知 emoji 统一` 在 6 份文档中都要出现。
