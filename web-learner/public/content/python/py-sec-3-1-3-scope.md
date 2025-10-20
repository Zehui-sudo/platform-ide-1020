好的，作为一名顶级的Python教育专家，我将为你生成关于 **作用域 (LEGB)** 的详细教学内容。内容将遵循循序渐进、重点突出、生动有趣的原则。

---

## 作用域 (LEGB)

### 🎯 核心概念
作用域规定了变量的“可见范围”，决定了你在代码的哪个位置可以访问哪个变量，以此来避免命名冲突并使代码结构更清晰。

### 💡 使用方式
想象一下你在一个大庄园里找东西，你肯定会先在**自己的房间（L）**找，找不到再去**整个房子（E）**里找，再找不到就去**整个庄园（G）**里找，如果还找不到，那这个东西可能就是**全世界公认的常识（B）**，比如“太阳”。

Python 查找变量的过程与此类似，遵循 **LEGB** 规则：

1.  **L (Local) - 局部作用域**: 函数内部定义的变量。这是查找的第一站。
2.  **E (Enclosing) - 嵌套作用域**: 嵌套函数中，外部函数（非全局）的作用域。
3.  **G (Global) - 全局作用域**: 在整个 `.py` 文件顶层定义的变量。
4.  **B (Built-in) - 内置作用域**: Python 解释器启动时就加载的变量，如 `print()`, `len()`, `str` 等。

Python 解释器会按照 **L → E → G → B** 的顺序依次查找变量，一旦找到，便会停止搜索。

### 📚 Level 1: 基础认知（30秒理解）
最常见的是局部作用域（函数内）和全局作用域（函数外）的区别。它们就像是你的“私房钱”和“家庭公共基金”，互不干扰。

```python
# Level 1: 局部作用域 vs 全局作用域

# G (Global): 这是在全局作用域定义的变量
player_health = 100

def player_action():
    # L (Local): 这是在函数内部定义的局部变量，与全局变量同名
    # 但它是一个全新的、只在函数内部有效的变量
    player_health = 50
    print(f"函数内部：玩家受到攻击，生命值变为 {player_health}")

# 调用函数
player_action()

# 打印全局变量，你会发现它没有被函数内的操作改变
print(f"函数外部：玩家的最终生命值是 {player_health}")

# 预期输出:
# 函数内部：玩家受到攻击，生命值变为 50
# 函数外部：玩家的最终生命值是 100
```

### 📈 Level 2: 核心特性（深入理解）
现在我们来深入了解 LEGB 规则中的另外两个关键部分：嵌套作用域和如何修改外层作用域的变量。

#### 特性1: 嵌套作用域 (Enclosing Scope)
当一个函数嵌套在另一个函数内部时，内部函数可以访问外部函数的变量，这就是嵌套作用域。

```python
# Level 2, 特性1: 嵌套作用域 (Enclosing)

def game_world():
    # E (Enclosing): 这是外部函数的变量，属于嵌套作用域
    world_name = "艾泽拉斯"

    def inner_character():
        # L (Local): 这是内部函数的局部变量
        char_name = "阿尔萨斯"
        # 内部函数可以自由访问外部(Enclosing)作用域的变量
        print(f"角色 '{char_name}' 正在探索 '{world_name}' 世界。")

    # 调用内部函数
    inner_character()

game_world()

# 预期输出:
# 角色 '阿尔萨斯' 正在探索 '艾泽拉斯' 世界。
```

#### 特性2: 使用 `global` 和 `nonlocal` 修改变量
默认情况下，函数只能读取外层作用域的变量，但不能修改。如果你尝试修改，Python 会默认创建一个新的同名局部变量。要真正修改外层变量，需要明确声明。

- `global`：用于在函数内部修改**全局作用域 (G)** 的变量。
- `nonlocal`：用于在嵌套函数内部修改**嵌套作用域 (E)** 的变量。

```python
# Level 2, 特性2: 使用 global 和 nonlocal

# --- 使用 global ---
score = 0  # G (Global)

def add_global_score(points):
    # 使用 global 关键字声明，我要修改的是全局变量 score
    global score
    score += points
    print(f"增加分数后，全局分数变为: {score}")

add_global_score(10)
add_global_score(20)
print(f"最终全局分数: {score}")
print("-" * 20)

# --- 使用 nonlocal ---
def create_level_tracker(level_name):
    # E (Enclosing)
    monsters_defeated = 0

    def defeat_monster():
        # 使用 nonlocal 关键字声明，我要修改的是嵌套作用域的 monsters_defeated
        nonlocal monsters_defeated
        monsters_defeated += 1
        print(f"在 '{level_name}' 关卡, 已击败 {monsters_defeated} 个怪物。")

    return defeat_monster

level1 = create_level_tracker("新手村")
level1()
level1()

# 预期输出:
# 增加分数后，全局分数变为: 10
# 增加分数后，全局分数变为: 30
# 最终全局分数: 30
# --------------------
# 在 '新手村' 关卡, 已击败 1 个怪物。
# 在 '新手村' 关卡, 已击败 2 个怪物。
```

