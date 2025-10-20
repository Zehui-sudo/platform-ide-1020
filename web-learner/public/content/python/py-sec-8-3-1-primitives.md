## asyncio.Queue/Lock/Semaphore

### 🎯 核心概念
asyncio的`Queue`、`Lock`、`Semaphore`是**异步协程间的同步与通信工具**，解决异步环境下的三大问题：  
- `Lock`：互斥访问共享资源（避免并发修改冲突）；  
- `Queue`：协程间安全传递任务（生产者-消费者模型）；  
- `Semaphore`：限制并发协程数（如控制API请求频率）。  
它们替代了线程同步原语（如`threading.Lock`），适配协程的`await`语法，是异步编程的"协作基石"。


### 💡 使用方式
1. **创建实例**：通过`asyncio`模块直接实例化（如`lock = asyncio.Lock()`）；  
2. **核心操作**：调用`await`able方法（如`await lock.acquire()`、`await queue.get()`）；  
3. **上下文管理**：优先用`async with`简化资源释放（如`async with lock:`自动管理锁的获取/释放）。


### 📚 Level 1: 基础认知（30秒理解）
用`Lock`保护共享资源，避免并发修改错误：
```python
import asyncio

async def modify_shared(lock, shared_data):
    # 用async with自动管理锁，避免忘记释放
    async with lock:
        shared_data["count"] += 1
        print(f"当前计数: {shared_data['count']}")

async def main():
    lock = asyncio.Lock()
    shared_data = {"count": 0}
    # 同时启动2个协程修改共享数据
    await asyncio.gather(
        modify_shared(lock, shared_data),
        modify_shared(lock, shared_data)
    )

asyncio.run(main())
```
**预期输出**（顺序可能不同，但计数一定是2）：
```
当前计数: 1
当前计数: 2
```


### 📈 Level 2: 核心特性（深入理解）
#### 特性1: asyncio.Queue - 生产者-消费者模型
用`Queue`实现任务的有序传递（比如爬虫的"任务队列"）：
```python
import asyncio

async def producer(queue):
    """生产者：生成5个任务"""
    for i in range(5):
        await asyncio.sleep(0.1)  # 模拟生产耗时
        await queue.put(f"任务{i}")  # 阻塞直到队列有空间
        print(f"生产任务: 任务{i}")

async def consumer(queue, name):
    """消费者：处理队列中的任务"""
    while True:
        task = await queue.get()  # 阻塞直到有任务
        print(f"消费者{name}处理: {task}")
        await asyncio.sleep(0.3)  # 模拟处理耗时
        queue.task_done()  # 标记任务完成

async def main():
    queue = asyncio.Queue(maxsize=2)  # 队列最大容量2（满时生产者阻塞）
    # 启动1个生产者、2个消费者
    producer_task = asyncio.create_task(producer(queue))
    consumers = [asyncio.create_task(consumer(queue, f"C{i}")) for i in range(2)]
    
    await producer_task  # 等待生产者完成
    await queue.join()   # 等待队列中所有任务处理完毕
    for c in consumers:  # 取消消费者（无限循环）
        c.cancel()

asyncio.run(main())
```
**关键说明**：  
- `maxsize`限制队列长度，避免内存溢出；  
- `queue.task_done()`与`queue.join()`配合，确保所有任务执行完毕。


#### 特性2: asyncio.Semaphore - 限制并发数
用`Semaphore`控制同时运行的协程数（比如限制API请求频率）：
```python
import asyncio

async def fetch_url(url, semaphore):
    # 用Semaphore限制同时只有2个协程能进入该块
    async with semaphore:
        print(f"开始下载: {url}")
        await asyncio.sleep(1)  # 模拟网络请求耗时
        print(f"完成下载: {url}")

async def main():
    semaphore = asyncio.Semaphore(2)  # 最多2个协程同时运行
    urls = [f"https://example.com/page{i}" for i in range(5)]
    # 并发执行5个下载任务，但同时只有2个在运行
    await asyncio.gather(*[fetch_url(url, semaphore) for url in urls])

asyncio.run(main())
```
**预期输出**（每次最多2个下载任务同时运行）：
```
开始下载: https://example.com/page0
开始下载: https://example.com/page1
完成下载: https://example.com/page0
完成下载: https://example.com/page1
开始下载: https://example.com/page2
开始下载: https://example.com/page3
...
```


