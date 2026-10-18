# 项目现状快照

> 当前版本：**v2.6.0**（2026-10-18）
> 本文件只回答「现在是什么状态、能不能跑、还剩什么问题」。版本历史见 [CHANGELOG.md](CHANGELOG.md)。

## 1. 总体状态

| 维度 | 状态 | 说明 |
|---|---|---|
| 可运行 | ✅ | `python start.py`（生产模式，FastAPI :5000）；`python start.py --dev`（Vite :5000 + FastAPI :5001） |
| 前端构建 | ✅ | `static/dist/` 已构建；改 `frontend/src/` 后必须重新 `npm run build` |
| 后端 | ✅ | FastAPI + SQLAlchemy + SQLite，约 3k 行 Python |
| 数据库 | ✅ | `data/healing.db`，12 张表，启动自动建表 + 轻量迁移 + 种子 |
| 前端 | ✅ | Vue 3 SPA，16 条业务路由 + 404，17 个 `.vue` 视图 |
| AI（可选） | ✅ | 3 个场景：漂流瓶鼓励语 / 情绪日历治愈语 / 音乐推荐；树洞对话已删除 |
| 身心调理 | ✅ | 问题输入 → 曲 / 八段锦 / 香囊 / 手串 / 食疗；八段锦跟练打卡 +1 露水/日 |
| 商品 | 🟡 橱窗 | 好物展示 + 预约/外链；**未接支付、库存、发货** |
| 后台 | ✅ | `/admin/login`（Jinja2 SSR，6 个页面 + 13 个 API） |
| 测试 | ❌ | 无 pytest 套件，依赖手工冒烟 + 浏览器验证 |
| HTTPS | ❌ | 本地 HTTP；生产需 Nginx + Let's Encrypt |

## 2. 模块矩阵

| 模块 | 路由 | 前端视图 | 后端 | 状态 |
|---|---|---|---|---|
| 首页 | `/` | [HomeView.vue](../frontend/src/views/HomeView.vue) | SPA fallback | ✅ |
| 琴音疗心 | `/music`、`/music/western`、`/music/:yin` | `views/music/MusicListView / MusicWesternView / MusicDetailView` | [music.py](../app/routers/music.py) | ✅ 22 首（16 真实 + 6 静音占位） |
| 身心调理 | `/music/therapy` | [TherapyView.vue](../frontend/src/views/music/TherapyView.vue) | [therapy.py](../app/routers/therapy.py) / [therapy_service.py](../app/services/therapy_service.py) | ✅ 推荐 + 八段锦打卡 + 好物橱窗 |
| 日记海岸 | `/diary`、`/diary/write`、`/diary/pick` | `views/diary/*` | [diary.py](../app/routers/diary.py) | ✅ 明文日记 + 漂流瓶 |
| 静屿角落 | `/corner` | [CornerView.vue](../frontend/src/views/diary/CornerView.vue) | [diary.py](../app/routers/diary.py) `/api/diary/corner` | ✅ 私密碎碎念（is_public=False） |
| 情绪日历 | `/calendar` | [MoodCalendarView.vue](../frontend/src/views/mood/MoodCalendarView.vue) | [mood.py](../app/routers/mood.py) | ✅ 一天多条 + 罗素环 + 今日可删 |
| 落叶花坊 | `/shop` | [ShopView.vue](../frontend/src/views/garden/ShopView.vue) | [garden.py](../app/routers/garden.py) / [energy.py](../app/routers/energy.py) | ✅ 28 件商品 |
| 屿上花田 | `/garden` | [GardenView.vue](../frontend/src/views/garden/GardenView.vue) | [flower_service.py](../app/services/flower_service.py) | ✅ 5 阶段生长 |
| 我的 | `/profile` | [ProfileView.vue](../frontend/src/views/profile/ProfileView.vue) | [profile.py](../app/routers/profile.py) | ✅ 头像/昵称/统计 |
| 通知 | `/notifications` | [NotificationsView.vue](../frontend/src/views/notification/NotificationsView.vue) | [notification.py](../app/routers/notification.py) | ✅ 60s 轮询未读 |
| 登录/注册 | `/login`、`/register` | `views/auth/*` | [auth.py](../app/routers/auth.py) | ✅ cookie session |
| 后台 | `/admin/*` | `templates/admin/*` | [admin.py](../app/routers/admin.py) / [admin_pages.py](../app/routers/admin_pages.py) | ✅ 秘密入口 |

