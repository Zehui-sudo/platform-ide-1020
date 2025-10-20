## 阻塞代码 offload (asyncio.to_thread/run_in_executor)

### 🎯 核心概念
解决**异步代码中调用阻塞函数导致事件循环“卡住”**的关键问题——通过将阻塞任务“卸载”到线程池执行，让事件循环继续处理其他协程，实现异步场景下的“伪并行”。


### 💡 使用方式
- **`asyncio.to_thread(func, *args, **kwargs)`**（Python 3.9+）：最简方式，自动使用默认线程池（推荐）。  
- **`loop.run_in_executor(executor, func, *args)`**：更底层的实现，支持自定义线程池（兼容 Python 3.5+）。  


### 📚 Level 1: 基础认知（30秒理解）
通过**阻塞sleep**的对比，直观感受offload的作用：  
直接调用`time.sleep(2)`会卡住整个事件循环，而用`asyncio.to_thread`则不会。

```python
import asyncio
import time

async def blocked_task():
    print("✅ 阻塞任务开始（调用time.sleep）")
    # 用to_thread卸载阻塞函数
    await asyncio.to_thread(time.sleep, 2)  
    print("✅ 阻塞任务结束")

async def normal_task():
    print("🔄 正常协程开始（用asyncio.sleep）")
    await asyncio.sleep(1)  # 非阻塞睡眠
    print("🔄 正常协程结束")

async def main():
    # 同时运行两个任务
    await asyncio.gather(blocked_task(), normal_task())

if __name__ == "__main__":
    asyncio.run(main())
```

**预期输出**（注意顺序）：
```
✅ 阻塞任务开始（调用time.sleep）
🔄 正常协程开始（用asyncio.sleep）
🔄 正常协程结束  # 1秒后先完成
✅ 阻塞任务结束  # 再等1秒（总耗时2秒）
```


### 📈 Level 2: 核心特性（深入理解）

#### 特性1: 兼容旧版本的`run_in_executor`
Python 3.9之前需用`loop.run_in_executor`，本质是`to_thread`的底层实现：

```python
import asyncio
import time

async def blocked_task():
    print("✅ 阻塞任务开始")
    # 获取当前事件循环
    loop = asyncio.get_running_loop()
    # 第一个参数为None → 使用默认线程池
    await loop.run_in_executor(None, time.sleep, 2)  
    print("✅ 阻塞任务结束")

async def main():
    await blocked_task()

asyncio.run(main())
```


#### 特性2: 自定义线程池（控制并发数）
当需要处理**大量阻塞任务**时，用`concurrent.futures.ThreadPoolExecutor`自定义线程池大小，避免线程爆炸：

```python
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor

# 自定义线程池（最多3个线程）
custom_executor = ThreadPoolExecutor(max_workers=3)

async def download_task(url: str):
    print(f"📥 开始下载: {url}")
    loop = asyncio.get_running_loop()
    # 使用自定义线程池执行阻塞的sleep（模拟下载）
    await loop.run_in_executor(custom_executor, time.sleep, 1)  
    print(f"✅ 完成下载: {url}")

async def main():
    urls = ["url1", "url2", "url3", "url4"]
    # 同时下载4个文件（线程池限制为3，总耗时≈2秒）
    await asyncio.gather(*[download_task(url) for url in urls])
    custom_executor.shutdown()  # 关闭线程池

asyncio.run(main())
```


### 🔍 Level 3: 对比学习（避免陷阱）
**错误用法**：直接调用阻塞函数，导致事件循环“瘫痪”：

```python
import asyncio
import time

async def bad_task():
    print("❌ 错误：直接调用阻塞函数")
    time.sleep(2)  # 阻塞事件循环！
    print("❌ 错误任务结束")

async def good_task():
    print("✅ 正常协程开始")
    await asyncio.sleep(1)
    print("✅ 正常协程结束")

async def main():
    await asyncio.gather(bad_task(), good_task())

asyncio.run(main())
```

**错误输出**（正常协程被卡住）：
```
❌ 错误：直接调用阻塞函数
（等待2秒）
❌ 错误任务结束
✅ 正常协程开始
✅ 正常协程结束
```

**正确用法**：用`to_thread`卸载阻塞函数：
```python
# 将bad_task中的time.sleep改为：
await asyncio.to_thread(time.sleep, 2)
```

**正确输出**（正常协程不受影响）：
```
❌ 错误：直接调用阻塞函数 → 改为to_thread后：
✅ 正常协程开始
✅ 正常协程结束  # 1秒后先完成
✅ 错误任务结束  # 再等1秒
```


### 🚀 Level 4: 实战应用（真实场景）
**场景**：用`requests`（阻塞库）异步下载多个网页，通过`to_thread`实现“并行”下载。

```python
import asyncio
import requests
from typing import List

# 阻塞的HTTP请求函数（模拟真实下载）
def fetch_url(url: str) -> str:
    response = requests.get(url, timeout=3)
    return f"[{url}] 状态码: {response.status_code}, 内容长度: {len(response.text)}"

# 异步下载函数（offload阻塞逻辑）
async def async_download(url: str) -> str:
    return await asyncio.to_thread(fetch_url, url)

async def main():
    urls = [
        "https://httpbin.org/get?name=alice",
        "https://httpbin.org/get?name=bob",
        "https://httpbin.org/get?name=charlie"
    ]
    # 同时下载3个网页（总耗时≈1秒，而非3秒）
    results = await asyncio.gather(*[async_download(url) for url in urls])
    
    # 打印结果
    print("\n📊 下载结果：")
    for res in results:
        print(res)

if __name__ == "__main__":
    import time
    start = time.time()
    asyncio.run(main())
    print(f"\n⏱️ 总耗时: {time.time() - start:.2f}秒")
```

**预期输出**（总耗时≈1秒）：
```
📊 下载结果：
[https://httpbin.org/get?name=alice] 状态码: 200, 内容长度: 351
[https://httpbin.org/get?name=bob] 状态码: 200, 内容长度: 349
[https://httpbin.org/get?name=charlie] 状态码: 200, 内容长度: 353

⏱️ 总耗时: 1.23秒
```


### 💡 记忆要点
- 🚫 **绝对不能**在异步函数中直接调用阻塞函数（如`time.sleep`、`requests.get`）！  
- 🎉 Python 3.9+优先用`asyncio.to_thread`（简洁），旧版本用`loop.run_in_executor`。  
- ⚙️ 自定义线程池可控制并发数（避免线程过多）。  
- 🔑 必须**await** offload后的任务（否则协程不会执行）。