# Platform IDE 运维命令速查

按照生产部署流程整理的常用命令，默认工作目录为 `/opt/platform-ide`。

## 进程管理（PM2）
- 查看状态：`pm2 status`
- 启动全部：`pm2 start pm2/ecosystem.config.js`
- 重启单个：`pm2 restart platform-api` / `pm2 restart platform-web`
- 平滑重载：`pm2 reload all`
- 停止服务：`pm2 stop platform-api` / `pm2 stop platform-web`
- 删除进程：`pm2 delete platform-api` / `pm2 delete all`
- 查看日志：`pm2 logs platform-api` / `pm2 logs platform-web`
- 实时监控：`pm2 monit`
- 保存当前列表（重启自启必备）：`pm2 save`
- Systemd 管理 PM2：`systemctl status pm2-root` / `systemctl restart pm2-root`

## 代码更新与构建
- 拉取最新代码：`git pull`
- 后端依赖（激活虚拟环境后）：`source venv/bin/activate && pip install -r requirements.txt`
- 前端依赖：`pnpm install`
- 低内存构建前端：
  - `NODE_OPTIONS=--max-old-space-size=1536 pnpm --filter @platform-ide/web-learner build`
- 构建沙箱镜像：`docker build -f docker/sandbox/Dockerfile -t platform-ide-python-sandbox:latest docker/sandbox`
- 构建完成后重启前端：`pm2 restart platform-web`

## 健康检查
- 后端自检：`curl http://127.0.0.1:8000/`
- 执行 API 测试：
  ```bash
  curl -H "Content-Type: application/json" \
    -d '{"code":"print(40+2)"}' \
    http://127.0.0.1:8000/api/execute/run
  ```
- 前端本地探测：`curl -I http://127.0.0.1:3000/`
- 输出目录：`ls -lh /opt/platform-ide/output`

## Nginx 与证书
- 检查配置：`sudo nginx -t`
- 重载配置：`sudo systemctl reload nginx`
- 查看状态：`systemctl status nginx`
- 首次签发证书（示例域名）：`sudo certbot --nginx -d your.domain.com`
- 续期演练：`sudo certbot renew --dry-run`

## 其他常用操作
- 切换虚拟环境：`source venv/bin/activate`
- 查看 Docker 状态：`docker info`
- 查看 PM2 dump 文件（排查自启）：`cat ~/.pm2/dump.pm2`
- 系统资源监控：`htop` 或 `free -h`

> 提示：变更配置后别忘记 `pm2 save` 和 `sudo nginx -t && sudo systemctl reload nginx`，并确认浏览器端能正常访问。*** End Patch
- 复制环境变量模板：`cp .env.example .env`（修改后 `chmod 600 .env`）
- 重载环境变量：`pm2 restart platform-api --update-env` / `pm2 restart platform-web --update-env`
