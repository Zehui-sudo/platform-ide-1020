好的，总建筑师。作为您的世界级技术教育者与命令行专家，我将依据这份“教学设计图”，为您打造一篇高质量的Markdown教程。

---

### 3.1.1 管道与重定向：命令行的“胶水”

### 🎯 核心概念
**通过管道（`|`）和重定向（`>`、`<`）来组合命令，将多个“只做一件事”的小工具连接起来，像乐高积木一样搭建出强大的数据处理流水线。** 这是Unix/Linux“一切皆文件”和“组合小程序”哲学的精髓体现。

### 💡 使用方式
管道与重定向是控制命令数据流向的特殊符号。它们本身不是命令，而是Shell提供的一种功能，用于连接命令的输入和输出。

*   **标准流 (Standard Streams)**
    *   `stdin` (标准输入, 文件描述符 0): 命令默认的数据来源，通常是键盘。
    *   `stdout` (标准输出, 文件描述符 1): 命令默认的成功输出目的地，通常是屏幕。
    *   `stderr` (标准错误, 文件描述符 2): 命令默认的错误信息输出目的地，通常也是屏幕。

*   **管道 (Pipe)**
    *   `command1 | command2`: 将 `command1` 的标准输出 (`stdout`) “管道”给 `command2` 作为其标准输入 (`stdin`)。

*   **重定向 (Redirection)**
    *   `command > file`: 将 `command` 的标准输出 (`stdout`) 写入 `file`。**如果文件已存在，会覆盖内容。**
    *   `command >> file`: 将 `command` 的标准输出 (`stdout`) **追加**到 `file` 的末尾。
    *   `command < file`: 将 `file` 的内容作为 `command` 的标准输入 (`stdin`)。
    *   `command 2> file`: 将 `command` 的标准错误 (`stderr`) 重定向到 `file`。
    *   `command > file 2>&1`: 将标准输出 (`stdout`) 重定向到 `file`，然后将标准错误 (`stderr`) 也重定向到标准输出 (`stdout`) 的相同位置。**顺序很重要**。
    *   `command &> file`: 上一条命令的简写形式，将 `stdout` 和 `stderr` 同时重定向到 `file`。

### 📚 Level 1: 基础认知（30秒理解）
最简单的用法就是将本应显示在屏幕上的内容，写入到一个文件中。这便是“输出重定向”。

```bash
# 场景：我们想创建一个文件，内容是 "Hello, Command Line!"

# 执行命令，使用 > 将 echo 命令的输出重定向到 greeting.txt 文件
echo "Hello, Command Line!" > greeting.txt

# 验证：使用 cat 命令查看文件内容
cat greeting.txt
# 预期输出:
# Hello, Command Line!
```
在这个例子中，`echo` 命令的结果没有出现在屏幕上，而是被直接“重定向”到了 `greeting.txt` 文件里。

### 📚 Level 2: 实战应用
掌握了基础，我们来看几个真实世界中最常用的组合，感受管道与重定向的威力。

**场景1：在当前目录查找所有 JavaScript 文件**
我们使用 `ls -l` 列出详细文件列表，然后通过管道 `|` 将这个列表“喂”给 `grep` 命令，让它筛选出包含 `.js` 的行。

```bash
# 准备环境：创建一些示例文件
touch main.js utils.js index.html README.md

# 使用管道组合 ls 和 grep
ls -l | grep '.js'

# 预期输出 (具体权限、日期等会不同):
# -rw-r--r--  1 user  group  0 Dec 12 10:30 main.js
# -rw-r--r--  1 user  group  0 Dec 12 10:30 utils.js

# 清理环境
rm main.js utils.js index.html README.md
```

**场景2：统计当前系统中运行的进程总数**
`ps aux` 会列出所有进程，每一行代表一个进程。我们把这个列表通过管道 `|` 发送给 `wc -l`，它会统计输入的总行数，从而得到进程总数。

```bash
# 统计当前系统运行的进程数
ps aux | wc -l

# 预期输出 (这是一个数字，具体数值因系统和当前运行的应用而异):
# 432
```

**场景3：记录日志，区分覆盖与追加**
`>` 会清空文件再写入，而 `>>` 会在文件末尾继续添加，这在记录日志时非常关键。

