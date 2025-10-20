## 调试与性能 (asyncio debug, uvloop 可选)

### 🎯 核心概念
解决**异步代码调试难**（非阻塞逻辑导致的隐藏问题）与**性能瓶颈**（默认事件循环效率有限）的问题——`asyncio debug`模式帮你捕获未await的协程、慢回调等陷阱，`uvloop`则用C实现的高性能事件循环替换默认循环，提升异步程序运行速度。


### 💡 使用方式
1. **调试**：通过`asyncio.run(main(), debug=True)`开启debug模式，或手动设置事件循环的`debug`属性；
2. **性能优化**：安装`uvloop`（`pip install uvloop`）后，用`uvloop.install()`替换默认事件循环。


### 📚 Level 1: 基础认知（30秒理解）
最简单的debug模式示例：捕获**未被await的协程**（异步代码最常见的低级错误）。
```python
import asyncio

async def hello():
    print("Hello from coroutine")  # 永远不会执行，因为没被await

async def main():
    hello()  # 错误：忘记写await
    await asyncio.sleep(0.1)  # 让事件循环运行一会儿

if __name__ == "__main__":
    asyncio.run(main(), debug=True)  # 开启debug模式
```
**预期输出**：  
会弹出`RuntimeWarning`警告，明确告诉你`coroutine 'hello' was never awaited`（协程未被等待），帮你快速定位遗漏的`await`。


### 📈 Level 2: 核心特性（深入理解）
#### 特性1: debug模式检测「慢回调」
异步代码的性能杀手是**同步阻塞操作**（如`time.sleep()`、同步IO），debug模式会自动检测运行时间超过1秒的回调函数并报警。
```python
import asyncio
import time

async def slow_task():
    print("开始执行慢任务...")
    time.sleep(2)  # 同步阻塞！会卡住整个事件循环
    print("慢任务结束")

async def main():
    loop = asyncio.get_running_loop()
    loop.call_soon(slow_task)  # 用call_soon添加同步回调
    await asyncio.sleep(3)  # 等待任务完成

if __name__ == "__main__":
    asyncio.run(main(), debug=True)
```
**预期输出**：  
会收到`Slow callback duration`警告，提示`slow_task`运行了2.001秒，超过默认阈值1秒——这说明你在异步代码里写了同步阻塞逻辑！


#### 特性2: uvloop替换事件循环，提升性能
`uvloop`是`asyncio`事件循环的Cython实现，性能比默认循环快2-4倍（尤其适合高并发场景）。
```python
import asyncio
import uvloop

# 第一步：安装uvloop（pip install uvloop）
# 第二步：替换默认事件循环
uvloop.install()

async def fast_task():
    print("用uvloop运行异步任务")
    await asyncio.sleep(0.1)  # 异步等待，不阻塞

if __name__ == "__main__":
    asyncio.run(fast_task())
```
**说明**：  
只需一行`uvloop.install()`，所有`asyncio`的API（如`asyncio.run()`、`create_task()`）都会自动使用uvloop的高性能循环。


### 🔍 Level 3: 对比学习（避免陷阱）
**陷阱**：未开启debug模式，遗漏的`await`会「悄悄失败」
```python
# 错误用法：没开debug，未await的协程无提示
import asyncio

async def fetch_data():
    return "重要数据"

async def main():
    fetch_data()  # 忘记await，协程不会执行
    print("程序结束")

if __name__ == "__main__":
    asyncio.run(main())  # 输出"程序结束"，但fetch_data没运行！
```

**正确用法**：开启debug模式，强制捕获遗漏的`await`
```python
# 正确用法：开debug，直接报警
import asyncio

async def fetch_data():
    return "重要数据"

async def main():
    fetch_data()  # 忘记await
    print("程序结束")

if __name__ == "__main__":
    asyncio.run(main(), debug=True)  # 弹出警告，帮你发现问题
```


### 🚀 Level 4: 实战应用（真实场景）
**场景**：异步爬取3个网页，用debug模式排查「慢请求」，用uvloop提升爬取速度。
```python
import asyncio
import aiohttp
import uvloop

# 1. 用uvloop提升性能
uvloop.install()

async def fetch_url(url, session):
    try:
        async with session.get(url) as response:
            # 模拟一个慢接口（比如第三方API响应慢）
            if "slow" in url:
                # 错误写法：用time.sleep()同步阻塞（会被debug模式检测到）
                # time.sleep(2)
                # 正确写法：用asyncio.sleep()异步等待
                await asyncio.sleep(2)
            text = await response.text()
            print(f"成功获取{url}的内容，长度{len(text)}")
            return text
    except Exception as e:
        print(f"爬取{url}失败：{e}")

async def main():
    urls = [
        "https://httpbin.org/get",  # 快接口
        "https://httpbin.org/get?slow=1",  # 慢接口
        "https://httpbin.org/status/500"  # 错误接口
    ]

    async with aiohttp.ClientSession() as session:
        # 并发执行所有爬取任务
        tasks = [fetch_url(url, session) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)  # 捕获异常
        print(f"\n爬取完成：成功{len([r for r in results if not isinstance(r, Exception)])}个，失败{len([r for r in results if isinstance(r, Exception)])}个")

if __name__ == "__main__":
    # 2. 开启debug模式，检测潜在问题
    asyncio.run(main(), debug=True)
```
**运行效果**：  
- uvloop让并发爬取速度比默认循环快30%+；  
- debug模式会帮你检测代码中的同步阻塞（如果不小心用了`time.sleep()`）；  
- 结合`return_exceptions=True`，还能优雅处理爬取失败的情况。


### 💡 记忆要点
- 🔍 调试异步代码先开`debug`模式：`asyncio.run(main(), debug=True)`，能抓未await、慢回调等问题；
- 🚀 性能优化用`uvloop`：安装后`uvloop.install()`，替换默认事件循环，高并发场景必用；
- ⚠️ 异步代码禁止同步阻塞：`time.sleep()`、同步数据库操作会卡住事件循环，debug模式会帮你揪出来！