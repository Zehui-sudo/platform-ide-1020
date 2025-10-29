好的，总建筑师！作为您的世界级技术教育者和命令行专家，我将严格遵循您的“教学设计图”和结构模板，为您打造一篇高质量的 Docker 命令行教程。

---

# 5.3 容器化：Docker

### 🎯 核心概念
Docker 通过将应用及其依赖打包成一个轻量、可移植的“容器”，彻底解决了“在我电脑上明明能跑”的环境不一致问题。

### 💡 使用方式
管理一个 Docker 容器的完整生命周期，通常遵循以下核心操作步骤：
1.  **拉取镜像 (`pull`)**: 从 Docker Hub 或其他镜像仓库获取标准化的应用模板（镜像）。
2.  **运行容器 (`run`)**: 基于镜像创建并启动一个可运行的实例（容器）。
3.  **查看状态 (`ps`)**: 检查当前有哪些容器正在运行或已经停止。
4.  **进入容器 (`exec`)**: 在运行的容器内部执行命令，进行调试或管理。
5.  **停止容器 (`stop`)**: 优雅地终止一个正在运行的容器。

---

### 📚 Level 1: 基础认知（30秒理解）
我们的第一个任务是：在30秒内启动一个功能齐全的 Nginx Web 服务器。只需一个命令！

```bash
# 首先，拉取官方的 Nginx 镜像（如果本地没有的话）
docker pull nginx

# 然后，在后台运行一个 Nginx 容器，并将容器的80端口映射到我们电脑的8080端口
docker run -d -p 8080:80 --name my-nginx nginx

# === 预期行为 ===
# 1. 命令行会输出一长串容器ID，表示启动成功。
# 2. 现在打开浏览器访问 http://localhost:8080，你会看到 Nginx 的欢迎页面！
# 3. 运行 `docker ps` 可以看到名为 my-nginx 的容器正在运行。
```

---

### 📈 Level 2: 核心特性（深入理解）
掌握了基础运行，我们再深入探索两个管理容器的核心特性。

#### 特性1: 全面掌控 - 查看所有容器
`docker ps` 只显示正在运行的容器。但有时我们需要查看那些已经停止的“历史容器”。

(简要说明)
使用 `-a` (all) 参数，`docker ps` 就能列出所有容器，无论其状态如何。这对于清理不再需要的容器或排查启动失败的容器非常有用。

```bash
# 让我们先停止之前创建的 my-nginx 容器
docker stop my-nginx

# 现在，运行 `docker ps`，你会发现列表是空的
docker ps
# === 预期输出 ===
# CONTAINER ID   IMAGE     COMMAND   CREATED   STATUS    PORTS     NAMES
# (空空如也)

# 接着，使用 -a 参数查看所有容器
docker ps -a
# === 预期输出 (示例) ===
# CONTAINER ID   IMAGE     COMMAND                  CREATED          STATUS                      PORTS     NAMES
# a1b2c3d4e5f6   nginx     "/docker-entrypoint.…"   2 minutes ago    Exited (0) 10 seconds ago             my-nginx
# (这里会显示刚刚被我们停止的 my-nginx 容器)
```

#### 特性2: 深入腹地 - 进入容器内部
容器就像一个“黑盒子”，但 `docker exec` 给了我们一把钥匙，可以随时进入其中进行探索或调试。

(简要说明)
`docker exec -it <容器名> <命令>` 允许我们在一个正在运行的容器内启动一个新的进程。`-i` (interactive) 保持输入流，`-t` (tty) 分配一个伪终端，两者结合通常用于启动一个交互式 shell，如 `bash`。

```bash
# 首先，确保我们的 my-nginx 容器是启动状态（如果已停止，请用 `docker start my-nginx` 启动）
docker start my-nginx

# 使用 exec 命令进入 my-nginx 容器，并启动一个 bash shell
docker exec -it my-nginx bash

# === 预期行为 ===
# 你的命令行提示符会改变，类似于 `root@a1b2c3d4e5f6:/#`
# 这表示你已经成功进入了容器内部的操作系统！