### 🔍 Level 3: 对比学习（避免陷阱）
一个非常常见的错误是，在函数内部试图修改全局变量，但忘记使用 `global` 关键字，这会导致 `UnboundLocalError`。

```python
# === 错误用法 ===
# ❌ 试图直接修改全局变量，但没有使用 `global` 声明
mana = 100

def cast_spell():
    # Python 在这里看到赋值操作，就认为 mana 是一个局部变量。
    # 但在赋值之前，它又试图读取 mana 的值 (mana - 20)，
    # 此时这个局部变量还未被定义，所以会报错。
    mana = mana - 20  
    print(f"施法后，剩余法力值: {mana}")

try:
    cast_spell()
except UnboundLocalError as e:
    print(f"出错了！错误信息: {e}")
# 解释: Python 认为函数内的 `mana` 是一个新的局部变量，
# 而不是全局的那个。你不能在一个变量被赋值前就读取它。

# === 正确用法 ===
# ✅ 使用 `global` 关键字明确指出要修改的是全局变量
mana = 100

def cast_spell_correctly():
    global mana
    mana = mana - 20
    print(f"施法后，剩余法力值: {mana}")

cast_spell_correctly()
print(f"全局法力值现在是: {mana}")

# 预期输出:
# 出错了！错误信息: local variable 'mana' referenced before assignment
# 施法后，剩余法力值: 80
# 全局法力值现在是: 80
```

### 🚀 Level 4: 实战应用（真实场景）

**场景：** 🐾 电子宠物养成游戏

在这个游戏中，我们有一个全局的游戏状态（如是否在运行）。然后我们创建一个宠物工厂函数，每个宠物都有自己的名字和饥饿度（嵌套作用域）。宠物可以进行各种活动，这些活动会消耗它的饥饿度（局部作用域）。

```python
import time
import random

# G (Global): 游戏全局设定
GAME_RUNNING = True
game_speed = 1.0 

def create_pet(name):
    # E (Enclosing): 每个宠物实例独有的属性
    pet_name = name
    hunger_level = 10

    def play():
        # L (Local): 本次活动的局部变量
        energy_cost = random.randint(1, 3)
        
        # nonlocal: 修改嵌套作用域的 hunger_level
        nonlocal hunger_level
        hunger_level -= energy_cost
        
        print(f"🐾 {pet_name} 快乐地玩耍，消耗了 {energy_cost} 点能量，饥饿度降至 {hunger_level}。")

    def feed():
        # nonlocal: 修改嵌套作用域的 hunger_level
        nonlocal hunger_level
        hunger_level += 5
        print(f"🍖 你给 {pet_name} 喂食，饥饿度恢复到 {hunger_level}！")

    def get_status():
        # 读取全局变量 GAME_RUNNING
        if not GAME_RUNNING:
            print("游戏已结束！")
            return False
            
        if hunger_level <= 0:
            print(f"😭 糟糕！{pet_name} 因为太饿而离家出走了...")
            return False
        else:
            print(f"💖 {pet_name} 当前状态：饥饿度 {hunger_level}")
            return True

    # 返回一个字典，包含了可以对这个宠物进行的操作
    return {"play": play, "feed": feed, "status": get_status}

# --- 游戏开始 ---
print("--- 欢迎来到电子宠物养成游戏 ---")
my_pet = create_pet("皮卡丘")

# 模拟游戏循环
while my_pet["status"]():
    action = random.choice(["play", "play", "feed"]) # 让玩耍的概率高一些
    
    if action == "play":
        my_pet["play"]()
    elif action == "feed":
        my_pet["feed"]()
    
    # 读取全局变量 game_speed
    time.sleep(game_speed)

# 预期输出 (由于随机性，每次可能不同):
# --- 欢迎来到电子宠物养成游戏 ---
# 💖 皮卡丘 当前状态：饥饿度 10
# 🐾 皮卡丘 快乐地玩耍，消耗了 2 点能量，饥饿度降至 8。
# 💖 皮卡丘 当前状态：饥饿度 8
# 🍖 你给 皮卡丘 喂食，饥饿度恢复到 13！
# 💖 皮卡丘 当前状态：饥饿度 13
# 🐾 皮卡丘 快乐地玩耍，消耗了 3 点能量，饥饿度降至 10。
# ... (循环直到饥饿度为0)
# 💖 皮卡丘 当前状态：饥饿度 1
# 🐾 皮卡丘 快乐地玩耍，消耗了 2 点能量，饥饿度降至 -1。
# 😭 糟糕！皮卡丘 因为太饿而离家出走了...
```

### 💡 记忆要点
- **要点1**: **LEGB 搜索顺序**：Python 查找变量的顺序是固定的：**局部 (L) → 