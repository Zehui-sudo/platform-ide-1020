--- 

在“7.1 我的第一个脚本”中，我们学习了如何创建、执行基本脚本，以及使用变量和命令替换。然而，这些脚本通常是线性执行的，缺乏根据不同情况做出决策或重复特定任务的能力。

现在，我们将为脚本注入“智慧”，使其能够根据条件判断选择不同的执行路径，或者循环执行一系列操作。这正是流程控制的核心：让你的自动化脚本更加灵活、强大和实用。

### 🎯 核心概念
流程控制允许脚本根据预设的条件**做出决策**（条件判断）或**重复执行**特定任务（循环），从而使其能够响应动态环境并实现更复杂的自动化逻辑。它将脚本从简单的指令序列升级为智能的自动化程序。

### 💡 使用方式
Shell 脚本提供了多种流程控制结构，其中最常用的是条件判断（`if-then-else`）和循环（`for` 循环）。这些结构通常与 `test` 命令或其简写形式 `[]` 结合使用来评估条件。

1.  **条件判断：`if-then-else`**
    根据一个或多个条件的真假来执行不同的代码块。
    *   **基本语法**:
        ```bash
        if condition; then
            # 如果 condition 为真，执行这里的命令
        elif another_condition; then # 可选
            # 如果 another_condition 为真，执行这里的命令
        else # 可选
            # 如果所有条件都为假，执行这里的命令
        fi
        ```
    *   **核心**: `condition` 部分通常是一个命令或一组命令的序列。`if` 语句会检查最后一个命令的退出状态码：`0` 表示真（成功），非 `0` 表示假（失败）。

2.  **测试命令：`test` 或 `[]`**
    专门用于评估各种条件的内置命令，其退出状态码可以被 `if` 语句利用。
    *   **语法**:
        *   `test expression`
        *   `[ expression ]` (注意 `[` 和 `]` 左右都必须有空格)
        *   `[[ expression ]]` (Bash 特有的增强版，支持更多高级特性，如正则匹配，更推荐在 Bash 脚本中使用)
    *   **常见条件表达式**:
        *   **字符串比较**:
            *   `-z STRING`: 如果 STRING 长度为零则为真 (空字符串)。
            *   `-n STRING`: 如果 STRING 长度非零则为真 (非空字符串)。
            *   `STRING1 = STRING2`: 如果 STRING1 和 STRING2 相等则为真。
            *   `STRING1 != STRING2`: 如果 STRING1 和 STRING2 不相等则为真。
        *   **数值比较**: (注意：`=`, `!=` 也用于字符串比较，数值比较使用以下)
            *   `NUM1 -eq NUM2`: 如果 NUM1 等于 NUM2 则为真。
            *   `NUM1 -ne NUM2`: 如果 NUM1 不等于 NUM2 则为真。
            *   `NUM1 -gt NUM2`: 如果 NUM1 大于 NUM2 则为真。
            *   `NUM1 -ge NUM2`: 如果 NUM1 大于或等于 NUM2 则为真。
            *   `NUM1 -lt NUM2`: 如果 NUM1 小于 NUM2 则为真。
            *   `NUM1 -le NUM2`: 如果 NUM1 小于或等于 NUM2 则为真。
        *   **文件测试**:
            *   `-f FILE`: 如果 FILE 存在且是普通文件则为真。
            *   `-d DIR`: 如果 DIR 存在且是目录则为真。
            *   `-e PATH`: 如果 PATH 存在则为真 (文件或目录)。
            *   `-r FILE`: 如果 FILE 存在且可读则为真。
            *   `-w FILE`: 如果 FILE 存在且可写则为真。
            *   `-x FILE`: 如果 FILE 存在且可执行则为真。
        *   **逻辑组合**:
            *   `[ EXPR1 -a EXPR2 ]`: 如果 EXPR1 和 EXPR2 都为真则为真 (AND)。
            *   `[ EXPR1 -o EXPR2 ]`: 如果 EXPR1 或 EXPR2 为真则为真 (OR)。
            *   `[[ EXPR1 && EXPR2 ]]`: 推荐的 AND 逻辑 (在 `[[...]]` 中)。
            *   `[[ EXPR1 || EXPR2 ]]`: 推荐的 OR 逻辑 (在 `[[...]]` 中)。

3.  **`for` 循环**
    重复执行一个命令序列，通常用于遍历一个列表（例如，文件列表、数字序列、命令行参数）。
    *   **基本语法**:
        ```bash
        for variable in item1 item2 ... itemN; do
            # 对每个 item 执行这里的命令
            # 可以使用 $variable 访问当前 item
        done
        ```
    *   **数字序列循环**:
        ```bash
        for i in {1..5}; do # 从1到5的数字序列 (Bash 特有)
            echo "当前数字是: $i"
        done
        # 或
        for ((i=1; i<=5; i++)); do # C 风格循环 (Bash 特有)
            echo "当前数字是: $i"
        done
        ```
    *   **遍历命令行参数**:
        ```bash
        for arg in "$@"; do # 遍历所有传入的命令行参数
            echo "处理参数: $arg"
        done
        ```

