# 静屿 · 文档地图

> 当前版本：**v2.6.2**（2026-10-25）
> 本目录只放项目文档；根目录的**文档**只保留 [README.md](../README.md)（产品首页 + 开发者速查）和 [AGENTS.md](../AGENTS.md)（工作规则），其余为代码 / 配置 / 启动脚本。

## 一、按角色读

| 你是 | 先读 | 再读 |
|---|---|---|
| 第一次访问项目 | [README.md](../README.md) | — |
| 接手的 AI / 新开发者 | [HANDOFF.md](HANDOFF.md) | [ARCHITECTURE.md](ARCHITECTURE.md) → [DEVELOPMENT.md](DEVELOPMENT.md) |
| 想知道「现在能不能跑」 | [PROJECT_STATE.md](PROJECT_STATE.md) | [DEPLOYMENT.md](DEPLOYMENT.md) |
| 要改代码 | [AGENTS.md](../AGENTS.md) + [DEVELOPMENT.md](DEVELOPMENT.md) | [HANDOFF §6 已知坑](HANDOFF.md) |
| 要部署 | [DEPLOYMENT.md](DEPLOYMENT.md) | [.env.example](../.env.example) |
| 只想看某版本改了什么 | [CHANGELOG.md](CHANGELOG.md) | — |
| 想接真实音频 | [曲目清单.md](曲目清单.md) | [ARCHITECTURE §9.5](ARCHITECTURE.md) |

## 二、每份文档的职责（避免重复）

| 文档 | 只负责 | 不负责 |
|---|---|---|
| [README.md](../README.md) | 产品介绍、快速启动、模块一览、开发者速查、关键文件表 | 版本历史、详细踩坑、完整部署步骤 |
| [HANDOFF.md](HANDOFF.md) | 接手上下文、技术栈、项目结构、关键决策、已知坑、改动指南 | 逐版本流水账（→ CHANGELOG） |
| [PROJECT_STATE.md](PROJECT_STATE.md) | 当前状态快照、模块矩阵、数据快照、已知问题、TODO | 历史变更详情（→ CHANGELOG） |
| [ARCHITECTURE.md](ARCHITECTURE.md) | 为什么这样分层、数据流、鉴权、AI、后台、安全的架构解释 | 操作步骤（→ DEVELOPMENT / DEPLOYMENT） |
| [DEVELOPMENT.md](DEVELOPMENT.md) | 开发铁律、前端开发模式、常见改动流程、踩坑复现与修法 | 产品介绍、部署上线 |
| [DEPLOYMENT.md](DEPLOYMENT.md) | 宝塔 / systemd / nohup 部署、Nginx、HTTPS、备份、验证 | 功能设计、版本历史 |
| [CHANGELOG.md](CHANGELOG.md) | **全部版本变更历史**（v2.2.2 → v2.6.2） | 当前状态、操作指南 |
| [曲目清单.md](曲目清单.md) | 22 首曲目清单、音频放置方式、当前接入状态 | 音频架构决策（→ ARCHITECTURE） |
| [HOME_REDESIGN_PROPOSAL.md](HOME_REDESIGN_PROPOSAL.md) | 首页重构设计提案（第一期已落地，第二期待拍板） | 已上线功能说明 |
| [AGENTS.md](../AGENTS.md) | AI/自动化开发者的硬性工作规则（自测、文档、推送） | 技术细节 |

## 三、事实优先级

1. **代码**是唯一事实来源；文档与代码冲突时，以代码为准并立即修文档。
2. **CHANGELOG** 是历史事实；其他文档只保留「当前仍有效」的信息。
3. 版本号以 [app/main.py](../app/main.py) `FastAPI(version=...)` 为准（当前 `2.6.2`）。

## 四、维护规则

- 改代码必须自测，并在**同一个 commit** 更新受影响的文档；完成后用 `gh` 推送到 `origin/main`。详见 [AGENTS.md](../AGENTS.md) 与 [HANDOFF §12](HANDOFF.md)。
- 新增文档前先问：能否并入现有文档？只有「独立主题 + 长期维护」才新建文件。
- 历史版本信息只写进 [CHANGELOG.md](CHANGELOG.md)，不要再往 README / HANDOFF / PROJECT_STATE / ARCHITECTURE / DEPLOYMENT / DEVELOPMENT 顶部堆版本块。
- 提交前跑一次 Markdown 相对链接检查；链接一律写「从本文件出发」的相对路径。
