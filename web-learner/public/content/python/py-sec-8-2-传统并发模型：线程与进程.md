好的，作为一名世界级的技术教育者和 Python 专家，我将无缝衔接之前的内容，继续为您精心打造这篇高质量的 Markdown 教程。

---

### 🎯 核心概念

当多个线程需要**同时访问和修改同一个共享资源**（例如一个全局变量）时，如果不对访问进行控制，就会导致数据错乱、结果不可预测，这种情况被称为**“竞态条件” (Race Condition)**。线程同步机制，如锁 (Lock)，就是为了解决这个问题，确保在任何时刻只有一个线程能够操作共享资源，从而保证数据的完整性和一致性。

### 💡 使用方式

Python 的 `threading` 模块提供了 `Lock` 对象来解决竞态条件。一个线程可以通过调用 `lock.acquire()` 来获取锁，此时其他线程如果也尝试获取该锁，就会被阻塞，直到持有锁的线程调用 `lock.release()` 释放锁为止。更推荐、更安全的方式是使用 `with` 语句，它能自动管理锁的获取和释放，即使在代码块中发生异常也能保证锁被释放。

### 📚 Level 1: 基础认知（30秒理解）

想象一下，两个收银员（线程）同时操作同一个银行账户（共享变量）。如果不加控制，账户余额就会算错。

```python
import threading
import time

# 共享资源：银行账户余额
balance = 0
# 创建一个锁
lock = threading.Lock()

def deposit(amount):
    """模拟存款操作"""
    global balance
    # 读取当前余额
    current_balance = balance
    # 模拟处理时间
    time.sleep(0.01)
    # 计算新余额并写入
    balance = current_balance + amount

def run_threads_without_lock(n_threads):
    """不使用锁，会产生竞态条件"""
    global balance
    balance = 0
    threads = []
    for _ in range(n_threads):
        thread = threading.Thread(target=deposit, args=(1,))
        threads.append(thread)
        thread.start()
    for thread in threads:
        thread.join()
    print(f"不使用锁，{n_threads} 个线程每个存入1元，最终余额: {balance}")

def run_threads_with_lock(n_threads):
    """使用 with lock: 语句保护共享资源"""
    global balance
    balance = 0
    
    def locked_deposit(amount):
        global balance
        with lock: # with语句自动获取和释放锁
            current_balance = balance
            time.sleep(0.01)
            balance = current_balance + amount

    threads = []
    for _ in range(n_threads):
        thread = threading.Thread(target=locked_deposit, args=(1,))
        threads.append(thread)
        thread.start()
    for thread in threads:
        thread.join()
    print(f"使用锁后，{n_threads} 个线程每个存入1元，最终余额: {balance}")


# 运行示例
THREAD_COUNT = 100
run_threads_without_lock(THREAD_COUNT)
run_threads_with_lock(THREAD_COUNT)

# 预期输出结果 (不使用锁的结果可能每次都不同，但几乎总是小于100):
# 不使用锁，100 个线程每个存入1元，最终余额: 2  <-- 结果错误！
# 使用锁后，100 个线程每个存入1元，最终余额: 100 <-- 结果正确！
```

### 📈 Level 2: 核心特性（深入理解）

#### 特性1: 可重入锁 (RLock)

一个线程在已经持有普通 `Lock` 的情况下，如果再次尝试获取该锁，将会造成**死锁 (Deadlock)**，程序会永远阻塞。`RLock` (Re-entrant Lock) 允许同一个线程多次获取同一个锁，而不会造成死锁。这在复杂的函数调用或递归场景中非常有用。