```bash
# 第一次记录日志，使用 > 创建并写入
date > system.log

# 查看日志内容
cat system.log
# 预期输出 (类似如下格式):
# Tue Dec 12 10:35:01 PST 2023

# 一段时间后，追加一条新日志，使用 >>
sleep 1 # 暂停一秒，让时间戳变化
date >> system.log

# 再次查看日志，会发现新内容被添加到了末尾
cat system.log
# 预期输出 (注意有两行了):
# Tue Dec 12 10:35:01 PST 2023
# Tue Dec 12 10:35:02 PST 2023

# 清理文件
rm system.log
```

### 📚 Level 3: 深入理解
高手不仅要处理正确的输出（`stdout`），还要能优雅地管理错误信息（`stderr`）。

**场景1：分离正确输出和错误输出**
当一个命令既可能成功也可能失败时，我们可以分别捕获它的 `stdout` 和 `stderr`。

```bash
# 准备环境：创建一个目录和一个文件
mkdir -p temp_dir
touch temp_dir/real_file.txt

# find 命令会成功找到 real_file.txt (输出到 stdout)
# 同时因为找不到 fake_file.txt 而产生一条错误信息 (输出到 stderr)
find temp_dir -name "real_file.txt" -o -name "fake_file.txt" > success.log 2> error.log

# 查看成功日志
cat success.log
# 预期输出:
# temp_dir/real_file.txt

# 查看错误日志
cat error.log
# 预期输出 (不同系统信息可能略有差异):
# find: ‘temp_dir/fake_file.txt’: No such file or directory

# 清理环境
rm -r temp_dir success.log error.log
```

**场景2：忽略所有错误信息**
有时我们只关心成功的结果，不希望看到烦人的错误提示。这时可以将错误流重定向到特殊文件 `/dev/null`，它像一个“黑洞”，会吞噬一切写入的数据。

```bash
# 再次执行上一个find命令，但这次将错误信息丢弃
find temp_dir -name "real_file.txt" -o -name "fake_file.txt" 2> /dev/null

# 预期输出 (只有成功的结果会显示在屏幕上):
# temp_dir/real_file.txt
```

**场景3：将所有输出（正确和错误）都保存到同一个日志文件**
在执行自动化脚本或安装软件时，我们希望把整个过程的所有信息，无论成功与否，都记录下来备查。

```bash
# 这是一个常见的安装或构建命令场景
# 我们用一个会同时产生 stdout 和 stderr 的 find 命令来模拟
# 语法 `> install.log 2>&1` 的意思是：
# 1. 先将 stdout 重定向到 install.log (`> install.log`)
# 2. 再将 stderr 重定向到 stdout 当前所在的位置 (`2>&1`)，也就是 install.log
find /etc -name "hosts" -o -name "nonexistentfile" > install.log 2>&1

# 查看日志文件，会发现正确和错误信息都按顺序记录在内
cat install.log
# 预期输出 (顺序和具体错误信息可能略有不同):
# /etc/hosts
# find: ‘/etc/nonexistentfile’: No such file or directory

# 更现代、简洁的写法是使用 `&>`
find /etc -name "hosts" -o -name "nonexistentfile" &> install.log

# 清理文件
rm install.log
```

### 📝 总结
管道和重定向是命令行从“玩具”变为“瑞士军刀”的关键。它们让我们可以将简单的命令串联起来，构建出符合自己需求的、一次性的强大工具。

*   **`|` (管道)**: 命令流水线，连接上一个的**输出**和下一个的**输入**。
*   **`>` (覆盖重定向)**: 将**输出**写入文件，像“另存为”，会覆盖旧内容。
*   **`>>` (追加重定向)**: 将**输出**添加到文件末尾，像“写日记”，不断累加。
*   **`<` (输入重定向)**: 让命令从文件而不是键盘读取**输入**。
*   **`2>` (错误重定向)**: 专门捕捉**错误信息**，不和正常输出混淆。
*   **`&>` (混合重定向)**: 将**所有输出**（正确+错误）一网打尽，是记录完整日志的最佳选择。

熟练运用它们，你将能以超乎想象的效率完成各种复杂的数据处理任务。