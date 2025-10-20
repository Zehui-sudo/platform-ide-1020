好的，作为一名顶级的Python教育专家，我将为你生成关于 **“装饰器”** 的详细教学内容。内容将严格遵循你的要求，循序渐进，生动有趣。

---

## 装饰器

### 🎯 核心概念
装饰器是一种特殊类型的函数，它允许我们在**不修改原函数代码**的情况下，为该函数**添加新功能**或修改其行为。它就像给你的函数穿上一件“装备”，让它瞬间拥有额外的“技能”。

### 💡 使用方式
装饰器的核心是利用了Python中“函数是一等公民”（可以作为参数传递）和“闭包”的特性。它的标准语法是使用 `@` 符号，将其放在函数定义的上一行。

`@my_decorator`
`def my_function():`
    `pass`

这行代码其实是一个“语法糖”，它等同于：

`my_function = my_decorator(my_function)`

理解这个等价关系是掌握装饰器的关键！

### 📚 Level 1: 基础认知（30秒理解）
让我们来看一个最简单的装饰器，它能在函数执行前后打印日志，就像一个忠实的“迎宾员”。

```python
# 1. 定义一个装饰器函数
def welcome_decorator(func):
    """一个简单的装饰器，在函数执行前后打印欢迎和告别信息。"""
    def wrapper():
        print("--- 欢迎光临！函数即将开始执行... ---")
        func()  # 调用原始函数
        print("--- 感谢使用！函数已经执行完毕。 ---")
    return wrapper

# 2. 使用 @ 语法应用装饰器
@welcome_decorator
def say_hello():
    """一个简单的问候函数。"""
    print("Hello, Python World!")

# 3. 调用被装饰的函数
say_hello()

# 预期输出:
# --- 欢迎光临！函数即将开始执行... ---
# Hello, Python World!
# --- 感谢使用！函数已经执行完毕。 ---
```

### 📈 Level 2: 核心特性（深入理解）
简单的装饰器很酷，但在真实世界中，函数通常有参数和返回值。我们的“装备”也需要升级才能应对这些情况。

#### 特性1: 装饰带参数和返回值的函数
为了让装饰器能够处理任意参数的函数，我们在 `wrapper` 函数中使用 `*args` 和 `**kwargs`。同时，为了不“吞掉”原函数的计算结果，我们需要捕获并返回它。

```python
import time

def timer_decorator(func):
    """一个计算并打印函数执行时间的装饰器。"""
    def wrapper(*args, **kwargs):
        start_time = time.time()
        # 调用原始函数，并传入所有参数
        result = func(*args, **kwargs) 
        end_time = time.time()
        print(f"函数 '{func.__name__}' 执行耗时: {end_time - start_time:.4f} 秒")
        # 返回原始函数的执行结果
        return result
    return wrapper

@timer_decorator
def calculate_sum(a, b):
    """计算两个数的和，并模拟一个耗时操作。"""
    print(f"正在计算 {a} + {b} ...")
    time.sleep(1) # 模拟耗时
    return a + b

# 调用被装饰的函数
sum_result = calculate_sum(10, 20)
print(f"计算结果是: {sum_result}")

# 预期输出 (耗时可能略有不同):
# 正在计算 10 + 20 ...
# 函数 'calculate_sum' 执行耗时: 1.0012 秒
# 计算结果是: 30
```

#### 特性2: 带参数的装饰器
有时候，我们希望装饰器本身也能接收参数，就像给“装备”镶嵌不同属性的“宝石”。例如，一个重试装饰器，我们想指定重试的次数。这需要再加一层函数嵌套。

