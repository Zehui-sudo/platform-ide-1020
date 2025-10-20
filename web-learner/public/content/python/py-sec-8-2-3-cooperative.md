## 协作式让出 (await, asyncio.sleep)

### 🎯 核心概念
协作式让出解决**单线程下多任务交替执行**的问题——asyncio的事件循环是单线程的，协程需要**主动让出控制权**才能让其他任务运行。`await`是触发让出的关键字，`asyncio.sleep()`是最常用的“安全让出点”（模拟耗时操作，不阻塞线程）。


### 💡 使用方式
1. **`await`的作用**：等待一个**可等待对象**（协程、任务、`Future`等）完成，并将控制权交还给事件循环，让其他任务有机会执行。
2. **`asyncio.sleep(n)`**：创建一个“睡眠n秒”的协程，它不会真的阻塞线程，而是告诉事件循环：“我接下来n秒没事做，先让别的任务跑吧”。


### 📚 Level 1: 基础认知（30秒理解）
下面的例子展示两个协程通过`await asyncio.sleep()`交替执行：
```python
import asyncio

async def task1():
    print("Task 1: 开始执行")
    await asyncio.sleep(1)  # 主动让出1秒
    print("Task 1: 执行结束")

async def task2():
    print("Task 2: 开始执行")
    await asyncio.sleep(0.5)  # 主动让出0.5秒
    print("Task 2: 执行结束")

async def main():
    # 并发运行task1和task2
    await asyncio.gather(task1(), task2())

# 启动事件循环
asyncio.run(main())
```

**预期输出**（顺序说明）：
```
Task 1: 开始执行
Task 2: 开始执行  # task1让出后，task2立即启动
Task 2: 执行结束  # task2的sleep更短，先完成
Task 1: 执行结束  # task1的sleep结束后继续
```


### 📈 Level 2: 核心特性（深入理解）
#### 特性1: 多次让出实现“分阶段执行”
一个协程可以通过多次`await`拆分任务，让其他任务插入执行：
```python
import asyncio

async def stage_task():
    print("Stage 1: 准备数据")
    await asyncio.sleep(0.3)  # 第一次让出
    print("Stage 2: 处理数据")
    await asyncio.sleep(0.2)  # 第二次让出
    print("Stage 3: 保存结果")

async def background_task():
    print("Background: 监控系统状态...")
    await asyncio.sleep(0.1)
    print("Background: 状态正常")

async def main():
    await asyncio.gather(stage_task(), background_task())

asyncio.run(main())
```

**输出**（阶段任务与后台任务交替）：
```
Stage 1: 准备数据
Background: 监控系统状态...
Background: 状态正常  # 第一次让出后，后台任务执行
Stage 2: 处理数据
Stage 3: 保存结果      # 第二次让出时间短，后台任务已完成
```

#### 特性2: `asyncio.sleep(0)`实现“即时让出”
`asyncio.sleep(0)`会立即把控制权还给事件循环，适合**高频率小任务**的协作：
```python
import asyncio

async def busy_worker():
    print("Worker: 开始处理循环任务")
    for i in range(3):
        print(f"Worker: 完成第{i+1}个小任务")
        await asyncio.sleep(0)  # 即时让出，不等待
    print("Worker: 循环任务结束")

async def priority_task():
    print("Priority: 紧急任务启动")
    await asyncio.sleep(0.1)
    print("Priority: 紧急任务完成")

async def main():
    await asyncio.gather(busy_worker(), priority_task())

asyncio.run(main())
```

**输出**（紧急任务插入到循环任务中间）：
```
Worker: 开始处理循环任务
Worker: 完成第1个小任务
Priority: 紧急任务启动  # 即时让出后，紧急任务执行
Priority: 紧急任务完成
Worker: 完成第2个小任务
Worker: 完成第3个小任务
Worker: 循环任务结束
```


