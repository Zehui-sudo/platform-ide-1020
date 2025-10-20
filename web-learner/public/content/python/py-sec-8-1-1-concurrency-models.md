## 线程、进程、协程对比

### 🎯 核心概念
解决**“如何高效利用计算机资源处理多任务”**的问题——当需要同时执行多个任务时，选择线程、进程还是协程，直接决定了程序的性能、复杂度和稳定性。


### 💡 使用方式
- **线程**：通过`threading`模块创建，共享进程内存空间，适合IO密集型任务（如网络请求、文件读写）。
- **进程**：通过`multiprocessing`模块创建，拥有独立内存空间，适合CPU密集型任务（如数据计算、图像处理）。
- **协程**：通过`asyncio`模块创建（Python 3.7+），单线程内协作式调度，适合高并发IO任务（如百万级网络连接）。


### 📚 Level 1: 基础认知（30秒理解）
用**同一个任务（打印数字）**展示三种模型的最简写法：

```python
# 1. 线程示例（threading）
import threading

def thread_worker(n):
    print(f"线程 {n} 运行")

t = threading.Thread(target=thread_worker, args=(1,))
t.start()  # 启动线程
t.join()   # 等待线程结束


# 2. 进程示例（multiprocessing）
import multiprocessing

def process_worker(n):
    print(f"进程 {n} 运行")

p = multiprocessing.Process(target=process_worker, args=(1,))
p.start()  # 启动进程
p.join()   # 等待进程结束


# 3. 协程示例（asyncio）
import asyncio

async def coro_worker(n):
    print(f"协程 {n} 运行")

asyncio.run(coro_worker(1))  # 运行协程主函数
```

**预期输出**（顺序可能因调度略有不同）：
```
线程 1 运行
进程 1 运行
协程 1 运行
```


### 📈 Level 2: 核心特性（深入理解）
#### 特性1: 线程——共享内存与锁（需同步）
线程共享进程的内存空间，**修改共享变量时必须加锁**，否则会出现“数据竞争”。

```python
import threading

counter = 0
lock = threading.Lock()  # 锁：保证同一时间只有一个线程修改变量

def increment():
    global counter
    for _ in range(100000):
        with lock:  # 加锁保护共享变量
            counter += 1

# 创建两个线程同时修改计数器
t1 = threading.Thread(target=increment)
t2 = threading.Thread(target=increment)
t1.start()
t2.start()
t1.join()
t2.join()

print(f"最终计数器值: {counter}")  # 正确结果：200000（无锁会小于200000）
```


#### 特性2: 进程——独立内存与通信（需队列）
进程拥有独立内存，**无法直接共享变量**，需通过`Queue`或`Pipe`通信。

```python
import multiprocessing

def producer(q):
    for i in range(3):
        q.put(f"数据 {i}")  # 向队列放入数据
        print(f"生产者发送: 数据 {i}")

def consumer(q):
    while True:
        data = q.get()  # 从队列取出数据（阻塞直到有数据）
        if data is None:  # 终止信号
            break
        print(f"消费者接收: {data}")

# 创建队列用于进程间通信
q = multiprocessing.Queue()
p1 = multiprocessing.Process(target=producer, args=(q,))
p2 = multiprocessing.Process(target=consumer, args=(q,))

p1.start()
p2.start()
p1.join()
q.put(None)  # 发送终止信号
p2.join()
```

**输出**：
```
生产者发送: 数据 0
消费者接收: 数据 0
生产者发送: 数据 1
消费者接收: 数据 1
生产者发送: 数据 2
消费者接收: 数据 2
```


#### 特性3: 协程——协作式调度（需await）
协程是**用户态调度**（无需内核干预），通过`await`主动让出控制权，避免线程切换的开销。

```python
import asyncio

async def task1():
    print("任务1: 开始")
    await asyncio.sleep(1)  # 让出控制权，等待1秒
    print("任务1: 结束")

async def task2():
    print("任务2: 开始")
    await asyncio.sleep(0.5)  # 让出控制权，等待0.5秒
    print("任务2: 结束")

async def main():
    # 同时运行两个协程（顺序执行但会交替让出）
    await asyncio.gather(task1(), task2())

asyncio.run(main())
```

**输出**（注意交替顺序）：
```
任务1: 开始
任务2: 开始
任务2: 结束  # 任务2等待时间更短，先完成
任务1: 结束
```


