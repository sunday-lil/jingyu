# 架构 — 静屿

> 本文件讲**为什么**这样设计，不是讲**做了什么**。想知道做了什么看 [README.md](../../README.md)。

> 🔒 **改了本文件涉及的代码，必须同步更新 [HANDOFF §12](../../HANDOFF.md) / [PROJECT_STATE §8](../PROJECT_STATE.md) / [DEVELOPMENT §1.8](DEVELOPMENT.md) 列出的对应文档。** 改代码不改文档 = 改了一半。

> 🔒 **2026-07-19 v2.0.1 端口策略 + Three.js 花田更新**：① §1 架构图改为 Vite :5000 / FastAPI :5001（开发）+ FastAPI :5000（生产）；② §1.1 前端架构加 `FlowerField.vue` 3D 花田组件说明；③ §1.2 开发/生产模式切换的端口策略更新（Vite 占 :5000，FastAPI 改 :5001）。关键词 `Vue 3` / `Vite` / `SPA fallback` / `frontend/` / `FlowerField` / `5001` 在 6 份文档（README / HANDOFF / PROJECT_STATE / ARCHITECTURE / DEPLOYMENT / DEVELOPMENT）中都要出现。

> 🔒 **2026-07-20 v2.1 视觉增强更新**：① §1.1 加 §1.1.6 视觉增强组件群（AmbientBackground / HeroScene / AudioVisualizer + utils/visual.js）；② §7.7 末尾的 Iron Rule 提醒扩展关键词，包含 `三层渐进增强` / `shallowRef` / `smartRAF` / `prefers-reduced-motion`。关键词 `三层渐进增强` / `AmbientBackground` / `HeroScene` / `AudioVisualizer` / `visual.js` / `shallowRef` / `smartRAF` 在 6 份文档中都要出现。

> 🔒 **2026-07-20 v2.2 3D 元素与动效全面重构**：① 4 个视觉组件全部升级到 PBR 渲染管线（ACESFilmicToneMapping + SRGBColorSpace + PCFSoftShadowMap + RoomEnvironment PMREM + UnrealBloomPass）；② 新增 [utils/three-helpers.js](../../frontend/src/utils/three-helpers.js) 集中导出 9 个共享 PBR 工具函数；③ 新增 [SceneHint.vue](../../frontend/src/components/SceneHint.vue) 交互指引横幅 + [SceneControls.vue](../../frontend/src/components/SceneControls.vue) 视图控制工具栏，解决「用户不知道如何与 3D 元素交互」问题；④ HeroScene 改用 `LatheGeometry` 旋转曲面浮岛 + 递归樱花树 + 水面 `onBeforeCompile` 顶点位移 shader；FlowerField 改用自定义 `BufferGeometry` 立体花瓣 + `MeshPhysicalMaterial`；AudioVisualizer 升级 4 模式 + 节拍检测；AmbientBackground 升级 Canvas2D 柔光 sprite + 滚动视差；⑤ 所有 3D 场景统一 `OrbitControls`（拖拽旋转 + 滚轮缩放）+ `raycaster` 点击拾取。关键词 `PBR` / `three-helpers` / `SceneHint` / `SceneControls` / `OrbitControls` / `raycaster` / `UnrealBloomPass` / `RoomEnvironment` / `LatheGeometry` 在 6 份文档中都要出现。

> 🔒 **2026-07-20 v2.2.1 start.py 自动构建**：`python start.py` 默认行为变更——dist 未构建时不再走开发模式（Vite 占 :5000），而是自动 `npm install + npm run build` 后走生产模式（**:5000 永远是 FastAPI**）。新增 `--dev` 参数显式走开发模式。§1.2 开发/生产模式切换的端口策略不变，但触发条件改为：dist 未构建 + 非 `--dev` → 自动构建后生产模式（而非开发模式）。关键词 `--dev` / `自动构建` / `:5000 永远是 FastAPI` 在 6 份文档中都要出现。

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

**v2.2 视觉文件群**（共 7 个）：

