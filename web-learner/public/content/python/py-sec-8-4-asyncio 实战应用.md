## 8.4 asyncio 实战应用

### 🎯 核心概念

在异步编程中，资源的获取和释放（如数据库连接）以及数据的迭代（如从网络流中读取数据）本身可能就是 I/O 密集型操作。`async with` 和 `async for` 提供了专门的语法，使得这些**需要 `await` 的资源管理和迭代过程**能够以一种自然、安全且非阻塞的方式进行，从而避免了手动管理的复杂性和潜在错误。

### 💡 使用方式

-   **异步上下文管理器 (`async with`)**: 用于需要异步操作来创建和销毁的资源。它依赖于对象实现 `__aenter__` 和 `__aexit__(self, exc_type, exc_val, traceback)` 这两个异步方法。
-   **异步迭代器 (`async for`)**: 用于遍历那些需要异步操作来获取下一个元素的数据集合。它依赖于对象实现 `__aiter__` 和 `__anext__` 方法，或者通过更简洁的异步生成器 (`async def` + `yield`) 来创建。

### 📚 Level 1: 基础认知（30秒理解）

让我们从最基础的 `async with` 和 `async for` 开始，感受它们的语法和作用。

```python
import asyncio

# --- 异步上下文管理器 (async with) ---
class AsyncResource:
    """一个需要异步获取和释放的模拟资源"""
    async def __aenter__(self):
        print("资源: 正在异步连接...")
        await asyncio.sleep(1)
        print("资源: 连接成功！")
        return self

    async def __aexit__(self, exc_type, exc_val, traceback):
        print("资源: 正在异步断开...")
        await asyncio.sleep(1)
        print("资源: 已安全断开！")

# --- 异步迭代器 (async for) ---
class AsyncCounter:
    """一个每隔一段时间产生一个数字的异步迭代器"""
    def __init__(self, limit):
        self.limit = limit
        self.count = 0

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self.count < self.limit:
            await asyncio.sleep(0.5)
            self.count += 1
            return f"数据点 {self.count}"
        else:
            raise StopAsyncIteration

async def main():
    print("--- 演示 async with ---")
    async with AsyncResource():
        print("在 'async with' 代码块内，资源已可用。")
    
    print("\n--- 演示 async for ---")
    async for item in AsyncCounter(3):
        print(f"接收到: {item}")

if __name__ == "__main__":
    asyncio.run(main())

# 预期输出结果:
# --- 演示 async with ---
# 资源: 正在异步连接...
# (等待1秒)
# 资源: 连接成功！
# 在 'async with' 代码块内，资源已可用。
# 资源: 正在异步断开...
# (等待1秒)
# 资源: 已安全断开！
#
# --- 演示 async for ---
# (等待0.5秒)
# 接收到: 数据点 1
# (等待0.5秒)
# 接收到: 数据点 2
# (等待0.5秒)
# 接收到: 数据点 3
```

### 📈 Level 2: 核心特性（深入理解）

#### 特性1: 异步生成器 - 更优雅的异步迭代

手动实现 `__aiter__` 和 `__anext__` 比较繁琐。Python 提供了**异步生成器 (Async Generator)**，让我们能用 `async def` 和 `yield` 关键字以更简洁、直观的方式创建异步迭代器。

```python
import asyncio
import random

async def sensor_data_stream(sensor_name):
    """
    一个异步生成器，模拟从传感器持续读取数据。
    它使用 `async def` 定义，并用 `yield` 产出数据。
    """
    print(f"▶️ 启动 {sensor_name} 传感器数据流...")
    for i in range(5):
        # 模拟异步获取数据，例如通过网络
        await asyncio.sleep(random.uniform(0.2, 0.6))
        yield f"[{sensor_name}] 读数: {random.randint(0, 100)}"
    print(f"⏹️ {sensor_name} 传感器数据流结束。")

async def main():
    print("--- 使用异步生成器处理传感器数据 ---")
    # async for 可以直接作用于异步生成器函数返回的对象
    async for data_point in sensor_data_stream("温度"):
        print(f"处理数据: {data_point}")

if __name__ == "__main__":
    asyncio.run(main())

# 预期输出结果 (每次的读数和间隔会变化):
# --- 使用异步生成器处理传感器数据 ---
# ▶️ 启动 温度 传感器数据流...
# 处理数据: [温度] 读数: 42
# 处理数据: [温度] 读数: 89
# 处理数据: [温度] 读数: 15
# 处理数据: [温度] 读数: 73
# 处理数据: [温度] 读数: 5
# ⏹️ 温度 传感器数据流结束。
```

