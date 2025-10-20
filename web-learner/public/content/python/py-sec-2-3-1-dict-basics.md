好的，作为一名顶级的Python教育专家，我将为你生成关于 **“字典创建与访问”** 的详细教学内容。

---

## 字典创建与访问

### 🎯 核心概念

字典（Dictionary）是 Python 中一种极其有用的数据结构，它让你能够通过一个自定义的“名字”（称为**键 Key**）来存取数据（称为**值 Value**），而不是像列表那样只能通过数字索引。它完美地解决了**“如何将相关信息关联存储并快速查找”**的问题。

想象一下电话簿：你通过“姓名”（键）来查找“电话号码”（值）。字典就是编程世界里的电话簿！

### 💡 使用方式

创建字典主要有两种方式：

1.  **使用花括号 `{}`**：这是最常见的方式。语法是 `{key1: value1, key2: value2, ...}`。
2.  **使用 `dict()` 构造函数**：可以从键值对序列中创建字典。

访问字典中的值，则是通过将**键**放入方括号 `[]` 中，如 `my_dict[key]`。

### 📚 Level 1: 基础认知（30秒理解）

让我们为一只可爱的虚拟宠物创建一个信息卡。

```python
# 使用花括号 {} 创建一个表示虚拟宠物的字典
# 'name', 'animal_type', 'age' 是键 (key)
# '皮卡丘', '电老鼠', 5 是对应的值 (value)
pet_profile = {
    "name": "皮卡丘",
    "animal_type": "电老鼠",
    "age": 5
}

# 通过键 'name' 来访问它的值
pet_name = pet_profile["name"]

print(f"我的宠物叫：{pet_name}")
print(f"它的年龄是：{pet_profile['age']}岁")

# 预期输出:
# 我的宠物叫：皮卡丘
# 它的年龄是：5岁
```

### 📈 Level 2: 核心特性（深入理解）

#### 特性1: 键 (Key) 的唯一性和不可变性

字典的“键”有两个非常重要的规则：

1.  **唯一性**：一个字典内不能有重复的键。如果重复赋值，后面的会覆盖前面的。
2.  **不可变性**：键必须是不可变类型的数据，如字符串、数字或元组。列表、字典等可变类型不能作为键。

```python
# 1. 演示键的唯一性
# 我们不小心给 'location' 赋了两次值
city_weather = {
    "city": "北京",
    "temperature": 15,
    "location": "东城区",
    "location": "朝阳区"  # 后面的值会覆盖前面的
}

print(f"天气预报地点: {city_weather['location']}")
# 预期输出:
# 天气预报地点: 朝阳区

# 2. 演示键的不可变性
# 字符串、数字、元组可以作为键
valid_keys_dict = {
    "name": "Alice",    # 字符串作键
    101: "学号",        # 整数作键
    (10, 20): "坐标"    # 元组作键
}

print(f"学号101对应的是: {valid_keys_dict[101]}")
# 预期输出:
# 学号101对应的是: 学号
```

#### 特性2: 使用 `get()` 方法安全地访问值

直接用 `my_dict['some_key']` 访问一个不存在的键会直接报错（`KeyError`），导致程序崩溃。`get()` 方法提供了一种更安全、更优雅的方式来处理这种情况。

`get(key, default_value)`:
- 如果 `key` 存在，返回对应的值。
- 如果 `key` 不存在，返回你指定的 `default_value` (如果不指定，则返回 `None`)。

```python
student_scores = {
    "Alice": 95,
    "Bob": 88
}

# 尝试访问存在的键 'Alice'
print(f"Alice的分数是: {student_scores.get('Alice')}")

# 尝试访问不存在的键 'Charlie'
# 使用 [] 会报错，但使用 .get() 不会
score_charlie = student_scores.get("Charlie")
print(f"Charlie的分数是: {score_charlie}")

# 还可以提供一个默认值，让输出更友好
score_david = student_scores.get("David", "这位同学缺考")
print(f"David的分数是: {score_david}")

# 预期输出:
# Alice的分数是: 95
# Charlie的分数是: None
# David的分数是: 这位同学缺考
```

