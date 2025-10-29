好的，总建筑师。在掌握了重定向和管道这两个连接数据流的“管道工”技能后，我们现在要为这条流水线装上真正强大的“加工机器”。如果说管道是传送带，那么 `grep`、`sed` 和 `awk` 就是这条传送带上用于筛选、修改和分析产品的三台精密仪器。它们是命令行文本处理的“三剑客”，是每个高级用户工具箱中的必备利器。

我将严格按照您的设计图，为您呈现这精彩的一节。

---

### 3.3 文本处理三剑客：`grep`, `sed`, `awk`

#### 🎯 核心概念

`grep`、`sed` 和 `awk` 是 Unix/Linux 环境下三个功能强大的文本处理工具，它们是管道命令中的核心“处理器”，能让你在数据流中实现复杂的**文本过滤 (grep)**、**内容替换 (sed)** 和**数据提取与报告 (awk)**。

#### 💡 使用方式

这三位“剑客”虽然经常并肩作战，但各有专精：

*   **`grep` (Global Regular Expression Print)**: **行过滤器**。它的任务是从输入中找出并打印出**匹配特定模式的行**。
    *   基本用法: `grep '模式' 文件名`
*   **`sed` (Stream Editor)**: **行编辑器**。它的主要任务是**编辑**流经它的文本，最常用于**查找和替换**。
    *   基本用法: `sed 's/旧内容/新内容/g' 文件名`
*   **`awk` (Aho, Weinberger, Kernighan)**: **列处理器**。它是一个强大的文本分析工具，能将每一行按列（字段）切分，并执行编程逻辑，非常适合**提取数据和生成报告**。
    *   基本用法: `awk '{print $1, $3}' 文件名`

---

#### 📚 Level 1: 基础认知（30秒理解）

假设我们有一个简单的员工名单 `employees.txt`，内容如下：

```bash
# 准备一个员工名单文件
cat << EOF > employees.txt
101,Alice,Engineering,Active
102,Bob,Marketing,Active
103,Charlie,Engineering,On-leave
104,David,Sales,Active
EOF
```

现在，让我们看看三剑客如何各自完成一个简单任务：

**1. `grep`：找出所有工程师**

```bash
# 场景: 快速找到所有在 "Engineering" 部门的员工记录。
# grep 会逐行检查，如果行中包含 "Engineering"，就打印该行。
grep "Engineering" employees.txt

# 预期输出:
# 101,Alice,Engineering,Active
# 103,Charlie,Engineering,On-leave
```

**2. `sed`：将 "Active" 状态改为 "Online"**

```bash
# 场景: 全局更新员工状态的术语，将 "Active" 替换为 "Online"。
# sed 的 's/旧/新/g' 命令会替换每行中所有匹配的字符串。
sed 's/Active/Online/g' employees.txt

# 预期输出:
# 101,Alice,Engineering,Online
# 102,Bob,Marketing,Online
# 103,Charlie,Engineering,On-leave
# 104,David,Sales,Online
```

**3. `awk`：只显示员工姓名和部门**

```bash
# 场景: 生成一份只包含员工姓名和部门的简报。
# awk 默认按逗号(需要-F选项)或空格分割列，这里我们用-F指定逗号。
# $2 代表第2列（姓名），$3 代表第3列（部门）。
awk -F',' '{print "Name: " $2, "| Department: " $3}' employees.txt

# 预期输出:
# Name: Alice | Department: Engineering
# Name: Bob | Department: Marketing
# Name: Charlie | Department: Engineering
# Name: David | Department: Sales
```

```bash
# 清理环境
rm employees.txt
```

---

#### 📈 Level 2: 核心特性（深入理解）

掌握了基础后，我们来探索它们在管道中更强大的用法。

##### 特性1: `grep` 的高级过滤

`grep` 不仅仅是简单查找，它还能反向选择 (`-v`)、忽略大小写 (`-i`)、只显示匹配部分 (`-o`) 等。

```bash
# 场景: 分析系统日志 /var/log/system.log (我们用模拟文件代替)
# 目标: 找出所有非 "INFO" 级别的错误或警告日志。

# 1. 准备模拟日志
cat << EOF > system.log
INFO: System startup complete.
WARNING: Low disk space.
ERROR: Failed to connect to database.
INFO: User 'admin' logged in.
EOF

# 2. 使用管道和 grep -v (反向匹配)
# cat system.log: 读取日志内容。
# | grep -v "INFO": 过滤掉所有包含 "INFO" 的行。
cat system.log | grep -v "INFO"

# 预期输出:
# WARNING: Low disk space.
# ERROR: Failed to connect to database.

# 清理环境
rm system.log
```

