### 🎯 核心概念
函数让我们能够将一堆代码打包、命名，并随时随地“召唤”它来执行特定任务，从而实现代码的复用，让程序更有条理。

### 💡 使用方式
在 Python 中，我们使用 `def` 关键字来定义一个函数。它的基本结构如下：

```python
def 函数名(参数1, 参数2, ...):
    """
    描述此函数的核心功能。

    这里可以写更详细的说明，例如函数的行为、副作用等。
    """
    # 函数体：包含一系列的 Python 语句
    # ...
    return 返回值  # 使用 return 语句将结果返回给调用者
```

- **`def`**: 定义函数的关键字。
- **`函数名`**: 你为函数取的名字，应遵循变量命名规则。
- **`参数`**: 函数接收的外部数据，是可选的。
- **`:`**: 函数头部的结束标记，必不可少。
- **`函数体`**: 必须缩进的代码块，是函数要执行的具体操作。
- **`return`**: 结束函数并返回一个值，是可选的。如果省略，函数默认返回 `None`。

### 📚 Level 1: 基础认知（30秒理解）
想象一下，你希望随时能向新来的朋友打个招呼。我们可以定义一个 `greet` 函数来完成这个任务。

```python
# 定义一个名为 greet 的函数，它接收一个参数 name
def greet(name):
  """这是一个简单的问候函数。"""
  message = f"你好, {name}！欢迎来到 Python 的魔法世界。✨"
  print(message)

# 调用函数，并传入 "爱丽丝" 作为参数
greet("爱丽丝")

# 预期输出:
# 你好, 爱丽丝！欢迎来到 Python 的魔法世界。✨
```

### 📈 Level 2: 核心特性（深入理解）
掌握了基础定义后，让我们深入了解函数更强大、更灵活的特性。

#### 特性1: 位置参数与关键字参数
向函数传递信息（参数）时，有两种主要方式：按位置或按名称。

- **位置参数**: 调用时，实参的顺序必须与形参的定义顺序一致。
- **关键字参数**: 调用时，通过 `参数名=值` 的形式指定，可以不考虑顺序。

```python
# 定义一个创建游戏角色的函数
def create_character(name, role, server):
  """根据名称、职业和服务器创建角色信息。"""
  print(f"角色创建成功！\n- 名字: {name}\n- 职业: {role}\n- 服务器: {server}")

# 1. 使用位置参数调用 (顺序必须正确)
print("--- 使用位置参数 ---")
create_character("阿尔萨斯", "死亡骑士", "艾泽拉斯")

# 2. 使用关键字参数调用 (顺序可以随意)
print("\n--- 使用关键字参数 ---")
create_character(server="诺森德", name="吉安娜", role="法师")

# 预期输出:
# --- 使用位置参数 ---
# 角色创建成功！
# - 名字: 阿尔萨斯
# - 职业: 死亡骑士
# - 服务器: 艾泽拉斯
#
# --- 使用关键字参数 ---
# 角色创建成功！
# - 名字: 吉安娜
# - 职业: 法师
# - 服务器: 诺森德
```

#### 特性2: 默认参数值与 return 语句
我们可以为参数提供一个默认值，使其在调用时变为可选。同时，使用 `return` 语句可以让函数“产出”一个结果，而不仅仅是打印信息。

```python
# 定义一个计算伤害的函数，武器加成默认为 5
def calculate_damage(base_attack, weapon_bonus=5):
    """
    计算角色的最终伤害值。
    
    Args:
        base_attack (int): 角色的基础攻击力。
        weapon_bonus (int, optional): 武器带来的额外加成. 默认为 5.

    Returns:
        int: 计算出的总伤害值。
    """
    final_damage = base_attack + weapon_bonus
    return final_damage

# 1. 不提供 weapon_bonus，使用默认值 5
warrior_damage = calculate_damage(100)
print(f"战士的基础伤害: {warrior_damage}")

# 2. 提供 weapon_bonus，覆盖默认值
mage_damage = calculate_damage(70, weapon_bonus=25) # 法师装备了传说级法杖，基础攻击力较低但加成高
print(f"法师的魔法伤害: {mage_damage}")


# 预期输出:
# 战士的基础伤害: 105
# 法师的魔法伤害: 95
```

### 🔍 Level 3: 对比学习（避免陷阱）
一个常见的陷阱是在函数调用时混合使用位置参数和关键字参数，顺序一旦错误就会导致 `SyntaxError`。

