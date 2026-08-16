# 部署指南

> 三种部署方式：**宝塔面板**（最简单，私人项目首选）、**systemd**（VPS 标准）、**手动 nohup**（临时调试）。

> 🔒 **改了本文件涉及的部署配置（端口 / Nginx / systemd / HTTPS / 反代 / 前端构建），必须同步更新**：[README §1](../../README.md) / [HANDOFF §1](../../HANDOFF.md) / [PROJECT_STATE §4](../PROJECT_STATE.md)。详见 [HANDOFF §12](../../HANDOFF.md) 文档自动同步铁律。

> 🔒 **2026-07-19 v2.0 Vue 3 重构**：部署前**必须**先 `cd frontend && npm install && npm run build`（或 `python start.py build` 一键构建）输出 `static/dist/`，否则 `python start.py` 后访问 :5000 只会看到「dist 未构建」提示页。关键词 `Vue 3` / `Vite` / `SPA fallback` / `frontend/` 在 6 份文档（README / HANDOFF / PROJECT_STATE / ARCHITECTURE / DEPLOYMENT / DEVELOPMENT）中都要出现。

> 🔒 **2026-07-19 v2.0.1 端口策略调整**：生产模式 FastAPI 监听 :5000（默认，从 `.env` 读 `QI_PORT`），Vite 不运行——**用户始终访问 :5000**；开发模式（不部署时）Vite 占 :5000，FastAPI 退到 :5001。**部署到服务器永远是生产模式**，无需关心 :5001，只需确保 `static/dist/` 已构建。关键词 `5001` / `FlowerField` / `Vite :5000` 在 6 份文档中都要出现。

> 🔒 **2026-07-20 v2.1 视觉增强**：4 个视觉组件（[AmbientBackground.vue](../frontend/src/components/AmbientBackground.vue) / [HeroScene.vue](../frontend/src/components/HeroScene.vue) / [AudioVisualizer.vue](../frontend/src/components/AudioVisualizer.vue) + [utils/visual.js](../frontend/src/utils/visual.js)）加入构建后，`three-vendor` chunk 因 HeroScene 共享而**仍只输出一个文件**（gzip 175KB），首屏不加载，仅访问 `/`（HeroScene）或 `/garden`（FlowerField）时按需拉取。**部署前必须重新 `npm run build`**，否则用户看不到 v2.1 视觉增强。关键词 `三层渐进增强` / `AmbientBackground` / `HeroScene` / `AudioVisualizer` / `visual.js` / `shallowRef` / `smartRAF` 在 6 份文档中都要出现。

> 🔒 **2026-07-20 v2.2 3D 元素与动效全面重构**：4 个视觉组件全部升级到 PBR 渲染管线（`UnrealBloomPass` + `RoomEnvironment` PMREM + ACESFilmic 色调映射），新增 [utils/three-helpers.js](../frontend/src/utils/three-helpers.js) PBR 工具集 + [SceneHint.vue](../frontend/src/components/SceneHint.vue) 交互指引 + [SceneControls.vue](../frontend/src/components/SceneControls.vue) 视图控制。构建产物体积变化：HeroScene 7.5KB → 13.54KB、FlowerField 单独 chunk 9.94KB、SceneControls 4.5KB、three-vendor 175KB → 719.84KB（含 addons：OrbitControls / EffectComposer / UnrealBloomPass / RoomEnvironment）。**部署前必须重新 `npm run build`**，否则用户看不到 v2.2 PBR 升级 + 交互指引。关键词 `PBR` / `three-helpers` / `SceneHint` / `SceneControls` / `OrbitControls` / `raycaster` / `UnrealBloomPass` / `RoomEnvironment` / `LatheGeometry` 在 6 份文档中都要出现。

> 🔒 **2026-07-25 v2.2.2 start.py 默认应用模式**：`python start.py`（无参数）默认行为变更——**默认走应用/开发模式**（前后端一起起：Vite :5000 HMR + FastAPI :5001 API），自动检测 `frontend/node_modules` 不存在则 `npm install`（约 7 分钟，仅首次）。新增 `--prod` 参数显式生产模式（FastAPI :5000 单进程，需 dist 已构建，部署用）。`--dev` 保留为兼容别名（等同默认行为）。**服务器部署只需 3 步**：① 上传代码 ② 装 Python 依赖 + Node.js 18+ ③ `python start.py`（首次自动 npm install，之后秒启，默认 Vite :5000 + FastAPI :5001）。生产部署可选 `python start.py build && python start.py --prod`（构建 dist + 单进程模式，端口代理 :5000 永远指向 FastAPI，不需要 Node.js 运行时）。关键词 `--prod` / `默认应用模式` / `自动 npm install` / `前后端一起起` 在 6 份文档中都要出现。

> 🔒 **2026-07-25 v2.2.3 移动端响应式 UI + 3D 几何降档**：三档断点系统（≤768px 手机 / 769-1024px 平板 / ≥1025px 桌面）差异化布局 + iOS Safari `100dvh` + `env(safe-area-inset-*)` 适配 + `fullscreen` 路由模式 + 4 个 3D 组件移动端几何精度降档（Lathe/Cylinder/Icosahedron 段数降低、樱花树深度 4→3、花瓣网格 5×8→4×6、AudioVisualizer 柱数减半）。**部署前必须重新 `npm run build`**，否则用户拿不到移动端布局优化 + 3D 几何降档。关键词 `三档断点` / `100dvh` / `safe-area-inset` / `fullscreen` / `几何精度降档` / `iPhone 16` 在 6 份文档中都要出现。

> 🔒 **2026-07-25 v2.3 六大四字名板块 + 双资源系统 + 花朵生命周期 + 通知 + 个人主页 + 古琴弹西洋曲谱**：① **部署前必须重新 `npm run build`**，否则用户拿不到新视图（MusicWesternView / ProfileView / NotificationsView）+ 双资源 UI + 通知铃铛 + 花田生长网格；② 数据库**自动迁移**（`_migrate_legacy_columns()` 一次性加 5 个新列：`users.leaves` + `diaries.content/send_to_ai_hole` + `shop_items.cost_currency` + `musics.category`），**不需要手动 ALTER TABLE**；新表 `user_flowers` / `notifications` 由 `init_db()` 自动建表；③ seed **按 title 幂等**自动补齐 6 首西方改编曲目（绿袖子/卡农/致爱丽丝/月光奏鸣曲/天鹅湖/昨日重现），老库重启即生效；④ pre-commit 5 项 checklist 正式化（Pydantic Out / `_migrate_legacy_columns` / `constants.py` / `.env.example` / README+HANDOFF 速查表）。关键词 `双资源` / `露水` / `落叶` / `UserFlower` / `Notification` / `ProfileView` / `古琴弹西洋曲谱` / `send_to_ai_hole` / `树洞` / `漂流瓶社交` / `琴音疗心` / `pre-commit 5 项` 在 6 份文档中都要出现。

> 🔒 **2026-07-28 v2.3.2 start.py 默认生产模式 + 自动构建简化**：`python start.py` 默认行为**再次变更**（回滚 v2.2.2「默认应用模式」）——**默认走生产模式**（FastAPI :5000 单进程，前后端不再一起起），需 `static/dist/` 已构建（不存在则自动 `npm install + npm run build`）。**`dist 存在检测`**——仅检测 `static/dist/index.html` 存在性，不再比较 `frontend/src/` 与 `static/dist/` 文件修改时间；**`自动构建`**：dist 不存在时自动 `npm install + npm run build`（需 Node.js 18+）。开发需显式 `python start.py --dev`（Vite :5000 HMR + FastAPI :5001 API，前后端一起起的「应用模式」）。`--prod` 改为兼容别名（默认就是生产模式）。**服务器部署简化为 2 步**：① 上传代码 ② `python start.py`（首次自动构建，之后秒启，FastAPI 单进程 :5000）。回滚理由：服务器端口代理已配好 :5000 不能动，应用模式会让 Vite 占 :5000 破坏代理。关键词 `默认生产模式` / `dist 存在检测` / `自动构建` / `--dev` / `应用模式` / `v2.3.2` 在 6 份文档中都要出现。