```python
import threading

# 使用普通锁在嵌套函数中会死锁
lock = threading.Lock()
# 使用可重入锁则可以正常工作
rlock = threading.RLock()

def complex_operation_deadlock():
    print("线程尝试获取 lock...")
    lock.acquire()
    print("线程已获取 lock，准备进入内层函数...")
    inner_operation_deadlock()
    lock.release()
    print("线程已释放 lock。")

def inner_operation_deadlock():
    print("内层函数尝试再次获取 lock...")
    lock.acquire() # 这里会永远阻塞，因为当前线程已经持有该锁
    print("这行代码永远不会执行")
    lock.release()

def complex_operation_with_rlock():
    print("线程尝试获取 rlock...")
    rlock.acquire()
    print("线程已获取 rlock，准备进入内层函数...")
    inner_operation_with_rlock()
    rlock.release()
    print("线程已释放 rlock。")

def inner_operation_with_rlock():
    print("内层函数尝试再次获取 rlock...")
    rlock.acquire() # RLock允许同一个线程重复获取
    print("RLock 获取成功！操作可以继续。")
    rlock.release()

print("--- 演示普通 Lock 的死锁 ---")
# deadlock_thread = threading.Thread(target=complex_operation_deadlock)
# deadlock_thread.start()
# deadlock_thread.join(timeout=2)
# if deadlock_thread.is_alive():
#     print("线程发生死锁！\n")
# (为防止程序卡住，以上代码已注释，可自行取消注释测试)
print("普通 Lock 在嵌套获取时会死锁。\n")

print("--- 演示 RLock 的正确工作 ---")
rlock_thread = threading.Thread(target=complex_operation_with_rlock)
rlock_thread.start()
rlock_thread.join()
print("RLock 演示完成。")

# 预期输出结果:
# --- 演示普通 Lock 的死锁 ---
# 普通 Lock 在嵌套获取时会死锁。
#
# --- 演示 RLock 的正确工作 ---
# 线程尝试获取 rlock...
# 线程已获取 rlock，准备进入内层函数...
# 内层函数尝试再次获取 rlock...
# RLock 获取成功！操作可以继续。
# 线程已释放 rlock。
# RLock 演示完成。
```

#### 特性2: 信号量 (Semaphore)

`Semaphore` 是一种更高级的锁机制，它维护一个计数器。每次调用 `acquire()` 时计数器减1，调用 `release()` 时计数器加1。当计数器为0时，`acquire()` 会阻塞。这使得 `Semaphore` 非常适合用来**限制能够同时访问某一资源（如数据库连接池、API调用限流）的线程数量**。

```python
import threading
import time
import random

# 创建一个值为3的信号量，表示最多允许3个线程同时访问资源
semaphore = threading.Semaphore(3)

def access_database(thread_id):
    """模拟一个访问数据库的线程"""
    print(f"线程 {thread_id}: 等待访问数据库...")
    with semaphore:
        # with语句自动管理acquire和release
        print(f"✅ 线程 {thread_id}: 已连接到数据库。正在处理业务...")
        time.sleep(random.uniform(1, 2)) # 模拟数据库操作耗时
        print(f"线程 {thread_id}: 操作完成，断开连接。")

threads = []
# 创建5个线程，但信号量只允许3个并发执行
for i in range(5):
    thread = threading.Thread(target=access_database, args=(i,))
    threads.append(thread)
    thread.start()

for thread in threads:
    thread.join()

# 预期输出结果 (你会看到同时最多只有3个线程在处理业务):
# 线程 0: 等待访问数据库...
# ✅ 线程 0: 已连接到数据库。正在处理业务...
# 线程 1: 等待访问数据库...
# ✅ 线程 1: 已连接到数据库。正在处理业务...
# 线程 2: 等待访问数据库...
# ✅ 线程 2: 已连接到数据库。正在处理业务...
# 线程 3: 等待访问数据库...
# 线程 4: 等待访问数据库...
# 线程 0: 操作完成，断开连接。
# ✅ 线程 3: 已连接到数据库。正在处理业务...
# 线程 1: 操作完成，断开连接。
# ✅ 线程 4: 已连接到数据库。正在处理业务...
# ... (后续输出)
```

### 🔍 Level 3: 对比学习（避免陷阱）

**陷阱：死锁 (Deadlock)**

当两个或多个线程互相持有对方需要的锁，并且等待对方释放时，就会形成死锁。所有相关线程都会被无限期地阻塞，程序无法继续执行。最常见的死锁原因是**以不同的顺序获取多个锁**。

