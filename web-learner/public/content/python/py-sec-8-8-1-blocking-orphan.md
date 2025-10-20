## 避免遗留任务与忘记 await

### 🎯 核心概念
解决异步编程中**任务未被正确等待**导致的三大问题：任务未执行、结果丢失、资源泄漏，确保异步流程的完整性与稳定性。


### 💡 使用方式
1. **调用async函数必加`await`**：所有用`async def`定义的函数，调用时必须前缀`await`，否则仅返回`coroutine`对象（不执行）。  
2. **等待所有`Task`**：用`asyncio.create_task()`创建的任务，需通过`await task`或`asyncio.gather(*tasks)`等待完成。  
3. **程序退出前清理任务**：确保主函数结束前，所有异步任务都已处理完毕。


### 📚 Level 1: 基础认知（30秒理解）
创建任务但**未等待**，会导致任务被"遗留"，程序提前退出：
```python
import asyncio

async def say_hello():
    await asyncio.sleep(1)  # 模拟耗时操作
    print("Hello, Async!")  # 未执行：任务没被等待

async def main():
    asyncio.create_task(say_hello())  # 创建任务但未等待
    print("Main done!")  # 先打印，程序直接退出

asyncio.run(main())
```
**预期输出**：  
`Main done!`（`say_hello`的打印未执行，因为任务没被等待）


### 📈 Level 2: 核心特性（深入理解）
#### 特性1: 忘记`await`=没执行函数
调用`async`函数时忘记`await`，会得到**`coroutine`对象**（而非函数结果）：
```python
async def fetch_data():
    await asyncio.sleep(1)
    return {"data": 42}  # 真实场景：从API/数据库获取数据

async def main():
    # 错误：忘记await，拿到的是coroutine对象
    result = fetch_data()
    print(type(result))  # 输出：<class 'coroutine'>（不是结果）
    
    # 正确：加await获取结果
    result = await fetch_data()
    print(result)  # 输出：{"data": 42}

asyncio.run(main())
```


#### 特性2: 必须等待所有`Task`完成
用`create_task()`创建的任务，需**显式等待**才能确保执行：
```python
async def task1():
    await asyncio.sleep(1)
    print("Task 1: 数据下载完成")

async def task2():
    await asyncio.sleep(2)
    print("Task 2: 文件保存完成")

async def main():
    t1 = asyncio.create_task(task1())  # 创建任务1
    t2 = asyncio.create_task(task2())  # 创建任务2
    
    # 正确：等待所有任务完成（顺序不影响执行顺序）
    await t1  
    await t2  
    # 或用asyncio.gather批量等待：await asyncio.gather(t1, t2)
    
    print("所有任务完成，程序可以安全退出")

asyncio.run(main())
```
**预期输出**：  
`Task 1: 数据下载完成` → `Task 2: 文件保存完成` → `所有任务完成，程序可以安全退出`


### 🔍 Level 3: 对比学习（避免陷阱）
通过**错误vs正确**的对比，识别常见陷阱：
```python
import asyncio

async def work():
    await asyncio.sleep(1)
    print("Work done!")

# -------------------- 错误用法 --------------------
async def bad_case1():
    work()  # 忘记await：coroutine对象未执行
    print("Bad 1: 我以为work执行了...")

async def bad_case2():
    asyncio.create_task(work())  # 创建任务但未等待
    print("Bad 2: 任务被遗留了...")

# -------------------- 正确用法 --------------------
async def good_case():
    # 1. 调用async函数加await
    await work()  
    # 2. 创建任务后等待
    task = asyncio.create_task(work())
    await task  
    print("Good: 所有任务都完成了！")

# 运行测试
async def main():
    print("=== 错误案例1 ===")
    await bad_case1()  # 输出：Bad 1: ...（Work done!未执行）
    print("\n=== 错误案例2 ===")
    await bad_case2()  # 输出：Bad 2: ...（Work done!未执行）
    print("\n=== 正确案例 ===")
    await good_case()  # 输出：Work done! ×2 + Good: ...

asyncio.run(main())
```


### 🚀 Level 4: 实战应用（真实场景）
模拟**多图片异步下载**场景，需等待所有下载任务完成后再处理结果：
```python
import asyncio
import random

async def download_image(url):
    print(f"开始下载: {url}")
    await asyncio.sleep(random.uniform(0.5, 2))  # 模拟网络延迟
    print(f"下载完成: {url}")
    return f"{url}_image.jpg"  # 返回下载后的文件名

async def main():
    urls = [
        "https://example.com/img1",
        "https://example.com/img2",
        "https://example.com/img3"
    ]
    
    # 1. 创建所有下载任务
    tasks = [asyncio.create_task(download_image(url)) for url in urls]
    # 2. 等待所有任务完成（获取结果）
    downloaded_files = await asyncio.gather(*tasks)
    
    print("\n所有图片下载完成！结果：")
    print(downloaded_files)  # 输出：['img1_image.jpg', 'img2_image.jpg', 'img3_image.jpg']

asyncio.run(main())
```
**关键**：如果不用`gather`等待，程序会在下载中途退出，导致图片未完全下载。


### 💡 记忆要点
- ✅ 调用`async`函数必加`await`，否则等于"没调用"。  
- ✅ `create_task()`创建的任务，必须用`await`或`gather`等待。  
- ✅ 程序退出前，确保所有异步任务都已处理完毕（避免遗留）。