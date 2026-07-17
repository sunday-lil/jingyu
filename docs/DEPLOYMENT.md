# 部署指南

> 三种部署方式：**宝塔面板**（最简单，私人项目首选）、**systemd**（VPS 标准）、**手动 nohup**（临时调试）。

> 🔒 **改了本文件涉及的部署配置（端口 / Nginx / systemd / HTTPS / 反代），必须同步更新**：[README §1](../../README.md) / [HANDOFF §1](../../HANDOFF.md) / [PROJECT_STATE §4](../PROJECT_STATE.md)。详见 [HANDOFF §12](../../HANDOFF.md) 文档自动同步铁律。

---

## 方式 1：宝塔面板（推荐 ⭐）

宝塔自带 Python 项目管理器，省心。

### 1.1 准备工作

- 一台装了宝塔的 Linux 服务器（CentOS / Ubuntu / Debian）
- 宝塔后台：软件商店 → 安装 **「Python 项目管理器」**（一般自带 Python 3.8-3.12）
- 解析好的域名（可选，没域名直接用 IP）

### 1.2 上传代码

方式 A（推荐）：用宝塔「文件」直接上传 zip，解压到 `/www/wwwroot/healing/`

方式 B：用 git
```bash
cd /www/wwwroot/
git clone <your-repo-url> healing
```

### 1.3 创建项目

宝塔后台 → Python 项目 → 「添加项目」：

| 字段 | 填什么 |
|---|---|
| 项目类型 | Python |
| 项目路径 | `/www/wwwroot/healing` |
| 项目名称 | `healing` |
| Python 版本 | 3.11+ |
| 启动方式 | **自定义命令**（见下） |
| 启动命令 | `python start.py` |
| 停止命令 | `python start.py stop` |
| 端口 | 5000 |

**为什么用自定义命令**：
- 宝塔默认用 `gunicorn`，但本项目**没有** gunicorn 依赖
- 我们用自研的 [start.py](../../start.py)，自带 PID / 日志 / 重启

### 1.4 配置 .env

SSH 到服务器：
```bash
cd /www/wwwroot/healing
cp .env.example .env
vi .env   # 改这几行：
```

```env
QI_SECRET_KEY=<用 python -c "import secrets; print(secrets.token_hex(32))" 生成>
QI_HOST=0.0.0.0
QI_PORT=5000
QI_DEBUG=false
# AI 接入（可选）：不配置也能跑，4 个 AI 端点会优雅降级返回治愈系提示
# QI_NVIDIA_API_KEY=nvapi-xxxxx
# QI_AI_MODEL=meta/llama-3.1-8b-instruct
# QI_AI_BASE_URL=https://integrate.api.nvidia.com/v1
# 详见下方「AI 接入（可选）」章节
```

### 1.5 安装依赖

SSH：
```bash
cd /www/wwwroot/healing
python3 -m pip install -r requirements.txt
```

或直接在宝塔「项目」页面点「一键依赖」。

### 1.6 启动

宝塔后台 → 项目 → 「启动」。

或 SSH：
```bash
cd /www/wwwroot/healing
python start.py
```

应该看到：
```
[START] 后台启动 -> http://0.0.0.0:5000
   日志文件 : /www/wwwroot/healing/logs/healing.log
   PID 文件 : /www/wwwroot/healing/run/healing.pid
[OK] 启动成功（PID 12345）
   首页     http://0.0.0.0:5000
   API 文档 http://0.0.0.0:5000/docs
```

### 1.7 反向代理（让外网能访问）

宝塔 → 网站 → 添加站点（PHP 静态就行）→ 站点的「设置」→「反向代理」：

| 字段 | 填什么 |
|---|---|
| 代理名称 | healing |
| 目标 URL | `http://127.0.0.1:5000` |
| 发送域名 | `$host` |

提交后，访问 `http://你的域名/` 就走 Nginx → Python 服务。

### 1.8 HTTPS（强烈推荐）

宝塔站点 → 「SSL」 → 选「Let's Encrypt」 → 申请 → 开启强制 HTTPS。

**完事。** 用户访问 `https://你的域名/` 就是你的应用。

### 1.9 日常维护

| 任务 | 命令 |
|---|---|
| 看服务状态 | SSH 跑 `python start.py status` |
| 看日志 | `tail -f logs/healing.log` |
| 重启服务 | `python start.py restart` |
| 备份数据库 | `cp data/healing.db backup/healing-$(date +%Y%m%d).db` |
| 更新代码 | `git pull && python start.py restart` |

> 🔒 **改了部署相关配置（端口 / Nginx / systemd / HTTPS）必须同步更新**：[README §1](../../README.md) / [HANDOFF §1](../../HANDOFF.md) / 本文件对应章节。改代码不改文档 = 改了一半（详见 [HANDOFF §12](../../HANDOFF.md)）。