```python
import threading
import time

# 两个共享资源，分别由两个锁保护
fork = threading.Lock()
knife = threading.Lock()

def philosopher_A():
    """哲学家A: 先拿叉子，再拿刀子"""
    print("哲学家 A 思考中...")
    time.sleep(1)
    with fork:
        print("哲学家 A 拿到了叉子。")
        time.sleep(0.5)
        print("哲学家 A 试图拿刀子...")
        with knife:
            print("哲学家 A 拿到了刀子，开始吃饭。") # 这句可能永远不会执行

def philosopher_B():
    """哲学家B: 先拿刀子，再拿叉子"""
    print("哲学家 B 思考中...")
    time.sleep(1)
    with knife:
        print("哲学家 B 拿到了刀子。")
        time.sleep(0.5)
        print("哲学家 B 试图拿叉子...")
        with fork:
            print("哲学家 B 拿到了叉子，开始吃饭。") # 这句也可能永远不会执行

# === 错误用法 ===
# ❌ 以不同顺序获取锁，极易导致死锁
print("--- 错误用法：可能导致死锁 ---")
thread_a_wrong = threading.Thread(target=philosopher_A)
thread_b_wrong = threading.Thread(target=philosopher_B)
thread_a_wrong.start()
thread_b_wrong.start()
thread_a_wrong.join(timeout=3)
thread_b_wrong.join(timeout=3)
if thread_a_wrong.is_alive() or thread_b_wrong.is_alive():
    print("❌ 死锁发生！程序卡住。\n")
# 解释为什么是错的:
# 哲学家A拿到叉子后，等待刀子。
# 同时，哲学家B拿到刀子后，等待叉子。
# 双方都持有对方需要的资源，并等待对方释放，程序陷入僵局。

time.sleep(4) # 等待上一个例子结束

# === 正确用法 ===
# ✅ 始终以相同的、固定的顺序获取所有锁
print("\n--- 正确用法：按固定顺序获取锁 ---")
def philosopher_C():
    """哲学家C: 始终先拿刀子，再拿叉子"""
    print("哲学家 C 思考中...")
    time.sleep(1)
    with knife:
        print("哲学家 C 拿到了刀子。")
        time.sleep(0.5)
        print("哲学家 C 试图拿叉子...")
        with fork:
            print("✅ 哲学家 C 拿到了叉子，开始吃饭。")

thread_a_correct = threading.Thread(target=philosopher_C)
thread_b_correct = threading.Thread(target=philosopher_C)
thread_a_correct.start()
thread_b_correct.start()
thread_a_correct.join()
thread_b_correct.join()
print("✅ 两位哲学家都吃完饭了。")
# 解释为什么这样是对的:
# 通过规定所有线程必须按同一顺序（例如，先 knife 后 fork）请求锁，
# 破坏了死锁产生的循环等待条件。一个线程要么能获取所有锁，要么在第一个锁就被阻塞，
# 不会持有部分锁去等待其他锁。
```

### 🚀 Level 4: 实战应用（真实场景）

**场景：** 🏰 矮人工匠的符文锻造工坊

在矮人的地下城里，有一个传奇的锻造工坊。多名矮人工匠（线程）需要使用**唯一的“符文铁砧”**（共享资源）和有限的**“冷却池”**（信号量限制的资源）来锻造魔法武器。我们需要确保：
1.  任何时候只有一个工匠能使用符文铁砧。
2.  最多只能有两个工匠同时使用冷却池。

