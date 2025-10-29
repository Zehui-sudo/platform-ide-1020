### 🎯 核心概念
Git 命令行是进行版本控制最直接、最强大的方式，它能让开发者在任何环境下（尤其是服务器）精准、高效地管理代码的每一次变更、协作和历史追溯。

### 💡 使用方式
Git 的核心操作围绕着一个清晰的工作流：将远程仓库克隆到本地，修改文件，将变更暂存，提交这些变更形成一个新版本，最后将新版本推送回远程仓库与团队共享。

1.  **全局配置 (仅需一次)**
    *   `git config --global user.name "Your Name"`: 设置你的提交者姓名。
    *   `git config --global user.email "your.email@example.com"`: 设置你的提交者邮箱。

2.  **获取与创建项目**
    *   `git clone [repository_url]`: 从远程服务器克隆一个完整的项目副本到本地。
    *   `git init`: 在当前目录初始化一个新的 Git 仓库。

3.  **日常工作流**
    *   `git status`: 查看当前工作区的文件状态（已修改、已暂存、未跟踪）。
    *   `git add [file_name]`（添加指定文件）或 `git add .`（添加当前目录下的所有变更）: 将文件的修改从工作区添加到暂存区，准备提交。
    *   `git commit -m "Your descriptive message"`: 将暂存区的所有修改永久记录到本地仓库，形成一个版本快照。
    *   `git push`: 将本地仓库的提交推送到远程仓库。

4.  **协作与同步**
    *   `git fetch`: 从远程仓库下载最新的历史记录，但**不**与本地工作合并。
    *   `git pull`: 从远程仓库下载最新历史记录，并**自动**与当前本地分支合并 (`fetch` + `merge`)。

5.  **查看与比较**
    *   `git log`: 查看提交历史记录。
    *   `git diff`: 查看工作区与暂存区之间的文件内容差异。
    *   `git diff --staged`: 查看暂存区与最新提交之间的差异。

### 📚 Level 1: 基础认知（30秒理解）
让我们在本地创建一个全新的项目，并完成第一次提交。这个过程完全在你的电脑上进行，不涉及任何远程服务器。

```bash
# 1. 创建一个新目录并进入
mkdir git-demo
cd git-demo

# 2. 初始化一个新的 Git 仓库
git init
# 预期输出:
# Initialized empty Git repository in /path/to/your/git-demo/.git/

# 3. 创建一个新文件并写入内容
echo "Hello, Git!" > README.md

# 4. 将新文件添加到暂存区
git add README.md

# 5. 提交暂存的更改，并附上描述信息
git commit -m "Initial commit: Add README.md"
# 预期输出:
# [main (root-commit) 1a2b3c4] Initial commit: Add README.md
#  1 file changed, 1 insertion(+)
#  create mode 100644 README.md
```

### 📚 Level 2: 场景实战
**场景：** 你加入了一个新项目，需要从远程仓库（如 GitHub）拉取代码，完成一项新功能的开发，并将其推送回去。

这是一个完整的“克隆 -> 修改 -> 添加 -> 提交 -> 推送”工作流。

```bash
# 1. 从远程地址克隆项目 (请将 URL 替换为你的真实项目地址)
git clone https://github.com/some-org/awesome-project.git
cd awesome-project

# 2. 创建一个新文件来代表你的新功能
echo "This is a new feature." > feature.txt

# 3. 查看当前仓库状态，Git 会提示你有一个未被追踪的文件
git status
# 预期输出 (部分):
# On branch main
# Your branch is up to date with 'origin/main'.
#
# Untracked files:
#   (use "git add <file>..." to include in what will be committed)
#         feature.txt

# 4. 将新文件添加到暂存区
git add feature.txt

# 5. 提交这次修改
git commit -m "feat: Add initial version of the new feature"
# 预期输出 (部分):
# [main 5d6e7f8] feat: Add initial version of the new feature
#  1 file changed, 1 insertion(+)
#  create mode 100644 feature.txt

# 6. 将你的提交推送到名为 'origin' 的远程仓库的 'main' 分支
git push origin main
# 预期输出 (部分):
# Enumerating objects: 4, done.
# Counting objects: 100% (4/4), done.
# ...
# To https://github.com/some-org/awesome-project.git
#    1a2b3c4..5d6e7f8  main -> main
```

