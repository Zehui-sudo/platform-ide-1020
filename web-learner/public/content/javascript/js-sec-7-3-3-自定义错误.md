## 自定义错误

### 🎯 核心概念
自定义错误允许我们创建比JavaScript内置错误（如 `TypeError`, `ReferenceError`）更具体、更有描述性的错误类型，使错误处理逻辑更清晰、代码更易于维护。

### 📚 Level 1: 基础认知（30秒理解）
通过继承内置的 `Error` 类，我们可以轻松创建一个属于自己的错误类型。这就像给错误贴上一个专属的标签。

```javascript
// 定义一个自定义错误类
class MyCustomError extends Error {
  constructor(message) {
    super(message); // 调用父类 Error 的构造函数
    this.name = "MyCustomError"; // 设置错误名称为类名
  }
}

try {
  // 抛出一个我们自定义的错误实例
  throw new MyCustomError("这是一个非常特殊的错误！");
} catch (error) {
  console.log(`捕获到错误类型: ${error.name}`);
  console.log(`错误信息: ${error.message}`);
}
```

### 📈 Level 2: 核心特性（深入理解）
自定义错误不仅可以有自己的名字和信息，还能携带额外的上下文数据，让错误处理更智能。

#### 特性1: 保持堆栈跟踪（Stack Trace）
继承自 `Error` 的最大好处是能完整保留错误发生时的调用堆栈信息，这对于调试至关重要。

```javascript
class ValidationError extends Error {
  constructor(message) {
    super(message);
    this.name = 'ValidationError';
  }
}

function validateUsername(username) {
  if (username.length < 3) {
    // 抛出自定义错误
    throw new ValidationError("用户名长度不能小于3个字符。");
  }
  return true;
}

function createUser(username) {
    console.log("正在尝试创建用户...");
    validateUsername(username);
    console.log(`用户 "${username}" 创建成功！`);
}

try {
  createUser("Li"); // 使用一个不符合条件的用户名
} catch (error) {
  console.error(`错误名称: ${error.name}`);
  console.error(`错误消息: ${error.message}`);
  // 注意：error.stack 包含了从 createUser 到 validateUsername 的完整调用路径
  console.error("错误堆栈信息:");
  console.error(error.stack);
}
```

#### 特性2: 添加自定义属性
我们可以为错误对象添加额外的属性，比如错误码、相关数据等，以便在 `catch` 块中进行更精细的处理。

```javascript
class ApiError extends Error {
  constructor(message, errorCode, details) {
    super(message);
    this.name = 'ApiError';
    this.errorCode = errorCode; // 自定义属性：错误码
    this.details = details;     // 自定义属性：详细信息
  }
}

function fetchData() {
  // 模拟一个API请求失败的场景
  const isSuccess = false;
  if (!isSuccess) {
    throw new ApiError(
      "无法从服务器获取用户信息", 
      404, // 错误码
      { userId: "user-123", reason: "Not Found" } // 详细信息
    );
  }
}

try {
  fetchData();
} catch (error) {
  // 检查是否是我们期望的 ApiError 类型
  if (error instanceof ApiError) {
    console.log(`捕获到API错误！`);
    console.log(`消息: ${error.message}`);
    console.log(`错误码: ${error.errorCode}`);
    console.log(`详细信息:`, error.details);
  } else {
    console.log("捕获到未知错误:", error);
  }
}
```

### 🔍 Level 3: 对比学习（避免陷阱）
直接抛出字符串或普通对象是常见的错误做法，这会丢失重要的调试信息。

```javascript
function performAction(shouldSucceed) {
    if (!shouldSucceed) {
        // 错误的做法是抛出一个字符串或普通对象
        // throw "操作失败了！"; 
        throw { code: 500, msg: "数据库连接中断" };
    }
    return "操作成功！";
}

class OperationError extends Error {
    constructor(message, code) {
        super(message);
        this.name = "OperationError";
        this.code = code;
    }
}

function performCorrectAction(shouldSucceed) {
    if (!shouldSucceed) {
        // 正确的做法是抛出 Error 或其子类的实例
        throw new OperationError("数据库连接中断", 500);
    }
    return "操作成功！";
}

console.log("=== 错误用法 ===");
// ❌ 展示常见错误
try {
    performAction(false);
} catch (e) {
    console.error("捕获到的错误:", e);
    console.error("错误信息 (e.message):", e.message); // undefined，因为普通对象没有 message 属性
    console.error("堆栈信息 (e.stack):", e.stack);   // undefined，丢失了宝贵的堆栈信息！
    // 解释：直接抛出字符串或普通对象，会丢失标准错误对象的 name, message, stack 属性，
    // 这使得调试变得极其困难，也无法进行基于类型的错误判断（如 instanceof）。
}

console.log("\n=== 正确用法 ===");
// ✅ 展示正确做法
try {
    performCorrectAction(false);
} catch (e) {
    console.error("捕获到的错误:", e.name);
    console.error("错误信息 (e.message):", e.message); // "数据库连接中断"
    console.error("自定义属性 (e.code):", e.code);   // 500
    console.error("堆栈信息可用 (e.stack):", e.stack.includes("performCorrectAction")); // true
    // 解释：通过抛出 Error 子类的实例，我们保留了所有关键信息，
    // 并且可以添加自定义数据，使得错误处理既健壮又灵活。
}
```

