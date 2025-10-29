好的，总建筑师。作为您的世界级技术教育者和命令行专家，我将依据这份“教学设计图”，将关于 I/O 重定向的知识点，转化为一篇清晰、生动、循序渐进的 Markdown 教程。

---

### 3.1 I/O 重定向：改变输入和输出

#### 🎯 核心概念

I/O 重定向让我们能够自由地控制命令的“数据来源”和“结果去向”，不再局限于键盘和屏幕，从而实现强大的自动化数据处理。

#### 💡 使用方式

在命令行中，我们主要通过以下几个符号来改变数据的流向：

*   **`>` (输出重定向 - 覆盖)**：将命令的**标准输出**写入文件，如果文件已存在，则**覆盖**其内容。
    *   格式：`command > filename`
*   **`>>` (输出重定向 - 追加)**：将命令的**标准输出**追加到文件末尾，如果文件不存在，则创建它。
    *   格式：`command >> filename`
*   **`<` (输入重定向)**：将文件的内容作为命令的**标准输入**，而不是从键盘读取。
    *   格式：`command < filename`
*   **`2>` (错误重定向)**：将命令的**标准错误**输出写入文件。
    *   格式：`command 2> error_filename`

在深入之前，请记住这三个“数据通道”：
*   **标准输入 (stdin)**: 默认是键盘，文件描述符为 `0`。
*   **标准输出 (stdout)**: 默认是屏幕，文件描述符为 `1`。
*   **标准错误 (stderr)**: 默认也是屏幕，文件描述符为 `2`。

---

#### 📚 Level 1: 基础认知（30秒理解）

让我们将 `ls -l` 命令（列出当前目录文件详情）的结果保存到一个文件中，而不是直接打印在屏幕上。

```bash
# 场景: 我们想把当前目录的文件列表保存下来，方便以后查看或发送给别人。

# 正常情况下，`ls -l` 的结果会显示在屏幕上。
# 现在，我们使用 `>` 将结果重定向到文件 `file_list.txt`。
ls -l > file_list.txt

# 预期输出:
# (你的终端屏幕上不会有任何输出)
#
# 验证:
# 运行 `cat file_list.txt` 命令，你会看到 `ls -l` 的完整输出内容已经被保存在了文件中。
# total 8
# -rw-r--r--  1 user  staff  123 Nov 21 10:30 file_list.txt
# ... (其他文件)
```

---

#### 📈 Level 2: 核心特性（深入理解）

掌握了基础，我们来探索更多实用的重定向特性。

##### 特性1: 追加内容而不是覆盖 (`>>`)

当你需要持续记录日志，而不是每次都从头开始时，`>>` 就派上用场了。它会在文件末尾添加新内容。

```bash
# 场景: 记录一个应用的启动日志。

# 第一次记录启动时间
date > app.log

# 一段时间后，再次记录，但这次我们想追加，而不是覆盖
echo "App restarted, performing health check..." >> app.log
date >> app.log

# 预期输出:
# (屏幕上不会有任何输出)
#
# 验证 `app.log` 的内容:
# cat app.log
#
# Tue Nov 21 10:35:00 CST 2023
# App restarted, performing health check...
# Tue Nov 21 10:35:05 CST 2023
```

##### 特性2: 从文件读取输入 (`<`)

有些命令（如 `sort`, `wc`）可以处理标准输入。`<` 让我们能方便地将文件内容“喂”给这些命令。

```bash
# 场景: 我们有一个未排序的购物清单，需要按字母顺序排序。

# 1. 先创建一个未排序的清单文件
echo "Milk" > shopping_list.txt
echo "Bread" >> shopping_list.txt
echo "Apples" >> shopping_list.txt

# 2. 使用 `<` 将文件内容作为 `sort` 命令的输入
sort < shopping_list.txt

# 预期输出:
# (屏幕上会直接显示排序后的结果)
# Apples
# Bread
# Milk
```

##### 特性3: 捕获错误信息 (`2>`)

默认情况下，成功信息（stdout）和错误信息（stderr）都会显示在屏幕上。`2>` 可以帮助我们分离它们，这对于自动化脚本的调试至关重要。

```bash
# 场景: 尝试访问一个存在的文件和一个不存在的文件，并分别捕获成功和错误信息。

# `ls` 尝试访问 'shopping_list.txt' (存在) 和 'ghost_file.txt' (不存在)
# 成功信息（stdout）仍然会显示在屏幕上
# 错误信息（stderr）会被重定向到 `error.log` 文件
ls shopping_list.txt ghost_file.txt 2> error.log

# 预期输出:
# (屏幕上只显示成功找到的文件)
# shopping_list.txt
#
# 验证错误日志:
# cat error.log
#
# ls: cannot access 'ghost_file.txt': No such file or directory
```

