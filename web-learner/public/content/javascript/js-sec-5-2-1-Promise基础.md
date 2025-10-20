## Promise基础

### 🎯 核心概念
Promise 是 JavaScript 中处理异步操作的解决方案，它就像一个“承诺”：代表一个未来才会知道结果的事件（通常是网络请求、文件读取等），让你能够以更清晰、更有序的方式处理成功或失败的结果，告别回调地狱。

### 📚 Level 1: 基础认知（30秒理解）
一个Promise就像一个外卖订单。你下单后（创建Promise），它处于“制作中”（pending）状态。一段时间后，外卖送到（fulfilled），或者订单被取消（rejected）。`.then()` 就是你拿到外卖后要做的事。

```javascript
// 创建一个外卖订单（Promise），承诺2秒后送到
const myOrder = new Promise((resolve, reject) => {
  console.log("👨‍🍳 厨房正在准备您的披萨...");
  setTimeout(() => {
    // 2秒后，披萨做好了！
    resolve("🍕 热腾腾的披萨"); 
  }, 2000);
});

console.log("🧾 订单已提交，等待厨房确认...");

// .then() 指定披萨送到后（Promise fulfilled）要做什么
myOrder.then((pizza) => {
  console.log(`耶！收到了我的 ${pizza}，准备开吃！`);
});

// 输出顺序:
// 1. "🧾 订单已提交，等待厨房确认..." (立即执行)
// 2. "👨‍🍳 厨房正在准备您的披萨..." (立即执行)
// 3. (等待2秒)
// 4. "耶！收到了我的 🍕 热腾腾的披萨，准备开吃！" (2秒后执行)
```

### 📈 Level 2: 核心特性（深入理解）

#### 特性1: 三种状态与结果处理
一个Promise实例有且仅有三种状态：
1.  **pending**: 初始状态，进行中。
2.  **fulfilled**: 操作成功完成。
3.  **rejected**: 操作失败。

状态一旦从 `pending` 变为 `fulfilled` 或 `rejected`，就不可再改变。`.then()` 处理成功，`.catch()` 处理失败。

```javascript
// 模拟一个可能会成功的任务
const successfulTask = new Promise((resolve, reject) => {
  console.log("开始执行一个【注定成功】的任务...");
  setTimeout(() => {
    resolve({ success: true, data: "一些重要数据" });
  }, 1000);
});

successfulTask
  .then(result => {
    console.log("✅ 成功:", result);
  })
  .catch(error => {
    console.log("❌ 失败:", error); // 这段代码不会执行
  });


// 模拟一个可能会失败的任务
const failedTask = new Promise((resolve, reject) => {
  console.log("开始执行一个【注定失败】的任务...");
  setTimeout(() => {
    reject(new Error("网络连接中断"));
  }, 2000);
});

failedTask
  .then(result => {
    console.log("✅ 成功:", result); // 这段代码不会执行
  })
  .catch(error => {
    // Error对象会打印出更详细的堆栈信息
    console.log("❌ 失败:", error.message); 
  });
```

#### 特性2: 链式调用 (Chaining)
`.then()` 或 `.catch()` 方法会返回一个新的Promise，这使得我们可以像链条一样将多个异步操作串联起来，前一个操作的成功结果会作为参数传递给下一个 `.then()`。

```javascript
// 模拟一个多步骤的操作：1. 获取用户ID -> 2. 根据ID获取用户信息
function getUserId() {
  return new Promise((resolve) => {
    console.log("步骤1: 开始获取用户ID...");
    setTimeout(() => {
      const userId = 123;
      console.log("步骤1: 成功获取用户ID:", userId);
      resolve(userId);
    }, 1000);
  });
}

function getUserInfo(id) {
  return new Promise((resolve) => {
    console.log(`步骤2: 开始根据ID [${id}] 获取用户信息...`);
    setTimeout(() => {
      const userInfo = { name: "Alice", age: 30 };
      console.log("步骤2: 成功获取用户信息:", userInfo);
      resolve(userInfo);
    }, 1000);
  });
}

// 链式调用
getUserId()
  .then(id => {
    // 从上一个 .then() 接收到 id
    // 返回一个新的 Promise，这个 Promise 的结果将被下一个 .then() 接收
    return getUserInfo(id);
  })
  .then(info => {
    // 从上一个 .then() (即 getUserInfo) 接收到 info
    console.log("🎉 最终结果:", `欢迎, ${info.name}!`);
  })
  .catch(error => {
    console.error("处理流程出现错误:", error);
  });
```

### 🔍 Level 3: 对比学习（避免陷阱）
一个常见的错误是“Promise金字塔”，即在 `.then()` 回调中嵌套另一个Promise调用，而不是使用优雅的链式调用。这会使代码难以阅读和维护。