> 🔒 **2026-07-30 v2.3.3 Safari 兼容性修复（3D 上下文恢复 + emoji 跨浏览器一致）**：① **部署前必须重新 `npm run build`**，否则 Safari / iOS 用户拿不到 **Safari 兼容**修复——主页 3D 浮岛不渲染（`hasWebGL` 误判 + `webglcontextlost` 无恢复 + Bloom/PMREM 内存超限）+ emoji 风格不一致（Apple Color Emoji vs 系统 emoji）。修复：[utils/visual.js](../frontend/src/utils/visual.js) **`hasWebGL` 重写**（区分 WebGL1/2 + 检测扩展 + max texture size）+ 新增 `getWebGLCaps()` / `isSafari()` / `isIOS()`；[utils/three-helpers.js](../frontend/src/utils/three-helpers.js) 添加 `webglcontextlost` / `webglcontextrestored` 事件监听处理 **WebGL 上下文丢失**；[HeroScene.vue](../frontend/src/components/HeroScene.vue) **iOS 降级**（**Bloom 降级**：iOS 关闭 UnrealBloomPass；**PMREM 降级**：iOS PMREM 256→128、阴影 2048→1024、dpr 2→1.5）；新建 [EmojiIcon.vue](../frontend/src/components/EmojiIcon.vue) 组件用 **Iconify** + `@iconify-json/twemoji` 离线 **SVG emoji**，确保 **跨浏览器一致**，替换 AppLayout.vue + ProfileView.vue 所有 emoji。构建 209 modules / 12.30s，HeroScene +0.71KB（降级逻辑）。无数据库迁移 / 无新依赖（Iconify + twemoji 已在 frontend/package.json）。关键词 `Safari 兼容` / `WebGL 上下文丢失` / `webglcontextlost` / `iOS 降级` / `EmojiIcon` / `Iconify` / `twemoji` / `SVG emoji` / `跨浏览器一致` / `hasWebGL 重写` / `getWebGLCaps` / `isSafari` / `isIOS` / `Bloom 降级` / `PMREM 降级` / `v2.3.3` 在 6 份文档中都要出现。

> 🔒 **2026-08-10 v2.4.0 UI/UX 18 项调整 + 头像/昵称编辑 + 一天多条心情 + 花坊改名 + 静屿使用指南**：① **部署前必须重新 `npm run build`**，否则用户拿不到 v2.4.0 新功能——首页文案改为「**潮声不止心安自屿**」（删「静屿」副标题 + 删今日打卡板块）+ 漂流日记入口统一显示「日记海岸」（含拾瓶/写日记）+ 情绪日历 emoji 显示/选择修复 + **一天多条心情**记录（情绪是多变的）+ 30 天心情趋势 1-5 评分多条取**平均分**（ecstatic=5/happy=4/calm=3/tired=2/anxious=2/angry=1/sad=1）+ 心语树洞 AI 系统提示词 **humanize**（更接地气、像朋友聊天）+ 「落叶画坊」→「**花坊**」改名 + 花种扩充至 12 种（向日葵/竹子/雏菊/莲花/薰衣草/郁金香/梅花/桃花/兰花/青松/桂花/银杏）+ 新装扮（油纸伞/蓑衣/乌篷船/鱼竿/橘猫/白鹤）+ 「古琴初学者」→「**琴音知音**」徽章改名 + **每板块徽章**（琴音知音/日记达人/七日静心/拾瓶旅人/树洞倾心/花田主人）+ 「竹编帽」描述改为「种花人遮阳的草帽」+ 花田 AI 基于实际种花情况（没种花不显示）+ 「我的」页面修复（收到鼓励/岛上物件可点击跳转 + 删重复岛上物件 + 新增**静屿使用指南**详细介绍所有模块）+ **头像/昵称修改**（[ProfileView.vue](../../frontend/src/views/profile/ProfileView.vue) 编辑弹窗 24 个可选 emoji）+ **露水累加修复**（写日记和留言鼓励后正确发放露水）；② 数据库**自动迁移**（`_migrate_legacy_columns()`）：① `users.avatar` 加列（`ALTER TABLE users ADD COLUMN avatar VARCHAR(16) DEFAULT '🙂' NOT NULL`，**User.avatar** 默认 🙂，与树洞显示一致）② **mood_checkins 唯一约束移除**（SQLite 重建表方式：CREATE TABLE _new AS SELECT * → DROP → RENAME → CREATE INDEX，支持一天多条心情记录）；③ 新增 schema 文件 [app/schemas/profile.py](../../app/schemas/profile.py) + `ProfileUpdateIn`（nickname 2-20 字符可选 / avatar 1-16 字符可选）；④ 新增 router **PATCH /api/profile**（更新头像/昵称，昵称查重 409，**头像同步树洞**显示——[AIChatView.vue](../../frontend/src/views/ai/AIChatView.vue) 用 `userStore.avatar`）；⑤ service 重构 [app/services/mood_service.py](../../app/services/mood_service.py)：`upsert_checkin` → `add_checkin`（不再 UPSERT，允许一天多条）+ 新增 `get_today_moods`（获取今日所有心情）+ `get_recent_trend` 多条取**平均分**；⑥ seed 更新：[DEFAULT_SHOP_ITEMS](../../app/utils/constants.py) 扩充至 27 件（12 花种 + 9 装扮 + 6 徽章），「古琴初学者」→「琴音知音」，「竹编帽」描述更新，新增 6 件装扮；⑦ 前端 stores/user.js 新增 `updateProfile` action。无数据库手动 ALTER / 无新前端依赖（Iconify + twemoji 已在 v2.3.3 加入）。关键词 `v2.4` / `潮声不止心安自屿` / `花坊` / `一天多条心情` / `mood_checkins 唯一约束移除` / `add_checkin` / `get_today_moods` / `平均分` / `humanize` / `琴音知音` / `每板块徽章` / `User.avatar` / `PATCH /api/profile` / `ProfileUpdateIn` / `头像同步树洞` / `静屿使用指南` / `露水累加修复` 在 6 份文档中都要出现。

> 🔒 **2026-08-10 v2.4.1 情绪日历罗素情绪环模型四象限图表**：① **部署前必须重新 `npm run build`**，否则用户拿不到情绪环模型图表（[MoodCalendarView.vue](../../frontend/src/views/mood/MoodCalendarView.vue) 移除 30 天趋势柱状图，新增罗素情绪环模型四象限图表——横轴效价 Valence 左消极→右积极 / 纵轴唤醒度 Arousal 下低唤醒→上高唤醒 / 四象限 Q1积极+高唤醒 · Q2消极+高唤醒 · Q3消极+低唤醒 · Q4积极+低唤醒 / `CIRCUMPLEX_EMOTIONS` 20 种情绪 / 点击 emoji 弹详情卡片显示「本月出现 X 次」）；② **无后端改动**（纯前端变更，[app/](../../app/) 下无任何 Python 代码改动）；③ **无数据库迁移**（不涉及 `_migrate_legacy_columns()`，`mood_checkins` 表结构不变，沿用 v2.4.0 的多条心情记录模型）；④ **无新依赖**（`frontend/package.json` 无新增，GSAP / Vue 3 已在依赖中）；⑤ `fetchTrend` 仍调用（为 `currentStreak` 连续打卡天数显示），`trend` 数据不再用于渲染。关键词 `v2.4.1` / `Russell情绪环模型` / `Circumplex Model` / `四象限图表` / `效价Valence` / `唤醒度Arousal` / `CIRCUMPLEX_EMOTIONS` / `emotionPosition` / `moodCounts` / `20种情绪` / `点击交互` / `本月出现次数` 在 6 份文档中都要出现。

