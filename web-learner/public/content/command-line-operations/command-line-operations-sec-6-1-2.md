好的，总建筑师。接续上一节对 Docker 核心概念的介绍，现在我们将从 `hello-world` 迈向实际应用。我将依据您的设计图，详细讲解如何通过命令行管理一个真实服务的完整生命周期。

---

### 🎯 核心概念
运行 `hello-world` 只是起点。要将 Docker 用于实际开发，我们必须掌握一套核心命令，**像操作手机App一样，对容器进行“下载安装”（拉取镜像）、“启动”、“查看状态”、“进入调试”、“停止”和“卸载”（清理）的全生命周期管理。**

### 💡 使用方式
我们将以一个非常流行的 Web 服务器 Nginx 为例，贯穿整个学习过程。这个流程模拟了在开发中部署和管理一个服务的标准步骤。

#### 1. 镜像操作：获取与管理“应用安装包”

镜像是容器的模板。在运行服务前，我们首先需要获取它的镜像。

*   **`docker pull <image_name>:<tag>`**: 从 Docker Hub（默认的公共仓库）拉取一个镜像。
    ```bash
    # 拉取最新版本的 Nginx 镜像
    docker pull nginx:latest
    ```
*   **`docker images`**: 列出本地已存在的所有镜像。
    ```bash
    # 查看本地已有的镜像，你会看到刚刚拉取的 nginx
    docker images
    ```
*   **`docker rmi <image_id_or_name>`**: 删除一个或多个本地镜像。
    *   注意：删除镜像前，必须先停止并删除所有基于该镜像创建的容器。你可以使用 `docker ps -a --filter ancestor=<image_name>` 命令来查找所有依赖于该镜像的容器。
    ```bash
    docker rmi nginx
    ```

#### 2. 容器生命周期：运行与控制“应用实例”

有了镜像，我们就可以创建和管理容器了。

*   **`docker run [OPTIONS] IMAGE [COMMAND] [ARG...]`**: 基于镜像创建一个新容器并运行它。这是最核心的命令，有许多常用选项：
    *   `-d` (`--detach`): 后台运行容器，并返回容器ID。
    *   `-p` (`--publish`) `host_port:container_port`: 将主机的端口映射到容器的端口。
    *   `--name <name>`: 为容器指定一个易于记忆的名称。
    *   `--rm`: 容器停止后自动删除。这对于运行一次性任务或测试脚本非常有用，可以保持环境整洁。

    ```bash
    # 在后台运行一个Nginx容器
    # --name my-nginx: 给容器取名为 my-nginx
    # -d: 后台运行
    # -p 8080:80: 将主机的 8080 端口映射到容器的 80 端口
    docker run --name my-nginx -d -p 8080:80 nginx
    ```
    运行成功后，访问 `http://localhost:8080`，你将看到 Nginx 的欢迎页面。

*   **`docker ps`**: 查看当前正在运行的容器。
    *   `docker ps -a`: 查看所有容器，包括已停止的。
    ```bash
    # 查看正在运行的容器
    docker ps
    ```
*   **`docker stop <container_id_or_name>`**: 停止一个正在运行的容器。
    ```bash
    docker stop my-nginx
    ```
*   **`docker start <container_id_or_name>`**: 启动一个已停止的容器。
    ```bash
    docker start my-nginx
    ```
*   **`docker rm <container_id_or_name>`**: 删除一个或多个容器。
    *   `-f` (`--force`): 强制删除一个正在运行的容器（不推荐，建议先 `stop`）。
    ```bash
    # 删除前需确保容器已停止（如上一步所示）
    docker rm my-nginx
    ```

#### 3. 进入容器：深入“应用内部”进行调试

有时我们需要进入容器内部，检查文件、查看日志或执行命令。

*   **`docker exec [OPTIONS] CONTAINER COMMAND [ARG...]`**: 在运行的容器中执行命令。
    *   `-i` (`--interactive`): 即使没有附加也保持 STDIN 打开（交互模式）。
    *   `-t` (`--tty`): 分配一个伪终端。
    *   我们通常将 `-i` 和 `-t` 合并为 `-it` 来获得一个交互式的 Shell。

    ```bash
    # 进入 my-nginx 容器，并启动一个 bash shell
    docker exec -it my-nginx bash
    
    # 进入容器后，你可以像在普通 Linux 系统中一样操作
    # 例如，查看 nginx 配置文件
    # root@<container_id>:/# cat /etc/nginx/nginx.conf
    
    # 输入 exit 命令即可退出容器返回到主机 Shell
    # root@<container_id>:/# exit
    ```
    执行后，你会发现命令行提示符发生了变化，这表明你已经成功进入了容器内部的 Shell 环境。

#### 🚨 排错指南

*   **问题：端口被占用**
    *   **现象**：执行 `docker run -p ...` 时，出现类似 `Error starting userland proxy: listen tcp4 0.0.0.0:8080: bind: address already in use` 的错误。
    *   **原因**：主机的该端口（如 8080）已经被其他程序占用。
    *   **解决方案**：更换一个主机端口，例如 `docker run -d -p 8081:80 ...`，然后通过新端口（`http://localhost:8081`）访问。

*   **问题：容器启动后立即退出**
    *   **现象**：执行 `docker run ...` 后，`docker ps` 看不到该容器，但在 `docker ps -a` 中看到其状态为 `Exited`。
    *   **原因**：容器内的主要进程执行完毕或启动失败。
    *   **解决方案**：使用 `docker logs <container_name_or_id>` 查看容器的日志输出，定位失败原因。
        ```bash
        # 假设名为 my-app 的容器启动失败
        docker logs my-app
        ```

### 📚 Level 1: 基础认知（30秒理解）
下面的代码块浓缩了最核心的容器生命周期管理流程：**运行一个服务 -> 查看状态 -> 停止服务 -> 清理环境**。这是一个独立、完整的操作循环，你可以直接复制并执行。

```bash
# 1. 在后台运行一个名为 "nginx-quick-demo" 的 Nginx 容器，并将主机 8081 端口映射到容器 80 端口
#    使用 8081 端口可以避免与常见的 8080 端口冲突
docker run -d -p 8081:80 --name nginx-quick-demo nginx

# 验证：此时在浏览器中打开 http://localhost:8081 ，应该能看到 Nginx 欢迎页。

# 2. 查看正在运行的容器，确认我们的 demo 正在运行
docker ps
# ----- 预期输出 (ID 和创建时间会有所不同) -----
# CONTAINER ID   IMAGE     COMMAND                  CREATED          STATUS          PORTS                  NAMES
# a1b2c3d4e5f6   nginx     "/docker-entrypoint.…"   5 seconds ago    Up 4 seconds    0.0.0.0:8081->80/tcp   nginx-quick-demo

# 3. 停止容器
docker stop nginx-quick-demo
# ----- 预期输出 -----
# nginx-quick-demo

# 4. 移除已停止的容器，完成清理
docker rm nginx-quick-demo
# ----- 预期输出 -----
# nginx-quick-demo

# 检查：再次运行 docker ps 和 docker ps -a，确认容器已被彻底删除。
```