## 3. 数据快照（2026-10-18 本地库）

| 表 | 行数 | 备注 |
|---|---|---|
| `users` | 4 | admin + 3 个测试账号 |
| `musics` | 22 | 16 classic（真实音频）+ 6 western（5338 字节静音占位） |
| `shop_items` | 28 | 11 花种 + 12 装扮 + 5 徽章（树洞徽章已移除） |
| `diaries` / `mood_checkins` | 0 / 0 | 测试数据已清理 |
| `baduanjin_checkins` / `therapy_interests` | 0 / 0 | v2.6.0 新表 |
| `energy_records` | 3 | 测试期间产生 |

> 种子：`SEED_MUSIC` 22 首、`DEFAULT_SHOP_ITEMS` 28 件；启动时按 title/name 幂等补齐。

## 4. 已知问题（按优先级）

1. **6 首西洋曲仍是静音占位**：每个 5338 字节（ID3 + 静音帧），播放无声。需要真实音频；用户同名覆盖 `static/audio/tracks/{曲名}.mp3` 后重启即可自动校准时长。
2. **`/admin` 无尾斜杠返回 404**：SPA fallback 把 `admin` 判 404；入口请用 `/admin/login` 或 `/admin/`。
3. **商品未接支付/发货**：当前只有橱窗 + 预约意向，不产生订单；购买赠露水也尚未实现（等真正交易闭环后再定）。
4. **八段锦未接视频验证**：当前是跟练打卡（每天一次 +1 露水），没有视频上传/审核/防作弊。
5. **无自动化测试**：没有 `tests/`；新增的 therapy / 日记 / 能量规则靠手工冒烟。
6. **AI 依赖外部模型**：NVIDIA NIM 模型可能下架（v2.5.3 已从 llama 切到 glm）；换模型需同时改 `.env` 与 [app/config.py](../app/config.py)。
7. **健康/食品合规**：香囊、手串、食疗目前只做展示与预约；真正售卖前需资质、标签、过敏原、售后与广告合规。
8. **音频版权**：现有 16 首真实录音来自用户自备；公开部署前需确认授权。

## 5. 待办（建议顺序）

### P0

- [ ] 补 6 首西洋曲真实音频（或明确下架该板块）
- [ ] 加 `tests/`：therapy_service、日记权限、能量规则、迁移
- [ ] 修 `/admin` 无尾斜杠 404
- [ ] 给八段锦打卡补一个 7 日徽章（可选，当前只有露水）

### P1

- [ ] 商品接入真实购买/预约通知（需主体资质、支付、发货、售后）
- [ ] 八段锦视频上传 + 审核/防作弊（需存储与隐私策略）
- [ ] 首页第二期：小岛等级系统（等 [HOME_REDESIGN_PROPOSAL.md](HOME_REDESIGN_PROPOSAL.md) 拍板）
- [ ] 生产部署加 HTTPS + 备份定时任务

### P2

- [ ] 漂流瓶 WebSocket 实时漂动
- [ ] 审计日志
- [ ] PWA / 离线
- [ ] 多语言 i18n

## 6. 文档与规则

- 文档职责边界见 [docs/README.md](README.md)。
- 工作规则（自测 + 同 commit 更新文档 + gh 推送）见 [AGENTS.md](../AGENTS.md)；完整铁律见 [HANDOFF §12](HANDOFF.md)。
- 本文件不记录逐版本变更；历史请查 [CHANGELOG.md](CHANGELOG.md)。