```python
import threading
import time
import random

# 共享资源
rune_anvil_lock = threading.Lock()  # 符文铁砧，独占资源
cooling_pool_semaphore = threading.Semaphore(2) # 冷却池，最多容纳2个

def dwarf_smith(name):
    """一个矮人工匠的工作流程"""
    print(f"⚒️ 工匠 {name} 进入了工坊。")
    
    # --- 阶段1: 使用符文铁砧 ---
    print(f"工匠 {name} 等待使用符文铁砧...")
    with rune_anvil_lock:
        print(f"🔥 工匠 {name} 正在使用符文铁砧锻造...")
        time.sleep(random.uniform(1.5, 2.5))
        print(f"✨ 工匠 {name} 的武器锻造完成，离开铁砧。")

    # --- 阶段2: 使用冷却池 ---
    print(f"工匠 {name} 等待使用冷却池...")
    with cooling_pool_semaphore:
        print(f"💧 工匠 {name} 正在使用冷却池淬火...")
        time.sleep(random.uniform(1, 2))
        print(f"💨 工匠 {name} 的武器淬火完成，离开冷却池。")

    print(f"🎉 工匠 {name} 完成了一件魔法武器！")

if __name__ == '__main__':
    dwarf_names = ["Gimli", "Balin", "Dwalin", "Thorin"]
    threads = []
    print("--- 矮人工坊开工了！---\n")

    for name in dwarf_names:
        thread = threading.Thread(target=dwarf_smith, args=(name,))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    print("\n--- 今天所有的锻造任务都完成了！ ---")

# 预期输出 (顺序可能变化，但规律不变):
# --- 矮人工坊开工了！---
#
# ⚒️ 工匠 Gimli 进入了工坊。
# 工匠 Gimli 等待使用符文铁砧...
# 🔥 工匠 Gimli 正在使用符文铁砧锻造...
# ⚒️ 工匠 Balin 进入了工坊。
# 工匠 Balin 等待使用符文铁砧...  (被阻塞)
# ⚒️ 工匠 Dwalin 进入了工坊。
# 工匠 Dwalin 等待使用符文铁砧... (被阻塞)
# ⚒️ 工匠 Thorin 进入了工坊。
# 工匠 Thorin 等待使用符文铁砧... (被阻塞)
# ✨ 工匠 Gimli 的武器锻造完成，离开铁砧。
# 工匠 Gimli 等待使用冷却池...
# 💧 工匠 Gimli 正在使用冷却池淬火...
# 🔥 工匠 Balin 正在使用符文铁砧锻造... (Gimli释放后，Balin获得锁)
# ✨ 工匠 Balin 的武器锻造完成，离开铁砧。
# 工匠 Balin 等待使用冷却池...
# 💧 工匠 Balin 正在使用冷却池淬火... (冷却池还有空位)
# 💨 工匠 Gimli 的武器淬火完成，离开冷却池。
# 🎉 工匠 Gimli 完成了一件魔法武器！
# ... (后续工匠依次完成)
```

### 💡 记忆要点
- **要点1**: **访问共享资源，必上锁**。只要有多个线程会修改同一个变量，就必须使用 `Lock` 或其他同步机制来保护它。
- **要点2**: **`with lock:` 是黄金法则**。它能保证锁在任何情况下（即使发生异常）都会被正确释放，是避免资源泄漏和死锁的最佳实践。
- **要点3**: **警惕死锁，统一加锁顺序**。当需要获取多个锁时，确保所有线程都遵循完全相同的顺序来获取它们，这是打破死锁循环等待条件的有效方法。

---

## 8.2.1 更现代的并发接口：`concurrent.futures`

### 🎯 核心概念

`concurrent.futures` 模块提供了一个**高级、统一的接口**来异步执行任务。它将线程和进程的管理细节（如创建、启动、加入）封装起来，让你能以相同的方式来使用线程池和进程池，只需关注**提交任务**和**获取结果**，从而极大地简化了并发编程。

### 💡 使用方式

核心是 `Executor` 对象，它有两种形式：`ThreadPoolExecutor`（线程池）和 `ProcessPoolExecutor`（进程池）。
1.  创建一个 `Executor` 实例（通常使用 `with` 语句）。
2.  使用 `.submit(func, *args, **kwargs)` 方法提交任务，它会立即返回一个 `Future` 对象。
3.  `Future` 对象代表一个尚未完成的计算，你可以通过它的 `.result()` 方法来获取任务的返回值（如果任务未完成，`.result()` 会阻塞等待）。

### 📚 Level 1: 基础认知（30秒理解）

