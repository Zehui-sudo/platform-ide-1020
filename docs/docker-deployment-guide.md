# Platform IDE Docker 部署步骤指南

本文档提供一份**逐步执行、可验证结果**的部署方案，目标是在 AWS Lightsail/EC2 等 Linux 主机上，通过 Docker 运行完整的 Platform IDE（Next.js 前端 + FastAPI 后端 + 代码沙箱 + Nginx）。

> **说明**：所有命令均以 `ubuntu` 用户为例，请根据实际环境调整路径与权限。若使用非 root 用户，注意为其配置 Docker 使用权限（加入 `docker` 用户组）。

---

## Step 0. 准备环境

- **操作**：
  1. 在主机上安装 Docker、Docker Compose（或 `docker compose` 插件）、Nginx、Git。
  2. 生成必要的 API Key，并写入 `config.json` 或环境变量。
- **命令**：
  ```bash
  sudo apt update && sudo apt install -y docker.io docker-compose-plugin nginx git
  sudo usermod -aG docker $USER   # 执行后需重新登录
  ```
- **验证**：重新登录后执行 `docker version`，确保无权限错误；`nginx -t` 输出 `syntax is ok`。

---

## Step 1. 拉取代码与配置

- **操作**：
  1. 克隆仓库到服务器，例如 `/opt/platform-ide`。
  2. 将本地调试过的 `config.json`、`nginx/local-dev.conf`、`.env` 等配置同步到服务器（生产环境请移除测试 Key）。
- **命令**：
  ```bash
  git clone https://https://github.com/Zehui-sudo/platform-ide-1020.git /opt/platform-ide
  cd /opt/platform-ide
  ```
- **验证**：`ls` 可看到 `web-learner/`、`scripts/`、`docker/` 等目录。

---

## Step 2. 构建代码执行沙箱镜像

- **操作**：
  1. 编辑 `docker/sandbox/requirements.base.txt`，加入需要的科学计算、机器学习、异步编程等 Python 库（工程已预置常用组合：NumPy、Pandas、scikit-learn、SciPy、Matplotlib、Seaborn、Requests、aiohttp、PyArrow 等）。
  2. 如需 GPU 或更大依赖，可在 `docker/sandbox/Dockerfile` 中替换基础镜像（例如 NVIDIA CUDA 版）并添加额外系统依赖。
  3. 在服务器本地构建镜像（或通过 CI/CD 推送到镜像仓库）。
- **命令**：
  ```bash
  docker build \
    -f docker/sandbox/Dockerfile \
    -t platform-ide-python-sandbox:latest \
    docker/sandbox
  ```
- **验证**：
  ```bash
  echo '{"code": "print(1+1)"}' | docker run --rm -i platform-ide-python-sandbox:latest
  ```
  输出应为 `{"status": "success", "stdout": "2\n", ...}`。如要验证科学计算库，可再执行：
  ```bash
  echo '{"code": "import numpy as np\nprint(np.arange(3))"}' | docker run --rm -i platform-ide-python-sandbox:latest
  ```
  应输出 `[0 1 2]`。

---

## Step 3. 创建 FastAPI 后端镜像

- **操作**：
  1. 在 `docker/backend/` 新建 `Dockerfile`（示例内容如下）。
  2. 同目录同步 `requirements.txt` 和项目代码。
- **示例 Dockerfile**（可直接复制粘贴到新文件中）：
  ```Dockerfile
  FROM python:3.11-slim

  ENV PYTHONUNBUFFERED=1 \
      PYTHONDONTWRITEBYTECODE=1

  WORKDIR /app

  COPY requirements.txt .
  RUN pip install --no-cache-dir -r requirements.txt

  COPY . .

  # 默认监听 8000 端口
  ENV SANDBOX_IMAGE=platform-ide-python-sandbox:latest
  CMD ["uvicorn", "scripts.api_server:app", "--host", "0.0.0.0", "--port", "8000"]
  ```
- **构建命令**（在仓库根目录执行）：
  ```bash
  docker build \
    -f docker/backend/Dockerfile \
    -t platform-ide-api:latest \
    .
  ```
- **验证**：
  ```bash
  docker run --rm -p 8000:8000 \
    -e SANDBOX_IMAGE=platform-ide-python-sandbox:latest \
    platform-ide-api:latest
  ```
  另开终端 `curl http://127.0.0.1:8000/`，应返回 `{"message":"Platform IDE Python API server is running"}`。

---

## Step 4. 创建 Next.js 前端镜像

- **操作**：
  1. 在 `docker/frontend/` 新建 `Dockerfile`（多阶段构建，第一阶段构建 Next.js 应用，第二阶段运行）。
  2. 根据需要设置 `NEXT_PUBLIC_BACKEND_URL`（例如 `https://your_domain`）。
