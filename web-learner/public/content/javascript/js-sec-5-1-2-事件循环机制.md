## 事件循环机制

### 🎯 核心概念
事件循环机制（Event Loop）是JavaScript实现异步编程的核心，它解决了“单线程的JavaScript如何处理耗时操作（如网络请求、定时器）而不会阻塞主线程”这一根本问题。

### 📚 Level 1: 基础认知（30秒理解）
JavaScript代码是单线程执行的，意味着一次只能做一件事。但`setTimeout`等异步操作似乎可以“稍后”执行。这是怎么回事？事件循环让这一切成为可能。同步代码会先执行完毕，然后才会执行异步任务的回调。

```javascript
// Level 1: 同步与异步的执行顺序

console.log("1. 早餐：开始做饭");

// 设置一个0毫秒的定时器，代表一个异步任务（比如：用微波炉热牛奶）
// 即使是0毫秒，它也会被放入“任务队列”等待
setTimeout(() => {
  console.log("3. 早餐：牛奶热好了！");
}, 0);

console.log("2. 早餐：面包烤好了，先吃面包");

// 输出结果：
// 1. 早餐：开始做饭
// 2. 早餐：面包烤好了，先吃面包
// 3. 早餐：牛奶热好了！
```

### 📈 Level 2: 核心特性（深入理解）
事件循环不仅仅是“先同步，后异步”。它有一个精确的调度模型，主要涉及调用栈、任务队列和微任务队列。

#### 特性1: 调用栈（Call Stack）与任务队列（Task Queue）
所有同步代码都在**调用栈**中执行。当遇到像`setTimeout`这样的异步API时，它的回调函数会被交给浏览器处理，并在指定时间后放入**任务队列**（也叫宏任务队列）。事件循环会不断检查调用栈是否为空，如果为空，就从任务队列中取出一个任务放入调用栈执行。

```javascript
// Level 2, Feature 1: 调用栈与任务队列

function main() {
  console.log('A: 进入主函数 main');
  taskA();
  // 设置一个宏任务
  setTimeout(() => {
    console.log('D: 定时器回调执行');
  }, 10); // 10ms后放入任务队列
  console.log('C: 退出主函数 main');
}

function taskA() {
  console.log('B: 执行任务A');
}

// 开始执行
main();

// 执行流程分析:
// 1. main() 进入调用栈。打印 'A'。
// 2. taskA() 进入调用栈。打印 'B'。taskA() 结束，出栈。
// 3. setTimeout 被调用，其回调函数被交给Web API，计时器开始。
// 4. 打印 'C'。main() 结束，出栈。
// 5. 调用栈变空。
// 6. 10ms后，Web API将定时器回调放入任务队列。
// 7. 事件循环发现调用栈为空，从任务队列取出回调，放入调用栈执行。
// 8. 打印 'D'。
```

#### 特性2: 微任务（Microtask）优先于宏任务（Macrotask）
任务队列实际上分为两种：宏任务（Macrotask）和微任务（Microtask）。`setTimeout`的回调是宏任务，而`Promise.then()`的回调是微任务。事件循环在一个宏任务执行完毕后，会立即清空所有微任务队列中的任务，然后再执行下一个宏任务。

```javascript
// Level 2, Feature 2: 微任务与宏任务

console.log('1. 同步代码：开始');

// 注册一个宏任务
setTimeout(() => {
  console.log('5. 宏任务：setTimeout 回调');
}, 0);

// 注册一个微任务
Promise.resolve().then(() => {
  console.log('3. 微任务：Promise.then 回调 1');
}).then(() => {
  console.log('4. 微任务：Promise.then 回调 2');
});

console.log('2. 同步代码：结束');

// 输出结果：
// 1. 同步代码：开始
// 2. 同步代码：结束
// 3. 微任务：Promise.then 回调 1
// 4. 微任务：Promise.then 回调 2
// 5. 宏任务：setTimeout 回调

// 分析：同步代码执行完后，事件循环发现微任务队列有任务，
// 于是清空微任务队列（执行所有.then），最后才从宏任务队列取任务执行。
```

### 🔍 Level 3: 对比学习（避免陷阱）
一个常见的误解是认为可以通过`setTimeout(fn, 0)`来强制改变一个变量，并立即在下一行代码中获取到更新后的值。这是不可能的，因为它违反了事件循环的规则。

