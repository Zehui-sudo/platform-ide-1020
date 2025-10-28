## 4.3 我的地盘我做主：环境变量与配置文件

### 🎯 核心概念
在掌握了进程管理（4.2 进程管理）之后，本节将探讨如何自定义和控制命令行环境。`环境变量`与`配置文件`是实现这一目标的关键。它们共同定义了 Shell 会话及其运行程序的行为，例如，程序运行时所需的信息、用户偏好设置，以及最重要的——命令的查找路径（`PATH`）。通过自定义这些设置并将其固化到配置文件中，我们能构建一个个性化、高效且可复现的工作环境。

### 💡 使用方式
本节将学习如何查看（`env`, `echo $VAR_NAME`）、临时设置（`export`）环境变量，以及如何通过修改 `~/.bashrc` 或 `~/.bash_profile` 等配置文件来永久保存这些设置。理解 `PATH` 变量的工作机制至关重要，它决定了系统能否找到并执行你输入的命令。同时，掌握 `source` 命令能让你在不重启 Shell 的情况下，即时应用配置文件的变更。

### 📚 Level 1: 基础认知（30秒理解）
快速了解当前命令行环境中的变量，特别是命令查找路径 `PATH`，并尝试进行一次临时设置。

```bash
# 示例代码：查看当前所有的环境变量
# `env` 命令会列出当前 Shell 会话的所有环境变量及其值。
env
```

```bash
# 预期输出示例 (实际输出会因系统环境和用户配置而异，这里仅为示意):
# SHELL=/bin/bash
# PWD=/home/user
# LOGNAME=user
# HOME=/home/user
# LANG=en_US.UTF-8
# PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/snap/bin
# TERM=xterm-256color
# ... (其他环境变量，每行一个键值对)
```

```bash
# 示例代码：单独查看 PATH 环境变量
# `echo $PATH` 会显示 PATH 变量的当前值。
echo $PATH
```

```bash
# 预期输出示例 (实际输出会因系统环境而异):
# /usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/snap/bin
#
# 解释：
# PATH 变量是一个由冒号（:）分隔的目录列表。
# 当你在终端输入一个命令时（例如 `ls`），Shell 会按照 PATH 中列出的顺序，
# 在这些目录中查找名为 `ls` 的可执行文件。如果找到，就会执行它。
# 这是你的系统如何知道 `ls`、`mkdir` 等常用命令存储在哪里的关键机制。
```

```bash
# 示例代码：临时设置一个环境变量并查看
# 使用 `export` 命令可以临时创建一个环境变量，或者修改一个现有变量的值。
# 这个变量只在当前会话（及其子进程）中有效。
export MY_GREETING="Hello from my shell!"
echo $MY_GREETING
```

```bash
# 预期输出示例:
# Hello from my shell!
#
# 解释：
# `export` 命令让 `MY_GREETING` 这个变量对当前 Shell 会话以及由它启动的
# 所有子进程可见。当你关闭终端或开启新的会话时，这个变量就会消失。
# 这是理解如何持久化配置的基础。
```