---

## 方式 2：systemd（VPS 标准做法）

适合纯 Linux VPS，没有宝塔。

### 2.1 准备

```bash
# 1. 安装 Python 3.11+
sudo apt update && sudo apt install python3.11 python3.11-venv python3-pip
# 或 CentOS:
# sudo yum install python311 python311-pip

# 2. 创建用户（不推荐用 root 跑）
sudo useradd -m -s /bin/bash healing
```

### 2.2 部署代码

```bash
sudo -iu healing
mkdir -p /home/healing/app
cd /home/healing/app
git clone <your-repo> .
# 或 scp 上传
```

### 2.3 安装依赖

```bash
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2.4 配置 .env

```bash
cp .env.example .env
vi .env
# 修改 QI_SECRET_KEY, QI_HOST=0.0.0.0, QI_DEBUG=false
# 可选：AI 接入（不配置也能跑，4 个端点会优雅降级）
#   QI_NVIDIA_API_KEY=nvapi-xxxxx
#   QI_AI_MODEL=meta/llama-3.1-8b-instruct
#   QI_AI_BASE_URL=https://integrate.api.nvidia.com/v1
#   详见下方「AI 接入（可选）」章节
```

### 2.5 写入 systemd unit

`/etc/systemd/system/healing.service`：

```ini
[Unit]
Description=Healing Platform (FastAPI)
After=network.target

[Service]
Type=simple
User=healing
Group=healing
WorkingDirectory=/home/healing/app
Environment="PATH=/home/healing/app/venv/bin"
Environment="QI_HOST=0.0.0.0"
Environment="QI_PORT=5000"
Environment="QI_DEBUG=false"
# 用 systemd 管，start.py 跑前台（fg 子命令）
ExecStart=/home/healing/app/venv/bin/python start.py fg
Restart=always
RestartSec=5
StandardOutput=append:/home/healing/app/logs/healing.log
StandardError=append:/home/healing/app/logs/healing.log

[Install]
WantedBy=multi-user.target
```

启用：
```bash
sudo systemctl daemon-reload
sudo systemctl enable healing
sudo systemctl start healing
sudo systemctl status healing
```

**注意**：systemd 模式下 `start.py` 用 `fg`（前台运行），systemd 负责进程管理 + 自动重启 + 日志收集。

### 2.6 Nginx 反代

`/etc/nginx/sites-available/healing`：

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    # 客户端真实 IP
    real_ip_header X-Real-IP;
    set_real_ip_from 127.0.0.1;

    # 静态资源（FastAPI 也能服务，但 Nginx 缓存更专业）
    location /static/ {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        expires 7d;
        add_header Cache-Control "public, immutable";
        # ⚠️ 改动 CSS / JS 后（如 05-animations.css、app.js），由于 expires 7d + immutable，
        # 老用户浏览器会一直用旧缓存。建议发版后：
        #   1) 改 style.css / base.html 里的查询串版本号（如 ?v=20260715），或
        #   2) 临时 `sudo nginx -s reload` + 让用户硬刷新（Ctrl+Shift+R）一次。
    }

    # API + 页面
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

启用：
```bash
sudo ln -s /etc/nginx/sites-available/healing /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 2.7 HTTPS（Let's Encrypt）

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com
```

自动续期（certbot 自带）。

### 2.8 防火墙

```bash
# UFW (Ubuntu)
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow OpenSSH

# firewall-cmd (CentOS)
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```

**完事。**

### 2.9 日常维护

```bash
sudo systemctl status healing         # 状态
sudo systemctl restart healing        # 重启
sudo journalctl -u healing -f        # 日志（systemd 自带）
tail -f /home/healing/app/logs/healing.log   # 业务日志
```

> 🔒 **改了 systemd unit / Nginx 配置 / 端口** → 必须同步更新 [README §1](../../README.md) / [HANDOFF §1](../../HANDOFF.md) / 本文件对应章节（详见 [HANDOFF §12](../../HANDOFF.md)）。

---

## 方式 3：手动 nohup（临时调试）

```bash
cd /path/to/healing
nohup python start.py > logs/manual.log 2>&1 &
echo $! > run/manual.pid
```

或用 start.py 的后台模式（自带 PID / 日志）：
```bash
python start.py start
```

**生产不要用**。进程没守护，挂了不会自动重启。

---

## 部署后验证清单

部署完成后**必须**跑一遍：

```bash
# 1. 服务在跑
curl -I http://127.0.0.1:5000/                        # 200

# 2. 静态资源
curl -I http://127.0.0.1:5000/static/css/style.css    # 200
curl -I http://127.0.0.1:5000/static/audio/gong.mp3   # 200