**【技巧】** 当项目历史变得复杂时，使用一个更清晰的 `git log` 命令来查看提交树：

```bash
git log --oneline --graph --decorate --all
# 预期输出 (一个美化的、带分支图形的提交历史):
# * 5d6e7f8 (HEAD -> main, origin/main) feat: Add initial version of the new feature
# * 1a2b3c4 Initial commit
```

### 📚 Level 3: 深度剖析
#### 1. `git pull` vs `git fetch`：同步的艺术

-   **`git fetch`**: 更安全的选择。它只从远程下载最新的数据（如新的分支和提交），但**不会**修改你的本地工作代码。这给了你一个机会在合并前先检查一下远程的变动 (`git log origin/main`)。
-   **`git pull`**: 是一个复合命令，相当于 `git fetch` 紧接着 `git merge FETCH_HEAD`。它会一步到位地将远程更新拉取并合并到你的当前分支。对于简单的个人项目或无冲突的团队协作，它很方便，但在复杂的协作场景下，先 `fetch` 再决定如何 `merge` 或 `rebase` 会更稳妥。

```bash
# 工作流1：先检查再合并 (推荐)
git fetch origin
# ... 检查远程分支的更新 ...
git merge origin/main

# 工作流2：直接拉取并合并 (快捷)
git pull origin main
```

#### 2. 排错指南：解决合并冲突 (Merge Conflict)

当两个人都修改了同一个文件的同一部分时，`git pull` 或 `git merge` 就会失败，并产生合并冲突。Git 无法决定该保留哪个版本，需要你手动介入。

**解决步骤：**

1.  执行 `git pull` 或 `git merge` 后，Git 提示存在冲突。
2.  使用 `git status` 查看哪些文件发生了冲突。
3.  打开冲突的文件，你会看到类似下面的标记：

    ```
    <<<<<<< HEAD
    这是你本地的修改内容。
    =======
    这是从远程拉取下来的、与你冲突的修改内容。
    >>>>>>> origin/main
    ```

4.  **手动编辑**这个文件，删除 `<<<<<<<`, `=======`, `>>>>>>>` 这些标记，并根据你的业务逻辑决定最终要保留的内容（可以是你的，也可以是对方的，或者是两者的结合）。
5.  保存文件后，使用 `git add [冲突文件名]` 将解决后的文件标记为“已解决”。
6.  最后，执行 `git commit` (此时无需 `-m` 参数，Git 会自动生成一个合并提交信息) 来完成这次合并。

```bash
# 1. 假设在 pull 时发生冲突
git pull
# 预期输出:
# Auto-merging conflicted-file.txt
# CONFLICT (content): Merge conflict in conflicted-file.txt
# Automatic merge failed; fix conflicts and then commit the result.

# 2. 手动编辑 conflicted-file.txt，解决冲突并保存

# 3. 将解决后的文件添加到暂存区
git add conflicted-file.txt

# 4. 提交这次合并
git commit
# 此时会打开一个编辑器让你确认合并提交信息，保存并退出即可。
```

### 🎓 总结
掌握 Git 命令行是每一位开发者的核心技能。虽然命令众多，但日常工作主要围绕以下黄金流程：

| 阶段         | 核心命令                                         | 作用                                       |
| :----------- | :----------------------------------------------- | :----------------------------------------- |
| **配置**     | `git config`                                     | 一次性设置用户信息。                       |
| **获取代码** | `git clone`                                      | 下载远程项目副本。                         |
| **日常开发** | `git status` -> `git add` -> `git commit`        | 检查状态 -> 暂存变更 -> 记录版本。         |
| **分享协作** | `git push`                                       | 将本地提交分享到远程。                     |
| **同步更新** | `git pull` / `git fetch`                         | 从远程获取最新代码。                       |
| **历史审查** | `git log`, `git diff`                            | 查看提交历史和具体文件变更。               |

熟练运用这个流程，你就能应对绝大多数的版本控制场景，并与全球的开发者高效协作。记住，命令行提供了最纯粹、最强大的 Git 体验。