##### 特性2: `sed` 的定点编辑

`sed` 不仅可以全局替换，还能通过行号或模式指定只对特定行进行操作。

```bash
# 场景: 我们有一个配置文件，需要修改其中某个特定配置项的值。
# 目标: 只修改 `DB_HOST` 的值为 `db.prod.internal`。

# 1. 准备模拟配置文件
cat << EOF > config.conf
APP_NAME=MyWebApp
DB_HOST=localhost
DB_USER=root
EOF

# 2. 使用 sed 的模式匹配进行替换
# `/DB_HOST/` 是一个地址模式，它告诉 sed 只在包含 "DB_HOST" 的那一行执行 s/.../.../ 命令。
sed '/DB_HOST/s/localhost/db.prod.internal/' config.conf

# 预期输出:
# APP_NAME=MyWebApp
# DB_HOST=db.prod.internal
# DB_USER=root

# 清理环境
rm config.conf
```

##### 特性3: `awk` 的计算与格式化

`awk` 最强大的地方在于它能像处理电子表格一样处理文本，进行计算和重新格式化。

```bash
# 场景: 统计一个目录下所有文件占用的总大小。
# `ls -l` 的输出中，第5列是文件大小（以字节为单位）。

# 1. 准备一些文件
touch file1.txt file2.txt
echo "hello" > file1.txt
echo "hello world" > file2.txt

# 2. 使用 ls -l 和 awk 进行计算
# `ls -l`: 列出文件详情。
# `awk '{sum += $5} END {print "Total size:", sum, "bytes"}'`:
#   - 对于每一行 (`{...}`): 将第5列($5)的值累加到变量 `sum` 中。
#   - 所有行处理完毕后 (`END {...}`): 打印最终结果。
ls -l file*.txt | awk '{sum += $5} END {print "Total size:", sum, "bytes"}'

# 预期输出: (具体数字可能因系统而异，但格式和计算逻辑是正确的)
# Total size: 18 bytes

# 清理环境
rm file1.txt file2.txt
```

---

#### 🔍 Level 3: 对比学习（避免陷阱）

三剑客的定位非常清晰，混用或错用会导致效率低下。让我们用一个任务来对比它们的职责。

**任务：** 从一份服务器日志 `server.log` 中，找出所有包含 "payment" 的错误记录，并将 "error" 标记为大写的 "URGENT"，最后提取出日期和错误ID。

```bash
# 准备日志文件
cat << EOF > server.log
2023-11-21 INFO [auth-service] User login successful
2023-11-22 error [payment-service:id-845] Payment failed
2023-11-22 INFO [shipping-service] Order shipped
2023-11-23 error [payment-service:id-912] Credit card expired
EOF
```

##### === `grep` 的用法 (只找) ===

`grep` 擅长第一步：筛选。但它无法修改内容或提取特定字段。

```bash
# ✅ grep 完美地完成了筛选任务
grep "payment" server.log

# 预期输出:
# 2023-11-22 error [payment-service:id-845] Payment failed
# 2023-11-23 error [payment-service:id-912] Credit card expired
```

##### === `grep | sed` 的组合 (找和改) ===

`sed` 在 `grep` 的基础上，可以完成修改任务。

```bash
# ✅ grep 筛选出相关行，然后 sed 进行替换
grep "payment" server.log | sed 's/error/URGENT/'

# 预期输出:
# 2023-11-22 URGENT [payment-service:id-845] Payment failed
# 2023-11-23 URGENT [payment-service:id-912] Credit card expired
```

##### === `grep | sed | awk` 的终极流水线 (找、改、算) ===

最后，`awk` 登场，从修改后的结果中提取并格式化我们想要的数据。

```bash
# ✅ grep 筛选 -> sed 修改 -> awk 提取和格式化
grep "payment" server.log | sed 's/error/URGENT/' | awk '{print "Date:", $1, "Error ID:", $3}'

# 预期输出:
# Date: 2023-11-22 Error ID: [payment-service:id-845]
# Date: 2023-11-23 Error ID: [payment-service:id-912]
```

**结论**：
*   **`grep`** 是侦察兵，负责**找**到目标。
*   **`sed`** 是工兵，负责对找到的目标进行**修改**或“爆破”。
*   **`awk`** 是情报分析员，负责对目标信息进行**提取、分析和重新格式化**，生成报告。

```bash
# 清理环境
rm server.log
```

---

#### 🚀 Level 4: 实战应用（真实场景）

**场景：📜 古代卷轴破译机器人**

