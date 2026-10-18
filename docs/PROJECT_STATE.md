# 项目现状快照

> 当前版本：**v2.5.3**（2026-09-13 代码；2026-10-18 文档整理）
> 本文件只回答「现在是什么状态、能不能跑、还剩什么问题」。版本历史见 [CHANGELOG.md](CHANGELOG.md)。

## 1. 总体状态

| 维度 | 状态 | 说明 |
|---|---|---|
| 可运行 | ✅ | `python start.py`（生产模式，FastAPI :5000）；`python start.py --dev`（Vite :5000 + FastAPI :5001） |
| 前端构建 | ✅ | `static/dist/` 已构建（2026-09-13）；改 `frontend/src/` 后必须重新 `npm run build` |
| 后端 | ✅ | FastAPI 0.111 + SQLAlchemy 2.0 + SQLite，约 2.5k 行 Python |
| 数据库 | ✅ | `data/healing.db`，10 张表，启动时自动建表 + 轻量迁移 + 种子 |
| 前端 | ✅ | Vue 3 SPA，15 条路由 + 404，16 个 `.vue` 视图 |
| AI（可选） | ✅ 可用 | NVIDIA NIM `z-ai/glm-5.3-flash`；未配置 key 时 4 个端点优雅降级 |
| 后台 | ✅ | `/admin/login`（Jinja2 SSR，6 个页面 + 13 个 API） |
| 测试 | ❌ | 无 pytest 套件，依赖手工冒烟 + 浏览器验证 |
| HTTPS | ❌ | 本地 HTTP；生产需 Nginx + Let's Encrypt |

## 2. 模块矩阵

| 模块 | 路由 | 前端视图 | 后端 | 状态 |
|---|---|---|---|---|
| 首页 | `/` | [HomeView.vue](../frontend/src/views/HomeView.vue) | SPA fallback | ✅ |
| 琴音疗心 | `/music`、`/music/western`、`/music/:yin` | [MusicListView.vue](../frontend/src/views/music/MusicListView.vue) / [MusicWesternView.vue](../frontend/src/views/music/MusicWesternView.vue) / [MusicDetailView.vue](../frontend/src/views/music/MusicDetailView.vue) | [music.py](../app/routers/music.py) | ✅ 22 首（16 首真实音频 + 6 首 0 字节西洋占位） |
| 日记海岸 | `/diary`、`/diary/write`、`/diary/pick` | `views/diary/*` | [diary.py](../app/routers/diary.py) | ✅ 明文日记 + 漂流瓶 |
| 情绪日历 | `/calendar` | [MoodCalendarView.vue](../frontend/src/views/mood/MoodCalendarView.vue) | [mood.py](../app/routers/mood.py) | ✅ 一天多条 + 罗素情绪环 + 今日可删 |
| 心语树洞 | `/ai-chat` | [AIChatView.vue](../frontend/src/views/ai/AIChatView.vue) | [ai.py](../app/routers/ai.py) | ✅ 文件式历史，可保留/删除 |
| 落叶花坊 | `/shop` | [ShopView.vue](../frontend/src/views/garden/ShopView.vue) | [garden.py](../app/routers/garden.py) + [energy.py](../app/routers/energy.py) | ✅ 29 件商品 |
| 屿上花田 | `/garden` | [GardenView.vue](../frontend/src/views/garden/GardenView.vue) | [garden.py](../app/routers/garden.py) + [flower_service.py](../app/services/flower_service.py) | ✅ 5 阶段生长 |
| 我的 | `/profile` | [ProfileView.vue](../frontend/src/views/profile/ProfileView.vue) | [profile.py](../app/routers/profile.py) | ✅ 头像/昵称/统计 |
| 通知 | `/notifications` | [NotificationsView.vue](../frontend/src/views/notification/NotificationsView.vue) | [notification.py](../app/routers/notification.py) | ✅ 60s 轮询未读 |
| 登录/注册 | `/login`、`/register` | `views/auth/*` | [auth.py](../app/routers/auth.py) | ✅ cookie session |
| 后台 | `/admin/*` | `templates/admin/*` | [admin.py](../app/routers/admin.py) / [admin_pages.py](../app/routers/admin_pages.py) | ✅ 秘密入口 |

