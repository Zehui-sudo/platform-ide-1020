## 异常处理与任务结果 (gather return_exceptions)

### 🎯 核心概念
解决**异步任务集群中的异常收集问题**——当多个协程任务同时运行时，默认情况下一个任务抛出异常会导致整个`gather`立即终止并抛出该异常，而`return_exceptions=True`能让`gather`**保留所有任务的结果（包括异常）**，避免“一个任务失败导致全盘崩溃”的问题。


### 💡 使用方式
`asyncio.gather(*coros_or_futures, return_exceptions=False)`  
- 默认`return_exceptions=False`：一旦有任务抛出异常，`gather`会立即终止并抛出该异常（其余任务可能未完成）。  
- 当`return_exceptions=True`：所有任务无论成功/失败都会执行完毕，异常会被**包装为实例**存入结果列表的对应位置（与任务顺序一致）。


### 📚 Level 1: 基础认知（30秒理解）
最简化示例：一个正常任务 + 一个抛异常的任务，用`return_exceptions=True`收集所有结果。
```python
import asyncio

async def success_task():
    """模拟成功的任务"""
    await asyncio.sleep(1)  # 模拟异步操作
    return "任务完成！"

async def fail_task():
    """模拟失败的任务"""
    await asyncio.sleep(0.5)
    raise ValueError("哦不，我出错了！")  # 主动抛异常

async def main():
    # 关键：return_exceptions=True 保留异常结果
    results = await asyncio.gather(
        success_task(),
        fail_task(),
        return_exceptions=True
    )
    print("最终结果:", results)  # 输出: 最终结果: ['任务完成！', ValueError('哦不，我出错了！')]

# 运行主函数
asyncio.run(main())
```


### 📈 Level 2: 核心特性（深入理解）
#### 特性1: 收集所有异常，不中断其他任务
当多个任务抛出不同异常时，`return_exceptions=True`会**保留所有异常**，不会因为第一个异常终止整个流程。
```python
import asyncio

async def task_a():
    raise TypeError("类型错误（比如参数类型不对）")

async def task_b():
    await asyncio.sleep(1)
    return 42  # 正常结果

async def task_c():
    raise RuntimeError("运行时错误（比如资源不足）")

async def main():
    results = await asyncio.gather(
        task_a(), task_b(), task_c(),
        return_exceptions=True
    )
    print("结果列表:", results)  # 输出: 结果列表: [TypeError(...), 42, RuntimeError(...)]

asyncio.run(main())
```


#### 特性2: 区分正常结果与异常（手动处理）
通过`isinstance(res, Exception)`判断结果是否为异常，实现**定制化错误处理**。
```python
import asyncio

async def main():
    results = await asyncio.gather(
        task_a(), task_b(), task_c(),
        return_exceptions=True
    )
    
    # 遍历结果，分别处理成功/失败
    for idx, res in enumerate(results, start=1):
        if isinstance(res, Exception):
            print(f"任务{idx}失败：{type(res).__name__} - {res}")
        else:
            print(f"任务{idx}成功：{res}")

# 运行后输出：
# 任务1失败：TypeError - 类型错误（比如参数类型不对）
# 任务2成功：42
# 任务3失败：RuntimeError - 运行时错误（比如资源不足）
asyncio.run(main())
```


### 🔍 Level 3: 对比学习（避免陷阱）
**错误用法**：不用`return_exceptions`，第一个异常直接崩溃
```python
import asyncio

async def main():
    try:
        # 错误：未设置return_exceptions，第一个异常会直接抛出
        results = await asyncio.gather(success_task(), fail_task())
    except ValueError as e:
        print(f"捕获到异常：{e}")  # 输出: 捕获到异常：哦不，我出错了！
    # 此时results未被赋值，无法获取success_task的结果！

asyncio.run(main())
```

**正确用法**：用`return_exceptions`保留所有结果
```python
import asyncio

async def main():
    results = await asyncio.gather(
        success_task(), fail_task(),
        return_exceptions=True  # 关键修复
    )
    # 即使有异常，也能拿到success_task的结果
    print("成功任务的结果：", results[0])  # 输出: 成功任务的结果：任务完成！
    print("失败任务的异常：", results[1])    # 输出: 失败任务的异常：哦不，我出错了！

asyncio.run(main())
```


### 🚀 Level 4: 实战应用（真实场景）
**场景**：异步爬取3个网站，收集所有结果（成功/失败）并统计
```python
import asyncio

async def fetch_url(url, delay):
    """模拟爬取网页的异步函数"""
    try:
        await asyncio.sleep(delay)  # 模拟网络延迟
        if "error" in url:
            # 模拟网页报错（比如404、500）
            raise ConnectionError(f"无法访问 {url}（服务器错误）")
        return f"[{url}] 的内容：这是网页正文..."  # 正常结果
    except Exception as e:
        # 可以在这里统一包装异常（可选）
        raise e  # 再抛出去让gather收集

async def main():
    # 待爬取的网站列表（含正常和错误链接）
    tasks = [
        fetch_url("https://正常网站1.com", delay=1),
        fetch_url("https://error网站.com", delay=0.5),  # 会报错
        fetch_url("https://正常网站2.com", delay=1.5)
    ]

    # 收集所有结果（含异常）
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # 统计成功/失败数量
    success_count = 0
    fail_count = 0

    # 遍历结果并打印
    for idx, res in enumerate(results, start=1):
        if isinstance(res, Exception):
            print(f"❌ 第{idx}个任务失败：{res}")
            fail_count += 1
        else:
            print(f"✅ 第{idx}个任务成功：{res[:30]}...")  # 截断长内容
            success_count += 1

    print(f"\n爬取完成：成功{success_count}个，失败{fail_count}个")

# 运行爬虫
asyncio.run(main())
```
**输出结果**：
```
✅ 第1个任务成功：[https://正常网站1.com] 的内容：这是网...
❌ 第2个任务失败：无法访问 https://error网站.com（服务器错误）
✅ 第3个任务成功：[https://正常网站2.com] 的内容：这是网...

爬取完成：成功2个，失败1个
```


### 💡 记忆要点
- `return_exceptions=True`是`gather`处理异常的**关键开关**，让异常“可见”而非“崩溃”。  
- 异常会被**原样保留**在结果列表中（位置与任务顺序一致），需用`isinstance(res, Exception)`判断。  
- 默认`return_exceptions=False`是“快速失败”模式，适合“一个任务失败则整个流程无效”的场景；`True`是“容忍失败”模式，适合“部分失败不影响整体”的场景（如批量爬虫、多接口调用）。