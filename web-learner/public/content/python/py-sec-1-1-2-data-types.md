好的，作为一名顶级的Python教育专家，我将为你生成关于 **“基本数据类型 (int, float, str, bool)”** 的详细教学内容。

---

## 基本数据类型 (int, float, str, bool)

### 🎯 核心概念
数据类型是Python理解和处理各种信息的**蓝图**。它告诉计算机一个值是**数字**、**文本**还是**逻辑判断**，从而决定能对这个值进行哪些操作（比如数字可以加减，文本可以变大写）。

### 💡 使用方式
在Python中，当你给变量赋值时，它的数据类型就自动确定了，你不需要预先声明。这就像给一个盒子贴标签，放进去的是苹果，它就是“水果盒”；放进去的是书，它就是“书盒”。

- **整数 (int):** 没有小数点的数字。
  - `age = 30`
- **浮点数 (float):** 带有小数点的数字。
  - `price = 19.99`
- **字符串 (str):** 用单引号 `' '` 或双引号 `" "` 包裹起来的文本。
  - `name = "艾克"`
- **布尔值 (bool):** 只有两个值，`True` (真) 或 `False` (假)，用于逻辑判断。
  - `is_logged_in = True`

### 📚 Level 1: 基础认知（30秒理解）
让我们为一款游戏创建一个角色，并定义他的基本属性。这四个类型立刻就能派上用场！

```python
# 为游戏角色“雷神”定义基本属性
character_name = "雷神"   # 字符串 (str): 角色的名字
level = 99              # 整数 (int): 角色的等级
attack_power = 150.5    # 浮点数 (float): 角色的攻击力，可能有小数
is_alive = True         # 布尔值 (bool): 角色是否存活

# 打印出角色的信息
print("角色名称:", character_name)
print("等级:", level)
print("攻击力:", attack_power)
print("存活状态:", is_alive)

# 预期输出:
# 角色名称: 雷神
# 等级: 99
# 攻击力: 150.5
# 存活状态: True
```

### 📈 Level 2: 核心特性（深入理解）
不同类型的数据有不同的“性格”和“技能”。

#### 特性1: 数字类型的自动转换
当整数 (`int`) 和浮点数 (`float`) 一起进行数学运算时，为了保证精度，Python会自动将结果转换为更精确的浮点数类型。

```python
# 一个整数等级和一个浮点数经验加成
base_experience = 1000      # int
bonus_multiplier = 0.25     # float

total_experience = base_experience + (base_experience * bonus_multiplier)

print("基础经验:", base_experience)
print("总经验值:", total_experience)
print("总经验值的类型是浮点数吗？", isinstance(total_experience, float)) # isinstance() 用来检查类型

# 预期输出:
# 基础经验: 1000
# 总经验值: 1250.0
# 总经验值的类型是浮点数吗？ True
```

#### 特性2: 字符串的“魔法”：拼接与重复
字符串可以使用 `+` 号进行拼接（连接），使用 `*` 号进行重复。这和数字的加法、乘法是完全不同的概念。

```python
# 字符串拼接
greeting = "你好, "
name = "冒险者"
welcome_message = greeting + name + "!"
print(welcome_message)

# 字符串重复
separator = "-=" * 10  # 将 "-=" 重复10次
print(separator)

# 预期输出:
# 你好, 冒险者!
# -=-=-=-=-=-=-=-=-=-=
```

#### 特性3: 布尔值的“双重身份”
在数学运算中，`True` 会被当作整数 `1`，而 `False` 会被当作整数 `0`。这个特性在某些计算中非常有用。

```python
# 假设任务完成奖励100分
task_completed_1 = True
task_completed_2 = False

# 计算总分
total_score = task_completed_1 * 100 + task_completed_2 * 100

print(f"任务1是否完成: {task_completed_1} (计为 {int(task_completed_1)} 分)")
print(f"任务2是否完成: {task_completed_2} (计为 {int(task_completed_2)} 分)")
print(f"总得分: {total_score}")

# 预期输出:
# 任务1是否完成: True (计为 1 分)
# 任务2是否完成: False (计为 0 分)
# 总得分: 100
```

### 🔍 Level 3: 对比学习（避免陷阱）
初学者最常犯的错误就是试图将不兼容的类型混合在一起，尤其是字符串和数字。

```python
# === 错误用法 ===
# ❌ 尝试用 '+' 连接字符串和数字
player_name = "战士"
player_level = 5
# 下面这行代码会引发 TypeError，因为Python不知道你是想做数学加法还是文本拼接
# message = "玩家 " + player_name + " 的等级是 " + player_level 
# print(message)
# TypeError: can only concatenate str (not "int") to str
print("错误演示：直接用 '+' 连接字符串和数字会失败！")


# === 正确用法 ===
# ✅ 使用 f-string (格式化字符串) 来优雅地组合不同类型的数据
player_name = "战士"
player_level = 5
# f-string 会自动将花括号 {} 内的变量转换为字符串
message = f"玩家 {player_name} 的等级是 {player_level}"
print(message)

# 预期输出:
# 错误演示：直接用 '+' 连接字符串和数字会失败！
# 玩家 战士 的等级是 5
```

### 🚀 Level 4: 实战应用（真实场景）

**场景：** 🐾 虚拟宠物互动模拟器

你正在开发一个简单的虚拟宠物游戏。你需要记录宠物的状态，并根据它的状态打印出不同的互动信息。这个场景将综合运用所有四种基本数据类型。

```python
# 1. 定义宠物的属性 (使用四种基本数据类型)
pet_name = "皮卡丘"             # str: 宠物的名字
age_in_months = 6             # int: 宠物的月龄
weight_kg = 4.5               # float: 宠物的体重 (公斤)
is_hungry = True              # bool: 宠物是否饿了

# 2. 打印宠物的基本档案
print("🐾 === 虚拟宠物档案 === 🐾")
print(f"名字: {pet_name}")
print(f"月龄: {age_in_months} 个月")
print(f"体重: {weight_kg} kg")
print("-" * 25) # 打印分割线

# 3. 根据宠物的状态进行互动
print("主人，你好！")

# 使用布尔值进行判断
if is_hungry:
    status_emoji = " голодный"  # 饿了的表情
    action_suggestion = "快给我喂食吧！"
else:
    status_emoji = "😊"  # 开心的表情
    action_suggestion = "我们一起玩吧！"

# 4