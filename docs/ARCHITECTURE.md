# 架构 — 静屿

> 本文件讲**为什么**这样设计，不是讲**做了什么**。想知道做了什么看 [README.md](../../README.md)。

> 🔒 **改了本文件涉及的代码，必须同步更新 [HANDOFF §12](../../HANDOFF.md) / [PROJECT_STATE §8](../PROJECT_STATE.md) / [DEVELOPMENT §1.8](DEVELOPMENT.md) 列出的对应文档。** 改代码不改文档 = 改了一半。

> 🔒 **2026-07-19 v2.0.1 端口策略 + Three.js 花田更新**：① §1 架构图改为 Vite :5000 / FastAPI :5001（开发）+ FastAPI :5000（生产）；② §1.1 前端架构加 `FlowerField.vue` 3D 花田组件说明；③ §1.2 开发/生产模式切换的端口策略更新（Vite 占 :5000，FastAPI 改 :5001）。关键词 `Vue 3` / `Vite` / `SPA fallback` / `frontend/` / `FlowerField` / `5001` 在 6 份文档（README / HANDOFF / PROJECT_STATE / ARCHITECTURE / DEPLOYMENT / DEVELOPMENT）中都要出现。

> 🔒 **2026-07-20 v2.1 视觉增强更新**：① §1.1 加 §1.1.6 视觉增强组件群（AmbientBackground / HeroScene / AudioVisualizer + utils/visual.js）；② §7.7 末尾的 Iron Rule 提醒扩展关键词，包含 `三层渐进增强` / `shallowRef` / `smartRAF` / `prefers-reduced-motion`。关键词 `三层渐进增强` / `AmbientBackground` / `HeroScene` / `AudioVisualizer` / `visual.js` / `shallowRef` / `smartRAF` 在 6 份文档中都要出现。

> 🔒 **2026-07-20 v2.2 3D 元素与动效全面重构**：① 4 个视觉组件全部升级到 PBR 渲染管线（ACESFilmicToneMapping + SRGBColorSpace + PCFSoftShadowMap + RoomEnvironment PMREM + UnrealBloomPass）；② 新增 [utils/three-helpers.js](../../frontend/src/utils/three-helpers.js) 集中导出 9 个共享 PBR 工具函数；③ 新增 [SceneHint.vue](../../frontend/src/components/SceneHint.vue) 交互指引横幅 + [SceneControls.vue](../../frontend/src/components/SceneControls.vue) 视图控制工具栏，解决「用户不知道如何与 3D 元素交互」问题；④ HeroScene 改用 `LatheGeometry` 旋转曲面浮岛 + 递归樱花树 + 水面 `onBeforeCompile` 顶点位移 shader；FlowerField 改用自定义 `BufferGeometry` 立体花瓣 + `MeshPhysicalMaterial`；AudioVisualizer 升级 4 模式 + 节拍检测；AmbientBackground 升级 Canvas2D 柔光 sprite + 滚动视差；⑤ 所有 3D 场景统一 `OrbitControls`（拖拽旋转 + 滚轮缩放）+ `raycaster` 点击拾取。关键词 `PBR` / `three-helpers` / `SceneHint` / `SceneControls` / `OrbitControls` / `raycaster` / `UnrealBloomPass` / `RoomEnvironment` / `LatheGeometry` 在 6 份文档中都要出现。

> 🔒 **2026-07-25 v2.2.2 start.py 默认应用模式**：`python start.py` 默认行为变更——**默认走应用/开发模式**（Vite :5000 HMR + FastAPI :5001 API 一起起），自动检测 `frontend/node_modules` 不存在则 `npm install`（不 build dist，应用模式用 Vite dev server 不需要构建产物）。新增 `--prod` 参数显式生产模式（FastAPI :5000 单进程，需 dist 已构建）。`--dev` 改为兼容别名（等同默认行为）。§1.2 开发/生产模式切换的端口策略不变，但触发条件改为：默认 → 应用模式（Vite :5000）；`--prod` → 生产模式（FastAPI :5000，需 dist 已构建）。关键词 `--prod` / `默认应用模式` / `自动 npm install` / `前后端一起起` 在 6 份文档中都要出现。

> 🔒 **2026-07-25 v2.3 六大四字名模块 + 双资源系统 + 花朵生命周期 + 通知 + 个人主页 + 古琴弹西洋曲谱**：① 新增 `UserFlower` + `Notification` 模型 + `flower_service` 业务层 + `/api/garden/flowers/*` + `/api/notifications/*` + `/api/profile/me` 端点；② 双资源系统 `User.dew` + `User.leaves` 替代单一 `total_energy`，`EnergyRecord.resource_type` 区分，`ShopItem.cost_resource` 决定扣哪种资源；③ 日记加 `visibility` / `category` 字段，情绪日历 `mood_emoji` 统一为 emoji 字符；④ 树洞文件式聊天历史 `data/chats/{user_id}/{session_id}.json`；⑤ 五音疗愈盘独立为顶级模块（`/healing` 路由）+ 古琴弹西洋曲谱子菜单（`musics.is_western_score` 列 + `/music/western` 路由）；⑥ pre-commit 5 项 checklist 正式化（Pydantic Out / `_migrate_legacy_columns` / `constants.py` / `.env.example` / README+HANDOFF 速查表）。详见 §1.1.7。关键词 `双资源` / `露水` / `落叶` / `UserFlower` / `Notification` / `ProfileView` / `古琴弹西洋曲谱` / `visibility` / `树洞` / `漂流瓶社交` / `五音疗愈盘` / `pre-commit 5 项` 在 6 份文档中都要出现。

> 🔒 **2026-07-28 v2.3.2 start.py 默认生产模式 + 自动构建简化**：`python start.py` 默认行为再次变更——**默认走生产模式**（FastAPI :5000 单进程，前后端不再一起起），需 `static/dist/` 已构建（不存在则自动 `npm install + npm run build`）。**自动构建仅检测 `static/dist/index.html` 存在性**（`dist 存在检测`），不再比较 `frontend/src/` 与 `static/dist/` 文件修改时间。**开发需显式 `python start.py --dev`**（Vite :5000 HMR + FastAPI :5001 API，前后端一起起的「应用模式」）。`--prod` 改为兼容别名（默认就是生产模式，加不加效果一样）。§1.2 开发/生产模式切换的端口策略更新：默认 → 生产模式（FastAPI :5000，dist 不存在则自动构建）；`--dev` → 应用模式（Vite :5000 + FastAPI :5001）。关键词 `默认生产模式` / `dist 存在检测` / `自动构建` / `--dev` / `应用模式` / `v2.3.2` 在 6 份文档中都要出现。

> 🔒 **2026-07-30 v2.3.3 Safari 兼容性修复（3D 上下文恢复 + emoji 跨浏览器一致）**：① §1.1.6 视觉组件群加 **Safari 兼容**增强——[utils/visual.js](../../frontend/src/utils/visual.js) **`hasWebGL` 重写**（区分 WebGL1/2 + 检测扩展 + max texture size）+ 新增 `getWebGLCaps()` / `isSafari()` / `isIOS()` 工具函数；[utils/three-helpers.js](../../frontend/src/utils/three-helpers.js) 添加 `webglcontextlost` / `webglcontextrestored` 事件监听处理 **WebGL 上下文丢失**（iOS Safari 切后台→前台触发）；[HeroScene.vue](../../frontend/src/components/HeroScene.vue) **iOS 降级**（**Bloom 降级**：iOS 关闭 UnrealBloomPass；**PMREM 降级**：iOS PMREM 256→128、阴影 2048→1024、dpr 上限 2→1.5；老 iOS 缺 `EXT_color_buffer_half_float` 扩展时关闭 PMREM + Bloom）。② 新建 [EmojiIcon.vue](../../frontend/src/components/EmojiIcon.vue) 组件，使用 **Iconify** + `@iconify-json/twemoji` 离线 **SVG emoji**，确保 **跨浏览器一致**（解决 Safari Apple Color Emoji vs 系统 emoji 字体差异），替换 AppLayout.vue + ProfileView.vue 所有 emoji。关键词 `Safari 兼容` / `WebGL 上下文丢失` / `webglcontextlost` / `iOS 降级` / `EmojiIcon` / `Iconify` / `twemoji` / `SVG emoji` / `跨浏览器一致` / `hasWebGL 重写` / `getWebGLCaps` / `isSafari` / `isIOS` / `Bloom 降级` / `PMREM 降级` / `v2.3.3` 在 6 份文档中都要出现。

> 🔒 **2026-08-10 v2.4.0 UI/UX 大改 + 一天多条心情 + 头像/昵称编辑 + 花坊扩充**：① §1.1.7.1 六大四字名板块表中'落叶画坊'改名'花坊'（[HomeView.vue](../../frontend/src/views/HomeView.vue) 模块名更新）；② §4.2 关键表字段 `mood_checkins` 唯一约束移除（支持**一天多条心情**，SQLite 重建表方式）；③ §1.1.8 新增 v2.4.0 架构要点节——头像/昵称编辑流程（`User.avatar` + `PATCH /api/profile` + `ProfileUpdateIn` + **头像同步树洞**）+ 一天多条心情数据模型（`mood_checkins` 唯一约束移除 + `add_checkin` + `get_today_moods` + 30 天趋势**平均分**）+ 花坊双资源经济扩充（`DEFAULT_SHOP_ITEMS` 27 件：12 花种 + 9 装扮 + 6 徽章；'古琴初学者' → '琴音知音' + **每板块徽章**）；④ §1.1.7.3 花田 AI 显示基于实际种花情况（没种花不显示）；⑤ 心语树洞 AI 系统提示词 **humanize**（更接地气、像朋友聊天）；⑥ 首页文案 '潮声不止，心安自屿' + 删'今日打卡'板块 + '漂流日记'入口统一；⑦ **静屿使用指南**（7 个模块详细介绍）+ **露水累加修复**（写日记和留言鼓励后正确发放露水）。关键词 `v2.4` / `潮声不止心安自屿` / `花坊` / `一天多条心情` / `mood_checkins 唯一约束移除` / `add_checkin` / `get_today_moods` / `平均分` / `humanize` / `琴音知音` / `每板块徽章` / `User.avatar` / `PATCH /api/profile` / `ProfileUpdateIn` / `头像同步树洞` / `静屿使用指南` / `露水累加修复` 在 6 份文档中都要出现。

> 🔒 **2026-08-10 v2.4.1 情绪日历罗素情绪环模型四象限图表**：① §1.1.9 新增 v2.4.1 架构要点节——情绪环模型四象限图表数据流（`CIRCUMPLEX_EMOTIONS` 数组 20 种情绪带 `valence`/`arousal` 坐标 → `emotionPosition(emotion)` 转 `left%`/`top%` 百分比定位 → 点击 emoji 弹详情卡片 → `moodCounts` computed 从 `checkins` 统计本月各心情次数 → `totalCheckins` 显示本月总打卡数）；② [MoodCalendarView.vue](../../frontend/src/views/mood/MoodCalendarView.vue) 移除 30 天趋势柱状图（`trendBars` computed / `scoreColor` 函数 / `.trend-section` 模板 / `.trend-bar` 样式全部删除），新增罗素情绪环模型四象限图表（横轴效价 Valence 左消极→右积极 / 纵轴唤醒度 Arousal 下低唤醒→上高唤醒 / 四象限 Q1 积极+高唤醒 · Q2 消极+高唤醒 · Q3 消极+低唤醒 · Q4 积极+低唤醒）；③ 7 种已追踪情绪（ecstatic/happy/calm/tired/anxious/angry/sad）映射后端 [MOOD_INFO](../../app/utils/constants.py) 有真实打卡数据（边框高亮 + 次数角标）+ 13 种参考情绪帮助用户理解位置（点击显示「该情绪暂未开放打卡记录」）；④ `fetchTrend` 仍调用（为 `currentStreak` 连续打卡天数显示），但 `trend` 数据不再用于渲染。关键词 `v2.4.1` / `Russell情绪环模型` / `Circumplex Model` / `四象限图表` / `效价Valence` / `唤醒度Arousal` / `CIRCUMPLEX_EMOTIONS` / `emotionPosition` / `moodCounts` / `20种情绪` / `点击交互` / `本月出现次数` 在 6 份文档中都要出现。

> 🔒 **2026-08-13 v2.4.2 整体架构优化与冗余清理（维护性清理版本）**：本次为维护性清理版本，**无功能变化 / 无数据库迁移 / 无新依赖**，7 项改动专注代码瘦身与架构一致性对齐。① **死模板清理**（`死模板清理`）：[templates/](../../templates/) 下 Vue 3 SPA 迁移前遗留的 15 个旧 Jinja2 SSR 模板（`base/_nav/_toast/index/login/register/music_list/diary_write/diary_detail/my_bottles/pick_bottle/mood_calendar/garden/shop/ai_chat.html`）+ `templates/partials/` 空目录全部删除；**仅保留** [templates/admin/](../../templates/admin/)（[admin_pages.py](../../app/routers/admin_pages.py) 仍使用 Jinja2 SSR，与 Vue SPA 隔离的后台架构不变）。② **死页面脚本清理**（`死页面脚本`）：[static/js/pages/](../../static/js/pages/) 下 10 个非 admin 脚本（`ai_chat/auth/diary/diary_detail/home/mood_calendar/music/my_bottles/pick/shop.js`）删除——仅被死模板引用，迁移后已无入口，前端架构「Vue 3 SPA + Vite」不受影响。③ **[app/main.py](../../app/main.py) 版本号 1.0.0 → 2.4.2**（`版本号对齐`）：与 git tag / README badge 对齐。④ **[app/main.py](../../app/main.py) `EXT_TO_MIME` 删除重复 `.webp` 条目**（`EXT_TO_MIME`）。⑤ **过时端口注释修复**（`过时注释`）：[app/routers/pages.py](../../app/routers/pages.py) / [frontend/vite.config.js](../../frontend/vite.config.js) / [static/js/app.js](../../static/js/app.js) 中 `:5173 → :5000`（Vite）/ `:5000 → :5001`（FastAPI 开发），与 §1.2 端口策略一致。⑥ **新增 5 个五音封面 SVG**（`SVG封面`）：[static/img/cover_gong.svg](../../static/img/cover_gong.svg) / `cover_shang.svg` / `cover_jue.svg` / `cover_zhi.svg` / `cover_yu.svg`，颜色取自 [app/utils/constants.py](../../app/utils/constants.py) `YIN_INFO`，修复 [app/seed.py](../../app/seed.py) 引用的缺失资源。⑦ **[app/routers/admin_pages.py](../../app/routers/admin_pages.py) admin_users N+1 查询优化**（`N+1优化` / `GROUP BY`）：原 for 循环内 3 个 COUNT/用户 × 50 用户 = 151 次查询 → 1 次查用户 + 3 个 `GROUP BY` 聚合 + 字典拼接 = 4 次查询。**不动**：[static/css/](../../static/css/) / [static/js/app.js](../../static/js/app.js) / [static/audio/](../../static/audio/) / [templates/admin/](../../templates/admin/) / [config.py](../../config.py) / [app/database.py](../../app/database.py) / [requirements.txt](../../requirements.txt)。关键词 `v2.4.2` / `死模板清理` / `死页面脚本` / `N+1优化` / `GROUP BY` / `SVG封面` / `EXT_TO_MIME` / `版本号对齐` / `过时注释` 在 6 份文档中都要出现。