| 文件 | 角色 | 嵌入位置 | 降级路径 |
|---|---|---|---|
| [frontend/src/utils/visual.js](../../frontend/src/utils/visual.js) | 视觉能力检测 | 被其他组件 import | 单次缓存检测结果，无降级（自身就是降级判断器） |
| [frontend/src/utils/three-helpers.js](../../frontend/src/utils/three-helpers.js) | **PBR 工具集（v2.2 加）** | 被 HeroScene / FlowerField / AmbientBackground import | 9 个共享函数：createRenderer / createEnvironment / createPostProcessing / createOrbitControls / createKeyLight / createFillLight / createSoftSpriteTexture / disposeObject3D / disposeRenderer |
| [frontend/src/components/AmbientBackground.vue](../../frontend/src/components/AmbientBackground.vue) | 全局氛围背景 v2 | [AppLayout.vue](../../frontend/src/components/AppLayout.vue) 根（所有页面可见） | CSS 永远启用 → Canvas2D 柔光 sprite（reduced-motion 关闭）→ Three.js 双层粒子 + 轻量 Bloom（WebGL + 非低性能） |
| [frontend/src/components/HeroScene.vue](../../frontend/src/components/HeroScene.vue) | 首页 3D 浮岛雾海 v2 | [HomeView.vue](../../frontend/src/views/HomeView.vue) 顶部 | 无 WebGL / reduced-motion / initScene 异常 → SVG 静态插画（800×480 viewBox：天空渐变 + 太阳 + 3 岛 + 3 层波浪 + 5 漂浮点） |
| [frontend/src/components/FlowerField.vue](../../frontend/src/components/FlowerField.vue) | 3D 花田 v2 | [GardenView.vue](../../frontend/src/views/garden/GardenView.vue) 顶部 | 无 WebGL / reduced-motion / initScene 异常 → CSS 渐变背景 + 提示文案 |
| [frontend/src/components/AudioVisualizer.vue](../../frontend/src/components/AudioVisualizer.vue) | 音波可视化 v2 | [MusicDetailView.vue](../../frontend/src/views/music/MusicDetailView.vue) 详情头之后 | 无 Web Audio / reduced-motion → CSS 5 色横条静态动画 |
| [frontend/src/components/SceneHint.vue](../../frontend/src/components/SceneHint.vue) | **3D 场景交互指引（v2.2 加）** | 被 HeroScene / FlowerField 引用 | `pointer-events: none` 不阻挡 3D 交互；3 秒后自动淡出 |
| [frontend/src/components/SceneControls.vue](../../frontend/src/components/SceneControls.vue) | **3D 场景视图控制（v2.2 加）** | 被 HeroScene / FlowerField 引用 | emit 事件由父组件处理；玻璃拟态样式 + 8px 圆角 |

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
| 移动端降级 | 粒子数减半 + `dpr` ≤ 1.5 + Bloom strength 0.3 → 0.18 | 移动端 GPU/CPU 弱，全量粒子 + 强 Bloom 会掉帧 |
| 配色一致性 | 4 个组件全部用治愈系 5 色（藕粉 `#E8B8C5` / 淡黄 `#E8D5A8` / 青绿 `#A8C5A0` / 雾蓝 `#A8B8C5` / 纯白 `#FAF6F2`）+ 米白 `#F9F6F0` 背景 | 与 [tailwind.config.js](../../frontend/tailwind.config.js) token 一致；AudioVisualizer 4 模式频响颜色低频暖色 → 高频冷色 |
| Web Audio 一次性约束 | `audioCtx.createMediaElementSource(audioEl)` 对同一 `<audio>` 元素只能调一次 | AudioVisualizer `if (!sourceNode)` 守卫 + MusicDetailView `visualizerConnected` ref 标记首次 `playIndex` 时连接（详见 [HANDOFF §6.23.1](../../HANDOFF.md)） |

**为什么 v2.2 引入 PBR + Bloom 后处理**（推翻 v2.1 决策）：
- v2.1 决策「不用全屏 shader / 后处理」基于「治愈系要柔和不刺眼」，但实际效果过于平淡，被用户评价为「粗糙过时，类似 80/90 年代红白机」
- v2.2 调整：Bloom strength 0.3（移动端 0.18）保持克制，只让发光物体（花瓣 / 樱花 / 光点）有柔光晕，**不**做全屏泛光；ACESFilmic 色调映射让暗部有细节不死黑，高光不爆白
- 性能保护：移动端 Bloom strength 降到 0.18 + 粒子数减半 + dpr ≤ 1.5；reduced-motion 直接降级为 SVG 静态插画，不走 Bloom 路径

**降级验证矩阵**：

| 环境 | AmbientBackground | HeroScene | FlowerField | AudioVisualizer |
|---|---|---|---|---|
| 桌面 Chrome（WebGL + 默认 motion） | CSS + Canvas2D 柔光 sprite + Three.js 双层粒子 + Bloom | 3D 浮岛雾海 + 樱花树 + PBR 水面 + Bloom + OrbitControls | 3D 立体花瓣 + MeshPhysicalMaterial + Bloom + OrbitControls + raycaster | Web Audio + Canvas2D 4 模式 + 节拍检测 |
| 桌面 Chrome + `prefers-reduced-motion` | 仅 CSS 雾气光斑 | SVG 静态插画 | CSS 渐变背景 + 提示文案 | CSS 5 色横条静态 |
| 移动端 Safari（WebGL + 默认 motion） | CSS + Canvas2D（粒子减半）+ Three.js 双层粒子（dpr≤1.5）+ Bloom strength 0.18 | 3D 浮岛雾海（粒子减半 + dpr≤1.5 + Bloom 0.18） | 3D 立体花瓣（粒子减半 + dpr≤1.5） | Web Audio + Canvas2D 4 模式 |
| 旧浏览器（无 WebGL） | CSS + Canvas2D 光点 | SVG 静态插画 | CSS 渐变背景 + 提示文案 | CSS 5 色横条 |
| `import('three')` 失败 | CSS + Canvas2D 光点 | SVG 静态插画 | CSS 渐变背景 + 提示文案 | 不受影响（不用 Three.js） |