# 现在你可以在容器里执行命令，比如查看 Nginx 的默认网页文件
ls -l /usr/share/nginx/html
# === 预期输出 ===
# -rw-r--r-- 1 root root 494 Sep 15  2020 50x.html
# -rw-r--r-- 1 root root 612 Sep 15  2020 index.html

# 输入 `exit` 并回车，即可退出容器，返回到你自己的电脑终端。
exit
```

---

### 🔍 Level 3: 对比学习（避免陷阱）
一个常见的初学者陷阱是：容器启动后，终端被“卡住”了，而且 `Ctrl+C` 还会直接把容器弄停。

```bash
# === 错误用法 ===
# ❌ 忘记使用 -d 参数，容器在前台运行
docker run -p 8081:80 --name my-nginx-foreground nginx

# 解释为什么是错的:
# 这个命令会启动 Nginx，但它会占据你当前的终端窗口，不断输出 Nginx 的日志。
# 你无法再输入其他命令。如果你按下 Ctrl+C，虽然终端恢复了，但容器也随之停止了。
# 这对于需要长时间运行的后台服务来说是不可接受的。

# === 正确用法 ===
# ✅ 使用 -d (detached) 参数，让容器在后台安静地运行
docker run -d -p 8080:80 --name my-nginx nginx

# 解释为什么这样是对的:
# -d 参数告诉 Docker 在后台（分离模式）运行容器。
# 命令执行后会立即返回容器ID，并将你的终端控制权交还给你。
# 容器会像一个守护进程一样在后台持续运行，这正是我们运行 Web 服务器等服务时所期望的。
```

---

### 🚀 Level 4: 实战应用（真实场景）
**场景：🚀 部署你的第一个“时空穿梭”个人博客！**

你是一位时空旅行者，想用 Docker 快速部署一个简单的博客首页，向世界宣告你的存在。

```bash
# --- 第1步: 在你的电脑上创建博客内容 ---
# 创建一个目录存放我们的网站文件
mkdir my-time-travel-blog
cd my-time-travel-blog

# 创建首页文件 index.html，并写入一条来自未来的消息
echo "<h1>Hello from the Future!</h1><p>I'm a time traveler. Docker is still cool in 2242.</p>" > index.html

# --- 第2步: 使用 Docker 部署博客 ---
# -d: 后台运行
# -p 8888:80: 将我们电脑的8888端口映射到容器的80端口
# -v "$(pwd)":/usr/share/nginx/html: 这是关键！将当前目录（包含index.html）挂载到Nginx容器的网站根目录
# --name time-blog: 给容器取个酷炫的名字
# nginx: 使用官方Nginx镜像
docker run -d -p 8888:80 --name time-blog -v "$(pwd)":/usr/share/nginx/html nginx

# (Windows PowerShell 用户请使用: docker run -d -p 8888:80 --name time-blog -v "${PWD}":/usr/share/nginx/html nginx)

# --- 第3步: 验证成果 ---
# 打开浏览器，访问 http://localhost:8888
# 你将看到你刚刚编写的“来自未来的消息”！
# 这证明了我们本地的文件已经被 Nginx 容器成功提供服务了。

# --- 第4步: 时空清理（结束任务） ---
# 停止博客容器
docker stop time-blog

# 移除容器（可选，用于清理）
docker rm time-blog

# === 预期输出 ===
# 运行 `docker run` 后，会输出一长串容器ID。
# 访问 http://localhost:8888 会显示：
# Hello from the Future!
# I'm a time traveler. Docker is still cool in 2242.
# 运行 `docker stop` 和 `docker rm` 后，会分别输出容器的名字 `time-blog`。
```

---

### 💡 记忆要点
- **镜像 vs 容器**: 镜像是“菜谱”（只读模板），容器是根据菜谱做出的“菜”（运行实例）。一个镜像可以创建无数个容器。
- **生命周期五步曲**: 牢记核心流程 `pull`(拉取) -> `run`(运行) -> `ps`(查看) -> `exec`(进入) -> `stop`(停止)。
- **三大核心参数**: `-d` (detach, 后台运行不卡手)，`-p` (port, 端口映射像架桥)，`--name` (给容器一个方便记忆的名字)。