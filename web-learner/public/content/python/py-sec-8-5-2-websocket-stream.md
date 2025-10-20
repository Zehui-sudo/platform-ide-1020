## WebSocket 与流式处理

### 🎯 核心概念
WebSocket 解决了 HTTP 单向、短连接的痛点，实现**双向实时通信**（客户端与服务器可互相主动发消息）；流式处理则是将数据**分块传输**（如 AI 逐字回复、实时日志推送），避免等待全部数据加载完成，提升交互体验。两者结合是构建实时应用（如 ChatGPT 对话、实时监控）的关键。


### 💡 使用方式
Python 中常用 `websockets` 库（基于 `asyncio`）实现 WebSocket，核心 API：
- 服务器：`websockets.serve()` 启动服务，处理客户端连接；
- 客户端：`websockets.connect()` 建立连接；
- 收发消息：`await websocket.send()`（发）、`await websocket.recv()`（收）或 `async for message in websocket`（迭代收）。


### 📚 Level 1: 基础认知（30秒理解）
最简化的 **Echo 服务器**：客户端发什么，服务器原样返回。  
需先安装依赖：`pip install websockets`

#### 服务器代码（server.py）
```python
import asyncio
import websockets

# 处理客户端连接的异步函数
async def echo_handler(websocket):
    # 迭代接收客户端消息（async for 自动处理多消息）
    async for message in websocket:
        print(f"Received: {message}")
        # 原样返回消息
        await websocket.send(f"Echo: {message}")

async def main():
    # 启动 WebSocket 服务器（监听 localhost:8765）
    async with websockets.serve(echo_handler, "localhost", 8765):
        await asyncio.Future()  # 保持服务器运行（永久阻塞）

asyncio.run(main())
```

#### 客户端代码（client.py）
```python
import asyncio
import websockets

async def echo_client():
    # 建立 WebSocket 连接（async with 自动关闭）
    async with websockets.connect("ws://localhost:8765") as websocket:
        # 发送消息
        message = "Hello WebSocket!"
        await websocket.send(message)
        # 接收回复
        response = await websocket.recv()
        print(f"Received: {response}")  # 输出: Echo: Hello WebSocket!

asyncio.run(echo_client())
```

**运行方式**：先启动服务器（`python server.py`），再运行客户端（`python client.py`）。


### 📈 Level 2: 核心特性（深入理解）
#### 特性1：双向实时通信（客户端与服务器互发消息）
扩展 Echo 服务器，支持**客户端连续发消息**，服务器实时回复：

```python
# 服务器代码（修改echo_handler）
async def echo_handler(websocket):
    try:
        while True:
            # 手动接收消息（更灵活的控制）
            message = await websocket.recv()
            print(f"Client said: {message}")
            # 服务器主动发消息（双向通信）
            await websocket.send(f"Server reply: {message}")
    except websockets.ConnectionClosed:
        print("Client disconnected")

# 客户端代码（修改echo_client）
async def echo_client():
    async with websockets.connect("ws://localhost:8765") as websocket:
        # 连续发送3条消息
        for i in range(3):
            message = f"Message {i+1}"
            await websocket.send(message)
            response = await websocket.recv()
            print(f"Server replied: {response}")
```

**运行效果**：客户端依次收到 `Server reply: Message 1`、`Server reply: Message 2` 等。


#### 特性2：流式数据传输（模拟AI逐字回复）
服务器**分块发送数据**，客户端**逐块接收**（如 ChatGPT 的“打字机”效果）：

```python
# 服务器代码（stream_server.py）
import asyncio
import websockets

async def stream_handler(websocket):
    # 模拟 AI 流式回复（逐句发送《春晓》）
    poem = ["春眠不觉晓，", "处处闻啼鸟。", "夜来风雨声，", "花落知多少。"]
    for line in poem:
        await websocket.send(line)
        await asyncio.sleep(1)  # 模拟1秒思考延迟

async def main():
    async with websockets.serve(stream_handler, "localhost", 8765):
        await asyncio.Future()

asyncio.run(main())
```

