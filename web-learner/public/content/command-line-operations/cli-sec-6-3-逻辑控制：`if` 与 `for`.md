好的，总建筑师。在前两章中，我们已经学会了如何创建脚本以及如何使用变量和参数让它们变得灵活。现在，是时候为我们的脚本装上“大脑”和“引擎”了。我们将赋予它们判断是非、做出选择的能力，以及不知疲倦、重复执行任务的能力。

作为您的世界级技术教育者和命令行专家，我将依据这份新的“教学设计图”，为您续写这篇高质量的 Markdown 教程。

---

### 章节 6.3：逻辑控制：`if` 与 `for`

🎯 **核心概念**
`if` 条件判断和 `for` 循环是脚本的“决策中心”和“执行引擎”，它们让脚本能够根据不同的情况执行不同的代码路径，或者对一组项目重复执行相同的操作，这是实现复杂自动化逻辑的基石。

💡 **使用方式**
掌握逻辑控制的核心在于理解它们的结构：

1.  **条件判断 (if)**: `if [ 条件 ]; then ... fi` 结构用于“如果满足某个条件，就做某件事”。
2.  **循环遍历 (for)**: `for 变量 in 列表; do ... done` 结构用于“对列表中的每一个项目，都做一遍某件事”。

📚 **Level 1: 基础认知（30秒理解）**
让我们通过两个最简单的例子，快速感受 `if` 的判断能力和 `for` 的重复能力。

**`if` 的初体验：检查文件是否存在**
`if` 就像一个哨兵，它会检查一个条件是否为真。

```bash
# 创建脚本 check_file.sh
cat > check_file.sh << EOF
#!/bin/bash
# -f 是一个测试操作符，用来检查 "secret_mission.txt" 是否是一个存在的文件
if [ -f "secret_mission.txt" ]; then
  echo "发现任务文件！准备执行..."
else
  echo "未找到任务文件，保持待命。"
fi
EOF

chmod +x check_file.sh

# 第一次执行，文件不存在
./check_file.sh
# 预期输出:
# 未找到任务文件，保持待命。

# 创建一个文件，再试一次
touch secret_mission.txt
./check_file.sh
# 预期输出:
# 发现任务文件！准备执行...
```

**`for` 的初体验：倒计时**
`for` 就像一个计数器，它会逐一取出列表中的元素并执行操作。

```bash
# 创建脚本 countdown.sh
cat > countdown.sh << EOF
#!/bin/bash
# {5..1} 会生成一个序列: 5 4 3 2 1
echo "火箭发射倒计时开始..."
for i in {5..1}; do
  echo "$i..."
  sleep 1 # sleep 1 表示暂停1秒
done
echo "发射！🚀"
EOF

chmod +x countdown.sh
./countdown.sh

# 预期输出 (每秒打印一行):
# 火箭发射倒计时开始...
# 5...
# 4...
# 3...
# 2...
# 1...
# 发射！🚀
```

---

📈 **Level 2: 核心特性（深入理解）**
`if` 和 `for` 的真正威力在于它们处理各种数据和情况的灵活性。

**特性1: `if` 的多样判断——不止检查文件**
`if` 配合不同的测试操作符，可以比较数字、判断字符串，让脚本的决策更加智能。

*   **数字比较**: `-eq` (等于), `-ne` (不等于), `-gt` (大于), `-lt` (小于)。
*   **字符串比较**: `==` 或 `=` (等于), `!=` (不等于), `-z` (检查字符串是否为空)。

```bash
# 创建脚本 access_control.sh
cat > access_control.sh << EOF
#!/bin/bash
ACCESS_LEVEL=$1 # 从第一个参数获取访问级别
AGENT_NAME=$2   # 从第二个参数获取特工代号

# 数字比较：检查访问级别是否大于 5
if [ "$ACCESS_LEVEL" -gt 5 ]; then
  echo "权限等级 $ACCESS_LEVEL，授权通过。"
else
  echo "权限等级 $ACCESS_LEVEL，权限不足！"
  exit 1 # 退出脚本
fi

# 字符串比较：检查代号是否为空
if [ -z "$AGENT_NAME" ]; then
  echo "错误：未提供特工代号！"
else
  echo "欢迎，特工 $AGENT_NAME。"
fi
EOF

chmod +x access_control.sh

# 场景1: 权限足够，但未提供代号
./access_control.sh 7
# 预期输出:
# 权限等级 7，授权通过。
# 错误：未提供特工代号！

# 场景2: 权限不足
./access_control.sh 3 "007"
# 预期输出:
# 权限等级 3，权限不足！
```

**特性2: `for` 的百变遍历——不止遍历数字**
`for` 循环可以遍历任何由空格分隔的列表，最强大的应用之一是遍历文件名。

```bash
# 创建脚本 backup_logs.sh
# 首先，创建一些假的日志文件用于测试
touch system.log auth.log kernel.log data.csv

cat > backup_logs.sh << EOF
#!/bin/bash
# *.log 是一个通配符，它会匹配当前目录下所有以 .log 结尾的文件
BACKUP_DIR="backup-$(date +%F)"
mkdir -p $BACKUP_DIR # 创建备份目录

echo "开始备份日志文件到 $BACKUP_DIR/"
for file in *.log; do
  echo "正在处理: $file"
  cp "$file" "$BACKUP_DIR/"
done

echo "备份完成！"
ls $BACKUP_DIR
EOF

chmod +x backup_logs.sh
./backup_logs.sh

# 预期输出:
# 开始备份日志文件到 backup-2023-10-27/
# 正在处理: auth.log
# 正在处理: kernel.log
# 正在处理: system.log
# 备份完成！
# auth.log  kernel.log  system.log
```

---

