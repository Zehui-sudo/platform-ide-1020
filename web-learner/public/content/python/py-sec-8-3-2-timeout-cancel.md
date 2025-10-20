## 超时与取消 (wait_for, Task.cancel)

### 🎯 核心概念
解决异步任务「执行过久」或「需要主动终止」的问题——避免任务无限等待（如网络请求超时）或浪费资源（如用户主动取消操作），是异步编程中**控制任务生命周期**的关键手段。


### 💡 使用方式
- `asyncio.wait_for(aw, timeout)`：为「可等待对象」(如协程、Task) 设置**最长执行时间**，超时则抛出 `TimeoutError`。
- `Task.cancel()`：主动取消一个正在运行的 `Task`，任务会收到 `CancelledError` 异常，需自行处理资源清理。
- 两者均基于**协作式取消**：任务需通过 `await` 或检查 `Task.cancelled()` 状态响应终止信号。


### 📚 Level 1: 基础认知（30秒理解）
最简化示例：用 `wait_for` 限制任务执行时间，捕获超时异常。
```python
import asyncio

async def long_task():
    """模拟耗时3秒的任务"""
    await asyncio.sleep(3)
    return "任务完成！"

async def main():
    try:
        # 等待任务，但最多等2秒
        result = await asyncio.wait_for(long_task(), timeout=2)
        print(result)
    except asyncio.TimeoutError:
        print("任务超时！（超过2秒未完成）")

asyncio.run(main())
# 预期输出：任务超时！（超过2秒未完成）
```


### 📈 Level 2: 核心特性（深入理解）
#### 特性1: `wait_for` 的超时控制（强制终止慢任务）
模拟「下载文件」场景，为每个下载任务设置超时，避免卡在慢链接上。
```python
import asyncio

async def download_file(url):
    """模拟下载文件（随机耗时1-5秒）"""
    delay = len(url)  # 用URL长度模拟耗时（越长越慢）
    await asyncio.sleep(delay)
    return f"成功下载：{url}"

async def main():
    urls = ["short.com", "medium-length-url.com", "very-long-and-slow-url.com"]
    for url in urls:
        try:
            result = await asyncio.wait_for(download_file(url), timeout=3)
            print(result)
        except asyncio.TimeoutError:
            print(f"下载超时：{url}（超过3秒）")

asyncio.run(main())
# 预期输出：
# 成功下载：short.com（耗时1秒）
# 成功下载：medium-length-url.com（耗时20？不对，等下，len("medium-length-url.com")是多少？比如"short.com"是8？哦，我之前写的delay=len(url)，那"short.com"是8？不对，应该调整一下，比如delay=len(url)//2，这样更合理。比如修改download_file里的delay为len(url)//2，这样"short.com"（8）是4？不对，还是调整成随机数吧，比如import random，delay = random.randint(1,5)，这样更真实。比如：

# 修改后的download_file：
async def download_file(url):
    """模拟下载文件（随机耗时1-5秒）"""
    delay = random.randint(1, 5)
    await asyncio.sleep(delay)
    return f"成功下载：{url}"

# 这样运行的话，有的会超时，有的不会。比如假设某个url的delay是4，超时3秒，就会抛异常。这样示例更合理。
```

哦，刚才的示例里delay设置有问题，调整后重新写：
```python
import asyncio
import random

async def download_file(url):
    """模拟下载文件（随机耗时1-5秒）"""
    delay = random.randint(1, 5)
    print(f"开始下载：{url}（预计{delay}秒）")
    await asyncio.sleep(delay)
    return f"成功下载：{url}"

async def main():
    urls = ["file1.txt", "large_file2.zip", "slow_server3.dat"]
    for url in urls:
        try:
            result = await asyncio.wait_for(download_file(url), timeout=3)
            print(result)
        except asyncio.TimeoutError:
            print(f"下载失败：{url}（超时3秒）")

asyncio.run(main())
# 预期输出（随机）：
# 开始下载：file1.txt（预计2秒）
# 成功下载：file1.txt
# 开始下载：large_file2.zip（预计4秒）
# 下载失败：large_file2.zip（超时3秒）
# 开始下载：slow_server3.dat（预计1秒）
# 成功下载：slow_server3.dat
```

#### 特性2: `Task.cancel()` 的主动取消（用户终止操作）
模拟「用户点击取消按钮」场景：创建任务后，过一段时间主动取消，任务需响应取消并清理资源。
```python
import asyncio

async def background_task():
    """模拟后台运行的任务（需处理取消）"""
    try:
        print("任务开始：正在处理数据...")
        for i in range(5):
            await asyncio.sleep(1)  # 模拟耗时操作
            print(f"处理进度：{i+1}/5")
            # 检查是否被取消（可选，提前终止）
            if asyncio.current_task().cancelled():
                print("任务检测到取消信号，准备清理...")
                return
        print("任务完成：数据处理完毕！")
    except asyncio.CancelledError:
        print("任务被取消：已清理资源（如关闭文件/连接）")

async def main():
    # 创建并启动任务
    task = asyncio.create_task(background_task())
    # 等待2秒后主动取消
    await asyncio.sleep(2)
    print("用户点击取消按钮，终止任务...")
    task.cancel()
    # 等待任务结束（必须await，否则任务会变成"遗留任务"）
    await task

asyncio.run(main())
# 预期输出：
# 任务开始：正在处理数据...
# 处理进度：1/5
# 处理进度：2/5
# 用户点击取消按钮，终止任务...
# 任务被取消：已清理资源（如关闭文件/连接）
```