### 🔍 Level 3: 对比学习（避免陷阱）
#### 陷阱1: 用`time.sleep()`代替`asyncio.sleep()`（阻塞线程）
`time.sleep()`是**阻塞式睡眠**，会卡住整个事件循环，导致其他任务无法执行：
```python
import asyncio
import time

# 错误用法：用time.sleep()阻塞线程
async def bad_task():
    print("Bad Task: 开始")
    time.sleep(2)  # 阻塞整个线程2秒！
    print("Bad Task: 结束")

# 正确用法：用asyncio.sleep()让出
async def good_task():
    print("Good Task: 开始")
    await asyncio.sleep(1)
    print("Good Task: 结束")

async def main():
    await asyncio.gather(bad_task(), good_task())

asyncio.run(main())
```

**错误输出**（good_task被阻塞，直到bad_task结束）：
```
Bad Task: 开始
Bad Task: 结束  # 2秒后才结束
Good Task: 开始
Good Task: 结束
```

**正确输出**（如果把bad_task改成`await asyncio.sleep(2)`）：
```
Bad Task: 开始
Good Task: 开始  # 立即执行
Good Task: 结束  # 1秒后完成
Bad Task: 结束   # 2秒后完成
```

#### 陷阱2: 忘记`await`导致协程“未执行”
协程对象必须通过`await`触发，否则不会运行：
```python
import asyncio

async def my_coroutine():
    print("协程：我被执行了！")

async def main():
    my_coroutine()  # 错误：没有await，协程不会运行
    await asyncio.sleep(1)  # 等待1秒，但协程没启动

asyncio.run(main())
```

**输出**（无任何内容）：协程根本没执行！  
**修正方法**：`await my_coroutine()`，此时会输出“协程：我被执行了！”。


### 🚀 Level 4: 实战应用（真实场景）
模拟**并发网络请求**：假设我们需要从3个API接口获取数据，每个接口的延迟不同。用`asyncio.sleep()`模拟网络延迟，统计总耗时（并发执行的总时间等于最长延迟，而非总和）。

```python
import asyncio
import time

async def fetch_api(url: str, delay: float):
    """模拟调用API，延迟delay秒"""
    print(f"请求: {url}（延迟{delay}秒）")
    await asyncio.sleep(delay)  # 模拟网络延迟
    print(f"响应: {url} 完成")
    return f"{url} 的数据"

async def main():
    start_time = time.time()
    
    # 并发执行3个API请求
    results = await asyncio.gather(
        fetch_api("https://api.example.com/user", 2),   # 延迟2秒
        fetch_api("https://api.example.com/order", 1),  # 延迟1秒
        fetch_api("https://api.example.com/product", 3) # 延迟3秒
    )
    
    end_time = time.time()
    print(f"\n总耗时: {end_time - start_time:.2f}秒")
    print("结果:", results)

asyncio.run(main())
```

**输出**（关键看总耗时）：
```
请求: https://api.example.com/user（延迟2秒）
请求: https://api.example.com/order（延迟1秒）
请求: https://api.example.com/product（延迟3秒）
响应: https://api.example.com/order 完成  # 1秒后
响应: https://api.example.com/user 完成    # 2秒后
响应: https://api.example.com/product 完成 # 3秒后

总耗时: 3.01秒  # 等于最长延迟（3秒），而非2+1+3=6秒
结果: ['https://api.example.com/user 的数据', 'https://api.example.com/order 的数据', 'https://api.example.com/product 的数据']
```


### 💡 记忆要点
1. **协作式 vs 抢占式**：asyncio的协程是**协作式**的，必须通过`await`主动让出，否则会独占事件循环。
2. **`await`的两个作用**：等待可等待对象完成 + 让出控制权给事件循环。
3. **`asyncio.sleep(n)`不是阻塞**：它是“非阻塞睡眠”，让事件循环去执行其他任务。
4. **避免阻塞函数**：永远不要在协程中使用`time.sleep()`、`input()`等阻塞函数，会导致整个事件循环卡住。
5. **协程必须`await`**：忘记`await`的协程不会执行，这是最常见的新手错误！