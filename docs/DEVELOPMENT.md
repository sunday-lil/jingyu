# 开发约定 + 踩坑清单

> 改代码前**必读**。这里汇总了当前仍然有效的开发铁律 + 踩坑复现与修法；逐版本历史见 [CHANGELOG.md](CHANGELOG.md)。

> **当前版本：v2.6.0（2026-10-18）**。逐版本变更见 [CHANGELOG.md](CHANGELOG.md)；本文只保留仍然有效的开发约定与踩坑。

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
- 改文案前先在 [README](../README.md) 找调性
- toast 提示放在对应 Vue 视图内，保持柔和措辞

### 1.3 配色字体
- 前台颜色 token → [frontend/tailwind.config.js](../frontend/tailwind.config.js)；全局 CSS 变量 / 通用类 → [frontend/src/assets/styles/main.css](../frontend/src/assets/styles/main.css)
- 后台颜色 → [static/css/07-admin.css](../static/css/07-admin.css)（与前台隔离）
- **不要**在组件里写死颜色
- 主色调：`#F9F6F0` 米白 / `#E3F0EA` 淡青 / `#F0E3E8` 藕粉
### 1.4 前端框架选型（2026-07-19 v2.0 重构后）

> **2026-07-19 v2.0 全站 Vue 3 重构后**：前台页面已迁移到 Vue 3 SPA（当前 17 个 `.vue` 视图），**不再**使用原生 HTML/CSS/JS。后台 `/admin/*` 仍保留 Jinja2 SSR（有意为之的独立隔离）。

**前台 Vue 3 SPA**（[`frontend/src/`](../frontend/src/)）：
- ✅ Vue 3 `<script setup>` + Vite 5 + Vue Router 4 + Pinia + Tailwind CSS 3.4 + GSAP + @vueuse/motion + Three.js + axios
- ❌ 不要再引入 React / Angular / Svelte（已选定 Vue 3，不再讨论）
- ❌ 不要在 Vue SPA 之外另起前端框架（后台 Jinja2 SSR 是有意为之的独立隔离）

**后台 Jinja2 SSR**（[`templates/admin/`](../templates/admin/)）：
- ✅ 原生 HTML + CSS + JS（继承 `admin/_base.html`）
- ❌ 不引 React / Vue / Tailwind / Vite / webpack
- 加第三方库前先问：「不用它能写吗？」