我们发现了一份来自外星文明的数字卷轴 `scroll.txt`，里面混杂着正常的日志、损坏的数据和重要的警报。我们的任务是编写一个单行命令，自动破译出所有来自 "Hoth" 星球的**紧急事件报告**。

报告要求：
1.  只处理来自 "Hoth" 星球的有效日志（以 `LOG:` 开头）。
2.  将所有 `STATUS=ERROR` 的记录提升为 `STATUS=CRITICAL`。
3.  最终只输出 `CRITICAL` 或 `ALERT` 级别的事件。
4.  报告格式为：`Hoth Event Report -> ID: [事件ID], Message: [事件消息]`。

```bash
# 1. 准备神秘的卷轴数据
cat << EOF > scroll.txt
LOG:ID=AX12,PLANET=Tatooine,STATUS=OK,MSG=Water vaporator functional.
CORRUPT-DATA-ENTRY-@#$!
LOG:ID=BX77,PLANET=Hoth,STATUS=ERROR,MSG=Tauntaun frozen.
LOG:ID=CZ34,PLANET=Coruscant,STATUS=OK,MSG=Speeder traffic normal.
WARNING: Unstable power fluctuation on ID=BX77
LOG:ID=DY91,PLANET=Hoth,STATUS=ALERT,MSG=Wampa sighting near base.
EOF

echo "📜 原始卷轴内容 (scroll.txt):"
cat scroll.txt
echo "----------------------------------------"

# 2. 构建一键式破译流水线
echo "🤖 启动破译机器人，生成霍斯星紧急报告..."
cat scroll.txt | \
    grep "^LOG.*PLANET=Hoth" | \
    sed 's/STATUS=ERROR/STATUS=CRITICAL/' | \
    awk -F '[,=]' '/CRITICAL|ALERT/ {print "Hoth Event Report -> ID: " $4 ", Message: " $8}'

# 步骤分解:
# 1. `cat scroll.txt`: 读取卷轴内容。
# 2. `grep "^LOG.*PLANET=Hoth"`: (侦察兵) 筛选出所有以 "LOG:" 开头且包含 "PLANET=Hoth" 的有效记录。
# 3. `sed 's/STATUS=ERROR/STATUS=CRITICAL/'`: (工兵) 将所有错误状态提升为更醒目的 "CRITICAL"。
# 4. `awk -F '[,=]' '/CRITICAL|ALERT/ {print ...}`: (分析员)
#    - `-F '[,=]'`: 将分隔符设为逗号或等号，这样就能精确提取键和值。
#    - `/CRITICAL|ALERT/`: 只处理包含 "CRITICAL" 或 "ALERT" 的行。
#    - `{print ...}`: 提取第4个字段(ID值)和第8个字段(消息)，并按指定格式打印。

# 3. 清理环境
rm scroll.txt

# 预期输出:
# 📜 原始卷轴内容 (scroll.txt):
# LOG:ID=AX12,PLANET=Tatooine,STATUS=OK,MSG=Water vaporator functional.
# CORRUPT-DATA-ENTRY-@#$!
# LOG:ID=BX77,PLANET=Hoth,STATUS=ERROR,MSG=Tauntaun frozen.
# LOG:ID=CZ34,PLANET=Coruscant,STATUS=OK,MSG=Speeder traffic normal.
# WARNING: Unstable power fluctuation on ID=BX77
# LOG:ID=DY91,PLANET=Hoth,STATUS=ALERT,MSG=Wampa sighting near base.
# ----------------------------------------
# 🤖 启动破译机器人，生成霍斯星紧急报告...
# Hoth Event Report -> ID: BX77, Message: Tauntaun frozen.
# Hoth Event Report -> ID: DY91, Message: Wampa sighting near base.
```
这个复杂的任务通过一行命令优雅地解决了，完美展现了三剑客组合在管道中的强大威力。

---

#### 💡 记忆要点

-   **要点1: 各司其职**：`grep` 是**侦察兵**（按行查找），`sed` 是**外科医生**（按行修改），`awk` 是**会计师/数据分析师**（按列提取、计算、格式化）。
-   **要点2: `grep` 找什么**：它的核心是**过滤**，从大量文本中筛选出你关心的**行**。它只看不改。
-   **要点3: `sed` 改什么**：它的核心是**替换**，`s/旧/新/g` 是它的招牌动作，用于修改流经它的文本**行**。
-   **要点4: `awk` 算什么**：它的核心是**按列处理**。它将每一行视为一条记录，将空格或分隔符分开的内容视为字段 (`$1`, `$2`...)，可以进行编程逻辑处理，非常适合生成结构化报告。