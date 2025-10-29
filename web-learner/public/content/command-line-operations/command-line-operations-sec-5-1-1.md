好的，总建筑师。作为您的世界级技术教育者和命令行专家，我将依据这份教学设计图，为您打造一篇清晰、深入、高质量的Markdown教程。

---

### 🎯 核心概念
环境变量让 Shell 知道去哪里寻找命令，而别名则让我们用更短的词来调用这些命令，从而实现 Shell 环境的个性化定制与效率提升。

### 💡 使用方式

**1. 环境变量 (Environment Variables)**

环境变量是操作系统或 Shell 提供给正在运行的程序的配置信息。它们以 `KEY=value` 的形式存在。

*   **查看所有变量**: 使用 `env` 或 `printenv` 命令。
*   **查看特定变量**: 使用 `echo` 和 `$` 符号，例如 `echo $HOME` 会显示你的家目录路径。
*   **临时设置变量**: 使用 `export` 命令。这个设置只在当前的 Shell 会话中有效。
    *   `export MY_VAR="hello world"`

**2. `PATH` 变量详解**

`PATH` 是一个至关重要的环境变量，它包含一个由冒号 (`:`) 分隔的目录列表。当你输入一个命令（如 `ls`）时，Shell 会依次在 `PATH` 的这些目录中查找对应的可执行文件。

*   **追加新目录到 `PATH`**: 这是最常见的操作，可以让你自己安装的程序或脚本在任何地方都能被直接调用。
    *   `export PATH="$HOME/.local/bin:$PATH"`
    *   **解读**: 这行命令将 `$HOME/.local/bin` 目录添加到了 `PATH` 变量的最前面。`$PATH` 会被展开为它当前的值，从而保留了所有原有的系统路径。将新目录放在 `$PATH` 的最前面，意味着 Shell 会优先在这个目录里查找命令。这在你想使用自定义版本的工具（例如新版 Python）而不是系统默认版本时非常有用。

**3. 命令别名 (Alias)**

别名是为一条更长、更复杂的命令创建的一个简短、易记的快捷方式。

*   **查看所有别名**: 直接运行 `alias` 命令。
*   **创建别名**: 使用 `alias 名称='完整命令'` 的格式。
    *   `alias ll='ls -lah'`
    *   **解读**: 这行命令创建了一个名为 `ll` 的新命令，每次你输入 `ll` 并回车，Shell 实际上会执行 `ls -lah`。
    *   **提示**：定义别名时常用单引号 `' '`，它会将其中的所有内容都当作纯文本，防止特殊字符被意外解析。而在设置 `PATH` 时使用双引号 `" "` 则是必需的，因为它允许 `$PATH` 和 `$HOME` 这样的变量被正确地展开为其当前的值。

**4. 永久生效**

为了不必每次打开新的终端都重新设置环境变量和别名，你需要将这些 `export` 和 `alias` 命令写入 Shell 的配置文件中。

*   **配置文件**:
    *   对于 Bash Shell (多数 Linux 发行版的默认)，文件是 `~/.bashrc`。
    *   对于 Zsh Shell (macOS 的默认)，文件是 `~/.zshrc`。
*   **写入文件**: 你可以直接编辑文件，或使用 `echo` 命令追加。
    *   `echo "alias ll='ls -lah'" >> ~/.bashrc`
*   **立即加载**: 修改配置文件后，它只对新打开的终端生效。要让当前终端也立即生效，使用 `source` 命令。
    *   `source ~/.bashrc`

### 📚 Level 1: 基础认知（30秒理解）
这个例子展示了如何创建一个最常用的别名 `ll`，让你用两个字母就完成一次详细的文件列表查看。

```bash
# 1. 为 'ls -lah' 命令创建一个名为 'll' 的别名
# 'ls -lah' 的作用是：
# -l: 使用长列表格式
# -a: 显示所有文件，包括以 . 开头的隐藏文件
# -h: 以人类可读的格式显示文件大小 (e.g., K, M, G)
alias ll='ls -lah'

# 2. 使用我们刚刚创建的别名
ll

# 预期输出：
# (输出会因你的目录内容而异，但格式如下)
# drwxr-xr-x  5 user group 4.0K Dec 10 10:00 .
# drwxr-xr-x 20 user group 4.0K Dec  9 09:00 ..
# -rw-r--r--  1 user group  512 Dec 10 10:00 .my_config
# -rw-r--r--  1 user group 1.2M Dec  8 14:00 my_document.pdf
# drwxr-xr-x  2 user group 4.0K Dec  7 11:30 my_project
```

