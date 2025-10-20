## 定时器（setTimeout/setInterval）

### 🎯 核心概念
定时器允许你在指定的时间间隔后执行代码，而不是立即执行。这是JavaScript实现**异步编程**的基础，能防止耗时任务阻塞主线程，让网页或应用保持响应。

### 📚 Level 1: 基础认知（30秒理解）
`setTimeout` 就像一个闹钟，你设定好时间，它会在那个时间点响一次（执行一次代码）。

```javascript
// Level 1: 最简单的setTimeout示例

console.log("指令员：火箭准备发射！倒计时开始...");

// 设置一个2秒后执行的“一次性闹钟”
setTimeout(() => {
  // 这部分代码将在2秒后执行
  console.log("🚀 发射！火箭成功升空！");
}, 2000); // 2000毫秒 = 2秒

console.log("指令已发出，正在等待倒计时结束...");
// 注意：这行代码会立即执行，不会等待2秒
// 执行结果顺序：
// 1. "指令员：火箭准备发射！倒计时开始..."
// 2. "指令已发出，正在等待倒计时结束..."
// 3. (等待2秒后) "🚀 发射！火箭成功升空！"
```

### 📈 Level 2: 核心特性（深入理解）

#### 特性1: 一次性 vs. 周期性 (`setTimeout` vs `setInterval`)
`setTimeout`只执行一次，而`setInterval`会像心跳一样，每隔一个固定的时间周期性地重复执行。

```javascript
// Level 2, 特性1: setTimeout vs setInterval

// --- setTimeout: 只在1秒后执行一次 ---
const oneTimeTaskId = setTimeout(() => {
  console.log("【setTimeout】: 您的外卖到了，请查收！(此消息只提醒一次)");
}, 1000);
// clearTimeout(oneTimeTaskId); // 如果想在执行前取消，可以调用这个


// --- setInterval: 每秒执行一次，直到被清除 ---
let deliveryCount = 0;
const periodicTaskId = setInterval(() => {
  deliveryCount++;
  console.log(`【setInterval】: 第 ${deliveryCount} 份包裹正在派送中...`);

  // 当派送3次后，停止派送，否则会一直执行下去
  if (deliveryCount >= 3) {
    clearInterval(periodicTaskId); // 非常重要：清除定时器，防止无限循环
    console.log("【setInterval】: 所有包裹派送完毕！");
  }
}, 1000);

console.log("定时任务已启动，请关注控制台输出。");
```

#### 特性2: 向回调函数传递参数
`setTimeout`和`setInterval`都允许你将额外的参数传递给需要执行的函数。

```javascript
// Level 2, 特性2: 传递参数

function greet(name, occasion) {
  console.log(`你好, ${name}! 祝你在${occasion}玩得开心!`);
}

// 第三个及以后的参数，会作为greet函数的参数传入
// setTimeout(要执行的函数, 延迟时间, 参数1, 参数2, ...)
setTimeout(greet, 1500, '爱丽丝', '代码乐园');

// setInterval同样适用
let missionCount = 1;
const missionTimer = setInterval((agent, objective) => {
  console.log(`特工 ${agent}, 你的第 ${missionCount} 个任务是: ${objective}`);
  missionCount++;
  if (missionCount > 2) {
    clearInterval(missionTimer);
    console.log(`特工 ${agent}, 所有任务已传达完毕。`);
  }
}, 2000, '007', '寻找黄金代码');

console.log("参数传递示例已启动...");
```

### 🔍 Level 3: 对比学习（避免陷阱）
一个常见的错误是直接调用函数，而不是将函数本身作为参数传递给定时器。

```javascript
// Level 3: 对比学习

function showMessage(message) {
  console.log(message);
}

console.log("=== 错误用法 ===");
// ❌ 错误：直接调用了函数 showMessage(...)
// 这会导致 showMessage 立即执行，它的返回值(undefined)被传给了setTimeout
// 结果就是 "紧急警报" 立即被打印，而1秒后什么都不会发生
setTimeout(showMessage("❌ 紧急警报：这个消息会立即出现！"), 1000);
console.log("错误用法演示完毕，你会发现上面的消息没有延迟。");


console.log("\n=== 正确用法 ===");
// ✅ 正确：使用箭头函数包装，确保 showMessage 在1秒后被调用
setTimeout(() => {
  showMessage("✅ 系统正常：这个消息在1秒后出现。");
}, 1000);
// ✅ 或者直接传递函数引用（如果不需要传递自定义参数）
setTimeout(showMessage, 2000, "✅ 系统正常：这是另一种正确方式，在2秒后出现。");

console.log("正确用法已设置，请等待消息出现...");
```

### 🚀 Level 4: 实战应用（真实场景）
**场景: 🚀 科幻冒险 - 紧急！拆除脉冲炸弹！**

你是一名星际工程师，必须在10秒内拆除一个脉冲炸弹。你需要在倒计时结束前，找到正确的“引线”（在我们的代码里就是调用`defuseBomb`函数）。

```javascript
// Level 4: 拆弹游戏

const BOMB_TIMER_SECONDS = 10;
let timeLeft = BOMB_TIMER_SECONDS;

console.log("💥 警报！检测到脉冲炸弹！必须在10秒内拆除！");
console.log("启动拆弹倒计时...");

// 设置一个每秒运行一次的“心跳”定时器，作为炸弹的倒计时
const countdown = setInterval(() => {
  timeLeft--;
  console.log(`...滴...答... 剩余 ${timeLeft} 秒！`);

  // 时间到了，炸弹爆炸
  if (timeLeft <= 0) {
    clearInterval(countdown); // 停止倒计时
    console.log("💣💥 BOOM!!! 任务失败，时空结构已坍塌...");
  }
}, 1000);

// 拆弹函数：清除倒计时并宣布成功
function defuseBomb() {
  // 检查是否还有时间
  if (timeLeft > 0) {
    clearInterval(countdown); // 关键！停止爆炸倒计时！
    console.log(`✅ 呼... 在最后 ${timeLeft} 秒成功拆除炸弹！你拯救了整个星系！`);
  }
}

// 模拟玩家在第4秒时，找到了正确的引线并剪断了它
// 我们用一个setTimeout来模拟这个“延迟”的英雄行为
const defuseTime = 4000; // 4秒后进行拆弹
console.log(`你将在 ${defuseTime / 1000} 秒后尝试拆弹... 祝你好运！`);
setTimeout(defuseBomb, defuseTime);

// 试着修改 defuseTime 的值，比如改成 11000 (11秒)，看看会发生什么？
```

### 💡 记忆要点
- **`setTimeout(fn, ms)`**：延迟`ms`毫秒后，**执行一次**函数`fn`。
- **`setInterval(fn, ms)`**：**每隔**`ms`毫秒，就执行一次函数`fn`，直到被清除。
- **异步执行**：定时器不会阻塞代码，主程序会继续往下运行。要取消定时器，请使用`clearTimeout()`和`clearInterval()`，并传入它们返回的ID。

<!--
metadata:
  syntax: [function, arrow-function, let, const]
  pattern: [callback]
  api: [setTimeout, setInterval, clearTimeout, clearInterval, console.log]
  concept: [asynchronous, event-loop]
  difficulty: basic
  dependencies: [无]
  related: []
-->