```python
# 客户端代码（stream_client.py）
import asyncio
import websockets

async def stream_client():
    async with websockets.connect("ws://localhost:8765") as websocket:
        print("Receiving stream:")
        while True:
            try:
                # 逐块接收数据
                chunk = await websocket.recv()
                print(chunk, end="", flush=True)  # end="" 不换行，flush=True 实时打印
            except websockets.ConnectionClosed:
                # 服务器关闭连接时退出循环
                break

asyncio.run(stream_client())
```

**运行效果**：客户端会逐秒打印诗句，像“打字”一样。


### 🔍 Level 3: 对比学习（避免陷阱）
#### 常见陷阱：同步调用 vs 异步调用
WebSocket 是**异步协议**，必须用 `await` 处理收发操作，否则会报错！

```python
import websockets

# ❌ 错误用法：同步调用 recv()（无await，会抛 RuntimeError）
def wrong_client():
    with websockets.connect("ws://localhost:8765") as websocket:
        message = websocket.recv()  # 同步调用，非异步
        print(message)

# ✅ 正确用法：用 await 和 async 上下文
async def correct_client():
    async with websockets.connect("ws://localhost:8765") as websocket:
        message = await websocket.recv()  # 必须加 await
        print(message)

# 运行正确客户端
asyncio.run(correct_client())
```


### 🚀 Level 4: 实战应用（真实场景）
#### 场景：实时翻译工具
客户端发送英文句子，服务器**逐词翻译**并**流式返回结果**（模拟有道翻译的“实时预览”）。

#### 服务器代码（translate_server.py）
```python
import asyncio
import websockets
from typing import AsyncGenerator

# 模拟翻译函数（逐词翻译，返回异步生成器）
async def translate_stream(text: str) -> AsyncGenerator[str, None]:
    words = text.split()
    translations = {
        "Hello": "你好", "world": "世界", "this": "这", 
        "is": "是", "a": "一个", "test": "测试"
    }
    for word in words:
        await asyncio.sleep(0.5)  # 模拟翻译延迟
        yield translations.get(word, word) + " "  # 逐词返回翻译结果

# 处理翻译请求的 handler
async def translate_handler(websocket):
    async for message in websocket:
        print(f"Received: {message}")
        # 流式翻译并发送结果
        async for chunk in translate_stream(message):
            await websocket.send(chunk)

async def main():
    async with websockets.serve(translate_handler, "localhost", 8765):
        await asyncio.Future()

asyncio.run(main())
```

#### 客户端代码（translate_client.py）
```python
import asyncio
import websockets

async def translate_client():
    text = "Hello world this is a test"  # 待翻译的英文
    async with websockets.connect("ws://localhost:8765") as websocket:
        # 发送英文文本
        await websocket.send(text)
        print("Translating:")
        result = ""
        while True:
            try:
                # 逐词接收翻译结果
                chunk = await websocket.recv()
                result += chunk
                print(f"\r{result}", end="", flush=True)  # \r 回到行首，覆盖旧内容
            except websockets.ConnectionClosed:
                break
        print("\nTranslation complete!")

asyncio.run(translate_client())
```

**运行效果**：
```
Translating:
你好 世界 这 是 一个 测试 
Translation complete!
```


### 💡 记忆要点
1. WebSocket 是**全双工、长连接**协议，替代 HTTP 轮询（效率更高）；
2. 用 `websockets` 库结合 `asyncio` 实现异步 WebSocket，核心是 `await send()`/`await recv()`；
3. 流式处理的关键是**分块发送/接收**，用 `async for` 或循环 `await recv()`；
4. 务必处理 `websockets.ConnectionClosed` 异常，避免连接断开后程序崩溃；
5. 永远不要在异步函数中**同步调用** WebSocket 方法（必须加 `await`）。