### 📚 Level 2: 实战应用（2分钟掌握）
假设你有一个存放自定义脚本的目录 `~/myscripts`，你希望目录里的脚本能像系统命令一样，在任何路径下直接运行。这需要将该目录添加到 `PATH` 环境变量中。

```bash
# 1. 创建一个用于存放脚本的目录
mkdir -p ~/myscripts

# 2. 创建一个简单的 "hello" 脚本
# '#!/bin/bash' 告诉系统这是一个 bash 脚本
# 第二行是脚本的实际内容
echo '#!/bin/bash' > ~/myscripts/hello
echo 'echo "Hello from my custom script!"' >> ~/myscripts/hello

# 3. 赋予该脚本可执行权限
chmod +x ~/myscripts/hello

# 4. 尝试直接运行，此时会失败，因为 Shell 不知道去哪里找它
hello
# 预期输出：
# command not found: hello

# 5. 将我们的脚本目录添加到 PATH 环境变量的最前面
# 这个设置只在当前终端会话中有效
export PATH="$HOME/myscripts:$PATH"

# 6. 再次尝试运行，这次成功了！
hello
# 预期输出：
# Hello from my custom script!

# 7. (可选) 为了让这个设置永久生效，将其写入你的 shell 配置文件
# 注意：根据你的 shell 选择 .bashrc 或 .zshrc
echo 'export PATH="$HOME/myscripts:$PATH"' >> ~/.bashrc
echo "配置已写入 ~/.bashrc，请运行 'source ~/.bashrc' 或重开终端使其生效。"
```

### 📚 Level 3: 高阶进阶（5分钟精通）
我们可以结合别名、函数和环境变量，创造出能根据环境改变行为的“智能”命令。下面的例子创建一个 `sg` (smart git) 别名，它会根据环境变量 `GIT_VIEW` 的值，决定是以简洁还是详细的方式显示 Git 提交日志。

```bash
# 1. 准备一个用于演示的 Git 仓库
# (如果已在 Git 仓库中，可以跳过此步)
# (我们使用 > /dev/null 来隐藏这些设置命令的输出，让教程更整洁)
mkdir -p /tmp/smart-git-demo && cd /tmp/smart-git-demo
git init -b main > /dev/null
touch file1.txt && git add . && git commit -m "Initial commit" > /dev/null
touch file2.txt && git add . && git commit -m "Add feature: file2" > /dev/null
echo "Git 演示仓库准备就绪。"

# 2. 定义一个 Shell 函数，它能检查环境变量
# Shell 函数比别名更强大，可以包含逻辑判断
smart_git_log() {
  # 检查名为 GIT_VIEW 的环境变量值是否为 "detailed"
  if [ "$GIT_VIEW" = "detailed" ]; then
    echo "--- 详细日志模式 ---"
    # 显示包含文件变动统计的详细日志
    git log --stat
  else
    echo "--- 简洁日志模式 ---"
    # 显示单行、带图形分支的简洁日志
    git log --oneline --graph --decorate
  fi
}

# 3. 创建一个别名 `sg` 来调用这个函数
alias sg='smart_git_log'

# 4. 场景一：默认行为 (环境变量未设置)
# 首先确保变量未设置
unset GIT_VIEW
sg
# 预期输出：
# --- 简洁日志模式 ---
# * 24f5a6b (HEAD -> main) Add feature: file2
# * 8c9e1d0 Initial commit

# 5. 场景二：智能切换行为 (设置环境变量)
export GIT_VIEW="detailed"
sg
# 预期输出：
# --- 详细日志模式 ---
# commit 24f5a6b... (HEAD -> main)
# Author: Your Name <your.email@example.com>
# Date:   ...
#
#     Add feature: file2
#
#  file2.txt | 1 +
#  1 file changed, 1 insertion(+)
#
# commit 8c9e1d0...
# Author: Your Name <your.email@example.com>
# Date:   ...
#
#     Initial commit
#
#  file1.txt | 1 +
#  1 file changed, 1 insertion(+)

# 清理演示环境
cd ~ && rm -rf /tmp/smart-git-demo
```