> 🔒 **2026-08-14 v2.4.3 花语文案焕新 + emoji 名称对齐 + 徽章奖励落叶 + 树洞三层回复 + 情绪日历空 bug 修复（内容运营 + Bug 修复版本）**：本次为内容运营 + Bug 修复版本，**无新依赖 / 不改后端模型结构 / 无需重建表**，专注文案打磨 / emoji 修正 / 资源死锁解除 / AI 回复质量提升。① **花种介绍统一为花语**（`花语化`）：[constants.py](../../app/utils/constants.py) `DEFAULT_SHOP_ITEMS` 12 种花种 description 全改为「花语：……」文案（薰衣草「等待爱情，安静与坚守」/ 郁金香「爱的告白，永恒的祝福」等）；② **emoji 与名称对齐**（`emoji对齐`）：薰衣草 💜→🪻 / 桂花🌾→改名「小麦」/ 银杏🍃→改名「青叶」/ 兰花+梅花🌸→合并改名「樱花」（删一留一去重）/ 白鹤🦩→改名「火烈鸟」/ 蓑衣🧥→改名「斗篷」；③ **动物装扮扩充**：新增「小鸟🐦」/「小鸭🦆」/「小狗🐶」三件装扮；④ **徽章奖励落叶打破死锁**（`落叶死锁解除`）：[constants.py](../../app/utils/constants.py) 新增 `BADGE_LEAF_REWARD=10`，[energy_service.py](../../app/services/energy_service.py) `check_achievements` 每解锁一个徽章额外发放 10 片落叶（返回 `new_badges` / `new_leaves` / `leaves_balance`），解决「没花没落叶」死锁；⑤ **废弃徽章删除**：seed.py 清理「古琴初学者」残留（含 GardenItem 引用）；⑥ **花田主人→花间客**改名（太直白→文艺）+ **花坊→落叶花坊**改名；⑦ **情绪日历空白 bug 修复**（`情绪日历空bug`）：[MoodCalendarView.vue](../../frontend/src/views/mood/MoodCalendarView.vue) 空单元格访问 `cell.moodKeys.length` 抛 TypeError 导致整页空白，加可选链 `cell.moodKeys?.length`；⑧ **花田 AI 基于实际种花**（`花田AI`）：[GardenView.vue](../../frontend/src/views/garden/GardenView.vue) `<FlowerField v-if="flowers.length > 0">`，没种花不显示 3D 花田与 AI 生成花朵；⑨ **岛上物件 emoji** + **首页 emoji 🏝️→🌊**（海浪，更贴合「静屿」海意）+ **漂流瓶 emoji 🍶→🏺**（双耳瓶，与「拾瓶旅人」徽章🏺对齐）；⑩ **树洞 AI 三层回复重写**（`树洞三层回复`）：[ai_service.py](../../app/services/ai_service.py) `SYSTEM_PROMPT_TREEHOLE` 重写为「① 先接住情绪（1 句用自己的话点出情绪）→ ② 给安慰或新视角（1-2 句）→ ③ 给具体可操作小建议或问题（1-2 句）」，解决旧版「只重复消极情绪、无用共鸣」问题；⑪ **seed 改名迁移**（`改名迁移`）：`RENAME_MAP` 旧名→新名 + 重复项合并去重；⑫ 各 router（mood/diary/music/ai）在原有动作后调用 `check_achievements` 并把 `leaves_balance` / `new_badges` 透传前端，前端各 View（MoodCalendarView/DiaryWriteView/PickBottleView/AIChatView/MusicDetailView）更新落叶余额 + 徽章解锁 toast。关键词 `v2.4.3` / `花语化` / `emoji对齐` / `BADGE_LEAF_REWARD` / `落叶死锁解除` / `树洞三层回复` / `情绪日历空bug` / `花田AI` / `改名迁移` / `落叶花坊` / `花间客` / `小麦` / `青叶` / `樱花` / `火烈鸟` / `斗篷` / `小鸟小鸭小狗` 在 6 份文档中都要出现。

> 🔧 **2026-08-15 v2.4.3 补丁（首页滚动提示可点击）**：[HomeView.vue](../../frontend/src/views/HomeView.vue) Hero 底部「向下」滚动提示原为 `pointer-events:none` 的 `<div>`（用户点击无反应），改为 `<button>` + `scrollToModules()` 点击平滑滚动到「岛上各处」板块，文案「向下沉入海面」→「向下，遇见岛上的去处」，hover 颜色反馈。纯前端交互修复，需重新 `npm run build`。

> 🔒 **2026-08-15 v2.4.4 情绪日历透明修复 + 旧版日记迁移 + mood_checkins 主键重建 + 头像图片上传 + 落叶花坊文案打磨（Bug 修复 + 功能增强版本）**：本次为 Bug 修复 + 功能增强版本，专注修复用户反馈的可见性 / 数据完整性 / 表结构问题 + 新增头像上传功能。① **[BUG FIX] 情绪日历 emoji 透明**（`情绪日历透明修复`）：[MoodCalendarView.vue](../../frontend/src/views/mood/MoodCalendarView.vue) GSAP 动画设置了 `opacity:0` 导致心情选择按钮几乎不可见，已移除该属性。② **[BUG FIX] 旧版日记无内容**（`旧版日记迁移`）：旧版加密日记 `content` 字段为空（`content_encrypted` 是假占位符），数据库迁移自动填入提示文本「（这段日记来自旧版本，内容已无法读取）」。③ **[BUG FIX] mood_checkins 表缺失 PRIMARY KEY**（`mood_checkins 主键重建`）：v2.4 的迁移用了 `CREATE TABLE AS SELECT` 导致 `mood_checkins` 表丢失主键和自增，批量打卡时 `db.flush()` 报 `NULL identity key` 错误（500）。已重建表（`id INTEGER PRIMARY KEY AUTOINCREMENT` + FK + 索引），数据完整迁移——**架构启示：SQLite 用 `CREATE TABLE AS SELECT` 重建表会丢失主键 / 自增 / 约束 / 索引，必须用 `CREATE TABLE` 显式定义 schema 后 `INSERT INTO ... SELECT *` 迁移数据**。④ **[BUG FIX] avatar 字段长度**（`avatar 字段长度`）：[User.avatar](../../app/models/user.py) 原为 `String(16)`，无法存储图片上传后的 URL 路径（如 `/static/uploads/avatars/1_1234567890.jpg`）。已改为 `String(255)`，[ProfileUpdateIn](../../app/schemas/profile.py) schema 同步调整为 `max_length=255`——**架构启示：字段长度变更必须 model + schema 同步**。⑤ **[FEATURE] 头像支持图片上传**（`头像图片上传`）：新增 `POST /api/profile/avatar` 端点，支持 JPG/PNG/WebP/GIF（≤2MB），存储到 `static/uploads/avatars/`（目录不存在自动创建）；[ProfileView.vue](../../frontend/src/views/profile/ProfileView.vue) 增加上传按钮（支持拍摄/相册选择），[AIChatView.vue](../../frontend/src/views/ai/AIChatView.vue) 支持图片头像渲染——**架构要点：头像字段同时支持 emoji 字符与图片 URL 路径，前端渲染时按是否以 `/static/uploads/` 开头判断**。⑥ **[IMPROVEMENT] 落叶花坊花朵介绍**（`花朵介绍`）：移除「花语：」前缀，只保留完整花语。⑦ **[IMPROVEMENT] 徽章落叶奖励分级**（`徽章落叶分级`）：按徽章 trigger 分级设置落叶奖励（streak_7=7, listen_10=10, pick_10=10, flower_10=10, chat_20=15, diary_30=20, 默认=10），替代原来统一的固定值——**架构要点：`BADGE_LEAF_REWARD` 由固定常量改为按 trigger 分级的字典 / 函数**。⑧ **[IMPROVEMENT] 情绪日历使用指南更新**（`情绪日历指南`）：介绍改为罗素情绪环模型（Russell's Circumplex Model）四象限说明。⑨ **[IMPROVEMENT] 岛上物件 emoji**（`岛上物件 emoji`）：🎁 → 🧳（行李箱）。⑩ **[IMPROVEMENT] 通知 emoji 统一**（`通知 emoji 统一`）：漂流瓶回复通知的 emoji 统一为 💛（黄色爱心）。关键词 `v2.4.4` / `情绪日历透明修复` / `旧版日记迁移` / `mood_checkins 主键重建` / `avatar 字段长度` / `头像图片上传` / `花朵介绍` / `徽章落叶分级` / `情绪日历指南` / `岛上物件 emoji` / `通知 emoji 统一` 在 6 份文档中都要出现。

---

> 🔒 **2026-08-16 v2.4.5 情绪日历 30 天趋势柱状图恢复 + 罗素情绪环显示修复 + 头像相册选择 + 通知空状态 emoji 统一（Bug 修复版本，纯前端）**：本次为 Bug 修复版本，**纯前端改动（3 个文件），无后端改动 / 无数据库迁移 / 无新依赖**。① **[BUG FIX] 情绪日历打卡后柱状图不显示**（`30天趋势柱状图恢复`）：v2.4.1 将「30 天趋势柱状图」替换为罗素情绪环时整体删除了柱状图板块。本次恢复该板块并与罗素情绪环**并存**（架构要点：趋势视图 `trend` computed 数据流恢复渲染，柱高 = 当日心情平均分（1-5 评分，一天多条取平均），柱色取当日主心情颜色渐变，柱顶悬浮当日主心情 emoji，未记录日 3px 浅色占位柱，底部首尾日期轴）——**架构启示：替换式重构若用户已形成使用习惯，应保留旧视图与新视图并存，而非整体删除**。② **[BUG FIX] 罗素情绪环模型不显示**（`罗素情绪环显示修复`）：GSAP `from()` 动画残留 `opacity:0` / `scale:0` 初始态，动画被中断（切后台 / 路由切换）时元素**永久卡在不可见状态**（与 v2.4.4「透明 bug」同类根因，当时只修了心情按钮一处，环模型区域漏修）。修复：全部入场动画（`.mood-header` / `.mood-picker__btn` / `.calendar-nav` / `.calendar-cell` / `.circumplex-section` / `.circumplex-emotion`）**只保留位移动画（`y`），不设置 `opacity` / `scale` 初始态**——**架构铁律：GSAP 入场动画禁用 `opacity:0` / `scale:0` 初始态，动画中断残留会导致元素永久不可见**。③ **[BUG FIX] 头像只能拍照不能从相册选择**（`头像相册选择`）：[ProfileView.vue](../../frontend/src/views/profile/ProfileView.vue) 头像上传 `<input type="file">` 带 `capture="environment"` 属性，移动端强制调起相机；移除 `capture`（保留 `accept="image/*"`）后弹出系统「拍照 / 从相册选择」选择框——**架构要点：`capture` 属性只在「仅相机」场景使用，通用图片上传禁用**。④ **[BUG FIX] 通知空状态 emoji 错误**（`通知空状态emoji`）：[NotificationsView.vue](../../frontend/src/views/notification/NotificationsView.vue) 空状态 emoji 🌙 → 💛，与 v2.4.4「通知 emoji 统一 💛」对齐。关键词 `v2.4.5` / `30天趋势柱状图恢复` / `罗素情绪环显示修复` / `头像相册选择` / `通知空状态emoji` 在 6 份文档中都要出现。

---

> 🔊 **2026-08-16 v2.4.6 五音音频真实化（静音占位 → Karplus-Strong 合成古琴拨弦，架构无变化）**：本次为历史遗留清理版本，**后端架构 / 前端架构均无变化**，只动了静态资源与数据层。① **静态资源层**：`static/audio/` 由 5 个假 MP3 占位（各 5338 字节静音帧）换成 5 个真实 WAV（Karplus-Strong 拨弦物理建模合成，五声调式各 78 秒 / 22050Hz / 16bit / mono，3.4MB/个）——FastAPI StaticFiles 按扩展名自动发 `audio/wav` MIME，浏览器 `<audio>` 原生支持，**前端零改动**（audio_url 全来自 DB）；② **数据层**：[database.py](../../app/database.py) `_migrate_legacy_columns()` 延续「无 Alembic 轻量迁移」模式（见 HANDOFF §2），musics 表新增幂等数据迁移 `audio_url .mp3→.wav`（`REPLACE()` + `LIKE '%.mp3'` 条件，重启即生效）；[seed.py](../../app/seed.py) 种子直写 `.wav` + 静音 RIFF 兜底；③ **音频生成独立成脚本**：[scripts/generate_audio.py](../../scripts/generate_audio.py) 纯标准库（random/struct/wave）零依赖、固定随机种子可复现——**架构要点：音频是「生成产物」而非「二进制资产」，进仓库的是生成结果，源是脚本，任何时候 `python scripts/generate_audio.py` 一键重生成**。关键词 `v2.4.6` / `五音音频合成` / `Karplus-Strong` / `audio_url切wav` 在 6 份文档中都要出现。

---

> 🔁 **2026-08-16 v2.4.7 音频方案回退（架构恢复至 v2.4.5 状态，待接入真实曲库）**：v2.4.6 的 Karplus-Strong 合成 wav 方案上线试听被用户否决（「随机拨弦声 ≠ 成曲」——合成音频无旋律结构，起不到疗愈作用），**全量回退，架构回到 v2.4.5**：① 静态资源层恢复 `static/audio/*.mp3` 5 个静音占位（各 5338 字节），`audio_url` 仍按 yin_type 映射 5 个共享文件（22 首曲目）；② 数据层迁移反转为幂等 `.wav→.mp3`（[database.py](../../app/database.py)，跑过 v2.4.6 的库重启自动切回）；③ 删除 `scripts/generate_audio.py`（音频不再是「生成产物」）。**接入真实曲库的方式（零代码）**：用户下载真实古琴音频命名为 `gong/shang/jue/zhi/yu.mp3` 覆盖 `static/audio/` 同名文件即可——audio_url 存 DB、按 yin 映射的架构不变。**教训（写给架构决策）**：音色合成解决的是「有声音」，疗愈音乐需要的是「成曲」（旋律结构 / 乐句呼应 / 起承转合），后者只能来自真实录音或真实作曲，架构选型时不要用算法合成糊弄音乐需求。关键词 `v2.4.7` / `音频方案回退` / `恢复mp3占位` / `待接入真实曲库` 在 6 份文档中都要出现。

