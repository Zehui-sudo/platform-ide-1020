## 背压、限速与重试


### 🎯 核心概念  
解决异步系统中**流量过载（下游扛不住）、频率超限（触发API限制）、临时错误（网络波动）**的稳定性问题，通过“限流-削峰-容错”三层机制保障系统平衡。


### 💡 使用方式  
- **背压**：用`asyncio.Queue`（固定容量）或`Semaphore`限制任务积压，让生产者“慢下来”；  
- **限速**：用时间窗口（固定/滑动）控制执行频率（如每秒5次）；  
- **重试**：用装饰器（如`tenacity`）处理临时失败，带**指数退避**避免雪崩。


### 📚 Level 1: 基础认知（30秒理解）  
用`asyncio.Queue`实现最简背压——生产者因队列满而等待，保障下游消费者不被压垮。  

```python
import asyncio

async def producer(queue: asyncio.Queue):
    for i in range(10):
        await queue.put(f"任务{i}")  # 队列满时会阻塞等待
        print(f"生产者：已发任务{i}，队列当前大小{queue.qsize()}")
        await asyncio.sleep(0.1)  # 模拟生产者速度

async def consumer(queue: asyncio.Queue):
    while True:
        task = await queue.get()
        print(f"消费者：处理{task}")
        await asyncio.sleep(1)  # 模拟消费者慢速度
        queue.task_done()

async def main():
    queue = asyncio.Queue(maxsize=3)  # 队列容量3，满了就阻塞生产者
    await asyncio.gather(producer(queue), consumer(queue))

asyncio.run(main())
```  
**预期输出**：  
生产者发3个任务后阻塞，等消费者处理1个才继续发，队列大小始终≤3。


### 📈 Level 2: 核心特性（深入理解）  

#### 特性1: 队列式背压（容量限制）  
通过`Queue(maxsize)`强制生产者等待，避免任务无限积压。  

```python
import asyncio

async def producer(queue: asyncio.Queue):
    for i in range(10):
        await queue.put(f"任务{i}")  # 队列满时阻塞
        print(f"生产者：队列大小{queue.qsize()}")
        await asyncio.sleep(0.2)  # 生产者速度：每秒5个

async def consumer(queue: asyncio.Queue):
    while True:
        task = await queue.get()
        print(f"消费者：处理{task}")
        await asyncio.sleep(1)  # 消费者速度：每秒1个
        queue.task_done()

async def main():
    queue = asyncio.Queue(maxsize=5)  # 最多存5个任务
    await asyncio.gather(producer(queue), consumer(queue))

asyncio.run(main())
```  
**效果**：生产者发5个任务后阻塞，等消费者处理1个才继续，队列始终不超过5。


#### 特性2: 固定窗口限速（控制频率）  
用`Semaphore`+`sleep`实现“每秒N次”的速率限制（如每秒2次）。  

```python
import asyncio

async def limited_task(semaphore: asyncio.Semaphore, task_id: int):
    async with semaphore:  # 最多同时2个任务
        print(f"执行任务{task_id}：{asyncio.get_running_loop().time():.1f}s")
        await asyncio.sleep(1)  # 模拟任务耗时

async def main():
    semaphore = asyncio.Semaphore(2)  # 限速：每秒2次
    tasks = [limited_task(semaphore, i) for i in range(5)]
    await asyncio.gather(*tasks)

asyncio.run(main())
```  
**输出**（时间戳验证频率）：  
```
执行任务0：0.0s
执行任务1：0.0s
执行任务2：1.0s  # 等1秒后才能执行第3个
执行任务3：1.0s
执行任务4：2.0s
```


#### 特性3: 指数退避重试（容错且不雪崩）  
用`tenacity`库实现“失败后等待时间指数增长”（如1s→2s→4s），避免频繁重试压垮下游。  

先安装依赖：`pip install tenacity`  

```python
import asyncio
from tenacity import retry, stop_after_attempt, wait_exponential

# 模拟不稳定的API请求
async def unstable_request(url: str):
    if asyncio.get_running_loop().time() % 2 < 1:  # 50%概率失败
        raise Exception("临时错误：网络波动")
    return f"成功获取{url}的数据"

# 带指数退避的重试装饰器
@retry(
    stop=stop_after_attempt(3),  # 最多重试3次
    wait=wait_exponential(multiplier=1, min=1, max=10)  # 等待时间：1s→2s→4s
)
async def retry_request(url: str):
    return await unstable_request(url)

async def main():
    try:
        result = await retry_request("https://api.example.com")
        print(result)
    except Exception as e:
        print(f"最终失败：{e}")

asyncio.run(main())
```  
**效果**：若前两次失败，第三次等待4秒后重试，成功概率更高。