## 3. 数据快照（2026-10-18 本地库）

| 表 | 行数 | 备注 |
|---|---|---|
| `users` | 4 | admin + 3 个测试账号 |
| `musics` | 22 | 16 classic（真实音频）+ 6 western（0 字节占位） |
| `shop_items` | 29 | 11 花种 + 12 装扮 + 6 徽章 |
| `diaries` / `mood_checkins` | 0 / 0 | 社交与打卡数据为空 |
| `energy_records` | 3 | 测试期间产生 |
| `garden_items` / `user_flowers` / `notifications` | 0 | 尚未使用 |

> 种子数据：`SEED_MUSIC` 22 首、`DEFAULT_SHOP_ITEMS` 29 件；启动时按 title/name 幂等补齐，并按真实音频自动校准 `duration`。

## 4. 已知问题（按优先级）

1. **6 首西洋曲音频是 0 字节**：`static/audio/tracks/` 中《绿袖子》《卡农》《致爱丽丝》《月光奏鸣曲》《天鹅湖》《昨日重现》为 0 字节且已被 git 跟踪；`seed.py` 的占位逻辑只在文件不存在时写入，不会自愈。播放会失败。处理：删除这 6 个 0 字节文件后重启让 seed 写静音占位，或直接放入真实音频。
2. **`/admin` 无尾斜杠返回 404**：SPA fallback 把 `full_path == "admin"` 判为 404；`/admin/` 和 `/admin/login` 正常。建议后续在 fallback 中把 `/admin` 302 到 `/admin/`。
3. **无自动化测试**：没有 `tests/`，能量规则 / 迁移 / 权限都靠手工验证；新增功能回归成本高。
4. **文档与实现曾长期不一致**：README 旧版仍写「日记端到端加密」、AI 模型仍写 `llama-3.1-8b`、曲目/商品数量偏旧。本次文档整理已按代码修正；以后改代码必须同步文档。
5. **AI 依赖外部模型生命周期**：模型由 NVIDIA NIM 提供，可能下架（v2.5.3 已因 `llama-3.1-8b` 下架切到 `z-ai/glm-5.3-flash`）。换模型必须同时改 `.env` 与 [app/config.py](../app/config.py) 默认值。
6. **后台管理员密码**：首次启动随机生成并写入 `logs/healing.log`；生产部署必须在 `.env` 设 `QI_ADMIN_PASSWORD`。不要把任何真实密码写进文档。

## 5. 待办（建议顺序）

### P0

- [ ] 补 6 首西洋曲音频（或先写静音占位，避免 0 字节文件）
- [ ] 加 `tests/`：`pytest` 覆盖能量规则、日记权限、心情打卡、迁移函数
- [ ] 修 `/admin` 无尾斜杠 404

### P1

- [ ] 首页第二期：小岛等级系统（等 [HOME_REDESIGN_PROPOSAL.md](HOME_REDESIGN_PROPOSAL.md) §六 的 4 个决策点拍板）
- [ ] 补齐 22 首曲目的真实封面/时长信息
- [ ] 生产部署加 HTTPS + 备份定时任务（见 [DEPLOYMENT.md](DEPLOYMENT.md)）
- [ ] 加一个最小 CI：`python -m compileall app` + `npm run build`

### P2

- [ ] 漂流瓶 WebSocket 实时漂动
- [ ] 审计日志（谁在何时拾取了谁的瓶子）
- [ ] PWA / 离线写日记
- [ ] 多语言 i18n

## 6. 文档与规则

- 全部文档的职责边界见 [docs/README.md](README.md)。
- 工作规则（自测 + 同 commit 更新文档 + gh 推送）见 [AGENTS.md](../AGENTS.md)；完整铁律见 [HANDOFF §12](HANDOFF.md)。
- 本文件不再记录逐版本变更；需要历史请查 [CHANGELOG.md](CHANGELOG.md)。
