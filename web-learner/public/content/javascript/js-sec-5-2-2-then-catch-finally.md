好的，作为一名专业的JavaScript教育专家，我将为您生成关于 "then/catch/finally" 的教学内容。

---

## then/catch/finally

### 🎯 核心概念
`then/catch/finally` 是 Promise 对象的方法，它们提供了一种优雅、可控的方式来处理异步操作的结果——无论是成功、失败，还是最终完成。

### 📚 Level 1: 基础认知（30秒理解）
想象你在网上订了一份披萨（一个异步操作）。`.then()` 就是你拿到披萨后要做的事（比如，开心地吃掉）。

```javascript
// 创建一个模拟网络请求的Promise，它会在1秒后成功
const orderPizzaPromise = new Promise((resolve, reject) => {
  console.log("正在下单披萨...");
  setTimeout(() => {
    // 模拟成功，并返回结果
    resolve("热腾腾的玛格丽特披萨🍕");
  }, 1000);
});

// 使用 .then() 来处理成功的结果
orderPizzaPromise.then(pizza => {
  console.log("订单成功！我收到了: " + pizza);
  console.log("开吃！");
});

// 输出:
// 正在下单披萨...
// (1秒后)
// 订单成功！我收到了: 热腾腾的玛格丽特披萨🍕
// 开吃！
```

### 📈 Level 2: 核心特性（深入理解）

#### 特性1: 链式调用 (Chaining)
`.then()` 和 `.catch()` 会返回一个新的 Promise，这使得我们可以像链条一样将多个异步操作串联起来。前一个 `.then()` 的返回值会作为下一个 `.then()` 的输入。

```javascript
// 模拟一个多步骤的烹饪过程
new Promise((resolve, reject) => {
  console.log("第一步：准备食材...");
  setTimeout(() => resolve("切好的蔬菜"), 1000);
})
.then(ingredients => {
  console.log(`拿到了: ${ingredients}。`);
  console.log("第二步：开始烹饪...");
  // 返回一个新的值给下一个.then()
  return `${ingredients} 和 炒锅`; 
})
.then(toolsAndIngredients => {
  console.log(`现在我们有: ${toolsAndIngredients}。`);
  console.log("第三步：装盘！");
  return "一盘美味的炒蔬菜";
})
.then(dish => {
  console.log(`任务完成！我们做好了: ${dish} 🍽️`);
});

// 输出:
// 第一步：准备食材...
// (1秒后)
// 拿到了: 切好的蔬菜。
// 第二步：开始烹饪...
// 现在我们有: 切好的蔬菜 和 炒锅。
// 第三步：装盘！
// 任务完成！我们做好了: 一盘美味的炒蔬菜 🍽️
```

#### 特性2: 错误捕获与最终执行
`.catch()` 用于捕获 Promise 链中任何地方发生的错误（rejection）。`.finally()` 里的代码则无论 Promise 成功还是失败，都一定会执行，非常适合做一些清理工作。

```javascript
// 模拟一个可能会失败的操作
const mightFailPromise = new Promise((resolve, reject) => {
  console.log("正在尝试一个危险操作...");
  setTimeout(() => {
    // 模拟一个随机的成功或失败
    if (Math.random() > 0.5) {
      resolve("操作成功！获得了宝藏！");
    } else {
      reject(new Error("操作失败！触发了陷阱！"));
    }
  }, 1000);
});

mightFailPromise
  .then(successMessage => {
    console.log("成功回调:", successMessage);
  })
  .catch(error => {
    console.error("失败回调:", error.message);
  })
  .finally(() => {
    console.log("最终操作: 无论如何，都要记录本次操作。");
  });

// 可能的输出 1 (成功):
// 正在尝试一个危险操作...
// (1秒后)
// 成功回调: 操作成功！获得了宝藏！
// 最终操作: 无论如何，都要记录本次操作。

// 可能的输出 2 (失败):
// 正在尝试一个危险操作...
// (1秒后)
// 失败回调: 操作失败！触发了陷阱！
// 最终操作: 无论如何，都要记录本次操作。
```

### 🔍 Level 3: 对比学习（避免陷阱）
一个常见的误区是使用 `.then` 的第二个参数来处理错误，而不是使用 `.catch`。这会使错误处理变得不彻底。

