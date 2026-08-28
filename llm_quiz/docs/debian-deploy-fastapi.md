# 在 Debian 上部署后端（FastAPI）与前端静态资源

本文档说明如何在 Debian 服务器上部署本项目的**后端 API**（FastAPI + uvicorn）与已经构建好的**前端静态资源**。
前端 `bun run build` 的产物会输出到 `backend/app/static/`，由 FastAPI 直接托管，因此 Debian 上只需跑一个服务进程即可同时提供 API 和页面资源。

> 前提：本仓库没有模块级机密依赖，仅需要 Python、bun（前端构建）与网络访问 LLM。

---

## 1. 两个组成部分

| 部分 | 技术栈 | 部署方式 |
|------|--------|----------|
| 后端 API | FastAPI + SQLAlchemy(aio sqlite) + uvicorn | 常驻进程（systemd）监听 `0.0.0.0:8070` |
| 前端页面 | React Router v8（SSR 构建）| `bun run build` 产物复制进 `backend/app/static/`，由 FastAPI 以静态文件对外提供 |

- 后端入口：`backend/main.py`，对象 `app`（命令里用 `uvicorn main:app`）。
- 前端产物目录：`backend/app/static/`（JS/CSS/favicon）。
- SQLite 数据库：默认 `backend/data/quizzes.db`（由 `DB_PATH` 环境变量，相对当前工作目录解析——**运行 uvicorn 时须在 backend 目录里**）。

### 关于 SSR 与“纯静态”的说明（重要）

本项目前端当前为 **SPA 模式**（`frontend/react-router.config.ts` 中 `ssr: false`）。构建会产出
一个真正的 `index.html`（连同 `assets/*.js/.css` 与 `favicon.ico`）放在 `build/client/`，
由 FastAPI 直接托管，无需 node 端渲染进程。

当前即为本文档对应的**纯静态方案**：`ssr: false` 使 `backend/app/static/` 生成 `index.html`，
FastAPI 的 `StaticFiles(html=True)` 在 `/` 返回页面，前端 SPA 路由（`/quizzes` 等）正常工作。
若日后改回 SSR（`ssr: true`），静态目录只会剩 JS/CSS，页面需由 node 端 `build/server` 渲染、另行配置反代。

---

## 2. 环境准备

### 2.1 系统依赖

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip git unzip curl
# 若用 bun 安装脚本（见下）已自带，可省略单独安装 node
```

### 2.2 安装 bun（仅构建前端时需要）

```bash
curl -fsSL https://bun.sh/install | bash
export PATH="$HOME/.bun/bin:$PATH"
bun --version
```

---

## 3. 拉取代码

```bash
sudo mkdir -p /srv/app
sudo chown "$USER" /srv/app
git clone <你的仓库> /srv/app/language_learning_quiz
cd /srv/app/language_learning_quiz
```

---

## 4. 后端：Python 虚拟环境 + 依赖

```bash
cd /srv/app/language_learning_quiz/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

> 依赖见 `pyproject.toml`（fastapi、uvicorn[standard]、pydantic、httpx、sqlalchemy、aiosqlite、openai、fugashi、unidic-lite）。

### 校验启动（快速冒烟）

```bash
uvicorn main:app --host 127.0.0.1 --port 8070
curl -s http://127.0.0.1:8070/health        # → {"status":"ok"}
```

---

## 5. 前端：构建并输出到 backend/app/static

在**开发机**或**服务器本机**执行均可（产物随部署一起拷贝最简）。

```bash
cd /srv/app/language_learning_quiz/frontend
bun install
bun run build        # 构建并复制到 ../backend/app/static/
```

`bun run build` 的执行内容见 `package.json`：
`react-router build` 后执行 `node scripts/build-static.mjs`，用 Node `fs` 跨平台地把 `build/client` 复制到 `../backend/app/static/`。
产物结构大致为：

```
backend/app/static/
├── assets/            # 打包后的 JS / CSS
└── favicon.ico
```

> 若切 SPA 模式（见 §1），此处还应有 `index.html`。

---

## 6. 配置环境变量

后端从环境变量读取 LLM 配置（见 `backend/app/config.py`）。在服务启动前导出，或在 systemd 的 `Environment=` 里配置：

| 变量 | 说明 | 默认 |
|------|------|------|
| `LLM_API_KEY` | LLM 密钥 | 空 |
| `LLM_BASE_URL` | LLM 服务商 base url（SDK 会自动拼接接口路径，**不要**自己追加 `/chat/completions`）| `https://api.openai.com/v1` |
| `LLM_MODEL` | 模型名 | `gpt-4o-mini` |
| `LLM_TIMEOUT` | 请求超时秒数 | `60` |
| `LLM_JSON_MODE` | 是否强制 JSON 输出 | `true` |
| `DB_PATH` | SQLite 路径（相对运行目录）| `data/quizzes.db` |

> 首次启动会自动建表（`init_db`）并写入语言/提示词模板；无需手工建库。

---

## 7. 以 systemd 常驻运行

创建服务文件 `/etc/systemd/system/quiz.service`：

```ini
[Unit]
Description=Language Learning Quiz Service (FastAPI)
After=network.target

[Service]
WorkingDirectory=/srv/app/language_learning_quiz/backend
User=www-data
Group=www-data
ExecStart=/srv/app/language_learning_quiz/backend/.venv/bin/uvicorn main:app --host 0.0.0.0 --port 8070 --workers 2
Restart=on-failure
Environment=LLM_API_KEY=<你的 key>
Environment=LLM_BASE_URL=https://api.openai.com/v1
Environment=LLM_MODEL=gpt-4o-mini
Environment=LLM_TIMEOUT=60

[Install]
WantedBy=multi-user.target
```

> 让 `www-data` 可读写 `backend/data/`：`sudo chown -R www-data:www-data /srv/app/language_learning_quiz/backend/data`。

启用并启动：

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now quiz
sudo systemctl status quiz
journalctl -u quiz -f          # 查看日志
```

---

## 8. （可选）前置 nginx 反向代理

若想用 80/443 + 域名，nginx 反代到 8070，并透传 `/api`：

```
# /etc/nginx/sites-available/quiz
server {
    listen 80;
    server_name quiz.example.com;

    location / {
        proxy_pass http://127.0.0.1:8070;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/quiz /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

---

## 9. 验证

```bash
curl -s http://<服务器IP>:8070/health                         # {"status":"ok"}
curl -s "http://<服务器IP>:8070/api/languages"                 # 语言列表
curl -s http://<服务器IP>:8070/assets/                        # 静态资源目录（SPA 模式下为 index.html）
```

---

## 10. 更新部署（滚动发布）

```bash
cd /srv/app/language_learning_quiz
git pull
cd backend && source .venv/bin/activate && pip install -e .
cd ../frontend && bun install && bun run build
sudo systemctl restart quiz
```

> 若后端改了数据库 schema 导致表结构不兼容，因项目采用 `create_all`（不改已有表），需先备份并删除 `backend/data/quizzes.db` 让其在启动时重建。