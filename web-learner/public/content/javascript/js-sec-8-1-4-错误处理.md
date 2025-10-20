## 错误处理

### 🎯 核心概念
错误处理机制让我们能够优雅地捕获并处理代码执行期间的意外问题，防止程序因错误而直接崩溃，并能给出明确的反馈或执行备用方案。

### 📚 Level 1: 基础认知（30秒理解）
`try...catch` 语句是最基本的错误处理方式。我们将可能出错的代码放入 `try` 块中，如果发生错误，程序会立即跳转到 `catch` 块执行，而不是中断整个脚本。

```javascript
// 尝试解析一个格式错误的JSON字符串
try {
  console.log("尝试解析JSON...");
  const invalidJson = '{"name": "Alice", "age": 30,}'; // 注意末尾多余的逗号，这是无效的JSON
  const user = JSON.parse(invalidJson);
  console.log("解析成功:", user); // 这行代码不会被执行
} catch (error) {
  // 如果try块中发生错误，代码会跳转到这里
  console.error("捕获到错误！程序不会崩溃。");
  console.error("错误详情:", error.message);
}

console.log("即使发生了错误，程序依然可以继续执行到这里。");
```

### 📈 Level 2: 核心特性（深入理解）

#### 特性1: `finally` - 无论如何都会执行的清理工作
`finally` 块中的代码，无论 `try` 块是否发生错误，都保证会被执行。它非常适合用于执行“清理”工作，比如关闭文件、断开网络连接等。

```javascript
function connectToDatabase(status) {
  console.log("正在尝试连接数据库...");
  if (status === 'fail') {
    throw new Error("数据库连接失败！");
  }
  console.log("数据库连接成功！");
}

// 场景一：连接成功
try {
  connectToDatabase('success');
  console.log("数据操作完成。");
} catch (error) {
  console.error("捕获到错误:", error.message);
} finally {
  console.log("--- 无论成功与否，关闭数据库连接。---\n");
}


// 场景二：连接失败
try {
  connectToDatabase('fail');
  console.log("这行不会被执行...");
} catch (error) {
  console.error("捕获到错误:", error.message);
} finally {
  // 即使发生错误，finally块依然会执行
  console.log("--- 无论成功与否，关闭数据库连接。---");
}
```

#### 特性2: `throw` - 主动抛出自定义错误
我们可以使用 `throw` 关键字主动抛出一个错误。这在函数接收到无效参数或遇到不符合预期的情况时非常有用，可以清晰地告诉调用者“这里出错了”。

```javascript
function calculateCircleArea(radius) {
  if (typeof radius !== 'number' || radius < 0) {
    // 如果半径不是一个正数，就抛出一个自定义错误
    throw new Error("无效的半径值！半径必须是一个非负数。");
  }
  return Math.PI * radius * radius;
}

try {
  // 尝试使用无效参数调用函数
  console.log("尝试计算面积，使用半径: -5");
  const area = calculateCircleArea(-5);
  console.log("计算的面积是:", area);
} catch (error) {
  console.error("计算失败，原因:", error.message);
}

try {
  // 尝试使用有效参数调用函数
  console.log("\n尝试计算面积，使用半径: 10");
  const area = calculateCircleArea(10);
  console.log("计算的面积是:", area.toFixed(2));
} catch (error) {
  console.error("计算失败，原因:", error.message);
}
```

### 🔍 Level 3: 对比学习（避免陷阱）
不使用错误处理会导致整个程序因一个可预见的错误而停止运行，这在实际应用中是不可接受的。

