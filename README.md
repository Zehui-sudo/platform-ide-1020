# Platform IDE

Platform IDE 是一个「前端 Next.js + 后端 FastAPI」的交互式学习平台，并包含 VSCode 插件辅助学习体验。最新架构已经将 Python 流水线和代码执行能力后移到后端服务，前端只负责 UI 与 API 交互。

## 架构总览

- **web-learner/**：Next.js 15 应用，提供完整的学习流程、AI 辅助以及交互式代码练习界面。
- **scripts/**：FastAPI 后端端点，封装原有 Python LangGraph 流水线与章节生成脚本，并新增 `/api/execute/run` 代码执行服务。
- **docker/sandbox/**：用于构建 Python 沙箱镜像（基于 Docker），后端通过 `docker run` 执行代码，提供 CPU/内存/时间限制。
- **nginx/**：本地与生产共用的反向代理示例，将 `/api/(outline|content|execute)` 转发到 FastAPI，其他流量交给 Next.js。
- **learn-linker/**：VSCode 插件源码。

```
platform-ide/
├── docker/
│   └── sandbox/             # Python 沙箱镜像 Dockerfile 与 runner
├── docs/                    # 文档（API、部署指南等）
├── nginx/
│   └── local-dev.conf       # 本地 Nginx 路由示例
├── scripts/                 # FastAPI + 流水线脚本
├── web-learner/             # Next.js 前端
└── learn-linker/            # VSCode 扩展
```

## 技术栈

- **前端**：Next.js 15.4、Tailwind CSS、Radix UI、Zustand、CodeMirror、Vercel AI SDK
- **后端**：FastAPI、Uvicorn、LangGraph、OpenAI/Gemini/Kimi 等 LLM (读取 `config.json`)
- **代码执行**：Docker 沙箱镜像（Python 3.11），FastAPI 通过 `docker run` 调用
- **代理**：Nginx（本地/生产统一反代）
- **工具**：pnpm、Python 3.11、Docker、Node.js 18+

## 快速开始（本地开发）

### 1. 前置依赖

- Node.js 18+ 与 pnpm
- Python 3.11
- Docker Engine（macOS 可通过 Docker Desktop）
- Nginx（可选，本地代理使用 Homebrew 安装 `brew install nginx`）

### 2. 安装前端依赖

```bash
pnpm install
```

### 3. 准备 Python 虚拟环境 & 安装依赖

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 4. 构建代码执行沙箱镜像

```bash
docker build \
  -f docker/sandbox/Dockerfile \
  -t platform-ide-python-sandbox \
  docker/sandbox
```

（如需使用其他镜像名，可后续设置 `SANDBOX_IMAGE` 环境变量）

### 5. 启动 FastAPI 后端

```bash
source venv/bin/activate
uvicorn scripts.api_server:app --reload --port 8000
```

后端会提供：
- `/api/outline/*`：调用原 LangGraph 流水线生成大纲
- `/api/content/*`：生成章节内容
- `/api/execute/run`：Docker 沙箱中的 Python 代码执行

### 6. 启动 Next.js 前端

```bash
pnpm dev:web
```

开发阶段推荐配合 `nginx/local-dev.conf` 使用本地 Nginx，统一通过 `http://localhost:8080` 访问：

```nginx
# nginx/local-dev.conf（摘录）
location ~ ^/api/(outline|content|execute)/ {
    proxy_pass http://127.0.0.1:8000;
    proxy_http_version 1.1;
    proxy_set_header Connection '';
    proxy_buffering off;
}

location / {
    proxy_pass http://127.0.0.1:3000;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_cache_bypass $http_upgrade;
}
```

修改后执行 `sudo nginx -s reload`，浏览器访问 `http://localhost:8080` 即可体验完整功能。

### 7. 验证代码执行 API

```bash
curl -X POST http://127.0.0.1:8000/api/execute/run \
  -H 'Content-Type: application/json' \
  -d '{"language":"python","code":"print(\"hello from sandbox\")"}'
```

成功会返回标准 JSON（stdout/stderr/耗时/是否超时等）。

## 常用脚本

```bash
# 启动前端 + 后端（分别在不同终端执行）
pnpm dev:web
uvicorn scripts.api_server:app --reload --port 8000

# 构建前端
pnpm build:web

# VSCode 插件开发
pnpm dev:ext
```

## 功能特性概览

- 交互式学习路径、Markdown 章节与进度管理
- 支持 LangGraph 流程：教材推荐、大纲重构、章节生成
- 代码执行通过后端 Docker 沙箱完成，支持超时和资源限制
- Nginx 层统一转发 `/api/outline|content|execute` → FastAPI
- VSCode 插件 `learn-linker` 可同步 Web 端学习内容（后续集成用）

## 部署说明

- 完整的 Docker 化部署步骤详见 `docs/docker-deployment-guide.md`。
- 生产环境需：
  - 构建并推送前端、后端、沙箱三类镜像
  - 设置 `SANDBOX_IMAGE`、LLM API Key 等环境变量
  - 使用 Nginx/Load Balancer 统一转发
  - 准备持久化目录（如大纲输出、内容发布目录）
- 建议结合 `config.json` 管理 LLM Key，在服务器上通过环境变量覆盖敏感信息。

## 贡献指南

1. Fork 仓库并创建功能分支
2. 提交更改并运行必要的 lint/测试
3. 提交 Pull Request

## License

MIT