> 🔒 **2026-08-13 v2.4.2 整体架构优化与冗余清理（维护性清理版本，无部署迁移）**：本次为维护性清理版本，**无功能变化 / 无数据库迁移 / 无新依赖 / 无需重新 `npm run build`**（前端无改动），纯清理 + 一致性对齐。① **无需重新构建前端**——本次改动不涉及 `frontend/src/`，`static/dist/` 沿用 v2.4.1 构建产物即可；删除的是 Vue 3 SPA 迁移前的旧 Jinja2 SSR 死模板（[templates/](../../templates/) 下 15 个 `.html` + `templates/partials/` 空目录，`死模板清理`）+ 死页面脚本（[static/js/pages/](../../static/js/pages/) 下 10 个非 admin `.js`，`死页面脚本`），仅保留 [templates/admin/](../../templates/admin/)（[admin_pages.py](../../app/routers/admin_pages.py) 仍用 Jinja2 SSR）。② **无数据库迁移**——不改后端模型 / 不改 API / 不改 service / 不改 `_migrate_legacy_columns()`。③ **无新依赖**——[requirements.txt](../../requirements.txt) / `frontend/package.json` 均不动。④ **[app/main.py](../../app/main.py) 版本号 1.0.0 → 2.4.2**（`版本号对齐`）+ `EXT_TO_MIME` 删除重复 `.webp` 条目（`EXT_TO_MIME`）。⑤ **过时端口注释修复**（`过时注释`）：[app/routers/pages.py](../../app/routers/pages.py) / [frontend/vite.config.js](../../frontend/vite.config.js) / [static/js/app.js](../../static/js/app.js) 中 `:5173 → :5000`（Vite）/ `:5000 → :5001`（FastAPI 开发），与实际端口策略一致。⑥ **新增 5 个五音封面 SVG**（`SVG封面`）：[static/img/cover_gong.svg](../../static/img/cover_gong.svg) / `cover_shang.svg` / `cover_jue.svg` / `cover_zhi.svg` / `cover_yu.svg`，修复 [app/seed.py](../../app/seed.py) 引用的缺失资源。⑦ **[app/routers/admin_pages.py](../../app/routers/admin_pages.py) admin_users N+1 查询优化**（`N+1优化` / `GROUP BY`）：151 次→4 次查询。**服务器部署**：直接 `python start.py`（dist 沿用 v2.4.1 构建产物，无需重新 build），首次重启自动应用清理。关键词 `v2.4.2` / `死模板清理` / `死页面脚本` / `N+1优化` / `GROUP BY` / `SVG封面` / `EXT_TO_MIME` / `版本号对齐` / `过时注释` 在 6 份文档中都要出现。

> 🔒 **2026-08-14 v2.4.3 花语文案焕新 + emoji 名称对齐 + 徽章奖励落叶 + 树洞三层回复 + 情绪日历空 bug 修复（内容运营 + Bug 修复版本，部署需重新 build）**：本次为内容运营 + Bug 修复版本，**无新依赖**，但**前端有改动，部署前必须重新 `npm run build`**，否则用户拿不到 v2.4.3 新文案 / emoji 修正 / 落叶 toast / 情绪日历修复 / 花田 AI 条件渲染。① **部署前必须重新 `npm run build`**——前端涉及 [HomeView.vue](../../frontend/src/views/HomeView.vue)（首页 emoji 🏝️→🌊 + 模块名「花坊」→「落叶花坊」+ 漂流瓶 🍶→🏺）+ [MoodCalendarView.vue](../../frontend/src/views/mood/MoodCalendarView.vue)（可选链修复空白 + 落叶/徽章 toast）+ [GardenView.vue](../../frontend/src/views/garden/GardenView.vue)（花田 AI `v-if="flowers.length > 0"` + 「岛上物件🏝️」+ 「落叶花坊」改名）+ [ShopView.vue](../../frontend/src/views/shop/ShopView.vue) / [ProfileView.vue](../../frontend/src/views/profile/ProfileView.vue)（文案改名）+ [EmojiIcon.vue](../../frontend/src/components/EmojiIcon.vue)（🌊 / 🏺 映射）+ 各 View 的落叶/徽章 toast；② **数据库自动迁移**（无需手动 ALTER）——seed.py 启动时自动执行 `RENAME_MAP` 改名迁移（桂花→小麦 / 银杏→青叶 / 兰花+梅花→樱花去重 / 白鹤→火烈鸟 / 蓑衣→斗篷 / 花田主人→花间客）+ 删除「古琴初学者」废弃徽章（含 GardenItem 引用清理），老库重启即生效；③ **无新依赖**——[requirements.txt](../../requirements.txt) / `frontend/package.json` 均不动；④ **不改后端模型结构**——不新增表 / 不新增列 / 不改 `_migrate_legacy_columns()`，仅 [constants.py](../../app/utils/constants.py) 新增 `BADGE_LEAF_REWARD=10` 常量 + [energy_service.py](../../app/services/energy_service.py) `check_achievements` 返回值新增 `new_badges` / `new_leaves` / `leaves_balance` 三个字段；⑤ **服务器部署**：`python start.py build && python start.py --prod`（重新构建 dist + 单进程模式），或 `python start.py`（应用模式，自动 HMR）。关键词 `v2.4.3` / `花语化` / `emoji对齐` / `BADGE_LEAF_REWARD` / `落叶死锁解除` / `树洞三层回复` / `情绪日历空bug` / `花田AI` / `改名迁移` / `落叶花坊` / `花间客` 在 6 份文档中都要出现。

> 🔧 **2026-08-15 v2.4.3 补丁（首页滚动提示可点击）**：[HomeView.vue](../../frontend/src/views/HomeView.vue) Hero 底部滚动提示改为可点击 `<button>`（原 `pointer-events:none` 点击无反应），文案「向下沉入海面」→「向下，遇见岛上的去处」。纯前端交互修复，**部署需重新 `npm run build`**。

> 🔒 **2026-08-15 v2.4.4 情绪日历透明修复 + 旧版日记迁移 + mood_checkins 主键重建 + 头像图片上传 + 落叶花坊文案打磨（Bug 修复 + 功能增强版本，部署需重新 build + 数据库迁移）**：本次为 Bug 修复 + 功能增强版本，**无新依赖**，但**前端 + 后端均有改动，部署前必须重新 `npm run build`，且数据库迁移在启动时自动执行**（`_migrate_legacy_columns()` + `mood_checkins` 表重建）。① **部署前必须重新 `npm run build`**——前端涉及 [MoodCalendarView.vue](../../frontend/src/views/mood/MoodCalendarView.vue)（移除 GSAP `opacity:0` 透明 bug + 情绪日历使用指南改罗素情绪环模型）+ [ProfileView.vue](../../frontend/src/views/profile/ProfileView.vue)（头像上传按钮 + 图片渲染）+ [AIChatView.vue](../../frontend/src/views/ai/AIChatView.vue)（图片头像渲染）+ [GardenView.vue](../../frontend/src/views/garden/GardenView.vue)（岛上物件 emoji 🎁→🧳）+ 通知 emoji 统一 💛；② **数据库自动迁移**（无需手动 ALTER）——`_migrate_legacy_columns()` 启动时自动执行：`mood_checkins` 表重建（`CREATE TABLE AS SELECT` 丢主键 → `id INTEGER PRIMARY KEY AUTOINCREMENT` + FK + 索引，数据完整迁移）+ `User.avatar` 字段长度 `String(16)` → `String(255)`（SQLite 重建表方式 ALTER）+ 旧版加密日记 `content` 空字段自动填入提示文本「（这段日记来自旧版本，内容已无法读取）」；③ **`static/uploads/avatars/` 目录自动创建**——`POST /api/profile/avatar` 上传端点首次调用时 `os.makedirs(exist_ok=True)` 自动创建目录，**部署无需手动 mkdir**；④ **无新依赖**——[requirements.txt](../../requirements.txt) / `frontend/package.json` 均不动；⑤ **服务器部署**：`python start.py build && python start.py --prod`（重新构建 dist + 单进程模式），或 `python start.py`（应用模式，自动 HMR）；首次启动时自动执行数据库迁移（`mood_checkins` 重建 + `avatar` 字段扩展 + 旧版日记填充）。关键词 `v2.4.4` / `情绪日历透明修复` / `旧版日记迁移` / `mood_checkins 主键重建` / `avatar 字段长度` / `头像图片上传` / `花朵介绍` / `徽章落叶分级` / `情绪日历指南` / `岛上物件 emoji` / `通知 emoji 统一` 在 6 份文档中都要出现。

---

