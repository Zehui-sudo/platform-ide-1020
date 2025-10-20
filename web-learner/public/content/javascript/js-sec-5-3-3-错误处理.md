## 错误处理

### 🎯 核心概念
错误处理是一种编程机制，它允许我们预见并优雅地处理代码中可能发生的异常情况，防止程序因意外错误而崩溃，从而提高应用的健壮性和用户体验。

### 📚 Level 1: 基础认知（30秒理解）
当一段代码可能出错时，我们可以使用 `try...catch` 语句来“捕捉”这个错误。`try` 块中放置可能出错的代码，如果真的发生错误，程序会立即跳转到 `catch` 块执行，而不会中断整个程序的运行。

```javascript
console.log("程序开始运行...");

try {
  // 尝试调用一个不存在的函数，这会引发一个错误
  nonExistentFunction(); 
} catch (error) {
  // 如果try块中发生错误，这里的代码就会被执行
  console.log("糟糕！捕捉到了一个错误！");
  console.log("错误信息:", error.message); // error对象包含了错误的详细信息
}

console.log("程序继续运行，没有因为错误而崩溃。");
```

### 📈 Level 2: 核心特性（深入理解）

#### 特性1: `finally` 块 - 无论如何都会执行
`finally` 块是可选的，它包含的代码无论 `try` 块中是否发生错误，都一定会被执行。这对于执行“清理”工作（如关闭文件、释放资源）非常有用。

```javascript
function processData(shouldThrowError) {
  console.log(`--- 开始处理数据 (是否会出错: ${shouldThrowError}) ---`);
  try {
    console.log("进入 try 块，尝试处理数据...");
    if (shouldThrowError) {
      // 模拟一个处理错误
      throw new Error("数据格式不正确！");
    }
    console.log("数据处理成功！");
  } catch (error) {
    console.log(`在 catch 块中捕获到错误: ${error.message}`);
  } finally {
    // 无论是否出错，finally块总会执行
    console.log("进入 finally 块，执行清理操作（例如：关闭数据库连接）。");
  }
  console.log("--- 数据处理结束 ---\n");
}

// 场景1: 没有发生错误
processData(false);

// 场景2: 发生错误
processData(true);
```

#### 特性2: `throw` - 主动抛出自定义错误
除了捕捉JavaScript内置的错误，我们还可以使用 `throw` 关键字来创建并抛出我们自己的错误。这在验证函数参数或检查业务逻辑时特别有用。

```javascript
function calculateCircleArea(radius) {
  console.log(`尝试计算半径为 ${radius} 的圆面积...`);
  
  if (typeof radius !== 'number') {
    // 如果输入不是数字，就主动抛出一个类型错误
    throw new TypeError("参数必须是数字！");
  }
  
  if (radius < 0) {
    // 如果半径为负数，不符合业务逻辑，抛出一个自定义错误
    throw new Error("半径不能为负数！");
  }
  
  const area = Math.PI * radius * radius;
  console.log(`计算成功，面积是: ${area.toFixed(2)}`);
  return area;
}

try {
  calculateCircleArea(10); // 正常情况
  calculateCircleArea(-5); // 触发自定义错误
} catch (error) {
  console.error(`[错误捕获] 计算失败: ${error.message}`);
}

try {
  calculateCircleArea("hello"); // 触发类型错误
} catch (error) {
  console.error(`[错误捕获] 计算失败: ${error.message}`);
}
```

### 🔍 Level 3: 对比学习（避免陷阱）
不处理潜在的错误，可能会导致程序崩溃或产生无法预料的静默失败。

