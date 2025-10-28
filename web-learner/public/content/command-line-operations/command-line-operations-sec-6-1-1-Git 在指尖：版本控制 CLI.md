### 🎯 核心概念
Git 是一款强大的分布式版本控制系统，它让团队协作开发代码变得有序、可追溯，并能轻松管理代码的每一次变更和不同版本，是现代软件开发不可或缺的基石。

### 💡 使用方式
Git 主要通过命令行界面（CLI）操作，开发者利用一系列 `git` 命令来执行诸如初始化仓库、跟踪文件变更、提交版本、切换分支、合并代码以及与远程仓库同步等核心工作流。熟悉这些命令是高效进行代码管理和团队协作的关键。

### 📚 Level 1: 基础认知（30秒理解）
最简单的 Git 工作流，就是在一个新项目里初始化 Git，添加一个文件，然后将它提交到版本历史中。这展示了 Git 如何开始跟踪你的项目。

```bash
# 1. 创建一个新的项目目录并进入
mkdir my_first_git_project
cd my_first_git_project

# 2. 在当前目录初始化一个新的 Git 仓库
# 这会在项目中创建一个隐藏的 .git 目录，用于存储所有版本信息
git init
# 预期输出:
# Initialized empty Git repository in /path/to/my_first_git_project/.git/

# 3. 创建一个简单的文件
echo "Hello, Git! This is my first file." > README.md

# 4. 查看当前仓库状态
# Git 会告诉我们有一个未被跟踪的新文件 README.md
git status
# 预期输出:
# On branch master
# No commits yet
# Untracked files:
#   (use "git add <file>..." to include in what will be committed)
#         README.md
#
# nothing added to commit but untracked files present (use "git add" to track)

# 5. 将 README.md 文件添加到暂存区（Stage Area）
# 暂存区是提交前的一个缓冲区，用于收集本次提交的所有变更
git add README.md

# 6. 再次查看状态，可以看到 README.md 已处于待提交状态
git status
# 预期输出:
# On branch master
# No commits yet
# Changes to be committed:
#   (use "git rm --cached <file>..." to unstage)
#         new file:   README.md

# 7. 提交暂存区中的文件到本地仓库，并附带一条有意义的提交信息
# 这会创建一个新的版本（commit），记录文件的当前状态
git commit -m "Initial commit: Add README.md"
# 预期输出:
# [master (root-commit) d1e2f3g] Initial commit: Add README.md # (哈希值和提交信息会根据实际情况变化)
#  1 file changed, 1 insertion(+)
#  create mode 100644 README.md

# 8. 查看提交历史
# 确认我们的提交已经成功记录
git log --oneline
# 预期输出:
# d1e2f3g (HEAD -> master) Initial commit: Add README.md

# 清理：如果你想删除这个示例项目，可以回到父目录并删除它
# cd ..
# rm -rf my_first_git_project
```