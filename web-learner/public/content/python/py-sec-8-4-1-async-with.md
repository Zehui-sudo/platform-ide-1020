## async with 上下文管理器

### 🎯 核心概念
`async with` 是 Python 用于**异步资源管理**的上下文管理器语法，解决了普通 `with` 无法处理异步操作（如异步数据库连接、HTTP 客户端会话）的问题，确保异步资源在使用后能正确释放（即使发生异常）。


### 💡 使用方式
`async with` 的核心是**异步上下文管理器**——需实现两个异步方法：
- `__aenter__()`：异步获取资源（进入上下文时调用）；
- `__aexit__(exc_type, exc_val, exc_tb)`：异步释放资源（退出上下文时调用，可处理异常）。

语法结构：
```python
async def main():
    async with 异步上下文对象 as 资源变量:
        # 使用资源（可包含 await 操作）
```


### 📚 Level 1: 基础认知（30秒理解）
先看一个最简单的异步上下文管理器示例，模拟异步资源的获取与释放：

```python
import asyncio

class AsyncResource:
    async def __aenter__(self):
        print("🔑 异步获取资源（模拟耗时操作）")
        await asyncio.sleep(0.1)  # 模拟异步IO
        return self  # 返回资源对象给 as 变量
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        print("🔓 异步释放资源（模拟耗时操作）")
        await asyncio.sleep(0.1)

async def main():
    print("=== 开始 ===")
    async with AsyncResource() as ar:
        print("✅ 使用异步资源")
    print("=== 结束 ===")

asyncio.run(main())
```

**预期输出**：
```
=== 开始 ===
🔑 异步获取资源（模拟耗时操作）
✅ 使用异步资源
🔓 异步释放资源（模拟耗时操作）
=== 结束 ===
```


### 📈 Level 2: 核心特性（深入理解）
#### 特性1: 异常处理与资源兜底
`__aexit__` 可捕获上下文内的异常，并决定是否“吞掉”异常（返回 `True`）或继续抛出（返回 `False`）。下面示例展示异常时如何保证资源释放：

```python
import asyncio

class SafeAsyncResource:
    async def __aenter__(self):
        print("🔑 获取数据库连接")
        return self  # 返回数据库连接对象
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        print(f"⚠️ 捕获异常：{exc_val}")
        print("🔓 关闭数据库连接（无论是否异常）")
        await asyncio.sleep(0.1)
        return True  # 吞掉异常，外部不会收到

async def main():
    try:
        async with SafeAsyncResource() as db:
            print("✅ 执行数据库操作")
            raise ValueError("模拟数据库查询错误")  # 故意抛出异常
    except ValueError:
        print("❌ 外部捕获到异常？")  # 不会执行，因为__aexit__返回True

asyncio.run(main())
```

**预期输出**：
```
🔑 获取数据库连接
✅ 执行数据库操作
⚠️ 捕获异常：模拟数据库查询错误
🔓 关闭数据库连接（无论是否异常）
```


#### 特性2: 用装饰器简化实现
通过 `contextlib.asynccontextmanager` 装饰器，可将**异步生成器函数**直接转为异步上下文管理器，无需手动写类：

```python
from contextlib import asynccontextmanager
import asyncio

@asynccontextmanager
async def async_resource_manager():
    # __aenter__ 逻辑（获取资源）
    print("🔑 异步获取HTTP客户端会话")
    await asyncio.sleep(0.1)
    
    try:
        yield "模拟HTTP会话对象"  # 返回给 as 变量
    finally:
        # __aexit__ 逻辑（释放资源）
        print("🔓 异步关闭HTTP客户端会话")
        await asyncio.sleep(0.1)

async def main():
    async with async_resource_manager() as session:
        print(f"✅ 使用资源：{session}")

asyncio.run(main())
```

**预期输出**：
```
🔑 异步获取HTTP客户端会话
✅ 使用资源：模拟HTTP会话对象
🔓 异步关闭HTTP客户端会话
```


### 🔍 Level 3: 对比学习（避免陷阱）
#### 错误用法 ❌：用普通 `with` 管理异步资源
普通 `with` 只认 `__enter__`/`__exit__` 同步方法，无法识别异步上下文管理器的 `__aenter__`/`__aexit__`：

```python
import asyncio

class AsyncResource:
    async def __aenter__(self):
        return self
    async def __aexit__(self, *args):
        pass

# 错误：普通with无法处理异步上下文管理器
def bad_main():
    with AsyncResource() as ar:  # 报错：AttributeError: __enter__
        pass

# bad_main()  # 取消注释会报错
```


#### 正确用法 ✅：必须在 `async` 函数中用 `async with`
```python
async def good_main():
    async with AsyncResource() as ar:
        print("✅ 正确使用异步资源")

asyncio.run(good_main())
```


### 🚀 Level 4: 实战应用（真实场景）
**场景**：用 `aiohttp` 异步爬取多个网页（需管理HTTP会话资源）。  
需先安装 `aiohttp`：`pip install aiohttp`

```python
import aiohttp
import asyncio

async def fetch_url(url: str):
    # 用async with管理aiohttp.ClientSession（异步资源）
    async with aiohttp.ClientSession() as session:
        # 用async with管理HTTP请求（异步资源）
        async with session.get(url) as response:
            return await response.text()  # 异步获取响应内容

async def main():
    urls = [
        "https://httpbin.org/get?name=Alice",
        "https://httpbin.org/get?name=Bob",
        "https://httpbin.org/get?name=Charlie"
    ]
    # 并发执行多个异步任务
    tasks = [fetch_url(url) for url in urls]
    results = await asyncio.gather(*tasks)
    
    # 打印结果
    for url, result in zip(urls, results):
        print(f"📌 URL: {url}，响应长度: {len(result)}")

if __name__ == "__main__":
    asyncio.run(main())
```

**预期输出**：
```
📌 URL: https://httpbin.org/get?name=Alice，响应长度: 352
📌 URL: https://httpbin.org/get?name=Bob，响应长度: 350
📌 URL: https://httpbin.org/get?name=Charlie，响应长度: 354
```


### 💡 记忆要点
- `async with` 用于**异步资源**管理，对应异步上下文管理器（`__aenter__`/`__aexit__`）；
- 可用 `@asynccontextmanager` 装饰器简化异步上下文管理器的实现；
- `__aexit__` 可处理异常（返回 `True` 吞掉异常，`False` 抛出）；
- 必须在 `async` 函数中使用 `async with`；
- 真实场景常见于：`aiohttp.ClientSession`、异步数据库连接（如 `asyncpg`）、WebSocket 会话等。