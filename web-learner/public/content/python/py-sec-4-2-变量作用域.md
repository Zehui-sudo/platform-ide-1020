在我们学会了如何定义和使用函数之后，一个至关重要的问题随之而来：函数内部定义的变量和函数外部定义的变量，如果名字相同，它们之间会互相干扰吗？Python 是如何管理这些“同名”变量的呢？

答案就在于 **变量作用域（Variable Scope）**。它就像是为变量划分的“领地”，规定了在代码的哪些区域可以访问某个变量。

### 🎯 核心概念
变量作用域定义了一个变量的“可见范围”和“生命周期”，它解决了**命名冲突**的问题，并实现了不同代码块之间的**数据隔离**，确保了程序的清晰和稳定。

### 💡 使用方式
Python 遵循 **LEGB 规则** 来查找一个变量，这是一个优先级顺序：

1.  **L (Local): 局部作用域** - 函数内部。这是查找的第一站。
2.  **E (Enclosing): 闭包作用域** - 嵌套函数中，外部函数的内部。
3.  **G (Global): 全局作用域** - 模块（.py文件）的顶层。
4.  **B (Built-in): 内置作用域** - Python 解释器预先定义的名称，如 `print()`, `len()` 等。

当使用一个变量时，Python 会像玩寻宝游戏一样，从当前位置（L）开始找，找不到就去上一层（E），再找不到就去更外层（G），最后才去查找内置的宝藏（B）。如果一路都找不到，就会抛出 `NameError`。

我们可以用一个图来形象地理解这个“套娃”般的结构：

```mermaid
graph TD
    B["B: 内置作用域 (print, len, ...)<br>整个Python环境"]
    G["G: 全局作用域<br>整个.py文件"]
    E["E: 闭包作用域<br>外部函数 `outer_func`"]
    L["L: 局部作用域<br>内部函数 `inner_func`"]

    subgraph B
        subgraph G
            subgraph E
                subgraph L
                    A[查找变量 `x` 从这里开始] --> L
                end
            end
        end
    end

    L -->|找不到| E -->|找不到| G -->|找不到| B -->|找不到| Error
```

### 📚 Level 1: 基础认知（30秒理解）
最常见的就是**局部作用域**和**全局作用域**的区别。函数内部的变量默认与外部的井水不犯河水。

```python
# G: 全局作用域
planet = "地球"

def spaceship_log():
    # L: 局部作用域
    # 函数内部定义了一个同名变量 planet
    planet = "火星"
    print(f"飞船日志：我们已抵达 {planet}。")

# 调用函数
spaceship_log()

# 在函数外部打印全局变量
print(f"地面指挥中心：飞船目前位于 {planet}。")

# 预期输出结果:
# 飞船日志：我们已抵达 火星。
# 地面指挥中心：飞船目前位于 地球。
# 解释：函数内部对 planet 的赋值，创建了一个全新的局部变量，丝毫没有影响到全局变量 planet。
```

### 📈 Level 2: 核心特性（深入理解）
默认情况下，你只能在函数内 *读取* 外部作用域的变量，但不能 *修改*。如果你想修改，就需要明确声明。

#### 特性1: 使用 `global` 关键字修改全局变量
如果你想在函数内部修改一个全局变量的值，必须使用 `global` 关键字进行声明。

```python
# 全局变量，表示游戏的总得分
total_score = 1000

def complete_mission(score_earned):
    """完成一个任务，将获得的分数加到总分上。"""
    # 使用 global 关键字声明，我们将要修改的是全局变量 total_score
    global total_score
    total_score += score_earned
    print(f"任务完成！获得 {score_earned} 分。当前总分: {total_score}")

print(f"游戏开始时总分: {total_score}")

# 调用函数完成任务
complete_mission(150)
complete_mission(200)

print(f"游戏结束时总分: {total_score}")

# 预期输出结果:
# 游戏开始时总分: 1000
# 任务完成！获得 150 分。当前总分: 1150
# 任务完成！获得 200 分。当前总分: 1350
# 游戏结束时总分: 1350
```

#### 特性2: 闭包与 `nonlocal` 关键字
当函数嵌套时，内部函数可以访问外部函数的变量，这构成了**闭包（Enclosing）作用域**。如果要修改这个外部（但非全局）的变量，需要使用 `nonlocal` 关键字。

```python
def create_counter(start_value):
    """一个创建计数器的工厂函数。"""
    # E: 闭包作用域的变量
    count = start_value

    def counter():
        """这个内部函数是真正的计数器。"""
        # nonlocal 声明 count 不是局部变量，而是来自外部闭包作用域
        nonlocal count
        count += 1
        print(f"计数值: {count}")

    return counter

# 创建两个独立的计数器
counter_A = create_counter(0)
counter_B = create_counter(10)

print("--- 操作计数器 A ---")
counter_A()
counter_A()

print("\n--- 操作计数器 B ---")
counter_B()

print("\n--- 再次操作计数器 A ---")
counter_A()

# 预期输出结果:
# --- 操作计数器 A ---
# 计数值: 1
# 计数值: 2
#
# --- 操作计数器 B ---
# 计数值: 11
#
# --- 再次操作计数器 A ---
# 计数值: 3
# 解释：每个计数器都有自己独立的闭包环境，counter_A 的 count 和 counter_B 的 count 互不影响。
```

### 🔍 Level 3: 对比学习（避免陷阱）
一个非常隐蔽且常见的陷阱是：**不要使用可变类型（如列表、字典）作为函数的默认参数**。

