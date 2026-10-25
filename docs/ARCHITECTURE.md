# 架构 — 静屿

> 本文件讲**为什么**这样设计，不是讲**做了什么**。想知道做了什么看 [README.md](../README.md)。

> 🔒 **改了本文件涉及的代码，必须同步更新**：[HANDOFF §12](HANDOFF.md) / [AGENTS.md](../AGENTS.md) / [DEVELOPMENT §1.8](DEVELOPMENT.md) 列出的对应文档。改代码不改文档 = 改了一半。

> **当前版本：v2.6.2（2026-10-25）**。版本变更历史见 [CHANGELOG.md](CHANGELOG.md)；本文件只解释当前架构与取舍。

---

## 1. 总体架构

> **2026-07-19 v2.0 全站 Vue 3 重构**：前端从 Jinja2 SSR + 原生 JS 迁移到 Vue 3 SPA + Vite 工程化，后端 FastAPI 简化为纯 API + SPA fallback。
>
> **2026-07-19 v2.0.1 端口策略调整**：开发模式 Vite 占 :5000（用户入口）+ FastAPI 改 :5001（API），避免 FastAPI 反代 Vite 内部路径含特殊字符失败（详见 [HANDOFF §6.16](HANDOFF.md)）。**用户始终访问 :5000**，由 [start.py](../start.py) 自动切换。

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

**单一进程承担 3 个角色**（生产模式）：API + SPA fallback + 静态资源。这是有意为之的简化（见 [HANDOFF §2](HANDOFF.md) + [HANDOFF §5.8](HANDOFF.md) 前端选型决策）。

