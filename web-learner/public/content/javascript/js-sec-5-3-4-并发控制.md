好的，作为一名专业的JavaScript教育专家，我将为您生成关于“并发控制”的学习内容。内容将严格遵循您的要求，结构清晰，代码完整可运行，并采用生动有趣的实战场景。

---

## 并发控制

### 🎯 核心概念
并发控制是指在处理大量异步任务时，**主动限制同时执行的任务数量**，以防止因瞬间产生过多请求或计算而导致系统资源耗尽、API限流或程序崩溃。

### 📚 Level 1: 基础认知（30秒理解）
想象一下，你有5个需要下载的文件。如果不加控制，它们会同时开始下载，可能会占满你的所有带宽。并发控制就像是创建一个下载管理器，只允许同时下载2个，下载完一个再开始下一个。

下面的代码模拟了5个任务，每个任务需要1秒。在没有并发控制的情况下，它们几乎同时开始和结束。

```javascript
// 模拟一个耗时任务，例如API请求或文件下载
function createTask(id) {
  return () => {
    console.log(`[${new Date().toLocaleTimeString()}] 任务 ${id} 开始执行...`);
    return new Promise(resolve => {
      setTimeout(() => {
        console.log(`[${new Date().toLocaleTimeString()}] ✅ 任务 ${id} 执行完毕!`);
        resolve(`任务 ${id} 的结果`);
      }, 1000); // 每个任务耗时1秒
    });
  };
}

// 创建5个任务
const tasks = [
  createTask(1),
  createTask(2),
  createTask(3),
  createTask(4),
  createTask(5),
];

console.log("💥 如果不控制并发，所有任务会立即启动：");

// 同时启动所有任务
tasks.forEach(task => task());

// 输出结果会显示，所有任务几乎在同一时间开始，然后在1秒后几乎同时结束。
// [HH:MM:SS] 任务 1 开始执行...
// [HH:MM:SS] 任务 2 开始执行...
// [HH:MM:SS] 任务 3 开始执行...
// [HH:MM:SS] 任务 4 开始执行...
// [HH:MM:SS] 任务 5 开始执行...
// (等待1秒)
// [HH:MM:SS] ✅ 任务 1 执行完毕!
// [HH:MM:SS] ✅ 任务 2 执行完毕!
// [HH:MM:SS] ✅ 任务 3 执行完毕!
// [HH:MM:SS] ✅ 任务 4 执行完毕!
// [HH:MM:SS] ✅ 任务 5 执行完毕!
```

### 📈 Level 2: 核心特性（深入理解）
为了实现有效的并发控制，我们需要一个调度器来管理任务队列和正在运行的任务。

#### 特性1: 任务队列与并发限制
我们可以创建一个函数，它接收一个任务数组和一个并发限制数。它会先启动达到限制数量的任务，然后每当一个任务完成时，就从队列中取出一个新任务来执行，直到所有任务完成。

```javascript
// 模拟一个异步任务
functioncreateAsyncTask(id) {
  const duration = Math.floor(Math.random() * 500) + 500; // 随机耗时 0.5-1秒
  return () => new Promise(resolve => {
    console.log(`[${new Date().toLocaleTimeString()}] 任务 ${id} 开始 (预计耗时: ${duration}ms)`);
    setTimeout(() => {
      console.log(`[${new Date().toLocaleTimeString()}] ✅ 任务 ${id} 完成`);
      resolve(id);
    }, duration);
  });
}

// 并发控制器
async function runWithConcurrency(tasks, limit) {
  const results = [];
  const running = []; // 存储正在运行的任务
  const queue = [...tasks]; // 任务队列

  function runNext() {
    // 当队列为空或正在运行的任务达到上限时，不再启动新任务
    if (queue.length === 0 || running.length >= limit) {
      return;
    }

    const task = queue.shift();
    const promise = task().then(result => {
      // 任务完成后，从 running 数组中移除
      const index = running.indexOf(promise);
      if (index > -1) {
        running.splice(index, 1);
      }
      results.push(result);
      // 启动下一个任务
      runNext();
    });

    running.push(promise);
  }

  // 初始启动任务，填满并发窗口
  for (let i = 0; i < limit && i < tasks.length; i++) {
    runNext();
  }

  // 等待所有任务完成
  // 通过检查队列和正在运行的任务来判断
  return new Promise(resolve => {
    const interval = setInterval(() => {
      if (queue.length === 0 && running.length === 0) {
        clearInterval(interval);
        resolve(results.sort((a, b) => a - b)); // 排序以方便查看
      }
    }, 100);
  });
}

const tasks = Array.from({ length: 8 }, (_, i) => createAsyncTask(i + 1));
const concurrencyLimit = 3;

console.log(`🚀 启动任务调度器，并发限制为: ${concurrencyLimit}`);

runWithConcurrency(tasks, concurrencyLimit).then(finalResults => {
  console.log("\n🎉 所有任务都已完成！");
  console.log("任务执行结果:", finalResults);
});

// 输出会显示，始终最多只有3个任务在同时运行。
```

