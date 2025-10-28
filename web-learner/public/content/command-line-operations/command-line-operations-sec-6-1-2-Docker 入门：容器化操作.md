在您先前的教程中，我们深入学习了 Git 如何管理和追踪代码的每一次变更。现在，我们将进一步探讨 Docker，它将解决代码运行环境一致性的难题，确保您的应用在任何地方都能以相同的方式运行。这正是开发者工具链中不可或缺的下一步，将代码版本控制的优势扩展到运行环境的管理。

---

### 🎯 核心概念
Docker 是一种开源平台，用于自动化应用程序的部署、扩展和管理。它通过将应用程序及其所有依赖项打包到一个名为**容器（Container）**的轻量级、可移植的隔离环境中，彻底解决了“在我的机器上能跑，但在你那里就不行”的问题。简单来说，Git 关注代码本身的版本，而 Docker 关注代码运行环境的版本和一致性。

### 💡 使用方式
Docker 主要通过 `docker` 命令行工具来操作，开发者利用一系列 `docker` 命令来执行诸如拉取镜像、运行容器、管理容器生命周期以及检查容器状态等核心工作流。熟悉这些命令是高效进行应用部署和环境管理的关键。本节我们将着重学习以下命令：
*   `docker pull`: 从 Docker Registry 拉取镜像。
*   `docker run`: 从镜像启动一个新容器。
*   `docker ps`: 查看正在运行的容器。
*   `docker stop`: 停止一个或多个运行中的容器。
*   `docker logs`: 查看容器的日志输出。
*   `docker exec`: 在运行中的容器内部执行命令。

### 📚 Level 1: 基础认知（30秒理解）
最简单的 Docker 工作流，就是拉取一个官方提供的 Nginx Web 服务器镜像，在本地启动一个容器，验证它是否正常运行，并尝试进入容器内部进行一些简单的操作。这展示了 Docker 如何快速部署一个应用程序。

在开始之前，请确保你已经安装了 Docker Desktop（macOS/Windows）或 Docker Engine（Linux）。

```bash
# 1. 验证 Docker 是否已正确安装并运行
# 预期输出会显示 Docker 客户端和服务器的版本信息
docker version
# 预期输出示例:
# Client: Docker Engine - Community
#  Version: 26.1.3
#  API version: 1.45
#  ...
# Server: Docker Engine - Community
#  Engine:
#   Version: 26.1.3
#   ...

# 2. 从 Docker Hub 拉取官方 Nginx 镜像
# Nginx 是一个流行的 Web 服务器，我们将用它来演示。
# 如果本地没有该镜像，Docker 会自动从远程仓库下载。
docker pull nginx:latest
# 预期输出示例:
# Using default tag: latest
# latest: Pulling from library/nginx
# ... (下载进度，取决于网络速度) ...
# Status: Downloaded newer image for nginx:latest
# docker.io/library/nginx:latest

# 3. 运行一个 Nginx 容器
# -d: 后台运行容器（detached mode）
# -p 8080:80: 将宿主机的 8080 端口映射到容器的 80 端口，这样我们就可以通过宿主机访问 Nginx
# --name my-nginx-web: 为容器指定一个易记的名称
# nginx:latest: 指定要基于此镜像启动容器，包括镜像名称和标签
docker run -d -p 8080:80 --name my-nginx-web nginx:latest
# 预期输出示例:
# e1f2g3h4i5j6k7l8m9n0... (一串容器 ID，表示容器已成功启动)

# 4. 验证 Nginx 容器是否正在运行
# docker ps 命令会列出所有正在运行的容器
docker ps
# 预期输出示例:
# CONTAINER ID   IMAGE          COMMAND                  CREATED          STATUS          PORTS                  NAMES
# e1f2g3h4i5j6   nginx:latest   "nginx -g 'daemon of…"   10 seconds ago   Up 8 seconds    0.0.0.0:8080->80/tcp   my-nginx-web

# 5. 通过浏览器访问 Nginx
# 在你的浏览器中打开 http://localhost:8080
# 预期你将看到 Nginx 的默认欢迎页面："Welcome to nginx!"

# 6. 查看 Nginx 容器的实时日志
# docker logs 命令可以查看容器的标准输出和标准错误日志
docker logs my-nginx-web
# 预期输出示例 (可能会有很多行，显示 Nginx 的启动信息):
# /docker-entrypoint.sh: Configuration complete; ready for start up
# 2023/10/27 08:30:05 [notice] 1#1: using the "epoll" event method
# ...
# 2023/10/27 08:30:05 [notice] 1#1: start worker process 47
# 172.17.0.1 - - [27/Oct/2023:08:30:15 +0000] "GET / HTTP/1.1" 200 615 "-" "Mozilla/5.0..." "-"
# (如果你在步骤 5 中访问了 Nginx，这里会显示对应的 GET 请求日志)

# 7. 进入正在运行的容器内部执行命令
# -i: 保持标准输入打开，即使没有连接到终端
# -t: 分配一个伪终端（pseudo-TTY）
# bash: 在容器内部启动一个 bash shell
docker exec -it my-nginx-web bash
# 预期输出:
# root@e1f2g3h4i5j6:/# (命令行提示符会变成容器内部的，表示你已进入容器)

# 在容器内部执行一些命令
# (例如，查看 Nginx 的配置文件路径)
# root@e1f2g3h4i5j6:/# ls /etc/nginx/conf.d/
# default.conf

# (或者，直接在容器内检查 Nginx 的版本)
# root@e1f2g3h4i5j6:/# nginx -v
# nginx version: nginx/1.25.5

# root@e1f2g3h4i5j6:/# exit
# 预期输出:
# exit (你将退出容器的 shell，返回到宿主机的命令行)

# 8. 停止 Nginx 容器
# docker stop 命令会发送 SIGTERM 信号给容器的主进程，使其优雅关闭
docker stop my-nginx-web
# 预期输出:
# my-nginx-web (显示容器名称，表示已停止)

# 9. 再次检查容器状态，确认已停止
docker ps
# 预期输出: (将不会看到 my-nginx-web)
# CONTAINER ID   IMAGE     COMMAND   CREATED   STATUS    PORTS     NAMES
# (空)

# 为了验证容器确实已停止，并学习如何查看所有容器（包括已停止的），我们可以使用 docker ps -a 命令。
docker ps -a
# 预期输出示例:
# CONTAINER ID   IMAGE          COMMAND                  CREATED              STATUS                      PORTS     NAMES
# e1f2g3h4i5j6   nginx:latest   "nginx -g 'daemon of…"   About a minute ago   Exited (0) 2 seconds ago              my-nginx-web

# 10. 删除已停止的容器 (可选，用于清理)
# 容器停止后仍然存在，会占用磁盘空间。如果不需要了可以删除。
docker rm my-nginx-web
# 预期输出:
# my-nginx-web

# 11. 删除下载的 Nginx 镜像 (可选，用于清理)
# 如果你不再需要 Nginx 镜像，也可以将其删除以释放磁盘空间。
docker rmi nginx:latest
# 预期输出:
# Untagged: nginx:latest
# Untagged: nginx@sha256:...
# Deleted: sha256:...
# ...
```