#### 特性2: 在 `async with` 中处理异常

和普通的 `with` 语句一样，`async with` 也能保证即使在代码块内部发生异常，资源的清理逻辑 (`__aexit__`) 依然会被执行。`__aexit__` 方法会接收到异常的详细信息。

```python
import asyncio

class SafeAsyncDatabase:
    """一个模拟的数据库连接，能安全处理事务"""
    async def __aenter__(self):
        print("DB: [BEGIN] 开始事务。")
        await asyncio.sleep(0.5)
        return self

    async def __aexit__(self, exc_type, exc_val, traceback):
        await asyncio.sleep(0.5)
        if exc_type is not None:
            # 如果有异常发生，exc_type 将不是 None
            print(f"DB: [ROLLBACK] 发生错误 '{exc_val}'，事务回滚！")
        else:
            print("DB: [COMMIT] 操作成功，事务提交。")

async def main():
    print("--- 场景1: 操作成功 ---")
    async with SafeAsyncDatabase():
        print("执行数据库写入操作...")

    print("\n--- 场景2: 操作中发生异常 ---")
    try:
        async with SafeAsyncDatabase():
            print("执行数据库写入操作...")
            raise ValueError("写入数据格式错误")
    except ValueError as e:
        print(f"主程序捕获到异常: {e}")

if __name__ == "__main__":
    asyncio.run(main())

# 预期输出结果:
# --- 场景1: 操作成功 ---
# DB: [BEGIN] 开始事务。
# 执行数据库写入操作...
# DB: [COMMIT] 操作成功，事务提交。
#
# --- 场景2: 操作中发生异常 ---
# DB: [BEGIN] 开始事务。
# 执行数据库写入操作...
# DB: [ROLLBACK] 发生错误 '写入数据格式错误'，事务回滚！
# 主程序捕获到异常: 写入数据格式错误
```

### 🔍 Level 3: 对比学习（避免陷阱）

**陷阱：混用同步与异步的迭代/上下文**

在 `async def` 函数中，误用同步的 `for` 或 `with` 来处理异步对象，是初学者常犯的错误。这会导致 `TypeError`，因为 Python 的同步和异步协议是完全独立的。

```python
import asyncio

# 一个异步生成器
async def async_generator():
    yield 1

# 一个异步上下文管理器
class AsyncContext:
    async def __aenter__(self): pass
    async def __aexit__(self, *args): pass

async def main():
    # === 错误用法 ===
    # ❌ 尝试用同步 for 循环遍历异步生成器
    print("--- 错误用法: for ... in async_generator() ---")
    try:
        for _ in async_generator():
            pass
    except TypeError as e:
        print(f"捕获到错误: {e}")
    # 解释为什么是错的:
    # 普通的 for 循环期望一个实现了 __iter__ 和 __next__ 的同步迭代器。
    # 而 async_generator() 返回的是一个异步迭代器，它实现了 __aiter__ 和 __anext__。
    # 这两种协议不兼容，因此 Python 抛出 TypeError。

    # ❌ 尝试用同步 with 处理异步上下文管理器
    print("\n--- 错误用法: with AsyncContext() ---")
    try:
        with AsyncContext():
            pass
    except TypeError as e:
        print(f"捕获到错误: {e}")
    # 解释为什么是错的:
    # 普通的 with 语句需要一个实现了 __enter__ 和 __exit__ 的上下文管理器。
    # 而 AsyncContext 实例实现了 __aenter__ 和 __aexit__，用于 `async with`。
    # 同样，协议不匹配导致了 TypeError。

    # === 正确用法 ===
    # ✅ 必须使用 `async for` 和 `async with`
    print("\n--- 正确用法 ---")
    print("使用 'async for'...")
    async for _ in async_generator():
        pass
    print("使用 'async with'...")
    async with AsyncContext():
        pass
    print("✅ 正确的语法执行成功！")


if __name__ == "__main__":
    asyncio.run(main())

# 预期输出结果:
# --- 错误用法: for ... in async_generator() ---
# 捕获到错误: 'async_generator' object is not iterable
#
# --- 错误用法: with AsyncContext() ---
# 捕获到错误: 'AsyncContext' object does not support the context manager protocol
#
# --- 正确用法 ---
# 使用 'async for'...
# 使用 'async with'...
# ✅ 正确的语法执行成功！
```

