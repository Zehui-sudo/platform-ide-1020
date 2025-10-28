## 第2章：核心技能 - 文件系统导航与操作
### 2.1 我在哪，这里有什么？

### 🎯 核心概念
在文件系统的浩瀚宇宙中，知道自己身在何处并能查看周围的“星系”（文件和目录），是所有命令行操作的基础。这避免你迷失方向，并为你下一步的指令提供清晰的上下文。

### 💡 使用方式
本节将介绍两个最基础也最重要的命令：
*   **`pwd` (Print Working Directory)**：你的命令行GPS，它会精确告诉你当前所在的绝对路径。
*   **`ls` (List)**：你的目录扫描器，它会列出当前目录或指定目录下的文件和文件夹。配合不同的选项，它能以多种形式展示这些内容，例如：
    *   `-l` (long format)：显示详细信息，如权限、所有者、大小、修改日期等。
    *   `-a` (all)：显示所有文件，包括隐藏文件（以 `.` 开头的文件和目录）。
    *   `-h` (human-readable)：与 `-l` 配合使用时，以人类可读的格式显示文件大小（如 K、M、G）。

### 📚 Level 1: 基础认知（30秒理解）
在命令行中，首先要做的就是确定自己的位置，然后查看周围有什么。这就像你走进一个房间，先看一眼门牌号（`pwd`），再环顾四周（`ls`）。

```bash
# 目标：了解当前在文件系统中的位置，并查看当前目录的内容。

# 步骤1：使用 'pwd' (Print Working Directory) 命令，查看当前所在的完整路径。
# 想象一下你在文件系统中的坐标。
pwd
# 预期输出示例 (路径会因操作系统和用户而异):
# /home/yourusername

# 步骤2：使用 'ls' (List) 命令，查看当前目录下的文件和文件夹列表。
# 看看你当前房间里有什么。
ls
# 预期输出示例 (内容会因当前目录而异):
# Desktop  Documents  Downloads  Music  Pictures
```

### 📚 Level 2: 深入探索（1分钟实践）
基础的 `ls` 命令只显示名称，但通常我们需要更多信息，比如文件大小、修改时间和权限。这时就需要为 `ls` 增加选项。

```bash
# 目标：使用 ls 的选项来获取更详细的文件信息。

# 步骤1：使用 '-l' (long format) 选项，查看详细列表。
ls -l
# 预期输出示例：
# total 20
# drwxr-xr-x  5 yourusername  staff  160 Jul 15 10:00 Desktop
# drwxr-xr-x  8 yourusername  staff  256 Jul 15 10:01 Documents
# drwx------ 12 yourusername  staff  384 Jul 15 11:30 Downloads

# 步骤2：使用 '-a' (all) 选项，查看所有文件，包括以 '.' 开头的隐藏文件。
ls -a
# 预期输出示例 (注意多出来的 . 和 .. 等隐藏项):
# .   ..   .bash_profile   Desktop   Documents   Downloads

# 步骤3：组合使用选项，这是最常用的方式之一。
# 'l' 显示详情, 'a' 显示全部, 'h' 使文件大小人类可读 (human-readable)。
ls -lah
# 预期输出示例 (注意文件大小列，如 4.5K)：
# total 48
# drwxr-xr-x@ 15 yourusername  staff   480B Jul 15 12:00 .
# drwxr-xr-x   6 root          admin   192B Jul 10 09:00 ..
# -rw-r--r--   1 yourusername  staff   4.5K Jul 14 17:00 .bash_profile
# drwxr-xr-x   5 yourusername  staff   160B Jul 15 10:00 Desktop
```
> **💡 快速提示**：在 Unix-like 系统中，选项通常可以合并。`ls -l -a -h` 等同于 `ls -lah`。