让我们用 `ThreadPoolExecutor` 重写本章开头的“下载文件”示例，体验一下代码有多简洁。

```python
import concurrent.futures
import time

def fake_download(task_name):
    """模拟一个需要等待I/O的任务"""
    print(f"开始下载 {task_name}...")
    time.sleep(2)
    result = f"{task_name} 下载完成!"
    print(result)
    return result

# 使用 ThreadPoolExecutor
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
    print("--- 使用 concurrent.futures 并发执行 ---")
    start_time = time.time()
    
    # 提交任务，立即返回 future 对象
    future1 = executor.submit(fake_download, "文件C")
    future2 = executor.submit(fake_download, "文件D")
    
    # 获取结果 (result() 方法会阻塞直到任务完成)
    print("主线程：等待结果...")
    result1 = future1.result()
    result2 = future2.result()
    
    end_time = time.time()
    
    print(f"\n获取到的结果: ['{result1}', '{result2}']")
    print(f"并发执行总耗时: {end_time - start_time:.2f} 秒")

# 预期输出结果:
# --- 使用 concurrent.futures 并发执行 ---
# 主线程：等待结果...
# 开始下载 文件C...
# 开始下载 文件D...
# 文件C 下载完成!
# 文件D 下载完成!
#
# 获取到的结果: ['文件C 下载完成!', '文件D 下载完成!']
# 并发执行总耗时: 2.01 秒
```

### 📈 Level 2: 核心特性（深入理解）

#### 特性1: `executor.map` 的批量处理

如果你想将同一个函数应用到一系列的输入数据上，`executor.map` 是比多次调用 `submit` 更简洁的选择。它的行为类似内置的 `map` 函数，但任务是并发执行的。它返回一个迭代器，你可以按输入顺序遍历任务的结果。

```python
import concurrent.futures
import time

urls = [
    "site1.com",
    "site2.com",
    "site3.com",
    "site4.com",
]

def fetch_url(url):
    """模拟请求网页"""
    print(f"开始请求 {url}...")
    time.sleep(1)
    return f"来自 {url} 的内容"

with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
    start_time = time.time()
    
    # executor.map 会保持结果的顺序与输入顺序一致
    results = executor.map(fetch_url, urls)
    
    print("主线程：开始遍历结果...")
    # 遍历 results 时，会按顺序等待每个任务完成
    for result in results:
        print(f"处理结果: {result}")
        
    end_time = time.time()
    print(f"\n使用 map 总耗时: {end_time - start_time:.2f} 秒")

# 预期输出结果:
# 开始请求 site1.com...
# 开始请求 site2.com...
# 开始请求 site3.com...
# 开始请求 site4.com...
# 主线程：开始遍历结果...
# 处理结果: 来自 site1.com 的内容
# 处理结果: 来自 site2.com 的内容
# 处理结果: 来自 site3.com 的内容
# 处理结果: 来自 site4.com 的内容
#
# 使用 map 总耗时: 1.01 秒
```

#### 特性2: `as_completed` 实时响应

有时你不想按顺序等待所有任务，而是希望**哪个任务先完成就先处理哪个**。`concurrent.futures.as_completed()` 函数接收一个 `Future` 列表，返回一个迭代器，该迭代器在每个 `Future` 完成时产出它。

```python
import concurrent.futures
import time
import random

def query_database(source_name):
    """模拟查询不同数据库，耗时不同"""
    delay = random.uniform(0.5, 3.0)
    print(f"开始查询 {source_name} (预计耗时 {delay:.2f}s)...")
    time.sleep(delay)
    return f"来自 {source_name} 的数据"

sources = ["主数据库", "备份数据库", "缓存服务器"]

with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
    # 提交所有任务，并将 future 对象存入列表
    future_to_source = {executor.submit(query_database, src): src for src in sources}
    
    print("\n--- 等待最先完成的任务 ---")
    
    # as_completed 会在任务完成时立即返回
    for future in concurrent.futures.as_completed(future_to_source):
        source = future_to_source[future]
        try:
            data = future.result()
            print(f"✅ 优先处理完成的结果: [{source}] -> {data}")
        except Exception as e:
            print(f"❌ {source} 查询失败: {e}")

# 预期输出结果 (顺序取决于随机的延迟时间):
# 开始查询 主数据库 (预计耗时 2.15s)...
# 开始查询 备份数据库 (预计耗时 0.78s)...
# 开始查询 缓存服务器 (预计耗时 1.50s)...
#
# --- 等待最先完成的任务 ---
# ✅ 优先处理完成的结果: [备份数据库] -> 来自 备份数据库 的数据
# ✅ 优先处理完成的结果: [缓存服务器] -> 来自 缓存服务器 的数据
# ✅ 优先处理完成的结果: [主数据库] -> 来自 主数据库 的数据
```