### 🔍 Level 3: 对比学习（避免陷阱）  

#### 陷阱1: 无背压导致内存爆炸  
**错误用法**：生产者无限生产，消费者处理慢，队列积压导致内存飙升。  

```python
import asyncio

async def bad_producer(queue: asyncio.Queue):
    for i in range(100000):
        await queue.put(f"任务{i}")  # 队列无容量限制，无限积压

async def slow_consumer(queue: asyncio.Queue):
    while True:
        await queue.get()
        await asyncio.sleep(1)  # 每秒处理1个

async def main():
    queue = asyncio.Queue()  # 无maxsize！
    await asyncio.gather(bad_producer(queue), slow_consumer(queue))

asyncio.run(main())  # 运行几秒后内存会暴涨！
```  

**正确用法**：加`maxsize`限制队列容量，强制生产者等待：  
```python
queue = asyncio.Queue(maxsize=100)  # 最多存100个任务
```


#### 陷阱2: 重试无退避导致雪崩  
**错误用法**：失败后立即重试，频繁请求压垮下游。  

```python
from tenacity import retry, stop_after_attempt

@retry(stop=stop_after_attempt(3), wait=wait_fixed(1))  # 固定1秒等待
async def bad_retry():
    raise Exception("失败")  # 每次重试都立即发请求
```  

**正确用法**：用指数退避，等待时间翻倍：  
```python
from tenacity import wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10)  # 1s→2s→4s
)
async def good_retry():
    raise Exception("失败")
```


### 🚀 Level 4: 实战应用（真实场景）  
**需求**：爬取`https://httpbin.org/delay/1`（模拟慢API），要求：  
1. 限速：每秒最多2次请求；  
2. 背压：队列最多保存5个任务；  
3. 重试：失败后重试3次，指数退避。  

**完整代码**：  

```python
import asyncio
import aiohttp  # 异步HTTP库，需安装：pip install aiohttp
from tenacity import retry, stop_after_attempt, wait_exponential

# 1. 重试逻辑：指数退避+3次上限
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10)
)
async def fetch_url(session: aiohttp.ClientSession, url: str, task_id: int):
    async with session.get(url) as response:
        if response.status != 200:
            raise Exception(f"请求失败：{response.status}")
        print(f"任务{task_id}：成功（状态码200）")
        return await response.text()

# 2. 消费者：处理队列任务（带限速）
async def consumer(queue: asyncio.Queue, semaphore: asyncio.Semaphore):
    async with aiohttp.ClientSession() as session:
        while True:
            task_id = await queue.get()
            try:
                async with semaphore:  # 限速：每秒2次
                    await fetch_url(session, "https://httpbin.org/delay/1", task_id)
            except Exception as e:
                print(f"任务{task_id}：最终失败→{e}")
            finally:
                queue.task_done()

# 3. 生产者：生成任务（带背压）
async def producer(queue: asyncio.Queue, total_tasks: int):
    for i in range(total_tasks):
        await queue.put(i)  # 队列满时阻塞
        print(f"生产者：已加入任务{i}，队列大小{queue.qsize()}")
        await asyncio.sleep(0.5)  # 生产者速度：每秒2个

async def main():
    queue = asyncio.Queue(maxsize=5)  # 背压：队列最多5个任务
    semaphore = asyncio.Semaphore(2)  # 限速：每秒2次请求

    # 启动生产者和消费者
    producer_task = asyncio.create_task(producer(queue, 10))  # 生成10个任务
    consumer_tasks = [asyncio.create_task(consumer(queue, semaphore)) for _ in range(2)]  # 2个消费者

    # 等待生产者完成，再等待队列清空
    await producer_task
    await queue.join()

    # 取消消费者（避免无限循环）
    for task in consumer_tasks:
        task.cancel()

asyncio.run(main())
```  

**效果**：  
- 生产者生成5个任务后阻塞，等消费者处理1个才继续；  
- 每秒最多2次请求，符合限速要求；  
- 请求失败时等待1s→2s→4s重试，避免压垮API。


### 💡 记忆要点  
- **背压**：用`Queue(maxsize)`或`Semaphore`限制任务数，防止下游过载；  
- **限速**：控制执行频率（如固定窗口），遵守API速率限制；  
- **重试**：必须加**指数退避**和**次数上限**，避免雪崩效应；  
- **工具**：背压用`asyncio`原生组件，重试用`tenacity`库，限速用`limits`或`Semaphore`。