```javascript
// 模拟一个可能失败的JSON解析函数
function parseUserData(jsonString) {
  // JSON.parse在遇到无效JSON时会抛出错误
  return JSON.parse(jsonString);
}

console.log("=== 错误用法 ===");
// ❌ 错误用法：直接调用，不处理潜在的错误
// 如果jsonString格式错误，下面这行代码会导致整个程序崩溃。
// 在这个可交互环境中，你可能只会看到一个错误信息，但在真实应用中，后续代码将全部停止执行。
try {
    const invalidJson = '{"name": "Alice", "age": 30,}'; // 注意末尾多余的逗号，这是无效JSON
    const user = parseUserData(invalidJson);
    console.log("用户信息:", user.name); // 这行代码永远不会执行
} catch (error) {
    console.log("程序因未捕获的错误而中断。错误信息:", error.message);
    console.log("❌ 这种方式非常危险，因为它没有错误处理机制。");
}


console.log("\n=== 正确用法 ===");
// ✅ 正确用法：使用 try...catch 包裹可能出错的代码
function safeParseUserData(jsonString) {
  try {
    const user = JSON.parse(jsonString);
    console.log(`✅ 解析成功！欢迎，${user.name}！`);
    return user;
  } catch (error) {
    console.error(`❌ 解析失败！无效的数据格式。错误详情: ${error.message}`);
    return null; // 返回一个默认值或null，让程序可以继续
  }
}

const validJson = '{"name": "Bob", "age": 25}';
const invalidJson = '{"name": "Charlie", "age": }'; // 故意写错的JSON

safeParseUserData(validJson);
safeParseUserData(invalidJson);
console.log("✅ 程序优雅地处理了错误，并继续执行。");
```

### 🚀 Level 4: 实战应用（真实场景）

**🚀 科幻冒险：外星语言翻译器**

在这个场景中，我们正在开发一个用于星际探索的“外星语言翻译器”。翻译器有一个小小的词典，但对于词典之外的词汇，它会抛出一个“未知信号”错误。我们需要捕获这个错误，并用友好的方式通知船员。

```javascript
// 模拟一个外星语言词典
const alienDictionary = {
  'hello': 'Gleep Glorp',
  'world': 'Zorp',
  'human': 'Squishy',
  'danger': 'Klaatu Barada Nikto'
};

// 翻译函数，如果找不到单词会抛出自定义错误
function translateToAlien(word) {
  const lowerCaseWord = word.toLowerCase();
  if (alienDictionary[lowerCaseWord]) {
    return alienDictionary[lowerCaseWord];
  } else {
    // 找不到单词，抛出一个特定的错误
    throw new Error(`未知信号: 无法翻译单词 "${word}"`);
  }
}

// 主程序：尝试翻译一条来自地球的信息
function broadcastMessage(message) {
  console.log(`🚀 正在尝试向外星文明广播信息: "${message}"`);
  const words = message.split(' ');
  let translatedMessage = '';

  for (const word of words) {
    try {
      // 尝试翻译每个单词
      const translatedWord = translateToAlien(word);
      translatedMessage += translatedWord + ' ';
    } catch (error) {
      // 捕获到翻译错误！
      console.warn(`[翻译模块警告] ${error.message}`);
      console.log(`...用[静态噪音]代替未知单词...`);
      // 用一个占位符代替无法翻译的词
      translatedMessage += '[STATIC_NOISE] ';
    }
  }
  
  console.log(`📡 广播已发送: "${translatedMessage.trim()}"\n`);
}

// 场景1: 一条可以完全翻译的信息
broadcastMessage("Hello human");

// 场景2: 包含未知词汇的信息
broadcastMessage("Warning: Danger ahead"); // 'Warning' 和 'ahead' 不在词典里
```

### 💡 记忆要点
- **`try`包裹**：将可能出错的代码放入 `try` 块中，像给它穿上“防护服”。
- **`catch`捕获**：在 `catch(error)` 块中定义错误发生时的应对策略，`error` 对象包含错误详情。
- **`finally`清理**：`finally` 块中的代码是“万金油”，无论成功失败，总会执行，适合做收尾工作。
- **`throw`主动**：使用 `throw new Error()` 来主动创造并抛出符合业务逻辑的自定义错误。

<!--
metadata:
  syntax: try-catch, throw, finally
  pattern: error-handling
  api: console.log, console.error, console.warn, Error, TypeError
  concept: exception, control-flow
  difficulty: advanced
  dependencies: []
  related: [js-sec-6-1-1]
-->