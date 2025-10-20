## await表达式

### 🎯 核心概念
`await` 表达式用于暂停一个 `async` 函数的执行，等待一个 `Promise` 被解决（resolved）或拒绝（rejected），然后恢复函数的执行并返回 `Promise` 的结果。它使得异步代码的写法看起来和同步代码一样直观、易于理解。

### 📚 Level 1: 基础认知（30秒理解）
`await` 就像在对一个耗时操作说：“嘿，我等你一下，你弄好了再告诉我结果，我再继续往下走。”

```javascript
// 模拟一个需要2秒才能完成的下载任务
function simulateDownload() {
  console.log("🚀 开始下载文件...");
  return new Promise(resolve => {
    setTimeout(() => {
      resolve("✅ 文件下载完成！");
    }, 2000); // 模拟2秒的延迟
  });
}

// 必须在 async 函数中使用 await
async function getFile() {
  console.log("准备调用下载函数...");
  const result = await simulateDownload(); // 程序会在这里暂停，直到Promise完成
  console.log("下载函数执行完毕！");
  console.log("收到的结果:", result);
}

getFile();
// 输出顺序:
// 准备调用下载函数...
// 🚀 开始下载文件...
// (等待约2秒)
// 下载函数执行完毕！
// 收到的结果: ✅ 文件下载完成！
```

### 📈 Level 2: 核心特性（深入理解）

#### 特性1: 获取Promise的解决值
`await` 会“解包”Promise，直接返回它所携带的解决值（resolved value）。你不需要再使用 `.then()` 来获取结果。

```javascript
// 模拟一个API请求，该请求会返回一个用户信息对象
function fetchUserProfile() {
  return new Promise(resolve => {
    setTimeout(() => {
      resolve({ name: "Alice", level: 99 });
    }, 1000);
  });
}

async function displayUser() {
  console.log("正在获取用户信息...");
  // await直接拿到了Promise中的{ name: "Alice", level: 99 }对象
  const user = await fetchUserProfile();
  console.log(`欢迎回来, ${user.name}! 你的等级是 ${user.level}。`);
}

displayUser();
// 输出:
// 正在获取用户信息...
// (等待1秒)
// 欢迎回来, Alice! 你的等级是 99。
```

#### 特性2: 使用 try...catch 处理拒绝的Promise
如果 `await` 等待的 `Promise` 被拒绝（rejected），它会抛出一个错误。我们可以像处理同步代码的错误一样，使用 `try...catch` 语句来捕获这个错误。

```javascript
// 模拟一个会失败的API请求
function unstableApiRequest() {
  return new Promise((resolve, reject) => {
    setTimeout(() => {
      // 模拟一个随机失败
      if (Math.random() > 0.5) {
        resolve("🎉 数据获取成功！");
      } else {
        reject(new Error("💥 网络连接中断！"));
      }
    }, 1000);
  });
}

async function fetchData() {
  try {
    console.log("尝试从不稳定的API获取数据...");
    const data = await unstableApiRequest();
    console.log("成功信息:", data);
  } catch (error) {
    console.error("捕获到错误:", error.message);
  } finally {
    console.log("--- 请求结束 ---");
  }
}

fetchData();
// 可能的输出 1:
// 尝试从不稳定的API获取数据...
// (等待1秒)
// 成功信息: 🎉 数据获取成功！
// --- 请求结束 ---

// 可能的输出 2:
// 尝试从不稳定的API获取数据...
// (等待1秒)
// 捕获到错误: 💥 网络连接中断！
// --- 请求结束 ---
```

### 🔍 Level 3: 对比学习（避免陷阱）
一个最常见的错误就是尝试在非 `async` 函数的顶层作用域使用 `await`。