```python
def retry(max_attempts):
    """
    一个可以指定重试次数的装饰器。
    这是一个装饰器工厂，调用它会返回一个真正的装饰器。
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            attempts = 0
            while attempts < max_attempts:
                try:
                    print(f"[尝试第 {attempts + 1} 次] ", end="")
                    return func(*args, **kwargs)
                except Exception as e:
                    attempts += 1
                    print(f"执行失败: {e}. ", end="")
                    if attempts == max_attempts:
                        print("达到最大尝试次数，任务失败。")
                        raise # 重新抛出最后的异常
            return None # 理论上不会执行到这里
        return wrapper
    return decorator

# 使用带参数的装饰器，指定重试3次
@retry(max_attempts=3)
def fetch_data_from_flaky_server():
    """模拟从一个不稳定的服务器获取数据。"""
    import random
    if random.random() < 0.7: # 70%的概率失败
        raise ConnectionError("网络连接超时")
    print("数据获取成功！")
    return {"data": "some important data"}

# 调用函数
fetch_data_from_flaky_server()

# 可能的预期输出 1 (在前两次失败后成功):
# [尝试第 1 次] 执行失败: 网络连接超时. [尝试第 2 次] 执行失败: 网络连接超时. [尝试第 3 次] 数据获取成功！

# 可能的预期输出 2 (三次全部失败):
# [尝试第 1 次] 执行失败: 网络连接超时. [尝试第 2 次] 执行失败: 网络连接超时. [尝试第 3 次] 执行失败: 网络连接超时. 达到最大尝试次数，任务失败。
# (然后会抛出 ConnectionError)
```

### 🔍 Level 3: 对比学习（避免陷阱）
一个常见的陷阱是，装饰器会“偷走”原函数的元信息（如函数名 `__name__`、文档字符串 `__doc__` 等），这会给调试带来困扰。

```python
# === 错误用法 ===
# ❌ 未使用 functools.wraps
import time

def timer_decorator_naive(func):
    def wrapper(*args, **kwargs):
        """我是 wrapper 函数的文档字符串"""
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        print(f"耗时: {end_time - start_time:.4f}s")
        return result
    return wrapper

@timer_decorator_naive
def slow_add(a, b):
    """这是一个计算两个数之和的慢函数。"""
    time.sleep(0.5)
    return a + b

print(f"函数名: {slow_add.__name__}")
print(f"函数文档: {slow_add.__doc__}")
# 解释为什么是错的:
# 看到输出了吗？函数名变成了 'wrapper'，文档字符串也变成了 wrapper 的，
# 原本 slow_add 的信息丢失了！这在大型项目中进行代码检查和调试时是灾难性的。

# === 正确用法 ===
# ✅ 使用 functools.wraps 保护原函数信息
import functools

def timer_decorator_pro(func):
    @functools.wraps(func) # 关键就是这一行！
    def wrapper(*args, **kwargs):
        """我是 wrapper 函数的文档字符串，但我不会覆盖原函数的。"""
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        print(f"耗时: {end_time - start_time:.4f}s")
        return result
    return wrapper

@timer_decorator_pro
def slow_multiply(a, b):
    """这是一个计算两个数之积的慢函数。"""
    time.sleep(0.5)
    return a * b

print("\n" + "="*20 + "\n")
print(f"函数名: {slow_multiply.__name__}")
print(f"函数文档: {slow_multiply.__doc__}")
# 解释为什么这样是对的:
# @functools.wraps(func) 就像一个魔法咒语，它把原函数 func 的元信息
# (如 __name__, __doc__ 等) 复制到了 wrapper 函数上。
# 这样，无论我们如何装饰，函数的“身份”都得以保留。
```

### 🚀 Level 4: 实战应用（真实场景）
**场景：** 🎮 魔法学院的技能授权系统

在霍格沃茨，不是每个巫师都能使用所有咒语。我们需要一个系统来检查施法者是否有权限使用某个强大的咒语。装饰器是实现这个权限检查的完美工具！

```python
import functools

# 用户权限数据库 (简化版)
USER_PERMISSIONS = {
    "Harry": ["Expecto Patronum", "Expelliarmus"],
    "Ron": ["Expelliarmus"],
    "Draco": [],
}

# 当前登录用户 (可以改变这个值来测试)
current_user = "Harry"

def requires_permission(permission):
    """
    权限检查装饰器。
    检查当前用户是否拥有施放特定咒语的权限。
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            print(f"'{current_user}' 正在尝试施放咒