> 详见 [§1.9 前端开发模式](#19-前端开发模式vue-3-spa2026-07-19-v20-加) / [HANDOFF §5.8](HANDOFF.md) 前端选型决策。

### 1.5 隐私边界
- 日记当前是**明文存储**；不要把「后台看不到正文」误当成「加密」。
- 日志 / 错误信息里**不要**出现用户日记正文、密码、cookie、API key。
- 错误处理**不**返回用户输入的原始内容。
- 调试 API 时**不**用真用户数据。

### 1.6 单日上限
- 所有「+x 能量」操作前先查当天累计
- 上限在 [app/utils/constants.py](../app/utils/constants.py) `DAILY_LIMITS` 里
- 改上限要同步更新文档

### 1.7 改完必须自测（未自测 = 未完成）

**任何代码改动，commit 前必须自测通过；自测不通过不得 commit。** 完整标准见 [AGENTS.md](../AGENTS.md)。

| 改动范围 | 最低验证 |
|---|---|
| 后端 API / service / model | `python start.py restart` 无报错 → 请求受影响接口 → `logs/healing.log` 无 ERROR → 字段变更确认老库迁移生效 |
| 前端 Vue / 路由 / 样式 | `cd frontend && npm run build` 通过 → 生产模式启动 → 浏览器验证页面功能 + console 无报错 |
| 前后端联动 | 至少走通一次完整用户动作（登录 → 操作 → 数据落库/刷新后仍在） |
| 仅文档 | 检查 Markdown 链接与命令可执行，无需启动服务 |

```bash
python start.py restart
python start.py status
curl -I http://127.0.0.1:5000/                       # 200
curl -I http://127.0.0.1:5000/api/<affected>         # 2xx / 预期 4xx

# 前端改动额外执行
cd frontend && npm run build

# 临时验证完记得停掉，不要留后台进程
python start.py stop
```

> 修 Bug 必须复验「原复现步骤不再复现」；UI 改动必须重新构建 `static/dist/`，否则生产入口仍是旧代码。

### 1.8 改完代码**必须**同步更新文档（自动同步铁律）
> 🔒 **本节优先级最高。** 完整版见 [HANDOFF §12](HANDOFF.md) / [AGENTS.md](../AGENTS.md)。

**铁律**：**改代码 + 改文档 = 同一个 commit。** 不允许「代码先上，文档周末补」。

**自检 5 件事**（详见 [HANDOFF §12.4](HANDOFF.md)）：
1. Pydantic Out schema 是否补了新字段（→ §3.10）
2. `_migrate_legacy_columns()` 是否补了老库列（→ §3.x / [HANDOFF §6.10](HANDOFF.md)）
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
> 改 Vue 3 前端代码（[`frontend/src/`](../frontend/src/)）+ 后端 SPA fallback（[app/main.py](../app/main.py)）= **同一 commit 同步更新 6 份文档**（README / HANDOFF / PROJECT_STATE / ARCHITECTURE / DEPLOYMENT / DEVELOPMENT）。关键词 `Vue 3` / `Vite` / `SPA fallback` / `frontend/` 在 6 份文档中都要出现。**改代码不改文档 = 改了一半。**
> 同步点速查：[README §9](../README.md) / [HANDOFF §12](HANDOFF.md) / [AGENTS.md](../AGENTS.md) / [ARCHITECTURE §7.7](ARCHITECTURE.md) / [DEPLOYMENT 顶部](DEPLOYMENT.md) / 本节。
> 完整规则 + 5 项 pre-commit checklist：[HANDOFF §12](HANDOFF.md) / [AGENTS.md](../AGENTS.md)。

#### 1.8.1 改完自动 push（不延迟，使用 gh）
- 推送前 `gh auth status` 必须通过；token 失效先 `gh auth refresh -h github.com`（或 `gh auth login`），再 `gh auth setup-git`
- `git commit` 完**立即** `git push origin main`
- 不允许「先 commit 一会儿一起推」/「明天推」/「攒一周推一次」
- 推送后验证 `git status --short` 为空，且远端 `main` 的 SHA == 本地 `HEAD`
- 完整规则：[HANDOFF §12.6](HANDOFF.md) / [AGENTS.md](../AGENTS.md)

#### 1.8.2 Commit 标题 / 脚本进度用 Conventional Commits
- 格式：`<type>(<scope>): <subject>`（subject ≤ 50 字符）
- type 9 个：`feat` / `fix` / `refactor` / `docs` / `style` / `test` / `chore` / `perf` / `revert`
- 项目 scope：`auth` / `diary` / `mood` / `music` / `energy` / `garden` / `admin` / `templates` / `static` / `docs` / `deps` / `scripts` …
- v2.0 起新增 scope：`frontend` / `vue` / `vite` / `tailwind` / `gsap`（[`frontend/`](../frontend/) 相关改动用）
- 脚本（`push-to-github.ps1`）的进度输出**也**用 `type(scope)` 标题
- 完整规则 + 示例：[HANDOFF §12.7](HANDOFF.md)

---

## 1.9 前端开发模式（Vue 3 SPA，2026-07-19 v2.0 加，v2.0.1 端口策略调整，v2.3.2 默认生产模式）

> 2026-07-19 v2.0 全站 Vue 3 重构后，前台迁移到 Vue 3 SPA（当前 17 个视图）。本节讲**怎么开发前端**，不是讲铁律。架构看 [ARCHITECTURE §1.1](ARCHITECTURE.md)，部署看 [DEPLOYMENT 前端构建](DEPLOYMENT.md)。

> 2026-07-19 v2.0.1 端口策略调整：开发模式 Vite 占 :5000（用户入口）+ FastAPI 退到 :5001（API），**用户始终访问 :5000**。理由见 [HANDOFF §6.16](HANDOFF.md)（FastAPI 反代 Vite 内部路径含 null 字节转义 + 冒号失败）。

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

[start.py](../start.py) 在 dev 模式会：
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

> ⚠️ Vite host 显式设 `127.0.0.1`（不写 `localhost`）避免 IPv6 `[::1]` 问题，详见 [HANDOFF §6.12](HANDOFF.md) / [§3.15](#315-vite-ipv6-localhost-连不上)。
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

### 1.9.3 dev proxy 配置（[frontend/vite.config.js](../frontend/vite.config.js)）

Vite dev server 把以下路径 proxy 到 FastAPI :5001，**无跨域**：

| 前端请求路径 | proxy 到 | 用途 |
|---|---|---|
| `/api/*` | `http://127.0.0.1:5001/api/*` | 所有 JSON API（axios `baseURL=/api`） |
| `/static/*` | `http://127.0.0.1:5001/static/*` | 静态资源（音频、图片、旧 CSS/JS） |
| `/admin/*` | `http://127.0.0.1:5001/admin/*` | 秘密后台 SSR（Jinja2） |
| `/docs` | `http://127.0.0.1:5001/docs` | FastAPI Swagger UI（开发调试用） |
| `/openapi.json` | `http://127.0.0.1:5001/openapi.json` | FastAPI OpenAPI schema（Swagger 依赖） |

> axios 实例（[frontend/src/api/index.js](../frontend/src/api/index.js)）配置 `baseURL='/api'` + `withCredentials=true`，cookie 自动带，401 自动跳 `/login`。

> **dev proxy 不要改**：5 项配置（`/api` / `/static` / `/admin` / `/docs` / `/openapi.json` + host=127.0.0.1）是项目最稳定的部分之一。改了必然破东西。

### 1.9.4 文件结构（[`frontend/src/`](../frontend/src/)）

```
frontend/
├── package.json / vite.config.js / tailwind.config.js / postcss.config.js / index.html
└── src/
    ├── main.js               ← createApp + Pinia + Router + MotionPlugin
    ├── App.vue               ← AppLayout + router-view + transition
    ├── router/index.js       ← 16 条业务路由 + 404 + requiresAuth 守卫
    ├── stores/user.js        ← Pinia user store（cookie session，不存 token）
    ├── api/index.js          ← axios 实例（baseURL=/api，withCredentials，401 拦截，已解包 response.data）
    ├── data/islandGuide.js   ← 首页指南 / 模块奖励 / 个人主页指南共享文案
    ├── components/           ← AppLayout / FlowerField / AmbientBackground / HeroScene /
    │                            AudioVisualizer / SceneHint / SceneControls / EmojiIcon
    ├── utils/                ← visual.js（能力检测 + smartRAF）/ three-helpers.js（PBR 工具集）
    ├── assets/styles/main.css
    └── views/
        ├── HomeView.vue / NotFoundView.vue
        ├── auth/ (Login / Register)
        ├── music/ (MusicList / MusicWestern / MusicDetail / Therapy)
        ├── diary/ (DiaryList / DiaryWrite / PickBottle / Corner)
        ├── mood/ (MoodCalendar)
        ├── garden/ (Garden / Shop)
        ├── profile/ (Profile)
        └── notification/ (Notifications)
```

**约定**：
- 一个视图一个 `.vue` 文件；文件名 = 路由名 + `View.vue`。
- 视图按模块分目录；复用组件放 `components/`；共享内容数据放 `data/`。
- 需登录的视图在 `router/index.js` 加 `meta.requiresAuth: true`，守卫统一处理跳转。

### 1.9.5 加新视图（Vue 3 SPA 模式，替代旧 §2.1 Jinja2 模式）

> **2026-07-19 v2.0 后**：加新前台页面走 Vue 3 SPA 模式（本节），**不再**走 §2.1 Jinja2 模式。§2.1 仅适用于 `/admin/*` 后台 SSR 页面。

1. 在 `frontend/src/views/<module>/` 加 `XxxView.vue`（一个视图一个文件）
2. 在 [frontend/src/router/index.js](../frontend/src/router/index.js) 加路由：
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
     const res = await api.get('/xxx')   // 拦截器已解包，res 就是 JSON body
     data.value = res
   })
   </script>

   <template>
     <div>{{ data }}</div>
   </template>
   ```
4. 同步更新 [README.md](../README.md) §2 目录树 + [docs/README.md](README.md) 文档地图（Iron Rule）

> **后台页面**仍走 §2.1 Jinja2 模式（继承 `admin/_base.html`），不要混用。

#### 1.9.5.1 异步加载重组件（defineAsyncComponent 示例，2026-07-19 v2.0.1 加）

> **场景**：某个视图依赖体积大的库（如 Three.js ~600KB / pdf.js / monaco-editor），不想让它进首屏包。用 `defineAsyncComponent` 按需加载，**首屏只加载主 chunk，重组件单独成 chunk 在访问时才拉**。

**真实案例**：[GardenView.vue](../frontend/src/views/garden/GardenView.vue) 顶部嵌入了 3D 花田场景 [FlowerField.vue](../frontend/src/components/FlowerField.vue)，后者动态 `import('three')` 加载 Three.js。通过 `defineAsyncComponent` 把 FlowerField.vue 整体异步化，访问 `/garden` 时才拉 Three.js chunk。

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

**配套：vite.config.js 的 manualChunks**（[frontend/vite.config.js](../frontend/vite.config.js)）：
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
- **Vite 启动慢 / HMR 不生效**：检查 [frontend/vite.config.js](../frontend/vite.config.js) 的 `host: '127.0.0.1'`（不要写 `localhost`，IPv6 `[::1]` 会连不上，详见 [HANDOFF §6.12](HANDOFF.md)）
- **API 401 不跳登录**：检查 [frontend/src/api/index.js](../frontend/src/api/index.js) 的 axios 拦截器
- **404 不显示**：检查 `router/index.js` 末尾的 `/:pathMatch(.*)*` catch-all 路由
- **dist 未构建提示页**：访问 :5000 看到「dist 未构建」→ `python start.py build` 或 `cd frontend && npm run build`（v2.3.2 起默认生产模式 `python start.py` 也会自动构建）
- **dev 模式 :5000 是 Vite，不是 FastAPI**（v2.0.1 加）：应用模式（`--dev`）访问 :5000 是 Vite dev server（HMR + 源码），API 请求经 Vite proxy 转发到 :5001 的 FastAPI。要看 FastAPI Swagger 文档直接访问 :5001（`http://127.0.0.1:5001/docs`）。**生产模式（默认）:5000 才是 FastAPI**。详见 [§1.9.1](#191-启动开发模式vite-dev-server-5000--fastapi-5001v232-起需显式---dev)。
- **端口 5000 被占用**：`python start.py stop` 停掉旧进程；或检查是否同时跑了 Vite 和 FastAPI（应用模式 Vite 占 :5000，如果 FastAPI 没改成 :5001 就会撞）。Vite `strictPort: true` 会直接报错不自动跳端口。
- **3D 花田不显示**：访问 `/garden` 看到「🌿 花田正在生长…」一直转 → 打开 DevTools Console 看是不是 `Failed to fetch dynamically imported module`（three-vendor chunk 没加载到，检查 `static/dist/assets/three-vendor-*.js` 是否存在 → 不存在重新 `npm run build`）
- **Safari 主页 3D 不渲染**（v2.3.3 加）：iOS Safari 切后台→前台后 3D 黑屏 → 检查 `webglcontextlost` / `webglcontextrestored` 监听是否挂载（详见 [§1.9.8 Safari / iOS 兼容](#safari--ios-兼容v233-加) / [HANDOFF §6.24](HANDOFF.md)）；Safari 直接降级 SVG → 检查 `hasWebGL()` 是否误判（v2.3.3 **hasWebGL 重写** 已修复，区分 WebGL1/2）
- **Safari emoji 与 Chrome 不一致**（v2.3.3 加）：检查是否用了裸 emoji 字符 → 改用 `<EmojiIcon name="..." />`（详见 [§1.9.9](#19-emoji-组件用法emojiiconvuev233-加2026-07-30)）
- **proxy 没生效**：检查 [vite.config.js](../frontend/vite.config.js) 的 `server.proxy` 是否包含 `/api`、`/static`、`/admin`、`/docs`、`/openapi.json`（v2.0.1 起多了 `/docs` 和 `/openapi.json`，方便开发时直接在 :5000 访问 Swagger）

### 1.9.8 视觉组件开发指南（v2.1 加，2026-07-20；v2.2 PBR 升级，2026-07-20）

> 适用范围：所有用 Three.js / Canvas2D / Web Audio API 的视觉组件。当前已有 7 个：[FlowerField.vue](../frontend/src/components/FlowerField.vue) / [AmbientBackground.vue](../frontend/src/components/AmbientBackground.vue) / [HeroScene.vue](../frontend/src/components/HeroScene.vue) / [AudioVisualizer.vue](../frontend/src/components/AudioVisualizer.vue) / [SceneHint.vue](../frontend/src/components/SceneHint.vue) / [SceneControls.vue](../frontend/src/components/SceneControls.vue) + [utils/three-helpers.js](../frontend/src/utils/three-helpers.js) PBR 工具集。

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
理由：v2.1 各组件自己写 `new THREE.WebGLRenderer({ canvas, antialias: true })` + `renderer.toneMapping = ...`，4 个组件 4 套配置不一致；v2.2 抽到 [utils/three-helpers.js](../frontend/src/utils/three-helpers.js) 统一管理，新组件直接调函数即可。

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
2. **复制模板**：从 [AmbientBackground.vue](../frontend/src/components/AmbientBackground.vue)（三层全有）或 [HeroScene.vue](../frontend/src/components/HeroScene.vue)（Three.js + SVG 降级）开始改
3. **配色一致性**：用治愈系 5 色（藕粉 `#E8B8C5` / 淡黄 `#E8D5A8` / 青绿 `#A8C5A0` / 雾蓝 `#A8B8C5` / 纯白 `#FAF6F2`）+ 米白 `#F9F6F0` 背景，与 [tailwind.config.js](../frontend/tailwind.config.js) token 一致
4. **性能保护**：移动端粒子数减半 + `dpr` ≤ 1.5 + 几何精度降档（Lathe/Cylinder/Icosahedron 段数与细分降低、花瓣网格 5×8→4×6、地面圆 64→32、AudioVisualizer 柱数减半）；`defineAsyncComponent` 异步加载 Three.js
5. **降级路径**：每个 Three.js 组件必须有 CSS / SVG 静态降级；reduced-motion 用户不能看到闪烁 / 摇晃内容
6. **验证清单**：
   - 桌面 Chrome 默认 motion：3D / Canvas2D 正常渲染
   - DevTools → Rendering → `prefers-reduced-motion: reduce`：降级为静态
   - 移动端 Safari：粒子数减半、dpr ≤ 1.5、几何精度降档（顶点数大幅减少）
   - 切走标签页 30s 后回切：GPU 占用应归零（smartRAF 生效）
   - 在该组件所在视图和其他 Three.js 视图间来回切 5 次：无 `Too many active WebGL contexts` 警告
   - DevTools 模拟 iPhone 16（390×844）：topbar + 底部 tabbar + 「更多」抽屉 + 各视图差异化布局生效
7. **文档同步**：新增视觉组件 = **同一 commit 同步更新 6 份文档**（详见 [HANDOFF §12](HANDOFF.md)）

#### 视觉能力检测 API（[utils/visual.js](../frontend/src/utils/visual.js)）

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

> 🔒 **Safari 兼容 3 大坑**（详见 [HANDOFF §6.24](HANDOFF.md)）：① **WebGL 上下文丢失**（iOS Safari 切后台→前台触发 `webglcontextlost`）；② **`hasWebGL` 误判**（老 Safari 仅 WebGL1 被判无 WebGL）；③ **emoji 字体不一致**（Apple Color Emoji vs 系统 emoji）。

**新建 3D 组件必须复制 [HeroScene.vue](../frontend/src/components/HeroScene.vue) 的 Safari 兼容逻辑**：

1. **`webglcontextlost` / `webglcontextrestored` 事件监听**（在 [utils/three-helpers.js](../frontend/src/utils/three-helpers.js) 的 `createRenderer` 中已统一挂载）：
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

详见 [ARCHITECTURE §1.1.6](ARCHITECTURE.md) Safari 兼容决策 + 降级验证矩阵 + [HANDOFF §6.24](HANDOFF.md) 3 大坑。

### 1.9.9 emoji 组件用法（EmojiIcon.vue，v2.3.3 加，2026-07-30）

> 🔒 **铁律**：**新增 emoji 必须用 `<EmojiIcon name="..." />` 而非裸 emoji 字符**。裸 emoji 在 Safari（Apple Color Emoji 彩色写实）与 Chrome（系统 emoji 扁平）风格不一致，破坏 **跨浏览器一致** 的视觉调性。

**是什么**：[EmojiIcon.vue](../frontend/src/components/EmojiIcon.vue) 是基于 **Iconify** + `@iconify-json/twemoji` 的离线 **SVG emoji** 组件。twemoji 风格统一扁平彩色，不依赖系统 emoji 字体，确保 Safari / Chrome / Firefox / Edge 渲染完全一致。

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
- [AppLayout.vue](../frontend/src/components/AppLayout.vue)：品牌图标 / 导航项 / 通知铃铛 / 资源条
- [ProfileView.vue](../frontend/src/views/profile/ProfileView.vue)：头像 / 通知 / 资源 / 统计卡 / 快捷入口 / 花朵阶段

**查 twemoji 图标名**：访问 https://icon-sets.iconify.design/twemoji/ 搜索 emoji，复制 `name`（如 🏝️ → `desert-island`）。`@iconify-json/twemoji` 已在 [frontend/package.json](../frontend/package.json) 依赖中，构建时打包进 bundle（离线，不联网）。

> ⚠️ **不要**用裸 emoji 字符（如 `🏝️`）写进 `.vue` 模板——Safari 与 Chrome 渲染不一致。**所有前台 emoji 必须走 `<EmojiIcon>`**。后台 `/admin/*` SSR 模板不受此约束（独立隔离，不强求跨浏览器一致）。

---

## 2. 常见改动流程

### 2.1 加新页面（后台 Jinja2 SSR，仅 `/admin/*`）

> 前台新页面走 [§1.9.5 Vue 3 SPA 模式](#195-加新视图vue-3-spa-模式替代旧-21-jinja2-模式)。本节仅适用于 `/admin/*` 后台。

1. `templates/admin/your_page.html` 继承 `admin/_base.html`
2. [app/routers/admin_pages.py](../app/routers/admin_pages.py) 加路由（**新 API**：传 `request` 作第一参数）
3. `static/js/pages/admin_your_page.js` 写逻辑
4. 模板底部 `<script defer src="/static/js/pages/admin_your_page.js"></script>`
5. 同步更新 [README.md](../README.md) §2 目录树

模板示例：
```html
{% extends "admin/_base.html" %}
{% block content %}
<div class="admin-card">
    <h1>你的标题</h1>
    <p>...</p>
</div>
{% endblock %}
```

### 2.2 加新 API
1. [app/schemas/<name>.py](../app/schemas/) 写 Pydantic 模型
2. [app/schemas/__init__.py](../app/schemas/__init__.py) 加 import + `model_rebuild()`
3. [app/routers/<name>.py](../app/routers/) 加 `@router.post(...)`
4. 业务逻辑在 [app/services/<name>.py](../app/services/)

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
1. [app/models/<name>.py](../app/models/) 写 `class Xxx(Base): __tablename__ = "xxx"; ...`
2. [app/models/__init__.py](../app/models/__init__.py) import 它
3. 重启 → `init_db()` 自动建表
4. 同步更新 [README.md](../README.md) §4 + [docs/ARCHITECTURE.md](ARCHITECTURE.md) §4

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
1. [app/services/energy_service.py](../app/services/energy_service.py) 改 `grant_energy()` 逻辑
2. [app/utils/constants.py](../app/utils/constants.py) 同步 `ENERGY_RULES` 字典
3. 更新 [README.md](../README.md) §3.4 表格

### 2.5 改种子数据
1. [app/seed.py](../app/seed.py) 改数据
2. `python start.py --init-db` 重置数据库

### 2.6 加新动效（Vue + GSAP）
1. 在对应 `.vue` 的 `<style>` 里加 `@keyframes`（或改 [main.css](../frontend/src/assets/styles/main.css) 的通用动画）。
2. 用 Vue 绑定 class 或 GSAP timeline 触发；**不要**再往 `static/css/05-animations.css` 加前台动画（那是旧 SSR 时代文件）。
3. GSAP 入场动画只允许位移（`y` / `x`），不要设 `opacity:0` / `scale:0` 初始态；列表动画在 fetch 成功后 + `nextTick` + `querySelector` 守卫再播。
4. 所有动效必须尊重 `prefers-reduced-motion`。

### 2.7 加一个 AI 场景（2026-07-17 起）

> 现有 3 个场景在 [app/services/ai_service.py](../app/services/ai_service.py) / [app/routers/ai.py](../app/routers/ai.py) / [app/schemas/ai.py](../app/schemas/ai.py)。再加一个走同样套路。完整决策见 [HANDOFF §7.9](HANDOFF.md)。

**4 步走**：

#### 第 1 步：Schema
在 [app/schemas/ai.py](../app/schemas/ai.py) 加 `AI<X>In` + `AI<X>Out` 两个 Pydantic 模型：

```python
class AIXxxIn(BaseModel):
    """入参：xxx 场景"""
    user_text: str = Field(..., min_length=1, max_length=500)

class AIXxxOut(BaseModel):
    """出参：xxx 场景"""
    available: bool
    text: str
```

在 [app/schemas/__init__.py](../app/schemas/__init__.py) 的 `__all__` 加 import；末尾 `model_rebuild()` 区段确保新模型也被 rebuild（防 §3.1 Pydantic 前向引用坑）。

#### 第 2 步：Service
在 [app/services/ai_service.py](../app/services/ai_service.py) 加：

```python
# 1. 系统提示词常量（温柔语气、不诊断不开药、危机引导专业帮助）
SYSTEM_PROMPT_XXX = """你是一个温柔的倾听者..."""

# 2. 上层方法
def generate_xxx(self, user_text: str) -> str:
    return self._call_nvidia(
        system_prompt=SYSTEM_PROMPT_XXX,
        user_content=user_text,
        max_tokens=900,
        temperature=0.7,
    )
```

**禁止**在 router 里直接调 `_call_nvidia()`——业务规则集中在 service。

#### 第 3 步：Router
在 [app/routers/ai.py](../app/routers/ai.py) 加：

```python
@router.post("/xxx", response_model=AIXxxOut)
def xxx(body: AIXxxIn, user: User = Depends(get_current_user)):
    try:
        msg = ai_service.generate_xxx(body.user_text)
        return {"available": True, "text": msg}
    except AIServiceUnavailable:
        # 降级：不报 500，返回治愈系友好提示
        return {"available": False, "text": "AI 在休息一下，待会儿再来轻声陪伴你"}
```

**铁律**：
- 端点**必须** `Depends(get_current_user)` 鉴权
- 端点**必须** try/except `AIServiceUnavailable` 降级，**不报 500**

#### 第 4 步：前端集成（Vue 3 SPA）

| 方式 | 做法 |
|---|---|
| **独立新页面**（如身心调理） | 新建 `frontend/src/views/xxx/XxxView.vue` + 在 [router/index.js](../frontend/src/router/index.js) 加路由 |
| **已有页面加区块**（鼓励语 / 治愈语） | 在对应 `.vue` 里加区块，调 `@/api` 的 axios 实例 |
| **首页卡片**（音乐推荐） | 改 [HomeView.vue](../frontend/src/views/HomeView.vue)，用 `userStore.isLoggedIn` 控制显示 |

JS 调用示例（注意拦截器已解包，`res` 就是 JSON body）：

```javascript
import api from '@/api'

const res = await api.post('/ai/xxx', { user_text: '...' })
// available:true/false 都正常显示文案，不报错
text.value = res.text
```

#### 第 5 步：测试降级（必做）
**先不配 `QI_NVIDIA_API_KEY`**，确认端点返回 `available:false` + 友好提示；**再配 key** 跑一遍，确认 `available:true` + AI 文案。详见 [§3.14](#314-ai-端点降级测试方法)。

### 2.8 加一条身心调理规则（v2.6.0）

1. 在 [app/services/therapy_service.py](../app/services/therapy_service.py) 的 `PROBLEM_RULES` 加一条：关键词、`yin`、两式 `moves`、`sachet`、`bracelet`、`food`。
2. 若新增香囊/手串/食疗，分别加到 `SACHETS` / `BRACELETS` / `FOODS`，必须写 `price`、`purchase_url`、`available` 与过敏原/材质/成分。
3. 新增八段锦招式加到 `BADUANJIN`（名称、focus、steps）。
4. 若新增每日奖励来源，同步 [app/utils/constants.py](../app/utils/constants.py) 的 `DAILY_ENERGY_LIMITS` 与 [README §3.4](../README.md)。
5. 重启后跑 `POST /api/therapy/recommend` 与 `POST /api/therapy/baduanjin/checkin`；前端 `npm run build`。

---

## 3. 踩坑清单（按主题，非版本顺序）

### 3.1 Pydantic 前向引用

**症状**：
```
pydantic.errors.PydanticUserError: `TypeAdapter[typing.Annotated[list[EnergyRecordOut], FieldInfo(...)]] is not fully defined`
```

**根因**：
Pydantic v2 用类型注解，前向引用不会自动 `model_rebuild()`。

**修复**：
1. **不要**在 schema 文件顶部加 `from __future__ import annotations`
2. 在 [app/schemas/__init__.py](../app/schemas/__init__.py) 显式 `BaseModel.model_rebuild()`

---

### 3.2 bcrypt 4.x 与 passlib 不兼容

**症状**：
```
AttributeError: module 'bcrypt' has no attribute '__about__'
```

**根因**：
passlib 1.7 用 `bcrypt.__about__.__version__` 检查版本，bcrypt 4.x 移除了这个属性。

**修复**：
[app/utils/crypto.py](../app/utils/crypto.py) **不**用 passlib：
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
[app/utils/crypto.py](../app/utils/crypto.py) 有 `_truncate()` 函数，**所有** hash/verify 之前必须调用。

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
1. [app/main.py](../app/main.py) 顶部（任何 import 之前）：
```python
import sys
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass
```

2. [app/main.py](../app/main.py) logging 初始化后强制所有 handler 用 utf-8

3. [start.py](../start.py) 启动 fg 子进程时：
```python
child_env["PYTHONIOENCODING"] = "utf-8"
child_env["PYTHONUTF8"] = "1"
```

4. **logger 输出不要用 emoji**（用户消息也容易出），统一用 ASCII 标记 `[OK]` `[FAIL]` `[WARN]`

---

### 3.6 日记 schema 的字段方向（v2.3 已反转）

**现状**：`DiaryCreateIn` 必填 **`content: str`**（明文），可选 `mood_type` / `is_public`；`send_to_ai_hole` / `content_encrypted` 是遗留字段，不是入参。

```python
class DiaryCreateIn(BaseModel):
    content: str = Field(..., min_length=1)   # 明文
    mood_type: Optional[str] = Field(None, max_length=20)
    is_public: bool = False
```

**历史坑**：v2.3 之前只收 `content_encrypted`；如果你在旧文档/旧 commit 看到「不要 content」，那是历史版本。现在传 `content_encrypted` 会被忽略或 422。

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

详见 [app/services/energy_service.py](../app/services/energy_service.py)。

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
[start.py](../start.py) 启动子进程时**永远**用 `Path(__file__).resolve()`：
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
1. [app/models/user.py](../app/models/user.py) 加了 `is_admin` 字段
2. `User.to_public_dict()` 也加了
3. ❌ **漏了**：[app/schemas/auth.py](../app/schemas/auth.py) `AuthOut` **没声明** `is_admin`
4. [app/routers/auth.py](../app/routers/auth.py) 用 `response_model=AuthOut` → FastAPI 序列化时**只保留 schema 声明的字段**
5. 前端 `data.is_admin` 永远 `undefined` → JS 卡在「此账号没有后台权限」

**修复**（[app/schemas/auth.py](../app/schemas/auth.py)）：
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

**修复**（[static/css/01-reset.css](../static/css/01-reset.css) + [02-layout.css](../static/css/02-layout.css) + [06-music.css](../static/css/06-music.css)）：
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

### 3.12 历史页面合并（已归档）

早期 SSR 时代的「今日手帐合并进情绪日历」「密码可见性切换」「iOS 导航栏避让」记录已不再适用于当前 Vue 3 前台；相关实现见 [CHANGELOG.md](CHANGELOG.md) 与 git 历史。当前只需记住：旧路由 `/mood`、`/mood-calendar`、`/my-bottles`、`/pick` 由 [app/routers/pages.py](../app/routers/pages.py) 302 到新路由。

---

### 3.14 AI 端点降级测试方法（2026-07-17 加）

**场景**：3 个 AI 端点（`/api/ai/encouragement` / `/api/ai/healing` / `/api/ai/recommend-music`）必须保证「未配 key 或调用失败时返回 200 + `available:false` + 治愈系友好提示」，**不报 500**。这是 AI 接入「渐进增强」的核心保证。

**测试 1：未配 key 降级**（默认状态）
```bash
# 1. 确保 .env 没有 QI_NVIDIA_API_KEY（或留空）
# 2. 重启
python start.py restart
# 3. 登录拿 cookie
curl -c c.txt -X POST http://127.0.0.1:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"nickname":"test","password":"hello123"}'
# 4. 调 3 个 AI 端点，应该都返回 200 + available:false
curl -b c.txt -X POST http://127.0.0.1:5000/api/ai/healing \
  -H "Content-Type: application/json" \
  -d '{"mood_emoji":"calm"}'
# 期望: {"available":false,"text":"今天的心，已经被这片海记下了。","model":""}
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
# 期望: {"available":true,"text":"<AI 生成的治愈语>","model":"z-ai/glm-5.3-flash"}
```

**测试 3：调用失败降级**（模拟网络/限流/4xx/5xx）
```bash
# 方法 A：临时把 QI_AI_BASE_URL 改成无效地址（如 https://invalid.example.com/v1）→ 重启 → 调端点
# 方法 B：临时把 QI_NVIDIA_API_KEY 改成无效 key（如 nvapi-invalid）→ 重启 → 调端点
# 期望: 200 + available:false + 治愈系提示（不报 500）
```

**测试 4：前端浏览器手动测**
```
# 1. /diary/pick 拾瓶后看 AI 鼓励语容器有内容
# 2. /calendar 打卡后看 AI 治愈语容器有内容
# 3. /music 或首页「AI 帮我选音」→ 描述状态 → 看推荐 + 跳转链接
# 4. AI 树洞已删除，/ai-chat 不再可用
```

**铁律**：
- AI 端点**永不**返回 5xx——失败时统一返回 200 + `available:false` + 治愈系提示
- 前端拿 `available:true/false` 都正常显示文案，**不报错**
- 改完 AI 代码必须跑测试 1（不配 key 降级）+ 测试 2（配 key 正常）—— 两个状态都要测
- 失败原因走 `logger.warning`，**不**暴露给前端（避免泄露内部信息）
- `_call_nvidia()` 单次超时 60s、瞬时错误重试 3 次（线性退避）；当前模型 `z-ai/glm-5.3-flash`（reasoning 模型，`max_tokens` 需 900–1200，否则可能静默返回空 content）；超时/空值也走降级返回 `available:false`，不报 500

---

### 3.15 双资源系统的实际实现（以代码为准）

- 露水 = `users.total_energy`；落叶 = `users.leaves`；**没有** `users.dew` / `EnergyRecord.resource_type` / `ShopItem.cost_resource` 这些字段（旧文档曾写错）。
- 兑换时看 `ShopItem.cost_currency`（`dew` / `leaves`）；发放露水用 `grant_energy()`，加落叶用显式 `UPDATE users SET leaves = leaves + N`。
- 详细规则见 [README §3.4](../README.md) / [ARCHITECTURE §1.1.7.2](ARCHITECTURE.md)。

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
- [ ] 用户日记正文 / 密码 / cookie / API key 出现在日志里了吗？（绝对不能）

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

- 项目 PRD：[README.md](../README.md)
- 关键设计决策：[HANDOFF.md](HANDOFF.md) §5
- 架构详解：[docs/ARCHITECTURE.md](ARCHITECTURE.md)
- 部署指南：[docs/DEPLOYMENT.md](DEPLOYMENT.md)
- 现状快照：[docs/PROJECT_STATE.md](PROJECT_STATE.md)