#### 特性2: 动态添加任务
一个健壮的并发控制器应该允许在运行时动态添加新任务。我们可以将其封装成一个类，使其更易于管理。

```javascript
class ConcurrencyController {
  constructor(limit) {
    this.limit = limit;
    this.queue = [];
    this.runningCount = 0;
    console.log(`控制器已创建，并发限制为 ${this.limit}`);
  }

  // 添加任务到队列
  addTask(task) {
    return new Promise((resolve, reject) => {
      this.queue.push({ task, resolve, reject });
      this.tryRunNext();
    });
  }

  // 尝试执行下一个任务
  tryRunNext() {
    if (this.runningCount < this.limit && this.queue.length > 0) {
      const { task, resolve, reject } = this.queue.shift();
      this.runningCount++;
      console.log(`[${new Date().toLocaleTimeString()}] 启动新任务... 当前运行数: ${this.runningCount}`);
      
      task()
        .then(resolve, reject)
        .finally(() => {
          this.runningCount--;
          console.log(`[${new Date().toLocaleTimeString()}] 一个任务完成。当前运行数: ${this.runningCount}`);
          this.tryRunNext();
        });
    }
  }
}

// 模拟任务
function createDynamicTask(id) {
  const duration = Math.floor(Math.random() * 1000) + 500;
  return () => new Promise(resolve => {
    console.log(`  -> 任务 ${id} 执行中 (耗时 ${duration}ms)`);
    setTimeout(() => resolve(`任务 ${id} 结果`), duration);
  });
}

const controller = new ConcurrencyController(2);

// 初始添加3个任务
console.log("--- 初始添加3个任务 ---");
controller.addTask(createDynamicTask(1)).then(res => console.log(`✅ ${res}`));
controller.addTask(createDynamicTask(2)).then(res => console.log(`✅ ${res}`));
controller.addTask(createDynamicTask(3)).then(res => console.log(`✅ ${res}`));

// 1秒后，动态添加更多任务
setTimeout(() => {
  console.log("\n--- 动态添加2个新任务 ---");
  controller.addTask(createDynamicTask(4)).then(res => console.log(`✅ ${res}`));
  controller.addTask(createDynamicTask(5)).then(res => console.log(`✅ ${res}`));
}, 1000);
```

### 🔍 Level 3: 对比学习（避免陷阱）
在处理大量异步操作时，不使用并发控制可能会导致灾难性后果。

```javascript
// 模拟一个会消耗资源的API请求
function mockApiRequest(id) {
  return new Promise(resolve => {
    console.log(`发起请求 ${id}...`);
    // 模拟网络延迟
    setTimeout(() => {
      resolve(`数据 ${id}`);
    }, 800);
  });
}

const requestIds = Array.from({ length: 10 }, (_, i) => i + 1);

async function runComparison() {
  console.log("=== 错误用法 ===");
  // ❌ 错误：使用 Promise.all 一次性发起所有请求
  // 这会导致在短时间内创建大量网络连接，可能超出浏览器或服务器的限制。
  console.log("💥 警告: 即将同时发起 10 个请求！");
  try {
    const results = await Promise.all(requestIds.map(id => mockApiRequest(id)));
    console.log("所有请求在几乎同一时间完成:", results.length, "个");
  } catch (error) {
    console.error("请求失败:", error);
  }

  await new Promise(r => setTimeout(r, 2000)); // 等待2秒，方便观察

  console.log("\n\n=== 正确用法 ===");
  // ✅ 正确：使用并发控制器，限制同时最多只有3个请求
  console.log("👍 优化: 使用并发控制，每次最多发起 3 个请求。");
  
  class RequestScheduler {
    constructor(limit) {
      this.limit = limit;
      this.queue = [];
      this.runningCount = 0;
    }
    
    add(requestFn) {
      return new Promise((resolve, reject) => {
        this.queue.push({ requestFn, resolve, reject });
        this.tryNext();
      });
    }

    tryNext() {
      if (this.runningCount < this.limit && this.queue.length > 0) {
        const { requestFn, resolve, reject } = this.queue.shift();
        this.runningCount++;
        console.log(`  [调度器] 批准一个新请求。当前并发数: ${this.runningCount}`);
        requestFn()
          .then(resolve, reject)
          .finally(() => {
            this.runningCount--;
            this.tryNext();
          });
      }
    }
  }

  const scheduler = new RequestScheduler(3);
  const promises = requestIds.map(id => scheduler.add(() => mockApiRequest(id)));
  const finalResults = await Promise.all(promises);
  console.log("所有请求在控制下有序完成:", finalResults.length, "个");
}

runComparison();
```