### 🚀 Level 4: 实战应用（真实场景）

**场景：** 👾 Pokémon API 数据探查器

我们将构建一个异步程序，它能并发地从 PokéAPI 获取多个宝可梦的数据。我们将使用 `aiohttp` 这个流行的异步 HTTP 客户端库，它完美地集成了 `async with` 语法，让我们能高效、优雅地处理网络请求。

(首先需要安装 `aiohttp`: `pip install aiohttp`)

```python
import asyncio
import aiohttp

# API基础URL
BASE_URL = "https://pokeapi.co/api/v2/pokemon"

async def fetch_pokemon_data(session, pokemon_id):
    """
    使用 aiohttp session 异步获取单个宝可梦的数据。
    `session.get` 返回一个异步上下文管理器，必须用 `async with`。
    """
    url = f"{BASE_URL}/{pokemon_id}"
    print(f"⏳ 开始请求: {url}")
    try:
        # 这里的 `timeout` 是一个好习惯，防止请求永远卡住
        async with session.get(url, timeout=10) as response:
            # 检查HTTP状态码，如果响应状态码是 4xx 或 5xx，则抛出 ClientResponseError
            response.raise_for_status() 
            # response.json() 是一个协程，需要 await
            data = await response.json()
            print(f"✅ 请求成功: {data['name']}")
            return {
                "name": data["name"].capitalize(),
                "id": data["id"],
                "types": [t["type"]["name"] for t in data["types"]]
            }
    except aiohttp.ClientError as e:
        print(f"❌ 请求失败: {url}, 错误: {e}")
        return None
    except asyncio.TimeoutError:
        print(f"⏰ 请求超时: {url}")
        return None

async def main():
    pokemon_to_fetch = [1, 4, 7, 25, 133] #妙蛙种子, 小火龙, 杰尼龟, 皮卡丘, 伊布

    # aiohttp.ClientSession() 也是一个异步上下文管理器
    async with aiohttp.ClientSession() as session:
        # 创建一个任务列表
        tasks = [fetch_pokemon_data(session, pid) for pid in pokemon_to_fetch]
        
        # 使用 asyncio.gather 并发执行所有请求
        results = await asyncio.gather(*tasks)

    print("\n--- 👾 Pokedex 查询结果 ---")
    for data in results:
        if data:
            types_str = ", ".join(data["types"])
            print(f"#{data['id']:03d} - {data['name']:<10} | 类型: {types_str}")

if __name__ == "__main__":
    asyncio.run(main())

# 预期输出结果 (请求成功/失败的顺序可能不同，但最终报告是固定的):
# ⏳ 开始请求: https://pokeapi.co/api/v2/pokemon/1
# ⏳ 开始请求: https://pokeapi.co/api/v2/pokemon/4
# ⏳ 开始请求: https://pokeapi.co/api/v2/pokemon/7
# ⏳ 开始请求: https://pokeapi.co/api/v2/pokemon/25
# ⏳ 开始请求: https://pokeapi.co/api/v2/pokemon/133
# ✅ 请求成功: bulbasaur
# ✅ 请求成功: charmander
# ✅ 请求成功: squirtle
# ✅ 请求成功: pikachu
# ✅ 请求成功: eevee
#
# --- 👾 Pokedex 查询结果 ---
# #001 - Bulbasaur  | 类型: grass, poison
# #004 - Charmander | 类型: fire
# #007 - Squirtle   | 类型: water
# #025 - Pikachu    | 类型: electric
# #133 - Eevee      | 类型: normal
```

### 💡 记忆要点
- **要点1**: **异步配异步，同步配同步**。`async with` 用于处理实现了 `__aenter__/__aexit__` 的异步资源；`async for` 用于遍历实现了 `__aiter__/__anext__` 的异步序列。绝不能混用。
- **要点2**: **异步生成器是首选**。当需要创建异步迭代器时，优先使用 `async def` + `yield` 的异步生成器语法，它比手动实现协议类更简洁、更不易出错。
- **要点3**: **`aiohttp` 是实战利器**。它是 `asyncio` 生态中进行网络编程的事实标准。其 `ClientSession` 和 `response` 对象都是异步上下文管理器，完美体现了 `async with` 在真实场景中的强大作用。