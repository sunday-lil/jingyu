# AGENTS.md — 静屿项目工作规则

> 本文件是给所有接手本项目的 AI / 自动化开发者的**硬性约定**，优先级高于个人习惯。
> 项目背景见 [README.md](README.md)，完整交接见 [docs/HANDOFF.md](docs/HANDOFF.md)。

## 两条铁律

### 铁律 1：改代码必须自测 + 同步更新全部文档

**任何代码改动，commit 前必须完成自测；自测不通过不得 commit。**

最低自测标准（按改动范围取并集）：

| 改动范围 | 必须做的事 |
|---|---|
| 后端 API / service / model | `python start.py restart` 无报错 → 请求受影响接口（2xx/4xx 符合预期）→ `logs/healing.log` 无 ERROR → 涉及字段变更时确认老库迁移生效 |
| 前端 Vue / 路由 / 样式 | `cd frontend && npm run build` 通过 → 生产模式启动 → 浏览器打开受影响页面，功能可用 + console 无报错 |
| 前后端联动 | 后端接口 + 前端页面一起验证，至少走通一次完整用户动作 |
| 仅文档 | 检查 Markdown 链接可解析、命令可执行；无需启动服务 |

补充要求：

- UI 改动必须重新 `npm run build`（`static/dist/` 是生产入口，改源码不构建等于没改）。
- 修 Bug 必须验证「原复现步骤不再复现」，不能只看代码推断。
- AI 功能采用优雅降级：未配置 key 时验证返回 200 + `available:false`，不要把真实 AI 输出当作自测前置条件。
- 临时启动的服务，验证完要 `python start.py stop`，不要把进程留在后台。

**同时必须在同一个 commit 内更新文档**（这是项目既有的最高优先级规则）：

- 默认 6 份：README / HANDOFF / PROJECT_STATE / ARCHITECTURE / DEPLOYMENT / DEVELOPMENT。
- 按 [HANDOFF §12.2](docs/HANDOFF.md) 的触发表判断哪些章节必须改；不确定就全量检查一遍。
- 禁止「代码先 commit，稍后补 docs」；文档与代码矛盾时**以代码为准，并立即修文档**。
- 提交前过一遍 [HANDOFF §12.4](docs/HANDOFF.md) 与 [README §9](README.md) 的自检清单。

### 铁律 2：完成后必须推送 GitHub（使用 gh）

**任务完成的定义包含「远端已同步」，本地 commit 不算完成。**

固定流程：

```bash
# 1. 认证前置（每次推送前确认）
gh auth status
# 若 token 失效：gh auth refresh -h github.com     （或 gh auth login）
# 让 git 复用 gh 凭据：gh auth setup-git

# 2. 提交（Conventional Commits，见 HANDOFF §12.7）
git add -A
git commit -m "type(scope): subject"

# 3. 立即推送
git push origin main

# 4. 验证远端与本地一致
git status --short                                   # 应为空
git ls-remote origin refs/heads/main                 # 应与下面一致
git rev-parse HEAD
# 或：gh api repos/sunday-lil/jingyu/commits/main --jq .sha
```

硬性约束：

- 不允许「先 commit，明天再推」「攒一周一起推」。
- 不允许 `git push --force`（除非 100% 确认且用户明确同意）。
- `gh auth status` 失败时，先修复认证；修复不了就**如实报告并停止**，不得声称任务完成。
- push 失败时保留本地 commit，报告失败原因与待执行的命令。

## 完成定义（DoD）

一次任务只有同时满足以下条件才算完成：

- [ ] 代码改动已自测（按上表），无报错、无 console error、无残留后台进程
- [ ] 前端改动已 `npm run build`
- [ ] 相关文档已在**同一个 commit** 更新完毕
- [ ] commit message 符合 Conventional Commits（`type(scope): subject`）
- [ ] `git push origin main` 成功
- [ ] 远端 `main` 的 SHA 与本地 `HEAD` 一致

## Commit 规范速查

- 格式：`<type>(<scope>): <subject>`，subject ≤ 50 字符、小写开头、句尾不加句号。
- type：`feat` / `fix` / `refactor` / `docs` / `style` / `test` / `chore` / `perf` / `revert`。
- scope：`auth` / `diary` / `mood` / `music` / `energy` / `garden` / `admin` / `frontend` / `docs` / `deps` / `start` 等。
- 完整规则与示例：[HANDOFF §12.7](docs/HANDOFF.md)。

## 快速入口

- 启动 / 停止：`python start.py` / `python start.py stop`（开发模式 `--dev`）
- 接口文档：<http://127.0.0.1:5000/docs>
- 后台：<http://127.0.0.1:5000/admin/login>
- 数据与迁移：[app/database.py](app/database.py) `_migrate_legacy_columns()` + [app/seed.py](app/seed.py)
- 已知坑：[HANDOFF §6](docs/HANDOFF.md)