### 🔍 Level 3: 对比学习（避免陷阱）
#### 陷阱1：忘记释放锁导致死锁
**错误用法**（手动`acquire`但未`release`）：
```python
async def bad_lock():
    lock = asyncio.Lock()
    await lock.acquire()
    raise Exception("出现异常！")  # 锁未释放，后续协程无法获取
    await lock.release()  # 永远不会执行
```
**正确用法**（用`async with`自动释放）：
```python
async def good_lock():
    lock = asyncio.Lock()
    async with lock:
        raise Exception("出现异常！")  # 自动释放锁，不会死锁
```


#### 陷阱2：Queue非阻塞方法未处理空队列
**错误用法**（`get_nowait()`未捕获`QueueEmpty`异常）：
```python
async def bad_queue():
    queue = asyncio.Queue()
    try:
        task = queue.get_nowait()  # 队列空时直接抛出异常
    except:
        pass  # 未正确处理，可能导致任务丢失
```
**正确用法**（要么阻塞等待，要么捕获异常）：
```python
async def good_queue():
    queue = asyncio.Queue()
    try:
        task = queue.get_nowait()
    except asyncio.QueueEmpty:
        print("队列空，等待1秒...")
        await asyncio.sleep(1)  # 等待生产者补充任务
```


### 🚀 Level 4: 实战应用（真实场景）
**场景**：异步爬虫的"任务队列+并发限制"  
需求：爬取5个网页，用`Queue`存URL，`Semaphore`限制同时3个请求，避免被反爬。
```python
import asyncio
import aiohttp  # 需要安装：pip install aiohttp

async def fetch(url, semaphore, session):
    """下载网页内容（带并发限制）"""
    async with semaphore:
        try:
            async with session.get(url) as response:
                content = await response.text()
                print(f"成功爬取: {url}（内容长度: {len(content)}）")
                return len(content)
        except Exception as e:
            print(f"爬取失败: {url}，错误: {e}")
            return 0

async def consumer(queue, semaphore, session):
    """消费者：从队列取URL并爬取"""
    while True:
        url = await queue.get()  # 阻塞等待任务
        await fetch(url, semaphore, session)
        queue.task_done()  # 标记任务完成

async def producer(queue, urls):
    """生产者：把URL加入队列"""
    for url in urls:
        await queue.put(url)
    print("所有URL已加入队列")

async def main():
    urls = [
        "https://www.python.org",
        "https://www.aiohttp.org",
        "https://www.github.com",
        "https://www.pypi.org",
        "https://www.docker.com"
    ]
    queue = asyncio.Queue(maxsize=5)
    semaphore = asyncio.Semaphore(3)  # 限制同时3个请求

    # 创建aiohttp会话（复用连接池，提升性能）
    async with aiohttp.ClientSession() as session:
        # 启动1个生产者、2个消费者
        producer_task = asyncio.create_task(producer(queue, urls))
        consumers = [asyncio.create_task(consumer(queue, semaphore, session)) for _ in range(2)]
        
        await producer_task  # 等待生产者完成
        await queue.join()   # 等待所有任务爬取完毕
        for c in consumers:  # 取消消费者
            c.cancel()

    print("所有爬取任务完成！")

asyncio.run(main())
```
**运行结果**：  
- 生产者把5个URL加入队列；  
- 2个消费者同时从队列取任务，每次最多3个请求并发；  
- 所有任务完成后自动退出。


### 💡 记忆要点
- **Lock**：互斥访问，同一时间只有1个协程能进入临界区；  
- **Queue**：任务传递，实现生产者-消费者模型，支持阻塞/非阻塞操作；  
- **Semaphore**：并发限制，控制同时运行的协程数（如API请求频率）；  
- **必记原则**：优先用`async with`管理资源，避免手动释放导致的死锁；  
- **核心区别**：Lock是"1个名额"，Semaphore是"N个名额"，Queue是"任务管道"。