> 🔒 **2026-08-16 v2.4.5 情绪日历 30 天趋势柱状图恢复 + 罗素情绪环显示修复 + 头像相册选择 + 通知空状态 emoji 统一（Bug 修复版本，部署需重新 build）**：本次为 Bug 修复版本，**纯前端改动（3 个文件），无后端改动 / 无数据库迁移 / 无新依赖**，但**前端有改动，部署前必须重新 `npm run build`**。① **部署前必须重新 `npm run build`**——前端涉及 [MoodCalendarView.vue](../../frontend/src/views/mood/MoodCalendarView.vue)（恢复 30 天趋势柱状图 + GSAP 动画只保留位移）+ [ProfileView.vue](../../frontend/src/views/profile/ProfileView.vue)（移除 `capture="environment"`，头像支持相册选择）+ [NotificationsView.vue](../../frontend/src/views/notification/NotificationsView.vue)（空状态 emoji 🌙→💛）；② **无数据库迁移**——不涉及 `_migrate_legacy_columns()` / 不改表结构 / 不改 API；③ **无新依赖**——[requirements.txt](../../requirements.txt) / `frontend/package.json` 均不动；④ **版本号**：[app/main.py](../../app/main.py) 2.4.4 → 2.4.5（`版本号对齐`）；⑤ **服务器部署**：`python start.py build && python start.py --prod`（重新构建 dist + 单进程模式），或 `python start.py`（首次检测 dist 已存在则直接启动）。关键词 `v2.4.5` / `30天趋势柱状图恢复` / `罗素情绪环显示修复` / `头像相册选择` / `通知空状态emoji` 在 6 份文档中都要出现。

---

> 🔊 **2026-08-16 v2.4.6 五音音频真实化（部署须知：音频文件更新 + 数据迁移自动执行）**：本次为历史遗留清理版本，**无新依赖、无需重新 npm run build（前端零改动）**，但有以下部署要点：① **静态音频文件更新**——`static/audio/` 下 5 个假 MP3 占位删除，新增 5 个真实 WAV（Karplus-Strong 合成古琴五音，各 78 秒 / 3.4MB，共约 17MB，git 拉取后自动就位）；② **数据迁移自动执行**——重启后端时 `_migrate_legacy_columns()` 自动把 `musics.audio_url` 从 `.mp3` 切到 `.wav`（幂等，日志可见 `[MIGRATE] musics.audio_url 已切换`），**无需手动操作**；③ **音频误删恢复**——运行 `python scripts/generate_audio.py` 一键重新生成 5 个 WAV（纯标准库零依赖，固定种子输出一致）；④ **版本号**：[app/main.py](../../app/main.py) 2.4.5 → 2.4.6（`版本号对齐`）；⑤ **服务器部署**：`python start.py`（静态文件 + 迁移全自动，无需 build）。关键词 `v2.4.6` / `五音音频合成` / `Karplus-Strong` / `audio_url切wav` 在 6 份文档中都要出现。

---

## 前端构建（v2.0 Vue 3 重构后必做，所有部署方式通用）

> 2026-07-19 v2.0 全站 Vue 3 重构后，前台从 Jinja2 SSR 迁移到 Vue 3 SPA。**部署前必须先构建前端**，否则访问 :5000 只看到「dist 未构建」提示页。

> 2026-07-19 v2.0.1 起 [start.py](../../start.py) 新增 `build` 子命令：`python start.py build` 一键执行 `npm install && npm run build`（自动检测 Node 是否装好 + 自动 cd frontend + 输出到 ../static/dist/），推荐用此方式。

### 构建步骤

#### 方式 A：一键构建（推荐 ⭐）

```bash
# 一键执行 npm install + npm run build，输出到 static/dist/
python start.py build
```

[start.py](../../start.py) 的 `build` 子命令内部做了 3 件事：
1. 检查 `frontend/node_modules/` 是否存在，不存在自动 `npm install`
2. 执行 `npm run build`（Vite 5 + Rollup）
3. 输出到 `../static/dist/`（即 [static/dist/](../../static/dist/)）

#### 方式 B：手动两步

```bash
# 1. 确保已装 Node.js 18+（推荐 20 LTS）
node --version    # 应 >= v18

# 2. 进入前端目录
cd frontend

# 3. 安装依赖（首次：含 three.js 等大包，约 7 分钟，详见 [HANDOFF §6.14](../../HANDOFF.md)）
npm install

# 4. 构建（Vite 5 + Rollup，输出到 ../static/dist/）
npm run build
```

构建成功后会看到：
```
vite v5.x.x building for production...
✓ N modules transformed.
dist/index.html                  ← ../static/dist/index.html
dist/assets/index-xxxxxx.js      ← Vue 3 + 依赖 chunk
dist/assets/three-vendor-*.js    ← Three.js + addons 单独 chunk（v2.2 起 /garden FlowerField + / HeroScene + AmbientBackground 共享，gzip 719.84KB，含 OrbitControls / EffectComposer / UnrealBloomPass / RoomEnvironment，首屏不加载）
dist/assets/gsap-vendor-*.js     ← GSAP 单独 chunk
dist/assets/vue-vendor-*.js      ← Vue 3 + Vue Router + Pinia 单独 chunk（v2.0.1 加 manualChunks 分包）
dist/assets/HeroScene-*.js       ← 首页 Hero 区 3D 浮岛雾海 v2 组件（v2.1 加 7.5KB → v2.2 PBR 升级 13.54KB，仅 / 按需加载）
dist/assets/FlowerField-*.js     ← 3D 花田 v2 组件（v2.2 PBR 升级，9.94KB，仅 /garden 按需加载）
dist/assets/SceneControls-*.js   ← 3D 场景视图控制工具栏（v2.2 加，4.5KB，被 HeroScene / FlowerField 引用）
dist/assets/AudioVisualizer-*.js ← 音波可视化 v2 组件（4 模式 + 节拍检测，仅 /music/:yin 按需加载）
dist/assets/index-xxxxxx.css     ← Tailwind CSS
✓ built in Xs
```

> 💡 **Three.js chunk（v2.2 更新）**：[FlowerField.vue](../../frontend/src/components/FlowerField.vue)（`/garden`）、[HeroScene.vue](../../frontend/src/components/HeroScene.vue)（`/`）和 [AmbientBackground.vue](../../frontend/src/components/AmbientBackground.vue)（全局，挂在 AppLayout）都用 `defineAsyncComponent` 异步导入 `three` + `three/addons/*`，所以 Three.js + addons 被打成单独的 `three-vendor-*.js` chunk，**首屏不加载**，仅在用户访问 `/` 或 `/garden` 时按需拉取。三处共享同一 chunk，不重复下载。v2.2 起 chunk 体积从 175KB 增长到 719.84KB，因为加入了 PBR 渲染管线所需的 addons：`OrbitControls`（交互）/ `EffectComposer` + `RenderPass` + `UnrealBloomPass` + `OutputPass`（后处理）/ `RoomEnvironment`（环境映射）。AmbientBackground 首屏 DOM 由 CSS 雾气光斑 + Canvas2D 光点兜底，Three.js 加载完前页面已有完整视觉效果（三层渐进增强）。

### 构建产物去向

| 文件 | 路径 | 由谁服务 |
|---|---|---|
| `index.html` | [static/dist/index.html](../../static/dist/) | FastAPI SPA fallback 兜底返回 |
| JS chunk | [static/dist/assets/index-*.js](../../static/dist/) | FastAPI StaticFiles `/static/dist/*` |
| CSS chunk | [static/dist/assets/index-*.css](../../static/dist/) | FastAPI StaticFiles `/static/dist/*` |

### 为什么必须先构建再启动

[app/main.py](../../app/main.py) 末尾的 SPA fallback 通配路由会检查 `static/dist/index.html` 是否存在：
- **存在** → 返回 `index.html`，Vue Router 接管客户端路由（生产模式）
- **不存在** → 返回提示页引导访问 Vite dev server（开发模式，详见 [DEVELOPMENT 前端开发](DEVELOPMENT.md)）

### 重新构建时机

