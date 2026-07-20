# 开发约定 + 踩坑清单

> 改代码前**必读**。这里汇总了 9 个真实踩过的坑 + 7 条开发铁律。

> 🔒 **2026-07-19 v2.0.1 端口策略调整 + Three.js 花田**：开发模式从 Vite :5173 + FastAPI :5000 改为 **Vite :5000 + FastAPI :5001**（用户始终访问 :5000）；新增 [FlowerField.vue](../../frontend/src/components/FlowerField.vue) 3D 花田组件作为 `defineAsyncComponent` 异步加载示例。关键词 `5001` / `FlowerField` / `Vite :5000` 在 6 份文档（README / HANDOFF / PROJECT_STATE / ARCHITECTURE / DEPLOYMENT / DEVELOPMENT）中都要出现。详见 [§1.9.1 启动开发模式](#191-启动开发模式vite-dev-server-5000--fastapi-50012026-07-19-v201-改) / [§1.9.5 加新视图](#195-加新视图vue-3-spa-模式替代旧-21-jinja2-模式) / [§1.9.7 调试技巧](#197-调试技巧)。

> 🔒 **2026-07-20 v2.1 视觉增强**：新增 4 个视觉组件（[AmbientBackground.vue](../../frontend/src/components/AmbientBackground.vue) / [HeroScene.vue](../../frontend/src/components/HeroScene.vue) / [AudioVisualizer.vue](../../frontend/src/components/AudioVisualizer.vue) + [utils/visual.js](../../frontend/src/utils/visual.js)），三层渐进增强策略（CSS 永远启用 → Canvas2D 中量级 → Three.js 按需）。**新建视觉组件必须遵守 4 大铁律**（详见 [§1.9.8 视觉组件开发指南](#198-视觉组件开发指南v21-加2026-07-20)）：① `createMediaElementSource` 一次性守卫；② Three.js 对象用 `shallowRef` 而非 `ref`；③ rAF 必须走 `smartRAF` 而非 `requestAnimationFrame`；④ `onBeforeUnmount` 必须完整释放。关键词 `三层渐进增强` / `AmbientBackground` / `HeroScene` / `AudioVisualizer` / `visual.js` / `shallowRef` / `smartRAF` 在 6 份文档中都要出现。

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

## 1.9 前端开发模式（Vue 3 SPA，2026-07-19 v2.0 加，v2.0.1 端口策略调整）

> 2026-07-19 v2.0 全站 Vue 3 重构后，前台 13 个页面迁移到 Vue 3 SPA。本节讲**怎么开发前端**，不是讲铁律。架构看 [ARCHITECTURE §1.1](../ARCHITECTURE.md)，部署看 [DEPLOYMENT 前端构建](../DEPLOYMENT.md)。

> 2026-07-19 v2.0.1 端口策略调整：开发模式 Vite 占 :5000（用户入口）+ FastAPI 退到 :5001（API），**用户始终访问 :5000**。理由见 [HANDOFF §6.16](../../HANDOFF.md)（FastAPI 反代 Vite 内部路径含 null 字节转义 + 冒号失败）。

### 1.9.1 启动开发模式（Vite dev server :5000 + FastAPI :5001，2026-07-19 v2.0.1 改）

#### 方式 A：一键启动（推荐 ⭐）

```bash
cd c:\Users\Administrator\Desktop\webwrold
python start.py                # 自动检测 dist 是否构建：
                               #   未构建 → 起 Vite :5000 + FastAPI :5001（dev 模式）
                               #   已构建 → 起 FastAPI :5000（prod 模式）
```

[start.py](../../start.py) 在 dev 模式会：
1. 后台启动 Vite dev server（监听 :5000）
2. 设置环境变量 `QI_PORT=5001` 启动 FastAPI（监听 :5001）
3. `python start.py status` 同时显示两个进程状态

#### 方式 B：手动两终端

```bash
# 终端 1：启动 Vite dev server（占 :5000，用户入口）
cd c:\Users\Administrator\Desktop\webwrold\frontend
npm install                    # 首次：含 three.js 大包，约 7 分钟
npm run dev                    # http://127.0.0.1:5000

# 终端 2：启动 FastAPI（退到 :5001，API 后端）
cd c:\Users\Administrator\Desktop\webwrold
set QI_PORT=5001
python start.py                # http://127.0.0.1:5001
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

### 1.9.2 开发模式 vs 生产模式

| 维度 | 开发模式（dev，v2.0.1） | 生产模式（prod） |
|---|---|---|
| 启动命令 | `python start.py`（自动检测 dist） | `python start.py build` + `python start.py` |
| 浏览器访问 | `http://127.0.0.1:5000/`（**始终**） | `http://127.0.0.1:5000/`（**始终**） |
| 谁服务 :5000 | Vite dev server（HMR + 源码） | FastAPI（服务 `static/dist/index.html` + SPA fallback） |
| FastAPI 监听 | :5001（由 start.py 设 QI_PORT=5001） | :5000（从 .env 读 QI_PORT） |
| Vite 是否运行 | ✅ 是 | ❌ 否（dist 已构建，不需要 Vite） |
| 改 .vue 后 | 浏览器自动热更新 | 必须重新 `python start.py build` 或 `npm run build` |
| 适用场景 | 日常开发 | 部署上线 / 真机测试 |

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
    │   └── FlowerField.vue   ← 3D 花田场景（Three.js + InstancedMesh，v2.0.1 加）
    ├── views/                ← 【一个视图一个 .vue 文件】
    │   ├── HomeView.vue
    │   ├── NotFoundView.vue
    │   ├── auth/
    │   │   ├── LoginView.vue
    │   │   └── RegisterView.vue
    │   ├── music/
    │   │   ├── MusicListView.vue
    │   │   └── MusicDetailView.vue
    │   ├── diary/
    │   │   ├── DiaryListView.vue
    │   │   ├── DiaryWriteView.vue
    │   │   └── PickBottleView.vue
    │   ├── mood/
    │   │   └── MoodCalendarView.vue
    │   ├── ai/
    │   │   └── AIChatView.vue
    │   └── garden/
    │       ├── GardenView.vue
    │       └── ShopView.vue
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

> **start.py 子命令对照**：`python start.py`（dev/prod 自动切换）/ `python start.py build`（构建前端）/ `python start.py fg`（前台）/ `python start.py status`（查 Vite + FastAPI 双进程状态）/ `python start.py stop`（停双进程）/ `python start.py restart`。

### 1.9.7 调试技巧

- **Vue DevTools**：浏览器装 [Vue.js devtools](https://devtools.vuejs.org/) 扩展，看组件树 / Pinia state / Router
- **Vite 启动慢 / HMR 不生效**：检查 [frontend/vite.config.js](../../frontend/vite.config.js) 的 `host: '127.0.0.1'`（不要写 `localhost`，IPv6 `[::1]` 会连不上，详见 [HANDOFF §6.12](../../HANDOFF.md)）
- **API 401 不跳登录**：检查 [frontend/src/api/index.js](../../frontend/src/api/index.js) 的 axios 拦截器
- **404 不显示**：检查 `router/index.js` 末尾的 `/:pathMatch(.*)*` catch-all 路由
- **dist 未构建提示页**：访问 :5000 看到「dist 未构建」→ `python start.py build` 或 `cd frontend && npm run build`
- **dev 模式 :5000 是 Vite，不是 FastAPI**（v2.0.1 加）：开发模式访问 :5000 是 Vite dev server（HMR + 源码），API 请求经 Vite proxy 转发到 :5001 的 FastAPI。要看 FastAPI Swagger 文档直接访问 :5001（`http://127.0.0.1:5001/docs`）。**生产模式 :5000 才是 FastAPI**。详见 [§1.9.1](#191-启动开发模式vite-dev-server-5000--fastapi-50012026-07-19-v201-改)。
- **端口 5000 被占用**：`python start.py stop` 停掉旧进程；或检查是否同时跑了 Vite 和 FastAPI（v2.0.1 dev 模式 Vite 占 :5000，如果 FastAPI 没改成 :5001 就会撞）。Vite `strictPort: true` 会直接报错不自动跳端口。
- **3D 花田不显示**：访问 `/garden` 看到「🌿 花田正在生长…」一直转 → 打开 DevTools Console 看是不是 `Failed to fetch dynamically imported module`（three-vendor chunk 没加载到，检查 `static/dist/assets/three-vendor-*.js` 是否存在 → 不存在重新 `npm run build`）
- **proxy 没生效**：检查 [vite.config.js](../../frontend/vite.config.js) 的 `server.proxy` 是否包含 `/api`、`/static`、`/admin`、`/docs`、`/openapi.json`（v2.0.1 起多了 `/docs` 和 `/openapi.json`，方便开发时直接在 :5000 访问 Swagger）

### 1.9.8 视觉组件开发指南（v2.1 加，2026-07-20）

> 适用范围：所有用 Three.js / Canvas2D / Web Audio API 的视觉组件。当前已有 4 个：[FlowerField.vue](../../frontend/src/components/FlowerField.vue) / [AmbientBackground.vue](../../frontend/src/components/AmbientBackground.vue) / [HeroScene.vue](../../frontend/src/components/HeroScene.vue) / [AudioVisualizer.vue](../../frontend/src/components/AudioVisualizer.vue)。

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
4. **性能保护**：移动端粒子数减半 + `dpr` ≤ 1.5；`defineAsyncComponent` 异步加载 Three.js
5. **降级路径**：每个 Three.js 组件必须有 CSS / SVG 静态降级；reduced-motion 用户不能看到闪烁 / 摇晃内容
6. **验证清单**：
   - 桌面 Chrome 默认 motion：3D / Canvas2D 正常渲染
   - DevTools → Rendering → `prefers-reduced-motion: reduce`：降级为静态
   - 移动端 Safari：粒子数减半、dpr ≤ 1.5
   - 切走标签页 30s 后回切：GPU 占用应归零（smartRAF 生效）
   - 在该组件所在视图和其他 Three.js 视图间来回切 5 次：无 `Too many active WebGL contexts` 警告
7. **文档同步**：新增视觉组件 = **同一 commit 同步更新 6 份文档**（详见 [HANDOFF §12](../../HANDOFF.md)）

#### 视觉能力检测 API（[utils/visual.js](../../frontend/src/utils/visual.js)）

| 函数 | 返回 | 说明 |
|---|---|---|
| `hasWebGL()` | boolean | 当前浏览器是否支持 WebGL（含 2 / 1 fallback 测试） |
| `prefersReducedMotion()` | boolean | 用户是否设置 `prefers-reduced-motion: reduce` |
| `isMobile()` | boolean | 视口宽度 < 768px 或 UA 含 Mobile |
| `isLowPower()` | boolean | `navigator.hardwareConcurrency` ≤ 4 或 `deviceMemory` ≤ 4 |
| `shouldUseThreeJS()` | boolean | `hasWebGL && !prefersReducedMotion && !isLowPower` |
| `shouldUseCanvas()` | boolean | `!prefersReducedMotion` |
| `smartRAF(callback)` | number | `requestAnimationFrame` 包装，`document.hidden` 时 `cancelAnimationFrame`，可见时自动恢复 |

所有函数**单次缓存**结果（同一会话内重复调用直接返回缓存值），不会重复检测拖累性能。

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
