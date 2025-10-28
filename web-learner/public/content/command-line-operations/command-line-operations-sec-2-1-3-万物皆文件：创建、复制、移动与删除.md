好的，总建筑师。我已接收您的“教学设计图”，并将其转化为一篇高质量、多层次、结构清晰的Markdown教程。以下是针对“2.1.3 万物皆文件：创建、复制、移动与删除”的教学内容。

---

### 2.1.3 万物皆文件：创建、复制、移动与删除

#### 🎯 核心概念
在命令行中，文件和目录是进行任何操作的基础。掌握它们的创建、复制、移动与删除，赋予你对文件系统内容的完全控制权，是所有系统管理、项目开发的核心技能。理解这些命令如同掌握了文件系统的“生命周期管理”，但也要时刻警惕其强大的破坏力，特别是删除操作。

#### 💡 使用方式
本节将介绍一套用于文件和目录生命周期管理的核心命令：

*   **`touch <文件名>`**:
    *   **作用**：主要用于创建一个**空文件**。如果文件已存在，它会更新文件的修改时间。
    *   **特点**：非常适合快速创建占位符文件或脚本文件。

*   **`mkdir <目录名>`**:
    *   **作用**：用于**创建新目录**（文件夹）。
    *   **常用选项**：
        *   `-p` (parents)：可以递归创建多级目录。例如 `mkdir -p project/src/main` 会同时创建 `project`、`src` 和 `main` 三层目录。

*   **`cp <源文件/目录> <目标位置>`**:
    *   **作用**：用于**复制文件或目录**。它既可以将源文件/目录复制到另一个位置，也可以在同一目录下通过指定新文件名来创建副本（即复制并重命名，如 `cp old.txt new.txt`）。
    *   **常用选项**：
        *   `-r` 或 `-R` (recursive)：**复制目录时必须使用**，它会递归地复制目录及其所有内容。
        *   `-i` (interactive)：在覆盖已有文件前进行提示，避免误操作。
        *   `-v` (verbose)：显示复制过程中的详细信息。

*   **`mv <源文件/目录> <目标位置>`**:
    *   **作用**：有两种主要用途：
        1.  **移动文件或目录**：将文件或目录从一个位置移动到另一个位置。
        2.  **重命名文件或目录**：当源和目标都在同一目录且目标名称不同时，`mv` 会执行重命名操作。
    *   **特点**：`mv` 是一个“原子”操作，文件内容不会被复制，而是直接改变其在文件系统中的链接。

*   **`rm <文件>`**:
    *   **作用**：用于**删除文件**。
    *   **⚠️ 危险警告**：`rm` 命令删除的文件通常**无法恢复**，请务必谨慎使用。
    *   **常用选项**：
        *   `-i` (interactive)：在删除前进行提示，避免误删。
        *   `-f` (force)：强制删除，不进行提示，即使文件是只读的。**慎用！**
        *   `-r` 或 `-R` (recursive)：**删除目录及其所有内容时必须使用**。与 `-f` 结合使用时（`rm -rf`），具有极高的破坏性，请务必再三确认目标！

*   **`rmdir <目录>`**:
    *   **作用**：用于**删除空目录**。
    *   **特点**：只能删除没有任何内容的空目录。如果目录非空，命令会失败。通常在需要删除非空目录时，我们会使用 `rm -r`。

#### 📚 Level 1: 基础认知（30秒理解）
掌握文件和目录的创建、复制、移动与删除是日常命令行操作的核心。让我们在一个临时目录下实践这些基本操作。

```bash
# 目标：在一个临时区域内，创建文件和目录，然后进行复制、移动和删除操作。

# 1. 切换到一个临时工作目录，确保我们的操作不会影响到其他重要文件。
#    首先检查当前位置，并创建一个名为 'my_cli_playground' 的目录。
#    如果此目录已存在，此操作不会报错，可以继续。
echo "--- 准备工作：进入临时操作区 ---"
mkdir -p my_cli_playground
cd my_cli_playground
pwd
# 预期输出示例: /home/yourusername/my_cli_playground (或类似路径)

# 2. 创建一个空文件 (report.txt)
echo "--- 步骤1：创建文件 ---"
touch report.txt
ls
# 预期输出示例: report.txt

# 3. 创建一个目录 (documents)
echo "--- 步骤2：创建目录 ---"
mkdir documents
ls
# 预期输出示例: documents  report.txt

# 4. 复制文件 (report.txt) 到目录 (documents) 中
echo "--- 步骤3：复制文件 ---"
cp report.txt documents/
ls documents/
# 预期输出示例: report.txt (在 documents 目录中)

# 5. 复制文件 (report.txt) 并重命名为 (backup_report.txt)
echo "--- 步骤4：复制并重命名文件 ---"
cp report.txt backup_report.txt
ls
# 预期输出示例: backup_report.txt  documents  report.txt

# 6. 移动文件 (backup_report.txt) 到目录 (documents) 中
echo "--- 步骤5：移动文件 ---"
mv backup_report.txt documents/
ls
# 预期输出示例: documents  report.txt
ls documents/
# 预期输出示例: backup_report.txt  report.txt

# 7. 重命名文件 (report.txt) 为 (final_report.txt) (在当前目录)
echo "--- 步骤6：重命名文件 ---"
mv report.txt final_report.txt
ls
# 预期输出示例: documents  final_report.txt

# 8. 删除文件 (documents/report.txt)
echo "--- 步骤7：删除文件 ---"
rm documents/report.txt
ls documents/
# 预期输出示例: backup_report.txt

# 9. 尝试删除非空目录 (documents) - 预期会失败
echo "--- 步骤8：尝试删除非空目录 (会失败) ---"
rmdir documents
# 预期输出示例: rmdir: failed to remove 'documents': Directory not empty
ls
# 预期输出示例: documents  final_report.txt (目录 documents 仍然存在)

# 10. 删除目录 (documents) 中的所有内容，使其变空
echo "--- 步骤9：清空目录以便删除 ---"
rm documents/backup_report.txt
ls documents/
# 预期输出示例: (无输出，表示 documents 目录已空)

# 11. 删除空目录 (documents)
echo "--- 步骤10：删除空目录 ---"
rmdir documents
ls
# 预期输出示例: final_report.txt (目录 documents 已被删除)

# 12. 清理：删除剩余的文件和目录，回到原始状态
echo "--- 步骤11：清理工作 ---"
rm final_report.txt # 删除剩余的文件
cd ..               # 返回上一级目录
rmdir my_cli_playground # 删除我们创建的临时工作目录
ls
# 预期输出示例: (你之前目录的内容，my_cli_playground 不再显示)
echo "清理完成，您已退出临时操作区。"
```