### 🚀 Level 4: 实战应用（真实场景）
**🚀 科幻冒险：星际飞船曲速引擎启动程序**

在这个场景中，我们模拟启动一艘名为“探索者号”的飞船的曲速引擎。启动过程可能会因为各种原因失败，我们将为每种失败情况创建自定义错误。

```javascript
// === 自定义错误类型定义 ===

// 能源不足错误
class InsufficientEnergyError extends Error {
  constructor(message, required, actual) {
    super(message);
    this.name = 'InsufficientEnergyError';
    this.requiredEnergy = required;
    this.actualEnergy = actual;
  }
}

// 导航系统错误
class NavigationSystemError extends Error {
  constructor(message, targetPlanet) {
    super(message);
    this.name = 'NavigationSystemError';
    this.targetPlanet = targetPlanet;
  }
}

// 外星生物干扰错误
class AlienInterferenceError extends Error {
  constructor(message, alienRace) {
    super(message);
    this.name = 'AlienInterferenceError';
    this.alienRace = alienRace;
  }
}

// === 飞船系统函数 ===

function engageWarpDrive(shipState) {
  console.log(`🚀 舰长，正在尝试启动曲速引擎，目标：${shipState.targetPlanet}...`);

  // 1. 检查能源
  if (shipState.energyLevel < 100) {
    throw new InsufficientEnergyError(
      "曲速核心能源不足！",
      100,
      shipState.energyLevel
    );
  }
  
  // 2. 检查导航系统
  if (!shipState.navSystemOnline) {
    throw new NavigationSystemError(
      "导航计算机未上线，无法锁定目标！",
      shipState.targetPlanet
    );
  }

  // 3. 检查外部环境 (随机事件)
  if (Math.random() > 0.7) { // 30%的概率遇到外星人
    throw new AlienInterferenceError(
      "警报！侦测到不明能量信号，曲速场被干扰！",
      "博格人"
    );
  }

  console.log(`✅ 曲速引擎成功启动！正在跃迁至 ${shipState.targetPlanet}！`);
}

// === 模拟一次启动尝试 ===

// 飞船当前状态
const explorerShipState = {
  energyLevel: 95, // 故意设置一个不足的能源值
  navSystemOnline: true,
  targetPlanet: "比邻星b"
};

try {
  engageWarpDrive(explorerShipState);
} catch (error) {
  console.error("\n--- 启动程序失败！---");
  // 根据不同的错误类型，执行不同的应对措施
  if (error instanceof InsufficientEnergyError) {
    console.error(`🔴 错误类型: ${error.name}`);
    console.error(`💬 舰长日志: ${error.message}`);
    console.error(`🔧 解决方案: 需要能量 ${error.requiredEnergy} 单位，当前仅剩 ${error.actualEnergy}。请立即为反应堆充能！`);
  } else if (error instanceof NavigationSystemError) {
    console.error(`🟡 错误类型: ${error.name}`);
    console.error(`💬 舰长日志: ${error.message}`);
    console.error(`🔧 解决方案: 工程师请立即重启导航系统，目标星球 ${error.targetPlanet} 的坐标需要重新校准。`);
  } else if (error instanceof AlienInterferenceError) {
    console.error(`🟣 错误类型: ${error.name}`);
    console.error(`💬 舰长日志: ${error.message}`);
    console.error(`⚔️ 紧急措施: 红色警报！升起护盾！可能是 ${error.alienRace} 的飞船！`);
  } else {
    // 处理其他未知错误
    console.error("🚨 发生未知系统故障！", error);
  }
}
```

### 💡 记忆要点
- **继承 `Error`**：自定义错误类应始终 `extends Error` 以获得堆栈跟踪等核心功能。
- **调用 `super()`**：在构造函数中，必须首先调用 `super(message)` 来正确初始化父类。
- **设置 `this.name`**：将 `this.name` 设置为你的类名，这有助于在调试时快速识别错误类型。

<!--
metadata:
  syntax: ["class", "extends", "constructor", "super", "throw", "try", "catch"]
  pattern: ["error-handling"]
  api: ["Error", "console.log", "console.error"]
  concept: ["inheritance", "prototype"]
  difficulty: intermediate
  dependencies: ["无"]
  related: ["js-sec-7-3-2"]
-->