- **示例 Dockerfile**：
  ```Dockerfile
  FROM node:20-bookworm AS builder
  WORKDIR /app

  COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
  COPY tsconfig.base.json ./
  COPY web-learner/package.json web-learner/
  RUN npm install -g pnpm && pnpm install

  COPY web-learner web-learner
  RUN pnpm --filter web-learner build

  FROM node:20-bookworm AS runner
  WORKDIR /app
  ENV NODE_ENV=production \
      NEXT_TELEMETRY_DISABLED=1

  COPY --from=builder /app/web-learner/.next ./web-learner/.next
  COPY --from=builder /app/web-learner/package.json ./web-learner/package.json
  COPY --from=builder /app/node_modules ./node_modules
  COPY web-learner/public ./web-learner/public

  EXPOSE 3000
  CMD ["pnpm", "--filter", "web-learner", "start"]
  ```
- **构建命令**：
  ```bash
  docker build \
    -f docker/frontend/Dockerfile \
    -t platform-ide-web:latest \
    .
  ```
- **验证**：
  ```bash
  docker run --rm -p 3000:3000 platform-ide-web:latest
  ```
  浏览器访问 `http://服务器IP:3000`，应看到学习平台首页（如需要 API 支持，请先启动后端容器）。

---

## Step 5. 编写 docker-compose.yml（推荐）

- **操作**：在仓库根目录创建 `docker-compose.yml`，统一管理三个服务与 Nginx。
- **示例**：
  ```yaml
  version: '3.9'
  services:
    sandbox:
      image: platform-ide-python-sandbox:latest
      container_name: python-sandbox
      restart: unless-stopped
      command: [ "sleep", "infinity" ]  # 仅用于预拉镜像，可省略

    api:
      image: platform-ide-api:latest
      container_name: platform-api
      restart: unless-stopped
      environment:
        SANDBOX_IMAGE: platform-ide-python-sandbox:latest
      volumes:
        - ./config.json:/app/config.json:ro
        - ./output:/app/output
      depends_on:
        - sandbox

    web:
      image: platform-ide-web:latest
      container_name: platform-web
      restart: unless-stopped
      environment:
        NEXT_PUBLIC_BACKEND_URL: ""
      depends_on:
        - api

    nginx:
      image: nginx:stable
      container_name: platform-nginx
      restart: unless-stopped
      volumes:
        - ./nginx/local-dev.conf:/etc/nginx/conf.d/platform.conf:ro
      ports:
        - "80:8080"
      depends_on:
        - web
        - api
  ```
- **验证**：
  ```bash
  docker compose up -d
  docker compose ps
  ```
  所有服务应处于 `Up` 状态。

---

## Step 6. 配置生产 Nginx

- **操作**：
  1. 将 `nginx/local-dev.conf` 复制为 `/etc/nginx/sites-available/platform-ide`。
  2. 根据域名修改 `server_name`、监听端口（80/443），并为 HTTPS 配置证书。
  3. 启用站点并重载 Nginx。
- **命令**：
  ```bash
  sudo ln -s /etc/nginx/sites-available/platform-ide /etc/nginx/sites-enabled/
  sudo nginx -t
  sudo systemctl reload nginx
  ```
- **验证**：浏览器访问 `http(s)://your_domain`，确保页面加载正常，控制台无 CORS 错误；访问 `/api/execute/run` 返回 JSON。

---

## Step 7. 健康检查与日志

- **健康检查**：
  - `curl http://localhost/api/outline/start`（配合 POST 数据）验证 LangGraph 流程。
  - `curl http://localhost/api/execute/run` 验证 Docker 沙箱。
  - 浏览器体验交互式代码块，看输出与错误提示是否正常。
- **日志查看**：
  ```bash
  docker compose logs -f api
  docker compose logs -f web
  docker compose logs -f nginx
  ```

---

## Step 8. 部署后的常见运维事项

- **镜像更新**：重新执行 `docker build`，再运行 `docker compose up -d --build` 滚动更新。
- **配置更新**：修改 `config.json` 或 `.env` 后，需要重启相关容器。
- **数据持久化**：确保 `output/`、`web-learner/public/content/` 等目录挂载到持久卷，避免容器销毁后丢失。
- **安全**：继续强化 Docker 运行参数（AppArmor seccomp、只读文件系统等），定期审查日志。

---

完成以上步骤，即可在 AWS 上以 Docker 方式运行 Platform IDE。如需进一步自动化（CI/CD、Kubernetes 部署等），可在此基础上继续扩展。祝部署顺利! 💪
