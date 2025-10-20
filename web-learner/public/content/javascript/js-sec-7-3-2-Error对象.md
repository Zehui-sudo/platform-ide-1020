## Error对象

### 🎯 核心概念
Error对象用于标准化地表示和处理代码在运行时发生的错误，它能提供错误的详细信息（如消息和调用堆栈），使调试和程序异常处理变得更加清晰和可控。

### 📚 Level 1: 基础认知（30秒理解）
最简单的用法是使用 `new Error()` 构造函数创建一个错误对象。它就像一个标准化的“问题报告”，包含了问题描述。

```javascript
// 创建一个最基本的Error对象
const simpleError = new Error('网络连接超时！');

// Error对象有两个主要属性：name 和 message
console.log('错误类型 (name):', simpleError.name);
console.log('错误信息 (message):', simpleError.message);

// 你也可以直接打印整个对象，但通常message更有用
// console.log(simpleError);
```

### 📈 Level 2: 核心特性（深入理解）
Error对象不仅有基本信息，还包含强大的调试工具，并且通常与 `throw` 和 `try...catch` 结合使用。

#### 特性1: 核心属性 (name, message, stack)
每个Error实例都包含关键的调试信息。

```javascript
function connectToDatabase() {
  // 模拟一个错误
  const dbError = new Error('数据库用户认证失败');
  dbError.name = 'DatabaseAuthError'; // 可以自定义错误名称

  console.log('错误名称:', dbError.name);
  console.log('错误消息:', dbError.message);
  
  // .stack 属性是调试的利器，它显示了错误发生时的函数调用路径
  // 注意：stack的内容和格式可能因不同的浏览器或Node.js环境而异
  console.log('--- 调用堆栈信息 (stack) ---');
  console.log(dbError.stack);
}

connectToDatabase();
```

#### 特性2: 使用 `throw` 抛出并用 `try...catch` 捕获
创建Error对象本身不会中断程序，你需要使用 `throw` 关键字将其“抛出”，然后用 `try...catch` 语句来“捕获”并处理它。

```javascript
function calculateArea(width, height) {
  if (typeof width !== 'number' || typeof height !== 'number') {
    // 当参数无效时，我们“抛出”一个Error对象，中断函数执行
    throw new Error('宽度和高度必须是数字！');
  }
  if (width <= 0 || height <= 0) {
    throw new Error('宽度和高度必须是正数！');
  }
  return width * height;
}

try {
  // 我们将可能出错的代码放入 try 块中
  const area = calculateArea(10, -5);
  console.log('计算出的面积是:', area);
} catch (error) {
  // 如果 try 块中抛出了错误，代码会立即跳转到 catch 块
  console.error('🚫 发生了一个错误！');
  console.error('错误详情:', error.message);
} finally {
  // finally 块中的代码无论是否发生错误都会执行
  console.log('--- 计算结束 ---');
}
```

### 🔍 Level 3: 对比学习（避免陷阱）
一个常见的错误是直接 `throw` 一个字符串，而不是一个 `Error` 对象。这会丢失大量有用的调试信息。

```javascript
console.log("=== 错误用法 ===");
// ❌ 直接抛出一个字符串
try {
  const data = '{"name": "Alice"'; // 这是一个不完整的JSON字符串
  JSON.parse(data);
} catch (e) {
  // 假设我们不知道JSON.parse会抛出Error对象，而是自己抛出一个字符串
  throw "解析用户数据失败"; 
}
// 注意：在现代JS环境中，上面的throw会直接导致程序崩溃并报错。
// 为了演示捕获，我们把它包在另一个try...catch中。
try {
  try { throw "解析用户数据失败"; } catch (e) { throw e; }
} catch (e) {
  console.log("捕获到的东西:", e);
  console.log("是Error对象吗?", e instanceof Error);
  console.log("有.message属性吗?", e.message); // undefined
  console.log("有.stack属性吗?", e.stack);   // undefined
  // 解释：直接抛出字符串，会丢失错误类型、堆栈等重要调试信息。
  // 捕获到的'e'只是一个普通的字符串，而不是一个带有上下文信息的对象。
}


console.log("\n=== 正确用法 ===");
// ✅ 抛出 new Error() 的实例
try {
  const data = '{"name": "Alice"';
  JSON.parse(data);
} catch (e) {
  // 将原始错误包装在一个新的、更具描述性的Error对象中
  throw new Error("解析用户数据失败，请检查数据格式。");
}
// 同样，为了演示捕获，我们把它包起来
try {
  try { throw new Error("解析用户数据失败"); } catch (e) { throw e; }
} catch (e) {
  console.log("捕获到的东西是一个对象");
  console.log("是Error对象吗?", e instanceof Error);
  console.log("有.message属性吗?", e.message);
  console.log("还有堆栈信息:", e.stack ? '是的，内容很长' : '没有');
  // 解释：抛出Error对象是标准做法。捕获到的'e'是一个真正的Error实例，
  // 包含了name, message, stack等标准属性，这对于日志记录和调试至关重要。
}
```

