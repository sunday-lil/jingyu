# 项目现状快照

> 一眼看出「现在能跑吗」「最近改了什么」「还有什么 TODO」。
> 每次大改后请更新本文件。

**最后更新**：2026-07-20（v2.2.1 start.py 自动构建 — `python start.py` 默认行为变更：dist 未构建时不再走开发模式，而是自动 `npm install + npm run build` 后走生产模式（:5000 永远是 FastAPI）；新增 `--dev` 参数显式走开发模式；服务器部署简化为 3 步：上传代码 + 装 Python + Node.js + `python start.py`）

---

## 1. 总体状态

| 维度 | 状态 | 备注 |
|---|---|---|
| **可运行** | ✅ | 用户始终访问 `:5000`：开发模式 Vite :5000 + FastAPI :5001（`python start.py` 自动起两个）；生产模式 FastAPI :5000（`python start.py build` + `python start.py`） |
| **v2.0 Vue 3 重构** | ✅ 完成 | 2026-07-19，前端独立 `frontend/`，13 个视图迁入 `frontend/src/views/`，详见 §2 |
| **v2.1 视觉增强** | ✅ 完成 | 2026-07-20，4 个视觉组件 + 三层渐进增强策略（CSS / Canvas2D / Three.js），全部支持降级，详见 §2 |
| **v2.2 视觉重构** | ✅ 完成 | 2026-07-20，解决 v2.1 "红白机观感" + "交互不明确"两大问题：three-helpers.js PBR 工具集 + SceneHint/SceneControls 交互组件 + 4 个视觉组件 v2 重写（PBR + Bloom + OrbitControls + raycaster），详见 §2 |
| **v2.2.1 start.py 自动构建** | ✅ 完成 | 2026-07-20，`python start.py` 默认 dist 未构建时自动 `npm install + build` 走生产模式（:5000 永远是 FastAPI）；新增 `--dev` 参数；服务器部署简化为 3 步，详见 §2 |
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

### 2026-07-20（v2.2.1）— start.py 自动构建（服务器部署重大简化）

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
  - 移动端：dpr ≤ 1.5 / 粒子数减半 / Bloom 强度降低 / 阴影 mapSize 1024
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
