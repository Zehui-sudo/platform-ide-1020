## 事件循环与任务 (create_task, gather)

### 🎯 核心概念
事件循环是异步程序的"调度中心"，负责管理协程的执行顺序；任务（Task）是协程的"执行容器"，通过`create_task`将协程包装为可被事件循环调度的单元；`gather`用于批量等待多个任务完成并收集结果——三者共同解决**多个协程的并发执行与结果管理**问题，让异步程序高效有序运行。


### 💡 使用方式
1. **启动事件循环**：用`asyncio.run(main())`自动管理事件循环（Python 3.7+推荐）；  
2. **创建任务**：`asyncio.create_task(coro)`将协程转为任务（立即加入事件循环调度）；  
3. **批量等待任务**：`asyncio.gather(*tasks)`同时等待多个任务完成，返回结果列表（顺序与传入任务一致）。


### 📚 Level 1: 基础认知（30秒理解）
最简化示例：两个协程通过任务并发执行，观察执行顺序。
```python
import asyncio

async def say_after(delay, content):
    """延迟delay秒后打印内容"""
    await asyncio.sleep(delay)
    print(content)

async def main():
    # 将协程包装为任务（事件循环会自动调度）
    task1 = asyncio.create_task(say_after(1, "Hello"))  # 延迟1秒
    task2 = asyncio.create_task(say_after(0.5, "World")) # 延迟0.5秒
    
    print("等待任务完成...")
    await task1  # 等待task1时，事件循环会切换到task2执行
    await task2

# 启动事件循环（自动处理循环的创建与关闭）
asyncio.run(main())
```
**预期输出**（顺序由`sleep`时间决定）：
```
等待任务完成...
World  # 0.5秒后先打印
Hello  # 1秒后打印
```


### 📈 Level 2: 核心特性（深入理解）
#### 特性1: 任务的自动调度（事件循环的"魔法"）
事件循环会在任务等待（如`await asyncio.sleep`）时，自动切换到其他就绪任务，实现"并发"。
```python
import asyncio

async def work(task_name, delay):
    """模拟耗时任务"""
    print(f"[{task_name}] 开始执行...")
    await asyncio.sleep(delay)
    print(f"[{task_name}] 执行完成！")

async def main():
    # 创建3个任务（延迟分别为2、1、3秒）
    tasks = [
        asyncio.create_task(work("任务A", 2)),
        asyncio.create_task(work("任务B", 1)),
        asyncio.create_task(work("任务C", 3))
    ]
    
    # 批量等待所有任务完成
    await asyncio.gather(*tasks)

asyncio.run(main())
```
**输出结果**（事件循环自动切换任务）：
```
[任务A] 开始执行...
[任务B] 开始执行...
[任务C] 开始执行...
[任务B] 执行完成！  # 1秒后先完成
[任务A] 执行完成！  # 2秒后完成
[任务C] 执行完成！  # 3秒后完成
```


#### 特性2: gather收集任务结果（顺序严格一致）
`gather`会按**传入任务的顺序**返回结果，即使任务执行顺序不同。
```python
import asyncio

async def compute(x):
    """异步计算x的平方（模拟耗时操作）"""
    await asyncio.sleep(x)  # 延迟x秒（模拟计算时间）
    return x * x

async def main():
    # 同时运行3个计算任务
    results = await asyncio.gather(compute(1), compute(2), compute(3))
    print("计算结果:", results)  # 结果顺序与传入任务一致

asyncio.run(main())
```
**输出结果**：
```
计算结果: [1, 4, 9]  # 即使compute(3)最后完成，结果仍在第3位
```


### 🔍 Level 3: 对比学习（避免陷阱）
**常见陷阱1：忘记await任务→任务未执行**  
错误用法：创建任务后不await，任务会被垃圾回收，永远不会执行。
```python
async def main():
    asyncio.create_task(say_after(1, "Hello"))  # 没await，任务未执行
    print("程序结束")

asyncio.run(main())  # 输出"程序结束"，但"Hello"没打印！
```

**常见陷阱2：直接await协程→同步执行**  
错误用法：直接await协程是**同步执行**（会阻塞直到协程完成），失去并发优势。
```python
async def main():
    await say_after(1, "Hello")  # 同步等待1秒
    await say_after(0.5, "World") # 再等待0.5秒
    # 总耗时1.5秒（非并发）

asyncio.run(main())
```

**正确用法：创建任务或用gather**
```python
async def main():
    # 方式1：创建任务后await
    task1 = asyncio.create_task(say_after(1, "Hello"))
    task2 = asyncio.create_task(say_after(0.5, "World"))
    await task1
    await task2

    # 方式2：用gather批量等待（更简洁）
    await asyncio.gather(
        say_after(1, "Hello"),
        say_after(0.5, "World")
    )
```


### 🚀 Level 4: 实战应用（真实场景）
**场景**：模拟异步下载3个文件（不同延迟），统计总耗时并收集结果。
```python
import asyncio
import time

async def download_file(filename, delay):
    """模拟文件下载（延迟delay秒）"""
    print(f"开始下载: {filename}")
    await asyncio.sleep(delay)
    print(f"完成下载: {filename}")
    return f"{filename} 的内容（大小: {delay*100}MB）"

async def main():
    # 待下载的文件列表（文件名+下载延迟）
    download_list = [
        ("report.pdf", 3),   # 延迟3秒
        ("photo.jpg", 1),    # 延迟1秒
        ("video.mp4", 2)     # 延迟2秒
    ]
    
    start_time = time.time()
    
    # 1. 创建所有下载任务（并发执行）
    tasks = [
        asyncio.create_task(download_file(name, delay))
        for name, delay in download_list
    ]
    
    # 2. 批量等待任务完成，收集结果
    results = await asyncio.gather(*tasks)
    
    end_time = time.time()
    
    # 3. 输出统计信息
    print(f"\n===== 下载完成 =====")
    print(f"总耗时: {end_time - start_time:.2f} 秒")  # 总耗时=最长延迟（3秒）
    for res in results:
        print(f"- {res}")

asyncio.run(main())
```
**输出结果**：
```
开始下载: report.pdf
开始下载: photo.jpg
开始下载: video.mp4
完成下载: photo.jpg
完成下载: video.mp4
完成下载: report.pdf

===== 下载完成 =====
总耗时: 3.00 秒
- report.pdf 的内容（大小: 300MB）
- photo.jpg 的内容（大小: 100MB）
- video.mp4 的内容（大小: 200MB）
```


### 💡 记忆要点
- **事件循环是"发动机"**：负责调度任务，没有循环就没有异步执行；  
- **任务是"容器"**：`create_task`将协程转为可调度的任务，必须await或用gather等待；  
- **gather的"顺序性"**：结果顺序与传入任务顺序一致，无关执行顺序；  
- **不要忘记await**：未被await的任务会被销毁，永远不会执行；  
- **创建任务才是并发**：直接await协程是同步，创建任务才是异步并发。