```javascript
console.log("=== 错误用法 ===");
// ❌ 错误做法：使用 .then(null, onRejected)
// 这种方式无法捕获第一个 .then() 成功回调内部抛出的新错误
new Promise((resolve, reject) => {
  resolve("一切正常");
})
.then(
  result => {
    console.log("成功回调执行:", result);
    // 在成功回调中手动抛出一个新错误
    throw new Error("成功回调里出了个新问题！");
  },
  error => {
    // 这个错误处理函数永远不会被调用
    console.error("这个处理函数不会执行，因为Promise是成功的", error.message);
  }
)
.then(() => {
    console.log("这个 then 也不会执行");
});
// 最终，这个错误会变成未捕获的异常 (Uncaught Error)


setTimeout(() => {
  console.log("\n=== 正确用法 ===");
  // ✅ 正确做法：使用 .catch()
  // .catch() 可以捕获它前面所有 .then() 中发生的任何错误
  new Promise((resolve, reject) => {
    resolve("一切正常");
  })
  .then(result => {
    console.log("成功回调执行:", result);
    // 同样，在成功回调中手动抛出一个新错误
    throw new Error("成功回调里出了个新问题！");
  })
  .catch(error => {
    // 这个错误被 .catch() 成功捕获！
    console.error("错误被 .catch() 捕获:", error.message);
  });
}, 1000);

// 输出:
// === 错误用法 ===
// 成功回调执行: 一切正常
// (之后会有一个 Uncaught Error 报错)
// 
// === 正确用法 ===
// 成功回调执行: 一切正常
// 错误被 .catch() 捕获: 成功回调里出了个新问题！
```

### 🚀 Level 4: 实战应用（真实场景）

**🚀 科幻冒险：星际矿物勘探**

我们来模拟一个驾驶太空飞船去外星球勘探矿物的任务。这个任务分为三步：发射探测器、扫描行星、分析样本。每一步都可能成功或失败。

```javascript
// 模拟发射探测器
function launchProbe() {
  console.log("🚀 发射探测器... 目标：未知行星 Gliese 581g");
  return new Promise((resolve, reject) => {
    setTimeout(() => {
      if (Math.random() > 0.2) {
        resolve("探测器成功着陆！");
      } else {
        reject(new Error("发射失败，探测器在小行星带失联！"));
      }
    }, 1000);
  });
}

// 模拟扫描行星
function scanPlanet(landingStatus) {
  console.log(`🛰️ 状态: ${landingStatus} 开始扫描行星...`);
  return new Promise((resolve, reject) => {
    setTimeout(() => {
      if (Math.random() > 0.3) {
        resolve({ status: "扫描完成", mineral: "超能量晶体" });
      } else {
        reject(new Error("扫描仪被强电磁风暴损坏！"));
      }
    }, 1000);
  });
}

// 模拟分析样本
function analyzeSample(scanResult) {
  console.log(`🔬 分析中... 发现矿物: ${scanResult.mineral}`);
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve(`分析报告：${scanResult.mineral} 纯度高达98.7%！价值连城！`);
    }, 1000);
  });
}

// --- 开始执行任务 ---
launchProbe()
  .then(scanPlanet)       // 发射成功后，扫描行星
  .then(analyzeSample)    // 扫描成功后，分析样本
  .then(finalReport => {  // 分析成功后，显示最终报告
    console.log(`🎉 任务大成功！${finalReport}`);
  })
  .catch(error => {       // 链条中任何一步失败，都会在这里捕获
    console.error(`💥 任务失败！原因: ${error.message}`);
  })
  .finally(() => {        // 无论成功或失败，都执行
    console.log("📡 任务结束，与地球总部的通讯关闭。");
  });

// 尝试多次运行，你会看到不同的任务结果！
```

### 💡 记忆要点
- **要点1**：`.then()` 处理成功结果，并能像链条一样把多个操作串起来。
- **要点2**：`.catch()` 是整个 Promise 链的“安全网”，捕获任何环节出现的错误。
- **要点3**：`.finally()` 是“收尾专家”，无论过程是喜是悲，它总会执行最后的清理工作。

<!--
metadata:
  syntax: [arrow-function]
  pattern: [promise-chain, error-handling]
  api: [Promise, console.log, setTimeout, Math.random, Error]
  concept: [asynchronous]
  difficulty: intermediate
  dependencies: [无]
  related: []
-->