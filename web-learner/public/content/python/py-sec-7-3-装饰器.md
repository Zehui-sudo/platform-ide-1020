好的，总建筑师。作为您的世界级技术教育者和 Python 专家，我将严格遵循您的“教学设计图”，将关于“装饰器”的知识点转化为一篇高质量、多层次的 Markdown 教程。

---

### 🎯 核心概念
装饰器是一种强大的编程范式，它允许你在**不修改函数本身代码**的前提下，为其动态地“装饰”上日志记录、性能测试、事务处理等新功能，是代码复用和功能增强的利器。

### 💡 使用方式
装饰器的核心思想是“函数作为一等公民”和“闭包”。它本质上是一个函数（装饰器函数），接收另一个函数（被装饰函数）作为输入，并返回一个新的函数（包装后的函数）。我们通常使用 `@` 语法糖来简化这个过程。

1.  **定义一个装饰器函数**：这个函数接收一个函数 `func` 作为参数。
2.  **在内部定义一个包装函数 `wrapper`**：这个函数会执行额外的逻辑，并调用原始的 `func`。
3.  **返回包装函数 `wrapper`**：装饰器函数返回这个包装好的新函数。
4.  **使用 `@decorator_name`**：将其放在目标函数的 `def` 语句之前。

```python
def my_decorator(func):
    def wrapper(*args, **kwargs):
        # 1. 在原函数执行前添加新功能
        print(f"函数 {func.__name__} 开始执行...")
        
        # 2. 调用原函数
        result = func(*args, **kwargs)
        
        # 3. 在原函数执行后添加新功能
        print(f"函数 {func.__name__} 执行完毕。")
        return result
    return wrapper

@my_decorator
def say_hello():
    print("你好，世界！")

# 调用被装饰的函数
say_hello()
```

### 📚 Level 1: 基础认知（30秒理解）
最简单的装饰器就是在函数执行前后打印一些信息，就像给函数加上了“入场”和“退场”的宣告。

```python
# 示例代码
def simple_announcer(func):
    """一个简单的装饰器，在函数执行前后打印信息。"""
    def wrapper(*args, **kwargs):
        print(f"即将调用函数: {func.__name__}")
        func(*args, **kwargs)
        print(f"函数 {func.__name__} 调用结束。")
    return wrapper

@simple_announcer
def celebrate():
    """一个简单的庆祝函数。"""
    print("🎉 耶！装饰器真有趣！")

# 调用被装饰后的函数
celebrate()

# 预期输出结果:
# 即将调用函数: celebrate
# 🎉 耶！装饰器真有趣！
# 函数 celebrate 调用结束。
```

### 📈 Level 2: 核心特性（深入理解）
掌握装饰器的基础后，让我们深入了解两个让它变得更强大、更专业的关键特性。

#### 特性1: 使用 `functools.wraps` 保留元信息
装饰器会返回一个新函数来替换原函数，这会导致原函数的名称、文档字符串等元信息丢失。`functools.wraps` 装饰器可以帮助我们将这些信息从原函数复制到包装函数中。

```python
# 示例代码
import functools

def logging_decorator(func):
    """一个带日志功能的装饰器，并使用 wraps 保留元信息。"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        print(f"调用函数 {func.__name__}，参数: {args}, {kwargs}")
        result = func(*args, **kwargs)
        print(f"函数 {func.__name__} 返回: {result}")
        return result
    return wrapper

@logging_decorator
def add(a, b):
    """这是一个计算两个数之和的函数。"""
    return a + b

print(f"函数名称: {add.__name__}")
print(f"函数文档: {add.__doc__}")
add(10, 5)

# 预期输出结果:
# 函数名称: add
# 函数文档: 这是一个计算两个数之和的函数。
# 调用函数 add，参数: (10, 5), {}
# 函数 add 返回: 15
```

#### 特性2: 带参数的装饰器
有时我们希望装饰器本身能够接收参数，以实现更灵活的配置。这需要再增加一层函数嵌套，形成一个“装饰器工厂”。

```python
# 示例代码
def repeat(num_times):
    """一个装饰器工厂，创建可以重复执行N次的装饰器。"""
    def decorator_repeat(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            print(f"--- {func.__name__} 将被重复执行 {num_times} 次 ---")
            for i in range(num_times):
                print(f"第 {i+1} 次执行:")
                result = func(*args, **kwargs)
            return result # 返回最后一次执行的结果
        return wrapper
    return decorator_repeat

@repeat(num_times=3)
def greet(name):
    """向某人问好。"""
    print(f"你好, {name}!")

# 调用被装饰后的函数
greet("Pythonista")

# 预期输出结果:
# --- greet 将被重复执行 3 次 ---
# 第 1 次执行:
# 你好, Pythonista!
# 第 2 次执行:
# 你好, Pythonista!
# 第 3 次执行:
# 你好, Pythonista!
```

### 🔍 Level 3: 对比学习（避免陷阱）
一个常见的陷阱是忘记使用 `functools.wraps`，导致调试和文档生成时出现意想不到的问题。

