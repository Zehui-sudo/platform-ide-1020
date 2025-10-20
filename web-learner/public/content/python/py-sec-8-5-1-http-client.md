## HTTP 客户端 (httpx/aiohttp)

### 🎯 核心概念
解决 Python 中**发送 HTTP 请求**的需求，尤其在异步场景下实现**高效 IO 操作**。httpx 支持同步/异步双模式（兼容 requests API），aiohttp 是 Python 生态最成熟的**纯异步 HTTP 客户端**，二者均为现代 Python 网络请求的主流选择。


### 💡 使用方式
1. 安装依赖：`pip install httpx aiohttp`  
2. 核心场景：
   - 同步请求：优先用 `httpx`（API 与 requests 几乎一致，学习成本低）；
   - 异步请求：用 `aiohttp`（纯异步，性能更优）或 `httpx.AsyncClient`；
   - 均需通过**会话对象**（Session/ClientSession）管理连接池，避免重复创建客户端。


### 📚 Level 1: 基础认知（30秒理解）
用最简代码实现**同步+异步**的 GET 请求，快速验证功能。

```python
# 1. httpx 同步 GET 请求
import httpx

def sync_get():
    response = httpx.get("https://httpbin.org/get")  # 发送GET请求
    print("同步响应状态码:", response.status_code)  # 输出: 200
    print("同步响应内容:", response.json()["args"])  # 输出: {}（无查询参数）

# 2. aiohttp 异步 GET 请求
import aiohttp
import asyncio

async def async_get():
    async with aiohttp.ClientSession() as session:  # 异步会话（必须用async with）
        response = await session.get("https://httpbin.org/get")  #  await 挂起请求
        print("异步响应状态码:", response.status)  # 输出: 200
        print("异步响应内容:", await response.json())  #  await 解析JSON

# 执行异步函数
if __name__ == "__main__":
    sync_get()
    asyncio.run(async_get())
```


### 📈 Level 2: 核心特性（深入理解）
#### 特性1: 会话保持（连接池优化）
会话对象会复用 TCP 连接，减少握手开销，**必用特性**！

```python
# httpx 同步会话
with httpx.Client() as client:  # 自动管理连接池
    response1 = client.get("https://httpbin.org/cookies/set?name=httpx")
    response2 = client.get("https://httpbin.org/cookies")  # 保持cookie
    print("同步会话的Cookies:", response2.json()["cookies"])  # 输出: {'name': 'httpx'}

# aiohttp 异步会话
async def async_session_demo():
    async with aiohttp.ClientSession() as session:  # 异步上下文管理器
        response1 = await session.get("https://httpbin.org/cookies/set?name=aiohttp")
        response2 = await session.get("https://httpbin.org/cookies")
        print("异步会话的Cookies:", await response2.json())  # 输出: {'cookies': {'name': 'aiohttp'}}

asyncio.run(async_session_demo())
```

#### 特性2: 发送 JSON 与处理响应
常见于 POST 请求（如调用 REST API）。

```python
# httpx 发送 JSON（同步）
with httpx.Client() as client:
    data = {"username": "test", "password": "123"}
    response = client.post("https://httpbin.org/post", json=data)  # 自动设置Content-Type: application/json
    print("JSON响应:", response.json()["json"])  # 输出: {'username': 'test', 'password': '123'}

# aiohttp 发送 JSON（异步）
async def async_post_json():
    async with aiohttp.ClientSession() as session:
        data = {"title": "async demo"}
        response = await session.post("https://httpbin.org/post", json=data)
        print("异步JSON响应:", await response.json())  # 输出包含data的响应

asyncio.run(async_post_json())
```

#### 特性3: 带参数与 Headers 的请求
模拟浏览器请求或传递认证信息。

```python
# httpx 带查询参数与Headers
params = {"q": "python httpx"}  # URL参数: ?q=python+httpx
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
response = httpx.get("https://httpbin.org/get", params=params, headers=headers)
print("带参数的URL:", response.url)  # 输出: https://httpbin.org/get?q=python+httpx
print("请求Headers:", response.json()["headers"]["User-Agent"])  # 输出模拟的浏览器UA
```


### 🔍 Level 3: 对比学习（避免陷阱）
#### 陷阱1: 忘记关闭会话（资源泄漏）
**错误用法**：每次请求都创建新客户端（重复建立连接，浪费资源）
```python
# ❌ 错误：频繁创建Client，导致资源泄漏
for _ in range(10):
    client = httpx.Client()
    client.get("https://httpbin.org/get")
    # 未关闭client！
```

**正确用法**：用上下文管理器自动关闭
```python
# ✅ 正确：上下文管理器自动管理会话生命周期
with httpx.Client() as client:
    for _ in range(10):
        client.get("https://httpbin.org/get")
```

#### 陷阱2: 同步代码阻塞异步循环
**错误用法**：在异步函数中调用同步 httpx 请求（阻塞事件循环）
```python
async def bad_async_code():
    # ❌ 同步httpx请求会阻塞整个事件循环！
    response = httpx.get("https://httpbin.org/get")
    print(response.text)

# 正确用法：使用httpx的异步客户端
async def good_async_code():
    async with httpx.AsyncClient() as client:  # 异步Client
        response = await client.get("https://httpbin.org/get")
        print(response.text)

asyncio.run(good_async_code())
```


### 🚀 Level 4: 实战应用（真实场景）
**场景**：批量获取 GitHub 用户信息（异步并发提升效率）  
需求：给定10个GitHub用户名，批量请求其公开信息，计算总耗时。

```python
import aiohttp
import asyncio
import time

# 要查询的GitHub用户名列表
USERS = ["octocat", "torvalds", "guaosi", "numpy", "pandas-dev", "python", "asyncio", "aiohttp", "httpx", "requests"]

async def fetch_user(session: aiohttp.ClientSession, username: str):
    """异步获取单个用户信息"""
    url = f"https://api.github.com/users/{username}"
    async with session.get(url) as response:
        response.raise_for_status()  # 检查HTTP错误（如404）
        return await response.json()

async def main():
    start_time = time.time()
    async with aiohttp.ClientSession() as session:
        # 创建所有异步任务（并发执行）
        tasks = [fetch_user(session, user) for user in USERS]
        # 等待所有任务完成
        results = await asyncio.gather(*tasks)
    
    # 输出结果（仅展示部分字段）
    for user in results:
        print(f"用户: {user['login']}，仓库数: {user['public_repos']}")
    
    print(f"\n总耗时: {time.time() - start_time:.2f}秒")

if __name__ == "__main__":
    asyncio.run(main())
```

**运行结果**（示例）：
```
用户: octocat，仓库数: 8
用户: torvalds，仓库数: 8
用户: guaosi，仓库数: 34
...
总耗时: 0.87秒  # 同步请求需约10秒，异步提升10倍效率！
```


### 💡 记忆要点
- 🔗 **优先使用会话对象**：用`with`上下文管理器管理`ClientSession`/`AsyncClient`，避免资源泄漏。
- ⏳ **异步请求必加await**：`aiohttp`和`httpx.AsyncClient`的请求方法均需`await`。
- 🚨 **检查响应状态**：用`response.raise_for_status()`快速定位HTTP错误（如404、500）。
- 🚀 **库的选择**：同步用`httpx`（兼容requests），高并发异步用`aiohttp`（性能更优）。
- ⚠️ **避免同步阻塞**：异步函数中绝对不能调用同步HTTP请求（如`httpx.get()`）！