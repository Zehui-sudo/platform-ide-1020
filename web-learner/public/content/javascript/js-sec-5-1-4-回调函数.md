## 回调函数

### 🎯 核心概念
回调函数解决了“在某个任务完成后，接下来该做什么”的问题。它允许我们将一个函数作为参数传递给另一个函数，以便在那个函数执行完毕后的某个特定时机被“回调”执行，这对于处理异步操作（如等待数据加载）或创建可定制的通用功能至关重要。

### 📚 Level 1: 基础认知（30秒理解）
想象一下你去餐厅点餐，你告诉服务员（主函数）你的菜单（参数），并留下你的电话号码（回调函数）。服务员做好菜后，会用你的电话号码联系你。这个“打电话”的动作，就是回调。

```javascript
// 服务员函数，接收订单和联系方式（回调函数）
function placeOrder(dish, callback) {
  console.log(`收到订单：一份香喷喷的 ${dish}！`);
  console.log("厨房正在加急制作中...");

  // 模拟制作过程需要2秒
  setTimeout(() => {
    // 制作完成，调用回调函数通知顾客
    const message = `${dish} 已经准备好了，请来取餐！`;
    callback(message);
  }, 2000);
}

// 顾客的联系方式（回调函数本身）
function customerNotification(message) {
  console.log("叮咚! 收到通知:");
  console.log(message);
}

// 顾客开始点餐，并把自己的联系方式告诉服务员
placeOrder("红烧JavaScript鱼", customerNotification);

console.log("我先去逛逛，做好了叫我。");
```

### 📈 Level 2: 核心特性（深入理解）
回调函数不仅用于异步，还能让函数变得更灵活、更通用。

#### 特性1: 异步操作的“信使”
在JavaScript中，很多操作（如网络请求、文件读写、定时器）不是立即完成的。回调函数就像一个信使，我们把它派出去，告诉主任务：“等你忙完了，就让这个信使回来告诉我结果。”

```javascript
function fetchDataFromServer(callback) {
  console.log("正在向服务器请求数据...");
  // 模拟一个需要3秒的网络请求
  setTimeout(() => {
    const data = { userId: 1, content: "Hello, Callback World!" };
    console.log("数据已成功获取！");
    // 数据回来后，调用回调函数处理数据
    callback(data);
  }, 3000);
}

function processData(data) {
  console.log("接收到数据，开始处理...");
  console.log(`用户ID: ${data.userId}, 内容: "${data.content}"`);
}

fetchDataFromServer(processData);

console.log("请求已发送，程序不会卡在这里，可以继续执行其他任务。");
```

#### 特性2: 函数行为的“插件”
回调函数可以让一个通用函数拥有多种不同的行为，就像给它安装了不同的“插件”。例如，一个处理数组的函数，具体如何处理每个元素，可以由传入的回调函数决定。

```javascript
function processArray(arr, processor) {
  const results = [];
  for (let i = 0; i < arr.length; i++) {
    // 使用传入的 processor 回调函数来处理每个元素
    results.push(processor(arr[i]));
  }
  return results;
}

// “插件1”：将每个数字翻倍
function double(num) {
  return num * 2;
}

// “插件2”：将每个数字转为描述性字符串
function describe(num) {
  return `这是一个神奇的数字: ${num}`;
}

const numbers = [1, 2, 3, 4];

// 使用 double 插件
const doubledNumbers = processArray(numbers, double);
console.log("使用'翻倍'插件:", doubledNumbers);

// 使用 describe 插件
const describedNumbers = processArray(numbers, describe);
console.log("使用'描述'插件:", describedNumbers);
```

### 🔍 Level 3: 对比学习（避免陷阱）
一个非常常见的错误是：在传递回调函数时，不小心把它执行了。

```javascript
function executeAfterDelay(callback) {
  console.log("准备在2秒后执行回调...");
  setTimeout(callback, 2000);
}

function myCallback() {
  console.log("回调函数被成功执行了！");
}

console.log("=== 错误用法 ===");
// ❌ 错误：传入了 myCallback() 的 *执行结果* (即 undefined)，而不是函数本身
// 这会导致 myCallback 立即执行，而 setTimeout 收到的是 undefined，什么都不会发生
executeAfterDelay(myCallback());
console.log("错误演示中，上面那行代码会立即打印回调内容，而不是等待2秒。");

console.log("\n=== 正确用法 ===");
// ✅ 正确：传入 myCallback 这个 *函数引用*
// setTimeout 会在2秒后拿到这个函数引用并执行它
executeAfterDelay(myCallback);
console.log("正确演示中，请等待2秒查看回调结果。");
```

### 🚀 Level 4: 实战应用（真实场景）
**场景：🎮 魔法装备升级系统**

在一个奇幻冒险游戏中，玩家“代码勇士”想升级他的传奇武器“语法圣剑”。升级过程充满了不确定性，可能会成功，也可能会失败。我们用回调函数来处理这两种不同的结果。

```javascript
/**
 * 魔法锻造台：尝试升级装备
 * @param {string} itemName - 要升级的装备名称
 * @param {function} onSuccess - 升级成功时调用的回调
 * @param {function} onFailure - 升级失败时调用的回调
 */
function attemptUpgrade(itemName, onSuccess, onFailure) {
  console.log(`代码勇士将【${itemName}】放入了魔法锻造台...`);
  console.log("锻造台发出神秘的光芒，开始进行强化... (请稍候)");

  // 模拟一个耗时且有风险的升级过程
  setTimeout(() => {
    const isSuccess = Math.random() > 0.5; // 50% 的成功率

    if (isSuccess) {
      // 成功了！调用成功回调
      onSuccess(itemName);
    } else {
      // 失败了！调用失败回调
      onFailure(itemName);
    }
  }, 3000);
}

// 准备好处理成功情况的“庆祝仪式”
function celebrateSuccess(item) {
  console.log(`🎉 哇！【${item}】升级成功！光芒四射，威力大增！`);
  console.log("代码勇士的攻击力 +100！");
}

// 准备好处理失败情况的“安慰话语”
function mournFailure(item) {
  console.log(`💥 啊哦...一阵黑烟冒出，【${item}】升级失败了...`);
  console.log("代码勇士叹了口气：没关系，下次再来！");
}

// 开始升级！把成功和失败的处理方案都告诉锻造台
attemptUpgrade("语法圣剑", celebrateSuccess, mournFailure);

console.log("升级结果将在3秒后揭晓，代码勇士正在紧张地搓手手...");
```

### 💡 记忆要点
- **函数作参数**：回调函数本质上就是一个被当作参数传递给另一个函数的函数。
- **延迟执行**：它不会立即执行，而是在主函数内部的特定时机（如异步操作完成时）被“回调”执行。
- **控制反转**：你写的代码（回调函数）的执行权，交给了你调用的那个函数（主函数）来控制。

<!--
metadata:
  syntax: [function]
  pattern: [callback]
  api: [setTimeout, console.log, Math.random]
  concept: [asynchronous, higher-order-function]
  difficulty: intermediate
  dependencies: [无]
  related: [js-sec-5-2-1]
-->