| 改动 | 是否需要 `npm run build` |
|---|---|
| 改 [`frontend/src/`](../../frontend/src/) 下任何 `.vue` / `.js` / `.ts` / `.css` | ✅ 必须 |
| 改 [`frontend/tailwind.config.js`](../../frontend/tailwind.config.js) | ✅ 必须 |
| 改 [`frontend/vite.config.js`](../../frontend/vite.config.js) | ✅ 必须 |
| 改 [`app/`](../../app/) 下 Python 代码 | ❌ 不需要（重启 `python start.py restart` 即可） |
| 改 [`templates/admin/`](../../templates/admin/) 后台 SSR 模板 | ❌ 不需要（Jinja2 模板运行时渲染） |
| 改 [`.env`](../../.env.example) | ❌ 不需要（重启即可） |

> 💡 **v2.3.3 Safari 兼容修复示例**：本次改了 [utils/visual.js](../../frontend/src/utils/visual.js)（**`hasWebGL` 重写** + `getWebGLCaps` / `isSafari` / `isIOS`）+ [utils/three-helpers.js](../../frontend/src/utils/three-helpers.js)（`webglcontextlost` / `webglcontextrestored` 监听）+ [HeroScene.vue](../../frontend/src/components/HeroScene.vue)（**iOS 降级**：**Bloom 降级** + **PMREM 降级**）+ 新建 [EmojiIcon.vue](../../frontend/src/components/EmojiIcon.vue)（**Iconify** + `twemoji` **SVG emoji**）+ 改 [AppLayout.vue](../../frontend/src/components/AppLayout.vue) / [ProfileView.vue](../../frontend/src/views/profile/ProfileView.vue)（替换 emoji）——全部命中表格首行（`.vue` / `.js`），**必须重新 `npm run build`** 才能让 Safari / iOS 用户拿到 **Safari 兼容**修复 + **跨浏览器一致** emoji。

### 部署流程（生产，v2.3.2 起默认生产模式 + 自动构建）

```bash
# 1. 拉代码
git pull

# 2. 构建前端（如果 frontend/src/ 有改动）
#    v2.3.2 起：也可跳过此步，python start.py 会 dist 存在检测，不存在则自动构建
cd frontend && npm install && npm run build && cd ..

# 3. 装/更新 Python 依赖（如果 requirements.txt 有改动）
pip install -r requirements.txt

# 4. 启动 / 重启后端（v2.3.2 起默认 = 生产模式，FastAPI :5000 单进程）
python start.py restart
```

> ⚠️ **顺序很重要**：先 `npm run build`，后 `python start.py`。否则 FastAPI 起来后还是返回旧 dist（v2.3.2 起 `dist 存在检测` 只看 `static/dist/index.html` 是否存在，不比较修改时间，旧 dist 不会自动触发重建）。

> 💡 **v2.3.2 服务器部署简化为 2 步**（首次或更新皆可）：① 上传代码（`git pull`）② `python start.py`（`dist 存在检测` → 不存在则 `自动构建` `npm install + npm run build`，需 Node.js 18+；已存在则秒启 FastAPI 单进程 :5000）。`--prod` 已改为兼容别名（默认就是生产模式）。

### 关于应用/开发模式（需要 `--dev` 显式开启，v2.3.2 起不再是默认行为）

> ⚠️ **v2.3.2 行为变更**：`python start.py`（无参数）默认走**生产模式**（FastAPI :5000 单进程，需 dist 已构建，不存在则自动构建）——回滚 v2.2.2「默认应用模式」。开发需显式 `python start.py --dev`（Vite :5000 HMR + FastAPI :5001 API，前后端一起起的「应用模式」）。`--prod` 改为兼容别名。理由：服务器端口代理已配好 :5000 不能动，应用模式会让 Vite 占 :5000 破坏代理。

开发时不用每次改前端都 `npm run build`，直接跑 Vite dev server：
```bash
python start.py --dev           # 应用/开发模式（v2.3.2 起需显式 --dev）：
                                #   自动 npm install 当 node_modules 不存在
                                #   起 Vite :5000（HMR + 用户入口）+ FastAPI :5001（API）
```

或手动两终端（v2.0.1 端口策略）：
```bash
# 终端 1：Vite dev server（用户访问 :5000）
cd frontend && npm run dev     # http://127.0.0.1:5000/

# 终端 2：FastAPI（API 退到 :5001）
set QI_PORT=5001 && python start.py fg    # http://127.0.0.1:5001/
```

> ⚠️ **v2.0.1 端口策略调整**：应用/开发模式 Vite 占 :5000（用户入口 + HMR），FastAPI 退到 :5001（API）；不再是 v2.0 的 Vite :5173 + FastAPI :5000。理由：让 FastAPI 反代 Vite 内部路径 `/@id/__x00__plugin-vue:export-helper` 会因 null 字节转义 + 冒号失败（详见 [HANDOFF §6.16](../../HANDOFF.md)）。**用户始终访问 :5000**。

Vite dev server 提供 HMR 热更新 + 自动 proxy `/api`、`/static`、`/admin`、`/docs`、`/openapi.json` 到 FastAPI :5001，详见 [DEVELOPMENT 前端开发](DEVELOPMENT.md)。

---

## 方式 1：宝塔面板（推荐 ⭐）

宝塔自带 Python 项目管理器，省心。

### 1.1 准备工作

- 一台装了宝塔的 Linux 服务器（CentOS / Ubuntu / Debian）
- 宝塔后台：软件商店 → 安装 **「Python 项目管理器」**（一般自带 Python 3.8-3.12）
- 解析好的域名（可选，没域名直接用 IP）

### 1.2 上传代码

方式 A（推荐）：用宝塔「文件」直接上传 zip，解压到 `/www/wwwroot/healing/`

方式 B：用 git
```bash
cd /www/wwwroot/
git clone <your-repo-url> healing
```

### 1.3 创建项目

宝塔后台 → Python 项目 → 「添加项目」：

| 字段 | 填什么 |
|---|---|
| 项目类型 | Python |
| 项目路径 | `/www/wwwroot/healing` |
| 项目名称 | `healing` |
| Python 版本 | 3.11+ |
| 启动方式 | **自定义命令**（见下） |
| 启动命令 | `python start.py` |
| 停止命令 | `python start.py stop` |
| 端口 | 5000 |

**为什么用自定义命令**：
- 宝塔默认用 `gunicorn`，但本项目**没有** gunicorn 依赖
- 我们用自研的 [start.py](../../start.py)，自带 PID / 日志 / 重启

### 1.4 配置 .env

SSH 到服务器：
```bash
cd /www/wwwroot/healing
cp .env.example .env
vi .env   # 改这几行：
```

```env
QI_SECRET_KEY=<用 python -c "import secrets; print(secrets.token_hex(32))" 生成>
QI_HOST=0.0.0.0
QI_PORT=5000
QI_DEBUG=false
# AI 接入（可选）：不配置也能跑，4 个 AI 端点会优雅降级返回治愈系提示
# QI_NVIDIA_API_KEY=nvapi-xxxxx
# QI_AI_MODEL=meta/llama-3.1-8b-instruct
# QI_AI_BASE_URL=https://integrate.api.nvidia.com/v1
# 详见下方「AI 接入（可选）」章节
```

### 1.5 安装依赖 + 构建前端

**5a. Python 依赖**（SSH 或宝塔「一键依赖」）：
```bash
cd /www/wwwroot/healing
python3 -m pip install -r requirements.txt
```

**5b. 前端构建**（v2.3.2 起默认生产模式，`dist 存在检测` + `自动构建`）：

**情况 A：默认生产模式部署**（推荐，FastAPI :5000 单进程）
```bash
# 服务器需先装 Node.js 18+（宝塔软件商店 → Node.js 版本管理器）
# 不需要手动 npm install / npm run build
# python start.py 首次启动时 dist 存在检测 → 不存在则自动 npm install + npm run build（约 7 分钟），之后秒启
# 端口代理 :5000 永远指向 FastAPI（单进程，API + SPA fallback + 静态资源）
# 也可提前手动构建（避免首次启动超时）：
cd /www/wwwroot/healing/frontend
npm install        # 首次约 7 分钟（含 three.js 大包）
npm run build      # 输出到 ../static/dist/
```