---

> 🎵 **2026-08-16 v2.4.8 曲目独立音频架构（audio_url 粒度从五音提升到曲目）**：本次为架构修正——**`audio_url` 的粒度（五音，5 个共享文件）与前端展示粒度（曲目，22 首）不一致**，导致用户无法按曲放置真实音频。① **URL 结构**：`audio_url` 从 `/static/audio/{五音}.mp3` 改为 `/static/audio/tracks/{曲名}.mp3`（22 个文件，中文曲名直接命名——浏览器自动 percent-encode，Starlette StaticFiles 解码按 UTF-8 匹配，git 原生支持 UTF-8 文件名，全链路无障碍）；② **数据层**：[database.py](../../app/database.py) musics 表幂等迁移**按 title 拼接**新路径（`'/static/audio/tracks/' || title || '.mp3'`，一条 SQL 重定向 22 行，已在 tracks/ 的行不受影响）；[seed.py](../../app/seed.py) `SEED_MUSIC` 驱动 audio_url 与逐曲占位；③ **前端零改动**：播放器本就 DB 驱动（`<audio :src="currentMusic.audio_url">`），粒度变更对前端透明。**架构教训**：静态资源 URL 的粒度必须对齐展示实体（曲目），不能按分类（五音）偷懒共享——否则内容接入（每曲放真实音频）直接被卡死。关键词 `v2.4.8` / `曲目独立音频` / `audio_url迁移tracks` / `五音共享废弃` 在 6 份文档中都要出现。

---

## 1. 总体架构

> **2026-07-19 v2.0 全站 Vue 3 重构**：前端从 Jinja2 SSR + 原生 JS 迁移到 Vue 3 SPA + Vite 工程化，后端 FastAPI 简化为纯 API + SPA fallback。
>
> **2026-07-19 v2.0.1 端口策略调整**：开发模式 Vite 占 :5000（用户入口）+ FastAPI 改 :5001（API），避免 FastAPI 反代 Vite 内部路径含特殊字符失败（详见 [HANDOFF §6.16](../../HANDOFF.md)）。**用户始终访问 :5000**，由 [start.py](../../start.py) 自动切换。

```
┌──────────────────────────────────────────────────────────────────┐
│                       浏览器（前端）                              │
│                                                                  │
│  开发模式：http://127.0.0.1:5000/  ← 用户始终访问 :5000           │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  Vite dev server (:5000)  ← 用户入口，HMR 热更新            │  │
│  │  ├─ Vue 3 SPA 热更新（<script setup> + HMR）              │  │
│  │  ├─ Vue Router 4 客户端路由                                │  │
│  │  ├─ Pinia 状态管理                                         │  │
│  │  ├─ Tailwind CSS + GSAP + @vueuse/motion + Three.js        │  │
│  │  │  └─ FlowerField.vue（异步加载，3D 花田）                │  │
│  │  └─ axios → proxy /api、/static、/admin、/docs、           │  │
│  │            /openapi.json → FastAPI :5001                   │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  生产模式：http://127.0.0.1:5000/  ← 用户始终访问 :5000           │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  FastAPI 直接服务 static/dist/  ← Vite 不运行                │  │
│  │  ├─ index.html + JS/CSS chunk（Vue 3 build 产物）          │  │
│  │  ├─ 静态资源走 EXT_TO_MIME 映射（.js/.css/.woff2 等）       │  │
│  │  └─ SPA fallback 兜底未匹配 GET → index.html               │  │
│  └────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
                                  ↑
                                  │ HTTP JSON（/api/*）+ cookie session
                                  ↓
┌──────────────────────────────────────────────────────────────────┐
│  开发模式：FastAPI（uvicorn :5001，由 start.py 设 QI_PORT=5001）  │
│  生产模式：FastAPI（uvicorn :5000，从 .env 读 QI_PORT）            │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────────┐  │
│  │ routers/api* │  │ SPA fallback │  │  StaticFiles mount     │  │
│  │ (返回 JSON)  │  │ (返回 HTML)  │  │  /static/*             │  │
│  │  + admin     │  │  排除 /api/  │  │  含 dist/index.html    │  │
│  │  + ai        │  │  /static/    │  │                        │  │
│  │              │  │  /admin      │  │                        │  │
│  │              │  │  /docs       │  │                        │  │
│  │              │  │  /openapi    │  │                        │  │
│  │              │  │  开发态返回  │  │                        │  │
│  │              │  │  提示页引导  │  │                        │  │
│  │              │  │  访问 Vite   │  │                        │  │
│  └──────┬───────┘  └──────────────┘  └────────────────────────┘  │
│         │                                                        │
│         │       ┌────────────────┐                               │
│         │       │  services/*    │  ← 业务逻辑层                  │
│         │       └────────┬───────┘                               │
│         │                ↓                                        │
│         │       ┌─────────────────┐                               │
│         │       │  models/*      │  ← ORM                         │
│         │       └────────┬────────┘                               │
│         │                ↓                                        │
│         │       ┌─────────────────┐                               │
│         │       │  SQLite        │                               │
│         │       │  data/healing.db│                               │
│         │       └─────────────────┘                               │
│         │                                                        │
│         │  ┌─────────────────────────────────────────────────┐   │
│         │  │ pages.py（4 个 302 重定向，兼容旧书签）          │   │
│         │  │  /mood→/calendar、/mood-calendar→/calendar       │   │
│         │  │  /my-bottles→/diary、/pick→/diary/pick           │   │
│         │  └─────────────────────────────────────────────────┘   │
│         │                                                        │
│         └─ [admin] → admin_pages.py → templates/admin/* (SSR)   │
│              → admin.py → /api/admin/* → services/models         │
└──────────────────────────────────────────────────────────────────┘
```

**单一进程承担 3 个角色**（生产模式）：API + SPA fallback + 静态资源。这是有意为之的简化（见 [HANDOFF §2](../../HANDOFF.md) + [HANDOFF §5.8](../../HANDOFF.md) 前端选型决策）。

