好的，作为一名专业的JavaScript教育专家，我将为您生成关于“异步错误处理”的学习内容。

---

## 异步错误处理

### 🎯 核心概念
异步错误处理是专门用于捕获和管理在非阻塞操作（如API请求、定时器、文件读取）中发生的错误，确保程序在遇到意料之外的问题时能够优雅地响应，而不是直接崩溃。

### 📚 Level 1: 基础认知（30秒理解）
最基础的异步错误处理是使用 Promise 的 `.catch()` 方法。当一个 Promise 被拒绝（rejected）时，`.catch()` 里的回调函数就会被执行。

```javascript
// 创建一个立即失败的 Promise 来模拟异步错误
const failedPromise = new Promise((resolve, reject) => {
  // 模拟一个网络请求失败
  setTimeout(() => {
    reject(new Error("网络连接超时！"));
  }, 500);
});

console.log("启动异步操作...");

failedPromise
  .then(result => {
    // 这部分代码不会执行，因为 Promise 失败了
    console.log("成功:", result);
  })
  .catch(error => {
    // .catch() 捕获到了错误
    console.error("捕获到错误:", error.message);
  });

// 输出:
// 启动异步操作...
// (大约500毫秒后)
// 捕获到错误: 网络连接超时！
```

### 📈 Level 2: 核心特性（深入理解）

#### 特性1: 使用 `async/await` 和 `try...catch`
`async/await` 语法让我们能像写同步代码一样写异步代码，错误处理也变得更直观，可以使用经典的 `try...catch` 语句块来捕获 `await` 操作的错误。

```javascript
// 模拟一个可能失败的异步API调用
function fetchUserData() {
  return new Promise((resolve, reject) => {
    setTimeout(() => {
      // 随机决定成功或失败
      if (Math.random() > 0.5) {
        resolve({ id: 1, name: "Alice" });
      } else {
        reject(new Error("无法从服务器获取用户数据。"));
      }
    }, 1000);
  });
}

// 使用 async/await 和 try...catch 处理
async function displayUserData() {
  console.log("正在尝试获取用户数据...");
  try {
    const userData = await fetchUserData();
    console.log("获取成功:", userData);
  } catch (error) {
    console.error("在 displayUserData 中捕获到错误:", error.message);
  } finally {
    console.log("数据获取流程结束。");
  }
}

displayUserData();

// 可能的输出 1 (成功):
// 正在尝试获取用户数据...
// (1秒后)
// 获取成功: { id: 1, name: 'Alice' }
// 数据获取流程结束。

// 可能的输出 2 (失败):
// 正在尝试获取用户数据...
// (1秒后)
// 在 displayUserData 中捕获到错误: 无法从服务器获取用户数据。
// 数据获取流程结束。
```

#### 特性2: 处理多个 Promise 的错误 (`Promise.all` vs `Promise.allSettled`)
当需要处理多个并行的异步操作时，错误处理策略会有所不同。

- `Promise.all`: “一荣俱荣，一损俱损”。只要有一个 Promise 失败，整个 `Promise.all` 就会立即失败。
- `Promise.allSettled`: “永不言败”。它会等待所有 Promise 完成（无论成功或失败），然后返回一个包含每个 Promise 结果的对象数组。

```javascript
const promiseSuccess = Promise.resolve("任务1成功");
const promiseFailure = Promise.reject(new Error("任务2失败"));
const promiseSuccess2 = Promise.resolve("任务3成功");

async function runAllTasks() {
  console.log("--- 使用 Promise.all ---");
  try {
    const results = await Promise.all([promiseSuccess, promiseFailure, promiseSuccess2]);
    console.log("所有任务都成功了:", results); // 这行不会执行
  } catch (error) {
    console.error("Promise.all 捕获到错误:", error.message);
  }

  console.log("\n--- 使用 Promise.allSettled ---");
  const resultsSettled = await Promise.allSettled([promiseSuccess, promiseFailure, promiseSuccess2]);
  console.log("Promise.allSettled 的结果:");
  resultsSettled.forEach(result => {
    if (result.status === 'fulfilled') {
      console.log(`  - 成功: ${result.value}`);
    } else {
      console.log(`  - 失败: ${result.reason.message}`);
    }
  });
}

runAllTasks();

// 输出:
// --- 使用 Promise.all ---
// Promise.all 捕获到错误: 任务2失败
//
// --- 使用 Promise.allSettled ---
// Promise.allSettled 的结果:
//   - 成功: 任务1成功
//   - 失败: 任务2失败
//   - 成功: 任务3成功
```

### 🔍 Level 3: 对比学习（避免陷阱）
一个常见的陷阱是试图用 `try...catch` 来捕获不带 `await` 的 Promise 错误。`try...catch` 只能捕获同步代码或 `await` 表达式抛出的错误，而不能捕获 Promise 链内部的异步错误。