**开发模式 = 双进程**：Vite :5000（前端 + HMR）+ FastAPI :5001（API），由 [start.py](../start.py) 自动起两个；用户**只**访问 :5000，Vite proxy 转发 API 请求到 :5001。详见 [§1.2 开发/生产模式切换](#12-开发生产模式切换2026-07-19-v20-加)。

**前台 = Vue 3 SPA**（[`frontend/`](../frontend/)），**后台 = Jinja2 SSR**（[templates/admin/](../templates/admin/)）：后台仍用 SSR 是有意为之（独立样式、独立隔离、管理工具不需要 SPA 体验，详见 [HANDOFF §5.8](HANDOFF.md)）。

**秘密后台**（[app/routers/admin.py](../app/routers/admin.py) + [app/routers/admin_pages.py](../app/routers/admin_pages.py)）挂在 `QI_ADMIN_PATH_PREFIX`（默认 `/admin`）下，**完全独立于前台 Vue SPA**：不共享 AppLayout，不共享 Tailwind 样式，不放任何前台链接（见 [§6.5](#65-秘密后台架构)）。

---

## 1.1 前端架构（Vue 3 SPA，2026-07-19 v2.0 加）

> 设计原则：**「组件化复用 + 客户端路由 + 集中状态 + 工程化构建」** —— 从原生 HTML/CSS/JS + Jinja2 SSR 迁移到 Vue 3 SPA，解决「一页一个 JS、状态散落、路由靠后端 302」的膨胀问题。

### 1.1.1 技术栈

| 层 | 选型 | 文件 | 说明 |
|---|---|---|---|
| 框架 | Vue 3 `<script setup>` | [frontend/package.json](../frontend/package.json) | ^3.4，组合式 API |
| 构建 | Vite 5 | [frontend/vite.config.js](../frontend/vite.config.js) | dev HMR + build Rollup；dev 监听 :5000（用户入口）；dev proxy /api、/static、/admin、/docs、/openapi.json → FastAPI :5001（详见 [§1.2](#12-开发生产模式切换2026-07-19-v20-加)） |
| 路由 | Vue Router 4 | [frontend/src/router/index.js](../frontend/src/router/index.js) | 16 条业务路由 + 404，`meta.requiresAuth` 守卫 |
| 状态 | Pinia 2 | [frontend/src/stores/user.js](../frontend/src/stores/user.js) | user store；cookie session 模式，**不存 token**，只缓存 user 对象到 localStorage |
| 样式 | Tailwind CSS 3.4 | [frontend/tailwind.config.js](../frontend/tailwind.config.js) | 治愈系色彩 token（mist/ink/五音色/accent）+ 动画（breathe/float/fade-up） |
| 动效 | GSAP 3.12 + @vueuse/motion 2.2 | 各 .vue 视图 | 入场 stagger + 呼吸动效；`prefers-reduced-motion` 自动降级 |
| 3D | Three.js 0.168 | [frontend/src/components/FlowerField.vue](../frontend/src/components/FlowerField.vue) | 治愈系 3D 花田场景（60 朵花 × 5 瓣 = 300 InstancedMesh），异步加载（详见 [§1.1.5](#115-3d-花田组件-flowerfieldvue2026-07-19-v201-加)） |
| HTTP | axios 1.7 | [frontend/src/api/index.js](../frontend/src/api/index.js) | `baseURL=/api`，`withCredentials=true`，401 自动跳 `/login` |

### 1.1.2 16 条业务路由 + 404（[frontend/src/router/index.js](../frontend/src/router/index.js)）

| 路径 | 视图 | requiresAuth | 说明 |
|---|---|---|---|
| `/` | HomeView.vue | 否 | 首页：Hero + 模块卡 + 岛上指南 |
| `/login` / `/register` | auth/LoginView.vue / RegisterView.vue | 否 | 登录 / 注册 |
| `/music` | music/MusicListView.vue | 否 | 五音 + 西洋曲谱六宫格 + AI 选音 |
| `/music/western` | music/MusicWesternView.vue | 否 | 西洋曲谱独立列表（必须排在 `:yin` 前） |
| `/music/therapy` | music/TherapyView.vue | 否 | 身心调理：问题 → 曲/八段锦/香囊/手串/食疗 |
| `/music/:yin` | music/MusicDetailView.vue | 否 | 单音曲目 + 播放器 + 90% 发放露水 |
| `/diary` / `/diary/write` / `/diary/pick` | diary/* | 是 | 时间线 / 写日记（明文）/ 拾瓶 |
| `/calendar` | mood/MoodCalendarView.vue | 是 | 日历 + 罗素情绪环 + 今日打卡删除 |
| `/corner` | diary/CornerView.vue | 是 | 静屿角落：不公开的私密碎碎念 |
| `/garden` / `/shop` | garden/* | 是 | 花田 / 落叶花坊 |
| `/profile` | profile/ProfileView.vue | 是 | 个人主页 / 头像昵称 |
| `/notifications` | notification/NotificationsView.vue | 是 | 通知中心 |
| `/:pathMatch(.*)*` | NotFoundView.vue | 否 | 404 catch-all |

### 1.1.3 调用流（登录 → 写日记）

```
浏览器                                FastAPI
  │ POST /api/auth/login                 │
  │ {nickname, password}                 │
  ├─────────────────────────────────────→│ 1. bcrypt.verify
  │                                      │ 2. 签 qi_session cookie
  │ ←─ 200 + Set-Cookie + user 对象      │ 3. 不返回 JWT
  │ Pinia userStore + localStorage       │
  │ POST /api/diary                      │
  │ Cookie: qi_session=...               │
  │ {content, mood_type, is_public}      │
  ├─────────────────────────────────────→│ 1. get_current_user
  │                                      │ 2. 写 diaries.content（明文）
  │                                      │ 3. +2 露水（write_diary）
  │ ←─ 201 {id, new_total_energy, ...}   │
```

**关键点**：
1. cookie session（不是 JWT）；前端只缓存 user 对象，不存 token。
2. axios `withCredentials=true` 自动带 cookie；401 自动跳 `/login`。
3. 写日记传明文 `content`，服务端直接落库；`content_encrypted` 不再使用。

### 1.1.4 日记数据模型（v2.3 起为明文）

```
浏览器（Vue 3 视图）              FastAPI
  │ 用户输入日记正文                 │
  │ POST /api/diary                  │
  │ {content: "..."}                 │
  ├─────────────────────────────────→│ 写 diaries.content（明文）
  │ ←─ 201                           │
```

- 私密日记按 `user_id` 过滤，仅作者可读；公开漂流瓶可被其他登录用户拾取。
- 后台 API 只返回统计 / 时间，不返回正文；但**数据库层面无加密**。
- `User.encryption_salt` 与 `Diary.content_encrypted` 仅为老库兼容字段；不要再声称端到端加密。

### 1.1.5 3D 花田组件（FlowerField.vue，2026-07-19 v2.0.1 加）

> 设计原则：**「治愈系视觉冲击 + 性能可控 + 按需加载」** —— 在精神花园页顶部用 Three.js 渲染一片真 3D 花田，弥补 v2.0 首屏「装饰性 emoji 平铺」的视觉单薄问题；同时通过 InstancedMesh + 异步导入把性能开销压到最小。

**文件**：[frontend/src/components/FlowerField.vue](../frontend/src/components/FlowerField.vue)

**嵌入位置**：[frontend/src/views/garden/GardenView.vue](../frontend/src/views/garden/GardenView.vue) 顶部 hero 区，高 380px，圆角 + 阴影包裹，下方叠加「移动鼠标，看花田随风摆动」提示文案。

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
| 花瓣几何 | 自定义 `BufferGeometry` 立体花瓣（4×6 顶点网格 + Z 轴凸起） | 5 片花瓣绕花蕊均匀分布；v2.2 起替代 `ShapeGeometry` |
| 花蕊 | `InstancedMesh` / 独立几何体的暖黄小点 | 比逐个 Mesh 更轻 |
| 氛围 | `THREE.Fog(0xF9F6F0, 8, 28)` + 远处漂浮光点 | 远处花朵融入雾色，光点缓缓上升 |
| 动画 | 绽放 + 风摆动 + 摄影机呼吸；rAF 走 `smartRAF` | 标签页隐藏时暂停 |
| 资源释放 | `onBeforeUnmount` 调 `disposeObject3D` / `disposeRenderer` | 避免切走后 WebGL 上下文泄漏 |

**为什么不用 CSS 3D / 简单 emoji 平铺**：
- CSS 3D 无法做 InstancedMesh 级别的实例化，300 个 DOM 节点会拖累首屏
- emoji 平铺缺乏景深和光影层次，被用户明确反馈「视觉单薄」
- Three.js 一次注入 + 异步加载，**首屏不增加 JS 体积**（Three.js 走单独 chunk，仅花园页加载）

**降级**：`onMounted` 异步 `import('three')` 失败时，`isLoading=true` 占位文案一直显示，不阻塞页面其他模块（能量卡 / 物品列表 / 流水正常渲染）。

**为什么 Three.js 0.168**：选择当时社区稳定版本；vite.config.js 的 `manualChunks` 把 `three` 单独打成 `three-vendor` chunk，避免和 vue/gsap 混在一起。

### 1.1.6 视觉增强组件群（v2.1 加，2026-07-20；v2.2 PBR 升级，2026-07-20）

> 设计原则：**「三层渐进增强 + 能力检测 + 异步加载 + 完整降级」** —— 在 FlowerField 3D 花田基础上，为全站加入 3D / 伪 3D 背景元素和动态视觉效果，提升治愈系沉浸感；同时**不能影响首屏性能**，且**必须为 3D 渲染能力有限的浏览器实现备用机制**。决策：用「CSS 永远启用 → Canvas2D 中量级 → Three.js 按需」三层独立可降级，配套 `utils/visual.js` 能力检测。
>
> **v2.2 PBR 升级**（2026-07-20）：4 个视觉组件全部升级到 PBR 渲染管线（`ACESFilmicToneMapping` + `SRGBColorSpace` + `PCFSoftShadowMap` + `RoomEnvironment` PMREM + `UnrealBloomPass`）；新增 [utils/three-helpers.js](../frontend/src/utils/three-helpers.js) 集中 9 个共享 PBR 工具函数；新增 [SceneHint.vue](../frontend/src/components/SceneHint.vue) 交互指引横幅 + [SceneControls.vue](../frontend/src/components/SceneControls.vue) 视图控制工具栏，解决「用户不知道如何与 3D 元素交互」问题；所有 3D 场景统一 `OrbitControls`（拖拽旋转 + 滚轮缩放）+ `raycaster` 点击拾取。决策理由详见 [HANDOFF §5.11](HANDOFF.md)。

**v2.2 视觉文件群**（共 9 个，含 v2.3.3 加的 EmojiIcon.vue）：

| 文件 | 角色 | 嵌入位置 | 降级路径 |
|---|---|---|---|
| [frontend/src/utils/visual.js](../frontend/src/utils/visual.js) | 视觉能力检测（v2.3.3 Safari 兼容增强） | 被其他组件 import | 单次缓存检测结果，无降级（自身就是降级判断器）；v2.3.3 **hasWebGL 重写**（区分 WebGL1/2 + 检测扩展 + max texture size）+ 新增 `getWebGLCaps()` / `isSafari()` / `isIOS()` |
| [frontend/src/utils/three-helpers.js](../frontend/src/utils/three-helpers.js) | **PBR 工具集（v2.2 加；v2.3.3 加上下文恢复）** | 被 HeroScene / FlowerField / AmbientBackground import | 9 个共享函数：createRenderer / createEnvironment / createPostProcessing / createOrbitControls / createKeyLight / createFillLight / createSoftSpriteTexture / disposeObject3D / disposeRenderer；v2.3.3 加 `webglcontextlost` / `webglcontextrestored` 事件监听处理 **WebGL 上下文丢失** |
| [frontend/src/components/AmbientBackground.vue](../frontend/src/components/AmbientBackground.vue) | 全局氛围背景 v2 | [AppLayout.vue](../frontend/src/components/AppLayout.vue) 根（所有页面可见） | CSS 永远启用 → Canvas2D 柔光 sprite（reduced-motion 关闭）→ Three.js 双层粒子 + 轻量 Bloom（WebGL + 非低性能） |
| [frontend/src/components/HeroScene.vue](../frontend/src/components/HeroScene.vue) | 首页 3D 浮岛雾海 v2（v2.3.3 iOS 降级） | [HomeView.vue](../frontend/src/views/HomeView.vue) 顶部 | 无 WebGL / reduced-motion / initScene 异常 → SVG 静态插画（800×480 viewBox：天空渐变 + 太阳 + 3 岛 + 3 层波浪 + 5 漂浮点）；v2.3.3 **iOS 降级**：**Bloom 降级**（iOS 关闭 UnrealBloomPass）+ **PMREM 降级**（PMREM 256→128、阴影 2048→1024、dpr 2→1.5）+ `webglcontextlost` 上下文恢复 |
| [frontend/src/components/FlowerField.vue](../frontend/src/components/FlowerField.vue) | 3D 花田 v2 | [GardenView.vue](../frontend/src/views/garden/GardenView.vue) 顶部 | 无 WebGL / reduced-motion / initScene 异常 → CSS 渐变背景 + 提示文案 |
| [frontend/src/components/AudioVisualizer.vue](../frontend/src/components/AudioVisualizer.vue) | 音波可视化 v2 | [MusicDetailView.vue](../frontend/src/views/music/MusicDetailView.vue) 详情头之后 | 无 Web Audio / reduced-motion → CSS 5 色横条静态动画 |
| [frontend/src/components/SceneHint.vue](../frontend/src/components/SceneHint.vue) | **3D 场景交互指引（v2.2 加）** | 被 HeroScene / FlowerField 引用 | `pointer-events: none` 不阻挡 3D 交互；3 秒后自动淡出 |
| [frontend/src/components/SceneControls.vue](../frontend/src/components/SceneControls.vue) | **3D 场景视图控制（v2.2 加）** | 被 HeroScene / FlowerField 引用 | emit 事件由父组件处理；玻璃拟态样式 + 8px 圆角 |
| [frontend/src/components/EmojiIcon.vue](../frontend/src/components/EmojiIcon.vue) | **跨浏览器 emoji 组件（v2.3.3 加）** | 被 AppLayout.vue / ProfileView.vue 引用（品牌 / 导航 / 通知 / 资源 / 统计 / 快捷入口 / 花朵阶段） | **Iconify** + `@iconify-json/twemoji` 离线 **SVG emoji**，确保 **跨浏览器一致**（解决 Safari Apple Color Emoji vs 系统 emoji 字体差异）；无降级（SVG 本身就是跨浏览器方案） |

**核心架构决策**：

| 维度 | 决策 | 理由 |
|---|---|---|
| 三层分级 | Layer 1 CSS（永远启用）/ Layer 2 Canvas2D（reduced-motion 关闭）/ Layer 3 Three.js（WebGL + 非低性能） | 治愈系要"柔和不刺眼"，分层降级让任何设备都有体面视觉 |
| **PBR 渲染管线（v2.2）** | `ACESFilmicToneMapping` + `SRGBColorSpace` + `PCFSoftShadowMap` + `RoomEnvironment` PMREM + `UnrealBloomPass` | 替代 v2.1 的 `LinearToneMapping` + `MeshBasicMaterial`，解决「视觉粗糙过时，类似 80/90 年代红白机」问题 |
| **共享工具集（v2.2）** | [utils/three-helpers.js](../frontend/src/utils/three-helpers.js) 集中 9 个 PBR 工具函数 | 避免 4 个组件重复造轮子；统一释放逻辑避免 WebGL context 泄漏 |
| **交互指引（v2.2）** | [SceneHint.vue](../frontend/src/components/SceneHint.vue) 横幅 + [SceneControls.vue](../frontend/src/components/SceneControls.vue) 工具栏 | 解决「用户不知道如何与 3D 元素交互」问题；3 秒淡出不遮挡视野 |
| **OrbitControls（v2.2）** | 所有 3D 场景统一 `OrbitControls`（阻尼 + 极角约束 + 禁用 pan + 自动旋转） | 用户可拖拽旋转 + 滚轮缩放；阻尼让旋转有惯性；极角约束防止视角穿地 |
| **raycaster 点击拾取（v2.2）** | HeroScene 点击浮岛相机飞入；FlowerField 点击花朵显示花语 toast | 让 3D 场景「可交互」而非「只能看」 |
| 能力检测 | `utils/visual.js` 单次缓存 `hasWebGL()` / `prefersReducedMotion()` / `isMobile()` / `isLowPower()` 结果 | 避免每次渲染重复检测；`shouldUseThreeJS()` = `hasWebGL && !prefersReducedMotion && !isLowPower` |
| 异步加载 | 所有 Three.js 组件 `defineAsyncComponent(() => import(...))` | Three.js (~600KB) 不进首屏包，仅访问 `/`（HeroScene）或 `/garden`（FlowerField）时按需拉取 |
| `manualChunks` | [vite.config.js](../frontend/vite.config.js) 函数形式把 `three` + `three/addons/*` 跨组件共享 `three-vendor` chunk（v2.2 含 OrbitControls / EffectComposer / UnrealBloomPass / RoomEnvironment，gzip 719.84KB） | 与 FlowerField / HeroScene / AmbientBackground 共享同一 chunk，不重复加载 |
| Vue 响应式 | Three.js 对象用 `shallowRef` 持有 | `ref` 会深度代理 Three.js 内部 Scene/Object3D 私有字段拖累性能（详见 [HANDOFF §6.23.2](HANDOFF.md)） |
| rAF 调度 | `smartRAF(callback)` 在 `document.hidden` 时 `cancelAnimationFrame`、可见时自动恢复 | 标签页隐藏时浏览器虽降为 1 fps 但仍执行渲染循环，GPU 不释放（详见 [HANDOFF §6.23.3](HANDOFF.md)） |
| 资源释放 | `onBeforeUnmount` 调 `disposeObject3D` + `disposeRenderer` 完整释放 geometry / material / texture / renderer / composer / 事件监听 / ResizeObserver | 5 次切走后浏览器报 `Too many active WebGL contexts` 黑屏（详见 [HANDOFF §6.23.4](HANDOFF.md)） |
| 移动端降级 | 粒子数减半 + `dpr` ≤ 1.5 + Bloom strength 0.3 → 0.18 + 几何精度降档（Lathe/Cylinder 段数 24→16、Icosahedron detail 2→1、樱花树递归深度 4→3、花瓣网格 5×8→4×6、地面圆 64→32、AudioVisualizer 柱数 48/64→32） | 移动端 GPU/CPU 弱，全量粒子 + 强 Bloom + 高精度几何会掉帧；几何降档可在不牺牲视觉层次的前提下大幅减少顶点数 |
| 配色一致性 | 4 个组件全部用治愈系 5 色（藕粉 `#E8B8C5` / 淡黄 `#E8D5A8` / 青绿 `#A8C5A0` / 雾蓝 `#A8B8C5` / 纯白 `#FAF6F2`）+ 米白 `#F9F6F0` 背景 | 与 [tailwind.config.js](../frontend/tailwind.config.js) token 一致；AudioVisualizer 4 模式频响颜色低频暖色 → 高频冷色 |
| Web Audio 一次性约束 | `audioCtx.createMediaElementSource(audioEl)` 对同一 `<audio>` 元素只能调一次 | AudioVisualizer `if (!sourceNode)` 守卫 + MusicDetailView `visualizerConnected` ref 标记首次 `playIndex` 时连接（详见 [HANDOFF §6.23.1](HANDOFF.md)） |
| **Safari 兼容（v2.3.3）** | ① **`hasWebGL` 重写**（区分 WebGL1/2 + 检测扩展 + max texture size）+ `getWebGLCaps()` / `isSafari()` / `isIOS()`；② `webglcontextlost` / `webglcontextrestored` 事件监听处理 **WebGL 上下文丢失**（iOS Safari 切后台→前台触发）；③ **iOS 降级**：**Bloom 降级**（iOS 关闭 UnrealBloomPass）+ **PMREM 降级**（PMREM 256→128、阴影 2048→1024、dpr 2→1.5；老 iOS 缺 `EXT_color_buffer_half_float` 扩展时关闭 PMREM + Bloom） | 解决 Safari / iOS 用户反馈的 3D 不渲染（hasWebGL 误判 + 上下文丢失无恢复 + Bloom/PMREM 内存超限）问题（详见 [HANDOFF §6.24](HANDOFF.md)） |
| **跨浏览器 emoji 一致性（v2.3.3）** | [EmojiIcon.vue](../frontend/src/components/EmojiIcon.vue) 组件用 **Iconify** + `@iconify-json/twemoji` 离线 **SVG emoji** | 解决 Safari Apple Color Emoji vs 系统 emoji 字体风格差异，确保 **跨浏览器一致**；已替换 AppLayout.vue + ProfileView.vue 所有 emoji |

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

详见 [frontend/src/components/AmbientBackground.vue](../frontend/src/components/AmbientBackground.vue) + [HeroScene.vue](../frontend/src/components/HeroScene.vue) + [AudioVisualizer.vue](../frontend/src/components/AudioVisualizer.vue) + [FlowerField.vue](../frontend/src/components/FlowerField.vue) + [SceneHint.vue](../frontend/src/components/SceneHint.vue) + [SceneControls.vue](../frontend/src/components/SceneControls.vue) + [EmojiIcon.vue](../frontend/src/components/EmojiIcon.vue) + [utils/visual.js](../frontend/src/utils/visual.js) + [utils/three-helpers.js](../frontend/src/utils/three-helpers.js)，决策理由详见 [HANDOFF §5.10](HANDOFF.md) + [HANDOFF §5.11](HANDOFF.md)，4 大坑详见 [HANDOFF §6.23](HANDOFF.md)，Safari 兼容 3 大坑详见 [HANDOFF §6.24](HANDOFF.md)。

---

## 1.1.7 v2.3 六大四字名板块 + 双资源系统 + 花朵生命周期 + 通知 + 个人主页（2026-07-25 加）

> 设计原则：**「四字名治愈系命名 + 双资源经济 + 生命周期叙事 + 通知触达」** —— 用更具东方治愈调性的命名替代纯功能名；把原单一能量语义拆为 `露水`（向内获得：听歌/打卡/写日记，用于浇灌花朵）+ `落叶`（向外获得：花朵枯萎后拾取，用于兑换花种）；用花朵生命周期（seed→sprout→bud→bloom→wilted）把屿上花田变成「持续可养护」的陪伴场景；用通知系统把漂流瓶评论返回等零散事件汇总成统一触达入口。

### 1.1.7.1 六大四字名板块 + 路由对照（含顶部品牌图标更新）

| 四字名 | 路由 | 前端视图 | 后端 API |
|---|---|---|---|
| 琴音疗心 | `/music` | [MusicListView.vue](../frontend/src/views/music/MusicListView.vue) | `/api/music/*` |
| 日记海岸 | `/diary` | [DiaryListView.vue](../frontend/src/views/diary/DiaryListView.vue) | `/api/diary/*` |
| 情绪日历 | `/calendar` | [MoodCalendarView.vue](../frontend/src/views/mood/MoodCalendarView.vue) | `/api/mood/*` |
| 静屿角落 | `/corner` | [CornerView.vue](../frontend/src/views/diary/CornerView.vue) | `/api/diary/corner` |
| 落叶花坊 | `/shop` | [ShopView.vue](../frontend/src/views/garden/ShopView.vue) | `/api/garden/shop` + `/api/energy/exchange` |
| 屿上花田 | `/garden` | [GardenView.vue](../frontend/src/views/garden/GardenView.vue)（含花田生长网格） | `/api/garden/*` + `/api/garden/flowers/*` |

辅助入口：拾瓶 `/diary/pick`（日记海岸子路由）/ 我的 `/profile`（个人主页，`requiresAuth`）；通知中心 `/notifications`（独立页，`requiresAuth`）。

[AppLayout.vue](../frontend/src/components/AppLayout.vue) 顶部品牌图标为 🏝️ 岛屿；桌面/平板/移动三档导航同步四字短标签；移动端 tabbar 固定核心项 + 中央「更多」抽屉。

### 1.1.7.2 双资源系统（露水 + 落叶）

**资源哲学**：
- `露水` = `User.total_energy`（保留原字段，语义即露水）= **向内获得**：听歌 / 打卡 / 写日记；用于浇灌花朵、兑换装扮
- `落叶` = `User.leaves`（v2.3 新增）= **向外获得**：花朵枯萎后拾取；用于在落叶花坊兑换花种（寓意「落叶归根能施肥种花」）
- `EnergyRecord` **不**加 `resource_type` 字段；资源类型由 `source` + `ShopItem.cost_currency` 体现

**模型层**（[app/models/user.py](../app/models/user.py) + [app/models/garden.py](../app/models/garden.py)）：
```python
# User
total_energy: Mapped[int] = mapped_column(Integer, default=0)   # 露水（保留原字段）
leaves: Mapped[int] = mapped_column(Integer, default=0)         # 落叶（v2.3 加）

# ShopItem
cost_currency: Mapped[str] = mapped_column(String(20), default="dew", nullable=False)
# "dew"（装扮/徽章）| "leaves"（花种）
```

**Service 层**（[app/services/energy_service.py](../app/services/energy_service.py) + [app/services/flower_service.py](../app/services/flower_service.py)）：
- `grant_energy(db, user, amount, source, ...)` 维持原签名，写 `EnergyRecord` + 累加 `User.total_energy`（仅露水有日上限 20）
- `exchange_item` 按 `ShopItem.cost_currency` 扣 `total_energy` 或 `leaves`
- `water_flower` 显式 `db.query(User).filter(...).update({User.total_energy: User.total_energy - 1})` 扣 1 露水
- `collect_wilted_leaves` 显式 `db.query(User).filter(...).update({User.leaves: User.leaves + 2})` 加 2 落叶

**常量层**（[app/utils/constants.py](../app/utils/constants.py)）：
- `DEFAULT_SHOP_ITEMS` 28 件全部带 `cost_currency`：11 件花种 = `leaves`，12 件装扮 = `dew`，5 件徽章 = `dew`（自动触发）
- `DAILY_ENERGY_LIMITS`：`listen_music: 20 / write_diary: 10 / checkin: 5 / encourage: 10`（仅露水有日上限，落叶无日上限）

**资源获取规则**：

| 行为 | 增量 | 资源 | 来源 code |
|---|---|---|---|
| 听完一首曲子（进度 ≥ 90%） | +1 露水 | total_energy | `listen_music` |
| 写完一篇日记 | +2 露水 | total_energy | `write_diary` |
| 当日心情打卡 | +1 露水 | total_energy | `checkin` |
| 给他人漂流瓶留言鼓励 | +1 露水 | total_energy | `encourage` |
| 连续 7 天打卡 | +5 露水 | total_energy | `streak_7` |
| 兑换商店物品 | -cost（按 item.cost_currency） | dew/leaves | `exchange` |
| 浇灌花朵 | -1 露水 | total_energy | `water_flower` |
| 拾取枯萎花朵 | +2 落叶 | leaves | `collect_wilted_leaves` |

### 1.1.7.3 花朵生命周期（UserFlower + flower_service + API + 前端）

**模型**（[app/models/garden.py](../app/models/garden.py)）：
```python
class UserFlower(Base):
    __tablename__ = "user_flowers"
    id, user_id, flower_type, stage, watered_count,
    planted_at, last_watered_at, bloom_at, wilted_at
    # 5 阶段：seed → sprout → bud → bloom → wilted
```
常量：`STAGE_SEED/STAGE_SPROUT/STAGE_BUD/STAGE_BLOOM/STAGE_WILTED` + `STAGE_ORDER` + `WATER_TO_NEXT_STAGE = {seed: 2, sprout: 3, bud: 2, bloom: 0, wilted: 0}` + `WILT_DAYS_AFTER_BLOOM = 7`。

**Service**（[app/services/flower_service.py](../app/services/flower_service.py)）：
- `list_my_flowers(db, user_id)` — 列出所有花朵（含枯萎待拾取的）；lazy 检查盛开花朵是否到枯萎时间
- `water_flower(db, user, flower_id)` — 浇 1 露水（`total_energy -1`），累加 `watered_count`，达阈值升级；盛开后再浇水仅刷新 `last_watered_at` 延长枯萎；枯萎花不能浇
- `collect_wilted_leaves(db, user, flower_id)` — 拾取枯花 → +2 落叶 → 删除该花
- `get_flower_detail(db, user, flower_id)` — 单朵详情（lazy 检查枯萎）
- `_check_wilt(flower)` — 内部函数：盛开超过 `WILT_DAYS_AFTER_BLOOM` 天未浇水 → 标记 `wilted` + 写 `wilted_at`

**API**（[app/routers/garden.py](../app/routers/garden.py)）：
- `GET /api/garden/flowers` — 我的所有花朵
- `GET /api/garden/flowers/{id}` — 单朵详情
- `POST /api/garden/flowers/{id}/water` — 浇水（消耗 1 露水，返回 `new_total_energy`）
- `POST /api/garden/flowers/{id}/collect` — 拾取枯花（返回 `gained_leaves` + `new_leaves`）

**前端**：[GardenView.vue](../frontend/src/views/garden/GardenView.vue) `STAGE_INFO` 映射（emoji/label/progress/desc）+ 浇水按钮 + 拾取按钮 + 移动端单列网格。

### 1.1.7.4 通知系统（Notification + 轮询）

**模型**（[app/models/notification.py](../app/models/notification.py)）：
```python
class Notification(Base):
    __tablename__ = "notifications"
    id, user_id, type, content, related_id, is_read, created_at
    # type: "encouragement"（漂流瓶评论返回）/ "system"（预留）
```

**Router**（[app/routers/notification.py](../app/routers/notification.py)）（**单数形式**）：
- `GET /api/notifications` — 通知列表（最近 50 条）
- `GET /api/notifications/unread` — 未读数（返回 `{unread: int}`）
- `POST /api/notifications/{id}/read` — 标记单条已读
- `POST /api/notifications/read-all` — 全部已读

**触发点**：读者在拾瓶后留鼓励语 → 写 `Encouragement` + 同步写 `Notification(type='encouragement', user_id=作者, related_id=diary_id)`。

**前端**：[AppLayout.vue](../frontend/src/components/AppLayout.vue) 顶部 + 移动端 topbar 加 🔔 铃铛 + 红点未读数；`onMounted` 起 60s 轮询 `/api/notifications/unread`；点击跳 `/notifications` 页（非下拉）。独立页 [NotificationsView.vue](../frontend/src/views/notification/NotificationsView.vue) 列表 + 未读高亮 + 单条已读 + 全部已读。

### 1.1.7.5 个人主页（profile router + ProfileView）

**Router**（[app/routers/profile.py](../app/routers/profile.py)）：
- `GET /api/profile` — 我的主页（基本信息 + 双资源 + 完整统计 + 连续打卡）
- `GET /api/profile/stats` — 轻量统计快照
- `GET /api/profile/{user_id}` — 他人主页（仅公开信息）

统计字段：`diary_count` / `public_diary_count` / `checkin_count` / `listen_count` / `flower_count` / `garden_item_count` / `received_encouragement_count` / `streak`（连续打卡天数，由 `mood_service.get_current_streak` 计算）。

**前端**：[ProfileView.vue](../frontend/src/views/profile/ProfileView.vue) — 卡片式布局：🏝️ 头像 + 昵称 + 在岛天数 + 双资源条（露水/落叶）+ 6 统计卡（日记/打卡/听曲/花朵/收到鼓励/岛上物件）+ 快捷入口；路由 `/profile` 加入 `requiresAuth: true` 守卫。

### 1.1.7.6 西洋曲谱（musics 迁移 + seed 幂等 + API 参数）

**模型**（[app/models/music.py](../app/models/music.py)）：
```python
category: Mapped[str] = mapped_column(String(20), default="classic", nullable=False)
# "classic"（五音传统古曲）| "western"（西洋曲谱）
```

**常量**：[app/utils/constants.py](../app/utils/constants.py) 新增 `class MusicCategory(str, Enum)`：`CLASSIC = "classic"` / `WESTERN = "western"`。

**seed**（[app/seed.py](../app/seed.py)）：`SEED_MUSIC` 含 6 首西洋改编——绿袖子（yu）/ 卡农（gong）/ 致爱丽丝（jue）/ 月光奏鸣曲（yu）/ 天鹅湖（shang）/ 昨日重现（zhi）；`seed_music()` 按 title 幂等，老库重启自动补齐。

**API**（[app/routers/music.py](../app/routers/music.py)）：
- `GET /api/music?category=western|classic` — query 参数过滤
- `GET /api/music/yin/{yin}` — **只返回 `category=="classic"`**，西洋曲不混入五音页

**前端**：[MusicListView.vue](../frontend/src/views/music/MusicListView.vue) 把西洋曲作为第六张卡并入六宫格；[MusicWesternView.vue](../frontend/src/views/music/MusicWesternView.vue) 为独立列表页。路由 `/music/western` **必须放在 `/music/:yin` 前面**避免动态段捕获。

### 1.1.7.7 日记与静屿角落（明文 + is_public）

**模型**（[app/models/diary.py](../app/models/diary.py)）：
```python
content: Mapped[str] = mapped_column(Text, nullable=False, default="")  # 明文
content_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)  # 遗留字段
is_public: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
send_to_ai_hole: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)  # 遗留列，固定 False
```
`User.encryption_salt` 保留仅为兼容老库（v2.3 起日记改明文，不再使用）。

**发布选项**（前端 radio）：
- 放入漂流瓶：`is_public=True`，公开可见 + 允许评论。
- 留在静屿角落：`is_public=False`，仅自己可见，集中显示在 `/corner`。

**前端**：[DiaryWriteView.vue](../frontend/src/views/diary/DiaryWriteView.vue) 两个选项；[CornerView.vue](../frontend/src/views/diary/CornerView.vue) 读取 `GET /api/diary/corner`，可删除。

### 1.1.7.8 情绪日历对齐修复（emoji 字符统一 + 字段名对齐）

- `MoodCheckin` 用 `mood_emoji` + `check_date`；`MOOD_INFO` 7 种心情：ecstatic 🤩 / happy 😊 / calm 😌 / tired 😪 / anxious 😰 / angry 😠 / sad 😢。
- 一天可多条；今日记录可删除；30 天趋势柱状图在 v2.5.3 移除，罗素情绪环保留。

### 1.1.7.9 静屿角落（v2.6.0 取代 AI 树洞）

- **背景**：v2.6.0 删除 AI 树洞对话、会话历史与「树洞倾心」徽章；原「不放入漂流瓶」的私密日记需要一个集中入口。
- **实现**：`is_public=False` 的日记统一视为「静屿角落」碎碎念，`GET /api/diary/corner` 按 `user_id + is_public=False` 返回；前端 `/corner` 页面可写、可看、可删。
- **为什么复用 `diaries` 而不是新表**：内容结构完全一致，复用可避免两套写入/删除/权限逻辑；`is_public` 已经是「公开/私密」的天然分界。
- **旧数据**：原 `send_to_ai_hole=True` 的日记自动落入角落（因为它们本来就是 `is_public=False`）；旧 AI 对话文件已删除。

### 1.1.7.10 数据库迁移（`_migrate_legacy_columns()` 一次性自动加列）

[app/database.py](../app/database.py) `_migrate_legacy_columns()` 新增：
- `users` 加 `leaves INTEGER DEFAULT 0 NOT NULL`（`total_energy` 即露水，原已存在不改）
- `diaries` 加 `content TEXT NOT NULL DEFAULT ''`（`send_to_ai_hole` 是 v2.6.0 前遗留列，保留映射只为兼容老库）
- `shop_items` 加 `cost_currency VARCHAR(20) DEFAULT 'dew' NOT NULL`
- `musics` 加 `category VARCHAR(20) DEFAULT 'classic' NOT NULL`
- 新表 `user_flowers` / `notifications` 由 `init_db()` 自动建表（`Base.metadata.create_all`）

### 1.1.7.11 pre-commit 5 项 checklist（正式化）

详见 [HANDOFF §12.4](HANDOFF.md) / [README §9.3](../README.md) / [AGENTS.md](../AGENTS.md)。5 项：
1. Pydantic Out schema 是否补了新字段（→ [§7.7](#77-pydantic-schema-字段完整性防-611-静默过滤) / [DEVELOPMENT §3.10](DEVELOPMENT.md)）
2. `_migrate_legacy_columns()` 是否补了老库列（→ [§9.4](#94-加一个新字段到旧库轻量迁移不引-alembic) / [HANDOFF §6.10](HANDOFF.md)）
3. `constants.py` 业务常量同步（→ [§4.3](#43-单日能量上限)）
4. `.env.example` 配置同步
5. README / HANDOFF 速查表同步

---

## 1.1.8 v2.4.0 头像/昵称编辑 + 一天多条心情 + 花坊扩充（2026-08-10 加）

> 设计原则：**「情绪多变允许多次记录 + 头像个性化 + 花坊扩充丰富经济」** —— 情绪是多变的，一天可以有多次心情打卡；用户头像/昵称可自定义；花坊扩充花种/装扮/徽章让双资源经济更丰富。

### 1.1.8.1 头像/昵称编辑流程（User.avatar + PATCH /api/profile + ProfileUpdateIn）

**模型**（[app/models/user.py](../app/models/user.py)）：
```python
avatar: Mapped[str] = mapped_column(String(255), default="🙂", nullable=False)
# emoji 字符或上传图片 URL，默认 🙂
```

**数据库迁移**（[app/database.py](../app/database.py) `_migrate_legacy_columns()`）：
- `ALTER TABLE users ADD COLUMN avatar VARCHAR(16) DEFAULT '🙂' NOT NULL`（v2.4 初版；v2.4.4 改为 `String(255)` 存图片 URL）

**Schema**（[app/schemas/profile.py](../app/schemas/profile.py)）：
```python
class ProfileUpdateIn(BaseModel):
    nickname: str | None = Field(None, min_length=2, max_length=20)
    avatar: str | None = Field(None, min_length=1, max_length=255)
```

**Router**（[app/routers/profile.py](../app/routers/profile.py)）：
- `PATCH /api/profile` — 更新头像/昵称（昵称查重 409，头像 1-255 字符）
- `POST /api/profile/avatar` — 上传 JPG/PNG/WebP/GIF（≤2MB），返回 URL

**前端**：
- [ProfileView.vue](../frontend/src/views/profile/ProfileView.vue) 头像/昵称编辑弹窗（24 个可选 emoji + 图片上传）
- [stores/user.js](../frontend/src/stores/user.js) 新增 `updateProfile` action（调用 `PATCH /api/profile`）
- **头像展示**：AI 树洞已删除；当前头像只用于个人主页 / 导航。

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
  │                                      │ 3. avatar 长度校验（1-255 字符）
  │                                      │ 4. UPDATE users SET ... 
  │                                      │ 5. 返回更新后 user 对象
  │ ←─ 200 + {user}                      │
  │                                      │
  │ Pinia userStore.setUser(user)        │
  │ → 个人主页 / 导航头像更新            │
```

### 1.1.8.2 一天多条心情数据模型（mood_checkins 唯一约束移除 + add_checkin + get_today_moods + 平均分）

**背景**：情绪是多变的，一天可以有多次心情打卡，原 `(user_id, check_date)` 唯一约束限制了这一表达。

**数据库迁移**（[app/database.py](../app/database.py) `_migrate_legacy_columns()`，SQLite 重建表方式）：
```sql
-- SQLite 不支持 DROP CONSTRAINT；且不能用 CREATE TABLE AS SELECT（会丢主键 / 自增）
CREATE TABLE mood_checkins_new (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  check_date DATE NOT NULL,
  mood_emoji VARCHAR(20) NOT NULL,
  note VARCHAR(500),
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL
);
INSERT INTO mood_checkins_new (id, user_id, check_date, mood_emoji, note, created_at)
  SELECT id, user_id, check_date, mood_emoji, note, created_at FROM mood_checkins;
DROP TABLE mood_checkins;
ALTER TABLE mood_checkins_new RENAME TO mood_checkins;
CREATE INDEX ix_mood_checkins_user_id ON mood_checkins (user_id);
CREATE INDEX ix_mood_checkins_check_date ON mood_checkins (check_date);
```

**Service**（[app/services/mood_service.py](../app/services/mood_service.py) 重构）：
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

### 1.1.8.3 落叶花坊双资源经济（DEFAULT_SHOP_ITEMS 28 件 + 每板块徽章）

**命名**：模块名「落叶花坊」（v2.4.3 起；早期叫「花坊 / 落叶画坊」）。

**常量**（[app/utils/constants.py](../app/utils/constants.py) `DEFAULT_SHOP_ITEMS` 共 28 件）：
- 11 花种（leaves 资源）：向日葵 / 竹子 / 雏菊 / 莲花 / 薰衣草 / 郁金香 / 樱花 / 桃花 / 青松 / 小麦 / 青叶
- 12 装扮（dew 资源）：竹编帽 / 茶具 / 小鸟 / 折扇 / 小鸭 / 油纸伞 / 小狗 / 斗篷 / 鱼竿 / 橘猫 / 乌篷船 / 火烈鸟
- 5 徽章（dew 资源，自动触发）：琴音知音 / 日记达人 / 七日静心 / 拾瓶旅人 / 花间客

**每板块徽章对应关系**：

| 徽章 | 对应板块 | 触发条件 |
|---|---|---|
| 琴音知音 | 琴音疗心 | 累计听完 10 首 |
| 日记达人 | 日记海岸 | 累计写 30 篇日记 |
| 七日静心 | 情绪日历 | 连续打卡 7 天 |
| 拾瓶旅人 | 拾瓶 / 鼓励 | 留言鼓励满 10 次 |
| 花间客 | 屿上花田 | 种满 10 朵花 |

### 1.1.8.4 其他 v2.4.0 改动

- **首页文案**：'海上有座岛，岛上有人听' → '潮声不止，心安自屿'，删除'静屿'副标题 + 删除'今日打卡'板块
- **'漂流日记'入口统一**：直接显示'日记海岸'界面（含拾瓶/写日记模块）
- **情绪日历 emoji 显示/选择修复**：[MoodCalendarView.vue](../frontend/src/views/mood/MoodCalendarView.vue) 多条打卡支持
- **心语树洞 AI 系统提示词 humanize**：更接地气、像朋友聊天（该模块已在 v2.6.0 删除）
- **花田 AI 显示基于实际种花情况**：[GardenView.vue](../frontend/src/views/garden/GardenView.vue) 没种花不显示 AI
- **'我的'页面修复**：'收到鼓励'/'岛上物件'可点击跳转，删除重复'岛上物件'，新增**静屿使用指南**（7 个模块详细介绍；AI 树洞已在 v2.6.0 删除）
- **露水累加修复**：写日记和留言鼓励后正确发放露水

---

## 1.1.9 情绪日历：罗素情绪环模型（当前形态）

> 说明：v2.4.1 首次用情绪环替换趋势柱状图；v2.4.5 恢复柱状图与环并存；**v2.5.3 再次移除 30 天趋势柱状图**。当前页面 = 月历网格 + 罗素情绪环 + 今日打卡（可删除）；`fetchTrend` 仍调用，仅用于 `currentStreak` 连胜显示。

> 设计原则：**「情绪可视化从线性趋势升级为二维情绪空间」** —— 将情绪日历的 30 天趋势柱状图替换为罗素情绪环模型（Russell's Circumplex Model of Affect）四象限图表，用效价（Valence）+ 唤醒度（Arousal）二维坐标系把情绪可视化，帮助用户更立体地理解自己的情绪分布。

**文件**：[frontend/src/views/mood/MoodCalendarView.vue](../frontend/src/views/mood/MoodCalendarView.vue)

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

- **已追踪情绪（7 种）**：ecstatic / happy / calm / tired / anxious / angry / sad —— 映射后端 [MOOD_INFO](../app/utils/constants.py)，有真实打卡数据，边框高亮 + 次数角标
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

## 1.2 开发 / 生产模式切换

> 当前默认是**生产模式**（v2.3.2 起）。`python start.py` = FastAPI :5000 单进程；只有显式 `--dev` 才启动 Vite :5000 + FastAPI :5001 双进程。

### 1.2.1 生产模式（默认）

```
浏览器 → http://127.0.0.1:5000/
  → FastAPI (:5000)
      ├─ /api/* → JSON API
      ├─ /static/* → 静态资源（含 dist/）
      ├─ /admin/* → 后台 SSR（Jinja2）
      └─ 其他 GET → SPA fallback → static/dist/index.html
```

- `python start.py`：`static/dist/index.html` 不存在时自动 `npm install + npm run build`，然后 FastAPI 单进程启动。
- 用户始终访问 :5000；Vite 不运行，服务器不需要 Node.js 运行时（仅首次构建需要）。
- 前端改动后必须重新构建（`python start.py build` 或 `cd frontend && npm run build`），否则仍返回旧 dist。

### 1.2.2 开发模式（`--dev`）

```
浏览器 → Vite dev server (:5000) → proxy /api /static /admin /docs /openapi.json → FastAPI (:5001)
```

- `python start.py --dev`：自动检测 `frontend/node_modules`，不存在则 `npm install`；Vite 占 :5000（HMR），FastAPI 退到 :5001。
- 开发时只访问 :5000；要看 Swagger 直接访问 :5001/docs。
- Vite `host` 必须写 `127.0.0.1`（避免 IPv6 `[::1]`），`strictPort: true` 防止端口漂移。

### 1.2.3 端口对照

| 模式 | 用户访问 | Vite | FastAPI | 启动 |
|---|---|---|---|---|
| 生产（默认） | :5000 | 不运行 | :5000（API + SPA + 静态） | `python start.py`（dist 不存在则自动构建） |
| 开发（`--dev`） | :5000 | :5000（入口 + HMR） | :5001（API） | `python start.py --dev` |

**为什么开发模式让 Vite 占 :5000**：FastAPI 反代 Vite 内部路径（含 null 转义 / 冒号）会失败，所以让 Vite 直接占用户入口，FastAPI 退到 :5001 专做 API。详见 [HANDOFF §6.16](HANDOFF.md)。

### 1.2.4 SPA fallback 路径排除（必读）

[app/main.py](../app/main.py) 末尾的通配路由 `@app.get("/{path:path}")` **必须**排除以下路径（详见 [HANDOFF §6.15](HANDOFF.md)）：

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

## 3. 鉴权流

```
浏览器                          FastAPI
  │ POST /api/auth/login           │
  │ {nickname, password}           │
  ├───────────────────────────────→│ 1. bcrypt.verify
  │                                │ 2. 签 qi_session cookie
  │ ←─ 200 + Set-Cookie            │
  │                                │
  │ GET /api/diary                 │
  │ Cookie: qi_session=...         │
  ├───────────────────────────────→│ 1. 验签 cookie → user
  │                                │ 2. 按 user_id 查 diaries
  │ ←─ 200 [{id, content, ...}]    │
```

**关键点**：
1. 密码只在登录时校验；之后仅靠签名 cookie 识别用户。
2. 前端不保存 token；只把 user 对象缓存到 localStorage。
3. 日记是明文存储，读接口按 `user_id` 做属主校验，不存在「服务端解密」步骤。
4. 详细依赖：`get_current_user` / `get_current_user_optional` 见 [app/deps.py](../app/deps.py)；会话签名见 [app/security.py](../app/security.py)。

---

## 4. 数据库架构

### 4.1 实体关系

```
users 1:N diaries / mood_checkins / energy_records / garden_items / user_flowers / notifications
diaries 1:N encouragements
shop_items 1:N garden_items
```

> **Session 规则（v2.6.2）**：routers 和 [app/deps.py](../app/deps.py) 必须引用**同一个** `app.database.get_db`。如果 deps 再包一层 `get_db`，FastAPI 会创建两个 session，`get_current_user` 返回的 `user` 与端点 `db` 分离，`db.refresh(user)` 会报 `Instance is not persistent`，写操作也可能静默失效。详见 [HANDOFF §6.25](HANDOFF.md)。

> **外键**：SQLite 连接建立时执行 `PRAGMA foreign_keys=ON`，让 `ondelete="CASCADE"` 真正生效（v2.6.2）。

### 4.2 关键表字段

| 表 | 关键字段 | 业务含义 |
|---|---|---|
| `users.encryption_salt` | str | **遗留字段**：v2.3 前用于日记加密，现在不再使用 |
| `users.total_energy` | int | 露水（向内获得，用于浇花；用 `db.query().update()` 更新） |
| `users.leaves` | int | 落叶（花朵枯萎后拾取，用于兑换花种） |
| `users.is_admin` / `avatar` | bool / str | 后台管理员 / 头像（emoji 或上传图片 URL） |
| `diaries.content` | text | **明文日记**（v2.3 起） |
| `diaries.content_encrypted` | str? | **遗留字段**，仅兼容老库，新数据不写 |
| `diaries.is_public` | bool | True=漂流瓶；False=静屿角落（仅自己可见） |
| `mood_checkins.check_date` | date | 一天可多条（v2.4 移除唯一约束） |
| `energy_records.source` | str | `listen_music` / `write_diary` / `checkin` / `streak_7` / `encourage` / `baduanjin` / `exchange` / `admin_adjust` |
| `garden_items.item_id` | int | FK → `shop_items.id` |
| `user_flowers.stage` | str | `seed` / `sprout` / `bud` / `bloom` / `wilted` |
| `encouragements.from_user_id` | int | 留言者；`to_user_id` 是作者（用于通知） |
| `baduanjin_checkins` | user_id, check_date, move_key | 八段锦跟练打卡（用户+日期唯一） |
| `therapy_interests` | user_id, product_key, product_name | 好物预约意向（不涉及支付） |

### 4.3 单日能量上限

在 [app/utils/constants.py](../app/utils/constants.py)：

```python
DAILY_ENERGY_LIMITS = {
    "listen_music": 20,
    "write_diary": 10,
    "checkin": 5,
    "encourage": 10,
    "baduanjin": 1,
}
```

`energy_service.grant_energy()` 每次发放前查当天累计，超限返回 `None`（不写流水）。`streak_7` 等一次性奖励用 `bypass_limit=True`。

---

## 5. 后台 SSR（仅 `/admin/*`）

> 前台是 Vue 3 SPA；后台仍保留 Jinja2 SSR，这是刻意隔离，不是历史遗留。

- 路由：[app/routers/admin_pages.py](../app/routers/admin_pages.py)，模板在 [templates/admin/](../templates/admin/)。
- 页面：登录 / 概览 / 用户列表 / 用户详情 / 日志 / 系统维护，共 6 个；样式独立在 [static/css/07-admin.css](../static/css/07-admin.css)，JS 在 `static/js/pages/admin_*.js`。
- 鉴权：[app/deps.py](../app/deps.py) 的 `get_current_admin`（API）/ `get_current_admin_or_redirect`（页面）。
- 与前台不共享 AppLayout / Tailwind / Pinia / axios；后台出问题不影响前台 SPA。
- 旧的前台 Jinja2 模板和 `static/js/pages/*.js` 已在 v2.4.2 清理，不要再按旧文档往 `templates/` 加前台页面。

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

> 设计原则：**「管理用户」而不「窥视用户」** —— 后台只做运维治理，不提供读日记正文的 API；但日记是明文存储，数据库文件本身可读（见 §6.5.4）。

### 6.5.1 模块组成

| 层 | 文件 | 说明 |
|---|---|---|
| API | [app/routers/admin.py](../app/routers/admin.py) | 全部 `/api/admin/*` JSON 端点 |
| 页面 | [app/routers/admin_pages.py](../app/routers/admin_pages.py) | 全部 `/admin/*` SSR 页面 |
| Schema | [app/schemas/admin.py](../app/schemas/admin.py) | Pydantic 入参/出参 |
| 鉴权 | [app/deps.py](../app/deps.py) `get_current_admin` / `get_current_admin_or_redirect` | 未登录 → 401 / 302；非 admin → 403 |
| 配置 | [app/config.py](../app/config.py) | `QI_ADMIN_USERNAME/PASSWORD/PATH_PREFIX` |
| 种子 | [app/seed.py](../app/seed.py) | 首次启动自动创建首管，密码随机 → `logs/healing.log` |
| 模板 | `templates/admin/` | 7 个 .html（_base + 6 页面） |
| 样式 | [static/css/07-admin.css](../static/css/07-admin.css) | 暗色侧栏 + 表格 + 模态（与前台完全隔离） |
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
- **robots meta `noindex,nofollow`**（[templates/admin/_base.html](../templates/admin/_base.html)）
- 用户必须知道 URL + 管理员账号才能进
- 与前台**完全独立**：
  - 不共享 base.html（后台有独立 `admin/_base.html`）
  - 不共享 nav / Toast
  - 不共享 CSS 入口（[static/css/07-admin.css](../static/css/07-admin.css) 独立）
  - JS 也独立（`admin_*.js`）

### 6.5.4 「管理」与「窥视」的分界

| 能做 | 不能做 |
|---|---|
| 看昵称 / 能量 / 创建时间 / 日记数量（不读内容） | 通过 API 读日记正文（后台接口未提供） |
| 重置用户密码 | 导出全库 |
| 删除账号 | 删自己 / 改自己的 `is_admin`（防手滑） |
| 调整能量（写流水，source=`admin_adjust`） | 绕过 cookie 鉴权（API 全部 `Depends(get_current_admin)`） |
| 看运行日志 | — |
| 一键清 `__pycache__` | — |

> ⚠️ 日记当前是明文存储：后台 API 不返回正文，但**数据库本身没有加密**，拥有 DB 文件的人可以直接读。不要把它描述成端到端加密。

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

- 重置时只改 `password_hash`；`encryption_salt` 已不再参与日记（v2.3 起明文存储）。
- 重置密码不会影响已有日记的可读性（因为没有日记密钥）。
- 但仍建议用户使用强密码，并在 `.env` 固定管理员密码，避免默认随机密码丢失。

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

> 设计原则：**「渐进增强」+「不污染数据」+「治愈系温柔语气」** —— AI 是「锦上添花」而非核心功能，没配 key 也能跑；AI 输出不写入数据库。

### 6.6.1 模块组成

| 层 | 文件 | 说明 |
|---|---|---|
| 配置 | [app/config.py](../app/config.py) | `nvidia_api_key` / `ai_model` / `ai_base_url`，从 `.env` 读 |
| Schema | [app/schemas/ai.py](../app/schemas/ai.py) | 4 个模型：`AIEncouragementIn` / `AIHealingIn` / `AIMusicRecommendIn` / `AIMusicRecommendOut` |
| Service | [app/services/ai_service.py](../app/services/ai_service.py) | `AIServiceUnavailable` + 3 个系统提示词 + `_call_nvidia()` + 3 个上层方法 |
| Router | [app/routers/ai.py](../app/routers/ai.py) | 3 个端点（全部需登录 + 全部 try/except 降级），prefix=`/api/ai` |
| 入口注册 | [app/main.py](../app/main.py) | `app.include_router(ai.router)` |
| 外部依赖 | NVIDIA NIM API | `https://integrate.api.nvidia.com/v1/chat/completions`，当前模型 `z-ai/glm-5.3-flash`；3 次线性退避重试；reasoning 模型 `max_tokens` 需 900–1200 |

### 6.6.2 调用流（3 个场景同构）

```
浏览器 → POST /api/ai/<scene> → get_current_user → ai_service.generate_xxx()
      → _call_nvidia(system_prompt, user_content) → NVIDIA /chat/completions
      → 200 + 文案；失败 → 200 + available:false + 友好提示
```

### 6.6.3 3 个场景

| # | 场景 | 端点 | 前端集成点 | AI 文案去向 |
|---|---|---|---|---|
| 1 | 漂流瓶 AI 鼓励语 | `POST /api/ai/encouragement` | [PickBottleView.vue](../frontend/src/views/diary/PickBottleView.vue) | 现场文案，**不写库**；日记内容只取前 120 字 |
| 2 | 情绪日历 AI 治愈语 | `POST /api/ai/healing` | [MoodCalendarView.vue](../frontend/src/views/mood/MoodCalendarView.vue) | 今日心情卡片下方，**不落库** |
| 3 | 音乐 AI 心情推荐 | `POST /api/ai/recommend-music` | [MusicListView.vue](../frontend/src/views/music/MusicListView.vue) | 五音之一 + 理由，**不落库** |

> AI 树洞对话、会话历史与「树洞倾心」徽章已在 v2.6.0 删除；私密碎碎念改存「静屿角落」。

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
| 漂流瓶 AI 鼓励语 | 后端读日记明文 → **截断到前 120 字** → NVIDIA → 返回文案给读者 | ❌ 文案不入库 |
| 情绪日历 AI 治愈语 | 心情 emoji + 可选 note → NVIDIA → 返回治愈语 | ❌ 不入库 |
| 音乐 AI 心情推荐 | 用户描述的状态文本 → NVIDIA → 返回五音之一 + 理由 | ❌ 不入库 |

> 日记本身是明文存储；AI 调用只是在函数栈内临时读取，不写日志、不写库。隐私承诺应表述为「AI 输出不落库 + 日记正文只在调用时截断发送」，不要表述为「端到端加密」。

详见 [HANDOFF §5.7](HANDOFF.md) AI 接入选型理由。

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

### 7.3 日记（明文，v2.3 起）

- 写日记：前端直接发 `content` 明文，服务端写 `diaries.content`。
- 读日记：按 `user_id` 做属主校验；公开漂流瓶（`is_public=True`）可被其他登录用户拾取。
- `content_encrypted` / `encryption_salt` 仅为老库兼容，不再参与新数据。

**安全边界**：
- 后台 API 不返回日记正文，只返回数量 / 时间。
- 但数据库层面**没有加密**：数据库泄露 = 日记明文泄露。
- 因此产品文案不要再承诺「端到端加密」；若未来要恢复，需重新设计密钥与找回流程。

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
- 详见 [HANDOFF §6.11](HANDOFF.md) / [DEVELOPMENT §3.10](DEVELOPMENT.md)

> 🔒 **2026-07-19 v2.0 Vue 3 重构后文档 Iron Rule 仍然适用**（6 份文档同步）：
> 完整规则见 [HANDOFF §12](HANDOFF.md)；本文件相关引用点 — 顶部提醒 + 本节 + [§1.1 前端架构](#11-前端架构vue-3-spa2026-07-19-v20-加) + [§1.2 开发/生产模式切换](#12-开发生产模式切换2026-07-19-v20-加) + [§5 旧 SSR 模式](#5-前端架构旧-jinja2-ssr-模式2026-07-19-v20-起仅-admin后台保留)。
> **改 Vue 3 前端代码（[`frontend/src/`](../frontend/src/)）+ 后端 SPA fallback（[app/main.py](../app/main.py)）= 同一 commit 同步更新 6 份文档**（README / HANDOFF / PROJECT_STATE / ARCHITECTURE / DEPLOYMENT / DEVELOPMENT），关键词 `Vue 3` / `Vite` / `SPA fallback` / `frontend/` 在 6 份文档中都要出现。**改代码不改文档 = 改了一半。**
> 同步点速查：[README §9](../README.md) / [HANDOFF §12](HANDOFF.md) / [AGENTS.md](../AGENTS.md) / 本节 / [DEPLOYMENT 顶部](DEPLOYMENT.md) / [DEVELOPMENT §1.8](DEVELOPMENT.md)。

> 🔒 **2026-07-20 v2.1 视觉增强 Iron Rule 扩展**：
> 改 4 个视觉组件（[AmbientBackground.vue](../frontend/src/components/AmbientBackground.vue) / [HeroScene.vue](../frontend/src/components/HeroScene.vue) / [AudioVisualizer.vue](../frontend/src/components/AudioVisualizer.vue) / [utils/visual.js](../frontend/src/utils/visual.js)）或 [vite.config.js](../frontend/vite.config.js) `manualChunks` 配置 = **同一 commit 同步更新 6 份文档**，关键词 `三层渐进增强` / `AmbientBackground` / `HeroScene` / `AudioVisualizer` / `visual.js` / `shallowRef` / `smartRAF` / `prefers-reduced-motion` 在 6 份文档中都要出现。
> 4 大集成铁律（缺任何一个都会在长时间使用或多视图切换后出问题）：① `createMediaElementSource` 一次性 — AudioVisualizer `if (!sourceNode)` 守卫；② Three.js 对象用 `shallowRef` 而非 `ref`；③ rAF 必须走 `smartRAF` 而非 `requestAnimationFrame`；④ `onBeforeUnmount` 必须完整释放 geometry / material / renderer / 监听 / ResizeObserver。详见 [HANDOFF §6.23](HANDOFF.md)。

> 🔒 **2026-07-30 v2.3.3 Safari 兼容 Iron Rule 扩展**：
> 改视觉组件的 **Safari 兼容**逻辑（[utils/visual.js](../frontend/src/utils/visual.js) `hasWebGL` 重写 / `getWebGLCaps` / `isSafari` / `isIOS` / [utils/three-helpers.js](../frontend/src/utils/three-helpers.js) `webglcontextlost` / `webglcontextrestored` / [HeroScene.vue](../frontend/src/components/HeroScene.vue) iOS 降级 Bloom 降级 + PMREM 降级 / [EmojiIcon.vue](../frontend/src/components/EmojiIcon.vue) Iconify + twemoji SVG emoji 跨浏览器一致）= **同一 commit 同步更新 6 份文档**，关键词 `Safari 兼容` / `WebGL 上下文丢失` / `webglcontextlost` / `iOS 降级` / `EmojiIcon` / `Iconify` / `twemoji` / `SVG emoji` / `跨浏览器一致` / `hasWebGL 重写` / `getWebGLCaps` / `isSafari` / `isIOS` / `Bloom 降级` / `PMREM 降级` / `v2.3.3` 在 6 份文档中都要出现。
> Safari 兼容 3 大坑（缺任何一个都会在 Safari / iOS 上出问题）：① `webglcontextlost` / `webglcontextrestored` 上下文恢复 — iOS Safari 切后台→前台触发；② `hasWebGL` 须区分 WebGL1+2 + 检测扩展 — 老 Safari 只有 WebGL1 不能误判；③ emoji 须用 SVG 统一而非系统字体 — Apple Color Emoji vs 系统 emoji 风格差异。详见 [HANDOFF §6.24](HANDOFF.md)。

### 7.8 AI 隐私边界

> AI 接入必须遵守「输出不落库、正文最小化发送」的边界。

**3 条边界**：
1. **AI 输出不写入数据库**——鼓励语 / 治愈语 / 推荐理由只在 HTTP 响应里，不写 SQLite。
2. **日记正文调用 AI 时截断到前 120 字**——漂流瓶 AI 鼓励语只发前 120 字预览，减少 token 与暴露面。
3. **API key 不入仓**——`QI_NVIDIA_API_KEY` 只在 `.env`（git 忽略），[.env.example](../.env.example) 只放注释占位。

**外部依赖边界**：
- 第三方服务：NVIDIA NIM API（`https://integrate.api.nvidia.com/v1`），会收到日记前 120 字 + 心情 emoji + 用户描述文本。
- 换自部署 vLLM / 其他厂商 → 只改 `QI_AI_BASE_URL` + `QI_AI_MODEL`（OpenAI 兼容格式）。
- 完全离线 → 不配 `QI_NVIDIA_API_KEY`，3 个端点自动降级返回治愈系提示，业务正常跑。

详见 [§6.6 AI 层架构](#66-ai-层架构2026-07-17-加可选) / [HANDOFF §5.7](HANDOFF.md)。

---

## 6.7 身心调理架构（v2.6.2）

> 设计原则：**规则可解释、结果可测试、不做医疗诊断**。问题 → 五类建议的映射写在 [app/services/therapy_service.py](../app/services/therapy_service.py)，不依赖 AI。

| 层 | 文件 | 说明 |
|---|---|---|
| 内容目录 | [therapy_service.py](../app/services/therapy_service.py) | `BADUANJIN` 8 式、`SACHETS`、`BRACELETS`、`FOODS`、`PROBLEM_RULES` |
| 推荐 | `recommend(db, problem, tags)` | 关键词/标签匹配 → 曲（按 yin 取第一首 classic）+ 2 式八段锦 + 香囊 + 手串 + 食疗 + 免责声明 |
| 打卡 | `checkin_baduanjin()` | `baduanjin_checkins` 每天唯一 + `EnergyRecord(source="baduanjin", +1)` |
| 好物 | `record_interest()` | `therapy_interests` 记录预约意向；当前不接支付/库存/发货 |
| API | [app/routers/therapy.py](../app/routers/therapy.py) | `POST /api/therapy/recommend`、`GET /catalog`、`POST /baduanjin/checkin`、`GET /baduanjin/status`、`POST /interest` |

**边界**：
- 香囊/手串/食疗只做传统养生与生活方式参考，不承诺疗效；食疗必须展示过敏原。
- 商品当前是「橱窗 + 预约/外链」，不是商城；购买赠露水等交易闭环未实现。
- 八段锦当前是跟练打卡 + Bilibili 跟练视频嵌入（16:9 iframe，`frame-src` 放行 `player.bilibili.com`）；**没有**视频上传/审核/防作弊。
- 视频仅在 `TherapyView` 的八段锦结果卡内展示，不落库；外链可跳转 B 站原视频。

---

## 8. 性能

### 8.1 首屏
- 生产入口是 `static/dist/index.html` + 分包后的 JS/CSS；Vue / GSAP / Three.js 分别走 `vue-vendor` / `gsap-vendor` / `three-vendor`。
- Three.js 组件异步加载，首屏不拉 `three-vendor`（仅 `/`、`/garden` 等场景按需加载）。
- 古琴音频用 `preload="metadata"`，不预加载整个文件。
- 静态资源 gzip 由 Nginx 负责。

### 8.2 数据库
- SQLite 单文件，< 1000 用户完全无压力。
- 写日记 / 能量 / 打卡 都是简单 INSERT，索引足够。
- 心情查询按 `user_id + check_date` 走索引；`energy_records` 有 `(user_id, music_id, created_at)` 用于 24h 去重。

### 8.3 加密
- 密码：bcrypt（登录时一次）。
- 日记：**明文存储**，没有客户端加密开销；隐私边界见 §7.3。
- 会话：itsdangerous 签名 cookie，无服务端 session 存储。

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
3. `app/routers/meditation.py` + 在 [app/main.py](../app/main.py) 注册
4. `app/services/meditation_service.py` 业务逻辑
5. `frontend/src/views/meditation/MeditationView.vue` + [router/index.js](../frontend/src/router/index.js) 加路由
6. `app/seed.py` 加种子数据（如需）
7. 重启 → `init_db()` 自动建表；前端 `npm run build`

### 9.3 加一个后台页面 / API
1. 后台 API：[app/routers/admin.py](../app/routers/admin.py) 加 `@router.get/post/...`，Pydantic in [app/schemas/admin.py](../app/schemas/admin.py)
2. 后台页面：[app/routers/admin_pages.py](../app/routers/admin_pages.py) 加 `@router.get(...)` + `admin_templates.TemplateResponse(request, "admin/your.html", {...})`
3. 鉴权统一 `Depends(get_current_admin)`（API）/ `get_current_admin_or_redirect`（页面）
4. 模板放 `templates/admin/your.html`，继承 `admin/_base.html`
5. 表格 / 模态样式直接用 [static/css/07-admin.css](../static/css/07-admin.css) 的 `.admin-*` 类
6. JS 放 `static/js/pages/admin_xxx.js`，模板底部 `<script defer src="/static/js/pages/admin_xxx.js"></script>`

### 9.4 加一个新字段到旧库（轻量迁移，不引 Alembic）
1. [app/models/xxx.py](../app/models/) 加 `Mapped[...] = mapped_column(...)`
2. [app/database.py](../app/database.py) 的 `_migrate_legacy_columns()` 加一段：
   ```python
   cols = {c["name"] for c in insp.get_columns("xxx")}
   if "new_field" not in cols:
       conn.execute(text("ALTER TABLE xxx ADD COLUMN new_field ... DEFAULT ..."))
   ```
3. 重启即可（已存在的老库自动加列）

⚠️ 这套方案只支持**加列 / 加默认值**。改列类型 / 删列 / 加索引需要显式重建表（参考 `mood_checkins` 的迁移写法），项目刻意不引 Alembic。

### 9.5 真实音频
1. 音频槽位是 `static/audio/tracks/{曲名}.mp3`（22 首，与 `musics.title` 一一对应）。
2. 放真实音频：同名覆盖即可，无需改代码；`seed.py` 启动时会按真实 MP3 校准 `duration`。
3. 新增曲目：改 [app/seed.py](../app/seed.py) 的 `SEED_MUSIC` → 重启（自动补行 + 生成占位）→ 放音频。
4. 当前状态：16 首古琴曲已有真实音频；6 首西洋改编是 5338 字节静音占位，需补文件。

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
- ❌ 禁止：通过后台 API 读日记正文（接口未提供）、导出全库
- ⚠️ 日记是明文存储，数据库文件本身可读；「后台不读」不等于「加密保护」。

这些边界是项目精神的一部分，不要突破。