### 🚀 Level 4: 实战应用（真实场景）
**场景：🚀 太空探索飞船的导航系统**

我们的飞船需要一个导航系统来计算跳跃到目标星球所需的燃料。如果输入无效或燃料不足，系统需要抛出特定的错误，以便控制台能给出清晰的警告！

```javascript
// --- 定义飞船专用的自定义错误类型 ---
// 这让我们可以更精确地识别错误来源
class NavigationError extends Error {
  constructor(message) {
    super(message);
    this.name = 'NavigationError';
  }
}

class InsufficientFuelError extends Error {
  constructor(required, available) {
    super(`燃料不足！需要 ${required} 单位，但只有 ${available} 单位。`);
    this.name = 'InsufficientFuelError';
    this.requiredFuel = required;
    this.availableFuel = available;
  }
}

// --- 飞船导航系统核心函数 ---
function calculateJumpFuel(targetPlanet, currentFuel) {
  console.log(`🛰️ 正在计算前往 '${targetPlanet}' 的航线...`);
  const planetDistances = {
    '火星': 50,
    '木星': 200,
    '半人马座α星': 1000,
    '未知领域': Infinity
  };

  const requiredFuel = planetDistances[targetPlanet];

  if (requiredFuel === undefined) {
    throw new NavigationError(`错误：目标星球 '${targetPlanet}' 不在星图中！`);
  }

  if (requiredFuel > currentFuel) {
    throw new InsufficientFuelError(requiredFuel, currentFuel);
  }

  return `✅ 计算完成！前往 ${targetPlanet} 需要 ${requiredFuel} 单位燃料。准备跳跃！`;
}

// --- 任务控制中心操作 ---
function attemptJump(target, fuel) {
  console.log(`\n--- 尝试跳跃到: ${target}, 当前燃料: ${fuel} ---`);
  try {
    const result = calculateJumpFuel(target, fuel);
    console.log(result);
  } catch (error) {
    // 根据错误类型，显示不同的警告信息
    if (error instanceof NavigationError) {
      console.error(`👨‍🚀 导航警告: ${error.message}`);
    } else if (error instanceof InsufficientFuelError) {
      console.error(`⛽️ 燃料警告: ${error.message}`);
      console.error(`   我们还差 ${error.requiredFuel - error.availableFuel} 单位燃料才能到达！`);
    } else {
      console.error(`🚨 未知系统故障: ${error.message}`);
    }
  }
}

// 模拟几次太空跳跃
attemptJump('火星', 100);       // 成功
attemptJump('木星', 150);       // 燃料不足
attemptJump('仙女座星系', 9999); // 目标不存在
```

### 💡 记忆要点
- **要点1**：`new Error('message')` 创建一个包含 `name`, `message`, `stack` 属性的标准错误对象。
- **要点2**：始终使用 `throw new Error(...)` 抛出错误，而不是抛出字符串或数字，以便保留完整的错误信息。
- **要点3**：使用 `try...catch` 结构来优雅地捕获和处理可能发生的错误，防止程序崩溃，并可以根据错误类型执行不同的逻辑。

<!--
metadata:
  syntax: ['class', 'constructor', 'super', 'throw', 'try-catch', 'instanceof']
  pattern: ['error-handling']
  api: ['Error', 'console.error', 'console.log']
  concept: ['exception-handling', 'custom-errors']
  difficulty: intermediate
  dependencies: [无]
  related: []
-->