### 🚀 Level 4: 实战应用（真实场景）
**场景：🚀 机器人军团的火星探索任务**

你是指挥官，需要派遣一支由10个机器人组成的军团去火星执行探索任务。但你的“量子通讯站”带宽有限，一次最多只能同时与3个机器人保持实时连接和指令下达。你需要一个任务调度系统来智能地管理整个军团。

```javascript
// 机器人探索任务的模拟
class MarsRover {
  constructor(name) {
    this.name = name;
  }

  // 模拟一个复杂的、多阶段的探索任务
  async explore() {
    console.log(`🤖 ${this.name}: 任务启动，离开着陆点...`);
    
    await this.performTask("分析土壤样本", 1000 + Math.random() * 500);
    await this.performTask("拍摄全景照片", 1000 + Math.random() * 500);
    await this.performTask("寻找水源迹象", 1500 + Math.random() * 500);

    const discoveries = ["奇特的蓝色晶体", "远古生物化石", "一个废弃的咖啡杯"];
    const discovery = discoveries[Math.floor(Math.random() * discoveries.length)];
    
    console.log(`✨ ${this.name}: 任务完成！重大发现: ${discovery}!`);
    return `${this.name} 报告: ${discovery}`;
  }

  // 辅助函数，模拟执行单个子任务
  performTask(taskName, duration) {
    console.log(`  🛰️  ${this.name}: 正在执行 -> ${taskName}...`);
    return new Promise(resolve => setTimeout(resolve, duration));
  }
}

// 并发控制器
async function deployFleet(rovers, limit) {
  console.log(`--- 指挥中心: 启动火星部署！通讯带宽限制: ${limit} ---`);
  const taskQueue = [...rovers];
  const activeTasks = [];
  const results = [];

  const runNext = async () => {
    if (taskQueue.length === 0) return;

    const rover = taskQueue.shift();
    const taskPromise = rover.explore().then(result => {
      results.push(result);
      // 当一个任务完成后，从活动任务中移除它，并尝试启动下一个
      activeTasks.splice(activeTasks.indexOf(taskPromise), 1);
      return runNext();
    });
    activeTasks.push(taskPromise);
  };

  // 初始部署，填满带宽
  const initialDeploy = Array.from({ length: Math.min(limit, rovers.length) }, runNext);
  await Promise.all(initialDeploy.concat(activeTasks));
  
  return results;
}

// --- 任务开始 ---
const roverNames = ["勇气号", "机遇号", "好奇号", "毅力号", "祝融号", "探索者1号", "先锋号", "开拓者", "守护者", "发现号"];
const fleet = roverNames.map(name => new MarsRover(name));

// 以3个并发的限制部署整个机器人舰队
deployFleet(fleet, 3).then(missionReports => {
  console.log("\n\n--- 任务简报 ---");
  console.log("所有机器人均已完成探索任务！");
  missionReports.forEach(report => console.log(`- ${report}`));
  console.log("--- 指挥中心: 火星任务圆满成功！---");
});
```

### 💡 记忆要点
- **控制流量**: 并发控制的核心是变“一拥而上”为“有序排队”，防止系统因瞬时压力过大而崩溃。
- **池化思想**: 维护一个固定大小的“执行池”，任务来了先进等待队列，池里有空位了再进去执行。
- **Promise是关键**: 利用 Promise 的链式调用和状态变化，是实现优雅并发控制的基础。

<!--
metadata:
  syntax: [async, await, class, function, Promise]
  pattern: [async-await, promise-chain, queue]
  api: [Promise, setTimeout, console.log, Array.map]
  concept: [asynchronous, concurrency, task-queue, event-loop]
  difficulty: advanced
  dependencies: [无]
  related: [js-sec-5-3-2]
-->