---

#### 🔍 Level 3: 对比学习（避免陷阱）

一个常见的陷阱是混淆 `>`（覆盖）和 `>>`（追加），这可能导致重要数据丢失。

```bash
# 场景: 记录多条系统日志到同一个文件。

# === 错误用法 ===
# ❌ 每次都用 `>` 覆盖文件
echo "Log entry 1: System started" > system.log
echo "Log entry 2: User logged in" > system.log # 这一步会覆盖掉第一行！

# 解释: `>` 符号像是一次性的“写入”，每次执行都会先清空目标文件。
# 运行 `cat system.log` 后，你会发现文件里只剩下 "Log entry 2: User logged in"。

# === 正确用法 ===
# ✅ 使用 `>` 创建或首次写入，然后用 `>>` 追加
echo "Log entry 1: System started" > system.log
echo "Log entry 2: User logged in" >> system.log # 使用 `>>` 追加，保留了原有内容

# 解释: `>>` 符号像是在记事本上“续写”，它总是在文件末尾添加新内容。
# 运行 `cat system.log` 后，你会看到两行日志都完整地保留了下来。
```

---

#### 🚀 Level 4: 实战应用（真实场景）

**场景：🚀 星际飞船自动诊断系统**

我们的飞船需要一个自动诊断脚本。该脚本会读取一个任务清单 `diagnostics.txt`，模拟执行每项任务。成功的操作记录到 `mission_report.txt`，而任何系统故障或错误警报则记录到 `mission_alerts.txt`，以便工程师能快速定位问题。

```bash
# 1. 准备诊断任务清单
echo "Check engine status" > diagnostics.txt
echo "Calibrate navigation" >> diagnostics.txt
echo "Access black_hole_data" >> diagnostics.txt # 这项任务会失败
echo "Verify life support" >> diagnostics.txt

echo "诊断任务清单 (diagnostics.txt) 已创建："
cat diagnostics.txt
echo "----------------------------------------"

# 2. 编写并执行“诊断程序”
# 这个 while 循环会逐行读取 diagnostics.txt 的内容。
# 我们用 `if` 语句模拟任务的成功与失败。
# 成功的消息 (echo) 默认输出到 stdout。
# 失败的消息 (echo ... >&2) 被特意发送到 stderr。
#
# 核心操作在最后一行：
# - `done < diagnostics.txt`: 将任务清单作为整个循环的输入。
# - `> mission_report.txt`: 将所有 stdout (成功日志) 存入报告。
# - `2> mission_alerts.txt`: 将所有 stderr (失败警报) 存入警报文件。

while read task; do
  if [[ "$task" == "Access black_hole_data" ]]; then
    # 模拟一个严重错误，输出到标准错误流 (stderr)
    echo "ALERT: Access to '$task' is forbidden! Quantum singularity detected!" >&2
  else
    # 模拟任务成功，输出到标准输出流 (stdout)
    echo "OK: Diagnostic for '$task' completed successfully."
  fi
done < diagnostics.txt > mission_report.txt 2> mission_alerts.txt

# 3. 查看最终报告
echo "✅ 任务报告 (mission_report.txt) 生成完毕:"
cat mission_report.txt

echo -e "\n🚨 紧急警报 (mission_alerts.txt) 已记录:"
cat mission_alerts.txt

# 预期输出:
# 诊断任务清单 (diagnostics.txt) 已创建：
# Check engine status
# Calibrate navigation
# Access black_hole_data
# Verify life support
# ----------------------------------------
# ✅ 任务报告 (mission_report.txt) 生成完毕:
# OK: Diagnostic for 'Check engine status' completed successfully.
# OK: Diagnostic for 'Calibrate navigation' completed successfully.
# OK: Diagnostic for 'Verify life support' completed successfully.
#
# 🚨 紧急警报 (mission_alerts.txt) 已记录:
# ALERT: Access to 'Access black_hole_data' is forbidden! Quantum singularity detected!
```
这个例子完美地将输入重定向、输出重定向和错误重定向结合起来，完成了一个自动化的分类和记录任务。

---

#### 💡 记忆要点

- **要点1: 三个标准流**：记住 `stdin (0)`、`stdout (1)`、`stderr (2)` 是所有命令与外部世界沟通的三个基本通道。
- **要点2: 箭头方向即数据流向**：`>` 和 `>>` 是把命令的输出“倒”进文件；`<` 是把文件的内容“喂”给命令。
- **要点3: `>` 覆盖, `>>` 追加**：`>` 是“全新写入”，会无情地清空旧内容；`>>` 是“继续添加”，会温柔地保留历史记录。
- **要点4: `2>` 专治错误**：`2>` 是分离和捕获错误信息的专用工具，是编写可靠、易于调试的自动化脚本的秘密武器。