# 3. 公开 API
curl http://127.0.0.1:5000/api/music | head           # 16 首曲
curl http://127.0.0.1:5000/api/garden/shop | head     # 11 件商品

# 4. 注册一个测试账号
curl -X POST http://127.0.0.1:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"nickname":"smoketest","password":"test123456"}'
# 应返回 201

# 5. （可选）用浏览器访问
# http://yourdomain.com
# 注册 → 听歌 → 写日记 → 打卡 → 兑换
```

**全部通过 = 部署完成。**

---

## AI 接入（可选，2026-07-17 加）

> **本节是可选功能**。不配置 AI 也能跑，4 个 AI 端点会优雅降级返回治愈系友好提示，业务不中断。详见 [ARCHITECTURE §6.6](../ARCHITECTURE.md) / [HANDOFF §5.7](../../HANDOFF.md)。

### 是什么

静屿 4 个场景接入 NVIDIA NIM API（OpenAI 兼容格式），模型 `meta/llama-3.1-8b-instruct`（8B 小模型，响应快；原默认 `nvidia/llama-3.1-nemotron-70b-instruct` 在用户 NVIDIA 账户下 404 不可用，详见 [HANDOFF §5.7](../../HANDOFF.md)）：

| 场景 | 端点 | 入口 |
|---|---|---|
| AI 树洞对话 | `POST /api/ai/chat` | `/ai-chat`（需登录） |
| 漂流瓶 AI 鼓励语 | `POST /api/ai/encouragement` | `/pick` 拾瓶后 |
| 情绪日历 AI 治愈语 | `POST /api/ai/healing` | `/mood-calendar` 打卡后 |
| 音乐 AI 心情推荐 | `POST /api/ai/recommend-music` | 首页 `/` 「AI 帮我选音」卡片 |

### 配置 3 个环境变量

获取 NVIDIA 免费 API key：访问 [build.nvidia.com](https://build.nvidia.com) → 注册 → 在 `meta/llama-3.1-8b-instruct` 模型页生成 key（格式 `nvapi-xxxxx`）。

在 `.env` 加入（或取消注释 [.env.example](../../.env.example) 末尾的对应行）：

```env
# NVIDIA NIM API（OpenAI 兼容格式）
QI_NVIDIA_API_KEY=nvapi-你的真实key
QI_AI_MODEL=meta/llama-3.1-8b-instruct
QI_AI_BASE_URL=https://integrate.api.nvidia.com/v1
```

**3 个变量说明**：

| 变量 | 必填？ | 默认值 | 说明 |
|---|---|---|---|
| `QI_NVIDIA_API_KEY` | 否 | 空 | NVIDIA NIM API 的 key，`nvapi-` 开头；**留空时 4 个 AI 端点自动降级**返回 `available:false` + 治愈系提示 |
| `QI_AI_MODEL` | 否 | `meta/llama-3.1-8b-instruct` | 模型名，OpenAI 兼容格式。换其他 NVIDIA NIM 模型只改这里 |
| `QI_AI_BASE_URL` | 否 | `https://integrate.api.nvidia.com/v1` | API base URL，换其他厂商（DeepSeek / 智谱 / 自部署 vLLM）只改这里 |

### 重启 + 验证

```bash
# 重启
python start.py restart    # 或 sudo systemctl restart healing

# 验证 1：不配 key 时降级正常（默认状态）
# 应返回 200 + {available:false, message:"治愈系友好提示"}
curl -b c.txt -X POST http://127.0.0.1:5000/api/ai/healing \
  -H "Content-Type: application/json" \
  -d '{"mood_emoji":"calm"}'
# 注意：c.txt 是登录后的 cookie 文件，参考「部署后验证清单」注册流程

# 验证 2：配 key 后 AI 正常返回
# 编辑 .env 加入 3 个变量 → 重启 → 再调一次
# 应返回 200 + {available:true, message:"<AI 生成的治愈语>"}
```

### 网络要求

- 出站访问 `https://integrate.api.nvidia.com`（443）— 服务器防火墙需放行
- 超时设置：[app/services/ai_service.py](../../app/services/ai_service.py) `_call_nvidia()` 默认 **60 秒**（8B 模型实际 1-10s，60s 纯兜底）
- 调用失败（网络/超时/限流/4xx/5xx）→ 端点返回 200 + `available:false` + 治愈系提示，**不报 500**
- **前端字体**：模板通过 `fonts.loli.net` / `gstatic.loli.net`（Google Fonts 国内镜像）加载 Noto Sans/Serif SC，国内可访问；如完全离线部署（不允许任何出站），CSS 变量 `--font-sans` / `--font-serif` 有 `"PingFang SC", "Microsoft YaHei"` 等系统字体兜底，不影响功能

### 成本

- NVIDIA 提供**免费** API key，符合本项目「非商业纯治愈」调性
- 限流策略由 NVIDIA 控制，本项目不主动限流；命中限流时自动降级，用户无感知