```javascript
console.log("=== 错误用法 ===");
// ❌ 错误做法：在 .then() 中嵌套，形成回调地狱
function fetchUserDataNested() {
  return new Promise(resolve => setTimeout(() => resolve(101), 500));
}
function fetchUserPostsNested(userId) {
  return new Promise(resolve => setTimeout(() => resolve([`Post A by ${userId}`, `Post B by ${userId}`]), 500));
}

fetchUserDataNested().then(userId => {
  console.log(`获取到用户ID: ${userId}`);
  // 嵌套的 .then() 使代码向右缩进，难以阅读
  fetchUserPostsNested(userId).then(posts => {
    console.log("获取到用户文章:", posts);
  });
});
// 解释：这种写法虽然能工作，但如果再多几层异步操作，就会形成“回调地狱”（Pyramid of Doom），
// 错误处理也变得复杂，每一层都可能需要自己的 .catch()。


// 等待上面的代码执行完
setTimeout(() => {
  console.log("\n=== 正确用法 ===");
  // ✅ 正确做法：使用扁平化的链式调用
  function fetchUserDataChained() {
    return new Promise(resolve => setTimeout(() => resolve(202), 500));
  }
  function fetchUserPostsChained(userId) {
    return new Promise(resolve => setTimeout(() => resolve([`Post X by ${userId}`, `Post Y by ${userId}`]), 500));
  }

  fetchUserDataChained()
    .then(userId => {
      console.log(`获取到用户ID: ${userId}`);
      // 关键：返回下一个Promise，而不是嵌套它
      return fetchUserPostsChained(userId);
    })
    .then(posts => {
      // 这个 .then() 处理的是 fetchUserPostsChained 的结果
      console.log("获取到用户文章:", posts);
    })
    .catch(error => {
      // 单一的 .catch() 可以捕获链条中任何一个环节的错误
      console.error("链式调用中发生错误:", error);
    });
  // 解释：代码是扁平的，从上到下执行，非常清晰。
  // 任何一步的失败都会被最后的 .catch() 捕获，便于统一错误处理。
}, 2000);

```

### 🚀 Level 4: 实战应用（真实场景）
**场景：🚀 科幻冒险 - 发射无人深空探测器**

我们来模拟一个发射探测器的多阶段任务。每个阶段都是异步的，并且有可能失败。只有前一阶段成功，才能进入下一阶段。

```javascript
// 模拟探测器发射流程

/**
 * 阶段1: 系统自检
 * @returns {Promise<string>}
 */
function systemCheck() {
  return new Promise((resolve, reject) => {
    console.log("🚀 [阶段1] 开始系统自检...");
    setTimeout(() => {
      if (Math.random() > 0.1) { // 90% 成功率
        resolve("✅ 系统自检通过，所有参数正常。");
      } else {
        reject("❌ 系统自检失败：主引擎控制器无响应！");
      }
    }, 1000);
  });
}

/**
 * 阶段2: 燃料加注
 * @param {string} checkResultMessage - 上一阶段的结果信息
 * @returns {Promise<string>}
 */
function fuelEngines(checkResultMessage) {
  return new Promise((resolve, reject) => {
    console.log(checkResultMessage); // 打印上一阶段的信息
    console.log("⛽ [阶段2] 开始加注液氢燃料...");
    setTimeout(() => {
      if (Math.random() > 0.15) { // 85% 成功率
        resolve("✅ 燃料加注完成，引擎已预热。");
      } else {
        reject("❌ 燃料加注失败：检测到燃料泄漏！");
      }
    }, 1500);
  });
}

/**
 * 阶段3: 启动点火程序
 * @param {string} fuelResultMessage - 上一阶段的结果信息
 * @returns {Promise<string>}
 */
function startIgnition(fuelResultMessage) {
  return new Promise((resolve) => {
    console.log(fuelResultMessage);
    console.log("🔥 [阶段3] 启动主引擎点火程序... 倒计时 3... 2... 1...");
    setTimeout(() => {
      resolve("🛰️ 点火成功！探测器已升空，飞向星辰大海！");
    }, 1000);
  });
}

// --- 执行发射任务 ---
console.log("--- 探测器发射任务启动 ---");
systemCheck()
  .then(result1 => fuelEngines(result1))
  .then(result2 => startIgnition(result2))
  .then(finalMessage => {
    console.log("🎉🎉🎉 任务成功! 🎉🎉🎉");
    console.log(finalMessage);
  })
  .catch(errorMessage => {
    console.error("💥💥💥 任务失败! 💥💥💥");
    console.error("原因:", errorMessage);
    console.log("地面控制中心正在分析故障...");
  });

// 提示：可以多次运行此代码块，看看不同的成功或失败结果！
```

### 💡 记忆要点
- **承诺未来**: Promise 是一个代表异步操作最终完成或失败的对象。
- **状态机**: 状态从 `pending` 只能变为 `fulfilled` (成功) 或 `rejected` (失败)，且状态一旦改变就无法再次更改。
- **链式调用**: 使用 `.then()` 处理成功，`.catch()` 处理失败，并通过返回新的Promise来构建清晰的、扁平化的异步流程。

<!--
metadata:
  syntax: ["promise", "function", "arrow-function"]
  pattern: ["promise-chain", "error-handling"]
  api: ["Promise", "setTimeout", "console.log", "Math.random"]
  concept: ["asynchronous", "event-loop"]
  difficulty: intermediate
  dependencies: ["js-sec-5-1-1"]
  related: ["js-sec-5-2-2", "js-sec-5-3-1"]
-->