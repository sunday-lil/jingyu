# 静屿 — 治愈系身心疗愈平台

> **非商业 · 纯治愈 · 强隐私 · 轻运营**

[![GitHub](https://img.shields.io/badge/GitHub-sunday--lil%2Fjingyu-181717?logo=github)](https://github.com/sunday-lil/jingyu)
[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)](https://www.python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Status](https://img.shields.io/badge/status-v2.3.3-success)]()

一个旨在缓解现代人焦虑情绪、关注心理健康的 Web 应用。通过「古琴五音疗愈」与「私密情绪记录」相结合，提供一个安全、安静、无压力的精神角落。

> 🤖 **AI 接手请先看 [HANDOFF.md](file:///c:/Users/Administrator/Desktop/webwrold/HANDOFF.md)**，那是元信息 + 关键决策 + 踩坑清单的汇总。

> 🔒 **2026-07-25 v2.2.2 start.py 默认应用模式**：`python start.py` 默认行为变更——**默认走应用/开发模式**（前后端一起起：Vite :5000 HMR + FastAPI :5001 API），自动检测 `frontend/node_modules` 不存在则 `npm install`（约 7 分钟，仅首次）。新增 `--prod` 参数显式生产模式（FastAPI :5000 单进程，需 dist 已构建，部署用）。`--dev` 保留为兼容别名（等同默认行为）。服务器部署 3 步：① 上传代码 ② 装 Python + Node.js 18+ ③ `python start.py`（首次自动 npm install，之后秒启）。

> 🔒 **2026-07-25 v2.3 六大模块重构 + 双资源系统 + 花朵生命周期 + 通知 + 个人主页 + 古琴弹西洋曲谱**：① **六板块 + 2 辅助**（含对应路由）+ 顶部导航品牌图标更新；② **双资源系统**（露水 + 落叶）替换原单一能量，`_migrate_legacy_columns()` 加列 + seed 数据更新；③ **花朵生命周期**：新增 `UserFlower` 模型 + `flower_service` + `/api/garden/flowers/*` 端点 + 前端 `GardenView` 花田生长视图；④ **通知系统**：新增 `Notification` 模型 + `routers/notification.py` + 前端 60s 轮询；⑤ **个人主页**：新增 `routers/profile.py` + `views/profile/ProfileView.vue`；⑥ **古琴弹西洋曲谱子菜单**：`musics` 表加 `category` 列 + seed 加 6 首西方曲目 + `/api/music?category=western` 参数 + 前端 `/music/western` 路由；⑦ **日记调整**：`Diary` 加 `send_to_ai_hole` 字段 + 发布选项 + 前端 DiaryWriteView 改造；⑧ **情绪日历对齐修复**（前后端字段一致）；⑨ **树洞改进**：统一图标 + 文本输入 + 文件式聊天历史 + 留存提示；⑩ **漂流瓶社交化**：通知集成；⑪ **花园/其他视图移动端兼容**；⑫ **琴音疗心板块即 /music 顶级模块**（路由 `/music`）；⑬ **pre-commit 5 项 checklist**（Pydantic Out / `_migrate_legacy_columns` / `constants.py` / `.env.example` / README+HANDOFF 速查表）。关键词 `双资源` / `露水` / `落叶` / `UserFlower` / `Notification` / `ProfileView` / `古琴弹西洋曲谱` / `send_to_ai_hole` / `树洞` / `漂流瓶社交` / `琴音疗心` / `pre-commit 5 项` 在 6 份文档中都要出现。

> 🔒 **2026-07-28 v2.3.2 start.py 默认生产模式 + 自动构建简化**：`python start.py` 默认行为再次变更——**默认走生产模式**（FastAPI :5000 单进程，前后端不再一起起），需 `static/dist/` 已构建（不存在则自动 `npm install + npm run build`）。**自动构建仅检测 `static/dist/index.html` 存在性**（`dist 存在检测`），不再比较 `frontend/src/` 与 `static/dist/` 文件修改时间。**开发需显式 `python start.py --dev`**（Vite :5000 HMR + FastAPI :5001 API，前后端一起起的「应用模式」）。`--prod` 改为兼容别名（默认就是生产模式，加不加效果一样）。**服务器部署 2 步**：① 上传代码 ② `python start.py`（首次自动构建，之后秒启，FastAPI 单进程 :5000）。本次回滚 v2.2.2「默认应用模式」决策，理由：服务器端口代理已配好 :5000 不能动，应用模式会让 Vite 占 :5000 破坏代理。关键词 `默认生产模式` / `dist 存在检测` / `自动构建` / `--dev` / `应用模式` / `v2.3.2` 在 6 份文档中都要出现。

> 🔒 **2026-07-30 v2.3.3 Safari 兼容性修复（3D 上下文恢复 + emoji 跨浏览器一致）**：解决 Safari / iOS 用户反馈的两类问题。① **Safari 主页 3D 不渲染**：根因包括 `hasWebGL()` 检测 bug、iOS Safari 切后台→前台后 WebGL 上下文丢失无恢复逻辑、老 iOS 缺 `EXT_color_buffer_half_float` 扩展、Bloom + 高分辨率 PMREM 内存超限。修复：**`hasWebGL` 重写**（区分 WebGL1/2 + 检测扩展 + max texture size），新增 `getWebGLCaps()` / `isSafari()` / `isIOS()` 工具函数；[frontend/src/utils/three-helpers.js](file:///c:/Users/Administrator/Desktop/webwrold/frontend/src/utils/three-helpers.js) 添加 `webglcontextlost` / `webglcontextrestored` 事件监听，上下文丢失时保存场景状态、恢复时重建；[HeroScene.vue](file:///c:/Users/Administrator/Desktop/webwrold/frontend/src/components/HeroScene.vue) 实现 **iOS 降级**策略（**Bloom 降级**：iOS 关闭 UnrealBloomPass；**PMREM 降级**：iOS PMREM 分辨率 256→128、阴影 2048→1024、dpr 上限 2→1.5；老 iOS 缺扩展时关闭 PMREM + Bloom）。② **Safari emoji 显示不一致**：根因为跨平台 emoji 字体风格差异（Apple Color Emoji vs 系统 emoji）。修复：新建 [EmojiIcon.vue](file:///c:/Users/Administrator/Desktop/webwrold/frontend/src/components/EmojiIcon.vue) 组件，使用 **Iconify** + `@iconify-json/twemoji` 离线 **SVG emoji**，确保 **跨浏览器一致**；替换 [AppLayout.vue](file:///c:/Users/Administrator/Desktop/webwrold/frontend/src/components/AppLayout.vue)（品牌 / 导航 / 通知 / 资源）+ [ProfileView.vue](file:///c:/Users/Administrator/Desktop/webwrold/frontend/src/views/profile/ProfileView.vue)（头像 / 通知 / 资源 / 统计 / 快捷入口 / 花朵阶段）所有 emoji。构建 209 modules / 12.30s，HeroScene +0.71KB（降级逻辑）。关键词 `Safari 兼容` / `WebGL 上下文丢失` / `webglcontextlost` / `iOS 降级` / `EmojiIcon` / `Iconify` / `twemoji` / `SVG emoji` / `跨浏览器一致` / `hasWebGL 重写` / `getWebGLCaps` / `isSafari` / `isIOS` / `Bloom 降级` / `PMREM 降级` / `v2.3.3` 在 6 份文档中都要出现。

---

## 0. 一句话速览

**FastAPI（纯 API 后端）+ Vue 3 SPA + SQLite** 的中文治愈系 Web 应用。完整 4 阶段功能：琴音疗心、漂流日记、情绪日历、屿上花田。前端 Vue 3 `<script setup>` + Vite 5 + Vue Router 4 + Pinia + Tailwind CSS + GSAP + @vueuse/motion + Three.js + axios，后端约 2 000 行 Python。无商业元素、无广告、无内购。

> 📌 **2026-07-19 全站 Vue 3 重构**：前端从「Jinja2 SSR + 原生 HTML/CSS/JS」迁移到「Vue 3 SPA + Vite 工程化」。FastAPI 后端简化为纯 API + SPA fallback，所有页面逻辑迁入 `frontend/src/views/` 13 个 .vue 视图。详见 [HANDOFF.md](file:///c:/Users/Administrator/Desktop/webwrold/HANDOFF.md) 元信息。

**强隐私承诺**：用户日记内容使用对称加密存储，密钥与用户密码派生。即便数据库泄露也无法直接读取明文（端到端加密）。

**AI 全面接入**（2026-07-17 加入，**可选**功能）：基于 NVIDIA NIM API（OpenAI 兼容格式，模型 `meta/llama-3.1-8b-instruct`）的 4 个治愈场景——AI 树洞对话、漂流瓶 AI 鼓励语、情绪日历 AI 治愈语、首页音乐 AI 心情推荐。**不配置 API key 时所有功能照常可用**（优雅降级，仅少 AI 文案），保持「渐进增强」原则。AI 文案不入库，对话历史只在浏览器内存（刷新即清空）。

---

## 1. 跑起来

### 1.1 推荐：`start.py` 一键起

```bash
# 安装依赖
pip install -r requirements.txt

# 启动（默认应用模式：Vite :5000 + FastAPI :5001 一起起，自动 npm install）
python start.py

# 浏览器打开 http://127.0.0.1:5000
```

> 📌 **用户始终访问 :5000**，应用 / 生产模式由 `start.py` 自动切换：
> - **应用模式**（默认）：Vite 监听 :5000（用户入口，HMR 热更新）+ FastAPI 改听 :5001（API 后端，由 `start.py` 设置 `QI_PORT=5001`）；Vite proxy 把 `/api`、`/static`、`/admin`、`/docs`、`/openapi.json` 转发到 :5001；自动检测 `frontend/node_modules` 不存在则 `npm install`
> - **生产模式**（`--prod`）：FastAPI 监听 :5000，提供 SPA + API + 静态资源（Vite 不运行），需 `static/dist/` 已构建（未构建报错退出，提示先 `python start.py build`）

**服务管理：**
```bash
python start.py start     # 后台启动（默认 = 应用模式，前后端一起起）
python start.py --prod    # 后台启动（显式生产模式，FastAPI 单进程，需 dist 已构建）
python start.py stop      # 停止（同时停 FastAPI + Vite）
python start.py restart   # 重启（默认应用模式）
python start.py status    # 查 PID + 端口（显示 FastAPI / Vite 两个进程状态）
python start.py fg        # 前台运行 FastAPI（systemd / 调试用；fg 默认应用模式，可加 --prod 切生产）
python start.py build     # 构建前端到 static/dist/（自动 npm install + npm run build）
python start.py --init-db # 启动前重置数据库
```

PID 写入 `run/healing.pid`（FastAPI）+ `run/vite.pid`（Vite），日志写入 `logs/healing.log` + `logs/vite.log`。

### 1.2 备选：直接 uvicorn

```bash
python -m uvicorn app.main:app --reload --port 5000
```

启动入口是 [app/main.py](file:///c:/Users/Administrator/Desktop/webwrold/app/main.py)。`--reload` 模式适合本地改代码热重启，**不要**在生产用。

### 1.3 前端开发模式（Vue 3 + Vite 热更新，2026-07-25 v2.2.2 起为默认行为）

2026-07-19 全站 Vue 3 重构后，前端代码独立到 [`frontend/`](file:///c:/Users/Administrator/Desktop/webwrold/frontend/) 目录，开发时用 Vite dev server 跑 SPA，热更新。**2026-07-25 v2.2.2 起，应用/开发模式成为 `python start.py` 的默认行为**（前后端一起起 + 自动 npm install）。

**推荐方式：`python start.py` 一键起**（默认应用模式，自动 npm install 当 node_modules 不存在）

```bash
python start.py         # 默认应用模式：自动起 Vite :5000（用户入口）+ FastAPI :5001（API）
                        # frontend/node_modules 不存在时自动 npm install（约 7 分钟，仅首次）
# 浏览器打开 http://127.0.0.1:5000（Vite dev server，HMR 热更新）
```

**备选方式：手动分两个终端起**（调试时方便看各自日志）

```bash
# 终端 1：启动 FastAPI 后端（应用模式手动设置 QI_PORT=5001）
cd c:\Users\Administrator\Desktop\webwrold
$env:QI_PORT="5001"; python start.py fg       # Windows PowerShell
# 或：QI_PORT=5001 python start.py fg          # Linux/macOS

# 终端 2：启动 Vite dev server
cd frontend
npm install     # 首次：装 vue / vue-router / pinia / axios / gsap / three / @vueuse/motion / tailwindcss / vite 等（含 three.js 大包，约 7 分钟）
npm run dev     # 启动 Vite dev server，访问 http://127.0.0.1:5000/
```

**dev proxy**：[frontend/vite.config.js](file:///c:/Users/Administrator/Desktop/webwrold/frontend/vite.config.js) 把 `/api` / `/static` / `/admin` / `/docs` / `/openapi.json` 反代到 FastAPI `:5001`，所以 Vite 跑 :5000、FastAPI 跑 :5001 同时开着，前端调 API 走代理无跨域。**注意** Vite host 显式设为 `127.0.0.1`（默认监听 IPv6 `[::1]` 会导致 127.0.0.1 连不上，详见 [HANDOFF.md](file:///c:/Users/Administrator/Desktop/webwrold/HANDOFF.md) 踩坑清单）。

> 📌 **为什么 Vite 占 :5000 而不是 :5173**：之前尝试 FastAPI :5000 代理转发到 Vite :5173，但 Vite 内部路径 `/@id/__x00__plugin-vue:export-helper` 含特殊字符（null 字符转义 + 冒号），httpx 转发会破坏，导致浏览器报 `SyntaxError: Unexpected token '.'`。改成 Vite 直接占 :5000 后，所有 Vite 内部路径都走本地，无转发问题。详见 [HANDOFF §6.16](file:///c:/Users/Administrator/Desktop/webwrold/HANDOFF.md) 踩坑清单。

**生产模式**（部署用）：先 `python start.py build`（或手动 `cd frontend && npm run build`）输出到 `static/dist/`，再 `python start.py --prod` 走 FastAPI :5000 单进程 SPA fallback（详见 [docs/ARCHITECTURE.md](file:///c:/Users/Administrator/Desktop/webwrold/docs/ARCHITECTURE.md)「开发/生产模式切换」节）。

---

## 2. 完整目录树

```
webwrold/
├── start.py                      # 一键启动脚本（start/stop/restart/status/fg/build；自动检测 dist 切换端口策略）
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
│   │   ├── energy.py
│   │   └── ai.py                 # AI 4 场景入参/出参（2026-07-17 加）
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── pages.py              # SPA 兼容重定向（4 个 302：/mood→/calendar、/mood-calendar→/calendar、/my-bottles→/diary、/pick→/diary/pick）
│   │   ├── auth.py               # /api/auth/*
│   │   ├── music.py              # /api/music/*
│   │   ├── diary.py              # /api/diary/*
│   │   ├── mood.py               # /api/mood/*
│   │   ├── energy.py             # /api/energy/*
│   │   ├── garden.py             # /api/garden/*
│   │   └── ai.py                 # /api/ai/* 4 个 AI 端点（2026-07-17 加）
│   ├── services/
│   │   ├── __init__.py
│   │   ├── energy_service.py     # 能量获取规则（听歌 90%+ / 日记 / 打卡 / 连胜）
│   │   ├── diary_service.py      # 漂流瓶随机拾取
│   │   ├── mood_service.py       # 心情日历统计 + 趋势数据
│   │   └── ai_service.py         # NVIDIA NIM API 调用 + 降级处理（2026-07-17 加）
│   └── utils/
│       ├── __init__.py
│       ├── constants.py          # 5 音定义 / 心情枚举 / 能量来源枚举
│       └── crypto.py             # bcrypt + Fernet + PBKDF2
│
├── templates/                    # Jinja2 SSR 模板
│   ├── base.html                 #   全局骨架（导航 + Toast + 页脚）
│   ├── _nav.html                 #   导航宏
│   ├── _toast.html               #   全局 Toast 提示
│   ├── index.html                #   首页（5 音入口 + 漂流瓶入口 + 情绪日历入口 + AI 推荐音卡片）
│   ├── login.html / register.html
│   ├── music_list.html           #   单音曲目列表 + 沉浸式播放器
│   ├── diary_write.html          #   漂流瓶写作页（含投瓶动效）
│   ├── my_bottles.html           #   我的瓶子时间线
│   ├── diary_detail.html         #   单个瓶子详情
│   ├── pick_bottle.html          #   拾取陌生人漂流瓶（含 #ai-encouragement 容器）
│   ├── mood_calendar.html        #   情绪日历（今日打卡 + 月历 + 30 天趋势 + #ai-healing-msg 容器）
│   ├── garden.html               #   屿上花田（已种植物 + 装扮）
│   ├── shop.html                 #   兑换商店（花种 / 装扮 / 徽章）
│   └── ai_chat.html              #   AI 树洞对话页（2026-07-17 加，需登录，多轮对话仅存浏览器）
│
├── frontend/                     # Vue 3 SPA 源码（2026-07-19 全站重构加）
│   ├── package.json              #   依赖：vue ^3.4 / vue-router ^4.4 / pinia ^2.2 / axios ^1.7 / gsap ^3.12 / @vueuse/motion ^2.2 / three ^0.168；devDeps：vite ^5.4 / @vitejs/plugin-vue ^5.1 / tailwindcss ^3.4 / postcss / autoprefixer
│   ├── vite.config.js            #   dev proxy /api、/static、/admin、/docs、/openapi.json → :5001；dev server 监听 :5000；build outDir ../static/dist/；base 仅 build 时为 /static/dist/；host 127.0.0.1，strictPort
│   ├── tailwind.config.js        #   治愈系色彩 token（mist/ink/五音色/accent）+ 动画（breathe/float/fade-up）
│   ├── postcss.config.js
│   ├── index.html                #   HTML 壳
│   └── src/
│       ├── main.js               #   入口（createApp + Pinia + Router + MotionPlugin）
│       ├── App.vue               #   根组件（AppLayout + router-view + transition）
│       ├── assets/
│       │   └── styles/main.css   #   Tailwind 指令 + 全局 CSS 变量 + 通用组件类（.btn/.card/.form-input）+ 系统字体（PingFang SC/Microsoft YaHei，零网络请求）
│       ├── router/
│       │   └── index.js          #   路由：/ /login /register /music /music/:yin /diary /diary/write /diary/pick /calendar /ai-chat /garden /shop /404；requiresAuth 守卫
│       ├── api/
│       │   └── index.js          #   axios 实例，baseURL=/api，withCredentials=true，401 自动跳登录
│       ├── stores/
│       │   └── user.js           #   Pinia user store（cookie session 模式，不存 token，只缓存 user 对象到 localStorage）
│       ├── components/
│       │   ├── AppLayout.vue     #   桌面顶部导航 + 移动端底部 tabbar（768px 断点）
│       │   ├── FlowerField.vue   #   Three.js 3D 花田场景 v2（立体花瓣 BufferGeometry + MeshPhysicalMaterial + Bloom + OrbitControls + raycaster 点击花语；异步加载）
│       │   ├── AmbientBackground.vue  #   全局氛围背景 v2（CSS 雾气 + Canvas2D 柔光 sprite + Three.js 双层粒子 + 鼠标排斥 + 滚动视差 + 轻量 Bloom；三层渐进增强；挂在 AppLayout 根）
│       │   ├── HeroScene.vue     #   首页 Hero 区 3D 浮岛雾海 v2（LatheGeometry 浮岛 + 递归樱花树 + PBR 水面 shader + Bloom + OrbitControls + raycaster 点击飞入；SVG 降级插画）
│       │   ├── AudioVisualizer.vue  #   音波可视化 v2（4 模式：波形/镜像柱/径向/粒子流 + 节拍检测粒子爆裂 + 频响颜色 + 点击切换；Web Audio API + Canvas2D；嵌入 MusicDetailView）
│       │   ├── SceneHint.vue     #   可复用 3D 场景交互指引横幅（v2.2 加；毛玻璃胶囊 + SVG 手势图标；首次交互后自动消失）
│       │   ├── SceneControls.vue #   可复用 3D 场景视图控制工具栏（v2.2 加；自动旋转开关 + 重置视角 + 全屏；v-model 双向绑定）
│       │   └── EmojiIcon.vue     #   跨浏览器一致 emoji 组件（v2.3.3 加；Iconify + @iconify-json/twemoji 离线 SVG emoji，解决 Safari emoji 字体差异）
│       ├── utils/
│       │   ├── visual.js         #   视觉能力检测（hasWebGL 重写 / getWebGLCaps / isSafari / isIOS / prefersReducedMotion / isMobile / isLowPower / shouldUseThreeJS / shouldUseCanvas / smartRAF；v2.3.3 Safari 兼容增强）
│       │   └── three-helpers.js  #   Three.js PBR 工具集（v2.2 加；createRenderer/createEnvironment/createPostProcessing/createOrbitControls/createSoftSpriteTexture/disposeObject3D/disposeRenderer/createKeyLight/createFillLight）
│       └── views/                #   13 个视图（一个功能一个 .vue）
│           ├── HomeView.vue              # 首页：Hero + 五音入口 + 模块卡 + GSAP 入场
│           ├── auth/
│           │   ├── LoginView.vue
│           │   └── RegisterView.vue
│           ├── music/
│           │   ├── MusicListView.vue     # 含 AI 帮我选音
│           │   └── MusicDetailView.vue   # 含底部播放器 + 听完 90% 调 /api/music/listen-complete
│           ├── diary/
│           │   ├── DiaryListView.vue     # 时间线 + Web Crypto 解密
│           │   ├── DiaryWriteView.vue    # 心情 emoji + 加密
│           │   └── PickBottleView.vue    # 拾瓶 + AI 鼓励语
│           ├── mood/
│           │   └── MoodCalendarView.vue  # 日历网格 + 30 天趋势 + AI 治愈语
│           ├── ai/
│           │   └── AIChatView.vue        # 多轮对话，历史只在内存
│           ├── garden/
│           │   ├── GardenView.vue        # 能量/来源/物品/流水
│           │   └── ShopView.vue          # 按 item_type 分组 + 兑换
│           └── NotFoundView.vue
│
├── static/
│   ├── css/
│   │   ├── style.css             #   入口（@import 7 个模块）
│   │   ├── 00-variables.css      #   CSS 变量（治愈系配色 + 字体）
│   │   ├── 01-reset.css          #   重置 + body 渐变背景
│   │   ├── 02-layout.css         #   .container / .nav / .grid
│   │   ├── 03-components.css     #   .btn / .card / .toast / .form
│   │   ├── 04-pages.css          #   首页 / 列表页 / 详情页
│   │   ├── 05-animations.css     #   漂流瓶动效 / 心情弹跳 / 花朵生长 / 滚动渐显 / 涟漪 / 花瓣 / 频谱
│   │   └── 06-music.css          #   沉浸式播放器
│   ├── js/
│   │   ├── app.js                #   window.QI 全局（fetch / toast / confirmThen / reveal / ripple / countUp / confetti）
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

`FastAPI()` 实例 → 挂载静态文件 → 注册 API router（auth/music/diary/mood/energy/garden/ai + admin）+ 1 个 SPA 兼容重定向 router（[pages.py](file:///c:/Users/Administrator/Desktop/webwrold/app/routers/pages.py)）→ 注册 `startup` 事件初始化数据库 + 种子数据 → **SPA fallback**。

**前后端分离 + SPA fallback**（2026-07-19 全站 Vue 3 重构后）：
- **前端**：Vue 3 SPA 工程化在 [`frontend/`](file:///c:/Users/Administrator/Desktop/webwrold/frontend/)，`npm run build` 输出到 `static/dist/`，含 `index.html` + JS/CSS chunk
- **后端**：FastAPI 只提供 `/api/*` JSON 接口 + SPA fallback；前台不再用 Jinja2 渲染（仅 `/admin/*` 后台仍保留 SSR）
- **端口策略**（用户始终访问 :5000，由 `start.py` 自动切换）：
  - **应用模式**（默认，v2.2.2 起）：Vite 监听 :5000（用户入口，HMR）+ FastAPI 改听 :5001（API，由 `start.py` 设置 `QI_PORT=5001`）；Vite proxy 把 `/api`、`/static`、`/admin`、`/docs`、`/openapi.json` 转发到 :5001；自动检测 `frontend/node_modules` 不存在则 `npm install`
  - **生产模式**（`--prod`）：FastAPI 监听 :5000，提供 SPA + API + 静态资源（Vite 不运行），需 `static/dist/` 已构建（未构建报错退出，提示先 `python start.py build`）
- **SPA fallback**（[app/main.py](file:///c:/Users/Administrator/Desktop/webwrold/app/main.py)）：所有未匹配的 GET 请求（排除 `/api/`、`/static/`、`/admin`、`/docs`、`/openapi.json`）：
  - **生产态**（dist 已构建）：从 `static/dist/` 读取对应静态文件（`.js` / `.css` / `.woff2` 等通过 `EXT_TO_MIME` 映射正确设置 `Content-Type`），未命中文件返回 `index.html` 让 Vue Router 接管
  - **开发态**（dist 未构建）：返回提示页引导用户访问 Vite dev server :5000（**不再**反向代理到 Vite，避免内部路径含特殊字符被 httpx 转发破坏，详见 [HANDOFF §6.16](file:///c:/Users/Administrator/Desktop/webwrold/HANDOFF.md)）
- **路由兼容层**：[app/routers/pages.py](file:///c:/Users/Administrator/Desktop/webwrold/app/routers/pages.py) 简化为 4 个 302 重定向（`/mood`→`/calendar`、`/mood-calendar`→`/calendar`、`/my-bottles`→`/diary`、`/pick`→`/diary/pick`），兼容旧书签
- **认证机制（不变）**：cookie session（不是 JWT token），登录用 nickname（不是 username），登录/注册直接返回 user 对象（不是 `{access_token, user}`），前端 userStore 只缓存 user 对象到 localStorage，不存 token
- **配置修复**：[app/config.py](file:///c:/Users/Administrator/Desktop/webwrold/app/config.py) 加 `env_prefix="qi_"`，让 `.env` 里 `QI_*` 变量正确加载
- **AI 调整**：[app/services/ai_service.py](file:///c:/Users/Administrator/Desktop/webwrold/app/services/ai_service.py) 超时 30s→60s；模型链 `nvidia/llama-3.1-nemotron-70b-instruct` → `meta/llama-3.3-70b-instruct` → `meta/llama-3.1-8b-instruct`
- **删除的旧页面**：showcase 动效页（`templates/showcase.html`、`static/js/pages/showcase.js`、`static/css/08-showcase.css`）已删

> 改代码 + 改文档 = 同一个 commit（详见 [HANDOFF §12](file:///c:/Users/Administrator/Desktop/webwrold/HANDOFF.md) 文档自动同步铁律）。本次 Vue 3 重构同步更新 6 份文档（README / HANDOFF / PROJECT_STATE / ARCHITECTURE / DEPLOYMENT / DEVELOPMENT），互链保持一致。

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
- **密码输入可见性切换**：登录 / 注册 / 日记解锁 modal 的密码框统一用 `.password-input-wrap` + `.password-toggle` 👁 按钮，点击切换明文/掩码；`app.js initPasswordToggle()` 用 document-level 事件委托，动态生成的 modal 也生效（2026-07-16 会话 7 加）。
- **会话**：用 `itsdangerous.URLSafeTimedSerializer` 签名 session_id，存在 cookie 里，HttpOnly + SameSite=Lax。
- **日记加密**：用户注册时生成随机 `encryption_salt` 存入 User 表。每次写日记时用 `PBKDF2HMAC(pw + salt)` 派生 Fernet 密钥，**密钥不存数据库**，只存在用户登录后的 session 上下文里。退出登录即丢失。
- **隐私边界**：管理员视图只能看到 `Diary.content_encrypted`（密文），没有任何方式读取明文。

### 3.4 能量规则（[app/services/energy_service.py](file:///c:/Users/Administrator/Desktop/webwrold/app/services/energy_service.py)）

> 🔒 **2026-07-25 v2.3 双资源系统**：原三资源（露水 / 阳光 / 养分）合并为**双资源**——`露水`（`User.total_energy` 字段保留作露水，向内获得：听歌 / 打卡 / 写日记）+ `落叶`（`User.leaves` 新字段，向外获得：花朵枯萎后拾取）。`User` 表加 `leaves` 列（`_migrate_legacy_columns()` 自动迁移老库，`total_energy` 即露水不作改动），`ShopItem` 表加 `cost_currency` 列（`dew` / `leaves`，决定兑换时扣哪种资源）。露水日上限维持 20 不变（`constants.py` `DAILY_ENERGY_LIMITS` 仅含 `listen_music: 20` / `write_diary: 10` / `checkin: 5`，未引入 leaves 项）。seed 数据同步更新。

**资源哲学**：
- 露水（`User.total_energy`）= 向内获得（听歌 / 写日记 / 打卡），用于浇灌花朵
- 落叶（`User.leaves`）= 花朵枯萎后拾取获得，用于在落叶画坊兑换花种（寓意「落叶归根能施肥种花」）
- 露水**不能**直接兑换商店花种（花种只能用落叶兑换；装扮 / 徽章用露水）

| 行为 | 增量 | 资源 | 来源 code |
|---|---|---|---|
| 听完一首曲子（进度 ≥ 90%） | +1 | 露水 | `listen_music` |
| 写完一篇日记并投入 | +2 | 露水 | `write_diary` |
| 当日心情打卡 | +1 | 露水 | `checkin` |
| 连续 7 天打卡 | +5 | 露水 | `streak_7` |
| 拾陌生人漂流瓶 | +1 | 露水 | `pick_bottle` |
| 树洞对话满 5 轮 | +1 | 露水 | `ai_chat` |
| 收集枯萎花朵 | +2 | 落叶 | `collect_wilted` |
| 兑换商店物品 | -cost（按 `ShopItem.cost_currency`） | 露水或落叶 | `exchange` |

每次能量变动都写一条 `EnergyRecord`，用户主页能看历史。v2.3 露水单日上限维持 20（防刷，未变）。

### 3.5 前端架构（Vue 3 SPA，2026-07-19 重构）

**前台 = Vue 3 SPA**（[`frontend/`](file:///c:/Users/Administrator/Desktop/webwrold/frontend/)）：

- **技术栈**：Vue 3 `<script setup>` + Vite 5 + Vue Router 4 + Pinia + Tailwind CSS + GSAP + @vueuse/motion + Three.js + axios
- **入口**：[frontend/src/main.js](file:///c:/Users/Administrator/Desktop/webwrold/frontend/src/main.js) `createApp(App).use(pinia).use(router).use(MotionPlugin).mount('#app')`
- **根组件**：[frontend/src/App.vue](file:///c:/Users/Administrator/Desktop/webwrold/frontend/src/App.vue) = `AppLayout`（导航/tabbar）+ `<router-view>` + `<transition>`
- **路由**：[frontend/src/router/index.js](file:///c:/Users/Administrator/Desktop/webwrold/frontend/src/router/index.js) 13 条路由（`/` / `/login` / `/register` / `/music` / `/music/:yin` / `/diary` / `/diary/write` / `/diary/pick` / `/calendar` / `/ai-chat` / `/garden` / `/shop` / `/:pathMatch(.*)*` 404），`meta.requiresAuth` 守卫
- **API 客户端**：[frontend/src/api/index.js](file:///c:/Users/Administrator/Desktop/webwrold/frontend/src/api/index.js) axios 实例，`baseURL=/api` + `withCredentials=true` + 401 自动跳 `/login`
- **状态管理**：[frontend/src/stores/user.js](file:///c:/Users/Administrator/Desktop/webwrold/frontend/src/stores/user.js) Pinia user store；cookie session 模式，**不存 token**，只缓存 user 对象到 localStorage
- **布局**：[frontend/src/components/AppLayout.vue](file:///c:/Users/Administrator/Desktop/webwrold/frontend/src/components/AppLayout.vue) 桌面顶部导航 + 移动端底部 tabbar（768px 断点）
- **3D 花田 v2**：[frontend/src/components/FlowerField.vue](file:///c:/Users/Administrator/Desktop/webwrold/frontend/src/components/FlowerField.vue) — Three.js PBR 升级版：立体花瓣（自定义 `BufferGeometry` 5 片花瓣 + `MeshPhysicalMaterial` 带透射/sheen）+ 花蕊 + 花茎，60 朵花共 180 个独立网格；`UnrealBloomPass` 后处理柔光 + `RoomEnvironment` 程序化环境映射；`OrbitControls` 拖拽旋转 + 滚轮缩放（阻尼 + 极角约束 + 禁用 pan）；`raycaster` 点击花朵显示花语 toast；用 `defineAsyncComponent` 异步加载，加载时显示 "🌿 花田正在生长…" 提示；嵌入 `GardenView.vue` 顶部 380px 高 + 圆角阴影包裹；配套 [SceneControls.vue](file:///c:/Users/Administrator/Desktop/webwrold/frontend/src/components/SceneControls.vue) 视图控制工具栏（重置视角 / 自动旋转开关）+ [SceneHint.vue](file:///c:/Users/Administrator/Desktop/webwrold/frontend/src/components/SceneHint.vue) 交互指引横幅（3 秒淡出）
- **全局氛围背景 v2**：[frontend/src/components/AmbientBackground.vue](file:///c:/Users/Administrator/Desktop/webwrold/frontend/src/components/AmbientBackground.vue) — 三层渐进增强升级版：CSS 雾气光斑（永远启用）→ Canvas2D 柔光圆点（预生成 32×32 sprite + `source-atop` 合成 + 鼠标 120px 半径柔和排斥 + 0.985 阻尼回归）→ Three.js 双层粒子（远景 90 + 近景 35，移动端减半，`createSoftSpriteTexture` 128×128 柔光 sprite + `AdditiveBlending`）+ 轻量 `UnrealBloomPass`（strength 0.3，移动端 0.18）；鼠标跟随相机轻微旋转（仅旋转不位移）+ 滚动视差（远景 `scrollY*0.0008`、近景 `scrollY*0.002`）；挂在 `AppLayout.vue` 根，`position: fixed; z-index: -1; pointer-events: none`；`smartRAF` 标签页隐藏暂停
- **首页浮岛雾海 v2**：[frontend/src/components/HeroScene.vue](file:///c:/Users/Administrator/Desktop/webwrold/frontend/src/components/HeroScene.vue) — PBR 渲染管线全面升级：`LatheGeometry` 旋转曲面浮岛（3 段贝塞尔曲线轮廓）+ 递归分枝樱花树（深 3 级 + 8 个花球 `InstancedMesh`）+ 水面 `MeshStandardMaterial` `onBeforeCompile` 注入顶点位移 shader 波纹；`ACESFilmicToneMapping` + `SRGBColorSpace` + `PCFSoftShadowMap` + `RoomEnvironment` PMREM 环境映射；`UnrealBloomPass` 后处理；`OrbitControls` 拖拽旋转 + 滚轮缩放 + 自动旋转；`raycaster` 点击浮岛相机飞入；用 `defineAsyncComponent` 异步加载；不支持 WebGL 或 `prefers-reduced-motion` 时降级为 SVG 静态插画（800×480 viewBox，含天空渐变 + 太阳光晕 + 3 个岛 + 3 层波浪）；配套 `SceneHint.vue` + `SceneControls.vue`。**v2.3.3 Safari 兼容**：[three-helpers.js](file:///c:/Users/Administrator/Desktop/webwrold/frontend/src/utils/three-helpers.js) 添加 `webglcontextlost` / `webglcontextrestored` 事件监听处理 **WebGL 上下文丢失**（iOS Safari 切后台→前台时触发，恢复时重建场景）；**iOS 降级**策略——**Bloom 降级**（iOS 关闭 UnrealBloomPass）+ **PMREM 降级**（iOS PMREM 256→128、阴影 2048→1024、dpr 上限 2→1.5；老 iOS 缺 `EXT_color_buffer_half_float` 扩展时关闭 PMREM + Bloom）
- **跨浏览器 emoji 组件**：[frontend/src/components/EmojiIcon.vue](file:///c:/Users/Administrator/Desktop/webwrold/frontend/src/components/EmojiIcon.vue)（v2.3.3 加）— 使用 **Iconify** + `@iconify-json/twemoji` 离线 **SVG emoji**，确保 **跨浏览器一致**（解决 Safari Apple Color Emoji 与系统 emoji 字体风格差异）；已替换 [AppLayout.vue](file:///c:/Users/Administrator/Desktop/webwrold/frontend/src/components/AppLayout.vue)（品牌 / 导航 / 通知 / 资源）+ [ProfileView.vue](file:///c:/Users/Administrator/Desktop/webwrold/frontend/src/views/profile/ProfileView.vue)（头像 / 通知 / 资源 / 统计 / 快捷入口 / 花朵阶段）所有 emoji
- **音波可视化 v2**：[frontend/src/components/AudioVisualizer.vue](file:///c:/Users/Administrator/Desktop/webwrold/frontend/src/components/AudioVisualizer.vue) — 嵌入 `MusicDetailView` 顶部；Web Audio API `createMediaElementSource` + `AnalyserNode`（fftSize=256）实时分析 `<audio>` 频谱；Canvas2D 4 种可视化模式（**wave** 流动波形 / **mirror** 镜像柱状 / **radial** 径向频谱 / **particles** 粒子流）+ 节拍检测（bass > 1.35× 平均 + > 0.35 阈值触发粒子爆裂）+ 频响颜色（低频暖色高频冷色）；点击画布切换模式 + toast 提示；160px 高；`createMediaElementSource` 一次性守卫；30fps（移动端 24fps）；`reduced-motion` 或无 Web Audio API 时降级为静态 5 色横条 CSS 动画
- **3D 场景交互指引**：[frontend/src/components/SceneHint.vue](file:///c:/Users/Administrator/Desktop/webwrold/frontend/src/components/SceneHint.vue) — 通用交互提示横幅组件，被 `HeroScene` / `FlowerField` 引用；显示「拖拽旋转 · 滚轮缩放 · 点击交互」图标 + 文案，3 秒后自动淡出；`pointer-events: none` 不阻挡 3D 交互
- **3D 场景视图控制**：[frontend/src/components/SceneControls.vue](file:///c:/Users/Administrator/Desktop/webwrold/frontend/src/components/SceneControls.vue) — 通用视图控制工具栏组件，被 `HeroScene` / `FlowerField` 引用；提供「重置视角」+「自动旋转开关」两个按钮，emit 事件由父组件处理；玻璃拟态样式 + 8px 圆角
- **视觉能力检测工具**：[frontend/src/utils/visual.js](file:///c:/Users/Administrator/Desktop/webwrold/frontend/src/utils/visual.js) — `hasWebGL()`（v2.3.3 **hasWebGL 重写**：区分 WebGL1/2 + 检测扩展 + max texture size）/ `getWebGLCaps()`（v2.3.3 加，检测 `EXT_color_buffer_half_float` 等扩展）/ `isSafari()` / `isIOS()`（v2.3.3 加，Safari 兼容判断）/ `prefersReducedMotion()` / `isMobile()` / `isLowPower()` / `shouldUseThreeJS()` / `shouldUseCanvas()` / `smartRAF(callback)`；单次检测缓存结果；`smartRAF` 在 `document.hidden` 时暂停 rAF、可见时自动恢复，避免标签页隐藏时浪费 GPU
- **Three.js PBR 工具集**：[frontend/src/utils/three-helpers.js](file:///c:/Users/Administrator/Desktop/webwrold/frontend/src/utils/three-helpers.js) — v2.2 新增；集中导出 9 个 PBR 渲染工具函数：`createRenderer`（ACESFilmic + SRGB + PCFSoft + dpr 上限 2）/ `createEnvironment`（RoomEnvironment + PMREM 程序化环境映射，无外部 HDR 依赖）/ `createPostProcessing`（EffectComposer + RenderPass + UnrealBloomPass + OutputPass）/ `createOrbitControls`（阻尼 + 极角约束 + 禁用 pan + 自动旋转）/ `createKeyLight` + `createFillLight`（主光 + 补光预设）/ `createSoftSpriteTexture`（程序化 Canvas2D 径向渐变柔光 sprite）/ `disposeObject3D` + `disposeRenderer`（完整释放 geometry/material/texture/renderer/composer）；被 `HeroScene` / `FlowerField` / `AmbientBackground` 共享。**v2.3.3 Safari 兼容**：添加 `webglcontextlost` / `webglcontextrestored` 事件监听，处理 **WebGL 上下文丢失**（iOS Safari 切后台→前台触发），上下文丢失时保存场景状态、恢复时重建
- **HomeView 五音卡片 3D 倾斜**：[frontend/src/views/HomeView.vue](file:///c:/Users/Administrator/Desktop/webwrold/frontend/src/views/HomeView.vue) — 鼠标移动驱动 `perspective(800px) rotateY/rotateX`，文字 `translateZ(20px/12px/8px)` 实现凸出层次；移动端关闭 translateZ 省 GPU；`prefers-reduced-motion` 关闭倾斜
- **样式**：Tailwind CSS + [frontend/src/assets/styles/main.css](file:///c:/Users/Administrator/Desktop/webwrold/frontend/src/assets/styles/main.css) 全局 CSS 变量 + 通用组件类（`.btn` / `.card` / `.form-input`）+ 系统字体（`PingFang SC` / `Microsoft YaHei`，**零网络请求**，不再依赖 Google Fonts 国内镜像）
- **治愈系配色**（[frontend/tailwind.config.js](file:///c:/Users/Administrator/Desktop/webwrold/frontend/tailwind.config.js)）：米白 `#F9F6F0` + 茶褐 `#8B7B5E` + 雾粉 / 雾蓝 / 青绿点缀；动画 token `breathe` / `float` / `fade-up`
- **动效**：GSAP 入场 stagger 浮入 + 呼吸动效；`prefers-reduced-motion` 自动降级
- **日记加密**：浏览器 Web Crypto API（PBKDF2 + Fernet 等价 AES-128-CBC），前端加密后只发密文给服务端
- **响应式（v2.2.3 强化）**：三档断点系统差异化布局 — 桌面（≥1025px）顶部完整导航 / 平板（769-1024px）紧凑导航 / 移动端（≤768px）topbar + 底部 tabbar + 「更多」抽屉；iPhone 16 Safari 底部地址栏用 `100dvh` + `env(safe-area-inset-bottom)` 适配；`fullscreen` 路由模式（如 `/ai-chat`）隐藏 tabbar 让聊天页占满视口；4 个 3D 组件移动端几何精度降档（Lathe/Cylinder/Icosahedron 段数降低、樱花树深度 4→3、花瓣网格 5×8→4×6、AudioVisualizer 柱数减半）

**后台 = Jinja2 SSR**（保留）：`/admin/*` 仍用 [templates/admin/](file:///c:/Users/Administrator/Desktop/webwrold/templates/admin/) + [static/css/07-admin.css](file:///c:/Users/Administrator/Desktop/webwrold/static/css/07-admin.css) + `static/js/pages/admin_*.js`，与前台 Vue SPA 完全隔离。

**旧 Jinja2 前台模板**（`templates/base.html` / `_nav.html` / `index.html` 等）仍保留在仓库，但 Vue 3 重构后**不再被路由引用**，仅作历史参考。新功能一律加在 `frontend/src/views/`。

> 想知道前端架构为什么这么分，看 [docs/ARCHITECTURE.md](file:///c:/Users/Administrator/Desktop/webwrold/docs/ARCHITECTURE.md)「前端架构」节；想本地起前端热更新，看 §1.3；想构建生产包，看 [docs/DEPLOYMENT.md](file:///c:/Users/Administrator/Desktop/webwrold/docs/DEPLOYMENT.md)「前端构建」。

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

### 3.7 AI 接入（NVIDIA NIM API，可选，2026-07-17 加入）

4 个治愈场景，全部走 NVIDIA NIM API（OpenAI 兼容格式 `/chat/completions`，模型 `meta/llama-3.1-8b-instruct`）。**未配置 API key 时端点返回 200 + `available:false` + 治愈系友好提示**，前端照常显示文案不报错——AI 是「渐进增强」，不是核心功能。

| 场景 | 前端入口 | 后端端点 | AI 文案去向 |
|---|---|---|---|
| AI 树洞对话 | `/ai-chat`（独立页面，需登录） | `POST /api/ai/chat` | 仅浏览器内存，刷新即清空，**不落库** |
| 漂流瓶 AI 鼓励语 | `/pick` 拾瓶后 `#ai-encouragement` | `POST /api/ai/encouragement` | 给读者看的现场文案，**不写库**，不污染作者收件箱 |
| 情绪日历 AI 治愈语 | `/mood-calendar` 打卡后 `#ai-healing-msg` | `POST /api/ai/healing` | 显示在今日心情卡片下方，**不落库** |
| 音乐 AI 心情推荐 | 首页 `/` 「AI 帮我选音」卡片（仅登录可见） | `POST /api/ai/recommend-music` | 推荐宫商角徵羽之一 + 理由 + 跳转 `/music/{yin}` 链接 |

**4 个 AI 场景的隐私承诺**：
- AI 树洞对话历史只在浏览器内存，刷新清空，**不落库**
- 漂流瓶 AI 鼓励语是给读者看的，不写入数据库，不污染作者收件箱
- 情绪日历 AI 治愈语也不落库
- 用户日记内容传给 AI 时只取**前 120 字**预览（在 `ai_service.generate_encouragement()` 里截断）

**相关文件**：
- 配置：[app/config.py](file:///c:/Users/Administrator/Desktop/webwrold/app/config.py) `Settings` 类的 `nvidia_api_key` / `ai_model` / `ai_base_url`
- Schema：[app/schemas/ai.py](file:///c:/Users/Administrator/Desktop/webwrold/app/schemas/ai.py) 7 个 Pydantic 模型
- Service：[app/services/ai_service.py](file:///c:/Users/Administrator/Desktop/webwrold/app/services/ai_service.py) — `AIServiceUnavailable` 异常 + 4 个系统提示词常量 + `_call_nvidia()` 底层调用 + 4 个上层方法
- Router：[app/routers/ai.py](file:///c:/Users/Administrator/Desktop/webwrold/app/routers/ai.py) 4 个端点（全部 `Depends(get_current_user)` + 全部有降级处理）
- 依赖：[requirements.txt](file:///c:/Users/Administrator/Desktop/webwrold/requirements.txt) 新增 `httpx>=0.27.0,<0.29.0`

**.env 配置示例**（在 [.env.example](file:///c:/Users/Administrator/Desktop/webwrold/.env.example) 末尾，默认注释掉）：
```env
# AI 接入（可选，不配置时所有功能正常，AI 端点会优雅降级）
# QI_NVIDIA_API_KEY=nvapi-xxxxx
# QI_AI_MODEL=meta/llama-3.1-8b-instruct
# QI_AI_BASE_URL=https://integrate.api.nvidia.com/v1
```

> 模型默认用 `meta/llama-3.1-8b-instruct`（8B 小模型，响应快：首次 5-10s，后续 1-3s）。原默认 `nvidia/llama-3.1-nemotron-70b-instruct` 在用户 NVIDIA 账户下 API 返回 404（"Function not found for account"，账户实际有 119 个可用模型但不含该 70B 模型），故换 8B 兼顾速度与质量。NVIDIA 提供**免费 API key**，注册 [build.nvidia.com](https://build.nvidia.com) 即可获取，符合本项目「非商业纯治愈」调性。

### 3.8 v2.3 新增章节速查（2026-07-25 加）

> 本节集中列出 v2.3 引入的新模块 + 关键文件 + 路由，便于快速定位。详见对应 §3.x 子节 / [HANDOFF §4 Phase 7](file:///c:/Users/Administrator/Desktop/webwrold/HANDOFF.md) / [docs/ARCHITECTURE.md](file:///c:/Users/Administrator/Desktop/webwrold/docs/ARCHITECTURE.md) §1.1.7。

#### 3.8.1 六大四字名模块（顶部导航品牌图标同步更新）

| 模块（四字名） | 路由 | 视图文件 | 路由 router |
|---|---|---|---|
| 琴音疗心 | `/music` | `views/music/MusicListView.vue` | `routers/music.py` |
| 漂流日记 | `/diary` | `views/diary/*` | `routers/diary.py` |
| 情绪日历 | `/calendar` | `views/mood/MoodCalendarView.vue` | `routers/mood.py` |
| 心语树洞 | `/ai-chat` | `views/ai/AIChatView.vue` | `routers/ai.py` |
| 落叶画坊 | `/shop` | `views/garden/ShopView.vue` | `routers/garden.py` |
| 屿上花田 | `/garden` | `views/garden/*` | `routers/garden.py` |

辅助入口：拾瓶 `/diary/pick`（漂流日记子路由）、我的 `/profile`（个人主页，`requiresAuth` 守卫）。

[AppLayout.vue](file:///c:/Users/Administrator/Desktop/webwrold/frontend/src/components/AppLayout.vue) 顶部品牌图标由 🌿 草本更新为 🏝️ 岛屿 emoji，移动端 tabbar 同步使用四字名短标签。

#### 3.8.2 双资源系统（露水 + 落叶，详见 §3.4）

- 模型：[app/models/user.py](file:///c:/Users/Administrator/Desktop/webwrold/app/models/user.py) `total_energy`（露水，保留）+ 新增 `leaves: int = 0`（落叶）；`EnergyRecord` **不**加 `resource_type`（露水/落叶的区分由来源 + `ShopItem.cost_currency` 决定）
- 迁移：[app/database.py](file:///c:/Users/Administrator/Desktop/webwrold/app/database.py) `_migrate_legacy_columns()` 加 `ALTER TABLE users ADD COLUMN leaves INTEGER DEFAULT 0 NOT NULL`（`total_energy` 即露水，原已存在，不改）
- Service：[app/services/energy_service.py](file:///c:/Users/Administrator/Desktop/webwrold/app/services/energy_service.py) `grant_energy(...)` 维持原签名（写 `EnergyRecord` + 更新 `User.total_energy`）；`exchange_item` 按 `ShopItem.cost_currency`（`dew` / `leaves`）扣对应资源
- Schema：[app/schemas/energy.py](file:///c:/Users/Administrator/Desktop/webwrold/app/schemas/energy.py) 不加 `resource_type` 字段（资源类型由 `source` / `cost_currency` 体现）
- 前端：`GardenView.vue` / `ShopView.vue` / `ProfileView.vue` 双资源条同步显示
- seed：[app/seed.py](file:///c:/Users/Administrator/Desktop/webwrold/app/seed.py) `ShopItem.cost_currency` 字段补齐（花种 `leaves` / 装扮 `dew` / 徽章 `dew`）

#### 3.8.3 花朵生命周期（v2.3 加）

- 模型：[app/models/garden.py](file:///c:/Users/Administrator/Desktop/webwrold/app/models/garden.py) 新增 `UserFlower`（id / user_id / flower_type / stage / watered_count / planted_at / last_watered_at / bloom_at / wilted_at）
- Service：[app/services/flower_service.py](file:///c:/Users/Administrator/Desktop/webwrold/app/services/flower_service.py) — `list_my_flowers` / `water_flower` / `collect_wilted_leaves` / `get_flower_detail`；阶段 `seed → sprout → bud → bloom → wilted`，每浇一次露水（消耗 1 `total_energy`）累加 `watered_count`，达阈值升级；盛开后超过 7 天未浇水 → 自动枯萎；枯萎花可拾取 → +2 落叶 → 删除该花
- API：[app/routers/garden.py](file:///c:/Users/Administrator/Desktop/webwrold/app/routers/garden.py) 新增 `GET /api/garden/flowers` / `GET /api/garden/flowers/{id}` / `POST /api/garden/flowers/{id}/water` / `POST /api/garden/flowers/{id}/collect`
- 前端：[GardenView.vue](file:///c:/Users/Administrator/Desktop/webwrold/frontend/src/views/garden/GardenView.vue) 嵌入花田生长网格，每朵花显示阶段 emoji + 浇水按钮（消耗 1 露水）

#### 3.8.4 通知系统（v2.3 加）

- 模型：[app/models/notification.py](file:///c:/Users/Administrator/Desktop/webwrold/app/models/notification.py) 新增（id / user_id / type / content / related_id / is_read / created_at）；类型：`encouragement`（漂流瓶收到鼓励）/ `system`（系统预留）
- Router：[app/routers/notification.py](file:///c:/Users/Administrator/Desktop/webwrold/app/routers/notification.py) — `GET /api/notifications` / `GET /api/notifications/unread` / `POST /api/notifications/{id}/read` / `POST /api/notifications/read-all`
- 触发点：拾瓶被鼓励（写入 Notification，type=`encouragement`）
- 前端：[AppLayout.vue](file:///c:/Users/Administrator/Desktop/webwrold/frontend/src/components/AppLayout.vue) 顶部加 🔔 铃铛 + 红点未读数；60s 轮询 `/api/notifications/unread`；点击铃铛跳转 `/notifications` 路由（独立通知列表页 `NotificationsView.vue`）
- Schema：[app/schemas/notification.py](file:///c:/Users/Administrator/Desktop/webwrold/app/schemas/notification.py) `NotificationOut` / `UnreadCountOut`

#### 3.8.5 个人主页（v2.3 加）

- Router：[app/routers/profile.py](file:///c:/Users/Administrator/Desktop/webwrold/app/routers/profile.py) — `GET /api/profile`（自己主页）/ `GET /api/profile/stats`（轻量统计）/ `GET /api/profile/{user_id}`（他人主页）；统计字段：`diary_count` / `public_diary_count` / `checkin_count` / `listen_count` / `flower_count` / `garden_item_count` / `received_encouragement_count` / `streak`
- 前端：[frontend/src/views/profile/ProfileView.vue](file:///c:/Users/Administrator/Desktop/webwrold/frontend/src/views/profile/ProfileView.vue) — 卡片式布局：头像 + 昵称 + 双资源条 + 4 统计卡 + 最近 5 条活动时间线
- 路由：`/profile` 加入 `requiresAuth: true` 守卫

#### 3.8.6 古琴弹西洋曲谱子菜单（v2.3 加）

- 模型：[app/models/music.py](file:///c:/Users/Administrator/Desktop/webwrold/app/models/music.py) 加 `category: str = "classic"`（`classic` 五音古曲 / `western` 古琴弹西洋）
- 迁移：`_migrate_legacy_columns()` 加 `ALTER TABLE musics ADD COLUMN category VARCHAR(20) DEFAULT 'classic' NOT NULL`
- seed：[app/seed.py](file:///c:/Users/Administrator/Desktop/webwrold/app/seed.py) 加 6 首西方名曲古琴改编（《绿袖子》《卡农》《致爱丽丝》《月光奏鸣曲》《天鹅湖》《昨日重现》），全部 `category="western"`；原 16 首 classic 曲目保留
- API：[app/routers/music.py](file:///c:/Users/Administrator/Desktop/webwrold/app/routers/music.py) `GET /api/music?category=western|classic` 加 query 参数过滤
- 前端：`/music/western` 路由 + `views/music/MusicWesternView.vue` 独立列表；导航「琴音疗心」下拉加「古琴弹西洋曲谱」入口

#### 3.8.7 日记调整（v2.3 加）

- 模型：[app/models/diary.py](file:///c:/Users/Administrator/Desktop/webwrold/app/models/diary.py) 加 `content: str`（明文，v2.3 起替代 `content_encrypted`）+ `send_to_ai_hole: bool = False`（不放入漂流瓶时同步至树洞）；`content_encrypted` 保留为遗留字段兼容老库
- 迁移：`_migrate_legacy_columns()` 加 `ALTER TABLE diaries ADD COLUMN content TEXT NOT NULL DEFAULT ''` + `ADD COLUMN send_to_ai_hole BOOLEAN DEFAULT 0 NOT NULL`
- API：`POST /api/diary` 入参加 `send_to_ai_hole`（`is_public=True` 时忽略）；`is_public=False` + `send_to_ai_hole=True` → 仅自己可见 + 同步树洞
- 前端：[DiaryWriteView.vue](file:///c:/Users/Administrator/Desktop/webwrold/frontend/src/views/diary/DiaryWriteView.vue) 加发布选项 radio（放入漂流瓶 🍶 / 不放入漂流瓶 🌳），无 category 下拉

#### 3.8.8 情绪日历对齐修复（v2.3 加）

- 修复：原前端 `MoodCalendarView.vue` 提交 `mood_emoji: "calm"` 字符串，但后端 `MoodCheckin.mood_emoji` 期望 emoji 字符（如 "😊"）；统一改为 emoji 字符
- [app/schemas/mood.py](file:///c:/Users/Administrator/Desktop/webwrold/app/schemas/mood.py) `MoodCheckinIn.mood_emoji: str` 加 `pattern` 校验 emoji 字符
- [app/utils/constants.py](file:///c:/Users/Administrator/Desktop/webwrold/app/utils/constants.py) `MOOD_INFO` 加 `emoji` 字段统一管理

#### 3.8.9 树洞改进（v2.3 加）

- 统一图标：AIChatView + AppLayout tabbar + 导航全部用 🌳 树 emoji（心语树洞）
- 文本输入：原仅文本框，加 `<textarea>` 多行 + 字数提示（500 字内）
- 文件式聊天历史：每轮对话保存到 `data/chat_history/<user_id>/<conversation_id>.json` 文件，前端加载时回放历史；单对话上限 100 条；用户可选「保留」/「不保留」，不保留则 `delete_conversation` 删文件
- 留存提示：用户离开 `/ai-chat` 时弹 toast「树洞会在这里等你回来」

#### 3.8.10 漂流瓶社交化 + 通知集成（v2.3 加）

- 拾瓶成功 → 写 `Notification(type="encouragement", user_id=作者)`，作者下次进入应用时看到「收到 1 个陌生人的拥抱」
- 通知 60s 轮询 + 红点未读数

#### 3.8.11 琴音疗心板块即 /music 顶级模块（v2.3 加）

- 琴音疗心 = `/music` 顶级模块（路由 `/music`），整合 5 音卡片 + 古琴弹西洋曲谱入口 + 沉浸式播放器入口 + AI 选音
- 路由：[frontend/src/router/index.js](file:///c:/Users/Administrator/Desktop/webwrold/frontend/src/router/index.js) 加 `/music/western`（古琴弹西洋曲谱子菜单）+ `/music/:yin` 保留

---

## 4. 数据库表速查

| 表 | 关键字段 | 说明 |
|---|---|---|
| `users` | id, nickname, password_hash, encryption_salt, total_energy（露水）, **leaves**（v2.3 加，落叶） | 用户（encryption_salt 为遗留字段；v2.3 加 leaves 落叶，total_energy 即露水保留） |
| `diaries` | id, user_id, **content**（v2.3 明文）, content_encrypted（遗留）, mood_type, is_public, **send_to_ai_hole**（v2.3 加）, created_at | 漂流日记（v2.3 起明文，content_encrypted 保留兼容老库） |
| `mood_checkins` | id, user_id, check_date, mood_emoji, note | 心情打卡 |
| `musics` | id, title, audio_url, cover_image, yin_type, **category**（v2.3 加 `classic`/`western`）, duration, tags | 古琴曲目（v2.3 加西方曲谱分类） |
| `energy_records` | id, user_id, amount, source, created_at, music_id | 能量流水（无 resource_type；资源类型由 source + cost_currency 体现） |
| `shop_items` | id, name, item_type, cost, **cost_currency**（v2.3 加 `dew`/`leaves`）, image, description, trigger | 商店物品 |
| `garden_items` | id, user_id, item_id, obtained_at | 用户持有 |
| `encouragements` | id, from_user_id, to_user_id, diary_id, content | 陌生人鼓励语 |
| `user_flowers`（v2.3 加） | id, user_id, flower_type, stage, watered_count, planted_at, last_watered_at, bloom_at, wilted_at | 花朵生命周期（seed→sprout→bud→bloom→wilted） |
| `notifications`（v2.3 加） | id, user_id, type（encouragement/system）, content, related_id, is_read, created_at | 通知系统（拾瓶鼓励事件触发） |

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
curl -I http://127.0.0.1:5000/mood-calendar       # 302
curl -I http://127.0.0.1:5000/mood                # 302（旧链接兼容，重定向到 /mood-calendar）

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

### 7.1 v2.3 smoke test 结果（2026-07-25）

v2.3 改动后跑的冒烟测试结果（详见 [PROJECT_STATE §2 v2.3 条目](file:///c:/Users/Administrator/Desktop/webwrold/docs/PROJECT_STATE.md)）：

| 验证项 | 结果 | 备注 |
|---|---|---|
| `python start.py restart` | ✅ PID 启动 | 应用模式（Vite :5000 + FastAPI :5001） |
| `curl -I http://127.0.0.1:5000/` | ✅ 200 | 首页加载，AppLayout 显示 v2.3 品牌图标 |
| `curl -I http://127.0.0.1:5000/api/music` | ✅ 200 | 含 v2.3 西方曲谱 6 首（共 22 首：16 classic + 6 western） |
| `curl -I http://127.0.0.1:5000/api/notifications` | ✅ 200 | 需登录后访问，302 → /login 验证守卫生效 |
| `curl -I http://127.0.0.1:5000/music` | ✅ 200 | v2.3 琴音疗心顶级路由 |
| `curl -I http://127.0.0.1:5000/profile` | ✅ 302 | 未登录跳 /login，requiresAuth 生效 |
| `curl -I http://127.0.0.1:5000/music/western` | ✅ 200 | 西方曲谱子菜单页 |
| `curl -I http://127.0.0.1:5000/api/admin/stats` | ✅ 401 | 未登录拒绝，符合预期 |
| `npm run build` | ✅ 通过 | Vite 5 + Rollup 编译，无错误 |
| `_migrate_legacy_columns()` | ✅ 跑通 | 老库自动加 `users.leaves` / `diaries.content` / `diaries.send_to_ai_hole` / `shop_items.cost_currency` / `musics.category` 列（5 列）；新表 `user_flowers` / `notifications` 由 `init_db()` 自动建表 |
| 双资源 UI 显示 | ✅ | GardenView / ShopView / ProfileView 双资源条同步显示 |
| 通知轮询 | ✅ | 60s 一次 `/api/notifications/unread`，红点显示未读数 |

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
| AI 服务层 | [app/services/ai_service.py](file:///c:/Users/Administrator/Desktop/webwrold/app/services/ai_service.py) |
| AI API 端点 | [app/routers/ai.py](file:///c:/Users/Administrator/Desktop/webwrold/app/routers/ai.py) |
| AI Schema | [app/schemas/ai.py](file:///c:/Users/Administrator/Desktop/webwrold/app/schemas/ai.py) |
| AI 树洞对话页 | [templates/ai_chat.html](file:///c:/Users/Administrator/Desktop/webwrold/templates/ai_chat.html) |
| **前端 Vue SPA 入口** | [frontend/src/main.js](file:///c:/Users/Administrator/Desktop/webwrold/frontend/src/main.js) |
| **前端路由表** | [frontend/src/router/index.js](file:///c:/Users/Administrator/Desktop/webwrold/frontend/src/router/index.js) |
| **前端 API 客户端** | [frontend/src/api/index.js](file:///c:/Users/Administrator/Desktop/webwrold/frontend/src/api/index.js) |
| **前端 user store** | [frontend/src/stores/user.js](file:///c:/Users/Administrator/Desktop/webwrold/frontend/src/stores/user.js) |
| **前端 Vite 配置** | [frontend/vite.config.js](file:///c:/Users/Administrator/Desktop/webwrold/frontend/vite.config.js) |
| **前端 Tailwind 配置** | [frontend/tailwind.config.js](file:///c:/Users/Administrator/Desktop/webwrold/frontend/tailwind.config.js) |
| **前端 3D 花田组件** | [frontend/src/components/FlowerField.vue](file:///c:/Users/Administrator/Desktop/webwrold/frontend/src/components/FlowerField.vue) |
| **前端全局氛围背景** | [frontend/src/components/AmbientBackground.vue](file:///c:/Users/Administrator/Desktop/webwrold/frontend/src/components/AmbientBackground.vue) |
| **前端首页浮岛雾海 3D** | [frontend/src/components/HeroScene.vue](file:///c:/Users/Administrator/Desktop/webwrold/frontend/src/components/HeroScene.vue) |
| **前端音波可视化** | [frontend/src/components/AudioVisualizer.vue](file:///c:/Users/Administrator/Desktop/webwrold/frontend/src/components/AudioVisualizer.vue) |
| **前端 3D 场景交互指引** | [frontend/src/components/SceneHint.vue](file:///c:/Users/Administrator/Desktop/webwrold/frontend/src/components/SceneHint.vue) |
| **前端 3D 场景视图控制** | [frontend/src/components/SceneControls.vue](file:///c:/Users/Administrator/Desktop/webwrold/frontend/src/components/SceneControls.vue) |
| **前端跨浏览器 emoji 组件** | [frontend/src/components/EmojiIcon.vue](file:///c:/Users/Administrator/Desktop/webwrold/frontend/src/components/EmojiIcon.vue)（v2.3.3 加；Iconify + twemoji SVG emoji，Safari 兼容） |
| **前端视觉能力检测工具** | [frontend/src/utils/visual.js](file:///c:/Users/Administrator/Desktop/webwrold/frontend/src/utils/visual.js)（v2.3.3 hasWebGL 重写 + getWebGLCaps / isSafari / isIOS） |
| **前端 Three.js PBR 工具集** | [frontend/src/utils/three-helpers.js](file:///c:/Users/Administrator/Desktop/webwrold/frontend/src/utils/three-helpers.js) |
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
| **前端 Vue 视图 / 路由 / store 改动** | §2 目录树 frontend/ 子树 + §3.5 前端架构 + [docs/ARCHITECTURE.md](file:///c:/Users/Administrator/Desktop/webwrold/docs/ARCHITECTURE.md)「前端架构」 + [docs/DEVELOPMENT.md](file:///c:/Users/Administrator/Desktop/webwrold/docs/DEVELOPMENT.md)「前端开发」 |
| **Vite / Tailwind / 依赖改动** | §1.3 + [frontend/package.json](file:///c:/Users/Administrator/Desktop/webwrold/frontend/package.json) + [HANDOFF §2](file:///c:/Users/Administrator/Desktop/webwrold/HANDOFF.md) + [docs/DEPLOYMENT.md](file:///c:/Users/Administrator/Desktop/webwrold/docs/DEPLOYMENT.md)「前端构建」 |
| **6 份文档同步**（Iron Rule） | 本次 Vue 3 重构涉及 README / HANDOFF / PROJECT_STATE / ARCHITECTURE / DEPLOYMENT / DEVELOPMENT 6 份文档，必须同一 commit 一起更新 |

### 9.3 提交前自检 5 件事

> 🔒 **2026-07-25 v2.3 pre-commit 5 项 checklist 正式化**：本项目 pre-commit checklist 固化为 5 项（与 [HANDOFF §12.4](file:///c:/Users/Administrator/Desktop/webwrold/HANDOFF.md) / [PROJECT_STATE §8.3](file:///c:/Users/Administrator/Desktop/webwrold/docs/PROJECT_STATE.md) 一致）。**改代码 + 改文档 = 同一个 commit** 的铁律依赖此 5 项自检。

- [ ] 改的 Pydantic 字段在 `*Out` schema 里**也都声明了**（→ 防止静默过滤 Bug）
- [ ] 改的 model 字段在 `_migrate_legacy_columns()` 里**也加了**（→ 防止老库丢列）
- [ ] 改的常量在 `constants.py` / §3.4 表格里**也更新了**（→ 业务规则可见性）
- [ ] 改的 .env 配置在 [.env.example](file:///c:/Users/Administrator/Desktop/webwrold/.env.example) 里**也加了**（→ 部署可见性）
- [ ] 新增页面 / API 在 README+HANDOFF 速查表里**也加了**（→ 可发现性）

如果发现这份文档和实际代码矛盾：**以代码为准，然后更新这份文档**。

---

## 10. License

MIT — 治愈系开源。