```javascript
function mightFail() {
  return new Promise((resolve, reject) => {
    setTimeout(() => reject(new Error("异步操作失败了！")), 500);
  });
}

console.log("=== 错误用法 ===");
// ❌ 错误：try...catch 无法捕获到 mightFail() 内部的异步错误
// 因为 mightFail() 立即返回一个 Promise 对象，并没有抛出同步错误。
// 错误在未来的某个时间点（500ms后）才发生，早已跳出了 try...catch 块。
try {
  mightFail(); 
  console.log("这个 Promise 已经启动，但错误还没发生。");
} catch (error) {
  // 这段代码永远不会执行
  console.error("错误用法捕获到了错误:", error.message);
}

// 需要一个延迟来让程序等待异步错误发生，否则脚本可能在错误抛出前就结束了。
setTimeout(() => {
  console.log("\n=== 正确用法 ===");
  // ✅ 正确：使用 async/await，错误会被 try...catch 捕获
  async function handleItRight() {
    try {
      await mightFail();
    } catch (error) {
      console.error("正确用法捕获到了错误:", error.message);
    }
  }
  handleItRight();
}, 1000);

// 输出:
// === 错误用法 ===
// 这个 Promise 已经启动，但错误还没发生。
// (控制台可能会报告一个 UnhandledPromiseRejectionWarning)
//
// (1秒后)
// === 正确用法 ===
// 正确用法捕获到了错误: 异步操作失败了！
```

### 🚀 Level 4: 实战应用（真实场景）
**🚀 科幻冒险：星际矿物探测器**

你正在驾驶一艘太空飞船，任务是扫描三颗小行星，寻找珍稀矿物。每颗小行星的扫描都是一次异步操作，可能会成功，也可能因为“能量护盾干扰”或“小行星带太密集”而失败。我们的探测器程序需要足够健壮，即使一次扫描失败，也要能继续尝试扫描其他小行星，并最终报告结果。

```javascript
// 模拟扫描一颗小行星，它可能成功也可能失败
function scanAsteroid(name) {
  console.log(`🛰️ 发送探测器前往小行星 ${name}...`);
  return new Promise((resolve, reject) => {
    const scanTime = Math.random() * 2000 + 500; // 随机扫描时间
    setTimeout(() => {
      const successChance = Math.random();
      if (successChance > 0.4) {
        const minerals = ['钛', '钻石', '超导矿石'][Math.floor(Math.random() * 3)];
        resolve(`在 ${name} 发现大量 ${minerals}!`);
      } else if (successChance > 0.2) {
        reject(new Error(`来自 ${name} 的能量护盾干扰，扫描失败！`));
      } else {
        reject(new Error(`小行星带过于密集，无法接近 ${name}！`));
      }
    }, scanTime);
  });
}

// 主控程序：启动星际探索任务
async function startExploration() {
  console.log("🚀 舰长，星际矿物探测任务启动！");
  const asteroids = ['C-53', 'X-7', 'Z-99'];
  const scanPromises = asteroids.map(name => scanAsteroid(name));

  // 我们使用 Promise.allSettled，因为我们想知道每一颗小行星的扫描结果，
  // 即使其中一些失败了也不想中断整个任务。
  const results = await Promise.allSettled(scanPromises);

  console.log("\n--- 任务报告 ---");
  let successfulScans = 0;
  
  results.forEach((result, index) => {
    const asteroidName = asteroids[index];
    if (result.status === 'fulfilled') {
      console.log(`✅ [${asteroidName}] 扫描成功: ${result.value}`);
      successfulScans++;
    } else {
      console.error(`❌ [${asteroidName}] 扫描失败: ${result.reason.message}`);
    }
  });

  console.log("\n--- 任务总结 ---");
  if (successfulScans > 0) {
    console.log(`🎉 任务部分成功！共在 ${successfulScans} 颗小行星上发现矿物。返航！`);
  } else {
    console.log("😭 所有扫描均失败。看来我们今天运气不佳，准备返航吧。");
  }
}

startExploration();
```

### 💡 记忆要点
- **`try...catch` 配 `await`**：在 `async` 函数中，使用 `try...catch` 包裹 `await` 表达式，是处理异步错误最直观的方式。
- **`.catch()` 是 Promise 的标配**：对于传统的 Promise 链，务必在链的末尾添加 `.catch()` 来捕获任何环节可能出现的错误。
- **`Promise.allSettled` 用于多任务**：当你需要执行多个独立的异步任务，并且关心每个任务的最终结果（无论成败）时，`Promise.allSettled` 是比 `Promise.all` 更安全、更合适的选择。

<!--
metadata:
  syntax: [async, await, try, catch, Promise]
  pattern: [error-handling, async-await, promise-chain]
  api: [Promise, Promise.reject, Promise.all, Promise.allSettled, console.log, setTimeout]
  concept: [asynchronous, error-handling, event-loop]
  difficulty: advanced
  dependencies: [js-sec-5-3-3]
  related: []
-->