### 隐私承诺

| 场景 | 发给 NVIDIA 的内容 | 入库？ |
|---|---|---|
| AI 树洞对话 | 用户对话文本 + 多轮历史 | ❌ 不入库，历史只在浏览器内存 |
| 漂流瓶 AI 鼓励语 | 作者日记**前 120 字**预览 | ❌ 文案不入库，明文不留存 |
| 情绪日历 AI 治愈语 | 心情 emoji + 可选 note | ❌ 不入库 |
| 音乐 AI 心情推荐 | 用户描述的状态文本 | ❌ 不入库 |

**API key 不入仓**：`.env` 已在 `.gitignore` 里，[.env.example](../../.env.example) 只放注释掉的占位。

**完全离线方案**：不配 `QI_NVIDIA_API_KEY` → 4 个端点自动降级 → 业务正常跑（仅少 AI 文案）。适合内网部署 / 不允许数据出站的环境。

---

## 备份与恢复

### 备份

```bash
# 数据库（最重要）
cp data/healing.db backup/healing-$(date +%Y%m%d-%H%M).db

# 用户上传（如果有，将来加）
tar czf backup/static-$(date +%Y%m%d).tar.gz static/

# 加密盐（已含在数据库里，不用单独备份）
```

**强烈建议**：每天 cron 备份一次：

```bash
# /etc/cron.daily/healing-backup
0 3 * * * healing cd /home/healing/app && cp data/healing.db /home/healing/backup/healing-$(date +\%Y\%m\%d).db
```

### 恢复

```bash
# 1. 停服务
python start.py stop

# 2. 覆盖数据库
cp backup/healing-20260714.db data/healing.db

# 3. 启动
python start.py
```

**注意**：用户密码和日记加密盐都在 DB 里，备份 = 备份了所有用户的所有数据。**加密文件妥善保管**。

---

## 监控（可选）

### 简单方案：宝塔自带监控

宝塔后台 → 监控 → 启用 CPU / 内存 / 磁盘告警。

### 进阶：uptime 检查

注册一个免费服务如 [UptimeRobot](https://uptimerobot.com/)，监控 `http://yourdomain.com/`，挂了发邮件 / 微信。

---

## 扩容（用户增长后）

### 阶段 1（0-1000 用户）：单服务器

当前架构完全够用。

### 阶段 2（1000-10 000 用户）：加 worker

```bash
# /etc/systemd/system/healing.service
ExecStart=/home/healing/app/venv/bin/python -m uvicorn app.main:app \
  --host 0.0.0.0 --port 5000 --workers 4
```

SQLite 换 MySQL：
```env
QI_DATABASE_URL=mysql+pymysql://user:pw@localhost:3306/healing?charset=utf8mb4
```

### 阶段 3（10 000+ 用户）：分离

- 应用服务器 × N（gunicorn + uvicorn workers）
- MySQL 主从
- Redis 缓存 + session
- 对象存储（音频文件）

**当前不需要做**。等真到了再处理。

---

## 故障排查

### 服务起不来

```bash
# 1. 看日志
tail -50 logs/healing.log

# 常见错误:
# - ModuleNotFoundError → pip install -r requirements.txt
# - PermissionError → chown -R healing:healing /home/healing/app
# - Address already in use → 别的进程占着 5000 端口，lsof -i :5000 查
```

### 502 Bad Gateway

```bash
# 1. uvicorn 没起
sudo systemctl status healing
# 2. Nginx 配置错
sudo nginx -t
# 3. 端口不通
curl -I http://127.0.0.1:5000/   # 应该 200
```

### 数据库锁死（SQLite）

```bash
# 1. 找长事务
lsof data/healing.db
# 2. 重启服务（最暴力也最有效）
python start.py restart
# 3. 长期方案：换 MySQL
```

### 静态资源 404

```bash
# 检查 static 目录
ls -la static/css/ static/js/ static/audio/
# 重启服务（init 阶段会确保目录存在）
python start.py restart
```

---

## 安全清单

部署前确认：

- [ ] `.env` 里 `QI_SECRET_KEY` 已改为随机长字符串
- [ ] `.env` 里 `QI_DEBUG=false`
- [ ] `.env` 文件**不**在 git 仓库里（.gitignore 已配）
- [ ] 数据库文件**不**暴露到公网（Nginx 不代理 `/data/` 路径）
- [ ] 服务器 SSH 用密钥登录，禁密码
- [ ] 服务器防火墙只开 80 / 443 / SSH
- [ ] HTTPS 已配置（Let's Encrypt）
- [ ] 数据库定期备份到异地
- [ ] 宝塔面板改默认端口 + 强密码

**完事。** 静屿已正式上线。🌿