### 🔍 Level 3: 对比学习（避免陷阱）

**陷阱：被“吞噬”的异常**

如果一个由 `submit` 或 `map` 提交的任务在执行过程中抛出异常，这个异常不会立即在主线程中引发。它会被捕获并存储在 `Future` 对象中。如果你从不调用该 `Future` 的 `.result()` 方法，你就永远不会知道发生了错误！

```python
import concurrent.futures
import time

def task_that_fails():
    print("任务开始，准备抛出异常...")
    time.sleep(1)
    raise ValueError("计算出错！")

# === 错误用法 ===
# ❌ 提交任务后不检查结果，异常会被忽略
print("--- 错误用法：异常被吞噬 ---")
with concurrent.futures.ThreadPoolExecutor() as executor:
    future = executor.submit(task_that_fails)
    print("任务已提交，主线程继续执行其他事情...")
    time.sleep(2)
    # 没有调用 future.result()
    print("主线程结束，但从未发现后台任务已失败！")
# 解释为什么是错的:
# 异常被存储在 future 对象里，但由于我们没有调用 .result() 来“解包”结果，
# 异常信息就丢失了，这会导致程序在静默中失败，极难调试。

# === 正确用法 ===
# ✅ 在 try...except 块中调用 .result() 来捕获并处理异常
print("\n--- 正确用法：捕获并处理异常 ---")
with concurrent.futures.ThreadPoolExecutor() as executor:
    future = executor.submit(task_that_fails)
    print("任务已提交，现在尝试获取结果...")
    try:
        result = future.result()
        print(f"任务成功，结果: {result}")
    except ValueError as e:
        print(f"✅ 成功捕获到后台任务的异常: {e}")
# 解释为什么这样是对的:
# 调用 .result() 会重新引发任务中发生的异常，允许主线程的 try...except 块
# 捕获它。这是处理并发任务中错误的正确、健壮的方式。
```

### 🚀 Level 4: 实战应用（真实场景）

**场景：** 📜 魔法图书馆的古卷修复流水线

一座古老的魔法图书馆需要修复一批破损的古卷。修复流程分为两步：
1.  **净化 (Purification)**: 使用“净化之泉”清洗古卷，这是一个耗时较长的I/O操作（等待魔法能量渗透）。
2.  **转录 (Transcription)**: 对净化后的古卷内容进行高速魔法转录，这是一个CPU密集型操作（需要大量计算来解析符文）。

我们将使用 `concurrent.futures` 构建一个高效的流水线，用 `ThreadPoolExecutor` 处理净化，`ProcessPoolExecutor` 处理转录。