```python
# === 错误用法 ===
# ❌ 未使用 functools.wraps
import functools
import time

def timer_decorator_bad(func):
    # 没有 @functools.wraps(func)
    def wrapper(*args, **kwargs):
        """我是包装函数的文档，不是原函数的！"""
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        print(f"{func.__name__} 运行耗时: {end_time - start_time:.4f} 秒")
        return result
    return wrapper

@timer_decorator_bad
def slow_task_bad():
    """这是一个模拟耗时操作的函数。"""
    time.sleep(0.1)
    return "任务完成"

print("--- 错误用法 ---")
print(f"函数名: {slow_task_bad.__name__}") # 输出 wrapper
print(f"函数文档: {slow_task_bad.__doc__}") # 输出 wrapper 的文档
slow_task_bad()
# 解释为什么是错的:
# 被装饰后，slow_task_bad 实际上指向了内部的 wrapper 函数。
# 它的 __name__ 和 __doc__ 都变成了 wrapper 函数的属性，
# 原函数的元信息丢失，这会给代码自省和调试带来困扰。


# === 正确用法 ===
# ✅ 使用 functools.wraps
def timer_decorator_good(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        """我是包装函数的文档，但 @wraps 会保护原函数的文档。"""
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        print(f"{func.__name__} 运行耗时: {end_time - start_time:.4f} 秒")
        return result
    return wrapper

@timer_decorator_good
def slow_task_good():
    """这是一个模拟耗时操作的函数。"""
    time.sleep(0.1)
    return "任务完成"

print("\n--- 正确用法 ---")
print(f"函数名: {slow_task_good.__name__}") # 输出 slow_task_good
print(f"函数文档: {slow_task_good.__doc__}") # 输出 slow_task_good 的文档
slow_task_good()
# 解释为什么这样是对的:
# @functools.wraps(func) 将原始函数(func)的元信息（如__name__, __doc__等）
# 复制到了包装函数(wrapper)上，使得装饰后的函数对外表现得和原函数一模一样。
```

### 🚀 Level 4: 实战应用（真实场景）
**场景：** 🎮 游戏角色的技能授权系统

在一个角色扮演游戏中，某些强大的技能需要满足特定条件（如等级足够、持有特定物品）才能释放。我们可以用装饰器优雅地实现这个授权检查逻辑。

```python
# 实战场景的完整代码
import functools

# --- 装饰器定义 ---
def requires_level(required_level):
    """装饰器：检查玩家等级是否满足要求。"""
    def decorator(skill_func):
        @functools.wraps(skill_func)
        def wrapper(player, *args, **kwargs):
            if player['level'] < required_level:
                print(f"🚫 等级不足！释放 '{skill_func.__name__}' 需要 {required_level} 级，你只有 {player['level']} 级。")
                return
            return skill_func(player, *args, **kwargs)
        return wrapper
    return decorator

def requires_item(required_item):
    """装饰器：检查玩家是否持有特定物品。"""
    def decorator(skill_func):
        @functools.wraps(skill_func)
        def wrapper(player, *args, **kwargs):
            if required_item not in player['inventory']:
                print(f"🚫 缺少物品！释放 '{skill_func.__name__}' 需要 '{required_item}'。")
                return
            return skill_func(player, *args, **kwargs)
        return wrapper
    return decorator


# --- 玩家和技能定义 ---
# 玩家数据
player1 = {'name': 'Arion', 'level': 15, 'inventory': ['健康药水', '法力水晶']}
player2 = {'name': 'Lira', 'level': 50, 'inventory': ['健康药水', '凤凰之羽']}

# 技能函数
@requires_level(10)
def fireball(player):
    """基础火球术"""
    print(f"🔥 {player['name']} 释放了火球术！")

@requires_level(40)
@requires_item('凤凰之羽') # 装饰器可以叠加，执行顺序从下到上
def summon_phoenix(player):
    """终极技能：召唤凤凰"""
    print(f"🐦🔥 {player['name']} 召唤了传说中的凤凰！天空被火焰染红！")


# --- 游戏模拟 ---
print("--- 玩家 Arion 的回合 ---")
fireball(player1)         # 成功：等级15 > 10
summon_phoenix(player1)   # 失败：等级15 < 40，且缺少物品

print("\n--- 玩家 Lira 的回合 ---")
fireball(player2)         # 成功：等级50 > 10
summon_phoenix(player2)   # 成功：等级50 > 40，且持有'凤凰之羽'

# 预期输出结果:
# --- 玩家 Arion 的回合 ---
# 🔥 Arion 释放了火球术！
# 🚫 等级不足！释放 'summon_phoenix' 需要 40 级，你只有 15 级。
# 
# --- 玩家 Lira 的回合 ---
# 🔥 Lira 释放了火球术！
# 🐦🔥 Lira 召唤了传说中的凤凰！天空被火焰染红！
```

### 💡 记忆要点
- **要点1**: **装饰器是函数**：装饰器本质上是一个接收函数并返回一个新函数的函数。`@syntax` 只是一个为了可读性而存在的语法糖。
- **要点2**: **保留元信息**: 务必使用 `functools.wraps` 来装饰你的内部包装函数，以保留原函数的名称、文档字符串等重要信息，这对于调试和工具链至关重要。
- **要点3**: **层层嵌套**: 带参数的装饰器需要再多一层函数嵌套，形成“三层结构”：最外层是接收参数的工厂函数，中间是标准的装饰器，最内层是执行逻辑的包装器。