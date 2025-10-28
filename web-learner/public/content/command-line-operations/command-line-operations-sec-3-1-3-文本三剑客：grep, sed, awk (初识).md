好的，总建筑师！我已领会您的教学设计图。作为一名世界级的技术教育者和命令行操作专家，我将为您精心打造一份高质量、多层次、结构清晰的Markdown教程，重点突出 `grep` 的掌握，并对 `sed` 和 `awk` 进行初步介绍。

---

### 🎯 核心概念
在海量文本数据中快速定位、过滤和提取所需信息，是命令行操作的核心需求。`grep`、`sed`、`awk` 这『文本三剑客』是解决这一痛点的终极利器，它们让文本处理变得高效而强大，能够帮助我们轻松解决80%的文本处理任务。

### 💡 使用方式
`grep` 用于在文本中搜索符合指定模式（pattern）的行，并打印出来。它是最常用的文本搜索工具。
`sed`（Stream Editor）是一个流编辑器，主要用于对文本进行转换，例如替换、删除、插入等操作，常用于管道中对输入流进行编辑。
`awk` 是一种强大的文本处理语言，它擅长处理结构化文本数据，可以按列（字段）进行操作和计算。

**`grep` 的基本语法和常用选项：**

`grep [选项] 模式 [文件...]`

*   **`模式`**: 你想要搜索的文本或正则表达式。
*   **`文件`**: 你想要搜索的文件名。

**常用选项：**
*   `-i` 或 `--ignore-case`: 忽略大小写。
*   `-v` 或 `--invert-match`: 反向匹配，显示不符合模式的行。
*   `-n` 或 `--line-number`: 显示匹配行的行号。
*   `-c` 或 `--count`: 只显示匹配到的行数。
*   `-w` 或 `--word-regexp`: 只匹配整个单词。
*   `-o` 或 `--only-matching`: 只显示匹配到的字符串本身，而不是整行。
*   `-r` 或 `--recursive`: 递归搜索子目录中的文件。
*   `-l` 或 `--files-with-matches`: 只列出包含匹配项的文件名。

**`sed` 的初步认识：**
*   `sed 's/旧字符串/新字符串/g' 文件名`: 最常见的用法是进行字符串替换（`s` 代表 substitute，`g` 代表全局替换）。

**`awk` 的初步认识：**
*   `awk '{print $1}' 文件名`: 默认以空格为分隔符，打印每行的第一个字段。
*   `awk -F':' '{print $1,$3}' /etc/passwd`: 使用 `-F` 指定分隔符，打印 `/etc/passwd` 文件中用户的用户名和UID。

### 📚 Level 1: 基础认知（30秒理解）
这个示例展示了如何使用 `grep` 在一个文件中查找特定的单词，并且演示了忽略大小写的常用选项。

```bash
# 1. 创建一个示例文件，包含一些文本内容
echo "Apple is red." > fruits.txt
echo "Banana is yellow." >> fruits.txt
echo "Orange is orange." >> fruits.txt
echo "GRAPE is purple." >> fruits.txt
echo "Another Apple." >> fruits.txt

# 2. 使用 grep 查找包含 "Apple" 的行
grep "Apple" fruits.txt
# 预期输出:
# Apple is red.
# Another Apple.

# 3. 使用 -i 选项进行不区分大小写的查找，找到 "Apple" 和 "apple"
grep -i "apple" fruits.txt
# 预期输出:
# Apple is red.
# Another Apple.
# GRAPE is purple. (如果你的grep版本在非单词边界也匹配)
# 注意：这里我们期待的是匹配所有包含 "apple" 字符串的行，不分大小写。
# 如果需要严格匹配"Apple"这个单词，可以使用 -w 选项，但在这里我们只展示基础的 -i。

# 4. 删除临时文件
rm fruits.txt
```