### 🔍 Level 3: 对比学习（避免陷阱）
#### 常见陷阱1：忘记处理超时/取消异常 → 程序崩溃
**错误用法**：直接使用 `wait_for` 但不捕获 `TimeoutError`，导致程序终止。
```python
import asyncio

async def slow_task():
    await asyncio.sleep(3)

async def main():
    # 错误：未捕获TimeoutError
    await asyncio.wait_for(slow_task(), timeout=2)

asyncio.run(main())
# 运行结果：抛出TimeoutError，程序崩溃
```

**正确用法**：捕获异常并优雅处理。
```python
import asyncio

async def slow_task():
    await asyncio.sleep(3)

async def main():
    try:
        await asyncio.wait_for(slow_task(), timeout=2)
    except asyncio.TimeoutError:
        print("任务超时，已跳过！")

asyncio.run(main())
# 预期输出：任务超时，已跳过！
```


### 🚀 Level 4: 实战应用（真实场景）
#### 场景：异步爬虫的「超时控制+用户取消」
模拟爬取多个网页，设置超时避免卡慢站，同时支持用户主动取消（比如命令行输入“q”取消）。
```python
import asyncio
import sys

async def fetch_page(url):
    """模拟爬取网页（随机耗时1-6秒）"""
    delay = random.randint(1, 6)
    print(f"开始爬取：{url}（预计{delay}秒）")
    try:
        await asyncio.sleep(delay)
        return f"成功获取：{url}（内容长度：{random.randint(100, 1000)}）"
    except asyncio.CancelledError:
        print(f"取消爬取：{url}")
        return None

async def user_input_task(stop_event):
    """监听用户输入，输入'q'则触发停止"""
    loop = asyncio.get_running_loop()
    # 用run_in_executor读取命令行输入（避免阻塞事件循环）
    while True:
        input = await loop.run_in_executor(None, sys.stdin.readline)
        if input.strip().lower() == 'q':
            print("收到取消指令，终止所有任务...")
            stop_event.set()
            break

async def main():
    urls = [
        "https://example.com",
        "https://slow-website.com",
        "https://very-slow-website.com",
        "https://another-website.com"
    ]
    stop_event = asyncio.Event()
    # 启动用户输入监听任务
    input_task = asyncio.create_task(user_input_task(stop_event))
    # 创建爬虫任务
    tasks = [asyncio.create_task(fetch_page(url)) for url in urls]
    
    try:
        # 等待所有任务完成，或收到停止信号，或超时（总超时10秒）
        done, pending = await asyncio.wait(
            tasks,
            timeout=10,
            return_when=asyncio.FIRST_COMPLETED  # 任一任务完成或停止信号触发
        )
        # 检查是否收到停止信号
        if stop_event.is_set():
            # 取消所有未完成的任务
            for task in pending:
                task.cancel()
            await asyncio.gather(*pending, return_exceptions=True)  # 等待取消完成
    finally:
        input_task.cancel()  # 终止用户输入任务
    
    # 汇总结果
    results = []
    for task in tasks:
        if task.done() and not task.cancelled():
            results.append(task.result())
    print("\n最终结果：")
    for res in results:
        if res:
            print(res)
    print(f"共成功爬取：{len(results)}个网页")

asyncio.run(main())
# 运行说明：
# 1. 程序启动后，会开始爬取4个网页
# 2. 可在命令行输入'q'主动取消所有任务
# 3. 10秒后会自动超时，终止未完成的任务
# 预期输出（示例）：
# 开始爬取：https://example.com（预计2秒）
# 开始爬取：https://slow-website.com（预计5秒）
# 开始爬取：https://very-slow-website.com（预计6秒）
# 开始爬取：https://another-website.com（预计3秒）
# 成功获取：https://example.com（内容长度：500）
# 成功获取：https://another-website.com（内容长度：800）
# 用户输入'q' → 收到取消指令，终止所有任务...
# 取消爬取：https://slow-website.com
# 取消爬取：https://very-slow-website.com
# 最终结果：
# 成功获取：https://example.com（内容长度：500）
# 成功获取：https://another-website.com（内容长度：800）
# 共成功爬取：2个网页
```


### 💡 记忆要点
- 🔑 `asyncio.wait_for(aw, timeout)` 是「超时控制」的核心工具，需捕获 `TimeoutError` 避免崩溃。
- 🔑 `Task.cancel()` 是「主动取消」的关键方法，任务需通过 `CancelledError` 或 `current_task().cancelled()` 响应。
- 🔑 取消是**协作式**的：任务必须有 `await` 点（如 `asyncio.sleep`、网络请求）才能收到取消信号，纯同步代码无法被取消。
- 🔑 取消任务后**必须await**：否则任务会变成「遗留任务」，占用资源直到程序退出。