```javascript
// 完整的对比示例，包含所有必要的变量定义
console.log("=== 错误用法 ===");
// ❌ 展示常见错误
function simulateTask() {
  return new Promise(resolve => setTimeout(() => resolve("任务完成"), 500));
}

// 下面的代码会直接导致 SyntaxError: await is only valid in async functions and the top level bodies of modules
// 为了让整个脚本能运行，我们注释掉这部分错误代码，并用文字说明
/*
  console.log("准备开始任务...");
  const result = await simulateTask(); // 语法错误！
  console.log(result);
*/
console.error("错误原因：`await` 只能在 `async` 函数内部或模块的顶层使用。在普通函数中直接使用会导致语法错误。");


console.log("\n=== 正确用法 ===");
// ✅ 展示正确做法
// 将 `await` 包装在一个 async 函数中
async function runTask() {
  function simulateCorrectTask() {
    return new Promise(resolve => setTimeout(() => resolve("✅ 正确的任务完成"), 500));
  }
  
  console.log("准备开始正确的任务...");
  const result = await simulateCorrectTask(); // 正确！在async函数内部使用
  console.log(result);
}

runTask();
// 解释为什么这样是对的
console.log("正确原因：我们将 `await` 表达式放在了 `async` 关键字声明的函数 `runTask` 内部，这完全符合语法规则。");
```

### 🚀 Level 4: 实战应用（真实场景）

**🚀 科幻冒险场景：星际飞船着陆序列**

你是一艘星际飞船的AI，在着陆到一个未知星球前，必须按顺序执行一系列检查。每个检查都是一个异步操作，只有前一个成功完成，才能进行下一个。`await` 在这里完美地保证了操作的顺序性。

```javascript
// 模拟各种异步检查任务，每个任务耗时不同
function simulateSystemCheck(systemName, delay) {
  console.log(`...开始检查 [${systemName}] 系统...`);
  return new Promise(resolve => {
    setTimeout(() => {
      console.log(`✅ [${systemName}] 系统正常!`);
      resolve(true);
    }, delay);
  });
}

// 模拟一个可能失败的检查
function scanForLifeForms(delay) {
  console.log(`...正在扫描生命信号...`);
  return new Promise((resolve, reject) => {
    setTimeout(() => {
      if (Math.random() > 0.2) { // 80% 概率成功
        console.log("👽 未发现敌对生命信号。安全！");
        resolve("安全");
      } else {
        console.error("🚨 警告！侦测到高能量读数！可能是危险生物！");
        reject("危险生物警告");
      }
    }, delay);
  });
}

// 主着陆流程
async function startLandingSequence() {
  try {
    console.log("--- 🚀 开始执行着陆序列 ---");

    // await确保了检查是按顺序一个接一个执行的
    await simulateSystemCheck("引擎冷却", 1000);
    await simulateSystemCheck("护盾校准", 1500);
    await simulateSystemCheck("大气成分分析", 2000);
    
    // 处理可能失败的扫描
    const scanResult = await scanForLifeForms(1200);
    console.log(`扫描结果: ${scanResult}。继续着陆流程...`);

    console.log("--- ✨ 所有检查通过！飞船准备着陆！---");
    
  } catch (error) {
    console.error(`--- ❌ 着陆序列中断！原因: ${error} ---`);
    console.log("--- 启动紧急规避程序！撤离当前空域！---");
  }
}

// 启动AI
startLandingSequence();
```

### 💡 记忆要点
- **要点1**：`await` 必须在 `async` 函数中使用，否则会报语法错误。
- **要点2**：`await` 会暂停 `async` 函数的执行，但不会阻塞整个程序的运行。
- **要点3**：使用 `try...catch` 结构来优雅地处理 `await` 可能遇到的 `Promise` 拒绝（rejection）。

<!--
metadata:
  syntax: [await, async]
  pattern: [async-await, error-handling]
  api: [Promise, setTimeout, console.log, Math.random]
  concept: [event-loop, promise]
  difficulty: advanced
  dependencies: [无]
  related: [js-sec-5-3-1]
-->