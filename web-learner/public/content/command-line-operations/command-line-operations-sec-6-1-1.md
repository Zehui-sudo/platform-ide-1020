### 🎯 核心概念
Docker 解决了软件开发中最经典的“在我的机器上能跑”（It works on my machine）问题。它通过将应用程序及其所有依赖（代码、运行时、库、环境变量）打包到一个标准化的、可移植的、隔离的单元（容器）中，确保应用在任何环境中都能以完全相同的方式运行。

### 💡 使用方式
Docker 的工作流围绕三个核心概念展开：镜像（Image）、容器（Container）和仓库（Registry）。

1.  **镜像 (Image): 应用的打包模板**
    *   **是什么**：一个只读的、静态的模板，包含了运行应用程序所需的一切：代码、运行时环境、库、配置文件等。
    *   **好比是**：面向对象编程中的 **类（Class）**。它定义了应用应该是什么样子，但它本身不运行。
    *   **如何来**：镜像通常由一个名为 `Dockerfile` 的文本文件构建而成，该文件描述了构建镜像的步骤。

2.  **容器 (Container): 镜像的运行实例**
    *   **是什么**：镜像的运行实例。容器是动态的、可读写的，并且与主机系统及其他容器相互隔离。
    *   **好比是**：由 **类（Class）** 创建的 **实例对象（Instance）**。你可以从同一个镜像创建出许多个相互隔离的容器，就像从一个类可以创建多个对象一样。
    *   **如何运行**：使用 `docker run` 命令基于一个镜像来启动一个容器。

3.  **仓库 (Registry): 存放和分发镜像的中心**
    *   **是什么**：一个集中存储和分发 Docker 镜像的服务。最著名的公共仓库是 Docker Hub。
    *   **好比是**：代码领域的 **GitHub**。开发者可以从仓库拉取（pull）他人构建好的镜像，也可以将自己构建的镜像推送（push）上去分享。

**典型工作流**：开发者编写 `Dockerfile` -> 使用 `docker build` 构建出 **镜像** -> 将镜像上传到 **仓库** -> 其他人或服务器从仓库拉取该镜像 -> 使用 `docker run` 启动 **容器** 来运行应用。

### 快速入门：运行你的第一个容器
这个最简单的命令完美地展示了 Docker 的核心流程：从远程仓库（Registry）拉取一个镜像（Image），并在本地运行为一个容器（Container）。

请确保你的机器已安装 Docker，然后在命令行中运行以下命令。它会运行官方的 `hello-world` 镜像。Docker 会自动检查本地是否存在该镜像，如果不存在，则从 Docker Hub 仓库拉取，然后基于该镜像启动一个容器。

```bash
docker run hello-world
```

容器执行完毕后会输出一段信息并退出。你将看到类似下面的输出：

```text
Hello from Docker!
This message shows that your installation appears to be working correctly.

To generate this message, Docker took the following steps:
 1. The Docker client contacted the Docker daemon.
 2. The Docker daemon pulled the "hello-world" image from the Docker Hub.
    (amd64)
 3. The Docker daemon created a new container from that image which runs the
    executable that produces the output you are currently reading.
 4. The Docker daemon streamed that output to the Docker client, which sent it
    to your terminal.

To try something more ambitious, you can run an Ubuntu container with:
 $ docker run -it ubuntu bash

Share images, automate workflows, and more with a free Docker ID:
 https://hub.docker.com/

For more examples and ideas, visit:
 https://docs.docker.com/get-started/
```