🔍 **Level 3: 对比学习（避免陷阱）**
初学者在使用 `if` 语句时，最容易掉进 `[` 和 `]` 两边空格的陷阱。

```bash
# === 错误用法 ===
# ❌ [ 和 ] 与条件紧紧贴在一起

# 1. 创建脚本
cat > bad_if.sh << EOF
#!/bin/bash
STATUS="ok"
# 注意 [ 和 "ok" 之间，以及 "ok" 和 ] 之间没有空格
if ["$STATUS"=="ok"]; then
  echo "状态正常。"
fi
EOF

# 2. 赋予权限并尝试执行
chmod +x bad_if.sh
./bad_if.sh

# 你会看到这样的错误信息:
# ./bad_if.sh: line 4: [ok==ok]: command not found

# 解释为什么是错的:
# 在 Shell 中，`[` 实际上是一个命令（等同于 `test` 命令），而不是一个语法符号。
# 因此，它必须像其他命令一样，与它的参数（也就是你要判断的条件）用空格隔开。
# 当你写 `["$STATUS"=="ok"]` 时，Shell 会把它看成一个单独的、名为 `[ok==ok]` 的命令，
# 系统里当然找不到这个命令，于是报错。

# === 正确用法 ===
# ✅ 在 [ 和 ] 的两边都保留空格

# 1. 创建脚本
cat > good_if.sh << EOF
#!/bin/bash
STATUS="ok"
# ✨ 关键：[ 后面和 ] 前面必须有空格 ✨
if [ "$STATUS" == "ok" ]; then
  echo "状态正常。"
fi
EOF

# 2. 赋予权限并执行
chmod +x good_if.sh
./good_if.sh

# 预期输出:
# 状态正常。

# 解释为什么这样是对的:
# `[ "$STATUS" == "ok" ]` 被 Shell 正确地解析为：
# 1. 执行 `[` 命令。
# 2. 传递 `"$STATUS"`、`==`、`"ok"` 和 `]` 作为参数给它。
# `[` 命令接收这些参数后进行逻辑判断，然后返回一个成功或失败的状态码，`if` 语句根据这个状态码决定是否执行 `then` 后面的代码块。
```

---

🚀 **Level 4: 实战应用（真实场景）**
**场景示例：📦 智能仓库盘点机器人**
你负责编写一个自动化脚本，模拟一个机器人在仓库中盘点货物。仓库里的“货物”就是各种文件，机器人需要遍历所有货物，根据货物的类型（文件名后缀）进行分类处理。

```bash
# 脚本名称: inventory_robot.sh

# 1. 准备工作：创建一些模拟的货物文件
mkdir -p warehouse # 创建仓库目录
touch warehouse/parts-A7.data
touch warehouse/parts-B2.data
touch warehouse/report-2023.log
touch warehouse/manual.pdf
touch warehouse/unknown-item

# 2. 创建并编写机器人脚本
cat > inventory_robot.sh << 'EOF'
#!/bin/bash
# --- 🤖 智能仓库盘点机器人 ---

# 检查仓库目录是否存在
if [ ! -d "warehouse" ]; then
  echo "错误：'warehouse' 目录不存在！"
  exit 1
fi

echo -e "\033[1;34m🤖 盘点任务启动... 目标：warehouse/ 目录\033[0m"
echo "=============================================="

# 使用 for 循环遍历仓库中的所有文件
for item in warehouse/*; do
  # 使用 if-elif-else 结构进行多条件判断
  if [[ "$item" == *.data ]]; then
    # 如果文件名以 .data 结尾
    echo -e "✅ \033[1;32m[核心零件]\033[0m  $item  -> 已归档至高价值区。"
  elif [[ "$item" == *.log ]]; then
    # 如果文件名以 .log 结尾
    echo -e "📋 \033[0;37m[操作日志]\033[0m  $item  -> 已发送至分析中心。"
  elif [[ "$item" == *.pdf ]]; then
    # 如果文件名以 .pdf 结尾
    echo -e "📚 \033[0;33m[说明手册]\033[0m  $item  -> 已存入知识库。"
  else
    # 其他所有情况
    echo -e "❓ \033[1;31m[未知物品]\033[0m  $item  -> 警告！需要人工检查！"
  fi
done

echo "=============================================="
echo -e "\033[1;34m🤖 盘点任务完成！\033[0m"
EOF

# 3. 赋予执行权限
chmod +x inventory_robot.sh

# 4. 运行机器人！
./inventory_robot.sh
```

**运行脚本后的预期输出：**
（文件顺序可能不同）
```
🤖 盘点任务启动... 目标：warehouse/ 目录
==============================================
✅ [核心零件]  warehouse/parts-A7.data  -> 已归档至高价值区。
✅ [核心零件]  warehouse/parts-B2.data  -> 已归档至高价值区。
📚 [说明手册]  warehouse/manual.pdf  -> 已存入知识库。
📋 [操作日志]  warehouse/report-2023.log  -> 已发送至分析中心。
❓ [未知物品]  warehouse/unknown-item  -> 警告！需要人工检查！
==============================================
🤖 盘点任务完成！
```

---

💡 **记忆要点**
- **要点1: `if` 做选择，`for` 做重复**: `if [ condition ]; then ... fi` 用于决策，`for var in list; do ... done` 用于循环。
- **要点2: `[ ]` 内有乾坤，但需空格**: `[` 是一个命令，它的前后必须有空格。这是最致命也最常见的语法错误。
- **要点3: 变量加引号，脚本更健壮**: 在 `if` 判断中，始终用双引号把变量包起来（如 `[ "$VAR" == "value" ]`），可以防止变量为空或包含空格时出错。
- **要点4: `*` 是 `for` 的好搭档**: `for file in *.txt` 是处理一批文件的经典模式，极其实用。