## 与线程/进程协同

### 🎯 核心概念
解决**异步代码（asyncio）**与**传统线程/进程任务**的协同问题——让同步任务不阻塞事件循环，同时利用线程的IO并行能力或进程的CPU并行能力，兼容旧同步库或优化特殊场景（如CPU密集型计算）。


### 💡 使用方式
通过`asyncio`提供的两个核心工具实现协同：
1. **线程协同**：用`asyncio.to_thread`（Python 3.9+，简化线程调用）或`ThreadPoolExecutor + run_in_executor`，将同步任务放到线程池中执行。
2. **进程协同**：用`multiprocessing.ProcessPoolExecutor + loop.run_in_executor`，将CPU密集型任务放到进程池中执行。

本质是将同步任务“外包”给线程/进程池，让事件循环继续处理其他异步任务。


### 📚 Level 1: 基础认知（30秒理解）
最简单示例：用`asyncio.to_thread`调用同步的`time.sleep`，模拟异步等待线程任务完成。

```python
import asyncio
import time

async def main():
    print(f"事件循环开始: {time.strftime('%X')}")
    
    # 将同步的time.sleep(1)放到线程中执行，不阻塞事件循环
    await asyncio.to_thread(time.sleep, 1)
    
    print(f"事件循环结束: {time.strftime('%X')}")  # 比开始晚1秒

asyncio.run(main())
# 预期输出：
# 事件循环开始: 14:30:00
# 事件循环结束: 14:30:01
```


### 📈 Level 2: 核心特性（深入理解）
#### 特性1: 异步调用线程任务（IO密集型）
适合**同步IO任务**（如文件读取、旧版数据库驱动），用线程池避免阻塞事件循环。

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

# 同步IO函数：读取大文件（模拟耗时IO）
def read_large_file(file_path: str) -> str:
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()  # 同步读取，会阻塞调用线程

async def main():
    # 创建线程池（最多2个线程）
    executor = ThreadPoolExecutor(max_workers=2)
    loop = asyncio.get_running_loop()
    
    # 提交2个文件读取任务到线程池，异步等待结果
    task1 = loop.run_in_executor(executor, read_large_file, 'file1.txt')
    task2 = loop.run_in_executor(executor, read_large_file, 'file2.txt')
    
    content1, content2 = await asyncio.gather(task1, task2)
    print(f"文件1长度: {len(content1)}, 文件2长度: {len(content2)}")

# 先创建测试文件：echo "hello" > file1.txt; echo "world" > file2.txt
asyncio.run(main())
# 预期输出：文件1长度: 6, 文件2长度: 6
```


#### 特性2: 异步调用进程任务（CPU密集型）
适合**CPU密集型任务**（如计算、加密、图像生成），用进程池突破GIL限制，利用多核CPU。

```python
import asyncio
import math
from concurrent.futures import ProcessPoolExecutor

# 同步CPU密集型函数：计算区间内的质数个数
def count_primes(start: int, end: int) -> int:
    count = 0
    for num in range(start, end):
        if all(num % i != 0 for i in range(2, int(math.sqrt(num)) + 1)):
            count += 1
    return count

async def main():
    # 创建进程池（自动匹配CPU核心数）
    with ProcessPoolExecutor() as executor:
        loop = asyncio.get_running_loop()
        
        # 提交2个计算任务到进程池（并行计算）
        task1 = loop.run_in_executor(executor, count_primes, 1, 100000)
        task2 = loop.run_in_executor(executor, count_primes, 100000, 200000)
        
        count1, count2 = await asyncio.gather(task1, task2)
        print(f"1-100000的质数: {count1}, 100000-200000的质数: {count2}")
        print(f"总质数: {count1 + count2}")  # 结果约17955

asyncio.run(main())
# 预期输出（耗时~1秒，比单线程快2倍以上）：
# 1-100000的质数: 9592, 100000-200000的质数: 8363
# 总质数: 17955
```


### 🔍 Level 3: 对比学习（避免陷阱）
**常见陷阱**：在异步函数中直接调用阻塞性同步函数，导致事件循环卡死！

```python
import asyncio
import time

# ❌ 错误用法：直接调用阻塞函数，阻塞整个事件循环
async def bad_example():
    print("开始执行错误示例")
    time.sleep(1)  # 阻塞事件循环，所有任务都得等它
    print("错误示例结束")

# ✅ 正确用法：用to_thread包装，不阻塞事件循环
async def good_example():
    print("开始执行正确示例")
    await asyncio.to_thread(time.sleep, 1)  # 线程执行，事件循环继续
    print("正确示例结束")

async def main():
    # 同时运行2个正确示例，看并行效果
    task1 = asyncio.create_task(good_example())
    task2 = asyncio.create_task(good_example())
    await asyncio.gather(task1, task2)

asyncio.run(main())
# 错误示例输出（若运行bad_example）：
# 开始执行错误示例 → 等待1秒 → 错误示例结束 → 开始执行正确示例
# 正确示例输出：
# 开始执行正确示例 → 开始执行正确示例 → （1秒后）两个示例同时结束
```


### 🚀 Level 4: 实战应用（真实场景）
**场景**：异步HTTP服务器处理请求时，需要调用同步CPU密集型函数（生成验证码图片），避免阻塞事件循环。

```python
import asyncio
import random
from aiohttp import web
from concurrent.futures import ProcessPoolExecutor

# 同步CPU密集型函数：生成随机验证码（模拟图像生成）
def generate_captcha(length: int = 6) -> str:
    import time
    time.sleep(0.1)  # 模拟复杂计算（如绘制图片）
    return ''.join(random.choices('abcdef123456', k=length))

# 异步请求处理器
async def handle_captcha(request):
    length = int(request.query.get('length', 6))
    executor = request.app['executor']  # 从app获取进程池
    
    # 提交验证码生成任务到进程池
    captcha = await asyncio.get_running_loop().run_in_executor(
        executor, generate_captcha, length
    )
    return web.json_response({'captcha': captcha})

# 初始化应用
async def init_app():
    app = web.Application()
    app['executor'] = ProcessPoolExecutor()  # 绑定进程池到app
    app.add_routes([web.get('/captcha', handle_captcha)])
    return app

if __name__ == '__main__':
    web.run_app(init_app())
```

**测试**：启动服务器后，用浏览器访问`http://localhost:8080/captcha?length=8`，会返回随机验证码。即使同时发送10个请求，也能并行处理（进程池负责计算，事件循环负责接收请求）。


### 💡 记忆要点
- **线程vs进程**：IO密集型用线程（`to_thread`），CPU密集型用进程（`ProcessPoolExecutor`）。
- **不阻塞原则**：永远不要在异步函数中直接调用阻塞性同步函数（如`time.sleep`、`requests.get`）。
- **工具选择**：Python 3.9+优先用`asyncio.to_thread`（简化线程调用），进程任务用`ProcessPoolExecutor + run_in_executor`。


通过以上内容，你已经掌握了异步代码与线程/进程的协同技巧，既能兼容旧同步库，又能优化特殊场景的性能！