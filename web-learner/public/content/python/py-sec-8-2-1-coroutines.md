## async/await 与协程

### 🎯 核心概念
协程是**单线程内的轻量级并发机制**，通过`async/await`语法实现"协作式"多任务——当一个任务需要等待IO（如网络请求、文件读写）时，主动让出CPU给其他任务，避免线程阻塞，比线程更高效（无上下文切换开销）。


### 💡 使用方式
1. **定义协程**：用`async def`声明函数（内部可使用`await`）；
2. **调用协程**：在`async`函数内用`await`等待协程执行完成；
3. **运行协程**：通过事件循环（如`asyncio.run()`）启动顶层协程。


### 📚 Level 1: 基础认知（30秒理解）
最简化的协程示例，体验`async/await`的基本流程：

```python
import asyncio

# 1. 定义协程函数（async def 开头）
async def greet():
    print("Hi!")
    # 2. await 模拟IO等待（不会阻塞线程）
    await asyncio.sleep(1)  # 相当于"等1秒，但期间可以做别的事"
    print("Nice to meet you!")

# 3. 运行协程（Python 3.7+推荐用asyncio.run）
asyncio.run(greet())

# 预期输出：
# Hi!
# （等待1秒，无卡顿）
# Nice to meet you!
```


### 📈 Level 2: 核心特性（深入理解）

#### 特性1: 协程的嵌套与返回值
协程可以像普通函数一样嵌套调用，通过`await`获取返回值：

```python
import asyncio

# 模拟获取用户信息的协程
async def get_user(id):
    print(f"正在查询用户 {id}")
    await asyncio.sleep(0.5)  # 模拟数据库查询耗时
    return {"id": id, "name": f"User_{id}"}  # 返回用户数据

# 顶层协程（负责统筹任务）
async def main():
    # 嵌套调用：await 另一个协程并接收结果
    user1 = await get_user(1)
    user2 = await get_user(2)
    print(f"查询结果：{user1} | {user2}")

asyncio.run(main())

# 预期输出：
# 正在查询用户 1
# （等待0.5秒）
# 正在查询用户 2
# （等待0.5秒）
# 查询结果：{'id': 1, 'name': 'User_1'} | {'id': 2, 'name': 'User_2'}
```

#### 特性2: 并发执行多个协程（关键！）
用`asyncio.gather()`可以**同时运行多个协程**，总耗时等于最慢的任务（而非累加）：

```python
import asyncio

async def fetch(url):
    print(f"请求 {url}")
    await asyncio.sleep(url.count('/') * 0.3)  # 不同URL耗时不同
    return f"{url} 响应"

async def main():
    # 并发执行3个协程（总耗时≈0.9秒，而非1.8秒）
    results = await asyncio.gather(
        fetch("https://example.com"),   # 耗时0.6秒（2个/）
        fetch("https://python.org"),   # 耗时0.6秒
        fetch("https://github.com")    # 耗时0.6秒
    )
    print("所有请求完成：", results)

asyncio.run(main())

# 预期输出：
# 请求 https://example.com
# 请求 https://python.org
# 请求 https://github.com
# （等待0.6秒）
# 所有请求完成： ['https://example.com 响应', 'https://python.org 响应', 'https://github.com 响应']
```

#### 特性3: 协程的"协作式"让出
`await`会主动让出CPU——当一个协程在`await`时，事件循环会切换到其他就绪的协程：

```python
import asyncio

async def task1():
    for i in range(3):
        print(f"任务1：第{i+1}次执行")
        await asyncio.sleep(0.2)  # 每执行一次就让出CPU

async def task2():
    for i in range(3):
        print(f"任务2：第{i+1}次执行")
        await asyncio.sleep(0.1)  # 更频繁地让出CPU

async def main():
    # 并发运行两个任务
    await asyncio.gather(task1(), task2())

asyncio.run(main())

# 预期输出（顺序体现"协作"）：
# 任务1：第1次执行
# 任务2：第1次执行
# 任务2：第2次执行
# 任务1：第2次执行
# 任务2：第3次执行
# 任务1：第3次执行
```


### 🔍 Level 3: 对比学习（避免陷阱）
**常见错误1: 忘记`await`，协程没执行**  
直接调用协程函数只会返回一个"协程对象"，不会执行函数体：

```python
import asyncio

async def do_something():
    print("任务执行了！")

# ❌ 错误：直接调用协程，无输出
do_something()  # 返回<coroutine object do_something at 0x104a9e8c0>

# ✅ 正确：用await（必须在async函数内）
async def main():
    await do_something()  # 等待协程执行

asyncio.run(main())  # 输出：任务执行了！
```

**常见错误2: 在非`async`函数中用`await`**  
`await`只能在`async def`定义的函数内使用：

```python
# ❌ 错误：非async函数中用await
def bad_func():
    await asyncio.sleep(1)  # 报错：SyntaxError: 'await' outside async function

# ✅ 正确：必须用async def
async def good_func():
    await asyncio.sleep(1)
```


### 🚀 Level 4: 实战应用（真实场景）
**场景**：批量爬取多个网页的标题（模拟网络请求），用协程并发提升效率：

```python
import asyncio

# 模拟爬取网页标题的协程（真实场景可用aiohttp库）
async def scrape_title(url):
    print(f"开始爬取：{url}")
    # 模拟网络耗时（根据URL长度模拟不同延迟）
    await asyncio.sleep(len(url) * 0.1)
    # 模拟解析标题（真实场景用BeautifulSoup）
    title = f"《{url.split('//')[-1]} 的标题》"
    print(f"完成爬取：{url} → {title}")
    return (url, title)

async def main():
    # 要爬取的10个网页（模拟）
    urls = [
        "https://example.com", "https://python.org", "https://github.com",
        "https://docs.python.org", "https://pypi.org", "https://reddit.com",
        "https://stackoverflow.com", "https://medium.com", "https://dev.to",
        "https://vuejs.org"
    ]
    
    # 并发爬取所有URL（总耗时≈最长的单个任务耗时）
    results = await asyncio.gather(*[scrape_title(url) for url in urls])
    
    # 输出结果
    print("\n📊 爬取结果：")
    for url, title in results:
        print(f"{url:25} → {title}")

asyncio.run(main())

# 预期输出（总耗时≈1.2秒，而非串行的5秒+）：
# 开始爬取：https://example.com
# 开始爬取：https://python.org
# 开始爬取：https://github.com
# ...（略）
# 完成爬取：https://example.com → 《example.com 的标题》
# 完成爬取：https://python.org → 《python.org 的标题》
# ...（略）
# 📊 爬取结果：
# https://example.com         → 《example.com 的标题》
# https://python.org          → 《python.org 的标题》
# ...（略）
```


### 💡 记忆要点
- **定义**：协程函数用`async def`，内部可加`await`；
- **调用**：`await`必须在`async`函数内，用于等待协程完成；
- **并发**：用`asyncio.gather()`同时运行多个协程，提升IO任务效率；
- **陷阱**：不要忘记`await`，否则协程不会执行；非`async`函数不能用`await`。


**总结**：协程是Python处理IO密集型任务的"神器"——用单线程实现多任务并发，代码简洁且高效。下一节我们会学习**事件循环与任务**，深入理解协程的运行机制！