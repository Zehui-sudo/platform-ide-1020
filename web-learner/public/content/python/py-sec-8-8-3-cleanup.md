## 资源释放与优雅关闭

### 🎯 核心概念
解决异步程序中**资源泄漏**（如文件未关闭、数据库连接未归还）和**强制退出不优雅**（如Ctrl+C直接中断导致任务残留）的问题，确保资源正确释放、任务有序终止，避免系统资源浪费或数据损坏。


### 💡 使用方式
通过**异步上下文管理器**（`async with`）、**`try-finally`块**、**信号处理**、**事件循环清理**等方式，保证资源在使用后或程序退出前被正确释放。


### 📚 Level 1: 基础认知（30秒理解）
用`async with`管理最常见的异步资源（如文件），自动完成“打开-使用-关闭”流程：
```python
import aiofiles  # 需要先安装：pip install aiofiles
import asyncio

async def read_file():
    # `async with`会自动关闭文件（即使中间出错）
    async with aiofiles.open("test.txt", "r") as f:
        content = await f.read()
        print(content)  # 预期输出：test.txt的内容（需提前创建文件）

asyncio.run(read_file())
```


### 📈 Level 2: 核心特性（深入理解）
#### 特性1: `async with`管理异步资源池（数据库连接）
数据库连接池是典型的“需复用+需释放”资源，用`async with`从池获取连接，自动归还：
```python
import asyncpg  # 需要先安装：pip install asyncpg
import asyncio

async def query_db():
    # 初始化连接池（5个连接）
    pool = await asyncpg.create_pool(
        user="postgres", password="your_pass", database="test_db", host="localhost"
    )
    try:
        # `async with`从池取连接，用完自动归还
        async with pool.acquire() as conn:
            result = await conn.fetchval("SELECT 2 + 3")
            print(f"Database result: {result}")  # 预期输出：5
    finally:
        # 最终关闭整个连接池（即使中间报错）
        await pool.close()

asyncio.run(query_db())
```


#### 特性2: `try-finally`兜底清理（自定义任务）
对于无法用`async with`的资源（如长期运行的任务），用`finally`确保清理：
```python
import asyncio

async def background_task(stop_flag):
    """模拟需要优雅停止的后台任务"""
    while not stop_flag.is_set():
        print("Background task running...")
        await asyncio.sleep(1)

async def main():
    stop_flag = asyncio.Event()
    task = asyncio.create_task(background_task(stop_flag))
    
    try:
        await asyncio.sleep(3)  # 让任务运行3秒
        print("Main task done,准备清理...")
    finally:
        # 无论是否异常，都停止后台任务
        stop_flag.set()
        await task  # 等待任务完全终止
        print("Background task stopped gracefully")

asyncio.run(main())
# 预期输出：
# Background task running...
# Background task running...
# Background task running...
# Main task done,准备清理...
# Background task stopped gracefully
```


#### 特性3: 处理系统信号（优雅应对Ctrl+C）
程序运行时按`Ctrl+C`会触发`SIGINT`信号，需捕获并执行清理逻辑：
```python
import asyncio
import signal

async def run_forever(stop_event):
    while not stop_event.is_set():
        print("Running... (Press Ctrl+C to stop)")
        await asyncio.sleep(1)

def handle_signal(stop_event):
    """信号处理器：触发停止事件"""
    def inner(signal_num, frame):
        print("\nReceived stop signal, cleaning up...")
        stop_event.set()
    return inner

async def main():
    stop_event = asyncio.Event()
    loop = asyncio.get_running_loop()
    
    # 注册信号处理器（处理Ctrl+C和kill命令）
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, handle_signal(stop_event))
    
    # 启动任务
    task = asyncio.create_task(run_forever(stop_event))
    
    # 等待停止信号
    await stop_event.wait()
    # 等待任务终止
    await task
    print("Program exited gracefully")

asyncio.run(main())
# 运行后按Ctrl+C：
# Running... (Press Ctrl+C to stop)
# Running... (Press Ctrl+C to stop)
# ^C
# Received stop signal, cleaning up...
# Program exited gracefully
```


### 🔍 Level 3: 对比学习（避免陷阱）
#### 错误用法：忘记释放资源
直接打开文件但未关闭，导致资源泄漏：
```python
import aiofiles
import asyncio

async def bad_example():
    f = await aiofiles.open("test.txt", "r")  # 打开文件
    content = await f.read()
    print(content)
    # 没有关闭文件！资源泄漏！

asyncio.run(bad_example())
```

#### 正确用法：用`async with`自动释放
```python
import aiofiles
import asyncio

async def good_example():
    async with aiofiles.open("test.txt", "r") as f:  # 自动关闭
        content = await f.read()
        print(content)

asyncio.run(good_example())
```


### 🚀 Level 4: 实战应用（异步HTTP服务）
用`aiohttp`实现一个Web服务，优雅处理启动/关闭流程：
```python
from aiohttp import web
import asyncio
import signal

# 模拟数据库资源
class Database:
    async def connect(self):
        print("✅ Database connected")
    async def disconnect(self):
        print("❌ Database disconnected")

# 请求处理函数
async def hello(request):
    return web.Response(text="Hello, Async World!")

# 启动钩子：初始化资源
async def on_startup(app):
    app["db"] = Database()
    await app["db"].connect()

# 清理钩子：释放资源
async def on_cleanup(app):
    await app["db"].disconnect()

# 信号处理：优雅关闭服务器
async def shutdown_server(app):
    print("\n⚠️  Received shutdown signal, cleaning up...")
    # 停止所有活跃任务
    for task in asyncio.all_tasks():
        if task is not asyncio.current_task():
            task.cancel()
    # 关闭服务器
    await app.shutdown()
    await app.cleanup()

def setup_signals(app):
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(
            sig, lambda: asyncio.create_task(shutdown_server(app))
        )

async def main():
    app = web.Application()
    app.add_routes([web.get("/", hello)])
    
    # 注册启动/清理钩子
    app.on_startup.append(on_startup)
    app.on_cleanup.append(on_cleanup)
    
    # 设置信号处理器
    setup_signals(app)
    
    # 启动服务器
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "localhost", 8080)
    await site.start()
    print("🌐 Server started at http://localhost:8080")
    
    # 保持运行直到信号触发
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
```
运行后访问`http://localhost:8080`会看到`Hello, Async World!`，按`Ctrl+C`会触发清理流程，打印数据库断开信息。


### 💡 记忆要点
- **优先用`async with`**：管理异步资源的“黄金法则”，自动释放更可靠；
- **`try-finally`兜底**：无法用上下文管理器时，确保清理逻辑执行；
- **处理系统信号**：捕获`SIGINT/SIGTERM`，避免强制退出导致资源泄漏；
- **框架钩子利用**：如`aiohttp`的`on_cleanup`，框架已封装好清理时机；
- **清理所有任务**：退出前终止事件循环中的遗留任务，避免“僵尸任务”。