### 🔍 Level 3: 对比学习（避免陷阱）
#### 陷阱1: 线程忘记加锁→数据竞争
**错误用法**（无锁导致计数器错误）：
```python
import threading

counter = 0

def bad_increment():
    global counter
    for _ in range(100000):
        counter += 1  # 无锁，两个线程同时修改会覆盖值

t1 = threading.Thread(target=bad_increment)
t2 = threading.Thread(target=bad_increment)
t1.start()
t2.start()
t1.join()
t2.join()
print(f"错误结果: {counter}")  # 结果可能是150000（而非200000）
```

**正确用法**（加锁保证原子操作）：
```python
lock = threading.Lock()

def good_increment():
    global counter
    for _ in range(100000):
        with lock:
            counter += 1  # 锁保护，结果正确
```


#### 陷阱2: 进程试图共享变量→无效
**错误用法**（进程无法共享列表）：
```python
import multiprocessing

shared_list = []  # 进程1修改的列表，进程2看不到

def add_item():
    shared_list.append("数据")  # 仅修改当前进程的列表

p1 = multiprocessing.Process(target=add_item)
p1.start()
p1.join()
print(f"错误结果: {shared_list}")  # 空列表（进程1的修改不共享）
```

**正确用法**（用`Queue`通信）：
```python
q = multiprocessing.Queue()

def add_item(q):
    q.put("数据")  # 放入队列

p1 = multiprocessing.Process(target=add_item, args=(q,))
p1.start()
p1.join()
print(f"正确结果: {q.get()}")  # 数据（从队列取出）
```


#### 陷阱3: 协程忘记await→任务未执行
**错误用法**（忘记await，`asyncio.sleep`不生效）：
```python
async def bad_task():
    print("开始")
    asyncio.sleep(1)  # 忘记await，直接跳过等待
    print("结束")

asyncio.run(bad_task())  # 输出“开始”→“结束”（无等待）
```

**正确用法**（加await让出控制权）：
```python
async def good_task():
    print("开始")
    await asyncio.sleep(1)  # 等待1秒
    print("结束")  # 1秒后输出
```


### 🚀 Level 4: 实战应用（真实场景）
**场景**：爬取5个网页，对比三种模型的效率（IO密集型任务，协程优势明显）。

需安装依赖：`pip install requests aiohttp`

```python
import time
import requests
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import asyncio
import aiohttp

# 待爬取的URL（重复5次模拟多任务）
urls = ["https://httpbin.org/get" for _ in range(5)]


# 1. 线程池方式（适合IO密集）
def fetch_url(url):
    response = requests.get(url)
    return response.status_code  # 返回状态码（200=成功）

start = time.time()
with ThreadPoolExecutor(max_workers=5) as executor:
    results = list(executor.map(fetch_url, urls))
print(f"线程池耗时: {time.time() - start:.2f}s, 结果: {results}")


# 2. 进程池方式（适合CPU密集，IO密集下无优势）
start = time.time()
with ProcessPoolExecutor(max_workers=5) as executor:
    results = list(executor.map(fetch_url, urls))
print(f"进程池耗时: {time.time() - start:.2f}s, 结果: {results}")


# 3. 协程方式（高并发IO最优）
async def fetch_url_async(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return response.status  # 返回状态码

async def main():
    tasks = [fetch_url_async(url) for url in urls]
    return await asyncio.gather(*tasks)  # 并发执行所有任务

start = time.time()
results = asyncio.run(main())
print(f"协程耗时: {time.time() - start:.2f}s, 结果: {results}")
```

**运行结果**（示例）：
```
线程池耗时: 1.23s, 结果: [200, 200, 200, 200, 200]
进程池耗时: 2.15s, 结果: [200, 200, 200, 200, 200]
协程耗时: 0.35s, 结果: [200, 200, 200, 200, 200]
```


### 💡 记忆要点
- **内存共享**：线程>共享（需锁）；进程>独立（需通信）；协程>共享（单线程无需锁）。
- **调度方式**：线程/进程>内核抢占式；协程>用户协作式（await让出）。
- **资源消耗**：进程>最高（独立内存）；线程>次之（共享内存）；协程>最低（单线程栈帧）。
- **适用场景**：
  - CPU密集（如计算）→ 进程（绕开GIL）；
  - IO密集（如网络/文件）→ 线程（简单）或协程（高效）；
  - 高并发（如百万连接）→ 协程（单线程处理数千任务）。