```python
import concurrent.futures
import time
import os

def purify_scroll(scroll_name):
    """(I/O密集型) 模拟净化古卷"""
    print(f"💧 [I/O线程-{os.getpid()}] 开始净化 '{scroll_name}'...")
    time.sleep(2)
    purified_content = f"'{scroll_name}' 的纯净内容"
    print(f"✨ [I/O线程-{os.getpid()}] '{scroll_name}' 净化完成！")
    return purified_content

def transcribe_runes(content):
    """(CPU密集型) 模拟转录符文"""
    print(f"✍️ [CPU进程-{os.getpid()}] 开始转录 '{content}'...")
    # 模拟大量计算
    n = 60_000_000
    _ = sum(i for i in range(n))
    transcribed_text = f"转录完成: {content}"
    print(f"📖 [CPU进程-{os.getpid()}] '{content}' 转录完成！")
    return transcribed_text

if __name__ == '__main__':
    scrolls_to_repair = ["火焰风暴之卷", "深度冻结之卷", "时空扭曲之卷"]
    
    print("--- 魔法图书馆古卷修复流水线启动 ---\n")
    start_time = time.time()

    # --- 阶段1: 使用线程池并发净化古卷 ---
    print("--- [阶段一] 开始并发净化 (I/O密集型) ---")
    purified_contents = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as purifier:
        # 使用 map 批量处理
        purified_contents = list(purifier.map(purify_scroll, scrolls_to_repair))
    
    print("\n--- [阶段一] 所有古卷净化完成! ---\n")
    
    # --- 阶段2: 使用进程池并行转录内容 ---
    print("--- [阶段二] 开始并行转录 (CPU密集型) ---")
    final_texts = []
    # os.cpu_count() or len(purified_contents) to avoid creating idle processes
    num_processes = min(os.cpu_count(), len(purified_contents))
    with concurrent.futures.ProcessPoolExecutor(max_workers=num_processes) as transcriber:
        final_texts = list(transcriber.map(transcribe_runes, purified_contents))
        
    end_time = time.time()
    
    print("\n--- 📜 所有古卷修复完成！ ---")
    for text in final_texts:
        print(f"- {text}")
        
    print(f"\n✨ 流水线总耗时: {end_time - start_time:.2f} 秒")

# 预期输出 (PID会变化，但能看出线程和进程的区别):
# --- 魔法图书馆古卷修复流水线启动 ---
#
# --- [阶段一] 开始并发净化 (I/O密集型) ---
# 💧 [I/O线程-12345] 开始净化 '火焰风暴之卷'...
# 💧 [I/O线程-12345] 开始净化 '深度冻结之卷'...
# 💧 [I/O线程-12345] 开始净化 '时空扭曲之卷'...
# ✨ [I/O线程-12345] '火焰风暴之卷' 净化完成！
# ✨ [I/O线程-12345] '深度冻结之卷' 净化完成！
# ✨ [I/O线程-12345] '时空扭曲之卷' 净化完成！
#
# --- [阶段一] 所有古卷净化完成! ---
#
# --- [阶段二] 开始并行转录 (CPU密集型) ---
# ✍️ [CPU进程-54321] 开始转录 ''火焰风暴之卷' 的纯净内容'...
# ✍️ [CPU进程-54322] 开始转录 ''深度冻结之卷' 的纯净内容'...
# ✍️ [CPU进程-54323] 开始转录 ''时空扭曲之卷' 的纯净内容'...
# 📖 [CPU进程-54321] ''火焰风暴之卷' 的纯净内容' 转录完成！
# 📖 [CPU进程-54322] ''深度冻结之卷' 的纯净内容' 转录完成！
# 📖 [CPU进程-54323] ''时空扭曲之卷' 的纯净内容' 转录完成！
#
# --- 📜 所有古卷修复完成！ ---
# - 转录完成: '火焰风暴之卷' 的纯净内容
# - 转录完成: '深度冻结之卷' 的纯净内容
# - 转录完成: '时空扭曲之卷' 的纯净内容
#
# ✨ 流水线总耗时: 5.89 秒 (远小于串行总和)
```

### 💡 记忆要点
- **要点1**: **`Executor` 是入口，`Future` 是凭证**。通过 `Executor` 提交任务，获得一个 `Future` 对象作为未来结果的凭证。
- **要点2**: **接口统一，按需切换**。`ThreadPoolExecutor` 和 `ProcessPoolExecutor` 拥有几乎相同的API，可以根据任务是I/O密集型还是CPU密集型，轻松地在它们之间切换。
- **要点3**: **结果虽迟但到，异常必须检查**。始终通过调用 `.result()` 来获取结果，并将其放在 `try...except` 块中，这是处理并发任务中潜在错误的唯一可靠方法。