**情况 B：应用/开发模式部署**（需 `--dev` 显式开启，Vite :5000 + FastAPI :5001 一起起）
```bash
# 仅本地开发 / 真机调试用，不建议生产部署
# 服务器需先装 Node.js 18+（运行时需要，Vite dev server 常驻）
python start.py --dev    # 端口代理 :5000 指向 Vite dev server（用户入口），:5001 是 FastAPI（API 后端）
```

> 💡 **v2.3.2 新行为**（回滚 v2.2.2）：`python start.py`（无参数）默认走**生产模式**（FastAPI :5000 单进程），**`dist 存在检测`**——`static/dist/index.html` 不存在则**`自动构建`** `npm install + npm run build`（需 Node.js 18+）；`--prod` 改为兼容别名（默认就是生产模式）。开发需显式 `python start.py --dev`（Vite :5000 + FastAPI :5001，前后端一起起的「应用模式」）。**端口代理 :5000 在生产模式指向 FastAPI，在应用模式指向 Vite**——服务器端口代理已配好 :5000 不能动，故默认生产模式。关键词 `默认生产模式` / `dist 存在检测` / `自动构建` / `--dev` / `应用模式` / `v2.3.2`。

### 1.6 启动

宝塔后台 → 项目 → 「启动」。

或 SSH：
```bash
cd /www/wwwroot/healing
python start.py          # v2.3.2 起默认 = 生产模式（FastAPI :5000 单进程，dist 不存在则自动构建）
```

应该看到（默认生产模式）：
```
[START] 后台启动（生产模式）
   FastAPI : http://0.0.0.0:5000（用户访问入口 + API）
   日志文件 : /www/wwwroot/healing/logs/healing.log
   PID 文件 : /www/wwwroot/healing/run/healing.pid
[OK] FastAPI 启动成功（PID 12345, :5000）
   访问     http://0.0.0.0:5000（FastAPI，服务 static/dist/ + SPA fallback）
   API      http://0.0.0.0:5000/docs
```

> 💡 **应用/开发模式启动**（本地开发用）：`python start.py --dev` → Vite :5000（用户入口，HMR）+ FastAPI :5001（API），前后端一起起。生产部署不需要。

### 1.7 反向代理（让外网能访问）

宝塔 → 网站 → 添加站点（PHP 静态就行）→ 站点的「设置」→「反向代理」：

| 字段 | 填什么 |
|---|---|
| 代理名称 | healing |
| 目标 URL | `http://127.0.0.1:5000` |
| 发送域名 | `$host` |

提交后，访问 `http://你的域名/` 就走 Nginx → Python 服务。

### 1.8 HTTPS（强烈推荐）

宝塔站点 → 「SSL」 → 选「Let's Encrypt」 → 申请 → 开启强制 HTTPS。

**完事。** 用户访问 `https://你的域名/` 就是你的应用。

### 1.9 日常维护

| 任务 | 命令 |
|---|---|
| 看服务状态 | SSH 跑 `python start.py status` |
| 看日志 | `tail -f logs/healing.log` |
| 重启服务 | `python start.py restart` |
| 备份数据库 | `cp data/healing.db backup/healing-$(date +%Y%m%d).db` |
| 更新代码（仅后端改动） | `git pull && python start.py restart` |
| 更新代码（含前端改动） | `git pull && cd frontend && npm install && npm run build && cd .. && python start.py restart` |

> 🔒 **改了部署相关配置（端口 / Nginx / systemd / HTTPS）必须同步更新**：[README §1](../../README.md) / [HANDOFF §1](../../HANDOFF.md) / 本文件对应章节。改代码不改文档 = 改了一半（详见 [HANDOFF §12](../../HANDOFF.md)）。

---

## 方式 2：systemd（VPS 标准做法）

适合纯 Linux VPS，没有宝塔。

### 2.1 准备

```bash
# 1. 安装 Python 3.11+
sudo apt update && sudo apt install python3.11 python3.11-venv python3-pip
# 或 CentOS:
# sudo yum install python311 python311-pip

# 2. 创建用户（不推荐用 root 跑）
sudo useradd -m -s /bin/bash healing
```

### 2.2 部署代码

```bash
sudo -iu healing
mkdir -p /home/healing/app
cd /home/healing/app
git clone <your-repo> .
# 或 scp 上传
```

### 2.3 安装依赖 + 构建前端

**3a. Python 依赖**：
```bash
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**3b. 前端构建**（v2.3.2 起默认生产模式，`dist 存在检测` + `自动构建`）：

**情况 A：默认生产模式部署**（systemd 推荐，FastAPI 单进程）
```bash
# 服务器需先装 Node.js 18+（构建用，运行时不需要）
sudo apt install nodejs npm     # Ubuntu/Debian
# 或: curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash - && sudo apt install -y nodejs

# 提前手动构建（避免 systemd 首次启动超时）：
cd /home/healing/app/frontend
npm install        # 首次约 7 分钟（含 three.js 大包）
npm run build      # 输出到 ../static/dist/
# 之后用 python start.py fg 走生产模式（v2.3.2 起默认就是生产模式，端口代理 :5000 永远指向 FastAPI）
# 也可不提前构建，python start.py fg 会 dist 存在检测 → 不存在则自动构建（但 systemd TimeoutStartSec=90 可能不够）
```

**情况 B：应用/开发模式部署**（需 `--dev` 显式开启，不推荐 systemd 用，Vite + FastAPI 双进程不易管理）
```bash
# 仅本地开发 / 真机调试用，不建议生产部署
# 服务器需先装 Node.js 18+（运行时需要，Vite dev server 常驻）
python start.py fg --dev    # Vite :5000（用户入口）+ FastAPI :5001（API），前后端一起起
# 注意：systemd 管理双进程较复杂，建议用 §1 宝塔面板或 §3 nohup 方式跑应用模式
```

> 💡 **v2.3.2 新行为**（回滚 v2.2.2）：`python start.py fg`（systemd 调用）默认走**生产模式**（FastAPI 单进程 :5000），**`dist 存在检测`**——`static/dist/index.html` 不存在则**`自动构建`** `npm install + npm run build`；`--prod` 改为兼容别名。应用/开发模式需显式 `python start.py fg --dev`（Vite :5000 + FastAPI :5001，前后端一起起的「应用模式」）。但 systemd 默认 `TimeoutStartSec=90` 秒，**建议提前手动跑情况 A 的构建** 避免 systemd 因首次 `自动构建` 超时。**生产模式端口代理 :5000 永远指向 FastAPI**。关键词 `默认生产模式` / `dist 存在检测` / `自动构建` / `--dev` / `应用模式` / `v2.3.2`。

### 2.4 配置 .env

```bash
cp .env.example .env
vi .env
# 修改 QI_SECRET_KEY, QI_HOST=0.0.0.0, QI_DEBUG=false
# 可选：AI 接入（不配置也能跑，4 个端点会优雅降级）
#   QI_NVIDIA_API_KEY=nvapi-xxxxx
#   QI_AI_MODEL=meta/llama-3.1-8b-instruct
#   QI_AI_BASE_URL=https://integrate.api.nvidia.com/v1
#   详见下方「AI 接入（可选）」章节
```

### 2.5 写入 systemd unit

`/etc/systemd/system/healing.service`：

```ini
[Unit]
Description=Healing Platform (FastAPI)
After=network.target

[Service]
Type=simple
User=healing
Group=healing
WorkingDirectory=/home/healing/app
Environment="PATH=/home/healing/app/venv/bin"
Environment="QI_HOST=0.0.0.0"
Environment="QI_PORT=5000"
Environment="QI_DEBUG=false"
# 用 systemd 管，start.py 跑前台（fg 子命令）；v2.3.2 起默认就是生产模式（FastAPI :5000 单进程，需 dist 已构建）
# --prod 为兼容别名（加不加效果一样）；应用/开发模式需 --dev（不适合 systemd 双进程管理）
# dist 不存在时 fg 会自动构建（npm install + npm run build），但建议提前手动构建避免 systemd 超时
ExecStart=/home/healing/app/venv/bin/python start.py fg
Restart=always
RestartSec=5
StandardOutput=append:/home/healing/app/logs/healing.log
StandardError=append:/home/healing/app/logs/healing.log