### 📚 Level 1: 基础认知（30秒理解）
```bash
#!/bin/bash
# 文件名: 7.2_flow_control.sh

# 1. 变量定义
DEFAULT_NUMBER=5
INPUT_NUMBER=""

# 2. 条件判断: 检查是否提供了命令行参数
#    [ -n "$1" ] 检查第一个参数 $1 是否非空。
if [ -n "$1" ]; then
  INPUT_NUMBER="$1"
  echo "✅ 检测到命令行参数: $INPUT_NUMBER"
else
  # 如果没有提供参数，则提示用户输入
  read -p "请输入一个整数 (默认值: $DEFAULT_NUMBER): " USER_INPUT
  # 如果用户输入为空，则使用默认值
  if [ -z "$USER_INPUT" ]; then
    INPUT_NUMBER="$DEFAULT_NUMBER"
    echo "使用默认值: $INPUT_NUMBER"
  else
    INPUT_NUMBER="$USER_INPUT"
  fi
fi

# 3. 验证输入是否为有效数字 (使用 Bash 的 [[ ]] 更强大)
if ! [[ "$INPUT_NUMBER" =~ ^[0-9]+$ ]]; then
  echo "❌ 输入 '$INPUT_NUMBER' 不是一个有效的正整数。脚本退出。"
  exit 1
fi

# 将输入转换为整数，方便后续数值判断
NUMBER_TO_PROCESS=$((INPUT_NUMBER + 0)) # 加0强制转换为整数

# 4. 再次条件判断: 判断数字的奇偶性
#    使用算术表达式 $((...)) 计算余数，然后用 -eq 进行数值比较。
if [ $((NUMBER_TO_PROCESS % 2)) -eq 0 ]; then
  echo "➡️ 数字 $NUMBER_TO_PROCESS 是一个偶数。"
else
  echo "➡️ 数字 $NUMBER_TO_PROCESS 是一个奇数。"
fi

echo "--- 开始从 1 循环到 $NUMBER_TO_PROCESS ---"

# 5. for 循环: 从 1 遍历到 NUMBER_TO_PROCESS
#    Bash 的 C 风格 for 循环 ((...)) 更适合数字范围迭代。
for ((i=1; i<=NUMBER_TO_PROCESS; i++)); do
  echo "当前循环计数: $i"
  # 在循环内部也可以有条件判断
  if [ "$i" -eq 3 ]; then
    echo "  (特别提醒: 到达数字 3 了!)"
  fi
done

echo "--- 循环结束 ---"

# --- 运行和预期输出 ---
# 1. 保存上述内容为文件 7.2_flow_control.sh
# 2. 赋予执行权限: chmod +x 7.2_flow_control.sh

# 3. 运行脚本（不带参数，输入 7）:
#    ./7.2_flow_control.sh
# 预期输出:
# 请输入一个整数 (默认值: 5): 7
# ➡️ 数字 7 是一个奇数。
# --- 开始从 1 循环到 7 ---
# 当前循环计数: 1
# 当前循环计数: 2
# 当前循环计数: 3
#   (特别提醒: 到达数字 3 了!)
# 当前循环计数: 4
# 当前循环计数: 5
# 当前循环计数: 6
# 当前循环计数: 7
# --- 循环结束 ---

# 4. 运行脚本（不带参数，输入空，使用默认值 5）:
#    ./7.2_flow_control.sh
# 预期输出:
# 请输入一个整数 (默认值: 5): 
# 使用默认值: 5
# ➡️ 数字 5 是一个奇数。
# --- 开始从 1 循环到 5 ---
# 当前循环计数: 1
# 当前循环计数: 2
# 当前循环计数: 3
#   (特别提醒: 到达数字 3 了!)
# 当前循环计数: 4
# 当前循环计数: 5
# --- 循环结束 ---

# 5. 运行脚本（带参数 4）:
#    ./7.2_flow_control.sh 4
# 预期输出:
# ✅ 检测到命令行参数: 4
# ➡️ 数字 4 是一个偶数。
# --- 开始从 1 循环到 4 ---
# 当前循环计数: 1
# 当前循环计数: 2
# 当前循环计数: 3
#   (特别提醒: 到达数字 3 了!)
# 当前循环计数: 4
# --- 循环结束 ---

# 6. 运行脚本（带非法参数）:
#    ./7.2_flow_control.sh "hello"
# 预期输出:
# ✅ 检测到命令行参数: hello
# ❌ 输入 'hello' 不是一个有效的正整数。脚本退出。
```