### 🔍 Level 3: 对比学习（避免陷阱）

**陷阱：访问不存在的键导致程序崩溃**

这是初学者最常遇到的错误之一。让我们看看如何避免它。

```python
# === 错误用法 ===
# ❌ 假设我们不确定一个键是否存在，就直接用 [] 访问
player_inventory = {"health_potion": 3, "sword": 1}

try:
    # 玩家可能没有 'mana_potion'，这行代码会触发 KeyError
    mana_potions = player_inventory['mana_potion']
    print(f"你有 {mana_potions} 瓶法力药水。")
except KeyError:
    print("❌ 错误：试图访问不存在的'mana_potion'，程序可能会在这里崩溃！")

# === 正确用法 ===
# ✅ 方法一：使用 in 关键字先检查键是否存在
if 'mana_potion' in player_inventory:
    mana_potions = player_inventory['mana_potion']
    print(f"你有 {mana_potions} 瓶法力药水。")
else:
    print("✅ 你背包里没有法力药水。")

# ✅ 方法二：使用 .get() 方法，代码更简洁
mana_potions_count = player_inventory.get('mana_potion', 0) # 如果没有，默认为0
print(f"✅ 你有 {mana_potions_count} 瓶法力药水。")

# 预期输出:
# ❌ 错误：试图访问不存在的'mana_potion'，程序可能会在这里崩溃！
# ✅ 你背包里没有法力药水。
# ✅ 你有 0 瓶法力药水。
```

### 🚀 Level 4: 实战应用（真实场景）

**场景：** 🚀 **星际飞船“探索号”的导航系统**

我们的任务是创建一个简单的导航系统。该系统存储了不同星球的坐标，并能根据用户输入的星球名称，返回其坐标。如果星球不存在于数据库中，系统需要给出友好提示。

```python
# 我们的星际坐标数据库 (一个字典)
# 键是星球名称，值是一个包含X,Y,Z坐标的元组
galaxy_map = {
    "地球": (0, 0, 0),
    "火星": (225, 0, 0),
    "木星": (778, 0, 0),
    "开普勒-186f": (475, 500, 100) # 一个遥远的系外行星
}

def navigate_to_planet(planet_name):
    """
    一个简单的导航函数，用于查询并显示星球坐标。
    """
    print(f"\n正在查询星球 '{planet_name}' 的坐标...")
    
    # 使用 .get() 安全地获取坐标
    # 如果找不到，返回一个特定的提示信息
    coordinates = galaxy_map.get(planet_name, "未知星球，无法在星图中找到！")
    
    # 检查返回的是坐标元组还是提示信息
    if isinstance(coordinates, tuple):
        # 如果是元组，说明找到了
        x, y, z = coordinates
        print(f"✅ 导航成功！'{planet_name}' 的坐标为: X={x}, Y={y}, Z={z} 百万公里。")
    else:
        # 否则，说明没找到
        print(f"⚠️ 导航失败: {coordinates}")

# --- 开始模拟导航 ---
# 1. 导航到已知的火星
navigate_to_planet("火星")

# 2. 导航到未知的潘多拉星
navigate_to_planet("潘多拉")

# 预期输出:
#
# 正在查询星球 '火星' 的坐标...
# ✅ 导航成功！'火星' 的坐标为: X=225, Y=0, Z=0 百万公里。
#
# 正在查询星球 '潘多拉' 的坐标...
# ⚠️ 导航失败: 未知星球，无法在星图中找到！
```

### 💡 记忆要点
- **要点1**: **键值配对**：字典的核心是 `key: value` 键值对，通过唯一的键来找到对应的值。
- **要点2**: **花括号与方括号**：使用 `{}` 创建字典，使用 `[key]` 来访问值。
- **要点3**: **安全访问用 `.get()`**：为了避免因键不存在而导致的 `KeyError`，请优先使用 `.get(key, default_value)` 方法进行访问。