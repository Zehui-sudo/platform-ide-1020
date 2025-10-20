好的，作为一名专业的JavaScript教育专家，我将为你生成关于 `Promise.all/race` 的教学内容。内容将严格遵循你的要求，确保清晰、实用、有趣。

---

## Promise.all/race

### 🎯 核心概念
`Promise.all` 和 `Promise.race` 用于处理多个Promise，解决了如何**并发**执行异步操作并根据不同需求（等待全部完成或仅等待第一个完成）来汇总结果的问题。

### 📚 Level 1: 基础认知（30秒理解）
`Promise.all` 像是在等所有朋友都到齐了才开饭，而 `Promise.race` 则是谁第一个跑到终点谁就赢了比赛。

```javascript
// 创建两个模拟异步操作的Promise
const promise1 = new Promise((resolve) => {
  setTimeout(() => resolve("任务1完成"), 200);
});

const promise2 = new Promise((resolve) => {
  setTimeout(() => resolve("任务2完成"), 500);
});

// Promise.all: 等待所有Promise都完成
Promise.all([promise1, promise2])
  .then((results) => {
    console.log("Promise.all 结果:", results); // 输出: ["任务1完成", "任务2完成"]
  });

// Promise.race: 只等待第一个完成的Promise
Promise.race([promise1, promise2])
  .then((result) => {
    console.log("Promise.race 结果:", result); // 输出: "任务1完成" (因为它更快)
  });
```

### 📈 Level 2: 核心特性（深入理解）

#### 特性1: `Promise.all` - 全都成功才成功（All or Nothing）
`Promise.all` 只有在所有输入的Promise都成功（resolved）时才会成功。只要有一个Promise失败（rejected），`Promise.all` 就会立即失败，并返回那个失败的Promise的原因。

```javascript
// 模拟一个会成功的下载任务
function createSuccessPromise(name, delay) {
  return new Promise((resolve) => {
    setTimeout(() => {
      console.log(`${name} 下载成功!`);
      resolve(`${name}的数据`);
    }, delay);
  });
}

// 模拟一个会失败的下载任务
function createFailurePromise(name, delay) {
  return new Promise((_, reject) => {
    setTimeout(() => {
      console.log(`${name} 下载失败!`);
      reject(`${name}的网络错误`);
    }, delay);
  });
}

// 场景1: 所有都成功
const allSuccessPromises = [
  createSuccessPromise('图片', 300),
  createSuccessPromise('音频', 500),
  createSuccessPromise('文档', 100)
];

Promise.all(allSuccessPromises)
  .then(results => console.log("✅ 全部成功，收到的数据:", results))
  .catch(error => console.error("❌ 不应该执行到这里:", error));


// 场景2: 其中一个失败
const oneFailurePromises = [
  createSuccessPromise('图片', 300),
  createFailurePromise('音频', 200), // 这个会最快失败
  createSuccessPromise('文档', 400)
];

Promise.all(oneFailurePromises)
  .then(results => console.log("✅ 不应该执行到这里:", results))
  .catch(error => console.error("❌ 其中一个失败，Promise.all立即失败:", error));
```

#### 特性2: `Promise.race` - 谁快谁赢（Winner Takes All）
`Promise.race` 会返回第一个“尘埃落定”（settled）的Promise的结果。这个Promise无论是成功（resolved）还是失败（rejected），`Promise.race` 都会采纳它的结果。

```javascript
function createPromise(name, delay, shouldSucceed = true) {
  return new Promise((resolve, reject) => {
    setTimeout(() => {
      if (shouldSucceed) {
        console.log(`${name} 第一个冲过终点! (成功)`);
        resolve(`${name}赢了!`);
      } else {
        console.log(`${name} 第一个冲过终点! (但失败了)`);
        reject(`${name}摔倒了!`);
      }
    }, delay);
  });
}

// 场景1: 最快的是一个成功的Promise
const fastestIsSuccess = [
  createPromise('慢悠悠的乌龟', 1000, true),
  createPromise('敏捷的兔子', 100, true),
  createPromise('沉睡的猫', 2000, true)
];

Promise.race(fastestIsSuccess)
  .then(winner => console.log("🏆 比赛结果:", winner))
  .catch(error => console.error("💥 比赛意外:", error));

// 场景2: 最快的是一个失败的Promise
const fastestIsFailure = [
  createPromise('稳健的大象', 500, true),
  createPromise('鲁莽的猎豹', 200, false), // 这个最快，但是会失败
  createPromise('飞翔的鹰', 600, true)
];

Promise.race(fastestIsFailure)
  .then(winner => console.log("🏆 比赛结果:", winner))
  .catch(error => console.error("💥 比赛意外:", error));
```

### 🔍 Level 3: 对比学习（避免陷阱）
一个常见的陷阱是忘记为`Promise.all`添加`.catch`处理。如果其中任何一个Promise失败，而你没有捕获这个错误，就会导致"Uncaught (in promise)"错误，可能让你的应用程序崩溃。