[Install]
WantedBy=multi-user.target
```

启用：
```bash
sudo systemctl daemon-reload
sudo systemctl enable healing
sudo systemctl start healing
sudo systemctl status healing
```

**注意**：systemd 模式下 `start.py` 用 `fg`（前台运行），systemd 负责进程管理 + 自动重启 + 日志收集。

### 2.6 Nginx 反代

`/etc/nginx/sites-available/healing`：

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    # 客户端真实 IP
    real_ip_header X-Real-IP;
    set_real_ip_from 127.0.0.1;

    # 静态资源（FastAPI 也能服务，但 Nginx 缓存更专业）
    location /static/ {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        expires 7d;
        add_header Cache-Control "public, immutable";
        # ⚠️ 改动 CSS / JS 后（如 05-animations.css、app.js），由于 expires 7d + immutable，
        # 老用户浏览器会一直用旧缓存。建议发版后：
        #   1) 改 style.css / base.html 里的查询串版本号（如 ?v=20260715），或
        #   2) 临时 `sudo nginx -s reload` + 让用户硬刷新（Ctrl+Shift+R）一次。
    }

    # API + 页面
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

启用：
```bash
sudo ln -s /etc/nginx/sites-available/healing /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 2.7 HTTPS（Let's Encrypt）

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com
```

自动续期（certbot 自带）。

### 2.8 防火墙

```bash
# UFW (Ubuntu)
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow OpenSSH

# firewall-cmd (CentOS)
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```

**完事。**

### 2.9 日常维护

```bash
sudo systemctl status healing         # 状态
sudo systemctl restart healing        # 重启
sudo journalctl -u healing -f        # 日志（systemd 自带）
tail -f /home/healing/app/logs/healing.log   # 业务日志
```

> 🔒 **改了 systemd unit / Nginx 配置 / 端口** → 必须同步更新 [README §1](../../README.md) / [HANDOFF §1](../../HANDOFF.md) / 本文件对应章节（详见 [HANDOFF §12](../../HANDOFF.md)）。

---

## 方式 3：手动 nohup（临时调试）

```bash
cd /path/to/healing
nohup python start.py > logs/manual.log 2>&1 &
echo $! > run/manual.pid
```

或用 start.py 的后台模式（自带 PID / 日志）：
```bash
python start.py start
```

**生产不要用**。进程没守护，挂了不会自动重启。

---

## 部署后验证清单

部署完成后**必须**跑一遍：

```bash
# 1. 服务在跑（v2.0.1 端口策略：生产模式 :5000 必须是 FastAPI）
curl -I http://127.0.0.1:5000/                        # 200
# 验证 :5000 是 FastAPI 而不是 Vite：
#   - 看响应头 Server: uvicorn（FastAPI）而非 Server: Vite
#   - 或 curl -s http://127.0.0.1:5000/ | grep -i "vite"  应无命中
#   - 若命中 Vite → 说明 dev 模式没切到 prod，检查 static/dist/ 是否已构建

# 1b. 前端 dist 已构建（v2.0 Vue 3 重构后必查）
curl http://127.0.0.1:5000/ | grep -E "Vue|<div id=\"app\">"   # 命中 = dist 已构建并返回 Vue 3 SPA
curl -I http://127.0.0.1:5000/static/dist/index.html           # 200
# 若返回「dist 未构建」提示页 → 回 [前端构建](#前端构建v20-vue-3-重构后必做所有部署方式通用) 跑 python start.py build

# 1c. 3D 花田 chunk 存在（v2.0.1 FlowerField.vue 加）
curl -I http://127.0.0.1:5000/static/dist/assets/three-vendor-*.js   # 200（Three.js chunk）
# 浏览器访问 /garden 应能看到 3D 花田场景

# 2. 静态资源
curl -I http://127.0.0.1:5000/static/css/style.css    # 200
curl -I http://127.0.0.1:5000/static/audio/gong.mp3   # 200

# 3. 公开 API
curl http://127.0.0.1:5000/api/music | head           # v2.3 起含 6 首西方改编，共 22 首（16 classic + 6 western）
curl http://127.0.0.1:5000/api/music?category=western | head   # v2.3 加：仅 6 首西方改编
curl http://127.0.0.1:5000/api/garden/shop | head     # 11 件商品（含 cost_currency 字段）

# 3b. v2.3 新路由（无需登录也能拿 200 / 302）
curl -I http://127.0.0.1:5000/music                  # 200（琴音疗心顶级路由）
curl -I http://127.0.0.1:5000/music/western          # 200（古琴弹西洋曲谱子菜单）
curl -I http://127.0.0.1:5000/profile                # 302（未登录跳 /login，requiresAuth 生效）
curl -I http://127.0.0.1:5000/notifications          # 302（未登录跳 /login，requiresAuth 生效）
curl -I http://127.0.0.1:5000/api/notifications      # 401 或 200（需登录后访问）
curl -I http://127.0.0.1:5000/api/admin/stats        # 401（未登录拒绝，符合预期）

# 4. 注册一个测试账号
curl -X POST http://127.0.0.1:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"nickname":"smoketest","password":"test123456"}'
# 应返回 201

# 5. （可选）用浏览器访问
# http://yourdomain.com
# 注册 → 听歌 → 写日记 → 打卡 → 兑换
# 访问 /garden 确认 3D 花田场景加载正常
# v2.3 加：访问 /music 看琴音疗心板块（5 音卡片 + 古琴弹西洋入口 + AI 选音）
# v2.3 加：访问 /music/western 看古琴弹西洋曲谱子菜单
# v2.3 加：登录后访问 /profile 看个人主页 + 双资源条（露水/落叶）
# v2.3 加：登录后访问 /notifications 看通知列表；顶部 🔔 铃铛显示未读数（60s 轮询）
# v2.3 加：访问 /garden 看花田生长网格（浇水 / 拾取按钮）
```

### v2.3 数据库自动迁移验证

部署后第一次启动时，`init_db()` → `_migrate_legacy_columns()` 会自动给老库加列，无需手动 ALTER TABLE。验证：

```bash
sqlite3 data/healing.db
sqlite> .schema users | grep leaves                  # 应看到 leaves INTEGER DEFAULT 0 NOT NULL
sqlite> .schema diaries | grep -E "content|send_to_ai_hole"
sqlite> .schema shop_items | grep cost_currency      # 应看到 cost_currency VARCHAR(20) DEFAULT 'dew'
sqlite> .schema musics | grep category               # 应看到 category VARCHAR(20) DEFAULT 'classic'
sqlite> .tables                                       # 应看到 user_flowers + notifications 新表
sqlite> SELECT COUNT(*) FROM musics WHERE category='western';  # 应为 6（西方改编 seed）
sqlite> .quit
```

**迁移失败排查**：
- 若新列不存在 → 检查 `logs/healing.log` 是否有 `_migrate_legacy_columns` 报错
- 若新表 `user_flowers` / `notifications` 不存在 → `init_db()` 没跑通，检查 `app/models/__init__.py` 是否 import 了 `UserFlower` / `Notification`
- 修复后重启 `python start.py restart` 即可重跑迁移（已存在的列会跳过，不重复加）

**全部通过 = 部署完成。**

---

## AI 接入（可选，2026-07-17 加）

> **本节是可选功能**。不配置 AI 也能跑，4 个 AI 端点会优雅降级返回治愈系友好提示，业务不中断。详见 [ARCHITECTURE §6.6](../ARCHITECTURE.md) / [HANDOFF §5.7](../../HANDOFF.md)。

### 是什么

静屿 4 个场景接入 NVIDIA NIM API（OpenAI 兼容格式），模型 `meta/llama-3.1-8b-instruct`（8B 小模型，响应快；原默认 `nvidia/llama-3.1-nemotron-70b-instruct` 在用户 NVIDIA 账户下 404 不可用，详见 [HANDOFF §5.7](../../HANDOFF.md)）：

| 场景 | 端点 | 入口 |
|---|---|---|
| AI 树洞对话 | `POST /api/ai/chat` | `/ai-chat`（需登录） |
| 漂流瓶 AI 鼓励语 | `POST /api/ai/encouragement` | `/pick` 拾瓶后 |
| 情绪日历 AI 治愈语 | `POST /api/ai/healing` | `/mood-calendar` 打卡后 |
| 音乐 AI 心情推荐 | `POST /api/ai/recommend-music` | 首页 `/` 「AI 帮我选音」卡片 |

### 配置 3 个环境变量

获取 NVIDIA 免费 API key：访问 [build.nvidia.com](https://build.nvidia.com) → 注册 → 在 `meta/llama-3.1-8b-instruct` 模型页生成 key（格式 `nvapi-xxxxx`）。

在 `.env` 加入（或取消注释 [.env.example](../../.env.example) 末尾的对应行）：

```env
# NVIDIA NIM API（OpenAI 兼容格式）
QI_NVIDIA_API_KEY=nvapi-你的真实key
QI_AI_MODEL=meta/llama-3.1-8b-instruct
QI_AI_BASE_URL=https://integrate.api.nvidia.com/v1
```

**3 个变量说明**：

| 变量 | 必填？ | 默认值 | 说明 |
|---|---|---|---|
| `QI_NVIDIA_API_KEY` | 否 | 空 | NVIDIA NIM API 的 key，`nvapi-` 开头；**留空时 4 个 AI 端点自动降级**返回 `available:false` + 治愈系提示 |
| `QI_AI_MODEL` | 否 | `meta/llama-3.1-8b-instruct` | 模型名，OpenAI 兼容格式。换其他 NVIDIA NIM 模型只改这里 |
| `QI_AI_BASE_URL` | 否 | `https://integrate.api.nvidia.com/v1` | API base URL，换其他厂商（DeepSeek / 智谱 / 自部署 vLLM）只改这里 |