```javascript
// Level 3: 对比学习

console.log("=== 错误用法 ===");
// ❌ 错误：试图在同步代码中获取异步更新的值
let pizzaStatus = "准备中...";
setTimeout(() => {
  pizzaStatus = "可以吃了！";
  console.log("内部更新状态:", pizzaStatus); // 这里是 "可以吃了！"
}, 0);
console.log("外部立即检查状态:", pizzaStatus); // 这里仍然是 "准备中..."
// 解释：console.log是同步代码，会立即执行。
// setTimeout的回调被放入任务队列，在所有同步代码执行完之前，它绝不会执行。
// 因此，外部检查时，状态尚未被更新。

console.log("\n=== 正确用法 ===");
// ✅ 正确：使用回调函数或Promise来处理异步结果
function preparePizza(callback) {
  let status = "准备中...";
  console.log("开始准备披萨...");
  // 模拟一个异步的烘焙过程
  setTimeout(() => {
    status = "可以吃了！";
    // 当披萨准备好后，调用回调函数并传入结果
    callback(status);
  }, 100);
}

// 定义一个回调函数，用于处理披萨准备好的情况
function enjoyPizza(status) {
  console.log("现在披萨的状态是:", status);
}

// 调用函数，并传入回调
preparePizza(enjoyPizza);
// 解释：我们将处理结果的逻辑（enjoyPizza）作为参数传给异步函数。
// 当异步操作完成时，它会主动调用我们传入的函数，确保了时序的正确性。
```

### 🚀 Level 4: 实战应用（真实场景）
**场景：🚀 太空探索 - 紧急任务计时器**

你是一名星际飞船的AI，需要为一个紧急的太空行走任务设计一个倒计时和指令系统。宇航员需要在倒计时结束前的特定“窗口期”内按下“紧急返回”按钮。事件循环将完美地处理这个时序问题。

```javascript
// Level 4: 太空探索任务计时器

function startSpacewalkMission(totalTime, returnWindowStart) {
  console.log("👩‍🚀 AI: 任务开始！太空行走总时长:", totalTime, "秒。");
  console.log("------------------------------------------");

  let missionStatus = "进行中";

  // 1. 设置任务结束的宏任务（最外层的定时器）
  setTimeout(() => {
    if (missionStatus === "进行中") {
      missionStatus = "失败";
      console.log("💥 AI: 时间耗尽！宇航员未能及时返回！任务失败！");
    }
  }, totalTime * 1000);

  // 2. 设置“返回窗口期”开始的宏任务
  setTimeout(() => {
    console.log("🟡 AI: 警告！返回窗口期开启！请在倒计时结束前返回！");
    missionStatus = "等待返回";
  }, returnWindowStart * 1000);

  // 3. 模拟宇航员的操作
  function astronautAction(actionTime) {
    // 宇航员的行动也是一个异步事件
    setTimeout(() => {
      console.log(`\n🧑‍🚀 宇航员在第 ${actionTime} 秒按下“紧急返回”按钮...`);
      // 使用Promise（微任务）来立即处理宇航员的行动结果
      Promise.resolve().then(() => {
        if (missionStatus === "等待返回") {
          missionStatus = "成功";
          console.log("✅ AI: 时机完美！宇航员安全返回！任务成功！");
        } else if (missionStatus === "进行中") {
          missionStatus = "提前返回";
          console.log("🤔 AI: 宇航员提前返回，虽然安全，但未完成所有勘探任务。");
        }
      });
    }, actionTime * 1000);
  }

  // --- 模拟场景 ---
  // 场景A: 宇航员在窗口期内正确返回
  astronautAction(8);

  // 场景B: (可以取消注释来测试) 宇航员返回太早
  // astronautAction(3);

  // 场景C: (可以取消注释来测试) 宇航员返回太晚 (此场景下任务会超时失败)
  // astronautAction(11);
}

// 任务总时长10秒，返回窗口从第5秒开始
startSpacewalkMission(10, 5);
```

### 💡 记忆要点
- **要点1**：先清空调用栈（所有同步代码），再处理异步任务。
- **要.点2**：微任务（如`Promise.then`）的优先级高于宏任务（如`setTimeout`）。当前宏任务执行完后，会立即清空所有微任务。
- **要点3**：`setTimeout(fn, 0)`不代表“立即执行”，而是“尽快执行”，即放入任务队列的开头，等待调用栈清空。

<!--
metadata:
  syntax: ["function", "arrow-function", "let"]
  pattern: ["callback", "asynchronous"]
  api: ["setTimeout", "console.log", "Promise"]
  concept: ["event-loop", "call-stack", "callback-queue", "microtask", "macrotask"]
  difficulty: advanced
  dependencies: [无]
  related: ["js-sec-5-1-1"]
-->