```javascript
function createAsyncTask(shouldFail = false) {
  return new Promise((resolve, reject) => {
    setTimeout(() => {
      if (shouldFail) {
        reject("数据库连接超时!");
      } else {
        resolve("数据加载成功");
      }
    }, 200);
  });
}

console.log("=== 错误用法 ===");
// ❌ 错误: 没有使用 .catch() 来处理潜在的失败
// 当 createAsyncTask(true) 失败时，会产生一个未捕获的Promise拒绝错误。
const promisesWithError = [
  createAsyncTask(),
  createAsyncTask(true), // 这个会失败
];

Promise.all(promisesWithError).then(results => {
  console.log("错误用法下的结果(永远不会执行):", results);
});
// 浏览器控制台会报错: Uncaught (in promise) 数据库连接超时!
console.error("❌ 错误用法: 如果没有.catch，当Promise.all失败时，错误将无法被捕获，可能导致程序异常。");


console.log("\n=== 正确用法 ===");
// ✅ 正确: 总是为Promise链添加 .catch() 来优雅地处理错误
const promisesForCorrectUsage = [
  createAsyncTask(),
  createAsyncTask(true), // 这个会失败
];

Promise.all(promisesForCorrectUsage)
  .then(results => {
    console.log("正确用法下的成功结果(不会执行):", results);
  })
  .catch(error => {
    console.log("✅ 正确用法: 成功捕获到了错误!", error);
  });
```

### 🚀 Level 4: 实战应用（真实场景）

**场景：🚀 太空探险家机器人大赛**

我们要举办一场机器人大赛，让几个机器人同时去探索不同的星球，并带回数据。
- **目标1 (`Promise.all`)**: 我们需要等待所有机器人都完成探索，集齐所有星球的数据后，才能宣布大赛圆满结束。
- **目标2 (`Promise.race`)**: 同时，我们要评选出“先锋奖”，奖励第一个完成探索并返回信号的机器人。

```javascript
// 定义机器人探索函数，返回一个Promise
// 每个机器人探索时间是随机的
function launchExplorerBot(botName, planet) {
  const explorationTime = Math.random() * 3000 + 500; // 随机探索时间 0.5-3.5秒
  console.log(`🤖 ${botName} 已发射，目标：${planet}星球！`);
  
  return new Promise((resolve, reject) => {
    setTimeout(() => {
      // 模拟10%的失败率
      if (Math.random() > 0.9) {
        console.log(`💥 ${botName} 在 ${planet} 遭遇小行星带，探索失败！`);
        reject(`${botName}信号丢失`);
      } else {
        console.log(`🛰️ ${botName} 成功从 ${planet} 返回数据！耗时: ${(explorationTime/1000).toFixed(2)}s`);
        resolve({
          bot: botName,
          planet: planet,
          data: `来自${planet}的土壤样本`
        });
      }
    }, explorationTime);
  });
}

// 创建机器人探险任务列表
const bots = [
  launchExplorerBot('AlphaBot', '火星'),
  launchExplorerBot('BetaBot', '木星'),
  launchExplorerBot('GammaBot', '土星')
];

// 目标1: 使用 Promise.all 等待所有机器人完成任务
console.log("\n--- [大赛监控中心] 等待所有机器人完成探索... ---");
Promise.all(bots)
  .then(results => {
    console.log("\n🎉🎉🎉 [大赛结果] 所有机器人都已返航！大赛圆满成功！");
    results.forEach(r => {
      console.log(`- ${r.bot} 带回了: ${r.data}`);
    });
  })
  .catch(error => {
    console.error(`\n🚨🚨🚨 [大赛警报] 出现意外! ${error}，大赛被迫中止！`);
  });

// 目标2: 使用 Promise.race 找出最快返回的机器人
console.log("\n--- [先锋奖评选] 谁是第一个返回信号的英雄？ ---");
Promise.race(bots)
  .then(firstBot => {
    console.log(`\n🏆🏆🏆 [先锋奖] 恭喜 ${firstBot.bot}！它第一个从 ${firstBot.planet} 返回信号，获得先锋奖！`);
  })
  .catch(error => {
    // 注意：即使race失败，all仍然可能在进行中
    console.warn(`\n💔💔💔 [先锋奖评选] ${error}！最快的机器人不幸失联了...`);
  });
```

### 💡 记忆要点
- **`Promise.all`**: “全家桶”，所有成员都成功，它才成功；一个失败，满盘皆输。返回一个包含所有结果的数组。
- **`Promise.race`**: “百米赛跑”，谁第一个到达终点（无论成功或失败），它就采纳谁的结果。
- **错误处理**: 永远不要忘记给 `Promise.all` 和 `Promise.race` 链条加上 `.catch()`，以防意外发生。

<!--
metadata:
  syntax: ["arrow-function", "const", "let"]
  pattern: ["promise-chain", "error-handling"]
  api: ["Promise.all", "Promise.race", "Promise", "setTimeout", "console.log", "Math.random"]
  concept: ["asynchronous-programming", "concurrency"]
  difficulty: intermediate
  dependencies: ["无"]
  related: ["js-sec-5-2-1", "js-sec-5-2-2"]
-->