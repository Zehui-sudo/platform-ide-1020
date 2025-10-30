# Platform IDE 使用 PM2 的云端部署指南

本文档面向需要在 **Linux (Ubuntu/Debian)** 服务器上用 **PM2** 管理 Platform IDE 前后端进程的场景，步骤覆盖环境准备、服务启动、反向代理与自启配置。每个步骤说明 **做什么、为什么做、怎么做、如何验证**。

---

## Step 0. 以 `sudo` 权限登录服务器
- **做什么**：使用 SSH 登录云服务器。
- **为什么**：后续需要安装系统包、配置 Docker，需要 sudo。
- **怎么做**：
  ```bash
  ssh ubuntu@your_server_ip
  sudo -i   # 如需切换 root
  ```
- **验证**：`whoami` 输出 `root` 或属于 sudo 组的普通用户。

---

## Step 1. 安装系统依赖 (Node/Python/Docker)
- **做什么**：安装 Node.js 20 LTS、pnpm、Python 3.11 与 Docker。
- **为什么**：Next.js 前端依赖 Node/pnpm；FastAPI 后端与沙箱构建依赖 Python 与 Docker。
- **怎么做**：
  ```bash
  # 1. 系统更新
  sudo apt update && sudo apt upgrade -y

  # 2. 安装构建工具
  sudo apt install -y build-essential curl git python3.11 python3.11-venv python3-pip

  # 3. 安装 Node.js 20（NodeSource）
  curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
  sudo apt install -y nodejs

  # 4. 启用 pnpm（使用 corepack）
  sudo corepack enable
  sudo corepack prepare pnpm@9.12.0 --activate

  # 5. 安装 Docker
  sudo apt install -y docker.io docker-compose-plugin
  sudo systemctl enable --now docker
  sudo usermod -aG docker $USER  # 加入 docker 组，重新登录生效
  ```
- **验证**：
  ```bash
  node -v        # 应输出 v20.x.x
  pnpm -v        # 应输出 9.x
  python3.11 --version
  docker info    # 无权限错误且能列出 docker 信息
  ```

> **低内存主机提示**：若服务器内存 ≤ 1GB，建议提前创建至少 2GB 的 swap，以避免后续构建 Next.js 时报 OOM。

```bash
# 示例：创建 2GB 交换分区
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

验证：`free -h` 中 Swap 一列应显示新增容量。

---

## Step 2. 拉取代码仓库 & 准备配置
- **做什么**：下载项目代码，准备 `config.json`、`.env` 等配置。
- **为什么**：部署需要完整代码与合法的 API key。
- **怎么做**：
  ```bash
  cd /opt
  sudo git clone https://github.com/Zehui-sudo/platform-ide-1020.git platform-ide
  sudo chown -R $USER:$USER platform-ide
  cd platform-ide

  # 拷贝/上传本地调试过的配置文件
  cp config.example.json config.json
  # 根据需要编辑 config.json，填入 LLM key、模型、输出目录等
  ```
- **验证**：`ls` 能看到 `web-learner/`, `scripts/`, `config.json`。

---

## Step 3. Python 虚拟环境与后端依赖
- **做什么**：为 FastAPI 后端创建虚拟环境并安装依赖。
- **为什么**：保持系统 Python 干净，避免依赖冲突。
- **怎么做**：
  ```bash
  python3.11 -m venv venv
  source venv/bin/activate
  pip install --upgrade pip
  pip install -r requirements.txt
  ```
- **验证**：`which python` 指向 `/opt/platform-ide/venv/bin/python`；`pip list` 可看到 fastapi、uvicorn 等包。

---

## Step 4. 构建代码沙箱 Docker 镜像
- **做什么**：构建 `platform-ide-python-sandbox:latest`。
- **为什么**：后端 `/api/execute/run` 需要该镜像运行代码。
- **怎么做**：
  ```bash
  docker build -f docker/sandbox/Dockerfile -t platform-ide-python-sandbox:latest docker/sandbox
  ```
- **验证**：
  ```bash
  echo '{"code":"print(1+1)"}' | docker run --rm -i platform-ide-python-sandbox:latest
  # 期望输出 stdout 为 2
  ```

---

## Step 5. 构建前端产物
- **做什么**：安装依赖并构建 Next.js 前端。
- **为什么**：线上环境用 `next start` 提供生产构建。
- **怎么做**：
  ```bash
  pnpm install
  pnpm --filter @platform-ide/web-learner build
  ```
- **低内存提示**：如果构建阶段仍出现 OOM，可暂时设置 `NODE_OPTIONS=--max-old-space-size=512` 减少单进程占用：
  ```bash
  NODE_OPTIONS=--max-old-space-size=2048 pnpm --filter @platform-ide/web-learner build
  ```
- **验证**：`web-learner/.next` 目录出现；命令输出无错误。

---

## Step 6. 准备 PM2 进程配置
- **做什么**：编写 `ecosystem.config.js` 管理后端和前端进程。
- **为什么**：PM2 能统一管理、重启、开机自启服务。
- **怎么做**：在项目根目录创建 `pm2/ecosystem.config.js`（可按需调整路径）：
  ```javascript
  module.exports = {
    apps: [
      {
        name: 'platform-api',
        script: 'uvicorn',
        cwd: '/opt/platform-ide',
        interpreter: '/opt/platform-ide/venv/bin/python',
        args: 'scripts.api_server:app --host 0.0.0.0 --port 8000',
        env: {
          PYTHONUNBUFFERED: '1',
          SANDBOX_IMAGE: 'platform-ide-python-sandbox:latest',
          CONFIG_PATH: '/opt/platform-ide/config.json'
        }
      },
      {
        name: 'platform-web',
        cwd: '/opt/platform-ide',
        script: 'pnpm',
        args: '--filter @platform-ide/web-learner start',
        env: {
          NODE_ENV: 'production',
          NEXT_PUBLIC_BACKEND_URL: 'https://your-domain-or-ip',
          OPENAI_API_KEY: '',
          GEMINI_API_KEY: '',
          DEEPSEEK_API_KEY: ''
        }
      }
    ]
  };
  ```
- **验证**：`node -c pm2/ecosystem.config.js` 无语法错误；`cat` 文件检查路径与环境变量设置正确。

---

## Step 7. 使用 PM2 启动服务
- **做什么**：启动 FastAPI 与 Next.js。
- **为什么**：让后端监听 `8000`，前端监听 `3000`。
- **怎么做**：
  ```bash
  pm2 start pm2/ecosystem.config.js
  pm2 status
  ```
- **验证**：
  - `pm2 status` 显示 `platform-api`、`platform-web` 为 `online`。
  - `curl http://127.0.0.1:8000/` 返回 `{"message":"Platform IDE Python API server is running"}`。
  - `curl -H "Content-Type: application/json" -d '{"code":"print(40+2)"}' http://127.0.0.1:8000/api/execute/run` 返回成功 JSON。
  - `curl -I http://127.0.0.1:3000/` 返回 `200 OK`。