```python
# === 错误用法 ===
# ❌ 使用了可变的列表 `[]` 作为默认参数
def add_to_shopping_list_bad(item, current_list=[]):
    current_list.append(item)
    print(f"已添加 '{item}'。当前购物清单: {current_list}")

print("--- 错误的购物清单 ---")
# 第一次调用，看起来没问题
add_to_shopping_list_bad("苹果")
# 第二次调用，期望清单里只有“香蕉”
add_to_shopping_list_bad("香蕉")
# 第三次调用，期望清单里只有“牛奶”
add_to_shopping_list_bad("牛奶")

# 解释为什么是错的:
# 函数的默认参数在函数被 *定义* 时只创建一次。
# 所有的调用如果没有提供自己的列表，都会共享这同一个、在内存中持续存在的列表。
# 结果就是，每次添加都在同一个“幽灵列表”上累加，造成了意想不到的数据污染。

# === 正确用法 ===
# ✅ 使用不可变的 `None` 作为默认值，在函数体内创建新列表
def add_to_shopping_list_good(item, current_list=None):
    if current_list is None:
        current_list = []  # 如果没有提供列表，则在函数 *调用* 时创建一个新的
    current_list.append(item)
    print(f"已添加 '{item}'。当前购物清单: {current_list}")
    
print("\n--- 正确的购物清单 ---")
add_to_shopping_list_good("苹果")
add_to_shopping_list_good("香蕉")
# 我们可以传入自己的列表
my_weekly_list = ["鸡蛋"]
add_to_shopping_list_good("牛奶", my_weekly_list)
print(f"我自己的周清单: {my_weekly_list}")

# 解释为什么这样是对的:
# 这种模式确保了每次函数调用时，如果调用者没有提供列表，函数内部都会创建一个全新的、干净的空列表。
# 这保证了每次调用都是独立的，符合直觉，避免了数据共享带来的副作用。
```

### 🚀 Level 4: 实战应用（真实场景）
**场景：** 🧙‍♂️ 魔法学院的魔咒计数器

**背景：** 邓布利多校长想要追踪霍格沃茨学生们的魔咒练习情况。他需要一个系统，既能统计每个学生在单次练习中施放的魔咒数量，也要能计入全校当天施放的魔咒总数。

```python
# 🧙‍♂️ 魔法学院的魔咒计数器

# G: 全局作用域，记录全校的魔咒总数
hogwarts_daily_spell_count = 0

def start_practice_session(student_name):
    """
    为一位学生开启一次新的魔咒练习。
    这将返回一个为该学生定制的施法函数。
    """
    # E: 闭包作用域，记录本次练习的魔咒数
    session_count = 0
    print(f"\n✨ {student_name} 的魔咒练习开始了！✨")

    def cast_spell(spell_name):
        """
        学生施放一个魔咒。
        """
        nonlocal session_count      # 修改闭包变量
        global hogwarts_daily_spell_count # 修改全局变量

        session_count += 1
        hogwarts_daily_spell_count += 1
        
        print(f"{student_name} 念出咒语: “{spell_name}！” (本次练习第 {session_count} 个, 全校今天第 {hogwarts_daily_spell_count} 个)")
    
    return cast_spell

# --- 练习日开始 ---

# 为哈利和赫敏分别创建练习会话
harry_cast = start_practice_session("哈利·波特")
hermione_cast = start_practice_session("赫敏·格兰杰")

# 哈利开始练习
harry_cast("Expecto Patronum") # 呼神护卫
harry_cast("Expelliarmus")     # 除你武器

# 赫敏加入练习
hermione_cast("Wingardium Leviosa") # 悬浮咒
hermione_cast("Alohomora")          # 阿拉霍洞开
hermione_cast("Oculus Reparo")      # 修复如初

# 哈利继续练习
harry_cast("Stupefy") # 昏昏倒地

# 预期输出结果:
#
# ✨ 哈利·波特 的魔咒练习开始了！✨
#
# ✨ 赫敏·格兰杰 的魔咒练习开始了！✨
# 哈利·波特 念出咒语: “Expecto Patronum！” (本次练习第 1 个, 全校今天第 1 个)
# 哈利·波特 念出咒语: “Expelliarmus！” (本次练习第 2 个, 全校今天第 2 个)
# 赫敏·格兰杰 念出咒语: “Wingardium Leviosa！” (本次练习第 1 个, 全校今天第 3 个)
# 赫敏·格兰杰 念出咒语: “Alohomora！” (本次练习第 2 个, 全校今天第 4 个)
# 赫敏·格兰杰 念出咒语: “Oculus Reparo！” (本次练习第 3 个, 全校今天第 5 个)
# 哈利·波特 念出咒语: “Stupefy！” (本次练习第 3 个, 全校今天第 6 个)

# 这个例子完美展示了：
# 1. `session_count` (nonlocal) 对每个学生是独立的。
# 2. `hogwarts_daily_spell_count` (global) 是所有学生共享的。
```

### 💡 记忆要点
- **要点1**: **LEGB 搜索顺序**: Python 按 **局部(L) -> 闭包(E) -> 全局(G) -> 内置(B)** 的顺序查找变量。这个顺序决定了哪个变量会被“看到”。
- **要点2**: **修改需要声明**: 默认只能 *读取* 外部作用域的变量。想在函数内 *修改* **全局**变量，请用 `global`；想修改**嵌套函数的外部**变量，请用 `nonlocal`。
- **要点3**: **警惕可变默认参数**: 千万不要用列表`[]`或字典`{}`等可变类型作函数默认参数。标准做法是使用 `None` 作占位符，并在函数内部创建新对象。