### 重启 + 验证

```bash
# 重启
python start.py restart    # 或 sudo systemctl restart healing

# 验证 1：不配 key 时降级正常（默认状态）
# 应返回 200 + {available:false, message:"治愈系友好提示"}
curl -b c.txt -X POST http://127.0.0.1:5000/api/ai/healing \
  -H "Content-Type: application/json" \
  -d '{"mood_emoji":"calm"}'
# 注意：c.txt 是登录后的 cookie 文件，参考「部署后验证清单」注册流程

# 验证 2：配 key 后 AI 正常返回
# 编辑 .env 加入 3 个变量 → 重启 → 再调一次
# 应返回 200 + {available:true, message:"<AI 生成的治愈语>"}
```

### 网络要求

- 出站访问 `https://integrate.api.nvidia.com`（443）— 服务器防火墙需放行
- 超时设置：[app/services/ai_service.py](../../app/services/ai_service.py) `_call_nvidia()` 默认 **60 秒**（8B 模型实际 1-10s，60s 纯兜底）
- 调用失败（网络/超时/限流/4xx/5xx）→ 端点返回 200 + `available:false` + 治愈系提示，**不报 500**
- **前端字体**：模板通过 `fonts.loli.net` / `gstatic.loli.net`（Google Fonts 国内镜像）加载 Noto Sans/Serif SC，国内可访问；如完全离线部署（不允许任何出站），CSS 变量 `--font-sans` / `--font-serif` 有 `"PingFang SC", "Microsoft YaHei"` 等系统字体兜底，不影响功能

### 成本

- NVIDIA 提供**免费** API key，符合本项目「非商业纯治愈」调性
- 限流策略由 NVIDIA 控制，本项目不主动限流；命中限流时自动降级，用户无感知

### 隐私承诺

| 场景 | 发给 NVIDIA 的内容 | 入库？ |
|---|---|---|
| AI 树洞对话 | 用户对话文本 + 多轮历史 | ❌ 不入库，历史只在浏览器内存 |
| 漂流瓶 AI 鼓励语 | 作者日记**前 120 字**预览 | ❌ 文案不入库，明文不留存 |
| 情绪日历 AI 治愈语 | 心情 emoji + 可选 note | ❌ 不入库 |
| 音乐 AI 心情推荐 | 用户描述的状态文本 | ❌ 不入库 |

**API key 不入仓**：`.env` 已在 `.gitignore` 里，[.env.example](../../.env.example) 只放注释掉的占位。

**完全离线方案**：不配 `QI_NVIDIA_API_KEY` → 4 个端点自动降级 → 业务正常跑（仅少 AI 文案）。适合内网部署 / 不允许数据出站的环境。

---

## 备份与恢复

### 备份

```bash
# 数据库（最重要）
cp data/healing.db backup/healing-$(date +%Y%m%d-%H%M).db

# 用户上传（如果有，将来加）
tar czf backup/static-$(date +%Y%m%d).tar.gz static/

# 加密盐（已含在数据库里，不用单独备份）
```

**强烈建议**：每天 cron 备份一次：

```bash
# /etc/cron.daily/healing-backup
0 3 * * * healing cd /home/healing/app && cp data/healing.db /home/healing/backup/healing-$(date +\%Y\%m\%d).db
```

### 恢复

```bash
# 1. 停服务
python start.py stop

# 2. 覆盖数据库
cp backup/healing-20260714.db data/healing.db

# 3. 启动
python start.py
```

**注意**：用户密码和日记加密盐都在 DB 里，备份 = 备份了所有用户的所有数据。**加密文件妥善保管**。

---

## 监控（可选）

### 简单方案：宝塔自带监控

宝塔后台 → 监控 → 启用 CPU / 内存 / 磁盘告警。

### 进阶：uptime 检查

注册一个免费服务如 [UptimeRobot](https://uptimerobot.com/)，监控 `http://yourdomain.com/`，挂了发邮件 / 微信。

---

## 扩容（用户增长后）

### 阶段 1（0-1000 用户）：单服务器

当前架构完全够用。

### 阶段 2（1000-10 000 用户）：加 worker

```bash
# /etc/systemd/system/healing.service
ExecStart=/home/healing/app/venv/bin/python -m uvicorn app.main:app \
  --host 0.0.0.0 --port 5000 --workers 4
```

SQLite 换 MySQL：
```env
QI_DATABASE_URL=mysql+pymysql://user:pw@localhost:3306/healing?charset=utf8mb4
```

### 阶段 3（10 000+ 用户）：分离

- 应用服务器 × N（gunicorn + uvicorn workers）
- MySQL 主从
- Redis 缓存 + session
- 对象存储（音频文件）

**当前不需要做**。等真到了再处理。

---

## 故障排查

### 服务起不来

```bash
# 1. 看日志
tail -50 logs/healing.log

# 常见错误:
# - ModuleNotFoundError → pip install -r requirements.txt
# - PermissionError → chown -R healing:healing /home/healing/app
# - Address already in use → 别的进程占着 5000 端口，lsof -i :5000 查
```

### 502 Bad Gateway

```bash
# 1. uvicorn 没起
sudo systemctl status healing
# 2. Nginx 配置错
sudo nginx -t
# 3. 端口不通
curl -I http://127.0.0.1:5000/   # 应该 200
```

### 数据库锁死（SQLite）

```bash
# 1. 找长事务
lsof data/healing.db
# 2. 重启服务（最暴力也最有效）
python start.py restart
# 3. 长期方案：换 MySQL
```

### 静态资源 404

```bash
# 检查 static 目录
ls -la static/css/ static/js/ static/audio/
# 重启服务（init 阶段会确保目录存在）
python start.py restart
```

---

## 安全清单

部署前确认：

- [ ] `.env` 里 `QI_SECRET_KEY` 已改为随机长字符串
- [ ] `.env` 里 `QI_DEBUG=false`
- [ ] `.env` 文件**不**在 git 仓库里（.gitignore 已配）
- [ ] 数据库文件**不**暴露到公网（Nginx 不代理 `/data/` 路径）
- [ ] 服务器 SSH 用密钥登录，禁密码
- [ ] 服务器防火墙只开 80 / 443 / SSH
- [ ] HTTPS 已配置（Let's Encrypt）
- [ ] 数据库定期备份到异地
- [ ] 宝塔面板改默认端口 + 强密码

**完事。** 静屿已正式上线。🌿
