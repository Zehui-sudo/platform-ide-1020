## async for 与异步生成器

### 🎯 核心概念
`async for` 用于遍历**异步迭代器**（实现 `__aiter__` 和 `__anext__` 方法的对象），解决了「异步场景下逐次获取结果」的问题；而异步生成器是创建异步迭代器的便捷方式（用 `async def` 加 `yield` 定义），能在迭代过程中暂停执行异步操作，避免一次性等待所有结果完成。


### 💡 使用方式
1. **异步生成器定义**：用 `async def` 定义函数，内部用 `yield` 返回值（每次 `yield` 会暂停函数，等待下一次迭代恢复）；  
2. **`async for` 遍历**：用 `async for item in async_iterable:` 语法遍历异步迭代器，每次迭代会等待 `__anext__()` 完成（即异步操作结束）。


### 📚 Level 1: 基础认知（30秒理解）
最简化示例：异步生成器每秒生成一个数字，`async for` 逐次获取。

```python
import asyncio

# 定义异步生成器：每秒生成一个数字
async def async_number_generator():
    for i in range(3):
        await asyncio.sleep(1)  # 模拟异步等待（比如网络请求）
        yield i  # 暂停并返回当前值，下一次迭代从这里恢复

async def main():
    # 用async for遍历异步生成器
    async for num in async_number_generator():
        print(f"获取到数字: {num}")  # 1秒后输出0，再1秒输出1，再1秒输出2

# 运行事件循环
asyncio.run(main())
```


### 📈 Level 2: 核心特性（深入理解）
#### 特性1: 逐次执行异步操作（分页数据场景）
异步生成器的核心价值是**将异步操作与迭代结合**，比如逐页获取API数据（不需要等所有页加载完成）。

```python
import asyncio
from typing import List

# 模拟异步获取单页数据（比如调用API）
async def fetch_page_data(page: int) -> str:
    await asyncio.sleep(0.5)  # 模拟网络延迟
    return f"第{page}页数据: 商品列表[{page}01, {page}02]"

# 定义异步生成器：逐页返回数据
async def paginated_data_generator(total_pages: int) -> str:
    for page in range(1, total_pages + 1):
        data = await fetch_page_data(page)  # 等待单页数据加载
        yield data  # 返回当前页数据，下一次迭代继续获取下一页

async def main():
    # 遍历并打印3页数据
    async for page_data in paginated_data_generator(3):
        print(page_data)  # 0.5秒后输出第1页，再0.5秒第2页，再0.5秒第3页

asyncio.run(main())
```


#### 特性2: 自动资源清理（finally 保障）
异步生成器会自动调用 `aclose()` 方法（即使循环提前终止），可通过 `try...finally` 清理资源（比如关闭文件/数据库连接）。

```python
import asyncio

async def resource_heavy_generator():
    print("初始化资源（比如打开数据库连接）")
    try:
        for i in range(2):
            await asyncio.sleep(1)
            yield i
    finally:
        print("清理资源（比如关闭数据库连接）")  # 必执行！

async def main():
    async for num in resource_heavy_generator():
        print(f"获取到: {num}")
        if num == 0:
            break  # 提前终止循环（模拟异常场景）

asyncio.run(main())
# 输出顺序：
# 初始化资源 → 获取到: 0 → 清理资源
```


### 🔍 Level 3: 对比学习（避免陷阱）
#### 陷阱1: 用普通 `for` 遍历异步生成器（错误）
普通 `for` 无法处理异步迭代器，会直接返回**异步生成器对象**而非结果。

```python
import asyncio

async def async_gen():
    yield 1
    yield 2

# ❌ 错误用法：普通for循环无法等待异步操作
def bad_main():
    for item in async_gen():
        print(item)  # 输出: <async_generator object async_gen at 0x...>

# ✅ 正确用法：必须用async for
async def good_main():
    async for item in async_gen():
        print(item)  # 输出: 1 → 2

asyncio.run(good_main())
```


#### 陷阱2: 忘记 `await` 异步操作（同步执行）
异步生成器中的异步操作必须加 `await`，否则会**跳过等待**（变成同步执行）。

```python
import asyncio

# ❌ 错误：忘记await asyncio.sleep(1)
async def bad_async_gen():
    for i in range(2):
        asyncio.sleep(1)  # 无await，不会暂停
        yield i

# ✅ 正确：加上await
async def good_async_gen():
    for i in range(2):
        await asyncio.sleep(1)  # 等待1秒
        yield i

async def main():
    print("错误示例（无等待）:")
    async for num in bad_async_gen():
        print(num)  # 瞬间输出0 → 1（无延迟）
    
    print("\n正确示例（有等待）:")
    async for num in good_async_gen():
        print(num)  # 1秒后输出0 → 再1秒输出1

asyncio.run(main())
```


### 🚀 Level 4: 实战应用（真实场景）
**场景**：异步爬取多个网页的标题（用 `aiohttp` 发起异步请求，`BeautifulSoup` 解析）。  
需提前安装依赖：`pip install aiohttp beautifulsoup4`

```python
import asyncio
from aiohttp import ClientSession
from bs4 import BeautifulSoup

# 异步获取网页标题
async def fetch_title(url: str, session: ClientSession) -> tuple[str, str]:
    async with session.get(url) as response:
        html = await response.text()
        soup = BeautifulSoup(html, "html.parser")
        title = soup.title.string if soup.title else "无标题"
        return (url, title)

# 异步生成器：逐次返回网页标题
async def title_generator(urls: List[str]) -> tuple[str, str]:
    async with ClientSession() as session:  # 复用HTTP连接池
        for url in urls:
            url, title = await fetch_title(url, session)
            yield (url, title)

async def main():
    urls = [
        "https://www.python.org",
        "https://www.github.com",
        "https://www.aiohttp.org"
    ]
    async for url, title in title_generator(urls):
        print(f"{url} → 标题: {title}")

asyncio.run(main())
# 输出示例：
# https://www.python.org → 标题: Python.org
# https://www.github.com → 标题: GitHub: Let’s build from here · GitHub
# https://www.aiohttp.org → 标题: aiohttp — Async HTTP client/server for asyncio and Python
```


### 💡 记忆要点
1. `async for` 是异步迭代的唯一方式，必须搭配**异步迭代器**（如异步生成器）；  
2. 异步生成器用 `async def + yield` 定义，自动实现异步迭代器协议（`__aiter__`/`__anext__`）；  
3. 异步生成器中的 `yield` 会**暂停执行**，等待下一次 `async for` 迭代时恢复；  
4. 无论循环是否正常结束，异步生成器都会自动调用 `aclose()`，用 `try...finally` 保障资源清理；  
5. 永远不要在异步生成器中遗漏 `await` —— 否则异步操作会变成同步执行。