详见 [frontend/src/components/AmbientBackground.vue](../../frontend/src/components/AmbientBackground.vue) + [HeroScene.vue](../../frontend/src/components/HeroScene.vue) + [AudioVisualizer.vue](../../frontend/src/components/AudioVisualizer.vue) + [FlowerField.vue](../../frontend/src/components/FlowerField.vue) + [SceneHint.vue](../../frontend/src/components/SceneHint.vue) + [SceneControls.vue](../../frontend/src/components/SceneControls.vue) + [utils/visual.js](../../frontend/src/utils/visual.js) + [utils/three-helpers.js](../../frontend/src/utils/three-helpers.js)，决策理由详见 [HANDOFF §5.10](../../HANDOFF.md) + [HANDOFF §5.11](../../HANDOFF.md)，4 大坑详见 [HANDOFF §6.23](../../HANDOFF.md)。

---

## 1.2 开发/生产模式切换（2026-07-19 v2.0 加，v2.0.1 端口策略调整）

> **2026-07-19 v2.0.1 端口策略调整**：开发模式从「Vite :5173 + FastAPI :5000」改为「**Vite :5000 + FastAPI :5001**」——用户**始终**访问 :5000，由 [start.py](../../start.py) 自动检测 dist 是否构建来切换端口策略。理由：原方案让 FastAPI :5000 反代 Vite :5173，但 Vite 内部路径 `/@id/__x00__plugin-vue:export-helper` 含 null 字节转义 + 冒号，httpx 转发时被破坏，浏览器报 `SyntaxError: Unexpected token '.'`（详见 [HANDOFF §6.16](../../HANDOFF.md)）。

### 1.2.1 开发模式（Vite dev server :5000 + FastAPI :5001）

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

- **推荐**：`python start.py`（自动起 Vite :5000 + FastAPI :5001 双进程，dev 模式由 `is_dist_built()` 检测自动切换）
- **备选**（手动两终端）：
  - 终端 1：`cd frontend && npm install && npm run dev`（Vite 监听 :5000）
  - 终端 2：`set QI_PORT=5001 && python start.py`（FastAPI 监听 :5001）
- 浏览器访问 **:5000**（即 Vite），前端调 API 走 proxy 无跨域
- start.py 在 dev 模式会设置环境变量 `QI_PORT=5001` 让 FastAPI 改听 5001（默认是 5000）
- Vite host 显式设 `127.0.0.1`（不写 `localhost`，避免 IPv6 `[::1]` 问题，详见 [HANDOFF §6.12](../../HANDOFF.md)）
- Vite `strictPort: true` 防止 5000 被占用时自动跳到 5001（会和 FastAPI 撞）

### 1.2.2 生产模式（FastAPI :5000 + SPA fallback，Vite 不运行）

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

- **推荐**：`python start.py build`（一键构建前端到 `static/dist/`）+ `python start.py`（启动 FastAPI）
- 备选：`cd frontend && npm run build` 输出到 `static/dist/`，然后 `python start.py`
- 浏览器访问 **:5000**（这次是 FastAPI），FastAPI 兜底返回 `index.html`，Vue Router 接管客户端路由
- dist 未构建时（仍走生产模式）返回治愈系提示页，引导用户访问 Vite dev server :5000 或运行 `python start.py build`

### 1.2.3 端口策略对照表

| 模式 | 用户访问 | Vite | FastAPI | 启动方式 |
|---|---|---|---|---|
| 开发（dist 未构建） | :5000 | :5000（用户入口 + HMR） | :5001（API） | `python start.py` |
| 生产（dist 已构建） | :5000 | 不运行 | :5000（API + SPA + 静态） | `python start.py`（自动检测 dist） |

**为什么 dev 让 Vite 占 :5000 而不是 FastAPI**：见 [HANDOFF §5.9](../../HANDOFF.md)（决策）/ [HANDOFF §6.16](../../HANDOFF.md)（踩坑）。核心：让 FastAPI 反代 Vite 内部路径会失败，所以让 Vite 直接占住用户入口，FastAPI 退到 :5001 专做 API。

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
| `mood_checkins.check_date` | date | 当天日期（unique + user_id） |
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
