### 🎯 核心概念
继上一节的别名之后，Shell 脚本是自动化的下一个飞跃：它将一系列复杂的命令封装成一个可执行文件，通过引入变量、判断和循环等编程元素，实现一键完成更智能、更复杂的重复性任务。

### 💡 使用方式
一个基础的 Shell 脚本由以下几个核心部分构成：

1.  **Shebang (解释器指令)**: 脚本的第一行，以 `#!` 开头，例如 `#!/bin/bash`。它告诉操作系统使用哪个解释器（在这里是 Bash）来执行此文件。
2.  **执行权限**: 默认情况下，文本文件是没有执行权限的。我们必须使用 `chmod +x <script_name>` 命令来赋予它可执行的权限，这样才能像普通命令一样运行它。
3.  **变量**: 使用 `VARIABLE_NAME="value"` 的形式定义变量（注意等号两边没有空格），使用 `$VARIABLE_NAME` 来引用它的值。
4.  **条件语句**: 使用 `if-then-fi` 结构来执行条件判断。
    *   基本语法: `if [ condition ]; then ... fi`
    *   `[ -z "$VAR" ]` 检查变量是否为空。
    *   `[ -f "$FILE" ]` 检查文件是否存在且为普通文件。
5.  **循环语句**: 用于重复执行代码块。
    *   **for 循环**: 遍历一个列表。`for i in 1 2 3; do echo $i; done`
    *   **while 循环**: 当条件为真时持续执行。`while [ condition ]; do ... done`
6.  **特殊变量**: 脚本中有一些预定义的特殊变量非常有用。
    *   `$0`: 脚本自身的名称。
    *   `$1`, `$2`, ...: 传递给脚本的第一个、第二个参数。
    *   `$@`: 所有传递给脚本的参数列表。
    *   `$#`: 传递给脚本的参数总数。

### 📚 Level 1: 基础认知（30秒理解）
让我们从最简单的脚本开始：创建一个脚本，它会定义一个变量并向你问好。这展示了脚本的三个最基本步骤：创建、赋权、执行。

```bash
# 1. 使用 cat 和 EOF 界定符，一次性创建完整的 hello.sh 脚本
# 这种方法比多行 echo 更清晰，也与后续示例保持一致
cat << 'EOF' > hello.sh
#!/bin/bash
# 第一行是 shebang，告诉系统用 bash 解释器
# 第二行定义一个变量 USER_NAME
# 第三行使用 echo 命令打印问候语，并引用该变量
USER_NAME="Alice"
echo "Hello, $USER_NAME! Welcome to the world of scripting."
EOF

# 2. 赋予脚本执行权限
chmod +x hello.sh

# 3. 执行脚本
# './' 表示当前目录，告诉 Shell 在这里找到并运行 hello.sh
./hello.sh

# 预期输出：
# Hello, Alice! Welcome to the world of scripting.
```

### 📚 Level 2: 实战应用（2分钟掌握）
现在，我们来编写一个真正有用的脚本：一个简单的文件备份工具。这个脚本将接收一个文件名作为参数，然后将其复制到一个 `backup` 目录下，并附上当前的时间戳，同时它还会检查用户是否提供了文件名。

```bash
# 1. 准备一个用于备份的测试文件
echo "This is my important file." > report.txt
echo "Original content." >> report.txt

# 2. 使用 cat 和 EOF 界定符，一次性创建完整的 backup.sh 脚本
# 这种方法比多行 echo 更清晰
cat << 'EOF' > backup.sh
#!/bin/bash
# 一个简单的备份脚本

# 检查用户是否提供了文件名参数（$1）
# -z 表示检查字符串是否为空
if [ -z "$1" ]; then
  # 如果为空，打印用法提示并以错误状态退出
  echo "用法: $0 <文件名>" # $0 是脚本自己的名字
  exit 1
fi

# 定义变量
FILENAME=$1
BACKUP_DIR="./backup"
TIMESTAMP=$(date +%Y%m%d-%H%M%S) # 执行命令并将输出存入变量

# -p 选项确保如果目录不存在，会自动创建它
# 使用双引号包裹变量是一个好习惯，可以防止因目录名包含空格等特殊字符而出错
mkdir -p "$BACKUP_DIR"

# 执行核心的复制操作
cp "$FILENAME" "$BACKUP_DIR/${FILENAME}.${TIMESTAMP}"

echo "成功: '$FILENAME' 的备份已创建于 '$BACKUP_DIR' 目录。"
EOF

# 3. 赋予脚本执行权限
chmod +x backup.sh

# 4. 场景一：不带参数运行，触发条件判断
./backup.sh
# 预期输出：
# 用法: ./backup.sh <文件名>

# 5. 场景二：正确运行
./backup.sh report.txt
# 预期输出：
# 成功: 'report.txt' 的备份已创建于 './backup' 目录。

# 6. 验证备份文件是否已创建
ls -l backup/
# 预期输出 (时间戳会不同):
# -rw-r--r-- 1 user group 46 Dec 10 10:30 report.txt.20231210-103000
```

### 📚 Level 3: 高阶进阶（5分钟精通）
让我们升级备份脚本，使其更强大、更健壮。新版本将能够：
1.  使用 `for` 循环接收任意数量的文件进行批量备份。
2.  在备份前检查文件是否存在，跳过不存在的文件或目录。

```bash
# 1. 准备多个测试文件和一个目录，用于演示批量处理和错误检查
echo "Log data 1" > app.log
echo "Config data" > config.ini
mkdir -p temp_dir
ls -F
# 预期输出 (可能包含其他文件):
# app.log  config.ini  temp_dir/

# 2. 创建功能更强的 multi_backup.sh 脚本
cat << 'EOF' > multi_backup.sh
#!/bin/bash
# 一个可以批量备份文件的脚本

# 检查参数数量是否为0
if [ $# -eq 0 ]; then
  echo "用法: $0 <文件1> [文件2] ..."
  exit 1
fi

BACKUP_DIR="./backup_multi"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
mkdir -p "$BACKUP_DIR"

# 使用 for 循环遍历所有命令行参数 ("$@")
for FILE in "$@"; do
  # 检查参数是否是一个存在且可读的普通文件
  if [ -f "$FILE" ] && [ -r "$FILE" ]; then
    cp "$FILE" "$BACKUP_DIR/${FILE}.${TIMESTAMP}"
    echo "✅ 成功: '$FILE' 已备份。"
  else
    # 如果不是常规文件或不可读，打印警告信息
    echo "⚠️ 警告: '$FILE' 不是一个常规文件或不可读，已跳过。"
  fi
done

echo "批量备份完成。"
EOF

# 3. 赋予执行权限
chmod +x multi_backup.sh

# 4. 执行脚本，提供两个有效文件、一个不存在的文件和一个目录作为参数
./multi_backup.sh app.log config.ini no_such_file.txt temp_dir

# 预期输出：
# ✅ 成功: 'app.log' 已备份。
# ✅ 成功: 'config.ini' 已备份。
# ⚠️ 警告: 'no_such_file.txt' 不是一个常规文件或不可读，已跳过。
# ⚠️ 警告: 'temp_dir' 不是一个常规文件或不可读，已跳过。
# 批量备份完成。

# 5. 验证结果
ls -l backup_multi/
# 预期输出 (时间戳会不同):
# -rw-r--r-- 1 user group 11 Dec 10 10:35 app.log.20231210-103500
# -rw-r--r-- 1 user group 12 Dec 10 10:35 config.ini.20231210-103500

# 清理演示文件
rm -r hello.sh backup.sh multi_backup.sh report.txt app.log config.ini temp_dir backup backup_multi
```