**开发模式 = 双进程**：Vite :5000（前端 + HMR）+ FastAPI :5001（API），由 [start.py](../../start.py) 自动起两个；用户**只**访问 :5000，Vite proxy 转发 API 请求到 :5001。详见 [§1.2 开发/生产模式切换](#12-开发生产模式切换2026-07-19-v20-加)。

**前台 = Vue 3 SPA**（[`frontend/`](../../frontend/)），**后台 = Jinja2 SSR**（[templates/admin/](../../templates/admin/)）：后台仍用 SSR 是有意为之（独立样式、独立隔离、管理工具不需要 SPA 体验，详见 [HANDOFF §5.8](../../HANDOFF.md)）。

**秘密后台**（[app/routers/admin.py](../../app/routers/admin.py) + [app/routers/admin_pages.py](../../app/routers/admin_pages.py)）挂在 `QI_ADMIN_PATH_PREFIX`（默认 `/admin`）下，**完全独立于前台 Vue SPA**：不共享 AppLayout，不共享 Tailwind 样式，不放任何前台链接（见 [§6.5](#65-秘密后台架构)）。

---

## 1.1 前端架构（Vue 3 SPA，2026-07-19 v2.0 加）

> 设计原则：**「组件化复用 + 客户端路由 + 集中状态 + 工程化构建」** —— 从原生 HTML/CSS/JS + Jinja2 SSR 迁移到 Vue 3 SPA，解决「一页一个 JS、状态散落、路由靠后端 302」的膨胀问题。

### 1.1.1 技术栈

| 层 | 选型 | 文件 | 说明 |
|---|---|---|---|
| 框架 | Vue 3 `<script setup>` | [frontend/package.json](../../frontend/package.json) | ^3.4，组合式 API |
| 构建 | Vite 5 | [frontend/vite.config.js](../../frontend/vite.config.js) | dev HMR + build Rollup；dev 监听 :5000（用户入口）；dev proxy /api、/static、/admin、/docs、/openapi.json → FastAPI :5001（详见 [§1.2](#12-开发生产模式切换2026-07-19-v20-加)） |
| 路由 | Vue Router 4 | [frontend/src/router/index.js](../../frontend/src/router/index.js) | 13 条路由，`meta.requiresAuth` 守卫，404 catch-all |
| 状态 | Pinia 2 | [frontend/src/stores/user.js](../../frontend/src/stores/user.js) | user store；cookie session 模式，**不存 token**，只缓存 user 对象到 localStorage |
| 样式 | Tailwind CSS 3.4 | [frontend/tailwind.config.js](../../frontend/tailwind.config.js) | 治愈系色彩 token（mist/ink/五音色/accent）+ 动画（breathe/float/fade-up） |
| 动效 | GSAP 3.12 + @vueuse/motion 2.2 | 各 .vue 视图 | 入场 stagger + 呼吸动效；`prefers-reduced-motion` 自动降级 |
| 3D | Three.js 0.168 | [frontend/src/components/FlowerField.vue](../../frontend/src/components/FlowerField.vue) | 治愈系 3D 花田场景（60 朵花 × 5 瓣 = 300 InstancedMesh），异步加载（详见 [§1.1.5](#115-3d-花田组件-flowerfieldvue2026-07-19-v201-加)） |
| HTTP | axios 1.7 | [frontend/src/api/index.js](../../frontend/src/api/index.js) | `baseURL=/api`，`withCredentials=true`，401 自动跳 `/login` |

### 1.1.2 13 个路由（[frontend/src/router/index.js](../../frontend/src/router/index.js)）

| 路径 | 视图 | requiresAuth | 说明 |
|---|---|---|---|
| `/` | HomeView.vue | 否 | 首页：Hero + 五音入口 + 模块卡 + GSAP 入场 |
| `/login` | auth/LoginView.vue | 否 | 登录（nickname + 密码 + 密码切换显示） |
| `/register` | auth/RegisterView.vue | 否 | 注册 |
| `/music` | music/MusicListView.vue | 否 | 5 音列表 + AI 帮我选音 |
| `/music/:yin` | music/MusicDetailView.vue | 否 | 单音曲目 + 底部播放器 + 听完 90% 调 /api/music/listen-complete |
| `/diary` | diary/DiaryListView.vue | 是 | 时间线 + Web Crypto 解密 |
| `/diary/write` | diary/DiaryWriteView.vue | 是 | 写日记 + 心情 emoji + 加密 |
| `/diary/pick` | diary/PickBottleView.vue | 是 | 拾瓶 + AI 鼓励语 |
| `/calendar` | mood/MoodCalendarView.vue | 是 | 日历网格 + 30 天趋势 + AI 治愈语 |
| `/ai-chat` | ai/AIChatView.vue | 是 | 多轮对话，历史只在内存 |
| `/garden` | garden/GardenView.vue | 是 | 能量/来源/物品/流水 |
| `/shop` | garden/ShopView.vue | 是 | 按 item_type 分组 + 兑换 |
| `/:pathMatch(.*)*` | NotFoundView.vue | 否 | 404 catch-all |

### 1.1.3 调用流（登录 → 写日记）

```
浏览器                                FastAPI
  │                                      │
  │ POST /api/auth/login                 │
  │ {nickname, password}                 │
  │ Cookie: (none)                       │
  ├─────────────────────────────────────→│
  │                                      │ 1. bcrypt.verify(password, hash)
  │                                      │ 2. 签 qi_session cookie
  │                                      │ 3. 返回 user 对象（不是 {access_token, user}）
  │ ←─ 200 + Set-Cookie + {user}         │
  │                                      │
  │ Pinia userStore.setUser(user)        │
  │ localStorage.setItem('user', user)   │
  │                                      │
  │ POST /api/diary                      │
  │ Cookie: qi_session=...               │
  │ {content_encrypted, mood_type, ...}  │
  ├─────────────────────────────────────→│
  │                                      │ 1. get_current_user 鉴权
  │                                      │ 2. 写入 diaries 表（密文）
  │                                      │ 3. 能量 +2 阳光（write_diary）
  │ ←─ 201 {id, ...}                     │
```

**关键点**：
1. cookie session（不是 JWT token）—— Vue 3 重构**不变**鉴权机制
2. 前端 userStore 只缓存 user 对象到 localStorage，**不存 token**——避免 XSS 拿 token 的风险
3. axios `withCredentials=true` 让浏览器自动带 cookie
4. 401 响应由 axios 拦截器自动跳 `/login`

### 1.1.4 Web Crypto 日记加密（与旧 SSR 模式一致）

```
浏览器（Vue 3 视图）              FastAPI
  │                                  │
  │ 用户输入密码 + 日记明文           │
  │                                  │
  │ 1. 从 userStore 取 encryption_salt│
  │ 2. PBKDF2(password + salt)       │
  │    → Fernet 密钥                  │
  │ 3. Fernet 加密明文 → 密文         │
  │                                  │
  │ POST /api/diary                  │
  │ {content_encrypted: "gAAAAA..."} │
  ├─────────────────────────────────→│
  │                                  │ 直接存密文，不接触明文
  │ ←─ 201                           │
```

服务端**永不**接触明文日记——这条端到端加密边界 Vue 3 重构后**依然成立**（[HANDOFF §5.1](../../HANDOFF.md)）。

### 1.1.5 3D 花田组件（FlowerField.vue，2026-07-19 v2.0.1 加）

> 设计原则：**「治愈系视觉冲击 + 性能可控 + 按需加载」** —— 在精神花园页顶部用 Three.js 渲染一片真 3D 花田，弥补 v2.0 首屏「装饰性 emoji 平铺」的视觉单薄问题；同时通过 InstancedMesh + 异步导入把性能开销压到最小。

**文件**：[frontend/src/components/FlowerField.vue](../../frontend/src/components/FlowerField.vue)

**嵌入位置**：[frontend/src/views/garden/GardenView.vue](../../frontend/src/views/garden/GardenView.vue) 顶部 hero 区，高 380px，圆角 + 阴影包裹，下方叠加「移动鼠标，看花田随风摆动」提示文案。

```vue
// GardenView.vue
import { defineAsyncComponent } from 'vue'
const FlowerField = defineAsyncComponent(() =>
  import('@/components/FlowerField.vue')
)
```

**核心实现要点**：

| 维度 | 实现 | 说明 |
|---|---|---|
| 性能 | `THREE.InstancedMesh` 单次 draw call 渲染全部花瓣 | 60 朵花 × 5 瓣 = 300 个 instance，性能与视觉平衡点 |
| 加载策略 | `defineAsyncComponent(() => import('three'))` | Three.js (~600KB) 按需加载，不进首屏包；加载中显示「🌿 花田正在生长…」占位 |
| Vue 响应式 | Three.js 对象用 `shallowRef` 持有 | 避免被 Vue 深度代理拖累性能 |
| 配色 | 5 种治愈系色：藕粉 `#E8B8C5` / 淡黄 `#E8D5A8` / 青绿 `#A8C5A0` / 雾蓝 `#A8B8C5` / 纯白 `#FAF6F2` | 与全站 CSS token 一致 |
| 花瓣几何 | `THREE.Shape` + bezierCurveTo 自定义圆润花瓣形 + `ShapeGeometry` | 5 片花瓣绕花蕊均匀分布（72° 间隔） |
| 花蕊 | `THREE.Points` 单独渲染 60 个暖黄小点 | 比 InstancedMesh 更轻 |
| 氛围 | `THREE.Fog(0xF9F6F0, 8, 28)` + 远处 80 个漂浮光点（`Points`） | 远处花朵融入雾色，光点缓缓上升 |
| 动画 | 绽放（错峰从地面升起 + 缩放）+ 风摆动（`sin(elapsed * 1.2 + phase)`）+ 摄影机自动呼吸 + 鼠标跟随 | `requestAnimationFrame` 循环 |
| 资源释放 | `onBeforeUnmount` 释放 geometry / material / renderer + 移除 DOM | 避免切走后 WebGL 上下文泄漏 |

**为什么不用 CSS 3D / 简单 emoji 平铺**：
- CSS 3D 无法做 InstancedMesh 级别的实例化，300 个 DOM 节点会拖累首屏
- emoji 平铺缺乏景深和光影层次，被用户明确反馈「视觉单薄」
- Three.js 一次注入 + 异步加载，**首屏不增加 JS 体积**（Three.js 走单独 chunk，仅花园页加载）

**降级**：`onMounted` 异步 `import('three')` 失败时，`isLoading=true` 占位文案一直显示，不阻塞页面其他模块（能量卡 / 物品列表 / 流水正常渲染）。

**为什么 Three.js 0.168**：选择当时社区稳定版本；vite.config.js 的 `manualChunks` 把 `three` 单独打成 `three-vendor` chunk，避免和 vue/gsap 混在一起。

### 1.1.6 视觉增强组件群（v2.1 加，2026-07-20；v2.2 PBR 升级，2026-07-20）

> 设计原则：**「三层渐进增强 + 能力检测 + 异步加载 + 完整降级」** —— 在 FlowerField 3D 花田基础上，为全站加入 3D / 伪 3D 背景元素和动态视觉效果，提升治愈系沉浸感；同时**不能影响首屏性能**，且**必须为 3D 渲染能力有限的浏览器实现备用机制**。决策：用「CSS 永远启用 → Canvas2D 中量级 → Three.js 按需」三层独立可降级，配套 `utils/visual.js` 能力检测。
>
> **v2.2 PBR 升级**（2026-07-20）：4 个视觉组件全部升级到 PBR 渲染管线（`ACESFilmicToneMapping` + `SRGBColorSpace` + `PCFSoftShadowMap` + `RoomEnvironment` PMREM + `UnrealBloomPass`）；新增 [utils/three-helpers.js](../../frontend/src/utils/three-helpers.js) 集中 9 个共享 PBR 工具函数；新增 [SceneHint.vue](../../frontend/src/components/SceneHint.vue) 交互指引横幅 + [SceneControls.vue](../../frontend/src/components/SceneControls.vue) 视图控制工具栏，解决「用户不知道如何与 3D 元素交互」问题；所有 3D 场景统一 `OrbitControls`（拖拽旋转 + 滚轮缩放）+ `raycaster` 点击拾取。决策理由详见 [HANDOFF §5.11](../../HANDOFF.md)。

**v2.2 视觉文件群**（共 8 个，v2.3.3 加 EmojiIcon.vue）：

| 文件 | 角色 | 嵌入位置 | 降级路径 |
|---|---|---|---|
| [frontend/src/utils/visual.js](../../frontend/src/utils/visual.js) | 视觉能力检测（v2.3.3 Safari 兼容增强） | 被其他组件 import | 单次缓存检测结果，无降级（自身就是降级判断器）；v2.3.3 **hasWebGL 重写**（区分 WebGL1/2 + 检测扩展 + max texture size）+ 新增 `getWebGLCaps()` / `isSafari()` / `isIOS()` |
| [frontend/src/utils/three-helpers.js](../../frontend/src/utils/three-helpers.js) | **PBR 工具集（v2.2 加；v2.3.3 加上下文恢复）** | 被 HeroScene / FlowerField / AmbientBackground import | 9 个共享函数：createRenderer / createEnvironment / createPostProcessing / createOrbitControls / createKeyLight / createFillLight / createSoftSpriteTexture / disposeObject3D / disposeRenderer；v2.3.3 加 `webglcontextlost` / `webglcontextrestored` 事件监听处理 **WebGL 上下文丢失** |
| [frontend/src/components/AmbientBackground.vue](../../frontend/src/components/AmbientBackground.vue) | 全局氛围背景 v2 | [AppLayout.vue](../../frontend/src/components/AppLayout.vue) 根（所有页面可见） | CSS 永远启用 → Canvas2D 柔光 sprite（reduced-motion 关闭）→ Three.js 双层粒子 + 轻量 Bloom（WebGL + 非低性能） |
| [frontend/src/components/HeroScene.vue](../../frontend/src/components/HeroScene.vue) | 首页 3D 浮岛雾海 v2（v2.3.3 iOS 降级） | [HomeView.vue](../../frontend/src/views/HomeView.vue) 顶部 | 无 WebGL / reduced-motion / initScene 异常 → SVG 静态插画（800×480 viewBox：天空渐变 + 太阳 + 3 岛 + 3 层波浪 + 5 漂浮点）；v2.3.3 **iOS 降级**：**Bloom 降级**（iOS 关闭 UnrealBloomPass）+ **PMREM 降级**（PMREM 256→128、阴影 2048→1024、dpr 2→1.5）+ `webglcontextlost` 上下文恢复 |
| [frontend/src/components/FlowerField.vue](../../frontend/src/components/FlowerField.vue) | 3D 花田 v2 | [GardenView.vue](../../frontend/src/views/garden/GardenView.vue) 顶部 | 无 WebGL / reduced-motion / initScene 异常 → CSS 渐变背景 + 提示文案 |
| [frontend/src/components/AudioVisualizer.vue](../../frontend/src/components/AudioVisualizer.vue) | 音波可视化 v2 | [MusicDetailView.vue](../../frontend/src/views/music/MusicDetailView.vue) 详情头之后 | 无 Web Audio / reduced-motion → CSS 5 色横条静态动画 |
| [frontend/src/components/SceneHint.vue](../../frontend/src/components/SceneHint.vue) | **3D 场景交互指引（v2.2 加）** | 被 HeroScene / FlowerField 引用 | `pointer-events: none` 不阻挡 3D 交互；3 秒后自动淡出 |
| [frontend/src/components/SceneControls.vue](../../frontend/src/components/SceneControls.vue) | **3D 场景视图控制（v2.2 加）** | 被 HeroScene / FlowerField 引用 | emit 事件由父组件处理；玻璃拟态样式 + 8px 圆角 |
| [frontend/src/components/EmojiIcon.vue](../../frontend/src/components/EmojiIcon.vue) | **跨浏览器 emoji 组件（v2.3.3 加）** | 被 AppLayout.vue / ProfileView.vue 引用（品牌 / 导航 / 通知 / 资源 / 统计 / 快捷入口 / 花朵阶段） | **Iconify** + `@iconify-json/twemoji` 离线 **SVG emoji**，确保 **跨浏览器一致**（解决 Safari Apple Color Emoji vs 系统 emoji 字体差异）；无降级（SVG 本身就是跨浏览器方案） |

**核心架构决策**：

| 维度 | 决策 | 理由 |
|---|---|---|
| 三层分级 | Layer 1 CSS（永远启用）/ Layer 2 Canvas2D（reduced-motion 关闭）/ Layer 3 Three.js（WebGL + 非低性能） | 治愈系要"柔和不刺眼"，分层降级让任何设备都有体面视觉 |
| **PBR 渲染管线（v2.2）** | `ACESFilmicToneMapping` + `SRGBColorSpace` + `PCFSoftShadowMap` + `RoomEnvironment` PMREM + `UnrealBloomPass` | 替代 v2.1 的 `LinearToneMapping` + `MeshBasicMaterial`，解决「视觉粗糙过时，类似 80/90 年代红白机」问题 |
| **共享工具集（v2.2）** | [utils/three-helpers.js](../../frontend/src/utils/three-helpers.js) 集中 9 个 PBR 工具函数 | 避免 4 个组件重复造轮子；统一释放逻辑避免 WebGL context 泄漏 |
| **交互指引（v2.2）** | [SceneHint.vue](../../frontend/src/components/SceneHint.vue) 横幅 + [SceneControls.vue](../../frontend/src/components/SceneControls.vue) 工具栏 | 解决「用户不知道如何与 3D 元素交互」问题；3 秒淡出不遮挡视野 |
| **OrbitControls（v2.2）** | 所有 3D 场景统一 `OrbitControls`（阻尼 + 极角约束 + 禁用 pan + 自动旋转） | 用户可拖拽旋转 + 滚轮缩放；阻尼让旋转有惯性；极角约束防止视角穿地 |
| **raycaster 点击拾取（v2.2）** | HeroScene 点击浮岛相机飞入；FlowerField 点击花朵显示花语 toast | 让 3D 场景「可交互」而非「只能看」 |
| 能力检测 | `utils/visual.js` 单次缓存 `hasWebGL()` / `prefersReducedMotion()` / `isMobile()` / `isLowPower()` 结果 | 避免每次渲染重复检测；`shouldUseThreeJS()` = `hasWebGL && !prefersReducedMotion && !isLowPower` |
| 异步加载 | 所有 Three.js 组件 `defineAsyncComponent(() => import(...))` | Three.js (~600KB) 不进首屏包，仅访问 `/`（HeroScene）或 `/garden`（FlowerField）时按需拉取 |
| `manualChunks` | [vite.config.js](../../frontend/vite.config.js) 函数形式把 `three` + `three/addons/*` 跨组件共享 `three-vendor` chunk（v2.2 含 OrbitControls / EffectComposer / UnrealBloomPass / RoomEnvironment，gzip 719.84KB） | 与 FlowerField / HeroScene / AmbientBackground 共享同一 chunk，不重复加载 |
| Vue 响应式 | Three.js 对象用 `shallowRef` 持有 | `ref` 会深度代理 Three.js 内部 Scene/Object3D 私有字段拖累性能（详见 [HANDOFF §6.23.2](../../HANDOFF.md)） |
| rAF 调度 | `smartRAF(callback)` 在 `document.hidden` 时 `cancelAnimationFrame`、可见时自动恢复 | 标签页隐藏时浏览器虽降为 1 fps 但仍执行渲染循环，GPU 不释放（详见 [HANDOFF §6.23.3](../../HANDOFF.md)） |
| 资源释放 | `onBeforeUnmount` 调 `disposeObject3D` + `disposeRenderer` 完整释放 geometry / material / texture / renderer / composer / 事件监听 / ResizeObserver | 5 次切走后浏览器报 `Too many active WebGL contexts` 黑屏（详见 [HANDOFF §6.23.4](../../HANDOFF.md)） |
| 移动端降级 | 粒子数减半 + `dpr` ≤ 1.5 + Bloom strength 0.3 → 0.18 + 几何精度降档（Lathe/Cylinder 段数 24→16、Icosahedron detail 2→1、樱花树递归深度 4→3、花瓣网格 5×8→4×6、地面圆 64→32、AudioVisualizer 柱数 48/64→32） | 移动端 GPU/CPU 弱，全量粒子 + 强 Bloom + 高精度几何会掉帧；几何降档可在不牺牲视觉层次的前提下大幅减少顶点数 |
| 配色一致性 | 4 个组件全部用治愈系 5 色（藕粉 `#E8B8C5` / 淡黄 `#E8D5A8` / 青绿 `#A8C5A0` / 雾蓝 `#A8B8C5` / 纯白 `#FAF6F2`）+ 米白 `#F9F6F0` 背景 | 与 [tailwind.config.js](../../frontend/tailwind.config.js) token 一致；AudioVisualizer 4 模式频响颜色低频暖色 → 高频冷色 |
| Web Audio 一次性约束 | `audioCtx.createMediaElementSource(audioEl)` 对同一 `<audio>` 元素只能调一次 | AudioVisualizer `if (!sourceNode)` 守卫 + MusicDetailView `visualizerConnected` ref 标记首次 `playIndex` 时连接（详见 [HANDOFF §6.23.1](../../HANDOFF.md)） |
| **Safari 兼容（v2.3.3）** | ① **`hasWebGL` 重写**（区分 WebGL1/2 + 检测扩展 + max texture size）+ `getWebGLCaps()` / `isSafari()` / `isIOS()`；② `webglcontextlost` / `webglcontextrestored` 事件监听处理 **WebGL 上下文丢失**（iOS Safari 切后台→前台触发）；③ **iOS 降级**：**Bloom 降级**（iOS 关闭 UnrealBloomPass）+ **PMREM 降级**（PMREM 256→128、阴影 2048→1024、dpr 2→1.5；老 iOS 缺 `EXT_color_buffer_half_float` 扩展时关闭 PMREM + Bloom） | 解决 Safari / iOS 用户反馈的 3D 不渲染（hasWebGL 误判 + 上下文丢失无恢复 + Bloom/PMREM 内存超限）问题（详见 [HANDOFF §6.24](../../HANDOFF.md)） |
| **跨浏览器 emoji 一致性（v2.3.3）** | [EmojiIcon.vue](../../frontend/src/components/EmojiIcon.vue) 组件用 **Iconify** + `@iconify-json/twemoji` 离线 **SVG emoji** | 解决 Safari Apple Color Emoji vs 系统 emoji 字体风格差异，确保 **跨浏览器一致**；已替换 AppLayout.vue + ProfileView.vue 所有 emoji |

**为什么 v2.2 引入 PBR + Bloom 后处理**（推翻 v2.1 决策）：
- v2.1 决策「不用全屏 shader / 后处理」基于「治愈系要柔和不刺眼」，但实际效果过于平淡，被用户评价为「粗糙过时，类似 80/90 年代红白机」
- v2.2 调整：Bloom strength 0.3（移动端 0.18）保持克制，只让发光物体（花瓣 / 樱花 / 光点）有柔光晕，**不**做全屏泛光；ACESFilmic 色调映射让暗部有细节不死黑，高光不爆白
- 性能保护：移动端 Bloom strength 降到 0.18 + 粒子数减半 + dpr ≤ 1.5 + 几何精度降档（Lathe/Cylinder/Icosahedron 段数与细分降低，樱花树递归深度 4→3，花瓣网格 5×8→4×6，地面圆 64→32，AudioVisualizer 柱数减半）；reduced-motion 直接降级为 SVG 静态插画，不走 Bloom 路径

**降级验证矩阵**：

| 环境 | AmbientBackground | HeroScene | FlowerField | AudioVisualizer |
|---|---|---|---|---|
| 桌面 Chrome（WebGL + 默认 motion） | CSS + Canvas2D 柔光 sprite + Three.js 双层粒子 + Bloom | 3D 浮岛雾海 + 樱花树 + PBR 水面 + Bloom + OrbitControls | 3D 立体花瓣 + MeshPhysicalMaterial + Bloom + OrbitControls + raycaster | Web Audio + Canvas2D 4 模式 + 节拍检测 |
| 桌面 Chrome + `prefers-reduced-motion` | 仅 CSS 雾气光斑 | SVG 静态插画 | CSS 渐变背景 + 提示文案 | CSS 5 色横条静态 |
| 移动端 Safari（WebGL + 默认 motion） | CSS + Canvas2D（粒子减半）+ Three.js 双层粒子（dpr≤1.5）+ Bloom strength 0.18 | 3D 浮岛雾海（粒子减半 + dpr≤1.5 + Bloom 0.18 + 樱花树深度 4→3 + Lathe/Cylinder 段数 24→16 + Icosahedron detail 2→1） | 3D 立体花瓣（粒子减半 + dpr≤1.5 + 花瓣网格 5×8→4×6 + 花蕊 Icosahedron detail 2→1 + 地面圆 64→32 + 茎圆柱段 6→5） | Web Audio + Canvas2D 4 模式（镜像柱 48→32 / 径向柱 64→32 / 粒子流 120→60 / 节拍粒子 10→6 / 24fps） |
| **iOS Safari v2.3.3 降级**（`isIOS()` 检测） | 同上（AmbientBackground 不受 iOS 降级影响） | **iOS 降级**：**Bloom 降级**（关闭 UnrealBloomPass）+ **PMREM 降级**（PMREM 256→128、阴影 2048→1024、dpr 2→1.5）；老 iOS 缺 `EXT_color_buffer_half_float` 扩展时关闭 PMREM + Bloom | 同上（FlowerField 不受 iOS 降级影响） | 同上（AudioVisualizer 不受 iOS 降级影响） |
| **iOS Safari 切后台→前台**（`webglcontextlost`） | Three.js 粒子暂停渲染，CSS + Canvas2D 兜底 | `webglcontextlost` 保存场景状态 → `webglcontextrestored` 重建 renderer + 恢复场景 + 重启 rAF | 同上（`webglcontextlost` 时暂停，`webglcontextrestored` 时恢复） | 不受影响（不用 Three.js） |
| 旧浏览器（无 WebGL，v2.3.3 hasWebGL 重写后准确检测） | CSS + Canvas2D 光点 | SVG 静态插画 | CSS 渐变背景 + 提示文案 | CSS 5 色横条 |
| `import('three')` 失败 | CSS + Canvas2D 光点 | SVG 静态插画 | CSS 渐变背景 + 提示文案 | 不受影响（不用 Three.js） |

详见 [frontend/src/components/AmbientBackground.vue](../../frontend/src/components/AmbientBackground.vue) + [HeroScene.vue](../../frontend/src/components/HeroScene.vue) + [AudioVisualizer.vue](../../frontend/src/components/AudioVisualizer.vue) + [FlowerField.vue](../../frontend/src/components/FlowerField.vue) + [SceneHint.vue](../../frontend/src/components/SceneHint.vue) + [SceneControls.vue](../../frontend/src/components/SceneControls.vue) + [EmojiIcon.vue](../../frontend/src/components/EmojiIcon.vue) + [utils/visual.js](../../frontend/src/utils/visual.js) + [utils/three-helpers.js](../../frontend/src/utils/three-helpers.js)，决策理由详见 [HANDOFF §5.10](../../HANDOFF.md) + [HANDOFF §5.11](../../HANDOFF.md)，4 大坑详见 [HANDOFF §6.23](../../HANDOFF.md)，Safari 兼容 3 大坑详见 [HANDOFF §6.24](../../HANDOFF.md)。

---

## 1.1.7 v2.3 六大四字名板块 + 双资源系统 + 花朵生命周期 + 通知 + 个人主页（2026-07-25 加）

> 设计原则：**「四字名治愈系命名 + 双资源经济 + 生命周期叙事 + 通知触达」** —— 用更具东方治愈调性的命名替代纯功能名；把原单一能量语义拆为 `露水`（向内获得：听歌/打卡/写日记，用于浇灌花朵）+ `落叶`（向外获得：花朵枯萎后拾取，用于兑换花种）；用花朵生命周期（seed→sprout→bud→bloom→wilted）把屿上花田变成「持续可养护」的陪伴场景；用通知系统把漂流瓶评论返回等零散事件汇总成统一触达入口。

### 1.1.7.1 六大四字名板块 + 路由对照（含顶部品牌图标更新）

| 四字名 | 路由 | 前端视图 | 后端 API |
|---|---|---|---|
| 琴音疗心 | `/music` | [MusicListView.vue](../../frontend/src/views/music/MusicListView.vue) | `/api/music/*` |
| 漂流日记 | `/diary` | [DiaryListView.vue](../../frontend/src/views/diary/DiaryListView.vue) | `/api/diary/*` |
| 情绪日历 | `/calendar` | [MoodCalendarView.vue](../../frontend/src/views/mood/MoodCalendarView.vue) | `/api/mood/*` |
| 心语树洞 | `/ai-chat` | [AIChatView.vue](../../frontend/src/views/ai/AIChatView.vue) | `/api/ai/chat` |
| 花坊 | `/shop` | [ShopView.vue](../../frontend/src/views/garden/ShopView.vue) | `/api/garden/shop` + `/api/energy/exchange` |
| 屿上花田 | `/garden` | [GardenView.vue](../../frontend/src/views/garden/GardenView.vue)（含花田生长网格） | `/api/garden/*` + `/api/garden/flowers/*` |

辅助入口：拾瓶 `/diary/pick` 🍶（漂流日记子路由）/ 我的 `/profile` 👤（个人主页，`requiresAuth`）；通知中心 `/notifications`（独立页，`requiresAuth`）。

[AppLayout.vue](../../frontend/src/components/AppLayout.vue) 顶部品牌图标由 🌿 草本更新为 🏝️ 岛屿 emoji；桌面/平板/移动三档导航同步四字短标签；移动端 tabbar 4 项固定（静屿 / 漂流日记 / 情绪日历 / 我的）+ 中央「更多」抽屉（琴音疗心 / 拾瓶 / 心语树洞 / 花坊 / 屿上花田）。

### 1.1.7.2 双资源系统（露水 + 落叶）

**资源哲学**：
- `露水` = `User.total_energy`（保留原字段，语义即露水）= **向内获得**：听歌 / 打卡 / 写日记；**不可兑换商品**，仅用于浇灌已播种的花朵
- `落叶` = `User.leaves`（v2.3 新增）= **向外获得**：花朵枯萎后拾取；用于在花坊兑换花种（寓意「落叶归根能施肥种花」）
- `EnergyRecord` **不**加 `resource_type` 字段；资源类型由 `source` + `ShopItem.cost_currency` 体现

**模型层**（[app/models/user.py](../../app/models/user.py) + [app/models/garden.py](../../app/models/garden.py)）：
```python
# User
total_energy: Mapped[int] = mapped_column(Integer, default=0)   # 露水（保留原字段）
leaves: Mapped[int] = mapped_column(Integer, default=0)         # 落叶（v2.3 加）

# ShopItem
cost_currency: Mapped[str] = mapped_column(String(20), default="dew", nullable=False)
# "dew"（装扮/徽章）| "leaves"（花种）
```

**Service 层**（[app/services/energy_service.py](../../app/services/energy_service.py) + [app/services/flower_service.py](../../app/services/flower_service.py)）：
- `grant_energy(db, user, amount, source, ...)` 维持原签名，写 `EnergyRecord` + 累加 `User.total_energy`（仅露水有日上限 20）
- `exchange_item` 按 `ShopItem.cost_currency` 扣 `total_energy` 或 `leaves`
- `water_flower` 显式 `db.query(User).filter(...).update({User.total_energy: User.total_energy - 1})` 扣 1 露水
- `collect_wilted_leaves` 显式 `db.query(User).filter(...).update({User.leaves: User.leaves + 2})` 加 2 落叶

**常量层**（[app/utils/constants.py](../../app/utils/constants.py)）：
- `DEFAULT_SHOP_ITEMS` 11 件全部带 `cost_currency`：5 件花种 = `leaves`，3 件装扮 = `dew`，3 件徽章 = `dew`（自动触发）
- `DAILY_ENERGY_LIMITS` 维持原 `listen_music: 20 / write_diary: 10 / checkin: 5`（仅露水有日上限，落叶无日上限）

**资源获取规则**：

| 行为 | 增量 | 资源 | 来源 code |
|---|---|---|---|
| 听完一首曲子（进度 ≥ 90%） | +1 露水 | total_energy | `listen_music` |
| 写完一篇日记 | +1 露水 | total_energy | `write_diary` |
| 当日心情打卡 | +1 露水 | total_energy | `checkin` |
| 兑换商店物品 | -cost（按 item.cost_currency） | dew/leaves | `exchange` |
| 浇灌花朵 | -1 露水 | total_energy | `water_flower` |
| 拾取枯萎花朵 | +2 落叶 | leaves | `collect_wilted_leaves` |

### 1.1.7.3 花朵生命周期（UserFlower + flower_service + API + 前端）

**模型**（[app/models/garden.py](../../app/models/garden.py)）：
```python
class UserFlower(Base):
    __tablename__ = "user_flowers"
    id, user_id, flower_type, stage, watered_count,
    planted_at, last_watered_at, bloom_at, wilted_at
    # 5 阶段：seed → sprout → bud → bloom → wilted
```
常量：`STAGE_SEED/STAGE_SPROUT/STAGE_BUD/STAGE_BLOOM/STAGE_WILTED` + `STAGE_ORDER` + `WATER_TO_NEXT_STAGE = {seed: 2, sprout: 3, bud: 2, bloom: 0, wilted: 0}` + `WILT_DAYS_AFTER_BLOOM = 7`。

**Service**（[app/services/flower_service.py](../../app/services/flower_service.py)）：
- `list_my_flowers(db, user_id)` — 列出所有花朵（含枯萎待拾取的）；lazy 检查盛开花朵是否到枯萎时间
- `water_flower(db, user, flower_id)` — 浇 1 露水（`total_energy -1`），累加 `watered_count`，达阈值升级；盛开后再浇水仅刷新 `last_watered_at` 延长枯萎；枯萎花不能浇
- `collect_wilted_leaves(db, user, flower_id)` — 拾取枯花 → +2 落叶 → 删除该花
- `get_flower_detail(db, user, flower_id)` — 单朵详情（lazy 检查枯萎）
- `_check_wilt(flower)` — 内部函数：盛开超过 `WILT_DAYS_AFTER_BLOOM` 天未浇水 → 标记 `wilted` + 写 `wilted_at`

**API**（[app/routers/garden.py](../../app/routers/garden.py)）：
- `GET /api/garden/flowers` — 我的所有花朵
- `GET /api/garden/flowers/{id}` — 单朵详情
- `POST /api/garden/flowers/{id}/water` — 浇水（消耗 1 露水，返回 `new_total_energy`）
- `POST /api/garden/flowers/{id}/collect` — 拾取枯花（返回 `gained_leaves` + `new_leaves`）

**前端**：[GardenView.vue](../../frontend/src/views/garden/GardenView.vue) `STAGE_INFO` 映射（emoji/label/progress/desc）+ 浇水按钮 + 拾取按钮 + 移动端单列网格。

### 1.1.7.4 通知系统（Notification + 轮询）

**模型**（[app/models/notification.py](../../app/models/notification.py)）：
```python
class Notification(Base):
    __tablename__ = "notifications"
    id, user_id, type, content, related_id, is_read, created_at
    # type: "encouragement"（漂流瓶评论返回）/ "system"（预留）
```

**Router**（[app/routers/notification.py](../../app/routers/notification.py)）（**单数形式**）：
- `GET /api/notifications` — 通知列表（最近 50 条）
- `GET /api/notifications/unread` — 未读数（返回 `{unread: int}`）
- `POST /api/notifications/{id}/read` — 标记单条已读
- `POST /api/notifications/read-all` — 全部已读

**触发点**：读者在拾瓶后留鼓励语 → 写 `Encouragement` + 同步写 `Notification(type='encouragement', user_id=作者, related_id=diary_id)`。

**前端**：[AppLayout.vue](../../frontend/src/components/AppLayout.vue) 顶部 + 移动端 topbar 加 🔔 铃铛 + 红点未读数；`onMounted` 起 60s 轮询 `/api/notifications/unread`；点击跳 `/notifications` 页（非下拉）。独立页 [NotificationsView.vue](../../frontend/src/views/notification/NotificationsView.vue) 列表 + 未读高亮 + 单条已读 + 全部已读。

### 1.1.7.5 个人主页（profile router + ProfileView）

**Router**（[app/routers/profile.py](../../app/routers/profile.py)）：
- `GET /api/profile` — 我的主页（基本信息 + 双资源 + 完整统计 + 连续打卡）
- `GET /api/profile/stats` — 轻量统计快照
- `GET /api/profile/{user_id}` — 他人主页（仅公开信息）

统计字段：`diary_count` / `public_diary_count` / `checkin_count` / `listen_count` / `flower_count` / `garden_item_count` / `received_encouragement_count` / `streak`（连续打卡天数，由 `mood_service.get_current_streak` 计算）。

**前端**：[ProfileView.vue](../../frontend/src/views/profile/ProfileView.vue) — 卡片式布局：🏝️ 头像 + 昵称 + 在岛天数 + 双资源条（露水/落叶）+ 6 统计卡（日记/打卡/听曲/花朵/收到鼓励/岛上物件）+ 快捷入口；路由 `/profile` 加入 `requiresAuth: true` 守卫。

### 1.1.7.6 古琴弹西洋曲谱子菜单（musics 迁移 + seed 幂等 + API 参数）

**模型**（[app/models/music.py](../../app/models/music.py)）：
```python
category: Mapped[str] = mapped_column(String(20), default="classic", nullable=False)
# "classic"（五音传统古曲）| "western"（古琴弹西洋曲谱）
```

**常量**：[app/utils/constants.py](../../app/utils/constants.py) 新增 `class MusicCategory(str, Enum)`：`CLASSIC = "classic"` / `WESTERN = "western"`。

**seed**（[app/seed.py](../../app/seed.py)）：`SEED_MUSIC` 加 6 首西方改编——绿袖子（yu）/ 卡农（gong）/ 致爱丽丝（jue）/ 月光奏鸣曲（yu）/ 天鹅湖（shang）/ 昨日重现（zhi）；**`seed_music()` 改为按 title 幂等**（不再「表空才插」），老库重启即自动补齐 western 曲目。

**API**（[app/routers/music.py](../../app/routers/music.py)）：
- `GET /api/music?category=western|classic` — query 参数过滤

**前端**：[MusicListView.vue](../../frontend/src/views/music/MusicListView.vue) 底部加「古琴弹西洋」入口卡片；新视图 [MusicWesternView.vue](../../frontend/src/views/music/MusicWesternView.vue) 按五音分组展示 + 内置播放器 + AudioVisualizer。路由 `/music/western` **必须放在 `/music/:yin` 前面**避免动态段捕获。

### 1.1.7.7 日记调整（明文化 + send_to_ai_hole + 发布选项）

**模型**（[app/models/diary.py](../../app/models/diary.py)）：
```python
content: Mapped[str] = mapped_column(Text, nullable=False, default="")  # 明文（v2.3 替代 content_encrypted）
content_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)  # 遗留字段，仅为兼容老库
send_to_ai_hole: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)  # 不放入漂流瓶时同步树洞
# 保留：is_public, mood_type
```
`User.encryption_salt` 保留仅为兼容老库（v2.3 起日记改明文，不再使用）。

**发布选项**（前端 radio）：
- 放入漂流瓶：`is_public=True`，公开可见 + 允许评论
- 不放入漂流瓶：`is_public=False`，仅自己可见 + 可选 `send_to_ai_hole=True` 同步至心语树洞

**前端**：[DiaryWriteView.vue](../../frontend/src/views/diary/DiaryWriteView.vue) 移除 emoji 选择器 + 移除密码 UI + 加发布选项 radio + 加 SVG 海浪动画（日记海岸主题）。

### 1.1.7.8 情绪日历对齐修复（emoji 字符统一 + 字段名对齐）

原前端用 `mood_type` + `date`，后端 `MoodCheckin` 用 `mood_emoji` + `check_date`；前端兼容旧字段但优先用后端字段名。修复：
- [app/utils/constants.py](../../app/utils/constants.py) `MOOD_INFO` 7 种心情：ecstatic 🤩 / happy 😊 / calm 😌 / tired 😪 / anxious 😰 / angry 😠 / sad 😢
- 前端 `MOOD_INFO` 同步 7 种 + 日历加心情图例（legend）解决「emoji 显示不全」问题

### 1.1.7.9 树洞改进（统一图标 + 文本输入 + 文件式聊天历史 + 留存提示）

- **统一图标**：AIChatView + AppLayout 导航 + tabbar 全部用 🌳 树形 emoji（心语树洞）
- **文本输入**：[AIChatView.vue](../../frontend/src/views/ai/AIChatView.vue) 加 `<textarea>` 多行输入框（原仅单行 input）
- **文件式聊天历史**：[app/services/chat_history_service.py](../../app/services/chat_history_service.py) 新增——存于 `data/chat_history/<user_id>/<conversation_id>.json`；函数 `create_conversation` / `load_messages` / `append_message` / `list_conversations` / `delete_conversation` / `get_or_create_conversation`；单对话上限 100 条；每次 AI 调用前加载历史
- **留存提示**：每次聊天结束时树洞询问用户是否保留记录；选「不保留」则 `delete_conversation` 删文件
- **上下文增强**：树洞根据用户当日 `MoodCheckin.mood_emoji` + 当日 `Diary.content`（若 `send_to_ai_hole=True`）提供针对性聊天和安慰

### 1.1.7.10 数据库迁移（`_migrate_legacy_columns()` 一次性自动加列）

[app/database.py](../../app/database.py) `_migrate_legacy_columns()` 新增：
- `users` 加 `leaves INTEGER DEFAULT 0 NOT NULL`（`total_energy` 即露水，原已存在不改）
- `diaries` 加 `content TEXT NOT NULL DEFAULT ''` + `send_to_ai_hole BOOLEAN DEFAULT 0 NOT NULL`
- `shop_items` 加 `cost_currency VARCHAR(20) DEFAULT 'dew' NOT NULL`
- `musics` 加 `category VARCHAR(20) DEFAULT 'classic' NOT NULL`
- 新表 `user_flowers` / `notifications` 由 `init_db()` 自动建表（`Base.metadata.create_all`）

### 1.1.7.11 pre-commit 5 项 checklist（正式化）

详见 [HANDOFF §12.4](../../HANDOFF.md) / [README §9.3](../../README.md) / [PROJECT_STATE §8.3](../PROJECT_STATE.md) / [DEVELOPMENT §1.8](DEVELOPMENT.md)。5 项：
1. Pydantic Out schema 是否补了新字段（→ [§7.7](#77-pydantic-schema-字段完整性防-611-静默过滤) / [DEVELOPMENT §3.10](DEVELOPMENT.md)）
2. `_migrate_legacy_columns()` 是否补了老库列（→ [§9.4](#94-加一个新字段到旧库轻量迁移不引-alembic) / [HANDOFF §6.10](../../HANDOFF.md)）
3. `constants.py` 业务常量同步（→ [§4.3](#43-单日能量上限)）
4. `.env.example` 配置同步
5. README / HANDOFF 速查表同步

---

## 1.1.8 v2.4.0 头像/昵称编辑 + 一天多条心情 + 花坊扩充（2026-08-10 加）

> 设计原则：**「情绪多变允许多次记录 + 头像个性化同步树洞 + 花坊扩充丰富经济」** —— 情绪是多变的，一天可以有多次心情打卡；用户头像/昵称可自定义并同步到树洞对话；花坊扩充花种/装扮/徽章让双资源经济更丰富。

### 1.1.8.1 头像/昵称编辑流程（User.avatar + PATCH /api/profile + ProfileUpdateIn + 头像同步树洞）

**模型**（[app/models/user.py](../../app/models/user.py)）：
```python
avatar: Mapped[str] = mapped_column(String(16), default="🙂", nullable=False)
# emoji 字符，默认 🙂，与树洞中显示的头像一致
```

**数据库迁移**（[app/database.py](../../app/database.py) `_migrate_legacy_columns()`）：
- `ALTER TABLE users ADD COLUMN avatar VARCHAR(16) DEFAULT '🙂' NOT NULL`（v2.4 用户头像）

**Schema**（[app/schemas/profile.py](../../app/schemas/profile.py)，v2.4 新增）：
```python
class ProfileUpdateIn(BaseModel):
    nickname: str | None = Field(None, min_length=2, max_length=20)
    avatar: str | None = Field(None, min_length=1, max_length=16)
```

**Router**（[app/routers/profile.py](../../app/routers/profile.py)）：
- `PATCH /api/profile` — 更新头像/昵称（昵称查重 409，头像 1-16 字符）

**前端**：
- [ProfileView.vue](../../frontend/src/views/profile/ProfileView.vue) 头像/昵称编辑弹窗（24 个可选 emoji）
- [stores/user.js](../../frontend/src/stores/user.js) 新增 `updateProfile` action（调用 `PATCH /api/profile`）
- **头像同步树洞**：[AIChatView.vue](../../frontend/src/views/ai/AIChatView.vue) 使用 `userStore.avatar` 显示头像（与个人主页一致）

**调用流**：
```
浏览器                                FastAPI
  │                                      │
  │ PATCH /api/profile                   │
  │ {nickname?, avatar?}                 │
  │ Cookie: qi_session=...               │
  ├─────────────────────────────────────→│
  │                                      │ 1. get_current_user 鉴权
  │                                      │ 2. nickname 查重（409 冲突）
  │                                      │ 3. avatar 长度校验（1-16 字符）
  │                                      │ 4. UPDATE users SET ... 
  │                                      │ 5. 返回更新后 user 对象
  │ ←─ 200 + {user}                      │
  │                                      │
  │ Pinia userStore.setUser(user)        │
  │ → AIChatView 头像同步更新            │
```

### 1.1.8.2 一天多条心情数据模型（mood_checkins 唯一约束移除 + add_checkin + get_today_moods + 平均分）

**背景**：情绪是多变的，一天可以有多次心情打卡，原 `(user_id, check_date)` 唯一约束限制了这一表达。

**数据库迁移**（[app/database.py](../../app/database.py) `_migrate_legacy_columns()`，SQLite 重建表方式）：
```sql
-- SQLite 不支持 DROP CONSTRAINT，用重建表方式
CREATE TABLE _mood_checkins_new AS SELECT * FROM mood_checkins;
DROP TABLE mood_checkins;
RENAME TABLE _mood_checkins_new TO mood_checkins;
CREATE INDEX ix_mood_checkins_user_id ON mood_checkins (user_id);
-- 移除 (user_id, check_date) 唯一约束，仅保留 user_id 普通索引
```

**Service**（[app/services/mood_service.py](../../app/services/mood_service.py) 重构）：
- `upsert_checkin` → `add_checkin`（不再 UPSERT，允许一天多条）
- 新增 `get_today_moods(db, user_id)` — 获取今日所有心情
- `get_recent_trend` 多条取**平均分**（MOOD_SCORE 映射：ecstatic=5 / happy=4 / calm=3 / tired=2 / anxious=2 / angry=1 / sad=1）

**评分系统**（1-5 分）：

| 心情 | emoji | 评分 |
|---|---|---|
| 极度开心 ecstatic | 🤩 | 5 |
| 开心 happy | 😊 | 4 |
| 平静 calm | 😌 | 3 |
| 疲惫 tired | 😪 | 2 |
| 焦虑 anxious | 😰 | 2 |
| 生气 angry | 😠 | 1 |
| 悲伤 sad | 😢 | 1 |

**数据模型对比**：

| 维度 | v2.3（原） | v2.4.0（新） |
|---|---|---|
| 唯一约束 | `(user_id, check_date)` 唯一 | **移除**，仅 `user_id` 索引 |
| 一天打卡次数 | 1 次（UPSERT 覆盖） | 多次（INSERT 新增） |
| service 函数 | `upsert_checkin` | `add_checkin` + `get_today_moods` |
| 30 天趋势 | 单条直接读 | 多条取**平均分**（MOOD_SCORE 映射） |

### 1.1.8.3 花坊双资源经济扩充（DEFAULT_SHOP_ITEMS 27 件 + 每板块徽章）

**改名**：'落叶画坊' → '花坊'（[HomeView.vue](../../frontend/src/views/HomeView.vue) 模块名更新）

**常量**（[app/utils/constants.py](../../app/utils/constants.py) `DEFAULT_SHOP_ITEMS` 扩充至 27 件）：
- 12 花种（leaves 资源）：向日葵 / 竹子 / 雏菊 / 莲花 / 薰衣草 / 郁金香 / 梅花 / 桃花 / 兰花 / 青松 / 桂花 / 银杏
- 9 装扮（dew 资源）：草帽（'竹编帽'描述改'种花人遮阳的草帽'）/ 长袍 / 蒲扇 + 新增 6 件：油纸伞 / 蓑衣 / 乌篷船 / 鱼竿 / 橘猫 / 白鹤
- 6 徽章（dew 资源，自动触发，**每板块徽章**）：琴音知音（原'古琴初学者'改名）/ 日记达人 / 七日静心 / 拾瓶旅人 / 树洞倾心 / 花田主人

**每板块徽章对应关系**：

| 徽章 | 对应板块 | 触发条件 |
|---|---|---|
| 琴音知音 | 琴音疗心 | 听曲达到一定次数 |
| 日记达人 | 漂流日记 | 写日记达到一定篇数 |
| 七日静心 | 情绪日历 | 连续打卡 7 天 |
| 拾瓶旅人 | 拾瓶 | 拾瓶达到一定次数 |
| 树洞倾心 | 心语树洞 | 树洞对话达到一定次数 |
| 花田主人 | 屿上花田 | 花朵盛开达到一定数量 |

### 1.1.8.4 其他 v2.4.0 改动

- **首页文案**：'海上有座岛，岛上有人听' → '潮声不止，心安自屿'，删除'静屿'副标题 + 删除'今日打卡'板块
- **'漂流日记'入口统一**：直接显示'日记海岸'界面（含拾瓶/写日记模块）
- **情绪日历 emoji 显示/选择修复**：[MoodCalendarView.vue](../../frontend/src/views/mood/MoodCalendarView.vue) 多条打卡支持
- **心语树洞 AI 系统提示词 humanize**：更接地气、像朋友聊天
- **花田 AI 显示基于实际种花情况**：[GardenView.vue](../../frontend/src/views/garden/GardenView.vue) 没种花不显示 AI
- **'我的'页面修复**：'收到鼓励'/'岛上物件'可点击跳转，删除重复'岛上物件'，新增**静屿使用指南**（7 个模块详细介绍：琴音疗心 / 日记海岸 / 情绪日历 / 心语树洞 / 花坊 / 屿上花田 / 我的）
- **露水累加修复**：写日记和留言鼓励后正确发放露水

---

## 1.1.9 v2.4.1 情绪日历罗素情绪环模型四象限图表（2026-08-10 加）

> 设计原则：**「情绪可视化从线性趋势升级为二维情绪空间」** —— 将情绪日历的 30 天趋势柱状图替换为罗素情绪环模型（Russell's Circumplex Model of Affect）四象限图表，用效价（Valence）+ 唤醒度（Arousal）二维坐标系把情绪可视化，帮助用户更立体地理解自己的情绪分布。

**文件**：[frontend/src/views/mood/MoodCalendarView.vue](../../frontend/src/views/mood/MoodCalendarView.vue)

### 数据流

```
CIRCUMPLEX_EMOTIONS（20 种情绪静态数组）
  │ 每种情绪带 { key, emoji, label, valence, arousal, tracked }
  │   valence: -1~+1（消极 → 积极，横轴）
  │   arousal: -1~+1（低唤醒 → 高唤醒，纵轴）
  │   tracked: 是否映射后端 MOOD_INFO（7 种已追踪 / 13 种参考）
  ↓
emotionPosition(emotion) 百分比转换
  │ left% = (valence + 1) / 2 * 100
  │ top%  = (1 - (arousal + 1) / 2) * 100（反转，上=高唤醒）
  ↓
四象限图表渲染（百分比绝对定位 emoji 到象限内）
  ├─ Q1 右上：积极 + 高唤醒（ecstatic 🤩 / happy 😊）
  ├─ Q2 左上：消极 + 高唤醒（anxious 😰 / angry 😠）
  ├─ Q3 左下：消极 + 低唤醒（sad 😢 / tired 😪）
  └─ Q4 右下：积极 + 低唤醒（calm 😌）
  ↓
点击 emoji → 弹详情卡片
  │ 已追踪情绪：显示「本月出现 X 次」（X = moodCounts[key]）
  │ 未追踪情绪：显示「该情绪暂未开放打卡记录」
  ↓
moodCounts computed（从 checkins 统计本月各心情出现次数）
  └─ totalCheckins：本月总打卡数
```

### 四象限划分

| 象限 | 位置 | 效价 + 唤醒度 | 典型情绪 |
|---|---|---|---|
| Q1 | 右上 | 积极 + 高唤醒 | ecstatic 🤩 / happy 😊 |
| Q2 | 左上 | 消极 + 高唤醒 | anxious 😰 / angry 😠 |
| Q3 | 左下 | 消极 + 低唤醒 | sad 😢 / tired 😪 |
| Q4 | 右下 | 积极 + 低唤醒 | calm 😌 |

### 已追踪情绪与参考情绪

- **已追踪情绪（7 种）**：ecstatic / happy / calm / tired / anxious / angry / sad —— 映射后端 [MOOD_INFO](../../app/utils/constants.py)，有真实打卡数据，边框高亮 + 次数角标
- **参考情绪（13 种）**：帮助用户理解情绪在环模型中的位置，点击显示「该情绪暂未开放打卡记录」

### 移除项与保留项

| 维度 | v2.4.0（原） | v2.4.1（新） |
|---|---|---|
| 30 天趋势柱状图 | `trendBars` computed / `scoreColor` 函数 / `.trend-section` 模板 / `.trend-bar` 样式 | **全部删除** |
| 情绪可视化 | 线性 1-5 分趋势柱状图 | **罗素情绪环模型四象限图表** |
| `fetchTrend` 调用 | 渲染趋势柱状图 | **仍调用**（为 `currentStreak` 连续打卡天数显示） |
| `trend` 数据 | 用于渲染柱状图 | **不再用于渲染** |
| `currentStreak` | 连续打卡天数显示 | **保留** |

### 视觉与交互

- 治愈系配色（四象限淡色背景区分）
- GSAP 入场动画
- 移动端响应式
- 已追踪情绪：边框高亮 + 次数角标（`moodCounts[key]`）
- 未追踪情绪：无角标，点击提示「该情绪暂未开放打卡记录」

---

## 1.2 开发/生产模式切换（2026-07-19 v2.0 加，v2.0.1 端口策略调整，v2.2.2 默认应用模式）

> **2026-07-19 v2.0.1 端口策略调整**：开发模式从「Vite :5173 + FastAPI :5000」改为「**Vite :5000 + FastAPI :5001**」——用户**始终**访问 :5000，由 [start.py](../../start.py) 切换端口策略。理由：原方案让 FastAPI :5000 反代 Vite :5173，但 Vite 内部路径 `/@id/__x00__plugin-vue:export-helper` 含 null 字节转义 + 冒号，httpx 转发时被破坏，浏览器报 `SyntaxError: Unexpected token '.'`（详见 [HANDOFF §6.16](../../HANDOFF.md)）。

> **2026-07-25 v2.2.2 默认应用模式**：`python start.py` 默认行为变更为**应用/开发模式**（Vite :5000 HMR + FastAPI :5001 API 一起起），自动检测 `frontend/node_modules` 不存在则 `npm install`。生产模式需显式 `python start.py --prod`（FastAPI :5000 单进程，需 dist 已构建）。`--dev` 改为兼容别名（等同默认行为）。

### 1.2.1 应用模式（Vite dev server :5000 + FastAPI :5001，默认）

```
浏览器 → http://127.0.0.1:5000/  ← 用户始终访问 :5000
                                  │
                                  ↓
                            Vite dev server (:5000)
                                  ├─ 服务 Vue 3 源码（HMR 热更新）
                                  └─ proxy /api、/static、/admin、/docs、
                                      /openapi.json → FastAPI :5001
                                                │
                                                ↓
                                       FastAPI (uvicorn :5001)
                                          ├─ /api/* → JSON API
                                          ├─ /static/* → 静态资源
                                          ├─ /admin/* → 后台 SSR
                                          └─ /docs、/openapi.json → Swagger
```

- **推荐**：`python start.py`（默认应用模式：自动起 Vite :5000 + FastAPI :5001 双进程，自动检测 `frontend/node_modules` 不存在则 `npm install`）
- **备选**（手动两终端）：
  - 终端 1：`cd frontend && npm install && npm run dev`（Vite 监听 :5000）
  - 终端 2：`set QI_PORT=5001 && python start.py fg`（FastAPI 监听 :5001）
- 浏览器访问 **:5000**（即 Vite），前端调 API 走 proxy 无跨域
- start.py 在应用模式会设置环境变量 `QI_PORT=5001` 让 FastAPI 改听 5001（默认是 5000）
- Vite host 显式设 `127.0.0.1`（不写 `localhost`，避免 IPv6 `[::1]` 问题，详见 [HANDOFF §6.12](../../HANDOFF.md)）
- Vite `strictPort: true` 防止 5000 被占用时自动跳到 5001（会和 FastAPI 撞）

### 1.2.2 生产模式（FastAPI :5000 + SPA fallback，Vite 不运行，需 --prod）

```
浏览器 → http://127.0.0.1:5000/  ← 用户始终访问 :5000
                                  │
                                  ↓
                            FastAPI (uvicorn :5000，从 .env 读 QI_PORT)
                                  ├─ /api/* → JSON API
                                  ├─ /static/* → 静态资源（含 dist/）
                                  ├─ /admin/* → 后台 SSR（Jinja2）
                                  └─ 其他 GET → SPA fallback → static/dist/index.html
                                                              + EXT_TO_MIME 映射静态资源
```

- **推荐**：`python start.py build`（一键构建前端到 `static/dist/`）+ `python start.py --prod`（启动 FastAPI 单进程）
- 备选：`cd frontend && npm run build` 输出到 `static/dist/`，然后 `python start.py --prod`
- 浏览器访问 **:5000**（这次是 FastAPI），FastAPI 兜底返回 `index.html`，Vue Router 接管客户端路由
- dist 未构建时（`--prod` 模式）报错退出，提示先 `python start.py build` 或不加 `--prod` 走默认应用模式

### 1.2.3 端口策略对照表

| 模式 | 用户访问 | Vite | FastAPI | 启动方式 |
|---|---|---|---|---|
| 应用（默认，v2.2.2 起） | :5000 | :5000（用户入口 + HMR） | :5001（API） | `python start.py`（自动 npm install 当 node_modules 不存在） |
| 生产（--prod） | :5000 | 不运行 | :5000（API + SPA + 静态） | `python start.py --prod`（需 dist 已构建，或先 `python start.py build`） |

**为什么应用模式让 Vite 占 :5000 而不是 FastAPI**：见 [HANDOFF §5.9](../../HANDOFF.md)（决策）/ [HANDOFF §6.16](../../HANDOFF.md)（踩坑）。核心：让 FastAPI 反代 Vite 内部路径会失败，所以让 Vite 直接占住用户入口，FastAPI 退到 :5001 专做 API。

### 1.2.4 SPA fallback 路径排除（必读）

[app/main.py](../../app/main.py) 末尾的通配路由 `@app.get("/{path:path}")` **必须**排除以下路径（详见 [HANDOFF §6.15](../../HANDOFF.md)）：

| 路径前缀 | 用途 | 排除原因 |
|---|---|---|
| `/api/` | JSON API | 让 API 返回 HTML 会破坏 axios |
| `/static/` | 静态资源 | StaticFiles 已挂载，不应被 fallback 拦截 |
| `/admin` | 后台 SSR | 后台是 Jinja2 渲染，不是 Vue SPA |
| `/docs`、`/redoc`、`/openapi` | FastAPI 自动文档 | Swagger UI 等 |

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
| `mood_checkins.check_date` | date | 当天日期（v2.4.0 移除 `(user_id, check_date)` 唯一约束，支持**一天多条心情**记录） |
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

## 5. 前端架构（旧 Jinja2 SSR 模式，2026-07-19 v2.0 起仅 `/admin/*` 后台保留）

> **2026-07-19 v2.0 Vue 3 重构后**：本节描述的 Jinja2 SSR + 原生 HTML/CSS/JS 模式**仅保留用于 `/admin/*` 秘密后台**（有意为之的独立隔离，详见 [§6.5](#65-秘密后台架构) / [HANDOFF §5.8](../../HANDOFF.md)）。前台 13 个页面已全部迁移到 Vue 3 SPA，**新前端架构看 [§1.1 前端架构（Vue 3 SPA）](#11-前端架构vue-3-spa2026-07-19-v20-加)**。
>
> 本节内容仍适用：
> - 后台 `/admin/*` 7 个页面（继承 `admin/_base.html`，见 [§5.1 模板继承](#51-模板继承)）
> - 后台 CSS（[static/css/07-admin.css](../../static/css/07-admin.css)，见 [§5.2 CSS 模块化](#52-css-模块化)）
> - 后台 JS（`static/js/pages/admin_*.js`，见 [§5.3 JS 模式](#53-js-模式)）
>
> ⚠️ 前台模板 [templates/](../../templates/) 与 [static/css/](../../static/css/)、[static/js/](../../static/js/) 在 v2.0 后**仅作历史参考保留**，不再被生产路径加载（生产走 `static/dist/index.html` Vue 3 SPA）。改动前台请走 [`frontend/src/`](../../frontend/src/)，本节规则不再适用。

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
  ├── mood_calendar.html      ← 情绪日历（今日打卡仅选表情 + 月历 + 30 天趋势；2026-07-16 会话 6 合并原 /mood 打卡页 / 会话 7 删文本输入、日历 emoji 替代数字）
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

**字体加载（国内镜像）**：[templates/base.html](../../templates/base.html) + [templates/admin/_base.html](../../templates/admin/_base.html) 通过 `fonts.loli.net` / `gstatic.loli.net`（Google Fonts 国内镜像）加载 Noto Sans/Serif SC，国内可访问（原 `fonts.googleapis.com` / `fonts.gstatic.com` 被墙会 ERR_CONNECTION_REFUSED）；CSS 变量 `--font-sans` / `--font-serif`（[static/css/00-variables.css](../../static/css/00-variables.css)）里有 `"PingFang SC", "Microsoft YaHei"` 等系统字体兜底，镜像挂了也不会变方块字。

### 5.2 CSS 模块化

```
style.css                 ← 前台入口
  @import 00-variables.css  ← 颜色 / 字体 / 间距 变量
  @import 01-reset.css      ← 重置 + body 渐变背景
  @import 02-layout.css     ← 容器 / 导航 / 网格
  @import 03-components.css ← 按钮 / 卡片 / Toast / 表单
  @import 04-pages.css      ← 页面专属样式
  @import 05-animations.css ← 动效（漂流瓶 / 心情弹跳 / 花朵生长 / §2 交互增强：滚动渐显 reveal / 卡片光泽 sheen / 涟漪 ripple / 计数 countup / 花瓣 petal / 频谱 eq-bars / 页面过渡 / 标题流光）
  @import 06-music.css      ← 沉浸式播放器
  @import 07-admin.css      ← 【后台专属】暗色侧栏 / 表格 / 模态
```

**为什么分 8 个**：
- 每个文件 < 300 行
- 改颜色只动 `00-variables.css`，全局生效
- 改动效只动 `05-animations.css`
- 浏览器只缓存变化的文件
- **07-admin.css 独立** —— 后台样式变了不影响前台；不加载 `style.css` 不会拖累后台首屏

**iOS Safari 兼容约定**（2026-07-15 会话 5 踩坑，详见 [DEVELOPMENT §3.11](DEVELOPMENT.md)）：
- 视口高度一律用 `100dvh`（带 `100vh` 兜底，写在下一行覆盖）—— iOS Safari 的 `100vh` 含地址栏，会遮挡底部内容、滚动时跳变
- body 已加 `isolation: isolate` 建立根 stacking context —— 让 `.bg-orb / .petal-layer` 等负 z-index 的 `position: fixed` 层在 iOS 上绘制顺序稳定（落在背景之上、内容之下）
- sticky / fixed 底部元素（如 `.player`、`.tabbar`）所在的页面，容器底部 `padding` 必须 ≥ 该元素高度 + `bottom offset + env(safe-area-inset-bottom)`，否则最后一项内容被盖住点不到
- **顶部导航避让刘海/灵动岛**（2026-07-16 会话 7 加）：`.nav` 加 `padding-top: env(safe-area-inset-top)`；移动端 `@media (max-width: 720px)` nav 高度压到 52px、隐藏 `.nav__nickname`、加大「离开」按钮点击区域，解决苹果用户反馈「导航栏占太大屏幕」

### 5.3 JS 模式

`window.QI` 全局（[static/js/app.js](../../static/js/app.js)）暴露：
- `QI.toast(msg, type)` — 治愈系 Toast
- `QI.confirmThen(msg, fn)` — 二次确认（柔和版）
- `QI.fetchJSON(url, opts)` — fetch 包装，自动带 cookie
- `QI.floatEnergy(text, fromEl)` — 能量飞升动效
- 交互增强（参考 Netflix / Spotify，适配治愈系，全部遵守 `prefers-reduced-motion`）：
  - `QI.initAll()` — `DOMContentLoaded` 自动初始化以下全部效果（app.js 末尾自动调用）
  - `QI.initReveal()` — `.reveal` 元素进入视口加 `.is-visible`（IntersectionObserver）
  - `QI.initRipple()` — `.btn` 点击涟漪（事件委托，动态按钮也生效）
  - `QI.initPasswordToggle()` — `.password-toggle` 👁/🙈 切换密码明文/掩码（事件委托，动态生成的日记解锁 modal 也生效，2026-07-16 会话 7 加）
  - `QI.initCountUp()` — `[data-countup]` 进入视口从 0 缓动到目标值
  - `QI.initPetals()` — 含 `.hero` 的页面在 `.petal-layer` 生成环境花瓣
  - `QI.initPageTransition()` — `<main class="page-transition">` 进入淡入
  - `QI.countUp(el, target, opts)` — 立即数字缓动
  - `QI.confetti(fromEl, opts)` — 花瓣撒落（兑换 / 打卡成功反馈）
  - `QI.prefersReducedMotion()` — 无障碍检测

页面 JS（[static/js/pages/](../../static/js/pages/)）只做：
1. 监听 DOM 事件
2. 调 `QI.fetchJSON('/api/...')`
3. 更新 DOM

**不**引入任何框架（React/Vue/Tailwind），**不**打包，**不**用 npm。

> **`.reveal` 使用约定**：只加在**容器**（如 `.yin-grid / .module-row / .music-detail__list`）上，**不要**直接加在 `.yin-card / .module-card / .song-item / .card` 等带 hover transform 的卡片上 —— `.reveal.is-visible` 的 `transform` 会覆盖 hover 的 transform（同特异性，后定义胜出）。容器级揭示是 Netflix 行卡片的惯用语言，也避免冲突。

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

## 6.6 AI 层架构（2026-07-17 加，可选）

> 设计原则：**「渐进增强」+「不污染数据」+「治愈系温柔语气」** —— AI 是「锦上添花」而非核心功能，没配 key 也能跑；AI 文案永不入库，与日记端到端加密一脉相承。

### 6.6.1 模块组成

| 层 | 文件 | 说明 |
|---|---|---|
| 配置 | [app/config.py](../../app/config.py) | `Settings` 类新增 `nvidia_api_key` / `ai_model` / `ai_base_url` 3 字段，从 `.env` 读 |
| Schema | [app/schemas/ai.py](../../app/schemas/ai.py) | 7 个 Pydantic 模型：`ChatMessage` / `AIChatIn` / `AIChatOut` / `AIEncouragementIn` / `AIHealingIn` / `AIMusicRecommendIn` / `AIMusicRecommendOut`；已注册到 [app/schemas/__init__.py](../../app/schemas/__init__.py) 的 `__all__` + `model_rebuild()` |
| Service | [app/services/ai_service.py](../../app/services/ai_service.py) | `AIServiceUnavailable` 异常 + 4 个系统提示词常量 + `_call_nvidia()` 底层同步调用 + 4 个上层方法 |
| Router | [app/routers/ai.py](../../app/routers/ai.py) | 4 个端点（全部 `Depends(get_current_user)` + 全部 try/except 降级），prefix=`/api/ai` |
| 入口注册 | [app/main.py](../../app/main.py) | `app.include_router(ai.router, prefix="/api/ai")` |
| 外部依赖 | NVIDIA NIM API | `https://integrate.api.nvidia.com/v1/chat/completions`（OpenAI 兼容格式），模型 `meta/llama-3.1-8b-instruct`（8B，`_call_nvidia` 60s 超时兜底；原默认 `nvidia/llama-3.1-nemotron-70b-instruct` 在用户账户下 404 不可用，见 [HANDOFF §5.7](../../HANDOFF.md)） |
| 依赖 | [requirements.txt](../../requirements.txt) | 新增 `httpx>=0.27.0,<0.29.0` |

### 6.6.2 调用流（4 个场景同构）

```
浏览器                          FastAPI                          NVIDIA NIM
  │                                │                                │
  │ POST /api/ai/<scene>           │                                │
  │ Cookie: qi_session=...         │                                │
  │ { ... 入参 ... }               │                                │
  ├───────────────────────────────→│                                │
  │                                │ 1. get_current_user 鉴权        │
  │                                │ 2. try:                         │
  │                                │    ai_service.generate_xxx()    │
  │                                │    → _call_nvidia(              │
  │                                │        system_prompt,           │
  │                                │        user_content,           │
  │                                │        history=...,             │
  │                                │      )                          │
  │                                │    ────────────────────────────→│
  │                                │    POST /chat/completions       │
  │                                │    Authorization: Bearer        │
  │                                │      ${QI_NVIDIA_API_KEY}      │
  │                                │  ←─────── 200 + AI 文案 ────────│
  │                                │ 3. except AIServiceUnavailable: │
  │                                │    return available:false + 友好提示
  │                                │                                │
  │ ←─ 200 { available:true/false, message }                        │
  │                                │                                │
```

### 6.6.3 4 个场景

| # | 场景 | 端点 | 前端集成点 | AI 文案去向 |
|---|---|---|---|---|
| 1 | AI 树洞对话 | `POST /api/ai/chat` | [templates/ai_chat.html](../../templates/ai_chat.html) + [static/js/pages/ai_chat.js](../../static/js/pages/ai_chat.js)，独立页面 `/ai-chat`，多轮对话 | 仅浏览器内存，刷新清空，**不落库** |
| 2 | 漂流瓶 AI 鼓励语 | `POST /api/ai/encouragement` | [templates/pick_bottle.html](../../templates/pick_bottle.html) `#ai-encouragement` + [static/js/pages/pick.js](../../static/js/pages/pick.js) `loadAIEncouragement` | 给读者看的现场文案，**不写库**，不污染作者收件箱；日记内容传 AI 时**只取前 120 字** |
| 3 | 情绪日历 AI 治愈语 | `POST /api/ai/healing` | [templates/mood_calendar.html](../../templates/mood_calendar.html) `#ai-healing-msg` + [static/js/pages/mood_calendar.js](../../static/js/pages/mood_calendar.js) `loadAIHealing` | 显示在今日心情卡片下方，**不落库** |
| 4 | 音乐 AI 心情推荐 | `POST /api/ai/recommend-music` | [templates/index.html](../../templates/index.html) 「AI 帮我选音」卡片（仅登录可见）+ [static/js/pages/home.js](../../static/js/pages/home.js)（新建） | 返回宫商角徵羽之一 + 理由 + 跳转 `/music/{yin}` 链接；service 层有容错 JSON 解析（处理 ```` ```json ```` 包裹、find `{` 到 `}`） |

### 6.6.4 降级策略（核心）

所有 AI 端点在以下情况返回 **200 + `available:false` + 治愈系友好提示**（**不报 500**）：
- 未配置 `QI_NVIDIA_API_KEY`（启动时检查）
- NVIDIA API 调用失败（网络 / 超时 / 限流 / 4xx / 5xx）

前端拿到 `available:false` 时**仍正常显示**提示文案，不报错。架构上意味着：

- **AI 是「渐进增强」**——没有 key 也能正常用所有功能
- **NVIDIA 限流时业务不中断**——用户只感知「AI 在休息」，不感知「故障」
- **可观测性**：失败原因走 `logger.warning`，不暴露给前端（避免泄露内部信息）

### 6.6.5 隐私承诺

| 场景 | 数据流向 | 入库？ |
|---|---|---|
| AI 树洞对话 | 浏览器内存 → POST /api/ai/chat → NVIDIA → 浏览器内存 | ❌ 不入库 |
| 漂流瓶 AI 鼓励语 | 后端读日记明文（已解密）→ **截断到前 120 字** → NVIDIA → 返回文案给读者 | ❌ 文案不入库；日记明文也不留存 |
| 情绪日历 AI 治愈语 | 心情 emoji + 可选 note → NVIDIA → 返回治愈语 | ❌ 不入库 |
| 音乐 AI 心情推荐 | 用户描述的状态文本 → NVIDIA → 返回五音之一 + 理由 | ❌ 不入库 |

**端到端加密边界依然成立**：AI 服务调日记明文时，明文只在 `generate_encouragement()` 函数栈内临时存在，函数返回即被 GC，**不写日志、不写库、不写文件**。

详见 [HANDOFF §5.7](../../HANDOFF.md) AI 接入选型理由。

---

## 7. 安全模型

### 7.1 密码
- bcrypt(rounds=12) + 72 字节截断
- 注册时存 `password_hash`，登录时 verify
- **密码输入可见性切换**（2026-07-16 会话 7 加）：登录 / 注册 / 日记解锁 modal 的密码框统一用 `.password-input-wrap` + `.password-toggle` 👁 按钮，`app.js initPasswordToggle()` 用 document-level 事件委托切换明文/掩码（👁 ↔ 🙈），动态生成的 modal 也生效

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

> 🔒 **2026-07-19 v2.0 Vue 3 重构后文档 Iron Rule 仍然适用**（6 份文档同步）：
> 完整规则见 [HANDOFF §12](../../HANDOFF.md)；本文件相关引用点 — 顶部提醒 + 本节 + [§1.1 前端架构](#11-前端架构vue-3-spa2026-07-19-v20-加) + [§1.2 开发/生产模式切换](#12-开发生产模式切换2026-07-19-v20-加) + [§5 旧 SSR 模式](#5-前端架构旧-jinja2-ssr-模式2026-07-19-v20-起仅-admin后台保留)。
> **改 Vue 3 前端代码（[`frontend/src/`](../../frontend/src/)）+ 后端 SPA fallback（[app/main.py](../../app/main.py)）= 同一 commit 同步更新 6 份文档**（README / HANDOFF / PROJECT_STATE / ARCHITECTURE / DEPLOYMENT / DEVELOPMENT），关键词 `Vue 3` / `Vite` / `SPA fallback` / `frontend/` 在 6 份文档中都要出现。**改代码不改文档 = 改了一半。**
> 同步点速查：[README §9](../../README.md) / [HANDOFF §12](../../HANDOFF.md) / [PROJECT_STATE §8](../PROJECT_STATE.md) / 本节 / [DEPLOYMENT 顶部](../DEPLOYMENT.md) / [DEVELOPMENT §1.8](DEVELOPMENT.md)。

> 🔒 **2026-07-20 v2.1 视觉增强 Iron Rule 扩展**：
> 改 4 个视觉组件（[AmbientBackground.vue](../../frontend/src/components/AmbientBackground.vue) / [HeroScene.vue](../../frontend/src/components/HeroScene.vue) / [AudioVisualizer.vue](../../frontend/src/components/AudioVisualizer.vue) / [utils/visual.js](../../frontend/src/utils/visual.js)）或 [vite.config.js](../../frontend/vite.config.js) `manualChunks` 配置 = **同一 commit 同步更新 6 份文档**，关键词 `三层渐进增强` / `AmbientBackground` / `HeroScene` / `AudioVisualizer` / `visual.js` / `shallowRef` / `smartRAF` / `prefers-reduced-motion` 在 6 份文档中都要出现。
> 4 大集成铁律（缺任何一个都会在长时间使用或多视图切换后出问题）：① `createMediaElementSource` 一次性 — AudioVisualizer `if (!sourceNode)` 守卫；② Three.js 对象用 `shallowRef` 而非 `ref`；③ rAF 必须走 `smartRAF` 而非 `requestAnimationFrame`；④ `onBeforeUnmount` 必须完整释放 geometry / material / renderer / 监听 / ResizeObserver。详见 [HANDOFF §6.23](../../HANDOFF.md)。

> 🔒 **2026-07-30 v2.3.3 Safari 兼容 Iron Rule 扩展**：
> 改视觉组件的 **Safari 兼容**逻辑（[utils/visual.js](../../frontend/src/utils/visual.js) `hasWebGL` 重写 / `getWebGLCaps` / `isSafari` / `isIOS` / [utils/three-helpers.js](../../frontend/src/utils/three-helpers.js) `webglcontextlost` / `webglcontextrestored` / [HeroScene.vue](../../frontend/src/components/HeroScene.vue) iOS 降级 Bloom 降级 + PMREM 降级 / [EmojiIcon.vue](../../frontend/src/components/EmojiIcon.vue) Iconify + twemoji SVG emoji 跨浏览器一致）= **同一 commit 同步更新 6 份文档**，关键词 `Safari 兼容` / `WebGL 上下文丢失` / `webglcontextlost` / `iOS 降级` / `EmojiIcon` / `Iconify` / `twemoji` / `SVG emoji` / `跨浏览器一致` / `hasWebGL 重写` / `getWebGLCaps` / `isSafari` / `isIOS` / `Bloom 降级` / `PMREM 降级` / `v2.3.3` 在 6 份文档中都要出现。
> Safari 兼容 3 大坑（缺任何一个都会在 Safari / iOS 上出问题）：① `webglcontextlost` / `webglcontextrestored` 上下文恢复 — iOS Safari 切后台→前台触发；② `hasWebGL` 须区分 WebGL1+2 + 检测扩展 — 老 Safari 只有 WebGL1 不能误判；③ emoji 须用 SVG 统一而非系统字体 — Apple Color Emoji vs 系统 emoji 风格差异。详见 [HANDOFF §6.24](../../HANDOFF.md)。

### 7.8 AI 隐私边界（2026-07-17 加）
> AI 接入必须**不破坏**日记端到端加密的隐私承诺。

**4 条边界**：
1. **AI 文案永不入库**——4 个 AI 场景的输出（对话历史 / 鼓励语 / 治愈语 / 推荐理由）都只在浏览器内存或一次 HTTP 响应里，**绝不**写 SQLite
2. **对话历史只在浏览器**——AI 树洞对话多轮历史存浏览器 JS 变量，刷新清空，服务端**不留存**
3. **日记明文调用 AI 时截断到前 120 字**——漂流瓶 AI 鼓励语调用 `generate_encouragement()` 时，把作者日记**只取前 120 字预览**发给 NVIDIA，减少 token + 减少隐私暴露面；明文在函数栈内临时存在，函数返回即被 GC
4. **API key 不入仓**——`QI_NVIDIA_API_KEY` 只在 `.env`（git 忽略），[.env.example](../../.env.example) 默认注释掉占位

**外部依赖边界**：
- 第三方服务：NVIDIA NIM API（`https://integrate.api.nvidia.com/v1`），用户日记内容前 120 字 + 心情 emoji + 用户描述的状态文本会发往 NVIDIA
- 将来想换自部署 vLLM / 其他厂商 → 只改 `QI_AI_BASE_URL` + `QI_AI_MODEL`，业务代码不动（OpenAI 兼容格式）
- 想完全离线（不发任何数据出去）→ **不配** `QI_NVIDIA_API_KEY`，4 个端点自动降级返回治愈系友好提示，业务正常跑

详见 [§6.6 AI 层架构](#66-ai-层架构2026-07-17-加可选) / [HANDOFF §5.7](../../HANDOFF.md)。

---

## 8. 性能

### 8.1 首屏 < 3s
- 10 个 HTML 页面共享 base.html，浏览器缓存 CSS/JS（2026-07-16 合并 /mood 打卡页后由 11 减为 10）
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