**规则：** 位置参数必须在关键字参数之前。

```python
def setup_mission(mission_name, difficulty, required_players):
    print(f"任务 '{mission_name}' 已设置，难度: {difficulty}，需要 {required_players} 名玩家。")

# === 错误用法 ===
# ❌ 将位置参数放在了关键字参数后面
# setup_mission(mission_name="拯救公主", 3, difficulty="困难")
# 解释：当 Python 看到关键字参数 difficulty="困难" 后，
# 它期望后面的所有参数也都是关键字参数。但紧接着又出现了一个位置参数 3，
# 这会让解释器感到困惑并报错：SyntaxError: positional argument follows keyword argument

# === 正确用法 ===
# ✅ 所有的位置参数都在关键字参数之前
setup_mission("拯救公主", difficulty="困难", required_players=3)
# 解释：首先提供位置参数 "拯救公主"，它会按顺序匹配给 mission_name。
# 然后，使用关键字参数来指定剩下的值，顺序可以任意。这样代码清晰且不会出错。

# 预期输出:
# 任务 '拯救公主' 已设置，难度: 困难，需要 3 名玩家。
```

### 🚀 Level 4: 实战应用（真实场景）

**场景：** 🚀 星际飞船导航系统

我们来设计一个函数，用于计算飞船从一个星球到另一个星球所需的燃料。这个函数需要考虑距离、飞船型号（影响基础消耗），以及是否开启“曲速引擎”（可以节省燃料）。

```python
def calculate_fuel_needed(distance_light_years, ship_model="探索者号", warp_drive_engaged=False):
    """
    计算星际航行所需的燃料。

    Args:
        distance_light_years (float): 航行距离（光年）。
        ship_model (str, optional): 飞船型号。不同型号基础油耗不同。默认为 "探索者号"。
        warp_drive_engaged (bool, optional): 是否开启曲速引擎。默认为 False。

    Returns:
        str: 一段描述燃料需求的报告。
    """
    # 基础油耗（单位：吨/光年）
    base_consumption = 1.2  # 探索者号的基础油耗

    if ship_model == "复仇者级":
        base_consumption = 2.5 # 重型战舰油耗更高
    elif ship_model == "蜂鸟侦察机":
        base_consumption = 0.7 # 轻型飞船油耗低

    # 如果开启曲速引擎，油耗降低为原来的 20%
    if warp_drive_engaged:
        consumption_rate = base_consumption * 0.2
        engine_status = "曲速引擎已启动"
    else:
        consumption_rate = base_consumption
        engine_status = "常规动力航行"

    total_fuel = distance_light_years * consumption_rate
    
    # 生成并返回报告
    report = (
        f"--- 航行燃料计算报告 ---\n"
        f"飞船型号: {ship_model}\n"
        f"航行距离: {distance_light_years} 光年\n"
        f"引擎状态: {engine_status}\n"
        f"预计燃料消耗: {total_fuel:.2f} 吨\n"
        f"--------------------------"
    )
    return report

# 场景1: 短途常规航行，使用默认的探索者号
report1 = calculate_fuel_needed(50.5)
print(report1)

# 场景2: 长途作战任务，使用重型战舰并开启曲速引擎
report2 = calculate_fuel_needed(1200.7, ship_model="复仇者级", warp_drive_engaged=True)
print("\n" + report2)

# 预期输出:
# --- 航行燃料计算报告 ---
# 飞船型号: 探索者号
# 航行距离: 50.5 光年
# 引擎状态: 常规动力航行
# 预计燃料消耗: 60.60 吨
# --------------------------
#
# --- 航行燃料计算报告 ---
# 飞船型号: 复仇者级
# 航行距离: 1200.7 光年
# 引擎状态: 曲速引擎已启动
# 预计燃料消耗: 600.35 吨
# --------------------------
```

### 💡 记忆要点
- **要点1**: **`def` 开头，冒号结尾，代码缩进**：这是函数定义的铁三角，缺一不可。
- **要点2**: **参数是入口，`return` 是出口**：函数通过参数接收外部数据，通过 `return` 语句返回处理结果。没有 `return` 的函数默默返回 `None`。
- **要点3**: **灵活的参数**：善用位置参数、关键字参数和默认值，可以让你的函数调用起来既清晰又方便，大大提升代码的可读性和灵活性。