```javascript
// 假设这是一个从服务器获取用户数据的函数，但可能失败
function fetchUserData(userId) {
  if (userId <= 0) {
    throw new Error("用户ID必须是正数！");
  }
  // 模拟成功获取数据
  return { id: userId, name: "CaptainCode" };
}

console.log("=== 错误用法 ===");
// ❌ 直接调用，不处理潜在的错误
// 下面的调用会抛出错误，导致程序崩溃，"程序结束" 这句话永远不会被打印出来。
try {
    console.log("正在获取用户 -1 的数据...");
    const user = fetchUserData(-1); 
    console.log("用户信息:", user);
} catch (e) {
    console.error("由于未捕获的错误，脚本在这里就停止了！");
    console.error(e.message);
}
// console.log("程序结束"); // 如果没有try...catch，这行不会执行

console.log("\n=== 正确用法 ===");
// ✅ 使用 try...catch 优雅地处理错误
try {
  console.log("正在获取用户 -1 的数据...");
  const user = fetchUserData(-1);
  console.log("用户信息:", user);
} catch (error) {
  console.error("获取用户数据失败，但程序可以继续运行。");
  console.error("失败原因:", error.message);
  console.log("可以执行备用逻辑，比如显示默认用户信息。");
}
console.log("程序优雅地处理了错误，并继续执行到了末尾。");

```

### 🚀 Level 4: 实战应用（真实场景）
**🚀 科幻冒险：星际跃迁引擎**

在这个场景中，我们扮演一艘星际飞船的舰长。我们的任务是启动跃迁引擎，前往新的星系。但是，跃迁引擎非常精密，如果坐标错误或者能量不足，就会抛出特定的错误。我们需要用 `try...catch` 来处理这些紧急情况，保证飞船的安全！

```javascript
// 定义一些自定义的错误类型，让问题更明确
class InvalidCoordinatesError extends Error {
  constructor(message) {
    super(message);
    this.name = "InvalidCoordinatesError";
  }
}

class InsufficientEnergyError extends Error {
  constructor(message) {
    super(message);
    this.name = "InsufficientEnergyError";
  }
}

// 跃迁引擎函数
function activateWarpDrive(destination, energyLevel) {
  console.log(`\n🚀 舰长，收到指令！目标：${destination}，当前能量：${energyLevel}%`);
  
  if (!destination || typeof destination !== 'string') {
    throw new InvalidCoordinatesError("跃迁坐标无效！导航系统无法锁定目标。");
  }
  
  if (energyLevel < 80) {
    throw new InsufficientEnergyError(`能量严重不足！跃迁需要至少80%，当前仅有${energyLevel}%。`);
  }
  
  // 如果一切正常
  return `✅ 跃迁引擎启动成功！正在前往 ${destination} 星系... 祝您旅途愉快！`;
}

// --- 任务开始 ---

// 尝试1: 忘记输入坐标
try {
  const result = activateWarpDrive(null, 95);
  console.log(result);
} catch (error) {
  console.error(`🚨 警报! ${error.name}: ${error.message}`);
  console.log("导航官：舰长，请提供明确的跃迁目标！");
}

// 尝试2: 能量不足
try {
  const result = activateWarpDrive("仙女座星系", 50);
  console.log(result);
} catch (error) {
  console.error(`🚨 警报! ${error.name}: ${error.message}`);
  console.log("轮机长：舰长，我们需要更多时间为引擎充能！");
}

// 尝试3: 一切顺利！
try {
  const result = activateWarpDrive("创作者星云", 100);
  console.log(result);
} catch (error) {
  console.error(`🚨 警报! ${error.name}: ${error.message}`);
  console.log("系统日志：出现未知跃迁故障。");
}

```

### 💡 记忆要点
- **要点1**：`try` 块用于包裹可能出错的代码，它是“代码的安全区”。
- **要点2**：`catch` 块是 `try` 块的“急救站”，当错误发生时，它会捕获错误对象并执行相应的处理逻辑。
- **要点3**：`finally` 块是“收尾专家”，无论成功还是失败，它都会执行，确保资源被正确释放。

<!--
metadata:
  syntax: ["try-catch", "finally", "throw", "class"]
  pattern: ["error-handling"]
  api: ["console.log", "console.error", "Error", "JSON.parse"]
  concept: ["exception", "control-flow", "custom-error"]
  difficulty: intermediate
  dependencies: ["js-sec-8-1-1"]
  related: ["js-sec-8-2-2"]
-->