---

## Step 8. 配置 Nginx 反向代理
- **做什么**：把 80/443 请求转发到 PM2 管理的前后端。
- **为什么**：统一域名、提供 HTTPS、解决跨域。
- **怎么做**：创建 `/etc/nginx/sites-available/platform-ide`（示例）：
  ```nginx
  server {
      listen 80;
      server_name your.domain.com;

      location ~ ^/api/(outline|content|execute)/ {
          proxy_pass http://127.0.0.1:8000;
          proxy_set_header Host $host;
          proxy_set_header X-Real-IP $remote_addr;
          proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
          proxy_set_header X-Forwarded-Proto $scheme;
          proxy_http_version 1.1;
          proxy_set_header Connection '';
          proxy_buffering off;
      }

      location /api/ {
          proxy_pass http://127.0.0.1:3000;
          proxy_http_version 1.1;
          proxy_set_header Upgrade $http_upgrade;
          proxy_set_header Connection 'upgrade';
          proxy_set_header Host $host;
      }

      location / {
          proxy_pass http://127.0.0.1:3000;
          proxy_http_version 1.1;
          proxy_set_header Upgrade $http_upgrade;
          proxy_set_header Connection 'upgrade';
          proxy_set_header Host $host;
      }
  }
  ```
  ```bash
  sudo ln -s /etc/nginx/sites-available/platform-ide /etc/nginx/sites-enabled/
  sudo nginx -t
  sudo systemctl reload nginx
  ```
- **验证**：`curl http://your.domain.com/` 返回首页 HTML；浏览器访问无 404/500；`sudo nginx -t` 输出 `syntax is ok`。

---

## Step 9. 配置 PM2 开机自启与日志
- **做什么**：保存进程列表，并让 PM2 随系统启动。
- **为什么**：服务器重启后自动拉起服务。
- **怎么做**：
  ```bash
  pm2 save
  pm2 startup systemd
  # 按命令提示执行 sudo 命令，例如：
  # sudo env PATH=$PATH:/usr/bin pm2 startup systemd -u ubuntu --hp /home/ubuntu
  ```
- **验证**：
  - `systemctl status pm2-$USER` 显示 `active (running)`。
  - 重启服务器 `sudo reboot` 后，通过 `pm2 status` 确认两个进程重新上线。
  - 使用 `pm2 logs platform-api`/`platform-web` 查看实时日志。

---

## Step 10. 持久化输出目录与监控
- **做什么**：确保 `output/` 等目录存在并有写权限，配置监控。
- **为什么**：生成的教材、日志需要持久化；便于自行备份和观测。
- **怎么做**：
  ```bash
  mkdir -p /opt/platform-ide/output
  chown $USER:$USER /opt/platform-ide/output
  ```
  - 若要对接 Prometheus/Grafana，可在 PM2 中启用 `pm2 monit` 或额外采集。
- **验证**：
  - 运行一次大纲/内容生成后检查 `/opt/platform-ide/output` 确认文件生成。
  - `pm2 monit` 能看到 CPU/内存走势。

---

## 常见问题排查
- **API key 缺失**：前端 `AIChatSidebar` 使用 `process.env.*` 环境变量，需在 PM2 `env` 或 `.env` 中填写。
- **Docker 权限错误**：后端需要访问 `docker.sock` 才能启动沙箱；确认用户加入 docker 组且 `sudo systemctl status docker` 为 running。
- **端口占用**：若 `3000/8000` 被占用，可在 PM2 args 和 Nginx 配置中同步调整端口。
- **依赖未更新**：代码拉取新版本后需重新执行 `pnpm install` / `pnpm build` / `pm2 restart`。

---

完成以上步骤后，Platform IDE 即可通过 PM2 在 Linux 上稳定运行。如需进一步自动化，可结合 Ansible/CI/CD 将上述步骤脚本化。祝部署顺利 🚀
